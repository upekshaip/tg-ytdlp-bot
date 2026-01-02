#!/usr/bin/env python3
"""
Create a backup of project modules before applying fixes.
"""

import os
import shutil
import datetime
from pathlib import Path

def create_backup():
    """Create a backup of project modules."""
    
    print("💾 CREATING BACKUP OF ALL MODULES")
    print("=" * 50)
    
    # Create the backup directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_before_fixes_{timestamp}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"📁 Created backup directory: {backup_dir}")
        
        # List of folders/files to back up
        items_to_backup = [
            'COMMANDS/',
            'HELPERS/',
            'DATABASE/',
            'URL_PARSERS/',
            'DOWN_AND_UP/',
            'CONFIG/',
            'PATCH/',
            'restore_from_backup.py',
            'update_from_repo.py',
            'magic.py'
        ]
        
        backed_up_count = 0
        
        for item in items_to_backup:
            if os.path.exists(item):
                if os.path.isdir(item):
                    # Copy directory
                    dest_path = os.path.join(backup_dir, item)
                    shutil.copytree(item, dest_path)
                    print(f"📁 Copied directory: {item}")
                    backed_up_count += 1
                else:
                    # Copy file
                    dest_path = os.path.join(backup_dir, item)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(item, dest_path)
                    print(f"📄 Copied file: {item}")
                    backed_up_count += 1
            else:
                print(f"⚠️  Not found: {item}")
        
        print("\n✅ BACKUP CREATED SUCCESSFULLY!")
        print(f"   📁 Backup directory: {backup_dir}")
        print(f"   📊 Items copied: {backed_up_count}")
        print(f"   🕒 Created at: {timestamp}")
        
        # Write backup metadata file
        backup_info = f"""BACKUP CREATED: {timestamp}
===============================

Purpose: Backup before fixing 'name messages is not defined'
Contents: All project modules and files
Items: {backed_up_count}

Restore steps:
1. Stop the bot
2. Remove the broken files
3. Copy files from this directory back into the project
4. Start the bot

WARNING: This backup was created automatically before applying fixes!
"""
        
        with open(os.path.join(backup_dir, "BACKUP_INFO.txt"), 'w', encoding='utf-8') as f:
            f.write(backup_info)
        
        print(f"📝 Wrote info file: {backup_dir}/BACKUP_INFO.txt")
        
        return backup_dir
        
    except Exception as e:
        print(f"❌ Error while creating backup: {e}")
        return None

if __name__ == "__main__":
    backup_dir = create_backup()
    if backup_dir:
        print(f"\n🎉 Backup ready! Directory: {backup_dir}")
    else:
        print("\n❌ Backup creation failed!")
