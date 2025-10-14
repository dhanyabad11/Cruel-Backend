# Backend Dockerfile for FastAPI
FROM python:3.10-slim

# Install build dependencies and bash
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Make start scripts executable
RUN chmod +x start.sh start_services.py

# Use Python startup script that runs Celery + FastAPI together
CMD ["python", "start_services.py"]
