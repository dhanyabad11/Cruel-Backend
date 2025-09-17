from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ScrapingStatus(Enum):
    """Status of scraping operation"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class ScrapedDeadline:
    """Data class for scraped deadline information"""
    title: str
    description: Optional[str]
    due_date: datetime
    priority: str = "medium"  # low, medium, high, urgent
    portal_task_id: str = ""
    portal_url: str = ""
    tags: Optional[List[str]] = None
    estimated_hours: Optional[int] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    status: ScrapingStatus
    deadlines: List[ScrapedDeadline]
    message: str = ""
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class BaseScraper(ABC):
    """Base class for all portal scrapers"""
    
    def __init__(self, portal_config: Dict[str, Any]):
        self.portal_config = portal_config
        self.portal_type = portal_config.get("type", "unknown")
        self.portal_name = portal_config.get("name", "Unknown Portal")
        self.base_url = portal_config.get("url", "")
        self.credentials = portal_config.get("credentials", {})
        self.scrape_config = portal_config.get("scrape_config", {})
        
        # Rate limiting
        self.rate_limit_delay = self.scrape_config.get("rate_limit_delay", 1.0)
        self.max_requests_per_minute = self.scrape_config.get("max_requests_per_minute", 60)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the portal
        Returns True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from the portal
        Returns ScrapingResult with found deadlines
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present
        Returns True if credentials are valid, False otherwise
        """
        pass
    
    def get_portal_info(self) -> Dict[str, Any]:
        """Get basic portal information"""
        return {
            "type": self.portal_type,
            "name": self.portal_name,
            "url": self.base_url,
            "supports_authentication": True,
            "supports_real_time": False,
        }
    
    def log_scraping_start(self):
        """Log the start of scraping operation"""
        self.logger.info(f"Starting scraping for {self.portal_name} ({self.portal_type})")
    
    def log_scraping_complete(self, result: ScrapingResult):
        """Log the completion of scraping operation"""
        self.logger.info(
            f"Scraping completed for {self.portal_name}. "
            f"Status: {result.status.value}, "
            f"Deadlines found: {len(result.deadlines)}"
        )
        
        if result.errors:
            for error in result.errors:
                self.logger.error(f"Scraping error: {error}")
    
    def create_error_result(self, message: str, errors: List[str] = None) -> ScrapingResult:
        """Create an error result"""
        return ScrapingResult(
            status=ScrapingStatus.ERROR,
            deadlines=[],
            message=message,
            errors=errors or [message]
        )
    
    def create_success_result(self, deadlines: List[ScrapedDeadline], message: str = "") -> ScrapingResult:
        """Create a success result"""
        return ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            deadlines=deadlines,
            message=message or f"Successfully scraped {len(deadlines)} deadlines"
        )
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse various date formats into datetime object
        Common formats: ISO 8601, RFC 3339, etc.
        """
        if not date_str:
            return None
            
        # Common date formats to try
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",           # ISO 8601 UTC
            "%Y-%m-%dT%H:%M:%S%z",          # ISO 8601 with timezone
            "%Y-%m-%d %H:%M:%S",            # Standard datetime
            "%Y-%m-%d",                     # Date only
            "%m/%d/%Y",                     # US format
            "%d/%m/%Y",                     # European format
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If no timezone info, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def normalize_priority(self, priority_str: str) -> str:
        """
        Normalize priority strings to standard values
        Returns: low, medium, high, urgent
        """
        if not priority_str:
            return "medium"
        
        priority_lower = priority_str.lower().strip()
        
        # Map various priority formats
        priority_map = {
            # Standard
            "low": "low",
            "medium": "medium", 
            "high": "high",
            "urgent": "urgent",
            "critical": "urgent",
            
            # Numbers
            "1": "low",
            "2": "medium", 
            "3": "high",
            "4": "urgent",
            "5": "urgent",
            
            # GitHub/Jira style
            "minor": "low",
            "major": "high", 
            "blocker": "urgent",
            "trivial": "low",
            
            # Other variations
            "p0": "urgent",
            "p1": "high",
            "p2": "medium", 
            "p3": "low",
            "p4": "low",
        }
        
        return priority_map.get(priority_lower, "medium")