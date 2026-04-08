# A Good Life - Multi-Manager Community Platform

## Overview

A Good Life is a **backend architecture** for a multi-manager community platform with robust role-based access control (RBAC). The platform enables multiple communities to coexist with independent management while sharing a unified authentication system.

### Key Features

✅ **Shared Authentication System**
- Email/password authentication (JWT-based)
- Google OAuth integration via Emergent
- Single sign-on across all communities

✅ **Multi-Community Support**
- Users can join multiple communities
- Different roles in different communities
- Subdirectory-based URL structure (`/community/{slug}/...`)

✅ **Role-Based Access Control**
- 4 platform roles: Super Admin, Community Manager, Moderator, Member
- Community-level permission checks
- Granular permission matrix

✅ **Flexible Membership**
- Self-join communities as member
- Administrators can assign specific roles
- Support for role changes and member removal

✅ **User Profile Management**
- Platform-wide user profiles
- Profile fields: name, picture, bio, phone, location
- Users manage their own profiles
- Super admin can view all profiles
- Password change for email/password users

---

## Architecture

### Technology Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT + Emergent OAuth
- **API Style**: REST

### Core Components

```
backend/
├── server.py              # Main FastAPI application
├── models.py              # Pydantic models and schemas
├── auth.py                # Authentication logic
├── permissions.py         # RBAC permission system
├── seed.py                # Database initialization script
└── routes/
    ├── auth_routes.py     # Authentication endpoints
    ├── community_routes.py # Community CRUD
    ├── membership_routes.py # Membership management
    └── profile_routes.py   # User profile management
```

---

## Data Model

### Collections

1. **users** - User accounts with authentication
2. **communities** - Community definitions and settings
3. **community_memberships** - User-community relationships with roles
4. **roles** - Role definitions with permissions
5. **user_sessions** - Session management for OAuth

### Relationships

```
User (1) ─────── (N) CommunityMembership (N) ─────── (1) Community
                           │
                           │ has role
                           ▼
                          Role
```

### Custom ID Strategy

All collections use custom UUID-based IDs (e.g., `user_abc123`, `comm_def456`) instead of MongoDB's `_id` to:
- Avoid BSON serialization issues
- Provide consistent API responses
- Enable better cross-collection references

---

## Roles & Permissions

### Platform Roles

| Role | Description | Scope |
|------|-------------|-------|
| **Super Admin** | Platform administrator | All communities |
| **Community Manager** | Community overseer | Assigned community |
| **Moderator** | Content moderator | Assigned community |
| **Member** | Regular participant | Joined communities |

### Permission Model

Permissions follow the pattern: `resource.action`

**Resources**: `platform`, `community`, `member`, `content`, `role`
**Actions**: `manage`, `create`, `read`, `update`, `delete`, `moderate`

Examples:
- `community.create` - Create new communities
- `member.manage` - Add/remove members
- `content.moderate` - Moderate community content
- `role.assign` - Assign roles to members

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete permission matrix.

---

## Key Business Rules

1. ✅ **Only Super Admin can create communities**
   - Regular users cannot self-create communities
   - Super admin assigns initial community manager

2. ✅ **Multi-community membership**
   - Users can join unlimited communities
   - Each membership has independent role

3. ✅ **Role hierarchy within communities**
   - Community Manager > Moderator > Member
   - Super Admin bypasses all checks

4. ✅ **Subdirectory URL structure**
   - URLs use readable slugs: `/community/tech-innovators/members`
   - Backend uses IDs for relationships
   - Slugs must be unique across platform

5. ✅ **Dual authentication support**
   - Email/password for traditional login
   - Google OAuth for social login
   - Both methods share same user database

6. ✅ **Platform-wide user profiles**
   - Shared profile across all communities
   - Users control their own profile data
   - Profile includes: name, picture, bio, phone, location
   - Super admin can view all profiles

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- MongoDB
- pip/venv

### Installation

```bash
# 1. Install dependencies
cd /app/backend
pip install -r requirements.txt

# 2. Configure environment
# Edit backend/.env with your MongoDB connection

# 3. Initialize database
python seed.py

# 4. Start server
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Database Seeding

The `seed.py` script initializes:
- Super admin account
- Role definitions with permissions
- Database indexes
- Permission mappings

**Default Super Admin Credentials:**
```
Email: admin@agoodlife.com
Password: Admin@123
```

⚠️ **Change the password after first login!**

---

## API Usage

### Base URL

```
Production: https://rbac-foundation-2.preview.emergentagent.com/api
```

### Quick Start Examples

#### 1. Register & Login

```bash
# Register new user
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePass123"
  }'

# Login
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

#### 2. Create Community (Super Admin Only)

```bash
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/communities/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "name": "Tech Innovators",
    "slug": "tech-innovators",
    "description": "A community for technology enthusiasts",
    "community_manager_id": "user_abc123"
  }'
```

#### 3. Add Member to Community

```bash
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/community/tech-innovators/members" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "user_id": "user_xyz789",
    "role_name": "moderator"
  }'
```

#### 4. Join Community (Self-Join)

```bash
curl -X POST "https://rbac-foundation-2.preview.emergentagent.com/api/community/tech-innovators/join" \
  -H "Authorization: Bearer <user_token>"
```

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete endpoint reference.

---

## Permission Checking

### How It Works

1. **Extract user from authentication token**
2. **Super admin check** - If user is super admin, allow all actions
3. **Lookup user's role in community** - Query `community_memberships`
4. **Check role permissions** - Verify role has required permission
5. **Allow or deny** - Return result

### Example Permission Check

```python
# Check if user can update community
has_permission = await check_permission(
    db=db,
    user=current_user,
    community_id="comm_abc123",
    required_permission="community.update"
)

if not has_permission:
    raise HTTPException(status_code=403, detail="Permission denied")
```

### Built-in Permission Helpers

```python
# Require specific permission
await require_permission(db, user, community_id, "member.create")

# Require specific role
await require_community_role(db, user, community_id, ["community_manager", "moderator"])

# Get user's communities with roles
communities = await get_user_communities(db, user_id)
```

---

## Testing

### Test Credentials

See `/app/memory/test_credentials.md` for current test accounts.

### Testing Checklist

- [x] User registration with email/password
- [x] User login with JWT authentication
- [x] Super admin can create communities
- [x] Super admin can assign community managers
- [x] Community manager can add members
- [x] Community manager can update community
- [x] Community manager cannot create new communities
- [x] Members can join communities
- [x] Members can leave communities
- [x] Users can be in multiple communities
- [x] Different roles in different communities
- [x] Permission checks work correctly
- [x] Subdirectory URLs work with slugs
- [x] User profile management (get/update)
- [x] Profile shared across all communities
- [x] Super admin can view all profiles
- [x] Regular users can only update own profile
- [x] Password change with current password verification
- [x] Password validation (min 8 characters)
- [x] OAuth users blocked from password change

---

## Security Considerations

### Implemented

✅ **Password hashing** with bcrypt
✅ **JWT tokens** with expiration (7 days)
✅ **HttpOnly cookies** for OAuth sessions
✅ **Role-based access control** at endpoint level
✅ **Custom user IDs** to avoid MongoDB `_id` exposure
✅ **Timezone-aware timestamps** for security checks
✅ **Password change** requires current password verification
✅ **Minimum password length** enforcement (8 characters)

### Recommendations for Production

- [ ] Add rate limiting on authentication endpoints
- [ ] Implement password reset flow
- [ ] Add email verification for new accounts
- [ ] Enable HTTPS only (already configured)
- [ ] Rotate JWT secret regularly
- [ ] Add audit logging for sensitive operations
- [ ] Implement session invalidation on password change
- [ ] Add CSRF protection for cookie-based auth

---

## Project Structure

```
/app/
├── backend/
│   ├── server.py                 # Main FastAPI app
│   ├── models.py                 # Data models
│   ├── auth.py                   # Authentication logic
│   ├── permissions.py            # RBAC system
│   ├── seed.py                   # Database initialization
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment configuration
│   └── routes/
│       ├── auth_routes.py        # Auth endpoints
│       ├── community_routes.py   # Community CRUD
│       ├── membership_routes.py  # Membership management
│       └── profile_routes.py     # Profile management
│
├── memory/
│   └── test_credentials.md       # Test account credentials
│
├── API_DOCUMENTATION.md          # Complete API reference
├── auth_testing.md               # Auth testing playbook
└── README.md                     # This file
```

---

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [MongoDB](https://www.mongodb.com/) - NoSQL database
- [Motor](https://motor.readthedocs.io/) - Async MongoDB driver
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [bcrypt](https://pypi.org/project/bcrypt/) - Password hashing
- [PyJWT](https://pyjwt.readthedocs.io/) - JWT tokens
