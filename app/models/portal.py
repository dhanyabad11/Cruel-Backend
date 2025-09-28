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
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # github, jira, trello, etc.
    url = Column(String(500), nullable=False)
    api_key = Column(Text)  # Encrypted API key
    username = Column(String(100))
    access_token = Column(Text)  # Encrypted access token
    refresh_token = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(DateTime(timezone=True))

    # Sync configuration
    sync_enabled = Column(Boolean, default=True)
    sync_frequency = Column(Integer, default=3600)  # seconds
    last_sync = Column(DateTime(timezone=True))
    sync_status = Column(String(50), default="idle")  # idle, running, error

    # Metadata
    config = Column(JSON)  # Additional configuration as JSON
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portals")
    deadlines = relationship("Deadline", back_populates="portal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portal(id={self.id}, name={self.name}, type={self.type})>"