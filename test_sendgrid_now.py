#!/usr/bin/env python3
"""Test SendGrid email sending in production"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_send():
    from app.services.email_service import send_email
    
    print("Testing SendGrid email...")
    print(f"API Key: {os.getenv('SENDGRID_API_KEY')[:10]}...")
    print(f"From: {os.getenv('SENDGRID_FROM_EMAIL')}")
    
    try:
        await send_email(
            to_email="dhanyabadbehera@gmail.com",
            subject="✅ Production Email Test - SendGrid Working!",
            body="This email was sent from your production server using SendGrid API! Email reminders are now working! 🎉"
        )
        print("✓ Email sent successfully!")
        return True
    except Exception as e:
        print(f"✗ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_send())
    sys.exit(0 if success else 1)
