from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.deadline import Deadline, StatusLevel
from app.schemas.deadline import DeadlineCreate, DeadlineUpdate, DeadlineResponse, DeadlineStats
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[DeadlineResponse])
async def get_deadlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all deadlines for the current user"""
    query = db.query(Deadline)
    
    # Apply filters
    if status:
        query = query.filter(Deadline.status == status)
    if priority:
        query = query.filter(Deadline.priority == priority)
    
    # Order by due date
    query = query.order_by(Deadline.due_date.asc())
    
    deadlines = query.offset(skip).limit(limit).all()
    return [DeadlineResponse.from_orm(deadline) for deadline in deadlines]

@router.post("/", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    deadline_data: DeadlineCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new deadline"""
    db_deadline = Deadline(
        user_id=current_user.id,
        **deadline_data.dict()
    )
    
    db.add(db_deadline)
    db.commit()
    db.refresh(db_deadline)
    
    return DeadlineResponse.from_orm(db_deadline)

@router.get("/{deadline_id}", response_model=DeadlineResponse)
async def get_deadline(
    deadline_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific deadline by ID"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )
    
    return DeadlineResponse.from_orm(deadline)

@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(
    deadline_id: int,
    deadline_data: DeadlineUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a deadline"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )
    
    # Update fields
    update_data = deadline_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deadline, field, value)
    
    deadline.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(deadline)
    
    return DeadlineResponse.from_orm(deadline)

@router.delete("/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a deadline"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )
    
    db.delete(deadline)
    db.commit()

@router.get("/stats/overview", response_model=DeadlineStats)
async def get_deadline_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get deadline statistics for the current user"""
    base_query = db.query(Deadline).filter(Deadline.user_id == current_user.id)
    
    total = base_query.count()
    pending = base_query.filter(Deadline.status == StatusLevel.PENDING).count()
    in_progress = base_query.filter(Deadline.status == StatusLevel.IN_PROGRESS).count()
    completed = base_query.filter(Deadline.status == StatusLevel.COMPLETED).count()
    overdue = base_query.filter(Deadline.status == StatusLevel.OVERDUE).count()
    
    # Due today and this week calculations
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Week calculation (next 7 days)
    week_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    from datetime import timedelta
    week_end = week_end + timedelta(days=7)
    
    due_today = base_query.filter(
        Deadline.due_date >= today_start,
        Deadline.due_date <= today_end,
        Deadline.status != StatusLevel.COMPLETED
    ).count()
    
    due_this_week = base_query.filter(
        Deadline.due_date >= now,
        Deadline.due_date <= week_end,
        Deadline.status != StatusLevel.COMPLETED
    ).count()
    
    return DeadlineStats(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        overdue=overdue,
        due_today=due_today,
        due_this_week=due_this_week
    )