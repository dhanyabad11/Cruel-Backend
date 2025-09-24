#!/usr/bin/env python3
"""
Database Management Tool

Utilities for managing the AI Cruel database including backup, restore, and maintenance operations.

Usage:
    python db_manager.py backup              # Create database backup
    python db_manager.py restore backup.db   # Restore from backup
    python db_manager.py stats               # Show database statistics
    python db_manager.py clean               # Clean up old data
"""

import sys
import os
import argparse
import sqlite3
import shutil
from datetime import datetime, timedelta

def backup_database(db_path="ai_cruel.db"):
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backup_ai_cruel_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def restore_database(backup_path, db_path="ai_cruel.db"):
    """Restore database from backup"""
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    try:
        # Create backup of current database first
        current_backup = backup_database(db_path)
        if current_backup:
            print(f"📦 Current database backed up to: {current_backup}")
        
        # Restore from backup
        shutil.copy2(backup_path, db_path)
        print(f"✅ Database restored from: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def show_database_stats(db_path="ai_cruel.db"):
    """Show database statistics"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 Database Statistics")
        print("=" * 50)
        
        # Table counts
        tables = ['users', 'deadlines', 'portals', 'notifications', 'schema_migrations']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table.capitalize()}: {count}")
            except sqlite3.OperationalError:
                print(f"{table.capitalize()}: Table not found")
        
        # Deadline statistics
        print("\n📅 Deadline Statistics:")
        try:
            cursor.execute("SELECT status, COUNT(*) FROM deadlines GROUP BY status")
            for status, count in cursor.fetchall():
                print(f"  {status.capitalize()}: {count}")
            
            cursor.execute("SELECT priority, COUNT(*) FROM deadlines GROUP BY priority")
            print("\n🎯 Priority Distribution:")
            for priority, count in cursor.fetchall():
                print(f"  {priority.capitalize()}: {count}")
                
            # Upcoming deadlines
            cursor.execute("""
                SELECT COUNT(*) FROM deadlines 
                WHERE due_date > datetime('now') AND status != 'completed'
            """)
            upcoming = cursor.fetchone()[0]
            print(f"\n⏰ Upcoming deadlines: {upcoming}")
            
            # Overdue deadlines
            cursor.execute("""
                SELECT COUNT(*) FROM deadlines 
                WHERE due_date < datetime('now') AND status != 'completed'
            """)
            overdue = cursor.fetchone()[0]
            print(f"🚨 Overdue deadlines: {overdue}")
            
        except sqlite3.OperationalError as e:
            print(f"Could not get deadline statistics: {e}")
        
        # Database size
        db_size = os.path.getsize(db_path)
        print(f"\n💾 Database size: {db_size / 1024:.1f} KB")
        
        print("=" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")

def clean_old_data(db_path="ai_cruel.db", days_old=365):
    """Clean up old data from the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        print(f"🧹 Cleaning data older than {cutoff_date.strftime('%Y-%m-%d')}")
        
        # Clean old completed deadlines
        cursor.execute("""
            DELETE FROM deadlines 
            WHERE status = 'completed' AND updated_at < ?
        """, (cutoff_date,))
        
        deleted_deadlines = cursor.rowcount
        
        # Clean old notifications
        cursor.execute("""
            DELETE FROM notifications 
            WHERE created_at < ?
        """, (cutoff_date,))
        
        deleted_notifications = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleaned {deleted_deadlines} old deadlines and {deleted_notifications} old notifications")
        
        # Vacuum database to reclaim space
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        
        print("✅ Database optimized")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def validate_database(db_path="ai_cruel.db"):
    """Validate database integrity"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Validating database integrity...")
        
        # Check for orphaned deadlines
        cursor.execute("""
            SELECT COUNT(*) FROM deadlines d 
            LEFT JOIN users u ON d.user_id = u.id 
            WHERE u.id IS NULL
        """)
        orphaned_deadlines = cursor.fetchone()[0]
        
        if orphaned_deadlines > 0:
            print(f"⚠️  Found {orphaned_deadlines} orphaned deadlines")
        else:
            print("✅ No orphaned deadlines found")
        
        # Check for invalid dates
        cursor.execute("""
            SELECT COUNT(*) FROM deadlines 
            WHERE due_date IS NULL OR due_date = ''
        """)
        invalid_dates = cursor.fetchone()[0]
        
        if invalid_dates > 0:
            print(f"⚠️  Found {invalid_dates} deadlines with invalid dates")
        else:
            print("✅ All deadlines have valid dates")
        
        # SQLite integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result == 'ok':
            print("✅ Database integrity check passed")
        else:
            print(f"❌ Database integrity issues: {integrity_result}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Database Management Tool for AI Cruel")
    parser.add_argument("action", choices=['backup', 'restore', 'stats', 'clean', 'validate'], 
                       help="Action to perform")
    parser.add_argument("--file", help="Backup file path for restore operation")
    parser.add_argument("--days", type=int, default=365, help="Days threshold for cleanup")
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        backup_database()
    elif args.action == 'restore':
        if not args.file:
            print("❌ Restore requires --file parameter")
            sys.exit(1)
        restore_database(args.file)
    elif args.action == 'stats':
        show_database_stats()
    elif args.action == 'clean':
        clean_old_data(days_old=args.days)
    elif args.action == 'validate':
        validate_database()

if __name__ == "__main__":
    main()