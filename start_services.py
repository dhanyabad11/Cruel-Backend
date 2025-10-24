#!/usr/bin/env python3
"""
Startup script to run Celery Beat, Celery Worker, and Uvicorn together
"""
import os
import sys
import subprocess
import signal
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def start_processes():
    processes = []
    
    # Print debug info
    redis_url = os.getenv('REDIS_URL', 'NOT SET')
    print(f"Starting with REDIS_URL: {redis_url[:50]}...")
    print(f"Python path: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Start Celery Beat
        print("Starting Celery Beat...")
        beat_process = subprocess.Popen([
            'celery', '-A', 'app.celery_app', 'beat', 
            '--loglevel=info'
        ])
        processes.append(('beat', beat_process))
        time.sleep(2)
        
        # Start Celery Worker
        print("Starting Celery Worker...")
        worker_process = subprocess.Popen([
            'celery', '-A', 'app.celery_app', 'worker',
            '--loglevel=info',
            '--pool=solo',
            '-Q', 'default,notifications,scraping'
        ])
        processes.append(('worker', worker_process))
        time.sleep(2)
        
        # Start Uvicorn (blocking)
        print("Starting Uvicorn...")
        port = os.getenv('PORT', '8000')
        uvicorn_process = subprocess.Popen([
            'uvicorn', 'main:app',
            '--host', '0.0.0.0',
            '--port', port
        ])
        processes.append(('uvicorn', uvicorn_process))
        
        # Wait for uvicorn (main process)
        uvicorn_process.wait()
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Kill all processes
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    start_processes()
