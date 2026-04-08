# A Good Life - Community Platform PRD

## Original Problem Statement
Build the core backend architecture for "A Good Life" as a multi-manager community platform. Create one shared authentication system (email/password + Google OAuth via Emergent) across the full platform. Support roles: super admin, community manager, moderator, and member. One user must be able to join multiple communities and hold different roles in different communities. Use subdirectory-based URLs for communities (`/community/{community-slug}`). Build role-based access control (RBAC) at the community level. Focus purely on backend logic, permissions, and data structures. Keep UI, design, styling, and layout STRICTLY OUT OF SCOPE.

## User Personas
- **Super Admin**: Platform owner, creates communities, manages all communities, assigns managers
- **Community Manager**: Manages a specific community (events, members, branding, discussions)
- **Moderator**: Helps moderate content within a community
- **Member**: Participates in communities (discussions, events)

## Core Requirements
- Shared Auth (Email/Pass + Google OAuth via Emergent)
- Super Admin Community Creation (status, branding fields)
- Community Manager Module (restricted edits, logo validation < 200KB)
- Member Onboarding (public vs. private join requests, approvals)
- Discussions and Forum Module (Categories, threads, posts, replies, moderation)
- Events and Media Module (Event CRUD, direct media upload, auto-cleanup on delete)

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (Motor Asyncio)
- **Auth**: JWT + Emergent Google OAuth (cookie-based sessions)
- **File Storage**: Local filesystem with FastAPI StaticFiles mount
- **Frontend**: OUT OF SCOPE

## Architecture
```
/app/backend/
├── server.py          # Main entry, routers, middleware, static mounts
├── auth.py            # JWT, bcrypt, session management, Emergent OAuth
├── models.py          # Pydantic models (User, Community, Membership, etc.)
├── permissions.py     # RBAC role definitions and permission checking
├── event_models.py    # Event and Media Pydantic models
├── discussion_models.py # Discussion thread/post models
├── seed.py            # DB seeding (admin, roles, indexes, migrations)
└── routes/
    ├── auth_routes.py              # Register, login, OAuth session, me, logout
    ├── community_routes.py         # Community CRUD
    ├── membership_routes.py        # Join/leave, member management
    ├── profile_routes.py           # User profile management
    ├── admin_community_routes.py   # Super admin community management
    ├── manager_routes.py           # Community manager operations
    ├── member_onboarding_routes.py # Join requests, approvals
    ├── discussion_routes.py        # Threads, posts, categories
    ├── discussion_moderation_routes.py # Content moderation
    └── event_routes.py             # Events CRUD + media upload
```

## What's Been Implemented

### Phase 1: Core Architecture, RBAC, Auth, Profile & Password Management ✅
- Email/password registration and login with JWT
- Google OAuth via Emergent Auth (session exchange, cookie-based auth)
- RBAC with 4 roles (super_admin, community_manager, moderator, member)
- User profile CRUD (bio, phone, location)
- Password change for email/password users

### Phase 2: Super Admin Community Creation ✅
- Community CRUD with slug-based URLs
- Status management (active, paused, disabled)
- Branding fields (logo, cover, accent_color, intro_copy, etc.)
- Manager assignment/removal

### Phase 3: Community Manager Module ✅
- Restricted field updates (name, branding, privacy - cannot change slug/status)
- Logo upload with <200KB validation
- Privacy toggle (public/private)

### Phase 4: Member Onboarding ✅
- Public community: direct join
- Private community: join request workflow
- Approval/rejection by managers
- Ban/restore members
- Membership status checking

### Phase 5: Discussions and Forum ✅
- Categories per community
- Threaded discussions (create, update, delete)
- Posts/replies within threads
- Moderation (approve/reject threads)
- Pinning threads

### Phase 6: Events and Media ✅ (Tested 2026-04-08)
- Event CRUD (create, read, update, delete)
- Draft/published/cancelled status
- Media upload (JPEG/PNG, max 5MB, max 10 per event)
- Static file serving via /api/media/events/
- Auto-cleanup of media files on event deletion
- Individual media deletion
- RBAC enforced (only managers/super admin)
- All validations (title, description, date, file type/size)
- 33/33 tests passed

## Prioritized Backlog

### P1 - Content Search & Filtering
- Search discussions by keyword
- Filter community content

### P1 - Notifications System
- Join request approval notifications
- New post notifications
- Event update notifications
- Email preference management

### P2 - Advanced Profile Features (Deferred by user)
- Social links
- Activity feeds
- Profile completion scoring
- Custom sections

## DB Collections
- `users`, `roles`, `communities`, `community_memberships`
- `join_requests`, `user_sessions`
- `discussion_categories`, `discussion_threads`, `posts`
- `events`, `event_media`
