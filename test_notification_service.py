"""
Test Twilio Notification Service

Simple test script to verify Twilio notification functionality.
Run this with proper environment variables set:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_SMS_FROM
- TWILIO_WHATSAPP_FROM (optional)
"""

import asyncio
import os
from datetime import datetime, timedelta
from app.services.notification_service import TwilioNotificationService, NotificationType


async def test_notification_service():
    """Test the Twilio notification service"""
    
    # Test configuration
    TEST_PHONE = "+1234567890"  # Replace with your test phone number
    
    try:
        # Initialize service
        service = TwilioNotificationService()
        print("✅ Notification service initialized")
        
        # Validate configuration
        if service.validate_config():
            print("✅ Twilio configuration is valid")
        else:
            print("❌ Twilio configuration is invalid")
            return
        
        # Test basic SMS
        print("\n🧪 Testing SMS notification...")
        sms_result = await service.send_notification(
            phone_number=TEST_PHONE,
            message="Test message from AI Cruel Deadline Manager! 📱",
            notification_type=NotificationType.SMS
        )
        print(f"SMS Result: {sms_result}")
        
        # Test deadline reminder
        print("\n🧪 Testing deadline reminder...")
        deadline_date = datetime.now() + timedelta(hours=2)
        reminder_result = await service.send_deadline_reminder(
            phone_number=TEST_PHONE,
            deadline_title="Test Project Deadline",
            deadline_date=deadline_date,
            deadline_url="https://github.com/example/project",
            notification_type=NotificationType.SMS,
            priority="high"
        )
        print(f"Deadline Reminder Result: {reminder_result}")
        
        # Test daily summary
        print("\n🧪 Testing daily summary...")
        test_deadlines = [
            {
                'title': 'Complete API documentation',
                'due_date': (datetime.now() + timedelta(hours=6)).isoformat(),
                'priority': 'high',
                'url': 'https://github.com/example/docs'
            },
            {
                'title': 'Review pull requests',
                'due_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'priority': 'medium',
                'url': 'https://github.com/example/pr'
            }
        ]
        
        summary_result = await service.send_daily_summary(
            phone_number=TEST_PHONE,
            deadlines=test_deadlines,
            notification_type=NotificationType.SMS
        )
        print(f"Daily Summary Result: {summary_result}")
        
        # Test overdue alert
        print("\n🧪 Testing overdue alert...")
        overdue_deadlines = [
            {
                'title': 'Overdue task 1',
                'due_date': (datetime.now() - timedelta(days=1)).isoformat(),
            },
            {
                'title': 'Overdue task 2', 
                'due_date': (datetime.now() - timedelta(days=3)).isoformat(),
            }
        ]
        
        overdue_result = await service.send_overdue_alert(
            phone_number=TEST_PHONE,
            overdue_deadlines=overdue_deadlines,
            notification_type=NotificationType.SMS
        )
        print(f"Overdue Alert Result: {overdue_result}")
        
        # Test WhatsApp if configured
        if service.whatsapp_from:
            print("\n🧪 Testing WhatsApp notification...")
            whatsapp_result = await service.send_notification(
                phone_number=TEST_PHONE,
                message="WhatsApp test from AI Cruel! 📱💚",
                notification_type=NotificationType.WHATSAPP
            )
            print(f"WhatsApp Result: {whatsapp_result}")
        else:
            print("\n⚠️ WhatsApp sender not configured, skipping WhatsApp test")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_SMS_FROM']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        print("export TWILIO_ACCOUNT_SID='your_account_sid'")
        print("export TWILIO_AUTH_TOKEN='your_auth_token'")
        print("export TWILIO_SMS_FROM='+1234567890'")
        print("export TWILIO_WHATSAPP_FROM='whatsapp:+1234567890'  # Optional")
        return False
    
    print("✅ Environment variables are set")
    return True


if __name__ == "__main__":
    print("🧪 AI Cruel Notification Service Test")
    print("=" * 50)
    
    if check_environment():
        asyncio.run(test_notification_service())
    else:
        print("\n💡 Tip: You can get Twilio credentials from https://console.twilio.com/")
        print("For WhatsApp, you need to set up Twilio WhatsApp Sandbox or approved number.")