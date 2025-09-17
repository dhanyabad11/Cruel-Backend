from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.deadline import PriorityLevel, StatusLevel

class DeadlineBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: datetime
    priority: PriorityLevel = PriorityLevel.MEDIUM
    status: StatusLevel = StatusLevel.PENDING
    portal_id: Optional[int] = None
    portal_task_id: Optional[str] = None
    portal_url: Optional[str] = None
    tags: Optional[str] = None
    estimated_hours: Optional[int] = None

class DeadlineCreate(DeadlineBase):
    pass

class DeadlineUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[PriorityLevel] = None
    status: Optional[StatusLevel] = None
    portal_id: Optional[int] = None
    portal_task_id: Optional[str] = None
    portal_url: Optional[str] = None
    tags: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None

class DeadlineResponse(DeadlineBase):
    id: int
    user_id: int
    reminder_sent: bool
    reminder_count: int
    last_reminder_sent: Optional[datetime] = None
    actual_hours: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_overdue: bool
    days_until_due: int

    class Config:
        from_attributes = True

class DeadlineStats(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    overdue: int
    due_today: int
    due_this_week: int