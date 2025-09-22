from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.deadline import Deadline, StatusLevel
from app.schemas.deadline import DeadlineCreate, DeadlineUpdate, DeadlineResponse, DeadlineStats

router = APIRouter()

@router.get("/", response_model=List[DeadlineResponse])
async def get_deadlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all deadlines"""
    query = db.query(Deadline)
    
    # Apply filters
    if status:
        query = query.filter(Deadline.status == status)
    if priority:
        query = query.filter(Deadline.priority == priority)
    
    deadlines = query.offset(skip).limit(limit).all()
    return deadlines

@router.post("/", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    deadline: DeadlineCreate,
    db: Session = Depends(get_db)
):
    """Create a new deadline"""
    # Default user_id for now
    db_deadline = Deadline(
        **deadline.dict(),
        user_id=1  # Default user for testing
    )
    db.add(db_deadline)
    db.commit()
    db.refresh(db_deadline)
    return db_deadline

@router.get("/{deadline_id}", response_model=DeadlineResponse)
async def get_deadline(
    deadline_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific deadline by ID"""
    deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if deadline is None:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline

@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(
    deadline_id: int,
    deadline_update: DeadlineUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific deadline"""
    deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if deadline is None:
        raise HTTPException(status_code=404, detail="Deadline not found")
    
    update_data = deadline_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deadline, field, value)
    
    deadline.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(deadline)
    return deadline

@router.delete("/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific deadline"""
    deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if deadline is None:
        raise HTTPException(status_code=404, detail="Deadline not found")
    
    db.delete(deadline)
    db.commit()

@router.get("/stats/overview", response_model=DeadlineStats)
async def get_deadline_stats(
    db: Session = Depends(get_db)
):
    """Get deadline statistics overview"""
    deadlines = db.query(Deadline).all()
    
    total = len(deadlines)
    pending = len([d for d in deadlines if d.status == "pending"])
    completed = len([d for d in deadlines if d.status == "completed"])
    overdue = len([d for d in deadlines if d.status == "overdue"])
    
    return DeadlineStats(
        total=total,
        pending=pending,
        completed=completed,
        overdue=overdue,
        completion_rate=round((completed / total * 100) if total > 0 else 0, 1)
    )