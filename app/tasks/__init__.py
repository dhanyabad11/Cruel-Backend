"""
Tasks Package

Contains all Celery background tasks for the AI Cruel application.
"""

from .scraping_tasks import *
from .notification_tasks import *
from .maintenance_tasks import *