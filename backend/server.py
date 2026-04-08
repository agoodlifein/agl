from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

# Import route creators
from routes.auth_routes import create_auth_router
from routes.community_routes import create_community_router
from routes.membership_routes import create_membership_router
from routes.profile_routes import create_profile_router, create_profiles_router
from routes.admin_community_routes import create_admin_community_router
from routes.manager_routes import create_manager_router
from routes.member_onboarding_routes import create_member_onboarding_router, create_join_request_management_router
from routes.discussion_routes import create_discussion_router
from routes.discussion_moderation_routes import create_discussion_moderation_router
from routes.event_routes import create_event_router, create_event_management_router


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="A Good Life - Community Platform API",
    description="Multi-manager community platform with role-based access control",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============ HEALTH CHECK ============
@api_router.get("/")
async def root():
    return {
        "message": "A Good Life API",
        "version": "1.0.0",
        "status": "active"
    }


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============ REGISTER ROUTE MODULES ============

# Authentication routes
auth_router = create_auth_router(db)
api_router.include_router(auth_router)

# Community routes
community_router = create_community_router(db)
api_router.include_router(community_router)

# Membership routes
membership_router = create_membership_router(db)
api_router.include_router(membership_router)

# Profile routes
profile_router = create_profile_router(db)
api_router.include_router(profile_router)

# Profiles routes (super admin)
profiles_router = create_profiles_router(db)
api_router.include_router(profiles_router)

# Admin community management routes
admin_community_router = create_admin_community_router(db)
api_router.include_router(admin_community_router)

# Community manager routes
manager_router = create_manager_router(db)
api_router.include_router(manager_router)

# Member onboarding routes
member_onboarding_router = create_member_onboarding_router(db)
api_router.include_router(member_onboarding_router)

# Join request management routes
join_request_router = create_join_request_management_router(db)
api_router.include_router(join_request_router)

# Discussion routes
discussion_router = create_discussion_router(db)
api_router.include_router(discussion_router)

# Discussion moderation routes
discussion_moderation_router = create_discussion_moderation_router(db)
api_router.include_router(discussion_moderation_router)

# Event routes
event_router = create_event_router(db)
api_router.include_router(event_router)

# Event management routes
event_management_router = create_event_management_router(db)
api_router.include_router(event_management_router)


# Include the API router in the main app
app.include_router(api_router)

# ============ STATIC FILE SERVING (MEDIA) ============
MEDIA_ROOT = Path("/app/media/events")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/api/media/events", StaticFiles(directory=str(MEDIA_ROOT)), name="event-media")


# ============ MIDDLEWARE ============

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ LOGGING ============

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============ LIFECYCLE EVENTS ============

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 A Good Life API starting up...")
    logger.info(f"📊 Connected to database: {os.environ['DB_NAME']}")
    logger.info("✅ API ready to serve requests")


@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("👋 Shutting down API...")
    client.close()
    logger.info("✅ Database connection closed")
