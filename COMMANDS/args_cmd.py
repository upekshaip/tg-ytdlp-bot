# ####################################################################################
# Args Command - Interactive yt-dlp parameters configuration
# ####################################################################################

import os
import json
import re
import threading
import time
from typing import Dict, Any, Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user, send_error_to_user
from HELPERS.limitter import check_user, is_user_in_channel
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config

# Get app instance
app = get_app()

# Global dictionaries to track user input states
# - For private chats: keyed by user_id (backward compatibility)
# - For groups with topics: keyed by (chat_id, thread_id)
user_input_states_dm = {}  # {user_id: {"param": param_name, "type": param_type}}
user_input_states_topic = {}  # {(chat_id, thread_id): {"param": param_name, "type": param_type}}
# Backward-compatibility alias for modules importing user_input_states (used in private chat flow)
user_input_states = user_input_states_dm

# Timers for auto-closing input states after 5 minutes
input_state_timers_dm = {}  # {user_id: timer_thread}
input_state_timers_topic = {}  # {(chat_id, thread_id): timer_thread}
# Flags to prevent duplicate timeout messages
timeout_sent_dm = set()  # {user_id}
timeout_sent_topic = set()  # {(chat_id, thread_id)}

# File to store user args settings
ARGS_FILE = "args.txt"

def clear_input_state_timer(user_id: int, thread_id: int = None):
    """Clear input state and its timer"""
    if thread_id:
        # Clear topic state
        user_input_states_topic.pop((user_id, thread_id), None)
        timer = input_state_timers_topic.pop((user_id, thread_id), None)
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass
        # Clear timeout flag
        timeout_sent_topic.discard((user_id, thread_id))
    else:
        # Clear DM state
        user_input_states_dm.pop(user_id, None)
        timer = input_state_timers_dm.pop(user_id, None)
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass
        # Clear timeout flag
        timeout_sent_dm.discard(user_id)

def start_input_state_timer(user_id: int, thread_id: int = None):
    """Start a 5-minute timer to auto-close input state"""
    def auto_close():
        time.sleep(300)  # 5 minutes = 300 seconds
        # Check if timer still exists (not cancelled)
        if thread_id:
            if (user_id, thread_id) not in input_state_timers_topic:
                return
            # Check if timeout message already sent
            if (user_id, thread_id) in timeout_sent_topic:
                return
            timeout_sent_topic.add((user_id, thread_id))
        else:
            if user_id not in input_state_timers_dm:
                return
            # Check if timeout message already sent
            if user_id in timeout_sent_dm:
                return
            timeout_sent_dm.add(user_id)
        
        clear_input_state_timer(user_id, thread_id)
        # Send notification to user only once
        try:
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                user_id,
                getattr(Messages, 'ARGS_INPUT_TIMEOUT_MSG', "⏰ Input mode automatically closed due to inactivity (5 minutes).")
            )
        except Exception as e:
            logger.error(f"Error sending timeout message: {e}")
    
    # Cancel existing timer if any
    if thread_id:
        existing_timer = input_state_timers_topic.get((user_id, thread_id))
        if existing_timer:
            existing_timer.cancel()
        timer = threading.Thread(target=auto_close, daemon=True)
        input_state_timers_topic[(user_id, thread_id)] = timer
    else:
        existing_timer = input_state_timers_dm.get(user_id)
        if existing_timer:
            existing_timer.cancel()
        timer = threading.Thread(target=auto_close, daemon=True)
        input_state_timers_dm[user_id] = timer
    
    timer.start()

# Available yt-dlp parameters with their types and options
YTDLP_PARAMS = {
    "impersonate": {
        "type": "select",
        "description": "Browser impersonation",
        "options": ["chrome", "firefox", "safari", "edge", "opera"],
        "default": "chrome"
    },
    "referer": {
        "type": "text",
        "description": "Referer header",
        "placeholder": "https://example.com",
        "default": "",
        "validation": "url"
    },
    "user_agent": {
        "type": "text", 
        "description": "User-Agent header",
        "placeholder": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "default": "",
        "validation": "text"
    },
    "geo_bypass": {
        "type": "boolean",
        "description": "Bypass geographic restrictions",
        "default": True
    },
    "check_certificate": {
        "type": "boolean", 
        "description": "Check SSL certificate",
        "default": False
    },
    "live_from_start": {
        "type": "boolean",
        "description": "Download live streams from start",
        "default": True
    },
    "no_live_from_start": {
        "type": "boolean",
        "description": "Do not download live streams from start",
        "default": False
    },
    "hls_use_mpegts": {
        "type": "boolean",
        "description": "Use MPEG-TS container for HLS videos",
        "default": True
    },
    "no_playlist": {
        "type": "boolean",
        "description": "Download only single video, not playlist",
        "default": False
    },
    "no_part": {
        "type": "boolean",
        "description": "Do not use .part files",
        "default": False
    },
    "no_continue": {
        "type": "boolean",
        "description": "Do not resume partial downloads",
        "default": False
    },
    "audio_format": {
        "type": "select",
        "description": "Audio format for extraction",
        "options": ["best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav", "alac", "ac3"],
        "default": "best"
    },
    "embed_metadata": {
        "type": "boolean",
        "description": "Embed metadata in video file",
        "default": False
    },
    "embed_thumbnail": {
        "type": "boolean",
        "description": "Embed thumbnail in video file",
        "default": False
    },
    "write_thumbnail": {
        "type": "boolean",
        "description": "Write thumbnail to file",
        "default": False
    },
    "concurrent_fragments": {
        "type": "number",
        "description": "Number of concurrent fragments to download",
        "placeholder": "1",
        "default": 1,
        "min": 1,
        "max": 16
    },
    "force_ipv4": {
        "type": "boolean",
        "description": "Force IPv4 connections",
        "default": False
    },
    "force_ipv6": {
        "type": "boolean",
        "description": "Force IPv6 connections",
        "default": False
    },
    "xff": {
        "type": "text",
        "description": "X-Forwarded-For header strategy",
        "placeholder": "default, never, US, GB, DE, 192.168.1.0/24",
        "default": "default",
        "validation": "xff"
    },
    "http_chunk_size": {
        "type": "number",
        "description": "HTTP chunk size (bytes)",
        "placeholder": "10485760",
        "default": 0,
        "min": 0,
        "max": 104857600
    },
    "sleep_subtitles": {
        "type": "number",
        "description": "Sleep before subtitle download (seconds)",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 60
    },
    "legacy_server_connect": {
        "type": "boolean",
        "description": "Allow legacy server connections",
        "default": False
    },
    "no_check_certificates": {
        "type": "boolean",
        "description": "Suppress HTTPS certificate validation",
        "default": False
    },
    "username": {
        "type": "text",
        "description": "Account username",
        "placeholder": "your_username",
        "default": "",
        "validation": "text"
    },
    "password": {
        "type": "text",
        "description": "Account password",
        "placeholder": "your_password",
        "default": "",
        "validation": "text"
    },
    "twofactor": {
        "type": "text",
        "description": "Two-factor authentication code",
        "placeholder": "123456",
        "default": "",
        "validation": "text"
    },
    "ignore_errors": {
        "type": "boolean",
        "description": "Ignore download errors and continue",
        "default": False
    },
    "min_filesize": {
        "type": "number",
        "description": "Minimum file size (MB)",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 10000
    },
    "max_filesize": {
        "type": "number",
        "description": "Maximum file size (MB)",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 10000
    },
    "playlist_items": {
        "type": "text",
        "description": "Playlist items to download (e.g., 1,3,5 or 1-5)",
        "placeholder": "1,3,5",
        "default": "",
        "validation": "text"
    },
    "date": {
        "type": "text",
        "description": "Download videos uploaded on this date (YYYYMMDD)",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "datebefore": {
        "type": "text",
        "description": "Download videos uploaded before this date (YYYYMMDD)",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "dateafter": {
        "type": "text",
        "description": "Download videos uploaded after this date (YYYYMMDD)",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "http_headers": {
        "type": "json",
        "description": "Custom HTTP headers (JSON)",
        "placeholder": '{"Authorization": "Bearer token", "X-API-Key": "key123"}',
        "default": "{}",
        "validation": "json"
    },
    "sleep_interval": {
        "type": "number",
        "description": "Sleep interval between requests (seconds)",
        "placeholder": "1",
        "default": 1,
        "min": 0,
        "max": 60
    },
    "max_sleep_interval": {
        "type": "number", 
        "description": "Maximum sleep interval (seconds)",
        "placeholder": "5",
        "default": 5,
        "min": 0,
        "max": 300
    },
    "retries": {
        "type": "number",
        "description": "Number of retries",
        "placeholder": "10",
        "default": 10,
        "min": 0,
        "max": 50
    },
    "video_format": {
        "type": "select",
        "description": "Video container format",
        "options": ["mp4", "webm", "mkv", "avi", "mov", "flv", "3gp", "ogv", "m4v", "wmv", "asf"],
        "default": "mp4"
    },
    "merge_output_format": {
        "type": "select",
        "description": "Output container format for merging",
        "options": ["mp4", "webm", "mkv", "avi", "mov", "flv", "3gp", "ogv", "m4v", "wmv", "asf"],
        "default": "mp4"
    },
    "send_as_file": {
        "type": "boolean",
        "description": "Send all media as document instead of media",
        "default": False
    }
}

def validate_input(value: str, param_name: str) -> tuple[bool, str]:
    """
    Validate user input based on parameter type and constraints
    Returns (is_valid, error_message)
    """
    param_config = YTDLP_PARAMS.get(param_name, {})
    validation_type = param_config.get("validation", "text")
    
    # Basic security checks - prevent SQL injection and other attacks
    dangerous_patterns = [
        r'[;\'"\\]',  # SQL injection patterns
        r'<script',   # XSS
        r'javascript:', # XSS
        r'data:',     # Data URI attacks
        r'vbscript:', # VBScript attacks
        r'<iframe',   # iframe injection
        r'<object',   # object injection
        r'<embed',    # embed injection
        r'<form',     # form injection
        r'<input',    # input injection
        r'<meta',     # meta injection
        r'<link',     # link injection
        r'<style',    # style injection
        r'<base',     # base injection
        r'<applet',   # applet injection
        r'<param',    # param injection
        r'<isindex',  # isindex injection
        r'<textarea', # textarea injection
        r'<select',   # select injection
        r'<option',   # option injection
        r'<button',   # button injection
        r'<fieldset', # fieldset injection
        r'<legend',   # legend injection
        r'<label',    # label injection
        r'<optgroup', # optgroup injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return False, f"❌ Input contains potentially dangerous content: {pattern}"
    
    # Length check
    if len(value) > 1000:
        return False, "❌ Input too long (max 1000 characters)"
    
    # Type-specific validation
    if validation_type == "url":
        if value and not re.match(r'^https?://[^\s]+$', value):
            return False, "❌ Invalid URL format. Must start with http:// or https://"
    
    elif validation_type == "json":
        if value:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return False, "❌ Invalid JSON format"
    
    elif validation_type == "number":
        try:
            num = float(value)
            min_val = param_config.get("min", 0)
            max_val = param_config.get("max", 999999)
            if num < min_val or num > max_val:
                return False, f"❌ Number must be between {min_val} and {max_val}"
        except ValueError:
            return False, "❌ Invalid number format"
    
    elif validation_type == "date":
        if value:
            # Validate YYYYMMDD format
            if not re.match(r'^\d{8}$', value):
                return False, "❌ Date must be in YYYYMMDD format (e.g., 20230930)"
            try:
                year = int(value[:4])
                month = int(value[4:6])
                day = int(value[6:8])
                if year < 1900 or year > 2100:
                    return False, "❌ Year must be between 1900 and 2100"
                if month < 1 or month > 12:
                    return False, "❌ Month must be between 01 and 12"
                if day < 1 or day > 31:
                    return False, "❌ Day must be between 01 and 31"
            except ValueError:
                return False, "❌ Invalid date format"
    
    elif validation_type == "xff":
        if value:
            # Validate X-Forwarded-For value
            if value.lower() in ["default", "never"]:
                return True, ""
            
            # Check if it's a country code (2 letters)
            if re.match(r'^[A-Z]{2}$', value.upper()):
                return True, ""
            
            # Check if it's an IP block in CIDR notation
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/\d{1,2})?$', value):
                return True, ""
            
            return False, "❌ XFF must be 'default', 'never', country code (e.g., US), or IP block (e.g., 192.168.1.0/24)"
    
    return True, ""

def get_user_args(user_id: int) -> Dict[str, Any]:
    """Get user's saved args settings"""
    user_dir = os.path.join("users", str(user_id))
    args_file = os.path.join(user_dir, ARGS_FILE)
    
    if not os.path.exists(args_file):
        return {}
    
    try:
        with open(args_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading user args for {user_id}: {e}")
        return {}

def save_user_args(user_id: int, args: Dict[str, Any]) -> bool:
    """Save user's args settings"""
    try:
        user_dir = os.path.join("users", str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        args_file = os.path.join(user_dir, ARGS_FILE)
        with open(args_file, 'w', encoding='utf-8') as f:
            json.dump(args, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving user args for {user_id}: {e}")
        return False

def get_args_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate main args menu keyboard with grouped parameters"""
    user_args = get_user_args(user_id)
    
    # Short descriptions for better UI
    short_descriptions = {
        "impersonate": "Impersonate",
        "referer": "Referer",
        "geo_bypass": "Geo Bypass",
        "check_certificate": "Check Cert",
        "live_from_start": "Live Start",
        "no_live_from_start": "No Live Start",
        "user_agent": "User Agent",
        "hls_use_mpegts": "HLS MPEG-TS",
        "no_playlist": "No Playlist",
        "no_part": "No Part",
        "no_continue": "No Continue",
        "audio_format": "Audio Format",
        "embed_metadata": "Embed Meta",
        "embed_thumbnail": "Embed Thumb",
        "write_thumbnail": "Write Thumb",
        "concurrent_fragments": "Concurrent",
        "force_ipv4": "Force IPv4",
        "force_ipv6": "Force IPv6",
        "xff": "XFF Header",
        "http_chunk_size": "Chunk Size",
        "sleep_subtitles": "Sleep Subs",
        "legacy_server_connect": "Legacy Connect",
        "no_check_certificates": "No Check Cert",
        "username": "Username",
        "password": "Password",
        "twofactor": "2FA",
        "ignore_errors": "Ignore Errors",
        "min_filesize": "Min Size",
        "max_filesize": "Max Size",
        "playlist_items": "Playlist Items",
        "date": "Date",
        "datebefore": "Date Before",
        "dateafter": "Date After",
        "http_headers": "HTTP Headers",
        "sleep_interval": "Sleep Interval",
        "max_sleep_interval": "Max Sleep",
        "video_format": "Video Format",
        "merge_output_format": "Merge Format",
        "send_as_file": "Send As File"
    }
    
    buttons = []
    
    # Group 1: Boolean parameters (True/False)
    boolean_params = []
    def _append_boolean_button(pname: str):
        pconfig = YTDLP_PARAMS.get(pname)
        if not pconfig or pconfig.get("type") != "boolean":
            return
        current_value = user_args.get(pname, pconfig.get("default", False))
        status = "✅" if current_value else "❌"
        short_desc = short_descriptions.get(pname, pconfig['description'][:15])
        btn_text = f"{status} {short_desc}"
        if len(btn_text) > 30:
            btn_text = f"{status} {short_desc[:25]}..."
        boolean_params.append(InlineKeyboardButton(btn_text, callback_data=f"args_set_{pname}"))

    # Ensure paired items stay together
    preferred_order = ["check_certificate", "no_check_certificates", "live_from_start", "no_live_from_start", "force_ipv4", "force_ipv6"]
    for pname in preferred_order:
        _append_boolean_button(pname)
    # Append the rest
    for pname, pconfig in YTDLP_PARAMS.items():
        if pconfig["type"] == "boolean" and pname not in preferred_order:
            _append_boolean_button(pname)
    
    # Add boolean parameters in rows of 2
    for i in range(0, len(boolean_params), 2):
        row = boolean_params[i:i+2]
        if len(row) == 1:
            row.append(InlineKeyboardButton("", callback_data="args_empty"))  # Empty button for alignment
        buttons.append(row)
    
    # Add separator
    buttons.append([InlineKeyboardButton("━━━━━━━━━━━━━━━━━━━━", callback_data="args_empty")])
    
    # Group 2: Select parameters (dropdown choices)
    select_params = []
    for param_name, param_config in YTDLP_PARAMS.items():
        if param_config["type"] == "select":
            current_value = user_args.get(param_name, param_config.get("default", ""))
            status = f"📋 {current_value}"
            short_desc = short_descriptions.get(param_name, param_config['description'][:15])
            button_text = f"{status} {short_desc}"
            if len(button_text) > 30:
                button_text = f"{status} {short_desc[:25]}..."
            
            select_params.append(InlineKeyboardButton(
                button_text,
                callback_data=f"args_set_{param_name}"
            ))
    
    # Add select parameters in rows of 2
    for i in range(0, len(select_params), 2):
        row = select_params[i:i+2]
        if len(row) == 1:
            row.append(InlineKeyboardButton("", callback_data="args_empty"))  # Empty button for alignment
        buttons.append(row)
    
    # Add separator
    buttons.append([InlineKeyboardButton("━━━━━━━━━━━━━━━━━━━━", callback_data="args_empty")])
    
    # Group 3: Numeric input parameters (require number input)
    numeric_params = []
    date_like_params = {"date", "datebefore", "dateafter"}
    for param_name, param_config in YTDLP_PARAMS.items():
        if param_config["type"] == "number" or param_name in date_like_params:
            current_value = user_args.get(param_name, param_config.get("default", ""))
            
            # Special handling for send_as_file parameter
            if param_name == "send_as_file":
                # Convert boolean to True/False display
                if isinstance(current_value, bool):
                    display_value = "True" if current_value else "False"
                else:
                    display_value = str(current_value)
                status = "✅" if current_value else "❌"
            else:
                status = f"🔢 {current_value}"
                display_value = str(current_value)
            
            short_desc = short_descriptions.get(param_name, param_config['description'][:15])
            button_text = f"{status} {short_desc}"
            if len(button_text) > 30:
                button_text = f"{status} {short_desc[:25]}..."
            
            numeric_params.append(InlineKeyboardButton(
                button_text,
                callback_data=f"args_set_{param_name}"
            ))
    
    # Add numeric parameters in rows of 2
    for i in range(0, len(numeric_params), 2):
        row = numeric_params[i:i+2]
        if len(row) == 1:
            row.append(InlineKeyboardButton("", callback_data="args_empty"))  # Empty button for alignment
        buttons.append(row)
    
    # Add separator
    buttons.append([InlineKeyboardButton("━━━━━━━━━━━━━━━━━━━━", callback_data="args_empty")])
    
    # Group 4: Text input parameters (require text/JSON input)
    text_params = []
    for param_name, param_config in YTDLP_PARAMS.items():
        if param_config["type"] in ["text", "json"] and param_name not in date_like_params:
            current_value = user_args.get(param_name, param_config.get("default", ""))
            if param_config["type"] == "text":
                status = "📝" if current_value else "📝"
            elif param_config["type"] == "json":
                status = "🔧" if current_value and current_value != "{}" else "🔧"
            
            short_desc = short_descriptions.get(param_name, param_config['description'][:15])
            button_text = f"{status} {short_desc}"
            if len(button_text) > 30:
                button_text = f"{status} {short_desc[:25]}..."
            
            text_params.append(InlineKeyboardButton(
                button_text,
                callback_data=f"args_set_{param_name}"
            ))
    
    # Add text parameters in rows of 2
    for i in range(0, len(text_params), 2):
        row = text_params[i:i+2]
        if len(row) == 1:
            row.append(InlineKeyboardButton("", callback_data="args_empty"))  # Empty button for alignment
        buttons.append(row)
    
    # Add separator
    buttons.append([InlineKeyboardButton("━━━━━━━━━━━━━━━━━━━━", callback_data="args_empty")])
    
    # Control buttons
    buttons.append([
        InlineKeyboardButton("🔄 Reset All", callback_data="args_reset_all"),
        InlineKeyboardButton("📋 View Current", callback_data="args_view_current")
    ])
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="args_close")])
    
    return InlineKeyboardMarkup(buttons)

def get_boolean_menu_keyboard(param_name: str, current_value: bool) -> InlineKeyboardMarkup:
    """Generate boolean parameter menu keyboard"""
    buttons = [
        [InlineKeyboardButton(
            "✅ True",
            callback_data=f"args_bool_{param_name}_true"
        )],
        [InlineKeyboardButton(
            "❌ False", 
            callback_data=f"args_bool_{param_name}_false"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data="args_back")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_select_menu_keyboard(param_name: str, current_value: str) -> InlineKeyboardMarkup:
    """Generate select parameter menu keyboard"""
    param_config = YTDLP_PARAMS[param_name]
    options = param_config["options"]
    
    buttons = []
    for option in options:
        status = "✅" if option == current_value else "⚪"
        buttons.append([InlineKeyboardButton(
            f"{status} {option}",
            callback_data=f"args_select_{param_name}_{option}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="args_back")])
    return InlineKeyboardMarkup(buttons)

def get_text_input_message(param_name: str, current_value: str) -> str:
    """Generate text input message"""
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "")
    
    from CONFIG.messages import MessagesConfig as Messages
    message = Messages.ARGS_PARAM_DESCRIPTION_MSG.format(description=param_config['description'])
    if current_value:
        message += Messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    
    if param_name == "xff":
        message += Messages.ARGS_XFF_EXAMPLES_MSG
        message += Messages.ARGS_XFF_NOTE_MSG
    elif placeholder:
        message += Messages.ARGS_EXAMPLE_MSG.format(placeholder=placeholder)
    
    message += Messages.ARGS_SEND_VALUE_MSG
    
    return message

def get_number_input_message(param_name: str, current_value: Any) -> str:
    """Generate number input message"""
    param_config = YTDLP_PARAMS[param_name]
    
    # Special handling for send_as_file parameter
    if param_name == "send_as_file":
        from CONFIG.messages import MessagesConfig as Messages
        message = f"<b>⚙️ {param_config['description']}</b>\n\n"
        if current_value is not None:
            display_value = "True" if current_value else "False"
            message += f"Current value: <code>{display_value}</code>\n\n"
        message += "Please send <code>True</code> or <code>False</code> to enable/disable this option."
        return message
    
    min_val = param_config.get("min", 0)
    max_val = param_config.get("max", 999999)
    
    from CONFIG.messages import MessagesConfig as Messages
    message = Messages.ARGS_NUMBER_PARAM_MSG.format(description=param_config['description'])
    if current_value is not None:
        message += Messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    message += Messages.ARGS_RANGE_MSG.format(min_val=min_val, max_val=max_val)
    message += Messages.ARGS_SEND_NUMBER_MSG
    
    return message

def get_json_input_message(param_name: str, current_value: str) -> str:
    """Generate JSON input message"""
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "{}")
    
    from CONFIG.messages import MessagesConfig as Messages
    message = Messages.ARGS_JSON_PARAM_MSG.format(description=param_config['description'])
    if current_value and current_value != "{}":
        message += Messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    
    if param_name == "http_headers":
        message += Messages.ARGS_HTTP_HEADERS_EXAMPLES_MSG.format(placeholder=placeholder)
        message += Messages.ARGS_HTTP_HEADERS_NOTE_MSG
    else:
        message += Messages.ARGS_EXAMPLE_MSG.format(placeholder=placeholder)
    
    message += "Please send valid JSON."
    
    return message

def format_current_args(user_args: Dict[str, Any]) -> str:
    """Format current args for display"""
    if not user_args:
        return "No custom arguments set. All parameters use default values."
    
    from CONFIG.messages import MessagesConfig as Messages
    message = Messages.ARGS_CURRENT_ARGS_MSG
    
    for param_name, value in user_args.items():
        param_config = YTDLP_PARAMS.get(param_name, {})
        description = param_config.get("description", param_name)
        
        if isinstance(value, bool):
            display_value = "✅ True" if value else "❌ False"
        elif isinstance(value, (int, float)):
            display_value = str(value)
        else:
            display_value = str(value) if value else "Not set"
        
        message += f"<b>{description}:</b> <code>{display_value}</code>\n"
    
    return message

@app.on_message(filters.command("args"))
def args_command(app, message):
    """Handle /args command"""
    chat_id = message.chat.id
    invoker_id = getattr(message, 'from_user', None).id if getattr(message, 'from_user', None) else chat_id
    
    # Subscription check for non-admins
    if int(invoker_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return  # is_user_in_channel already sends subscription message
    
    # Create user directory after subscription check
    user_dir = os.path.join("users", str(invoker_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    keyboard = get_args_menu_keyboard(invoker_id)
    
    from CONFIG.messages import MessagesConfig as Messages
    safe_send_message(
        chat_id,
        Messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=Messages.ARGS_MENU_DESCRIPTION_MSG),
        reply_markup=keyboard,
        message=message
    )

@app.on_callback_query(filters.regex("^args_"))
def args_callback_handler(app, callback_query):
    """Handle args menu callbacks"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    try:
        if data == "args_close":
            callback_query.message.delete()
            from CONFIG.messages import MessagesConfig as Messages
            callback_query.answer(Messages.ARGS_CLOSED_MSG)
            return
        
        elif data == "args_empty":
            # Ignore separator buttons
            callback_query.answer()
            return
        
        elif data == "args_back":
            # Очищаем состояние и превращаем подменю обратно в главное меню (редактируем текущее сообщение)
            try:
                chat_id = callback_query.message.chat.id
                thread_id = getattr(callback_query.message, 'message_thread_id', None) or 0
                if thread_id:
                    clear_input_state_timer(chat_id, thread_id)
                else:
                    clear_input_state_timer(callback_query.from_user.id)
            except Exception:
                pass
            keyboard = get_args_menu_keyboard(user_id)
            try:
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.edit_message_text(
                    Messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=Messages.ARGS_MENU_DESCRIPTION_MSG),
                    reply_markup=keyboard
                )
            except Exception:
                # Если не удалось отредактировать (удалено/невалидно) — просто игнор
                pass
            try:
                callback_query.answer()
            except Exception:
                pass
            return
        
        elif data == "args_view_current":
            user_args = get_user_args(user_id)
            message = format_current_args(user_args)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="args_back")
            ]])
            callback_query.edit_message_text(message, reply_markup=keyboard)
            callback_query.answer()
            return
        
        elif data == "args_reset_all":
            if save_user_args(user_id, {}):
                keyboard = get_args_menu_keyboard(user_id)
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.edit_message_text(
                    Messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=Messages.ARGS_MENU_DESCRIPTION_MSG) + "\n\n✅ All arguments reset to defaults.",
                    reply_markup=keyboard
                )
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.answer(Messages.ARGS_ALL_RESET_MSG)
            else:
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.answer(Messages.ARGS_RESET_ERROR_MSG, show_alert=True)
            return
        
        elif data.startswith("args_set_"):
            param_name = data.replace("args_set_", "")
            if param_name not in YTDLP_PARAMS:
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.answer(Messages.ARGS_INVALID_PARAM_MSG, show_alert=True)
                return
            
            param_config = YTDLP_PARAMS[param_name]
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, param_config.get("default", ""))
            
            if param_config["type"] == "boolean" or param_name == "send_as_file":
                keyboard = get_boolean_menu_keyboard(param_name, current_value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {param_config['description']}</b>\n\n"
                    f"Current value: {'✅ True' if current_value else '❌ False'}",
                    reply_markup=keyboard
                )
            
            elif param_config["type"] == "select":
                keyboard = get_select_menu_keyboard(param_name, current_value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {param_config['description']}</b>\n\n"
                    f"Current value: <code>{current_value}</code>",
                    reply_markup=keyboard
                )
            
            elif param_config["type"] in ["text", "json", "number"]:
                # Set user input state keyed by chat/topic (or DM by user_id)
                chat_id = callback_query.message.chat.id
                thread_id = getattr(callback_query.message, 'message_thread_id', None) or 0
                state = {"param": param_name, "type": param_config["type"]}
                if thread_id:
                    user_input_states_topic[(chat_id, thread_id)] = state
                    start_input_state_timer(chat_id, thread_id)
                else:
                    user_input_states_dm[callback_query.from_user.id] = state
                    start_input_state_timer(callback_query.from_user.id)
                
                if param_config["type"] == "text":
                    message = get_text_input_message(param_name, current_value)
                elif param_config["type"] == "json":
                    message = get_json_input_message(param_name, current_value)
                else:  # number
                    message = get_number_input_message(param_name, current_value)
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="args_back")
                ]])
                # Для текстовых/числовых/JSON параметров заменяем текущее сообщение на приглашение ввода,
                # чтобы не плодить дубликаты главного меню.
                try:
                    callback_query.edit_message_text(
                        message,
                        reply_markup=keyboard
                    )
                except Exception:
                    # Фоллбек: если редактирование не удалось — отправим как ответ в ту же тему
                    safe_send_message(chat_id, message, reply_markup=keyboard, message=callback_query.message)
            
            return
        
        elif data.startswith("args_bool_"):
            # Parse: args_bool_{param_name}_{true/false}
            remaining = data.replace("args_bool_", "")
            if remaining.endswith("_true"):
                param_name = remaining[:-5]  # Remove "_true"
                value = True
            elif remaining.endswith("_false"):
                param_name = remaining[:-6]  # Remove "_false"
                value = False
            else:
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.answer(Messages.ARGS_INVALID_BOOL_MSG, show_alert=True)
                return
            
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, YTDLP_PARAMS[param_name].get("default", False))
            
            # Save value and enforce mutual exclusivity for paired booleans
            user_args[param_name] = value
            # Enforce pairs: check_certificate vs no_check_certificates
            try:
                if param_name in ("check_certificate", "no_check_certificates"):
                    opposite = "no_check_certificates" if param_name == "check_certificate" else "check_certificate"
                    user_args[opposite] = (not value)
            except Exception:
                pass
            # Enforce pairs: live_from_start vs no_live_from_start
            try:
                if param_name in ("live_from_start", "no_live_from_start"):
                    opposite = "no_live_from_start" if param_name == "live_from_start" else "live_from_start"
                    user_args[opposite] = (not value)
            except Exception:
                pass
            # Enforce pairs: force_ipv4 vs force_ipv6
            try:
                if param_name in ("force_ipv4", "force_ipv6"):
                    opposite = "force_ipv6" if param_name == "force_ipv4" else "force_ipv4"
                    user_args[opposite] = (not value)
            except Exception:
                pass
            save_user_args(user_id, user_args)
            
            # Only update message if value actually changed
            if current_value != value:
                # Rebuild main menu to reflect paired toggles instantly
                keyboard = get_args_menu_keyboard(user_id)
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.edit_message_text(
                    Messages.ARGS_MENU_TEXT,
                    reply_markup=keyboard
                )
                try:
                    from CONFIG.messages import MessagesConfig as Messages
                    callback_query.answer(Messages.ARGS_BOOL_SET_MSG.format(value='True' if value else 'False'))
                except Exception:
                    pass
            else:
                # Value is the same, just acknowledge
                try:
                    from CONFIG.messages import MessagesConfig as Messages
                    callback_query.answer(Messages.ARGS_BOOL_ALREADY_SET_MSG.format(value='True' if value else 'False'))
                except Exception:
                    pass
            return
        
        elif data.startswith("args_select_"):
            # Parse: args_select_{param_name}_{value}
            remaining = data.replace("args_select_", "")
            # Find the last underscore to separate param_name and value
            last_underscore = remaining.rfind("_")
            if last_underscore == -1:
                from CONFIG.messages import MessagesConfig as Messages
                callback_query.answer(Messages.ARGS_INVALID_SELECT_MSG, show_alert=True)
                return
            param_name = remaining[:last_underscore]
            value = remaining[last_underscore + 1:]
            
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, YTDLP_PARAMS[param_name].get("default", ""))
            
            # Always save the value (even if it's the same)
            user_args[param_name] = value
            save_user_args(user_id, user_args)
            
            # Only update message if value actually changed
            if current_value != value:
                keyboard = get_select_menu_keyboard(param_name, value)
                # If we changed impersonate, it may affect headers; but keep same screen
                callback_query.edit_message_text(
                    f"<b>⚙️ {YTDLP_PARAMS[param_name]['description']}</b>\n\n"
                    f"Current value: <code>{value}</code>",
                    reply_markup=keyboard
                )
                try:
                    from CONFIG.messages import MessagesConfig as Messages
                    callback_query.answer(Messages.ARGS_VALUE_SET_MSG.format(value=value))
                except Exception:
                    pass
            else:
                # Value is the same, just acknowledge
                try:
                    from CONFIG.messages import MessagesConfig as Messages
                    callback_query.answer(Messages.ARGS_VALUE_ALREADY_SET_MSG.format(value=value))
                except Exception:
                    pass
            return
        
    except Exception as e:
        logger.error(f"Error in args callback handler: {e}")
        try:
            from CONFIG.messages import MessagesConfig as Messages
            callback_query.answer(Messages.ERROR_OCCURRED_SHORT_MSG, show_alert=False)
        except Exception:
            pass

def handle_args_text_input(app, message):
    """Handle text input for args parameters"""
    user_id = message.chat.id  # where to reply
    owner_id = getattr(message, 'from_user', None).id if getattr(message, 'from_user', None) else user_id  # whose settings to change
    text = message.text.strip()
    thread_id = getattr(message, 'message_thread_id', None) or 0
    # Try topic state first, then DM state
    state = None
    if thread_id and (user_id, thread_id) in user_input_states_topic:
        state = user_input_states_topic[(user_id, thread_id)]
    elif not thread_id and owner_id in user_input_states_dm:
        state = user_input_states_dm[owner_id]
    else:
        return
    param_name = state["param"]
    param_type = state["type"]
    
    try:
        # Validate and process input based on type
        if param_type == "text":
            # Basic validation for text input
            if len(text) > 500:
                error_msg = "❌ Text too long. Maximum 500 characters."
                safe_send_message(user_id, error_msg, message=message)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
            
            # Save the value
            user_args = get_user_args(owner_id)
            user_args[param_name] = text
            save_user_args(owner_id, user_args)
            
            # Clear state and show success
            clear_input_state_timer(user_id, thread_id)
            safe_send_message(
                user_id,
                f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{text}</code>",
                parse_mode=enums.ParseMode.HTML,
                message=message
            )
            
        elif param_type == "json":
            # Validate JSON input
            try:
                import json
                parsed_json = json.loads(text)
                if not isinstance(parsed_json, dict):
                    error_msg = "❌ JSON must be an object (dictionary)."
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
                
                # Save the value
                user_args = get_user_args(owner_id)
                user_args[param_name] = text
                save_user_args(owner_id, user_args)
                
                # Clear state and show success
                clear_input_state_timer(user_id, thread_id)
                safe_send_message(
                    user_id,
                    f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{text}</code>",
                    parse_mode=enums.ParseMode.HTML,
                    message=message
                )
                
            except json.JSONDecodeError:
                error_msg = "❌ Invalid JSON format. Please provide valid JSON."
                safe_send_message(user_id, error_msg, message=message)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
                
        elif param_type == "number":
            # Special handling for send_as_file parameter
            if param_name == "send_as_file":
                # Handle True/False input for send_as_file
                text_lower = text.lower().strip()
                if text_lower in ["true", "1", "yes", "on", "включено", "да"]:
                    value = True
                elif text_lower in ["false", "0", "no", "off", "выключено", "нет"]:
                    value = False
                else:
                    error_msg = "❌ Please enter 'True' or 'False' for Send As File option."
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
                
                # Save the value
                user_args = get_user_args(owner_id)
                user_args[param_name] = value
                save_user_args(owner_id, user_args)
                
                # Clear state and show success
                clear_input_state_timer(user_id, thread_id)
                safe_send_message(
                    user_id,
                    f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{'True' if value else 'False'}</code>",
                    parse_mode=enums.ParseMode.HTML,
                    message=message
                )
            else:
                # Validate number input for other parameters
                try:
                    value = int(text)
                    param_config = YTDLP_PARAMS[param_name]
                    min_val = param_config.get("min", 0)
                    max_val = param_config.get("max", 999999)
                    
                    if value < min_val or value > max_val:
                        safe_send_message(
                            user_id,
                            f"❌ Value must be between {min_val} and {max_val}.",
                            message=message
                        )
                        return
                    
                    # Save the value
                    user_args = get_user_args(owner_id)
                    user_args[param_name] = value
                    save_user_args(owner_id, user_args)
                    
                    # Clear state and show success
                    clear_input_state_timer(user_id, thread_id)
                    safe_send_message(
                        user_id,
                        f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{value}</code>",
                        parse_mode=enums.ParseMode.HTML,
                        message=message
                    )
                    
                except ValueError:
                    error_msg = "❌ Please provide a valid number."
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
                
    except Exception as e:
        logger.error(f"Error handling args text input: {e}")
        error_msg = "❌ Error processing input. Please try again."
        safe_send_message(user_id, error_msg, message=message)
        from HELPERS.logger import log_error_to_channel
        log_error_to_channel(message, error_msg)
        # Clear state on error
        clear_input_state_timer(user_id, thread_id)

def _has_args_state(flt, client, message) -> bool:
    try:
        chat_id = message.chat.id
        thread_id = getattr(message, 'message_thread_id', None) or 0
        if thread_id:
            return (chat_id, thread_id) in user_input_states_topic
        else:
            uid = getattr(message, 'from_user', None).id if getattr(message, 'from_user', None) else chat_id
            return uid in user_input_states_dm
    except Exception:
        return False

@app.on_message(filters.text & ~filters.regex(r'^/') & filters.create(_has_args_state))
def args_text_handler(app, message):
    """Handle text input for args configuration in same chat/topic using stored state"""
    try:
        handle_args_text_input(app, message)
    except Exception as e:
        logger.error(f"args_text_handler critical error: {e}")

def get_user_ytdlp_args(user_id: int, url: str = None) -> Dict[str, Any]:
    """Get user's yt-dlp arguments for use in download functions"""
    user_args = get_user_args(user_id)
    logger.info(f"User {user_id} args loaded: {user_args}")
    if not user_args:
        return {}
    
    # Convert user args to yt-dlp format
    ytdlp_args = {}
    
    # Priority parameters - these override other format settings
    if "video_format" in user_args:
        value = user_args["video_format"]
        if value and value != "mp4":
            # Use more flexible format selection with fallbacks
            if value == "webm":
                # For webm, use best available format and let FFmpeg convert to webm
                ytdlp_args["format"] = "best"
                logger.info(f"User {user_id} selected video_format=webm, using format=best for compatibility")
            else:
                ytdlp_args["format"] = f"best[ext={value}]/best[ext=mp4]/best"
                logger.info(f"User {user_id} selected video_format={value}, using format={ytdlp_args['format']}")
    
    for param_name, value in user_args.items():
        if param_name == "impersonate":
            ytdlp_args["extractor_args"] = ytdlp_args.get("extractor_args", {})
            ytdlp_args["extractor_args"]["generic"] = {"impersonate": [value]}
        
        elif param_name == "referer":
            if value:
                # For all services, use both http_headers and referer for maximum compatibility
                ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                ytdlp_args["http_headers"]["Referer"] = value
                ytdlp_args["referer"] = value
                logger.info(f"Setting Referer for all services: {value}")
        
        elif param_name == "user_agent":
            if value:
                ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                ytdlp_args["http_headers"]["User-Agent"] = value
        
        elif param_name == "http_headers":
            if value and value != "{}":
                try:
                    custom_headers = json.loads(value)
                    ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                    ytdlp_args["http_headers"].update(custom_headers)
                except json.JSONDecodeError:
                    pass
        
        elif param_name in ["geo_bypass", "check_certificate", "live_from_start", "no_live_from_start", "hls_use_mpegts", 
                           "no_playlist", "no_part", "no_continue", "embed_metadata", "embed_thumbnail", 
                           "write_thumbnail", "force_ipv4", "force_ipv6", "legacy_server_connect", 
                           "no_check_certificates", "ignore_errors"]:
            ytdlp_args[param_name] = value
        
        elif param_name == "audio_format":
            if value and value != "best":
                ytdlp_args["audio_format"] = value
        
        elif param_name == "merge_output_format":
            if value and value != "mp4":
                ytdlp_args["merge_output_format"] = value
                logger.info(f"User {user_id} selected merge_output_format={value}")
        
        elif param_name == "format":
            # Handle format parameter (including id: format) - only if video_format not set
            if value and "format" not in ytdlp_args:
                ytdlp_args["format"] = value
        
        elif param_name in ["sleep_interval", "max_sleep_interval", "retries", "concurrent_fragments", 
                           "http_chunk_size", "sleep_subtitles"]:
            ytdlp_args[param_name] = int(value)
        
        elif param_name == "xff":
            if value and value != "default":
                ytdlp_args["xff"] = value
        
        elif param_name in ["username", "password", "twofactor"]:
            if value:
                ytdlp_args[param_name] = value
        
        elif param_name in ["min_filesize", "max_filesize"]:
            if value and value > 0:
                # Convert MB to bytes
                ytdlp_args[param_name] = int(value * 1024 * 1024)
        
        elif param_name == "playlist_items":
            if value:
                ytdlp_args["playlist_items"] = value
        
        elif param_name in ["date", "datebefore", "dateafter"]:
            if value:
                ytdlp_args[param_name] = value
        
        elif param_name == "send_as_file":
            # This parameter is handled in the sender functions, not in yt-dlp
            # We'll store it in user_args but not pass to yt-dlp
            ytdlp_args[param_name] = value
    
    logger.info(f"User {user_id} final ytdlp_args: {ytdlp_args}")
    return ytdlp_args

def log_ytdlp_options(user_id: int, ytdlp_opts: dict, operation: str = "download"):
    """Log the final yt-dlp options for debugging"""
    try:
        # Create a copy to avoid modifying the original
        opts_copy = ytdlp_opts.copy()
        
        # Remove sensitive information
        if 'cookiefile' in opts_copy:
            opts_copy['cookiefile'] = '[REDACTED]'
        
        # Рекурсивная санитизация для JSON: функции/объекты -> строка
        def _sanitize(value):
            try:
                if isinstance(value, dict):
                    return {k: _sanitize(v) for k, v in value.items()}
                if isinstance(value, (list, tuple, set)):
                    return [ _sanitize(v) for v in value ]
                if callable(value):
                    return str(value)
                # Приводим match_filter и подобные объекты к строке
                value_str = str(value)
                # Простые типы оставляем как есть
                if isinstance(value, (str, int, float, bool)) or value is None:
                    return value
                # Неподдерживаемые типы заменяем строкой-представлением
                return value_str
            except Exception:
                try:
                    return str(value)
                except Exception:
                    return "<unserializable>"

        # Санитизируем копию перед JSON
        opts_sanitized = _sanitize(opts_copy)

        # Format the options nicely
        import json
        opts_str = json.dumps(opts_sanitized, indent=2, ensure_ascii=False)
        logger.info(f"User {user_id} - Final yt-dlp options for {operation}:\n{opts_str}")
        
    except Exception as e:
        logger.error(f"Error logging yt-dlp options: {e}")
