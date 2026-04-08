"""Community-scoped search routes.

GET /api/communities/{slug}/search?q=keyword&type=all|discussions|events|members&limit=20&skip=0
Results filtered by community_id and user permission level.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, Header
from typing import Annotated, Optional
from auth import get_current_user
from models import User
from search_models import SearchResultItem, SearchResponse, SEARCH_TYPES


def create_search_router(db):
    router = APIRouter(tags=["search"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    @router.get("/communities/{slug}/search", response_model=SearchResponse)
    async def search_community(
        slug: str,
        q: str = Query(..., min_length=2, max_length=200),
        type: str = Query('all'),
        limit: int = Query(20, ge=1, le=50),
        skip: int = Query(0, ge=0),
        current_user: User = Depends(get_user_dep),
    ):
        if type not in SEARCH_TYPES:
            raise HTTPException(400, f"type must be one of: {SEARCH_TYPES}")

        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(404, "Community not found")
        cid = community['community_id']

        # Check membership for permission level
        membership = await db.community_memberships.find_one(
            {'community_id': cid, 'user_id': current_user.user_id, 'is_active': True},
            {'_id': 0, 'role_name': 1},
        )
        is_admin = current_user.is_super_admin
        is_manager = is_admin or (membership and membership.get('role_name') == 'community_manager')
        is_member = is_admin or membership is not None

        if not is_member:
            raise HTTPException(403, "You must be a member of this community to search")

        # Check if member search is enabled for this community
        member_search_enabled = community.get('member_search_enabled', True)

        results = []
        search_filter = {'$regex': q, '$options': 'i'}

        # Search discussions
        if type in ('all', 'discussions'):
            thread_query = {
                'community_id': cid,
                '$or': [
                    {'title': search_filter},
                    {'content': search_filter},
                ],
            }
            # Non-managers only see published threads
            if not is_manager:
                thread_query['status'] = 'published'

            threads = await db.discussion_threads.find(
                thread_query, {'_id': 0}
            ).sort('created_at', -1).limit(limit).to_list(limit)

            for t in threads:
                content = t.get('content', '')
                snippet = _make_snippet(content, q)
                results.append(SearchResultItem(
                    result_type='discussion',
                    id=t['thread_id'],
                    title=t['title'],
                    snippet=snippet,
                    meta={
                        'author_name': t.get('author_name', ''),
                        'reply_count': t.get('reply_count', 0),
                        'category_id': t.get('category_id', ''),
                        'status': t.get('status', ''),
                    },
                    created_at=t.get('created_at', ''),
                ))

        # Search events
        if type in ('all', 'events'):
            event_query = {
                'community_id': cid,
                '$or': [
                    {'title': search_filter},
                    {'description': search_filter},
                    {'venue': search_filter},
                ],
            }
            if not is_manager:
                event_query['status'] = 'published'

            events = await db.events.find(
                event_query, {'_id': 0}
            ).sort('event_date', -1).limit(limit).to_list(limit)

            for e in events:
                desc = e.get('description', '')
                snippet = _make_snippet(desc, q)
                results.append(SearchResultItem(
                    result_type='event',
                    id=e['event_id'],
                    title=e['title'],
                    snippet=snippet,
                    meta={
                        'event_date': e.get('event_date', ''),
                        'event_time': e.get('event_time', ''),
                        'venue': e.get('venue', ''),
                        'status': e.get('status', ''),
                    },
                    created_at=e.get('created_at', ''),
                ))

        # Search members (only if enabled)
        if type in ('all', 'members') and member_search_enabled:
            member_ids_cursor = db.community_memberships.find(
                {'community_id': cid, 'is_active': True},
                {'_id': 0, 'user_id': 1},
            )
            member_ids = [m['user_id'] async for m in member_ids_cursor]

            if member_ids:
                user_query = {
                    'user_id': {'$in': member_ids},
                    '$or': [
                        {'name': search_filter},
                        {'full_name': search_filter},
                        {'bio': search_filter},
                    ],
                }
                users = await db.users.find(
                    user_query, {'_id': 0, 'password_hash': 0}
                ).limit(limit).to_list(limit)

                for u in users:
                    name = u.get('name') or u.get('full_name', '')
                    bio = u.get('bio', '') or ''
                    snippet = _make_snippet(bio, q) if bio else ''
                    results.append(SearchResultItem(
                        result_type='member',
                        id=u['user_id'],
                        title=name,
                        snippet=snippet,
                        meta={
                            'email': u.get('email', ''),
                            'location': u.get('location', ''),
                        },
                        created_at=u.get('created_at', ''),
                    ))

        # Apply skip/limit to combined results
        total = len(results)
        results = results[skip:skip + limit]

        return SearchResponse(
            query=q,
            community_id=cid,
            total=total,
            results=results,
        )

    return router


def _make_snippet(text: str, query: str, max_len: int = 150) -> str:
    """Extract a snippet around the query match."""
    if not text:
        return ''
    lower = text.lower()
    q_lower = query.lower()
    idx = lower.find(q_lower)
    if idx == -1:
        return text[:max_len] + ('...' if len(text) > max_len else '')
    start = max(0, idx - 50)
    end = min(len(text), idx + len(query) + 100)
    snippet = text[start:end]
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'
    return snippet
