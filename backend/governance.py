"""Governance middleware and cross-module enforcement.

Subscription enforcement: Block community actions if subscription is expired/canceled.
Branding validation: Enforce limits on logo size, accent colors, etc.
Media cleanup: Auto-delete orphaned media files.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)

# Routes that require an active subscription for community actions
SUBSCRIPTION_ENFORCED_PREFIXES = [
    '/api/manager/communities/',
    '/api/communities/{slug}/threads',
    '/api/communities/{slug}/events',
]

# Routes exempt from subscription checks (read-only or admin)
EXEMPT_PATTERNS = [
    r'^/api/communities/[^/]+$',           # GET community detail
    r'^/api/communities/$',                  # GET community list
    r'^/api/communities/[^/]+/search',       # Search
    r'^/api/communities/[^/]+/seo/',         # SEO reads
    r'^/api/communities/[^/]+/membership-status',  # Membership check
    r'^/api/admin/',                         # Admin routes
    r'^/api/auth/',                          # Auth routes
    r'^/api/profile',                        # Profile routes
    r'^/api/health',                         # Health
]


class SubscriptionEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to check subscription status before allowing community write actions."""

    def __init__(self, app, db):
        super().__init__(app)
        self.db = db

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Only enforce on write operations to community-scoped routes
        if method in ('GET', 'HEAD', 'OPTIONS'):
            return await call_next(request)

        # Check if this is a community-scoped write action
        slug_match = re.match(r'^/api/(?:manager/)?communities/([^/]+)/', path)
        if not slug_match:
            return await call_next(request)

        slug = slug_match.group(1)

        # Check exemptions
        for pattern in EXEMPT_PATTERNS:
            if re.match(pattern, path):
                return await call_next(request)

        # Look up community and subscription
        try:
            community = await self.db.communities.find_one({'slug': slug}, {'_id': 0, 'community_id': 1})
            if not community:
                return await call_next(request)  # Let route handle 404

            sub = await self.db.subscriptions.find_one(
                {'community_id': community['community_id']},
                {'_id': 0, 'status': 1, 'trial_end_date': 1, 'trial_threshold_type': 1, 'trial_member_limit': 1, 'billing_end_date': 1},
            )

            # No subscription = unrestricted (subscription system is opt-in)
            if not sub:
                return await call_next(request)

            status = sub.get('status')

            # Explicitly blocked statuses
            if status in ('canceled', 'expired'):
                return self._block_response(f"Community subscription is {status}. Please renew to continue.")

            if status == 'pending_payment':
                return self._block_response("Community subscription is pending payment.")

            # Trial expiry check
            if status == 'trial':
                trial_end = sub.get('trial_end_date')
                if trial_end:
                    end_dt = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > end_dt:
                        # Auto-expire
                        await self.db.subscriptions.update_one(
                            {'community_id': community['community_id'], 'status': 'trial'},
                            {'$set': {'status': 'expired', 'updated_at': datetime.now(timezone.utc).isoformat()}},
                        )
                        return self._block_response("Trial period has expired. Please subscribe to continue.")

                # Member count check
                if sub.get('trial_threshold_type') in ('member_count', 'both') and sub.get('trial_member_limit'):
                    member_count = await self.db.community_memberships.count_documents({
                        'community_id': community['community_id'], 'is_active': True,
                    })
                    if member_count >= sub['trial_member_limit']:
                        return self._block_response(f"Trial member limit ({sub['trial_member_limit']}) reached. Please subscribe to add more members.")

            # Active billing expiry check
            if status == 'active':
                billing_end = sub.get('billing_end_date')
                if billing_end:
                    end_dt = datetime.fromisoformat(billing_end.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > end_dt:
                        await self.db.subscriptions.update_one(
                            {'community_id': community['community_id'], 'status': 'active'},
                            {'$set': {'status': 'expired', 'updated_at': datetime.now(timezone.utc).isoformat()}},
                        )
                        return self._block_response("Subscription has expired. Please renew.")

        except Exception:
            logger.exception("Subscription enforcement error for %s", path)
            # Fail open - don't block on middleware errors

        return await call_next(request)

    def _block_response(self, message: str):
        from starlette.responses import JSONResponse
        return JSONResponse(status_code=402, content={"detail": message})


# ── Branding validation helpers ──

BRANDING_LIMITS = {
    'logo_max_bytes': 200 * 1024,       # 200KB
    'cover_max_bytes': 1024 * 1024,      # 1MB
    'accent_color_pattern': r'^#[0-9a-fA-F]{6}$',
    'name_max_length': 100,
    'intro_copy_max_length': 200,
    'welcome_text_max_length': 1000,
}


def validate_branding(field: str, value) -> bool:
    """Validate a branding field against governance limits."""
    if field == 'accent_color' and value:
        if not re.match(BRANDING_LIMITS['accent_color_pattern'], value):
            raise ValueError("Accent color must be a valid hex color (e.g., #FF5500)")
    if field == 'name' and value:
        if len(value) > BRANDING_LIMITS['name_max_length']:
            raise ValueError(f"Name must be <= {BRANDING_LIMITS['name_max_length']} chars")
    if field == 'intro_copy' and value:
        if len(value) > BRANDING_LIMITS['intro_copy_max_length']:
            raise ValueError(f"Intro copy must be <= {BRANDING_LIMITS['intro_copy_max_length']} chars")
    if field == 'welcome_text' and value:
        if len(value) > BRANDING_LIMITS['welcome_text_max_length']:
            raise ValueError(f"Welcome text must be <= {BRANDING_LIMITS['welcome_text_max_length']} chars")
    return True


# ── Media cleanup utility ──

async def cleanup_orphaned_media(db):
    """Find and remove media files without matching events. Run as maintenance task."""
    import os
    from pathlib import Path
    media_root = Path("/app/media/events")
    if not media_root.exists():
        return {'cleaned': 0}

    cleaned = 0
    for comm_dir in media_root.iterdir():
        if not comm_dir.is_dir():
            continue
        comm_id = comm_dir.name
        for event_dir in comm_dir.iterdir():
            if not event_dir.is_dir():
                continue
            event_id = event_dir.name
            event = await db.events.find_one({'event_id': event_id})
            if not event:
                import shutil
                shutil.rmtree(event_dir)
                cleaned += 1
                logger.info("Cleaned orphaned media dir: %s", event_dir)

    return {'cleaned': cleaned}
