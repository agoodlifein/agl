"""SEO and Metadata module.

Supports editable SEO fields for communities, discussions, and events.
Includes Open Graph, schema.org JSON-LD, canonical URLs, and redirect mapping.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import re


ENTITY_TYPES = ['community', 'discussion', 'event']


class SeoMetadata(BaseModel):
    seo_id: str = Field(default_factory=lambda: f"seo_{uuid.uuid4().hex[:12]}")
    entity_type: str  # community, discussion, event
    entity_id: str
    community_id: str
    # Core SEO fields
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_tags: List[str] = []
    focus_keyword: Optional[str] = None
    # Open Graph
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: str = 'website'  # website, article, event
    # Canonical & redirect
    canonical_url: Optional[str] = None
    # Auto vs manual
    is_manual_override: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SeoUpdate(BaseModel):
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_tags: Optional[List[str]] = None
    focus_keyword: Optional[str] = Field(None, max_length=100)
    og_title: Optional[str] = Field(None, max_length=200)
    og_description: Optional[str] = Field(None, max_length=500)
    og_image: Optional[str] = None
    og_type: Optional[str] = None
    canonical_url: Optional[str] = None


class SeoResponse(BaseModel):
    seo_id: str
    entity_type: str
    entity_id: str
    community_id: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_tags: List[str] = []
    focus_keyword: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: str = 'website'
    canonical_url: Optional[str] = None
    is_manual_override: bool = False
    schema_markup: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None


class SlugRedirect(BaseModel):
    redirect_id: str = Field(default_factory=lambda: f"redir_{uuid.uuid4().hex[:12]}")
    entity_type: str
    entity_id: str
    community_id: str
    old_slug: str
    new_slug: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Auto-generation helpers ──────────────────────────────────────────

def auto_generate_meta_title(entity_type: str, entity: dict, community_name: str = '') -> str:
    if entity_type == 'community':
        return entity.get('name', 'Community')
    elif entity_type == 'discussion':
        title = entity.get('title', 'Discussion')
        return f"{title} | {community_name}" if community_name else title
    elif entity_type == 'event':
        title = entity.get('title', 'Event')
        date = entity.get('event_date', '')
        return f"{title} - {date}" if date else title
    return ''


def auto_generate_meta_description(entity_type: str, entity: dict) -> str:
    if entity_type == 'community':
        desc = entity.get('description', '')
    elif entity_type == 'discussion':
        desc = entity.get('content', '')
    elif entity_type == 'event':
        desc = entity.get('description', '')
    else:
        desc = ''
    desc = re.sub(r'<[^>]+>', '', desc)  # strip HTML
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:160] + '...' if len(desc) > 160 else desc


def generate_schema_markup(entity_type: str, entity: dict, community: dict, base_url: str = '') -> dict:
    """Generate schema.org JSON-LD markup."""
    slug = community.get('slug', '')
    if entity_type == 'community':
        return {
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            'name': entity.get('name', ''),
            'description': entity.get('description', ''),
            'url': f"{base_url}/communities/{slug}",
            'breadcrumb': {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': base_url},
                    {'@type': 'ListItem', 'position': 2, 'name': entity.get('name', ''), 'item': f"{base_url}/communities/{slug}"},
                ],
            },
        }
    elif entity_type == 'discussion':
        return {
            '@context': 'https://schema.org',
            '@type': 'DiscussionForumPosting',
            'headline': entity.get('title', ''),
            'text': (entity.get('content', '') or '')[:500],
            'author': {'@type': 'Person', 'name': entity.get('author_name', '')},
            'datePublished': entity.get('created_at', ''),
            'url': f"{base_url}/communities/{slug}/discussions/{entity.get('thread_id', '')}",
            'breadcrumb': {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': base_url},
                    {'@type': 'ListItem', 'position': 2, 'name': community.get('name', ''), 'item': f"{base_url}/communities/{slug}"},
                    {'@type': 'ListItem', 'position': 3, 'name': entity.get('title', ''), 'item': f"{base_url}/communities/{slug}/discussions/{entity.get('thread_id', '')}"},
                ],
            },
        }
    elif entity_type == 'event':
        schema = {
            '@context': 'https://schema.org',
            '@type': 'Event',
            'name': entity.get('title', ''),
            'description': entity.get('description', ''),
            'startDate': entity.get('event_date', ''),
            'url': f"{base_url}/communities/{slug}/events/{entity.get('event_id', '')}",
            'breadcrumb': {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': base_url},
                    {'@type': 'ListItem', 'position': 2, 'name': community.get('name', ''), 'item': f"{base_url}/communities/{slug}"},
                    {'@type': 'ListItem', 'position': 3, 'name': entity.get('title', ''), 'item': f"{base_url}/communities/{slug}/events/{entity.get('event_id', '')}"},
                ],
            },
        }
        if entity.get('venue'):
            schema['location'] = {'@type': 'Place', 'name': entity['venue']}
        if entity.get('event_time'):
            schema['startDate'] = f"{entity.get('event_date', '')}T{entity['event_time']}"
        return schema
    return {}
