"""
Notification Model

Database model for tracking sent notifications and their delivery status.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class Notification(Base):
    """Model for tracking sent notifications"""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="notifications")
    
    # Deadline relationship (optional - some notifications might not be deadline-specific)
    deadline_id = Column(Integer, ForeignKey("deadlines.id"), nullable=True)
    deadline = relationship("Deadline", back_populates="notifications")
    
    # Notification details
    notification_type = Column(String(20), nullable=False)  # 'sms' or 'whatsapp'
    phone_number = Column(String(20), nullable=False)
    message_content = Column(Text, nullable=False)
    
    # Twilio details
    message_sid = Column(String(100), nullable=True)  # Twilio message SID
    twilio_status = Column(String(20), nullable=True)  # Twilio delivery status
    
    # Our tracking
    status = Column(String(20), nullable=False, default='pending')  # pending, sent, delivered, failed
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_code = Column(String(10), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    notification_reason = Column(String(50), nullable=True)  # 'reminder', 'daily_summary', 'overdue_alert', etc.
    scheduled_for = Column(DateTime, nullable=True)  # When the notification was scheduled to be sent
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Additional data (JSON field for flexible storage)
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'deadline_id': self.deadline_id,
            'notification_type': self.notification_type,
            'phone_number': self.phone_number,
            'message_content': self.message_content,
            'message_sid': self.message_sid,
            'twilio_status': self.twilio_status,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'notification_reason': self.notification_reason,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'retry_count': self.retry_count,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_status(self, status: str, **kwargs):
        """Update notification status with timestamp"""
        self.status = status
        
        if status == 'sent' and 'sent_at' not in kwargs:
            kwargs['sent_at'] = datetime.utcnow()
        elif status == 'delivered' and 'delivered_at' not in kwargs:
            kwargs['delivered_at'] = datetime.utcnow()
        elif status == 'failed' and 'failed_at' not in kwargs:
            kwargs['failed_at'] = datetime.utcnow()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def increment_retry_count(self):
        """Increment the retry count"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()


# Add notification preferences to User model
class NotificationPreference(Base):
    """Model for user notification preferences"""
    
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="notification_preferences")
    
    # Contact preferences
    phone_number = Column(String(20), nullable=True)
    preferred_method = Column(String(20), nullable=False, default='sms')  # 'sms' or 'whatsapp'
    
    # Notification timing preferences
    daily_summary_enabled = Column(Boolean, nullable=False, default=True)
    daily_summary_time = Column(String(5), nullable=False, default='09:00')  # HH:MM format
    
    reminder_enabled = Column(Boolean, nullable=False, default=True)
    reminder_hours_before = Column(String(20), nullable=False, default='24,4,1')  # Hours before deadline
    
    overdue_alerts_enabled = Column(Boolean, nullable=False, default=True)
    weekend_notifications = Column(Boolean, nullable=False, default=False)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, nullable=False, default=True)
    quiet_hours_start = Column(String(5), nullable=False, default='22:00')  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=False, default='08:00')   # HH:MM format
    
    # Timezone
    timezone = Column(String(50), nullable=False, default='UTC')
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id}, method={self.preferred_method}, phone={self.phone_number})>"
    
    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'preferred_method': self.preferred_method,
            'daily_summary_enabled': self.daily_summary_enabled,
            'daily_summary_time': self.daily_summary_time,
            'reminder_enabled': self.reminder_enabled,
            'reminder_hours_before': self.reminder_hours_before,
            'overdue_alerts_enabled': self.overdue_alerts_enabled,
            'weekend_notifications': self.weekend_notifications,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_reminder_hours_list(self):
        """Get reminder hours as a list of integers"""
        try:
            return [int(h.strip()) for h in self.reminder_hours_before.split(',') if h.strip()]
        except (ValueError, AttributeError):
            return [24, 4, 1]  # Default reminder hours
    
    def is_quiet_time(self, check_time: datetime = None) -> bool:
        """Check if the given time falls within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        if check_time is None:
            check_time = datetime.now()
        
        # Convert to time objects for comparison
        current_time = check_time.time()
        start_time = datetime.strptime(self.quiet_hours_start, '%H:%M').time()
        end_time = datetime.strptime(self.quiet_hours_end, '%H:%M').time()
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time