from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.portal import PortalType

class PortalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Portal type: github, jira, trello, asana, custom")
    url: str = Field(..., description="Base URL or API endpoint")
    sync_frequency: int = Field(3600, description="Sync frequency in seconds")
    auto_sync: bool = True

class PortalCreate(PortalBase):
    credentials: Dict[str, Any] = Field(..., description="Portal credentials (will be encrypted)")

class PortalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    sync_frequency: Optional[int] = None
    auto_sync: Optional[bool] = None
    is_active: Optional[bool] = None

class PortalResponse(PortalBase):
    id: int
    user_id: int
    is_active: bool
    last_sync: Optional[datetime] = None
    sync_status: str
    last_error: Optional[str] = None
    sync_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_due_for_sync: bool

    class Config:
        from_attributes = True

class PortalCredentials(BaseModel):
    """Base class for portal credentials"""
    pass

class GitHubCredentials(PortalCredentials):
    token: str = Field(..., description="GitHub personal access token")
    username: Optional[str] = None
    repositories: Optional[list] = Field(default=[], description="List of repos to monitor")

class JiraCredentials(PortalCredentials):
    email: str = Field(..., description="Jira account email")
    api_token: str = Field(..., description="Jira API token")
    domain: str = Field(..., description="Jira domain (e.g., yourcompany.atlassian.net)")
    projects: Optional[list] = Field(default=[], description="List of project keys to monitor")

class TrelloCredentials(PortalCredentials):
    api_key: str = Field(..., description="Trello API key")
    token: str = Field(..., description="Trello token")
    boards: Optional[list] = Field(default=[], description="List of board IDs to monitor")

class SyncResult(BaseModel):
    success: bool
    message: str
    deadlines_found: int
    deadlines_created: int
    deadlines_updated: int
    errors: Optional[list] = None