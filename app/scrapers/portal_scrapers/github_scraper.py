"""
GitHub Scraper Implementation

This module implements a scraper for GitHub repositories to extract deadlines
from Issues and Pull Requests. It uses the GitHub API to fetch data.
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from ..base_scraper import BaseScraper, ScrapedDeadline, ScrapingResult, ScrapingStatus
from ..scraper_registry import register_scraper
from ..utils import ScrapingUtils


@register_scraper('github')
class GitHubScraper(BaseScraper):
    """Scraper for GitHub repositories to extract deadlines from Issues and PRs."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = "https://api.github.com"
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
    
    async def authenticate(self) -> bool:
        """
        Authenticate with GitHub API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        token = self.credentials.get('token')
        if not token:
            # No token provided, can still use public API with rate limits
            self.logger.info("No GitHub token provided, using public API with rate limits")
            return True
        
        # Test the token by making a simple API call
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}',
            'User-Agent': 'AI-Cruel-Deadline-Manager'
        }
        
        try:
            response = await ScrapingUtils.make_request(
                f"{self.api_base}/user", 
                headers=headers
            )
            return response is not None
        except Exception as e:
            self.logger.error(f"GitHub authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        # GitHub token is optional for public repositories
        token = self.credentials.get('token')
        if token and not isinstance(token, str):
            return False
        
        # Validate repository URL
        repo_url = self.scrape_config.get('repo_url') or self.base_url
        if not repo_url or not self._is_valid_github_url(repo_url):
            return False
            
        return True
    
    def _is_valid_github_url(self, url: str) -> bool:
        """Check if URL is a valid GitHub repository URL."""
        try:
            parsed = urlparse(url)
            if parsed.netloc.lower() not in ['github.com', 'www.github.com']:
                return False
            
            # Check path format: /owner/repo
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) < 2:
                return False
                
            return True
        except Exception:
            return False
    
    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        parsed = urlparse(repo_url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        
        raise ValueError(f"Invalid GitHub URL format: {repo_url}")
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from GitHub repository.
        
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
                    errors=["Failed to authenticate with GitHub"]
                )
            
            # Get configuration
            repo_url = self.scrape_config.get('repo_url') or self.base_url
            if not repo_url:
                return ScrapingResult(
                    status=ScrapingStatus.ERROR,
                    deadlines=[],
                    message="No repository URL provided",
                    errors=["repo_url is required in configuration"]
                )
            
            owner, repo = self._extract_repo_info(repo_url)
            token = self.credentials.get('token')
            include_closed = self.scrape_config.get('include_closed', False)
            milestone_filter = self.scrape_config.get('milestone_filter')
            
            # Set up headers for API requests
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'AI-Cruel-Deadline-Manager'
            }
            if token:
                headers['Authorization'] = f'token {token}'
            
            deadlines = []
            
            # Scrape issues
            issues_deadlines = await self._scrape_issues(
                owner, repo, headers, include_closed, milestone_filter
            )
            deadlines.extend(issues_deadlines)
            
            # Scrape pull requests
            prs_deadlines = await self._scrape_pull_requests(
                owner, repo, headers, include_closed
            )
            deadlines.extend(prs_deadlines)
            
            # Scrape milestones
            milestone_deadlines = await self._scrape_milestones(
                owner, repo, headers, milestone_filter
            )
            deadlines.extend(milestone_deadlines)
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from {owner}/{repo}",
                metadata={
                    'repository': f"{owner}/{repo}",
                    'include_closed': include_closed,
                    'milestone_filter': milestone_filter,
                    'total_deadlines': len(deadlines)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping GitHub repository: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message=f"Scraping failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _scrape_issues(
        self, 
        owner: str, 
        repo: str, 
        headers: Dict[str, str],
        include_closed: bool = False,
        milestone_filter: Optional[str] = None
    ) -> List[ScrapedDeadline]:
        """Scrape deadlines from GitHub issues."""
        deadlines = []
        
        # Build API URL
        state = 'all' if include_closed else 'open'
        url = f"{self.api_base}/repos/{owner}/{repo}/issues"
        params = {
            'state': state,
            'per_page': 100
        }
        
        if milestone_filter:
            # First, get milestone number
            milestone_number = await self._get_milestone_number(
                owner, repo, milestone_filter, headers
            )
            if milestone_number:
                params['milestone'] = milestone_number
        
        page = 1
        while True:
            params['page'] = page
            
            try:
                response = await ScrapingUtils.make_request(url, headers=headers, params=params)
                if not response:
                    break
                
                issues = response  # GitHub API returns array directly
                if not issues:
                    break
                
                for issue in issues:
                    # Skip pull requests (they appear in issues API)
                    if 'pull_request' in issue:
                        continue
                    
                    deadline = await self._extract_deadline_from_issue(issue, owner, repo)
                    if deadline:
                        deadlines.append(deadline)
                
                # Check if there are more pages
                if len(issues) < 100:
                    break
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error scraping issues for {owner}/{repo}: {e}")
                break
        
        return deadlines
    
    async def _scrape_pull_requests(
        self, 
        owner: str, 
        repo: str, 
        headers: Dict[str, str],
        include_closed: bool = False
    ) -> List[ScrapedDeadline]:
        """Scrape deadlines from GitHub pull requests."""
        deadlines = []
        
        # Build API URL
        state = 'all' if include_closed else 'open'
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
        params = {
            'state': state,
            'per_page': 100
        }
        
        page = 1
        while True:
            params['page'] = page
            
            try:
                response = await ScrapingUtils.make_request(url, headers=headers, params=params)
                if not response:
                    break
                
                pulls = response  # GitHub API returns array directly
                if not pulls:
                    break
                
                for pr in pulls:
                    deadline = await self._extract_deadline_from_pr(pr, owner, repo)
                    if deadline:
                        deadlines.append(deadline)
                
                # Check if there are more pages
                if len(pulls) < 100:
                    break
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error scraping PRs for {owner}/{repo}: {e}")
                break
        
        return deadlines
    
    async def _scrape_milestones(
        self, 
        owner: str, 
        repo: str, 
        headers: Dict[str, str],
        milestone_filter: Optional[str] = None
    ) -> List[ScrapedDeadline]:
        """Scrape deadlines from GitHub milestones."""
        deadlines = []
        
        url = f"{self.api_base}/repos/{owner}/{repo}/milestones"
        params = {
            'state': 'all',
            'per_page': 100
        }
        
        try:
            response = await ScrapingUtils.make_request(url, headers=headers, params=params)
            if not response:
                return deadlines
            
            milestones = response  # GitHub API returns array directly
            
            for milestone in milestones:
                # Filter by milestone name if specified
                if milestone_filter and milestone.get('title') != milestone_filter:
                    continue
                
                due_on = milestone.get('due_on')
                if due_on:
                    try:
                        deadline_date = datetime.fromisoformat(
                            due_on.replace('Z', '+00:00')
                        ).replace(tzinfo=timezone.utc)
                        
                        deadline = ScrapedDeadline(
                            title=f"Milestone: {milestone.get('title', 'Untitled')}",
                            description=milestone.get('description', ''),
                            due_date=deadline_date,
                            portal_url=milestone.get('html_url', ''),
                            portal_task_id=str(milestone.get('id', '')),
                            priority='medium',
                            tags=['milestone', 'github'],
                            estimated_hours=None
                        )
                        deadlines.append(deadline)
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing milestone date {due_on}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error scraping milestones for {owner}/{repo}: {e}")
        
        return deadlines
    
    async def _extract_deadline_from_issue(
        self, issue: Dict[str, Any], owner: str, repo: str
    ) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a GitHub issue."""
        title = issue.get('title', '')
        body = issue.get('body', '') or ''
        
        # Check for deadline in title and body
        deadline_date = self._parse_deadline_from_text(f"{title} {body}")
        
        if not deadline_date:
            return None
        
        # Determine priority based on labels
        priority = self._determine_priority_from_labels(issue.get('labels', []))
        
        # Extract tags from labels
        tags = ['issue', 'github']
        labels = issue.get('labels', [])
        for label in labels[:5]:  # Limit to 5 labels
            tags.append(label.get('name', '').lower())
        
        return ScrapedDeadline(
            title=title,
            description=body[:500] + ('...' if len(body) > 500 else ''),  # Truncate long descriptions
            due_date=deadline_date,
            portal_url=issue.get('html_url', ''),
            portal_task_id=str(issue.get('number', '')),
            priority=priority,
            tags=tags,
            estimated_hours=None
        )
    
    async def _extract_deadline_from_pr(
        self, pr: Dict[str, Any], owner: str, repo: str
    ) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a GitHub pull request."""
        title = pr.get('title', '')
        body = pr.get('body', '') or ''
        
        # Check for deadline in title and body
        deadline_date = self._parse_deadline_from_text(f"{title} {body}")
        
        if not deadline_date:
            return None
        
        # Determine priority based on labels and PR status
        priority = self._determine_priority_from_labels(pr.get('labels', []))
        if pr.get('draft'):
            priority = 'low'
        
        # Extract tags
        tags = ['pull-request', 'github']
        labels = pr.get('labels', [])
        for label in labels[:5]:  # Limit to 5 labels
            tags.append(label.get('name', '').lower())
        
        return ScrapedDeadline(
            title=f"PR: {title}",
            description=body[:500] + ('...' if len(body) > 500 else ''),
            due_date=deadline_date,
            portal_url=pr.get('html_url', ''),
            portal_task_id=str(pr.get('number', '')),
            priority=priority,
            tags=tags,
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
                    # Try parsing different date formats
                    parsed_date = ScrapingUtils.parse_date(date_str)
                    if parsed_date:
                        return parsed_date
                except Exception:
                    continue
        
        return None
    
    def _determine_priority_from_labels(self, labels: List[Dict[str, Any]]) -> str:
        """Determine priority based on GitHub labels."""
        label_names = [label.get('name', '').lower() for label in labels]
        
        # High priority indicators
        high_priority_labels = [
            'critical', 'urgent', 'high priority', 'blocker', 'p0', 'p1'
        ]
        for label in label_names:
            if any(keyword in label for keyword in high_priority_labels):
                return 'high'
        
        # Low priority indicators
        low_priority_labels = [
            'low priority', 'nice to have', 'enhancement', 'p3', 'p4', 'p5'
        ]
        for label in label_names:
            if any(keyword in label for keyword in low_priority_labels):
                return 'low'
        
        return 'medium'  # Default priority
    
    async def _get_milestone_number(
        self, owner: str, repo: str, milestone_name: str, headers: Dict[str, str]
    ) -> Optional[int]:
        """Get milestone number by name."""
        url = f"{self.api_base}/repos/{owner}/{repo}/milestones"
        
        try:
            response = await ScrapingUtils.make_request(url, headers=headers)
            if not response:
                return None
            
            milestones = response  # GitHub API returns array directly
            for milestone in milestones:
                if milestone.get('title') == milestone_name:
                    return milestone.get('number')
        
        except Exception as e:
            self.logger.error(f"Error getting milestone number for {milestone_name}: {e}")
        
        return None