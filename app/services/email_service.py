import os
from dotenv import load_dotenv
import aiosmtplib
from email.message import EmailMessage

async def send_email(to_email, subject, body):
    load_dotenv()
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USERNAME")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    await aiosmtplib.send(
        msg,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT")),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        start_tls=True,
    )
