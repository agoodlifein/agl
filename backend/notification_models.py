from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


# ============ NOTIFICATION TYPES ============

NOTIFICATION_TYPES = [
    'welcome_member',
    'post_approved',
    'post_rejected',
    'member_banned',
    'discussion_reply',
    'new_event',
    'join_request_received',
]

CHANNELS = ['email', 'whatsapp']

# System-decided channel mapping per notification type
CHANNEL_MAP = {
    'welcome_member': ['email'],
    'post_approved': ['email'],
    'post_rejected': ['email'],
    'member_banned': ['email'],
    'discussion_reply': ['email'],
    'new_event': ['email', 'whatsapp'],
    'join_request_received': ['email'],
}

# Audience segments
SEGMENTS = ['all', 'member', 'moderator', 'community_manager']


# ============ TEMPLATE MODELS ============

class NotificationTemplate(BaseModel):
    """Default notification template managed by super admin"""
    template_id: str = Field(default_factory=lambda: f"tmpl_{uuid.uuid4().hex[:12]}")
    notification_type: str
    channel: str  # email or whatsapp
    name: str
    subject: Optional[str] = None  # email subject line
    body: str  # template body with {{placeholders}}
    placeholders: List[str] = []  # available placeholder names
    is_locked: bool = False  # if locked, community managers cannot override
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateCreate(BaseModel):
    notification_type: str
    channel: str
    name: str
    subject: Optional[str] = None
    body: str
    placeholders: List[str] = []

    @field_validator('notification_type')
    @classmethod
    def validate_type(cls, v):
        if v not in NOTIFICATION_TYPES:
            raise ValueError(f'Must be one of: {NOTIFICATION_TYPES}')
        return v

    @field_validator('channel')
    @classmethod
    def validate_channel(cls, v):
        if v not in CHANNELS:
            raise ValueError(f'Must be one of: {CHANNELS}')
        return v


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    placeholders: Optional[List[str]] = None


class TemplateResponse(BaseModel):
    template_id: str
    notification_type: str
    channel: str
    name: str
    subject: Optional[str] = None
    body: str
    placeholders: List[str] = []
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime


class TemplateWithOverrideResponse(BaseModel):
    """Template with community-level override info"""
    template_id: str
    notification_type: str
    channel: str
    name: str
    subject: Optional[str] = None
    body: str
    placeholders: List[str] = []
    is_locked: bool = False
    has_override: bool = False
    override_subject: Optional[str] = None
    override_body: Optional[str] = None


# ============ COMMUNITY TEMPLATE OVERRIDE ============

class CommunityTemplateOverride(BaseModel):
    """Community-level template customization by manager"""
    override_id: str = Field(default_factory=lambda: f"ovr_{uuid.uuid4().hex[:12]}")
    template_id: str
    community_id: str
    subject: Optional[str] = None
    body: Optional[str] = None
    updated_by: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateOverrideUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None


# ============ NOTIFICATION LOG ============

class NotificationLog(BaseModel):
    """Delivery log for every notification dispatched"""
    log_id: str = Field(default_factory=lambda: f"nlog_{uuid.uuid4().hex[:12]}")
    notification_type: str
    channel: str
    community_id: str
    community_name: Optional[str] = None
    recipient_user_id: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    template_id: str
    subject: Optional[str] = None
    body: str
    status: str = "queued"  # queued, sent, failed
    error_message: Optional[str] = None
    trigger_event: Optional[str] = None
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None


class NotificationLogResponse(BaseModel):
    log_id: str
    notification_type: str
    channel: str
    community_id: str
    community_name: Optional[str] = None
    recipient_user_id: str
    recipient_email: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    subject: Optional[str] = None
    trigger_event: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None


# ============ EVENT NOTIFICATION REQUEST ============

class EventNotificationRequest(BaseModel):
    """Send event announcement to a segment"""
    event_id: str
    segment: str = "all"  # all, member, moderator, community_manager

    @field_validator('segment')
    @classmethod
    def validate_segment(cls, v):
        if v not in SEGMENTS:
            raise ValueError(f'Must be one of: {SEGMENTS}')
        return v
