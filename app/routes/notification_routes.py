from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta
from supabase import Client
from app.database import get_supabase_client
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationPreferenceCreate, NotificationPreferenceUpdate, NotificationPreferenceResponse, NotificationSendResponse, SendNotificationRequest, SendDeadlineReminderRequest, SendDailySummaryRequest, NotificationStatusResponse, NotificationListResponse, NotificationStatsResponse
from app.utils.auth import get_current_user
from app.models.user import User
from datetime import datetime

# Mock get_current_user for testing
async def mock_get_current_user() -> User:
    print("DEBUG: Mock get_current_user called")
    return User(
        id="62fd877b-9515-411a-bbb7-6a47d021d970",
        email="testuser@gmail.com",
        username="testuser",
        full_name="Test User",
        phone=None,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow()
    )
from app.services.notification_service import get_notification_service, NotificationType

router = APIRouter(tags=["notifications"])

@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    notification_type: Optional[str] = Query(None, regex="^(sms|whatsapp)$"),
    status: Optional[str] = Query(None, regex="^(pending|sent|delivered|failed)$"),
    
    supabase: Client = Depends(get_supabase_client)
):
    """List notifications for the current user from Supabase"""
    # Build query
    query = supabase.table('notifications').select('*', count='exact').eq('user_id', current_user.id)
    
    # Apply filters
    if notification_type:
        query = query.eq('notification_type', notification_type)
    if status:
        query = query.eq('status', status)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1).order('created_at', desc=True)
    
    result = query.execute()
    notifications = result.data or []
    total = result.count or 0
    
    # Calculate pages
    pages = (total + per_page - 1) // per_page
    
    return NotificationListResponse(
        notifications=[NotificationResponse(**n) for n in notifications],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific notification by ID"""
    query = supabase.table('notifications').select('*').eq('id', notification_id).eq('user_id', current_user.id)
    result = query.execute()
    notification = result.data[0] if result.data else None
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse(**notification)


# Notification Preference Routes
@router.post("/preferences", response_model=NotificationPreferenceResponse)
async def create_notification_preferences(
    preferences: NotificationPreferenceCreate,
    
    supabase: Client = Depends(get_supabase_client)
):
    """Create notification preferences for the current user"""
    logger = logging.getLogger("notification_preferences")
    try:
        # Check if preferences already exist
        existing = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
        if existing.data:
            logger.warning(f"User {current_user.id} tried to create duplicate notification preferences.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification preferences already exist. Use PUT to update.")

        # Create new preferences
        insert_data = {
            'user_id': current_user.id,
            'preferred_method': preferences.preferred_method,
            'phone_number': preferences.phone_number,
            'email': preferences.email,
            'daily_summary_enabled': preferences.daily_summary_enabled,
            'daily_summary_time': preferences.daily_summary_time,
            'reminder_enabled': preferences.reminder_enabled,
            'reminder_hours_before': preferences.reminder_hours_before,
            'overdue_alerts_enabled': preferences.overdue_alerts_enabled,
            'weekend_notifications': preferences.weekend_notifications,
            'quiet_hours_enabled': preferences.quiet_hours_enabled,
            'quiet_hours_start': preferences.quiet_hours_start,
            'quiet_hours_end': preferences.quiet_hours_end,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        result = supabase.table('notification_preferences').insert(insert_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create notification preferences")

        preferences_data = result.data[0]
        logger.info(f"Notification preferences created for user {current_user.id}.")
        return NotificationPreferenceResponse(**preferences_data)
    except Exception as e:
        logger.error(f"Error creating notification preferences for user {current_user.id}: {e}")
        raise

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    
    supabase: Client = Depends(get_supabase_client)
):
    """Get notification preferences for the current user"""
    result = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification preferences not found")
    return NotificationPreferenceResponse(**result.data[0])

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferenceUpdate,
    
    supabase: Client = Depends(get_supabase_client)
):
    """Update notification preferences for the current user"""
    logger = logging.getLogger("notification_preferences")
    try:
        # Check if preferences exist
        existing = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
        if not existing.data:
            logger.warning(f"User {current_user.id} tried to update non-existent notification preferences.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification preferences not found. Create them first.")

        # Update preferences
        update_data = preferences_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()

        result = supabase.table('notification_preferences').update(update_data).eq('user_id', current_user.id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update notification preferences")

        preferences_data = result.data[0]
        logger.info(f"Notification preferences updated for user {current_user.id}.")
        return NotificationPreferenceResponse(**preferences_data)
    except Exception as e:
        logger.error(f"Error updating notification preferences for user {current_user.id}: {e}")
        raise

@router.delete("/preferences")
async def delete_notification_preferences(
    
    supabase: Client = Depends(get_supabase_client)
):
    """Delete notification preferences for the current user"""
    logger = logging.getLogger("notification_preferences")
    try:
        # Check if preferences exist
        existing = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
        if not existing.data:
            logger.warning(f"User {current_user.id} tried to delete non-existent notification preferences.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification preferences not found")

        # Delete preferences
        result = supabase.table('notification_preferences').delete().eq('user_id', current_user.id).execute()
        logger.info(f"Notification preferences deleted for user {current_user.id}.")
        return {"message": "Notification preferences deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting notification preferences for user {current_user.id}: {e}")
        raise

@router.post("/send-custom-notification", response_model=NotificationSendResponse)
async def send_custom_notification(
    request: SendNotificationRequest,
    
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
    
    supabase: Client = Depends(get_supabase_client)
):
    """Send a deadline reminder notification"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    
    # Get deadline from Supabase
    deadline_result = supabase.table('deadlines').select('*').eq('id', request.deadline_id).eq('user_id', current_user.id).execute()
    deadline = deadline_result.data[0] if deadline_result.data else None
    
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found"
        )
    
    # Get user's notification preferences from Supabase
    preferences_result = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
    preferences = preferences_result.data[0] if preferences_result.data else None
    
    # Determine phone number and notification type
    phone_number = request.phone_number
    notification_type = request.notification_type
    
    if not phone_number and preferences:
        phone_number = preferences.get('phone_number')
    if not notification_type and preferences:
        notification_type = preferences.get('preferred_method')
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number available. Please provide one or set up notification preferences."
        )
    
    notification_type = notification_type or 'sms'
    
    # Create notification record in Supabase
    notification_insert = {
        'user_id': current_user.id,
        'deadline_id': deadline['id'],
        'notification_type': notification_type,
        'phone_number': phone_number,
        'message_content': '',  # Will be set by service
        'notification_reason': 'deadline_reminder',
        'scheduled_for': datetime.utcnow().isoformat(),
        'status': 'pending'
    }
    notification_result = supabase.table('notifications').insert(notification_insert).execute()
    notification = notification_result.data[0]
    
    # Send deadline reminder
    notif_type = NotificationType.WHATSAPP if notification_type == 'whatsapp' else NotificationType.SMS
    result = await notification_service.send_deadline_reminder(
        phone_number=phone_number,
        deadline_title=deadline['title'],
        deadline_date=deadline['due_date'],
        deadline_url=deadline.get('portal_url'),
        notification_type=notif_type,
        priority=deadline.get('priority', 'medium')
    )
    
    # Update notification record in Supabase
    update_data = {
        'message_content': result.get('message_content', ''),
        'status': result['status'],
        'message_sid': result.get('message_sid'),
        'sent_at': datetime.utcnow().isoformat() if result['success'] else None,
        'error_message': result.get('error')
    }
    supabase.table('notifications').update(update_data).eq('id', notification['id']).execute()
    
    result['notification_id'] = notification['id']
    return NotificationSendResponse(**result)


@router.post("/send-daily-summary", response_model=NotificationSendResponse)
async def send_daily_summary(
    request: SendDailySummaryRequest,
    
    supabase: Client = Depends(get_supabase_client)
):
    """Send a daily summary of deadlines"""
    notification_service = get_notification_service()
    if not notification_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not available"
        )
    
    # Get user's notification preferences from Supabase
    preferences_result = supabase.table('notification_preferences').select('*').eq('user_id', current_user.id).execute()
    preferences = preferences_result.data[0] if preferences_result.data else None
    
    # Determine phone number and notification type
    phone_number = request.phone_number
    notification_type = request.notification_type
    
    if not phone_number and preferences:
        phone_number = preferences.get('phone_number')
    if not notification_type and preferences:
        notification_type = preferences.get('preferred_method')
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number available. Please provide one or set up notification preferences."
        )
    
    notification_type = notification_type or 'sms'
    
    # Get deadlines for summary from Supabase
    target_date = datetime.utcnow().date()
    if request.date:
        target_date = datetime.strptime(request.date, '%Y-%m-%d').date()
    
    # Get upcoming deadlines (next 7 days)
    end_date = target_date + timedelta(days=7)
    deadlines_result = supabase.table('deadlines').select('*').eq('user_id', current_user.id).gte('due_date', target_date.isoformat()).lte('due_date', end_date.isoformat()).neq('status', 'completed').order('due_date').execute()
    deadlines = deadlines_result.data or []
    
    # Convert to dict format
    deadline_dicts = []
    for deadline in deadlines:
        deadline_dicts.append({
            'title': deadline['title'],
            'due_date': deadline['due_date'],
            'priority': deadline.get('priority', 'medium'),
            'url': deadline.get('portal_url')
        })
    
    # Create notification record in Supabase
    notification_insert = {
        'user_id': current_user.id,
        'deadline_id': None,
        'notification_type': notification_type,
        'phone_number': phone_number,
        'message_content': '',  # Will be set by service
        'notification_reason': 'daily_summary',
        'scheduled_for': datetime.utcnow().isoformat(),
        'status': 'pending'
    }
    notification_result = supabase.table('notifications').insert(notification_insert).execute()
    notification = notification_result.data[0]
    
    # Send daily summary
    notif_type = NotificationType.WHATSAPP if notification_type == 'whatsapp' else NotificationType.SMS
    result = await notification_service.send_daily_summary(
        phone_number=phone_number,
        deadlines=deadline_dicts,
        notification_type=notif_type
    )
    
    # Update notification record in Supabase
    update_data = {
        'message_content': result.get('message_content', ''),
        'status': result['status'],
        'message_sid': result.get('message_sid'),
        'sent_at': datetime.utcnow().isoformat() if result['success'] else None,
        'error_message': result.get('error')
    }
    supabase.table('notifications').update(update_data).eq('id', notification['id']).execute()
    
    result['notification_id'] = notification['id']
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
    
    supabase: Client = Depends(get_supabase_client)
):
    """List notifications for the current user from Supabase"""
    # Build query
    query = supabase.table('notifications').select('*', count='exact').eq('user_id', current_user.id)
    
    # Apply filters
    if notification_type:
        query = query.eq('notification_type', notification_type)
    if status:
        query = query.eq('status', status)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1).order('created_at', desc=True)
    
    result = query.execute()
    notifications = result.data or []
    total = result.count or 0
    
    # Calculate pages
    pages = (total + per_page - 1) // per_page
    
    return NotificationListResponse(
        notifications=[NotificationResponse(**n) for n in notifications],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    
    supabase: Client = Depends(get_supabase_client)
):
    """Get notification statistics for the current user from Supabase"""
    # Get total sent (not pending)
    sent_result = supabase.table('notifications').select('*', count='exact').eq('user_id', current_user.id).neq('status', 'pending').execute()
    total_sent = sent_result.count or 0
    
    # Get total delivered
    delivered_result = supabase.table('notifications').select('*', count='exact').eq('user_id', current_user.id).eq('status', 'delivered').execute()
    total_delivered = delivered_result.count or 0
    
    # Get total failed
    failed_result = supabase.table('notifications').select('*', count='exact').eq('user_id', current_user.id).eq('status', 'failed').execute()
    total_failed = failed_result.count or 0
    
    # Calculate delivery rate
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    
    # Get recent notifications
    recent_result = supabase.table('notifications').select('*').eq('user_id', current_user.id).order('created_at', desc=True).limit(5).execute()
    recent_notifications = recent_result.data or []
    
    return NotificationStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_failed=total_failed,
        delivery_rate=round(delivery_rate, 2),
        recent_notifications=[NotificationResponse(**n) for n in recent_notifications]
    )