"""
Celery Application Configuration

This module sets up Celery for background task processing including:
- Portal scraping tasks
- Notification scheduling
- Deadline monitoring
- Periodic cleanup tasks
"""

import os
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "ai_cruel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.scraping_tasks',
        'app.tasks.notification_tasks',
        'app.tasks.maintenance_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.scraping_tasks.*': {'queue': 'scraping'},
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
        'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Scrape all portals every 30 minutes
        'scrape-all-portals': {
            'task': 'app.tasks.scraping_tasks.scrape_all_portals',
            'schedule': crontab(minute='*/30'),
            'options': {'queue': 'scraping'}
        },
        
        # Send daily summaries at 9 AM
        'send-daily-summaries': {
            'task': 'app.tasks.notification_tasks.send_daily_summaries',
            'schedule': crontab(hour=9, minute=0),
            'options': {'queue': 'notifications'}
        },
        
        # Check for overdue deadlines every hour
        'check-overdue-deadlines': {
            'task': 'app.tasks.notification_tasks.check_overdue_deadlines',
            'schedule': crontab(minute=0),
            'options': {'queue': 'notifications'}
        },
        
        # Send deadline reminders (check every 15 minutes)
        'send-deadline-reminders': {
            'task': 'app.tasks.notification_tasks.send_deadline_reminders',
            'schedule': crontab(minute='*/15'),
            'options': {'queue': 'notifications'}
        },
        
        # Clean up old notifications daily at 2 AM
        'cleanup-old-notifications': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_notifications',
            'schedule': crontab(hour=2, minute=0),
            'options': {'queue': 'maintenance'}
        },
        
        # Update notification statuses every 10 minutes
        'update-notification-statuses': {
            'task': 'app.tasks.notification_tasks.update_notification_statuses',
            'schedule': crontab(minute='*/10'),
            'options': {'queue': 'notifications'}
        },
    }
)

# Error handling
celery_app.conf.task_annotations = {
    '*': {
        'rate_limit': '100/m',  # Global rate limit
        'retry_kwargs': {
            'max_retries': 3,
            'countdown': 60,  # Wait 1 minute between retries
        }
    },
    'app.tasks.scraping_tasks.*': {
        'rate_limit': '20/m',  # Lower rate limit for scraping
    },
    'app.tasks.notification_tasks.*': {
        'rate_limit': '50/m',  # Moderate rate limit for notifications
    }
}

# Task failure handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'


if __name__ == '__main__':
    celery_app.start()