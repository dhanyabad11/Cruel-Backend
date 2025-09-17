from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.portal import Portal
from app.schemas.portal import PortalCreate, PortalUpdate, PortalResponse, SyncResult
from app.utils.auth import get_current_active_user
from app.scrapers import scrape_portal, get_available_scrapers

router = APIRouter()

@router.get("/", response_model=List[PortalResponse])
async def get_portals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all portals for the current user"""
    portals = db.query(Portal).filter(Portal.user_id == current_user.id).all()
    return [PortalResponse.from_orm(portal) for portal in portals]

@router.post("/", response_model=PortalResponse, status_code=status.HTTP_201_CREATED)
async def create_portal(
    portal_data: PortalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new portal connection"""
    
    # Validate portal type
    available_types = get_available_scrapers()
    if portal_data.type not in available_types and portal_data.type != "custom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported portal type. Available types: {', '.join(available_types)}"
        )
    
    db_portal = Portal(
        user_id=current_user.id,
        **portal_data.dict()
    )
    
    db.add(db_portal)
    db.commit()
    db.refresh(db_portal)
    
    return PortalResponse.from_orm(db_portal)

@router.get("/{portal_id}", response_model=PortalResponse)
async def get_portal(
    portal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific portal"""
    portal = db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.user_id == current_user.id
    ).first()
    
    if not portal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portal not found"
        )
    
    return PortalResponse.from_orm(portal)

@router.put("/{portal_id}", response_model=PortalResponse)
async def update_portal(
    portal_id: int,
    portal_data: PortalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a portal"""
    portal = db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.user_id == current_user.id
    ).first()
    
    if not portal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portal not found"
        )
    
    # Update fields
    update_data = portal_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(portal, field, value)
    
    portal.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(portal)
    
    return PortalResponse.from_orm(portal)

@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portal(
    portal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a portal"""
    portal = db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.user_id == current_user.id
    ).first()
    
    if not portal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portal not found"
        )
    
    db.delete(portal)
    db.commit()

@router.post("/{portal_id}/sync", response_model=SyncResult)
async def sync_portal(
    portal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually sync a portal to fetch deadlines"""
    portal = db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.user_id == current_user.id
    ).first()
    
    if not portal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portal not found"
        )
    
    if not portal.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portal is not active"
        )
    
    # Perform the scraping
    try:
        result = await scrape_portal(portal)
        
        # Update portal sync information
        portal.last_sync = datetime.now(timezone.utc)
        portal.sync_status = result.status.value
        portal.sync_count += 1
        
        if result.status.value == "error":
            portal.last_error = "; ".join(result.errors) if result.errors else "Unknown error"
        else:
            portal.last_error = None
        
        # TODO: Save scraped deadlines to database
        # This will be implemented when we create deadline sync logic
        
        db.commit()
        
        return SyncResult(
            success=result.status.value == "success",
            message=result.message,
            deadlines_found=len(result.deadlines),
            deadlines_created=0,  # TODO: Implement
            deadlines_updated=0,  # TODO: Implement
            errors=result.errors
        )
        
    except Exception as e:
        portal.last_error = str(e)
        portal.sync_status = "error"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync portal: {str(e)}"
        )

@router.get("/types/available")
async def get_available_portal_types():
    """Get list of available portal types"""
    return {
        "available_types": get_available_scrapers(),
        "custom_supported": True
    }