from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from models import (
    Community, CommunityCreate, CommunityUpdate, CommunityResponse,
    User, UserResponse
)
from auth import get_current_user, require_super_admin
from permissions import get_user_communities, check_permission


def create_community_router(db):
    """Create community router with database dependency"""
    router = APIRouter(prefix="/communities", tags=["communities"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.post("/", response_model=CommunityResponse)
    async def create_community(
        community_data: CommunityCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Create new community - ONLY super admin"""
        # Only super admin can create communities
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=403,
                detail="Only super admin can create communities"
            )
        
        # Check slug uniqueness
        existing = await db.communities.find_one(
            {'slug': community_data.slug},
            {'_id': 0}
        )
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Community slug already exists"
            )
        
        # Create community
        community = Community(
            name=community_data.name,
            slug=community_data.slug,
            description=community_data.description,
            created_by=current_user.user_id,
            logo=community_data.logo,
            cover_image=community_data.cover_image,
            intro_copy=community_data.intro_copy,
            welcome_text=community_data.welcome_text,
            accent_color=community_data.accent_color,
            section_headings=community_data.section_headings or {},
            cta_text=community_data.cta_text,
            status='active'
        )
        
        community_doc = community.model_dump()
        community_doc['created_at'] = community_doc['created_at'].isoformat()
        community_doc['updated_at'] = community_doc['updated_at'].isoformat()
        
        await db.communities.insert_one(community_doc)
        
        # If community_manager_id provided, assign them
        if community_data.community_manager_id:
            from models import CommunityMembership
            
            # Verify user exists
            user_exists = await db.users.find_one(
                {'user_id': community_data.community_manager_id},
                {'_id': 0}
            )
            
            if not user_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Community manager user not found"
                )
            
            membership = CommunityMembership(
                user_id=community_data.community_manager_id,
                community_id=community.community_id,
                role_name='community_manager'
            )
            
            membership_doc = membership.model_dump()
            membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
            
            await db.community_memberships.insert_one(membership_doc)
        
        return CommunityResponse(**community.model_dump())

    @router.get("/", response_model=List[CommunityResponse])
    async def list_communities(
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """List all active communities"""
        communities = await db.communities.find(
            {'is_active': True},
            {'_id': 0}
        ).to_list(1000)
        
        # Convert datetime strings
        for comm in communities:
            if isinstance(comm.get('created_at'), str):
                comm['created_at'] = datetime.fromisoformat(comm['created_at'])
            if isinstance(comm.get('updated_at'), str):
                comm['updated_at'] = datetime.fromisoformat(comm['updated_at'])
        
        return [CommunityResponse(**c) for c in communities]

    @router.get("/my-communities")
    async def get_my_communities(
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get all communities current user is member of"""
        communities = await get_user_communities(db, current_user.user_id)
        
        # Convert datetime strings
        for item in communities:
            comm = item['community']
            if isinstance(comm.get('created_at'), str):
                comm['created_at'] = datetime.fromisoformat(comm['created_at'])
            if isinstance(comm.get('updated_at'), str):
                comm['updated_at'] = datetime.fromisoformat(comm['updated_at'])
            
            if isinstance(item.get('joined_at'), str):
                item['joined_at'] = datetime.fromisoformat(item['joined_at'])
        
        return communities

    @router.get("/{slug}", response_model=CommunityResponse)
    async def get_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get community by slug"""
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Convert datetime strings
        if isinstance(community.get('created_at'), str):
            community['created_at'] = datetime.fromisoformat(community['created_at'])
        if isinstance(community.get('updated_at'), str):
            community['updated_at'] = datetime.fromisoformat(community['updated_at'])
        
        return CommunityResponse(**community)

    @router.patch("/{slug}", response_model=CommunityResponse)
    async def update_community(
        slug: str,
        update_data: CommunityUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update community - super admin or community manager"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        has_permission = await check_permission(
            db,
            current_user,
            community['community_id'],
            'community.update'
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="Permission denied: community.update required"
            )
        
        # Update community
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.communities.update_one(
            {'slug': slug},
            {'$set': update_dict}
        )
        
        # Get updated community
        updated = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        # Convert datetime strings
        if isinstance(updated.get('created_at'), str):
            updated['created_at'] = datetime.fromisoformat(updated['created_at'])
        if isinstance(updated.get('updated_at'), str):
            updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
        
        return CommunityResponse(**updated)

    @router.delete("/{slug}")
    async def delete_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Delete community - ONLY super admin"""
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=403,
                detail="Only super admin can delete communities"
            )
        
        # Soft delete - set is_active to False
        result = await db.communities.update_one(
            {'slug': slug},
            {'$set': {'is_active': False, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Community not found")
        
        return {"message": "Community deleted successfully"}

    return router
