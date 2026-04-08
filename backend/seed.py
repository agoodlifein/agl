"""Seed script to initialize platform with super admin and roles"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

from auth import hash_password
from models import User, Role
from permissions import ROLE_PERMISSIONS


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


async def seed_database():
    """Initialize database with super admin and roles"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🌱 Starting database seeding...")
    
    # ============ SEED SUPER ADMIN ============
    print("\n👤 Creating super admin...")
    
    super_admin_email = "admin@agoodlife.com"
    super_admin_password = "Admin@123"
    
    # Check if super admin exists
    existing_admin = await db.users.find_one(
        {'email': super_admin_email},
        {'_id': 0}
    )
    
    if existing_admin:
        print(f"   ✓ Super admin already exists: {super_admin_email}")
    else:
        # Create super admin
        admin = User(
            email=super_admin_email,
            name="Super Admin",
            password_hash=hash_password(super_admin_password),
            is_super_admin=True
        )
        
        admin_doc = admin.model_dump()
        admin_doc['created_at'] = admin_doc['created_at'].isoformat()
        admin_doc['updated_at'] = admin_doc['updated_at'].isoformat()
        
        await db.users.insert_one(admin_doc)
        
        print(f"   ✓ Created super admin: {super_admin_email}")
        print(f"   Password: {super_admin_password}")
    
    # ============ SEED ROLES ============
    print("\n🎭 Creating roles...")
    
    role_definitions = [
        {
            'name': 'super_admin',
            'description': 'Platform super administrator with full access',
            'permissions': ROLE_PERMISSIONS['super_admin']
        },
        {
            'name': 'community_manager',
            'description': 'Community manager who oversees community operations',
            'permissions': ROLE_PERMISSIONS['community_manager']
        },
        {
            'name': 'moderator',
            'description': 'Community moderator who helps manage content and members',
            'permissions': ROLE_PERMISSIONS['moderator']
        },
        {
            'name': 'member',
            'description': 'Regular community member',
            'permissions': ROLE_PERMISSIONS['member']
        }
    ]
    
    for role_def in role_definitions:
        existing_role = await db.roles.find_one(
            {'name': role_def['name']},
            {'_id': 0}
        )
        
        if existing_role:
            print(f"   ✓ Role already exists: {role_def['name']}")
        else:
            role = Role(
                name=role_def['name'],
                description=role_def['description'],
                permissions=role_def['permissions']
            )
            
            role_doc = role.model_dump()
            role_doc['created_at'] = role_doc['created_at'].isoformat()
            
            await db.roles.insert_one(role_doc)
            
            print(f"   ✓ Created role: {role_def['name']}")
    
    # ============ CREATE INDEXES ============
    print("\n📊 Creating database indexes...")
    
    # User indexes
    await db.users.create_index('email', unique=True)
    await db.users.create_index('user_id', unique=True)
    print("   ✓ User indexes created")
    
    # Community indexes
    await db.communities.create_index('slug', unique=True)
    await db.communities.create_index('community_id', unique=True)
    await db.communities.create_index('status')
    print("   ✓ Community indexes created")
    
    # Membership indexes
    await db.community_memberships.create_index(
        [('user_id', 1), ('community_id', 1)],
        unique=True
    )
    await db.community_memberships.create_index('user_id')
    await db.community_memberships.create_index('community_id')
    print("   ✓ Membership indexes created")
    
    # Session indexes
    await db.user_sessions.create_index('session_token', unique=True)
    await db.user_sessions.create_index('user_id')
    await db.user_sessions.create_index('expires_at')
    print("   ✓ Session indexes created")
    
    # Role indexes
    await db.roles.create_index('name', unique=True)
    print("   ✓ Role indexes created")
    
    # Join request indexes
    await db.join_requests.create_index('request_id', unique=True)
    await db.join_requests.create_index([('user_id', 1), ('community_id', 1)])
    await db.join_requests.create_index('status')
    print("   ✓ Join request indexes created")
    
    # Discussion indexes
    await db.discussion_categories.create_index('category_id', unique=True)
    await db.discussion_categories.create_index('community_id')
    await db.discussion_threads.create_index('thread_id', unique=True)
    await db.discussion_threads.create_index('community_id')
    await db.discussion_threads.create_index('category_id')
    await db.discussion_threads.create_index([('is_pinned', -1), ('last_activity_at', -1)])
    await db.posts.create_index('post_id', unique=True)
    await db.posts.create_index('thread_id')
    await db.posts.create_index('community_id')
    print("   ✓ Discussion indexes created")
    
    # Event indexes
    await db.events.create_index('event_id', unique=True)
    await db.events.create_index('community_id')
    await db.events.create_index([('community_id', 1), ('event_date', 1)])
    await db.events.create_index('status')
    await db.event_media.create_index('media_id', unique=True)
    await db.event_media.create_index('event_id')
    await db.event_media.create_index('community_id')
    print("   ✓ Event indexes created")
    
    # Notification indexes
    await db.notification_templates.create_index('template_id', unique=True)
    await db.notification_templates.create_index([('notification_type', 1), ('channel', 1)], unique=True)
    await db.community_template_overrides.create_index('override_id', unique=True)
    await db.community_template_overrides.create_index([('template_id', 1), ('community_id', 1)], unique=True)
    await db.notification_logs.create_index('log_id', unique=True)
    await db.notification_logs.create_index('community_id')
    await db.notification_logs.create_index([('created_at', -1)])
    await db.notification_logs.create_index([('notification_type', 1), ('status', 1)])
    print("   ✓ Notification indexes created")
    
    # SEO indexes
    await db.seo_metadata.create_index('seo_id', unique=True)
    await db.seo_metadata.create_index([('entity_type', 1), ('entity_id', 1), ('community_id', 1)], unique=True)
    await db.slug_redirects.create_index('redirect_id', unique=True)
    await db.slug_redirects.create_index([('old_slug', 1), ('entity_type', 1)])
    print("   ✓ SEO indexes created")
    
    # Subscription indexes
    await db.plans.create_index('plan_id', unique=True)
    await db.subscriptions.create_index('subscription_id', unique=True)
    await db.subscriptions.create_index('community_id')
    await db.subscriptions.create_index([('community_id', 1), ('status', 1)])
    await db.billing_audit_logs.create_index('audit_id', unique=True)
    await db.billing_audit_logs.create_index('subscription_id')
    await db.billing_audit_logs.create_index([('created_at', -1)])
    print("   ✓ Subscription indexes created")
    
    # ============ SEED DEFAULT NOTIFICATION TEMPLATES ============
    print("\n📧 Seeding default notification templates...")
    
    default_templates = [
        {
            'notification_type': 'welcome_member',
            'channel': 'email',
            'name': 'Welcome Email',
            'subject': 'Welcome to {{community_name}}!',
            'body': 'Hi {{user_name}},\n\nYour request to join {{community_name}} has been approved. Welcome aboard!\n\nFeel free to introduce yourself and explore the community discussions and events.\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name'],
        },
        {
            'notification_type': 'post_approved',
            'channel': 'email',
            'name': 'Post Approved',
            'subject': 'Your post in {{community_name}} has been approved',
            'body': 'Hi {{user_name}},\n\nYour discussion thread "{{thread_title}}" in {{community_name}} has been approved and is now visible to all members.\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name', 'thread_title'],
        },
        {
            'notification_type': 'post_rejected',
            'channel': 'email',
            'name': 'Post Rejected',
            'subject': 'Your post in {{community_name}} was not approved',
            'body': 'Hi {{user_name}},\n\nYour discussion thread "{{thread_title}}" in {{community_name}} was not approved by a moderator. Please review our community guidelines and feel free to resubmit.\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name', 'thread_title'],
        },
        {
            'notification_type': 'member_banned',
            'channel': 'email',
            'name': 'Member Banned',
            'subject': 'You have been removed from {{community_name}}',
            'body': 'Hi {{user_name}},\n\nYou have been banned from {{community_name}}. If you believe this was a mistake, please contact the community administrators.\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name'],
        },
        {
            'notification_type': 'discussion_reply',
            'channel': 'email',
            'name': 'Discussion Reply',
            'subject': 'New reply to "{{thread_title}}" in {{community_name}}',
            'body': 'Hi {{user_name}},\n\n{{reply_author}} replied to your discussion "{{thread_title}}" in {{community_name}}:\n\n"{{reply_preview}}"\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name', 'thread_title', 'reply_author', 'reply_preview'],
        },
        {
            'notification_type': 'new_event',
            'channel': 'email',
            'name': 'New Event (Email)',
            'subject': 'New event in {{community_name}}: {{event_title}}',
            'body': 'Hi {{user_name}},\n\nA new event has been announced in {{community_name}}!\n\n{{event_title}}\nDate: {{event_date}} {{event_time}}\nVenue: {{event_venue}}\n\n{{event_description}}\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['user_name', 'community_name', 'event_title', 'event_date', 'event_time', 'event_venue', 'event_description'],
        },
        {
            'notification_type': 'new_event',
            'channel': 'whatsapp',
            'name': 'New Event (WhatsApp)',
            'subject': None,
            'body': '*New event in {{community_name}}*\n\n*{{event_title}}*\nDate: {{event_date}} {{event_time}}\nVenue: {{event_venue}}\n\n{{event_description}}',
            'placeholders': ['community_name', 'event_title', 'event_date', 'event_time', 'event_venue', 'event_description'],
        },
        {
            'notification_type': 'join_request_received',
            'channel': 'email',
            'name': 'Join Request Received',
            'subject': 'New join request for {{community_name}}',
            'body': 'Hi {{manager_name}},\n\n{{user_name}} ({{user_email}}) has requested to join {{community_name}}.\n\nPlease review the request in your community dashboard.\n\nBest,\nThe {{community_name}} Team',
            'placeholders': ['manager_name', 'community_name', 'user_name', 'user_email'],
        },
    ]

    from notification_models import NotificationTemplate
    for tmpl_data in default_templates:
        existing = await db.notification_templates.find_one({
            'notification_type': tmpl_data['notification_type'],
            'channel': tmpl_data['channel'],
        })
        if not existing:
            tmpl = NotificationTemplate(**tmpl_data, created_by='system')
            doc = tmpl.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.notification_templates.insert_one(doc)
    
    template_count = await db.notification_templates.count_documents({})
    print(f"   ✓ {template_count} notification templates seeded")
    
    # ============ DATA MIGRATION ============
    print("\n🔧 Running data migrations...")
    
    # Ensure all communities have privacy and status fields
    await db.communities.update_many(
        {'privacy': {'$exists': False}},
        {'$set': {'privacy': 'public'}}
    )
    await db.communities.update_many(
        {'status': {'$exists': False}},
        {'$set': {'status': 'active'}}
    )
    print("   ✓ Community field defaults applied")
    
    print("\n✨ Database seeding completed successfully!")
    print("\n🔑 Super Admin Credentials:")
    print(f"   Email: {super_admin_email}")
    print(f"   Password: {super_admin_password}")
    print("\n⚠️  Please change the super admin password after first login!\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
