from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from discussion_models import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ThreadResponse, PendingContentResponse, ModerationAction
)
from models import User
from auth import get_current_user
from notification_engine import notify
from permissions import get_user_role_in_community, check_permission


def create_discussion_moderation_router(db):
    """Create discussion moderation router for managers/moderators"""
    router = APIRouter(prefix="/manager/communities/{slug}", tags=["discussion-moderation"])
    
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)
    
    async def require_moderator(current_user: User, community_id: str):
        """Require moderator or manager role"""
        if current_user.is_super_admin:
            return True
        
        role = await get_user_role_in_community(db, current_user.user_id, community_id)
        if role not in ['community_manager', 'moderator']:
            raise HTTPException(
                status_code=403,
                detail="Moderator or manager access required"
            )
        return True

    # ============ CATEGORY MANAGEMENT ============
    
    @router.post("/categories", response_model=CategoryResponse)
    async def create_category(
        slug: str,
        category_data: CategoryCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Create discussion category (manager only)"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check permission
        has_permission = await check_permission(
            db, current_user, community['community_id'], 'content.manage'
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        from discussion_models import DiscussionCategory
        category = DiscussionCategory(
            community_id=community['community_id'],
            name=category_data.name,
            description=category_data.description,
            display_order=category_data.display_order or 0
        )
        
        category_doc = category.model_dump()
        category_doc['created_at'] = category_doc['created_at'].isoformat()
        category_doc['updated_at'] = category_doc['updated_at'].isoformat()
        
        await db.discussion_categories.insert_one(category_doc)
        
        if isinstance(category_doc['created_at'], str):
            category_doc['created_at'] = datetime.fromisoformat(category_doc['created_at'])
        
        return CategoryResponse(**category_doc, thread_count=0)
    
    @router.post("/threads/{thread_id}/approve")
    async def approve_thread(
        slug: str,
        thread_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Approve pending thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_moderator(current_user, community['community_id'])
        
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        if thread['status'] != 'pending':
            raise HTTPException(status_code=400, detail=f"Thread is {thread['status']}")
        
        await db.discussion_threads.update_one(
            {'thread_id': thread_id},
            {'$set': {'status': 'published', 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        
        # Notify thread author
        await notify(db, 'post_approved', community['community_id'], {
            'community_name': community['name'],
            'thread_title': thread['title'],
        }, recipient_user_ids=[thread['author_id']])
        
        return {"message": "Thread approved successfully"}

    @router.post("/threads/{thread_id}/reject")
    async def reject_thread(
        slug: str,
        thread_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Reject pending thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_moderator(current_user, community['community_id'])
        
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        if thread['status'] != 'pending':
            raise HTTPException(status_code=400, detail=f"Thread is {thread['status']}")
        
        await db.discussion_threads.update_one(
            {'thread_id': thread_id},
            {'$set': {'status': 'rejected', 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        
        # Notify thread author
        await notify(db, 'post_rejected', community['community_id'], {
            'community_name': community['name'],
            'thread_title': thread['title'],
        }, recipient_user_ids=[thread['author_id']])
        
        return {"message": "Thread rejected successfully"}

    return router
