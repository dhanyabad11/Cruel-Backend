"""
WhatsApp Chat Parser for AI Cruel
Extracts deadlines from WhatsApp group chat messages
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import dateparser
from dateutil.relativedelta import relativedelta

class WhatsAppChatParser:
    def __init__(self):
        # Common deadline keywords
        self.deadline_keywords = [
            'due', 'deadline', 'submit', 'assignment', 'homework', 'project',
            'exam', 'test', 'quiz', 'presentation', 'report', 'essay',
            'lab', 'meeting', 'class', 'lecture', 'seminar', 'workshop'
        ]
        
        # Time expressions
        self.time_expressions = [
            'tomorrow', 'today', 'tonight', 'yesterday',
            'next week', 'this week', 'next month', 'this month',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ]
        
        # Priority indicators
        self.priority_high = ['urgent', 'asap', 'important', 'critical', 'emergency', 'rush']
        self.priority_low = ['optional', 'if possible', 'when you can', 'no rush', 'flexible']
    
    def parse_whatsapp_export(self, chat_content: str) -> List[Dict]:
        """
        Parse WhatsApp chat export and extract deadlines
        
        Args:
            chat_content: Raw WhatsApp chat export text
            
        Returns:
            List of extracted deadlines with metadata
        """
        lines = chat_content.split('\n')
        extracted_deadlines = []
        
        for line in lines:
            message_data = self._parse_chat_line(line)
            if message_data:
                deadlines = self._extract_deadlines_from_message(
                    message_data['message'],
                    message_data['sender'],
                    message_data['timestamp']
                )
                extracted_deadlines.extend(deadlines)
        
        # Remove duplicates and sort by confidence
        unique_deadlines = self._remove_duplicates(extracted_deadlines)
        return sorted(unique_deadlines, key=lambda x: x['confidence'], reverse=True)
    
    def parse_single_message(self, message: str, sender: str = "Unknown") -> List[Dict]:
        """
        Parse a single message for deadlines
        
        Args:
            message: The message text
            sender: Who sent the message
            
        Returns:
            List of extracted deadlines
        """
        return self._extract_deadlines_from_message(message, sender, datetime.now())
    
    def _parse_chat_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single line from WhatsApp export
        Format: "MM/DD/YY, HH:MM - Contact Name: Message"
        """
        # Common WhatsApp export patterns
        patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*(?:AM|PM)?\s*-\s*([^:]+):\s*(.+)',
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.+)',
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                try:
                    date_str = match.group(1)
                    time_str = match.group(2)
                    sender = match.group(3).strip()
                    message = match.group(4).strip()
                    
                    # Parse timestamp
                    datetime_str = f"{date_str} {time_str}"
                    timestamp = dateparser.parse(datetime_str)
                    
                    if timestamp:
                        return {
                            'timestamp': timestamp,
                            'sender': sender,
                            'message': message
                        }
                except Exception:
                    continue
        
        return None
    
    def _extract_deadlines_from_message(self, message: str, sender: str, timestamp: datetime) -> List[Dict]:
        """
        Extract deadline information from a single message
        """
        deadlines = []
        message_lower = message.lower()
        
        # Skip if message is too short or doesn't contain deadline indicators
        if len(message) < 10 or not self._contains_deadline_indicators(message_lower):
            return deadlines
        
        # Find deadline patterns
        deadline_patterns = self._find_deadline_patterns(message, timestamp)
        
        for pattern in deadline_patterns:
            deadline = {
                'title': pattern['task'],
                'description': f"Extracted from WhatsApp: {message}",
                'due_date': pattern['date'],
                'priority': self._determine_priority(message_lower),
                'source': 'whatsapp',
                'original_message': message,
                'sender': sender,
                'confidence': pattern['confidence'],
                'extracted_at': timestamp,
                'status': 'pending'
            }
            deadlines.append(deadline)
        
        return deadlines
    
    def _contains_deadline_indicators(self, message: str) -> bool:
        """Check if message contains deadline-related keywords"""
        for keyword in self.deadline_keywords:
            if keyword in message:
                return True
        
        for time_expr in self.time_expressions:
            if time_expr in message:
                return True
        
        return False
    
    def _find_deadline_patterns(self, message: str, reference_date: datetime) -> List[Dict]:
        """Find and parse deadline patterns in message"""
        patterns = []
        
        # Pattern 1: Direct deadline mentions
        deadline_patterns = [
            r'(.+?)\s+(?:is\s+)?due\s+(?:on\s+)?(.+?)(?:\.|$|,)',
            r'(.+?)\s+deadline\s+(?:is\s+)?(.+?)(?:\.|$|,)',
            r'submit\s+(.+?)\s+(?:by\s+|before\s+)(.+?)(?:\.|$|,)',
            r'(.+?)\s+(?:assignment|homework|project)\s+(?:due\s+)?(.+?)(?:\.|$|,)',
        ]
        
        for pattern in deadline_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                task = match.group(1).strip()
                date_text = match.group(2).strip()
                
                parsed_date = self._parse_date_expression(date_text, reference_date)
                if parsed_date and len(task) > 2:
                    patterns.append({
                        'task': task,
                        'date': parsed_date,
                        'confidence': 0.9
                    })
        
        # Pattern 2: Event/meeting patterns
        event_patterns = [
            r'(.+?)\s+(?:meeting|presentation|exam|test|quiz)\s+(?:is\s+|on\s+)?(.+?)(?:\.|$|,)',
            r'(.+?)\s+(?:tomorrow|today|tonight|next\s+week|this\s+week)',
            r'(?:remember|don\'t forget),?\s+(.+?)\s+(?:is\s+)?(.+?)(?:\.|$|,)',
        ]
        
        for pattern in event_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    task = match.group(1).strip()
                    date_text = match.group(2).strip()
                    parsed_date = self._parse_date_expression(date_text, reference_date)
                else:
                    task = match.group(1).strip()
                    # Extract relative time from task
                    relative_words = ['tomorrow', 'today', 'tonight', 'next week', 'this week']
                    date_text = next((word for word in relative_words if word in task.lower()), 'tomorrow')
                    parsed_date = self._parse_date_expression(date_text, reference_date)
                
                if parsed_date and len(task) > 2:
                    patterns.append({
                        'task': task,
                        'date': parsed_date,
                        'confidence': 0.7
                    })
        
        return patterns
    
    def _parse_date_expression(self, date_text: str, reference_date: datetime) -> Optional[datetime]:
        """Parse various date expressions"""
        date_text = date_text.lower().strip()
        
        # Handle relative dates first
        if 'tomorrow' in date_text:
            return reference_date + timedelta(days=1)
        elif 'today' in date_text:
            return reference_date
        elif 'tonight' in date_text:
            return reference_date.replace(hour=23, minute=59)
        elif 'next week' in date_text:
            return reference_date + timedelta(days=7)
        elif 'this week' in date_text:
            return reference_date + timedelta(days=3)
        elif 'next month' in date_text:
            return reference_date + relativedelta(months=1)
        
        # Handle day names
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in date_text:
                days_ahead = (i - reference_date.weekday()) % 7
                if days_ahead == 0:  # Same day, assume next week
                    days_ahead = 7
                target_date = reference_date + timedelta(days=days_ahead)
                
                # Extract time if present
                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', date_text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    ampm = time_match.group(3)
                    
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    
                    target_date = target_date.replace(hour=hour, minute=minute)
                
                return target_date
        
        # Try parsing with dateparser
        try:
            parsed = dateparser.parse(date_text, settings={
                'RELATIVE_BASE': reference_date,
                'PREFER_DATES_FROM': 'future'
            })
            if parsed and parsed > reference_date:
                return parsed
        except:
            pass
        
        return None
    
    def _determine_priority(self, message: str) -> str:
        """Determine priority based on message content"""
        message_lower = message.lower()
        
        # Check for high priority indicators
        if any(word in message_lower for word in self.priority_high):
            return 'high'
        
        # Check for low priority indicators
        if any(phrase in message_lower for phrase in self.priority_low):
            return 'low'
        
        # Check for time urgency
        if any(word in message_lower for word in ['tomorrow', 'today', 'tonight']):
            return 'high'
        
        return 'medium'
    
    def _remove_duplicates(self, deadlines: List[Dict]) -> List[Dict]:
        """Remove duplicate deadlines based on title and date similarity"""
        unique_deadlines = []
        
        for deadline in deadlines:
            is_duplicate = False
            
            for existing in unique_deadlines:
                # Check if titles are similar and dates are close
                if (self._similar_strings(deadline['title'], existing['title']) and
                    abs((deadline['due_date'] - existing['due_date']).total_seconds()) < 86400):  # Within 24 hours
                    
                    # Keep the one with higher confidence
                    if deadline['confidence'] > existing['confidence']:
                        unique_deadlines.remove(existing)
                        unique_deadlines.append(deadline)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_deadlines.append(deadline)
        
        return unique_deadlines
    
    def _similar_strings(self, str1: str, str2: str, threshold: float = 0.7) -> bool:
        """Check if two strings are similar using simple word overlap"""
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        similarity = overlap / max(len(words1), len(words2))
        
        return similarity >= threshold