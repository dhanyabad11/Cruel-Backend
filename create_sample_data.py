import sqlite3
from datetime import datetime, timedelta

# Connect to database
conn = sqlite3.connect('ai_cruel.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    is_superuser BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    portal_id INTEGER,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (portal_id) REFERENCES portals (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS portals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    portal_type VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    username VARCHAR(100),
    password VARCHAR(100),
    api_key VARCHAR(200),
    config TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_sync TIMESTAMP,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Insert sample user
cursor.execute('''
INSERT OR IGNORE INTO users (id, username, email, hashed_password, full_name) 
VALUES (1, 'testuser', 'test@example.com', 'hashedpassword', 'Test User')
''')

# Insert sample deadlines
sample_deadlines = [
    ('Complete Project Report', 'Final project report for Q3', datetime.now() + timedelta(days=7), 'high', 'pending', None, 1),
    ('Client Meeting Prep', 'Prepare presentation slides', datetime.now() + timedelta(days=3), 'medium', 'pending', None, 1),
    ('Submit Tax Documents', 'Annual tax filing deadline', datetime.now() + timedelta(days=30), 'high', 'pending', None, 1),
    ('Team Review Meeting', 'Quarterly team performance review', datetime.now() + timedelta(days=14), 'low', 'completed', None, 1),
    ('Update Website Content', 'Refresh homepage and about section', datetime.now() + timedelta(days=5), 'medium', 'pending', None, 1),
]

cursor.executemany('''
INSERT OR IGNORE INTO deadlines (title, description, due_date, priority, status, portal_id, user_id)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', sample_deadlines)

# Insert sample portals
sample_portals = [
    ('GitHub Issues', 'github', 'https://github.com/myproject/issues', 'myusername', '', 'ghp_token123', '{}', 1, 1),
    ('Jira Dashboard', 'jira', 'https://mycompany.atlassian.net', 'jira@company.com', 'password', '', '{}', 1, 1),
    ('Trello Board', 'trello', 'https://trello.com/b/boardid', '', '', 'trello_key_123', '{}', 1, 1),
]

cursor.executemany('''
INSERT OR IGNORE INTO portals (name, portal_type, url, username, password, api_key, config, is_active, user_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', sample_portals)

conn.commit()
conn.close()

print("Sample data inserted successfully!")