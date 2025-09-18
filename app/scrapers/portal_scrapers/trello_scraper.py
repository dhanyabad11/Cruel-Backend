"""
Trello Scraper Implementation

This module implements a scraper for Trello boards to extract deadlines
from cards and their due dates. It uses the Trello REST API.
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from ..base_scraper import BaseScraper, ScrapedDeadline, ScrapingResult, ScrapingStatus
from ..scraper_registry import register_scraper
from ..utils import ScrapingUtils


@register_scraper('trello')
class TrelloScraper(BaseScraper):
    """Scraper for Trello boards to extract deadlines from cards and due dates."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        super().__init__(portal_config)
        self.api_base = "https://api.trello.com/1"
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
        Authenticate with Trello API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        api_key = self.credentials.get('api_key')
        api_token = self.credentials.get('api_token')
        
        if not api_key or not api_token:
            self.logger.error("Trello API key and token are required")
            return False
        
        # Test authentication by getting current user info
        params = {
            'key': api_key,
            'token': api_token
        }
        
        try:
            response = await ScrapingUtils.make_request(
                f"{self.api_base}/members/me",
                params=params
            )
            return response is not None and 'id' in response
        except Exception as e:
            self.logger.error(f"Trello authentication failed: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are present.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        api_key = self.credentials.get('api_key')
        api_token = self.credentials.get('api_token')
        
        if not api_key or not isinstance(api_key, str):
            return False
        
        if not api_token or not isinstance(api_token, str):
            return False
        
        # Validate board configuration
        boards = self.scrape_config.get('boards', [])
        board_urls = self.scrape_config.get('board_urls', [])
        
        if not boards and not board_urls:
            # At least one board ID or URL must be provided
            return False
        
        # Validate board URLs if provided
        for board_url in board_urls:
            if not self._is_valid_trello_url(board_url):
                return False
                
        return True
    
    def _is_valid_trello_url(self, url: str) -> bool:
        """Check if URL is a valid Trello board URL."""
        try:
            parsed = urlparse(url)
            if parsed.netloc.lower() not in ['trello.com', 'www.trello.com']:
                return False
            
            # Check path format: /b/board_id/board_name or /c/card_id/card_name
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) >= 2 and path_parts[0] in ['b', 'c']:
                return True
                
            return False
        except Exception:
            return False
    
    def _extract_board_id_from_url(self, board_url: str) -> Optional[str]:
        """Extract board ID from Trello board URL."""
        try:
            parsed = urlparse(board_url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if len(path_parts) >= 2 and path_parts[0] == 'b':
                return path_parts[1]
                
            return None
        except Exception:
            return None
    
    async def scrape_deadlines(self) -> ScrapingResult:
        """
        Scrape deadlines from Trello boards.
        
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
                    errors=["Failed to authenticate with Trello"]
                )
            
            # Get API credentials
            api_key = self.credentials.get('api_key')
            api_token = self.credentials.get('api_token')
            auth_params = {'key': api_key, 'token': api_token}
            
            # Get board IDs to scrape
            board_ids = await self._get_board_ids(auth_params)
            if not board_ids:
                return ScrapingResult(
                    status=ScrapingStatus.ERROR,
                    deadlines=[],
                    message="No valid boards found to scrape",
                    errors=["No board IDs could be determined from configuration"]
                )
            
            deadlines = []
            
            # Scrape each board
            for board_id in board_ids:
                try:
                    board_deadlines = await self._scrape_board(board_id, auth_params)
                    deadlines.extend(board_deadlines)
                except Exception as e:
                    self.logger.error(f"Error scraping board {board_id}: {e}")
            
            return ScrapingResult(
                status=ScrapingStatus.SUCCESS,
                deadlines=deadlines,
                message=f"Successfully scraped {len(deadlines)} deadlines from {len(board_ids)} Trello boards",
                metadata={
                    'boards_scanned': len(board_ids),
                    'board_ids': board_ids,
                    'total_deadlines': len(deadlines)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping Trello boards: {e}")
            return ScrapingResult(
                status=ScrapingStatus.ERROR,
                deadlines=[],
                message=f"Scraping failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _get_board_ids(self, auth_params: Dict[str, str]) -> List[str]:
        """Get list of board IDs to scrape from configuration."""
        board_ids = []
        
        # Add directly specified board IDs
        configured_boards = self.scrape_config.get('boards', [])
        board_ids.extend(configured_boards)
        
        # Extract board IDs from URLs
        board_urls = self.scrape_config.get('board_urls', [])
        for board_url in board_urls:
            board_id = self._extract_board_id_from_url(board_url)
            if board_id and board_id not in board_ids:
                board_ids.append(board_id)
        
        # If no specific boards configured, get user's boards
        if not board_ids:
            try:
                response = await ScrapingUtils.make_request(
                    f"{self.api_base}/members/me/boards",
                    params=auth_params
                )
                if response:
                    for board in response:
                        if not board.get('closed', True):  # Only open boards
                            board_ids.append(board['id'])
            except Exception as e:
                self.logger.error(f"Error fetching user boards: {e}")
        
        return board_ids
    
    async def _scrape_board(self, board_id: str, auth_params: Dict[str, str]) -> List[ScrapedDeadline]:
        """Scrape deadlines from a specific Trello board."""
        deadlines = []
        
        try:
            # Get board info
            board_response = await ScrapingUtils.make_request(
                f"{self.api_base}/boards/{board_id}",
                params={**auth_params, 'fields': 'name,url,desc'}
            )
            
            if not board_response:
                return deadlines
            
            board_name = board_response.get('name', 'Unknown Board')
            board_url = board_response.get('url', '')
            
            # Get cards with due dates
            cards_params = {
                **auth_params,
                'fields': 'name,desc,due,dueComplete,url,labels,members',
                'filter': 'open'  # Only open cards
            }
            
            # Add list filtering if specified
            target_lists = self.scrape_config.get('lists', [])
            if target_lists:
                # Get lists first to filter by names
                lists_response = await ScrapingUtils.make_request(
                    f"{self.api_base}/boards/{board_id}/lists",
                    params={**auth_params, 'fields': 'name'}
                )
                
                if lists_response:
                    target_list_ids = []
                    for trello_list in lists_response:
                        if trello_list.get('name') in target_lists:
                            target_list_ids.append(trello_list['id'])
                    
                    if target_list_ids:
                        cards_params['list'] = ','.join(target_list_ids)
            
            cards_response = await ScrapingUtils.make_request(
                f"{self.api_base}/boards/{board_id}/cards",
                params=cards_params
            )
            
            if not cards_response:
                return deadlines
            
            # Process each card
            for card in cards_response:
                deadline = await self._extract_deadline_from_card(card, board_name, board_url)
                if deadline:
                    deadlines.append(deadline)
        
        except Exception as e:
            self.logger.error(f"Error scraping Trello board {board_id}: {e}")
        
        return deadlines
    
    async def _extract_deadline_from_card(
        self, card: Dict[str, Any], board_name: str, board_url: str
    ) -> Optional[ScrapedDeadline]:
        """Extract deadline information from a Trello card."""
        
        # Check for due date field
        due_date = card.get('due')
        deadline_date = None
        
        if due_date:
            try:
                deadline_date = datetime.fromisoformat(
                    due_date.replace('Z', '+00:00')
                ).replace(tzinfo=timezone.utc)
            except Exception:
                pass
        
        # If no due date, check card name and description for deadline mentions
        if not deadline_date:
            card_name = card.get('name', '')
            card_desc = card.get('desc', '') or ''
            deadline_date = self._parse_deadline_from_text(f"{card_name} {card_desc}")
        
        if not deadline_date:
            return None
        
        # Skip completed cards if due date is complete
        if card.get('dueComplete', False):
            include_completed = self.scrape_config.get('include_completed', False)
            if not include_completed:
                return None
        
        # Determine priority from labels
        priority = self._determine_priority_from_labels(card.get('labels', []))
        
        # Build tags
        tags = ['trello', 'card']
        labels = card.get('labels', [])
        for label in labels[:5]:  # Limit to 5 labels
            label_name = label.get('name', '').lower()
            if label_name:
                tags.append(label_name)
        
        # Add board name as tag
        if board_name:
            tags.append(board_name.lower().replace(' ', '-'))
        
        # Get assigned members
        members = card.get('members', [])
        member_names = [member.get('fullName', member.get('username', '')) for member in members]
        
        # Build description
        description = card.get('desc', '') or f"Card from {board_name}"
        if member_names:
            description += f"\nAssigned to: {', '.join(member_names)}"
        
        return ScrapedDeadline(
            title=card.get('name', 'Untitled Card'),
            description=self._truncate_text(description, 500),
            due_date=deadline_date,
            portal_url=card.get('url', ''),
            portal_task_id=card.get('id', ''),
            priority=priority,
            tags=tags,
            estimated_hours=self._extract_time_estimate_from_text(card.get('desc', ''))
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
    
    def _determine_priority_from_labels(self, labels: List[Dict[str, Any]]) -> str:
        """Determine priority based on Trello labels."""
        if not labels:
            return 'medium'
        
        # Check label names and colors for priority indicators
        for label in labels:
            label_name = label.get('name', '').lower()
            label_color = label.get('color', '').lower()
            
            # Low priority indicators (check first to avoid conflicts)
            low_indicators = [
                'low priority', 'low', 'minor', 'nice to have', 'optional', 
                'someday', 'enhancement', 'feature'
            ]
            if any(indicator in label_name for indicator in low_indicators):
                return 'low'
            
            # Green labels often indicate low priority
            if label_color == 'green':
                return 'low'
            
            # High priority indicators
            high_indicators = [
                'urgent', 'critical', 'high', 'priority', 'important', 
                'blocker', 'asap', 'rush'
            ]
            if any(indicator in label_name for indicator in high_indicators):
                return 'high'
            
            # Red labels often indicate urgency
            if label_color == 'red':
                return 'high'
        
        return 'medium'  # Default priority
    
    def _extract_time_estimate_from_text(self, text: str) -> Optional[int]:
        """Extract time estimate from card description text."""
        if not text:
            return None
        
        # Look for common time estimate patterns
        time_patterns = [
            r'(\d+)\s*h(?:ours?)?',
            r'(\d+)\s*hrs?',
            r'estimate[:\s]+(\d+)\s*h(?:ours?)?',
            r'time[:\s]+(\d+)\s*h(?:ours?)?',
            r'effort[:\s]+(\d+)\s*h(?:ours?)?'
        ]
        
        text_lower = text.lower()
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    hours = int(match.group(1))
                    if 0 < hours <= 1000:  # Reasonable range
                        return hours
                except ValueError:
                    continue
        
        return None
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        if not text:
            return ''
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length] + '...'