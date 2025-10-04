from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    email = Column(String)
    phone_number = Column(String)
    whatsapp_number = Column(String) 
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    reminder_frequency = Column(String, default="1_day")  # '1_hour', '6_hours', '1_day', '3_days', '1_week'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)