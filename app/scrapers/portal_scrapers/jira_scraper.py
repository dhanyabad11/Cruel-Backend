"""
Jira Scraper Implementation

This module implements a scraper for Jira instances to extract deadlines
from tickets, sprints, and project milestones. It uses the Jira REST API.
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import base64

from ..base_scraper import BaseScraper, ScrapedDeadline, ScrapingResult, ScrapingStatus
from ..scraper_registry import register_scraper
from ..utils import ScrapingUtils


@register_scraper('jira')
class JiraScraper(BaseScraper):
    """Scraper for Jira instances to extract deadlines from tickets and sprints."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = self._get_api_base()
        self.date_patterns = [
            r'due[\s:]+(\d{4}-\d{2}-\d{2})',
            r'deadline[\s:]+(\d{4}-\d{2}-\d{2})',
            r'target[\s:]+(\d{4}-\d{2}-\d{2})',
            r'delivery[\s:]+(\d{4}-\d{2}-\d{2})',
            r'finish[\s:]by[\s:]+(\d{4}-\d{2}-\d{2})',
            r'complete[\s:]by[\s:]+(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})[\s:]+deadline',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2})',
        ]
    
    def _get_api_base(self) -> str:
        """Get the Jira API base URL from the base URL."""
        base_url = self.base_url.rstrip('/')
        if not base_url.endswith('/rest/api/2'):
            base_url = urljoin(base_url, '/rest/api/2')
        return base_url
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Jira API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        username = self.credentials.get('username')
        api_token = self.credentials.get('api_token')
        password = self.credentials.get('password')
        
        if not username:
            self.logger.error("Jira username is required")
            return False
        
        if not (api_token or password):
            self.logger.error("Jira API token or password is required")
            return False
        
        # Create basic auth header
        auth_string = f"{username}:{api_token or password}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_bytes}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Test authentication by getting current user info
        try:
            response = await ScrapingUtils.make_request(
                f"{self.api_base}/myself",
                headers=headers
            )
            return response is not None and 'accountId' in response
        except Exception as e:
            self.logger.error(f"Jira authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        username = self.credentials.get('username')
        api_token = self.credentials.get('api_token')
        password = self.credentials.get('password')
        
        if not username or not isinstance(username, str):
            return False
        
        if not (api_token or password):
            return False
        
        if api_token and not isinstance(api_token, str):
            return False
        
        if password and not isinstance(password, str):
            return False
        
        # Validate Jira URL
        if not self.base_url or not self._is_valid_jira_url(self.base_url):
            return False
            
        return True
    
    def _is_valid_jira_url(self, url: str) -> bool:
        """Check if URL is a valid Jira instance URL."""
        try:
            parsed = urlparse(url)
            if not parsed.netloc or not parsed.scheme:
                return False
            
            # Only allow http/https schemes
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for common Jira URL patterns
            netloc_lower = parsed.netloc.lower()
            
            # Atlassian Cloud instances
            if netloc_lower.endswith('.atlassian.net'):
                return True
            
            # On-premise instances (basic validation)
            # Must have a valid domain format
            if '.' in netloc_lower or 'localhost' in netloc_lower:
                return True
                
            return False
        except Exception:
            return False
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from Jira instance.
        
        Returns:
            ScrapingResult: Result containing scraped deadlines
        """
        try:
            # Authenticate first
            if not await self.authenticate():
                return ScrapingResult(
                    status=ScrapingStatus.ERROR,
                    deadlines=[],
                    message="Authentication failed",
                    errors=["Failed to authenticate with Jira"]
                )
            
            # Get authentication headers
            headers = self._get_auth_headers()
            
            deadlines = []
            
            # Scrape tickets/issues
            tickets_deadlines = await self._scrape_tickets(headers)
            deadlines.extend(tickets_deadlines)
            
            # Scrape sprints
            sprints_deadlines = await self._scrape_sprints(headers)
            deadlines.extend(sprints_deadlines)
            
            # Scrape versions/releases
            versions_deadlines = await self._scrape_versions(headers)
            deadlines.extend(versions_deadlines)
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from Jira",
                metadata={
                    'jira_url': self.base_url,
                    'total_deadlines': len(deadlines),
                    'projects_scanned': self.scrape_config.get('projects', [])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping Jira instance: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message=f"Scraping failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        username = self.credentials.get('username')
        api_token = self.credentials.get('api_token')
        password = self.credentials.get('password')
        
        auth_string = f"{username}:{api_token or password}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        return {
            'Authorization': f'Basic {auth_bytes}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    async def _scrape_tickets(self, headers: Dict[str, str]) -> List[ScrapedDeadline]:
        """Scrape deadlines from Jira tickets/issues."""
        deadlines = []
        
        # Build JQL query
        jql_conditions = []
        
        # Filter by projects if specified
        projects = self.scrape_config.get('projects', [])
        if projects:
            project_list = "', '".join(projects)
            jql_conditions.append(f"project in ('{project_list}')")
        
        # Filter by assignee if specified
        assignee = self.scrape_config.get('assignee')
        if assignee:
            jql_conditions.append(f"assignee = '{assignee}'")
        
        # Filter by status if specified
        statuses = self.scrape_config.get('statuses', [])
        if statuses:
            status_list = "', '".join(statuses)
            jql_conditions.append(f"status in ('{status_list}')")
        else:
            # Default: exclude resolved/closed issues
            jql_conditions.append("status not in ('Resolved', 'Closed', 'Done')")
        
        # Build final JQL
        jql = " AND ".join(jql_conditions) if jql_conditions else ""
        if not jql:
            jql = "status not in ('Resolved', 'Closed', 'Done')"
        
        # Add ordering
        jql += " ORDER BY created DESC"
        
        # Search for issues
        url = f"{self.api_base}/search"
        params = {
            'jql': jql,
            'maxResults': self.scrape_config.get('max_results', 100),
            'fields': 'key,summary,description,duedate,priority,status,assignee,created,updated,customfield_*'
        }
        
        try:
            response = await ScrapingUtils.make_request(url, headers=headers, params=params)
            if not response:
                return deadlines
            
            issues = response.get('issues', [])
            
            for issue in issues:
                deadline = await self._extract_deadline_from_ticket(issue)
                if deadline:
                    deadlines.append(deadline)
            
        except Exception as e:
            self.logger.error(f"Error scraping Jira tickets: {e}")
        
        return deadlines
    
    async def _scrape_sprints(self, headers: Dict[str, str]) -> List[ScrapedDeadline]:
        """Scrape deadlines from Jira sprints."""
        deadlines = []
        
        # Get projects to scan for sprints
        projects = self.scrape_config.get('projects', [])
        if not projects:
            return deadlines
        
        for project_key in projects:
            try:
                # Get boards for project
                boards_url = f"{self.api_base}/../agile/1.0/board"
                boards_params = {
                    'projectKeyOrId': project_key,
                    'type': 'scrum'
                }
                
                boards_response = await ScrapingUtils.make_request(
                    boards_url, headers=headers, params=boards_params
                )
                
                if not boards_response:
                    continue
                
                boards = boards_response.get('values', [])
                
                for board in boards:
                    board_id = board.get('id')
                    
                    # Get sprints for board
                    sprints_url = f"{self.api_base}/../agile/1.0/board/{board_id}/sprint"
                    sprints_params = {
                        'state': 'active,future'
                    }
                    
                    sprints_response = await ScrapingUtils.make_request(
                        sprints_url, headers=headers, params=sprints_params
                    )
                    
                    if not sprints_response:
                        continue
                    
                    sprints = sprints_response.get('values', [])
                    
                    for sprint in sprints:
                        deadline = self._extract_deadline_from_sprint(sprint, project_key)
                        if deadline:
                            deadlines.append(deadline)
            
            except Exception as e:
                self.logger.error(f"Error scraping sprints for project {project_key}: {e}")
        
        return deadlines
    
    async def _scrape_versions(self, headers: Dict[str, str]) -> List[ScrapedDeadline]:
        """Scrape deadlines from Jira versions/releases."""
        deadlines = []
        
        projects = self.scrape_config.get('projects', [])
        if not projects:
            return deadlines
        
        for project_key in projects:
            try:
                # Get versions for project
                url = f"{self.api_base}/project/{project_key}/versions"
                
                response = await ScrapingUtils.make_request(url, headers=headers)
                if not response:
                    continue
                
                versions = response if isinstance(response, list) else []
                
                for version in versions:
                    deadline = self._extract_deadline_from_version(version, project_key)
                    if deadline:
                        deadlines.append(deadline)
            
            except Exception as e:
                self.logger.error(f"Error scraping versions for project {project_key}: {e}")
        
        return deadlines
    
    async def _extract_deadline_from_ticket(self, issue: Dict[str, Any]) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a Jira ticket/issue."""
        fields = issue.get('fields', {})
        
        # Check for due date field
        due_date = fields.get('duedate')
        deadline_date = None
        
        if due_date:
            try:
                deadline_date = datetime.fromisoformat(due_date).replace(tzinfo=timezone.utc)
            except Exception:
                pass
        
        # If no due date, check description and summary for deadline mentions
        if not deadline_date:
            summary = fields.get('summary', '')
            description = fields.get('description', '') or ''
            deadline_date = self._parse_deadline_from_text(f"{summary} {description}")
        
        if not deadline_date:
            return None
        
        # Determine priority
        priority = self._determine_priority_from_jira_priority(fields.get('priority', {}))
        
        # Get assignee
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName') if assignee else None
        
        # Build tags
        tags = ['jira', 'ticket']
        if fields.get('status', {}).get('name'):
            tags.append(fields['status']['name'].lower())
        if fields.get('issuetype', {}).get('name'):
            tags.append(fields['issuetype']['name'].lower())
        
        return ScrapedDeadline(
            title=fields.get('summary', 'Untitled Issue'),
            description=self._truncate_text(fields.get('description', ''), 500),
            due_date=deadline_date,
            portal_url=f"{self.base_url.replace('/rest/api/2', '')}/browse/{issue.get('key')}",
            portal_task_id=issue.get('key', ''),
            priority=priority,
            tags=tags,
            estimated_hours=self._extract_time_estimate(fields)
        )
    
    def _extract_deadline_from_sprint(self, sprint: Dict[str, Any], project_key: str) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a Jira sprint."""
        end_date = sprint.get('endDate')
        if not end_date:
            return None
        
        try:
            deadline_date = datetime.fromisoformat(
                end_date.replace('Z', '+00:00')
            ).replace(tzinfo=timezone.utc)
        except Exception:
            return None
        
        state = sprint.get('state', 'unknown')
        priority = 'high' if state == 'active' else 'medium'
        
        return ScrapedDeadline(
            title=f"Sprint: {sprint.get('name', 'Untitled Sprint')}",
            description=f"Sprint end date for {project_key}",
            due_date=deadline_date,
            portal_url=f"{self.base_url.replace('/rest/api/2', '')}/secure/RapidBoard.jspa?rapidView={sprint.get('originBoardId', '')}",
            portal_task_id=str(sprint.get('id', '')),
            priority=priority,
            tags=['jira', 'sprint', state.lower()],
            estimated_hours=None
        )
    
    def _extract_deadline_from_version(self, version: Dict[str, Any], project_key: str) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a Jira version/release."""
        release_date = version.get('releaseDate')
        if not release_date:
            return None
        
        try:
            deadline_date = datetime.fromisoformat(release_date).replace(tzinfo=timezone.utc)
        except Exception:
            return None
        
        # Don't include released versions
        if version.get('released', False):
            return None
        
        return ScrapedDeadline(
            title=f"Release: {version.get('name', 'Untitled Release')}",
            description=version.get('description', f"Release version for {project_key}"),
            due_date=deadline_date,
            portal_url=f"{self.base_url.replace('/rest/api/2', '')}/projects/{project_key}",
            portal_task_id=str(version.get('id', '')),
            priority='high',
            tags=['jira', 'release', 'version'],
            estimated_hours=None
        )
    
    def _parse_deadline_from_text(self, text: str) -> Optional[datetime]:
        """Parse deadline from text using various patterns."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                try:
                    parsed_date = ScrapingUtils.parse_date(date_str)
                    if parsed_date:
                        return parsed_date
                except Exception:
                    continue
        
        return None
    
    def _determine_priority_from_jira_priority(self, priority: Dict[str, Any]) -> str:
        """Determine priority based on Jira priority field."""
        if not priority:
            return 'medium'
        
        priority_name = priority.get('name', '').lower()
        
        # High priority indicators
        if any(keyword in priority_name for keyword in ['highest', 'critical', 'blocker']):
            return 'high'
        
        # Low priority indicators
        if any(keyword in priority_name for keyword in ['lowest', 'trivial', 'minor']):
            return 'low'
        
        # Medium priority (default)
        return 'medium'
    
    def _extract_time_estimate(self, fields: Dict[str, Any]) -> Optional[int]:
        """Extract time estimate from Jira fields."""
        # Check common time tracking fields
        time_estimate = fields.get('timeoriginalestimate')
        if time_estimate:
            # Convert seconds to hours
            return int(time_estimate / 3600)
        
        # Check for custom fields that might contain estimates
        for field_name, field_value in fields.items():
            if 'estimate' in field_name.lower() and isinstance(field_value, (int, float)):
                return int(field_value)
        
        return None
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        if not text:
            return ''
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length] + '...'