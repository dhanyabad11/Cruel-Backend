"""
Database Migration System

Simple migration system for AI Cruel database schema changes.
This allows us to version control our database changes and apply them systematically.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Callable
import logging

logger = logging.getLogger(__name__)

class MigrationManager:
    """Simple migration manager for SQLite database"""
    
    def __init__(self, db_path: str = "ai_cruel.db", migrations_dir: str = "migrations"):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.migrations: Dict[str, Callable] = {}
        
    def register_migration(self, version: str, description: str):
        """Decorator to register a migration function"""
        def decorator(func: Callable):
            self.migrations[version] = {
                'function': func,
                'description': description,
                'version': version
            }
            return func
        return decorator
    
    def create_migration_table(self):
        """Create migrations table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(20) PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
        finally:
            conn.close()
    
    def apply_migration(self, version: str):
        """Apply a single migration"""
        if version not in self.migrations:
            raise ValueError(f"Migration {version} not found")
        
        migration = self.migrations[version]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            logger.info(f"Applying migration {version}: {migration['description']}")
            
            # Apply the migration
            migration['function'](cursor)
            
            # Record the migration
            cursor.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, migration['description'])
            )
            
            conn.commit()
            logger.info(f"✅ Migration {version} applied successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration {version} failed: {e}")
            raise
        finally:
            conn.close()
    
    def migrate(self):
        """Apply all pending migrations"""
        self.create_migration_table()
        applied = self.get_applied_migrations()
        
        # Sort migrations by version
        pending = sorted([
            version for version in self.migrations.keys() 
            if version not in applied
        ])
        
        if not pending:
            logger.info("✅ No pending migrations")
            return
        
        logger.info(f"📦 Applying {len(pending)} pending migrations...")
        
        for version in pending:
            self.apply_migration(version)
        
        logger.info("🎉 All migrations applied successfully!")
    
    def status(self):
        """Show migration status"""
        self.create_migration_table()
        applied = self.get_applied_migrations()
        
        print("\n📊 Migration Status:")
        print("=" * 50)
        
        all_versions = sorted(self.migrations.keys())
        
        for version in all_versions:
            migration = self.migrations[version]
            status = "✅ Applied" if version in applied else "⏳ Pending"
            print(f"{version}: {migration['description']} - {status}")
        
        print("=" * 50)
        print(f"Applied: {len(applied)}, Pending: {len(all_versions) - len(applied)}")

# Initialize migration manager
migration_manager = MigrationManager()

# Migration decorator
migrate = migration_manager.register_migration