from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from supabase import Client
from app.database import get_supabase_client, get_supabase_admin
from app.models.user import User
from app.models.deadline import StatusLevel
from app.schemas.deadline import DeadlineCreate, DeadlineUpdate, DeadlineResponse, DeadlineStats
from app.auth_deps import get_current_user

router = APIRouter(tags=["deadlines"])

@router.get("/")
async def get_deadlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all deadlines for the current user from Supabase"""
    try:
        print(f"DEBUG: Current user in deadlines: {current_user}")
        # Return proper array format for frontend compatibility
        return []  # Return empty array directly - frontend expects this format
        
        # Original logic commented out for now
        # query = supabase.table('deadlines').select('*').eq('user_id', current_user['id'])
        # if status:
        #     query = query.eq('status', status)
        # if priority:
        #     query = query.eq('priority', priority)
        # query = query.range(skip, skip + limit - 1)
        # result = query.execute()
        # deadlines = result.data or []
        # return [DeadlineResponse(**deadline) for deadline in deadlines]
    except Exception as e:
        print(f"DEBUG: Error in deadlines endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/")
async def create_deadline(
    deadline_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new deadline - simplified for testing"""
    try:
        print(f"DEBUG: Creating deadline for user: {current_user}")
        print(f"DEBUG: Raw deadline data: {deadline_data}")
        
        # For now, return a simple mock response to test frontend functionality
        mock_deadline = {
            "id": 999,
            "title": deadline_data.get("title", ""),
            "description": deadline_data.get("description", ""),
            "due_date": deadline_data.get("due_date", ""),
            "priority": deadline_data.get("priority", "medium"),
            "status": "pending",
            "user_id": current_user['id'],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"DEBUG: Returning mock deadline: {mock_deadline}")
        return mock_deadline
        
    except Exception as e:
        print(f"DEBUG: Error creating deadline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create deadline: {str(e)}")
    return DeadlineResponse(**deadline)

@router.get("/{deadline_id}", response_model=DeadlineResponse)
async def get_deadline(
    deadline_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific deadline by ID from Supabase"""
    result = supabase.table('deadlines').select('*').eq('id', deadline_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found")
    deadline = result.data[0]
    return DeadlineResponse(**deadline)

@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(
    deadline_id: int,
    deadline_data: DeadlineUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a deadline in Supabase"""
    update_data = deadline_data.dict(exclude_unset=True)
    result = supabase.table('deadlines').update(update_data).eq('id', deadline_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found or update failed")
    deadline = result.data[0]
    return DeadlineResponse(**deadline)

@router.delete("/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a deadline in Supabase"""
    result = supabase.table('deadlines').delete().eq('id', deadline_id).eq('user_id', current_user['id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Deadline not found or delete failed")

@router.get("/stats/overview", response_model=DeadlineStats)
async def get_deadline_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get deadline statistics for the current user from Supabase"""
    result = supabase.table('deadlines').select('*').eq('user_id', current_user['id']).execute()
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