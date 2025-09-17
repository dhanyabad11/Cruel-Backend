from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class PortalType(enum.Enum):
    GITHUB = "github"
    JIRA = "jira"
    TRELLO = "trello"
    ASANA = "asana"
    CUSTOM = "custom"

class Portal(Base):
    __tablename__ = "portals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "My GitHub", "Work Jira"
    type = Column(String(50), nullable=False)  # github, jira, trello, asana, custom
    url = Column(String(500), nullable=False)  # Base URL or API endpoint
    
    # Encrypted credentials (stored as JSON)
    credentials = Column(JSON)  # Will store encrypted API keys, tokens, etc.
    
    # Scraping configuration
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))
    sync_frequency = Column(Integer, default=3600)  # Seconds between syncs (default 1 hour)
    auto_sync = Column(Boolean, default=True)
    
    # Scraping settings
    scrape_config = Column(JSON)  # Store specific scraping rules per portal
    
    # Status tracking
    sync_status = Column(String(50), default="idle")  # idle, syncing, error, success
    last_error = Column(Text)
    sync_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portals")
    deadlines = relationship("Deadline", back_populates="portal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portal(id={self.id}, name={self.name}, type={self.type})>"
    
    @property
    def is_due_for_sync(self):
        if not self.auto_sync or not self.is_active:
            return False
        if not self.last_sync:
            return True
        from datetime import datetime, timezone
        time_since_sync = (datetime.now(timezone.utc) - self.last_sync).total_seconds()
        return time_since_sync >= self.sync_frequency