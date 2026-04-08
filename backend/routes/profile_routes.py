from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from models import User, ProfileUpdate, ProfileResponse
from auth import get_current_user


def create_profile_router(db):
    """Create profile router with database dependency"""
    router = APIRouter(prefix="/profile", tags=["profile"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.get("/", response_model=ProfileResponse)
    async def get_my_profile(
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get current user's profile"""
        return ProfileResponse(**current_user.model_dump())

    @router.patch("/", response_model=ProfileResponse)
    async def update_my_profile(
        profile_data: ProfileUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update current user's profile"""
        # Build update dict with only provided fields
        update_dict = profile_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )
        
        # Add updated timestamp
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update user in database
        await db.users.update_one(
            {'user_id': current_user.user_id},
            {'$set': update_dict}
        )
        
        # Get updated user
        updated_user = await db.users.find_one(
            {'user_id': current_user.user_id},
            {'_id': 0}
        )
        
        # Convert datetime strings
        if isinstance(updated_user.get('created_at'), str):
            updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
        if isinstance(updated_user.get('updated_at'), str):
            updated_user['updated_at'] = datetime.fromisoformat(updated_user['updated_at'])
        
        return ProfileResponse(**updated_user)

    return router


def create_profiles_router(db):
    """Create profiles router for super admin with database dependency"""
    router = APIRouter(prefix="/profiles", tags=["profiles"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.get("/", response_model=List[ProfileResponse])
    async def list_all_profiles(
        current_user: Annotated[User, Depends(get_user_dep)],
        skip: int = 0,
        limit: int = 100
    ):
        """List all user profiles - SUPER ADMIN ONLY"""
        # Only super admin can list all profiles
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=403,
                detail="Super admin access required"
            )
        
        # Get users with pagination
        users = await db.users.find(
            {},
            {'_id': 0, 'password_hash': 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        # Convert datetime strings
        for user in users:
            if isinstance(user.get('created_at'), str):
                user['created_at'] = datetime.fromisoformat(user['created_at'])
            if isinstance(user.get('updated_at'), str):
                user['updated_at'] = datetime.fromisoformat(user['updated_at'])
        
        return [ProfileResponse(**user) for user in users]

    @router.get("/{user_id}", response_model=ProfileResponse)
    async def get_user_profile(
        user_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get specific user profile - SUPER ADMIN ONLY"""
        # Only super admin can view other user profiles
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=403,
                detail="Super admin access required"
            )
        
        # Get user
        user = await db.users.find_one(
            {'user_id': user_id},
            {'_id': 0, 'password_hash': 0}
        )
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Convert datetime strings
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if isinstance(user.get('updated_at'), str):
            user['updated_at'] = datetime.fromisoformat(user['updated_at'])
        
        return ProfileResponse(**user)

    return router
