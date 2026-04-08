# A Good Life - API Documentation

## Overview

A Good Life is a multi-manager community platform with role-based access control (RBAC). The platform supports:

- **Shared authentication** across the entire platform
- **Multiple communities** with unique subdirectory-based URLs
- **Role-based permissions** at the community level
- **Multi-community membership** where users can have different roles in different communities

---

## Base URL

```
Production: https://rbac-foundation-2.preview.emergentagent.com/api
```

All API endpoints are prefixed with `/api`.

---

## Authentication

The platform supports two authentication methods:

1. **Email/Password Authentication** (JWT-based)
2. **Google OAuth** (via Emergent)

### Authentication Headers

```
Authorization: Bearer <jwt_token>
```

Or use `session_token` cookie (from Google OAuth).

---

## Roles & Permissions

### Platform Roles

1. **Super Admin** (`super_admin`)
   - Platform-wide administrator
   - Can create/delete communities
   - Can manage all communities
   - Full access to all resources

2. **Community Manager** (`community_manager`)
   - Manages specific community
   - Can update community settings
   - Can add/remove members
   - Can assign roles within community

3. **Moderator** (`moderator`)
   - Can moderate content
   - Can read member information
   - Limited management capabilities

4. **Member** (`member`)
   - Basic community member
   - Can create/update own content
   - Can read community information

### Permission Matrix

| Permission | Super Admin | Community Manager | Moderator | Member |
|------------|-------------|-------------------|-----------|--------|
| `platform.manage` | ✓ | | | |
| `community.create` | ✓ | | | |
| `community.delete` | ✓ | | | |
| `community.update` | ✓ | ✓ | | |
| `community.read` | ✓ | ✓ | ✓ | ✓ |
| `member.manage` | ✓ | ✓ | | |
| `member.create` | ✓ | ✓ | | |
| `member.delete` | ✓ | ✓ | | |
| `member.read` | ✓ | ✓ | ✓ | ✓ |
| `role.assign` | ✓ | ✓ | | |
| `content.manage` | ✓ | ✓ | | |
| `content.moderate` | ✓ | ✓ | ✓ | |
| `content.create` | ✓ | ✓ | ✓ | ✓ |

---

## API Endpoints

### Health Check

#### `GET /api/health`

Check API health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Authentication Endpoints

#### `POST /api/auth/register`

Register new user with email/password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "is_super_admin": false,
    "created_at": "2026-04-08T08:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### `POST /api/auth/login`

Login with email/password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "is_super_admin": false,
    "created_at": "2026-04-08T08:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### `POST /api/auth/session`

Exchange Google OAuth session_id for session token (used by frontend after OAuth redirect).

**Request Body:**
```json
{
  "session_id": "sess_xyz789"
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://...",
  "is_super_admin": false,
  "created_at": "2026-04-08T08:00:00Z"
}
```

Sets `session_token` cookie.

---

#### `GET /api/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": null,
  "is_super_admin": false,
  "created_at": "2026-04-08T08:00:00Z"
}
```

---

#### `POST /api/auth/logout`

Logout current user and clear session.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

### Community Endpoints

#### `POST /api/communities/`

Create new community (**Super Admin Only**).

**Request Body:**
```json
{
  "name": "Tech Innovators",
  "slug": "tech-innovators",
  "description": "A community for technology enthusiasts",
  "community_manager_id": "user_abc123"
}
```

**Response:**
```json
{
  "community_id": "comm_def456",
  "name": "Tech Innovators",
  "slug": "tech-innovators",
  "description": "A community for technology enthusiasts",
  "created_by": "user_superadmin",
  "created_at": "2026-04-08T08:00:00Z",
  "updated_at": "2026-04-08T08:00:00Z",
  "is_active": true,
  "settings": {}
}
```

---

#### `GET /api/communities/`

List all active communities (requires authentication).

**Response:**
```json
[
  {
    "community_id": "comm_def456",
    "name": "Tech Innovators",
    "slug": "tech-innovators",
    "description": "A community for technology enthusiasts",
    "created_by": "user_superadmin",
    "created_at": "2026-04-08T08:00:00Z",
    "updated_at": "2026-04-08T08:00:00Z",
    "is_active": true,
    "settings": {}
  }
]
```

---

#### `GET /api/communities/my-communities`

Get all communities current user is member of with their roles.

**Response:**
```json
[
  {
    "community": {
      "community_id": "comm_def456",
      "name": "Tech Innovators",
      "slug": "tech-innovators",
      ...
    },
    "role": "community_manager",
    "joined_at": "2026-04-08T08:00:00Z"
  }
]
```

---

#### `GET /api/communities/{slug}`

Get community details by slug.

**Response:**
```json
{
  "community_id": "comm_def456",
  "name": "Tech Innovators",
  "slug": "tech-innovators",
  "description": "A community for technology enthusiasts",
  "created_by": "user_superadmin",
  "created_at": "2026-04-08T08:00:00Z",
  "updated_at": "2026-04-08T08:00:00Z",
  "is_active": true,
  "settings": {}
}
```

---

#### `PATCH /api/communities/{slug}`

Update community (requires `community.update` permission).

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_active": true
}
```

All fields are optional.

**Response:** Updated community object.

---

#### `DELETE /api/communities/{slug}`

Delete/deactivate community (**Super Admin Only**).

**Response:**
```json
{
  "message": "Community deleted successfully"
}
```

---

### Membership Endpoints

All membership endpoints use the pattern: `/api/community/{slug}/...`

#### `POST /api/community/{slug}/members`

Add member to community (requires `member.create` permission).

**Request Body:**
```json
{
  "user_id": "user_abc123",
  "role_name": "moderator"
}
```

**Role options:** `community_manager`, `moderator`, `member`

**Response:**
```json
{
  "membership_id": "memb_ghi789",
  "user_id": "user_abc123",
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "community_id": "comm_def456",
  "role_name": "moderator",
  "joined_at": "2026-04-08T08:00:00Z",
  "is_active": true
}
```

---

#### `GET /api/community/{slug}/members`

List all members of community (requires `member.read` permission).

**Response:**
```json
[
  {
    "membership_id": "memb_ghi789",
    "user_id": "user_abc123",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "community_id": "comm_def456",
    "role_name": "moderator",
    "joined_at": "2026-04-08T08:00:00Z",
    "is_active": true
  }
]
```

---

#### `PATCH /api/community/{slug}/members/{user_id}/role`

Update member role (requires `role.assign` permission).

**Request Body:**
```json
{
  "role_name": "community_manager"
}
```

**Response:** Updated membership object.

---

#### `DELETE /api/community/{slug}/members/{user_id}`

Remove member from community (requires `member.delete` permission).

**Response:**
```json
{
  "message": "Member removed successfully"
}
```

---

#### `POST /api/community/{slug}/join`

Join community as member (self-join).

**Response:**
```json
{
  "membership_id": "memb_jkl012",
  "user_id": "user_current",
  "user_name": "Current User",
  "user_email": "current@example.com",
  "community_id": "comm_def456",
  "role_name": "member",
  "joined_at": "2026-04-08T08:00:00Z",
  "is_active": true
}
```

---

#### `POST /api/community/{slug}/leave`

Leave community (self-remove).

**Response:**
```json
{
  "message": "Left community successfully"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Permission denied: community.update required"
}
```

### 404 Not Found
```json
{
  "detail": "Community not found"
}
```

---

## Data Models

### User
```typescript
{
  user_id: string;          // Custom UUID
  email: string;
  name: string;
  picture?: string;         // From Google OAuth
  is_super_admin: boolean;
  created_at: datetime;
  updated_at: datetime;
}
```

### Community
```typescript
{
  community_id: string;     // Custom UUID
  name: string;
  slug: string;             // Unique, URL-friendly
  description: string;
  created_by: string;       // user_id
  created_at: datetime;
  updated_at: datetime;
  is_active: boolean;
  settings: object;
}
```

### CommunityMembership
```typescript
{
  membership_id: string;    // Custom UUID
  user_id: string;
  community_id: string;
  role_name: string;        // community_manager, moderator, member
  joined_at: datetime;
  is_active: boolean;
}
```

---

## URL Pattern

Communities use subdirectory-based URLs:

```
/community/{slug}                    → Community home
/community/{slug}/members            → Members list
/community/{slug}/discussions        → Discussions (future)
/community/{slug}/events             → Events (future)
```

**Important:**
- **Slug** is used in URLs for readability
- **Community ID** is used internally for relationships and permissions
- Slugs must be unique and URL-safe (lowercase, numbers, hyphens only)

---

## Database Collections

1. **users** - User accounts
2. **communities** - Community definitions
3. **community_memberships** - User-community relationships with roles
4. **roles** - Role definitions with permissions
5. **user_sessions** - Authentication sessions

All collections use custom IDs (not MongoDB's `_id`) to avoid serialization issues.

---

## Testing

### Super Admin Credentials

```
Email: admin@agoodlife.com
Password: Admin@123
```

### Example API Flow

```bash
# 1. Login as super admin
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@agoodlife.com","password":"Admin@123"}'

# 2. Create community
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/communities/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"My Community","slug":"my-community","description":"Test community"}'

# 3. Add member to community
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/community/my-community/members" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"user_id":"user_abc123","role_name":"moderator"}'
```

---

## Notes

- All endpoints require authentication except registration and login
- Permissions are checked at the community level
- Super admin bypasses all permission checks
- Users can be members of multiple communities with different roles
- Only super admin can create and delete communities
- Community managers can manage their assigned communities
- Soft delete is used (set `is_active: false`)
