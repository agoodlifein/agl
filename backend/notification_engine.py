"""Core notification engine.

Responsibilities:
1. Resolve audience (recipients) from segment + community
2. Resolve the effective template (community override or default)
3. Render placeholders
4. Dispatch via the pluggable provider
5. Write delivery logs

Usage from any route:
    from notification_engine import notify
    await notify(db, 'welcome_member', community_id, {'user_name': 'Alice', ...})
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from notification_models import (
    CHANNEL_MAP, NotificationLog,
)
from notification_providers import MockProvider, NotificationProvider

logger = logging.getLogger(__name__)

# Global provider instance — swap for real provider when keys are available
_provider: NotificationProvider = MockProvider()


def set_provider(provider: NotificationProvider):
    """Replace the active notification provider at runtime."""
    global _provider
    _provider = provider


# ── Public API ───────────────────────────────────────────────────────

async def notify(
    db: AsyncIOMotorDatabase,
    notification_type: str,
    community_id: str,
    context: dict,
    recipient_user_ids: Optional[list[str]] = None,
    segment: Optional[str] = None,
):
    """Fire-and-forget notification trigger.

    Args:
        db: Database handle
        notification_type: One of NOTIFICATION_TYPES
        community_id: Community context
        context: Dict of placeholder values (user_name, community_name, etc.)
        recipient_user_ids: Explicit list of user IDs (overrides segment)
        segment: Audience segment ('all', 'member', 'moderator', 'community_manager')
    """
    try:
        await _process_notification(
            db, notification_type, community_id, context,
            recipient_user_ids, segment,
        )
    except Exception:
        logger.exception("Notification engine error for type=%s community=%s",
                         notification_type, community_id)


# ── Internal ─────────────────────────────────────────────────────────

async def _process_notification(
    db, notification_type, community_id, context,
    recipient_user_ids, segment,
):
    channels = CHANNEL_MAP.get(notification_type, ['email'])

    # Resolve recipients
    if recipient_user_ids:
        recipients = await _get_users_by_ids(db, recipient_user_ids)
    elif segment:
        recipients = await _get_recipients_by_segment(db, community_id, segment)
    else:
        recipients = []

    if not recipients:
        logger.warning("No recipients for %s in community %s", notification_type, community_id)
        return

    # Get community name for context
    community = await db.communities.find_one({'community_id': community_id}, {'_id': 0, 'name': 1})
    context.setdefault('community_name', community['name'] if community else 'Unknown')

    for channel in channels:
        template, is_override = await _resolve_template(db, notification_type, channel, community_id)
        if not template:
            logger.warning("No template for type=%s channel=%s", notification_type, channel)
            continue

        for user in recipients:
            ctx = {**context, 'user_name': user.get('name', ''), 'manager_name': user.get('name', '')}
            rendered_subject = _render(template.get('subject', ''), ctx)
            rendered_body = _render(template.get('body', ''), ctx)

            log = NotificationLog(
                notification_type=notification_type,
                channel=channel,
                community_id=community_id,
                community_name=context.get('community_name'),
                recipient_user_id=user['user_id'],
                recipient_email=user.get('email'),
                recipient_phone=user.get('phone'),
                template_id=template['template_id'],
                subject=rendered_subject,
                body=rendered_body,
                status='queued',
                trigger_event=notification_type,
                trigger_data=context,
            )

            result = await _dispatch(channel, user, rendered_subject, rendered_body)

            log.status = 'sent' if result['success'] else 'failed'
            log.error_message = result.get('error')
            log.sent_at = datetime.now(timezone.utc) if result['success'] else None

            log_doc = log.model_dump()
            log_doc['created_at'] = log_doc['created_at'].isoformat()
            if log_doc.get('sent_at'):
                log_doc['sent_at'] = log_doc['sent_at'].isoformat()

            await db.notification_logs.insert_one(log_doc)


async def _resolve_template(db, notification_type, channel, community_id):
    """Return (effective template dict, is_override)."""
    default = await db.notification_templates.find_one(
        {'notification_type': notification_type, 'channel': channel},
        {'_id': 0},
    )
    if not default:
        return None, False

    # Check for community override (only if template is not locked)
    if not default.get('is_locked'):
        override = await db.community_template_overrides.find_one(
            {'template_id': default['template_id'], 'community_id': community_id},
            {'_id': 0},
        )
        if override:
            merged = {**default}
            if override.get('subject'):
                merged['subject'] = override['subject']
            if override.get('body'):
                merged['body'] = override['body']
            return merged, True

    return default, False


def _render(template_str: str, context: dict) -> str:
    """Replace {{placeholder}} with context values."""
    def replacer(match):
        key = match.group(1).strip()
        return str(context.get(key, f'{{{{{key}}}}}'))
    return re.sub(r'\{\{(\w+)\}\}', replacer, template_str)


async def _dispatch(channel, user, subject, body):
    """Send via the active provider."""
    try:
        if channel == 'email':
            email = user.get('email')
            if not email:
                return {'success': False, 'error': 'No email address'}
            return await _provider.send_email(email, subject, body)
        elif channel == 'whatsapp':
            phone = user.get('phone')
            if not phone:
                return {'success': False, 'error': 'No phone number'}
            return await _provider.send_whatsapp(phone, body)
        else:
            return {'success': False, 'error': f'Unknown channel: {channel}'}
    except Exception as exc:
        logger.exception("Dispatch error channel=%s user=%s", channel, user.get('user_id'))
        return {'success': False, 'error': str(exc)}


async def _get_users_by_ids(db, user_ids):
    """Fetch user docs for a list of IDs."""
    users = await db.users.find(
        {'user_id': {'$in': user_ids}},
        {'_id': 0, 'user_id': 1, 'email': 1, 'name': 1, 'phone': 1},
    ).to_list(1000)
    return users


async def _get_recipients_by_segment(db, community_id, segment):
    """Get community members filtered by role segment."""
    query = {'community_id': community_id, 'is_active': True}
    if segment and segment != 'all':
        query['role_name'] = segment

    memberships = await db.community_memberships.find(
        query, {'_id': 0, 'user_id': 1},
    ).to_list(10000)

    if not memberships:
        return []

    user_ids = [m['user_id'] for m in memberships]
    return await _get_users_by_ids(db, user_ids)
