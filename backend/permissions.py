from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from models import User


# ============ PERMISSION DEFINITIONS ============

# Permissions by role
ROLE_PERMISSIONS = {
    'super_admin': [
        'platform.manage',
        'community.create',
        'community.delete',
        'community.update',
        'community.read',
        'member.manage',
        'member.create',
        'member.delete',
        'role.assign',
    ],
    'community_manager': [
        'community.update',
        'community.read',
        'member.manage',
        'member.create',
        'member.delete',
        'role.assign',
        'content.manage',
        'content.create',
        'content.delete',
    ],
    'moderator': [
        'community.read',
        'member.read',
        'content.moderate',
        'content.create',
        'content.update',
    ],
    'member': [
        'community.read',
        'member.read',
        'content.create',
        'content.update.own',
    ]
}


# ============ PERMISSION CHECKING ============

async def get_user_role_in_community(
    db: AsyncIOMotorDatabase,
    user_id: str,
    community_id: str
) -> Optional[str]:
    """Get user's role in a specific community"""
    membership = await db.community_memberships.find_one(
        {
            'user_id': user_id,
            'community_id': community_id,
            'is_active': True
        },
        {'_id': 0}
    )
    
    if membership:
        return membership['role_name']
    return None


async def check_permission(
    db: AsyncIOMotorDatabase,
    user: User,
    community_id: str,
    required_permission: str
) -> bool:
    """Check if user has permission in community
    
    Args:
        db: Database connection
        user: Current user
        community_id: Community ID to check permission in
        required_permission: Permission name (e.g., 'content.create')
    
    Returns:
        True if user has permission, False otherwise
    """
    # Super admin has all permissions
    if user.is_super_admin:
        return True
    
    # Get user's role in this community
    role_name = await get_user_role_in_community(db, user.user_id, community_id)
    
    if not role_name:
        return False
    
    # Check if role has required permission
    role_perms = ROLE_PERMISSIONS.get(role_name, [])
    return required_permission in role_perms


async def require_permission(
    db: AsyncIOMotorDatabase,
    user: User,
    community_id: str,
    required_permission: str
):
    """Require user to have permission in community (raises exception if not)"""
    has_permission = await check_permission(db, user, community_id, required_permission)
    
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {required_permission} required"
        )


async def require_community_role(
    db: AsyncIOMotorDatabase,
    user: User,
    community_id: str,
    required_roles: list[str]
):
    """Require user to have one of the specified roles in community"""
    # Super admin bypasses role checks
    if user.is_super_admin:
        return
    
    role_name = await get_user_role_in_community(db, user.user_id, community_id)
    
    if role_name not in required_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role required: one of {required_roles}"
        )


async def get_user_communities(
    db: AsyncIOMotorDatabase,
    user_id: str
) -> list:
    """Get all communities user is member of with their roles"""
    memberships = await db.community_memberships.find(
        {'user_id': user_id, 'is_active': True},
        {'_id': 0}
    ).to_list(1000)
    
    # Enrich with community details
    result = []
    for membership in memberships:
        community = await db.communities.find_one(
            {'community_id': membership['community_id']},
            {'_id': 0}
        )
        if community:
            result.append({
                'community': community,
                'role': membership['role_name'],
                'joined_at': membership['joined_at']
            })
    
    return result
