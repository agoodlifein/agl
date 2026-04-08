"""Governance and Platform Control API routes.

Super admin: run media cleanup, view branding limits, check system integrity.
"""

from fastapi import APIRouter, Depends, HTTPException, Cookie, Header
from typing import Annotated

from auth import get_current_user
from models import User
from governance import (
    BRANDING_LIMITS, cleanup_orphaned_media,
)


def create_governance_router(db):
    router = APIRouter(prefix="/admin/governance", tags=["governance"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    async def require_admin(user: User):
        if not user.is_super_admin:
            raise HTTPException(403, "Super admin access required")

    @router.get("/branding-limits")
    async def get_branding_limits(current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        return BRANDING_LIMITS

    @router.post("/cleanup-media")
    async def run_media_cleanup(current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)
        result = await cleanup_orphaned_media(db)
        return {"message": "Media cleanup complete", **result}

    @router.get("/system-check")
    async def system_integrity_check(current_user: User = Depends(get_user_dep)):
        await require_admin(current_user)

        # Count all collections
        checks = {}
        for col in ['users', 'communities', 'community_memberships', 'discussion_threads',
                     'posts', 'events', 'event_media', 'notification_templates',
                     'notification_logs', 'seo_metadata', 'plans', 'subscriptions']:
            checks[col] = await db[col].count_documents({})

        # Check for orphaned memberships (community doesn't exist)
        comm_ids = [c['community_id'] async for c in db.communities.find({}, {'_id': 0, 'community_id': 1})]
        orphaned_memberships = await db.community_memberships.count_documents({
            'community_id': {'$nin': comm_ids}
        }) if comm_ids else 0

        # Check for expired trials not yet marked
        from datetime import datetime, timezone
        expired_trials = await db.subscriptions.count_documents({
            'status': 'trial',
            'trial_end_date': {'$lt': datetime.now(timezone.utc).isoformat()},
        })

        # Check for subscriptions past billing end
        expired_billing = await db.subscriptions.count_documents({
            'status': 'active',
            'billing_end_date': {'$lt': datetime.now(timezone.utc).isoformat()},
        })

        return {
            'collections': checks,
            'issues': {
                'orphaned_memberships': orphaned_memberships,
                'expired_trials_not_marked': expired_trials,
                'expired_billing_not_marked': expired_billing,
            },
            'status': 'healthy' if (orphaned_memberships == 0 and expired_trials == 0 and expired_billing == 0) else 'needs_attention',
        }

    return router
