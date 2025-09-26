import asyncio
from dotenv import load_dotenv
from app.services.email_service import send_email

async def main():
    load_dotenv()
    to_email = "dhanyabadbehera@gmail.com"  # Change to your test recipient
    subject = "Test Email from AI Cruel Backend"
    body = "This is a test email sent from your FastAPI backend using Gmail SMTP."
    await send_email(to_email, subject, body)
    print("Test email sent!")

if __name__ == "__main__":
    asyncio.run(main())
