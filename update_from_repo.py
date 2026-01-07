#!/usr/bin/env python3
# Version 1.0.1
"""
Script to automatically update code from a GitHub repository.
Clones the repository into a temporary folder and replaces required files.
"""

import os
import sys
import shutil
import tempfile
from CONFIG.messages import Messages, safe_get_messages
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
REPO_URL = "https://github.com/chelaxian/tg-ytdlp-bot.git"
# Use explicit branch
BRANCH = "newdesign2"
# BRANCH = "main"

# Files and directories that MUST NOT be updated
EXCLUDED_FILES = [
    "CONFIG/domains.py",  # Main configuration file (contains domains data)
    "CONFIG/config.py",  # Main configuration file (contains sensitive data)
    #"requirements.txt", # Dependencies may differ
    ".env",              # Environment variables
    ".bot_pid",          # Bot PID file
    "bot.log",           # Bot logs
    "runtime.log",       # Runtime logs
    "magic.session",     # Pyrogram session
    "magic.session-journal",  # Session journal
    "dump.json",         # Firebase dump
    "script.sh",         # Script for updating porn lists
    #"update_from_repo.py",  # Do not overwrite the updater itself
    #"update.sh",             # Do not overwrite the update shell script
]

EXCLUDED_DIRS = [
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

# Additional directories/files that must always be synced
INCLUDE_DIRS = [
    "web",  # Includes templates, static assets, and the FastAPI app itself
    "CONFIG/templates",  # In case templates/localizations are added
]

ALWAYS_INCLUDE_FILES = [
    "requirements.txt",
]

def log(message, level="INFO"):
    """Logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def _is_inside(path: str, directory: str) -> bool:
    """Helper: checks if path is the directory itself or inside it."""
    return path == directory or path.startswith(f"{directory}/")


def should_update_file(file_path, exclude_include_dirs=False):
    """Checks whether the file should be updated
    
    Args:
        file_path: Path to the file to check
        exclude_include_dirs: If True, exclude files from INCLUDE_DIRS 
                             (they will be synced separately via sync_include_directories)
    """
    # Check excluded files
    for excluded in EXCLUDED_FILES:
        if file_path == excluded:
            return False
    
    # Check excluded directories
    for excluded_dir in EXCLUDED_DIRS:
        if _is_inside(file_path, excluded_dir):
            return False
    
    # If exclude_include_dirs is True, skip files from INCLUDE_DIRS
    # (they will be synced via sync_include_directories)
    if exclude_include_dirs:
        for include_dir in INCLUDE_DIRS:
            if _is_inside(file_path, include_dir):
                return False
    
    # Ensure explicitly listed files are synced
    if file_path in ALWAYS_INCLUDE_FILES:
        return True
    
    # Ensure specific directories (e.g. web UI) are synced entirely
    # (only if not excluding them)
    if not exclude_include_dirs:
        for include_dir in INCLUDE_DIRS:
            if _is_inside(file_path, include_dir):
                return True
    
    # Update Python files
    if file_path.endswith('.py'):
        return True
    
    # Update files from LANGUAGES directory (all file types)
    if file_path.startswith('CONFIG/LANGUAGES/'):
        return True
    
    return False

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
    messages = safe_get_messages(None)
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
            messages = safe_get_messages()
            log(messages.UPDATE_REPOSITORY_CLONED_SUCCESS_MSG)
            return True
        else:
            messages = safe_get_messages()
            log(messages.UPDATE_CLONE_ERROR_MSG.format(error=result.stderr), "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        messages = safe_get_messages()
        log(messages.UPDATE_CLONE_TIMEOUT_MSG, "ERROR")
        return False
    except Exception as e:
        messages = safe_get_messages()
        log(messages.UPDATE_CLONE_EXCEPTION_MSG.format(error=e), "ERROR")
        return False

def find_python_files(source_dir, exclude_include_dirs=False):
    """Find all Python files and LANGUAGES files in the source directory
    
    Args:
        source_dir: Source directory to search
        exclude_include_dirs: If True, exclude files from INCLUDE_DIRS 
                             (they will be synced separately via sync_include_directories)
    """
    files_to_update = []
    
    for root, dirs, files in os.walk(source_dir):
        # Exclude unnecessary directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv']]
        
        # Also exclude INCLUDE_DIRS from walking if we're excluding them
        if exclude_include_dirs:
            for include_dir in INCLUDE_DIRS:
                if include_dir in dirs:
                    dirs.remove(include_dir)
        
        for file in files:
            # Build relative path
            rel_path = os.path.relpath(os.path.join(root, file), source_dir)
            if should_update_file(rel_path, exclude_include_dirs=exclude_include_dirs):
                files_to_update.append(rel_path)
    
    return sorted(files_to_update)


def sync_include_directories(source_root: str) -> None:
    """Fully sync directories from INCLUDE_DIRS (hard copy)."""
    for include_dir in INCLUDE_DIRS:
        source_path = os.path.join(source_root, include_dir)
        if not os.path.exists(source_path):
            log(f"⚠️ Include directory missing in repo: {include_dir}", "WARNING")
            continue
        
        target_path = Path(include_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Count files before removal
        file_count = 0
        if target_path.exists():
            for root, dirs, files in os.walk(target_path):
                file_count += len(files)
            log(f"🧹 Removing existing directory: {include_dir} ({file_count} files)")
            shutil.rmtree(target_path)
        
        # Count files to copy
        files_to_copy = []
        for root, dirs, files in os.walk(source_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), source_path)
                files_to_copy.append(rel_path)
        
        log(f"📦 Syncing directory: {include_dir} ({len(files_to_copy)} files)")
        shutil.copytree(source_path, target_path)
        log(f"✅ Successfully synced {include_dir}: {len(files_to_copy)} files updated")

def update_file_from_source(source_file, target_file):
    """Update a file from the source repository"""
    try:
        # Create directories if missing (only if file is not in the project root)
        dir_name = os.path.dirname(target_file)
        if dir_name:  # Directory path is not empty
            os.makedirs(dir_name, exist_ok=True)
            log(f"📁 Created directory: {dir_name}")
        
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
    messages = safe_get_messages(None)
    """Move all *.backup* files into _backup directory, keeping relative paths."""
    try:
        log("📦 Moving backups to _backup/...")
        cmd = "mkdir -p _backup && find . -path './_backup' -prune -o -type f -name \"*.backup*\" -print0 | sed -z 's#^\\./##' | rsync -a --relative --from0 --files-from=- --remove-source-files ./ _backup/"
        subprocess.run(["bash", "-lc", cmd], check=True)
        messages = safe_get_messages()
        log(messages.UPDATE_BACKUPS_MOVED_MSG)
    except Exception as e:
        log(f"⚠️ Failed to move backups: {e}", "WARNING")

def main():
    messages = safe_get_messages(None)
    """Main update routine"""
    log("🚀 Starting update from GitHub repository")
    log(f"Repository: {REPO_URL}")
    log(f"Branch: {BRANCH}")
    
    # Ensure we are in the correct directory
    if not os.path.exists("magic.py"):
        log("❌ File magic.py not found. Make sure you run this in the bot folder.", "ERROR")
        return False
    
    # Ensure LANGUAGES directory exists
    languages_dir = "CONFIG/LANGUAGES"
    if not os.path.exists(languages_dir):
        try:
            os.makedirs(languages_dir, exist_ok=True)
            log(f"📁 Created LANGUAGES directory: {languages_dir}")
        except Exception as e:
            log(f"⚠️ Failed to create LANGUAGES directory: {e}", "WARNING")
    
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
        
        # Find files to update (exclude INCLUDE_DIRS - they will be synced separately)
        files_to_update = find_python_files(temp_dir, exclude_include_dirs=True)
        
        if not files_to_update:
            log("❌ No files found to update", "ERROR")
            return False
        
        log(f"📋 Found {len(files_to_update)} files to update")
        
        # Show file list to update
        log("📝 Files to update:")
        for file_path in files_to_update:
            log(f"  - {file_path}")
        
        # Ask for confirmation
        response = input("\n🤔 Proceed with update? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            messages = safe_get_messages()
            log(messages.UPDATE_CANCELED_BY_USER_MSG)
            return False
        
        # Update files
        updated_count = 0
        failed_count = 0
        
        for file_path in files_to_update:
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
        log(f"📁 Total files: {len(files_to_update)}")

        # Force-sync required directories (e.g., web/)
        log("=" * 50)
        log("📦 Syncing include directories (web/, etc.)...")
        sync_include_directories(temp_dir)

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
