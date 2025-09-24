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
    
    # Notifications table for tracking sent notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            deadline_id INTEGER,
            
            -- Notification details
            notification_type VARCHAR(20) NOT NULL, -- 'sms', 'whatsapp', 'email'
            phone_number VARCHAR(20),
            email VARCHAR(255),
            message_content TEXT NOT NULL,
            
            -- External service details (Twilio, etc.)
            message_sid VARCHAR(100), -- External service message ID
            external_status VARCHAR(20), -- External service status
            
            -- Our tracking
            status VARCHAR(20) DEFAULT 'pending', -- pending, sent, delivered, failed
            sent_at TIMESTAMP,
            delivered_at TIMESTAMP,
            failed_at TIMESTAMP,
            
            -- Error tracking
            error_code VARCHAR(10),
            error_message TEXT,
            
            -- Metadata
            notification_reason VARCHAR(50), -- 'reminder', 'daily_summary', 'overdue_alert'
            scheduled_for TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            extra_data TEXT, -- JSON for additional data
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (deadline_id) REFERENCES deadlines (id) ON DELETE CASCADE
        )
    ''')
    
    # Notification preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            
            -- Contact preferences
            phone_number VARCHAR(20),
            preferred_method VARCHAR(20) DEFAULT 'sms', -- 'sms', 'whatsapp', 'email'
            
            -- Daily summary preferences
            daily_summary_enabled BOOLEAN DEFAULT 1,
            daily_summary_time VARCHAR(5) DEFAULT '09:00', -- HH:MM format
            
            -- Reminder preferences
            reminder_enabled BOOLEAN DEFAULT 1,
            reminder_hours_before VARCHAR(20) DEFAULT '24,4,1', -- Comma-separated hours
            
            -- Overdue alert preferences
            overdue_alerts_enabled BOOLEAN DEFAULT 1,
            overdue_check_frequency VARCHAR(20) DEFAULT 'daily', -- hourly, daily
            
            -- Quiet hours
            quiet_hours_enabled BOOLEAN DEFAULT 0,
            quiet_hours_start VARCHAR(5) DEFAULT '22:00',
            quiet_hours_end VARCHAR(5) DEFAULT '08:00',
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # WhatsApp messages table for parsing history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            
            -- Message details
            sender VARCHAR(255),
            message_text TEXT NOT NULL,
            timestamp TIMESTAMP,
            chat_name VARCHAR(255),
            
            -- Processing details
            processed BOOLEAN DEFAULT 0,
            processing_error TEXT,
            deadlines_extracted INTEGER DEFAULT 0,
            confidence_score DECIMAL(3,2),
            
            -- Source file information
            source_file VARCHAR(255),
            line_number INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_user_id ON deadlines (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON deadlines (due_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadlines (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_portals_user_id ON portals (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_deadline_id ON notifications (deadline_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_user_id ON whatsapp_messages (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_processed ON whatsapp_messages (processed)')

@migrate("002", "Add sample data for development and testing")
def add_sample_data(cursor):
    """Add sample data for development and testing"""
    from datetime import datetime, timedelta
    import json
    
    # Sample user
    cursor.execute('''
        INSERT OR IGNORE INTO users (
            id, email, hashed_password, full_name, phone, university, major, graduation_year
        ) VALUES (
            1, 'test@example.com', 'hashed_password_here', 'Test User', '+1234567890',
            'Test University', 'Computer Science', 2025
        )
    ''')
    
    # Sample notification preferences
    cursor.execute('''
        INSERT OR IGNORE INTO notification_preferences (
            user_id, phone_number, preferred_method, daily_summary_enabled,
            reminder_enabled, reminder_hours_before
        ) VALUES (
            1, '+1234567890', 'whatsapp', 1, 1, '24,4,1'
        )
    ''')
    
    # Sample portals
    portals = [
        (1, 'GitHub - Personal', 'github', 'https://github.com', '{}', '{"auto_sync": true}'),
        (1, 'WhatsApp - Study Group', 'whatsapp', '', '{}', '{"chat_name": "CS Study Group"}'),
    ]
    
    for user_id, name, portal_type, url, credentials, config in portals:
        cursor.execute('''
            INSERT OR IGNORE INTO portals (
                user_id, name, portal_type, url, credentials, config
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, portal_type, url, credentials, config))
    
    # Sample deadlines
    base_date = datetime.now()
    deadlines = [
        # Upcoming deadlines
        (1, 'Complete Project Proposal', 'Write and submit the final project proposal for CS 301', 
         base_date + timedelta(days=3), 'high', 'pending', None, 'manual'),
        
        (1, 'Math Assignment 5', 'Solve problems 1-20 from Chapter 8', 
         base_date + timedelta(days=7), 'medium', 'pending', None, 'manual'),
        
        (1, 'Prepare Presentation', 'Create slides for the project presentation', 
         base_date + timedelta(days=10), 'medium', 'pending', None, 'manual'),
        
        # WhatsApp extracted deadline
        (1, 'Submit Lab Report', 'Lab report due according to WhatsApp message from Prof. Johnson', 
         base_date + timedelta(days=5), 'high', 'pending', None, 'whatsapp'),
    ]
    
    for user_id, title, description, due_date, priority, status, portal_id, portal_source in deadlines:
        cursor.execute('''
            INSERT OR IGNORE INTO deadlines (
                user_id, title, description, due_date, priority, status, portal_id, portal_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, due_date, priority, status, portal_id, portal_source))

@migrate("003", "Add WhatsApp integration enhancements") 
def add_whatsapp_enhancements(cursor):
    """Add enhancements for WhatsApp integration"""
    
    # Add WhatsApp-specific user fields if not exists
    cursor.execute('''
        ALTER TABLE users ADD COLUMN whatsapp_integration_enabled BOOLEAN DEFAULT 0
    ''')
    
    cursor.execute('''
        ALTER TABLE users ADD COLUMN whatsapp_webhook_token VARCHAR(255)
    ''')
    
    # Add WhatsApp chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_name VARCHAR(255),
            participants TEXT, -- JSON array
            total_messages INTEGER DEFAULT 0,
            deadlines_found INTEGER DEFAULT 0,
            processed_at TIMESTAMP,
            
            -- File upload details
            original_filename VARCHAR(255),
            file_size INTEGER,
            file_hash VARCHAR(64), -- For deduplication
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Link WhatsApp messages to chat sessions
    cursor.execute('''
        ALTER TABLE whatsapp_messages ADD COLUMN chat_session_id INTEGER REFERENCES whatsapp_chat_sessions(id)
    ''')
    
    # Add indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_chat_sessions_user_id ON whatsapp_chat_sessions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_chat_session ON whatsapp_messages (chat_session_id)')