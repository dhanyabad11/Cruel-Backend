"""
Manually trigger the email reminder task to test immediately
"""
from app.celery_app import celery_app

# Trigger the email reminder task
result = celery_app.send_task('check_and_send_email_reminders')
print(f"Task triggered: {result.id}")
print("Check the Celery worker logs to see the email sending process...")
print("Email will be sent to: dhanyabadbehera@gmail.com")
