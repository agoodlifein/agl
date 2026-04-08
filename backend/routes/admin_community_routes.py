from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from models import (
    User, CommunityStatusUpdate, ManagerAssignment,
    MembershipResponse
)
from auth import get_current_user


def create_admin_community_router(db):
    """Create admin community management router with database dependency"""
    router = APIRouter(prefix="/admin/communities", tags=["admin-communities"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)
    
    async def require_super_admin(current_user: User):
        """Ensure user is super admin"""
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=403,
                detail="Super admin access required"
            )
        return current_user

    @router.post("/{slug}/activate")
    async def activate_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Activate community - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Update status
        await db.communities.update_one(
            {'slug': slug},
            {
                '$set': {
                    'status': 'active',
                    'is_active': True,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Community activated successfully",
            "slug": slug,
            "status": "active"
        }

    @router.post("/{slug}/pause")
    async def pause_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Pause community - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Update status
        await db.communities.update_one(
            {'slug': slug},
            {
                '$set': {
                    'status': 'paused',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Community paused successfully",
            "slug": slug,
            "status": "paused"
        }

    @router.post("/{slug}/disable")
    async def disable_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Disable community - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Update status
        await db.communities.update_one(
            {'slug': slug},
            {
                '$set': {
                    'status': 'disabled',
                    'is_active': False,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Community disabled successfully",
            "slug": slug,
            "status": "disabled"
        }

    @router.post("/{slug}/assign-manager")
    async def assign_community_manager(
        slug: str,
        assignment: ManagerAssignment,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Assign community manager - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Verify user exists
        user = await db.users.find_one(
            {'user_id': assignment.user_id},
            {'_id': 0}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # If replace_existing, remove all current managers
        if assignment.replace_existing:
            await db.community_memberships.update_many(
                {
                    'community_id': community['community_id'],
                    'role_name': 'community_manager'
                },
                {'$set': {'role_name': 'member'}}
            )
        
        # Check if user is already a member
        existing_membership = await db.community_memberships.find_one(
            {
                'user_id': assignment.user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if existing_membership:
            # Update existing membership to manager role
            await db.community_memberships.update_one(
                {
                    'user_id': assignment.user_id,
                    'community_id': community['community_id']
                },
                {'$set': {'role_name': 'community_manager', 'is_active': True}}
            )
        else:
            # Create new membership as manager
            from models import CommunityMembership
            membership = CommunityMembership(
                user_id=assignment.user_id,
                community_id=community['community_id'],
                role_name='community_manager'
            )
            
            membership_doc = membership.model_dump()
            membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
            
            await db.community_memberships.insert_one(membership_doc)
        
        return {
            "message": "Community manager assigned successfully",
            "community": community['name'],
            "manager_id": assignment.user_id,
            "manager_name": user['name']
        }

    @router.delete("/{slug}/remove-manager/{user_id}")
    async def remove_community_manager(
        slug: str,
        user_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Remove community manager - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is a manager
        membership = await db.community_memberships.find_one(
            {
                'user_id': user_id,
                'community_id': community['community_id'],
                'role_name': 'community_manager'
            },
            {'_id': 0}
        )
        
        if not membership:
            raise HTTPException(
                status_code=404,
                detail="User is not a manager of this community"
            )
        
        # Downgrade to member (don't remove completely)
        await db.community_memberships.update_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'$set': {'role_name': 'member'}}
        )
        
        return {
            "message": "Community manager removed successfully",
            "community": community['name'],
            "user_id": user_id
        }

    @router.get("/{slug}/managers", response_model=List[MembershipResponse])
    async def get_community_managers(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get all managers of a community - SUPER ADMIN ONLY"""
        await require_super_admin(current_user)
        
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Get all managers
        managers = await db.community_memberships.find(
            {
                'community_id': community['community_id'],
                'role_name': 'community_manager',
                'is_active': True
            },
            {'_id': 0}
        ).to_list(100)
        
        # Enrich with user details
        result = []
        for membership in managers:
            user = await db.users.find_one(
                {'user_id': membership['user_id']},
                {'_id': 0}
            )
            
            if user:
                if isinstance(membership['joined_at'], str):
                    membership['joined_at'] = datetime.fromisoformat(membership['joined_at'])
                
                result.append(MembershipResponse(
                    **membership,
                    user_name=user['name'],
                    user_email=user['email']
                ))
        
        return result

    return router
