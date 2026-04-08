# A Good Life - Community Platform PRD

## Original Problem Statement
Build the core backend architecture for "A Good Life" as a multi-manager community platform. Create one shared authentication system (email/password + Google OAuth via Emergent) across the full platform. Support roles: super admin, community manager, moderator, and member. One user must be able to join multiple communities and hold different roles in different communities. Use subdirectory-based URLs for communities (`/community/{community-slug}`). Build role-based access control (RBAC) at the community level.

## Tech Stack
- **Backend**: FastAPI (Python) + MongoDB (Motor Asyncio)
- **Frontend**: React 19 + Shadcn/UI + Tailwind CSS
- **Auth**: JWT + Emergent Google OAuth (cookie-based sessions)
- **File Storage**: Local filesystem with FastAPI StaticFiles

## Architecture
```
/app/backend/
├── server.py, auth.py, models.py, permissions.py, seed.py
├── event_models.py, discussion_models.py
└── routes/ (auth, community, membership, profile, admin, manager, onboarding, discussion, moderation, event)

/app/frontend/src/
├── App.js (routing + AuthProvider)
├── contexts/AuthContext.js
├── lib/api.js
└── pages/ (AuthPage, Dashboard, ProfilePage, CommunitiesPage, CommunityPage, DiscussionPage, EventPage)
```

## What's Been Implemented

### Backend (Phases 1-6) - All Complete & Tested
- Phase 1: Auth (email/password + Google OAuth), RBAC, Profile, Password Management
- Phase 2: Super Admin Community Creation (status, branding, manager assignment)
- Phase 3: Community Manager Module (restricted edits, logo validation <200KB)
- Phase 4: Member Onboarding (public/private join, approval workflows)
- Phase 5: Discussions/Forum (categories, threads, posts, moderation)
- Phase 6: Events & Media (CRUD, upload, static serving, auto-cleanup) - 33/33 tests passed

### Frontend (Test UI) - Complete (2026-04-08)
- Auth: Login, Signup, Google Login button, Logout
- Dashboard: Role-based with admin panel, managed/member communities
- Profile: View/Edit (name, bio, phone, location) + Change Password
- Communities: Browse all, create (admin), status management (admin), assign manager (admin)
- Community Detail: Discussions tab (create/list threads), Events tab (create/list events), Settings tab (edit community, create category)
- Discussion Detail: View thread, list replies, post reply
- Event Detail: View details, upload media (images), display gallery
- Frontend testing: 95% pass rate, all major flows verified

## Prioritized Backlog
### P1 - Content Search & Filtering
### P1 - Notifications System
### P2 - Advanced Profile Features (deferred by user)

## DB Collections
users, roles, communities, community_memberships, join_requests, user_sessions, discussion_categories, discussion_threads, posts, events, event_media
