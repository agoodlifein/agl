from fastapi import APIRouter, HTTPException, Depends, Cookie, Header, UploadFile, File
from fastapi.responses import FileResponse
from typing import Annotated, List
from datetime import datetime, timezone, date
import os
import shutil
from pathlib import Path

from event_models import (
    EventCreate, EventUpdate, EventResponse, MediaResponse
)
from models import User
from auth import get_current_user
from permissions import get_user_role_in_community


# Media storage configuration
MEDIA_ROOT = Path("/app/media/events")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGES_PER_EVENT = 10
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png"]


def create_event_router(db):
    """Create event router for public event access"""
    router = APIRouter(prefix="/communities/{slug}", tags=["events"])
    
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)

    @router.get("/events", response_model=List[EventResponse])
    async def list_events(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)],
        upcoming_only: bool = True
    ):
        """List published events in community"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        query = {
            'community_id': community['community_id'],
            'status': 'published'
        }
        
        if upcoming_only:
            query['event_date'] = {'$gte': date.today().isoformat()}
        
        events = await db.events.find(query, {'_id': 0}).sort('event_date', 1).to_list(100)
        
        result = []
        for event in events:
            creator = await db.users.find_one({'user_id': event['created_by']}, {'_id': 0})
            
            # Get media
            media = await db.event_media.find(
                {'event_id': event['event_id']},
                {'_id': 0}
            ).to_list(100)
            
            # Convert date strings
            if isinstance(event.get('event_date'), str):
                event['event_date'] = date.fromisoformat(event['event_date'])
            if isinstance(event.get('created_at'), str):
                event['created_at'] = datetime.fromisoformat(event['created_at'])
            if isinstance(event.get('updated_at'), str):
                event['updated_at'] = datetime.fromisoformat(event['updated_at'])
            if event.get('event_time') and isinstance(event['event_time'], str):
                from datetime import time as dt_time
                event['event_time'] = dt_time.fromisoformat(event['event_time'])
            
            media_urls = [f"/api/media/events/{m['file_path']}" for m in media]
            
            result.append(EventResponse(
                **event,
                creator_name=creator['name'] if creator else 'Unknown',
                media_count=len(media),
                media_urls=media_urls
            ))
        
        return result

    @router.get("/events/{event_id}", response_model=EventResponse)
    async def get_event(
        slug: str,
        event_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Get event details"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        event = await db.events.find_one(
            {'event_id': event_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Only show published events to regular members
        if event['status'] != 'published':
            role = await get_user_role_in_community(db, current_user.user_id, community['community_id'])
            if role not in ['community_manager', 'moderator'] and not current_user.is_super_admin:
                raise HTTPException(status_code=404, detail="Event not found")
        
        creator = await db.users.find_one({'user_id': event['created_by']}, {'_id': 0})
        
        # Get media
        media = await db.event_media.find(
            {'event_id': event_id},
            {'_id': 0}
        ).to_list(100)
        
        # Convert date strings
        if isinstance(event.get('event_date'), str):
            event['event_date'] = date.fromisoformat(event['event_date'])
        if isinstance(event.get('created_at'), str):
            event['created_at'] = datetime.fromisoformat(event['created_at'])
        if isinstance(event.get('updated_at'), str):
            event['updated_at'] = datetime.fromisoformat(event['updated_at'])
        if event.get('event_time') and isinstance(event['event_time'], str):
            from datetime import time as dt_time
            event['event_time'] = dt_time.fromisoformat(event['event_time'])
        
        media_urls = [f"/api/media/events/{m['file_path']}" for m in media]
        
        return EventResponse(
            **event,
            creator_name=creator['name'] if creator else 'Unknown',
            media_count=len(media),
            media_urls=media_urls
        )

    return router


def create_event_management_router(db):
    """Create event management router for managers"""
    router = APIRouter(prefix="/manager/communities/{slug}", tags=["event-management"])
    
    async def get_user_dep(
        session_token: Annotated[str | None, Cookie()] = None,
        authorization: Annotated[str | None, Header()] = None
    ):
        return await get_current_user(db, session_token, authorization)
    
    async def require_manager(current_user: User, community_id: str):
        """Require manager role"""
        if current_user.is_super_admin:
            return True
        
        role = await get_user_role_in_community(db, current_user.user_id, community_id)
        if role != 'community_manager':
            raise HTTPException(
                status_code=403,
                detail="Community manager access required"
            )
        return True

    @router.post("/events", response_model=EventResponse)
    async def create_event(
        slug: str,
        event_data: EventCreate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Create event"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        from event_models import Event
        event = Event(
            community_id=community['community_id'],
            created_by=current_user.user_id,
            title=event_data.title,
            description=event_data.description,
            event_date=event_data.event_date,
            event_time=event_data.event_time,
            venue=event_data.venue,
            details=event_data.details,
            status=event_data.status or 'published'
        )
        
        event_doc = event.model_dump()
        event_doc['event_date'] = event_doc['event_date'].isoformat()
        if event_doc.get('event_time'):
            event_doc['event_time'] = event_doc['event_time'].isoformat()
        event_doc['created_at'] = event_doc['created_at'].isoformat()
        event_doc['updated_at'] = event_doc['updated_at'].isoformat()
        
        await db.events.insert_one(event_doc)
        event_doc.pop('_id', None)
        
        # Convert back for response
        event_doc['event_date'] = date.fromisoformat(event_doc['event_date'])
        if event_doc.get('event_time'):
            from datetime import time as dt_time
            event_doc['event_time'] = dt_time.fromisoformat(event_doc['event_time'])
        event_doc['created_at'] = datetime.fromisoformat(event_doc['created_at'])
        event_doc['updated_at'] = datetime.fromisoformat(event_doc['updated_at'])
        
        return EventResponse(
            **event_doc,
            creator_name=current_user.name,
            media_count=0,
            media_urls=[]
        )

    @router.get("/events", response_model=List[EventResponse])
    async def list_all_events(
        slug: str,
        current_user: Annotated[User, Depends(get_user_dep)],
        status: str = None
    ):
        """List all events (including drafts) for manager"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        query = {'community_id': community['community_id']}
        if status:
            query['status'] = status
        
        events = await db.events.find(query, {'_id': 0}).sort('event_date', 1).to_list(100)
        
        result = []
        for event in events:
            creator = await db.users.find_one({'user_id': event['created_by']}, {'_id': 0})
            
            media = await db.event_media.find(
                {'event_id': event['event_id']},
                {'_id': 0}
            ).to_list(100)
            
            # Convert dates
            if isinstance(event.get('event_date'), str):
                event['event_date'] = date.fromisoformat(event['event_date'])
            if isinstance(event.get('created_at'), str):
                event['created_at'] = datetime.fromisoformat(event['created_at'])
            if isinstance(event.get('updated_at'), str):
                event['updated_at'] = datetime.fromisoformat(event['updated_at'])
            if event.get('event_time') and isinstance(event['event_time'], str):
                from datetime import time as dt_time
                event['event_time'] = dt_time.fromisoformat(event['event_time'])
            
            media_urls = [f"/api/media/events/{m['file_path']}" for m in media]
            
            result.append(EventResponse(
                **event,
                creator_name=creator['name'] if creator else 'Unknown',
                media_count=len(media),
                media_urls=media_urls
            ))
        
        return result

    @router.patch("/events/{event_id}", response_model=EventResponse)
    async def update_event(
        slug: str,
        event_id: str,
        update_data: EventUpdate,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Update event"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        event = await db.events.find_one(
            {'event_id': event_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Convert date/time to strings
        if 'event_date' in update_dict:
            update_dict['event_date'] = update_dict['event_date'].isoformat()
        if 'event_time' in update_dict and update_dict['event_time']:
            update_dict['event_time'] = update_dict['event_time'].isoformat()
        
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.events.update_one(
            {'event_id': event_id},
            {'$set': update_dict}
        )
        
        updated = await db.events.find_one({'event_id': event_id}, {'_id': 0})
        creator = await db.users.find_one({'user_id': updated['created_by']}, {'_id': 0})
        
        media = await db.event_media.find(
            {'event_id': event_id},
            {'_id': 0}
        ).to_list(100)
        
        # Convert back
        if isinstance(updated.get('event_date'), str):
            updated['event_date'] = date.fromisoformat(updated['event_date'])
        if isinstance(updated.get('created_at'), str):
            updated['created_at'] = datetime.fromisoformat(updated['created_at'])
        if isinstance(updated.get('updated_at'), str):
            updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
        if updated.get('event_time') and isinstance(updated['event_time'], str):
            from datetime import time as dt_time
            updated['event_time'] = dt_time.fromisoformat(updated['event_time'])
        
        media_urls = [f"/api/media/events/{m['file_path']}" for m in media]
        
        return EventResponse(
            **updated,
            creator_name=creator['name'] if creator else 'Unknown',
            media_count=len(media),
            media_urls=media_urls
        )

    @router.delete("/events/{event_id}")
    async def delete_event(
        slug: str,
        event_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Delete event and all associated media"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        event = await db.events.find_one(
            {'event_id': event_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get all media files
        media_files = await db.event_media.find(
            {'event_id': event_id},
            {'_id': 0}
        ).to_list(100)
        
        # Delete physical files
        event_dir = MEDIA_ROOT / community['community_id'] / event_id
        if event_dir.exists():
            shutil.rmtree(event_dir)
        
        # Delete media records
        await db.event_media.delete_many({'event_id': event_id})
        
        # Delete event
        await db.events.delete_one({'event_id': event_id})
        
        return {
            "message": "Event deleted successfully",
            "media_files_deleted": len(media_files)
        }

    @router.post("/events/{event_id}/upload-media", response_model=MediaResponse)
    async def upload_event_media(
        slug: str,
        event_id: str,
        current_user: Annotated[User, Depends(get_user_dep)],
        file: UploadFile = File(...)
    ):
        """Upload event media"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        event = await db.events.find_one(
            {'event_id': event_id, 'community_id': community['community_id']},
            {'_id': 0}
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check media count
        media_count = await db.event_media.count_documents({'event_id': event_id})
        if media_count >= MAX_IMAGES_PER_EVENT:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_IMAGES_PER_EVENT} images per event"
            )
        
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: JPG, PNG. Got: {file.content_type}"
            )
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max: 5MB. Your file: {file_size / (1024*1024):.1f}MB"
            )
        
        # Create directory structure
        event_dir = MEDIA_ROOT / community['community_id'] / event_id
        event_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex[:12]}_{file.filename}"
        file_path = event_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Store in database
        from event_models import EventMedia
        relative_path = f"{community['community_id']}/{event_id}/{unique_filename}"
        
        media = EventMedia(
            event_id=event_id,
            community_id=community['community_id'],
            file_path=relative_path,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            uploaded_by=current_user.user_id
        )
        
        media_doc = media.model_dump()
        media_doc['uploaded_at'] = media_doc['uploaded_at'].isoformat()
        
        await db.event_media.insert_one(media_doc)
        media_doc.pop('_id', None)
        
        return MediaResponse(
            media_id=media.media_id,
            event_id=event_id,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            url=f"/api/media/events/{relative_path}",
            uploaded_at=media.uploaded_at
        )

    @router.delete("/events/{event_id}/media/{media_id}")
    async def delete_event_media(
        slug: str,
        event_id: str,
        media_id: str,
        current_user: Annotated[User, Depends(get_user_dep)]
    ):
        """Delete event media"""
        community = await db.communities.find_one({'slug': slug}, {'_id': 0})
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        await require_manager(current_user, community['community_id'])
        
        media = await db.event_media.find_one(
            {'media_id': media_id, 'event_id': event_id},
            {'_id': 0}
        )
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Delete physical file
        file_path = MEDIA_ROOT / media['file_path']
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        await db.event_media.delete_one({'media_id': media_id})
        
        return {"message": "Media deleted successfully"}

    return router
