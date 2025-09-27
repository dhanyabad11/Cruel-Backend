"""
Celery Task: Supabase-based Deadline Reminders
"""
import os
from datetime import datetime, timedelta
from celery import Celery
from supabase import create_client, Client
from app.services.notification_service import get_notification_service, NotificationType

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "supabase_notification_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@celery_app.task(name="send_supabase_deadline_reminders")
def send_supabase_deadline_reminders():
    """
    Celery task to send reminders for upcoming/overdue deadlines using Supabase.
    """
    now = datetime.utcnow()
    soon = now + timedelta(hours=1)
    overdue = now
    # Get all active users
    users_result = supabase.table('users').select('id', 'phone', 'is_active').eq('is_active', True).execute()
    users = users_result.data or []
    notification_service = get_notification_service()
    for user in users:
        user_id = user['id']
        phone = user.get('phone')
        if not phone:
            continue
        # Upcoming deadlines (due in next hour)
        deadlines_result = supabase.table('deadlines').select('*').eq('user_id', user_id).eq('status', 'pending').gte('deadline_date', now.isoformat()).lte('deadline_date', soon.isoformat()).execute()
        deadlines = deadlines_result.data or []
        for d in deadlines:
            notification_service.send_deadline_reminder(
                phone_number=phone,
                deadline_title=d['title'],
                deadline_date=datetime.fromisoformat(d['deadline_date']),
                deadline_url=d.get('portal_url'),
                notification_type=NotificationType.WHATSAPP if phone.startswith('whatsapp:') else NotificationType.SMS,
                priority=d.get('priority', 'medium')
            )
        # Overdue deadlines
        overdue_result = supabase.table('deadlines').select('*').eq('user_id', user_id).eq('status', 'overdue').lte('deadline_date', overdue.isoformat()).execute()
        overdue_deadlines = overdue_result.data or []
        for d in overdue_deadlines:
            notification_service.send_deadline_reminder(
                phone_number=phone,
                deadline_title=d['title'],
                deadline_date=datetime.fromisoformat(d['deadline_date']),
                deadline_url=d.get('portal_url'),
                notification_type=NotificationType.WHATSAPP if phone.startswith('whatsapp:') else NotificationType.SMS,
                priority=d.get('priority', 'medium')
            )
    return {"success": True, "message": "Reminders sent."}


@celery_app.task(name="send_deadline_reminder")
def send_deadline_reminder(deadline_id: int):
    """
    Send a reminder for a specific deadline.
    """
    notification_service = get_notification_service()
    
    # Get deadline details
    deadline_result = supabase.table('deadlines').select('*').eq('id', deadline_id).execute()
    if not deadline_result.data:
        return {"success": False, "error": "Deadline not found"}
    
    deadline = deadline_result.data[0]
    
    # Get user details
    user_result = supabase.table('user_profiles').select('*').eq('id', deadline['user_id']).execute()
    if not user_result.data:
        return {"success": False, "error": "User not found"}
    
    user = user_result.data[0]
    phone = user.get('phone_number') or user.get('phone')
    
    if not phone:
        return {"success": False, "error": "No phone number configured"}
    
    # Send the reminder
    try:
        notification_service.send_deadline_reminder(
            phone_number=phone,
            deadline_title=deadline['title'],
            deadline_date=datetime.fromisoformat(deadline['due_date'].replace('Z', '+00:00')),
            deadline_url=deadline.get('portal_url'),
            notification_type=NotificationType.WHATSAPP if phone.startswith('whatsapp:') else NotificationType.SMS,
            priority=deadline.get('priority', 'medium')
        )
        return {"success": True, "message": f"Reminder sent for deadline {deadline_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
