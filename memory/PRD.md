# A Good Life - Community Platform PRD

## Original Problem Statement
Multi-manager community platform with shared auth (email/password + Google OAuth via Emergent), RBAC (super_admin, community_manager, moderator, member), subdirectory-based community URLs, and role-based access control at the community level. Backend-first architecture.

## Tech Stack
- **Backend**: FastAPI (Python) + MongoDB (Motor Asyncio)
- **Frontend**: React 19 + Shadcn/UI + Tailwind CSS (minimal test UI)
- **Auth**: JWT + Emergent Google OAuth (cookie-based sessions)
- **Notifications**: Pluggable provider (MockProvider for dev, ready for SendGrid/Twilio)
- **Billing**: Admin-managed (no live payment gateway yet)

## Architecture
```
/app/backend/
├── server.py                    # Entry, 16 routers, middleware, static mounts
├── auth.py                      # JWT, bcrypt, session, Emergent OAuth
├── models.py                    # Core models (User, Community, Membership)
├── permissions.py               # RBAC role definitions
├── event_models.py              # Event & Media models
├── discussion_models.py         # Discussion thread/post models
├── notification_models.py       # Template, Override, Log models
├── notification_engine.py       # Trigger → resolve → render → dispatch → log
├── notification_providers.py    # Pluggable ABC + MockProvider
├── search_models.py             # Search query/response models
├── seo_models.py                # SEO metadata, schema.org, redirects
├── subscription_models.py       # Plan, Subscription, BillingAuditLog
├── governance.py                # Subscription middleware, branding limits, cleanup
├── seed.py                      # DB seeding, indexes, templates, migrations
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
    ├── notification_routes.py
    ├── search_routes.py
    ├── seo_routes.py
    ├── subscription_routes.py
    └── governance_routes.py
```

## Completed Phases

### Phase 1-5: Core Platform ✅
Auth, RBAC, profiles, super admin, community manager, member onboarding, discussions/forum

### Phase 6: Events & Media ✅ (33/33 tests)
Event CRUD, media upload, static serving, auto-cleanup

### Phase 7: Notifications ✅ (33/33 tests)
7 trigger types, 8 templates, pluggable providers (MOCKED), template hierarchy, delivery logs

### Frontend Test UI ✅ (95% pass rate)
Login/signup/OAuth, dashboard, profile, communities, discussions, events

### Phase 8: Community-Scoped Search ✅ (2026-04-08)
- Search discussions, events, members within a community
- Filtered by permissions (members only see published, managers see drafts)
- Non-members blocked (403), minimum 2-char query

### Phase 9: SEO & Metadata ✅ (2026-04-08)
- Auto-generated meta title, description, OG tags from content
- Manual override with PATCH, reset with DELETE
- Schema.org JSON-LD: WebPage (communities), DiscussionForumPosting (threads), Event (events)
- Breadcrumb markup, canonical URLs
- Slug redirect tracking and resolution

### Phase 10: Subscription & Billing ✅ (52 tests)
- Plans: monthly/yearly, price, features, limits
- Subscriptions: assign with trial, activate, pause, resume, cancel, mark-paid offline
- Trials: time-based, member-count-based, or both; manual extension
- Status workflow: trial → active ↔ paused → canceled/expired
- Full audit trail with previous/new status tracking

### Phase 11: Governance & Platform Control ✅ (52 tests)
- Subscription enforcement middleware: blocks writes (402) when canceled/expired, reads always pass
- Auto-expiry: trials and billing periods auto-expire when dates pass
- Branding limits: logo <200KB, cover <1MB, color hex validation, field length limits
- Media cleanup: removes orphaned event media directories
- System integrity check: counts all collections, flags orphaned data

## DB Collections (15)
users, roles, communities, community_memberships, join_requests, user_sessions,
discussion_categories, discussion_threads, posts, events, event_media,
notification_templates, community_template_overrides, notification_logs,
seo_metadata, slug_redirects, plans, subscriptions, billing_audit_logs

## Prioritized Backlog
### P1 - Connect real email/WhatsApp providers (SendGrid, Twilio)
### P1 - Connect payment gateway (Stripe) for automated billing
### P2 - User notification preferences (opt-in/opt-out per type/channel)
### P2 - Advanced Profile Features (deferred by user)
### P2 - Full merge with Inner Circle GitHub project (design + functionality)
### P3 - Event reminders, community status change notifications
