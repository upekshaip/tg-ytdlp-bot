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
from HELPERS.decorators import background_handler
from CONFIG.config import Config
from CONFIG.messages import Messages, get_messages_instance, safe_get_messages
from CONFIG.logger_msg import LoggerMsg

# Initialize messages for global use (will be overridden in functions)
# Note: This will be overridden in each function with proper user_id

# Get app instance
app = get_app()

def get_param_description(param_config, param_name, messages):
    """Get parameter description from messages using description_key"""
    description_key = param_config.get('description_key', f'ARGS_{param_name.upper()}_DESC_MSG')
    return getattr(messages, description_key, f'{param_name} description')

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
    messages = get_messages_instance(user_id)
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
    messages = get_messages_instance(user_id)
    """Start a 5-minute timer to auto-close input state"""
    def auto_close():
        messages = get_messages_instance(user_id)
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
            messages = get_messages_instance(user_id)
            safe_send_message(
                user_id,
                messages.ARGS_INPUT_TIMEOUT_MSG
            )
        except Exception as e:
            messages = get_messages_instance(user_id)
            logger.error(messages.ARGS_ERROR_SENDING_TIMEOUT_MSG.format(error=e))
    
    # Cancel existing timer if any
    if thread_id:
        existing_timer = input_state_timers_topic.get((user_id, thread_id))
        if existing_timer:
            existing_timer.cancel()
        timer = threading.Timer(300, auto_close)  # 5 minutes = 300 seconds
        input_state_timers_topic[(user_id, thread_id)] = timer
    else:
        existing_timer = input_state_timers_dm.get(user_id)
        if existing_timer:
            existing_timer.cancel()
        timer = threading.Timer(300, auto_close)  # 5 minutes = 300 seconds
        input_state_timers_dm[user_id] = timer
    
    timer.start()

# Available yt-dlp parameters with their types and options
# Note: descriptions will be loaded dynamically in functions
YTDLP_PARAMS = {
    "impersonate": {
        "type": "select",
        "description_key": "ARGS_IMPERSONATE_DESC_MSG",
        "options": ["chrome", "firefox", "safari", "edge", "opera"],
        "default": "chrome"
    },
    "referer": {
        "type": "text",
        "description_key": "ARGS_REFERER_DESC_MSG",
        "placeholder": "https://example.com",
        "default": "",
        "validation": "url"
    },
    "user_agent": {
        "type": "text", 
        "description_key": "ARGS_USER_AGENT_DESC_MSG",
        "placeholder": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "default": "",
        "validation": "text"
    },
    "geo_bypass": {
        "type": "boolean",
        "description_key": "ARGS_GEO_BYPASS_DESC_MSG",
        "default": True
    },
    "check_certificate": {
        "type": "boolean", 
        "description_key": "ARGS_CHECK_CERTIFICATE_DESC_MSG",
        "default": False
    },
    "live_from_start": {
        "type": "boolean",
        "description_key": "ARGS_LIVE_FROM_START_DESC_MSG",
        "default": True
    },
    "no_live_from_start": {
        "type": "boolean",
        "description_key": "ARGS_NO_LIVE_FROM_START_DESC_MSG",
        "default": False
    },
    "hls_use_mpegts": {
        "type": "boolean",
        "description_key": "ARGS_HLS_USE_MPEGTS_DESC_MSG",
        "default": True
    },
    "no_playlist": {
        "type": "boolean",
        "description_key": "ARGS_NO_PLAYLIST_DESC_MSG",
        "default": False
    },
    "no_part": {
        "type": "boolean",
        "description_key": "ARGS_NO_PART_DESC_MSG",
        "default": False
    },
    "no_continue": {
        "type": "boolean",
        "description_key": "ARGS_NO_CONTINUE_DESC_MSG",
        "default": False
    },
    "audio_format": {
        "type": "select",
        "description_key": "ARGS_AUDIO_FORMAT_DESC_MSG",
        "options": ["best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav", "alac", "ac3"],
        "default": "best"
    },
    "embed_metadata": {
        "type": "boolean",
        "description_key": "ARGS_EMBED_METADATA_DESC_MSG",
        "default": False
    },
    "embed_thumbnail": {
        "type": "boolean",
        "description_key": "ARGS_EMBED_THUMBNAIL_DESC_MSG",
        "default": False
    },
    "write_thumbnail": {
        "type": "boolean",
        "description_key": "ARGS_WRITE_THUMBNAIL_DESC_MSG",
        "default": False
    },
    "concurrent_fragments": {
        "type": "number",
        "description_key": "ARGS_CONCURRENT_FRAGMENTS_DESC_MSG",
        "placeholder": "1",
        "default": 1,
        "min": 1,
        "max": 16
    },
    "force_ipv4": {
        "type": "boolean",
        "description_key": "ARGS_FORCE_IPV4_DESC_MSG",
        "default": False
    },
    "force_ipv6": {
        "type": "boolean",
        "description_key": "ARGS_FORCE_IPV6_DESC_MSG",
        "default": False
    },
    "xff": {
        "type": "text",
        "description_key": "ARGS_XFF_DESC_MSG",
        "placeholder": "default, never, US, GB, DE, 192.168.1.0/24",
        "default": "default",
        "validation": "xff"
    },
    "http_chunk_size": {
        "type": "number",
        "description_key": "ARGS_HTTP_CHUNK_SIZE_DESC_MSG",
        "placeholder": "10485760",
        "default": 0,
        "min": 0,
        "max": 104857600
    },
    "sleep_subtitles": {
        "type": "number",
        "description_key": "ARGS_SLEEP_SUBTITLES_DESC_MSG",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 60
    },
    "legacy_server_connect": {
        "type": "boolean",
        "description_key": "ARGS_LEGACY_SERVER_CONNECT_DESC_MSG",
        "default": False
    },
    "no_check_certificates": {
        "type": "boolean",
        "description_key": "ARGS_NO_CHECK_CERTIFICATES_DESC_MSG",
        "default": False
    },
    "username": {
        "type": "text",
        "description_key": "ARGS_USERNAME_DESC_MSG",
        "placeholder": "your_username",
        "default": "",
        "validation": "text"
    },
    "password": {
        "type": "text",
        "description_key": "ARGS_PASSWORD_DESC_MSG",
        "placeholder": "your_password",
        "default": "",
        "validation": "text"
    },
    "twofactor": {
        "type": "text",
        "description_key": "ARGS_TWOFACTOR_DESC_MSG",
        "placeholder": "123456",
        "default": "",
        "validation": "text"
    },
    "ignore_errors": {
        "type": "boolean",
        "description_key": "ARGS_IGNORE_ERRORS_DESC_MSG",
        "default": False
    },
    "min_filesize": {
        "type": "number",
        "description_key": "ARGS_MIN_FILESIZE_DESC_MSG",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 10000
    },
    "max_filesize": {
        "type": "number",
        "description_key": "ARGS_MAX_FILESIZE_DESC_MSG",
        "placeholder": "0",
        "default": 0,
        "min": 0,
        "max": 10000
    },
    "playlist_items": {
        "type": "text",
        "description_key": "ARGS_PLAYLIST_ITEMS_DESC_MSG",
        "placeholder": "1,3,5",
        "default": "",
        "validation": "text"
    },
    "date": {
        "type": "text",
        "description_key": "ARGS_DATE_DESC_MSG",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "datebefore": {
        "type": "text",
        "description_key": "ARGS_DATEBEFORE_DESC_MSG",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "dateafter": {
        "type": "text",
        "description_key": "ARGS_DATEAFTER_DESC_MSG",
        "placeholder": "20230930",
        "default": "",
        "validation": "date"
    },
    "http_headers": {
        "type": "json",
        "description_key": "ARGS_HTTP_HEADERS_DESC_MSG",
        "placeholder": '{"Authorization": "Bearer token", "X-API-Key": "key123"}',
        "default": "{}",
        "validation": "json"
    },
    "sleep_interval": {
        "type": "number",
        "description_key": "ARGS_SLEEP_INTERVAL_DESC_MSG",
        "placeholder": "1",
        "default": 1,
        "min": 0,
        "max": 60
    },
    "max_sleep_interval": {
        "type": "number", 
        "description_key": "ARGS_MAX_SLEEP_INTERVAL_DESC_MSG",
        "placeholder": "5",
        "default": 5,
        "min": 0,
        "max": 300
    },
    "retries": {
        "type": "number",
        "description_key": "ARGS_RETRIES_DESC_MSG",
        "placeholder": "10",
        "default": 10,
        "min": 0,
        "max": 50
    },
    "video_format": {
        "type": "select",
        "description_key": "ARGS_VIDEO_FORMAT_DESC_MSG",
        "options": ["mp4", "webm", "mkv", "avi", "mov", "flv", "3gp", "ogv", "m4v", "wmv", "asf"],
        "default": "mp4"
    },
    "merge_output_format": {
        "type": "select",
        "description_key": "ARGS_MERGE_OUTPUT_FORMAT_DESC_MSG",
        "options": ["mp4", "webm", "mkv", "avi", "mov", "flv", "3gp", "ogv", "m4v", "wmv", "asf"],
        "default": "mp4"
    },
    "send_as_file": {
        "type": "boolean",
        "description_key": "ARGS_SEND_AS_FILE_DESC_MSG",
        "default": False
    }
}

def validate_input(value: str, param_name: str, user_id: int = None) -> tuple[bool, str]:
    """
    Validate user input based on parameter type and constraints
    Returns (is_valid, error_message)
    """
    messages = get_messages_instance(user_id)
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
            return False, messages.ARGS_INPUT_DANGEROUS_MSG.format(pattern=pattern)
    
    # Length check
    if len(value) > 1000:
        return False, messages.ARGS_INPUT_TOO_LONG_MSG
    
    # Type-specific validation
    if validation_type == "url":
        if value and not re.match(r'^https?://[^\s]+$', value):
            return False, messages.ARGS_INVALID_URL_MSG
    
    elif validation_type == "json":
        if value:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return False, messages.ARGS_INVALID_JSON_MSG
    
    elif validation_type == "number":
        try:
            num = float(value)
            min_val = param_config.get("min", 0)
            max_val = param_config.get("max", 999999)
            if num and num < min_val or num > max_val:
                return False, messages.ARGS_NUMBER_RANGE_MSG.format(min_val=min_val, max_val=max_val)
        except ValueError:
            return False, messages.ARGS_INVALID_NUMBER_MSG
    
    elif validation_type == "date":
        if value:
            # Validate YYYYMMDD format
            if not re.match(r'^\d{8}$', value):
                return False, messages.ARGS_DATE_FORMAT_MSG
            try:
                year = int(value[:4])
                month = int(value[4:6])
                day = int(value[6:8])
                if year and year < 1900 or year > 2100:
                    return False, messages.ARGS_YEAR_RANGE_MSG
                if month and month < 1 or month > 12:
                    return False, messages.ARGS_MONTH_RANGE_MSG
                if day and day < 1 or day > 31:
                    return False, messages.ARGS_DAY_RANGE_MSG
            except ValueError:
                return False, messages.ARGS_INVALID_DATE_MSG
    
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
            
            return False, messages.ARGS_INVALID_XFF_MSG
    
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
        logger.error(LoggerMsg.ARGS_ERROR_READING_USER_ARGS_LOG_MSG.format(user_id=user_id, error=e))
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
        logger.error(LoggerMsg.ARGS_ERROR_SAVING_USER_ARGS_LOG_MSG.format(user_id=user_id, error=e))
        return False

def get_args_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate main args menu keyboard with grouped parameters"""
    messages = get_messages_instance(user_id)
    user_args = get_user_args(user_id)
    
    # Short descriptions for better UI
    short_descriptions = {
        "impersonate": messages.ARGS_IMPERSONATE_SHORT_MSG,
        "referer": messages.ARGS_REFERER_SHORT_MSG,
        "geo_bypass": messages.ARGS_GEO_BYPASS_SHORT_MSG,
        "check_certificate": messages.ARGS_CHECK_CERTIFICATE_SHORT_MSG,
        "live_from_start": messages.ARGS_LIVE_FROM_START_SHORT_MSG,
        "no_live_from_start": messages.ARGS_NO_LIVE_FROM_START_SHORT_MSG,
        "user_agent": messages.ARGS_USER_AGENT_SHORT_MSG,
        "hls_use_mpegts": messages.ARGS_HLS_USE_MPEGTS_SHORT_MSG,
        "no_playlist": messages.ARGS_NO_PLAYLIST_SHORT_MSG,
        "no_part": messages.ARGS_NO_PART_SHORT_MSG,
        "no_continue": messages.ARGS_NO_CONTINUE_SHORT_MSG,
        "audio_format": messages.ARGS_AUDIO_FORMAT_SHORT_MSG,
        "embed_metadata": messages.ARGS_EMBED_METADATA_SHORT_MSG,
        "embed_thumbnail": messages.ARGS_EMBED_THUMBNAIL_SHORT_MSG,
        "write_thumbnail": messages.ARGS_WRITE_THUMBNAIL_SHORT_MSG,
        "concurrent_fragments": messages.ARGS_CONCURRENT_FRAGMENTS_SHORT_MSG,
        "force_ipv4": messages.ARGS_FORCE_IPV4_SHORT_MSG,
        "force_ipv6": messages.ARGS_FORCE_IPV6_SHORT_MSG,
        "xff": messages.ARGS_XFF_SHORT_MSG,
        "http_chunk_size": messages.ARGS_HTTP_CHUNK_SIZE_SHORT_MSG,
        "sleep_subtitles": messages.ARGS_SLEEP_SUBTITLES_SHORT_MSG,
        "legacy_server_connect": messages.ARGS_LEGACY_SERVER_CONNECT_SHORT_MSG,
        "no_check_certificates": messages.ARGS_NO_CHECK_CERTIFICATES_SHORT_MSG,
        "username": messages.ARGS_USERNAME_SHORT_MSG,
        "password": messages.ARGS_PASSWORD_SHORT_MSG,
        "twofactor": messages.ARGS_TWOFACTOR_SHORT_MSG,
        "ignore_errors": messages.ARGS_IGNORE_ERRORS_SHORT_MSG,
        "min_filesize": messages.ARGS_MIN_FILESIZE_SHORT_MSG,
        "max_filesize": messages.ARGS_MAX_FILESIZE_SHORT_MSG,
        "playlist_items": messages.ARGS_PLAYLIST_ITEMS_SHORT_MSG,
        "date": messages.ARGS_DATE_SHORT_MSG,
        "datebefore": messages.ARGS_DATEBEFORE_SHORT_MSG,
        "dateafter": messages.ARGS_DATEAFTER_SHORT_MSG,
        "http_headers": messages.ARGS_HTTP_HEADERS_SHORT_MSG,
        "sleep_interval": messages.ARGS_SLEEP_INTERVAL_SHORT_MSG,
        "max_sleep_interval": messages.ARGS_MAX_SLEEP_INTERVAL_SHORT_MSG,
        "video_format": messages.ARGS_VIDEO_FORMAT_SHORT_MSG,
        "merge_output_format": messages.ARGS_MERGE_OUTPUT_FORMAT_SHORT_MSG,
        "send_as_file": messages.ARGS_SEND_AS_FILE_SHORT_MSG
    }
    
    buttons = []
    
    # Group 1: Boolean parameters (True/False)
    boolean_params = []
    def _append_boolean_button(pname: str):
        messages = get_messages_instance(None)
        pconfig = YTDLP_PARAMS.get(pname)
        if not pconfig or pconfig.get("type") != "boolean":
            return
        current_value = user_args.get(pname, pconfig.get("default", False))
        status = messages.ARGS_STATUS_TRUE_MSG if current_value else messages.ARGS_STATUS_FALSE_MSG
        # Get description from messages using the key
        description_key = pconfig.get('description_key', f'ARGS_{pname.upper()}_DESC_MSG')
        description = getattr(messages, description_key, f'{pname} description')
        short_desc = short_descriptions.get(pname, description[:15])
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
            description = get_param_description(param_config, param_name, messages)
            short_desc = short_descriptions.get(param_name, description[:15])
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
                status = messages.ARGS_STATUS_TRUE_MSG if current_value else messages.ARGS_STATUS_FALSE_MSG
            else:
                status = f"🔢 {current_value}"
                display_value = str(current_value)
            
            description = get_param_description(param_config, param_name, messages)
            short_desc = short_descriptions.get(param_name, description[:15])
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
            
            description = get_param_description(param_config, param_name, messages)
            short_desc = short_descriptions.get(param_name, description[:15])
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
        InlineKeyboardButton(messages.ARGS_RESET_ALL_BUTTON_MSG, callback_data="args_reset_all"),
        InlineKeyboardButton(messages.ARGS_VIEW_CURRENT_BUTTON_MSG, callback_data="args_view_current")
    ])
    buttons.append([InlineKeyboardButton(messages.ARGS_CLOSE_BUTTON_MSG, callback_data="args_close")])
    
    return InlineKeyboardMarkup(buttons)

def get_boolean_menu_keyboard(param_name: str, current_value: bool, user_id: int = None) -> InlineKeyboardMarkup:
    """Generate boolean parameter menu keyboard"""
    messages = get_messages_instance(user_id)
    buttons = [
        [InlineKeyboardButton(
            messages.ARGS_TRUE_BUTTON_MSG,
            callback_data=f"args_bool_{param_name}_true"
        )],
        [InlineKeyboardButton(
            messages.ARGS_FALSE_BUTTON_MSG, 
            callback_data=f"args_bool_{param_name}_false"
        )],
        [InlineKeyboardButton(messages.ARGS_BACK_BUTTON_MSG, callback_data="args_back")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_select_menu_keyboard(param_name: str, current_value: str, user_id: int = None) -> InlineKeyboardMarkup:
    """Generate select parameter menu keyboard"""
    messages = get_messages_instance(user_id)
    param_config = YTDLP_PARAMS[param_name]
    options = param_config["options"]
    
    buttons = []
    for option in options:
        status = messages.ARGS_STATUS_SELECTED_MSG if option == current_value else messages.ARGS_STATUS_UNSELECTED_MSG
        buttons.append([InlineKeyboardButton(
            f"{status} {option}",
            callback_data=f"args_select_{param_name}_{option}"
        )])
    
    buttons.append([InlineKeyboardButton(messages.ARGS_BACK_BUTTON_MSG, callback_data="args_back")])
    return InlineKeyboardMarkup(buttons)

def get_text_input_message(param_name: str, current_value: str, user_id: int = None) -> str:
    """Generate text input message"""
    messages = get_messages_instance(user_id)
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "")
    
    description = get_param_description(param_config, param_name, messages)
    message = messages.ARGS_PARAM_DESCRIPTION_MSG.format(description=description)
    if current_value:
        message += messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    
    if param_name == "xff":
        message += messages.ARGS_XFF_EXAMPLES_MSG
        message += messages.ARGS_XFF_NOTE_MSG
    elif placeholder:
        message += messages.ARGS_EXAMPLE_MSG.format(placeholder=placeholder)
    
    message += messages.ARGS_SEND_VALUE_MSG
    
    return message

def get_number_input_message(param_name: str, current_value: Any, user_id: int = None) -> str:
    """Generate number input message"""
    messages = get_messages_instance(user_id)
    param_config = YTDLP_PARAMS[param_name]
    
    # Special handling for send_as_file parameter
    if param_name == "send_as_file":
        description = get_param_description(param_config, param_name, messages)
        message = f"<b>⚙️ {description}</b>\n\n"
        if current_value is not None:
            display_value = "True" if current_value else "False"
            message += f"Current value: <code>{display_value}</code>\n\n"
        message += messages.ARGS_BOOL_VALUE_REQUEST_MSG
        return message
    
    min_val = param_config.get("min", 0)
    max_val = param_config.get("max", 999999)
    
    description = get_param_description(param_config, param_name, messages)
    message = messages.ARGS_NUMBER_PARAM_MSG.format(description=description)
    if current_value is not None:
        message += messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    message += messages.ARGS_RANGE_MSG.format(min_val=min_val, max_val=max_val)
    message += messages.ARGS_SEND_NUMBER_MSG
    
    return message

def get_json_input_message(param_name: str, current_value: str, user_id: int = None) -> str:
    """Generate JSON input message"""
    messages = get_messages_instance(user_id)
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "{}")
    
    description = get_param_description(param_config, param_name, messages)
    message = messages.ARGS_JSON_PARAM_MSG.format(description=description)
    if current_value and current_value != "{}":
        message += messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)
    
    if param_name == "http_headers":
        message += messages.ARGS_HTTP_HEADERS_EXAMPLES_MSG.format(placeholder=placeholder)
        message += messages.ARGS_HTTP_HEADERS_NOTE_MSG
    else:
        message += messages.ARGS_EXAMPLE_MSG.format(placeholder=placeholder)
    
    message += messages.ARGS_JSON_VALUE_REQUEST_MSG
    
    return message

def format_current_args(user_args: Dict[str, Any], user_id: int = None) -> str:
    """Format current args for display with localized names"""
    messages = get_messages_instance(user_id)
    if not user_args:
        return messages.ARGS_NO_CUSTOM_MSG
    
    message = messages.ARGS_CURRENT_ARGS_MSG
    
    # Get localized parameter names based on user language
    display_names = get_localized_display_names(user_id)
    
    for param_name, value in user_args.items():
        display_name = display_names.get(param_name, param_name)
        
        if isinstance(value, bool):
            display_value = "✅ True" if value else "❌ False"
        elif isinstance(value, (int, float)):
            display_value = str(value)
        else:
            display_value = str(value) if value else "Not set"
        
        message += f"<b>{display_name}:</b> <code>{display_value}</code>\n"
    
    return message

def get_localized_display_names(user_id: int = None) -> Dict[str, str]:
    """Get localized parameter names for display based on user language"""
    messages = get_messages_instance(user_id)
    
    # Get language-specific parameter names
    if hasattr(messages, 'ARGS_PARAM_NAMES'):
        return messages.ARGS_PARAM_NAMES
    
    # Fallback to English if no localized names available
    return get_export_display_names()

def get_export_display_names() -> Dict[str, str]:
    """Get English parameter names for export (human-readable names)"""
    return {
        "force_ipv6": "Force IPv6 connections",
        "force_ipv4": "Force IPv4 connections", 
        "no_live_from_start": "Do not download live streams from start",
        "live_from_start": "Download live streams from start",
        "no_check_certificates": "Suppress HTTPS certificate validation",
        "check_certificate": "Check SSL certificate",
        "no_playlist": "Download only single video, not playlist",
        "embed_metadata": "Embed metadata in video file",
        "embed_thumbnail": "Embed thumbnail in video file",
        "write_thumbnail": "Write thumbnail to file",
        "ignore_errors": "Ignore download errors and continue",
        "legacy_server_connect": "Allow legacy server connections",
        "concurrent_fragments": "Number of concurrent fragments to download",
        "xff": "X-Forwarded-For header strategy",
        "user_agent": "User-Agent header",
        "impersonate": "Browser impersonation",
        "referer": "Referer header",
        "geo_bypass": "Bypass geographic restrictions",
        "hls_use_mpegts": "Use MPEG-TS for HLS",
        "no_part": "Do not use .part files",
        "no_continue": "Do not resume partial downloads",
        "audio_format": "Audio format",
        "video_format": "Video format",
        "merge_output_format": "Merge output format",
        "send_as_file": "Send as file",
        "username": "Username",
        "password": "Password",
        "twofactor": "Two-factor authentication code",
        "min_filesize": "Minimum file size (MB)",
        "max_filesize": "Maximum file size (MB)",
        "playlist_items": "Playlist items",
        "date": "Date",
        "datebefore": "Date before",
        "dateafter": "Date after",
        "http_headers": "HTTP headers",
        "sleep_interval": "Sleep interval",
        "max_sleep_interval": "Maximum sleep interval",
        "retries": "Number of retries",
        "http_chunk_size": "HTTP chunk size",
        "sleep_subtitles": "Sleep for subtitles"
    }

def get_localized_to_english_mapping() -> Dict[str, str]:
    """Get mapping from localized parameter names to English parameter names"""
    return {
        # New English mappings (from get_export_display_names)
        "Force IPv6 connections": "force_ipv6",
        "Force IPv4 connections": "force_ipv4",
        "Do not download live streams from start": "no_live_from_start",
        "Download live streams from start": "live_from_start",
        "Suppress HTTPS certificate validation": "no_check_certificates",
        "Check SSL certificate": "check_certificate",
        "Download only single video, not playlist": "no_playlist",
        "Embed metadata in video file": "embed_metadata",
        "Embed thumbnail in video file": "embed_thumbnail",
        "Write thumbnail to file": "write_thumbnail",
        "Ignore download errors and continue": "ignore_errors",
        "Allow legacy server connections": "legacy_server_connect",
        "Number of concurrent fragments to download": "concurrent_fragments",
        "X-Forwarded-For header strategy": "xff",
        "User-Agent header": "user_agent",
        "Browser impersonation": "impersonate",
        "Referer header": "referer",
        "Bypass geographic restrictions": "geo_bypass",
        "Use MPEG-TS for HLS": "hls_use_mpegts",
        "Do not use .part files": "no_part",
        "Do not resume partial downloads": "no_continue",
        "Audio format": "audio_format",
        "Video format": "video_format",
        "Merge output format": "merge_output_format",
        "Send as file": "send_as_file",
        "Username": "username",
        "Password": "password",
        "Two-factor authentication code": "twofactor",
        "Minimum file size (MB)": "min_filesize",
        "Maximum file size (MB)": "max_filesize",
        "Playlist items": "playlist_items",
        "Date": "date",
        "Date before": "datebefore",
        "Date after": "dateafter",
        "HTTP headers": "http_headers",
        "Sleep interval": "sleep_interval",
        "Maximum sleep interval": "max_sleep_interval",
        "Number of retries": "retries",
        "HTTP chunk size": "http_chunk_size",
        "Sleep for subtitles": "sleep_subtitles",
        
        # Old English mappings (for backward compatibility) - removed duplicates
        
        # Russian mappings (if any)
        "Разрешить устаревшие подключения к серверу": "legacy_server_connect",
        "Имитация браузера": "impersonate",
        "Проверить SSL сертификат": "check_certificate",
        "Не загружать прямые трансляции с начала": "no_live_from_start",
        "Загружать прямые трансляции с начала": "live_from_start",
        "Загружать только одно видео, не плейлист": "no_playlist",
        "Встроить метаданные в видеофайл": "embed_metadata",
        "Встроить миниатюру в видеофайл": "embed_thumbnail",
        "Принудительные IPv4 подключения": "force_ipv4",
        "Принудительные IPv6 подключения": "force_ipv6",
        "Игнорировать ошибки загрузки и продолжать": "ignore_errors",
        "Количество одновременных фрагментов для загрузки": "concurrent_fragments",
        "Подавить проверку HTTPS сертификата": "no_check_certificates",
        "Заголовок User-Agent": "user_agent",
        "Записать миниатюру в файл": "write_thumbnail",
        "Стратегия заголовка X-Forwarded-For": "xff",
        
        # Add more mappings as needed for other languages
    }

def create_export_message(user_args: Dict[str, Any], user_id: int = None) -> str:
    """Create export message for forwarding to favorites - always in English"""
    if not user_args:
        return "📋 Current yt-dlp Arguments:\n\nNo custom settings configured.\n\n---\n\n<i>Forward this message to your favorites to save these settings as a template.</i> \n\n<i>Forward this message back here to apply these settings.</i>"
    
    # Always use English header
    message = "📋 Current yt-dlp Arguments:\n\n"
    
    # Get English parameter names
    display_names = get_export_display_names()
    
    # Sort parameters for consistent display
    sorted_params = sorted(user_args.items(), key=lambda x: display_names.get(x[0], x[0]))
    
    for param_name, value in sorted_params:
        display_name = display_names.get(param_name, param_name)
        
        if isinstance(value, bool):
            status = "✅ True" if value else "❌ False"
        elif isinstance(value, (int, float)):
            status = str(value)
        else:
            status = str(value) if value else "Not set"
        
        # Make parameter names bold and values monospace
        message += f"<b>{display_name}:</b> <code>{status}</code>\n"
    
    # Always use English footer
    message += "\n---\n\n<i>Forward this message to your favorites to save these settings as a template.</i> \n\n<i>Forward this message back here to apply these settings.</i>"
    
    return message

def parse_import_message(text: str, user_id: int = None) -> Dict[str, Any]:
    """Parse settings from imported message text"""
    messages = get_messages_instance(user_id)
    
    if not text:
        logger.info(f"parse_import_message: No text provided")
        return {}
    
    # Check for args header in any supported language
    args_headers = [
        "📋 Current yt-dlp Arguments:",  # English
        "📋 Текущие аргументы yt-dlp:",  # Russian
        "📋 वर्तमान yt-dlp तर्क:",  # Hindi
        "📋 وسائط yt-dlp الحالية:",  # Arabic
    ]
    
    has_args_header = any(header in text for header in args_headers)
    
    if not has_args_header:
        logger.info(f"parse_import_message: No header found in text. Text: {text[:200] if text else 'None'}")
        return {}
    
    # For forwarded messages, try to extract the actual content
    # Look for the start of the settings section
    settings_start = -1
    for header in args_headers:
        if header in text:
            settings_start = text.find(header)
            break
    
    if settings_start == -1:
        logger.info(f"parse_import_message: Could not find settings start position")
        return {}
    
    # Extract the settings part, skipping any forwarded message metadata
    settings_text = text[settings_start:]
    
    # Remove any potential forwarded message metadata that might appear at the beginning
    lines = settings_text.split('\n')
    clean_lines = []
    in_settings = False
    
    for line in lines:
        line = line.strip()
        # Start processing when we find the header
        if any(header in line for header in args_headers):
            in_settings = True
            clean_lines.append(line)
        elif in_settings:
            # Stop if we hit a separator or instruction line
            if (line.startswith('---') or 
                'Forward this message' in line or 
                'Перешлите это сообщение' in line):
                break
            clean_lines.append(line)
    
    # Reconstruct the clean text
    clean_text = '\n'.join(clean_lines)
    logger.info(f"parse_import_message: Cleaned text length: {len(clean_text)}")
    logger.info(f"parse_import_message: Cleaned text preview: {clean_text[:200]}...")
    
    # Use the cleaned text for parsing
    text = clean_text
    
    # Get valid parameter names from YTDLP_PARAMS
    valid_params = set(YTDLP_PARAMS.keys())
    
    # Get mapping from localized names to English parameter names
    localized_mapping = get_localized_to_english_mapping()
    
    parsed_args = {}
    lines = text.split('\n')
    
    logger.info(f"parse_import_message: Processing {len(lines)} lines")
    
    for line in lines:
        line = line.strip()
        # Skip empty lines, headers, separators, and HTML tags
        if (not line or line.startswith('📋') or line.startswith('---') or 
            line.startswith('<i>') or line.startswith('Forward this message') or
            line.startswith('Перешлите это сообщение')):
            continue
            
        # Parse format: "Display Name: Value"
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                param_name = parts[0].strip()
                value_str = parts[1].strip()
                
                # Clean param name from potential HTML tags and extra whitespace
                import re
                param_name = re.sub(r'<[^>]+>', '', param_name).strip()
                # Remove any potential emoji or special characters that might interfere
                param_name = re.sub(r'^[^\w\s]+', '', param_name).strip()
                # Remove any potential forwarded message indicators
                param_name = re.sub(r'^[^\w\s]*', '', param_name).strip()
                # Clean value string as well
                value_str = re.sub(r'<[^>]+>', '', value_str).strip()
                
                logger.info(f"parse_import_message: Found line '{line}', param_name='{param_name}', value_str='{value_str}'")
                
                # Try to map localized name to English parameter name
                english_param_name = None
                if param_name in valid_params:
                    # Direct match with English parameter name
                    english_param_name = param_name
                    logger.info(f"parse_import_message: Direct match found: {param_name}")
                elif param_name in localized_mapping:
                    # Mapped from localized name
                    english_param_name = localized_mapping[param_name]
                    logger.info(f"parse_import_message: Mapped '{param_name}' -> '{english_param_name}'")
                else:
                    logger.info(f"parse_import_message: Unknown parameter '{param_name}', skipping")
                    continue
                
                # Check if the mapped parameter exists in YTDLP_PARAMS
                if english_param_name in valid_params:
                    param_config = YTDLP_PARAMS[english_param_name]
                    param_type = param_config.get("type", "text")
                    
                    # Clean value string from potential HTML tags
                    value_str = re.sub(r'<[^>]+>', '', value_str).strip()
                    
                    # Parse value based on type
                    if param_type == "boolean":
                        if value_str in ["✅ True", "True", "true", "1", "yes", "on", "✅"]:
                            parsed_args[english_param_name] = True
                            logger.info(f"parse_import_message: Set {english_param_name} = True")
                        elif value_str in ["❌ False", "False", "false", "0", "no", "off", "❌"]:
                            parsed_args[english_param_name] = False
                            logger.info(f"parse_import_message: Set {english_param_name} = False")
                    elif param_type == "number":
                        try:
                            # Extract number from string (handle cases like "16" or "Number: 16")
                            import re
                            numbers = re.findall(r'\d+', value_str)
                            if numbers:
                                num_value = int(numbers[0])
                                if english_param_name in ["min_filesize", "max_filesize"]:
                                    # These are in MB, convert to int
                                    parsed_args[english_param_name] = num_value
                                else:
                                    parsed_args[english_param_name] = num_value
                                logger.info(f"parse_import_message: Set {english_param_name} = {num_value}")
                        except ValueError:
                            continue
                    elif param_type in ["text", "json"]:
                        if value_str and value_str != "Not set":
                            parsed_args[english_param_name] = value_str
                            logger.info(f"parse_import_message: Set {english_param_name} = '{value_str}'")
                    elif param_type == "select":
                        if value_str and value_str != "Not set":
                            # Validate that the value is in the allowed options
                            options = param_config.get("options", [])
                            if value_str in options:
                                parsed_args[english_param_name] = value_str
                                logger.info(f"parse_import_message: Set {english_param_name} = '{value_str}'")
                else:
                    logger.info(f"parse_import_message: Mapped parameter '{english_param_name}' not found in YTDLP_PARAMS")
    
    logger.info(f"parse_import_message: Parsed {len(parsed_args)} arguments: {list(parsed_args.keys())}")
    return parsed_args

@app.on_message(filters.command("args"))
@background_handler(label="args_command")
def args_command(app, message):
    messages = get_messages_instance(message.chat.id)
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
    
    safe_send_message(
        chat_id,
        messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=messages.ARGS_MENU_DESCRIPTION_MSG),
        reply_markup=keyboard,
        message=message
    )

@app.on_callback_query(filters.regex("^args_"))
def args_callback_handler(app, callback_query):
    messages = get_messages_instance(callback_query.message.chat.id)
    """Handle args menu callbacks"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    try:
        if data == "args_close":
            callback_query.message.delete()
            callback_query.answer(messages.ARGS_CLOSED_MSG)
            return
        
        elif data == "args_empty":
            # Ignore separator buttons
            callback_query.answer()
            return
        
        elif data == "args_back":
            # Clear state and convert submenu back to main menu (edit current message)
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
                callback_query.edit_message_text(
                    messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=messages.ARGS_MENU_DESCRIPTION_MSG),
                    reply_markup=keyboard
                )
            except Exception:
                # If editing failed (deleted/invalid) — just ignore
                pass
            try:
                callback_query.answer()
            except Exception:
                pass
            return
        
        elif data == "args_view_current":
            user_args = get_user_args(user_id)
            message = format_current_args(user_args, user_id)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(messages.ARGS_EXPORT_SETTINGS_BUTTON_MSG, callback_data="args_export")],
                [InlineKeyboardButton(messages.ARGS_BACK_BUTTON_MSG, callback_data="args_back")]
            ])
            callback_query.edit_message_text(message, reply_markup=keyboard)
            callback_query.answer()
            return
        
        elif data == "args_export":
            user_args = get_user_args(user_id)
            export_message = create_export_message(user_args, user_id)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(messages.ARGS_BACK_BUTTON_MSG, callback_data="args_view_current")
            ]])
            callback_query.edit_message_text(export_message, reply_markup=keyboard)
            callback_query.answer(messages.ARGS_SETTINGS_READY_MSG)
            return
        
        elif data == "args_reset_all":
            if save_user_args(user_id, {}):
                keyboard = get_args_menu_keyboard(user_id)
                callback_query.edit_message_text(
                    messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=messages.ARGS_MENU_DESCRIPTION_MSG) + "\n\n" + messages.ARGS_RESET_SUCCESS_MSG,
                    reply_markup=keyboard
                )
                callback_query.answer(messages.ARGS_ALL_RESET_MSG)
            else:
                callback_query.answer(messages.ARGS_RESET_ERROR_MSG, show_alert=True)
            return
        
        elif data.startswith("args_set_"):
            param_name = data.replace("args_set_", "")
            if not param_name or param_name not in YTDLP_PARAMS:
                callback_query.answer(messages.ARGS_INVALID_PARAM_MSG, show_alert=True)
                return
            
            param_config = YTDLP_PARAMS[param_name]
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, param_config.get("default", ""))
            
            if param_config["type"] == "boolean" or param_name == "send_as_file":
                keyboard = get_boolean_menu_keyboard(param_name, current_value, user_id)
                display_value = messages.ARGS_STATUS_TRUE_DISPLAY_MSG if current_value else messages.ARGS_STATUS_FALSE_DISPLAY_MSG
                callback_query.edit_message_text(
                    f"<b>⚙️ {get_param_description(param_config, param_name, messages)}</b>\n\n"
                    f"{messages.ARGS_CURRENT_VALUE_MSG.format(current_value=display_value)}",
                    reply_markup=keyboard
                )
            
            elif param_config["type"] == "select":
                keyboard = get_select_menu_keyboard(param_name, current_value, user_id)
                display_value = f'<code>{current_value}</code>'
                callback_query.edit_message_text(
                    f"<b>⚙️ {get_param_description(param_config, param_name, messages)}</b>\n\n"
                    f"{messages.ARGS_CURRENT_VALUE_MSG.format(current_value=current_value)}",
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
                    message = get_text_input_message(param_name, current_value, user_id)
                elif param_config["type"] == "json":
                    message = get_json_input_message(param_name, current_value, user_id)
                else:  # number
                    message = get_number_input_message(param_name, current_value, user_id)
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(messages.ARGS_BACK_BUTTON_MSG, callback_data="args_back")
                ]])
                # For text/numeric/JSON parameters, replace current message with input prompt,
                # to avoid duplicating main menu.
                try:
                    callback_query.edit_message_text(
                        message,
                        reply_markup=keyboard
                    )
                except Exception:
                    # Fallback: if editing failed — send as reply in the same topic
                    safe_send_message(chat_id, message, reply_markup=keyboard, message=callback_query.message)
            
            return
        
        elif data.startswith("args_bool_"):
            # Parse: args_bool_{param_name}_{true/false}
            remaining = data.replace("args_bool_", "")
            if not remaining:
                callback_query.answer(messages.ARGS_INVALID_BOOL_MSG, show_alert=True)
                return
                
            value = None  # Initialize value
            if remaining.endswith("_true"):
                param_name = remaining[:-5]  # Remove "_true"
                value = True
            elif remaining.endswith("_false"):
                param_name = remaining[:-6]  # Remove "_false"
                value = False
            else:
                callback_query.answer(messages.ARGS_INVALID_BOOL_MSG, show_alert=True)
                return
            
            # Validate param_name exists in YTDLP_PARAMS
            if param_name not in YTDLP_PARAMS:
                callback_query.answer(messages.ARGS_INVALID_PARAM_MSG, show_alert=True)
                return
            
            # Ensure value is defined
            if value is None:
                callback_query.answer(messages.ARGS_INVALID_BOOL_MSG, show_alert=True)
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
                callback_query.edit_message_text(
                    messages.ARGS_CONFIG_TITLE_MSG.format(groups_msg=messages.ARGS_MENU_DESCRIPTION_MSG),
                    reply_markup=keyboard
                )
                try:
                    callback_query.answer(messages.ARGS_BOOL_SET_MSG.format(value='True' if value else 'False'))
                except Exception:
                    pass
            else:
                # Value is the same, just acknowledge
                try:
                    callback_query.answer(messages.ARGS_BOOL_ALREADY_SET_MSG.format(value='True' if value else 'False'))
                except Exception:
                    pass
            return
        
        elif data.startswith("args_select_"):
            # Parse: args_select_{param_name}_{value}
            remaining = data.replace("args_select_", "")
            if not remaining:
                callback_query.answer(messages.ARGS_INVALID_SELECT_MSG, show_alert=True)
                return
                
            # Find the last underscore to separate param_name and value
            last_underscore = remaining.rfind("_")
            if last_underscore == -1:
                callback_query.answer(messages.ARGS_INVALID_SELECT_MSG, show_alert=True)
                return
            param_name = remaining[:last_underscore]
            value = remaining[last_underscore + 1:]
            
            if not param_name or not value:
                callback_query.answer(messages.ARGS_INVALID_SELECT_MSG, show_alert=True)
                return
            
            # Validate param_name exists in YTDLP_PARAMS
            if param_name not in YTDLP_PARAMS:
                callback_query.answer(messages.ARGS_INVALID_PARAM_MSG, show_alert=True)
                return
            
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
                    f"<b>⚙️ {get_param_description(YTDLP_PARAMS[param_name], param_name, messages)}</b>\n\n"
                    f"{messages.ARGS_CURRENT_VALUE_MSG.format(current_value=value)}",
                    reply_markup=keyboard
                )
                try:
                    callback_query.answer(messages.ARGS_VALUE_SET_MSG.format(value=value))
                except Exception:
                    pass
            else:
                # Value is the same, just acknowledge
                try:
                    callback_query.answer(messages.ARGS_VALUE_ALREADY_SET_MSG.format(value=value))
                except Exception:
                    pass
            return
        
        else:
            # Unknown callback_data
            logger.warning(f"Unknown args callback_data: {data}")
            callback_query.answer(messages.ERROR_OCCURRED_SHORT_MSG, show_alert=False)
            return
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in args callback handler: {e}")
        logger.error(f"Callback data: {data}")
        logger.error(f"Traceback:\n{error_trace}")
        try:
            callback_query.answer(messages.ERROR_OCCURRED_SHORT_MSG, show_alert=False)
        except Exception:
            pass
        # Clear any input states to prevent further errors
        try:
            user_id = callback_query.from_user.id
            chat_id = callback_query.message.chat.id
            thread_id = getattr(callback_query.message, 'message_thread_id', None) or 0
            if thread_id:
                clear_input_state_timer(chat_id, thread_id)
            else:
                clear_input_state_timer(user_id)
        except Exception:
            pass

def handle_args_text_input(app, message):
    messages = get_messages_instance(message.chat.id)
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
                error_msg = messages.ARGS_TEXT_TOO_LONG_MSG
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
                    messages.ARGS_PARAM_SET_TO_MSG.format(description=get_param_description(YTDLP_PARAMS[param_name], param_name, messages), value=text),
                parse_mode=enums.ParseMode.HTML,
                message=message
            )
            
        elif param_type == "json":
            # Validate JSON input
            try:
                import json
                parsed_json = json.loads(text)
                if not isinstance(parsed_json, dict):
                    error_msg = messages.ARGS_JSON_MUST_BE_OBJECT_MSG
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
                    messages.ARGS_PARAM_SET_TO_MSG.format(description=get_param_description(YTDLP_PARAMS[param_name], param_name, messages), value=text),
                    parse_mode=enums.ParseMode.HTML,
                    message=message
                )
                
            except json.JSONDecodeError:
                error_msg = messages.ARGS_INVALID_JSON_FORMAT_MSG
                safe_send_message(user_id, error_msg, message=message)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
                
        elif param_type == "number":
            # Special handling for send_as_file parameter
            if param_name == "send_as_file":
                # Handle True/False input for send_as_file
                text_lower = text.lower().strip()
                if text_lower in ["true", "1", "yes", "on"]:
                    value = True
                elif text_lower in ["false", "0", "no", "off"]:
                    value = False
                else:
                    error_msg = messages.ARGS_BOOL_INPUT_MSG
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
                    messages.ARGS_PARAM_SET_TO_MSG.format(description=get_param_description(YTDLP_PARAMS[param_name], param_name, messages), value='True' if value else 'False'),
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
                    
                    if value and value < min_val or value > max_val:
                        safe_send_message(
                            user_id,
                            messages.ARGS_VALUE_MUST_BE_BETWEEN_MSG.format(min_val=min_val, max_val=max_val),
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
                        messages.ARGS_PARAM_SET_TO_MSG.format(description=get_param_description(YTDLP_PARAMS[param_name], param_name, messages), value=value),
                        parse_mode=enums.ParseMode.HTML,
                        message=message
                    )
                    
                except ValueError:
                    error_msg = messages.ARGS_INVALID_NUMBER_INPUT_MSG
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
                
    except Exception as e:
        logger.error(LoggerMsg.ARGS_ERROR_HANDLING_TEXT_INPUT_LOG_MSG.format(error=e))
        error_msg = messages.ARGS_ERROR_PROCESSING_MSG
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
@background_handler(label="args_text_handler")
def args_text_handler(app, message):
    """Handle text input for args configuration in same chat/topic using stored state"""
    try:
        handle_args_text_input(app, message)
    except Exception as e:
        logger.error(LoggerMsg.ARGS_CRITICAL_ERROR_LOG_MSG.format(error=e))

def args_import_handler(app, message):
    messages = get_messages_instance(message.chat.id)
    """Handle import of settings from forwarded message"""
    try:
        # Check if this is a forwarded message with settings template
        # Check for headers in all supported languages
        args_headers = [
            "📋 Current yt-dlp Arguments:",  # English
            "📋 Текущие аргументы yt-dlp:",  # Russian
            "📋 वर्तमान yt-dlp तर्क:",  # Hindi
            "📋 وسائط yt-dlp الحالية:",  # Arabic
        ]
        
        has_args_header = any(header in message.text for header in args_headers) if message.text else False
        
        if not message.text or not has_args_header:
            logger.info(f"args_import_handler: No text or header not found. Text: {message.text[:100] if message.text else 'None'}")
            return
        
        # Log that we're attempting to import settings
        logger.info(f"{LoggerMsg.ARGS_ATTEMPTING_IMPORT_SETTINGS_LOG_MSG}")
        logger.info(f"args_import_handler: Full message text: {message.text}")
        
        user_id = message.chat.id
        invoker_id = getattr(message, 'from_user', None).id if getattr(message, 'from_user', None) else user_id
        
        logger.info(f"args_import_handler: user_id={user_id}, invoker_id={invoker_id}")
        
        # Subscription check for non-admins
        if int(invoker_id) not in Config.ADMIN and not is_user_in_channel(app, message):
            logger.info(f"args_import_handler: User {invoker_id} not subscribed, skipping import")
            return  # is_user_in_channel already sends subscription message
        
        # Parse settings from message
        parsed_args = parse_import_message(message.text, invoker_id)
        logger.info(f"{LoggerMsg.ARGS_PARSED_SETTINGS_LOG_MSG}")
        logger.info(f"args_import_handler: Parsed {len(parsed_args)} settings: {list(parsed_args.keys())}")
        
        if not parsed_args:
            logger.info(f"args_import_handler: No settings parsed, sending failure message")
            safe_send_message(
                user_id,
                messages.ARGS_FAILED_RECOGNIZE_MSG,
                message=message
            )
            return
        
        # Apply mutual exclusivity for paired booleans
        if "check_certificate" in parsed_args and parsed_args["check_certificate"]:
            parsed_args["no_check_certificates"] = False
        elif "no_check_certificates" in parsed_args and parsed_args["no_check_certificates"]:
            parsed_args["check_certificate"] = False
            
        if "live_from_start" in parsed_args and parsed_args["live_from_start"]:
            parsed_args["no_live_from_start"] = False
        elif "no_live_from_start" in parsed_args and parsed_args["no_live_from_start"]:
            parsed_args["live_from_start"] = False
            
        if "force_ipv4" in parsed_args and parsed_args["force_ipv4"]:
            parsed_args["force_ipv6"] = False
        elif "force_ipv6" in parsed_args and parsed_args["force_ipv6"]:
            parsed_args["force_ipv4"] = False
        
        # Save imported settings
        if save_user_args(invoker_id, parsed_args):
            # Show success message with applied settings count
            applied_count = len(parsed_args)
            success_message = f"{messages.ARGS_SUCCESSFULLY_IMPORTED_MSG.format(applied_count=applied_count)}\n\n"
            
            # Show ALL settings that were applied (no truncation)
            all_settings = []
            for param_name, value in parsed_args.items():
                param_config = YTDLP_PARAMS.get(param_name, {})
                description = param_config.get("description", param_name)
                if isinstance(value, bool):
                    display_value = "✅" if value else "❌"
                else:
                    display_value = str(value)
                all_settings.append(f"• {description}: {display_value}")
            
            if all_settings:
                success_message += messages.ARGS_KEY_SETTINGS_MSG + "\n".join(all_settings)
            
            safe_send_message(
                user_id,
                success_message,
                message=message
            )
        else:
            safe_send_message(
                user_id,
                messages.ARGS_ERROR_SAVING_MSG,
                message=message
            )
            
    except Exception as e:
        logger.error(f"Error in args_import_handler: {e}")
        safe_send_message(
            message.chat.id,
            messages.ARGS_ERROR_IMPORTING_MSG,
            message=message
        )

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
                logger.info(f"{LoggerMsg.ARGS_SETTING_REFERER_LOG_MSG}")
        
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
                logger.info(f"{LoggerMsg.ARGS_USER_SELECTED_MERGE_OUTPUT_FORMAT_LOG_MSG}")
        
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
    messages = get_messages_instance(user_id)
    """Log the final yt-dlp options for debugging"""
    try:
        # Create a copy to avoid modifying the original
        opts_copy = ytdlp_opts.copy()
        
        # Remove sensitive information
        if 'cookiefile' in opts_copy:
            opts_copy['cookiefile'] = '[REDACTED]'
        
        # Recursive sanitization for JSON: functions/objects -> string
        def _sanitize(value):
            try:
                if isinstance(value, dict):
                    return {k: _sanitize(v) for k, v in value.items()}
                if isinstance(value, (list, tuple, set)):
                    return [ _sanitize(v) for v in value ]
                if callable(value):
                    return str(value)
                # Convert match_filter and similar objects to string
                value_str = str(value)
                # Keep simple types as is
                if isinstance(value, (str, int, float, bool)) or value is None:
                    return value
                # Replace unsupported types with string representation
                return value_str
            except Exception:
                try:
                    return str(value)
                except Exception:
                    return "<unserializable>"

        # Sanitize copy before JSON
        opts_sanitized = _sanitize(opts_copy)

        # Format the options nicely
        import json
        opts_str = json.dumps(opts_sanitized, indent=2, ensure_ascii=False)
        logger.info(LoggerMsg.ARGS_FINAL_YTDLP_OPTIONS_LOG_MSG.format(user_id=user_id, operation=operation, opts_str=opts_str))
        
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_ERROR_LOGGING_LOG_MSG.format(e=e))
