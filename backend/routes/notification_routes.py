"""Notification & communication API routes.

Super admin: manage default templates, lock/unlock, view all logs.
Community manager: override unlocked templates, send event notifications, view community logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, Header
from typing import Annotated, Optional
from datetime import datetime, timezone

from models import User
from auth import get_current_user
from notification_models import (
    NOTIFICATION_TYPES, CHANNELS, SEGMENTS,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateOverrideUpdate, TemplateWithOverrideResponse,
    NotificationLogResponse, EventNotificationRequest,
    NotificationTemplate, CommunityTemplateOverride,
)
from notification_engine import notify


# ── Super Admin Routes ───────────────────────────────────────────────

def create_admin_notification_router(db):
    router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    async def require_admin(current_user: User):
        if not current_user.is_super_admin:
            raise HTTPException(403, "Super admin access required")
        return current_user

    # ── List all default templates ──
    @router.get("/templates", response_model=list[TemplateResponse])
    async def list_templates(
        notification_type: Optional[str] = None,
        channel: Optional[str] = None,
        current_user: User = Depends(get_user_dep),
    ):
        await require_admin(current_user)
        query = {}
        if notification_type:
            query['notification_type'] = notification_type
        if channel:
            query['channel'] = channel
        templates = await db.notification_templates.find(
            query, {'_id': 0}
        ).sort('notification_type', 1).to_list(100)
        return templates

    # ── Create default template ──
    @router.post("/templates", response_model=TemplateResponse, status_code=201)
    async def create_template(data: TemplateCreate, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        existing = await db.notification_templates.find_one({
            'notification_type': data.notification_type,
            'channel': data.channel,
        })
        if existing:
            raise HTTPException(400, "Template for this type+channel already exists")

        tmpl = NotificationTemplate(
            notification_type=data.notification_type,
            channel=data.channel,
            name=data.name,
            subject=data.subject,
            body=data.body,
            placeholders=data.placeholders,
            created_by=current_user.user_id,
        )
        doc = tmpl.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.notification_templates.insert_one(doc)
        doc.pop('_id', None)
        return doc

    # ── Update default template ──
    @router.patch("/templates/{template_id}", response_model=TemplateResponse)
    async def update_template(template_id: str, data: TemplateUpdate, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        tmpl = await db.notification_templates.find_one({'template_id': template_id}, {'_id': 0})
        if not tmpl:
            raise HTTPException(404, "Template not found")

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(400, "No fields to update")
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()

        await db.notification_templates.update_one({'template_id': template_id}, {'$set': updates})
        updated = await db.notification_templates.find_one({'template_id': template_id}, {'_id': 0})
        return updated

    # ── Lock / Unlock template ──
    @router.post("/templates/{template_id}/lock")
    async def lock_template(template_id: str, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        result = await db.notification_templates.update_one(
            {'template_id': template_id},
            {'$set': {'is_locked': True, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(404, "Template not found")
        return {"message": "Template locked"}

    @router.post("/templates/{template_id}/unlock")
    async def unlock_template(template_id: str, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        result = await db.notification_templates.update_one(
            {'template_id': template_id},
            {'$set': {'is_locked': False, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(404, "Template not found")
        return {"message": "Template unlocked"}

    # ── Delete template ──
    @router.delete("/templates/{template_id}")
    async def delete_template(template_id: str, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        result = await db.notification_templates.delete_one({'template_id': template_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Template not found")
        await db.community_template_overrides.delete_many({'template_id': template_id})
        return {"message": "Template deleted"}

    # ── All delivery logs ──
    @router.get("/logs", response_model=list[NotificationLogResponse])
    async def list_all_logs(
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        community_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
        current_user: User = Depends(get_user_dep),
    ):
        await require_admin(current_user)
        query = {}
        if notification_type:
            query['notification_type'] = notification_type
        if status:
            query['status'] = status
        if community_id:
            query['community_id'] = community_id
        logs = await db.notification_logs.find(
            query, {'_id': 0}
        ).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        return logs

    # ── Log stats ──
    @router.get("/logs/stats")
    async def log_stats(current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        pipeline = [
            {'$group': {
                '_id': {'type': '$notification_type', 'status': '$status', 'channel': '$channel'},
                'count': {'$sum': 1},
            }},
            {'$sort': {'_id.type': 1}},
        ]
        results = await db.notification_logs.aggregate(pipeline).to_list(100)
        stats = {}
        for r in results:
            key = r['_id']['type']
            if key not in stats:
                stats[key] = {'total': 0, 'sent': 0, 'failed': 0, 'by_channel': {}}
            stats[key]['total'] += r['count']
            stats[key][r['_id']['status']] = stats[key].get(r['_id']['status'], 0) + r['count']
            ch = r['_id']['channel']
            stats[key]['by_channel'][ch] = stats[key]['by_channel'].get(ch, 0) + r['count']
        return stats

    return router


# ── Community Manager Routes ─────────────────────────────────────────

def create_manager_notification_router(db):
    router = APIRouter(prefix="/manager", tags=["manager-notifications"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    async def verify_manager(slug: str, current_user: User):
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(404, "Community not found")
        if not current_user.is_super_admin:
            membership = await db.community_memberships.find_one({
                'community_id': community['community_id'],
                'user_id': current_user.user_id,
                'role_name': 'community_manager',
                'is_active': True,
            })
            if not membership:
                raise HTTPException(403, "Community manager access required")
        return community

    # ── List templates with override status ──
    @router.get("/communities/{slug}/notifications/templates",
                response_model=list[TemplateWithOverrideResponse])
    async def list_community_templates(slug: str, current_user: User = Depends(get_user_dep)):
        community = await verify_manager(slug, current_user)
        cid = community['community_id']

        templates = await db.notification_templates.find({}, {'_id': 0}).sort('notification_type', 1).to_list(100)
        result = []
        for t in templates:
            override = await db.community_template_overrides.find_one(
                {'template_id': t['template_id'], 'community_id': cid}, {'_id': 0}
            )
            result.append(TemplateWithOverrideResponse(
                template_id=t['template_id'],
                notification_type=t['notification_type'],
                channel=t['channel'],
                name=t['name'],
                subject=t.get('subject'),
                body=t['body'],
                placeholders=t.get('placeholders', []),
                is_locked=t.get('is_locked', False),
                has_override=override is not None,
                override_subject=override.get('subject') if override else None,
                override_body=override.get('body') if override else None,
            ))
        return result

    # ── Create/Update template override ──
    @router.patch("/communities/{slug}/notifications/templates/{template_id}")
    async def upsert_template_override(
        slug: str, template_id: str, data: TemplateOverrideUpdate,
        current_user: User = Depends(get_user_dep),
    ):
        community = await verify_manager(slug, current_user)
        cid = community['community_id']

        tmpl = await db.notification_templates.find_one({'template_id': template_id}, {'_id': 0})
        if not tmpl:
            raise HTTPException(404, "Template not found")
        if tmpl.get('is_locked'):
            raise HTTPException(403, "This template is locked by super admin and cannot be overridden")

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(400, "No fields to update")

        existing = await db.community_template_overrides.find_one(
            {'template_id': template_id, 'community_id': cid}
        )
        if existing:
            updates['updated_by'] = current_user.user_id
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            await db.community_template_overrides.update_one(
                {'template_id': template_id, 'community_id': cid},
                {'$set': updates},
            )
        else:
            override = CommunityTemplateOverride(
                template_id=template_id,
                community_id=cid,
                subject=updates.get('subject'),
                body=updates.get('body'),
                updated_by=current_user.user_id,
            )
            doc = override.model_dump()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.community_template_overrides.insert_one(doc)

        return {"message": "Template override saved"}

    # ── Remove template override ──
    @router.delete("/communities/{slug}/notifications/templates/{template_id}")
    async def remove_template_override(
        slug: str, template_id: str, current_user: User = Depends(get_user_dep),
    ):
        community = await verify_manager(slug, current_user)
        result = await db.community_template_overrides.delete_one(
            {'template_id': template_id, 'community_id': community['community_id']}
        )
        if result.deleted_count == 0:
            raise HTTPException(404, "No override found for this template")
        return {"message": "Override removed, reverted to default"}

    # ── Send event notification ──
    @router.post("/communities/{slug}/notifications/send-event")
    async def send_event_notification(
        slug: str, req: EventNotificationRequest, current_user: User = Depends(get_user_dep),
    ):
        community = await verify_manager(slug, current_user)
        cid = community['community_id']

        event = await db.events.find_one({'event_id': req.event_id, 'community_id': cid}, {'_id': 0})
        if not event:
            raise HTTPException(404, "Event not found in this community")

        context = {
            'community_name': community['name'],
            'event_title': event['title'],
            'event_date': event.get('event_date', ''),
            'event_time': event.get('event_time', ''),
            'event_venue': event.get('venue', 'TBD'),
            'event_description': event.get('description', ''),
        }

        await notify(db, 'new_event', cid, context, segment=req.segment)
        return {"message": f"Event notification queued for segment: {req.segment}"}

    # ── Community delivery logs ──
    @router.get("/communities/{slug}/notifications/logs", response_model=list[NotificationLogResponse])
    async def list_community_logs(
        slug: str,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
        current_user: User = Depends(get_user_dep),
    ):
        community = await verify_manager(slug, current_user)
        query = {'community_id': community['community_id']}
        if notification_type:
            query['notification_type'] = notification_type
        if status:
            query['status'] = status
        logs = await db.notification_logs.find(
            query, {'_id': 0}
        ).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        return logs

    return router
