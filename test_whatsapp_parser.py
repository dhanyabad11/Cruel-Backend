"""
Test script for WhatsApp Chat Parser
Demonstrates parsing capabilities with sample messages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.whatsapp_parser import WhatsAppChatParser
from datetime import datetime, timedelta
import json

def test_parser():
    parser = WhatsAppChatParser()
    
    # Sample WhatsApp chat export format
    sample_chat = """
12/1/23, 2:30 PM - John: Hey guys, don't forget math assignment is due tomorrow at 11:59 PM
12/1/23, 3:45 PM - Sarah: Physics lab report deadline is Friday 5 PM
12/1/23, 4:20 PM - Mike: Urgent: Submit project proposal by Monday morning
12/1/23, 5:15 PM - Prof Smith: Chemistry exam next Tuesday at 2 PM in room 301
12/1/23, 6:30 PM - Lisa: History essay due next week, no rush
12/1/23, 7:45 PM - Tom: Presentation meeting tomorrow at 3 PM
12/1/23, 8:20 PM - Anna: Optional workshop on Friday if you can make it
12/1/23, 9:10 PM - John: Class canceled tomorrow
12/1/23, 10:05 PM - Sarah: Remember final exam is December 15th at 9 AM
"""
    
    print("🔍 Testing WhatsApp Chat Parser")
    print("=" * 50)
    
    # Test full chat parsing
    print("\n📱 Parsing full WhatsApp chat export:")
    extracted = parser.parse_whatsapp_export(sample_chat)
    
    print(f"Found {len(extracted)} potential deadlines:")
    for i, deadline in enumerate(extracted, 1):
        print(f"\n{i}. {deadline['title']}")
        print(f"   Due: {deadline['due_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Priority: {deadline['priority']}")
        print(f"   Confidence: {deadline['confidence']:.1f}")
        print(f"   Sender: {deadline['sender']}")
        print(f"   Source: {deadline['original_message'][:60]}...")
    
    # Test individual messages
    print("\n\n💬 Testing individual message parsing:")
    test_messages = [
        "Submit your research paper by Friday 5 PM",
        "Don't forget group presentation tomorrow",
        "Math quiz next Monday",
        "Assignment due today at midnight",
        "Optional study session this evening",
        "Urgent: Final project due December 20th"
    ]
    
    for message in test_messages:
        print(f"\nMessage: '{message}'")
        results = parser.parse_single_message(message, "Test User")
        
        if results:
            for result in results:
                print(f"  → Task: {result['title']}")
                print(f"  → Due: {result['due_date'].strftime('%Y-%m-%d %H:%M')}")
                print(f"  → Priority: {result['priority']}")
                print(f"  → Confidence: {result['confidence']:.1f}")
        else:
            print("  → No deadlines extracted")
    
    # Test edge cases
    print("\n\n⚠️ Testing edge cases:")
    edge_cases = [
        "Hello everyone!",  # No deadline content
        "Meeting yesterday was great",  # Past date
        "Maybe we should do something",  # Vague
        "Due",  # Too short
        "Assignment due tomorrow assignment due next week",  # Duplicates
    ]
    
    for message in edge_cases:
        print(f"\nEdge case: '{message}'")
        results = parser.parse_single_message(message, "Test User")
        print(f"  → Extracted: {len(results)} deadline(s)")
    
    # Performance test
    print("\n\n⚡ Performance test with larger chat:")
    large_chat = sample_chat * 10  # 10x larger
    start_time = datetime.now()
    extracted_large = parser.parse_whatsapp_export(large_chat)
    end_time = datetime.now()
    
    print(f"Processed {len(large_chat.split())} words in {(end_time - start_time).total_seconds():.2f} seconds")
    print(f"Extracted {len(extracted_large)} deadlines")
    
    # Export results as JSON for inspection
    output_file = "whatsapp_test_results.json"
    results_data = {
        "test_timestamp": datetime.now().isoformat(),
        "sample_chat_deadlines": [
            {
                "title": d["title"],
                "due_date": d["due_date"].isoformat(),
                "priority": d["priority"],
                "confidence": d["confidence"],
                "sender": d["sender"],
                "original_message": d["original_message"]
            }
            for d in extracted
        ],
        "individual_message_tests": [
            {
                "message": msg,
                "extracted_count": len(parser.parse_single_message(msg, "Test"))
            }
            for msg in test_messages
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📄 Results exported to {output_file}")
    print("\n✅ WhatsApp parser testing complete!")

if __name__ == "__main__":
    test_parser()