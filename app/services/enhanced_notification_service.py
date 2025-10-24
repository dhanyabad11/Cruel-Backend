"""
Enhanced Notification Service

This module handles sending notifications via multiple channels:
- Email notifications using SMTP
- WhatsApp notifications using Twilio
- SMS notifications using Twilio
- Push notifications (web push)
"""

import logging
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
import asyncio
import httpx

from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import os
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class NotificationStatus(Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class EnhancedNotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        """Initialize notification service with all channels"""
        # Twilio setup
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        self.sms_from = getattr(settings, 'TWILIO_SMS_FROM', None)
        
        # Email setup
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        
        # Initialize Twilio client if credentials are available
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.twilio_client = None
            logger.warning("Twilio credentials not found - SMS and WhatsApp notifications disabled")
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_config(self) -> Dict[str, bool]:
        """
        Validate configuration for all notification channels.
        
        Returns:
            Dict with status of each channel
        """
        status = {
            "email": False,
            "sms": False,
            "whatsapp": False,
            "push": False
        }
        
        # Check email configuration
        try:
            if all([self.smtp_host, self.smtp_port, self.smtp_username, self.smtp_password]):
                status["email"] = True
        except Exception as e:
            self.logger.error(f"Email configuration validation failed: {e}")
        
        # Check Twilio configuration
        try:
            if self.twilio_client:
                account = self.twilio_client.api.accounts(self.twilio_account_sid).fetch()
                if account.status == 'active':
                    if self.sms_from:
                        status["sms"] = True
                    if self.whatsapp_from:
                        status["whatsapp"] = True
        except Exception as e:
            self.logger.error(f"Twilio configuration validation failed: {e}")
        
        # Push notifications - placeholder for now
        status["push"] = True  # Will implement with web push later
        
        return status
    
    async def send_email_notification(self,
                                    to_email: str,
                                    subject: str,
                                    body: str,
                                    html_body: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email notification using SendGrid API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            Dict containing notification result
        """
        try:
            # Get SendGrid credentials
            sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
            from_email = os.getenv("SENDGRID_FROM_EMAIL", self.smtp_username)
            
            if not sendgrid_api_key:
                raise ValueError("SENDGRID_API_KEY environment variable is required")
            
            # SendGrid API endpoint
            url = "https://api.sendgrid.com/v3/mail/send"
            
            # Build email payload
            content = [{"type": "text/plain", "value": body}]
            if html_body:
                content.append({"type": "text/html", "value": html_body})
            
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {"email": from_email},
                "content": content
            }
            
            headers = {
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code not in [200, 202]:
                    raise Exception(f"SendGrid API error: {response.status_code} - {response.text}")
            
            self.logger.info(f"Email sent successfully to {to_email} via SendGrid")
            return {
                "success": True,
                "message": "Email sent successfully",
                "notification_type": NotificationType.EMAIL.value,
                "recipient": to_email,
                "status": NotificationStatus.SENT.value,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": NotificationType.EMAIL.value,
                "recipient": to_email,
                "status": NotificationStatus.FAILED.value,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def send_sms_notification(self,
                                  phone_number: str,
                                  message: str) -> Dict[str, Any]:
        """
        Send SMS notification using Twilio.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message text
            
        Returns:
            Dict containing notification result
        """
        try:
            if not self.twilio_client or not self.sms_from:
                raise ValueError("SMS configuration incomplete")
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.sms_from,
                to=phone_number
            )
            
            self.logger.info(f"SMS sent successfully to {phone_number}")
            return {
                "success": True,
                "message": "SMS sent successfully",
                "notification_type": NotificationType.SMS.value,
                "recipient": phone_number,
                "status": NotificationStatus.SENT.value,
                "twilio_sid": message_obj.sid,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": NotificationType.SMS.value,
                "recipient": phone_number,
                "status": NotificationStatus.FAILED.value,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def send_whatsapp_notification(self,
                                       phone_number: str,
                                       message: str) -> Dict[str, Any]:
        """
        Send WhatsApp notification using Twilio.
        
        Args:
            phone_number: Recipient phone number (format: +1234567890)
            message: WhatsApp message text
            
        Returns:
            Dict containing notification result
        """
        try:
            if not self.twilio_client or not self.whatsapp_from:
                raise ValueError("WhatsApp configuration incomplete")
            
            # Format phone number for WhatsApp
            whatsapp_to = f"whatsapp:{phone_number}"
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=whatsapp_to
            )
            
            self.logger.info(f"WhatsApp message sent successfully to {phone_number}")
            return {
                "success": True,
                "message": "WhatsApp message sent successfully",
                "notification_type": NotificationType.WHATSAPP.value,
                "recipient": phone_number,
                "status": NotificationStatus.SENT.value,
                "twilio_sid": message_obj.sid,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message to {phone_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": NotificationType.WHATSAPP.value,
                "recipient": phone_number,
                "status": NotificationStatus.FAILED.value,
                "failed_at": datetime.utcnow().isoformat()
            }
    
    async def send_push_notification(self,
                                   user_id: str,
                                   title: str,
                                   body: str,
                                   data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send push notification (placeholder for now).
        
        Args:
            user_id: User identifier
            title: Notification title
            body: Notification body
            data: Optional additional data
            
        Returns:
            Dict containing notification result
        """
        # TODO: Implement web push notifications
        self.logger.info(f"Push notification queued for user {user_id}: {title}")
        return {
            "success": True,
            "message": "Push notification queued",
            "notification_type": NotificationType.PUSH.value,
            "recipient": user_id,
            "status": NotificationStatus.PENDING.value,
            "queued_at": datetime.utcnow().isoformat()
        }
    
    async def send_deadline_reminder(self,
                                   user_email: str,
                                   user_phone: Optional[str],
                                   deadline_title: str,
                                   deadline_date: datetime,
                                   deadline_url: Optional[str] = None,
                                   notification_types: List[NotificationType] = None,
                                   priority: str = "medium") -> List[Dict[str, Any]]:
        """
        Send deadline reminder via multiple channels.
        
        Args:
            user_email: User's email address
            user_phone: User's phone number (optional)
            deadline_title: Title of the deadline
            deadline_date: When the deadline is due
            deadline_url: Optional URL to the deadline source
            notification_types: List of notification types to send
            priority: Priority level (low, medium, high, urgent)
            
        Returns:
            List of notification results
        """
        if notification_types is None:
            notification_types = [NotificationType.EMAIL]
        
        results = []
        
        # Format the message
        time_until = deadline_date - datetime.utcnow()
        if time_until.days > 0:
            time_str = f"in {time_until.days} day{'s' if time_until.days > 1 else ''}"
        elif time_until.seconds > 3600:
            hours = time_until.seconds // 3600
            time_str = f"in {hours} hour{'s' if hours > 1 else ''}"
        else:
            time_str = "soon"
        
        # Email notification
        if NotificationType.EMAIL in notification_types:
            subject = f"🔔 Deadline Reminder: {deadline_title}"
            body = f"""
Hi there!

This is a reminder about your upcoming deadline:

📋 Task: {deadline_title}
⏰ Due: {deadline_date.strftime('%Y-%m-%d at %H:%M')} ({time_str})
🚨 Priority: {priority.upper()}
"""
            if deadline_url:
                body += f"\n🔗 Link: {deadline_url}"
            
            body += f"""

Don't forget to complete this task on time!

Best regards,
Your AI Cruel Deadline Manager
            """
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">🔔 Deadline Reminder</h2>
                    <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #2563eb;">
                        <h3 style="margin: 0 0 10px 0; color: #1e293b;">{deadline_title}</h3>
                        <p style="margin: 5px 0;"><strong>Due:</strong> {deadline_date.strftime('%Y-%m-%d at %H:%M')} ({time_str})</p>
                        <p style="margin: 5px 0;"><strong>Priority:</strong> <span style="color: #dc2626;">{priority.upper()}</span></p>
                        {f'<p style="margin: 5px 0;"><strong>Link:</strong> <a href="{deadline_url}">{deadline_url}</a></p>' if deadline_url else ''}
                    </div>
                    <p style="margin-top: 20px;">Don't forget to complete this task on time!</p>
                    <p style="color: #64748b; font-size: 14px;">Best regards,<br>Your AI Cruel Deadline Manager</p>
                </div>
            </body>
            </html>
            """
            
            result = await self.send_email_notification(user_email, subject, body, html_body)
            results.append(result)
        
        # SMS notification
        if NotificationType.SMS in notification_types and user_phone:
            sms_message = f"⏰ Deadline Reminder: {deadline_title} is due {time_str} ({deadline_date.strftime('%m/%d at %H:%M')}). Priority: {priority.upper()}"
            
            result = await self.send_sms_notification(user_phone, sms_message)
            results.append(result)
        
        # WhatsApp notification
        if NotificationType.WHATSAPP in notification_types and user_phone:
            whatsapp_message = f"""🔔 *Deadline Reminder*

📋 *Task:* {deadline_title}
⏰ *Due:* {deadline_date.strftime('%Y-%m-%d at %H:%M')} ({time_str})
🚨 *Priority:* {priority.upper()}

Don't forget to complete this task on time! 💪"""
            
            result = await self.send_whatsapp_notification(user_phone, whatsapp_message)
            results.append(result)
        
        # Push notification
        if NotificationType.PUSH in notification_types:
            result = await self.send_push_notification(
                user_email,  # Using email as user_id for now
                f"Deadline: {deadline_title}",
                f"Due {time_str} - Priority: {priority.upper()}",
                {"deadline_url": deadline_url, "priority": priority}
            )
            results.append(result)
        
        return results


# Initialize the global notification service
notification_service = EnhancedNotificationService()


def get_notification_service() -> EnhancedNotificationService:
    """Get the global notification service instance"""
    return notification_service


def initialize_notification_service() -> EnhancedNotificationService:
    """Initialize and return notification service"""
    return notification_service