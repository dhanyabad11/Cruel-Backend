#!/usr/bin/env python3
"""
Test the email reminder system by manually triggering it
"""
from app.tasks.celery_supabase_notification import check_and_send_email_reminders

print('=' * 60)
print('Testing Email Reminder System')
print('=' * 60)
print()

try:
    result = check_and_send_email_reminders()
    print()
    print('=' * 60)
    print('Task Result:')
    print(result)
    print('=' * 60)
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
