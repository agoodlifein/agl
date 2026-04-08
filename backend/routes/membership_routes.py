from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime

from models import (
    CommunityMembership, MembershipCreate, MembershipUpdate,
    MembershipResponse, User
)
from auth import get_current_user
from permissions import check_permission, require_permission


def create_membership_router(db):
    """Create membership router with database dependency"""
    router = APIRouter(prefix="/community/{slug}", tags=["memberships"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.post("/members", response_model=MembershipResponse)
    async def add_member(
        slug: str,
        membership_data: MembershipCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Add member to community - requires member.create permission"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        await require_permission(
            db,
            current_user,
            community['community_id'],
            'member.create'
        )
        
        # Verify user exists
        user = await db.users.find_one(
            {'user_id': membership_data.user_id},
            {'_id': 0}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if membership already exists
        existing = await db.community_memberships.find_one(
            {
                'user_id': membership_data.user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this community"
            )
        
        # Create membership
        membership = CommunityMembership(
            user_id=membership_data.user_id,
            community_id=community['community_id'],
            role_name=membership_data.role_name
        )
        
        membership_doc = membership.model_dump()
        membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
        
        await db.community_memberships.insert_one(membership_doc)
        
        # Build response with user details
        if isinstance(membership_doc['joined_at'], str):
            membership_doc['joined_at'] = datetime.fromisoformat(membership_doc['joined_at'])
        
        return MembershipResponse(
            **membership_doc,
            user_name=user['name'],
            user_email=user['email']
        )

    @router.get("/members", response_model=List[MembershipResponse])
    async def list_members(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """List all members of community"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        await require_permission(
            db,
            current_user,
            community['community_id'],
            'member.read'
        )
        
        # Get memberships
        memberships = await db.community_memberships.find(
            {'community_id': community['community_id'], 'is_active': True},
            {'_id': 0}
        ).to_list(1000)
        
        # Enrich with user details
        result = []
        for membership in memberships:
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

    @router.patch("/members/{user_id}/role", response_model=MembershipResponse)
    async def update_member_role(
        slug: str,
        user_id: str,
        update_data: MembershipUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update member role - requires role.assign permission"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        await require_permission(
            db,
            current_user,
            community['community_id'],
            'role.assign'
        )
        
        # Update membership
        result = await db.community_memberships.update_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'$set': {'role_name': update_data.role_name}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        # Get updated membership
        membership = await db.community_memberships.find_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        # Get user details
        user = await db.users.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if isinstance(membership['joined_at'], str):
            membership['joined_at'] = datetime.fromisoformat(membership['joined_at'])
        
        return MembershipResponse(
            **membership,
            user_name=user['name'],
            user_email=user['email']
        )

    @router.delete("/members/{user_id}")
    async def remove_member(
        slug: str,
        user_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Remove member from community - requires member.delete permission"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        await require_permission(
            db,
            current_user,
            community['community_id'],
            'member.delete'
        )
        
        # Soft delete - set is_active to False
        result = await db.community_memberships.update_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'$set': {'is_active': False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        return {"message": "Member removed successfully"}

    @router.post("/join", response_model=MembershipResponse)
    async def join_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Join community as member (self-join)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if already member
        existing = await db.community_memberships.find_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="You are already a member of this community"
            )
        
        # Create membership as 'member'
        membership = CommunityMembership(
            user_id=current_user.user_id,
            community_id=community['community_id'],
            role_name='member'
        )
        
        membership_doc = membership.model_dump()
        membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
        
        await db.community_memberships.insert_one(membership_doc)
        
        if isinstance(membership_doc['joined_at'], str):
            membership_doc['joined_at'] = datetime.fromisoformat(membership_doc['joined_at'])
        
        return MembershipResponse(
            **membership_doc,
            user_name=current_user.name,
            user_email=current_user.email
        )

    @router.post("/leave")
    async def leave_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Leave community (self-remove)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Remove membership
        result = await db.community_memberships.update_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id']
            },
            {'$set': {'is_active': False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="You are not a member of this community")
        
        return {"message": "Left community successfully"}

    return router
