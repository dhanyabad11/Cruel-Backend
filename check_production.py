#!/usr/bin/env python3
"""
Quick diagnostic tool to check Redis connection and Celery status
"""
import os
import sys
from dotenv import load_dotenv

# Load production env
load_dotenv('.env.production')

def check_redis():
    """Check if Redis is accessible"""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            print("❌ REDIS_URL not found in environment")
            return False
        
        print(f"🔍 Connecting to Redis...")
        print(f"   URL: {redis_url[:30]}...")
        
        r = redis.from_url(redis_url)
        r.ping()
        
        # Get info
        info = r.info()
        print(f"✅ Redis connection successful!")
        print(f"   Version: {info.get('redis_version', 'unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'unknown')}")
        
        return True
        
    except redis.exceptions.ResponseError as e:
        if 'max requests limit exceeded' in str(e).lower():
            print("❌ Redis LIMIT EXCEEDED!")
            print(f"   Error: {e}")
            print("\n⚠️  Your Upstash free tier has been exhausted")
            print("   Solutions:")
            print("   1. Upgrade to Upstash Pro ($10/month)")
            print("   2. Use Redis Labs free tier (30MB)")
            print("   3. Self-host Redis on a $4 droplet")
            print("\n   See REDIS_SETUP_GUIDE.md for instructions")
            return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def check_celery():
    """Check if Celery is configured"""
    try:
        from app.celery_app import celery_app
        
        print("\n🔍 Checking Celery configuration...")
        print(f"   Broker: {celery_app.conf.broker_url[:50]}...")
        
        # Try to get workers
        inspect = celery_app.control.inspect(timeout=5)
        active = inspect.active()
        stats = inspect.stats()
        
        if stats:
            print(f"✅ Celery workers online: {list(stats.keys())}")
            return True
        else:
            print("⚠️  No Celery workers found")
            print("   This is normal if workers aren't running yet")
            return False
            
    except Exception as e:
        print(f"❌ Celery check failed: {e}")
        return False

def check_email_config():
    """Check if email is configured"""
    print("\n🔍 Checking email configuration...")
    
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USERNAME')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    
    if all([smtp_host, smtp_user, smtp_pass]):
        print(f"✅ Email configured")
        print(f"   Host: {smtp_host}")
        print(f"   User: {smtp_user}")
        return True
    else:
        print("❌ Email not fully configured")
        return False

def main():
    print("=" * 60)
    print("AI CRUEL - Production Diagnostic Tool")
    print("=" * 60)
    
    redis_ok = check_redis()
    celery_ok = check_celery()
    email_ok = check_email_config()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Redis:  {'✅' if redis_ok else '❌'}")
    print(f"Celery: {'✅' if celery_ok else '⚠️  (needs Redis)'}")
    print(f"Email:  {'✅' if email_ok else '❌'}")
    
    if not redis_ok:
        print("\n🚨 ACTION REQUIRED:")
        print("   Your Redis limit is exceeded. Email reminders will NOT work.")
        print("   Follow the instructions in REDIS_SETUP_GUIDE.md")
    elif redis_ok and not celery_ok:
        print("\n⚠️  NEEDS SETUP:")
        print("   Redis is working, but Celery workers need to be started.")
        print("   Make sure your production server runs start_services.py")
    elif redis_ok and celery_ok and email_ok:
        print("\n✅ ALL SYSTEMS GO!")
        print("   Email reminders should be working automatically")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
