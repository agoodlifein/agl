from fastapi import HTTPException, Cookie, Header
from typing import Optional, Annotated
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import bcrypt
import jwt
import os
import httpx

from models import User, UserSession, SessionData


# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7


# ============ PASSWORD HASHING ============

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ============ JWT TOKEN HANDLING ============

def create_jwt_token(user_id: str, email: str) -> str:
    """Create JWT token for user"""
    expiration = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============ SESSION MANAGEMENT ============

async def create_session(db: AsyncIOMotorDatabase, user_id: str, session_token: str) -> UserSession:
    """Create user session in database"""
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    session_doc = session.model_dump()
    session_doc['expires_at'] = session_doc['expires_at'].isoformat()
    session_doc['created_at'] = session_doc['created_at'].isoformat()
    
    await db.user_sessions.insert_one(session_doc)
    return session


async def get_session_by_token(db: AsyncIOMotorDatabase, session_token: str) -> Optional[dict]:
    """Get session by token"""
    session_doc = await db.user_sessions.find_one(
        {'session_token': session_token},
        {'_id': 0}
    )
    
    if not session_doc:
        return None
    
    # Check expiration
    expires_at = session_doc['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        # Session expired
        await db.user_sessions.delete_one({'session_token': session_token})
        return None
    
    return session_doc


async def delete_session(db: AsyncIOMotorDatabase, session_token: str):
    """Delete session (logout)"""
    await db.user_sessions.delete_one({'session_token': session_token})


# ============ GOOGLE OAUTH (EMERGENT) ============

async def exchange_session_id(session_id: str) -> SessionData:
    """Exchange session_id for user data from Emergent Auth"""
    url = 'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data'
    headers = {'X-Session-ID': session_id}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid session ID from OAuth provider"
            )
        
        data = response.json()
        return SessionData(**data)


# ============ AUTHENTICATOR DEPENDENCY ============

async def get_current_user(
    db: AsyncIOMotorDatabase,
    session_token: Annotated[Optional[str], Cookie()] = None,
    authorization: Annotated[Optional[str], Header()] = None
) -> User:
    """Get current authenticated user from session token or JWT
    
    Checks session_token cookie first, then Authorization header as fallback.
    IMPORTANT: Don't use FastAPI's HTTPAuthorizationCredentials - it breaks cookie auth.
    """
    
    # Try session_token cookie first (from Google OAuth)
    if session_token:
        session = await get_session_by_token(db, session_token)
        if session:
            user_doc = await db.users.find_one(
                {'user_id': session['user_id']},
                {'_id': 0}
            )
            if user_doc:
                # Convert datetime strings
                if isinstance(user_doc.get('created_at'), str):
                    user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
                if isinstance(user_doc.get('updated_at'), str):
                    user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
                return User(**user_doc)
    
    # Try Authorization header (JWT from email/password login)
    if authorization:
        try:
            # Extract token from "Bearer <token>"
            scheme, token = authorization.split()
            if scheme.lower() != 'bearer':
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            
            payload = decode_jwt_token(token)
            user_doc = await db.users.find_one(
                {'user_id': payload['user_id']},
                {'_id': 0}
            )
            
            if user_doc:
                # Convert datetime strings
                if isinstance(user_doc.get('created_at'), str):
                    user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
                if isinstance(user_doc.get('updated_at'), str):
                    user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
                return User(**user_doc)
        except ValueError:
            pass  # Invalid header format
    
    raise HTTPException(status_code=401, detail="Not authenticated")


async def require_super_admin(user: User) -> User:
    """Require user to be super admin"""
    if not user.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required"
        )
    return user
