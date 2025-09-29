"""
Blackboard Learn Scraper Implementation

This module implements a scraper for Blackboard Learn LMS
to extract assignment deadlines and due dates.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import asyncio

from ..base_scraper import BaseScraper, ScrapedDeadline, ScrapingResult, ScrapingStatus
from ..scraper_registry import register_scraper
from ..utils import ScrapingUtils


@register_scraper('blackboard')
class BlackboardScraper(BaseScraper):
    """Scraper for Blackboard Learn to extract assignment deadlines."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = f"{self.base_url}/learn/api/public/v1"
        self.session = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with Blackboard using username/password or API key.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        username = self.credentials.get('username')
        password = self.credentials.get('password')
        api_key = self.credentials.get('api_key')
        
        if api_key:
            return await self._authenticate_with_api_key(api_key)
        elif username and password:
            return await self._authenticate_with_credentials(username, password)
        else:
            self.logger.error("No valid Blackboard credentials provided")
            return False
    
    async def _authenticate_with_api_key(self, api_key: str) -> bool:
        """Authenticate using Blackboard REST API key."""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test API key by getting system version
            response = await ScrapingUtils.make_request(
                f"{self.api_base}/system/version",
                headers=headers
            )
            if response:
                self.logger.info("Blackboard API authentication successful")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Blackboard API authentication failed: {e}")
            return False
    
    async def _authenticate_with_credentials(self, username: str, password: str) -> bool:
        """Authenticate using username/password (web scraping approach)."""
        try:
            # This would require web scraping Blackboard's login page
            # For now, we'll return True and handle it in scrape_deadlines
            self.logger.info("Blackboard credential authentication not fully implemented")
            return True
        except Exception as e:
            self.logger.error(f"Blackboard credential authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        api_key = self.credentials.get('api_key')
        username = self.credentials.get('username')
        password = self.credentials.get('password')
        
        # Either API key or username/password required
        if not (api_key or (username and password)):
            return False
        
        # Validate Blackboard URL
        if not self.base_url or not self._is_valid_blackboard_url(self.base_url):
            return False
            
        return True
    
    def _is_valid_blackboard_url(self, url: str) -> bool:
        """Check if URL is a valid Blackboard instance URL."""
        try:
            parsed = urlparse(url)
            domain_patterns = [
                'blackboard',
                'bb.',
                'learn.',
                'mylms.',
                'elearn.'
            ]
            return any(pattern in parsed.netloc.lower() for pattern in domain_patterns)
        except Exception:
            return False
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from Blackboard courses.
        
        Returns:
            ScrapingResult: Result containing found deadlines and status
        """
        if not await self.authenticate():
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message="Authentication failed",
                errors=["Failed to authenticate with Blackboard"]
            )
        
        # Check if we have API access
        if self.credentials.get('api_key'):
            return await self._scrape_with_api()
        else:
            return await self._scrape_with_web_parsing()
    
    async def _scrape_with_api(self) -> ScrapingResult:
        """Scrape using Blackboard REST API."""
        deadlines = []
        errors = []
        
        headers = {
            'Authorization': f'Bearer {self.credentials["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get user's courses
            courses = await self._get_courses_api(headers)
            self.logger.info(f"Found {len(courses)} Blackboard courses")
            
            # Get assignments from each course
            for course in courses:
                try:
                    course_deadlines = await self._get_course_assignments_api(course, headers)
                    deadlines.extend(course_deadlines)
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    error_msg = f"Failed to get assignments for course {course.get('name', 'Unknown')}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from Blackboard",
                errors=errors,
                metadata={
                    'courses_count': len(courses),
                    'deadlines_count': len(deadlines)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Blackboard API scraping failed: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=deadlines,
                message="API scraping failed",
                errors=[str(e)]
            )
    
    async def _scrape_with_web_parsing(self) -> ScrapingResult:
        """Scrape using web parsing (fallback method)."""
        # For demonstration, return mock data
        # In real implementation, this would parse Blackboard's web interface
        mock_deadlines = [
            ScrapedDeadline(
                title="[Sample Course] Assignment 1",
                description="Sample assignment description",
                due_date=datetime.now(timezone.utc) + timedelta(days=3),
                priority="medium",
                portal_task_id="bb_sample_1",
                portal_url=f"{self.base_url}/webapps/assignment",
                tags=["blackboard", "assignment", "sample"],
                estimated_hours=2
            )
        ]
        
        return ScrapingResult(
            status=ScrapingStatus.SUCCESS,
            deadlines=mock_deadlines,
            message="Web scraping completed (demo mode)",
            errors=[],
            metadata={'demo_mode': True}
        )
    
    async def _get_courses_api(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get courses using Blackboard REST API."""
        try:
            courses_url = f"{self.api_base}/courses"
            params = {
                'limit': 100,
                'fields': 'id,courseId,name,description'
            }
            
            response = await ScrapingUtils.make_request(
                courses_url,
                headers=headers,
                params=params
            )
            
            if isinstance(response, dict) and 'results' in response:
                return response['results']
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get courses: {e}")
            return []
    
    async def _get_course_assignments_api(self, course: Dict[str, Any], headers: Dict[str, str]) -> List[ScrapedDeadline]:
        """Get assignments from a course using Blackboard REST API."""
        course_id = course.get('id')
        course_name = course.get('name', 'Unknown Course')
        
        assignments_url = f"{self.api_base}/courses/{course_id}/gradebook/columns"
        params = {
            'limit': 100
        }
        
        deadlines = []
        
        try:
            response = await ScrapingUtils.make_request(
                assignments_url,
                headers=headers,
                params=params
            )
            
            if isinstance(response, dict) and 'results' in response:
                assignments = response['results']
                
                for assignment in assignments:
                    deadline = self._parse_blackboard_assignment(assignment, course_name)
                    if deadline:
                        deadlines.append(deadline)
            
            return deadlines
            
        except Exception as e:
            self.logger.error(f"Failed to get assignments for course {course_name}: {e}")
            return []
    
    def _parse_blackboard_assignment(self, assignment: Dict[str, Any], course_name: str) -> Optional[ScrapedDeadline]:
        """Parse a Blackboard assignment into a ScrapedDeadline."""
        try:
            # Check if it's a gradable assignment with due date
            if assignment.get('type') != 'Assignment':
                return None
            
            due_date_str = assignment.get('dueDate')
            if not due_date_str:
                return None
            
            # Parse due date
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            
            # Skip past assignments
            if due_date < datetime.now(timezone.utc) - timedelta(days=1):
                return None
            
            title = assignment.get('name', 'Untitled Assignment')
            description = assignment.get('description', '')
            
            # Determine priority based on due date
            days_until_due = (due_date - datetime.now(timezone.utc)).days
            if days_until_due <= 1:
                priority = "urgent"
            elif days_until_due <= 3:
                priority = "high"
            elif days_until_due <= 7:
                priority = "medium"
            else:
                priority = "low"
            
            # Estimate hours based on points
            points = assignment.get('pointsPossible', 0)
            estimated_hours = max(1, int(points / 10)) if points else None
            
            return ScrapedDeadline(
                title=f"[{course_name}] {title}",
                description=description,
                due_date=due_date,
                priority=priority,
                portal_task_id=str(assignment.get('id', '')),
                portal_url=f"{self.base_url}/webapps/assignment/uploadAssignment",
                tags=[course_name, 'blackboard', 'assignment'],
                estimated_hours=estimated_hours
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Blackboard assignment: {e}")
            return None