from fastapi import APIRouter, HTTPException, Depends, Cookie, Header, UploadFile, File
from typing import Annotated, List
from datetime import datetime, timezone
import base64
import io

from models import (
    User, CommunityManagerUpdate, CommunityResponse
)
from auth import get_current_user
from permissions import get_user_role_in_community


def create_manager_router(db):
    """Create community manager router with database dependency"""
    router = APIRouter(prefix="/manager", tags=["manager"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)
    
    async def require_community_manager(
        current_user: User,
        community_id: str
    ):
        """Ensure user is a manager of the specific community"""
        # Super admin can manage all communities
        if current_user.is_super_admin:
            return True
        
        role = await get_user_role_in_community(db, current_user.user_id, community_id)
        
        if role != 'community_manager':
            raise HTTPException(
                status_code=403,
                detail="Community manager access required for this community"
            )
        return True

    @router.get("/my-communities", response_model=List[CommunityResponse])
    async def get_managed_communities(
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get all communities managed by current user"""
        # Get all communities where user is a manager
        memberships = await db.community_memberships.find(
            {
                'user_id': current_user.user_id,
                'role_name': 'community_manager',
                'is_active': True
            },
            {'_id': 0}
        ).to_list(1000)
        
        # Get community details
        communities = []
        for membership in memberships:
            community = await db.communities.find_one(
                {'community_id': membership['community_id']},
                {'_id': 0}
            )
            
            if community:
                # Convert datetime strings
                if isinstance(community.get('created_at'), str):
                    community['created_at'] = datetime.fromisoformat(community['created_at'])
                if isinstance(community.get('updated_at'), str):
                    community['updated_at'] = datetime.fromisoformat(community['updated_at'])
                
                communities.append(CommunityResponse(**community))
        
        return communities

    @router.get("/communities/{slug}", response_model=CommunityResponse)
    async def get_managed_community(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get specific community details (must be manager)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Convert datetime strings
        if isinstance(community.get('created_at'), str):
            community['created_at'] = datetime.fromisoformat(community['created_at'])
        if isinstance(community.get('updated_at'), str):
            community['updated_at'] = datetime.fromisoformat(community['updated_at'])
        
        return CommunityResponse(**community)

    @router.patch("/communities/{slug}", response_model=CommunityResponse)
    async def update_managed_community(
        slug: str,
        update_data: CommunityManagerUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update community (manager can only update allowed fields)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Build update dict with only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )
        
        # Add updated timestamp
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update community
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

    @router.post("/communities/{slug}/upload-logo")
    async def upload_community_logo(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)],
        logo: UploadFile = File(...)
    ):
        """Upload community logo with validation (JPG/PNG, max 200KB)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if logo.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only JPG and PNG files are allowed. Got: {logo.content_type}"
            )
        
        # Read file content
        content = await logo.read()
        file_size = len(content)
        
        # Validate file size (200KB = 204800 bytes)
        max_size = 200 * 1024  # 200KB in bytes
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum of 200KB. Your file: {file_size / 1024:.1f}KB"
            )
        
        # Convert to base64 data URI for storage
        file_extension = logo.content_type.split('/')[-1]
        base64_data = base64.b64encode(content).decode('utf-8')
        data_uri = f"data:{logo.content_type};base64,{base64_data}"
        
        # Update community logo
        await db.communities.update_one(
            {'slug': slug},
            {
                '$set': {
                    'logo': data_uri,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Logo uploaded successfully",
            "filename": logo.filename,
            "size": f"{file_size / 1024:.1f}KB",
            "type": logo.content_type
        }

    return router
