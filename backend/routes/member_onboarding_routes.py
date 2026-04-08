from fastapi import APIRouter, HTTPException, Depends, Cookie, Header
from typing import Annotated, List
from datetime import datetime, timezone

from models import (
    User, JoinRequest, JoinRequestCreate, JoinRequestResponse,
    MembershipStatusResponse, MembershipResponse, CommunityMembership
)
from auth import get_current_user
from permissions import get_user_role_in_community


def create_member_onboarding_router(db):
    """Create member onboarding router with database dependency"""
    router = APIRouter(prefix="/communities/{slug}", tags=["member-onboarding"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.get("/membership-status", response_model=MembershipStatusResponse)
    async def get_membership_status(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Check current user's membership status in community"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check membership
        membership = await db.community_memberships.find_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        is_member = bool(membership and membership.get('is_active'))
        is_banned = bool(membership and not membership.get('is_active') and membership.get('banned_at'))
        role = membership.get('role_name') if is_member else None
        
        # Check pending join request
        pending_request = await db.join_requests.find_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id'],
                'status': 'pending'
            },
            {'_id': 0}
        )
        
        has_pending_request = bool(pending_request)
        
        # Can join immediately only if public
        community_privacy = community.get('privacy', 'public')  # Default to public for older communities
        can_join = community_privacy == 'public' or is_member
        
        return MembershipStatusResponse(
            is_member=is_member,
            role=role,
            has_pending_request=has_pending_request,
            is_banned=is_banned,
            can_join=can_join
        )

    @router.post("/request-join")
    async def request_join_community(
        slug: str,
        request_data: JoinRequestCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Request to join community (instant for public, pending for private)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if community is active
        if community.get('status') != 'active':
            raise HTTPException(
                status_code=400,
                detail="This community is not currently accepting new members"
            )
        
        # Check if already a member
        existing_membership = await db.community_memberships.find_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if existing_membership:
            if existing_membership.get('is_active'):
                raise HTTPException(
                    status_code=400,
                    detail="You are already a member of this community"
                )
            elif existing_membership.get('banned_at'):
                raise HTTPException(
                    status_code=403,
                    detail="You have been banned from this community"
                )
        
        # Check if there's already a pending request
        existing_request = await db.join_requests.find_one(
            {
                'user_id': current_user.user_id,
                'community_id': community['community_id'],
                'status': 'pending'
            },
            {'_id': 0}
        )
        
        if existing_request:
            raise HTTPException(
                status_code=400,
                detail="You already have a pending join request for this community"
            )
        
        # Handle based on privacy
        community_privacy = community.get('privacy', 'public')  # Default to public for older communities
        if community_privacy == 'public':
            # Instant join for public communities
            membership = CommunityMembership(
                user_id=current_user.user_id,
                community_id=community['community_id'],
                role_name='member'
            )
            
            membership_doc = membership.model_dump()
            membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
            
            await db.community_memberships.insert_one(membership_doc)
            
            return {
                "message": "Joined community successfully",
                "community": community['name'],
                "instant": True
            }
        else:
            # Create join request for private communities
            join_request = JoinRequest(
                user_id=current_user.user_id,
                community_id=community['community_id'],
                message=request_data.message
            )
            
            request_doc = join_request.model_dump()
            request_doc['requested_at'] = request_doc['requested_at'].isoformat()
            
            await db.join_requests.insert_one(request_doc)
            
            return {
                "message": "Join request submitted successfully",
                "community": community['name'],
                "instant": False,
                "status": "pending"
            }

    return router


def create_join_request_management_router(db):
    """Create join request management router for managers/admins"""
    router = APIRouter(prefix="/manager/communities/{slug}", tags=["join-request-management"])
    
    # Create dependency that captures db
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)
    
    async def require_community_manager(
        current_user: User,
        community_id: str
    ):
        """Ensure user is a manager of the specific community"""
        if current_user.is_super_admin:
            return True
        
        role = await get_user_role_in_community(db, current_user.user_id, community_id)
        
        if role != 'community_manager':
            raise HTTPException(
                status_code=403,
                detail="Community manager access required for this community"
            )
        return True

    @router.get("/join-requests", response_model=List[JoinRequestResponse])
    async def list_join_requests(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)],
        status: str = "pending"
    ):
        """List join requests for community (pending by default)"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Get join requests
        requests = await db.join_requests.find(
            {
                'community_id': community['community_id'],
                'status': status
            },
            {'_id': 0}
        ).to_list(1000)
        
        # Enrich with user details
        result = []
        for request in requests:
            user = await db.users.find_one(
                {'user_id': request['user_id']},
                {'_id': 0}
            )
            
            if user:
                if isinstance(request['requested_at'], str):
                    request['requested_at'] = datetime.fromisoformat(request['requested_at'])
                if request.get('reviewed_at') and isinstance(request['reviewed_at'], str):
                    request['reviewed_at'] = datetime.fromisoformat(request['reviewed_at'])
                
                result.append(JoinRequestResponse(
                    **request,
                    user_name=user['name'],
                    user_email=user['email']
                ))
        
        return result

    @router.post("/join-requests/{request_id}/approve")
    async def approve_join_request(
        slug: str,
        request_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Approve join request and create membership"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Get join request
        join_request = await db.join_requests.find_one(
            {
                'request_id': request_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if not join_request:
            raise HTTPException(status_code=404, detail="Join request not found")
        
        if join_request['status'] != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Request already {join_request['status']}"
            )
        
        # Create membership
        membership = CommunityMembership(
            user_id=join_request['user_id'],
            community_id=community['community_id'],
            role_name='member'
        )
        
        membership_doc = membership.model_dump()
        membership_doc['joined_at'] = membership_doc['joined_at'].isoformat()
        
        await db.community_memberships.insert_one(membership_doc)
        
        # Update join request
        await db.join_requests.update_one(
            {'request_id': request_id},
            {
                '$set': {
                    'status': 'approved',
                    'reviewed_at': datetime.now(timezone.utc).isoformat(),
                    'reviewed_by': current_user.user_id
                }
            }
        )
        
        return {
            "message": "Join request approved successfully",
            "request_id": request_id
        }

    @router.post("/join-requests/{request_id}/reject")
    async def reject_join_request(
        slug: str,
        request_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Reject join request"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Get join request
        join_request = await db.join_requests.find_one(
            {
                'request_id': request_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if not join_request:
            raise HTTPException(status_code=404, detail="Join request not found")
        
        if join_request['status'] != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Request already {join_request['status']}"
            )
        
        # Update join request
        await db.join_requests.update_one(
            {'request_id': request_id},
            {
                '$set': {
                    'status': 'rejected',
                    'reviewed_at': datetime.now(timezone.utc).isoformat(),
                    'reviewed_by': current_user.user_id
                }
            }
        )
        
        return {
            "message": "Join request rejected successfully",
            "request_id": request_id
        }

    @router.post("/members/{user_id}/ban")
    async def ban_member(
        slug: str,
        user_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Ban member from community"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Get membership
        membership = await db.community_memberships.find_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if not membership:
            raise HTTPException(status_code=404, detail="User is not a member of this community")
        
        if not membership.get('is_active'):
            raise HTTPException(status_code=400, detail="User is already banned or inactive")
        
        # Ban member
        await db.community_memberships.update_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {
                '$set': {
                    'is_active': False,
                    'banned_at': datetime.now(timezone.utc).isoformat(),
                    'banned_by': current_user.user_id
                }
            }
        )
        
        return {
            "message": "Member banned successfully",
            "user_id": user_id
        }

    @router.post("/members/{user_id}/restore")
    async def restore_member(
        slug: str,
        user_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Restore banned member"""
        # Get community
        community = await db.communities.find_one(
            {'slug': slug},
            {'_id': 0}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is manager
        await require_community_manager(current_user, community['community_id'])
        
        # Get membership
        membership = await db.community_memberships.find_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {'_id': 0}
        )
        
        if not membership:
            raise HTTPException(status_code=404, detail="User is not a member of this community")
        
        if membership.get('is_active'):
            raise HTTPException(status_code=400, detail="User is already active")
        
        # Restore member
        await db.community_memberships.update_one(
            {
                'user_id': user_id,
                'community_id': community['community_id']
            },
            {
                '$set': {
                    'is_active': True
                },
                '$unset': {
                    'banned_at': '',
                    'banned_by': ''
                }
            }
        )
        
        return {
            "message": "Member restored successfully",
            "user_id": user_id
        }

    return router
