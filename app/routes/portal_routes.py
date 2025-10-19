from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime, timezone
from supabase import Client
from app.database import get_supabase_client, get_supabase_admin
from app.models.user import User
from app.schemas.portal import PortalCreate, PortalUpdate, PortalResponse, SyncResult
from app.auth_deps import get_current_user
from app.scrapers import scrape_portal, get_available_scrapers

router = APIRouter()

@router.get("/")
async def get_portals(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all portals for the current user from Supabase"""
    try:
        print(f"DEBUG: Current user in portals: {current_user}")
        # Fetch portals from Supabase
        result = supabase.table('portals').select('*').eq('user_id', current_user['id']).execute()
        portals = result.data or []
        print(f"DEBUG: Found {len(portals)} portals for user")
        return portals  # Return array directly - frontend expects this format
    except Exception as e:
        print(f"DEBUG: Error in portals endpoint: {e}")
        # Return empty array on error instead of raising exception
        return []

@router.post("/", response_model=PortalResponse, status_code=status.HTTP_201_CREATED)
async def create_portal(
    portal_data: PortalCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new portal connection in Supabase"""
    available_types = get_available_scrapers()
    if portal_data.type not in available_types and portal_data.type != "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported portal type. Available types: {', '.join(available_types)}"
        )
    insert_data = portal_data.dict()
    insert_data['user_id'] = current_user['id']
    result = supabase.table('portals').insert(insert_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create portal")
    portal = result.data[0]
    return PortalResponse(**portal)

@router.get("/{portal_id}", response_model=PortalResponse)
async def get_portal(
    portal_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific portal from Supabase"""
    result = supabase.table('portals').select('*').eq('id', portal_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    portal = result.data[0]
    return PortalResponse(**portal)

@router.put("/{portal_id}", response_model=PortalResponse)
async def update_portal(
    portal_id: int,
    portal_data: PortalUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a portal in Supabase"""
    update_data = portal_data.dict(exclude_unset=True)
    result = supabase.table('portals').update(update_data).eq('id', portal_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Portal not found or update failed")
    portal = result.data[0]
    return PortalResponse(**portal)

@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portal(
    portal_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a portal in Supabase"""
    result = supabase.table('portals').delete().eq('id', portal_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Portal not found or delete failed")

@router.post("/{portal_id}/sync", response_model=SyncResult)
async def sync_portal(
    portal_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually sync a portal to fetch deadlines"""
    from supabase import Client
    from app.database import get_supabase_client
    supabase: Client = get_supabase_client()
    # Get portal from Supabase
    result_portal = supabase.table('portals').select('*').eq('id', portal_id).eq('user_id', current_user['id']).execute()
    if not result_portal.data:
        raise HTTPException(status_code=404, detail="Portal not found")
    portal = result_portal.data[0]
    if not portal.get('is_active', True):
        raise HTTPException(status_code=400, detail="Portal is not active")
    # Perform the scraping
    try:
        # Use scraper registry to scrape
        from app.scrapers.scraper_registry import scrape_portal, ScraperRegistry
        # Create a dummy Portal object for registry (if needed)
        class DummyPortal:
            def __init__(self, portal_dict):
                for k, v in portal_dict.items():
                    setattr(self, k, v)
        portal_obj = DummyPortal(portal)
        result = await scrape_portal(portal_obj)
        # Save scraped deadlines to Supabase
        deadlines_created = 0
        deadlines_updated = 0
        from app.services.notification_service import get_notification_service, NotificationType
        notification_service = get_notification_service()
        from app.services.email_service import send_email
        for d in result.deadlines:
            # Check if deadline already exists (by portal_task_id and portal_id)
            existing = supabase.table('deadlines').select('id').eq('portal_task_id', d.portal_task_id).eq('portal_id', portal_id).execute()
            deadline_data = {
                'user_id': portal['user_id'],
                'title': d.title,
                'description': d.description,
                'deadline_date': d.due_date.isoformat(),
                'priority': d.priority,
                'portal_id': portal_id,
                'portal_task_id': d.portal_task_id,
                'portal_url': d.portal_url,
                'tags': ','.join(d.tags) if d.tags else None,
                'estimated_hours': d.estimated_hours
            }
            if existing.data:
                # Update existing deadline
                supabase.table('deadlines').update(deadline_data).eq('id', existing.data[0]['id']).execute()
                deadlines_updated += 1
            else:
                # Create new deadline
                supabase.table('deadlines').insert(deadline_data).execute()
                deadlines_created += 1
                # Trigger notification for new/urgent deadlines
                if notification_service and d.priority in ['high', 'urgent']:
                    # Fetch user phone and email from Supabase users table
                    user_result = supabase.table('users').select('phone', 'email').eq('id', portal['user_id']).execute()
                    phone = None
                    email = None
                    if user_result.data:
                        phone = user_result.data[0].get('phone')
                        email = user_result.data[0].get('email')
                    if phone:
                        await notification_service.send_deadline_reminder(
                            phone_number=phone,
                            deadline_title=d.title,
                            deadline_date=d.due_date,
                            deadline_url=d.portal_url,
                            notification_type=NotificationType.WHATSAPP if phone.startswith('whatsapp:') else NotificationType.SMS,
                            priority=d.priority
                        )
                    if email:
                        await send_email(
                            to_email=email,
                            subject=f"[AI Cruel] New {d.priority} Deadline: {d.title}",
                            body=f"A new {d.priority} deadline '{d.title}' is due on {d.due_date}.\nDetails: {d.description}\nURL: {d.portal_url}"
                        )
        # Update portal sync info in Supabase
        update_portal_data = {
            'last_sync': datetime.now(timezone.utc).isoformat(),
            'sync_status': result.status.value,
            'sync_count': portal.get('sync_count', 0) + 1,
            'last_error': '; '.join(result.errors) if result.status.value == "error" and result.errors else None
        }
        supabase.table('portals').update(update_portal_data).eq('id', portal_id).execute()
        return SyncResult(
            success=result.status.value == "success",
            message=result.message,
            deadlines_found=len(result.deadlines),
            deadlines_created=deadlines_created,
            deadlines_updated=deadlines_updated,
            errors=result.errors
        )
    except Exception as e:
        update_portal_data = {
            'last_error': str(e),
            'sync_status': 'error'
        }
        supabase.table('portals').update(update_portal_data).eq('id', portal_id).execute()
        raise HTTPException(status_code=500, detail=f"Failed to sync portal: {str(e)}")

@router.get("/types/available")
async def get_available_portal_types():
    """Get list of available portal types"""
    return {
        "available_types": get_available_scrapers(),
        "custom_supported": True
    }