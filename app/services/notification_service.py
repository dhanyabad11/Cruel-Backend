"""
Twilio Notification Service

This module handles sending SMS and WhatsApp notifications for deadline reminders
using the Twilio API.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import os

from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported"""
    SMS = "sms"
    WHATSAPP = "whatsapp"


class NotificationStatus(Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TwilioNotificationService:
    """Service for sending notifications via Twilio SMS and WhatsApp"""
    
    def __init__(self, 
                 account_sid: Optional[str] = None, 
                 auth_token: Optional[str] = None,
                 whatsapp_from: Optional[str] = None,
                 sms_from: Optional[str] = None):
        """
        Initialize Twilio notification service.
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            whatsapp_from: WhatsApp sender number (format: whatsapp:+1234567890)
            sms_from: SMS sender number (format: +1234567890)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = whatsapp_from or os.getenv('TWILIO_WHATSAPP_FROM')
        self.sms_from = sms_from or os.getenv('TWILIO_SMS_FROM')
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio Account SID and Auth Token are required")
        
        self.client = Client(self.account_sid, self.auth_token)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_config(self) -> bool:
        """
        Validate Twilio configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Test connection by fetching account info
            account = self.client.api.accounts(self.account_sid).fetch()
            return account.status == 'active'
        except Exception as e:
            self.logger.error(f"Twilio configuration validation failed: {e}")
            return False
    
    async def send_deadline_reminder(self,
                                   phone_number: str,
                                   deadline_title: str,
                                   deadline_date: datetime,
                                   deadline_url: Optional[str] = None,
                                   notification_type: NotificationType = NotificationType.SMS,
                                   priority: str = "medium") -> Dict[str, Any]:
        """
        Send a deadline reminder notification.
        
        Args:
            phone_number: Recipient phone number
            deadline_title: Title of the deadline
            deadline_date: When the deadline is due
            deadline_url: Optional URL to the deadline source
            notification_type: SMS or WhatsApp
            priority: Priority level (low, medium, high, urgent)
            
        Returns:
            Dict containing notification result
        """
        message_body = self._format_deadline_message(
            deadline_title, deadline_date, deadline_url, priority
        )
        
        return await self.send_notification(
            phone_number=phone_number,
            message=message_body,
            notification_type=notification_type
        )
    
    async def send_daily_summary(self,
                               phone_number: str,
                               deadlines: List[Dict[str, Any]],
                               notification_type: NotificationType = NotificationType.SMS) -> Dict[str, Any]:
        """
        Send a daily summary of upcoming deadlines.
        
        Args:
            phone_number: Recipient phone number
            deadlines: List of deadline dictionaries
            notification_type: SMS or WhatsApp
            
        Returns:
            Dict containing notification result
        """
        message_body = self._format_daily_summary(deadlines)
        
        return await self.send_notification(
            phone_number=phone_number,
            message=message_body,
            notification_type=notification_type
        )
    
    async def send_overdue_alert(self,
                               phone_number: str,
                               overdue_deadlines: List[Dict[str, Any]],
                               notification_type: NotificationType = NotificationType.SMS) -> Dict[str, Any]:
        """
        Send an alert for overdue deadlines.
        
        Args:
            phone_number: Recipient phone number
            overdue_deadlines: List of overdue deadline dictionaries
            notification_type: SMS or WhatsApp
            
        Returns:
            Dict containing notification result
        """
        message_body = self._format_overdue_alert(overdue_deadlines)
        
        return await self.send_notification(
            phone_number=phone_number,
            message=message_body,
            notification_type=notification_type
        )
    
    async def send_notification(self,
                              phone_number: str,
                              message: str,
                              notification_type: NotificationType = NotificationType.SMS) -> Dict[str, Any]:
        """
        Send a notification via SMS or WhatsApp.
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            notification_type: SMS or WhatsApp
            
        Returns:
            Dict containing notification result
        """
        try:
            # Format phone number
            to_number = self._format_phone_number(phone_number, notification_type)
            from_number = self._get_from_number(notification_type)
            
            if not from_number:
                return {
                    'success': False,
                    'error': f'No sender number configured for {notification_type.value}',
                    'message_sid': None,
                    'status': NotificationStatus.FAILED.value
                }
            
            # Send message
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            self.logger.info(f"Notification sent successfully. SID: {message_obj.sid}")
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': NotificationStatus.SENT.value,
                'to': to_number,
                'from': from_number,
                'type': notification_type.value
            }
            
        except TwilioException as e:
            self.logger.error(f"Twilio error sending notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_sid': None,
                'status': NotificationStatus.FAILED.value
            }
        except Exception as e:
            self.logger.error(f"Unexpected error sending notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_sid': None,
                'status': NotificationStatus.FAILED.value
            }
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get the delivery status of a sent message.
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dict containing message status information
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            # Map Twilio status to our enum
            status_mapping = {
                'queued': NotificationStatus.PENDING,
                'sending': NotificationStatus.PENDING,
                'sent': NotificationStatus.SENT,
                'delivered': NotificationStatus.DELIVERED,
                'undelivered': NotificationStatus.FAILED,
                'failed': NotificationStatus.FAILED
            }
            
            status = status_mapping.get(message.status, NotificationStatus.UNKNOWN)
            
            return {
                'message_sid': message_sid,
                'status': status.value,
                'twilio_status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
            
        except TwilioException as e:
            self.logger.error(f"Error fetching message status: {e}")
            return {
                'message_sid': message_sid,
                'status': NotificationStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    def _format_phone_number(self, phone_number: str, notification_type: NotificationType) -> str:
        """Format phone number for the specific notification type."""
        # Remove any existing prefixes
        clean_number = phone_number.replace('whatsapp:', '').replace('+', '').replace(' ', '').replace('-', '')
        
        # Ensure it starts with country code (assume +1 for US if not provided)
        if not clean_number.startswith('1') and len(clean_number) == 10:
            clean_number = '1' + clean_number
        
        formatted_number = '+' + clean_number
        
        if notification_type == NotificationType.WHATSAPP:
            return f'whatsapp:{formatted_number}'
        else:
            return formatted_number
    
    def _get_from_number(self, notification_type: NotificationType) -> Optional[str]:
        """Get the appropriate sender number for the notification type."""
        if notification_type == NotificationType.WHATSAPP:
            return self.whatsapp_from
        else:
            return self.sms_from
    
    def _format_deadline_message(self, 
                               title: str, 
                               deadline_date: datetime, 
                               url: Optional[str] = None,
                               priority: str = "medium") -> str:
        """Format a deadline reminder message."""
        # Calculate time until deadline
        now = datetime.now(deadline_date.tzinfo)
        time_diff = deadline_date - now
        
        # Format time remaining
        if time_diff.total_seconds() < 0:
            time_str = "OVERDUE"
            urgency = "🚨 URGENT"
        elif time_diff.days > 0:
            time_str = f"in {time_diff.days} day{'s' if time_diff.days != 1 else ''}"
            urgency = "⏰" if priority in ['high', 'urgent'] else "📅"
        elif time_diff.seconds > 3600:
            hours = int(time_diff.seconds / 3600)
            time_str = f"in {hours} hour{'s' if hours != 1 else ''}"
            urgency = "⏰ URGENT"
        else:
            minutes = max(1, int(time_diff.seconds / 60))
            time_str = f"in {minutes} minute{'s' if minutes != 1 else ''}"
            urgency = "🚨 CRITICAL"
        
        # Build message
        message = f"{urgency} Deadline Reminder\n\n"
        message += f"📋 {title}\n"
        message += f"⏱️ Due: {time_str}\n"
        message += f"📅 {deadline_date.strftime('%Y-%m-%d %H:%M')}"
        
        if url:
            message += f"\n🔗 {url}"
        
        message += "\n\n-- AI Cruel Deadline Manager"
        
        return message
    
    def _format_daily_summary(self, deadlines: List[Dict[str, Any]]) -> str:
        """Format a daily summary message."""
        if not deadlines:
            return "📅 Daily Summary\n\nNo upcoming deadlines today. Great job staying on top of things!\n\n-- AI Cruel Deadline Manager"
        
        message = f"📅 Daily Summary - {len(deadlines)} deadline{'s' if len(deadlines) != 1 else ''}\n\n"
        
        # Group by urgency
        urgent = []
        today = []
        upcoming = []
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        
        for deadline in deadlines[:10]:  # Limit to 10 deadlines
            due_date = deadline.get('due_date')
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            if due_date < now:
                urgent.append(deadline)
            elif due_date < tomorrow_start:
                today.append(deadline)
            else:
                upcoming.append(deadline)
        
        # Add urgent deadlines
        if urgent:
            message += "🚨 OVERDUE:\n"
            for deadline in urgent:
                message += f"• {deadline.get('title', 'Untitled')}\n"
            message += "\n"
        
        # Add today's deadlines
        if today:
            message += "⏰ TODAY:\n"
            for deadline in today:
                due_time = deadline.get('due_date')
                if isinstance(due_time, str):
                    due_time = datetime.fromisoformat(due_time.replace('Z', '+00:00'))
                message += f"• {deadline.get('title', 'Untitled')} ({due_time.strftime('%H:%M')})\n"
            message += "\n"
        
        # Add upcoming deadlines
        if upcoming:
            message += "📅 UPCOMING:\n"
            for deadline in upcoming[:5]:  # Limit upcoming to 5
                due_date = deadline.get('due_date')
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                days_until = (due_date.date() - now.date()).days
                message += f"• {deadline.get('title', 'Untitled')} ({days_until} day{'s' if days_until != 1 else ''})\n"
        
        message += "\n-- AI Cruel Deadline Manager"
        return message
    
    def _format_overdue_alert(self, overdue_deadlines: List[Dict[str, Any]]) -> str:
        """Format an overdue alert message."""
        count = len(overdue_deadlines)
        message = f"🚨 OVERDUE ALERT - {count} deadline{'s' if count != 1 else ''}\n\n"
        
        for deadline in overdue_deadlines[:5]:  # Limit to 5 overdue items
            title = deadline.get('title', 'Untitled')
            due_date = deadline.get('due_date')
            
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            days_overdue = (datetime.now() - due_date).days
            message += f"• {title} ({days_overdue} day{'s' if days_overdue != 1 else ''} overdue)\n"
        
        if count > 5:
            message += f"... and {count - 5} more\n"
        
        message += "\nPlease review and update these deadlines.\n\n-- AI Cruel Deadline Manager"
        return message


# Singleton instance for global use
_notification_service: Optional[TwilioNotificationService] = None


def get_notification_service() -> Optional[TwilioNotificationService]:
    """Get the global notification service instance."""
    global _notification_service
    return _notification_service


def initialize_notification_service(account_sid: Optional[str] = None,
                                  auth_token: Optional[str] = None,
                                  whatsapp_from: Optional[str] = None,
                                  sms_from: Optional[str] = None) -> TwilioNotificationService:
    """Initialize the global notification service."""
    global _notification_service
    _notification_service = TwilioNotificationService(
        account_sid=account_sid,
        auth_token=auth_token,
        whatsapp_from=whatsapp_from,
        sms_from=sms_from
    )
    return _notification_service