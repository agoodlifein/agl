from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
import uuid


# ============ DISCUSSION CATEGORY MODELS ============

class DiscussionCategory(BaseModel):
    """Discussion category within a community"""
    category_id: str = Field(default_factory=lambda: f"cat_{uuid.uuid4().hex[:12]}")
    community_id: str
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CategoryCreate(BaseModel):
    """Create discussion category"""
    name: str
    description: Optional[str] = None
    display_order: Optional[int] = 0
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError('Category name must be between 2 and 100 characters')
        return v


class CategoryUpdate(BaseModel):
    """Update discussion category"""
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Category response"""
    category_id: str
    community_id: str
    name: str
    description: Optional[str] = None
    display_order: int
    is_active: bool
    thread_count: int = 0  # Computed field
    created_at: datetime


# ============ DISCUSSION THREAD MODELS ============

class DiscussionThread(BaseModel):
    """Discussion thread/topic"""
    thread_id: str = Field(default_factory=lambda: f"thread_{uuid.uuid4().hex[:12]}")
    category_id: str
    community_id: str
    author_id: str
    title: str
    content: str  # First post content
    status: str = "published"  # draft, pending, published, rejected
    is_pinned: bool = False
    is_locked: bool = False
    view_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThreadCreate(BaseModel):
    """Create discussion thread"""
    category_id: str
    title: str
    content: str
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) < 5 or len(v) > 200:
            raise ValueError('Title must be between 5 and 200 characters')
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if len(v) < 10:
            raise ValueError('Content must be at least 10 characters')
        if len(v) > 10000:
            raise ValueError('Content must not exceed 10,000 characters')
        return v


class ThreadUpdate(BaseModel):
    """Update thread"""
    title: Optional[str] = None
    content: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v and (len(v) < 5 or len(v) > 200):
            raise ValueError('Title must be between 5 and 200 characters')
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if v and len(v) < 10:
            raise ValueError('Content must be at least 10 characters')
        if v and len(v) > 10000:
            raise ValueError('Content must not exceed 10,000 characters')
        return v


class ThreadResponse(BaseModel):
    """Thread response"""
    thread_id: str
    category_id: str
    community_id: str
    author_id: str
    author_name: str
    title: str
    content: str
    status: str
    is_pinned: bool
    is_locked: bool
    view_count: int
    reply_count: int = 0  # Computed field
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime


# ============ POST/REPLY MODELS ============

class Post(BaseModel):
    """Post/reply within a thread"""
    post_id: str = Field(default_factory=lambda: f"post_{uuid.uuid4().hex[:12]}")
    thread_id: str
    community_id: str
    author_id: str
    content: str
    parent_post_id: Optional[str] = None  # For nested replies
    status: str = "published"  # draft, pending, published, rejected
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PostCreate(BaseModel):
    """Create post/reply"""
    content: str
    parent_post_id: Optional[str] = None
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if len(v) < 1:
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:
            raise ValueError('Content must not exceed 10,000 characters')
        return v


class PostUpdate(BaseModel):
    """Update post"""
    content: str
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if len(v) < 1:
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:
            raise ValueError('Content must not exceed 10,000 characters')
        return v


class PostResponse(BaseModel):
    """Post response"""
    post_id: str
    thread_id: str
    author_id: str
    author_name: str
    content: str
    parent_post_id: Optional[str] = None
    status: str
    is_edited: bool
    edited_at: Optional[datetime] = None
    created_at: datetime


# ============ MODERATION MODELS ============

class ModerationAction(BaseModel):
    """Moderation action tracking"""
    action_id: str = Field(default_factory=lambda: f"action_{uuid.uuid4().hex[:12]}")
    content_type: str  # thread or post
    content_id: str
    community_id: str
    moderator_id: str
    action: str  # approve, reject, delete, pin, unpin, lock, unlock
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PendingContentResponse(BaseModel):
    """Pending content for moderation"""
    content_type: str  # thread or post
    content_id: str
    author_name: str
    title: Optional[str] = None  # For threads
    content: str
    created_at: datetime
