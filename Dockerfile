# Backend Dockerfile for FastAPI
FROM python:3.10-slim

# Install build dependencies for compiling Python packages (blis, spacy)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Make start script executable
RUN chmod +x start.sh

# Use startup script that runs Celery + FastAPI together
CMD ["./start.sh"]
