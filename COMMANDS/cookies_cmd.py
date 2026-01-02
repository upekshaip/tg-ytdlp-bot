
# Command to Set Browser Cookies and Auto-Update YouTube Cookies
from pyrogram import filters, enums
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app

from HELPERS.decorators import reply_with_keyboard, background_handler
from HELPERS.limitter import is_user_in_channel
from HELPERS.logger import send_to_logger, logger, send_to_user, send_to_all
from HELPERS.filesystem_hlp import create_directory
from HELPERS.safe_messeger import fake_message, safe_send_message, safe_edit_message_text
from pyrogram.errors import FloodWait
import subprocess
import os
import requests
import re
import time
from requests import Session
from requests.adapters import HTTPAdapter
import yt_dlp
import random
from HELPERS.pot_helper import add_pot_to_ytdl_opts
from COMMANDS.proxy_cmd import add_proxy_to_ytdl_opts
from URL_PARSERS.youtube import is_youtube_url

# Get app instance for decorators
app = get_app()

# Cache for YouTube cookie validation results
# Format: {user_id: {'result': bool, 'timestamp': float, 'cookie_path': str, 'task_id': str, 'active': bool}}
_youtube_cookie_cache = {}

# Global cache for tracking checked cookie sources per user to prevent infinite loops
# Format: {user_id: {'checked_sources': set, 'last_reset': float}}
_checked_cookie_sources = {}

# Cache for non-YouTube cookie validation results
# Format: {cache_key: {'result': bool, 'timestamp': float, 'cookie_path': str, 'task_id': str, 'active': bool}}
_non_youtube_cookie_cache = {}

# Active task tracking for cookie validation
# Format: {task_id: {'user_id': int, 'start_time': float, 'url': str, 'service': str}}
_active_cookie_tasks = {}

# Round-robin pointer for YouTube cookie sources
_yt_round_robin_index = 0

# YouTube cookie retry tracking per user
# Format: {user_id: {'attempts': [timestamp1, timestamp2, ...], 'last_reset': timestamp}}
_youtube_cookie_retry_tracking = {}

def generate_task_id(user_id: int, url: str, service: str = None) -> str:
    """
    Generate a unique task ID for tracking state.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        service (str, optional): Service name
        
    Returns:
        str: Unique task ID
    """
    import hashlib
    task_data = f"{user_id}_{url}_{service}_{time.time()}"
    return hashlib.md5(task_data.encode()).hexdigest()[:16]

def start_cookie_task(user_id: int, url: str, service: str = None) -> str:
    """
    Start tracking a cookie validation task.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        service (str, optional): Service name
        
    Returns:
        str: Task ID
    """
    global _active_cookie_tasks
    
    task_id = generate_task_id(user_id, url, service)
    _active_cookie_tasks[task_id] = {
        'user_id': user_id,
        'start_time': time.time(),
        'url': url,
        'service': service
    }
    
    logger.info(f"Started cookie task {task_id} for user {user_id}, URL: {url}")
    return task_id

def finish_cookie_task(task_id: str, success: bool, cookie_path: str = None):
    """
    Finish a cookie validation task and update cache.
    
    Args:
        task_id (str): Task ID
        success (bool): Validation success
        cookie_path (str, optional): Cookie file path
    """
    global _active_cookie_tasks, _youtube_cookie_cache, _non_youtube_cookie_cache
    
    if task_id not in _active_cookie_tasks:
        logger.warning(f"Task {task_id} not found in active tasks")
        return
    
    task_info = _active_cookie_tasks[task_id]
    user_id = task_info['user_id']
    url = task_info['url']
    service = task_info['service']
    
    # Update cache depending on service type
    if service == 'youtube' or (service is None and is_youtube_url(url)):
        _youtube_cookie_cache[user_id] = {
            'result': success,
            'timestamp': time.time(),
            'cookie_path': cookie_path,
            'task_id': task_id,
            'active': False
        }
    else:
        cache_key = get_cookie_cache_key(user_id, url, service)
        _non_youtube_cookie_cache[cache_key] = {
            'result': success,
            'timestamp': time.time(),
            'cookie_path': cookie_path,
            'task_id': task_id,
            'active': False
        }
    
    # Remove task from active set
    del _active_cookie_tasks[task_id]
    
    logger.info(f"Finished cookie task {task_id} for user {user_id}, success: {success}")

def is_cookie_task_active(user_id: int, url: str, service: str = None) -> bool:
    """
    Check whether a cookie validation task is active for the user.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        service (str, optional): Service name
        
    Returns:
        bool: True if task is active
    """
    global _active_cookie_tasks
    
    for task_id, task_info in _active_cookie_tasks.items():
        if (task_info['user_id'] == user_id and 
            task_info['url'] == url and 
            task_info['service'] == service):
            return True
    return False

def cleanup_expired_tasks():
    """
    Clean up expired tasks and force-deactivate stale cache entries.
    """
    global _active_cookie_tasks, _youtube_cookie_cache, _non_youtube_cookie_cache
    
    from CONFIG.limits import LimitsConfig
    current_time = time.time()
    max_lifetime = LimitsConfig.COOKIE_CACHE_MAX_LIFETIME
    
    # Clean up expired active tasks
    expired_tasks = []
    for task_id, task_info in _active_cookie_tasks.items():
        if current_time - task_info['start_time'] > max_lifetime:
            expired_tasks.append(task_id)
    
    for task_id in expired_tasks:
        logger.warning(f"Forcefully deactivating expired cookie task {task_id}")
        del _active_cookie_tasks[task_id]
    
    # Clean up expired cache entries
    expired_youtube_cache = []
    for user_id, cache_entry in _youtube_cookie_cache.items():
        if current_time - cache_entry['timestamp'] > max_lifetime:
            expired_youtube_cache.append(user_id)
    
    for user_id in expired_youtube_cache:
        logger.warning(f"Forcefully deactivating expired YouTube cookie cache for user {user_id}")
        del _youtube_cookie_cache[user_id]
    
    expired_non_youtube_cache = []
    for cache_key, cache_entry in _non_youtube_cookie_cache.items():
        if current_time - cache_entry['timestamp'] > max_lifetime:
            expired_non_youtube_cache.append(cache_key)
    
    for cache_key in expired_non_youtube_cache:
        logger.warning(f"Forcefully deactivating expired non-YouTube cookie cache {cache_key}")
        del _non_youtube_cookie_cache[cache_key]
    
    # Clean up expired checked-source tracking (older than 1 hour)
    global _checked_cookie_sources
    expired_checked_users = []
    for user_id, checked_data in _checked_cookie_sources.items():
        if current_time - checked_data.get('last_reset', 0) > 3600:  # 1 hour
            expired_checked_users.append(user_id)
    
    for user_id in expired_checked_users:
        del _checked_cookie_sources[user_id]
        logger.info(f"Cleared expired checked cookie sources for user {user_id}")

def get_checked_cookie_sources(user_id: int) -> set:
    """Get the set of already-checked cookie sources for the user."""
    global _checked_cookie_sources
    if user_id not in _checked_cookie_sources:
        _checked_cookie_sources[user_id] = {'checked_sources': set(), 'last_reset': time.time()}
    return _checked_cookie_sources[user_id]['checked_sources']

def mark_cookie_source_checked(user_id: int, source_index: int):
    """Mark a cookie source as checked for the user."""
    global _checked_cookie_sources
    if user_id not in _checked_cookie_sources:
        _checked_cookie_sources[user_id] = {'checked_sources': set(), 'last_reset': time.time()}
    _checked_cookie_sources[user_id]['checked_sources'].add(source_index)

def reset_checked_cookie_sources(user_id: int):
    """Reset checked cookie sources for the user."""
    global _checked_cookie_sources
    if user_id in _checked_cookie_sources:
        _checked_cookie_sources[user_id] = {'checked_sources': set(), 'last_reset': time.time()}
        logger.info(f"Reset checked cookie sources for user {user_id}")

def reset_all_checked_cookie_sources():
    """Reset checked cookie sources for all users."""
    global _checked_cookie_sources
    _checked_cookie_sources.clear()
    logger.info("Reset checked cookie sources for all users")

def check_youtube_cookie_retry_limit(user_id: int) -> bool:
    """
    Check whether the user has exceeded the YouTube cookie retry limit.
    
    Args:
        user_id (int): User ID
        
    Returns:
        bool: True if under the limit, False if exceeded
    """
    global _youtube_cookie_retry_tracking
    
    from CONFIG.limits import LimitsConfig
    
    current_time = time.time()
    
    # Clean old entries
    if user_id in _youtube_cookie_retry_tracking:
        user_data = _youtube_cookie_retry_tracking[user_id]
        # Drop attempts outside the configured time window
        user_data['attempts'] = [
            attempt_time for attempt_time in user_data['attempts']
            if current_time - attempt_time < LimitsConfig.YOUTUBE_COOKIE_RETRY_WINDOW
        ]
        
        # If no attempts remain, remove the user entry
        if not user_data['attempts']:
            del _youtube_cookie_retry_tracking[user_id]
            return True
    
    # Check limit
    if user_id in _youtube_cookie_retry_tracking:
        attempts_count = len(_youtube_cookie_retry_tracking[user_id]['attempts'])
        if attempts_count >= LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR:
            logger.warning(f"YouTube cookie retry limit exceeded for user {user_id}: {attempts_count}/{LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR}")
            return False
    
    return True

def record_youtube_cookie_retry_attempt(user_id: int):
    """
    Record a YouTube cookie retry attempt for the user.
    
    Args:
        user_id (int): User ID
    """
    global _youtube_cookie_retry_tracking
    
    current_time = time.time()
    
    if user_id not in _youtube_cookie_retry_tracking:
        _youtube_cookie_retry_tracking[user_id] = {
            'attempts': [],
            'last_reset': current_time
        }
    
    _youtube_cookie_retry_tracking[user_id]['attempts'].append(current_time)
    logger.info(f"Recorded YouTube cookie retry attempt for user {user_id}")

def get_youtube_cookie_retry_status(user_id: int) -> dict:
    """
    Return the YouTube cookie retry status for the user.
    
    Args:
        user_id (int): User ID
        
    Returns:
        dict: Attempt status
    """
    global _youtube_cookie_retry_tracking
    
    from CONFIG.limits import LimitsConfig
    
    current_time = time.time()
    
    if user_id in _youtube_cookie_retry_tracking:
        user_data = _youtube_cookie_retry_tracking[user_id]
        # Drop old attempts
        user_data['attempts'] = [
            attempt_time for attempt_time in user_data['attempts']
            if current_time - attempt_time < LimitsConfig.YOUTUBE_COOKIE_RETRY_WINDOW
        ]
        
        attempts_count = len(user_data['attempts'])
        remaining_attempts = max(0, LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR - attempts_count)
        
        return {
            'user_id': user_id,
            'attempts_count': attempts_count,
            'limit': LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR,
            'remaining_attempts': remaining_attempts,
            'window_seconds': LimitsConfig.YOUTUBE_COOKIE_RETRY_WINDOW,
            'oldest_attempt': user_data['attempts'][0] if user_data['attempts'] else None,
            'can_retry': remaining_attempts > 0
        }
    else:
        return {
            'user_id': user_id,
            'attempts_count': 0,
            'limit': LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR,
            'remaining_attempts': LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR,
            'window_seconds': LimitsConfig.YOUTUBE_COOKIE_RETRY_WINDOW,
            'oldest_attempt': None,
            'can_retry': True
        }

def reset_youtube_cookie_retry_tracking(user_id: int = None):
    """
    Reset tracking of YouTube cookie-rotation attempts.
    
    Args:
        user_id (int, optional): User ID. If None, resets for all users.
    """
    global _youtube_cookie_retry_tracking
    
    if user_id is None:
        _youtube_cookie_retry_tracking.clear()
        logger.info("Reset YouTube cookie retry tracking for all users")
    else:
        if user_id in _youtube_cookie_retry_tracking:
            del _youtube_cookie_retry_tracking[user_id]
            logger.info(f"Reset YouTube cookie retry tracking for user {user_id}")
        else:
            logger.info(f"No YouTube cookie retry tracking found for user {user_id}")

def get_unchecked_cookie_sources(user_id: int, cookie_urls: list) -> list:
    """Return the list of unchecked cookie sources for the user."""
    checked_sources = get_checked_cookie_sources(user_id)
    unchecked_indices = []
    
    for i, url in enumerate(cookie_urls):
        if i not in checked_sources:
            unchecked_indices.append(i)
    
    return unchecked_indices

@app.on_message(filters.command("cookies_from_browser") & filters.private)
# @reply_with_keyboard
@background_handler(label="cookies_from_browser")
def cookies_from_browser(app, message):
    """
    Let the user choose a browser to extract cookies from.
    
    Behavior:
    - Detect installed browsers
    - Show a selection menu
    - Fall back to COOKIE_URL when no browsers are found
    
    Args:
        app: Application instance
        message: Command message
    """
    user_id = message.chat.id
    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    # Logging a request for cookies from browser
    send_to_logger(message, safe_get_messages(user_id).COOKIES_BROWSER_REQUESTED_LOG_MSG)

    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # Dictionary with Browsers and Their Paths
    browsers = {
        "brave": "~/.config/BraveSoftware/Brave-Browser/",
        "chrome": "~/.config/google-chrome/",
        "chromium": "~/.config/chromium/",
        "edge": "~/.config/microsoft-edge/",
        "firefox": "~/.mozilla/firefox/",
        "opera": "~/.config/opera/",
        "safari": "~/Library/Safari/",
        "vivaldi": "~/.config/vivaldi/",
        "whale": ["~/.config/Whale/", "~/.config/naver-whale/"]
    }

    # Create a list of only installed browsers
    installed_browsers = []
    for browser, path in browsers.items():
        if browser == "safari":
            exists = False
        elif isinstance(path, list):
            exists = any(os.path.exists(os.path.expanduser(p)) for p in path)
        else:
            exists = os.path.exists(os.path.expanduser(path))
        if exists:
            installed_browsers.append(browser)

    # Always show menu, even if no browsers found

    # Create buttons for installed browsers
    buttons = []
    for browser in installed_browsers:
        display_name = browser.capitalize()
        button = InlineKeyboardButton(safe_get_messages(user_id).COOKIES_BROWSER_BUTTON_MSG.format(browser_name=display_name), callback_data=f"browser_choice|{browser}")
        buttons.append([button])

    # Add a button to download from remote URL (always available)
    fallback_url = getattr(Config, "COOKIE_URL", None)
    if fallback_url:
        buttons.append([InlineKeyboardButton(safe_get_messages(user_id).DOWNLOAD_FROM_URL_BUTTON_MSG, callback_data="browser_choice|download_from_url")])

    # Add a button to open browser monitoring page
    miniapp_url = getattr(Config, 'MINIAPP_URL', None)
    # Use the URL as a regular link instead of WebApp
    if miniapp_url and miniapp_url.startswith('https://t.me/'):
        logger.info(safe_get_messages(user_id).COOKIES_ADDING_BROWSER_MONITORING_MSG.format(miniapp_url=miniapp_url))
        buttons.append([InlineKeyboardButton(safe_get_messages(user_id).BROWSER_OPEN_BUTTON_MSG, url=miniapp_url)])
    else:
        logger.warning(safe_get_messages(user_id).COOKIES_BROWSER_MONITORING_URL_NOT_CONFIGURED_MSG.format(miniapp_url=miniapp_url))

    # Add a close button
    buttons.append([InlineKeyboardButton(safe_get_messages(user_id).BTN_CLOSE, callback_data="browser_choice|close")])
    keyboard = InlineKeyboardMarkup(buttons)

    # Choose message based on whether browsers are found
    if installed_browsers:
        message_text = safe_get_messages(user_id).SELECT_BROWSER_MSG
    else:
        message_text = safe_get_messages(user_id).SELECT_BROWSER_NO_BROWSERS_MSG
    
    if miniapp_url and miniapp_url.startswith('https://t.me/'):
        message_text += f"\n\n{safe_get_messages(user_id).BROWSER_MONITOR_HINT_MSG}"

    safe_send_message(
        user_id,
        message_text,
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, safe_get_messages(user_id).COOKIES_BROWSER_SELECTION_SENT_LOG_MSG)

# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
# @reply_with_keyboard
def browser_choice_callback(app, callback_query):
    """
    Handle browser selection for cookie extraction.
    
    Behavior:
    - Extract cookies from the selected browser
    - Validate cookies
    - Save only working cookies
    
    Args:
        app: Application instance
        callback_query: Callback query with selected browser
    """
    user_id = callback_query.from_user.id
    logger.info(safe_get_messages(user_id).COOKIES_BROWSER_CALLBACK_MSG.format(callback_data=callback_query.data))
    data = callback_query.data.split("|")[1]  # E.G. "Chromium", "Firefox", or "Close"
    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).COOKIES_MENU_CLOSED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_BROWSER_SELECTION_CLOSED_LOG_MSG)
        return

    if data == "download_from_url":
        # Handle download from remote URL
        fallback_url = getattr(Config, "COOKIE_URL", None)
        if not fallback_url:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_NO_BROWSERS_NO_URL_MSG)
            callback_query.answer(safe_get_messages(user_id).COOKIES_NO_REMOTE_URL_MSG)
            return

        # Update message to show downloading
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_DOWNLOADING_FROM_URL_MSG)
        
        try:
            ok, status, content, err = _download_content(fallback_url, timeout=30, user_id=user_id)
            if ok:
                # basic validation
                if not fallback_url.lower().endswith('.txt'):
                    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_URL_NOT_TXT_MSG)
                    callback_query.answer(safe_get_messages(user_id).COOKIES_INVALID_FILE_FORMAT_MSG)
                    return
                if len(content or b"") > 100 * 1024:
                    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_TOO_LARGE_MSG)
                    callback_query.answer(safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_CALLBACK_MSG)
                    return
                with open(cookie_file, "wb") as f:
                    f.write(content)
                safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_YT_FALLBACK_SAVED_MSG)
                callback_query.answer(safe_get_messages(user_id).COOKIES_DOWNLOADED_SUCCESSFULLY_MSG)
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_SUCCESS_LOG_MSG)
            else:
                if status is not None:
                    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_UNAVAILABLE_MSG.format(status=status))
                    callback_query.answer(safe_get_messages(user_id).COOKIES_SERVER_ERROR_MSG.format(status=status))
                else:
                    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_ERROR_MSG)
                    callback_query.answer(safe_get_messages(user_id).COOKIES_DOWNLOAD_FAILED_MSG)
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_FAILED_LOG_MSG.format(status=status))
        except Exception as e:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_UNEXPECTED_MSG)
            callback_query.answer(safe_get_messages(user_id).COOKIES_UNEXPECTED_ERROR_MSG)
            send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_UNEXPECTED_ERROR_LOG_MSG.format(error_type=type(e).__name__, error=str(e)))
        return

    browser_option = data

    # Dictionary with Browsers and Their Paths (Same as ABOVE)
    browsers = {
        "brave": "~/.config/BraveSoftware/Brave-Browser/",
        "chrome": "~/.config/google-chrome/",
        "chromium": "~/.config/chromium/",
        "edge": "~/.config/microsoft-edge/",
        "firefox": "~/.mozilla/firefox/",
        "opera": "~/.config/opera/",
        "safari": "~/Library/Safari/",
        "vivaldi": "~/.config/vivaldi/",
        "whale": ["~/.config/Whale/", "~/.config/naver-whale/"]
    }
    path = browsers.get(browser_option)
    # If the browser is not installed, we inform the user and do not execute the command
    if (browser_option == "safari") or (
            isinstance(path, list) and not any(os.path.exists(os.path.expanduser(p)) for p in path)
    ) or (isinstance(path, str) and not os.path.exists(os.path.expanduser(path))):
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_MSG.format(browser=browser_option.capitalize()))
        try:
            callback_query.answer(safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_CALLBACK_MSG)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_LOG_MSG.format(browser=browser_option))
        return

    # Build the command for cookie extraction using the same yt-dlp as Python API
    import sys
    cmd = [sys.executable, '-m', 'yt_dlp', '--cookies', str(cookie_file), '--cookies-from-browser', str(browser_option)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

    if result.returncode != 0:
        if "You must provide at least one URL" in result.stderr:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_SAVED_USING_BROWSER_MSG.format(browser=browser_option))
            send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SAVED_BROWSER_LOG_MSG.format(browser=browser_option))
        else:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_FAILED_TO_SAVE_MSG.format(error=result.stderr))
            send_to_logger(callback_query.message,
                           f"Failed to save cookies using browser {browser_option}: {result.stderr}")
    else:
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_SAVED_USING_BROWSER_MSG.format(browser=browser_option))
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SAVED_BROWSER_LOG_MSG.format(browser=browser_option))

    callback_query.answer(safe_get_messages(user_id).COOKIES_BROWSER_CHOICE_UPDATED_MSG)

#############################################################################################################################

# SEND COOKIE VIA Document
# Accept cookie.txt not only in private chats, but also in groups/topics
@app.on_message(filters.document)
@reply_with_keyboard
@background_handler(label="cookie_document")
def save_my_cookie(app, message):
    """
    Save cookies uploaded by the user as a document.
    
    Validates:
    - File size (max 100KB)
    - Extension (.txt)
    - Format (Netscape HTTP Cookie File)
    
    Args:
        app: Application instance
        message: Message containing the document
    """
    user_id = str(message.chat.id)
    # Check file size
    if message.document.file_size > 100 * 1024:
        send_to_all(message, safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_MSG)
        return
    # Check extension
    if not message.document.file_name.lower().endswith('.txt'):
        send_to_all(message, safe_get_messages(user_id).COOKIES_INVALID_FORMAT_MSG)
        return
    # Download the file to a temporary folder to check the contents
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, message.document.file_name)
        app.download_media(message, file_name=tmp_path)
        try:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # read only the first 4 KB
                if '# Netscape HTTP Cookie File' not in content:
                    send_to_all(message, safe_get_messages(user_id).COOKIES_INVALID_COOKIE_MSG)
                    return
        except Exception as e:
            send_to_all(message, safe_get_messages(user_id).COOKIES_ERROR_READING_MSG.format(error=e))
            return
        # If all checks are passed - save the file to the user's folder
        user_folder = f"./users/{user_id}"
        create_directory(user_folder)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_folder, cookie_filename)
        import shutil
        shutil.copyfile(tmp_path, cookie_file_path)
    send_to_user(message, safe_get_messages(user_id).COOKIES_FILE_SAVED_MSG)
    send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_SAVED_USER_LOG_MSG.format(user_id=user_id))

@app.on_callback_query(filters.regex(r"^download_cookie\|"))
# @reply_with_keyboard
def download_cookie_callback(app, callback_query):
    """
    Handle cookie download service selection.
    
    Supported services:
    - YouTube (with validation)
    - Instagram, Twitter, TikTok, Facebook
    - User-provided cookies
    - Browser extraction
    
    Args:
        app: Application instance
        callback_query: Callback query with selected service
    """
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "youtube":
        # Send initial message about starting the process
        safe_edit_message_text(
            callback_query.message.chat.id, 
            callback_query.message.id, 
            safe_get_messages(user_id).COOKIES_YOUTUBE_TEST_START_MSG
        )
        download_and_validate_youtube_cookies(app, callback_query, user_id=user_id)
    elif data == "instagram":
        download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "vk":
        download_and_save_cookie(app, callback_query, Config.VK_COOKIE_URL, "vk")
    elif data == "check_cookie":
        try:
            # Run cookie checking directly using a fake message
            checking_cookie_file(app, fake_message(Config.CHECK_COOKIE_COMMAND, user_id))
            try:
                app.answer_callback_query(callback_query.id)
            except Exception:
                pass
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_FAILED_START_BROWSER_LOG_MSG.format(e=e))
            try:
                app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FAILED_RUN_CHECK_MSG, show_alert=False)
            except Exception:
                pass
    #elif data == "facebook":
        #download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
    elif data == "own":
        try:
            app.answer_callback_query(callback_query.id)
        except Exception:
            pass
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        safe_send_message(
            callback_query.message.chat.id,
            safe_get_messages(user_id).SAVE_AS_COOKIE_HINT,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id if hasattr(callback_query.message, 'id') else None),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice=safe_get_messages(user_id).FLOOD_LIMIT_TRY_LATER_MSG
        )
    elif data == "from_browser":
        try:
            cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_FAILED_START_BROWSER_LOG_MSG.format(e=e))
            try:
                app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FAILED_OPEN_BROWSER_MSG, show_alert=True)
            except Exception:
                pass
    elif data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).COOKIES_MENU_CLOSED_MSG)
        return

@app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))
def save_as_cookie_hint_callback(app, callback_query):
    """
    Handle closing the "save cookie" hint.
    
    Args:
        app: Application instance
        callback_query: Callback query
    """
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).COOKIES_HINT_CLOSED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SAVE_AS_HINT_CLOSED_MSG)
        return

# Called from url_distractor - no decorator needed
def checking_cookie_file(app, message):
    """
    Validate an existing user cookie file.
    
    Checks:
    - Cookie file exists
    - Format is correct (Netscape HTTP Cookie File)
    - Contains YouTube domains
    - Works via test_youtube_cookies()
    """
    user_id = str(message.chat.id)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    file_path = os.path.join("users", user_id, cookie_filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as cookie:
            cookie_content = cookie.read()
        if cookie_content.startswith("# Netscape HTTP Cookie File"):
            # Check the functionality of YouTube cookies
            from HELPERS.safe_messeger import safe_send_message
            initial_msg = safe_send_message(message.chat.id, safe_get_messages(user_id).COOKIES_FILE_EXISTS_MSG, parse_mode=enums.ParseMode.HTML)
            
            # Check if the file contains YouTube cookies (by domain column)
            def _has_youtube_domain(text: str) -> bool:
                for raw in text.split('\n'):
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Split by tabs or spaces, domain is the first column
                    parts = line.split('\t') if '\t' in line else line.split()
                    if not parts:
                        continue
                    domain = parts[0].lower()
                    if 'youtube.com' in domain:
                        return True
                return False
            if _has_youtube_domain(cookie_content):
                if test_youtube_cookies(file_path, user_id=user_id):
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        safe_edit_message_text(message.chat.id, initial_msg.id, safe_get_messages(user_id).COOKIES_YOUTUBE_WORKING_PROPERLY_MSG)
                    send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_WORKING_LOG_MSG)
                else:
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        safe_edit_message_text(message.chat.id, initial_msg.id, safe_get_messages(user_id).COOKIES_YOUTUBE_EXPIRED_INVALID_MSG)
                    send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_EXPIRED_LOG_MSG)
            else:
                send_to_user(message, safe_get_messages(user_id).COOKIES_SKIPPED_VALIDATION_MSG)
                send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_CORRECT_FORMAT_LOG_MSG)
        else:
            send_to_user(message, safe_get_messages(user_id).COOKIES_INCORRECT_FORMAT_MSG)
            send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_INCORRECT_FORMAT_LOG_MSG)
    else:
        send_to_user(message, safe_get_messages(user_id).COOKIES_FILE_NOT_FOUND_MSG)
        send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_NOT_FOUND_LOG_MSG)


# @reply_with_keyboard
def download_cookie(app, message):
    """
    Show a menu with buttons to download cookie files for different services.
    
    Supported services:
    - YouTube, Instagram, Twitter/X, TikTok, Facebook
    - User-provided cookies
    - Browser extraction
    
    Args:
        app: Application instance
        message: Command message
    """
    user_id = str(message.chat.id)
    
    # Check for fast command with arguments: /cookie youtube, /cookie youtube <n>, /cookie instagram, etc.
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            service = parts[1].lower()
            if service == "youtube":
                # Handle YouTube cookies directly
                user_id = str(message.chat.id)
                user_dir = os.path.join("users", user_id)
                create_directory(user_dir)
                cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
                cookie_file_path = os.path.join(user_dir, cookie_filename)
                
                # Send initial message
                send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_TEST_START_MSG)
                
                # Check existing cookies first
                if os.path.exists(cookie_file_path):
                    if test_youtube_cookies(cookie_file_path, user_id=user_id):
                        send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_WORKING_MSG)
                        return
                    else:
                        send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_EXPIRED_MSG)
                # Optional specific index: /cookie youtube <n>
                selected_index = None
                if len(parts) >= 3 and parts[2].isdigit():
                    try:
                        selected_index = int(parts[2])
                    except Exception:
                        selected_index = None
                # Download and validate new cookies (optionally a specific source)
                download_and_validate_youtube_cookies(app, message, selected_index=selected_index, user_id=user_id)
                return
            elif service in ["instagram", "twitter", "tiktok", "facebook", "own", "from_browser", "vk"]:
                # Fast command - directly call the callback
                fake_callback = fake_message(f"/cookie {service}", user_id)
                fake_callback.data = f"download_cookie|{service}"
                fake_callback.from_user = message.from_user
                fake_callback.message = message
                download_cookie_callback(app, fake_callback)
                return
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_ERROR_FAST_COMMAND_LOG_MSG.format(e=e))
        pass
    
    # Buttons for services
    buttons = [
        [
            InlineKeyboardButton(
                safe_get_messages(user_id).COOKIES_YOUTUBE_BUTTON_MSG.format(max=max(1, len(get_youtube_cookie_urls()))),
                callback_data="download_cookie|youtube"
            ),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_FROM_BROWSER_BUTTON_MSG, callback_data="download_cookie|from_browser"),            
        ],
        [
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_TWITTER_BUTTON_MSG, callback_data="download_cookie|twitter"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_TIKTOK_BUTTON_MSG, callback_data="download_cookie|tiktok"),
        ],
        [
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_VK_BUTTON_MSG, callback_data="download_cookie|vk"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_INSTAGRAM_BUTTON_MSG, callback_data="download_cookie|instagram"),
        ],
        [

            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_CHECK_COOKIE_BUTTON_MSG, callback_data="download_cookie|check_cookie"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_YOUR_OWN_BUTTON_MSG, callback_data="download_cookie|own"),            
        ],
        [         
            InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="download_cookie|close")
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    messages = safe_get_messages(user_id)
    text = f"""
{messages.COOKIE_MENU_TITLE_MSG}

{messages.COOKIE_MENU_DESCRIPTION_MSG}
{messages.COOKIE_MENU_SAVE_INFO_MSG}

<blockquote>
{messages.COOKIE_MENU_TIP_HEADER_MSG}
{messages.COOKIE_MENU_TIP_YOUTUBE_MSG}
{messages.COOKIE_MENU_TIP_YOUTUBE_INDEX_MSG.format(max_index=len(get_youtube_cookie_urls()))}
{messages.COOKIE_MENU_TIP_VERIFY_MSG}
</blockquote>
"""
    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        reply_parameters=ReplyParameters(message_id=message.id),
        message=message
    )




def _sanitize_error_detail(detail: str, url: str) -> str:
    """
    Remove sensitive information (URL) from an error detail string.
    
    Args:
        detail (str): Error details
        url (str): URL to redact
        
    Returns:
        str: Sanitized error string
    """
    try:
        return (detail or "").replace(url or "", "<hidden-url>")
    except Exception:
        return "<hidden>"

def _download_content(url: str, timeout: int = 30, user_id: int | None = None, allow_domain_fallback: bool = True):
    """Download binary content, using the user's proxy when needed."""
    if not url:
        return False, None, None, "empty-url"
    
    sess = Session()
    sess.trust_env = False
    proxy_reason = None
    proxies = None
    
    if user_id is not None:
        try:
            from COMMANDS.proxy_cmd import get_requests_proxies
            proxies, proxy_reason = get_requests_proxies(user_id=user_id, url=url, allow_domain_fallback=allow_domain_fallback)
            if proxies:
                logger.info(f"[COOKIES] Using {proxy_reason or 'user'} proxy for {_sanitize_error_detail(url, url)} download (user_id={user_id})")
        except Exception as e:
            logger.warning(f"[COOKIES] Failed to build proxy config for user {user_id}: {e}")
            proxies = None
            proxy_reason = None
    
    try:
        sess.headers.update({'User-Agent': 'tg-ytdlp-bot/1.0', 'Connection': 'close'})
        adapter = HTTPAdapter(pool_connections=2, pool_maxsize=4, max_retries=2, pool_block=False)
        sess.mount('http://', adapter)
        sess.mount('https://', adapter)
        resp = sess.get(url, timeout=timeout, proxies=proxies)
        status = resp.status_code
        if status == 200:
            data = resp.content
            resp.close()
            return True, status, data, None
        else:
            resp.close()
            return False, status, None, f"http-status-{status}"
    except requests.exceptions.RequestException as e:
        return False, None, None, f"{type(e).__name__}: {e}"
    finally:
        try:
            sess.close()
        except Exception:
            pass

def download_and_save_cookie(app, callback_query, url, service):
    """
    Download and save cookies for the specified service.
    
    Args:
        app: Application instance
        callback_query: Callback query
        url (str): Cookie download URL
        service (str): Service name (youtube, instagram, etc.)
    """
    user_id = str(callback_query.from_user.id)

    # Validate config
    if not url:
        send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_NOT_CONFIGURED_MSG.format(service=service.capitalize()))
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_URL_EMPTY_LOG_MSG.format(service=service.capitalize(), user_id=user_id))
        return

    try:
        ok, status, content, err = _download_content(url, timeout=30, user_id=user_id)
        if ok:
            # Optional: validate extension (do not expose URL); keep internal check
            if not url.lower().endswith('.txt'):
                send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_MUST_BE_TXT_MSG.format(service=service.capitalize()))
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_URL_NOT_TXT_LOG_MSG.format(service=service.capitalize()))
                return
            # size check (max 100KB)
            content_size = len(content or b"")
            if content_size and content_size > 100 * 1024:
                send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_DOWNLOAD_MSG.format(service=service.capitalize(), size=content_size // 1024))
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_FILE_TOO_LARGE_LOG_MSG.format(service=service.capitalize(), size=content_size))
                return
            # Save to user folder
            user_dir = os.path.join("users", user_id)
            create_directory(user_dir)
            cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
            file_path = os.path.join(user_dir, cookie_filename)
            with open(file_path, "wb") as cf:
                cf.write(content)
            send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_FILE_DOWNLOADED_MSG.format(service=service.capitalize()))
            send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_FILE_DOWNLOADED_LOG_MSG.format(service=service.capitalize(), user_id=user_id))
        else:
            # Do not leak URL in user-facing errors
            if status is not None:
                send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_UNAVAILABLE_MSG.format(service=service.capitalize(), status=status))
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_FAILED_LOG_MSG.format(service=service.capitalize(), status=status))
            else:
                send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_ERROR_DOWNLOADING_MSG.format(service=service.capitalize()))
                safe_err = _sanitize_error_detail(err or "", url)
                send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_ERROR_LOG_MSG.format(service=service.capitalize(), error=safe_err))
    except Exception as e:
        send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_ERROR_DOWNLOADING_MSG.format(service=service.capitalize()))
        send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_UNEXPECTED_ERROR_LOG_MSG.format(service=service.capitalize(), error_type=type(e).__name__, error=e))

# Updating The Cookie File.
# @reply_with_keyboard
def save_as_cookie_file(app, message):
    """
    Save cookies provided by the user as plain text.
    
    Handles:
    - Text inside code blocks (```)
    - Plain text
    - Automatically replaces multiple spaces with a tab character
    
    Args:
        app: Application instance
        message: Message containing cookies
    """
    user_id = str(message.chat.id)
    content = message.text[len(Config.SAVE_AS_COOKIE_COMMAND):].strip()
    new_cookie = ""

    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            new_cookie = "\n".join(lines).strip()
        else:
            new_cookie = content
    else:
        new_cookie = content

    processed_lines = []
    for line in new_cookie.splitlines():
        if "\t" not in line:
            line = re.sub(r' {2,}', '\t', line)
        processed_lines.append(line)
    final_cookie = "\n".join(processed_lines)

    if final_cookie:
        send_to_all(message, safe_get_messages(user_id).COOKIES_USER_PROVIDED_MSG)
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_cookie)
        send_to_user(message, safe_get_messages(user_id).COOKIES_SUCCESSFULLY_UPDATED_MSG.format(final_cookie=final_cookie))
        send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_UPDATED_LOG_MSG.format(user_id=user_id))
    else:
        send_to_user(message, safe_get_messages(user_id).COOKIES_NOT_VALID_MSG)
        send_to_logger(message, safe_get_messages(user_id).COOKIES_INVALID_CONTENT_LOG_MSG.format(user_id=user_id))

def test_youtube_cookies_on_url(cookie_file_path: str, url: str, user_id: int | None = None) -> bool:
    """
    Check whether YouTube cookies work for a specific user URL.
    
    Args:
        cookie_file_path (str): Path to the cookie file
        url (str): URL to test
        
    Returns:
        bool: True if cookies work for the URL, otherwise False
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'format': 'best',
            'ignore_no_formats_error': False,
            'cookiefile': cookie_file_path,
            'extractor_args': {
                'youtube': {'player_client': ['tv']}
            },
            'retries': 2,
            'extractor_retries': 1,
        }
        
        ydl_opts = add_proxy_to_ytdl_opts(ydl_opts, url, user_id=user_id)
        # Add PO token provider for YouTube domains
        ydl_opts = add_pot_to_ytdl_opts(ydl_opts, url)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # Ensure we extracted video info
        if not info:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_INFO_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Ensure key fields exist
        if not info.get('title') or not info.get('duration'):
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_MISSING_INFO_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Ensure formats exist
        formats = info.get('formats', [])
        if len(formats) < 2:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INSUFFICIENT_FORMATS_LOG_MSG.format(formats_count=len(formats), cookie_file_path=cookie_file_path))
            return False
            
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIES_WORK_LOG_MSG.format(cookie_file_path=cookie_file_path))
        return True
        
    except Exception as e:
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_USER_URL_LOG_MSG.format(cookie_file_path=cookie_file_path, e=e))
        return False

def test_youtube_cookies(cookie_file_path: str, user_id: int | None = None) -> bool:
    """
    Thoroughly validate YouTube cookies.
    
    Checks:
    - Full video info extraction (title, duration, uploader, view_count, like_count, upload_date)
    - Availability of downloadable formats
    - Quality of extracted info (title length, reasonable duration)
    - Minimum number of formats (at least 3)
    
    Returns:
        bool: True if cookies work correctly, otherwise False
    """
    try:
        # Test URL - use a short YouTube video for testing
        test_url = Config.YOUTUBE_COOKIE_TEST_URL
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            # Don't specify format to avoid "Requested format is not available" errors
            # We only need to check if info can be extracted, not if formats can be processed
            'ignore_no_formats_error': True,  # Ignore format errors - we only check if info is extractable
            'cookiefile': cookie_file_path,
            'extractor_args': {
                'youtube': {'player_client': ['tv']}
            },
            'retries': 3,
            'extractor_retries': 2,
        }
        
        ydl_opts = add_proxy_to_ytdl_opts(ydl_opts, test_url, user_id=user_id)
        # Add PO token provider for YouTube domains
        ydl_opts = add_pot_to_ytdl_opts(ydl_opts, test_url)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        # Ensure we got full video info
        required_fields = ['title', 'duration', 'uploader', 'view_count', 'like_count', 'upload_date']
        if not info:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_INFO_RETURNED_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Check required fields
        missing_fields = [field for field in required_fields if field not in info or not info[field]]
        if missing_fields:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_MISSING_FIELDS_LOG_MSG.format(missing_fields=missing_fields, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_AVAILABLE_FIELDS_LOG_MSG.format(available_fields=list(info.keys())))
            return False
            
        # Ensure there are downloadable formats available
        # Note: formats might be empty if nsig extraction failed, but that's not necessarily a cookie issue
        # We check if formats exist, but don't fail if they're empty - we rely on other fields instead
        formats = info.get('formats', [])
        if not formats:
            # If no formats but we have other required fields, cookies might still be working
            # This can happen if nsig extraction fails (not a cookie issue)
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_FORMATS_LOG_MSG.format(cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INFO_KEYS_LOG_MSG.format(info_keys=list(info.keys())))
            # Don't fail immediately - check if we have enough info to consider cookies valid
            # If we have title, duration, uploader, etc., cookies are likely working
            if not all(field in info and info[field] for field in ['title', 'duration', 'uploader']):
                return False
            # If we have basic info but no formats, it might be a format extraction issue, not cookie issue
            # Log warning but don't fail - cookies might still be valid
            logger.warning(f"Cookies test: No formats available but basic info extracted - might be format extraction issue, not cookie issue")
            # Continue to check other fields
            
        # Validate extracted info quality
        title = info.get('title', '')
        if len(title) < 5:  # Title should be reasonably long
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TITLE_TOO_SHORT_LOG_MSG.format(title=title, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TITLE_LENGTH_LOG_MSG.format(title_length=len(title)))
            return False
            
        # Validate duration (not 0 and not unreasonably large)
        duration = info.get('duration', 0)
        if duration and duration <= 0 or duration > 86400:  # More than 24 hours
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INVALID_DURATION_LOG_MSG.format(duration=duration, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_DURATION_SECONDS_LOG_MSG.format(duration=duration))
            return False
            
        # Validate format count (enough options to choose from)
        # Only check if formats exist - if they don't, we already handled that above
        formats_count = len(formats) if formats else 0
        if formats_count > 0 and formats_count < 3:  # At least 3 formats to choose from (only if formats exist)
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TOO_FEW_FORMATS_LOG_MSG.format(formats_count=formats_count, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_AVAILABLE_FORMATS_LOG_MSG.format(available_formats=[f.get('format_id', 'unknown') for f in formats[:5]]))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_ALL_FORMAT_IDS_LOG_MSG.format(all_format_ids=[f.get('format_id', 'unknown') for f in formats]))
            # If we have formats but too few, it might still be a cookie issue
            # But if we have all required fields, cookies are likely working
            if not all(field in info and info[field] for field in ['title', 'duration', 'uploader', 'view_count', 'like_count', 'upload_date']):
                return False
            # If we have all required fields, cookies are working even if formats are limited
            logger.info(f"Cookies test: Few formats ({formats_count}) but all required fields present - cookies likely valid")
            
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_PASSED_LOG_MSG.format(cookie_file_path=cookie_file_path, formats_count=formats_count))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_TITLE_LOG_MSG.format(title=title))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_DURATION_LOG_MSG.format(duration=duration))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UPLOADER_LOG_MSG.format(uploader=info.get('uploader', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_VIEW_COUNT_LOG_MSG.format(view_count=info.get('view_count', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UPLOAD_DATE_LOG_MSG.format(upload_date=info.get('upload_date', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_LIKE_COUNT_LOG_MSG.format(like_count=info.get('like_count', 'N/A')))
        if formats:
            logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_FORMAT_IDS_LOG_MSG.format(format_ids=[f.get('format_id', 'unknown') for f in formats[:10]]))
        else:
            logger.info("Cookies test: No formats available but all required fields present - cookies are valid")
        return True
            
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e).lower()
        
        # Check for specific YouTube errors that are not cookie-related
        if any(keyword in error_text for keyword in [
            'video is private', 'private video', 'members only', 'premium content'
        ]):
            # These are content availability issues, not cookie issues
            logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UNAVAILABLE_LOG_MSG.format(e=e))
            return False
        elif any(keyword in error_text for keyword in [
            'sign in', 'login required', 'age restricted', 'cookies', 
            'authentication', 'unable to extract'
        ]):
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_AUTH_ERROR_LOG_MSG.format(e=e))
            return False
        elif 'format not found' in error_text or 'no formats found' in error_text or 'requested format is not available' in error_text:
            # Format errors might be due to nsig extraction issues, not necessarily cookie issues
            # Try to extract info without format selection to verify cookies
            logger.warning(f"Format error detected (might be nsig issue, not cookie issue): {e}")
            # Try again without format selection
            try:
                ydl_opts_no_format = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'noplaylist': True,
                    'ignore_no_formats_error': True,
                    'cookiefile': cookie_file_path,
                    'extractor_args': {
                        'youtube': {'player_client': ['tv']}
                    },
                    'retries': 2,
                    'extractor_retries': 1,
                }
                ydl_opts_no_format = add_pot_to_ytdl_opts(ydl_opts_no_format, test_url)
                with yt_dlp.YoutubeDL(ydl_opts_no_format) as ydl:
                    info_retry = ydl.extract_info(test_url, download=False)
                # Check if we can get basic info
                if info_retry and info_retry.get('title') and info_retry.get('duration'):
                    logger.info(f"Cookies test: Format error but basic info extractable - cookies are valid")
                    return True
                else:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_AUTH_ERROR_LOG_MSG.format(e=e))
                    return False
            except Exception as retry_e:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_AUTH_ERROR_LOG_MSG.format(e=retry_e))
                return False
        else:
            # Other errors may not be related to cookies
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_OTHER_ERROR_LOG_MSG.format(e=e))
            return False
            
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_TEST_EXCEPTION_LOG_MSG.format(e=e))
        logger.error(LoggerMsg.COOKIES_YOUTUBE_TEST_EXCEPTION_TYPE_LOG_MSG.format(exception_type=type(e).__name__))
        return False

def get_youtube_cookie_urls() -> list:
    """
    Return a list of YouTube cookie URLs in priority order.
    
    Checks:
    - Main `YOUTUBE_COOKIE_URL`
    - Numbered `YOUTUBE_COOKIE_URL_1`, `YOUTUBE_COOKIE_URL_2`, etc.
    
    Returns:
        list: Cookie download URLs
    """
    urls = []
    
    # Check the main URLs in order of priority
    if hasattr(Config, 'YOUTUBE_COOKIE_URL') and Config.YOUTUBE_COOKIE_URL:
        urls.append(Config.YOUTUBE_COOKIE_URL)
    
    # Add numbered URLs
    for i in range(1, 10):  # Support up to 9 URLs
        url_attr = f'YOUTUBE_COOKIE_URL_{i}'
        if hasattr(Config, url_attr):
            url_value = getattr(Config, url_attr)
            if url_value:
                urls.append(url_value)
    
    return urls

def download_and_validate_youtube_cookies(app, message, selected_index: int | None = None, user_id: int = None) -> bool:
    """
    Download and validate YouTube cookies from all available sources.
    
    Process:
    1. Check the per-user cookie rotation retry limit
    2. Download cookies from each source in order
    3. Thoroughly validate them via test_youtube_cookies()
    4. Save only working cookies
    5. If none work, report an error
    
    Args:
        app: Application instance
        message: Command message or callback_query
    
    Returns:
        bool: True if working cookies were found, otherwise False
    """
    # Handle both message and callback_query objects
    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
        user_id = str(message.chat.id)
    elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
        user_id = str(message.from_user.id)
    else:
        logger.error(LoggerMsg.COOKIES_CANNOT_DETERMINE_USER_ID_LOG_MSG)
        return False
    
    # Check the YouTube cookie rotation retry limit
    if not check_youtube_cookie_retry_limit(int(user_id)):
        # Create a helper to send a "limit exceeded" message
        def send_limit_message():
            try:
                from CONFIG.limits import LimitsConfig
                
                # Get and format the message
                messages = safe_get_messages(user_id)
                limit_value = LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR
                
                # Ensure the message exists
                if hasattr(messages, 'COOKIES_YOUTUBE_RETRY_LIMIT_EXCEEDED_MSG'):
                    limit_message = messages.COOKIES_YOUTUBE_RETRY_LIMIT_EXCEEDED_MSG.format(limit=limit_value)
                else:
                    # Fallback if the message template wasn't found
                    limit_message = f"⚠️ YouTube cookie retry limit exceeded!\n\n🔢 Maximum: {limit_value} attempts per hour\n⏰ Please try again later"
                
                # Log for debugging
                logger.info(f"Sending limit message to user {user_id}")
                logger.info(f"Limit value: {limit_value}")
                logger.info(f"Raw message: {messages.COOKIES_YOUTUBE_RETRY_LIMIT_EXCEEDED_MSG if hasattr(messages, 'COOKIES_YOUTUBE_RETRY_LIMIT_EXCEEDED_MSG') else 'NOT FOUND'}")
                logger.info(f"Formatted message: {limit_message}")
                
                if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                    from HELPERS.logger import send_to_user
                    send_to_user(message, limit_message)
                elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                    from HELPERS.safe_messeger import safe_send_message
                    from pyrogram import enums
                    safe_send_message(message.from_user.id, limit_message, parse_mode=enums.ParseMode.HTML)
                else:
                    from HELPERS.safe_messeger import safe_send_message
                    from pyrogram import enums
                    safe_send_message(user_id, limit_message, parse_mode=enums.ParseMode.HTML)
            except Exception as e:
                logger.error(f"Error sending retry limit message: {e}")
                # Fallback message without formatting
                try:
                    fallback_message = f"⚠️ YouTube cookie retry limit exceeded!\n\n🔢 Maximum: {LimitsConfig.YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR} attempts per hour\n⏰ Please try again later"
                    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                        from HELPERS.logger import send_to_user
                        send_to_user(message, fallback_message)
                    elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                        from HELPERS.safe_messeger import safe_send_message
                        from pyrogram import enums
                        safe_send_message(message.from_user.id, fallback_message, parse_mode=enums.ParseMode.HTML)
                    else:
                        from HELPERS.safe_messeger import safe_send_message
                        from pyrogram import enums
                        safe_send_message(user_id, fallback_message, parse_mode=enums.ParseMode.HTML)
                except Exception as e2:
                    logger.error(f"Error sending fallback limit message: {e2}")
        
        send_limit_message()
        logger.warning(f"YouTube cookie retry limit exceeded for user {user_id}")
        return False
    
    # Record a cookie rotation attempt
    record_youtube_cookie_retry_attempt(int(user_id))
    
    # Create a helper function to send messages safely
    def safe_send_to_user(msg):
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                # It's a Message object
                from HELPERS.logger import send_to_user
                send_to_user(message, msg)
            elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                # It's a CallbackQuery object
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(message.from_user.id, msg, parse_mode=enums.ParseMode.HTML)
            else:
                # Fallback - try to get user_id and send directly
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_ERROR_SENDING_MESSAGE_LOG_MSG.format(e=e))
            # Try direct send as last resort
            try:
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
            except Exception as e2:
                logger.error(LoggerMsg.COOKIES_FINAL_FALLBACK_SEND_FAILED_LOG_MSG.format(e2=e2))
    
    cookie_urls = get_youtube_cookie_urls()
    
    if not cookie_urls:
        safe_send_to_user(safe_get_messages(user_id).COOKIES_YOUTUBE_SOURCES_NOT_CONFIGURED_MSG)
        # Safe logging
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG.format(user_id=user_id))
            else:
                logger.error(LoggerMsg.COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG.format(user_id=user_id))
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_ERROR_LOGGING_LOG_MSG.format(e=e))
        return False
    
    # Create user folder
    user_dir = os.path.join("users", user_id)
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Send initial message and store message ID for updates
    initial_msg = None
    try:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            # It's a Message object - send initial message
            from HELPERS.logger import send_to_user
            initial_msg = send_to_user(message, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)))
        elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
            # It's a CallbackQuery object - send initial message
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = safe_send_message(message.from_user.id, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)), parse_mode=enums.ParseMode.HTML)
        else:
            # Fallback - send directly
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = safe_send_message(user_id, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_ERROR_SENDING_INITIAL_MESSAGE_LOG_MSG.format(e=e))
    
    # Helper function to update the message (avoid MESSAGE_NOT_MODIFIED)
    _last_update_text = { 'text': None }
    def update_message(new_text, user_id_param=None):
        try:
            if new_text == _last_update_text['text']:
                return
            if initial_msg and hasattr(initial_msg, 'id'):
                if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                    app.edit_message_text(message.chat.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                    app.edit_message_text(message.from_user.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                else:
                    app.edit_message_text(user_id_param or user_id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                _last_update_text['text'] = new_text
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" in str(e):
                return
            logger.error(LoggerMsg.COOKIES_ERROR_UPDATING_MESSAGE_LOG_MSG.format(e=e))
    
    # Determine the order of attempts - only use unchecked sources
    unchecked_indices = get_unchecked_cookie_sources(int(user_id), cookie_urls)
    if not unchecked_indices:
        update_message(safe_get_messages(user_id).COOKIES_ALL_EXPIRED_MSG, user_id)
        logger.warning(f"All cookie sources have been checked for user {user_id}, no more sources to try")
        # Reset checked-source cache for this user
        reset_checked_cookie_sources(int(user_id))
        logger.info(f"Reset checked cookie sources for user {user_id} to allow retry in future")
        return False
    
    global _yt_round_robin_index
    if selected_index is not None:
        # Use a specific 1-based index
        if 1 <= selected_index <= len(cookie_urls):
            if (selected_index - 1) in unchecked_indices:
                indices = [selected_index - 1]
            else:
                update_message(safe_get_messages(user_id).COOKIES_INVALID_YOUTUBE_INDEX_MSG.format(selected_index=selected_index, total_urls=len(cookie_urls)), user_id)
                return False
        else:
            update_message(safe_get_messages(user_id).COOKIES_INVALID_YOUTUBE_INDEX_MSG.format(selected_index=selected_index, total_urls=len(cookie_urls)), user_id)
            return False
    else:
        indices = unchecked_indices.copy()
        order = getattr(Config, 'YOUTUBE_COOKIE_ORDER', 'round_robin')
        if not order:
            order = 'round_robin'
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIE_ORDER_MODE_LOG_MSG.format(order=order))
        if order == 'random':
            random.shuffle(indices)
        else:
            # round_robin: rotate starting position
            if len(indices) > 0:
                start = _yt_round_robin_index % len(indices)
                indices = indices[start:] + indices[:start]
                # advance pointer for next call
                _yt_round_robin_index = (start + 1) % len(indices)
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIE_INDICES_ORDER_LOG_MSG.format(indices=[i+1 for i in indices]))

    # Iterate over chosen order
    for attempt_number, idx in enumerate(indices, 1):
        url = cookie_urls[idx]
        try:
            # Update message about the current attempt
            update_message(safe_get_messages(user_id).COOKIES_DOWNLOADING_CHECKING_MSG.format(attempt=attempt_number, total=len(indices)), user_id)
            
            # Mark this source as checked
            mark_cookie_source_checked(int(user_id), idx)
            
            # Download cookies
            ok, status, content, err = _download_content(url, timeout=30, user_id=user_id)
            if not ok:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_FAILED_LOG_MSG.format(url_index=idx + 1, status=status, error=err))
                continue
            
            # Check the format and size
            if not url.lower().endswith('.txt'):
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_URL_NOT_TXT_LOG_MSG.format(url_index=idx + 1))
                continue
                
            content_size = len(content or b"")
            if content_size and content_size > 100 * 1024:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_FILE_TOO_LARGE_LOG_MSG.format(url_index=idx + 1, file_size=content_size))
                continue
            
            # Save cookies to a temporary file
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Update message about testing
            update_message(safe_get_messages(user_id).COOKIES_DOWNLOADING_TESTING_MSG.format(attempt=attempt_number, total=len(indices)), user_id)
            
            # Check the functionality of cookies
            if test_youtube_cookies(cookie_file_path, user_id=user_id):
                update_message(safe_get_messages(user_id).COOKIES_SUCCESS_VALIDATED_MSG.format(source=idx + 1, total=len(cookie_urls)), user_id)
                # Safe logging
                try:
                    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                        send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG.format(user_id=user_id, source=idx + 1))
                    else:
                        logger.info(LoggerMsg.COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG.format(user_id=user_id, source=idx + 1))
                except Exception as e:
                    logger.error(LoggerMsg.COOKIES_ERROR_LOGGING_LOG_MSG.format(e=e))
                return True
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_FROM_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=idx + 1))
                # Remove non-working cookies
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_EXCEPTION_LOG_MSG.format(e=e))
            # Remove the file in case of an error
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # If no source worked
    update_message(safe_get_messages(user_id).COOKIES_ALL_EXPIRED_MSG, user_id)
    # Safe logging
    try:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_ALL_FAILED_LOG_MSG.format(user_id=user_id))
        else:
            logger.error(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_LOG_MSG.format(user_id=user_id))
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_ERROR_LOG_MSG.format(e=e))
    return False

def ensure_working_youtube_cookies(user_id: int) -> bool:
    """
    Ensure the user has working YouTube cookies.
    
    Process:
    1. Check the per-user cookie rotation retry limit
    2. Check cached results and active tasks
    3. Check the user's existing cookies
    4. If they don't work, download fresh cookies from all sources
    5. If no source works, delete cookies and return False
    
    Args:
        user_id (int): User ID
        
    Returns:
        bool: True if working cookies exist, otherwise False
    """
    global _youtube_cookie_cache
    
    from CONFIG.limits import LimitsConfig
    
    # Check the YouTube cookie rotation retry limit
    if not check_youtube_cookie_retry_limit(user_id):
        logger.warning(f"YouTube cookie retry limit exceeded for user {user_id}")
        return False
    
    # Clean expired tasks before checking
    cleanup_expired_tasks()
    
    # Check cache first
    current_time = time.time()
    if user_id in _youtube_cookie_cache:
        cache_entry = _youtube_cookie_cache[user_id]
        
        # Check whether the cache entry exceeded max lifetime
        if current_time - cache_entry['timestamp'] > LimitsConfig.COOKIE_CACHE_MAX_LIFETIME:
            logger.warning(f"Forcefully deactivating expired YouTube cookie cache for user {user_id}")
            del _youtube_cookie_cache[user_id]
        elif current_time - cache_entry['timestamp'] < LimitsConfig.COOKIE_CACHE_DURATION:
            # Check whether a task is already active for this user
            if not cache_entry.get('active', False):
                # Check if cookie file still exists and hasn't changed
                if os.path.exists(cache_entry['cookie_path']):
                    logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_VALID_LOG_MSG.format(user_id=user_id, cache_duration=LimitsConfig.COOKIE_CACHE_DURATION))
                    return cache_entry['result']
                else:
                    # Cookie file was deleted, remove from cache
                    del _youtube_cookie_cache[user_id]
            else:
                logger.info(f"Cookie validation task is already active for user {user_id}")
                return False
    
    # Start a new cookie validation task
    task_id = start_cookie_task(user_id, Config.YOUTUBE_COOKIE_TEST_URL, 'youtube')
    
    try:
        logger.info(LoggerMsg.COOKIES_YOUTUBE_STARTING_ENSURE_LOG_MSG.format(user_id=user_id))
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_dir, cookie_filename)
        
        # Check existing cookies
        if os.path.exists(cookie_file_path):
            logger.info(LoggerMsg.COOKIES_YOUTUBE_CHECKING_EXISTING_LOG_MSG.format(user_id=user_id))
            if test_youtube_cookies(cookie_file_path, user_id=user_id):
                logger.info(LoggerMsg.COOKIES_YOUTUBE_EXISTING_WORKING_LOG_MSG.format(user_id=user_id))
                logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_EXISTING_WORKING_LOG_MSG.format(user_id=user_id))
                # Finish the task successfully
                finish_cookie_task(task_id, True, cookie_file_path)
                return True
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_EXISTING_FAILED_LOG_MSG.format(user_id=user_id))
    
        # If cookies are missing or invalid, try downloading fresh ones
        cookie_urls = get_youtube_cookie_urls()
        if not cookie_urls:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_NO_SOURCES_CONFIGURED_LOG_MSG.format(user_id=user_id))
            # Remove non-working cookies
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            # Finish the task unsuccessfully
            finish_cookie_task(task_id, False, cookie_file_path)
            return False
    
        # Use only unchecked sources for this user
        unchecked_indices = get_unchecked_cookie_sources(user_id, cookie_urls)
        if not unchecked_indices:
            logger.warning(f"All cookie sources have been checked for user {user_id}, no more sources to try")
            # Reset the checked-source cache for this user
            reset_checked_cookie_sources(user_id)
            logger.info(f"Reset checked cookie sources for user {user_id} to allow retry in future")
            # Remove non-working cookies
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            # Finish the task unsuccessfully
            finish_cookie_task(task_id, False, cookie_file_path)
            return False
        
        logger.info(LoggerMsg.COOKIES_YOUTUBE_ATTEMPTING_DOWNLOAD_LOG_MSG.format(user_id=user_id, sources_count=len(unchecked_indices)))
        
        # Record a cookie-rotation attempt only when downloading fresh cookies
        record_youtube_cookie_retry_attempt(user_id)
        
        for i, idx in enumerate(unchecked_indices, 1):
            url = cookie_urls[idx]
            try:
                logger.info(LoggerMsg.COOKIES_YOUTUBE_TRYING_SOURCE_LOG_MSG.format(source_index=idx + 1, total_sources=len(cookie_urls), user_id=user_id))
                
                # Mark this source as checked
                mark_cookie_source_checked(user_id, idx)
                
                # Download cookies
                ok, status, content, err = _download_content(url, timeout=30, user_id=user_id)
                if not ok:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_FAILED_LOG_MSG.format(url_index=idx + 1, status=status, error=err))
                    continue
                
                # Validate format and size
                if not url.lower().endswith('.txt'):
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_URL_NOT_TXT_LOG_MSG.format(url_index=idx + 1))
                    continue
                    
                content_size = len(content or b"")
                if content_size and content_size > 100 * 1024:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_FILE_TOO_LARGE_LOG_MSG.format(url_index=idx + 1, file_size=content_size))
                    continue
                
                # Save cookies
                with open(cookie_file_path, "wb") as cf:
                    cf.write(content)
                
                # Validate cookies
                if test_youtube_cookies(cookie_file_path, user_id=user_id):
                    logger.info(LoggerMsg.COOKIES_YOUTUBE_SOURCE_WORKING_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_WORKING_FOUND_LOG_MSG.format(user_id=user_id, source_index=idx + 1))
                    # Finish task successfully
                    finish_cookie_task(task_id, True, cookie_file_path)
                    return True
                else:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    # Remove non-working cookies
                    if os.path.exists(cookie_file_path):
                        os.remove(cookie_file_path)
                        
            except Exception as e:
                logger.error(LoggerMsg.COOKIES_YOUTUBE_PROCESSING_ERROR_LOG_MSG.format(source_index=idx + 1, user_id=user_id, e=e))
                # Remove the file on error
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                continue
    
        # If no source worked
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_REMOVING_LOG_MSG.format(user_id=user_id))
        if os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)
        logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_NO_WORKING_LOG_MSG.format(user_id=user_id))
        # Finish task unsuccessfully
        finish_cookie_task(task_id, False, cookie_file_path)
        return False
        
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_ERROR_LOG_MSG.format(e=e))
        # Finish task unsuccessfully on error
        finish_cookie_task(task_id, False)
        return False

def is_youtube_cookie_error(error_message: str) -> bool:
    """
    Determine whether a download error is related to YouTube cookies.
    
    Args:
        error_message (str): Error message from yt-dlp
        
    Returns:
        bool: True if the error is cookie-related, otherwise False
    """
    error_lower = error_message.lower()
    
    # Check for content-unavailable errors that are NOT cookie-related.
    # "Video unavailable" can be caused by invalid cookies, so we don't exclude it here.
    content_unavailable_keywords = [
        'video is private', 'private video', 'members only', 'premium content',
        'this video is not available', 'copyright', 'dmca'
    ]
    
    if any(keyword in error_lower for keyword in content_unavailable_keywords):
        return False  # Definitely not a cookie error
    
    # "Video unavailable" and "content isn't available" CAN be due to invalid cookies,
    # so we keep them eligible for cookie rotation.
    
    # Keywords indicating cookie/auth-related problems
    cookie_related_keywords = [
        'sign in', 'login required', 'age restricted', 'cookies', 
        'authentication', 'format not found', 'no formats found', 'unable to extract', 
        'http error 403', 'http error 401', 'forbidden', 'unauthorized', 'access denied',
        'subscription required'
    ]
    
    return any(keyword in error_lower for keyword in cookie_related_keywords)

def is_youtube_geo_error(error_message: str) -> bool:
    """
    Determine whether a download error is related to YouTube geo restrictions.
    
    Args:
        error_message (str): Error message from yt-dlp
        
    Returns:
        bool: True if the error is geo-restriction-related, otherwise False
    """
    error_lower = error_message.lower()
    
    # Keywords indicating geo restrictions
    geo_related_keywords = [
        'region blocked', 'geo-blocked', 'country restricted', 'not available in your country',
        'this video is not available in your country', 'video unavailable in your region',
        'blocked in your region', 'geographic restriction', 'location restricted',
        'not available in this region', 'country not supported', 'regional restriction'
    ]
    
    return any(keyword in error_lower for keyword in geo_related_keywords)

def retry_download_with_proxy(user_id: int, url: str, download_func, *args, **kwargs):
    """
    Retry a download via proxy for geo-restriction errors.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        download_func: Download function to retry
        *args, **kwargs: Arguments for the download function
        
    Returns:
        Successful download result, or None if all attempts fail
    """
    from URL_PARSERS.youtube import is_youtube_url
    
    # Only retry for YouTube URLs
    if not is_youtube_url(url):
        return None
    
    logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_LOG_MSG.format(user_id=user_id))
    
    # Get proxy configuration
    try:
        from COMMANDS.proxy_cmd import get_proxy_config
        proxy_config = get_proxy_config()
        
        if not proxy_config or 'type' not in proxy_config or 'ip' not in proxy_config or 'port' not in proxy_config:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_NO_PROXY_CONFIG_LOG_MSG.format(user_id=user_id))
            return None
        
        # Build proxy URL
        if proxy_config['type'] == 'http':
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
        elif proxy_config['type'] == 'https':
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"https://{proxy_config['ip']}:{proxy_config['port']}"
        elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
        else:
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
        
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_URL_LOG_MSG.format(proxy_url=proxy_url))
        
        # Retry download with proxy
        try:
            # Add use_proxy=True for the download function
            kwargs['use_proxy'] = True
            result = download_func(*args, **kwargs)
            if result is not None:
                logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_SUCCESS_LOG_MSG.format(user_id=user_id))
                return result
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_FAILED_LOG_MSG.format(user_id=user_id))
                return None
        except Exception as e:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_FAILED_ERROR_LOG_MSG.format(user_id=user_id, e=e))
            return None
            
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_SETUP_ERROR_LOG_MSG.format(user_id=user_id, e=e))
        return None

def retry_download_with_different_cookies(user_id: int, url: str, download_func, *args, **kwargs):
    """
    Retry a download with different cookies when cookie-related errors occur.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        download_func: Download function to retry
        *args, **kwargs: Arguments for the download function
        
    Returns:
        Successful download result, or None if all attempts fail
    """
    from URL_PARSERS.youtube import is_youtube_url
    
    # Only retry for YouTube URLs
    if not is_youtube_url(url):
        return None
    
    # Guard against recursion: ensure retry is not already in progress
    retry_key = f"{user_id}_{url}_retry"
    if retry_key in globals().get('_active_retries', set()):
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_ALREADY_IN_PROGRESS_LOG_MSG.format(user_id=user_id))
        return None
    
    # Add key to active retries
    if '_active_retries' not in globals():
        globals()['_active_retries'] = set()
    globals()['_active_retries'].add(retry_key)
    
    try:
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_DIFFERENT_COOKIES_LOG_MSG.format(user_id=user_id))
        
        # Check the YouTube cookie rotation retry limit
        if not check_youtube_cookie_retry_limit(user_id):
            logger.warning(f"YouTube cookie retry limit exceeded for user {user_id}")
            return None
        
        # Get cookie sources
        cookie_urls = get_youtube_cookie_urls()
        if not cookie_urls:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_NO_SOURCES_LOG_MSG.format(user_id=user_id))
            return None
        
        # Use only unchecked sources for this user
        unchecked_indices = get_unchecked_cookie_sources(user_id, cookie_urls)
        if not unchecked_indices:
            logger.warning(f"All cookie sources have been checked for user {user_id}, no more sources to try")
            # Reset the checked-source cache for this user
            reset_checked_cookie_sources(user_id)
            logger.info(f"Reset checked cookie sources for user {user_id} to allow retry in future")
            return None
        
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_dir, cookie_filename)
        
        # Determine the attempt order for unchecked sources only
        indices = unchecked_indices.copy()
        global _yt_round_robin_index
        order = getattr(Config, 'YOUTUBE_COOKIE_ORDER', 'round_robin')
        if order == 'random':
            import random
            random.shuffle(indices)
        else:
            # round_robin: start from the next source
            if len(indices) > 0:
                start = _yt_round_robin_index % len(indices)
                indices = indices[start:] + indices[:start]
                _yt_round_robin_index = (start + 1) % len(indices)
        
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCES_ORDER_LOG_MSG.format(indices=[i+1 for i in indices]))
        
        # Record a cookie rotation attempt
        record_youtube_cookie_retry_attempt(user_id)
        
        # Try each cookie source
        for attempt, idx in enumerate(indices, 1):
            try:
                logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ATTEMPT_LOG_MSG.format(attempt=attempt, total_attempts=len(indices), source_index=idx + 1, user_id=user_id))
                
                # Mark this source as checked
                mark_cookie_source_checked(user_id, idx)
                
                # Download cookies
                try:
                    ok, status, content, err = _download_content(cookie_urls[idx], timeout=30, user_id=user_id)
                except Exception as download_e:
                    logger.error(LoggerMsg.COOKIES_ERROR_PROCESSING_SOURCE_LOG_MSG.format(idx=idx + 1, user_id=user_id, error=download_e))
                    continue
                    
                if not ok:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_DOWNLOAD_FAILED_LOG_MSG.format(source_index=idx + 1, status=status, error=err))
                    continue
                
                # Validate format and size
                if not cookie_urls[idx].lower().endswith('.txt'):
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_URL_NOT_TXT_LOG_MSG.format(source_index=idx + 1))
                    continue
                    
                content_size = len(content or b"")
                if content_size and content_size > 100 * 1024:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FILE_TOO_LARGE_LOG_MSG.format(source_index=idx + 1, file_size=content_size))
                    continue
                
                # Save cookies
                with open(cookie_file_path, "wb") as cf:
                    cf.write(content)
                
                # Validate cookies
                if test_youtube_cookies(cookie_file_path, user_id=user_id):
                    logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCE_WORKING_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    
                    # Update cache
                    current_time = time.time()
                    _youtube_cookie_cache[user_id] = {
                        'result': True,
                        'timestamp': current_time,
                        'cookie_path': cookie_file_path
                    }
                    
                    # Retry download
                    try:
                        result = download_func(*args, **kwargs)
                        if result is not None:
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SUCCESS_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                            return result
                        else:
                            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FAILED_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    except Exception as e:
                        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FAILED_ERROR_LOG_MSG.format(source_index=idx + 1, user_id=user_id, e=e))
                        # Check whether the error is cookie-related
                        if is_youtube_cookie_error(str(e)):
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ERROR_COOKIE_RELATED_LOG_MSG.format(user_id=user_id))
                            continue
                        else:
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ERROR_NOT_COOKIE_RELATED_LOG_MSG.format(user_id=user_id))
                            return None
                else:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    # Remove non-working cookies
                    if os.path.exists(cookie_file_path):
                        os.remove(cookie_file_path)
                        
            except Exception as e:
                logger.error(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROCESSING_ERROR_LOG_MSG.format(source_index=idx + 1, user_id=user_id, e=e))
                # Remove the file on error
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                continue
        
        # If all sources failed
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_ALL_SOURCES_FAILED_LOG_MSG.format(user_id=user_id))
        if os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)
        
        # Update cache
        current_time = time.time()
        _youtube_cookie_cache[user_id] = {
            'result': False,
            'timestamp': current_time,
            'cookie_path': cookie_file_path
        }
        
        return None
    finally:
        # Remove key from active retries
        if '_active_retries' in globals():
            globals()['_active_retries'].discard(retry_key)

def clear_youtube_cookie_cache(user_id: int = None):
    """
    Clear the YouTube cookie validation cache.
    
    Args:
        user_id (int, optional): User ID to clear for. If None, clears the whole cache.
    """
    global _youtube_cookie_cache, _active_cookie_tasks
    
    if user_id is None:
        _youtube_cookie_cache.clear()
        # Remove only YouTube tasks
        youtube_tasks_to_remove = [task_id for task_id, task_info in _active_cookie_tasks.items() if task_info.get('service') == 'youtube']
        for task_id in youtube_tasks_to_remove:
            del _active_cookie_tasks[task_id]
        logger.info(LoggerMsg.COOKIES_CLEARED_CACHE_LOG_MSG)
    else:
        if user_id in _youtube_cookie_cache:
            del _youtube_cookie_cache[user_id]
            logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_CLEARED_LOG_MSG.format(user_id=user_id))
        else:
            logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_NO_ENTRY_LOG_MSG.format(user_id=user_id))
        
        # Remove active YouTube tasks for this user
        youtube_tasks_to_remove = [task_id for task_id, task_info in _active_cookie_tasks.items() 
                                  if task_info['user_id'] == user_id and task_info.get('service') == 'youtube']
        for task_id in youtube_tasks_to_remove:
            del _active_cookie_tasks[task_id]

# Cache for non-YouTube cookie validation results
# Format: {cache_key: {'result': bool, 'timestamp': float, 'cookie_path': str, 'task_id': str, 'active': bool}}
_non_youtube_cookie_cache = {}

def get_service_cookie_url(service_name: str) -> str | None:
    """
    Get a cookie URL for a given service from config.
    
    Args:
        service_name (str): Service name (instagram, twitter, tiktok, vk, facebook)
        
    Returns:
        str | None: Cookie URL, or None if not configured
    """
    service_upper = service_name.upper()
    cookie_url_attr = f"{service_upper}_COOKIE_URL"
    
    if hasattr(Config, cookie_url_attr):
        return getattr(Config, cookie_url_attr)
    return None

def try_download_with_cookie_fallback(user_id: int, url: str, download_func, *args, **kwargs):
    """
    Try downloading with cookie rotation for non-YouTube sites.
    
    Logic:
    1. Try user cookies first
    2. If that fails, try service cookies from config
    3. If that fails, try global cookies from COOKIE_FILE_PATH
    4. If that fails, try without cookies
    5. If nothing works, return an error
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        download_func: Download function to call
        *args, **kwargs: Arguments for the download function
        
    Returns:
        Successful download result, or None if all attempts fail
    """
    from URL_PARSERS.youtube import is_youtube_url
    
    # For YouTube, use the dedicated logic
    if is_youtube_url(url):
        return retry_download_with_different_cookies(user_id, url, download_func, *args, **kwargs)
    
    # Determine service by domain
    service_name = None
    if 'instagram.com' in url or 'instagr.am' in url:
        service_name = 'instagram'
    elif 'twitter.com' in url or 'x.com' in url:
        service_name = 'twitter'
    elif 'tiktok.com' in url:
        service_name = 'tiktok'
    elif 'vk.com' in url:
        service_name = 'vk'
    elif 'facebook.com' in url or 'fb.com' in url:
        service_name = 'facebook'
    
    logger.info(f"Trying cookie fallback for non-YouTube URL: {url}, service: {service_name}")
    
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    user_cookie_path = os.path.join(user_dir, cookie_filename)
    
    # Cookie attempt list
    cookie_attempts = []
    
    # 1) User cookies
    if os.path.exists(user_cookie_path):
        cookie_attempts.append(('user', user_cookie_path))
    
    # 2) Service cookies from config
    if service_name:
        service_cookie_url = get_service_cookie_url(service_name)
        if service_cookie_url:
            cookie_attempts.append(('service', service_cookie_url))
    
    # 3) Global cookies from COOKIE_FILE_PATH
    global_cookie_path = Config.COOKIE_FILE_PATH
    if os.path.exists(global_cookie_path):
        cookie_attempts.append(('global', global_cookie_path))
    
    # Try each cookie attempt
    for attempt_type, cookie_source in cookie_attempts:
        try:
            cookie_file_path = None
            
            if attempt_type == 'user':
                cookie_file_path = cookie_source
                logger.info(f"Trying user cookies for {url}")
            elif attempt_type == 'service':
                # Download service cookies
                try:
                    ok, status, content, err = _download_content(cookie_source, timeout=30, user_id=user_id)
                    if ok and content and len(content) <= 100 * 1024:
                        cookie_file_path = user_cookie_path
                        with open(cookie_file_path, "wb") as cf:
                            cf.write(content)
                        logger.info(f"Downloaded {service_name} cookies for {url}")
                    else:
                        logger.warning(f"Failed to download {service_name} cookies: status={status}, error={err}")
                        continue
                except Exception as e:
                    logger.error(f"Error downloading {service_name} cookies: {e}")
                    continue
            elif attempt_type == 'global':
                # Copy global cookies
                try:
                    import shutil
                    cookie_file_path = user_cookie_path
                    shutil.copy2(cookie_source, cookie_file_path)
                    logger.info(f"Copied global cookies for {url}")
                except Exception as e:
                    logger.error(f"Failed to copy global cookies: {e}")
                    continue
            
            if cookie_file_path and os.path.exists(cookie_file_path):
                # Try downloading with these cookies
                try:
                    # Attach cookies to options
                    if 'ytdl_opts' in kwargs:
                        kwargs['ytdl_opts']['cookiefile'] = cookie_file_path
                    elif len(args) > 0 and isinstance(args[0], dict):
                        args[0]['cookiefile'] = cookie_file_path
                    
                    result = download_func(*args, **kwargs)
                    if result is not None:
                        logger.info(f"Successfully downloaded {url} with {attempt_type} cookies")
                        return result
                    else:
                        logger.warning(f"Download failed with {attempt_type} cookies for {url}")
                except Exception as e:
                    logger.warning(f"Download failed with {attempt_type} cookies for {url}: {e}")
                    # Check whether the error is cookie-related
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['cookie', 'auth', 'login', 'sign in', '403', '401']):
                        logger.info(f"Error appears to be cookie-related for {url}")
                    else:
                        logger.info(f"Error appears to be non-cookie-related for {url}")
                        # If the error is not cookie-related, don't try further
                        return None
        except Exception as e:
            logger.error(f"Error in cookie attempt {attempt_type} for {url}: {e}")
            continue
    
    # 4) Try without cookies
    try:
        logger.info(f"Trying download without cookies for {url}")
        # Remove cookies from options
        if 'ytdl_opts' in kwargs:
            kwargs['ytdl_opts']['cookiefile'] = None
        elif len(args) > 0 and isinstance(args[0], dict):
            args[0]['cookiefile'] = None
        
        result = download_func(*args, **kwargs)
        if result is not None:
            logger.info(f"Successfully downloaded {url} without cookies")
            return result
        else:
            logger.warning(f"Download failed without cookies for {url}")
    except Exception as e:
        logger.warning(f"Download failed without cookies for {url}: {e}")
    
    # All attempts failed
    logger.error(f"All cookie attempts failed for {url}")
    return None

def get_cookie_cache_key(user_id: int, url: str, service: str = None) -> str:
    """
    Create a cache key for cookie validation results.
    
    Args:
        user_id (int): User ID
        url (str): URL
        service (str, optional): Service name
        
    Returns:
        str: Cache key
    """
    if service:
        return f"{user_id}_{service}_cookie_cache"
    else:
        # For YouTube, use a dedicated domain key
        from URL_PARSERS.youtube import is_youtube_url
        if is_youtube_url(url):
            return f"{user_id}_youtube_cookie_cache"
        else:
            return f"{user_id}_other_cookie_cache"

def set_cookie_cache_result(user_id: int, url: str, result: bool, cookie_path: str = None, service: str = None):
    """
    Store a cookie validation result in the cache.
    
    Args:
        user_id (int): User ID
        url (str): URL
        result (bool): Validation result
        cookie_path (str, optional): Path to the cookie file
        service (str, optional): Service name
    """
    global _non_youtube_cookie_cache
    
    cache_key = get_cookie_cache_key(user_id, url, service)
    _non_youtube_cookie_cache[cache_key] = {
        'result': result,
        'timestamp': time.time(),
        'cookie_path': cookie_path,
        'task_id': None,  # Set when the task finishes
        'active': False
    }
    
    logger.info(f"Cached cookie result for {cache_key}: {result}")

def get_cookie_cache_result(user_id: int, url: str, service: str = None) -> dict | None:
    """
    Get a cookie validation result from the cache.
    
    Args:
        user_id (int): User ID
        url (str): URL
        service (str, optional): Service name
        
    Returns:
        dict | None: Cached result, or None
    """
    global _non_youtube_cookie_cache
    
    from CONFIG.limits import LimitsConfig
    
    # Clean expired tasks before checking
    cleanup_expired_tasks()
    
    cache_key = get_cookie_cache_key(user_id, url, service)
    if cache_key in _non_youtube_cookie_cache:
        cache_entry = _non_youtube_cookie_cache[cache_key]
        
        # Check whether the cache entry exceeded max lifetime
        if time.time() - cache_entry['timestamp'] > LimitsConfig.COOKIE_CACHE_MAX_LIFETIME:
            logger.warning(f"Forcefully deactivating expired non-YouTube cookie cache {cache_key}")
            del _non_youtube_cookie_cache[cache_key]
        elif time.time() - cache_entry['timestamp'] < LimitsConfig.COOKIE_CACHE_DURATION:
            # Check whether a task is already active for this user
            if not cache_entry.get('active', False):
                # Ensure the cookie file still exists
                if cache_entry['cookie_path'] and os.path.exists(cache_entry['cookie_path']):
                    logger.info(f"Using cached cookie result for {cache_key}: {cache_entry['result']}")
                    return cache_entry
                else:
                    # Cookie file was removed; drop the cache entry
                    del _non_youtube_cookie_cache[cache_key]
            else:
                logger.info(f"Cookie validation task is already active for {cache_key}")
                return None
    
    return None

def clear_cookie_cache(user_id: int = None):
    """
    Clear cookie caches.
    
    Args:
        user_id (int, optional): User ID to clear for. If None, clears all caches.
    """
    global _non_youtube_cookie_cache, _youtube_cookie_cache, _active_cookie_tasks
    
    if user_id is None:
        _non_youtube_cookie_cache.clear()
        _youtube_cookie_cache.clear()
        _active_cookie_tasks.clear()
        logger.info("Cleared all cookie caches and active tasks")
    else:
        # Clear cache for a specific user
        keys_to_remove = [key for key in _non_youtube_cookie_cache.keys() if key.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del _non_youtube_cookie_cache[key]
        
        if user_id in _youtube_cookie_cache:
            del _youtube_cookie_cache[user_id]
        
        # Clear active tasks for the user
        tasks_to_remove = [task_id for task_id, task_info in _active_cookie_tasks.items() if task_info['user_id'] == user_id]
        for task_id in tasks_to_remove:
            del _active_cookie_tasks[task_id]
        
        logger.info(f"Cleared cookie cache and active tasks for user {user_id}")

def try_non_youtube_cookie_fallback(user_id: int, url: str, download_func, *args):
    """
    Try downloading with cookie rotation for non-YouTube sites.
    
    Args:
        user_id (int): User ID
        url (str): Download URL
        download_func: Download function
        *args: Extra arguments for the download function
        
    Returns:
        Download result, or None on failure
    """
    from CONFIG.limits import LimitsConfig
    
    # Clean expired tasks before checking
    cleanup_expired_tasks()
    
    # Start a new cookie validation task
    task_id = start_cookie_task(user_id, url, 'non_youtube')
    
    try:
        # 1) Try user cookies
        user_dir = os.path.join("users", str(user_id))
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        
        if os.path.exists(user_cookie_path):
            logger.info(f"Trying user cookies for non-YouTube URL: {url}")
            try:
                result = download_func(*args)
                if result is not None:
                    finish_cookie_task(task_id, True, user_cookie_path)
                    return result
            except Exception as e:
                logger.warning(f"User cookies failed for {url}: {e}")
        
        # 2) Try service cookies from config URLs
        service_name = get_service_name_from_url(url)
        if service_name:
            service_cookie_url = get_service_cookie_url(service_name)
            if service_cookie_url:
                logger.info(f"Trying service cookies for {service_name}: {url}")
                try:
                    ok, status, content, err = _download_content(service_cookie_url, timeout=30, user_id=user_id)
                    if ok and content:
                        # Save cookies to a temporary file
                        temp_cookie_path = os.path.join(user_dir, f"temp_{service_name}_cookie.txt")
                        with open(temp_cookie_path, "wb") as f:
                            f.write(content)
                        
                        try:
                            result = download_func(*args)
                            if result is not None:
                                finish_cookie_task(task_id, True, temp_cookie_path)
                                return result
                        except Exception as e:
                            logger.warning(f"Service cookies failed for {url}: {e}")
                        finally:
                            # Remove temporary file
                            if os.path.exists(temp_cookie_path):
                                os.remove(temp_cookie_path)
                except Exception as e:
                    logger.warning(f"Failed to download service cookies for {service_name}: {e}")
        
        # 3) Try global cookies
        global_cookie_path = Config.COOKIE_FILE_PATH
        if os.path.exists(global_cookie_path):
            logger.info(f"Trying global cookies for non-YouTube URL: {url}")
            try:
                result = download_func(*args)
                if result is not None:
                    finish_cookie_task(task_id, True, global_cookie_path)
                    return result
            except Exception as e:
                logger.warning(f"Global cookies failed for {url}: {e}")
        
        # 4) Try without cookies
        logger.info(f"Trying without cookies for non-YouTube URL: {url}")
        try:
            result = download_func(*args)
            if result is not None:
                finish_cookie_task(task_id, True, None)
                return result
        except Exception as e:
            logger.warning(f"Download without cookies failed for {url}: {e}")
        
        # All attempts failed
        finish_cookie_task(task_id, False)
        return None
        
    except Exception as e:
        logger.error(f"Cookie fallback error for {url}: {e}")
        finish_cookie_task(task_id, False)
        return None

def get_service_name_from_url(url: str) -> str | None:
    """
    Determine service name by URL.
    
    Args:
        url (str): URL to analyze
        
    Returns:
        str | None: Service name, or None
    """
    url_lower = url.lower()
    
    if 'instagram.com' in url_lower:
        return 'instagram'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'vk.com' in url_lower:
        return 'vk'
    elif 'facebook.com' in url_lower:
        return 'facebook'
    
    return None

def force_reset_youtube_cookie_sources(user_id: int = None):
    """
    Force-reset the checked-source cache for YouTube cookies.
    
    Args:
        user_id (int, optional): User ID to reset for. If None, resets for all users.
    """
    global _checked_cookie_sources
    
    if user_id is None:
        _checked_cookie_sources.clear()
        logger.info("Force reset checked cookie sources for all users")
    else:
        if user_id in _checked_cookie_sources:
            _checked_cookie_sources[user_id] = {'checked_sources': set(), 'last_reset': time.time()}
            logger.info(f"Force reset checked cookie sources for user {user_id}")
        else:
            logger.info(f"No checked cookie sources found for user {user_id}")

def get_checked_sources_status(user_id: int = None) -> dict:
    """
    Return the status of checked cookie sources.
    
    Args:
        user_id (int, optional): User ID. If None, returns status for all users.
        
    Returns:
        dict: Checked-source status
    """
    global _checked_cookie_sources
    
    if user_id is None:
        return {
            'total_users': len(_checked_cookie_sources),
            'users': {
                uid: {
                    'checked_count': len(data['checked_sources']),
                    'checked_sources': list(data['checked_sources']),
                    'last_reset': data.get('last_reset', 0)
                }
                for uid, data in _checked_cookie_sources.items()
            }
        }
    else:
        if user_id in _checked_cookie_sources:
            data = _checked_cookie_sources[user_id]
            return {
                'user_id': user_id,
                'checked_count': len(data['checked_sources']),
                'checked_sources': list(data['checked_sources']),
                'last_reset': data.get('last_reset', 0)
            }
        else:
            return {
                'user_id': user_id,
                'checked_count': 0,
                'checked_sources': [],
                'last_reset': 0
            }
