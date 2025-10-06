"""
Test script to immediately send an email reminder for the current deadline
"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.services.email_service import EmailService
from supabase import create_client

async def send_test_reminder():
    """Send email reminder for the yo deadline"""
    
    # Initialize services
    email_service = EmailService()
    supabase = create_client(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("Fetching your deadline...")
    
    # Get the most recent deadline for your user
    user_id = "dbd43bd0-bacf-4054-8b8f-2574be5c7f1f"  # Your user ID from logs
    
    deadlines_result = supabase.table('deadlines').select('*').eq('user_id', user_id).eq('status', 'pending').order('created_at', desc=True).limit(1).execute()
    
    if not deadlines_result.data:
        print("No pending deadlines found")
        return
    
    deadline = deadlines_result.data[0]
    print(f"\nFound deadline: {deadline['title']}")
    print(f"Due: {deadline['due_date']}")
    
    # Get notification settings
    settings_result = supabase.table('notification_settings').select('*').eq('user_id', user_id).execute()
    
    if not settings_result.data:
        print("No notification settings found")
        return
    
    settings = settings_result.data[0]
    email = settings.get('email')
    
    if not email:
        print("No email configured in notification settings")
        return
    
    print(f"\nSending email to: {email}")
    
    # Send the email
    deadline_date = datetime.fromisoformat(deadline['due_date'].replace('Z', '+00:00'))
    
    success = await email_service.send_deadline_reminder(
        to_email=email,
        deadline_title=deadline['title'],
        deadline_description=deadline.get('description', ''),
        deadline_date=deadline_date,
        priority=deadline.get('priority', 'medium')
    )
    
    if success:
        print("\n✓ Email sent successfully!")
        print(f"Check your inbox at {email}")
    else:
        print("\n✗ Failed to send email")

if __name__ == "__main__":
    asyncio.run(send_test_reminder())
