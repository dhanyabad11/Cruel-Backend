#!/bin/bash

# Backend Cleanup Script
# This script removes unnecessary and unused files from the backend

echo "🧹 Starting Backend Cleanup..."
echo ""

BACKEND_DIR="/Users/dhanyabad/code2/cruel/ai-cruel/backend"
cd "$BACKEND_DIR"

# Create backup directory
BACKUP_DIR="$BACKEND_DIR/cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backup directory created: $BACKUP_DIR"
echo ""

# Function to move files to backup
backup_and_remove() {
    local file=$1
    if [ -f "$file" ]; then
        echo "  ➜ Moving $file to backup"
        mv "$file" "$BACKUP_DIR/"
    fi
}

# 1. Remove duplicate/old SQL setup files
echo "1️⃣  Removing duplicate SQL setup files..."
echo "   (Keeping: complete_notification_database_setup.sql, supabase_database_setup.sql)"

backup_and_remove "complete_database_setup.sql"
backup_and_remove "simple_database_setup.sql"
backup_and_remove "quick_setup.sql"
backup_and_remove "supabase_setup.sql"
backup_and_remove "notification_settings_setup.sql"
backup_and_remove "enhanced_notification_settings_setup.sql"

echo ""

# 2. Remove duplicate RLS fix files
echo "2️⃣  Removing duplicate RLS fix files..."
echo "   (These were one-time fixes, no longer needed)"

backup_and_remove "fix_rls.sql"
backup_and_remove "simple_rls_fix.sql"
backup_and_remove "simple_working_rls.sql"
backup_and_remove "working_rls.sql"
backup_and_remove "final_rls_fix.sql"
backup_and_remove "fix_database_schema.sql"

echo ""

# 3. Remove old/test files
echo "3️⃣  Removing old test and fix files..."

backup_and_remove "fix_auth.py"
backup_and_remove "create_test_user.sql"

echo ""

# 4. Remove unused service files
echo "4️⃣  Removing unused service files..."

backup_and_remove "app/services/auth_service_old.py"
backup_and_remove "app/services/test_email.py"

echo ""

# 5. Remove redundant documentation
echo "5️⃣  Removing redundant documentation files..."
echo "   (Keeping: README.md only)"

backup_and_remove "DATABASE.md"
backup_and_remove "ENHANCED_NOTIFICATION_SETTINGS.md"
backup_and_remove "NOTIFICATIONS.md"
backup_and_remove "NOTIFICATION_SETTINGS.md"
backup_and_remove "SUPABASE_SETUP.md"

echo ""

# 6. Remove Celery beat schedule (regenerates automatically)
echo "6️⃣  Removing Celery beat schedule (auto-regenerates)..."

if [ -f "celerybeat-schedule" ]; then
    echo "  ➜ Removing celerybeat-schedule"
    rm -f "celerybeat-schedule"
fi

echo ""

# 7. Clean Python cache
echo "7️⃣  Cleaning Python cache files..."

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

echo ""

# Summary
echo "✅ Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  • Backup location: $BACKUP_DIR"
echo "  • Removed duplicate SQL files"
echo "  • Removed old RLS fix files"
echo "  • Removed unused service files"
echo "  • Removed redundant documentation"
echo "  • Cleaned Python cache"
echo ""
echo "📁 Files kept (essential):"
echo "  • main.py"
echo "  • requirements.txt"
echo "  • complete_notification_database_setup.sql"
echo "  • supabase_database_setup.sql"
echo "  • README.md"
echo "  • All app/ directory files (routes, services, models)"
echo ""
echo "💡 If you need any deleted file, check: $BACKUP_DIR"
