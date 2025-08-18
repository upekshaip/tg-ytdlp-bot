# Add signal processing for correct termination
import signal
import os
import sys
import shutil
import threading

from HELPERS.app_instance import get_app
from HELPERS.logger import logger

# Get app instance for decorators
app = get_app()

def close_firebase_connections():
    """Close Firebase connections to prevent file descriptor leaks"""
    try:
        from DATABASE.firebase_init import db
        if hasattr(db, 'close'):
            db.close()
            logger.info("Firebase connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing Firebase connections: {e}")

def signal_handler(sig, frame):
    """
    Handler for system signals to ensure graceful shutdown

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {sig}, shutting down gracefully...")

    # Close Firebase connections first
    close_firebase_connections()

    # Stop all active animations and threads
    active_threads = [t for t in threading.enumerate()
                     if t != threading.current_thread() and not t.daemon]

    if active_threads:
        logger.info(f"Waiting for {len(active_threads)} active threads to finish")
        for thread in active_threads:
            logger.info(f"Waiting for thread {thread.name} to finish...")
            thread.join(timeout=2)  # Wait with timeout to avoid hanging

    # Clean up temporary files
    try:
        cleanup_temp_files()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    # Finish the application
    logger.info("Shutting down Pyrogram client...")
    try:
        app.stop()
        logger.info("Pyrogram client stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping Pyrogram client: {e}")

    logger.info("Shutdown complete.")
    sys.exit(0)

def cleanup_temp_files():
    """Clean up temporary files across all user directories"""
    if not os.path.exists("users"):
        return

    logger.info("Cleaning up temporary files")
    for user_dir in os.listdir("users"):
        try:
            user_path = os.path.join("users", user_dir)
            if os.path.isdir(user_path):
                for filename in os.listdir(user_path):
                    if filename.endswith(('.part', '.ytdl', '.temp', '.tmp')):
                        try:
                            os.remove(os.path.join(user_path, filename))
                        except Exception as e:
                            logger.error(f"Failed to remove temp file {filename}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning user directory {user_dir}: {e}")

def cleanup_user_temp_files(user_id):
    """Clean up temporary files for a specific user"""
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        return
    
    logger.info(f"Cleaning up temporary files for user {user_id}")
    
    # Log all files before cleanup
    try:
        all_files = os.listdir(user_dir)
        logger.info(f"Files in {user_dir} before cleanup: {all_files}")
    except Exception as e:
        logger.error(f"Error listing files in {user_dir}: {e}")
        return
    
    try:
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            # Remove temporary files
            if (filename.endswith(('.part', '.ytdl', '.temp', '.tmp')) or  # Removed .srt - subtitles are handled separately
                filename.startswith('yt_thumb_') or  # YouTube thumbnails
                filename.endswith('.jpg') or  # Thumbnails
                filename == 'full_title.txt' or  # Full title file
                filename == 'full_description.txt'):  # Tags file
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed temp file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove temp file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning user directory {user_id}: {e}")

def cleanup_subtitle_files(user_id):
    """Clean up subtitle files for a specific user after embedding"""
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        return
    
    logger.info(f"Cleaning up subtitle files for user {user_id}")
    
    try:
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            # Remove subtitle files
            if filename.endswith(('.srt', '.vtt', '.ass', '.ssa')):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed subtitle file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove subtitle file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning subtitle files for user {user_id}: {e}")

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
        if free < required_bytes:
            logger.warning(
                f"Not enough disk space. Required: {humanbytes(required_bytes)}, Available: {humanbytes(free)}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        # If we can't check, assume there's enough space
        return True

def create_directory(path):
    # Create The Directory (And All Intermediate Directories) IF Its Not Exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# Remove All User Media Files

def remove_media(message, only=None):
    dir = f'./users/{str(message.chat.id)}'
    if not os.path.exists(dir):
        logger.warning(f"Directory {dir} does not exist, nothing to remove")
        return
    if only:
        for fname in only:
            file_path = os.path.join(dir, fname)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file_path}: {e}")
        return
    allfiles = os.listdir(dir)
    file_extensions = [
        '.mp4', '.mkv', '.mp3', '.m4a', '.jpg', '.jpeg', '.part', '.ytdl',
        '.txt', '.ts', '.m3u8', '.webm', '.wmv', '.avi', '.mpeg', '.wav'
    ]
    for extension in file_extensions:
        if isinstance(extension, tuple):
            files = [fname for fname in allfiles if any(fname.endswith(ext) for ext in extension)]
        else:
            files = [fname for fname in allfiles if fname.endswith(extension)]
        for file in files:
            if extension == '.txt' and file in ['logs.txt', 'tags.txt']:
                continue
            file_path = os.path.join(dir, file)
            try:
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove file {file_path}: {e}")
    logger.info(f"Media cleanup completed for user {message.chat.id}")

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
       if max_name_length > 3:
          name = name[:max_name_length-3] + "..."
       else:
          name = name[:max_name_length]
       full_name = name + ext
    
    return full_name
