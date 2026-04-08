"""Community-scoped search module.

Supports searching discussions, events, and optionally members
within a single community, filtered by user permission level.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime


SEARCH_TYPES = ['all', 'discussions', 'events', 'members']


class SearchQuery(BaseModel):
    q: str = Field(..., min_length=2, max_length=200)
    type: str = 'all'
    limit: int = Field(20, ge=1, le=50)
    skip: int = Field(0, ge=0)

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in SEARCH_TYPES:
            raise ValueError(f'Must be one of: {SEARCH_TYPES}')
        return v


class SearchResultItem(BaseModel):
    result_type: str  # 'discussion', 'event', 'member'
    id: str
    title: str
    snippet: str = ''
    meta: dict = Field(default_factory=dict)
    score: float = 0.0
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    community_id: str
    total: int
    results: List[SearchResultItem]
