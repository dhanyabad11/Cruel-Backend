"""
Test Task System

Script to test Celery task system functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.celery_app import celery_app
from app.tasks.scraping_tasks import scrape_all_portals
from app.tasks.notification_tasks import send_deadline_reminders
from app.tasks.maintenance_tasks import health_check, generate_system_stats


def test_celery_connection():
    """Test basic Celery connectivity"""
    print("🧪 Testing Celery Connection...")
    
    try:
        # Test broker connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery broker is connected")
            print(f"Active workers: {list(stats.keys())}")
        else:
            print("⚠️ No active Celery workers found")
            print("To start workers, run: ./start_worker.sh")
        
        return bool(stats)
        
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False


def test_task_registration():
    """Test that tasks are properly registered"""
    print("\n🧪 Testing Task Registration...")
    
    try:
        inspect = celery_app.control.inspect()
        registered = inspect.registered()
        
        if registered:
            print("✅ Tasks are registered")
            
            # Check for our specific tasks
            expected_tasks = [
                'app.tasks.scraping_tasks.scrape_all_portals',
                'app.tasks.notification_tasks.send_deadline_reminders',
                'app.tasks.maintenance_tasks.health_check'
            ]
            
            all_tasks = []
            for worker, tasks in registered.items():
                all_tasks.extend(tasks)
            
            for task in expected_tasks:
                if task in all_tasks:
                    print(f"  ✅ {task}")
                else:
                    print(f"  ❌ {task} - NOT FOUND")
            
        else:
            print("❌ No tasks registered (no workers running?)")
        
        return bool(registered)
        
    except Exception as e:
        print(f"❌ Task registration check failed: {e}")
        return False


def test_simple_task():
    """Test a simple task execution"""
    print("\n🧪 Testing Simple Task Execution...")
    
    try:
        # Test the debug task
        result = celery_app.send_task('app.celery_app.debug_task')
        print(f"✅ Task submitted: {result.id}")
        
        # Wait for result (with timeout)
        try:
            task_result = result.get(timeout=10)
            print(f"✅ Task completed: {task_result}")
            return True
        except Exception as e:
            print(f"⚠️ Task execution timeout or failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Simple task test failed: {e}")
        return False


def test_scheduled_tasks():
    """Test scheduled task configuration"""
    print("\n🧪 Testing Scheduled Tasks Configuration...")
    
    try:
        beat_schedule = celery_app.conf.beat_schedule
        
        if beat_schedule:
            print("✅ Beat schedule configured")
            for task_name, config in beat_schedule.items():
                print(f"  📅 {task_name}: {config['schedule']}")
        else:
            print("❌ No beat schedule configured")
        
        return bool(beat_schedule)
        
    except Exception as e:
        print(f"❌ Scheduled tasks test failed: {e}")
        return False


def test_queue_configuration():
    """Test queue configuration"""
    print("\n🧪 Testing Queue Configuration...")
    
    try:
        # Check queue routing
        task_routes = celery_app.conf.task_routes
        
        if task_routes:
            print("✅ Task routing configured")
            for pattern, route in task_routes.items():
                print(f"  🔀 {pattern} -> {route}")
        else:
            print("⚠️ No task routing configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Queue configuration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 AI Cruel Task System Tests")
    print("=" * 50)
    
    tests = [
        ("Celery Connection", test_celery_connection),
        ("Task Registration", test_task_registration),
        ("Simple Task", test_simple_task),
        ("Scheduled Tasks", test_scheduled_tasks),
        ("Queue Configuration", test_queue_configuration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Task system is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        print("\nTo fix common issues:")
        print("1. Make sure Redis is running: brew services start redis")
        print("2. Start Celery worker: ./start_worker.sh")
        print("3. Start Celery beat: ./start_beat.sh")


if __name__ == "__main__":
    main()