#!/bin/bash

# Start Celery Beat in background
celery -A app.celery_app beat --loglevel=info &

# Start Celery Worker in background
celery -A app.celery_app worker --loglevel=info -Q default,notifications,scraping &

# Start FastAPI server in foreground
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
