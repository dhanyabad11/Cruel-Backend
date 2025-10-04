from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict
from datetime import datetime
import re

# Notification Reminder Schema (for individual reminder configurations)
class NotificationReminderBase(BaseModel):
    reminder_time: str  # '1_hour', '6_hours', '1_day', '3_days', '1_week'
    email_enabled: bool = False
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    push_enabled: bool = False
    
    @validator('reminder_time')
    def validate_reminder_time(cls, v):
        valid_times = ['1_hour', '6_hours', '1_day', '3_days', '1_week']
        if v not in valid_times:
            raise ValueError(f'reminder_time must be one of: {valid_times}')
        return v

class NotificationReminderCreate(NotificationReminderBase):
    pass

class NotificationReminderUpdate(NotificationReminderBase):
    pass

class NotificationReminderResponse(NotificationReminderBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Main Notification Settings Schema
class NotificationSettingsBase(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    push_enabled: bool = True
    
    @validator('phone_number', 'whatsapp_number')
    def validate_phone_number(cls, v):
        if v is not None and v.strip():
            # Remove all non-digit characters
            phone = re.sub(r'[^\d]', '', v)
            # Check if it's an Indian number (10 digits) or international format
            if len(phone) == 10:
                return f"+91{phone}"
            elif len(phone) == 12 and phone.startswith('91'):
                return f"+{phone}"
            elif len(phone) == 13 and phone.startswith('91'):
                return f"+{phone[1:]}"
            else:
                raise ValueError('Phone number must be a valid Indian number (+91XXXXXXXXXX or XXXXXXXXXX)')
        return v

class NotificationSettingsCreate(NotificationSettingsBase):
    pass

class NotificationSettingsUpdate(NotificationSettingsBase):
    pass

class NotificationSettingsResponse(NotificationSettingsBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Combined Settings with Reminders
class NotificationSettingsWithReminders(BaseModel):
    settings: NotificationSettingsResponse
    reminders: List[NotificationReminderResponse]

# Bulk Reminder Update Schema
class BulkReminderUpdate(BaseModel):
    reminders: List[NotificationReminderBase]