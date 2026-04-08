"""SEO and Metadata API routes.

GET /api/communities/{slug}/seo/{entity_type}/{entity_id} — Get SEO data (auto-generated or manual)
PATCH /api/communities/{slug}/seo/{entity_type}/{entity_id} — Update SEO (manual override)
DELETE /api/communities/{slug}/seo/{entity_type}/{entity_id} — Reset to auto-generated
GET /api/communities/{slug}/seo/redirects — List slug redirects
GET /api/seo/resolve-redirect?old_slug=x — Resolve a redirect
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, Header
from typing import Annotated, Optional
from datetime import datetime, timezone

from auth import get_current_user
from models import User
from seo_models import (
    SeoMetadata, SeoUpdate, SeoResponse, SlugRedirect, ENTITY_TYPES,
    auto_generate_meta_title, auto_generate_meta_description,
    generate_schema_markup,
)


def create_seo_router(db):
    router = APIRouter(tags=["seo"])

    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ):
        return await get_current_user(db, session_token, authorization)

    async def _get_community(slug):
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(404, "Community not found")
        return community

    async def _require_manager(community, user):
        if user.is_super_admin:
            return
        m = await db.community_memberships.find_one({
            'community_id': community['community_id'],
            'user_id': user.user_id,
            'role_name': 'community_manager',
            'is_active': True,
        })
        if not m:
            raise HTTPException(403, "Community manager access required")

    async def _get_entity(entity_type, entity_id, community_id):
        """Fetch the underlying entity for auto-generation."""
        if entity_type == 'community':
            return await db.communities.find_one({'community_id': community_id}, {'_id': 0})
        elif entity_type == 'discussion':
            return await db.discussion_threads.find_one(
                {'thread_id': entity_id, 'community_id': community_id}, {'_id': 0}
            )
        elif entity_type == 'event':
            return await db.events.find_one(
                {'event_id': entity_id, 'community_id': community_id}, {'_id': 0}
            )
        return None

    # ── Get SEO data (with auto-generation fallback) ──
    @router.get("/communities/{slug}/seo/{entity_type}/{entity_id}", response_model=SeoResponse)
    async def get_seo(slug: str, entity_type: str, entity_id: str):
        if entity_type not in ENTITY_TYPES:
            raise HTTPException(400, f"entity_type must be one of: {ENTITY_TYPES}")

        community = await _get_community(slug)
        cid = community['community_id']

        # For community itself, entity_id = community_id
        if entity_type == 'community':
            entity_id = cid

        # Check if manual override exists
        seo_doc = await db.seo_metadata.find_one(
            {'entity_type': entity_type, 'entity_id': entity_id, 'community_id': cid},
            {'_id': 0},
        )

        entity = await _get_entity(entity_type, entity_id, cid)
        if not entity and entity_type != 'community':
            raise HTTPException(404, f"{entity_type} not found")

        base_url = ''  # Would be set from request in production
        schema = generate_schema_markup(entity_type, entity or {}, community, base_url)

        if seo_doc and seo_doc.get('is_manual_override'):
            return SeoResponse(**seo_doc, schema_markup=schema)

        # Auto-generate
        community_name = community.get('name', '')
        meta_title = auto_generate_meta_title(entity_type, entity or {}, community_name)
        meta_desc = auto_generate_meta_description(entity_type, entity or {})

        og_type_map = {'community': 'website', 'discussion': 'article', 'event': 'event'}

        return SeoResponse(
            seo_id=seo_doc['seo_id'] if seo_doc else f"auto_{entity_type}_{entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            community_id=cid,
            meta_title=meta_title,
            meta_description=meta_desc,
            og_title=meta_title,
            og_description=meta_desc,
            og_type=og_type_map.get(entity_type, 'website'),
            canonical_url=f"/communities/{slug}/{entity_type}s/{entity_id}" if entity_type != 'community' else f"/communities/{slug}",
            is_manual_override=False,
            schema_markup=schema,
        )

    # ── Update SEO (manual override) ──
    @router.patch("/communities/{slug}/seo/{entity_type}/{entity_id}", response_model=SeoResponse)
    async def update_seo(
        slug: str, entity_type: str, entity_id: str,
        data: SeoUpdate, current_user: User = Depends(get_user_dep),
    ):
        if entity_type not in ENTITY_TYPES:
            raise HTTPException(400, f"entity_type must be one of: {ENTITY_TYPES}")

        community = await _get_community(slug)
        cid = community['community_id']
        await _require_manager(community, current_user)

        if entity_type == 'community':
            entity_id = cid

        entity = await _get_entity(entity_type, entity_id, cid)
        if not entity and entity_type != 'community':
            raise HTTPException(404, f"{entity_type} not found")

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(400, "No fields to update")

        updates['is_manual_override'] = True
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()

        existing = await db.seo_metadata.find_one(
            {'entity_type': entity_type, 'entity_id': entity_id, 'community_id': cid}
        )

        if existing:
            await db.seo_metadata.update_one(
                {'entity_type': entity_type, 'entity_id': entity_id, 'community_id': cid},
                {'$set': updates},
            )
        else:
            seo = SeoMetadata(
                entity_type=entity_type, entity_id=entity_id, community_id=cid,
                **{k: v for k, v in updates.items() if k not in ('is_manual_override', 'updated_at')},
                is_manual_override=True,
            )
            doc = seo.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.seo_metadata.insert_one(doc)

        # Return updated
        return await get_seo(slug, entity_type, entity_id)

    # ── Reset to auto-generated ──
    @router.delete("/communities/{slug}/seo/{entity_type}/{entity_id}")
    async def reset_seo(
        slug: str, entity_type: str, entity_id: str,
        current_user: User = Depends(get_user_dep),
    ):
        community = await _get_community(slug)
        cid = community['community_id']
        await _require_manager(community, current_user)

        if entity_type == 'community':
            entity_id = cid

        result = await db.seo_metadata.delete_one(
            {'entity_type': entity_type, 'entity_id': entity_id, 'community_id': cid}
        )
        return {"message": "SEO reset to auto-generated", "deleted": result.deleted_count > 0}

    # ── Slug redirects for a community ──
    @router.get("/communities/{slug}/seo/redirects")
    async def list_redirects(slug: str, current_user: User = Depends(get_user_dep)):
        community = await _get_community(slug)
        await _require_manager(community, current_user)
        redirects = await db.slug_redirects.find(
            {'community_id': community['community_id']}, {'_id': 0}
        ).sort('created_at', -1).to_list(100)
        return redirects

    # ── Resolve a redirect (public) ──
    @router.get("/seo/resolve-redirect")
    async def resolve_redirect(
        old_slug: str = Query(...),
        entity_type: str = Query('community'),
    ):
        redirect = await db.slug_redirects.find_one(
            {'old_slug': old_slug, 'entity_type': entity_type},
            {'_id': 0},
        )
        if not redirect:
            raise HTTPException(404, "No redirect found")
        return redirect

    return router


async def record_slug_redirect(db, entity_type: str, entity_id: str, community_id: str, old_slug: str, new_slug: str):
    """Called from other routes when a slug changes. Creates a redirect record."""
    redirect = SlugRedirect(
        entity_type=entity_type, entity_id=entity_id, community_id=community_id,
        old_slug=old_slug, new_slug=new_slug,
    )
    doc = redirect.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.slug_redirects.insert_one(doc)
