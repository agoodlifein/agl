from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date, time, timezone
import uuid


# ============ EVENT MODELS ============

class Event(BaseModel):
    """Community event"""
    event_id: str = Field(default_factory=lambda: f"event_{uuid.uuid4().hex[:12]}")
    community_id: str
    created_by: str  # user_id
    title: str
    description: str
    event_date: date
    event_time: Optional[time] = None
    venue: Optional[str] = None
    details: Optional[str] = None  # Additional details/agenda
    status: str = "published"  # draft, published, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventCreate(BaseModel):
    """Create event"""
    title: str
    description: str
    event_date: date
    event_time: Optional[time] = None
    venue: Optional[str] = None
    details: Optional[str] = None
    status: Optional[str] = "published"
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) < 5 or len(v) > 200:
            raise ValueError('Title must be between 5 and 200 characters')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if len(v) < 10 or len(v) > 5000:
            raise ValueError('Description must be between 10 and 5000 characters')
        return v
    
    @field_validator('event_date')
    @classmethod
    def validate_event_date(cls, v):
        if v < date.today():
            raise ValueError('Event date cannot be in the past')
        return v
    
    @field_validator('venue')
    @classmethod
    def validate_venue(cls, v):
        if v and len(v) > 500:
            raise ValueError('Venue must not exceed 500 characters')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['draft', 'published', 'cancelled']:
            raise ValueError('Status must be draft, published, or cancelled')
        return v


class EventUpdate(BaseModel):
    """Update event"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    event_time: Optional[time] = None
    venue: Optional[str] = None
    details: Optional[str] = None
    status: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v and (len(v) < 5 or len(v) > 200):
            raise ValueError('Title must be between 5 and 200 characters')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v and (len(v) < 10 or len(v) > 5000):
            raise ValueError('Description must be between 10 and 5000 characters')
        return v
    
    @field_validator('venue')
    @classmethod
    def validate_venue(cls, v):
        if v and len(v) > 500:
            raise ValueError('Venue must not exceed 500 characters')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['draft', 'published', 'cancelled']:
            raise ValueError('Status must be draft, published, or cancelled')
        return v


class EventResponse(BaseModel):
    """Event response"""
    event_id: str
    community_id: str
    created_by: str
    creator_name: str
    title: str
    description: str
    event_date: date
    event_time: Optional[time] = None
    venue: Optional[str] = None
    details: Optional[str] = None
    status: str
    media_count: int = 0
    media_urls: List[str] = []
    created_at: datetime
    updated_at: datetime


# ============ EVENT MEDIA MODELS ============

class EventMedia(BaseModel):
    """Event media file"""
    media_id: str = Field(default_factory=lambda: f"media_{uuid.uuid4().hex[:12]}")
    event_id: str
    community_id: str
    file_path: str  # Relative path from media root
    file_name: str  # Original filename
    file_type: str  # image/jpeg, image/png
    file_size: int  # Bytes
    uploaded_by: str  # user_id
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MediaResponse(BaseModel):
    """Media response"""
    media_id: str
    event_id: str
    file_name: str
    file_type: str
    file_size: int
    url: str  # Public URL to access the file
    uploaded_at: datetime
