#!/bin/bash

# Start Celery Beat
# This script starts the Celery beat scheduler for periodic tasks

echo "Starting AI Cruel Celery Beat Scheduler..."

# Set environment variables if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Celery beat scheduler
exec ./venv/bin/celery -A app.celery_app beat \
    --loglevel=info \
    --schedule=celerybeat-schedule.db \
    --pidfile=celerybeat.pid