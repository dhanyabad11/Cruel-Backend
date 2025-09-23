"""
Simple test for WhatsApp parser functionality
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import dateparser
from dateutil.relativedelta import relativedelta

def simple_test():
    print("🔍 Testing WhatsApp Parser Components")
    print("=" * 50)
    
    # Test dateparser
    print("\n📅 Testing date parsing:")
    test_dates = ["tomorrow", "Friday", "next week", "December 15th", "2023-12-20"]
    
    for date_str in test_dates:
        try:
            parsed = dateparser.parse(date_str)
            print(f"  '{date_str}' → {parsed}")
        except Exception as e:
            print(f"  '{date_str}' → Error: {e}")
    
    # Test regex patterns
    print("\n🔍 Testing regex patterns:")
    test_messages = [
        "Don't forget math assignment is due tomorrow at 11:59 PM",
        "Physics lab report deadline is Friday 5 PM",
        "Submit project proposal by Monday morning"
    ]
    
    deadline_pattern = r'(.+?)\s+(?:is\s+)?due\s+(?:on\s+)?(.+?)(?:\.|$|,)'
    
    for message in test_messages:
        matches = re.finditer(deadline_pattern, message, re.IGNORECASE)
        print(f"\nMessage: '{message}'")
        for match in matches:
            task = match.group(1).strip()
            date_text = match.group(2).strip()
            print(f"  Task: '{task}'")
            print(f"  Date: '{date_text}'")
    
    # Test basic WhatsApp line parsing
    print("\n💬 Testing WhatsApp line parsing:")
    chat_lines = [
        "12/1/23, 2:30 PM - John: Don't forget math assignment is due tomorrow",
        "12/1/23, 3:45 PM - Sarah: Physics lab report deadline is Friday 5 PM"
    ]
    
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*(?:AM|PM)?\s*-\s*([^:]+):\s*(.+)'
    
    for line in chat_lines:
        match = re.match(pattern, line.strip())
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            sender = match.group(3).strip()
            message = match.group(4).strip()
            
            print(f"\nLine: '{line}'")
            print(f"  Date: {date_str}")
            print(f"  Time: {time_str}")
            print(f"  Sender: {sender}")
            print(f"  Message: {message}")
        else:
            print(f"\nLine: '{line}' → No match")
    
    print("\n✅ Component testing complete!")

if __name__ == "__main__":
    simple_test()