# A Good Life - Community Platform PRD

## Original Problem Statement
Build the core backend architecture for "A Good Life" as a multi-manager community platform. Shared authentication (email/password + Google OAuth via Emergent), RBAC with 4 roles (super_admin, community_manager, moderator, member), subdirectory-based community URLs, and role-based access control at the community level.

## Tech Stack
- **Backend**: FastAPI (Python) + MongoDB (Motor Asyncio)
- **Frontend**: React 19 + Shadcn/UI + Tailwind CSS (minimal test UI)
- **Auth**: JWT + Emergent Google OAuth (cookie-based sessions)
- **File Storage**: Local filesystem with FastAPI StaticFiles
- **Notifications**: Pluggable provider architecture (MockProvider for dev, ready for SendGrid/Twilio)

## Architecture
```
/app/backend/
├── server.py                    # Main entry, routers, middleware, static mounts
├── auth.py                      # JWT, bcrypt, session management, Emergent OAuth
├── models.py                    # Core Pydantic models (User, Community, Membership, etc.)
├── permissions.py               # RBAC role definitions and permission checking
├── event_models.py              # Event and Media Pydantic models
├── discussion_models.py         # Discussion thread/post models
├── notification_models.py       # Template, Override, Log, Request models
├── notification_engine.py       # Core engine: trigger → resolve → render → dispatch → log
├── notification_providers.py    # Pluggable ABC + MockProvider (SendGrid/Twilio stubs)
├── seed.py                      # DB seeding (admin, roles, indexes, templates, migrations)
└── routes/
    ├── auth_routes.py
    ├── community_routes.py
    ├── membership_routes.py
    ├── profile_routes.py
    ├── admin_community_routes.py
    ├── manager_routes.py
    ├── member_onboarding_routes.py  (+ notification triggers)
    ├── discussion_routes.py         (+ notification triggers)
    ├── discussion_moderation_routes.py (+ notification triggers)
    ├── event_routes.py
    └── notification_routes.py       # Admin template CRUD + Manager overrides + Logs
```

## What's Been Implemented

### Phase 1: Core Auth, RBAC, Profiles ✅
### Phase 2: Super Admin Community Creation ✅
### Phase 3: Community Manager Module ✅
### Phase 4: Member Onboarding ✅
### Phase 5: Discussions/Forum ✅
### Phase 6: Events & Media ✅ (33/33 backend tests)
### Frontend Test UI ✅ (95% pass rate)

### Phase 7: Notifications & Communication ✅ (33/33 tests, 2026-04-08)
- **7 notification types**: welcome_member, post_approved, post_rejected, member_banned, discussion_reply, new_event, join_request_received
- **8 default templates** seeded (new_event has both email + WhatsApp)
- **Pluggable providers**: MockProvider (dev), ABC ready for SendGrid (email) and Twilio (WhatsApp)
- **System-decided channel mapping**: email for most, email+whatsapp for new_event
- **Template hierarchy**: Super admin controls universal templates, can lock templates. Managers customize unlocked templates per community.
- **Audience segmentation**: By role within community (all, member, moderator, community_manager)
- **Delivery logs**: Per-notification log with status, rendered content, recipient info. Admin sees all, manager sees community-scoped. Aggregated stats endpoint.
- **Trigger hooks**: Integrated into member_onboarding, discussion, discussion_moderation routes
- **RBAC**: Admin-only for template management + global logs. Manager-only for community overrides + community logs.
- **MOCKED**: Email and WhatsApp sending via MockProvider (no live API keys needed yet)

## DB Collections
users, roles, communities, community_memberships, join_requests, user_sessions,
discussion_categories, discussion_threads, posts, events, event_media,
notification_templates, community_template_overrides, notification_logs

## Prioritized Backlog
### P1 - Content Search & Filtering
### P1 - Connect real email/WhatsApp providers (SendGrid, Twilio) when keys available
### P2 - User notification preferences (opt-in/opt-out per type/channel)
### P2 - Advanced Profile Features (deferred by user)
### P3 - Event reminders, community status change notifications
