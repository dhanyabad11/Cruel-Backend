"""
Canvas LMS Scraper Implementation

This module implements a scraper for Canvas Learning Management System
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


@register_scraper('canvas')
class CanvasScraper(BaseScraper):
    """Scraper for Canvas LMS to extract assignment deadlines."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = f"{self.base_url}/api/v1"
        
    async def authenticate(self) -> bool:
        """
        Authenticate with Canvas API using access token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        token = self.credentials.get('access_token')
        if not token:
            self.logger.error("Canvas access token not provided")
            return False
        
        # Test the token by getting user profile
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = await ScrapingUtils.make_request(
                f"{self.api_base}/users/self/profile", 
                headers=headers
            )
            if response and 'id' in response:
                self.logger.info(f"Canvas authentication successful for user: {response.get('name', 'Unknown')}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Canvas authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        access_token = self.credentials.get('access_token')
        if not access_token or not isinstance(access_token, str):
            return False
        
        # Validate Canvas URL
        if not self.base_url or not self._is_valid_canvas_url(self.base_url):
            return False
            
        return True
    
    def _is_valid_canvas_url(self, url: str) -> bool:
        """Check if URL is a valid Canvas instance URL."""
        try:
            parsed = urlparse(url)
            # Canvas URLs typically contain 'instructure' or end with common patterns
            domain_patterns = [
                'instructure.com',
                'canvas.',
                '.edu',
                'learning.',
                'lms.'
            ]
            return any(pattern in parsed.netloc.lower() for pattern in domain_patterns)
        except Exception:
            return False
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from Canvas courses.
        
        Returns:
            ScrapingResult: Result containing found deadlines and status
        """
        if not await self.authenticate():
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message="Authentication failed",
                errors=["Failed to authenticate with Canvas"]
            )
        
        deadlines = []
        errors = []
        
        try:
            # Get all courses for the user
            courses = await self._get_courses()
            self.logger.info(f"Found {len(courses)} Canvas courses")
            
            # Get assignments from each course
            for course in courses:
                try:
                    course_deadlines = await self._get_course_assignments(course)
                    deadlines.extend(course_deadlines)
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    error_msg = f"Failed to get assignments for course {course.get('name', 'Unknown')}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from Canvas",
                errors=errors,
                metadata={
                    'courses_count': len(courses),
                    'deadlines_count': len(deadlines)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Canvas scraping failed: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=deadlines,
                message="Scraping failed",
                errors=[str(e)]
            )
    
    async def _get_courses(self) -> List[Dict[str, Any]]:
        """Get all active courses for the user."""
        headers = {
            'Authorization': f'Bearer {self.credentials["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        # Get current enrollment courses
        courses_url = f"{self.api_base}/courses"
        params = {
            'enrollment_state': 'active',
            'state[]': 'available',
            'per_page': 100
        }
        
        try:
            response = await ScrapingUtils.make_request(
                courses_url,
                headers=headers,
                params=params
            )
            return response if isinstance(response, list) else []
        except Exception as e:
            self.logger.error(f"Failed to get courses: {e}")
            return []
    
    async def _get_course_assignments(self, course: Dict[str, Any]) -> List[ScrapedDeadline]:
        """Get assignments with due dates from a specific course."""
        headers = {
            'Authorization': f'Bearer {self.credentials["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        course_id = course.get('id')
        course_name = course.get('name', 'Unknown Course')
        
        assignments_url = f"{self.api_base}/courses/{course_id}/assignments"
        params = {
            'per_page': 100,
            'order_by': 'due_at'
        }
        
        deadlines = []
        
        try:
            assignments = await ScrapingUtils.make_request(
                assignments_url,
                headers=headers,
                params=params
            )
            
            if not isinstance(assignments, list):
                return deadlines
            
            for assignment in assignments:
                deadline = self._parse_assignment(assignment, course_name)
                if deadline:
                    deadlines.append(deadline)
            
            return deadlines
            
        except Exception as e:
            self.logger.error(f"Failed to get assignments for course {course_name}: {e}")
            return []
    
    def _parse_assignment(self, assignment: Dict[str, Any], course_name: str) -> Optional[ScrapedDeadline]:
        """Parse a Canvas assignment into a ScrapedDeadline."""
        try:
            # Check if assignment has a due date
            due_at = assignment.get('due_at')
            if not due_at:
                return None
            
            # Parse due date
            due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
            
            # Skip past assignments (older than 1 day)
            if due_date < datetime.now(timezone.utc) - timedelta(days=1):
                return None
            
            title = assignment.get('name', 'Untitled Assignment')
            description = assignment.get('description', '')
            
            # Clean HTML from description
            if description:
                description = ScrapingUtils.clean_html(description)
                # Limit description length
                if len(description) > 200:
                    description = description[:200] + "..."
            
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
            
            # Estimate hours based on points possible
            points_possible = assignment.get('points_possible', 0)
            estimated_hours = max(1, int(points_possible / 10)) if points_possible else None
            
            return ScrapedDeadline(
                title=f"[{course_name}] {title}",
                description=description,
                due_date=due_date,
                priority=priority,
                portal_task_id=str(assignment.get('id', '')),
                portal_url=assignment.get('html_url', ''),
                tags=[course_name, 'canvas', 'assignment'],
                estimated_hours=estimated_hours
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse assignment: {e}")
            return None