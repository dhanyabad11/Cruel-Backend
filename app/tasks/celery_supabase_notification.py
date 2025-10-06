"""
Celery Task: Supabase-based Deadline Reminders
"""
import os
import asyncio
from datetime import datetime, timedelta
from celery import Celery
from supabase import create_client, Client
from app.services.notification_service import get_notification_service, NotificationType
from app.services.email_service import send_email

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "supabase_notification_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Create Supabase client lazily to avoid import-time errors
def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
    return create_client(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )

@celery_app.task(name="send_supabase_deadline_reminders")
def send_supabase_deadline_reminders():
    """
    Celery task to send reminders for upcoming/overdue deadlines using Supabase.
    """
    supabase = get_supabase_client()
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
    supabase = get_supabase_client()
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


@celery_app.task(name="check_and_send_email_reminders")
def check_and_send_email_reminders():
    """
    Check for deadlines and send email reminders based on notification_settings and notification_reminders.
    This task runs periodically to send reminders at the configured times before deadlines.
    Supports relative times like: 1_hour, 1_day, 1_week before deadline.
    """
    supabase = get_supabase_client()
    now = datetime.utcnow()
    
    print(f"[EMAIL REMINDERS] Running at {now.isoformat()}")
    
    # Parse reminder time to timedelta
    def parse_reminder_time(reminder_str):
        """Convert reminder time string (1_hour, 1_day, etc) to timedelta"""
        time_map = {
            '15_min': timedelta(minutes=15),
            '30_min': timedelta(minutes=30),
            '1_hour': timedelta(hours=1),
            '2_hours': timedelta(hours=2),
            '1_day': timedelta(days=1),
            '2_days': timedelta(days=2),
            '1_week': timedelta(weeks=1),
        }
        return time_map.get(reminder_str, timedelta(hours=1))
    
    try:
        # Get all users with email notifications enabled
        settings_result = supabase.table('notification_settings').select('*').eq('email_enabled', True).execute()
        all_settings = settings_result.data or []
        
        print(f"[EMAIL REMINDERS] Found {len(all_settings)} users with email enabled")
        
        for settings in all_settings:
            user_id = settings['user_id']
            email = settings.get('email')
            
            if not email:
                print(f"[EMAIL REMINDERS] User {user_id} has no email configured, skipping")
                continue
            
            # Get reminder times for this user
            reminders_result = supabase.table('notification_reminders').select('*').eq('user_id', user_id).eq('email_enabled', True).execute()
            reminders = reminders_result.data or []
            
            if not reminders:
                print(f"[EMAIL REMINDERS] User {user_id} has no email reminder times configured")
                continue
            
            print(f"[EMAIL REMINDERS] Checking deadlines for user {user_id} ({email})")
            
            # Get all pending deadlines for this user
            deadlines_result = supabase.table('deadlines').select('*').eq('user_id', user_id).eq('status', 'pending').gte('due_date', now.isoformat()).execute()
            deadlines = deadlines_result.data or []
            
            if not deadlines:
                print(f"[EMAIL REMINDERS] No pending deadlines for {email}")
                continue
            
            print(f"[EMAIL REMINDERS] Found {len(deadlines)} pending deadlines for {email}")
            
            # Check each deadline against reminder times
            for deadline in deadlines:
                try:
                    deadline_date = datetime.fromisoformat(deadline['due_date'].replace('Z', '+00:00'))
                    time_until_deadline = deadline_date - now
                    
                    # Check if we should send reminder for any configured time
                    for reminder in reminders:
                        reminder_time_str = reminder.get('reminder_time')
                        if not reminder_time_str:
                            continue
                        
                        reminder_delta = parse_reminder_time(reminder_time_str)
                        
                        # Check if we're within 5 minutes of the reminder time
                        # e.g., if deadline is in 1 day and reminder is "1_day", send now
                        time_diff = abs(time_until_deadline - reminder_delta)
                        
                        if time_diff < timedelta(minutes=5):
                            print(f"[EMAIL REMINDERS] Sending email for '{deadline['title']}' ({reminder_time_str} reminder)")
                            
                            # Check if we already sent this reminder (to avoid duplicates)
                            # You can add a "last_reminder_sent" check here if needed
                            
                            # Prepare email content
                            subject = f"Reminder: {deadline['title']} deadline approaching"
                            body = f"""
Hello,

This is a reminder about your upcoming deadline:

Title: {deadline['title']}
Description: {deadline.get('description', 'No description')}
Due Date: {deadline_date.strftime('%B %d, %Y at %I:%M %p')}
Priority: {deadline.get('priority', 'medium').upper()}

Time until deadline: {reminder_time_str.replace('_', ' ')}

Don't forget to complete this task on time!

Best regards,
Your Deadline Reminder System
"""
                            
                            # Run async email send in sync context
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            try:
                                loop.run_until_complete(
                                    send_email(
                                        to_email=email,
                                        subject=subject,
                                        body=body
                                    )
                                )
                                print(f"[EMAIL REMINDERS] ✓ Email sent to {email} for deadline: {deadline['title']}")
                            except Exception as email_error:
                                print(f"[EMAIL REMINDERS] ✗ Failed to send email to {email}: {email_error}")
                            finally:
                                loop.close()
                            
                            break  # Only send once per deadline per check
                            
                except Exception as e:
                    print(f"[EMAIL REMINDERS] Error processing deadline {deadline.get('id')}: {e}")
        
        return {"success": True, "message": f"Checked reminders at {now.isoformat()}"}
        
    except Exception as e:
        print(f"[EMAIL REMINDERS] Error in check_and_send_email_reminders: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
