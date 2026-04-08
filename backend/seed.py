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
    
    print("\n✨ Database seeding completed successfully!")
    print("\n🔑 Super Admin Credentials:")
    print(f"   Email: {super_admin_email}")
    print(f"   Password: {super_admin_password}")
    print("\n⚠️  Please change the super admin password after first login!\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
