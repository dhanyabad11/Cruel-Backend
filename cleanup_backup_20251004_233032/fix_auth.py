#!/usr/bin/env python3
"""
Script to fix authentication issues across all route files
"""

import os
import re

# Files that need to be fixed
FILES_TO_FIX = [
    "app/routes/portal_routes.py",
    "app/routes/notification_routes.py", 
    "app/routes/task_routes.py",
    "app/routes/whatsapp_routes.py"
]

def fix_file(filepath):
    """Fix authentication issues in a single file"""
    print(f"Fixing {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports
    content = re.sub(
        r'from app\.utils\.auth import get_current_active_user',
        'from app.auth_deps import get_current_user',
        content
    )
    
    content = re.sub(
        r'from app\.utils\.auth import get_current_user',
        'from app.auth_deps import get_current_user',
        content
    )
    
    # Add Dict and Any imports if not present
    if 'from typing import' in content and 'Dict' not in content:
        content = re.sub(
            r'from typing import ([^\\n]+)',
            r'from typing import \1, Dict, Any',
            content
        )
    
    # Fix function signatures
    content = re.sub(
        r'current_user: User = Depends\(get_current_active_user\)',
        'current_user: Dict[str, Any] = Depends(get_current_user)',
        content
    )
    
    content = re.sub(
        r'current_user: User = Depends\(get_current_user\)',
        'current_user: Dict[str, Any] = Depends(get_current_user)',
        content
    )
    
    # Fix current_user.id references
    content = re.sub(
        r'current_user\.id',
        "current_user['id']",
        content
    )
    
    # Fix current_user.email references  
    content = re.sub(
        r'current_user\.email',
        "current_user['email']",
        content
    )
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Fixed {filepath}")
    else:
        print(f"  ⚪ No changes needed for {filepath}")

def main():
    """Main function"""
    print("🔧 Fixing authentication issues across all route files...")
    
    for file_path in FILES_TO_FIX:
        fix_file(file_path)
    
    print("✅ Authentication fixes complete!")

if __name__ == "__main__":
    main()