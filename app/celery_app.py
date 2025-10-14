"""
Celery Application Configuration

This module sets up Celery for background task processing including:
- Portal scraping tasks
- Notification scheduling
- Deadline monitoring
- Periodic cleanup tasks
"""

import os
import ssl
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Configure SSL for Redis if using rediss://
broker_use_ssl = None
if settings.REDIS_URL.startswith('rediss://'):
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE  # For Upstash, we don't verify certs
    }

# Create Celery instance
celery_app = Celery(
    "ai_cruel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.scraping_tasks',
        'app.tasks.celery_supabase_notification'
    ]
)

# Apply SSL configuration
if broker_use_ssl:
    celery_app.conf.broker_use_ssl = broker_use_ssl
    celery_app.conf.redis_backend_use_ssl = broker_use_ssl

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.celery_supabase_notification.*': {'queue': 'notifications'},
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
        
        # Send deadline reminders every 15 minutes using Supabase
        'send-supabase-deadline-reminders': {
            'task': 'app.tasks.celery_supabase_notification.send_supabase_deadline_reminders',
            'schedule': crontab(minute='*/15'),
            'options': {'queue': 'notifications'}
        },
        
        # Check and send email reminders every 5 minutes
        'check-email-reminders': {
            'task': 'check_and_send_email_reminders',
            'schedule': crontab(minute='*/5'),
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
    'app.tasks.celery_supabase_notification.*': {
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