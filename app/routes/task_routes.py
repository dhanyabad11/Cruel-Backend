"""
Task Routes

API endpoints for managing and monitoring background tasks.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.models import User
from app.utils.auth import get_current_user
from app.celery_app import celery_app

# Import task functions for manual triggering
from app.tasks.scraping_tasks import scrape_portal, scrape_user_portals, scrape_all_portals
from app.tasks.celery_supabase_notification import send_supabase_deadline_reminders, send_deadline_reminder

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    """Response model for task operations"""
    task_id: str
    task_name: str
    status: str
    timestamp: str
    message: Optional[str] = None


class TaskResultResponse(BaseModel):
    """Response model for task results"""
    task_id: str
    task_name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


# Manual Task Triggers

@router.post("/scraping/portal/{portal_id}", response_model=TaskResponse)
async def trigger_portal_scrape(
    portal_id: int,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual scraping for a specific portal"""
    task = scrape_portal.apply_async(args=[portal_id])
    
    return TaskResponse(
        task_id=task.id,
        task_name="scrape_portal",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message=f"Started scraping portal {portal_id}"
    )


@router.post("/scraping/user", response_model=TaskResponse)
async def trigger_user_scrape(
    current_user: User = Depends(get_current_user)
):
    """Trigger manual scraping for current user's portals"""
    task = scrape_user_portals.apply_async(args=[current_user.id])
    
    return TaskResponse(
        task_id=task.id,
        task_name="scrape_user_portals",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message=f"Started scraping portals for user {current_user.id}"
    )


@router.post("/scraping/all", response_model=TaskResponse)
async def trigger_all_scrape(
    current_user: User = Depends(get_current_user)
):
    """Trigger manual scraping for all portals (admin only)"""
    # In a real app, you'd check for admin permissions here
    task = scrape_all_portals.apply_async()
    
    return TaskResponse(
        task_id=task.id,
        task_name="scrape_all_portals",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message="Started scraping all portals"
    )


@router.post("/notifications/deadline-reminder/{deadline_id}", response_model=TaskResponse)
async def trigger_deadline_reminder(
    deadline_id: int,
    current_user: User = Depends(get_current_user)
):
    """Send manual deadline reminder"""
    task = send_deadline_reminder.apply_async(args=[deadline_id])
    
    return TaskResponse(
        task_id=task.id,
        task_name="send_deadline_reminder",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message=f"Started sending reminder for deadline {deadline_id}"
    )


@router.post("/notifications/daily-summary", response_model=TaskResponse)
async def trigger_daily_summary(
    current_user: User = Depends(get_current_user)
):
    """Trigger manual daily summary for all users"""
    task = send_daily_summaries.apply_async()
    
    return TaskResponse(
        task_id=task.id,
        task_name="send_daily_summaries",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message="Started sending daily summaries"
    )


@router.post("/notifications/check-overdue", response_model=TaskResponse)
async def trigger_overdue_check(
    current_user: User = Depends(get_current_user)
):
    """Trigger manual overdue deadline check"""
    task = check_overdue_deadlines.apply_async()
    
    return TaskResponse(
        task_id=task.id,
        task_name="check_overdue_deadlines",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message="Started checking for overdue deadlines"
    )


@router.post("/maintenance/cleanup-notifications", response_model=TaskResponse)
async def trigger_notification_cleanup(
    days_to_keep: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """Trigger cleanup of old notifications"""
    task = cleanup_old_notifications.apply_async(args=[days_to_keep])
    
    return TaskResponse(
        task_id=task.id,
        task_name="cleanup_old_notifications",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message=f"Started cleanup of notifications older than {days_to_keep} days"
    )


@router.post("/maintenance/health-check", response_model=TaskResponse)
async def trigger_health_check(
    current_user: User = Depends(get_current_user)
):
    """Trigger system health check"""
    task = health_check.apply_async()
    
    return TaskResponse(
        task_id=task.id,
        task_name="health_check",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message="Started system health check"
    )


@router.post("/maintenance/generate-stats", response_model=TaskResponse)
async def trigger_stats_generation(
    current_user: User = Depends(get_current_user)
):
    """Trigger system statistics generation"""
    task = generate_system_stats.apply_async()
    
    return TaskResponse(
        task_id=task.id,
        task_name="generate_system_stats",
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        message="Started generating system statistics"
    )


# Task Monitoring

@router.get("/status/{task_id}", response_model=TaskResultResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status and result of a task"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = TaskResultResponse(
                task_id=task_id,
                task_name=task_result.name or "unknown",
                status="pending",
                timestamp=datetime.utcnow().isoformat()
            )
        elif task_result.state == 'SUCCESS':
            response = TaskResultResponse(
                task_id=task_id,
                task_name=task_result.name or "unknown",
                status="success",
                result=task_result.result,
                timestamp=datetime.utcnow().isoformat()
            )
        elif task_result.state == 'FAILURE':
            response = TaskResultResponse(
                task_id=task_id,
                task_name=task_result.name or "unknown",
                status="failure",
                error=str(task_result.result),
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            response = TaskResultResponse(
                task_id=task_id,
                task_name=task_result.name or "unknown",
                status=task_result.state.lower(),
                timestamp=datetime.utcnow().isoformat()
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found or error retrieving status: {str(e)}"
        )


@router.get("/active")
async def get_active_tasks(
    current_user: User = Depends(get_current_user)
):
    """Get list of currently active tasks"""
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active": active_tasks or {},
            "scheduled": scheduled_tasks or {},
            "reserved": reserved_tasks or {}
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active tasks: {str(e)}"
        )


@router.get("/stats")
async def get_task_stats(
    current_user: User = Depends(get_current_user)
):
    """Get Celery task statistics"""
    try:
        inspect = celery_app.control.inspect()
        
        stats = inspect.stats()
        registered_tasks = inspect.registered()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats or {},
            "registered_tasks": registered_tasks or {},
            "celery_info": {
                "broker": celery_app.conf.broker_url,
                "backend": celery_app.conf.result_backend
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task stats: {str(e)}"
        )


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Task {task_id} has been cancelled"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling task: {str(e)}"
        )


# Celery Beat Schedule Information

@router.get("/schedule")
async def get_task_schedule(
    current_user: User = Depends(get_current_user)
):
    """Get the current task schedule configuration"""
    try:
        beat_schedule = celery_app.conf.beat_schedule
        
        # Format schedule for better readability
        formatted_schedule = {}
        for task_name, config in beat_schedule.items():
            formatted_schedule[task_name] = {
                "task": config["task"],
                "schedule": str(config["schedule"]),
                "options": config.get("options", {}),
                "enabled": True  # In a real app, you might track this
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "schedule": formatted_schedule,
            "total_scheduled_tasks": len(formatted_schedule)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task schedule: {str(e)}"
        )