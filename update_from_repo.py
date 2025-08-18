#!/usr/bin/env python3
"""
Script to automatically update code from a GitHub repository.
Clones the repository into a temporary folder and replaces required files.
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
REPO_URL = "https://github.com/chelaxian/tg-ytdlp-bot.git"
#BRANCH = "newdesign"
BRANCH = "main"

# Files and directories that MUST NOT be updated
EXCLUDED_FILES = [
    "CONFIG/config.py",  # Main configuration file
    #"requirements.txt", # Dependencies may differ
    ".env",              # Environment variables
    ".bot_pid",          # Bot PID file
    "bot.log",           # Bot logs
    "runtime.log",       # Runtime logs
    "magic.session",     # Pyrogram session
    "magic.session-journal",  # Session journal
    "dump.json",         # Firebase dump
    "script.sh",         # Script for updating porn lists
]

EXCLUDED_DIRS = [
    "CONFIG",            # Entire configuration directory
    "venv",              # Virtual environment
    ".git",              # Git repository
    "__pycache__",       # Python cache
    "_backup",           # Backups
    "users",             # User data
    "cookies",           # Cookie files
    "TXT",               # Text files
    "_arabic_fonts_amiri",  # Fonts
    "_cursor",           # Cursor temp workspace
]

def log(message, level="INFO"):
    """Logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def should_update_file(file_path):
    """Checks whether the file should be updated"""
    # Check excluded files
    for excluded in EXCLUDED_FILES:
        if file_path == excluded:
            return False
    
    # Check excluded directories
    for excluded_dir in EXCLUDED_DIRS:
        if file_path.startswith(excluded_dir + "/"):
            return False
    
    # Update only Python files
    if not file_path.endswith('.py'):
        return False
    
    return True

def backup_file(file_path):
    """Create a backup copy of a file"""
    try:
        if os.path.exists(file_path):
            # Use minute-level timestamp to group all backups within a minute
            backup_ts = datetime.now().strftime('%Y%m%d_%H%M')
            backup_path = f"{file_path}.backup_{backup_ts}"
            shutil.copy2(file_path, backup_path)
            log(f"Backup created: {backup_path}")
            return backup_path
    except Exception as e:
        log(f"Error creating backup for {file_path}: {e}", "ERROR")
    return None

def clone_repository(temp_dir):
    """Clone the repository into the temporary folder"""
    try:
        log(f"📥 Cloning repository into {temp_dir}...")
        
        # Command for cloning
        cmd = [
            'git', 'clone', 
            '--branch', BRANCH,
            '--depth', '1',  # Only the last commit
            '--single-branch',
            REPO_URL, 
            temp_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            log("✅ Repository cloned successfully")
            return True
        else:
            log(f"❌ Clone error: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log("❌ Clone timeout", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Clone exception: {e}", "ERROR")
        return False

def find_python_files(source_dir):
    """Find all Python files in the source directory"""
    python_files = []
    
    for root, dirs, files in os.walk(source_dir):
        # Exclude unnecessary directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                # Build relative path
                rel_path = os.path.relpath(os.path.join(root, file), source_dir)
                if should_update_file(rel_path):
                    python_files.append(rel_path)
    
    return sorted(python_files)

def update_file_from_source(source_file, target_file):
    """Update a file from the source repository"""
    try:
        # Create directories if missing (only if file is not in the project root)
        dir_name = os.path.dirname(target_file)
        if dir_name:  # Directory path is not empty
            os.makedirs(dir_name, exist_ok=True)
        
        # Create a backup
        backup_path = backup_file(target_file)
        
        # Copy the file
        shutil.copy2(source_file, target_file)
        
        log(f"Updated file: {target_file}")
        if backup_path:
            log(f"Backup: {backup_path}")
        
        return True
    except Exception as e:
        log(f"Error updating file {target_file}: {e}", "ERROR")
        return False

def move_backups_to_backup_dir():
    """Move all *.backup* files into _backup directory, keeping relative paths."""
    try:
        log("📦 Moving backups to _backup/...")
        cmd = "mkdir -p _backup && find . -path './_backup' -prune -o -type f -name \"*.backup*\" -print0 | sed -z 's#^\\./##' | rsync -a --relative --from0 --files-from=- --remove-source-files ./ _backup/"
        subprocess.run(["bash", "-lc", cmd], check=True)
        log("✅ Backups moved to _backup/")
    except Exception as e:
        log(f"⚠️ Failed to move backups: {e}", "WARNING")

def main():
    """Main update routine"""
    log("🚀 Starting update from GitHub repository")
    log(f"Repository: {REPO_URL}")
    log(f"Branch: {BRANCH}")
    
    # Ensure we are in the correct directory
    if not os.path.exists("magic.py"):
        log("❌ File magic.py not found. Make sure you run this in the bot folder.", "ERROR")
        return False
    
    # Ensure git is available
    if not shutil.which('git'):
        log("❌ Git not found. Please install Git to use this updater.", "ERROR")
        return False
    
    # Create temp directory
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="tg-ytdlp-update-")
        log(f"📁 Temporary directory created: {temp_dir}")
        
        # Clone repository
        if not clone_repository(temp_dir):
            return False
        
        # Find Python files
        python_files = find_python_files(temp_dir)
        
        if not python_files:
            log("❌ No Python files found to update", "ERROR")
            return False
        
        log(f"📋 Found {len(python_files)} Python files to update")
        
        # Show file list to update
        log("📝 Files to update:")
        for file_path in python_files:
            log(f"  - {file_path}")
        
        # Ask for confirmation
        response = input("\n🤔 Proceed with update? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            log("❌ Update canceled by user")
            return False
        
        # Update files
        updated_count = 0
        failed_count = 0
        
        for file_path in python_files:
            log(f"🔄 Updating {file_path}...")
            
            source_file = os.path.join(temp_dir, file_path)
            target_file = file_path
            
            if update_file_from_source(source_file, target_file):
                updated_count += 1
            else:
                failed_count += 1
        
        # Results
        log("=" * 50)
        log("📊 Update results:")
        log(f"✅ Successfully updated: {updated_count}")
        log(f"❌ Errors: {failed_count}")
        log(f"📁 Total files: {len(python_files)}")

        # Move backups into _backup/
        move_backups_to_backup_dir()
        
        if failed_count == 0:
            log("🎉 All files updated successfully!")
            return True
        else:
            log(f"⚠️ Updated with errors: {failed_count} files", "WARNING")
            return False
        
    except Exception as e:
        log(f"❌ Critical error: {e}", "ERROR")
        return False
    
    finally:
        # Remove temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                log(f"🗑️ Temporary directory removed: {temp_dir}")
            except Exception as e:
                log(f"⚠️ Failed to remove temporary directory: {e}", "WARNING")

def show_excluded_files():
    """Display excluded files and directories"""
    log("📋 Excluded files:")
    for file_path in EXCLUDED_FILES:
        log(f"  - {file_path}")
    
    log("📁 Excluded directories:")
    for dir_path in EXCLUDED_DIRS:
        log(f"  - {dir_path}/")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show-excluded":
        show_excluded_files()
    else:
        success = main()
        sys.exit(0 if success else 1)
