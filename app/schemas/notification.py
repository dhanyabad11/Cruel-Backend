"""
Notification Schemas

Pydantic schemas for notification-related API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator


class NotificationCreate(BaseModel):
    """Schema for creating a new notification"""
    deadline_id: Optional[int] = None
    notification_type: str = Field(..., pattern="^(sms|whatsapp)$")
    phone_number: str = Field(..., min_length=10, max_length=20)
    message_content: str = Field(..., min_length=1, max_length=1600)  # SMS limit
    notification_reason: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove common separators and spaces
        cleaned = ''.join(c for c in v if c.isdigit() or c in ['+'])
        if not cleaned.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optional +')
        if len(cleaned.replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    status: Optional[str] = Field(None, pattern="^(pending|sent|delivered|failed)$")
    message_sid: Optional[str] = None
    twilio_status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


    class NotificationPreferenceBase(BaseModel):
        preferred_method: str = Field(default="email", description="Preferred notification method: email, sms, whatsapp")
        phone_number: Optional[str] = None
        email: Optional[EmailStr] = None

    class NotificationPreferenceCreate(NotificationPreferenceBase):
        pass

    class NotificationPreferenceUpdate(NotificationPreferenceBase):
        pass

    class NotificationPreferenceResponse(NotificationPreferenceBase):
        id: int
        user_id: int
        created_at: Optional[str]
        updated_at: Optional[str]
class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int
    deadline_id: Optional[int]
    notification_type: str
    phone_number: str
    message_content: str
    message_sid: Optional[str]
    twilio_status: Optional[str]
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_code: Optional[str]
    error_message: Optional[str]
    notification_reason: Optional[str]
    scheduled_for: Optional[datetime]
    retry_count: int
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceCreate(BaseModel):
    """Schema for creating notification preferences"""
    phone_number: Optional[str] = None
    preferred_method: str = Field(default='sms', pattern="^(sms|whatsapp)$")
    daily_summary_enabled: bool = True
    daily_summary_time: str = Field(default='09:00', pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    reminder_enabled: bool = True
    reminder_hours_before: str = Field(default='24,4,1')
    overdue_alerts_enabled: bool = True
    weekend_notifications: bool = False
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = Field(default='22:00', pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str = Field(default='08:00', pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field(default='UTC', max_length=50)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Remove common separators and spaces
        cleaned = ''.join(c for c in v if c.isdigit() or c in ['+'])
        if not cleaned.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optional +')
        if len(cleaned.replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned

    @validator('reminder_hours_before')
    def validate_reminder_hours(cls, v):
        try:
            hours = [int(h.strip()) for h in v.split(',') if h.strip()]
            if not hours:
                raise ValueError('At least one reminder hour must be specified')
            for hour in hours:
                if hour < 0 or hour > 168:  # Max 1 week (168 hours)
                    raise ValueError('Reminder hours must be between 0 and 168')
            return ','.join(map(str, sorted(set(hours), reverse=True)))
        except ValueError as e:
            if 'invalid literal' in str(e):
                raise ValueError('Reminder hours must be comma-separated integers')
            raise e


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences"""
    phone_number: Optional[str] = None
    preferred_method: Optional[str] = Field(None, pattern="^(sms|whatsapp)$")
    daily_summary_enabled: Optional[bool] = None
    daily_summary_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    reminder_enabled: Optional[bool] = None
    reminder_hours_before: Optional[str] = None
    overdue_alerts_enabled: Optional[bool] = None
    weekend_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = Field(None, max_length=50)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Remove common separators and spaces
        cleaned = ''.join(c for c in v if c.isdigit() or c in ['+'])
        if not cleaned.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optional +')
        if len(cleaned.replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned

    @validator('reminder_hours_before')
    def validate_reminder_hours(cls, v):
        if v is None:
            return v
        try:
            hours = [int(h.strip()) for h in v.split(',') if h.strip()]
            if not hours:
                raise ValueError('At least one reminder hour must be specified')
            for hour in hours:
                if hour < 0 or hour > 168:  # Max 1 week (168 hours)
                    raise ValueError('Reminder hours must be between 0 and 168')
            return ','.join(map(str, sorted(set(hours), reverse=True)))
        except ValueError as e:
            if 'invalid literal' in str(e):
                raise ValueError('Reminder hours must be comma-separated integers')
            raise e


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response"""
    id: int
    user_id: int
    phone_number: Optional[str]
    preferred_method: str
    daily_summary_enabled: bool
    daily_summary_time: str
    reminder_enabled: bool
    reminder_hours_before: str
    overdue_alerts_enabled: bool
    weekend_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SendNotificationRequest(BaseModel):
    """Schema for sending a notification"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=1600)
    notification_type: str = Field(default='sms', pattern="^(sms|whatsapp)$")
    deadline_id: Optional[int] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove common separators and spaces
        cleaned = ''.join(c for c in v if c.isdigit() or c in ['+'])
        if not cleaned.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optional +')
        if len(cleaned.replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned


class SendDeadlineReminderRequest(BaseModel):
    """Schema for sending a deadline reminder"""
    deadline_id: int
    phone_number: Optional[str] = None  # If not provided, use user's preference
    notification_type: Optional[str] = Field(None, pattern="^(sms|whatsapp)$")  # If not provided, use user's preference


class SendDailySummaryRequest(BaseModel):
    """Schema for sending daily summary"""
    phone_number: Optional[str] = None  # If not provided, use user's preference
    notification_type: Optional[str] = Field(None, pattern="^(sms|whatsapp)$")  # If not provided, use user's preference
    date: Optional[str] = None  # YYYY-MM-DD format, default to today


class NotificationStatusResponse(BaseModel):
    """Schema for notification status response"""
    message_sid: str
    status: str
    twilio_status: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    date_sent: Optional[datetime]
    date_updated: Optional[datetime]


class NotificationSendResponse(BaseModel):
    """Schema for notification send response"""
    success: bool
    message_sid: Optional[str]
    status: str
    error: Optional[str] = None
    notification_id: Optional[int] = None
    to: Optional[str] = None
    from_: Optional[str] = Field(None, alias='from')
    type: str

    class Config:
        populate_by_name = True


class NotificationListResponse(BaseModel):
    """Schema for notification list response"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics"""
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    recent_notifications: List[NotificationResponse]