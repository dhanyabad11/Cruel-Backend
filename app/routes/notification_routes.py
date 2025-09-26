@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """List notifications for the current user from Supabase"""
    query = supabase.table('notifications').select('*').eq('user_id', current_user.id)
    query = query.range(skip, skip + limit - 1)
    result = query.execute()
    notifications = result.data or []
    return [NotificationResponse(**n) for n in notifications]

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific notification by ID from Supabase"""
    result = supabase.table('notifications').select('*').eq('id', notification_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = result.data[0]
    return NotificationResponse(**notification)

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a notification in Supabase"""
    update_data = notification_data.dict(exclude_unset=True)
    result = supabase.table('notifications').update(update_data).eq('id', notification_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found or update failed")
    notification = result.data[0]
    return NotificationResponse(**notification)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a notification in Supabase"""
    result = supabase.table('notifications').delete().eq('id', notification_id).eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found or delete failed")

@router.get("/stats/overview", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get notification statistics for the current user from Supabase"""
    result = supabase.table('notifications').select('*').eq('user_id', current_user.id).execute()
    notifications = result.data or []
    total = len(notifications)
    sent = sum(1 for n in notifications if n.get('delivery_status') == 'sent')
    pending = sum(1 for n in notifications if n.get('delivery_status') == 'pending')
    failed = sum(1 for n in notifications if n.get('delivery_status') == 'failed')
    return NotificationStatsResponse(
        total=total,
        sent=sent,
        pending=pending,
        failed=failed
    )
"""
Notification Routes

API endpoints for notification management and sending SMS/WhatsApp messages.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client
from app.database import get_supabase_client, get_supabase_admin
from app.models import User
from app.schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationPreferenceCreate, NotificationPreferenceUpdate, NotificationPreferenceResponse,
    SendNotificationRequest, SendDeadlineReminderRequest, SendDailySummaryRequest,
    NotificationStatusResponse, NotificationSendResponse, NotificationListResponse, NotificationStatsResponse
)
from app.utils.auth import get_current_user
from app.services.notification_service import get_notification_service, NotificationType

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send", response_model=NotificationSendResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Send a custom notification using Supabase"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    # Create notification record in Supabase
    notification_insert = {
        'user_id': current_user.id,
        'deadline_id': request.deadline_id,
        'notification_type': request.notification_type,
        'message': request.message,
        'sent_at': datetime.utcnow().isoformat(),
        'delivery_status': 'pending'
    }
    result = supabase.table('notifications').insert(notification_insert).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create notification")
    notification = result.data[0]
    # Send notification
    notification_type = NotificationType.WHATSAPP if request.notification_type == 'whatsapp' else NotificationType.SMS
    send_result = await notification_service.send_notification(
        phone_number=request.phone_number,
        message=request.message,
        notification_type=notification_type
    )
    # Also send email if user has email
    from app.services.email_service import send_email
    user_result = supabase.table('users').select('email').eq('id', current_user.id).execute()
    email = None
    if user_result.data:
        email = user_result.data[0].get('email')
    if email:
        await send_email(
            to_email=email,
            subject="[AI Cruel] Notification",
            body=request.message
        )
    # Update notification record in Supabase
    update_data = {
        'delivery_status': send_result['status'],
        'sent_at': datetime.utcnow().isoformat() if send_result['success'] else None,
        'message_sid': send_result.get('message_sid'),
        'error_message': send_result.get('error')
    }
    supabase.table('notifications').update(update_data).eq('id', notification['id']).execute()
    send_result['notification_id'] = notification['id']
    return NotificationSendResponse(**send_result)


@router.post("/send-deadline-reminder", response_model=NotificationSendResponse)
async def send_deadline_reminder(
    request: SendDeadlineReminderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a deadline reminder notification"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    
    # Get deadline
    deadline = db.query(Deadline).filter(
        and_(Deadline.id == request.deadline_id, Deadline.user_id == current_user.id)
    ).first()
    
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )
    
    # Get user's notification preferences
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    # Determine phone number and notification type
    phone_number = request.phone_number
    notification_type = request.notification_type
    
    if not phone_number and preferences:
        phone_number = preferences.phone_number
    if not notification_type and preferences:
        notification_type = preferences.preferred_method
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number available. Please provide one or set up notification preferences."
        )
    
    notification_type = notification_type or 'sms'
    
    # Create notification record
    notification = Notification(
        user_id=current_user.id,
        deadline_id=deadline.id,
        notification_type=notification_type,
        phone_number=phone_number,
        message_content="",  # Will be set by service
        notification_reason="deadline_reminder",
        scheduled_for=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Send deadline reminder
    notif_type = NotificationType.WHATSAPP if notification_type == 'whatsapp' else NotificationType.SMS
    result = await notification_service.send_deadline_reminder(
        phone_number=phone_number,
        deadline_title=deadline.title,
        deadline_date=deadline.due_date,
        deadline_url=deadline.portal_url,
        notification_type=notif_type,
        priority=deadline.priority.value if deadline.priority else "medium"
    )
    
    # Update notification record
    notification.message_content = result.get('message_content', '')
    notification.update_status(
        status=result['status'],
        message_sid=result.get('message_sid'),
        sent_at=datetime.utcnow() if result['success'] else None,
        error_message=result.get('error')
    )
    db.commit()
    
    result['notification_id'] = notification.id
    return NotificationSendResponse(**result)


@router.post("/send-daily-summary", response_model=NotificationSendResponse)
async def send_daily_summary(
    request: SendDailySummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a daily summary of deadlines"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    
    # Get user's notification preferences
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    # Determine phone number and notification type
    phone_number = request.phone_number
    notification_type = request.notification_type
    
    if not phone_number and preferences:
        phone_number = preferences.phone_number
    if not notification_type and preferences:
        notification_type = preferences.preferred_method
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number available. Please provide one or set up notification preferences."
        )
    
    notification_type = notification_type or 'sms'
    
    # Get deadlines for summary
    target_date = datetime.utcnow().date()
    if request.date:
        target_date = datetime.strptime(request.date, '%Y-%m-%d').date()
    
    # Get upcoming deadlines (next 7 days)
    end_date = target_date + timedelta(days=7)
    deadlines = db.query(Deadline).filter(
        and_(
            Deadline.user_id == current_user.id,
            Deadline.due_date >= target_date,
            Deadline.due_date <= end_date,
            Deadline.status != 'completed'
        )
    ).order_by(Deadline.due_date).all()
    
    # Convert to dict format
    deadline_dicts = []
    for deadline in deadlines:
        deadline_dicts.append({
            'title': deadline.title,
            'due_date': deadline.due_date.isoformat(),
            'priority': deadline.priority.value if deadline.priority else 'medium',
            'url': deadline.portal_url
        })
    
    # Create notification record
    notification = Notification(
        user_id=current_user.id,
        deadline_id=None,
        notification_type=notification_type,
        phone_number=phone_number,
        message_content="",  # Will be set by service
        notification_reason="daily_summary",
        scheduled_for=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Send daily summary
    notif_type = NotificationType.WHATSAPP if notification_type == 'whatsapp' else NotificationType.SMS
    result = await notification_service.send_daily_summary(
        phone_number=phone_number,
        deadlines=deadline_dicts,
        notification_type=notif_type
    )
    
    # Update notification record
    notification.message_content = result.get('message_content', '')
    notification.update_status(
        status=result['status'],
        message_sid=result.get('message_sid'),
        sent_at=datetime.utcnow() if result['success'] else None,
        error_message=result.get('error')
    )
    db.commit()
    
    result['notification_id'] = notification.id
    return NotificationSendResponse(**result)


@router.get("/status/{message_sid}", response_model=NotificationStatusResponse)
async def get_notification_status(
    message_sid: str,
    current_user: User = Depends(get_current_user)
):
    """Get the delivery status of a sent notification"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    
    status_info = notification_service.get_message_status(message_sid)
    
    if 'error' in status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {status_info['error']}"
        )
    
    return NotificationStatusResponse(**status_info)


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    notification_type: Optional[str] = Query(None, regex="^(sms|whatsapp)$"),
    status: Optional[str] = Query(None, regex="^(pending|sent|delivered|failed)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List notifications for the current user"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    # Apply filters
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    if status:
        query = query.filter(Notification.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    notifications = query.order_by(desc(Notification.created_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Calculate pages
    pages = (total + per_page - 1) // per_page
    
    return NotificationListResponse(
        notifications=[NotificationResponse.from_orm(n) for n in notifications],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the current user"""
    # Get stats
    total_sent = db.query(func.count(Notification.id)).filter(
        and_(Notification.user_id == current_user.id, Notification.status != 'pending')
    ).scalar() or 0
    
    total_delivered = db.query(func.count(Notification.id)).filter(
        and_(Notification.user_id == current_user.id, Notification.status == 'delivered')
    ).scalar() or 0
    
    total_failed = db.query(func.count(Notification.id)).filter(
        and_(Notification.user_id == current_user.id, Notification.status == 'failed')
    ).scalar() or 0
    
    # Calculate delivery rate
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    
    # Get recent notifications
    recent_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(5).all()
    
    return NotificationStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_failed=total_failed,
        delivery_rate=round(delivery_rate, 2),
        recent_notifications=[NotificationResponse.from_orm(n) for n in recent_notifications]
    )


# Notification Preference Routes
@router.post("/preferences", response_model=NotificationPreferenceResponse)
async def create_notification_preferences(
    preferences: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update notification preferences"""
    # Check if preferences already exist
    existing = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification preferences already exist. Use PUT to update."
        )
    
    # Create new preferences
    db_preferences = NotificationPreference(
        user_id=current_user.id,
        **preferences.dict()
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    
    return NotificationPreferenceResponse.from_orm(db_preferences)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification preferences for the current user"""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    return NotificationPreferenceResponse.from_orm(preferences)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found. Create them first."
        )
    
    # Update preferences
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    return NotificationPreferenceResponse.from_orm(preferences)


@router.delete("/preferences")
async def delete_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete notification preferences"""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    db.delete(preferences)
    db.commit()
    
    return {"message": "Notification preferences deleted successfully"}