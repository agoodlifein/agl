from fastapi import APIRouter, HTTPException, Response, Cookie, Depends, Header
from typing import Annotated
from datetime import datetime, timezone

from models import (
    UserCreate, UserLogin, UserResponse, AuthResponse,
    SessionData
)
from auth import (
    hash_password, verify_password, create_jwt_token,
    exchange_session_id, create_session, delete_session,
    get_current_user
)
from models import User


def create_auth_router(db):
    """Create authentication router with database dependency"""
    router = APIRouter(prefix="/auth", tags=["authentication"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.post("/register", response_model=AuthResponse)
    async def register(user_data: UserCreate):
        """Register new user with email/password"""
        # Check if user exists
        existing_user = await db.users.find_one(
            {'email': user_data.email},
            {'_id': 0}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hash_password(user_data.password),
            is_super_admin=False
        )
        
        user_doc = user.model_dump()
        user_doc['created_at'] = user_doc['created_at'].isoformat()
        user_doc['updated_at'] = user_doc['updated_at'].isoformat()
        
        await db.users.insert_one(user_doc)
        
        # Generate JWT token
        token = create_jwt_token(user.user_id, user.email)
        
        return AuthResponse(
            user=UserResponse(**user.model_dump()),
            token=token
        )

    @router.post("/login", response_model=AuthResponse)
    async def login(credentials: UserLogin):
        """Login with email/password"""
        # Find user
        user_doc = await db.users.find_one(
            {'email': credentials.email},
            {'_id': 0}
        )
        
        if not user_doc:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not user_doc.get('password_hash'):
            raise HTTPException(
                status_code=401,
                detail="This account uses Google OAuth. Please login with Google."
            )
        
        if not verify_password(credentials.password, user_doc['password_hash']):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Convert datetime strings
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        if isinstance(user_doc.get('updated_at'), str):
            user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
        
        user = User(**user_doc)
        
        # Generate JWT token
        token = create_jwt_token(user.user_id, user.email)
        
        return AuthResponse(
            user=UserResponse(**user.model_dump()),
            token=token
        )

    @router.post("/session")
    async def create_session_from_oauth(session_id: str, response: Response):
        """Exchange session_id from Google OAuth for session token
        
        This is called by frontend after OAuth redirect with session_id in URL fragment.
        """
        # Exchange session_id with Emergent Auth
        session_data: SessionData = await exchange_session_id(session_id)
        
        # Find or create user
        user_doc = await db.users.find_one(
            {'email': session_data.email},
            {'_id': 0}
        )
        
        if user_doc:
            # Update existing user
            user_id = user_doc['user_id']
            await db.users.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'name': session_data.name,
                        'picture': session_data.picture,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Convert datetime strings for response
            if isinstance(user_doc.get('created_at'), str):
                user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
            if isinstance(user_doc.get('updated_at'), str):
                user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
        else:
            # Create new user
            user = User(
                email=session_data.email,
                name=session_data.name,
                picture=session_data.picture,
                is_super_admin=False
            )
            
            user_doc = user.model_dump()
            user_doc['created_at'] = user_doc['created_at'].isoformat()
            user_doc['updated_at'] = user_doc['updated_at'].isoformat()
            
            await db.users.insert_one(user_doc)
            
            user_id = user.user_id
            user_doc = user.model_dump()
        
        # Create session
        await create_session(db, user_id, session_data.session_token)
        
        # Set httpOnly cookie
        # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
        response.set_cookie(
            key="session_token",
            value=session_data.session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return UserResponse(**user_doc)

    @router.get("/me", response_model=UserResponse)
    async def get_current_user_info(
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get current authenticated user info"""
        return UserResponse(**current_user.model_dump())

    @router.post("/logout")
    async def logout(
        response: Response,
        session_token: Annotated[str | None, Cookie()] = None
    ):
        """Logout user and clear session"""
        if session_token:
            await delete_session(db, session_token)
        
        # Clear cookie
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=True,
            samesite="none"
        )
        
        return {"message": "Logged out successfully"}

    return router
