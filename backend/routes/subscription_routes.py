"""Subscription, Billing, and Trial API routes.

Super admin: create plans, assign subscriptions, manage billing status.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, Header
from typing import Annotated, Optional
from datetime import datetime, timezone, timedelta

from auth import get_current_user
from models import User
from subscription_models import (
    SUBSCRIPTION_STATUSES, BILLING_CYCLES,
    Plan, PlanCreate, PlanUpdate, PlanResponse,
    Subscription, SubscriptionAssign, SubscriptionAction,
    TrialExtension, MarkPaidOffline, SubscriptionResponse,
    BillingAuditLog,
)


def create_subscription_router(db):
    router = APIRouter(prefix="/admin/billing", tags=["billing"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    async def require_admin(user: User):
        if not user.is_super_admin:
            raise HTTPException(403, "Super admin access required")

    async def _audit(sub_id, cid, action, prev, new, user_id, notes='', meta=None):
        log = BillingAuditLog(
            subscription_id=sub_id, community_id=cid, action=action,
            previous_status=prev, new_status=new, performed_by=user_id,
            notes=notes, metadata=meta or {},
        )
        doc = log.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.billing_audit_logs.insert_one(doc)

    async def _enrich_sub(sub: dict) -> dict:
        """Add community_name and plan_name to subscription response."""
        comm = await db.communities.find_one({'community_id': sub['community_id']}, {'_id': 0, 'name': 1})
        plan = await db.plans.find_one({'plan_id': sub['plan_id']}, {'_id': 0, 'name': 1})
        sub['community_name'] = comm['name'] if comm else None
        sub['plan_name'] = plan['name'] if plan else None
        return sub

    # ══════ PLAN CRUD ══════

    @router.get("/plans", response_model=list[PlanResponse])
    async def list_plans(
        active_only: bool = False,
        current_user: User = Depends(get_user_dep),
    ):
        await require_admin(current_user)
        query = {'is_active': True} if active_only else {}
        plans = await db.plans.find(query, {'_id': 0}).sort('created_at', -1).to_list(100)
        return plans

    @router.post("/plans", response_model=PlanResponse, status_code=201)
    async def create_plan(data: PlanCreate, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        existing = await db.plans.find_one({'name': data.name, 'billing_cycle': data.billing_cycle})
        if existing:
            raise HTTPException(400, "Plan with this name and billing cycle already exists")

        plan = Plan(**data.model_dump())
        doc = plan.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.plans.insert_one(doc)
        doc.pop('_id', None)
        return doc

    @router.patch("/plans/{plan_id}", response_model=PlanResponse)
    async def update_plan(plan_id: str, data: PlanUpdate, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        plan = await db.plans.find_one({'plan_id': plan_id}, {'_id': 0})
        if not plan:
            raise HTTPException(404, "Plan not found")

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(400, "No fields to update")
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        await db.plans.update_one({'plan_id': plan_id}, {'$set': updates})
        return await db.plans.find_one({'plan_id': plan_id}, {'_id': 0})

    @router.delete("/plans/{plan_id}")
    async def delete_plan(plan_id: str, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        active_subs = await db.subscriptions.count_documents({'plan_id': plan_id, 'status': {'$in': ['active', 'trial']}})
        if active_subs > 0:
            raise HTTPException(400, f"Cannot delete: {active_subs} active subscriptions use this plan. Deactivate it instead.")
        result = await db.plans.delete_one({'plan_id': plan_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Plan not found")
        return {"message": "Plan deleted"}

    # ══════ SUBSCRIPTION MANAGEMENT ══════

    @router.get("/subscriptions", response_model=list[SubscriptionResponse])
    async def list_subscriptions(
        status: Optional[str] = None,
        community_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
        current_user: User = Depends(get_user_dep),
    ):
        await require_admin(current_user)
        query = {}
        if status:
            query['status'] = status
        if community_id:
            query['community_id'] = community_id
        subs = await db.subscriptions.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        return [await _enrich_sub(s) for s in subs]

    @router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
    async def get_subscription(subscription_id: str, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        return await _enrich_sub(sub)

    @router.post("/subscriptions/assign", response_model=SubscriptionResponse, status_code=201)
    async def assign_subscription(data: SubscriptionAssign, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)

        community = await db.communities.find_one({'community_id': data.community_id}, {'_id': 0})
        if not community:
            raise HTTPException(404, "Community not found")
        plan = await db.plans.find_one({'plan_id': data.plan_id}, {'_id': 0})
        if not plan:
            raise HTTPException(404, "Plan not found")
        if not plan.get('is_active'):
            raise HTTPException(400, "Cannot assign inactive plan")

        existing = await db.subscriptions.find_one({
            'community_id': data.community_id,
            'status': {'$in': ['active', 'trial', 'pending_payment']},
        })
        if existing:
            raise HTTPException(400, "Community already has an active/trial subscription")

        now = datetime.now(timezone.utc)
        trial_end = (now + timedelta(days=data.trial_days)).isoformat() if data.trial_days > 0 else None

        sub = Subscription(
            community_id=data.community_id,
            plan_id=data.plan_id,
            status='trial' if data.trial_days > 0 else 'pending_payment',
            trial_start_date=now.isoformat() if data.trial_days > 0 else None,
            trial_end_date=trial_end,
            trial_threshold_type=data.trial_threshold_type,
            trial_member_limit=data.trial_member_limit,
            assigned_by=current_user.user_id,
            notes=data.notes,
        )
        doc = sub.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.subscriptions.insert_one(doc)
        doc.pop('_id', None)

        await _audit(doc['subscription_id'], data.community_id, 'assigned', None, doc['status'], current_user.user_id, data.notes)
        return await _enrich_sub(doc)

    # ── Status transitions ──

    @router.post("/subscriptions/{subscription_id}/activate")
    async def activate_subscription(subscription_id: str, data: SubscriptionAction = SubscriptionAction(), current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        if sub['status'] not in ('trial', 'pending_payment', 'paused'):
            raise HTTPException(400, f"Cannot activate from status: {sub['status']}")

        plan = await db.plans.find_one({'plan_id': sub['plan_id']}, {'_id': 0})
        now = datetime.now(timezone.utc)
        cycle_days = 365 if plan and plan['billing_cycle'] == 'yearly' else 30

        updates = {
            'status': 'active',
            'billing_start_date': now.isoformat(),
            'billing_end_date': (now + timedelta(days=cycle_days)).isoformat(),
            'next_payment_date': (now + timedelta(days=cycle_days)).isoformat(),
            'updated_at': now.isoformat(),
        }
        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': updates})
        await _audit(subscription_id, sub['community_id'], 'activated', sub['status'], 'active', current_user.user_id, data.notes)
        return {"message": "Subscription activated", "status": "active"}

    @router.post("/subscriptions/{subscription_id}/pause")
    async def pause_subscription(subscription_id: str, data: SubscriptionAction = SubscriptionAction(), current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        if sub['status'] != 'active':
            raise HTTPException(400, f"Cannot pause from status: {sub['status']}")

        now = datetime.now(timezone.utc).isoformat()
        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': {
            'status': 'paused', 'paused_at': now, 'updated_at': now,
        }})
        await _audit(subscription_id, sub['community_id'], 'paused', 'active', 'paused', current_user.user_id, data.notes)
        return {"message": "Subscription paused", "status": "paused"}

    @router.post("/subscriptions/{subscription_id}/resume")
    async def resume_subscription(subscription_id: str, data: SubscriptionAction = SubscriptionAction(), current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        if sub['status'] != 'paused':
            raise HTTPException(400, f"Cannot resume from status: {sub['status']}")

        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': {
            'status': 'active', 'paused_at': None, 'updated_at': datetime.now(timezone.utc).isoformat(),
        }})
        await _audit(subscription_id, sub['community_id'], 'resumed', 'paused', 'active', current_user.user_id, data.notes)
        return {"message": "Subscription resumed", "status": "active"}

    @router.post("/subscriptions/{subscription_id}/cancel")
    async def cancel_subscription(subscription_id: str, data: SubscriptionAction = SubscriptionAction(), current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        if sub['status'] in ('canceled', 'expired'):
            raise HTTPException(400, f"Subscription already {sub['status']}")

        now = datetime.now(timezone.utc).isoformat()
        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': {
            'status': 'canceled', 'canceled_at': now, 'updated_at': now,
        }})
        await _audit(subscription_id, sub['community_id'], 'canceled', sub['status'], 'canceled', current_user.user_id, data.notes)
        return {"message": "Subscription canceled", "status": "canceled"}

    @router.post("/subscriptions/{subscription_id}/mark-paid")
    async def mark_paid_offline(subscription_id: str, data: MarkPaidOffline, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")

        plan = await db.plans.find_one({'plan_id': sub['plan_id']}, {'_id': 0})
        now = datetime.now(timezone.utc)
        cycle_days = 365 if plan and plan['billing_cycle'] == 'yearly' else 30

        updates = {
            'status': 'active',
            'last_payment_date': now.isoformat(),
            'billing_start_date': now.isoformat(),
            'billing_end_date': (now + timedelta(days=cycle_days)).isoformat(),
            'next_payment_date': (now + timedelta(days=cycle_days)).isoformat(),
            'updated_at': now.isoformat(),
        }
        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': updates})
        await _audit(subscription_id, sub['community_id'], 'paid_offline', sub['status'], 'active', current_user.user_id, data.notes, {
            'amount': data.amount, 'reference': data.payment_reference,
        })
        return {"message": "Payment recorded, subscription activated", "status": "active"}

    # ── Trial management ──

    @router.post("/subscriptions/{subscription_id}/extend-trial")
    async def extend_trial(subscription_id: str, data: TrialExtension, current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        sub = await db.subscriptions.find_one({'subscription_id': subscription_id}, {'_id': 0})
        if not sub:
            raise HTTPException(404, "Subscription not found")
        if sub['status'] != 'trial':
            raise HTTPException(400, "Can only extend trial-status subscriptions")

        current_end = sub.get('trial_end_date', '')
        if current_end:
            end_dt = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now(timezone.utc)
        new_end = (end_dt + timedelta(days=data.extra_days)).isoformat()

        await db.subscriptions.update_one({'subscription_id': subscription_id}, {'$set': {
            'trial_end_date': new_end,
            'trial_extended': True,
            'trial_extension_days': sub.get('trial_extension_days', 0) + data.extra_days,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }})
        await _audit(subscription_id, sub['community_id'], 'trial_extended', 'trial', 'trial', current_user.user_id, data.notes, {'extra_days': data.extra_days})
        return {"message": f"Trial extended by {data.extra_days} days", "new_trial_end": new_end}

    # ── Audit logs ──

    @router.get("/audit-logs")
    async def list_audit_logs(
        subscription_id: Optional[str] = None,
        community_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
        current_user: User = Depends(get_user_dep),
    ):
        await require_admin(current_user)
        query = {}
        if subscription_id:
            query['subscription_id'] = subscription_id
        if community_id:
            query['community_id'] = community_id
        if action:
            query['action'] = action
        logs = await db.billing_audit_logs.find(query, {'_id': 0}).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
        return logs

    # ── Community subscription check (public for middleware) ──

    @router.get("/communities/{community_id}/subscription", response_model=SubscriptionResponse)
    async def get_community_subscription(community_id: str, current_user: User = Depends(get_user_dep)):
        sub = await db.subscriptions.find_one(
            {'community_id': community_id, 'status': {'$nin': ['canceled', 'expired']}},
            {'_id': 0},
        )
        if not sub:
            raise HTTPException(404, "No active subscription found")
        return await _enrich_sub(sub)

    return router
