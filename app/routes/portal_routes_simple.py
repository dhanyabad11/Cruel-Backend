from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.portal import Portal
from app.schemas.portal import PortalCreate, PortalUpdate, PortalResponse

router = APIRouter()

@router.get("/", response_model=List[PortalResponse])
async def get_portals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    portal_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all portals"""
    query = db.query(Portal)
    
    # Apply filters
    if portal_type:
        query = query.filter(Portal.portal_type == portal_type)
    if is_active is not None:
        query = query.filter(Portal.is_active == is_active)
    
    portals = query.offset(skip).limit(limit).all()
    return portals

@router.post("/", response_model=PortalResponse, status_code=status.HTTP_201_CREATED)
async def create_portal(
    portal: PortalCreate,
    db: Session = Depends(get_db)
):
    """Create a new portal"""
    db_portal = Portal(
        **portal.dict(),
        user_id=1  # Default user for testing
    )
    db.add(db_portal)
    db.commit()
    db.refresh(db_portal)
    return db_portal

@router.get("/{portal_id}", response_model=PortalResponse)
async def get_portal(
    portal_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific portal by ID"""
    portal = db.query(Portal).filter(Portal.id == portal_id).first()
    if portal is None:
        raise HTTPException(status_code=404, detail="Portal not found")
    return portal

@router.put("/{portal_id}", response_model=PortalResponse)
async def update_portal(
    portal_id: int,
    portal_update: PortalUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific portal"""
    portal = db.query(Portal).filter(Portal.id == portal_id).first()
    if portal is None:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    update_data = portal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(portal, field, value)
    
    db.commit()
    db.refresh(portal)
    return portal

@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portal(
    portal_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific portal"""
    portal = db.query(Portal).filter(Portal.id == portal_id).first()
    if portal is None:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    db.delete(portal)
    db.commit()