# 🗄️ Database Management System

This document describes the database management system for AI Cruel, including migrations, backups, and maintenance operations.

## 📋 Overview

The AI Cruel database system uses SQLite with a custom migration system to handle schema changes and data management. The system includes:

-   **Migration System**: Version-controlled database schema changes
-   **Backup & Restore**: Database backup and recovery tools
-   **Statistics & Monitoring**: Database health and usage statistics
-   **Maintenance**: Cleanup and optimization tools

## 🔄 Migration System

### Running Migrations

```bash
# Apply all pending migrations
python3 migrate.py

# Check migration status
python3 migrate.py --status

# Create new migration template
python3 migrate.py --create "Add user preferences table"
```

### Migration Structure

```python
from migrations import migrate

@migrate("004", "Description of migration")
def migration_name(cursor):
    """Implementation of migration"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL
        )
    ''')
```

### Current Migrations

| Version | Description                            | Status     |
| ------- | -------------------------------------- | ---------- |
| 001     | Create enhanced database schema        | ✅ Applied |
| 002     | Add sample data for testing            | ✅ Applied |
| 003     | Update existing schema to match models | ✅ Applied |

## 💾 Database Management

### Backup Operations

```bash
# Create backup
python3 db_manager.py backup

# Restore from backup
python3 db_manager.py restore --file backup_ai_cruel_20250924_111740.db
```

### Statistics & Monitoring

```bash
# Show database statistics
python3 db_manager.py stats

# Validate database integrity
python3 db_manager.py validate
```

### Maintenance

```bash
# Clean old data (older than 1 year)
python3 db_manager.py clean

# Clean with custom threshold (older than 90 days)
python3 db_manager.py clean --days 90
```

## 📊 Current Database Schema

### Users Table

-   **id**: Primary key
-   **email**: Unique user email
-   **hashed_password**: Bcrypt hashed password
-   **full_name**: User's display name
-   **phone**: Phone number for notifications
-   **is_active**: Account status
-   **is_verified**: Email/phone verification status
-   **notification_preferences**: JSON string with user preferences
-   **created_at**: Account creation timestamp
-   **updated_at**: Last modification timestamp

### Deadlines Table

-   **id**: Primary key
-   **user_id**: Foreign key to users table
-   **title**: Deadline title (max 500 chars)
-   **description**: Detailed description
-   **due_date**: Deadline date and time
-   **priority**: low, medium, high, critical
-   **status**: pending, in_progress, completed, overdue
-   **portal_id**: Foreign key to portals table
-   **portal_task_id**: External system ID
-   **portal_url**: Link to original task
-   **reminder_sent**: Notification tracking
-   **reminder_count**: Number of reminders sent
-   **last_reminder_sent**: Last reminder timestamp
-   **estimated_hours**: Time estimation
-   **actual_hours**: Actual time spent
-   **tags**: JSON array of tags
-   **created_at**: Creation timestamp
-   **updated_at**: Last modification timestamp

### Portals Table

-   **id**: Primary key
-   **user_id**: Foreign key to users table
-   **name**: Portal display name
-   **portal_type**: github, jira, trello, whatsapp, manual
-   **url**: Portal URL
-   **credentials**: Encrypted JSON credentials
-   **config**: JSON configuration
-   **is_active**: Portal status
-   **last_sync**: Last synchronization time
-   **sync_status**: idle, syncing, error, success
-   **last_error**: Last error message
-   **sync_count**: Number of sync operations
-   **created_at**: Creation timestamp
-   **updated_at**: Last modification timestamp

## 🔧 Development Workflow

### Adding New Features

1. **Create Migration**: Use the migration system for schema changes

    ```bash
    python3 migrate.py --create "Add feature X table"
    ```

2. **Update Models**: Modify SQLAlchemy models in `app/models/`

3. **Update Schemas**: Add Pydantic schemas in `app/schemas/`

4. **Test Migration**: Apply and test migration

    ```bash
    python3 migrate.py
    python3 db_manager.py validate
    ```

5. **Create Backup**: Always backup before production deployment
    ```bash
    python3 db_manager.py backup
    ```

### Database Maintenance Schedule

-   **Daily**: Automated backup (in production)
-   **Weekly**: Statistics review and performance monitoring
-   **Monthly**: Data cleanup and optimization
-   **Before Updates**: Manual backup and validation

## 📈 Performance Optimization

### Indexes

The system includes optimized indexes for:

-   User lookups by email
-   Deadline queries by user_id, due_date, and status
-   Portal queries by user_id
-   Notification queries by user_id and deadline_id

### Query Optimization

-   Use proper WHERE clauses with indexed columns
-   Limit result sets with LIMIT/OFFSET for pagination
-   Use EXISTS instead of IN for subqueries
-   Consider EXPLAIN QUERY PLAN for complex queries

## 🚨 Troubleshooting

### Common Issues

**Migration Fails**

```bash
# Check current schema
sqlite3 ai_cruel.db ".schema table_name"

# Manual fix if needed
sqlite3 ai_cruel.db "ALTER TABLE ..."

# Mark migration as applied
sqlite3 ai_cruel.db "INSERT INTO schema_migrations (version, description) VALUES ('XXX', 'Description')"
```

**Database Corruption**

```bash
# Check integrity
python3 db_manager.py validate

# Restore from backup
python3 db_manager.py restore --file backup_file.db
```

**Performance Issues**

```bash
# Show statistics
python3 db_manager.py stats

# Clean old data
python3 db_manager.py clean --days 30

# Rebuild indexes
sqlite3 ai_cruel.db "REINDEX"
```

## 🔐 Security Considerations

-   **Credentials**: Portal credentials are stored encrypted
-   **Backups**: Ensure backups are stored securely
-   **Access Control**: Database access limited to application
-   **SQL Injection**: Always use parameterized queries
-   **Personal Data**: Follow data retention policies

## 📝 Best Practices

1. **Always backup before migrations**
2. **Test migrations on development data first**
3. **Use transactions for multi-step operations**
4. **Monitor database size and performance**
5. **Clean old data regularly**
6. **Validate database integrity periodically**
7. **Document all schema changes**
8. **Use proper indexing for query performance**

---

This database management system ensures reliable, scalable, and maintainable data storage for the AI Cruel deadline management system.
