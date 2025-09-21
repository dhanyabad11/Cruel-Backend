#!/bin/bash

# Start Celery Worker
# This script starts the Celery worker for processing background tasks

echo "Starting AI Cruel Celery Worker..."

# Set environment variables if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Celery worker with multiple queues
exec ./venv/bin/celery -A app.celery_app worker \
    --loglevel=info \
    --queues=scraping,notifications,maintenance \
    --concurrency=4 \
    --hostname=worker@%h \
    --without-heartbeat \
    --without-mingle