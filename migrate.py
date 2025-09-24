#!/usr/bin/env python3
"""
Database Migration Runner

Run database migrations for AI Cruel system.

Usage:
    python migrate.py                  # Apply all pending migrations
    python migrate.py --status         # Show migration status
    python migrate.py --create NAME    # Create new migration template
"""

import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Setup logging configuration"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_migrations():
    """Apply all pending migrations"""
    try:
        # Import migrations to register them
        import migrations.migration_001_enhanced_schema
        import migrations.migration_003_update_schema
        
        # Get migration manager and run migrations
        from migrations import migration_manager
        migration_manager.migrate()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

def show_status():
    """Show migration status"""
    try:
        # Import migrations to register them
        import migrations.migration_001_enhanced_schema
        import migrations.migration_003_update_schema
        
        # Get migration manager and show status
        from migrations import migration_manager
        migration_manager.status()
        
    except Exception as e:
        print(f"❌ Failed to show status: {e}")
        sys.exit(1)

def create_migration_template(name: str):
    """Create a new migration template"""
    # Get next version number
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    existing = [f for f in os.listdir(migrations_dir) if f.startswith("migration_") and f.endswith(".py")]
    
    if existing:
        versions = [int(f.split("_")[1]) for f in existing if f.split("_")[1].isdigit()]
        next_version = max(versions) + 1 if versions else 1
    else:
        next_version = 1
    
    version_str = f"{next_version:03d}"
    filename = f"migration_{version_str}_{name.lower().replace(' ', '_')}.py"
    filepath = os.path.join(migrations_dir, filename)
    
    template = f'''"""
Migration {version_str}: {name.title()}

TODO: Describe what this migration does
"""

from migrations import migrate

@migrate("{version_str}", "{name.title()}")
def {name.lower().replace(' ', '_').replace('-', '_')}(cursor):
    """TODO: Implement migration"""
    
    # Example: Add a new column
    # cursor.execute(\'\'\'
    #     ALTER TABLE users ADD COLUMN new_field VARCHAR(255)
    # \'\'\')
    
    # Example: Create a new table
    # cursor.execute(\'\'\'
    #     CREATE TABLE IF NOT EXISTS new_table (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         name VARCHAR(255) NOT NULL,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     )
    # \'\'\')
    
    # Example: Create an index
    # cursor.execute(\'\'\'
    #     CREATE INDEX IF NOT EXISTS idx_new_table_name ON new_table (name)
    # \'\'\')
    
    pass  # Remove this when implementing
'''
    
    with open(filepath, 'w') as f:
        f.write(template)
    
    print(f"✅ Created migration template: {filepath}")
    print(f"📝 Edit the file to implement your migration, then run: python migrate.py")

def main():
    parser = argparse.ArgumentParser(description="Database Migration Runner for AI Cruel")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--create", metavar="NAME", help="Create new migration template")
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.status:
        show_status()
    elif args.create:
        create_migration_template(args.create)
    else:
        run_migrations()

if __name__ == "__main__":
    main()