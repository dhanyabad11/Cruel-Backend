from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from supabase import Client
from app.database import get_supabase_client, get_supabase_admin
from app.models.user import User
from app.schemas.deadline import DeadlineCreate, DeadlineUpdate, DeadlineResponse, DeadlineStats
from app.utils.auth import get_current_active_user
from app.models.deadline import StatusLevel

router = APIRouter(prefix="/deadlines", tags=["deadlines"])

@router.get("/", response_model=List[DeadlineResponse])
async def get_deadlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all deadlines for the current user from Supabase"""
    query = supabase.table('deadlines').select('*').eq('user_id', current_user.id)
    if status:
        query = query.eq('status', status)
    if priority:
        query = query.eq('priority', priority)
    query = query.range(skip, skip + limit - 1)
    result = query.execute()
    deadlines = result.data or []
    return [DeadlineResponse(**deadline) for deadline in deadlines]

@router.post("/", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    deadline_data: DeadlineCreate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new deadline in Supabase"""
    insert_data = deadline_data.dict()
    insert_data['user_id'] = current_user.id
    result = supabase.table('deadlines').insert(insert_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create deadline")
    deadline = result.data[0]
    # Send notification and email for high/urgent deadlines
    if deadline.get('priority') in ['high', 'urgent']:
        from app.services.notification_service import get_notification_service, NotificationType
        from app.services.email_service import send_email
        notification_service = get_notification_service()
        # Fetch user phone and email
        user_result = supabase.table('users').select('phone', 'email').eq('id', current_user.id).execute()
        phone = None
        email = None
        if user_result.data:
            phone = user_result.data[0].get('phone')
            email = user_result.data[0].get('email')
        if phone:
            await notification_service.send_deadline_reminder(
                phone_number=phone,
                deadline_title=deadline['title'],
                deadline_date=deadline['deadline_date'],
                deadline_url=deadline.get('portal_url'),
                notification_type=NotificationType.WHATSAPP if phone.startswith('whatsapp:') else NotificationType.SMS,
                priority=deadline['priority']
            )
        if email:
            await send_email(
                to_email=email,
                subject=f"[AI Cruel] New {deadline['priority']} Deadline: {deadline['title']}",
                body=f"A new {deadline['priority']} deadline '{deadline['title']}' is due on {deadline['deadline_date']}.\nDetails: {deadline.get('description', '')}\nURL: {deadline.get('portal_url', '')}"
            )
    return DeadlineResponse(**deadline)

@router.get("/{deadline_id}", response_model=DeadlineResponse)
async def get_deadline(
    deadline_id: int,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific deadline by ID from Supabase"""
    result = supabase.table('deadlines').select('*').eq('id', deadline_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found")
    deadline = result.data[0]
    return DeadlineResponse(**deadline)

@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(
    deadline_id: int,
    deadline_data: DeadlineUpdate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a deadline in Supabase"""
    update_data = deadline_data.dict(exclude_unset=True)
    result = supabase.table('deadlines').update(update_data).eq('id', deadline_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found or update failed")
    deadline = result.data[0]
    return DeadlineResponse(**deadline)

@router.delete("/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: int,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a deadline in Supabase"""
    result = supabase.table('deadlines').delete().eq('id', deadline_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found or delete failed")

@router.get("/stats/overview", response_model=DeadlineStats)
async def get_deadline_stats(
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get deadline statistics for the current user from Supabase"""
    result = supabase.table('deadlines').select('*').eq('user_id', current_user.id).execute()
    deadlines = result.data or []
    total = len(deadlines)
    pending = sum(1 for d in deadlines if d.get('status') == StatusLevel.PENDING.value)
    in_progress = sum(1 for d in deadlines if d.get('status') == StatusLevel.IN_PROGRESS.value)
    completed = sum(1 for d in deadlines if d.get('status') == StatusLevel.COMPLETED.value)
    overdue = sum(1 for d in deadlines if d.get('status') == StatusLevel.OVERDUE.value)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_end = today_end + timedelta(days=7)
    due_today = sum(1 for d in deadlines if d.get('due_date') and today_start <= datetime.fromisoformat(d['due_date']) <= today_end and d.get('status') != StatusLevel.COMPLETED.value)
    due_this_week = sum(1 for d in deadlines if d.get('due_date') and now <= datetime.fromisoformat(d['due_date']) <= week_end and d.get('status') != StatusLevel.COMPLETED.value)
    return DeadlineStats(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        overdue=overdue,
        due_today=due_today,
        due_this_week=due_this_week
    )