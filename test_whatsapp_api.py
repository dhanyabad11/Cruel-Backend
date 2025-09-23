"""
Test WhatsApp API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_parse_message():
    """Test single message parsing endpoint"""
    print("🧪 Testing WhatsApp message parsing...")
    
    # Test message
    test_message = "Don't forget the physics assignment is due tomorrow at 11:59 PM"
    
    # Call API
    response = requests.post(
        f"{BASE_URL}/api/whatsapp/parse-message",
        data={
            "message": test_message,
            "sender": "Test User",
            "auto_create": False
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Extracted {len(data['extracted_deadlines'])} deadline(s)")
        
        for deadline in data['extracted_deadlines']:
            print(f"  📅 {deadline['title']} - Due: {deadline['due_date']}")
            print(f"     Priority: {deadline['priority']}, Confidence: {deadline['confidence']}")
    else:
        print(f"❌ Error: {response.text}")

def test_parsing_examples():
    """Test the examples endpoint"""
    print("\n🧪 Testing parsing examples endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/whatsapp/examples")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got {len(data['examples'])} examples")
        print(f"Supported formats: {len(data['supported_formats'])}")
        print(f"Tips: {len(data['tips'])}")
    else:
        print(f"❌ Error: {response.text}")

def test_upload_chat():
    """Test file upload endpoint with sample chat"""
    print("\n🧪 Testing WhatsApp chat upload...")
    
    # Create sample chat content
    sample_chat = """12/1/23, 2:30 PM - John: Don't forget math assignment is due tomorrow at 11:59 PM
12/1/23, 3:45 PM - Sarah: Physics lab report deadline is Friday 5 PM
12/1/23, 4:20 PM - Mike: Urgent: Submit project proposal by Monday morning
12/1/23, 5:15 PM - Prof Smith: Chemistry exam next Tuesday at 2 PM in room 301
12/1/23, 6:30 PM - Lisa: History essay due next week, no rush"""
    
    # Create temporary file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_chat)
        temp_file_path = f.name
    
    try:
        # Upload file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_chat.txt', f, 'text/plain')}
            data = {'auto_create': False}
            
            response = requests.post(
                f"{BASE_URL}/api/whatsapp/upload-chat",
                files=files,
                data=data
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Extracted {data['total_extracted']} deadline(s)")
            print(f"Auto-created: {data['auto_created']}")
            
            for deadline in data['deadlines'][:3]:  # Show first 3
                print(f"  📅 {deadline['title']} - Due: {deadline['due_date']}")
                print(f"     Confidence: {deadline['confidence']}")
        else:
            print(f"❌ Error: {response.text}")
    
    finally:
        # Clean up
        os.unlink(temp_file_path)

def main():
    print("🚀 Testing WhatsApp Integration API")
    print("=" * 40)
    
    try:
        # Test basic endpoint
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ Server not running or not accessible")
            return
        
        print("✅ Server is running!")
        
        # Run tests
        test_parsing_examples()
        test_parse_message()
        test_upload_chat()
        
        print("\n🎉 All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 8000.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()