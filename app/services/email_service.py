import os
from dotenv import load_dotenv
import httpx

async def send_email(to_email, subject, body):
    """
    Send email using SendGrid API (bypasses SMTP port blocking)
    Free tier: 100 emails/day
    """
    load_dotenv()
    
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", os.getenv("SMTP_USERNAME"))
    
    if not sendgrid_api_key:
        raise ValueError("SENDGRID_API_KEY environment variable is required")
    
    # SendGrid API endpoint
    url = "https://api.sendgrid.com/v3/mail/send"
    
    # Email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {"email": from_email},
        "content": [
            {
                "type": "text/plain",
                "value": body
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {sendgrid_api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code not in [200, 202]:
            raise Exception(f"SendGrid API error: {response.status_code} - {response.text}")
        
        return True
