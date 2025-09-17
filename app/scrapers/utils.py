import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
import json
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class ScrapingUtils:
    """Utility functions for web scraping"""
    
    @staticmethod
    async def make_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP request and return JSON response
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data
                ) as response:
                    if response.status >= 400:
                        logger.error(f"HTTP {response.status} error for {url}")
                        return None
                    
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        logger.warning(f"Non-JSON response from {url}: {content_type}")
                        return {"text": text}
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for {url}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return None
    
    @staticmethod
    def extract_urls(text: str, base_url: str = "") -> List[str]:
        """Extract URLs from text"""
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        urls = url_pattern.findall(text)
        
        # Also look for relative URLs if base_url is provided
        if base_url:
            relative_pattern = re.compile(r'(?:href|src)=["\']([^"\']+)["\']')
            relative_urls = relative_pattern.findall(text)
            for rel_url in relative_urls:
                if not rel_url.startswith(('http://', 'https://')):
                    full_url = urljoin(base_url, rel_url)
                    urls.append(full_url)
        
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def extract_dates(text: str) -> List[datetime]:
        """Extract dates from text using various patterns"""
        dates = []
        
        # Common date patterns
        patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',           # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',       # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',       # MM-DD-YYYY or DD-MM-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Try to parse the date
                parsed_date = ScrapingUtils.parse_flexible_date(match)
                if parsed_date:
                    dates.append(parsed_date)
        
        return dates
    
    @staticmethod
    def parse_flexible_date(date_str: str) -> Optional[datetime]:
        """Parse dates in various formats"""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%m/%d/%Y",
            "%d/%m/%Y", 
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%B %d %Y",
            "%b %d %Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def extract_priority_keywords(text: str) -> str:
        """Extract priority level from text"""
        text_lower = text.lower()
        
        # Priority keywords mapping
        priority_keywords = {
            "urgent": ["urgent", "critical", "blocker", "p0", "emergency"],
            "high": ["high", "important", "p1", "major"],
            "medium": ["medium", "normal", "p2", "moderate"],
            "low": ["low", "minor", "p3", "p4", "trivial", "nice to have"]
        }
        
        for priority, keywords in priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return priority
        
        return "medium"  # default
    
    @staticmethod
    def clean_html(html_text: str) -> str:
        """Remove HTML tags and clean text"""
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def rate_limit_delay(last_request_time: Optional[datetime], min_delay: float = 1.0) -> float:
        """Calculate delay needed to respect rate limits"""
        if not last_request_time:
            return 0.0
        
        now = datetime.now(timezone.utc)
        time_since_last = (now - last_request_time).total_seconds()
        
        if time_since_last < min_delay:
            return min_delay - time_since_last
        
        return 0.0

class APIHelper:
    """Helper class for API interactions"""
    
    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.default_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make GET request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status >= 400:
                    logger.error(f"GET {url} returned {response.status}")
                    return None
                return await response.json()
        except Exception as e:
            logger.error(f"GET {url} failed: {str(e)}")
            return None
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make POST request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status >= 400:
                    logger.error(f"POST {url} returned {response.status}")
                    return None
                return await response.json()
        except Exception as e:
            logger.error(f"POST {url} failed: {str(e)}")
            return None