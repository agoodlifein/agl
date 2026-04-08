"""Subscription, Billing, and Trial module.

Plans, subscriptions, trial thresholds, and billing status workflows.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


BILLING_CYCLES = ['monthly', 'yearly']
SUBSCRIPTION_STATUSES = ['active', 'paused', 'canceled', 'expired', 'trial', 'pending_payment']
TRIAL_THRESHOLD_TYPES = ['time', 'member_count', 'both']


# ── Plan Models ──

class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    name: str
    description: str = ''
    billing_cycle: str
    price: float = Field(ge=0)
    currency: str = 'USD'
    features: List[str] = []
    limits: Dict[str, Any] = Field(default_factory=dict)
    # limits can include: max_members, max_events, max_discussions, storage_mb
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ''
    billing_cycle: str
    price: float = Field(ge=0)
    currency: str = 'USD'
    features: List[str] = []
    limits: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('billing_cycle')
    @classmethod
    def validate_cycle(cls, v):
        if v not in BILLING_CYCLES:
            raise ValueError(f'Must be one of: {BILLING_CYCLES}')
        return v


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    features: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    plan_id: str
    name: str
    description: str = ''
    billing_cycle: str
    price: float
    currency: str = 'USD'
    features: List[str] = []
    limits: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ── Subscription Models ──

class Subscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    community_id: str
    plan_id: str
    status: str = 'trial'
    # Billing
    billing_start_date: Optional[str] = None
    billing_end_date: Optional[str] = None
    last_payment_date: Optional[str] = None
    next_payment_date: Optional[str] = None
    # Trial
    trial_start_date: Optional[str] = None
    trial_end_date: Optional[str] = None
    trial_threshold_type: str = 'time'
    trial_member_limit: Optional[int] = None
    trial_extended: bool = False
    trial_extension_days: int = 0
    # Status tracking
    paused_at: Optional[str] = None
    canceled_at: Optional[str] = None
    # Audit
    assigned_by: Optional[str] = None
    notes: str = ''
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionAssign(BaseModel):
    community_id: str
    plan_id: str
    trial_days: int = Field(14, ge=0, le=365)
    trial_threshold_type: str = 'time'
    trial_member_limit: Optional[int] = Field(None, ge=1)
    notes: str = ''

    @field_validator('trial_threshold_type')
    @classmethod
    def validate_threshold(cls, v):
        if v not in TRIAL_THRESHOLD_TYPES:
            raise ValueError(f'Must be one of: {TRIAL_THRESHOLD_TYPES}')
        return v


class SubscriptionAction(BaseModel):
    notes: str = ''


class TrialExtension(BaseModel):
    extra_days: int = Field(..., ge=1, le=365)
    notes: str = ''


class MarkPaidOffline(BaseModel):
    payment_reference: str = ''
    amount: float = Field(ge=0)
    notes: str = ''


class SubscriptionResponse(BaseModel):
    subscription_id: str
    community_id: str
    community_name: Optional[str] = None
    plan_id: str
    plan_name: Optional[str] = None
    status: str
    billing_start_date: Optional[str] = None
    billing_end_date: Optional[str] = None
    last_payment_date: Optional[str] = None
    next_payment_date: Optional[str] = None
    trial_start_date: Optional[str] = None
    trial_end_date: Optional[str] = None
    trial_threshold_type: str = 'time'
    trial_member_limit: Optional[int] = None
    trial_extended: bool = False
    paused_at: Optional[str] = None
    canceled_at: Optional[str] = None
    assigned_by: Optional[str] = None
    notes: str = ''
    created_at: datetime
    updated_at: datetime


# ── Audit Log ──

class BillingAuditLog(BaseModel):
    audit_id: str = Field(default_factory=lambda: f"baud_{uuid.uuid4().hex[:12]}")
    subscription_id: str
    community_id: str
    action: str  # assigned, activated, paused, resumed, canceled, expired, paid_offline, trial_extended
    previous_status: Optional[str] = None
    new_status: str
    performed_by: str
    notes: str = ''
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
