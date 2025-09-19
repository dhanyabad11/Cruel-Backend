from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class PriorityLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class StatusLevel(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class Deadline(Base):
    __tablename__ = "deadlines"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True), nullable=False)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.MEDIUM)
    status = Column(Enum(StatusLevel), default=StatusLevel.PENDING)
    
    # Portal integration fields
    portal_id = Column(Integer, ForeignKey("portals.id"))
    portal_task_id = Column(String(100))  # ID from the source portal (e.g., GitHub issue ID)
    portal_url = Column(String(500))  # Direct link to the task in portal
    
    # Notification tracking
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime(timezone=True))
    
    # Metadata
    tags = Column(Text)  # JSON string for tags
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="deadlines")
    portal = relationship("Portal", back_populates="deadlines")
    notifications = relationship("Notification", back_populates="deadline", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Deadline(id={self.id}, title={self.title}, due_date={self.due_date})>"
    
    @property
    def is_overdue(self):
        from datetime import datetime, timezone
        return self.due_date < datetime.now(timezone.utc) and self.status != StatusLevel.COMPLETED
    
    @property
    def days_until_due(self):
        from datetime import datetime, timezone
        delta = self.due_date - datetime.now(timezone.utc)
        return delta.days