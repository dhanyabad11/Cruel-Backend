"""
Notification Tasks

Background tasks for automated deadline notifications and reminders.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import shared_task

from app.supabase_client import SupabaseConfig
from app.services.notification_service import get_notification_service, NotificationType

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Get Supabase client for tasks"""
    config = SupabaseConfig()
    return config.get_service_client() or config.get_client()


@shared_task(bind=True, name='app.tasks.notification_tasks.send_deadline_reminder')
def send_deadline_reminder(self, deadline_id: int, notification_type: str = 'sms'):
    """
    Send a reminder for a specific deadline.

    Args:
        deadline_id: ID of the deadline to remind about
        notification_type: 'sms' or 'whatsapp'

    Returns:
        Dict with notification result
    """
    supabase = get_supabase_client()
    try:
        # Get deadline with user
        deadline_response = supabase.table('deadlines').select('*').eq('id', deadline_id).execute()
        deadline = deadline_response.data[0] if deadline_response.data else None
        if not deadline:
            return {"success": False, "error": "Deadline not found"}
        
        # Get user
        user_response = supabase.table('user_profiles').select('*').eq('id', deadline['user_id']).execute()
        user = user_response.data[0] if user_response.data else None
        if not user:
            return {"success": False, "error": "User not found"}

        # Get user's notification preferences (assuming they're in user_profiles)
        preferences = user  # For now, assume preferences are in user profile

        if not preferences.get('reminder_enabled', True):
            return {"success": True, "message": "Reminders disabled for user"}

        phone_number = preferences.get('phone_number')
        if not phone_number:
            return {"success": False, "error": "No phone number configured"}

        # Check quiet hours (simplified - you might want to add this to user_profiles)
        # For now, skip quiet hours check

        # Get notification service
        notification_service = get_notification_service()
        if not notification_service:
            return {"success": False, "error": "Notification service not available"}

        # Create notification record
        notification_data = {
            'user_id': user['id'],
            'deadline_id': deadline['id'],
            'type': 'reminder',
            'message': "",  # Will be set by service
            'scheduled_for': datetime.utcnow().isoformat()
        }
        notification_response = supabase.table('notifications').insert(notification_data).execute()
        notification = notification_response.data[0]

        # Send notification
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            notif_type = NotificationType.WHATSAPP if preferences.get('preferred_method') == 'whatsapp' else NotificationType.SMS
            result = loop.run_until_complete(
                notification_service.send_deadline_reminder(
                    phone_number=phone_number,
                    deadline_title=deadline['title'],
                    deadline_date=datetime.fromisoformat(deadline['due_date'].replace('Z', '+00:00')),
                    deadline_url=deadline.get('portal_url'),
                    notification_type=notif_type,
                    priority=deadline.get('priority', 'medium')
                )
            )

            loop.close()
            
        except Exception as e:
            logger.error(f"Failed to send deadline reminder: {e}")
            result = {"success": False, "error": str(e)}

        # Update notification record
        update_data = {
            'status': 'sent' if result.get('success') else 'failed',
            'sent_at': datetime.utcnow().isoformat() if result.get('success') else None
        }
        if result.get('error'):
            update_data['message'] = result['error']
        supabase.table('notifications').update(update_data).eq('id', notification['id']).execute()

        # Update deadline reminder tracking (assuming we add these fields to deadlines table)
        # For now, skip this part as the table might not have these fields

        return {
            "success": result.get('success', False),
            "deadline_id": deadline_id,
            "notification_id": notification['id'],
            "message_sid": result.get('message_sid'),
            "error": result.get('error')
        }

    except Exception as e:
        logger.error(f"Error sending deadline reminder for {deadline_id}: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True, name='app.tasks.notification_tasks.send_deadline_reminders')
def send_deadline_reminders(self):
    """
    Send reminders for upcoming deadlines based on user preferences.
    
    Returns:
        Dict with batch reminder results
    """
    db = get_db_session()
    try:
        # Get all users with notification preferences
        users_with_prefs = db.query(User).join(NotificationPreference).filter(
            NotificationPreference.reminder_enabled == True
        ).all()
        
        if not users_with_prefs:
            return {"success": True, "message": "No users with reminders enabled"}
        
        total_sent = 0
        total_skipped = 0
        errors = []
        
        for user in users_with_prefs:
            try:
                preferences = user.notification_preferences
                if not preferences or not preferences.phone_number:
                    continue
                
                # Check quiet hours
                if preferences.is_quiet_time():
                    continue
                
                # Get reminder hours
                reminder_hours = preferences.get_reminder_hours_list()
                
                # Find deadlines that need reminders
                now = datetime.utcnow()
                reminder_conditions = []
                
                for hours in reminder_hours:
                    # Calculate when to send reminder (hours before deadline)
                    reminder_time = now + timedelta(hours=hours)
                    # Allow 15-minute window for reminder
                    window_start = reminder_time - timedelta(minutes=7.5)
                    window_end = reminder_time + timedelta(minutes=7.5)
                    
                    reminder_conditions.append(
                        and_(
                            Deadline.due_date >= window_start,
                            Deadline.due_date <= window_end
                        )
                    )
                
                if not reminder_conditions:
                    continue
                
                # Find deadlines needing reminders
                deadlines_to_remind = db.query(Deadline).filter(
                    and_(
                        Deadline.user_id == user.id,
                        Deadline.status != "completed",
                        or_(*reminder_conditions),
                        or_(
                            Deadline.last_reminder_sent.is_(None),
                            Deadline.last_reminder_sent < (now - timedelta(hours=1))  # Don't spam
                        )
                    )
                ).all()
                
                # Send reminders
                for deadline in deadlines_to_remind:
                    result = send_deadline_reminder.apply(args=[deadline.id])
                    
                    if result.successful() and result.result.get("success"):
                        total_sent += 1
                        logger.info(f"Sent reminder for deadline {deadline.id}")
                    else:
                        total_skipped += 1
                        error_msg = result.result.get("error", "Unknown error") if result.successful() else "Task failed"
                        errors.append(f"Deadline {deadline.id}: {error_msg}")
                        
            except Exception as e:
                logger.error(f"Error processing reminders for user {user.id}: {e}")
                errors.append(f"User {user.id}: {str(e)}")
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "users_processed": len(users_with_prefs),
            "reminders_sent": total_sent,
            "reminders_skipped": total_skipped,
            "errors": errors[:10]  # Limit errors
        }
        
    except Exception as e:
        logger.error(f"Error in batch deadline reminders: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.notification_tasks.send_daily_summaries')
def send_daily_summaries(self):
    """
    Send daily summaries to all users who have them enabled.
    
    Returns:
        Dict with batch summary results
    """
    db = get_db_session()
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Get users with daily summaries enabled
        users_with_summaries = db.query(User).join(NotificationPreference).filter(
            NotificationPreference.daily_summary_enabled == True
        ).all()
        
        if not users_with_summaries:
            return {"success": True, "message": "No users with daily summaries enabled"}
        
        total_sent = 0
        total_skipped = 0
        errors = []
        
        for user in users_with_summaries:
            try:
                preferences = user.notification_preferences
                if not preferences or not preferences.phone_number:
                    total_skipped += 1
                    continue
                
                # Check if it's time for this user's daily summary
                summary_time = datetime.strptime(preferences.daily_summary_time, '%H:%M').time()
                current_time = now.time()
                
                # Allow 30-minute window around scheduled time
                time_diff = abs((datetime.combine(now.date(), current_time) - 
                               datetime.combine(now.date(), summary_time)).total_seconds())
                
                if time_diff > 1800:  # 30 minutes
                    total_skipped += 1
                    continue
                
                # Check if summary was already sent today
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                existing_summary = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user.id,
                        Notification.notification_reason == "daily_summary",
                        Notification.created_at >= today_start
                    )
                ).first()
                
                if existing_summary:
                    total_skipped += 1
                    continue
                
                # Get deadlines for summary (next 7 days)
                end_date = now + timedelta(days=7)
                deadlines = db.query(Deadline).filter(
                    and_(
                        Deadline.user_id == user.id,
                        Deadline.due_date >= now,
                        Deadline.due_date <= end_date,
                        Deadline.status != "completed"
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
                
                # Get notification service
                notification_service = get_notification_service()
                if not notification_service:
                    errors.append(f"User {user.id}: Notification service not available")
                    continue
                
                # Create notification record
                notification = Notification(
                    user_id=user.id,
                    deadline_id=None,
                    notification_type=preferences.preferred_method,
                    phone_number=preferences.phone_number,
                    message_content="",  # Will be set by service
                    notification_reason="daily_summary",
                    scheduled_for=datetime.utcnow()
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                
                # Send summary
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    notif_type = NotificationType.WHATSAPP if preferences.preferred_method == 'whatsapp' else NotificationType.SMS
                    result = loop.run_until_complete(
                        notification_service.send_daily_summary(
                            phone_number=preferences.phone_number,
                            deadlines=deadline_dicts,
                            notification_type=notif_type
                        )
                    )
                    
                    loop.close()
                    
                except Exception as e:
                    logger.error(f"Failed to send daily summary to user {user.id}: {e}")
                    result = {"success": False, "error": str(e)}
                
                # Update notification record
                notification.update_status(
                    status=result['status'],
                    message_sid=result.get('message_sid'),
                    sent_at=datetime.utcnow() if result['success'] else None,
                    error_message=result.get('error')
                )
                db.commit()
                
                if result['success']:
                    total_sent += 1
                    logger.info(f"Sent daily summary to user {user.id}")
                else:
                    total_skipped += 1
                    errors.append(f"User {user.id}: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"Error sending daily summary to user {user.id}: {e}")
                total_skipped += 1
                errors.append(f"User {user.id}: {str(e)}")
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "users_processed": len(users_with_summaries),
            "summaries_sent": total_sent,
            "summaries_skipped": total_skipped,
            "errors": errors[:10]
        }
        
    except Exception as e:
        logger.error(f"Error in batch daily summaries: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.notification_tasks.check_overdue_deadlines')
def check_overdue_deadlines(self):
    """
    Check for overdue deadlines and send alerts.
    
    Returns:
        Dict with overdue alert results
    """
    db = get_db_session()
    try:
        now = datetime.utcnow()
        
        # Find overdue deadlines
        overdue_deadlines = db.query(Deadline).filter(
            and_(
                Deadline.due_date < now,
                Deadline.status != "completed",
                Deadline.status != "overdue"
            )
        ).all()
        
        if not overdue_deadlines:
            return {"success": True, "message": "No new overdue deadlines found"}
        
        # Update status to overdue
        for deadline in overdue_deadlines:
            deadline.status = "overdue"
        
        # Group by user for alerts
        user_overdue = {}
        for deadline in overdue_deadlines:
            if deadline.user_id not in user_overdue:
                user_overdue[deadline.user_id] = []
            user_overdue[deadline.user_id].append(deadline)
        
        total_sent = 0
        total_skipped = 0
        errors = []
        
        # Send overdue alerts
        for user_id, deadlines in user_overdue.items():
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue
                
                preferences = db.query(NotificationPreference).filter(
                    NotificationPreference.user_id == user_id
                ).first()
                
                if not preferences or not preferences.overdue_alerts_enabled or not preferences.phone_number:
                    total_skipped += 1
                    continue
                
                # Check if overdue alert was already sent today for this user
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                existing_alert = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.notification_reason == "overdue_alert",
                        Notification.created_at >= today_start
                    )
                ).first()
                
                if existing_alert:
                    total_skipped += 1
                    continue
                
                # Get notification service
                notification_service = get_notification_service()
                if not notification_service:
                    errors.append(f"User {user_id}: Notification service not available")
                    continue
                
                # Prepare overdue deadline data
                overdue_data = []
                for deadline in deadlines:
                    overdue_data.append({
                        'title': deadline.title,
                        'due_date': deadline.due_date.isoformat(),
                        'url': deadline.portal_url
                    })
                
                # Create notification record
                notification = Notification(
                    user_id=user_id,
                    deadline_id=None,
                    notification_type=preferences.preferred_method,
                    phone_number=preferences.phone_number,
                    message_content="",  # Will be set by service
                    notification_reason="overdue_alert",
                    scheduled_for=datetime.utcnow()
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                
                # Send overdue alert
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    notif_type = NotificationType.WHATSAPP if preferences.preferred_method == 'whatsapp' else NotificationType.SMS
                    result = loop.run_until_complete(
                        notification_service.send_overdue_alert(
                            phone_number=preferences.phone_number,
                            overdue_deadlines=overdue_data,
                            notification_type=notif_type
                        )
                    )
                    
                    loop.close()
                    
                except Exception as e:
                    logger.error(f"Failed to send overdue alert to user {user_id}: {e}")
                    result = {"success": False, "error": str(e)}
                
                # Update notification record
                notification.update_status(
                    status=result['status'],
                    message_sid=result.get('message_sid'),
                    sent_at=datetime.utcnow() if result['success'] else None,
                    error_message=result.get('error')
                )
                
                if result['success']:
                    total_sent += 1
                    logger.info(f"Sent overdue alert to user {user_id} for {len(deadlines)} deadlines")
                else:
                    total_skipped += 1
                    errors.append(f"User {user_id}: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"Error sending overdue alert to user {user_id}: {e}")
                total_skipped += 1
                errors.append(f"User {user_id}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "overdue_deadlines_found": len(overdue_deadlines),
            "users_affected": len(user_overdue),
            "alerts_sent": total_sent,
            "alerts_skipped": total_skipped,
            "errors": errors[:10]
        }
        
    except Exception as e:
        logger.error(f"Error checking overdue deadlines: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.notification_tasks.update_notification_statuses')
def update_notification_statuses(self):
    """
    Update delivery statuses for recent notifications using Twilio status.
    
    Returns:
        Dict with status update results
    """
    db = get_db_session()
    try:
        # Get notification service
        notification_service = get_notification_service()
        if not notification_service:
            return {"success": False, "error": "Notification service not available"}
        
        # Get recent notifications that might need status updates
        recent_time = datetime.utcnow() - timedelta(hours=24)
        notifications_to_check = db.query(Notification).filter(
            and_(
                Notification.message_sid.isnot(None),
                Notification.status.in_(['pending', 'sent']),
                Notification.created_at >= recent_time
            )
        ).all()
        
        if not notifications_to_check:
            return {"success": True, "message": "No notifications to update"}
        
        updated_count = 0
        errors = []
        
        for notification in notifications_to_check:
            try:
                # Get status from Twilio
                status_info = notification_service.get_message_status(notification.message_sid)
                
                if 'error' not in status_info:
                    # Update notification status
                    old_status = notification.status
                    notification.twilio_status = status_info.get('twilio_status')
                    notification.status = status_info.get('status', notification.status)
                    
                    if status_info.get('error_code'):
                        notification.error_code = status_info['error_code']
                        notification.error_message = status_info['error_message']
                    
                    if old_status != notification.status:
                        notification.updated_at = datetime.utcnow()
                        updated_count += 1
                        logger.debug(f"Updated notification {notification.id} status: {old_status} -> {notification.status}")
                
            except Exception as e:
                logger.error(f"Error updating notification {notification.id} status: {e}")
                errors.append(f"Notification {notification.id}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "notifications_checked": len(notifications_to_check),
            "notifications_updated": updated_count,
            "errors": errors[:10]
        }
        
    except Exception as e:
        logger.error(f"Error updating notification statuses: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()