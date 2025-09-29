"""
Moodle LMS Scraper Implementation

This module implements a scraper for Moodle Learning Management System
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


@register_scraper('moodle')
class MoodleScraper(BaseScraper):
    """Scraper for Moodle LMS to extract assignment deadlines."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = f"{self.base_url}/webservice/rest/server.php"
        self.web_service_token = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with Moodle using username/password or web service token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        token = self.credentials.get('webservice_token')
        username = self.credentials.get('username')
        password = self.credentials.get('password')
        
        if token:
            return await self._authenticate_with_token(token)
        elif username and password:
            return await self._authenticate_with_credentials(username, password)
        else:
            self.logger.error("No valid Moodle credentials provided")
            return False
    
    async def _authenticate_with_token(self, token: str) -> bool:
        """Authenticate using Moodle web service token."""
        try:
            # Test token by getting site info
            params = {
                'wstoken': token,
                'wsfunction': 'core_webservice_get_site_info',
                'moodlewsrestformat': 'json'
            }
            
            response = await ScrapingUtils.make_request(
                self.api_base,
                params=params
            )
            
            if response and 'sitename' in response:
                self.web_service_token = token
                self.logger.info(f"Moodle authentication successful for site: {response.get('sitename')}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Moodle token authentication failed: {e}")
            return False
    
    async def _authenticate_with_credentials(self, username: str, password: str) -> bool:
        """Authenticate using username/password to get web service token."""
        try:
            # Get token using login credentials
            login_url = f"{self.base_url}/login/token.php"
            params = {
                'username': username,
                'password': password,
                'service': 'moodle_mobile_app'  # or custom service
            }
            
            response = await ScrapingUtils.make_request(
                login_url,
                params=params
            )
            
            if response and 'token' in response:
                self.web_service_token = response['token']
                self.logger.info("Moodle credential authentication successful")
                return True
            else:
                self.logger.error("Failed to get Moodle web service token")
                return False
                
        except Exception as e:
            self.logger.error(f"Moodle credential authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        token = self.credentials.get('webservice_token')
        username = self.credentials.get('username')
        password = self.credentials.get('password')
        
        # Either token or username/password required
        if not (token or (username and password)):
            return False
        
        # Validate Moodle URL
        if not self.base_url or not self._is_valid_moodle_url(self.base_url):
            return False
            
        return True
    
    def _is_valid_moodle_url(self, url: str) -> bool:
        """Check if URL is a valid Moodle instance URL."""
        try:
            parsed = urlparse(url)
            # Check for common Moodle indicators
            domain_patterns = [
                'moodle',
                'lms.',
                'elearning.',
                'learn.',
                '.edu'
            ]
            return any(pattern in parsed.netloc.lower() for pattern in domain_patterns)
        except Exception:
            return False
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from Moodle courses.
        
        Returns:
            ScrapingResult: Result containing found deadlines and status
        """
        if not await self.authenticate():
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message="Authentication failed",
                errors=["Failed to authenticate with Moodle"]
            )
        
        deadlines = []
        errors = []
        
        try:
            # Get user's enrolled courses
            courses = await self._get_enrolled_courses()
            self.logger.info(f"Found {len(courses)} Moodle courses")
            
            # Get assignments from each course
            for course in courses:
                try:
                    course_deadlines = await self._get_course_assignments(course)
                    deadlines.extend(course_deadlines)
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    error_msg = f"Failed to get assignments for course {course.get('fullname', 'Unknown')}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from Moodle",
                errors=errors,
                metadata={
                    'courses_count': len(courses),
                    'deadlines_count': len(deadlines)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Moodle scraping failed: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=deadlines,
                message="Scraping failed",
                errors=[str(e)]
            )
    
    async def _get_enrolled_courses(self) -> List[Dict[str, Any]]:
        """Get courses the user is enrolled in."""
        try:
            params = {
                'wstoken': self.web_service_token,
                'wsfunction': 'core_enrol_get_users_courses',
                'moodlewsrestformat': 'json',
                'userid': 0  # 0 means current user
            }
            
            response = await ScrapingUtils.make_request(
                self.api_base,
                params=params
            )
            
            return response if isinstance(response, list) else []
            
        except Exception as e:
            self.logger.error(f"Failed to get enrolled courses: {e}")
            return []
    
    async def _get_course_assignments(self, course: Dict[str, Any]) -> List[ScrapedDeadline]:
        """Get assignments from a specific course."""
        course_id = course.get('id')
        course_name = course.get('fullname', 'Unknown Course')
        
        deadlines = []
        
        try:
            # Get course assignments
            assignments = await self._get_assignments_by_course(course_id)
            
            for assignment in assignments:
                deadline = self._parse_moodle_assignment(assignment, course_name)
                if deadline:
                    deadlines.append(deadline)
            
            # Also get upcoming events (which may include assignment due dates)
            events = await self._get_course_events(course_id)
            for event in events:
                deadline = self._parse_moodle_event(event, course_name)
                if deadline:
                    deadlines.append(deadline)
            
            return deadlines
            
        except Exception as e:
            self.logger.error(f"Failed to get assignments for course {course_name}: {e}")
            return []
    
    async def _get_assignments_by_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Get assignments for a specific course."""
        try:
            params = {
                'wstoken': self.web_service_token,
                'wsfunction': 'mod_assign_get_assignments',
                'moodlewsrestformat': 'json',
                'courseids[0]': course_id
            }
            
            response = await ScrapingUtils.make_request(
                self.api_base,
                params=params
            )
            
            if isinstance(response, dict) and 'courses' in response:
                courses = response['courses']
                if courses and len(courses) > 0:
                    return courses[0].get('assignments', [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get assignments for course {course_id}: {e}")
            return []
    
    async def _get_course_events(self, course_id: int) -> List[Dict[str, Any]]:
        """Get upcoming events for a course."""
        try:
            # Get events for the next 30 days
            time_start = int(datetime.now(timezone.utc).timestamp())
            time_end = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
            
            params = {
                'wstoken': self.web_service_token,
                'wsfunction': 'core_calendar_get_calendar_events',
                'moodlewsrestformat': 'json',
                'events[courseids][0]': course_id,
                'options[timestart]': time_start,
                'options[timeend]': time_end
            }
            
            response = await ScrapingUtils.make_request(
                self.api_base,
                params=params
            )
            
            if isinstance(response, dict) and 'events' in response:
                return response['events']
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get events for course {course_id}: {e}")
            return []
    
    def _parse_moodle_assignment(self, assignment: Dict[str, Any], course_name: str) -> Optional[ScrapedDeadline]:
        """Parse a Moodle assignment into a ScrapedDeadline."""
        try:
            due_date = assignment.get('duedate', 0)
            if not due_date or due_date == 0:
                return None
            
            # Convert timestamp to datetime
            due_datetime = datetime.fromtimestamp(due_date, tz=timezone.utc)
            
            # Skip past assignments
            if due_datetime < datetime.now(timezone.utc) - timedelta(days=1):
                return None
            
            title = assignment.get('name', 'Untitled Assignment')
            description = assignment.get('intro', '')
            
            # Clean HTML from description
            if description:
                description = ScrapingUtils.clean_html(description)
                if len(description) > 200:
                    description = description[:200] + "..."
            
            # Determine priority based on due date
            days_until_due = (due_datetime - datetime.now(timezone.utc)).days
            if days_until_due <= 1:
                priority = "urgent"
            elif days_until_due <= 3:
                priority = "high"
            elif days_until_due <= 7:
                priority = "medium"
            else:
                priority = "low"
            
            return ScrapedDeadline(
                title=f"[{course_name}] {title}",
                description=description,
                due_date=due_datetime,
                priority=priority,
                portal_task_id=str(assignment.get('id', '')),
                portal_url=f"{self.base_url}/mod/assign/view.php?id={assignment.get('cmid', '')}",
                tags=[course_name, 'moodle', 'assignment'],
                estimated_hours=2  # Default estimation
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Moodle assignment: {e}")
            return None
    
    def _parse_moodle_event(self, event: Dict[str, Any], course_name: str) -> Optional[ScrapedDeadline]:
        """Parse a Moodle calendar event into a ScrapedDeadline."""
        try:
            # Only process assignment-related events
            event_type = event.get('eventtype', '')
            if 'due' not in event_type.lower() and 'assignment' not in event.get('name', '').lower():
                return None
            
            time_start = event.get('timestart', 0)
            if not time_start:
                return None
            
            # Convert timestamp to datetime
            due_datetime = datetime.fromtimestamp(time_start, tz=timezone.utc)
            
            # Skip past events
            if due_datetime < datetime.now(timezone.utc) - timedelta(days=1):
                return None
            
            title = event.get('name', 'Untitled Event')
            description = event.get('description', '')
            
            # Clean HTML from description
            if description:
                description = ScrapingUtils.clean_html(description)
                if len(description) > 200:
                    description = description[:200] + "..."
            
            # Determine priority based on due date
            days_until_due = (due_datetime - datetime.now(timezone.utc)).days
            if days_until_due <= 1:
                priority = "urgent"
            elif days_until_due <= 3:
                priority = "high"
            elif days_until_due <= 7:
                priority = "medium"
            else:
                priority = "low"
            
            return ScrapedDeadline(
                title=f"[{course_name}] {title}",
                description=description,
                due_date=due_datetime,
                priority=priority,
                portal_task_id=str(event.get('id', '')),
                portal_url=event.get('url', ''),
                tags=[course_name, 'moodle', 'event'],
                estimated_hours=1
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Moodle event: {e}")
            return None