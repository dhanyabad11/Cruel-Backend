"""
Migration 001: Enhanced Database Schema

Creates the complete database schema with all tables and relationships
for the AI Cruel deadline management system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations import migrate

@migrate("001", "Create enhanced database schema with all core tables")
def create_enhanced_schema(cursor):
    """Create all tables for the AI Cruel system"""
    
    # Users table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            
            -- Student-specific fields
            university VARCHAR(255),
            major VARCHAR(255),
            graduation_year INTEGER,
            
            -- WhatsApp integration
            whatsapp_phone VARCHAR(20),
            whatsapp_verified BOOLEAN DEFAULT 0,
            
            -- Preferences
            timezone VARCHAR(50) DEFAULT 'UTC',
            notification_preferences TEXT, -- JSON string
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Portals table for external integrations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            portal_type VARCHAR(50) NOT NULL CHECK (portal_type IN ('github', 'jira', 'trello', 'whatsapp', 'manual')),
            url VARCHAR(500),
            
            -- Credentials (encrypted JSON)
            credentials TEXT,
            config TEXT, -- JSON for portal-specific config
            
            -- Status tracking
            is_active BOOLEAN DEFAULT 1,
            last_sync TIMESTAMP,
            sync_status VARCHAR(50) DEFAULT 'idle', -- idle, syncing, error, success
            last_error TEXT,
            sync_count INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Enhanced deadlines table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            due_date TIMESTAMP NOT NULL,
            
            -- Priority and status
            priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
            
            -- Source information
            portal_id INTEGER,
            portal_source VARCHAR(50) DEFAULT 'manual',
            external_id VARCHAR(255), -- ID from external system
            external_url VARCHAR(1000), -- Link to original item
            
            -- WhatsApp-specific fields
            original_message TEXT, -- Original WhatsApp message
            sender VARCHAR(255), -- WhatsApp sender
            confidence_score DECIMAL(3,2), -- AI extraction confidence (0.00-1.00)
            
            -- Notification tracking
            reminder_sent BOOLEAN DEFAULT 0,
            reminder_count INTEGER DEFAULT 0,
            last_reminder_sent TIMESTAMP,
            
            -- Time tracking
            estimated_hours INTEGER,
            actual_hours INTEGER,
            
            -- Metadata
            tags TEXT, -- JSON array of tags
            attachments TEXT, -- JSON array of file paths/URLs
            notes TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (portal_id) REFERENCES portals (id) ON DELETE SET NULL
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_user_id ON deadlines (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON deadlines (due_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadlines (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_portals_user_id ON portals (user_id)')

@migrate("002", "Add sample data for development and testing")
def add_sample_data(cursor):
    """Add sample data for development and testing"""
    from datetime import datetime, timedelta
    
    # Update existing test user instead of trying to create
    cursor.execute('''
        UPDATE users SET 
            phone = '+1234567890',
            notification_preferences = '{"daily_summary": true, "reminder_hours": [24, 4, 1]}'
        WHERE email = 'test@example.com'
    ''')
    
    # Sample deadlines
    base_date = datetime.now()
    deadlines = [
        (1, 'Complete Project Proposal', 'Write and submit the final project proposal for CS 301', 
         base_date + timedelta(days=3), 'high', 'pending', None, 'manual'),
        
        (1, 'Math Assignment 5', 'Solve problems 1-20 from Chapter 8', 
         base_date + timedelta(days=7), 'medium', 'pending', None, 'manual'),
        
        (1, 'WhatsApp Lab Report', 'Submit lab report due according to WhatsApp message', 
         base_date + timedelta(days=5), 'high', 'pending', None, 'whatsapp'),
    ]
    
    for user_id, title, description, due_date, priority, status, portal_id, portal_source in deadlines:
        cursor.execute('''
            INSERT OR IGNORE INTO deadlines (
                user_id, title, description, due_date, priority, status, portal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, due_date, priority, status, portal_id))