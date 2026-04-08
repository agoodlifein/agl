from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


# ============ USER MODELS ============

class User(BaseModel):
    """User model - shared across entire platform"""
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: EmailStr
    name: str
    password_hash: Optional[str] = None  # Only for email/password auth
    picture: Optional[str] = None  # From Google OAuth or uploaded
    is_super_admin: bool = False
    # Profile fields
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    """User registration with email/password"""
    email: EmailStr
    name: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserLogin(BaseModel):
    """User login credentials"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response without sensitive data"""
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_super_admin: bool
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime


# ============ ROLE MODELS ============

class Role(BaseModel):
    """Platform-wide role definitions"""
    role_id: str = Field(default_factory=lambda: f"role_{uuid.uuid4().hex[:8]}")
    name: str  # super_admin, community_manager, moderator, member
    description: str
    permissions: List[str]  # List of permission names
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoleResponse(BaseModel):
    """Role response model"""
    role_id: str
    name: str
    description: str
    permissions: List[str]


# ============ COMMUNITY MODELS ============

class Community(BaseModel):
    """Community model with unique slug"""
    community_id: str = Field(default_factory=lambda: f"comm_{uuid.uuid4().hex[:12]}")
    name: str
    slug: str  # Unique, URL-friendly identifier
    description: str
    created_by: str  # user_id of super admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class CommunityCreate(BaseModel):
    """Create community - only super admin"""
    name: str
    slug: str
    description: str
    community_manager_id: Optional[str] = None  # Assign initial manager
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class CommunityUpdate(BaseModel):
    """Update community details"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class CommunityResponse(BaseModel):
    """Community response model"""
    community_id: str
    name: str
    slug: str
    description: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    settings: Dict[str, Any]


# ============ MEMBERSHIP MODELS ============

class CommunityMembership(BaseModel):
    """User membership in a community with role"""
    membership_id: str = Field(default_factory=lambda: f"memb_{uuid.uuid4().hex[:12]}")
    user_id: str
    community_id: str
    role_name: str  # community_manager, moderator, member
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class MembershipCreate(BaseModel):
    """Add member to community"""
    user_id: str
    role_name: str = "member"  # Default to member
    
    @field_validator('role_name')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['community_manager', 'moderator', 'member']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {allowed_roles}')
        return v


class MembershipUpdate(BaseModel):
    """Update membership role"""
    role_name: str
    
    @field_validator('role_name')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['community_manager', 'moderator', 'member']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {allowed_roles}')
        return v


class MembershipResponse(BaseModel):
    """Membership response with user details"""
    membership_id: str
    user_id: str
    user_name: str
    user_email: str
    community_id: str
    role_name: str
    joined_at: datetime
    is_active: bool


# ============ SESSION MODELS ============

class UserSession(BaseModel):
    """User session for authentication"""
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:16]}")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionData(BaseModel):
    """Session data from Emergent OAuth"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str


class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    token: str
    token_type: str = "bearer"


# ============ PERMISSION MODELS ============

class Permission(BaseModel):
    """Permission definition"""
    permission_id: str = Field(default_factory=lambda: f"perm_{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    resource: str  # community, member, content, etc.
    action: str  # create, read, update, delete, manage


class PermissionCheck(BaseModel):
    """Check user permission in community"""
    user_id: str
    community_slug: str
    permission_name: str


# ============ PROFILE MODELS ============

class ProfileUpdate(BaseModel):
    """Update user profile"""
    name: Optional[str] = None
    picture: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError('Bio must be 500 characters or less')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and len(v) > 20:
            raise ValueError('Phone must be 20 characters or less')
        return v


class ProfileResponse(BaseModel):
    """Complete user profile response"""
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    is_super_admin: bool
    created_at: datetime
    updated_at: datetime


# ============ PASSWORD MANAGEMENT MODELS ============

class PasswordChange(BaseModel):
    """Change user password"""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v


