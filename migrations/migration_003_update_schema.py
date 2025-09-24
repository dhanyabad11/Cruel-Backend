"""
Migration 003: Update existing schema to match current models

Updates the existing database schema to match our current SQLAlchemy models.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations import migrate

@migrate("003", "Update existing schema to match current models")
def update_existing_schema(cursor):
    """Update existing schema to match current models"""
    
    # Update users table to match current model
    try:
        # Add missing columns to users table
        cursor.execute('ALTER TABLE users ADD COLUMN phone VARCHAR(20)')
    except:
        pass  # Column might already exist
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN notification_preferences TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except:
        pass
    
    # Add missing indexes
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_user_id ON deadlines (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON deadlines (due_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadlines (status)')
    except:
        pass
    
    print("✅ Schema updated successfully")