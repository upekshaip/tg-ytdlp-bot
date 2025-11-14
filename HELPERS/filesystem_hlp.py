# Add signal processing for correct termination
import signal
import os
import sys
import shutil
import threading

from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.limitter import humanbytes
from CONFIG.config import Config
from CONFIG.logger_msg import LoggerMsg
from pyrogram import enums

# Get app instance for decorators
app = get_app()

def close_firebase_connections():
    """Close Firebase connections to prevent file descriptor leaks"""
    try:
        from DATABASE.firebase_init import db
        if hasattr(db, 'close'):
            db.close()
            logger.info(LoggerMsg.FILESYSTEM_FIREBASE_CLOSED_LOG_MSG)
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_FIREBASE_CLOSE_ERROR_LOG_MSG.format(error=e))

def signal_handler(sig, frame):
    """
    Handler for system signals to ensure graceful shutdown

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(LoggerMsg.FILESYSTEM_SIGNAL_RECEIVED_LOG_MSG.format(signal=sig))

    # Close Firebase connections first
    close_firebase_connections()

    # Stop all active animations and threads
    active_threads = [t for t in threading.enumerate()
                     if t != threading.current_thread() and not t.daemon]

    if active_threads:
        logger.info(LoggerMsg.FILESYSTEM_WAITING_THREADS_LOG_MSG.format(count=len(active_threads)))
        for thread in active_threads:
            logger.info(LoggerMsg.FILESYSTEM_WAITING_THREAD_LOG_MSG.format(name=thread.name))
            thread.join(timeout=2)  # Wait with timeout to avoid hanging

    # Clean up temporary files
    try:
        cleanup_temp_files()
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_CLEANUP_ERROR_LOG_MSG.format(error=e))

    # Finish the application
    logger.info(LoggerMsg.FILESYSTEM_SHUTTING_DOWN_PYROGRAM_LOG_MSG)
    try:
        app.stop()
        logger.info(LoggerMsg.FILESYSTEM_PYROGRAM_STOPPED_LOG_MSG)
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_PYROGRAM_STOP_ERROR_LOG_MSG.format(error=e))

    # Close logger handlers
    try:
        from HELPERS.logger import close_logger
        close_logger()
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_LOGGER_CLOSE_ERROR_LOG_MSG.format(error=e))

    logger.info(LoggerMsg.FILESYSTEM_SHUTDOWN_COMPLETE_LOG_MSG)
    sys.exit(0)

def cleanup_temp_files():
    """Clean up temporary files across all user directories"""
    if not os.path.exists("users"):
        return

    logger.info(LoggerMsg.FILESYSTEM_CLEANING_TEMP_FILES_LOG_MSG)
    for user_dir in os.listdir("users"):
        try:
            user_path = os.path.join("users", user_dir)
            if os.path.isdir(user_path):
                for filename in os.listdir(user_path):
                    if filename.endswith(('.part', '.ytdl', '.temp', '.tmp', '.json', '.jsonl', '.srt', '.vtt', '.ass', '.ssa')):
                        try:
                            os.remove(os.path.join(user_path, filename))
                        except Exception as e:
                            logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_TEMP_FILE_LOG_MSG.format(filename=filename, error=e))
        except Exception as e:
            logger.error(LoggerMsg.FILESYSTEM_ERROR_CLEANING_USER_DIR_LOG_MSG.format(user_dir=user_dir, error=e))

def cleanup_user_temp_files(user_id):
    """Clean up temporary files and media files in download folders for a specific user"""
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        return
    
    logger.info(LoggerMsg.FILESYSTEM_CLEANING_USER_TEMP_FILES_LOG_MSG.format(user_id=user_id))
    
    # Log all files before cleanup
    try:
        all_files = os.listdir(user_dir)
        logger.info(LoggerMsg.FILESYSTEM_FILES_BEFORE_CLEANUP_LOG_MSG.format(user_dir=user_dir, files=all_files))
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_ERROR_LISTING_FILES_LOG_MSG.format(user_dir=user_dir, error=e))
        return
    
    try:
        # Clean files in root directory
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            
            # Skip subdirectories (download folders are handled separately)
            if os.path.isdir(file_path):
                continue
                
            # Remove temporary files and media files
            if (filename.endswith(('.part', '.ytdl', '.temp', '.tmp', '.json', '.jsonl', '.srt', '.vtt', '.ass', '.ssa', '.mp3', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4a', '.aac', '.ogg', '.wav')) or  # Media files
                filename.startswith('yt_thumb_') or  # YouTube thumbnails
                filename.endswith('.jpg') or  # Thumbnails
                filename == 'full_title.txt' or  # Full title file
                filename == 'full_description.txt'):  # Tags file
                # Skip formats_cache files - they should be preserved
                if filename.startswith('formats_cache_') and filename.endswith('.json'):
                    continue
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(LoggerMsg.FILESYSTEM_REMOVED_TEMP_FILE_LOG_MSG.format(filename=filename))
                except Exception as e:
                    logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_TEMP_FILE_LOG_MSG.format(filename=filename, error=e))
        
        # Clean media files in download folders (but keep txt, json, jpg, jpeg, png files)
        download_folders = ["downloads", "cyberdrop.me"]
        for folder_name in download_folders:
            folder_path = os.path.join(user_dir, folder_name)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                cleanup_media_in_download_folder(folder_path)
                
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_ERROR_CLEANING_USER_DIR_LOG_MSG.format(user_dir=user_id, error=e))

def cleanup_media_in_download_folder(folder_path):
    """Clean up media files in download folder, keeping txt, json, jpg, jpeg, png files"""
    try:
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Keep txt, json, jpg, jpeg, png files
                if filename.endswith(('.txt', '.json', '.jpg', '.jpeg', '.png')):
                    continue
                
                # Always keep formats_cache files
                if filename.startswith('formats_cache_') and filename.endswith('.json'):
                    continue
                
                # Remove media files
                if filename.endswith(('.mp3', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4a', '.aac', '.ogg', '.wav', '.part', '.ytdl', '.temp', '.tmp')):
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed media file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove media file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning media in download folder {folder_path}: {e}")

def cleanup_subtitle_files(user_id):
    """Clean up subtitle files for a specific user after embedding (only in root directory, not in protected subdirectories)"""
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        return
    
    logger.info(LoggerMsg.FILESYSTEM_CLEANING_SUBTITLE_FILES_LOG_MSG.format(user_id=user_id))
    
    try:
        # Only clean files in root directory, not in subdirectories (which might be protected)
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            # Skip subdirectories (they might be protected download folders)
            if os.path.isdir(file_path):
                continue
                
            # Remove subtitle files
            if filename.endswith(('.srt', '.vtt', '.ass', '.ssa', '.json', '.jsonl')):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(LoggerMsg.FILESYSTEM_REMOVED_SUBTITLE_FILE_LOG_MSG.format(filename=filename))
                except Exception as e:
                    logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_SUBTITLE_FILE_LOG_MSG.format(filename=filename, error=e))
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_ERROR_CLEANING_SUBTITLE_FILES_LOG_MSG.format(user_id=user_id, error=e))

# Register handlers for the most common termination signals
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Helper function to check available disk space
def check_disk_space(path, required_bytes):
    """
    Checks if there's enough disk space available at the specified path.

    Args:
        path (str): Path to check
        required_bytes (int): Required bytes of free space

    Returns:
        bool: True if enough space is available, False otherwise
    """
    try:
        total, used, free = shutil.disk_usage(path)
        if free and free < required_bytes:
            logger.warning(
                f"Not enough disk space. Required: {humanbytes(required_bytes)}, Available: {humanbytes(free)}")
            return False
        return True
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_ERROR_CHECKING_DISK_SPACE_LOG_MSG.format(error=e))
        # If we can't check, assume there's enough space
        return True

def create_directory(path):
    # Create The Directory (And All Intermediate Directories) IF Its Not Exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# Remove All User Media Files

def remove_media(message, only=None, force_clean=False):
    """
    Remove media files from user directory.
    
    Args:
        message: Telegram message object
        only: List of specific files to remove (if None, removes all media files)
        force_clean: If True, ignores protection files and cleans everything (for /clean command)
    """
    dir = f'./users/{str(message.chat.id)}'
    if not os.path.exists(dir):
        logger.warning(LoggerMsg.FILESYSTEM_DIRECTORY_NOT_EXISTS_LOG_MSG.format(directory=dir))
        return
    
    if only:
        for fname in only:
            file_path = os.path.join(dir, fname)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(LoggerMsg.FILESYSTEM_REMOVED_FILE_LOG_MSG.format(file_path=file_path))
                except Exception as e:
                    logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=file_path, error=e))
        return
    
    # Check if parallel downloads are allowed and we're not forcing cleanup
    if not force_clean and is_parallel_download_allowed(message):
        # For parallel downloads, only clean files in root directory, skip protected subdirectories
        allfiles = os.listdir(dir)
        file_extensions = [
            '.mp4', '.mkv', '.mp3', '.m4a', '.jpg', '.jpeg', '.part', '.ytdl',
            '.txt', '.ts', '.m3u8', '.webm', '.wmv', '.avi', '.mpeg', '.wav',
            '.json', '.jsonl', '.srt', '.vtt', '.ass', '.ssa',
        ]
        
        # Clean files in root directory
        for extension in file_extensions:
            if isinstance(extension, tuple):
                files = [fname for fname in allfiles if any(fname.endswith(ext) for ext in extension)]
            else:
                files = [fname for fname in allfiles if fname.endswith(extension)]
            for file in files:
                if extension == '.txt' and file in ['logs.txt', 'tags.txt', 'keyboard.txt', 'lang.txt']:
                    continue
                file_path = os.path.join(dir, file)
                try:
                    os.remove(file_path)
                    logger.info(LoggerMsg.FILESYSTEM_REMOVED_FILE_LOG_MSG.format(file_path=file_path))
                except Exception as e:
                    logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=file_path, error=e))
        
        # Clean unprotected subdirectories
        for item in os.listdir(dir):
            item_path = os.path.join(dir, item)
            if os.path.isdir(item_path):
                if not is_directory_protected(item_path):
                    try:
                        shutil.rmtree(item_path)
                        logger.info(LoggerMsg.FILESYSTEM_REMOVED_UNPROTECTED_DIR_LOG_MSG.format(item_path=item_path))
                    except Exception as e:
                        logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_DIRECTORY_LOG_MSG.format(item_path=item_path, error=e))
                else:
                    logger.info(LoggerMsg.FILESYSTEM_SKIPPED_PROTECTED_DIR_LOG_MSG.format(item_path=item_path))
    else:
        # For non-parallel downloads or force cleanup, clean everything
        allfiles = os.listdir(dir)
        file_extensions = [
            '.mp4', '.mkv', '.mp3', '.m4a', '.jpg', '.jpeg', '.part', '.ytdl',
            '.txt', '.ts', '.m3u8', '.webm', '.wmv', '.avi', '.mpeg', '.wav',
            '.json', '.jsonl', '.srt', '.vtt', '.ass', '.ssa',
        ]
        for extension in file_extensions:
            if isinstance(extension, tuple):
                files = [fname for fname in allfiles if any(fname.endswith(ext) for ext in extension)]
            else:
                files = [fname for fname in allfiles if fname.endswith(extension)]
            for file in files:
                if extension == '.txt' and file in ['logs.txt', 'tags.txt', 'keyboard.txt', 'lang.txt']:
                    continue
                file_path = os.path.join(dir, file)
                try:
                    os.remove(file_path)
                    logger.info(LoggerMsg.FILESYSTEM_REMOVED_FILE_LOG_MSG.format(file_path=file_path))
                except Exception as e:
                    logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=file_path, error=e))
    
    logger.info(LoggerMsg.FILESYSTEM_MEDIA_CLEANUP_COMPLETED_LOG_MSG.format(user_id=message.chat.id))

# Helper function to sanitize and shorten filenames
def sanitize_filename(filename, max_length=150):
    """
    Sanitize filename by removing invalid characters and shortening if needed
    Only allows letters (any language), numbers, and Linux-safe symbols

    Args:
        filename (str): Original filename
        max_length (int): Maximum allowed length for filename (excluding extension)

    Returns:
        str: Sanitized and shortened filename
    """
    # Exit early if None
    if filename is None:
        return "untitled"

    # Extract extension first
    name, ext = os.path.splitext(filename)

    # Remove all emoji and special Unicode characters
    # Keep only letters (any language), numbers, spaces, dots, dashes, underscores
    import unicodedata
    
    # Normalize Unicode characters
    name = unicodedata.normalize('NFKC', name)
    
    # Remove all emoji and special symbols, keep only:
    # - Letters (any language): \p{L}
    # - Numbers: \p{N}
    # - Spaces: \s
    # - Safe symbols: .-_()
    import re
    
    # Pattern to keep only safe characters
    # Remove all non-alphanumeric characters except safe symbols
    # \w includes [a-zA-Z0-9_] but we want to keep all Unicode letters
    import unicodedata
    
    # Keep only letters, numbers, spaces, and safe symbols
    cleaned_name = ''
    for char in name:
        if (char.isalnum() or  # letters and numbers
            char.isspace() or  # spaces
            char in '.-_()'):  # safe symbols
            cleaned_name += char
    
    name = cleaned_name
    
    # Remove invalid filesystem characters (Windows and Linux safe)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name = re.sub(invalid_chars, '', name)
    
    # Remove leading/trailing dots and spaces (not allowed in Linux)
    name = name.strip(' .')
    
    # Replace multiple spaces/dots with single ones
    name = re.sub(r'[\s.]+', ' ', name).strip()
    
    # If name is empty after cleaning, use default
    if not name:
        name = "untitled"
    
    # Shorten if too long
    full_name = name + ext
    max_total = 100
    if len(full_name) > max_total:
       max_name_length = max_total - len(ext)
       if max_name_length and max_name_length > 3:
          name = name[:max_name_length-3] + "..."
       else:
          name = name[:max_name_length]
       full_name = name + ext
    
    return full_name

def sanitize_filename_strict(filename, max_length=150):
    """
    Strict sanitization for filenames - removes all characters except letters and numbers,
    replaces spaces with underscores. Used specifically for yt-dlp file downloads.
    
    Args:
        filename (str): Original filename
        max_length (int): Maximum allowed length for filename (excluding extension)
    
    Returns:
        str: Strictly sanitized filename with only letters, numbers, and underscores
    """
    # Exit early if None
    if filename is None:
        return "untitled"
    
    # Extract extension first
    name, ext = os.path.splitext(filename)
    
    # Normalize Unicode characters
    import unicodedata
    name = unicodedata.normalize('NFKC', name)
    
    # Keep only letters, numbers, and safe ASCII characters, replace everything else with underscores
    import re
    # Keep letters, numbers, underscores, hyphens, dots, parentheses
    # Replace all other characters (including spaces) with underscores
    name = re.sub(r'[^\w\-\.\(\)]', '_', name)
    
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # If name is empty after cleaning, use default
    if not name:
        name = "untitled"
    
    # Shorten if too long
    full_name = name + ext
    max_total = max_length
    if len(full_name) > max_total:
        max_name_length = max_total - len(ext)
        if max_name_length and max_name_length > 3:
            name = name[:max_name_length-3] + "..."
        else:
            name = name[:max_name_length]
        full_name = name + ext
    
    return full_name

def is_parallel_download_allowed(message):
    """
    Check if parallel downloads are allowed for this user/chat.
    Allowed for:
    1. Groups (chat_id < 0)
    2. Admin users in private chats (chat_id > 0)
    """
    try:
        # Groups always allow parallel downloads
        if message.chat.id < 0:
            return True
        
        # For private chats, only admins can have parallel downloads
        if message.chat.id > 0:
            return int(message.chat.id) in Config.ADMIN
        
        return False
    except Exception as e:
        logger.warning(LoggerMsg.FILESYSTEM_ERROR_CHECKING_PARALLEL_PERMISSION_LOG_MSG.format(error=e))
        return False

def create_protection_file(directory_path):
    """
    Create do_not_delete_me file in the specified directory to protect it from cleanup.
    """
    try:
        protection_file = os.path.join(directory_path, "do_not_delete_me")
        with open(protection_file, 'w') as f:
            f.write(f"Protected directory created at: {os.path.basename(directory_path)}\n")
            f.write("This directory is currently being used for download.\n")
            f.write("Do not delete this directory until download is complete.\n")
        logger.info(LoggerMsg.FILESYSTEM_CREATED_PROTECTION_FILE_LOG_MSG.format(protection_file=protection_file))
        return True
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_FAILED_CREATE_PROTECTION_FILE_LOG_MSG.format(directory_path=directory_path, error=e))
        return False

def remove_protection_file(directory_path):
    """
    Remove do_not_delete_me file from the specified directory.
    """
    try:
        protection_file = os.path.join(directory_path, "do_not_delete_me")
        if os.path.exists(protection_file):
            os.remove(protection_file)
            logger.info(LoggerMsg.FILESYSTEM_REMOVED_PROTECTION_FILE_LOG_MSG.format(protection_file=protection_file))
            return True
        return False
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_FAILED_REMOVE_PROTECTION_FILE_LOG_MSG.format(directory_path=directory_path, error=e))
        return False

def is_directory_protected(directory_path):
    """
    Check if directory is protected by do_not_delete_me file.
    """
    try:
        protection_file = os.path.join(directory_path, "do_not_delete_me")
        return os.path.exists(protection_file)
    except Exception as e:
        logger.error(LoggerMsg.FILESYSTEM_ERROR_CHECKING_PROTECTION_FILE_LOG_MSG.format(directory_path=directory_path, error=e))
        return False
