from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from discussion_models import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ThreadCreate, ThreadUpdate, ThreadResponse,
    PostCreate, PostUpdate, PostResponse,
    PendingContentResponse, ModerationAction
)
from models import User
from auth import get_current_user
from notification_engine import notify
from permissions import get_user_role_in_community, check_permission


def create_discussion_router(db):
    """Create discussion router for public discussion access"""
    router = APIRouter(prefix="/communities/{slug}", tags=["discussions"])
    
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    async def get_optional_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        try:
            return await get_current_user(db, session_token, authorization)
        except Exception:
            return None

    # ============ CATEGORIES ============
    
    @router.get("/categories", response_model=List[CategoryResponse])
    async def list_categories(
        slug: str,
        current_user=Depends(get_optional_user_dep)
    ):
        """List all active categories in community (public)"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        categories = await db.discussion_categories.find(
            {'community_id': community['community_id'], 'is_active': True},
            {'_id': 0}
        ).sort('display_order', 1).to_list(100)
        
        result = []
        for cat in categories:
            if isinstance(cat.get('created_at'), str):
                cat['created_at'] = datetime.fromisoformat(cat['created_at'])
            
            thread_count = await db.discussion_threads.count_documents({
                'category_id': cat['category_id'],
                'status': 'published'
            })
            
            result.append(CategoryResponse(**cat, thread_count=thread_count))
        
        return result

    # ============ THREADS ============
    
    @router.post("/threads", response_model=ThreadResponse)
    async def create_thread(
        slug: str,
        thread_data: ThreadCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Create discussion thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is member
        has_permission = await check_permission(
            db, current_user, community['community_id'], 'content.create'
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Verify category exists
        category = await db.discussion_categories.find_one(
            {'category_id': thread_data.category_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check if moderation required
        require_approval = community.get('settings', {}).get('require_post_approval', False)
        status = 'pending' if require_approval else 'published'
        
        from discussion_models import DiscussionThread
        thread = DiscussionThread(
            category_id=thread_data.category_id,
            community_id=community['community_id'],
            author_id=current_user.user_id,
            title=thread_data.title,
            content=thread_data.content,
            status=status
        )
        
        thread_doc = thread.model_dump()
        for field in ['created_at', 'updated_at', 'last_activity_at']:
            thread_doc[field] = thread_doc[field].isoformat()
        
        await db.discussion_threads.insert_one(thread_doc)
        
        if isinstance(thread_doc['created_at'], str):
            thread_doc['created_at'] = datetime.fromisoformat(thread_doc['created_at'])
        if isinstance(thread_doc['updated_at'], str):
            thread_doc['updated_at'] = datetime.fromisoformat(thread_doc['updated_at'])
        if isinstance(thread_doc['last_activity_at'], str):
            thread_doc['last_activity_at'] = datetime.fromisoformat(thread_doc['last_activity_at'])
        
        return ThreadResponse(**thread_doc, author_name=current_user.name, reply_count=0)

    @router.get("/threads", response_model=List[ThreadResponse])
    async def list_threads(
        slug: str,
        current_user=Depends(get_optional_user_dep),
        category_id: str = None,
        skip: int = 0,
        limit: int = 50
    ):
        """List threads in community or category (public)"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        query = {
            'community_id': community['community_id'],
            'status': 'published'
        }
        if category_id:
            query['category_id'] = category_id
        
        threads = await db.discussion_threads.find(
            query,
            {'_id': 0}
        ).sort([('is_pinned', -1), ('last_activity_at', -1)]).skip(skip).limit(limit).to_list(limit)
        
        result = []
        for thread in threads:
            user = await db.users.find_one({'user_id': thread['author_id']}, {'_id': 0})
            
            for field in ['created_at', 'updated_at', 'last_activity_at']:
                if isinstance(thread.get(field), str):
                    thread[field] = datetime.fromisoformat(thread[field])
            
            reply_count = await db.posts.count_documents({
                'thread_id': thread['thread_id'],
                'status': 'published'
            })
            
            result.append(ThreadResponse(
                **thread,
                author_name=user['name'] if user else 'Unknown',
                reply_count=reply_count
            ))
        
        return result

    @router.get("/threads/{thread_id}", response_model=ThreadResponse)
    async def get_thread(
        slug: str,
        thread_id: str,
        current_user=Depends(get_optional_user_dep)
    ):
        """Get thread details (public)"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Increment view count
        await db.discussion_threads.update_one(
            {'thread_id': thread_id},
            {'$inc': {'view_count': 1}}
        )
        thread['view_count'] = thread.get('view_count', 0) + 1
        
        user = await db.users.find_one({'user_id': thread['author_id']}, {'_id': 0})
        
        for field in ['created_at', 'updated_at', 'last_activity_at']:
            if isinstance(thread.get(field), str):
                thread[field] = datetime.fromisoformat(thread[field])
        
        reply_count = await db.posts.count_documents({
            'thread_id': thread_id,
            'status': 'published'
        })
        
        return ThreadResponse(
            **thread,
            author_name=user['name'] if user else 'Unknown',
            reply_count=reply_count
        )

    @router.patch("/threads/{thread_id}", response_model=ThreadResponse)
    async def update_thread(
        slug: str,
        thread_id: str,
        update_data: ThreadUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update own thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Only author can update (unless moderator)
        if thread['author_id'] != current_user.user_id:
            can_moderate = await check_permission(
                db, current_user, community['community_id'], 'content.moderate'
            )
            if not can_moderate:
                raise HTTPException(status_code=403, detail="You can only edit your own threads")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.discussion_threads.update_one(
            {'thread_id': thread_id},
            {'$set': update_dict}
        )
        
        updated = await db.discussion_threads.find_one({'thread_id': thread_id}, {'_id': 0})
        user = await db.users.find_one({'user_id': updated['author_id']}, {'_id': 0})
        
        for field in ['created_at', 'updated_at', 'last_activity_at']:
            if isinstance(updated.get(field), str):
                updated[field] = datetime.fromisoformat(updated[field])
        
        reply_count = await db.posts.count_documents({
            'thread_id': thread_id,
            'status': 'published'
        })
        
        return ThreadResponse(
            **updated,
            author_name=user['name'] if user else 'Unknown',
            reply_count=reply_count
        )

    @router.delete("/threads/{thread_id}")
    async def delete_thread(
        slug: str,
        thread_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Delete own thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Only author can delete (unless moderator)
        if thread['author_id'] != current_user.user_id:
            can_moderate = await check_permission(
                db, current_user, community['community_id'], 'content.moderate'
            )
            if not can_moderate:
                raise HTTPException(status_code=403, detail="You can only delete your own threads")
        
        await db.discussion_threads.delete_one({'thread_id': thread_id})
        await db.posts.delete_many({'thread_id': thread_id})
        
        return {"message": "Thread deleted successfully"}

    # ============ POSTS/REPLIES ============
    
    @router.post("/threads/{thread_id}/posts", response_model=PostResponse)
    async def create_post(
        slug: str,
        thread_id: str,
        post_data: PostCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Create post/reply in thread"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is member
        has_permission = await check_permission(
            db, current_user, community['community_id'], 'content.create'
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Verify thread exists and not locked
        thread = await db.discussion_threads.find_one(
            {'thread_id': thread_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        if thread.get('is_locked'):
            can_moderate = await check_permission(
                db, current_user, community['community_id'], 'content.moderate'
            )
            if not can_moderate:
                raise HTTPException(status_code=403, detail="Thread is locked")
        
        # Check if moderation required
        require_approval = community.get('settings', {}).get('require_post_approval', False)
        status = 'pending' if require_approval else 'published'
        
        from discussion_models import Post
        post = Post(
            thread_id=thread_id,
            community_id=community['community_id'],
            author_id=current_user.user_id,
            content=post_data.content,
            parent_post_id=post_data.parent_post_id,
            status=status
        )
        
        post_doc = post.model_dump()
        for field in ['created_at', 'updated_at']:
            if post_doc.get(field):
                post_doc[field] = post_doc[field].isoformat()
        if post_doc.get('edited_at'):
            post_doc['edited_at'] = post_doc['edited_at'].isoformat()
        
        await db.posts.insert_one(post_doc)
        
        # Update thread activity
        await db.discussion_threads.update_one(
            {'thread_id': thread_id},
            {'$set': {'last_activity_at': datetime.now(timezone.utc).isoformat()}}
        )
        
        # Notify thread author about the reply (if replier is not the author)
        if thread['author_id'] != current_user.user_id:
            await notify(db, 'discussion_reply', community['community_id'], {
                'community_name': community['name'],
                'thread_title': thread['title'],
                'reply_author': current_user.name,
                'reply_preview': post_data.content[:100],
            }, recipient_user_ids=[thread['author_id']])
        
        for field in ['created_at', 'updated_at']:
            if isinstance(post_doc.get(field), str):
                post_doc[field] = datetime.fromisoformat(post_doc[field])
        if post_doc.get('edited_at') and isinstance(post_doc['edited_at'], str):
            post_doc['edited_at'] = datetime.fromisoformat(post_doc['edited_at'])
        
        return PostResponse(**post_doc, author_name=current_user.name)

    @router.get("/threads/{thread_id}/posts", response_model=List[PostResponse])
    async def list_posts(
        slug: str,
        thread_id: str,
        current_user=Depends(get_optional_user_dep),
        skip: int = 0,
        limit: int = 100
    ):
        """List posts in thread (public)"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        posts = await db.posts.find(
            {
                'thread_id': thread_id,
                'community_id': community['community_id'],
                'status': 'published'
            },
            {'_id': 0}
        ).sort('created_at', 1).skip(skip).limit(limit).to_list(limit)
        
        result = []
        for post in posts:
            user = await db.users.find_one({'user_id': post['author_id']}, {'_id': 0})
            
            for field in ['created_at', 'updated_at']:
                if isinstance(post.get(field), str):
                    post[field] = datetime.fromisoformat(post[field])
            if post.get('edited_at') and isinstance(post['edited_at'], str):
                post['edited_at'] = datetime.fromisoformat(post['edited_at'])
            
            result.append(PostResponse(
                **post,
                author_name=user['name'] if user else 'Unknown'
            ))
        
        return result

    @router.patch("/threads/{thread_id}/posts/{post_id}", response_model=PostResponse)
    async def update_post(
        slug: str,
        thread_id: str,
        post_id: str,
        update_data: PostUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update own post"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        post = await db.posts.find_one(
            {
                'post_id': post_id,
                'thread_id': thread_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Only author can update (unless moderator)
        if post['author_id'] != current_user.user_id:
            can_moderate = await check_permission(
                db, current_user, community['community_id'], 'content.moderate'
            )
            if not can_moderate:
                raise HTTPException(status_code=403, detail="You can only edit your own posts")
        
        await db.posts.update_one(
            {'post_id': post_id},
            {
                '$set': {
                    'content': update_data.content,
                    'is_edited': True,
                    'edited_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        updated = await db.posts.find_one({'post_id': post_id}, {'_id': 0})
        
        for field in ['created_at', 'updated_at']:
            if isinstance(updated.get(field), str):
                updated[field] = datetime.fromisoformat(updated[field])
        if updated.get('edited_at') and isinstance(updated['edited_at'], str):
            updated['edited_at'] = datetime.fromisoformat(updated['edited_at'])
        
        return PostResponse(**updated, author_name=current_user.name)

    @router.delete("/threads/{thread_id}/posts/{post_id}")
    async def delete_post(
        slug: str,
        thread_id: str,
        post_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Delete own post"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        post = await db.posts.find_one(
            {
                'post_id': post_id,
                'thread_id': thread_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Only author can delete (unless moderator)
        if post['author_id'] != current_user.user_id:
            can_moderate = await check_permission(
                db, current_user, community['community_id'], 'content.moderate'
            )
            if not can_moderate:
                raise HTTPException(status_code=403, detail="You can only delete your own posts")
        
        await db.posts.delete_one({'post_id': post_id})
        
        return {"message": "Post deleted successfully"}

    return router
