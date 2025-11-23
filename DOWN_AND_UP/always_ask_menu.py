# --- Callback Processor ---
import os
import hashlib
import re
from datetime import datetime
import json
from pyrogram import filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters, WebAppInfo
import requests

def safe_callback_answer(callback_query, text, show_alert=False):
    """Safely answer callback query, handling QueryIdInvalid errors"""
    try:
        callback_query.answer(text, show_alert=show_alert)
    except Exception:
        pass  # Query ID might be invalid after long operation

from HELPERS.app_instance import get_app
from HELPERS.decorators import get_main_reply_keyboard
from HELPERS.logger import send_to_logger, logger, send_error_to_user, log_error_to_channel
from HELPERS.safe_messeger import safe_send_message, safe_delete_messages
from CONFIG.logger_msg import LoggerMsg
from HELPERS.filesystem_hlp import create_directory
from HELPERS.qualifier import get_quality_by_min_side, get_real_height_for_quality
from HELPERS.limitter import check_subs_limits, check_playlist_range_limits, TimeFormatter

from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from URL_PARSERS.tags import extract_url_range_tags

from COMMANDS.subtitles_cmd import (
    clear_subs_check_cache, is_subs_enabled, check_subs_availability, 
    get_user_subs_auto_mode, download_subtitles_only, get_user_subs_language, _subs_check_cache,
    LANGUAGES, get_language_keyboard, is_subs_always_ask, save_subs_always_ask,
    get_language_keyboard_always_ask, get_available_subs_languages, get_flag,
    save_user_subs_language, save_user_subs_auto_mode,
)
from COMMANDS.split_sizer import get_user_split_size
from COMMANDS.nsfw_cmd import should_apply_spoiler

from DATABASE.cache_db import (
    get_cached_qualities, get_cached_playlist_count, get_cached_playlist_videos, 
    get_cached_playlist_qualities, save_to_video_cache, get_cached_message_ids
)

from DOWN_AND_UP.yt_dlp_hook import get_video_formats
from HELPERS.pot_helper import build_cli_extractor_args
from COMMANDS.format_cmd import set_session_mkv_override
from DOWN_AND_UP.down_and_audio import down_and_audio
from DOWN_AND_UP.down_and_up import down_and_up

from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.tags import generate_final_tags, extract_url_range_tags
from URL_PARSERS.youtube import is_youtube_url, download_thumbnail, youtube_to_piped_url
from URL_PARSERS.tiktok import is_tiktok_url
from URL_PARSERS.normalizer import get_clean_playlist_url
from URL_PARSERS.embedder import transform_to_embed_url, is_instagram_url, is_twitter_url, is_reddit_url
from URL_PARSERS.thumbnail_downloader import download_thumbnail as download_universal_thumbnail

# Import function to get user args
def get_user_args(user_id: int):
    """Get user's saved args settings"""
    import os
    import json
    user_dir = os.path.join("users", str(user_id))
    args_file = os.path.join(user_dir, "args.txt")
    
    if not os.path.exists(args_file):
        return {}
    
    try:
        with open(args_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(LoggerMsg.ALWAYS_ASK_ERROR_READING_USER_ARGS_LOG_MSG.format(user_id=user_id, error=e))
        return {}
from COMMANDS.image_cmd import image_command
from HELPERS.safe_messeger import fake_message

# Get app instance for decorators
app = get_app()

# Proxy functionality is now handled by COMMANDS.proxy_cmd
logger.info(LoggerMsg.ALWAYS_ASK_IMPORTED_LOG_MSG.format(app_available=app is not None))

def format_filesize(size_str):
    """Convert filesize to shortest readable format (kb, mb, gb)"""
    if not size_str or size_str in ['unknown', 'none', '|', '≈']:
        return None
    
    # Only process KiB, MiB, GiB formats
    import re
    if not re.match(r'^\d+\.?\d*(KiB|MiB|GiB)$', size_str, re.IGNORECASE):
        return None
    
    # Remove any non-numeric characters except decimal point
    clean_size = re.sub(r'[^\d.]', '', size_str)
    
    try:
        size = float(clean_size)
    except ValueError:
        return None
    
    # Determine the original unit from the original string
    original_str = size_str.lower()
    if 'kib' in original_str:
        unit_multiplier = 1024
    elif 'mib' in original_str:
        unit_multiplier = 1024 * 1024
    elif 'gib' in original_str:
        unit_multiplier = 1024 * 1024 * 1024
    else:
        return None  # Only process KiB/MiB/GiB
    
    # Convert to bytes
    bytes_size = size * unit_multiplier
    
    # Convert to shortest readable format
    if bytes_size and bytes_size >= 1024 * 1024 * 1024:  # GB
        return f"{bytes_size / (1024 * 1024 * 1024):.0f}gb"
    elif bytes_size and bytes_size >= 1024 * 1024:  # MB
        return f"{bytes_size / (1024 * 1024):.0f}mb"
    elif bytes_size and bytes_size >= 1024:  # KB
        return f"{bytes_size / 1024:.0f}kb"
    else:
        return f"{bytes_size:.0f}b"

def create_safe_callback_data(prefix, data, max_length=50):
    """Create safe callback_data that doesn't exceed Telegram's 64-byte limit"""
    import hashlib
    
    # Calculate total length including prefix and separators
    full_data = f"{prefix}|{data}"
    
    if len(full_data) <= 64:
        return full_data
    
    # If too long, use hash
    data_hash = hashlib.md5(data.encode()).hexdigest()[:16]
    safe_callback = f"{prefix}|{data_hash}"
    
    # Store mapping for later retrieval
    mapping_attr = f"_{prefix.replace('|', '_')}_mapping"
    if not hasattr(create_safe_callback_data, mapping_attr):
        setattr(create_safe_callback_data, mapping_attr, {})
    
    mapping = getattr(create_safe_callback_data, mapping_attr)
    mapping[data_hash] = data
    setattr(create_safe_callback_data, mapping_attr, mapping)
    
    return safe_callback

def get_original_data_from_callback(prefix, callback_data):
    """Get original data from safe callback_data using mapping"""
    try:
        data_hash = callback_data.replace(f"{prefix}|", "")
        mapping_attr = f"_{prefix.replace('|', '_')}_mapping"
        
        logger.info(f"Looking for data_hash '{data_hash}' in mapping_attr '{mapping_attr}'")
        
        if hasattr(create_safe_callback_data, mapping_attr):
            mapping = getattr(create_safe_callback_data, mapping_attr)
            logger.info(f"Mapping found: {mapping}")
            result = mapping.get(data_hash, data_hash)  # Return original data or hash if not found
            logger.info(f"Retrieved result: '{result}'")
            return result
        else:
            logger.warning(f"Mapping attribute '{mapping_attr}' not found")
    except Exception as e:
        logger.warning(LoggerMsg.ALWAYS_ASK_ERROR_RETRIEVING_CALLBACK_LOG_MSG.format(error=e))
    
    fallback = callback_data.replace(f"{prefix}|", "")
    logger.info(f"Using fallback: '{fallback}'")
    return fallback

def extract_button_data(format_line):
    """Extract only needed data for button display from complete format line"""
    parts = format_line.split()
    button_parts = []
    
    # Media extensions to look for (popular formats only)
    media_extensions = ['mp4', 'webm', 'm4a', 'mkv', 'avi', 'mov', 'flv', 'wmv', '3gp', 'ogv', 'ts', 'mts', 'm2ts', 'mp3', 'ogg', 'm3u8', 'f4v', 'm4v', 'm4p', 'm4b', 'm4r', '3g2', '3gpp', '3gpp2', 'asf', 'divx', 'xvid', 'rm', 'rmvb', 'vob', 'vcd', 'svcd', 'dvd', 'iso', 'sub', 'idx', 'srt', 'ssa', 'ass', 'vtt', 'smi', 'sami', 'rt', 'txt', 'lrc', 'vobsub', 'dvdsub', 'pgs', 'dvb', 'hdmv', 'pcm', 'wav', 'aiff', 'wma', 'ape', 'flac', 'alac', 'aac', 'ac3', 'dts', 'dtshd', 'truehd', 'eac3', 'mp2', 'opus', 'vorbis', 'speex', 'amr', 'awb', 'gsm', 'amrnb', 'amrwb']
    
    # Codec patterns to look for (popular codecs only)
    codec_patterns = ['avc', 'vp9', 'av1', 'h264', 'h265', 'hevc', 'avc1', 'vp09', 'av01', 'opus', 'aac', 'ac3', 'dts', 'mp3', 'wav', 'flac', 'alac', 'vorbis', 'speex', 'amr', 'gsm', 'amrnb', 'amrwb', 'mp2', 'eac3', 'truehd', 'dtshd', 'pcm', 'aiff', 'wma', 'ape', 'ogg', 'm4a', 'm4b', 'm4p', 'm4r', 'f4a', 'f4b', 'f4p', 'f4v', '3g2', '3gpp', '3gpp2', 'asf', 'divx', 'xvid', 'rm', 'rmvb', 'vob', 'vcd', 'svcd', 'dvd', 'sub', 'idx', 'srt', 'ssa', 'ass', 'vtt', 'smi', 'sami', 'rt', 'txt', 'lrc', 'vobsub', 'dvdsub', 'pgs', 'dvb', 'hdmv']
    
    # Extract all possible data from format line
    all_extracted = []
    
    for part in parts:
        part = part.strip()
        
        # Skip empty or invalid parts
        if not part or part in ['unknown', 'none', '|', '≈'] or len(part) == 1 and part.isdigit():
            continue
        
        # Check for media extension
        if part.lower() in media_extensions:
            all_extracted.append(part)
            continue
        
        # Check for resolution pattern (WxH)
        if 'x' in part and part.replace('x', '').replace('p', '').isdigit():
            all_extracted.append(part)
            continue
        
        # Check for filesize pattern (only KiB/MiB/GiB)
        import re
        if re.match(r'^\d+\.?\d*(KiB|MiB|GiB)$', part, re.IGNORECASE):
            formatted_size = format_filesize(part)
            if formatted_size:
                all_extracted.append(formatted_size)
            continue
        
        # Check for quality pattern (e.g., 144p, 720p60, 1080p60)
        if re.match(r'^\d+p\d*$', part):
            all_extracted.append(part)
            continue
        
        # Extract quality from format names (e.g., h264_540p_389369-0 -> 540p)
        quality_match = re.search(r'(\d+p\d*)', part)
        if quality_match:
            all_extracted.append(quality_match.group(1))
            continue
        
        # Check for video codec patterns
        if any(codec in part.lower() for codec in codec_patterns):
            # Shorten video codec names
            if part.startswith('avc1'):
                part = 'avc1'
            elif part.startswith('vp9'):
                part = 'vp9'
            elif part.startswith('vp09'):
                part = 'vp9'
            elif part.startswith('av1'):
                part = 'av1'
            elif part.startswith('av01'):
                part = 'av1'
            all_extracted.append(part)
            continue
        
        # Check for audio indicator
        if part.lower() == 'audio':
            all_extracted.append('audio')
            continue
    
    # Extract data from format names (first part of the line)
    format_name = parts[0] if parts else ""
    
    # Replace url360, url240, etc. with 360p, 240p, etc.
    url_quality_match = re.search(r'url(\d+)', format_name, re.IGNORECASE)
    if url_quality_match:
        quality = url_quality_match.group(1) + 'p'
        all_extracted.append(quality)
    
    # Extract specific patterns from format names
    # Extract hls from hls_fmp4-12_4-Audio
    if 'hls' in format_name.lower():
        all_extracted.append('hls')
    
    # Extract mp4 from hls_fmp4-12_4-Audio
    if 'mp4' in format_name.lower():
        all_extracted.append('mp4')
    
    # Extract dash from dash_sep-7
    if 'dash' in format_name.lower():
        all_extracted.append('dash')
    
    # Extract other extensions and codecs from format names
    for ext in media_extensions:
        if ext.lower() in format_name.lower() and ext not in ['mp4', 'hls', 'dash']:  # Avoid duplicates
            all_extracted.append(ext)
    
    for codec in codec_patterns:
        if codec.lower() in format_name.lower():
            # Shorten codec names
            if codec.startswith('avc1.'):
                codec = 'avc1'
            elif codec.startswith('vp9'):
                codec = 'vp9'
            elif codec.startswith('vp09'):
                codec = 'vp9'
            elif codec.startswith('av1.'):
                codec = 'av1'
            elif codec.startswith('av01.'):
                codec = 'av1'
            all_extracted.append(codec)
    
    # Extract quality from format names like hls_fmp4-12_4-Audio
    quality_from_name = re.search(r'(\d+p\d*)', format_name, re.IGNORECASE)
    if quality_from_name:
        all_extracted.append(quality_from_name.group(1))
    
    # Remove duplicates while preserving order (including comma variations)
    seen = set()
    for item in all_extracted:
        # Clean up item (remove commas, extra spaces)
        clean_item = item.strip().rstrip(',')
        
        # Handle combined items like m4a_dash, mp4_dash
        if '_' in clean_item:
            # Split combined items and add each part if not already present
            parts_combined = clean_item.split('_')
            for part_combined in parts_combined:
                part_combined = part_combined.strip()
                if part_combined and part_combined.lower() not in seen:
                    seen.add(part_combined.lower())
                    button_parts.append(part_combined)
            continue
        
        # Convert to lowercase for comparison but keep original case
        clean_item_lower = clean_item.lower()
        if clean_item_lower not in seen:
            seen.add(clean_item_lower)
            button_parts.append(clean_item)
    
    return button_parts

# In-memory filters for Always Ask (per user session)
_ASK_FILTERS = {}
_ASK_INFO_CACHE_FILE = "ask_formats.json"
_ASK_SUBS_LANGS_PREFIX = "ask_subs_"
# Store download directories for each user session
_USER_DOWNLOAD_DIRS = {}
# Store processing messages for each user session
_PROC_MSG_CACHE = {}

def get_filters(user_id):
    f = _ASK_FILTERS.get(str(user_id))
    if not f:
        # defaults: filters hidden to keep UI simple
        f = {"codec": "avc1", "ext": "mp4", "visible": False, "audio_lang": None, "has_dubs": False, "available_dubs": []}
        _ASK_FILTERS[str(user_id)] = f
    return f

def set_user_download_dir(user_id, download_dir):
    """Set download directory for user session"""
    _USER_DOWNLOAD_DIRS[str(user_id)] = download_dir

def get_user_download_dir(user_id):
    """Get download directory for user session"""
    return _USER_DOWNLOAD_DIRS.get(str(user_id))

def set_user_proc_msg(user_id, proc_msg):
    """Set processing message for user session"""
    _PROC_MSG_CACHE[str(user_id)] = proc_msg

def get_user_proc_msg(user_id):
    """Get processing message for user session"""
    return _PROC_MSG_CACHE.get(str(user_id))

def clear_user_proc_msg(user_id):
    """Clear processing message for user session"""
    _PROC_MSG_CACHE.pop(str(user_id), None)

def copy_cookies_to_download_dir(user_id, download_dir):
    """Copy cookies from user root directory to download directory"""
    try:
        if not download_dir or not os.path.exists(download_dir):
            return False
            
        user_dir = os.path.join("users", str(user_id))
        cookie_file = os.path.join(user_dir, "cookie.txt")
        
        if os.path.exists(cookie_file):
            import shutil
            download_cookie_file = os.path.join(download_dir, "cookie.txt")
            shutil.copy2(cookie_file, download_cookie_file)
            logger.info(f"Copied cookies to download directory: {download_cookie_file}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Failed to copy cookies to download directory: {e}")
        return False

def generate_download_dir_name(url):
    """Generate download directory name based on URL with minimal sanitization - only replace unsupported characters"""
    try:
        from urllib.parse import urlparse
        import re
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Start with domain
        dir_name = domain
        
        # Add path if exists and not just '/'
        if parsed.path and parsed.path != '/':
            path = parsed.path.strip('/')
            # Remove file extension if present
            path = re.sub(r'\.[a-zA-Z0-9]+$', '', path)
            if path:
                dir_name += f"_{path}"
        
        # Add query parameters if exist
        if parsed.query:
            # Add first few query parameters for all sites
            query_parts = parsed.query.split('&')[:3]
            for part in query_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    # Only replace truly problematic characters, keep most symbols
                    key = re.sub(r'[^\w\-_.]', '_', key)
                    value = re.sub(r'[^\w\-_.]', '_', value)
                    dir_name += f"_{key}_{value}"
        
        # Only replace characters that are truly problematic for filesystem
        # Keep letters, numbers, hyphens, underscores, dots
        dir_name = re.sub(r'[^\w\-_.]', '_', dir_name)
        
        # Clean up multiple underscores
        dir_name = re.sub(r'_+', '_', dir_name)
        dir_name = dir_name.strip('_')
        
        # Limit length to reasonable size
        if len(dir_name) > 150:
            # Keep domain and first part, truncate rest
            parts = dir_name.split('_')
            if len(parts) > 1:
                domain_part = parts[0]
                remaining = '_'.join(parts[1:])
                if len(remaining) > 100:
                    remaining = remaining[:100]
                dir_name = f"{domain_part}_{remaining}"
            else:
                dir_name = dir_name[:150]
        
        # Ensure we have something
        if not dir_name or dir_name == '_':
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            dir_name = f"{domain}_{url_hash}"
        
        return dir_name
    except Exception as e:
        logger.warning(f"Failed to generate download directory name: {e}")
        try:
            from urllib.parse import urlparse
            import hashlib
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"{domain}_{url_hash}"
        except:
            return "unknown"

def set_filter(user_id, kind, value):
    f = get_filters(user_id)
    if kind == "codec":
        f["codec"] = value
    elif kind == "ext":
        f["ext"] = value
    elif kind == "audio_lang":
        f["audio_lang"] = value
    elif kind == "quality":
        f["quality"] = value
    elif kind == "toggle":
        f["visible"] = (value == "on")
    _ASK_FILTERS[str(user_id)] = f

def save_filters(user_id, state):
    """Persist current in-memory filters back to the session map."""
    _ASK_FILTERS[str(user_id)] = dict(state)

def _ask_cache_path(user_id):
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    return os.path.join(user_dir, _ASK_INFO_CACHE_FILE)

def _subs_langs_cache_path(user_id, url: str) -> str:
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    h = hashlib.sha1((url or "").encode("utf-8", errors="ignore")).hexdigest()[:16]
    return os.path.join(user_dir, f"{_ASK_SUBS_LANGS_PREFIX}{h}.json")

def save_subs_langs_cache(user_id: int, url: str, normal_langs, auto_langs) -> None:
    try:
        path = _subs_langs_cache_path(user_id, url)
        data = {
            "url": url,
            "normal": list(normal_langs or []),
            "auto": list(auto_langs or []),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

def load_subs_langs_cache(user_id: int, url: str):
    try:
        path = _subs_langs_cache_path(user_id, url)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("normal", []), data.get("auto", [])
    except Exception:
        return [], []
    return [], []

def delete_subs_langs_cache(user_id: int, url: str) -> None:
    try:
        path = _subs_langs_cache_path(user_id, url)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def save_ask_info(user_id, url, info, download_dir=None):
    try:
        # Use stored download directory if not provided
        if download_dir is None:
            download_dir = get_user_download_dir(user_id)
        
        # Create ask_formats.json directly in download directory if available
        if download_dir and os.path.exists(download_dir):
            download_ask_file = os.path.join(download_dir, _ASK_INFO_CACHE_FILE)
            data = {}
            if os.path.exists(download_ask_file):
                with open(download_ask_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[url] = {
                "title": info.get("title"),
                "id": info.get("id"),
                "formats": info.get("formats", [])
            }
            with open(download_ask_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Created ask_formats.json in download directory: {download_ask_file}")
        else:
            # Fallback to user root directory if download directory not available
            path = _ask_cache_path(user_id)
            data = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[url] = {
                "title": info.get("title"),
                "id": info.get("id"),
                "formats": info.get("formats", [])
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Created ask_formats.json in user directory: {path}")
    except Exception as e:
        logger.warning(f"Failed to save ask_formats.json: {e}")

def load_ask_info(user_id, url):
    try:
        # First try to find ask_formats.json in download directory
        download_dir = get_user_download_dir(user_id)
        if download_dir and os.path.exists(download_dir):
            download_cache_file = os.path.join(download_dir, _ASK_INFO_CACHE_FILE)
            if os.path.exists(download_cache_file):
                with open(download_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Using ask_formats.json from download directory: {download_cache_file}")
                return data.get(url)
        
        # Fallback to user root directory
        path = _ask_cache_path(user_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Using ask_formats.json from user directory: {path}")
            return data.get(url)
    except Exception as e:
        logger.warning(f"Failed to load ask_formats.json: {e}")
        return None
    return None

# --- DUBS flag resolver (robust) ---
_DUBS_FLAG_OVERRIDES = {
    'de': '🇩🇪',
    'fr': '🇫🇷',
    'es': '🇪🇸',
    'it': '🇮🇹',
    'en': '🇬🇧',
    'pt': '🇵🇹',
}

def _dub_flag(lang_code: str) -> str:
    try:
        base = (lang_code or '').split('-', 1)[0].lower()
        if base in _DUBS_FLAG_OVERRIDES:
            return _DUBS_FLAG_OVERRIDES[base]
        # fallback to generic resolver by first part
        return get_flag(lang_code, use_second_part=False)
    except Exception:
        return '🌐'

@app.on_callback_query(filters.regex(r"^askf\|"))
def ask_filter_callback(app, callback_query):
    messages = safe_get_messages(callback_query.from_user.id)
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    logger.info(LoggerMsg.ALWAYS_ASK_CALLBACK_RECEIVED_LOG_MSG.format(callback_data=callback_query.data))
    user_id = callback_query.from_user.id
    parts = callback_query.data.split("|")
    if len(parts) >= 3:
        _, kind, value = parts[:3]
        logger.info(LoggerMsg.ALWAYS_ASK_PARSED_LOG_MSG.format(kind=kind, value=value))

        # --- SUBS handlers must run BEFORE generic filter rebuild ---
        if kind == "subs" and value == "open":
            # In Always Ask mode, allow user to choose from available subtitle languages
            # regardless of their current subtitle settings
                
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            try:
                # Warm up once per session: try to load from per-session cache,
                # otherwise compute a single time and persist for reuse within this download
                from COMMANDS.subtitles_cmd import get_or_compute_subs_langs
                normal, auto = get_or_compute_subs_langs(user_id, url)
                # Also warm in-memory availability cache classification once
                check_subs_availability(url, user_id, return_type=True)
                langs = sorted(set(normal) | set(auto))
            except Exception:
                # fallback to local cache if network check failed
                normal, auto = load_subs_langs_cache(user_id, url)
                langs = sorted(set(normal) | set(auto))
            if not langs:
                safe_callback_answer(callback_query, safe_get_messages(user_id).NO_SUBTITLES_DETECTED_MSG, show_alert=True)
                return
            kb = get_language_keyboard_always_ask(page=0, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            safe_callback_answer(callback_query, safe_get_messages(user_id).CHOOSE_SUBTITLE_LANGUAGE_MSG)
            return
        if kind == "subs_page":
            page = int(value)
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            # Prefer persisted cache to avoid list loss on edits
            n_cached, a_cached = load_subs_langs_cache(user_id, url)
            if n_cached or a_cached:
                normal, auto = n_cached, a_cached
            else:
                normal = _subs_check_cache.get(f"{url}_{user_id}_normal_langs") or []
                auto = _subs_check_cache.get(f"{url}_{user_id}_auto_langs") or []
            langs = sorted(set(normal) | set(auto))
            kb = get_language_keyboard_always_ask(page=page, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer(safe_get_messages(user_id).PAGE_NUMBER_MSG.format(page=page + 1))
            return
        if kind == "subs" and value in ("back", "close"):
            if value == "back":
                original_message = callback_query.message.reply_to_message
                if original_message:
                    url_text = original_message.text or (original_message.caption or "")
                    import re as _re
                    m = _re.search(r'https?://[^\s\*#]+', url_text)
                    url = m.group(0) if m else url_text
                    ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
                return
            # close
            try:
                safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            except Exception:
                app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=None)
            callback_query.answer(safe_get_messages(user_id).SUBTITLE_MENU_CLOSED_MSG)
            return
        if kind == "subs_lang":
            # Persist selected subtitle language as global setting used by embed logic
            try:
                save_user_subs_language(user_id, value)
                # If user picks explicit language from SUBS menu – assume manual, not auto
                save_user_subs_auto_mode(user_id, False)
            except Exception:
                pass
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                # Close subs keyboard and rebuild Always Ask menu with selected lang in summary
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer(safe_get_messages(user_id).SUBTITLE_LANGUAGE_SET_MSG.format(value=value))
            except Exception:
                pass
            return
        # DUBS open: show languages grid with flags
        if kind == "dubs" and value == "open":
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            fstate = get_filters(user_id)
            langs = fstate.get("available_dubs", [])
            if not langs or len(langs) <= 1:
                callback_query.answer(safe_get_messages(user_id).NO_ALTERNATIVE_AUDIO_LANGUAGES_MSG, show_alert=True)
                return
            rows, row = [], []
            for i, lang in enumerate(sorted(langs)):
                # Use robust flag lookup for DUBS (strict overrides first)
                flag = _dub_flag(lang)
                label = f"{flag} {lang}" if flag else lang
                row.append(InlineKeyboardButton(label, callback_data=f"askf|audio_lang|{lang}"))
                if (i+1) % 3 == 0:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            rows.append([InlineKeyboardButton(safe_get_messages(user_id).BACK_BUTTON_TEXT, callback_data="askf|dubs|back"), InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askf|dubs|close")])
            try:
                callback_query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
            except Exception:
                pass
            try:
                callback_query.answer(safe_get_messages(user_id).CHOOSE_AUDIO_LANGUAGE_MSG)
            except Exception:
                pass
            return
        if kind == "audio_lang":
            set_filter(user_id, kind, value)
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer(safe_get_messages(user_id).AUDIO_SET_MSG.format(value=value))
            except Exception:
                pass
            return
        if kind == "dubs" and value in ("back", "close"):
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer(safe_get_messages(user_id).FILTERS_UPDATED_MSG)
            except Exception:
                pass
            return
        if kind in ("codec", "ext"):
            set_filter(user_id, kind, value)
            try:
                if kind == "ext":
                    set_session_mkv_override(user_id, value == "mkv")
            except Exception:
                pass
        elif kind == "toggle":
            set_filter(user_id, kind, value)
            # Reset codec/ext to defaults when closing CODEC menu via Back
            if value == "off":
                set_filter(user_id, "codec", "avc1")
                set_filter(user_id, "ext", "mp4")
        # Rebuild the same message in place (fast, using cache)
        original_message = callback_query.message.reply_to_message
        if original_message:
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            # After starting download from menu, we will remove temp subs cache in down_and_up_with_format
            try:
                callback_query.answer(safe_get_messages(user_id).FILTERS_UPDATED_MSG)
            except Exception:
                pass
            return
        try:
            callback_query.answer(safe_get_messages(user_id).FILTERS_UPDATED_MSG)
        except Exception:
            pass

def get_available_formats_from_cache(user_id, url, download_dir=None):
    """Get available codecs and formats from ask_formats.json cache"""
    try:
        # First try to find ask_formats.json in download directory
        cache_file = None
        if download_dir and os.path.exists(download_dir):
            download_cache_file = os.path.join(download_dir, _ASK_INFO_CACHE_FILE)
            if os.path.exists(download_cache_file):
                cache_file = download_cache_file
                logger.info(f"Using ask_formats.json from download directory: {download_cache_file}")
        
        # Fallback to user root directory
        if not cache_file:
            user_dir = os.path.join("users", str(user_id))
            cache_file = os.path.join(user_dir, _ASK_INFO_CACHE_FILE)
            if os.path.exists(cache_file):
                logger.info(f"Using ask_formats.json from user directory: {cache_file}")
        
        if not cache_file or not os.path.exists(cache_file):
            return {"codecs": set(), "formats": set()}
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        available_codecs = set()
        available_formats = set()
        
        # Check if this URL matches the cached data
        if data.get('url') == url:
            formats = data.get('formats', [])
            
            for format_line in formats:
                # Extract codecs and formats using our existing function
                extracted = extract_button_data(format_line)
                
                for item in extracted:
                    # Check for codecs
                    if item.lower() in ['avc1', 'avc', 'h264']:
                        available_codecs.add('avc1')
                    elif item.lower() in ['av1', 'av01']:
                        available_codecs.add('av01')
                    elif item.lower() in ['vp9', 'vp09']:
                        available_codecs.add('vp9')
                    
                    # Check for formats
                    if item.lower() in ['mp4']:
                        available_formats.add('mp4')
                    elif item.lower() in ['mkv', 'webm', 'avi', 'mov', 'flv', 'wmv', '3gp', 'ogv', 'ts', 'mts', 'm2ts']:
                        # These formats can be converted to MKV by ffmpeg
                        available_formats.add('mkv')
        
        return {"codecs": available_codecs, "formats": available_formats}
    except Exception as e:
        logger.warning(f"{LoggerMsg.ALWAYS_ASK_ERROR_READING_AVAILABLE_FORMATS_FROM_CACHE_LOG_MSG}: {e}")
        return {"codecs": set(), "formats": set()}

def filter_qualities_by_codec_format(user_id, url, qualities, download_dir=None):
    """Filter qualities based on selected codec and format"""
    try:
        # Get current filters
        f = get_filters(user_id)
        selected_codec = f.get("codec", "avc1")
        selected_format = f.get("ext", "mp4")
        
        # Get available formats from cache
        user_download_dir = get_user_download_dir(user_id) if download_dir is None else download_dir
        available_formats = get_available_formats_from_cache(user_id, url, user_download_dir)
        
        # If no cache or no specific formats available, return all qualities
        if not available_formats["codecs"] and not available_formats["formats"]:
            return qualities
        
        # Get all format lines from cache
        user_dir = os.path.join("users", str(user_id))
        cache_file = os.path.join(user_dir, _ASK_INFO_CACHE_FILE)
        
        if not os.path.exists(cache_file):
            return qualities
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('url') != url:
            return qualities
        
        formats = data.get('formats', [])
        filtered_qualities = set()
        
        for format_line in formats:
            extracted = extract_button_data(format_line)
            
            # Check if this format matches selected codec and format
            has_codec = False
            has_format = False
            
            for item in extracted:
                # Check codec
                if selected_codec == 'avc1' and item.lower() in ['avc1', 'avc', 'h264']:
                    has_codec = True
                elif selected_codec == 'av01' and item.lower() in ['av1', 'av01']:
                    has_codec = True
                elif selected_codec == 'vp9' and item.lower() in ['vp9', 'vp09']:
                    has_codec = True
                
                # Check format
                if selected_format == 'mp4' and item.lower() == 'mp4':
                    has_format = True
                elif selected_format == 'mkv' and item.lower() in ['mkv', 'webm', 'avi', 'mov', 'flv', 'wmv', '3gp', 'ogv', 'ts', 'mts', 'm2ts']:
                    has_format = True
            
            # If both codec and format match, extract quality
            if has_codec and has_format:
                for item in extracted:
                    # Look for quality patterns (e.g., 720p, 1080p)
                    if 'p' in item and any(char.isdigit() for char in item):
                        quality_match = re.search(r'(\d+p\d*)', item)
                        if quality_match:
                            filtered_qualities.add(quality_match.group(1))
        
        # Return intersection of available qualities and filtered qualities
        if filtered_qualities:
            return [q for q in qualities if q in filtered_qualities]
        else:
            return qualities
            
    except Exception as e:
        logger.warning(f"{LoggerMsg.ALWAYS_ASK_ERROR_FILTERING_QUALITIES_LOG_MSG}: {e}")
        return qualities

def get_link_mode(user_id):
    """
    Получает состояние режима LINK для пользователя
    """
    try:
        user_dir = os.path.join("users", str(user_id))
        link_mode_file = os.path.join(user_dir, "link_mode.txt")
        if os.path.exists(link_mode_file):
            with open(link_mode_file, 'r') as f:
                return f.read().strip() == "enabled"
        return False
    except Exception:
        return False

def set_link_mode(user_id, enabled):
    """
    Устанавливает состояние режима LINK для пользователя
    """
    try:
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        link_mode_file = os.path.join(user_dir, "link_mode.txt")
        with open(link_mode_file, 'w') as f:
            f.write("enabled" if enabled else "disabled")
        return True
    except Exception as e:
        logger.error(f"{LoggerMsg.ALWAYS_ASK_ERROR_SETTING_LINK_MODE_LOG_MSG} {user_id}: {e}")
        return False

def build_filter_rows(user_id, url=None, is_private_chat=False, download_dir=None):
    messages = safe_get_messages(user_id)
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    f = get_filters(user_id)
    codec = f.get("codec", "avc1")
    ext = f.get("ext", "mp4")
    visible = bool(f.get("visible", False))
    audio_lang = f.get("audio_lang")
    has_dubs = bool(f.get("has_dubs"))
    
    # Check if user has fixed container format via /args
    user_fixed_format = None
    try:
        user_args = get_user_args(user_id)
        user_video_format = user_args.get('video_format', 'mp4')
        user_merge_format = user_args.get('merge_output_format', 'mp4')
        
        # If user has set video_format to something other than mp4, it's fixed
        if user_video_format != 'mp4':
            user_fixed_format = user_video_format
        # If user has set merge_output_format to something other than mp4, it's fixed
        elif user_merge_format != 'mp4':
            user_fixed_format = user_merge_format
    except Exception:
        pass
    
    # Get available formats from cache if URL is provided
    available_formats = {"codecs": set(), "formats": set()}
    if url:
        user_download_dir = get_user_download_dir(user_id) if download_dir is None else download_dir
        available_formats = get_available_formats_from_cache(user_id, url, user_download_dir)
    
    # When filters are hidden – show compact row with CODEC + audio (+ optional DUBS, SUBS)
    if not visible:
        # Determine NSFW for star icon on MP3
        is_nsfw = False
        if url:
            try:
                info = load_ask_info(user_id, url) or {}
                tags_text = ' '.join(generate_final_tags(url, [], info)) if isinstance(generate_final_tags(url, [], info), list) else generate_final_tags(url, [], info)
                is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
            except Exception:
                is_nsfw = False
        # Get user's audio format setting and check send_as_file
        try:
            user_args = get_user_args(user_id)
            audio_format = user_args.get('audio_format', 'mp3').upper()
            send_as_file = user_args.get('send_as_file', False)
        except Exception:
            audio_format = 'MP3'
            send_as_file = False
        
        # Determine MP3 cache status for rocket icon (skip if send_as_file is enabled)
        is_cached_mp3 = False
        if url and not send_as_file:
            try:
                cq = get_cached_qualities(url)
                is_cached_mp3 = ('mp3' in cq)
            except Exception:
                is_cached_mp3 = False
        
        mp3_label = (
            f"1⭐️{audio_format}" if (is_nsfw and is_private_chat)
            else (f"🚀{audio_format}" if is_cached_mp3 else f"🎧{audio_format}")
        )
        
        # Create dynamic layout based on available buttons
        buttons = [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_CODEC_BUTTON_MSG, callback_data="askf|toggle|on"), InlineKeyboardButton(mp3_label, callback_data="askq|mp3")]
        
        # Show DUBS button only if audio dubs are detected for this video (set elsewhere)
        if has_dubs:
            buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_DUBS_BUTTON_MSG, callback_data="askf|dubs|open"))
        
        # Show SUBS button if Always Ask is enabled for this user
        try:
            if is_subs_always_ask(user_id):
                buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_SUBS_BUTTON_MSG, callback_data="askf|subs|open"))
        except Exception:
            pass
        
        # Dynamic layout: 2 or 4 buttons = 2 per row, 3 buttons = all in one row
        if len(buttons) == 2 or len(buttons) == 4:
            # Split into 2 rows of 2 buttons each
            first_row = buttons[:2]
            second_row = buttons[2:] if len(buttons) > 2 else []
            return [first_row, second_row] if second_row else [first_row], []
        elif len(buttons) == 3:
            # All 3 buttons in one row
            return [buttons], []
        else:
            # Fallback: single row
            return [buttons], []
    
    # Build codec buttons with availability check
    avc1_available = 'avc1' in available_formats["codecs"] or not available_formats["codecs"]  # Show if available or if no cache
    av01_available = 'av01' in available_formats["codecs"] or not available_formats["codecs"]
    vp9_available = 'vp9' in available_formats["codecs"] or not available_formats["codecs"]
    
    avc1_btn = (safe_get_messages(user_id).AA_AVC_BUTTON_MSG if codec == "avc1" else safe_get_messages(user_id).AA_AVC_BUTTON_INACTIVE_MSG) if avc1_available else safe_get_messages(user_id).AA_AVC_BUTTON_UNAVAILABLE_MSG
    av01_btn = (safe_get_messages(user_id).AA_AV1_BUTTON_MSG if codec == "av01" else safe_get_messages(user_id).AA_AV1_BUTTON_INACTIVE_MSG) if av01_available else safe_get_messages(user_id).AA_AV1_BUTTON_UNAVAILABLE_MSG
    vp9_btn = (safe_get_messages(user_id).AA_VP9_BUTTON_MSG if codec == "vp9" else safe_get_messages(user_id).AA_VP9_BUTTON_INACTIVE_MSG) if vp9_available else safe_get_messages(user_id).AA_VP9_BUTTON_UNAVAILABLE_MSG
    
    # Build format buttons with availability check
    # If user has fixed format via /args, don't show container buttons
    if user_fixed_format:
        # Show fixed format as read-only
        fixed_format_btn = f"🔒 {user_fixed_format.upper()}"
        mp4_btn = fixed_format_btn
        mkv_btn = None  # Don't show MKV button
    else:
        mp4_available = 'mp4' in available_formats["formats"] or not available_formats["formats"]
        mkv_available = 'mkv' in available_formats["formats"] or not available_formats["formats"]
        
        mp4_btn = (safe_get_messages(user_id).AA_MP4_BUTTON_MSG if ext == "mp4" else safe_get_messages(user_id).AA_MP4_BUTTON_INACTIVE_MSG) if mp4_available else safe_get_messages(user_id).AA_MP4_BUTTON_UNAVAILABLE_MSG
        mkv_btn = (safe_get_messages(user_id).AA_MKV_BUTTON_MSG if ext == "mkv" else safe_get_messages(user_id).AA_MKV_BUTTON_INACTIVE_MSG) if mkv_available else safe_get_messages(user_id).AA_MKV_BUTTON_UNAVAILABLE_MSG
    
    # NSFW detection for expanded filters
    is_nsfw = False
    if url:
        try:
            info = load_ask_info(user_id, url) or {}
            tags_text = ' '.join(generate_final_tags(url, [], info)) if isinstance(generate_final_tags(url, [], info), list) else generate_final_tags(url, [], info)
            is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
        except Exception:
            is_nsfw = False
    # Get user's audio format setting and check send_as_file
    try:
        user_args = get_user_args(user_id)
        audio_format = user_args.get('audio_format', 'mp3').upper()
        send_as_file = user_args.get('send_as_file', False)
    except Exception:
        audio_format = 'MP3'
        send_as_file = False
    
    # Determine MP3 cache status for rocket icon (skip if send_as_file is enabled)
    is_cached_mp3 = False
    if url and not send_as_file:
        try:
            cq = get_cached_qualities(url)
            is_cached_mp3 = ('mp3' in cq)
        except Exception:
            is_cached_mp3 = False
    
    mp3_label = (
        f"1⭐️{audio_format}" if (is_nsfw and is_private_chat)
        else (f"🚀{audio_format}" if is_cached_mp3 else f"🎧{audio_format}")
    )
    # Build rows based on whether format is fixed
    rows = [
        [InlineKeyboardButton(avc1_btn, callback_data="askf|codec|avc1"), InlineKeyboardButton(av01_btn, callback_data="askf|codec|av01"), InlineKeyboardButton(vp9_btn, callback_data="askf|codec|vp9")]
    ]
    
    # Add format row - only show container buttons if not fixed via /args
    if user_fixed_format:
        # Show fixed format as non-clickable
        format_row = [InlineKeyboardButton(mp4_btn, callback_data="askf|empty"), InlineKeyboardButton(mp3_label, callback_data="askq|mp3")]
    else:
        # Show normal container selection
        format_row = [InlineKeyboardButton(mp4_btn, callback_data="askf|ext|mp4"), InlineKeyboardButton(mkv_btn, callback_data="askf|ext|mkv"), InlineKeyboardButton(mp3_label, callback_data="askq|mp3")]
    
    rows.append(format_row)
    action_buttons = []
    if has_dubs:
        action_buttons.append(InlineKeyboardButton("🗣 DUBS", callback_data="askf|dubs|open"))
    try:
        if is_subs_always_ask(user_id):
            action_buttons.append(InlineKeyboardButton("💬 SUBS", callback_data="askf|subs|open"))
    except Exception:
        pass
    
    return rows, action_buttons

@app.on_callback_query(filters.regex(r"^askq\|"))
# @reply_with_keyboard
def askq_callback(app, callback_query):
    messages = safe_get_messages(callback_query.from_user.id)
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    logger.info(f"{LoggerMsg.ALWAYS_ASK_CALLBACK_LOG_MSG}: {callback_query.data}")
    user_id = callback_query.from_user.id
    # Parse callback data correctly - handle both old and new formats
    parts = callback_query.data.split("|")
    if len(parts) >= 3 and parts[1] == "other_id":
        data = f"other_id_{parts[2]}"  # Reconstruct other_id_XXX format
    else:
        data = parts[1] if len(parts) > 1 else ""
    found_type = None
    
    logger.info(f"Processing callback data: '{data}' for user {user_id}")
    
    # Get processing message from cache (created in ask_quality_menu)
    proc_msg = get_user_proc_msg(user_id)
    if data == "close":
        # Clean up old format cache files before closing menu
        try:
            user_dir = os.path.join("users", str(user_id))
            create_directory(user_dir)
            
            # Get download directory if available
            user_download_dir = get_user_download_dir(user_id)
            
            # Remove all old format cache files
            import glob
            # Use download directory if available, otherwise fallback to user directory
            if user_download_dir and os.path.exists(user_download_dir):
                format_cache_pattern = os.path.join(user_download_dir, "formats_cache_*.json")
            else:
                format_cache_pattern = os.path.join(user_dir, "formats_cache_*.json")
            old_cache_files = glob.glob(format_cache_pattern)
            
            for cache_file in old_cache_files:
                try:
                    os.remove(cache_file)
                    logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_LOG_MSG}: {cache_file}")
                except Exception as e:
                    logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_REMOVE_OLD_CACHE_FILE_LOG_MSG} {cache_file}: {e}")
            if old_cache_files:
                logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_FILES_BEFORE_CLOSING_LOG_MSG}: {len(old_cache_files)}")
        except Exception as e:
            logger.warning(f"{LoggerMsg.ALWAYS_ASK_ERROR_CLEANING_UP_OLD_FORMAT_CACHE_FILES_BEFORE_CLOSING_LOG_MSG}: {e}")
        
        try:
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        except Exception:
            app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_MENU_CLOSED_MSG)
        return
        
    # Handle LINK button - get direct link with BV+BA/BEST format
    if data == "link":
        # Get original URL from the reply message
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            return
            
        url_text = original_message.text or (original_message.caption or "")
        import re as _re
        m = _re.search(r'https?://[^\s\*#]+', url_text)
        url = m.group(0) if m else url_text
        
        try:
            callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_GETTING_DIRECT_LINK_MSG)
        except Exception:
            pass
        
        # Import link function with proxy support
        from HELPERS.proxy_link_helper import get_direct_link_with_proxy
        
        # Get direct link with BV+BA/BEST format using proxy
        result = get_direct_link_with_proxy(url, "bv+ba/best", user_id)
        
        if result.get('success'):
            title = result.get('title', 'Unknown')
            duration = result.get('duration', 0)
            player_urls = result.get('player_urls', {})
            
            # Browser button will be sent in main message
            
            # Send main response with browser button
            main_response = safe_get_messages(user_id).STREAM_LINKS_TITLE_MSG
            main_response += safe_get_messages(user_id).STREAM_TITLE_MSG.format(title=title)
            if duration and duration > 0:
                main_response += f"{safe_get_messages(user_id).ALWAYS_ASK_DURATION_MSG} {duration} sec\n"
            main_response += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_MSG} <code>bv+ba/best</code>\n\n"
            main_response += f"{safe_get_messages(user_id).ALWAYS_ASK_BROWSER_MSG}\n\n"
            
            # Create browser keyboard
            browser_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_BROWSER_BUTTON_MSG, url=player_urls['direct'])],
                [InlineKeyboardButton("🔚 Close", callback_data="askq|close")]
            ])
            
            # Send main message with browser button
            app.send_message(
                user_id, 
                main_response, 
                reply_parameters=ReplyParameters(message_id=original_message.id),
                reply_markup=browser_keyboard,
                parse_mode=enums.ParseMode.HTML
            )
            
            # Send VLC iOS message
            if 'vlc_ios' in player_urls:
                vlc_ios_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_VLC_IOS_BUTTON_MSG, url=player_urls['vlc_ios'])],
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_CLOSE_BUTTON_MSG, callback_data="askq|close")]
                ])
                app.send_message(
                    user_id,
                    safe_get_messages(user_id).AA_VLC_IOS_MSG,
                    reply_parameters=ReplyParameters(message_id=original_message.id),
                    reply_markup=vlc_ios_keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            
            # Send VLC Android message
            if 'vlc_android' in player_urls:
                vlc_android_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_VLC_ANDROID_BUTTON_MSG, url=player_urls['vlc_android'])],
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_CLOSE_BUTTON_MSG, callback_data="askq|close")]
                ])
                app.send_message(
                    user_id,
                    safe_get_messages(user_id).AA_VLC_ANDROID_MSG,
                    reply_parameters=ReplyParameters(message_id=original_message.id),
                    reply_markup=vlc_android_keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            
            send_to_logger(original_message, safe_get_messages(user_id).DIRECT_LINK_MENU_CREATED_LOG_MSG.format(user_id=user_id, url=url))
            
        else:
            error_msg = result.get('error', 'Unknown error')
            app.send_message(
                user_id,
                safe_get_messages(user_id).AA_ERROR_GETTING_LINK_MSG.format(error_msg=error_msg),
                reply_parameters=ReplyParameters(message_id=original_message.id),
                parse_mode=enums.ParseMode.HTML
            )
            
            log_error_to_channel(original_message, safe_get_messages(user_id).DIRECT_LINK_EXTRACTION_FAILED_LOG_MSG.format(user_id=user_id, url=url, error=error_msg), url)
        
        # Удаляем Always Ask меню после обработки
        try:
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        except Exception as e:
            logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_DELETE_ALWAYS_ASK_MENU_LOG_MSG}: {e}")
        return

    # Handle LIST button - get available formats
    if data == "list":
        # Get original URL from the reply message
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            return
            
        url_text = original_message.text or (original_message.caption or "")
        import re as _re
        m = _re.search(r'https?://[^\s\*#]+', url_text)
        url = m.group(0) if m else url_text
        
        try:
            callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_GETTING_FORMATS_MSG)
        except Exception:
            pass
        
        # Import list function
        from COMMANDS.list_cmd import run_ytdlp_list
        
        # Run yt-dlp list command
        success, output = run_ytdlp_list(url, user_id)
        
        if success:
            # Check if any format contains "audio only" and "video only" and extract format IDs
            audio_only_formats = []
            video_only_formats = []
            lines = output.split('\n')
            for line in lines:
                if 'audio only' in line.lower() or 'audio_only' in line.lower():
                    # Extract format ID from the line (usually at the beginning)
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        format_id = parts[0]
                        audio_only_formats.append(format_id)
                elif 'video only' in line.lower() or 'video_only' in line.lower():
                    # Extract format ID from the line (usually at the beginning)
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        format_id = parts[0]
                        video_only_formats.append(format_id)
            
            # Create temporary file with output
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_AVAILABLE_FORMATS_FOR_MSG}: {url}\n")
                temp_file.write("=" * 50 + "\n\n")
                temp_file.write(output)
                temp_file.write("\n\n" + "=" * 50 + "\n")
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_HOW_TO_USE_FORMAT_IDS_MSG}\n")
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_AFTER_GETTING_LIST_MSG}\n")
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ID_401_MSG}\n")
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ID401_MSG}\n")
                temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ID_140_AUDIO_MSG}\n")
                
                # Add special note for audio-only formats
                if audio_only_formats:
                    temp_file.write(f"\n{safe_get_messages(user_id).ALWAYS_ASK_AUDIO_ONLY_FORMATS_DETECTED_MSG}: {', '.join(audio_only_formats)}\n")
                    temp_file.write(f"{safe_get_messages(user_id).ALWAYS_ASK_THESE_FORMATS_MP3_MSG}\n")
                
                temp_file_path = temp_file.name
            
            try:
                # Send the file
                # Build caption with audio-only format info
                caption = f"{safe_get_messages(user_id).ALWAYS_ASK_AVAILABLE_FORMATS_FOR_MSG}:\n<code>{url}</code>\n\n"
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_HOW_TO_SET_FORMAT_MSG}\n"
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ID_134_MSG}\n"
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_720P_MSG}\n"
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_BEST_MSG}\n"
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ASK_MSG}\n\n"
                
                # Add video-only formats info first
                if video_only_formats:
                    video_formats_text = ', '.join([f'<code>{fmt}</code>' for fmt in video_only_formats])
                    caption += f"\n{safe_get_messages(user_id).LIST_VIDEO_ONLY_FORMATS_MSG.format(formats=video_formats_text)}\n"
                
                # Add special note for audio-only formats with monospace formatting
                if audio_only_formats:
                    audio_formats_text = ', '.join([f'<code>{fmt}</code>' for fmt in audio_only_formats])
                    caption += f"{safe_get_messages(user_id).ALWAYS_ASK_AUDIO_ONLY_FORMATS_MSG}: {audio_formats_text}\n"
                    caption += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_ID_140_AUDIO_CAPTION_MSG}\n"
                    caption += f"{safe_get_messages(user_id).ALWAYS_ASK_THESE_WILL_BE_MP3_MSG}\n\n"
                
                caption += f"{safe_get_messages(user_id).ALWAYS_ASK_USE_FORMAT_ID_MSG}"
                
                app.send_document(
                    user_id,
                    document=temp_file_path,
                    file_name=f"formats_{user_id}.txt",
                    caption=caption,
                    reply_parameters=ReplyParameters(message_id=original_message.id)
                )
                
                send_to_logger(original_message, safe_get_messages(user_id).LIST_COMMAND_EXECUTED_LOG_MSG.format(user_id=user_id, url=url))
                    
            except Exception as e:
                logger.error(f"{LoggerMsg.ALWAYS_ASK_ERROR_SENDING_FORMATS_FILE_LOG_MSG}: {e}")
                app.send_message(
                    user_id,
                    safe_get_messages(user_id).AA_ERROR_SENDING_FORMATS_MSG.format(error=str(e)),
                    reply_parameters=ReplyParameters(message_id=original_message.id)
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        else:
            app.send_message(
                user_id,
                safe_get_messages(user_id).AA_FAILED_GET_FORMATS_MSG.format(output=output),
                reply_parameters=ReplyParameters(message_id=original_message.id)
            )
        
        # Удаляем Always Ask меню после обработки
        try:
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        except Exception as e:
            logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_DELETE_ALWAYS_ASK_MENU_LOG_MSG}: {e}")
        return

    # ---- IMAGE fallback: process via gallery-dl (/img) ----
    if data == "image":
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            return
        # ЖЕСТКО: Получаем полный текст сообщения
        url_text = original_message.text or (original_message.caption or "")
        logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_DEBUG_ORIGINAL_MESSAGE_TEXT_LOG_MSG}: {original_message.text}")
        logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_DEBUG_ORIGINAL_MESSAGE_CAPTION_LOG_MSG}: {original_message.caption}")
        logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_DEBUG_URL_TEXT_LOG_MSG}: {url_text}")
        
        # ЖЕСТКО: Ищем URL с диапазоном в полном тексте
        import re as _re
        # Сначала ищем URL с диапазоном *start*end
        range_url_match = _re.search(r'(https?://[^\s\*#]+)\*(\d+)\*(\d+)', url_text)
        if range_url_match:
            url = range_url_match.group(1)
            start_range = int(range_url_match.group(2))
            end_range = int(range_url_match.group(3))
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_DEBUG_FOUND_RANGE_URL_LOG_MSG}: {url} with range {start_range}-{end_range}")
        else:
            # Fallback к обычному URL
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            start_range = 1
            end_range = 1
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_DEBUG_NO_RANGE_FOUND_LOG_MSG}: {url}")
        try:
            callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_STARTING_GALLERY_DL_MSG)
        except Exception:
            pass
        try:
            # Check if content is NSFW for fallback - same as original function
            from HELPERS.porn import is_porn
            is_nsfw = bool(is_porn(url, "", "", None))
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_IS_PORN_CHECK_LOG_MSG} {url}: {is_nsfw}")
            
            # Check for explicit NSFW tags in original message
            user_forced_nsfw = bool(re.search(r"(?i)(?:^|\s)#nsfw(?:\s|$)", url_text))
            if user_forced_nsfw:
                is_nsfw = True
                logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_USER_FORCED_NSFW_TAG_DETECTED_LOG_MSG} {url}")
            
            # Range already extracted above - ЖЕСТКО!
            parsed_url = url
            
            # Create fallback command converting *1*10 to 1-10 format
            if start_range and end_range and start_range != 1 and end_range != 1:
                # Convert *1*10 format to 1-10 format
                fallback_text = f"/img {start_range}-{end_range} {parsed_url}"
                logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_CONVERTING_RANGE_LOG_MSG}: *{start_range}*{end_range} -> {start_range}-{end_range}, fallback_text: {fallback_text}")
            else:
                fallback_text = f"/img {url}"
                logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_NO_RANGE_DETECTED_LOG_MSG}: {fallback_text}")
            
            if is_nsfw and "#nsfw" not in fallback_text.lower():
                fallback_text += " #nsfw"
                logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_ADDED_NSFW_TAG_LOG_MSG}: {url}")
            
            # Запускаем /img с «фейковым» сообщением, чтобы работать через gallery-dl
            fake_msg = fake_message(fallback_text, original_message.chat.id, original_chat_id=original_message.chat.id)
            # Сохраняем message_thread_id из оригинального сообщения
            fake_msg.message_thread_id = getattr(original_message, 'message_thread_id', None)
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_FAKE_MSG_DETAILS_LOG_MSG}={fake_msg.chat.id}, fake_msg.message_thread_id={fake_msg.message_thread_id}, original_message.chat.id={original_message.chat.id}, original_message.message_thread_id={getattr(original_message, 'message_thread_id', None)}")
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_ORIGINAL_MESSAGE_TYPE_LOG_MSG}: {type(original_message)}, original_message.chat type: {type(original_message.chat)}")
            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_ORIGINAL_MESSAGE_ATTRIBUTES_LOG_MSG}: {dir(original_message)}")
            image_command(app, fake_msg)
        except Exception as e:
            logger.error(f"{LoggerMsg.ALWAYS_ASK_IMAGE_FALLBACK_FAILED_LOG_MSG}: {e}")
        
        # Удаляем Always Ask меню после обработки
        try:
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        except Exception as e:
            logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_DELETE_ALWAYS_ASK_MENU_LOG_MSG}: {e}")
        return
    
    if data == "quick_embed":
        # Get original URL from the reply message
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            return
            
        url = original_message.text
        if not url:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_URL_NOT_FOUND_MSG, show_alert=True)
            return
            
        # Transform URL
        embed_url = transform_to_embed_url(url)
        if embed_url == url:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_URL_NOT_EMBEDDABLE_MSG, show_alert=True)
            return
            
        # Send transformed URL
        app.send_message(
            callback_query.message.chat.id,
            embed_url,
            reply_parameters=ReplyParameters(message_id=original_message.id)
        )
        send_to_logger(original_message, safe_get_messages(user_id).QUICK_EMBED_LOG_MSG.format(embed_url=embed_url))
        safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        return
    
    # Handle manual quality selection menu
    if data == "try_manual":
        show_manual_quality_menu(app, callback_query)
        return
    
    # Handle other qualities menu
    if data == "other_qualities":
        show_other_qualities_menu(app, callback_query)
        return

    # Handle filter toggles
    if data.startswith("f|") or data.startswith("askf|"):
        parts = callback_query.data.split("|")
        # support both prefixes
        _, kind, value = parts[0], parts[1], parts[2]
        if kind in ("codec", "ext"):
            # Handle empty callback (fixed format)
            if value == "empty":
                callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG, show_alert=True)
                return
                
            # Get original message and URL
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url = original_message.text or (original_message.caption or "")
            # try to extract url
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url)
            if m:
                url = m.group(0)
            
            # Check if the selected codec/format is available
            available_formats = get_available_formats_from_cache(user_id, url)
            
            if kind == "codec":
                if value not in available_formats["codecs"] and available_formats["codecs"]:
                    # Codec is not available, show warning
                    callback_query.answer(safe_get_messages(user_id).AA_ERROR_CODEC_NOT_AVAILABLE_MSG.format(codec=value.upper()), show_alert=True)
                    return
            elif kind == "ext":
                if value not in available_formats["formats"] and available_formats["formats"]:
                    # Format is not available, show warning
                    callback_query.answer(safe_get_messages(user_id).AA_ERROR_FORMAT_NOT_AVAILABLE_MSG.format(format=value.upper()), show_alert=True)
                    return
            
            # Set filter and reopen menu
            set_filter(callback_query.from_user.id, kind, value)
            callback_query.answer(safe_get_messages(user_id).FILTERS_UPDATED_MSG)
            ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "open":
            # Build and show dubs selection menu with flags
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            # Use precomputed list from filters state for speed/stability
            fstate = get_filters(callback_query.from_user.id)
            langs = fstate.get('available_dubs', [])
            # Build buttons 3 per row with flags
            rows = []
            row = []
            for i, lang in enumerate(sorted(langs)):
                # DUBS: use first part for flags (de from de-DE)
                flag = get_flag(lang, use_second_part=False)
                label = f"{flag} {lang}" if flag else lang
                row.append(InlineKeyboardButton(label, callback_data=f"askf|audio_lang|{lang}"))
                if (i+1) % 3 == 0:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            rows.append([InlineKeyboardButton("🔙Back", callback_data="askf|dubs|back"), InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="askf|dubs|close")])
            kb = InlineKeyboardMarkup(rows)
            try:
                # Replace entire keyboard (keeping caption/text) to show dubs
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer(safe_get_messages(user_id).AA_CHOOSE_AUDIO_LANGUAGE_MSG)
            return
        # LINK MENU HANDLER REMOVED - now using direct link approach
        if kind == "subs_page":
            # Handle page navigation in Always Ask subtitle menu
            page = int(value)
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer(safe_get_messages(user_id).ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            try:
                normal = _subs_check_cache.get(f"{url}_{user_id}_normal_langs") or []
                auto = _subs_check_cache.get(f"{url}_{user_id}_auto_langs") or []
            except Exception:
                normal, auto = [], []
            langs = sorted(set(normal) | set(auto))
            kb = get_language_keyboard_always_ask(page=page, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer(safe_get_messages(user_id).PAGE_NUMBER_MSG.format(page=page + 1))
            return
        if kind == "subs" and value == "back":
            # Go back to main Always Ask menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "subs" and value == "close":
            # Close subtitle menu
            try:
                safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            except Exception:
                app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=None)
            callback_query.answer(safe_get_messages(user_id).SUBTITLE_MENU_CLOSED_MSG)
            return
        # OLD LINK TOGGLE HANDLER REMOVED - now using submenu approach
        if kind == "subs_lang":
            # Handle subtitle language selection in Always Ask
            selected_lang = value
            # Store the selected subtitle language for this video
            fstate = get_filters(user_id)
            fstate['selected_subs_lang'] = selected_lang
            save_filters(user_id, fstate)
            callback_query.answer(safe_get_messages(user_id).SUBTITLE_LANGUAGE_SET_MSG.format(value=selected_lang))
            # Return to main Always Ask menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "close":
            # Close dubs menu without changing audio_lang
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "audio_lang":
            set_filter(callback_query.from_user.id, kind, value)
            callback_query.answer(safe_get_messages(user_id).AUDIO_SET_MSG.format(value=value))
            # Return to main menu with updated summary
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "back":
            # Go back to main menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        # LINK BACK/CLOSE HANDLERS REMOVED - no longer needed
    
    # Handle other qualities page navigation
    if data.startswith("other_page_"):
        page = int(data.replace("other_page_", ""))
        # For page navigation, use cached data for speed
        original_message = callback_query.message.reply_to_message
        if original_message:
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            
            if url:
                # Clean up old format cache files before using current cache
                try:
                    user_dir = os.path.join("users", str(callback_query.from_user.id))
                    create_directory(user_dir)
                    
                    # Get download directory if available
                    user_download_dir = get_user_download_dir(callback_query.from_user.id)
                    
                    # Remove all old format cache files except current one
                    import glob
                    # Use download directory if available, otherwise fallback to user directory
                    if user_download_dir and os.path.exists(user_download_dir):
                        format_cache_pattern = os.path.join(user_download_dir, "formats_cache_*.json")
                        current_cache_file = os.path.join(user_download_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
                    else:
                        format_cache_pattern = os.path.join(user_dir, "formats_cache_*.json")
                        current_cache_file = os.path.join(user_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
                    old_cache_files = glob.glob(format_cache_pattern)
                    
                    for cache_file in old_cache_files:
                        if cache_file != current_cache_file:  # Don't delete current cache
                            try:
                                os.remove(cache_file)
                                logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_LOG_MSG}: {cache_file}")
                            except Exception as e:
                                logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_REMOVE_OLD_CACHE_FILE_LOG_MSG} {cache_file}: {e}")
                    if len(old_cache_files) > 1:
                        logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_FILES_DURING_NAVIGATION_LOG_MSG}: {len(old_cache_files) - 1}")
                except Exception as e:
                    logger.warning(f"{LoggerMsg.ALWAYS_ASK_ERROR_CLEANING_UP_OLD_FORMAT_CACHE_FILES_DURING_NAVIGATION_LOG_MSG}: {e}")
                
                cache_file = current_cache_file
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                            format_lines = cached_data.get('formats', [])
                            if format_lines:
                                show_formats_from_cache(app, callback_query, format_lines, page, url)
                                return
                    except Exception:
                        pass
        
                    # Fallback to full function if cache not available
            show_other_qualities_menu(app, callback_query, page)
        return
    
    if data == "other_back":
        # Go back to main Always Ask menu
        original_message = callback_query.message.reply_to_message
        if original_message:
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            
            # Clean up old format cache files before returning to main menu
            try:
                user_dir = os.path.join("users", str(callback_query.from_user.id))
                create_directory(user_dir)
                
                # Get download directory if available
                user_download_dir = get_user_download_dir(callback_query.from_user.id)
                
                # Remove all old format cache files except current one
                import glob
                # Use download directory if available, otherwise fallback to user directory
                if user_download_dir and os.path.exists(user_download_dir):
                    format_cache_pattern = os.path.join(user_download_dir, "formats_cache_*.json")
                    current_cache_file = os.path.join(user_download_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
                else:
                    format_cache_pattern = os.path.join(user_dir, "formats_cache_*.json")
                    current_cache_file = os.path.join(user_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
                old_cache_files = glob.glob(format_cache_pattern)
                
                for cache_file in old_cache_files:
                    if cache_file != current_cache_file:  # Don't delete current cache
                        try:
                            os.remove(cache_file)
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_LOG_MSG}: {cache_file}")
                        except Exception as e:
                            logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_REMOVE_OLD_CACHE_FILE_LOG_MSG} {cache_file}: {e}")
                if len(old_cache_files) > 1:
                    logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_FILES_BEFORE_RETURNING_TO_MAIN_MENU_LOG_MSG}: {len(old_cache_files) - 1}")
            except Exception as e:
                logger.warning(f"{LoggerMsg.ALWAYS_ASK_ERROR_CLEANING_UP_OLD_FORMAT_CACHE_FILES_BEFORE_RETURNING_TO_MAIN_MENU_LOG_MSG}: {e}")
            
            ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
        return
    
    if data == "manual_back":
        # Extract URL and tags to regenerate the original menu
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            return
        
        url = None
        if callback_query.message.caption_entities:
            for entity in callback_query.message.caption_entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                    url = entity.url
                    break
        if not url and callback_query.message.reply_to_message:
            url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
            if url_match:
                url = url_match.group(0)
        
        if url:
            tags = []
            caption_text = callback_query.message.caption
            if caption_text:
                tag_matches = re.findall(r'#\S+', caption_text)
                if tag_matches:
                    tags = tag_matches
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            ask_quality_menu(app, original_message, url, tags)
        else:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_URL_NOT_FOUND_MSG, show_alert=True)
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        return
    
    # Handle other quality selection by ID
    if data.startswith("other_id_"):
        logger.info(f"Processing other_id_ callback: {data}")
        format_id_hash = data.replace("other_id_", "")
        
        # Get original format_id from callback data
        format_id = get_original_data_from_callback("askq|other_id", callback_query.data)
        logger.info(f"Retrieved format_id from callback: '{format_id}' for hash '{format_id_hash}'")
        
        # If format_id is still a hash, try to get it from the cache
        if format_id == format_id_hash:
            logger.warning(f"Format ID is still a hash, trying to get from cache")
            # Try to get format_id from the cached formats
            try:
                user_id = callback_query.from_user.id
                user_dir = os.path.join("users", str(user_id))
                cache_file = os.path.join(user_dir, "formats_cache_75170fc2.json")
                if os.path.exists(cache_file):
                    import json
                    with open(cache_file, 'r') as f:
                        formats = json.load(f)
                    # Find format by hash or try to use the hash as format_id
                    format_id = format_id_hash
                    logger.info(f"Using hash as format_id: {format_id}")
                else:
                    logger.error(f"Cache file not found: {cache_file}")
            except Exception as e:
                logger.error(f"Error reading cache file: {e}")
        
        # Delete the menu message immediately to prevent multiple menus
        try:
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            logger.info("Deleted Other menu message successfully")
        except Exception as e:
            logger.warning(f"Failed to delete Other menu message: {e}")
        
        callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOADING_FORMAT_MSG} {format_id}...")
        logger.info(f"Starting download process for format_id: {format_id}")
        
        original_message = callback_query.message.reply_to_message
        if not original_message:
            logger.error("Original message not found")
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            return
        
        url = None
        if callback_query.message.caption_entities:
            for entity in callback_query.message.caption_entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                    url = entity.url
                    break
        if not url and callback_query.message.reply_to_message:
            url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
            if url_match:
                url = url_match.group(0)
        
        logger.info(f"Extracted URL: {url}")
        if not url:
            logger.error("URL not found in message")
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_URL_NOT_FOUND_MSG, show_alert=True)
            return
        
        # Extract tags from the user's source message
        original_text = original_message.text or original_message.caption or ""
        _, _, _, _, tags, tags_text, _ = extract_url_range_tags(original_text)
        logger.info(f"Extracted tags: {tags_text}")
        
        # Use specific format ID for download
        format_override = format_id
        logger.info(f"Using format_override: {format_override}")
        
        # Handle playlists
        if is_playlist_with_range(original_text):
            logger.info("Detected playlist, using down_and_up")
            _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(original_text)
            # Правильное вычисление video_count для отрицательных индексов
            if video_start_with < 0 and video_end_with < 0:
                video_count = abs(video_end_with) - abs(video_start_with) + 1
            elif video_start_with > video_end_with:
                video_count = abs(video_start_with - video_end_with) + 1
            else:
                video_count = video_end_with - video_start_with + 1
            # Delete processing message before starting download
            delete_processing_message(app, user_id, None)
            down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=format_id, cookies_already_checked=True, cached_video_info=None, clear_subs_cache_on_start=False)
        else:
            logger.info("Single video, using down_and_up_with_format")
            # Delete processing message before starting download
            delete_processing_message(app, user_id, None)
            down_and_up_with_format(app, original_message, url, format_override, tags_text, quality_key=format_id, proc_msg=None)
        logger.info("Download process initiated successfully")
        return
    
    # Handle manual quality selection
    if data.startswith("manual_"):
        quality = data.replace("manual_", "")
        callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOADING_QUALITY_MSG} {quality}...")
        
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_ORIGINAL_NOT_FOUND_MSG, show_alert=True)
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            return
        
        url = None
        if callback_query.message.caption_entities:
            for entity in callback_query.message.caption_entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                    url = entity.url
                    break
        if not url and callback_query.message.reply_to_message:
            url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
            if url_match:
                url = url_match.group(0)
        
        if not url:
            callback_query.answer(safe_get_messages(user_id).AA_ERROR_URL_NOT_FOUND_MSG, show_alert=True)
            safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            return
        
        # New method: always extract tags from the user's source message
        original_text = original_message.text or original_message.caption or ""
        _, _, _, _, tags, tags_text, _ = extract_url_range_tags(original_text)
        
        safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        
        # Force use specific quality format like in /format command
        if quality == "best":
            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best"
        elif quality == "mp3":
            # Delete processing message before starting download
            delete_processing_message(app, user_id, proc_msg)
            down_and_audio(app, original_message, url, tags, quality_key="mp3", format_override="ba", cookies_already_checked=True, cached_video_info=None)
            return
        else:
            try:
                quality_str = quality.replace('p', '')
                quality_val = int(quality_str)
                # choose previous rung for lower bound
                if quality_val and quality_val >= 4320:
                    prev = 2160
                elif quality_val and quality_val >= 2160:
                    prev = 1440
                elif quality_val and quality_val >= 1440:
                    prev = 1080
                elif quality_val and quality_val >= 1080:
                    prev = 720
                elif quality_val and quality_val >= 720:
                    prev = 480
                elif quality_val and quality_val >= 480:
                    prev = 360
                elif quality_val and quality_val >= 360:
                    prev = 240
                elif quality_val and quality_val >= 240:
                    prev = 144
                else:
                    prev = 0
                format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
            except ValueError:
                format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best"
        
        # Handle playlists
        original_text = original_message.text or original_message.caption or ""
        if is_playlist_with_range(original_text):
            _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(original_text)
            # Правильное вычисление video_count для отрицательных индексов
            if video_start_with < 0 and video_end_with < 0:
                video_count = abs(video_end_with) - abs(video_start_with) + 1
            elif video_start_with > video_end_with:
                video_count = abs(video_start_with - video_end_with) + 1
            else:
                video_count = video_end_with - video_start_with + 1
            # Delete processing message before starting download
            delete_processing_message(app, user_id, proc_msg)
            down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=quality, cookies_already_checked=True, cached_video_info=None, clear_subs_cache_on_start=False)
        else:
            # Delete processing message before starting download
            delete_processing_message(app, user_id, proc_msg)
            down_and_up_with_format(app, original_message, url, format_override, tags_text, quality_key=quality, proc_msg=proc_msg)
        return

    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_DETAILED_MSG, show_alert=True)
        safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        return

    url = None
    if callback_query.message.caption_entities:
        for entity in callback_query.message.caption_entities:
            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                url = entity.url
                break
    if not url and callback_query.message.reply_to_message:
        url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    if not url:
        callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_ORIGINAL_URL_NOT_FOUND_MSG, show_alert=True)
        safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
        return

    # We extract tags from the initial message of the user
    original_text = original_message.text or original_message.caption or ""
    _, _, _, _, tags, tags_text, _ = extract_url_range_tags(original_text)

    safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])

    original_text = original_message.text or original_message.caption or ""
    if is_playlist_with_range(original_text):
        logger.info(f"{LoggerMsg.ALWAYS_ASK_PLAYLIST_WITH_RANGE_DETECTED_LOG_MSG}: {url}")
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(original_text)
        # Правильное вычисление video_count для отрицательных индексов
        if video_start_with < 0 and video_end_with < 0:
            video_count = abs(video_end_with) - abs(video_start_with) + 1
        elif video_start_with > video_end_with:
            video_count = abs(video_start_with - video_end_with) + 1
        else:
            video_count = video_end_with - video_start_with + 1
        
        # Формируем список индексов с учетом отрицательных индексов
        # Для отрицательных индексов нужно будет преобразовать их в положительные после получения общего количества видео
        has_negative_indices = video_start_with < 0 or video_end_with < 0
        if has_negative_indices:
            # Для отрицательных индексов сначала создаем список с отрицательными значениями
            if abs(video_start_with) < abs(video_end_with):
                # -1 до -7: создаем список [-1, -2, -3, -4, -5, -6, -7]
                requested_indices = list(range(video_start_with, video_end_with - 1, -1))
            else:
                # -7 до -1: создаем список [-7, -6, -5, -4, -3, -2, -1]
                requested_indices = list(range(video_start_with, video_end_with + 1, 1))
        elif video_start_with > video_end_with:
            # Для обратного порядка: от start до end включительно в обратном порядке
            requested_indices = list(range(video_start_with, video_end_with - 1, -1))
        else:
            # Для прямого порядка: от start до end включительно
            requested_indices = list(range(video_start_with, video_start_with + video_count))
        
        # Если есть отрицательные индексы, нужно получить общее количество видео и преобразовать их
        if has_negative_indices:
            try:
                from DOWN_AND_UP.yt_dlp_hook import get_video_formats
                logger.info(f"Getting total playlist count for negative indices conversion (always_ask)...")
                temp_info = get_video_formats(url, user_id, 1, True, False, 1)
                if temp_info and isinstance(temp_info, dict):
                    if "entries" in temp_info:
                        total_playlist_count = len(temp_info["entries"])
                    elif "_playlist_entries" in temp_info:
                        total_playlist_count = len(temp_info["_playlist_entries"])
                    else:
                        total_playlist_count = None
                    
                    if total_playlist_count:
                        logger.info(f"Total playlist count (always_ask): {total_playlist_count}")
                        # Преобразуем отрицательные индексы в положительные
                        converted_indices = []
                        for neg_idx in requested_indices:
                            if neg_idx < 0:
                                pos_idx = total_playlist_count + neg_idx + 1
                                converted_indices.append(pos_idx)
                            else:
                                converted_indices.append(neg_idx)
                        # Сортируем в обратном порядке для скачивания от последнего к первому
                        converted_indices.sort(reverse=True)
                        requested_indices = converted_indices
                        logger.info(f"Converted negative indices to positive (always_ask): {converted_indices}")
            except Exception as e:
                logger.warning(f"Failed to get total playlist count for negative indices (always_ask): {e}, using original indices")
        
        # Check if Always Ask mode is enabled - if yes, skip cache completely
        # Also check if send_as_file is enabled - if so, skip cache completely
        user_args = get_user_args(user_id)
        send_as_file = user_args.get("send_as_file", False)
        
        if not is_subs_always_ask(user_id) and not send_as_file:
            # Check cache for selected quality
            cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), data, requested_indices)
            uncached_indices = [i for i in requested_indices if i not in cached_videos]
            used_quality_key = data
            
            # If there is no cache for the selected quality, try fallback to best
            if not cached_videos and data != "best":
                logger.info(f"{LoggerMsg.ALWAYS_ASK_NO_CACHE_FOR_QUALITY_KEY_LOG_MSG}={data}, trying fallback to best")
                best_cached = get_cached_playlist_videos(get_clean_playlist_url(url), "best", requested_indices)
                if best_cached:
                    cached_videos = best_cached
                    used_quality_key = "best"
                    uncached_indices = [i for i in requested_indices if i not in cached_videos]
                    logger.info(f"{LoggerMsg.ALWAYS_ASK_FOUND_CACHE_WITH_BEST_QUALITY_LOG_MSG}: {list(cached_videos.keys())}, uncached: {uncached_indices}")
        else:
            logger.info(f"{LoggerMsg.ALWAYS_ASK_SKIPPING_CACHE_CHECK_FOR_PLAYLIST_LOG_MSG}: url={url}, quality={data}")
            cached_videos = {}
            uncached_indices = requested_indices
            used_quality_key = data
        
        if cached_videos:
            # Reposting cached videos
            callback_query.answer("🚀 Found in cache! Reposting...", show_alert=False)
            try:
                target_chat_id = getattr(original_message.chat, 'id', user_id)
            except Exception:
                target_chat_id = user_id
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        thread_id = getattr(original_message, 'message_thread_id', None)
                        # Use forward everywhere; in groups try to keep topic via message_thread_id
                        if thread_id:
                            from HELPERS.logger import get_log_channel
                            from HELPERS.porn import is_porn
                            # Determine the correct log channel based on content type
                            is_nsfw = is_porn(url, "", "", None)
                            is_private_chat = getattr(original_message.chat, "type", None) == enums.ChatType.PRIVATE
                            is_paid = is_nsfw and is_private_chat
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_URL_ANALYSIS_LOG_MSG}: url={url}, is_nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}")
                            
                            # Get the correct log channel for reposting
                            if is_paid:
                                from_chat_id = get_log_channel("video", paid=True)
                                channel_type = "PAID"
                            elif is_nsfw:
                                from_chat_id = get_log_channel("video", nsfw=True)
                                channel_type = "NSFW"
                            else:
                                from_chat_id = get_log_channel("video")
                                channel_type = "regular"
                            
                            logger.info(f"[VIDEO CACHE] Channel selection: nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}, channel_type={channel_type}, from_chat_id={from_chat_id}")
                            
                            # Verify we're reposting from a valid log channel
                            valid_channels = [
                                get_log_channel("video"),
                                get_log_channel("video", nsfw=True),
                                get_log_channel("video", paid=True)
                            ]
                            if from_chat_id not in valid_channels:
                                logger.error(f"CRITICAL: Attempting to repost from wrong channel {from_chat_id}")
                                continue
                                
                            logger.info(f"[VIDEO CACHE] Reposting video {index} from channel {from_chat_id} to user {target_chat_id}, message_id={cached_videos[index]}")
                            app.forward_messages(
                                chat_id=target_chat_id,
                                from_chat_id=from_chat_id,
                                message_ids=[cached_videos[index]],
                                message_thread_id=thread_id
                            )
                        else:
                            from HELPERS.logger import get_log_channel
                            from HELPERS.porn import is_porn
                            # Determine the correct log channel based on content type
                            is_nsfw = is_porn(url, "", "", None)
                            is_private_chat = getattr(original_message.chat, "type", None) == enums.ChatType.PRIVATE
                            is_paid = is_nsfw and is_private_chat
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_URL_ANALYSIS_LOG_MSG}: url={url}, is_nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}")
                            
                            # Get the correct log channel for reposting
                            if is_paid:
                                from_chat_id = get_log_channel("video", paid=True)
                                channel_type = "PAID"
                            elif is_nsfw:
                                from_chat_id = get_log_channel("video", nsfw=True)
                                channel_type = "NSFW"
                            else:
                                from_chat_id = get_log_channel("video")
                                channel_type = "regular"
                            
                            logger.info(f"[VIDEO CACHE] Channel selection: nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}, channel_type={channel_type}, from_chat_id={from_chat_id}")
                            
                            # Verify we're reposting from a valid log channel
                            valid_channels = [
                                get_log_channel("video"),
                                get_log_channel("video", nsfw=True),
                                get_log_channel("video", paid=True)
                            ]
                            if from_chat_id not in valid_channels:
                                logger.error(f"CRITICAL: Attempting to repost from wrong channel {from_chat_id}")
                                continue
                                
                            logger.info(f"[VIDEO CACHE] Reposting video {index} from channel {from_chat_id} to user {target_chat_id}, message_id={cached_videos[index]}")
                            forward_kwargs = {
                                'chat_id': target_chat_id,
                                'from_chat_id': from_chat_id,
                                'message_ids': [cached_videos[index]]
                            }
                            # Only apply thread_id in groups/channels, not in private chats
                            if getattr(original_message.chat, "type", None) != enums.ChatType.PRIVATE and thread_id:
                                forward_kwargs['message_thread_id'] = thread_id
                            app.forward_messages(**forward_kwargs)
                    except Exception as e:
                        logger.warning(f"askq_callback: cached video for index {index} not found: {e}")
            
            # If there are missing videos - download them
            if uncached_indices:
                logger.info(f"askq_callback: we start downloading the missing indexes: {uncached_indices}")
                new_start = uncached_indices[0]
                new_end = uncached_indices[-1]
                new_count = new_end - new_start + 1
                
                if data == "mp3":
                    # Delete processing message before starting download
                    delete_processing_message(app, user_id, proc_msg)
                    down_and_audio(app, original_message, url, tags, quality_key=used_quality_key, playlist_name=playlist_name, video_count=new_count, video_start_with=new_start, format_override="ba", cookies_already_checked=True, cached_video_info=None)
                else:
                    try:
                        # Form the correct format for the missing videos
                        if used_quality_key == "best":
                            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                        else:
                            quality_str = used_quality_key.replace('p', '')
                            quality_val = int(quality_str)
                            if quality_val and quality_val >= 4320:
                                prev = 2160
                            elif quality_val and quality_val >= 2160:
                                prev = 1440
                            elif quality_val and quality_val >= 1440:
                                prev = 1080
                            elif quality_val and quality_val >= 1080:
                                prev = 720
                            elif quality_val and quality_val >= 720:
                                prev = 480
                            elif quality_val and quality_val >= 480:
                                prev = 360
                            elif quality_val and quality_val >= 360:
                                prev = 240
                            elif quality_val and quality_val >= 240:
                                prev = 144
                            else:
                                prev = 0
                            format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                    except Exception as e:
                        logger.error(f"askq_callback: error forming format: {e}")
                        format_override = "bestvideo+bestaudio/best/bv+ba/best"
                    
                    # Delete processing message before starting download
                    delete_processing_message(app, user_id, proc_msg)
                    down_and_up(app, original_message, url, playlist_name, new_count, new_start, tags_text, force_no_title=False, format_override=format_override, quality_key=used_quality_key, cookies_already_checked=True, cached_video_info=None, clear_subs_cache_on_start=False)
            else:
                # All videos were in the cache
                app.send_message(target_chat_id, safe_get_messages(user_id).PLAYLIST_CACHE_SENT_MSG.format(cached=len(cached_videos), total=len(requested_indices)), reply_parameters=ReplyParameters(message_id=original_message.id))
                media_type = safe_get_messages(user_id).ALWAYS_ASK_AUDIO_TYPE_MSG if data == "mp3" else safe_get_messages(user_id).ALWAYS_ASK_VIDEO_TYPE_MSG
                log_msg = f"{media_type} playlist sent from cache to user.\nURL: {url}\nUser: {callback_query.from_user.first_name} ({user_id})"
                send_to_logger(original_message, log_msg)
            return
        else:
            # If there is no cache at all - download everything again
            logger.info(f"askq_callback: no cache found for any quality, starting new download")
            if data == "mp3":
                # Delete processing message before starting download
                delete_processing_message(app, user_id, proc_msg)
                down_and_audio(app, original_message, url, tags, quality_key=data, playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with, format_override="ba", cookies_already_checked=True, cached_video_info=None)
            else:
                try:
                    # Form the correct format for the new download
                    if data == "best":
                        format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                    else:
                        quality_str = data.replace('p', '')
                        quality_val = int(quality_str)
                        if quality_val and quality_val >= 4320:
                            prev = 2160
                        elif quality_val and quality_val >= 2160:
                            prev = 1440
                        elif quality_val and quality_val >= 1440:
                            prev = 1080
                        elif quality_val and quality_val >= 1080:
                            prev = 720
                        elif quality_val and quality_val >= 720:
                            prev = 480
                        elif quality_val and quality_val >= 480:
                            prev = 360
                        elif quality_val and quality_val >= 360:
                            prev = 240
                        elif quality_val and quality_val >= 240:
                            prev = 144
                        else:
                            prev = 0
                        format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                except ValueError:
                    format_override = "bestvideo+bestaudio/best/bv+ba/best"
                
                # Save selected quality to filters
                set_filter(user_id, "quality", data)
                
                # Delete processing message before starting download
                delete_processing_message(app, user_id, proc_msg)
                down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=data, cookies_already_checked=True, cached_video_info=None, clear_subs_cache_on_start=False)
            return
    # --- other logic for single files ---
    found_type = check_subs_availability(url, user_id, data, return_type=True)
    available_langs = _subs_check_cache.get(
        f"{url}_{user_id}_{'auto' if found_type == 'auto' else 'normal'}_langs",
        []
    )

    subs_enabled = is_subs_enabled(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)
    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
    
    # Check if send_as_file is enabled - if so, skip cache repost
    user_args = get_user_args(user_id)
    send_as_file = user_args.get("send_as_file", False)
    
    if not need_subs and not is_subs_always_ask(user_id) and not send_as_file:

        message_ids = get_cached_message_ids(url, data)
        # Если кэш по основному URL не найден, проверяем кэш по уникальной ссылке видео (для одиночных видео из плейлиста)
        if not message_ids:
            try:
                # Пытаемся загрузить info из кэша, чтобы получить уникальную ссылку видео
                cached_info = load_ask_info(user_id, url)
                if cached_info:
                    video_page_url = (
                        cached_info.get("webpage_url")
                        or cached_info.get("original_url")
                        or cached_info.get("url")
                        or cached_info.get("canonical_url")
                    )
                    # Если это не URL плейлиста, проверяем кэш по уникальной ссылке
                    if video_page_url and video_page_url != url:
                        message_ids = get_cached_message_ids(video_page_url, data)
                        if message_ids:
                            logger.info(f"🔍 [CACHE] Найдено одиночное видео в кэше по уникальной ссылке: {video_page_url}, quality: {data}")
                            # Обновляем url для дальнейшей обработки
                            url = video_page_url
            except Exception as e:
                logger.warning(f"⚠️ [CACHE] Ошибка при проверке кэша для одиночного видео: {e}")
        
        if message_ids:
            callback_query.answer("🚀 Found in cache! Forwarding instantly...", show_alert=False)
            # found_type = None
            try:
                try:
                    target_chat_id = getattr(original_message.chat, 'id', user_id)
                except Exception:
                    target_chat_id = user_id
                thread_id = getattr(original_message, 'message_thread_id', None)
                # Only apply thread_id in groups/channels, not in private chats
                if thread_id and getattr(original_message.chat, "type", None) != enums.ChatType.PRIVATE:
                    # Forward each to ensure thread id is applied
                    for mid in message_ids:
                        from HELPERS.logger import get_log_channel
                        from HELPERS.porn import is_porn
                        # Determine if this is paid media (NSFW in private chat)
                        is_nsfw = is_porn(url, "", "", None)
                        is_private_chat = getattr(original_message.chat, "type", None) == enums.ChatType.PRIVATE
                        is_paid = is_nsfw and is_private_chat
                        logger.info(f"[VIDEO CACHE] URL analysis: url={url}, is_nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}")
                        # Get the correct log channel for reposting
                        if is_paid:
                            from_chat_id = get_log_channel("video", paid=True)
                            channel_type = "PAID"
                        elif is_nsfw:
                            from_chat_id = get_log_channel("video", nsfw=True)
                            channel_type = "NSFW"
                        else:
                            from_chat_id = get_log_channel("video")
                            channel_type = "regular"
                        
                        logger.info(f"[VIDEO CACHE] Channel selection: nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}, channel_type={channel_type}, from_chat_id={from_chat_id}")
                        
                        # Check channel access restrictions
                        if is_private_chat and channel_type == "NSFW":
                            logger.info(f"[VIDEO CACHE] Access denied: NSFW cache not allowed in private chat, skipping message {mid}")
                            continue  # Skip this message
                        elif not is_private_chat and channel_type == "PAID":
                            logger.info(f"[VIDEO CACHE] Access denied: Paid cache not allowed in group chat, skipping message {mid}")
                            continue  # Skip this message
                        
                        app.forward_messages(
                            chat_id=target_chat_id,
                            from_chat_id=from_chat_id,
                            message_ids=[mid],
                            message_thread_id=thread_id
                        )
                else:
                    from HELPERS.logger import get_log_channel
                    from HELPERS.porn import is_porn
                    # Determine if this is paid media (NSFW in private chat)
                    is_nsfw = is_porn(url, "", "", None)
                    is_private_chat = getattr(original_message.chat, "type", None) == enums.ChatType.PRIVATE
                    is_paid = is_nsfw and is_private_chat
                    logger.info(f"[VIDEO CACHE] URL analysis: url={url}, is_nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}")
                    # Get the correct log channel for reposting
                    if is_paid:
                        from_chat_id = get_log_channel("video", paid=True)
                        channel_type = "PAID"
                    elif is_nsfw:
                        from_chat_id = get_log_channel("video", nsfw=True)
                        channel_type = "NSFW"
                    else:
                        from_chat_id = get_log_channel("video")
                        channel_type = "regular"
                    
                    logger.info(f"[VIDEO CACHE] Channel selection: nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}, channel_type={channel_type}, from_chat_id={from_chat_id}")
                    
                    # Check channel access restrictions
                    if is_private_chat and channel_type == "NSFW":
                        logger.info(f"[VIDEO CACHE] Access denied: NSFW cache not allowed in private chat, forcing re-download")
                        # Don't forward, let the function continue to download
                        return
                    elif not is_private_chat and channel_type == "PAID":
                        logger.info(f"[VIDEO CACHE] Access denied: Paid cache not allowed in group chat, forcing re-download")
                        # Don't forward, let the function continue to download
                        return
                    
                    app.forward_messages(
                        chat_id=target_chat_id,
                        from_chat_id=from_chat_id,
                        message_ids=message_ids
                    )
                app.send_message(target_chat_id, safe_get_messages(user_id).VIDEO_SENT_FROM_CACHE_MSG, reply_parameters=ReplyParameters(message_id=original_message.id))
                media_type = safe_get_messages(user_id).ALWAYS_ASK_AUDIO_TYPE_MSG if data == "mp3" else safe_get_messages(user_id).ALWAYS_ASK_VIDEO_TYPE_MSG
                log_msg = f"{media_type} sent from cache to user.\nURL: {url}\nUser: {callback_query.from_user.first_name} ({user_id})"
                send_to_logger(original_message, log_msg)
                return
            except Exception as e:
                logger.error(f"Error forwarding cached video: {e}")
                # found_type = check_subs_availability(url, user_id, data, return_type=True)
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                if not need_subs:
                    save_to_video_cache(url, data, [], clear=True)
                else:
                    logger.info("Video with subtitles (real subs found and needed) is not cached!")
                # Don't show error message if we successfully got video from cache
                # The video was already sent successfully in the try block
                askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs, proc_msg)
            
            # Удаляем Always Ask меню после обработки
            try:
                safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
            except Exception as e:
                logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_DELETE_ALWAYS_ASK_MENU_LOG_MSG}: {e}")
            return
    else:
        if is_subs_always_ask(user_id):
            logger.info(f"[VIDEO CACHE] Skipping cache check because Always Ask mode is enabled: url={url}, quality={data}")
        else:
            logger.info(f"[VIDEO CACHE] Skipping cache check because need_subs=True: url={url}, quality={data}")
    askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs, proc_msg)
    
    # Удаляем Always Ask меню после обработки
    try:
        safe_delete_messages(chat_id=callback_query.message.chat.id, message_ids=[callback_query.message.id])
    except Exception as e:
        logger.warning(f"Failed to delete Always Ask menu: {e}")

###########################

@app.on_callback_query(filters.regex(r"^fallback_gallery_dl\|"))
def fallback_gallery_dl_callback(app, callback_query):
    """Handle fallback to gallery-dl when yt-dlp fails"""
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    try:
        user_id = callback_query.from_user.id
        data_parts = callback_query.data.split("|")
        url_hash = data_parts[1]  # Extract URL or URL hash from callback data
        
        # Get original URL data from callback
        url_data = get_original_data_from_callback("fallback_gallery_dl", callback_query.data)
        url_parts = url_data.split("|")
        url = url_parts[0]
        
        # Extract range from URL data if available
        if len(url_parts) >= 3:
            video_start_with = int(url_parts[1])
            video_end_with = int(url_parts[2])
            logger.info(f"[FALLBACK DEBUG] Extracted range from callback data: {video_start_with}-{video_end_with}")
        else:
            video_start_with = 1
            video_end_with = 1
            logger.info(f"[FALLBACK DEBUG] No range in callback data, using default: 1-1")
        
        # Extract chat_id from URL data if available
        if len(url_parts) >= 4:
            original_chat_id = int(url_parts[3])
        else:
            original_chat_id = callback_query.message.chat.id
        
        logger.info(f"Fallback to gallery-dl requested for user {user_id}: {url} (range: {video_start_with}-{video_end_with})")
        
        # Answer callback query
        callback_query.answer("🔄 Switching to gallery-dl...")
        
        # Delete the fallback message after clicking the button
        try:
            callback_query.message.delete()
            logger.info(f"Deleted fallback gallery-dl message for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to delete fallback gallery-dl message: {e}")
        
        # Import gallery-dl command
        from COMMANDS.image_cmd import image_command
        from HELPERS.safe_messeger import fake_message
        
        # Create fallback command with range if available
        if video_start_with and video_end_with and (video_start_with != 1 or video_end_with != 1):
            # Convert *1*20 format to 1-20 format for gallery-dl
            fallback_text = f"/img {video_start_with}-{video_end_with} {url}"
            logger.info(f"[FALLBACK DEBUG] Creating fallback command with range: {video_start_with}-{video_end_with}")
        else:
            fallback_text = f"/img {url}"
            logger.info(f"[FALLBACK DEBUG] Creating fallback command without range")
        
        # Сохраняем message_thread_id из оригинального сообщения
        message_thread_id = getattr(callback_query.message, 'message_thread_id', None)
        fake_msg = fake_message(fallback_text, user_id, original_chat_id=original_chat_id, message_thread_id=message_thread_id, original_message=callback_query.message)
        logger.info(f"[FALLBACK] fake_msg.chat.id={fake_msg.chat.id}, fake_msg.message_thread_id={fake_msg.message_thread_id}, callback_query.message.chat.id={callback_query.message.chat.id}, callback_query.message.message_thread_id={getattr(callback_query.message, 'message_thread_id', None)}")
        
        # Execute gallery-dl command
        logger.info(f"About to execute image_command for user {user_id} with fake_msg: {fallback_text}")
        image_command(app, fake_msg)
        
        logger.info(f"Gallery-dl fallback executed for user {user_id}: {fallback_text}")
        
    except Exception as e:
        logger.error(f"Error in fallback_gallery_dl_callback: {e}")
        try:
            callback_query.answer("❌ Error switching to gallery-dl", show_alert=True)
        except:
            pass

###########################

# @reply_with_keyboard
def show_manual_quality_menu(app, callback_query):
    messages = safe_get_messages(callback_query.from_user.id)
    """Show manual quality selection menu when automatic detection fails"""
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    user_id = callback_query.from_user.id
    subs_available = ""
    found_type = None
    # Extract URL and tags from the callback
    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_MSG, show_alert=True)
        callback_query.message.delete()
        return
    
    url = None
    if callback_query.message.caption_entities:
        for entity in callback_query.message.caption_entities:
            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                url = entity.url
                break
    if not url and callback_query.message.reply_to_message:
        url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    
    if not url:
        callback_query.answer("❌ Error: URL not found.", show_alert=True)
        callback_query.message.delete()
        return
    
    tags = []
    caption_text = callback_query.message.caption
    if caption_text:
        tag_matches = re.findall(r'#\S+', caption_text)
        if tag_matches:
            tags = tag_matches
    tags_text = ' '.join(tags)
    # NSFW detection for paid media warning
    try:
        is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
    except Exception:
        is_nsfw = False
    
    # Check if we're in a private chat (paid media only works in private chats)
    is_private_chat = getattr(callback_query.message.chat, "type", None) == enums.ChatType.PRIVATE
    
    # Check if user has send_as_file enabled
    user_args = get_user_args(user_id)
    send_as_file = user_args.get("send_as_file", False)
    
    # Check if it's a playlist
    original_text = original_message.text or original_message.caption or ""
    is_playlist = is_playlist_with_range(original_text)
    playlist_range = None
    if is_playlist:
        _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
        playlist_range = (video_start_with, video_end_with)
        cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url)) if not send_as_file else set()
    else:
        cached_qualities = get_cached_qualities(url) if not send_as_file else set()
    
    # Create manual quality buttons
    manual_qualities = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p"]
    buttons = []
    
    for quality in manual_qualities:
        if is_playlist and playlist_range:
            # Правильное формирование indices для отрицательных индексов
            start, end = playlist_range
            if start < 0 and end < 0:
                # Для отрицательных индексов в обратном порядке
                if abs(start) < abs(end):
                    indices = list(range(start, end - 1, -1))
                else:
                    indices = list(range(start, end + 1, 1))
            elif start > end:
                # Для обратного порядка
                indices = list(range(start, end - 1, -1))
            else:
                # Для прямого порядка
                indices = list(range(start, end + 1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality, indices)
            total = len(indices)
            icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
            button_text = f"{icon}{quality}{postfix}"
        else:
            icon = "🚀" if (quality in cached_qualities and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            button_text = f"{icon}{quality}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality}"))

    # {safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} Quality
    if is_playlist and playlist_range:
        # Правильное формирование indices для отрицательных индексов
        start, end = playlist_range
        if start < 0 and end < 0:
            if abs(start) < abs(end):
                indices = list(range(start, end - 1, -1))
            else:
                indices = list(range(start, end + 1, 1))
        elif start > end:
            indices = list(range(start, end - 1, -1))
        else:
            indices = list(range(start, end + 1))
        n_cached = get_cached_playlist_count(get_clean_playlist_url(url), "best", indices)
        total = len(indices)
        icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
        postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
        button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} Quality{postfix}"
    else:
        icon = "🚀" if ("best" in cached_qualities and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
        button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} Quality"
    buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|manual_best"))
    
    # Form rows of 3 buttons
    keyboard_rows = []
    for i in range(0, len(buttons), 3):
        keyboard_rows.append(buttons[i:i+3])
    
    # Add mp3 button
    quality_key = "mp3"
    if is_playlist and playlist_range:
        # Правильное формирование indices для отрицательных индексов
        start, end = playlist_range
        if start < 0 and end < 0:
            if abs(start) < abs(end):
                indices = list(range(start, end - 1, -1))
            else:
                indices = list(range(start, end + 1, 1))
        elif start > end:
            indices = list(range(start, end - 1, -1))
        else:
            indices = list(range(start, end + 1))
        n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
        total = len(indices)
        icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "🎧")
        postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
        button_text = f"{icon} audio (mp3){postfix}"
    else:
        icon = "🚀" if (quality_key in cached_qualities and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "🎧")
        button_text = f"{icon} audio (mp3)"
    keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality_key}")])
    
    # Add subtitles only button if enabled
    subs_enabled = is_subs_enabled(user_id)
    if subs_enabled and is_youtube_url(url):
        found_type = check_subs_availability(url, user_id, return_type=True)
        auto_mode = get_user_subs_auto_mode(user_id)
        need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
        
        if need_subs:
            keyboard_rows.append([InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_SUB_ONLY_BUTTON_MSG, callback_data="askq|subs_only")])
    
    # Add Back and close buttons
    keyboard_rows.append([
        InlineKeyboardButton(safe_get_messages(user_id).BACK_BUTTON_TEXT, callback_data="askq|manual_back"),
        InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askq|close")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_rows)
    
    # Get video title for caption - try cached info first
    try:
        cached_info = load_ask_info(user_id, url)
        if cached_info:
            title = cached_info.get('title', 'Video')
            video_title = title
            logger.info(f"✅ [OPTIMIZATION] Using cached title for caption")
        else:
            info = get_video_formats(url, user_id, cookies_already_checked=True)
            title = info.get('title', 'Video')
            video_title = title
            logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info for title")
    except:
        video_title = safe_get_messages(user_id).ALWAYS_ASK_VIDEO_TITLE_MSG
    
    # Form caption
    cap = f"<b>{video_title}</b>\n"
    if tags_text:
        cap += f"{tags_text}"
    try:
        is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
    except Exception:
        is_nsfw = False
    if is_nsfw and is_private_chat:
        cap += "\n<b>⭐️ — 🔞NSFW is paid (⭐️$0.02)</b>\n"
    if is_nsfw and is_private_chat:
        cap += "\n<b>⭐️ — 🔞NSFW is paid (⭐️$0.02)</b>\n"
    cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_MANUAL_QUALITY_SELECTION_MSG}</b>\n"
    cap += f"\n<i>{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_QUALITY_MANUALLY_MSG}</i>\n"
    
    # Update current menu; if MESSAGE_ID_INVALID, send new message
    if callback_query and getattr(callback_query, 'message', None):
        try:
            if callback_query.message.photo:
                callback_query.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            else:
                callback_query.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            callback_query.answer("Меню выбора качества открыто.")
            return
        except Exception as ee:
            # Если не получилось отредактировать (например, MESSAGE_ID_INVALID) — шлём новое сообщение
            if 'MESSAGE_ID_INVALID' not in str(ee):
                logger.warning(f"Manual menu edit failed, fallback to new message: {ee}")
    # Fallback: отправляем новое сообщение, привязанное к исходному
    try:
        chat_id = callback_query.message.chat.id if callback_query and getattr(callback_query, 'message', None) else user_id
        ref_id = original_message.id if original_message else None
        app.send_message(chat_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard,
                         reply_parameters=ReplyParameters(message_id=ref_id))
        if callback_query:
            callback_query.answer("Меню выбора качества открыто.")
    except Exception as e2:
        logger.error(f"Error showing manual quality menu (fallback): {e2}")
        if callback_query:
            callback_query.answer("❌ Не удалось открыть меню выбора качества.", show_alert=True)

def show_other_qualities_menu(app, callback_query, page=0):
    messages = safe_get_messages(callback_query.from_user.id)
    """Show all available qualities from yt-dlp -F output with pagination"""
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    user_id = callback_query.from_user.id
    
    # Local safe wrapper to avoid noisy QueryIdInvalid when answering twice/late
    def _safe_answer(text, show_alert=False):
        messages = safe_get_messages(user_id)
        try:
            callback_query.answer(text, show_alert=show_alert)
        except Exception as e:
            if 'QUERY_ID_INVALID' in str(e).upper():
                return
            try:
                # Some environments provide .MESSAGE_ID_INVALID
                if 'MESSAGE_ID_INVALID' in str(e).upper():
                    return
            except Exception:
                pass
            raise
    
    # Check if we have cached formats for this URL
    url = None
    original_message = callback_query.message.reply_to_message
    if original_message:
        url_text = original_message.text or (original_message.caption or "")
        import re as _re
        m = _re.search(r'https?://[^\s\*#]+', url_text)
        url = m.group(0) if m else url_text
    
    if url:
        # Clean up old format cache files before checking current cache
        try:
            user_dir = os.path.join("users", str(user_id))
            create_directory(user_dir)
            
            # Get download directory if available
            user_download_dir = get_user_download_dir(user_id)
            
            # Remove all old format cache files except current one
            import glob
            # Use download directory if available, otherwise fallback to user directory
            if user_download_dir and os.path.exists(user_download_dir):
                format_cache_pattern = os.path.join(user_download_dir, "formats_cache_*.json")
                current_cache_file = os.path.join(user_download_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
            else:
                format_cache_pattern = os.path.join(user_dir, "formats_cache_*.json")
                current_cache_file = os.path.join(user_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
            old_cache_files = glob.glob(format_cache_pattern)
            
            for cache_file in old_cache_files:
                if cache_file != current_cache_file:  # Don't delete current cache
                    try:
                        os.remove(cache_file)
                        logger.info(f"{LoggerMsg.ALWAYS_ASK_CLEANED_UP_OLD_FORMAT_CACHE_LOG_MSG}: {cache_file}")
                    except Exception as e:
                        logger.warning(f"{LoggerMsg.ALWAYS_ASK_FAILED_TO_REMOVE_OLD_CACHE_FILE_LOG_MSG} {cache_file}: {e}")
                        
            if len(old_cache_files) > 1:  # More than just current cache
                logger.info(f"Cleaned up {len(old_cache_files) - 1} old format cache files for user {user_id}")
        except Exception as e:
            logger.warning(f"Error cleaning up old format cache files: {e}")
        
        cache_file = current_cache_file
        if os.path.exists(cache_file):
            # Use cached formats for any page
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    format_lines = cached_data.get('formats', [])
                    if format_lines:
                        # Show cached formats immediately
                        logger.info(f"Using cached formats for page {page + 1}, {len(format_lines)} formats found")
                        show_formats_from_cache(app, callback_query, format_lines, page, url)
                        return
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                pass  # Fall back to fresh fetch
    
    # Extract URL from the callback
    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_MSG, show_alert=True)
        callback_query.message.delete()
        return
    
    url = None
    if callback_query.message.caption_entities:
        for entity in callback_query.message.caption_entities:
            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                url = entity.url
                break
    if not url and callback_query.message.reply_to_message:
        url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    
    if not url:
        callback_query.answer("❌ Error: URL not found.", show_alert=True)
        callback_query.message.delete()
        return
    
    # Extract tags
    tags = []
    caption_text = callback_query.message.caption
    if caption_text:
        tag_matches = re.findall(r'#\S+', caption_text)
        if tag_matches:
            tags = tag_matches
    tags_text = ' '.join(tags)
    try:
        is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
    except Exception:
        is_nsfw = False
    
    # Check if we're in a private chat (paid media only works in private chats)
    is_private_chat = getattr(callback_query.message.chat, "type", None) == enums.ChatType.PRIVATE
    
    # Check if it's a playlist
    original_text = original_message.text or original_message.caption or ""
    is_playlist = is_playlist_with_range(original_text)
    
    # Get video title for caption - try cached info first
    try:
        cached_info = load_ask_info(user_id, url)
        if cached_info:
            title = cached_info.get('title', 'Video')
            video_title = title
            logger.info(f"✅ [OPTIMIZATION] Using cached title for caption")
        else:
            info = get_video_formats(url, user_id, cookies_already_checked=True)
            title = info.get('title', 'Video')
            video_title = title
            logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info for title")
    except:
        video_title = safe_get_messages(user_id).ALWAYS_ASK_VIDEO_TITLE_MSG
    
    # Form caption
    cap = f"<b>{video_title}</b>\n"
    if tags_text:
        cap += f"{tags_text}"
    if is_nsfw and is_private_chat:
        cap += "\n<b>⭐️ — 🔞NSFW is paid (⭐️$0.02)</b>\n"
    cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_ALL_AVAILABLE_FORMATS_MSG}</b>\n"
    cap += f"\n<i>{safe_get_messages(user_id).PAGE_NUMBER_MSG.format(page=page + 1)}</i>\n"
    
    # Get all formats using yt-dlp -F
    try:
        import subprocess
        import sys
        
        # Create cache file path
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        
        # Get download directory if available
        user_download_dir = get_user_download_dir(user_id)
        
        # Use download directory if available, otherwise fallback to user directory
        if user_download_dir and os.path.exists(user_download_dir):
            cache_file = os.path.join(user_download_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
        else:
            cache_file = os.path.join(user_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
        
        # Check if we have cached formats
        format_lines = []
        if os.path.exists(cache_file):
            # Use cached data if available
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    format_lines = cached_data.get('formats', [])
                    if format_lines:
                        logger.info(f"Using cached formats from {cache_file}")
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
        
        if not format_lines:
            # Run yt-dlp -F to get all formats
            logger.info(f"Running yt-dlp -F for URL: {url}")
            
            # Build command with cookies if available (use same yt-dlp as Python API)
            cmd = [sys.executable, "-m", "yt_dlp"]
            # Add PO token extractor-args for CLI if applicable (YouTube only)
            cmd.extend(build_cli_extractor_args(url))
            # -F list formats
            cmd.append("-F")
            
            # Add cookies file if it exists
            user_cookie_file = os.path.join("users", str(user_id), "cookie.txt")
            if os.path.exists(user_cookie_file):
                cmd.extend(["--cookies", user_cookie_file])
                logger.info(f"Using cookies from: {user_cookie_file}")
            else:
                logger.info("No user cookie file found, using default")
            
            # Add proxy if needed for this domain
            from HELPERS.proxy_helper import is_proxy_domain, get_proxy_config
            if is_proxy_domain(url):
                proxy_config = get_proxy_config()
                if proxy_config and 'proxy' in proxy_config:
                    proxy_url = proxy_config['proxy']
                    cmd.extend(["--proxy", proxy_url])
                    logger.info(f"Added proxy to yt-dlp command: {proxy_url}")
            
            cmd.append(url)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            logger.info(f"yt-dlp -F completed with return code: {result.returncode}")
            if result.returncode != 0:
                logger.warning(f"yt-dlp -F failed with stderr: {result.stderr}")
                # Fallback: try to get formats from cached info
                info = get_video_formats(url, user_id, cookies_already_checked=True)
                formats = info.get('formats', [])
                format_lines = []
                for f in formats:
                    format_id = f.get('format_id', 'unknown')
                    ext = f.get('ext', 'unknown')
                    resolution = f.get('resolution', 'unknown')
                    proto = f.get('protocol', 'https')
                    vcodec = f.get('vcodec', 'none')
                    
                    # Validate format_id - should not contain brackets or special characters
                    if format_id and not format_id.startswith('[') and not format_id.startswith('(') and format_id != 'unknown':
                        # Skip non-media formats
                        if ext.lower() in ['mhtml', 'html', 'txt', 'json', 'xml']:
                            continue
                        
                        # Store format info for button creation
                        format_lines.append(f"{format_id:<12} {ext:<8} {resolution:<12} {proto:<12} {vcodec}")
                        logger.debug(f"Fallback format: {format_id} | {ext} | {resolution} | {proto} | {vcodec}")
                    else:
                        logger.warning(f"Skipping invalid fallback format_id: {format_id}")
                
                # If no formats found, create basic format list
                if not format_lines:
                    # Create basic format list based on common patterns
                    basic_formats = [
                        "best",
                        "worst", 
                        "bestvideo+bestaudio",
                        "bv+ba"
                    ]
                    for fmt in basic_formats:
                        format_lines.append(f"{fmt:<12} mp4 unknown https none")
                
                # Cache the fallback formats for future use
                if format_lines:
                    try:
                        cache_data = {
                            'url': url,
                            'timestamp': datetime.now().isoformat(),
                            'formats': format_lines
                        }
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Cached {len(format_lines)} fallback formats to {cache_file}")
                    except Exception as e:
                        logger.warning(f"Failed to cache fallback formats: {e}")
            else:
                # Parse yt-dlp output
                output_lines = result.stdout.strip().split('\n')
                format_lines = []
                logger.info(f"Parsing yt-dlp output: {len(output_lines)} lines")
                
                for line in output_lines:
                    if line.strip() and not line.startswith('ID') and not line.startswith('─') and not line.startswith('format_id'):
                        # Parse format line (ID, EXT, RESOLUTION, FPS, FILESIZE, TBR, PROTO, VCODEC, VBR, ACODEC, ABR, ASR, MORE INFO)
                        parts = line.split()
                        if len(parts) >= 7:  # Need at least ID, EXT, RESOLUTION, FPS, FILESIZE, TBR, PROTO
                            format_id = parts[0]
                            ext = parts[1] if len(parts) > 1 else 'unknown'
                            resolution = parts[2] if len(parts) > 2 else '—'
                            filesize = parts[4] if len(parts) > 4 else 'unknown'
                            proto = parts[6] if len(parts) > 6 else 'unknown'
                            vcodec = 'none'
                            
                            # Remove ≈ symbol from filesize
                            if filesize.startswith('≈'):
                                filesize = filesize[1:].strip()
                            
                            # Find VCODEC (usually around position 8-9)
                            for j, part in enumerate(parts):
                                if j and j > 7 and part and part != 'none' and not part.startswith('mp4a') and not part.startswith('—') and not part.startswith('audio') and not part.startswith('≈'):
                                    # Check if this looks like a video codec
                                    if any(codec in part.lower() for codec in ['avc', 'vp9', 'av1', 'h264', 'h265', 'hevc']):
                                        vcodec = part
                                        break
                            
                            # Skip non-media formats
                            if ext.lower() in ['mhtml', 'html', 'txt', 'json', 'xml']:
                                continue
                            
                            # Validate format_id - should not contain brackets or special characters
                            if format_id and not format_id.startswith('[') and not format_id.startswith('('):
                                # Store complete original line for full data preservation
                                format_lines.append(line.strip())
                                logger.debug(f"Stored complete format line: {line.strip()}")
                            else:
                                logger.warning(f"Skipping invalid format_id: {format_id}")
                
                logger.info(f"Parsed {len(format_lines)} formats from yt-dlp output")
                
                # Cache the formats for future use
                if format_lines:
                    try:
                        cache_data = {
                            'url': url,
                            'timestamp': datetime.now().isoformat(),
                            'formats': format_lines
                        }
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Cached {len(format_lines)} formats to {cache_file}")
                    except Exception as e:
                        logger.warning(f"Failed to cache formats: {e}")
        
        # Pagination: 10 formats per page (1 row × 10 columns)
        formats_per_page = 10
        total_formats = len(format_lines)
        total_pages = (total_formats + formats_per_page - 1) // formats_per_page
        
        start_idx = page * formats_per_page
        end_idx = min(start_idx + formats_per_page, total_formats)
        page_formats = format_lines[start_idx:end_idx]
        
        # Check if user has send_as_file enabled
        user_args = get_user_args(user_id)
        send_as_file = user_args.get("send_as_file", False)
        
        # Get cached qualities to show rocket emoji for cached formats (skip if send_as_file is enabled)
        cached_qualities = set()
        if not send_as_file:
            try:
                cached_qualities = get_cached_qualities(url)
            except Exception:
                pass
        
        # Build keyboard with format buttons (1 row × 10 columns max)
        keyboard_rows = []
        row = []
        for i, format_line in enumerate(page_formats):
            format_id = format_line.split()[0].strip()
            
            # Additional validation - skip invalid format IDs
            if format_id and not format_id.startswith('[') and not format_id.startswith('(') and format_id != 'unknown':
                # Extract only needed data for button display
                button_parts = extract_button_data(format_line)
                
                if button_parts:  # Only create button if we have valid data
                    # Join with | separator
                    button_text = ' | '.join(button_parts)
                    
                    # Add rocket emoji if format is cached, or paid emoji for NSFW
                    if format_id in cached_qualities and not is_nsfw:
                        button_text = f"🚀 {button_text}"
                    elif is_nsfw and is_private_chat:
                        button_text = f"1⭐️ {button_text}"
                    
                    # Limit button text length
                    if len(button_text) > 40:
                        button_text = button_text[:37] + "..."
                    
                    # Create safe callback data
                    callback_data = create_safe_callback_data("askq|other_id", format_id)
                    logger.info(f"Created callback_data '{callback_data}' for format_id '{format_id}'")
                    
                    # Each button goes in its own row (1 column layout)
                    keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_PREV_BUTTON_MSG, callback_data=f"askq|other_page_{page-1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_NEXT_BUTTON_MSG, callback_data=f"askq|other_page_{page+1}"))
        if nav_row:
            keyboard_rows.append(nav_row)
        
        # Add back and close buttons
        keyboard_rows.append([
            InlineKeyboardButton(safe_get_messages(user_id).BACK_BUTTON_TEXT, callback_data="askq|other_back"),
            InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askq|close")
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        
        # Update message
        try:
            if callback_query.message.photo:
                callback_query.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            else:
                callback_query.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            _safe_answer(f"Formats page {page + 1}/{total_pages}")
        except Exception as e:
            # Fallback: send new message
            try:
                chat_id = callback_query.message.chat.id
                ref_id = original_message.id if original_message else None
                app.send_message(chat_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard,
                               reply_parameters=ReplyParameters(message_id=ref_id))
                _safe_answer(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMATS_PAGE_MSG} {page + 1}/{total_pages}")
            except Exception as e2:
                logger.error(f"Error showing other qualities menu: {e2}")
                _safe_answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_SHOWING_FORMATS_MENU_MSG, show_alert=True)
        
            # Clean up temp file
        # No temp file used here; keep block for future extensions
            
    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        _safe_answer(safe_get_messages(user_id).ALWAYS_ASK_ERROR_GETTING_FORMATS_MSG, show_alert=True)
        # Show error message
        error_cap = f"<b>{video_title}</b>\n\n{safe_get_messages(user_id).ALWAYS_ASK_ERROR_GETTING_AVAILABLE_FORMATS_MSG}\n{safe_get_messages(user_id).ALWAYS_ASK_PLEASE_TRY_AGAIN_LATER_MSG}"
        try:
            if callback_query.message.photo:
                callback_query.edit_message_caption(caption=error_cap, parse_mode=enums.ParseMode.HTML)
            else:
                callback_query.edit_message_text(text=error_cap, parse_mode=enums.ParseMode.HTML)
        except:
            pass

def show_formats_from_cache(app, callback_query, format_lines, page, url):
    messages = safe_get_messages(callback_query.from_user.id)
    """Show formats from cached data for fast navigation"""
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    user_id = callback_query.from_user.id
    logger.info(f"Showing formats from cache for user {user_id}, page {page}, {len(format_lines)} formats")
    
    # Get video title for caption - try cached info first
    try:
        cached_info = load_ask_info(user_id, url)
        if cached_info:
            title = cached_info.get('title', 'Video')
            video_title = title
            logger.info(f"✅ [OPTIMIZATION] Using cached title for caption")
        else:
            info = get_video_formats(url, user_id, cookies_already_checked=True)
            title = info.get('title', 'Video')
            video_title = title
            logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info for title")
    except:
        video_title = safe_get_messages(user_id).ALWAYS_ASK_VIDEO_TITLE_MSG
    
    # Form caption
    cap = f"<b>{video_title}</b>\n"
    cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_ALL_AVAILABLE_FORMATS_MSG}</b>\n"
    try:
        orig_text = callback_query.message.reply_to_message.text or callback_query.message.reply_to_message.caption or ""
    except Exception:
        orig_text = ""
    is_nsfw = isinstance(orig_text, str) and ('#nsfw' in orig_text.lower())
    # Check if we're in a private chat (paid media only works in private chats)
    is_private_chat = getattr(callback_query.message.chat, "type", None) == enums.ChatType.PRIVATE
    if isinstance(url, str) and is_nsfw and is_private_chat:
        cap += "\n<b>⭐️ — 🔞NSFW is paid (⭐️$0.02)</b>\n"
    cap += f"\n<i>{safe_get_messages(user_id).PAGE_NUMBER_MSG.format(page=page + 1)}</i>\n"
    
    # Pagination: 10 formats per page (1 column × 10 rows)
    formats_per_page = 10
    total_formats = len(format_lines)
    total_pages = (total_formats + formats_per_page - 1) // formats_per_page
    
    start_idx = page * formats_per_page
    end_idx = min(start_idx + formats_per_page, total_formats)
    page_formats = format_lines[start_idx:end_idx]
    
    # Check if user has send_as_file enabled
    user_args = get_user_args(user_id)
    send_as_file = user_args.get("send_as_file", False)
    
    # Get cached qualities to show rocket emoji for cached formats (skip if send_as_file is enabled)
    cached_qualities = set()
    if not send_as_file:
        try:
            cached_qualities = get_cached_qualities(url)
        except Exception:
            pass
    
    # Build keyboard with format buttons (1 column × 10 rows max)
    keyboard_rows = []
    for i, format_line in enumerate(page_formats):
        format_id = format_line.split()[0].strip()
        
        # Additional validation - skip invalid format IDs
        if format_id and not format_id.startswith('[') and not format_id.startswith('(') and format_id != 'unknown':
            # Extract only needed data for button display
            button_parts = extract_button_data(format_line)
            
            if button_parts:  # Only create button if we have valid data
                # Join with | separator
                button_text = ' | '.join(button_parts)
                
                # Add rocket emoji if format is cached, or paid emoji for NSFW
                if format_id in cached_qualities and not is_nsfw:
                    button_text = f"🚀 {button_text}"
                elif is_nsfw and is_private_chat:
                    button_text = f"1⭐️ {button_text}"
                
                # Limit button text length
                if len(button_text) > 64:
                    button_text = button_text[:61] + "..."
                
                # Create safe callback data
                callback_data = create_safe_callback_data("askq|other_id", format_id)
                logger.info(f"Created callback_data '{callback_data}' for format_id '{format_id}'")
                
                # Each button goes in its own row (1 column layout)
                keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        else:
            logger.warning(f"Invalid format line structure: {format_line}")
    else:
        logger.warning(f"Skipping invalid format_id for button: {format_id}")
    
    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_PREV_BUTTON_MSG, callback_data=f"askq|other_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_NEXT_BUTTON_MSG, callback_data=f"askq|other_page_{page+1}"))
    if nav_row:
        keyboard_rows.append(nav_row)
    
    # Add back and close buttons
    keyboard_rows.append([
        InlineKeyboardButton("🔙Back", callback_data="askq|other_back"),
        InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="askq|close")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_rows)
    
    # Update message
    try:
        if callback_query.message.photo:
            callback_query.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        else:
            callback_query.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMATS_PAGE_FROM_CACHE_MSG} {page + 1}/{total_pages} {safe_get_messages(user_id).ALWAYS_ASK_FROM_CACHE_MSG}")
    except Exception as e:
        # Fallback: send new message
        try:
            chat_id = callback_query.message.chat.id
            ref_id = callback_query.message.reply_to_message.id if callback_query.message.reply_to_message else None
            app.send_message(chat_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard,
                           reply_parameters=ReplyParameters(message_id=ref_id) if ref_id else None)
            callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_FORMATS_PAGE_FROM_CACHE_MSG} {page + 1}/{total_pages} {safe_get_messages(user_id).ALWAYS_ASK_FROM_CACHE_MSG}")
        except Exception as e2:
            logger.error(f"Error showing cached formats: {e2}")
            callback_query.answer("❌ Error showing formats menu", show_alert=True)

# --- Always ask processing ---
def sort_quality_key(quality_key):
    """Sort qualities by increasing resolution from lower to higher"""
    if quality_key == "best":
        return 999999  # best is always at the end
    elif quality_key == "mp3":
        return -1  # mp3 at the very beginning
    else:
        # Extract a number from a string (e.g. "720p" -> 720)
        try:
            return int(quality_key.replace('p', ''))
        except ValueError:
            return 0  # for unknown formats

def create_cached_qualities_menu(app, message, url, tags, proc_msg, user_id, original_text, is_playlist, playlist_range):
    messages = safe_get_messages(user_id)
    """
    Создает меню качества из кэшированных данных когда не удается получить новые.
    
    Args:
        app: Экземпляр приложения
        message: Сообщение пользователя
        url: URL видео
        tags: Теги
        proc_msg: Сообщение о процессе
        user_id: ID пользователя
        original_text: Оригинальный текст сообщения
        is_playlist: Является ли плейлистом
        playlist_range: Диапазон плейлиста
        
    Returns:
        bool: True если меню создано успешно, False если нет кэшированных данных
    """
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    try:
        logger.info(f"Attempting to create menu from cached qualities for user {user_id}")
        
        # Check if user has fixed format via /args
        user_fixed_format = None
        try:
            user_args = get_user_args(user_id)
            user_video_format = user_args.get('video_format', 'mp4')
            user_merge_format = user_args.get('merge_output_format', 'mp4')
            
            # If user has set video_format to something other than mp4, it's fixed
            if user_video_format != 'mp4':
                user_fixed_format = user_video_format
            # If user has set merge_output_format to something other than mp4, it's fixed
            elif user_merge_format != 'mp4':
                user_fixed_format = user_merge_format
        except Exception:
            pass
        
        # Check if user has send_as_file enabled
        user_args = get_user_args(user_id)
        send_as_file = user_args.get("send_as_file", False)
        
        # Получаем кэшированные качества (skip if send_as_file is enabled)
        if send_as_file:
            cached_qualities = set()
        elif is_playlist and playlist_range:
            cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url))
        else:
            cached_qualities = get_cached_qualities(url)
        
        if not cached_qualities:
            logger.info(f"No cached qualities found for user {user_id}")
            return False
        
        logger.info(f"Found cached qualities for user {user_id}: {list(cached_qualities)}")
        
        # Получаем базовую информацию о видео из кэша
        try:
            info = load_ask_info(user_id, url)
            if not info:
                # Пробуем получить минимальную информацию
                info = {'title': 'Video (cached)', 'id': 'cached'}
        except Exception:
            info = {'title': 'Video (cached)', 'id': 'cached'}
        
        title = info.get('title', 'Video (cached)')
        tags_text = generate_final_tags(url, tags, info)
        
        # Определяем NSFW
        try:
            is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
        except Exception:
            is_nsfw = False
        
        # Check if we're in a private chat (paid media only works in private chats)
        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
        
        # Создаем заголовок
        cap = f"<b>{title}</b>\n"
        if tags_text:
            cap += f"{tags_text}"
        if is_nsfw and is_private_chat:
            cap += "\n<b>⭐️ — 🔞NSFW is paid (⭐️$0.02)</b>\n"
        if user_fixed_format:
                cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG}: {user_fixed_format.upper()}</b>\n"
        cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_AVAILABLE_QUALITIES_FROM_CACHE_MSG}</b>\n"
        cap += f"\n<i>{safe_get_messages(user_id).ALWAYS_ASK_USING_CACHED_QUALITIES_MSG}</i>\n"
        
        # Создаем кнопки качества из кэша
        buttons = []
        
        # Добавляем кнопки для каждого кэшированного качества
        quality_order = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p", "mp3"]
        
        for quality_key in quality_order:
            if quality_key in cached_qualities:
                if is_playlist and playlist_range:
                    # Правильное формирование indices для отрицательных индексов
                    start, end = playlist_range
                    if start < 0 and end < 0:
                        if abs(start) < abs(end):
                            indices = list(range(start, end - 1, -1))
                        else:
                            indices = list(range(start, end + 1, 1))
                    elif start > end:
                        indices = list(range(start, end - 1, -1))
                    else:
                        indices = list(range(start, end + 1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
                    button_text = f"{icon}{quality_key}{postfix}"
                else:
                    # Проверяем кэш для одиночного видео
                    is_cached = quality_key in cached_qualities
                    # Дополнительно проверяем кэш по уникальной ссылке видео, если это видео из плейлиста
                    if not is_cached:
                        try:
                            cached_info = load_ask_info(user_id, url)
                            if cached_info:
                                video_page_url = (
                                    cached_info.get("webpage_url")
                                    or cached_info.get("original_url")
                                    or cached_info.get("url")
                                    or cached_info.get("canonical_url")
                                )
                                # Если это не URL плейлиста, проверяем кэш по уникальной ссылке
                                if video_page_url and video_page_url != url:
                                    single_video_cached = get_cached_message_ids(video_page_url, quality_key)
                                    if single_video_cached:
                                        is_cached = True
                                        logger.info(f"🔍 [CACHE] Найдено одиночное видео в кэше по уникальной ссылке: {video_page_url}, quality: {quality_key}")
                        except Exception as e:
                            logger.warning(f"⚠️ [CACHE] Ошибка при проверке кэша для одиночного видео: {e}")
                    
                    icon = "🚀" if (is_cached and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    button_text = f"{icon}{quality_key}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        
        # Всегда добавляем {safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} Quality
        quality_key = "best"
        if is_playlist and playlist_range:
            # Правильное формирование indices для отрицательных индексов
            start, end = playlist_range
            if start < 0 and end < 0:
                if abs(start) < abs(end):
                    indices = list(range(start, end - 1, -1))
                else:
                    indices = list(range(start, end + 1, 1))
            elif start > end:
                indices = list(range(start, end - 1, -1))
            else:
                indices = list(range(start, end + 1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
            total = len(indices)
            icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
            button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG}{postfix}"
        else:
            icon = "🚀" if (quality_key in cached_qualities and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        
        # Всегда добавляем Other Qualities
        buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_OTHER_LABEL_MSG, callback_data=f"askq|other_qualities"))

        # Создаем клавиатуру
        keyboard_rows = []
        
        # Добавляем фильтры
        filter_rows, filter_action_buttons = build_filter_rows(user_id, url, is_private_chat)
        keyboard_rows.extend(filter_rows)
        
        # Группируем кнопки качества по 3 в ряд
        if buttons:
            total_quality_buttons = len(buttons)
            if total_quality_buttons % 3 == 0:
                for i in range(0, total_quality_buttons, 3):
                    keyboard_rows.append(buttons[i:i+3])
            elif total_quality_buttons % 3 == 1 and total_quality_buttons > 1:
                for i in range(0, total_quality_buttons - 4, 3):
                    keyboard_rows.append(buttons[i:i+3])
                keyboard_rows.append(buttons[-4:-2])
                keyboard_rows.append(buttons[-2:])
            else:
                for i in range(0, total_quality_buttons, 3):
                    keyboard_rows.append(buttons[i:i+3])
        
        # Собираем action buttons
        action_buttons = []
        action_buttons.extend(filter_action_buttons)
        # IMAGE fallback из кэш-меню
        action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).IMAGE_BUTTON_TEXT, callback_data="askq|image"))        
        # Добавляем WATCH кнопку для YouTube
        # - в личке: WebApp (удобный просмотр)
        # - в группах: обычная URL-кнопка (WebApp может давать BUTTON_TYPE_INVALID в некоторых контекстах)
        try:
            if is_youtube_url(url):
                piped_url = youtube_to_piped_url(url)
                try:
                    is_group = isinstance(user_id, int) and user_id < 0
                except Exception:
                    is_group = False
                if is_group:
                    action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_WATCH_BUTTON_MSG, url=piped_url))
                else:
                    wa = WebAppInfo(url=piped_url)
                    action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_WATCH_BUTTON_MSG, web_app=wa))
        except Exception as e:
            logger.error(f"Error adding WATCH button: {e}")
        
        # Группируем action buttons
        if action_buttons:
            for i in range(0, len(action_buttons), 3):
                keyboard_rows.append(action_buttons[i:i+3])
        
        # Добавляем кнопку закрытия
        keyboard_rows.append([InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askq|close")])
        
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        
        # Отправляем меню
        try:
            if proc_msg:
                try:
                    result = app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                    if result is None:
                        app.send_message(user_id, cap, reply_parameters=ReplyParameters(message_id=message.id), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                except Exception as edit_error:
                    if "MESSAGE_ID_INVALID" in str(edit_error):
                        logger.warning(f"Message ID invalid, sending new message: {edit_error}")
                        app.send_message(user_id, cap, reply_parameters=ReplyParameters(message_id=message.id), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                    elif "BUTTON_TYPE_INVALID" in str(edit_error):
                        logger.warning(f"Button type invalid, sending without keyboard: {edit_error}")
                        app.send_message(user_id, cap, reply_parameters=ReplyParameters(message_id=message.id), parse_mode=enums.ParseMode.HTML)
                    else:
                        raise edit_error
            else:
                try:
                    app.send_message(user_id, cap, reply_parameters=ReplyParameters(message_id=message.id), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                except Exception as send_error:
                    if "BUTTON_TYPE_INVALID" in str(send_error):
                        logger.warning(f"Button type invalid, sending without keyboard: {send_error}")
                        app.send_message(user_id, cap, reply_parameters=ReplyParameters(message_id=message.id), parse_mode=enums.ParseMode.HTML)
                    else:
                        raise send_error
            
            logger.info(f"Successfully created cached qualities menu for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending cached qualities menu: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating cached qualities menu: {e}")
        return False

# @reply_with_keyboard
def delete_processing_message(app, user_id, proc_msg):
    """Delete processing message if it exists"""
    if proc_msg:
        try:

            logger.info(f"Deleting processing message {proc_msg.id} for user {user_id}")
            from HELPERS.safe_messeger import safe_delete_messages
            safe_delete_messages(chat_id=user_id, message_ids=[proc_msg.id], revoke=True)
            logger.info(f"Successfully deleted processing message {proc_msg.id}")
            # Clear from cache after successful deletion
            clear_user_proc_msg(user_id)
        except Exception as e:
            logger.warning(f"Failed to delete processing message: {e}")
    else:
        logger.warning(f"proc_msg is None for user {user_id}, cannot delete processing message")

def ask_quality_menu(app, message, url, tags, playlist_start_index=1, cb=None, download_dir=None):
    """Show quality selection menu for video"""
    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
    logger.info(f"🔍 [DEBUG] ask_quality_menu вызвана с параметрами:")
    logger.info(f"   url: {url}")
    logger.info(f"   tags: {tags}")
    logger.info(f"   playlist_start_index: {playlist_start_index}")
    logger.info(f"   download_dir: {download_dir}")
    
    # ГЛОБАЛЬНАЯ ЗАЩИТА: messages НИКОГДА не будет undefined
    try:
        messages = safe_get_messages(message.chat.id)
        logger.info(f"✅ [DEBUG] messages инициализированы успешно")
    except Exception as e:
        logger.error(f"❌ [DEBUG] Ошибка инициализации messages: {e}")
        # Если все не удается, создаем минимальную защиту
        # Используем правильную систему переводов
        messages = safe_get_messages(message.chat.id)
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    user_id = message.chat.id
    proc_msg = None
    # Defensive init to avoid UnboundLocalError in rare branches
    action_buttons = []
    
    # Create download directory if not provided
    if download_dir is None:
        try:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate download directory name based on URL
            dir_name = generate_download_dir_name(url)
            download_dir = os.path.join(user_dir, "downloads", dir_name)
            os.makedirs(download_dir, exist_ok=True)
            logger.info(f"Created download directory for ask_quality_menu: {download_dir}")
            # Store download directory for this user session
            set_user_download_dir(user_id, download_dir)
            # Copy cookies to download directory
            copy_cookies_to_download_dir(user_id, download_dir)
        except Exception as e:
            logger.warning(f"Failed to create download directory in ask_quality_menu: {e}")
            download_dir = None
    
    # Clean up old format cache files before starting
    try:
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        
        # Remove old format cache files except current one
        import glob
        # Use download directory if available, otherwise fallback to user directory
        if download_dir and os.path.exists(download_dir):
            format_cache_pattern = os.path.join(download_dir, "formats_cache_*.json")
            current_cache_file = os.path.join(download_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
        else:
            format_cache_pattern = os.path.join(user_dir, "formats_cache_*.json")
            current_cache_file = os.path.join(user_dir, f"formats_cache_{hashlib.md5(url.encode()).hexdigest()[:8]}.json")
        old_cache_files = glob.glob(format_cache_pattern)
        
        for cache_file in old_cache_files:
            if cache_file != current_cache_file:  # Don't delete current cache
                try:
                    os.remove(cache_file)
                    logger.info(f"Cleaned up old format cache: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove old cache file {cache_file}: {e}")
                
        if len(old_cache_files) > 1:  # More than just current cache
            logger.info(f"Cleaned up {len(old_cache_files) - 1} old format cache files for user {user_id}")
    except Exception as e:
        logger.warning(f"Error cleaning up old format cache files: {e}")
    
    # Early FloodWait check: if there is a saved waiting time, inform user and try to clear on success
    try:
        user_dir = os.path.join("users", str(user_id))
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")
        if os.path.exists(flood_time_file):
            with open(flood_time_file, 'r') as f:
                try:
                    wait_time = int(f.read().strip())
                except Exception:
                    wait_time = None
            if wait_time is not None:
                hours = wait_time // 3600
                minutes = (wait_time % 3600) // 60
                seconds = wait_time % 60
                time_str = f"{hours}h {minutes}m {seconds}s"
                proc_msg = app.send_message(user_id, safe_get_messages(user_id).RATE_LIMIT_WITH_TIME_MSG.format(time=time_str))
            else:
                proc_msg = app.send_message(user_id, safe_get_messages(user_id).RATE_LIMIT_NO_TIME_MSG)
            try:
                app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=safe_get_messages(user_id).DOWNLOAD_STARTED_MSG, parse_mode=enums.ParseMode.HTML)
                try:
                    from HELPERS.safe_messeger import schedule_delete_message
                    schedule_delete_message(user_id, proc_msg.id, delete_after_seconds=5)
                except Exception:
                    pass
                if os.path.exists(flood_time_file):
                    os.remove(flood_time_file)
            except FloodWait as e:
                # Keep/refresh timer and exit early
                try:
                    os.makedirs(user_dir, exist_ok=True)
                    with open(flood_time_file, 'w') as f:
                        f.write(str(e.value))
                except Exception:
                    pass
                return
            except Exception:
                return
            # If edit succeeded, proceed as usual (no flood)
            proc_msg = None
    except Exception:
        pass
    found_type = None
    # Clean the cache of subtitles only on initial open (when no callback provided).
    # On filter toggles (when cb is not None), we KEEP the cache to avoid re-fetching subtitles.
    if cb is None:
        clear_subs_check_cache()
    # --- checking the range of the range for Always ASK Menu ---
    original_text = message.text or message.caption or ""
    is_playlist = is_playlist_with_range(original_text)
    if is_playlist:
        _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
        if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
            return
        # Обновляем playlist_start_index из original_text, если там есть диапазон
        # Это гарантирует, что отрицательные индексы будут правильно обработаны
        # Проверяем, что есть диапазон (не 1-1) или отрицательные индексы
        has_range = (video_start_with != 1 or video_end_with != 1) or (video_start_with < 0 or video_end_with < 0)
        if video_start_with is not None and has_range:
            playlist_start_index = video_start_with
            logger.info(f"🔍 [DEBUG] Обновлен playlist_start_index из original_text: {playlist_start_index}, video_end_with: {video_end_with}")
    try:
        # Check if subtitles are included
        subs_enabled = is_subs_enabled(user_id)
        processing_text = safe_get_messages(user_id).AA_PROCESSING_WAIT_MSG if subs_enabled else safe_get_messages(user_id).AA_PROCESSING_MSG
        
        # Only send new processing message if this is the initial menu open (no callback)
        # If callback is provided, we should NOT edit the message here - let the final logic handle it
        if cb is None:
            proc_msg = app.send_message(user_id, processing_text, reply_parameters=ReplyParameters(message_id=message.id), reply_markup=get_main_reply_keyboard())
            # Save processing message to cache for deletion when download starts
            set_user_proc_msg(user_id, proc_msg)
        else:
            # For callback queries, we don't edit the message here - let the final logic handle it
            # This prevents the menu from being replaced with "🔎 Analyzing..." temporarily
            proc_msg = None
        original_text = message.text or message.caption or ""
        logger.info(f"🔍 [DEBUG] ask_quality_menu: original_text='{original_text}'")
        is_playlist = is_playlist_with_range(original_text)
        logger.info(f"🔍 [DEBUG] ask_quality_menu: is_playlist={is_playlist}")
        playlist_range = None
        # Check if user has send_as_file enabled
        user_args = get_user_args(user_id)
        send_as_file = user_args.get("send_as_file", False)
        
        if is_playlist:
            _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
            logger.info(f"🔍 [DEBUG] ask_quality_menu: после extract_url_range_tags: video_start_with={video_start_with}, video_end_with={video_end_with}")
            playlist_range = (video_start_with, video_end_with)
            cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url)) if not send_as_file else set()
        else:
            cached_qualities = get_cached_qualities(url) if not send_as_file else set()
        # Try load cached info first to make UI instant
        info = load_ask_info(user_id, url)
        if not info:
            logger.info(f"🔍 [DEBUG] Загружаем информацию о видео через get_video_formats")
            logger.info(f"   url: {url}")
            logger.info(f"   user_id: {user_id}")
            logger.info(f"   playlist_start_index: {playlist_start_index}")
            logger.info(f"   cookies_already_checked: True")
            
            # Для плейлиста передаем диапазон, иначе только start_index
            playlist_end_index = None
            if is_playlist and playlist_range:
                playlist_end_index = playlist_range[1]
            
            # Импортируем get_video_formats локально, так как есть локальные импорты в других местах функции
            from DOWN_AND_UP.yt_dlp_hook import get_video_formats
            
            try:
                info = get_video_formats(url, user_id, playlist_start_index, cookies_already_checked=True, playlist_end_index=playlist_end_index)
                logger.info(f"✅ [DEBUG] get_video_formats выполнен успешно")
                logger.info(f"   info type: {type(info)}")
                if isinstance(info, dict):
                    logger.info(f"   info keys: {list(info.keys())}")
                    if 'duration' in info:
                        logger.info(f"   duration: {info['duration']} (тип: {type(info['duration'])})")
                    if 'formats' in info:
                        logger.info(f"   formats count: {len(info.get('formats', []))}")
            except Exception as e:
                logger.error(f"❌ [DEBUG] Ошибка в get_video_formats: {e}")
                logger.error(f"   Тип ошибки: {type(e)}")
                logger.error(f"   Строка ошибки: {str(e)}")
                raise e
            
            # Check for live stream detection (only if detection is enabled)
            if isinstance(info, dict) and info.get('error') == 'LIVE_STREAM_DETECTED':
                from CONFIG.limits import LimitsConfig
                if LimitsConfig.ENABLE_LIVE_STREAM_BLOCKING:
                    logger.warning(f"Live stream detected in ask_quality_menu for user {user_id}: {url}")
                    live_stream_message = (
                        "🚫 <b>Live Stream Detected</b>\n\n"
                        "Downloading of ongoing or infinite live streams is not allowed.\n\n"
                        "<blockquote>Please wait for the stream to end and try downloading again when:\n"
                        "• The stream duration is known\n"
                        "• The stream has finished\n"
                        "• You can see the final video length</blockquote>\n\n"
                        "Once the stream is completed, you'll be able to download it as a regular video."
                    )
                    send_error_to_user(message, live_stream_message)
                    return
            
            # Check for TikTok private account error
            if isinstance(info, dict) and info.get('error') == 'TIKTOK_PRIVATE_ACCOUNT':
                logger.info(f"TikTok private account detected in ask_quality_menu for user {user_id}: {url}")
                
                # Extract username from TikTok URL
                import re
                username_match = re.search(r'tiktok\.com/@([^/?]+)', url)
                username = username_match.group(1) if username_match else "unknown"
                
                # Get localized message
                messages = safe_get_messages(user_id)
                tiktok_message = messages.TIKTOK_PRIVATE_ACCOUNT_MSG.format(username=username)
                
                send_error_to_user(message, tiktok_message)
                return
            
            # Check for fallback to gallery-dl recommendation
            if isinstance(info, dict) and info.get('error') == 'FALLBACK_TO_GALLERY_DL':
                logger.info(f"Fallback to gallery-dl recommended in ask_quality_menu for user {user_id}: {url}")
                original_error = info.get('original_error', 'Unknown error')
                
                # ГЛОБАЛЬНАЯ ЗАЩИТА: Убедимся, что messages инициализирована
                if 'messages' not in locals() or messages is None:
                    try:
                        messages = safe_get_messages(user_id)
                    except Exception:
                        # Используем правильную систему переводов
                        messages = safe_get_messages(user_id)
                
                # Extract range info for better messaging
                _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(message.text or "")
                
                # Get total media count for fallback
                from DOWN_AND_UP.gallery_dl_hook import get_total_media_count
                detected_total = get_total_media_count(url, user_id, use_proxy=False)
                if detected_total and detected_total > 0:
                    logger.info(f"Fallback detected {detected_total} media items for range selection")
                
                # Create fallback message with gallery-dl option
                if video_start_with and video_end_with and (video_start_with != 1 or video_end_with != 1):
                    range_info = f" (range {video_start_with}-{video_end_with})"
                    range_examples = f"• For your range: <code>/img {video_start_with}-{video_end_with}</code>\n"
                else:
                    range_info = ""
                    range_examples = ""
                
                fallback_message = (
                    f"{safe_get_messages(user_id).ALWAYS_ASK_YTDLP_CANNOT_PROCESS_MSG}{range_info}</b>\n\n"
                    f"<b>Error:</b> <code>{original_error[:200]}{'...' if len(original_error) > 200 else ''}</code>\n\n"
                    f"{safe_get_messages(user_id).ALWAYS_ASK_SYSTEM_RECOMMENDS_GALLERY_DL_MSG}\n\n"
                    f"{safe_get_messages(user_id).ALWAYS_ASK_OPTIONS_MSG}\n"
                    f"{range_examples}"
                    f"{safe_get_messages(user_id).ALWAYS_ASK_FOR_IMAGE_GALLERIES_MSG}\n"
                    f"{safe_get_messages(user_id).ALWAYS_ASK_FOR_SINGLE_IMAGES_MSG}\n\n"
                    f"{safe_get_messages(user_id).ALWAYS_ASK_GALLERY_DL_WORKS_BETTER_MSG}"
                )
                
                # Create inline keyboard with gallery-dl option
                from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
                # Include range info and chat_id in callback data - use safe callback data for long URLs
                chat_id = message.chat.id
                
                # ИСПРАВЛЕНИЕ: Извлекаем диапазон из оригинального сообщения, если он не был передан явно
                original_start = video_start_with
                original_end = video_end_with
                
                # Если диапазон не был передан явно, пытаемся извлечь его из оригинального сообщения
                if (video_start_with == 1 and video_end_with == 1) and hasattr(message, 'text'):
                    import re
                    # Ищем диапазон в формате *start*end в оригинальном тексте
                    range_match = re.search(r'(https?://[^\s\*#]+)\*(\d+)\*(\d+)', message.text)
                    if range_match:
                        original_start = int(range_match.group(2))
                        original_end = int(range_match.group(3))
                        logger.info(f"[FALLBACK DEBUG] Extracted range from original message: {original_start}-{original_end}")
                
                if original_start and original_end and (original_start != 1 or original_end != 1):
                    url_data = f"{url}|{original_start}|{original_end}|{chat_id}"
                    logger.info(f"[FALLBACK DEBUG] Using extracted range: {original_start}-{original_end}")
                else:
                    # Fallback: Use detected_total if available, otherwise default to 1-1
                    if detected_total and detected_total > 0:
                        url_data = f"{url}|1|{detected_total}|{chat_id}"
                        logger.info(f"[FALLBACK DEBUG] Using detected_total: 1-{detected_total}")
                    else:
                        url_data = f"{url}|1|1|{chat_id}"
                        logger.info(f"[FALLBACK DEBUG] Using default range: 1-1")
                
                callback_data = create_safe_callback_data("fallback_gallery_dl", url_data)
                keyboard = [
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_TRY_GALLERY_DL_BUTTON_MSG, callback_data=callback_data)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send message with inline keyboard
                app.send_message(
                    message.chat.id, 
                    fallback_message, 
                    reply_markup=reply_markup,
                    reply_parameters=ReplyParameters(message_id=message.id)
                )
                return
            
            # Save minimal info to cache
            try:
                save_ask_info(user_id, url, info)
            except Exception:
                pass
        title = info.get('title', 'Video')
        video_id = info.get('id')
        tags_text = generate_final_tags(url, tags, info)
        # Determine NSFW to hide preview under spoiler in Always Ask Menu too
        try:
            is_nsfw = isinstance(tags_text, str) and ('#nsfw' in tags_text.lower())
        except Exception:
            is_nsfw = False
        
        # Check if we're in a private chat (paid media only works in private chats)
        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
        thumb_path = None
        # Use download directory if available, otherwise fallback to user directory
        download_dir = get_user_download_dir(user_id)
        if download_dir and os.path.exists(download_dir):
            thumb_dir = download_dir
        else:
            thumb_dir = os.path.join("users", str(user_id))
            create_directory(thumb_dir)
        
        # Для плейлистов скачиваем обложки для всех видео
        playlist_entries = info.get('_playlist_entries')
        if is_playlist and playlist_entries and isinstance(playlist_entries, list):
            logger.info(f"🔍 [DEBUG] Плейлист обнаружен, скачиваем обложки для {len(playlist_entries)} видео")
            for entry in playlist_entries:
                if not entry:
                    continue
                entry_id = entry.get('id')
                entry_url = entry.get('url') or entry.get('webpage_url')
                if not entry_id:
                    continue
                
                # Для YouTube используем специальную функцию
                if ("youtube.com" in url or "youtu.be" in url) and entry_id:
                    entry_thumb_path = os.path.join(thumb_dir, f"yt_thumb_{entry_id}.jpg")
                    try:
                        # Используем URL конкретного видео, если доступен
                        entry_video_url = entry_url or f"https://www.youtube.com/watch?v={entry_id}"
                        download_thumbnail(entry_id, entry_thumb_path, entry_video_url)
                        logger.info(f"✅ Скачана обложка для видео {entry_id}: {entry_thumb_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось скачать обложку для видео {entry_id}: {e}")
                elif entry_url:
                    # Для других сервисов используем универсальный загрузчик
                    try:
                        service_name = "unknown"
                        if 'vk.com' in entry_url:
                            service_name = "vk"
                        elif 'tiktok.com' in entry_url:
                            service_name = "tiktok"
                        elif any(x in entry_url for x in ['twitter.com', 'x.com']):
                            service_name = "twitter"
                        # Добавьте другие сервисы по необходимости
                        
                        if service_name != "unknown":
                            entry_thumb_path = os.path.join(thumb_dir, f"{service_name}_thumb_{entry_id}.jpg")
                            if download_universal_thumbnail(entry_url, entry_thumb_path):
                                logger.info(f"✅ Скачана обложка для видео {entry_id}: {entry_thumb_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось скачать обложку для видео {entry_id}: {e}")
        
        # Скачиваем обложку для первого видео (для отображения в меню)
        if ("youtube.com" in url or "youtu.be" in url) and video_id:
            thumb_path = os.path.join(thumb_dir, f"yt_thumb_{video_id}.jpg")
            try:
                download_thumbnail(video_id, thumb_path, url)
                logger.info(f"Downloaded thumbnail to download directory: {thumb_path}")
            except Exception as e:
                logger.warning(f"Failed to download thumbnail: {e}")
                thumb_path = None
        else:
            # Try to download thumbnail for non-YouTube services
            service_name = "unknown"
            if 'vk.com' in url:
                service_name = "vk"
            elif 'tiktok.com' in url:
                service_name = "tiktok"
            elif any(x in url for x in ['twitter.com', 'x.com']):
                service_name = "twitter"
            elif 'facebook.com' in url:
                service_name = "facebook"
            elif 'pornhub.com' in url or 'pornhub.org' in url:
                service_name = "pornhub"
            elif any(x in url for x in ['instagram.com', 'instagr.am']):
                service_name = "instagram"
            elif 'vimeo.com' in url:
                service_name = "vimeo"
            elif any(x in url for x in ['dailymotion.com', 'dai.ly']):
                service_name = "dailymotion"
            elif 'rutube.ru' in url:
                service_name = "rutube"
            elif 'twitch.tv' in url:
                service_name = "twitch"
            elif 'boosty.to' in url:
                service_name = "boosty"
            elif 'ok.ru' in url:
                service_name = "okru"
            elif any(x in url for x in ['reddit.com', 'redd.it']):
                service_name = "reddit"
            elif 'pikabu.ru' in url:
                service_name = "pikabu"
            elif 'zen.yandex.ru' in url:
                service_name = "yandex_zen"
            elif any(x in url for x in ['drive.google.com', 'docs.google.com']):
                service_name = "google_drive"
            elif 'redtube.com' in url:
                service_name = "redtube"
            elif 'bilibili.com' in url:
                service_name = "bilibili"
            elif 'nicovideo.jp' in url:
                service_name = "niconico"
            elif 'xvideos.com' in url:
                service_name = "xvideos"
            elif 'xnxx.com' in url:
                service_name = "xnxx"
            elif 'youporn.com' in url:
                service_name = "youporn"
            elif 'xhamster.com' in url:
                service_name = "xhamster"
            elif 'porntube.com' in url:
                service_name = "porntube"
            elif 'spankbang.com' in url:
                service_name = "spankbang"
            elif 'onlyfans.com' in url:
                service_name = "onlyfans"
            elif 'patreon.com' in url:
                service_name = "patreon"
            elif 'soundcloud.com' in url:
                service_name = "soundcloud"
            elif 'bandcamp.com' in url:
                service_name = "bandcamp"
            elif 'mixcloud.com' in url:
                service_name = "mixcloud"
            elif 'deezer.com' in url:
                service_name = "deezer"
            elif 'spotify.com' in url:
                service_name = "spotify"
            elif 'music.apple.com' in url:
                service_name = "apple_music"
            elif 'tidal.com' in url:
                service_name = "tidal"
            
            if service_name != "unknown":
                thumb_path = os.path.join(user_dir, f"{service_name}_thumb_{video_id or 'unknown'}.jpg")
                try:
                    if download_universal_thumbnail(url, thumb_path):
                        thumb_path = thumb_path
                    else:
                        thumbnail_url = info.get('thumbnail')
                        if thumbnail_url:
                            try:
                                response = requests.get(thumbnail_url, timeout=10)
                                if response.status_code == 200 and len(response.content) <= 1024 * 1024:
                                    with open(thumb_path, "wb") as f:
                                        f.write(response.content)
                                    thumb_path = thumb_path
                            except Exception:
                                pass
                except Exception:
                    pass
        # At this point, lack of thumbnail must NOT block further UI
        # --- Detect available audio dubs (languages) once per menu open ---
        filters_state = get_filters(user_id)
        sel_codec = filters_state.get("codec", "avc1")
        sel_ext = filters_state.get("ext", "mp4")
        # Build list of available audio languages from formats
        available_dubs = []
        lang_seen = set()
        for f in info.get('formats', []):
            if (f.get('vcodec') == 'none' and f.get('acodec') and f.get('language')):
                lang = f.get('language')
                if lang and lang not in lang_seen:
                    lang_seen.add(lang)
                    available_dubs.append(lang)
        # Save dubs availability per-user (show only if 2+ languages exist)
        fstate = get_filters(user_id)
        has_dubs = len(available_dubs) > 1
        fstate["has_dubs"] = has_dubs
        fstate["available_dubs"] = sorted(available_dubs)
        if not has_dubs:
            # If only one or zero languages, reset audio selection
            fstate["audio_lang"] = None
        _ASK_FILTERS[str(user_id)] = fstate
        # If user selected MKV container, reflect this to the download session preference
        try:
            set_session_mkv_override(user_id, sel_ext == "mkv")
        except Exception:
            pass
        # --- Table with qualities and sizes ---
        table_block = ''
        found_quality_keys = set()
        
        # Check if user has fixed format via /args
        user_fixed_format = None
        try:
            user_args = get_user_args(user_id)
            user_video_format = user_args.get('video_format', 'mp4')
            user_merge_format = user_args.get('merge_output_format', 'mp4')
            
            # If user has set video_format to something other than mp4, it's fixed
            if user_video_format != 'mp4':
                user_fixed_format = user_video_format
            # If user has set merge_output_format to something other than mp4, it's fixed
            elif user_merge_format != 'mp4':
                user_fixed_format = user_merge_format
        except Exception:
            pass
        
        if ("youtube.com" in url or "youtu.be" in url):
            quality_map = {}
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                    vcodec = f.get('vcodec') or ''
                    ext = f.get('ext') or ''
                    # Filter by codec
                    if sel_codec == 'avc1' and 'avc1' not in vcodec:
                        continue
                    if sel_codec == 'av01' and not vcodec.startswith('av01'):
                        continue
                    if sel_codec == 'vp9' and 'vp9' not in vcodec:
                        continue
                    
                    # Filter by extension - use fixed format if available
                    target_ext = user_fixed_format if user_fixed_format else sel_ext
                    if target_ext == 'mp4' and ext != 'mp4':
                        continue
                    if target_ext == 'mkv' and ext == 'mp4':
                        continue
                    if target_ext == 'webm' and ext != 'webm':
                        continue
                    if target_ext == 'avi' and ext != 'avi':
                        continue
                    if target_ext == 'mov' and ext != 'mov':
                        continue
                    if target_ext == 'flv' and ext != 'flv':
                        continue
                    if target_ext == '3gp' and ext not in ('3gp', '3g2'):
                        continue
                    if target_ext == 'ogv' and ext not in ('ogv', 'ogg'):
                        continue
                    if target_ext == 'wmv' and ext != 'wmv':
                        continue
                    if target_ext == 'asf' and ext != 'asf':
                        continue
                    w = f['width']
                    h = f['height']
                    quality_key = get_quality_by_min_side(w, h)
                    if quality_key == "best":
                        continue
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    if quality_key not in quality_map or (filesize and filesize > (quality_map[quality_key].get('filesize') or 0)):
                        quality_map[quality_key] = f
            table_lines = []
            for q in sorted(quality_map.keys(), key=sort_quality_key):
                f = quality_map[q]
                w = f.get('width')
                h = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                if filesize:
                    if filesize and filesize >= 1024*1024*1024:
                        size_str = f"{round(filesize/1024/1024/1024, 2)}GB"
                    else:
                        size_str = f"{round(filesize/1024/1024, 1)}MB"
                else:
                    size_str = '—'
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and filesize:
                    video_bytes = filesize
                    if video_bytes and video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                # Check the availability of subtitles for this quality 
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                subs_available = ""
                # Audio language marker for rows (keep UI light; summary shows selection)
                if subs_enabled:
                    if sel_ext == 'mkv':
                        # Для MKV при включённых субтитрах показываем без ограничений
                        subs_available = "💬"
                    elif is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
                        found_type = check_subs_availability(url, user_id, q, return_type=True)
                        if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                            temp_info = {
                                'duration': info.get('duration'),
                                'filesize': filesize,
                                'filesize_approx': filesize
                            }
                            if check_subs_limits(temp_info, q):
                                subs_available = "💬"
                # Cache/icon (skip if send_as_file is enabled)
                if send_as_file:
                    is_cached = False
                    postfix = ""
                elif is_playlist and playlist_range:
                    # Правильное формирование indices для отрицательных индексов
                    start, end = playlist_range
                    has_negative = start < 0 or end < 0
                    
                    if has_negative:
                        # Для отрицательных индексов сначала создаем список с отрицательными значениями
                        if abs(start) < abs(end):
                            indices = list(range(start, end - 1, -1))
                        else:
                            indices = list(range(start, end + 1, 1))
                        
                        # Преобразуем отрицательные индексы в положительные для проверки кэша
                        # (в кэше они хранятся как положительные индексы)
                        try:
                            from DOWN_AND_UP.yt_dlp_hook import get_video_formats
                            temp_info = get_video_formats(url, user_id, 1, True, False, 1)
                            if temp_info and isinstance(temp_info, dict):
                                if "entries" in temp_info:
                                    total_playlist_count = len(temp_info["entries"])
                                elif "_playlist_entries" in temp_info:
                                    total_playlist_count = len(temp_info["_playlist_entries"])
                                else:
                                    total_playlist_count = None
                                
                                if total_playlist_count:
                                    # Преобразуем отрицательные индексы в положительные
                                    converted_indices = []
                                    for neg_idx in indices:
                                        if neg_idx < 0:
                                            pos_idx = total_playlist_count + neg_idx + 1
                                            converted_indices.append(pos_idx)
                                        else:
                                            converted_indices.append(neg_idx)
                                    indices = converted_indices
                        except Exception as e:
                            logger.warning(f"Failed to convert negative indices for cache check: {e}")
                    elif start > end:
                        indices = list(range(start, end - 1, -1))
                    else:
                        indices = list(range(start, end + 1))
                    
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), q, indices)
                    total = len(indices)
                    postfix = f" ({n_cached}/{total})"
                    is_cached = n_cached > 0
                else:
                    # Проверяем кэш для одиночного видео
                    is_cached = q in cached_qualities
                    # Дополнительно проверяем кэш по уникальной ссылке видео, если это видео из плейлиста
                    if not is_cached:
                        # Извлекаем уникальную ссылку текущего видео
                        video_page_url = (
                            info.get("webpage_url")
                            or info.get("original_url")
                            or info.get("url")
                            or info.get("canonical_url")
                            or url
                        )
                        # Если это не URL плейлиста, проверяем кэш по уникальной ссылке
                        if video_page_url != url and video_page_url:
                            try:
                                single_video_cached = get_cached_message_ids(video_page_url, q)
                                if single_video_cached:
                                    is_cached = True
                                    logger.info(f"🔍 [CACHE] Найдено одиночное видео в кэше по уникальной ссылке: {video_page_url}, quality: {q}")
                            except Exception as e:
                                logger.warning(f"⚠️ [CACHE] Ошибка при проверке кэша для одиночного видео: {e}")
                    postfix = ""
                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                emoji = "🚀" if (is_cached and not need_subs and not is_nsfw) else "📹"
                # Show selected audio language if any
                sel_audio_lang = get_filters(user_id).get("audio_lang")
                audio_mark = f" 🗣{sel_audio_lang}" if sel_audio_lang else ""
                table_lines.append(f"{emoji}{q}{subs_available}{audio_mark}:  {size_str}{dim_str}{scissors}{postfix}")
                found_quality_keys.add(q)
            table_block = "\n".join(table_lines)
        else:
            # --- Non-YouTube: build quality map from actual formats (VK, PH etc.) ---
            import re as _re
            quality_map = {}  # quality_key -> best candidate dict

            def infer_quality_key(f):
                messages = safe_get_messages(message.chat.id)
                w = f.get('width')
                h = f.get('height')
                if w and h:
                    return get_quality_by_min_side(w, h)
                fid = f.get('format_id') or ''
                # url360 / 240p / 1080p etc.
                # Case 1: 144p/240p/.. from PH-like ids
                m = _re.match(r'^(\d{3,4})p$', fid)
                if m:
                    try:
                        return f"{int(m.group(1))}p"
                    except Exception:
                        return None
                # Case 2: url144/url240/... from VK
                m2 = _re.match(r'^url(\d{3,4})$', fid)
                if m2:
                    try:
                        return f"{int(m2.group(1))}p"
                    except Exception:
                        return None
                # Case 3: generic *_540p_* like on TikTok
                m3 = _re.search(r'(\d{3,4})p', fid)
                if m3:
                    try:
                        return f"{int(m3.group(1))}p"
                    except Exception:
                        return None
                
                # Case 4: Universal - check format_note and other fields for any service
                # Try to extract quality from format_note
                format_note = f.get('format_note') or ''
                m4 = _re.search(r'(\d{3,4})p', format_note)
                if m4:
                    try:
                        return f"{int(m4.group(1))}p"
                    except Exception:
                        pass
                
                # Try to extract from url field
                url_field = f.get('url') or ''
                m5 = _re.search(r'(\d{3,4})p', url_field)
                if m5:
                    try:
                        return f"{int(m5.group(1))}p"
                    except Exception:
                        pass
                
                # Universal fallback: if we have dimensions but no quality key, try to infer from resolution
                if w and h:
                    # Use the existing quality mapping function for consistency
                    return get_quality_by_min_side(w, h)
                
                return None

            def is_manifest(f):
                messages = safe_get_messages(message.chat.id)
                proto = (f.get('protocol') or '').lower()
                return 'm3u8' in proto or 'dash' in (f.get('format_note') or '').lower() or f.get('manifest_url') is not None

            # --- Helpers for size estimation when FILESIZE is missing ---
            def best_audio_kbps() -> int:
                kbps = 0
                for af in info.get('formats', []):
                    if af.get('vcodec') == 'none':
                        # Prefer tbr, else abr
                        val = None
                        if af.get('tbr'):
                            val = float(af['tbr'])
                        elif af.get('abr'):
                            val = float(af['abr'])
                        if val:
                            kbps = max(kbps, int(val))
                return kbps or 128  # default to 128 kbps if unknown

            _audio_kbps = best_audio_kbps()

            def default_video_kbps_for_height(height: int, fps: int | None, vcodec: str | None) -> int:
                # Baseline by height (rough real-world averages for SDR 16:9)
                baseline = {
                    144: 250,
                    240: 400,
                    360: 800,
                    480: 1200,
                    540: 2000,
                    576: 2200,
                    720: 2500,
                    1080: 4500,
                    1440: 8000,
                    2160: 14000,
                    4320: 40000,
                }
                # pick nearest not-greater baseline
                h_keys = sorted(baseline.keys())
                chosen = baseline[h_keys[0]]
                for hk in h_keys:
                    if height >= hk:
                        chosen = baseline[hk]
                # fps adjustment
                if fps and fps > 30:
                    chosen = int(chosen * 1.25)
                # codec efficiency (AV1/VP9 can be ~10% better than AVC)
                if vcodec and (vcodec.startswith('av01') or 'vp9' in vcodec):
                    chosen = int(chosen * 0.9)
                return max(chosen, 200)

            def sibling_video_kbps_for_quality(qk: str) -> int:
                # Try to find any sibling format with same quality and known tbr/vbr
                best = 0
                for sf in info.get('formats', []):
                    if infer_quality_key(sf) != qk:
                        continue
                    val = 0.0
                    if sf.get('tbr'):
                        val = float(sf['tbr'])
                    elif sf.get('vbr'):
                        val = float(sf['vbr'])
                    if val:
                        best = max(best, int(val))
                return best

            def estimate_size_mb(f, qk: str, filesize_str: str = '') -> int:
                # 1) Exact sizes
                if f.get('filesize'):
                    return int(f['filesize']) // (1024*1024)
                if f.get('filesize_approx'):
                    return int(f['filesize_approx']) // (1024*1024)
                
                # 2) Try to parse human-readable size strings (like "624KB", "1.4MB")
                if filesize_str:
                    try:
                        import re as _re
                        # Parse patterns like "624KB", "1.4MB", "2.1GB"
                        match = _re.match(r'^([\d.]+)\s*(KB|MB|GB)$', filesize_str.strip())
                        if match:
                            size_val = float(match.group(1))
                            unit = match.group(2)
                            if unit == 'KB':
                                return max(1, int(size_val / 1024))  # At least 1 MB for any KB
                            elif unit == 'MB':
                                return int(size_val)
                            elif unit == 'GB':
                                return int(size_val * 1024)
                    except Exception:
                        pass
                
                duration = info.get('duration')
                if not duration:
                    return 0
                # 3) Use tbr/vbr/abr when available
                kbps = 0.0
                if f.get('tbr'):
                    kbps = float(f['tbr'])
                elif f.get('vbr'):
                    kbps = float(f['vbr'])
                elif f.get('abr'):
                    kbps = float(f['abr'])
                # 4) Else use sibling with same quality
                if not kbps:
                    kbps = float(sibling_video_kbps_for_quality(qk))
                # 5) Else heuristic by height/fps/codec
                if not kbps:
                    # derive height from qk like '360p'
                    try:
                        height = int((qk or '0p').rstrip('p'))
                    except Exception:
                        height = f.get('height') or 0
                    fps = f.get('fps') or 30
                    vcodec = f.get('vcodec') or ''
                    kbps = float(default_video_kbps_for_height(int(height or 0), int(fps or 0), vcodec))
                # add audio kbps if stream is likely video-only (no abr or explicit no audio)
                if (f.get('acodec') in (None, '', 'none')) or (not f.get('abr')):
                    kbps += float(_audio_kbps)
                try:
                    mb = (kbps * float(duration) * 125) / (1024*1024)
                    if mb and mb > 0 and mb < 1:
                        return 1
                    return int(round(mb))
                except Exception:
                    return 0

            for f in info.get('formats', []):
                # Skip audio-only
                if f.get('vcodec') == 'none' and (f.get('audio_ext') or '') != 'none':
                    continue

                # Filter by user's fixed format if set
                if user_fixed_format:
                    ext = f.get('ext') or ''
                    if user_fixed_format == 'mp4' and ext != 'mp4':
                        continue
                    if user_fixed_format == 'webm' and ext != 'webm':
                        continue
                    if user_fixed_format == 'mkv' and ext == 'mp4':
                        continue
                    if user_fixed_format == 'avi' and ext != 'avi':
                        continue
                    if user_fixed_format == 'mov' and ext != 'mov':
                        continue
                    if user_fixed_format == 'flv' and ext != 'flv':
                        continue
                    if user_fixed_format == '3gp' and ext not in ('3gp', '3g2'):
                        continue
                    if user_fixed_format == 'ogv' and ext not in ('ogv', 'ogg'):
                        continue
                    if user_fixed_format == 'wmv' and ext != 'wmv':
                        continue
                    if user_fixed_format == 'asf' and ext != 'asf':
                        continue
                
                # Filter by selected codec
                vcodec = f.get('vcodec') or ''
                if sel_codec == 'avc1' and 'avc1' not in vcodec:
                    continue
                if sel_codec == 'av01' and not vcodec.startswith('av01'):
                    continue
                if sel_codec == 'vp9' and 'vp9' not in vcodec:
                    continue
                
                # Filter by selected extension
                ext = f.get('ext') or ''
                target_ext = user_fixed_format if user_fixed_format else sel_ext
                if target_ext == 'mp4' and ext != 'mp4':
                    continue
                if target_ext == 'mkv' and ext == 'mp4':
                    continue
                if target_ext == 'webm' and ext != 'webm':
                    continue

                qk = infer_quality_key(f)
                if not qk or qk == 'best':
                    continue

                # derive dimensions when missing (assume 16:9)
                w_val = f.get('width') or 0
                h_val = f.get('height') or 0
                if not h_val:
                    try:
                        h_val = int(qk.rstrip('p'))
                    except Exception:
                        h_val = 0
                if not w_val and h_val:
                    w_val = int(h_val * 16 / 9)

                candidate = {
                    'w': w_val,
                    'h': h_val,
                    'size_mb': estimate_size_mb(f, qk, f.get('filesize_str') or ''),
                    'format_id': f.get('format_id') or '',
                    'protocol': f.get('protocol') or '',
                    'filesize_str': f.get('filesize_str') or '',  # Capture human-readable size like "624KB"
                }

                prev = quality_map.get(qk)
                if not prev:
                    quality_map[qk] = candidate
                else:
                    # Prefer entries with known resolution/size; then prefer non-manifest; then larger size
                    prev_has_dims = bool(prev.get('w')) and bool(prev.get('h'))
                    curr_has_dims = bool(candidate.get('w')) and bool(candidate.get('h'))
                    prev_has_size = prev.get('size_mb', 0) > 0
                    curr_has_size = candidate.get('size_mb', 0) > 0
                    prev_manifest = is_manifest(prev)
                    curr_manifest = is_manifest(candidate)

                    def better(a_has_dims, a_has_size, a_manifest, a_size, b_has_dims, b_has_size, b_manifest, b_size):
                        messages = safe_get_messages(user_id)
                        # 1) prefer with dimensions
                        if a_has_dims != b_has_dims:
                            return a_has_dims
                        # 2) prefer with size estimation
                        if a_has_size != b_has_size:
                            return a_has_size
                        # 3) prefer non-manifest
                        if a_manifest != b_manifest:
                            return not a_manifest
                        # 4) prefer bigger size
                        return a_size > b_size

                    if better(curr_has_dims, curr_has_size, curr_manifest, candidate['size_mb'],
                              prev_has_dims, prev_has_size, prev_manifest, prev.get('size_mb', 0)):
                        quality_map[qk] = candidate
            
            # Universal fallback when no qualities were found for any service
            if not quality_map:
                # Try to create default qualities based on available formats
                video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
                if video_formats:
                    # Group formats by resolution and create quality keys
                    resolution_groups = {}
                    for f in video_formats:
                        w = f.get('width', 0)
                        h = f.get('height', 0)
                        if w and h:
                            # Find the best quality for this resolution
                            res_key = f"{w}x{h}"
                            if res_key not in resolution_groups or (f.get('filesize') or 0) > (resolution_groups[res_key].get('filesize') or 0):
                                resolution_groups[res_key] = f
                    
                    # Convert resolution groups to quality keys
                    for res_key, f in resolution_groups.items():
                        w, h = f.get('width', 0), f.get('height', 0)
                        if w and h:
                            # Use the existing quality mapping function for consistency
                            qk = get_quality_by_min_side(w, h)
                            
                            if qk not in quality_map:
                                quality_map[qk] = {
                                    'w': w,
                                    'h': h,
                                    'size_mb': estimate_size_mb(f, qk, f.get('filesize_str') or ''),
                                    'format_id': f.get('format_id') or '',
                                    'protocol': f.get('protocol') or '',
                                    'filesize_str': f.get('filesize_str') or '',
                                }
            
            table_lines = []
            for quality_key in sorted(quality_map.keys(), key=sort_quality_key):
                entry = quality_map[quality_key]
                w, h, size_val = entry['w'], entry['h'], entry['size_mb']
                found_quality_keys.add(quality_key)
                size_str = f"{round(size_val/1024, 1)}GB" if size_val and size_val >= 1024 else (f"{size_val}MB" if size_val else '—')
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and size_val:
                    video_bytes = size_val * 1024 * 1024
                    if video_bytes and video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                emoji = "📹"
                table_lines.append(f"{emoji}{quality_key}:  {size_str}{dim_str}{scissors}")
            table_block = "\n".join(table_lines)

        # --- Forming caption ---
        cap = f"<b>{title}</b>\n"
        
        # Show fixed format info if set via /args
        if user_fixed_format:
                cap += f"\n<b>{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG}: {user_fixed_format.upper()}</b>\n"
        
        # Audio/subs selection summary line
        fstate = get_filters(user_id)
        sel_audio_lang = fstate.get("audio_lang")
        subs_enabled = is_subs_enabled(user_id)
        subs_lang = get_user_subs_language(user_id) if subs_enabled else None
        summary_parts = []
        if sel_audio_lang:
            summary_parts.append(f"🗣 {sel_audio_lang}")
        # Always show chosen subtitle language if subs are enabled
        if subs_enabled and subs_lang:
            summary_parts.append(f"💬 {subs_lang}")
        if summary_parts:
            cap += "<blockquote>" + " | ".join(summary_parts) + "</blockquote>\n"
        # --- YouTube expanded block ---
        is_youtube = ("youtube.com" in url or "youtu.be" in url)
        if is_youtube:
            uploader = info.get('uploader') or ''
            channel_url = info.get('channel_url') or ''
            view_count = info.get('view_count')
            like_count = info.get('like_count')
            channel_follower_count = info.get('channel_follower_count')
            duration = info.get('duration')
            upload_date = info.get('upload_date')
            title_val = info.get('title') or ''
            # Formatting
            duration_str = TimeFormatter(duration*1000) if duration else ''
            upload_date_str = ''
            if upload_date and len(str(upload_date)) == 8:
                try:
                    dt = datetime.strptime(str(upload_date), '%Y%m%d')
                    upload_date_str = dt.strftime('%d.%m.%Y')
                except Exception:
                    upload_date_str = str(upload_date)
            # Emoji
            views_str = f'👁 {view_count:,}' if view_count is not None else ''
            likes_str = f'❤️ {like_count:,}' if like_count is not None else ''
            subs_str = f'👥 {channel_follower_count:,}' if channel_follower_count is not None else ''
            # First line: channel and subscribers
            meta_lines = []
            if uploader:
                ch_line = f"📺 <b>{uploader}</b>\n"
                if subs_str:
                    ch_line += f"<blockquote>{subs_str}</blockquote>\n"
                meta_lines.append(ch_line)
            # Second line: name
            t_line = ''
            if title_val:
                t_line = f"<b>{title_val}</b>"
            if t_line:
                meta_lines.append(t_line)
            # Third line: Date + Duration (in the quote)
            date_dur_line = ''
            if upload_date_str:
                date_dur_line += f"📅 {upload_date_str}"
            if duration_str:
                if date_dur_line:
                    date_dur_line += f"  ⏱️ {duration_str}"
                else:
                    date_dur_line = f"⏱️ {duration_str}"
            if date_dur_line:
                meta_lines.append(f"<blockquote>{date_dur_line}</blockquote>")
            # Fourth line: views + likes (in quote)
            stat_line = ''
            if views_str:
                stat_line += views_str
            if likes_str:
                if stat_line:
                    stat_line += f"  {likes_str}"
                else:
                    stat_line = likes_str
            if stat_line:
                meta_lines.append(f"<blockquote>{stat_line}</blockquote>")
            # Collect the block
            meta_block = '\n'.join(meta_lines)
            cap = meta_block + '\n\n'
        else:
            # For non-YouTube: show Uploader, Duration, then Title if present
            title_ny = info.get('title') or ''
            uploader_ny = info.get('uploader') or ''
            duration_ny = info.get('duration')
            duration_str_ny = TimeFormatter(duration_ny*1000) if duration_ny else ''
            meta_lines_ny = []
            if uploader_ny:
                meta_lines_ny.append(f"📺 <b>{uploader_ny}</b>")
            if duration_str_ny:
                meta_lines_ny.append(f"<blockquote>⏱️ {duration_str_ny}</blockquote>")
            if title_ny:
                meta_lines_ny.append(f"\n<b>{title_ny}</b>")
            cap = ('\n'.join(meta_lines_ny) + '\n\n') if meta_lines_ny else ''
        # --- a table of qualities ---
        if table_block:
            cap += f"<blockquote>{table_block}</blockquote>\n"
        
        # --- Add subtitles and dubs count info ---
        subs_count_info = ""
        dubs_count_info = ""
        
        # Check if subtitles are enabled and Always Ask mode is enabled for subs
        if is_subs_enabled(user_id) and is_subs_always_ask(user_id):
            try:
                # Get available subtitles count (single-check/cached within session)
                from COMMANDS.subtitles_cmd import get_or_compute_subs_langs
                normal_subs, auto_subs = get_or_compute_subs_langs(user_id, url)
                total_subs = len(set(normal_subs) | set(auto_subs))
                if total_subs and total_subs > 0:
                    subs_count_info = f"{safe_get_messages(user_id).ALWAYS_ASK_SUBTITLES_MSG}: {total_subs} available\n"
            except Exception as e:
                logger.error(f"Error getting subtitles count: {e}")
        
        # Check if dubs are available
        fstate = get_filters(user_id)
        available_dubs = fstate.get("available_dubs", [])
        if len(available_dubs) > 1:  # More than 1 language means dubs are available
            dubs_count_info = f"{safe_get_messages(user_id).ALWAYS_ASK_DUBBED_AUDIO_MSG}: {len(available_dubs)} languages"
        
        # Add the info to caption - each type independently
        info_parts = []
        if subs_count_info:
            info_parts.append(subs_count_info)
        if dubs_count_info:
            info_parts.append(dubs_count_info)
        
        if info_parts:
            cap += f"<blockquote>{''.join(info_parts)}</blockquote>\n"
        # --- tags ---
        if tags_text:
            cap += f"{tags_text}"
        # --- links at the very bottom ---
        # if ("youtube.com" in url or "youtu.be" in url):
            # webpage_url = info.get('webpage_url') or ''
            # video_url_link = f'<a href="{webpage_url}">[VIDEO]</a>' if webpage_url else ''
            # channel_url_link = f'<a href="{channel_url}">[CHANNEL]</a>' if channel_url else ''
            # thumbnail_url = info.get('thumbnail') or ''
            # thumb_link = f'<a href="{thumbnail_url}">[Thumbnail]</a>' if thumbnail_url else ''
            # links = '  '.join([x for x in [channel_url_link, thumb_link] if x])
            # if links:
                # cap += f"\n{links}"
        # --- Cutting by the limit ---
        if len(cap) > 1024:
            if is_youtube:
                # We cut off by priority: likes, subscribers, views, date, duration, name, channel
                # 1. Likes
                cap1 = cap.replace(likes_str, '') if likes_str else cap
                if len(cap1) <= 1024:
                    cap = cap1
                else:
                    # 2. Subscribers
                    cap2 = cap1.replace(subs_str, '') if subs_str else cap1
                    if len(cap2) <= 1024:
                        cap = cap2
                    else:
                        # 3. Views
                        cap3 = cap2.replace(views_str, '') if views_str else cap2
                        if len(cap3) <= 1024:
                            cap = cap3
                        else:
                            # 4. Date
                            cap4 = cap3.replace(upload_date_str, '') if upload_date_str else cap3
                            if len(cap4) <= 1024:
                                cap = cap4
                            else:
                                # 5. Duration
                                cap5 = cap4.replace(duration_str, '') if duration_str else cap4
                                if len(cap5) <= 1024:
                                    cap = cap5
                                else:
                                    # 6. Name
                                    cap6 = cap5.replace(title_val, '') if title_val else cap5
                                    if len(cap6) <= 1024:
                                        cap = cap6
                                    else:
                                        # 7. Channel
                                        cap7 = cap6.replace(uploader, '') if uploader else cap6
                                        cap = cap7[:1021] + '...'
            else:
                # Simple trim for non-YouTube: cut title first, then uploader, then duration
                if title_ny and len(cap) > 1024:
                    cap = cap.replace(f"<b>{title_ny}</b>", "")
                if uploader_ny and len(cap) > 1024:
                    cap = cap.replace(f"📺 <b>{uploader_ny}</b>", "")
                if duration_str_ny and len(cap) > 1024:
                    cap = cap.replace(f"⏱️ {duration_str_ny}", "")
                if len(cap) > 1024:
                    cap = cap[:1021] + '...'
        # --- Hint ---
        subs_enabled = is_subs_enabled(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        subs_lang = get_user_subs_language(user_id)

        # We check for subtitles of the desired type for the selected language
        subs_hint = ""
        subs_warn = ""
        show_repost_hint = True

        if subs_enabled and is_youtube_url(url):
            found_type = check_subs_availability(url, user_id, return_type=True)
            # Check if we're in Always Ask mode (user will choose language manually)
            is_always_ask_mode = is_subs_always_ask(user_id)
            
            if is_always_ask_mode:
                # In Always Ask menu, always show subtitles as available if found, regardless of auto_mode
                # User will choose language and type manually
                need_subs = found_type is not None  # True if any subtitles found (auto or normal)
            else:
                # In manual mode, respect user's auto_mode setting
                need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            
            logger.info(f"Always Ask menu: subs_enabled={subs_enabled}, auto_mode={auto_mode}, found_type={found_type}, is_always_ask={is_always_ask_mode}, need_subs={need_subs}")
            if need_subs:
                subs_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_SUBTITLES_ARE_AVAILABLE_MSG}"
                show_repost_hint = False  # 🚀 we don't show if subs really exist and are needed
            elif is_always_ask_mode and not need_subs:
                # In Always Ask mode, show subs hint even if not found (user can still try)
                subs_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_SUBTITLE_LANGUAGE_MSG}"
            else:
                subs_warn = f"\n{safe_get_messages(user_id).ALWAYS_ASK_SUBS_NOT_FOUND_MSG}"

        repost_line = f"\n{safe_get_messages(user_id).ALWAYS_ASK_INSTANT_REPOST_MSG}" if show_repost_hint else ""
        # Add DUBS hint if available
        dubs_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG}" if get_filters(user_id).get("has_dubs") else ""
        # Replace quality hint with paid note for NSFW
        paid_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_NSFW_IS_PAID_MSG}" if (is_nsfw and is_private_chat) else f"\n{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_DOWNLOAD_QUALITY_MSG}"
        # Hints tied to optional buttons
        image_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOAD_IMAGE_MSG}" if not found_quality_keys else ""
        watch_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_WATCH_VIDEO_MSG}" if is_youtube_url(url) else ""
        link_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_GET_DIRECT_LINK_MSG}"  # Link button is always present
        list_hint = f"\n{safe_get_messages(user_id).ALWAYS_ASK_SHOW_AVAILABLE_FORMATS_MSG}"  # LIST button is always present
        
        # Create dynamic hints based on actual buttons that will be shown
        def create_dynamic_hints(action_buttons, found_quality_keys, is_youtube_url, url, is_nsfw, is_private_chat, get_filters, user_id, subs_hint, subs_warn):
            messages = safe_get_messages(message.chat.id)
            """Create hints only for emojis that are actually used in the menu"""
            hints = []
            
            # Always show format change hint (📼) - this is always available
            hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_CHANGE_VIDEO_EXT_MSG}")
            
            # Quality hint (📹) - always shown unless NSFW
            if is_nsfw and is_private_chat:
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_NSFW_IS_PAID_MSG}")
            else:
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_DOWNLOAD_QUALITY_MSG}")
            
            # Repost hint (🚀) - only if show_repost_hint is True
            if show_repost_hint:
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_INSTANT_REPOST_MSG}")
            
            # Watch hint (👁) - only for YouTube
            if is_youtube_url(url):
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_WATCH_VIDEO_MSG}")
            
            # Link hint (🔗) - always present
            hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_GET_DIRECT_LINK_MSG}")
            
            # List hint (📃) - always present
            hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_SHOW_AVAILABLE_FORMATS_MSG}")
            
            # Image hint (🖼) - only if no quality keys found
            if not found_quality_keys:
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOAD_IMAGE_MSG}")
            
            # Subs hints
            if subs_hint:
                hints.append(subs_hint.strip())
            if subs_warn:
                hints.append(subs_warn.strip())
            
            # Dubs hint (🗣) - only if available
            if get_filters(user_id).get("has_dubs"):
                hints.append(f"{safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG}")
            
            return "\n".join(hints)
        
        # We need to create action_buttons first to determine which hints to show
        # This will be done later in the code, so for now we'll use the old logic
        # but we'll replace it after action_buttons are created
        # Temporary hint for now - will be replaced later
        temp_hint = (
            f"<pre language=\"info\">{safe_get_messages(user_id).ALWAYS_ASK_CHANGE_VIDEO_EXT_MSG}"
            + paid_hint
            + repost_line
            + watch_hint
            + link_hint
            + list_hint
            + image_hint
            + subs_hint
            + subs_warn
            + dubs_hint
            + "</pre>"
        )
        cap += f"\n{temp_hint}\n"
        buttons = []
        # Sort buttons by quality from lowest to highest
        if ("youtube.com" in url or "youtu.be" in url):
            for quality_key in sorted(quality_map.keys(), key=sort_quality_key):
                f = quality_map[quality_key]
                w = f.get('width')
                h = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                if filesize:
                    if filesize and filesize >= 1024*1024*1024:
                        size_str = f"{round(filesize/1024/1024/1024, 2)}GB"
                    else:
                        size_str = f"{round(filesize/1024/1024, 1)}MB"
                else:
                    size_str = '—'
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and filesize:
                    video_bytes = filesize
                    if video_bytes and video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                # Check the availability of subtitles for this quality
                subs_available = ""
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                if subs_enabled:
                    if sel_ext == 'mkv':
                        subs_available = "💬"
                    elif is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
                        # Check if we're in Always Ask mode
                        is_always_ask_mode = is_subs_always_ask(user_id)
                        
                        if is_always_ask_mode:
                            # In Always Ask menu, show 💬 if any subtitles found, regardless of auto_mode
                            if found_type is not None:  # Any subtitles found (auto or normal)
                                temp_info = {
                                    'duration': info.get('duration'),
                                    'filesize': filesize,
                                    'filesize_approx': filesize
                                }
                                if check_subs_limits(temp_info, quality_key):
                                    subs_available = "💬"
                        else:
                            # In manual mode, respect user's auto_mode setting
                            if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                                temp_info = {
                                    'duration': info.get('duration'),
                                    'filesize': filesize,
                                    'filesize_approx': filesize
                                }
                                if check_subs_limits(temp_info, quality_key):
                                    subs_available = "💬"
                
                # Cache/icon (skip if send_as_file is enabled)
                if send_as_file:
                    icon = "1⭐️" if (is_nsfw and is_private_chat) else "📹"
                    postfix = ""
                    button_text = f"{icon}{quality_key}{subs_available}"
                elif is_playlist and playlist_range:
                    # Правильное формирование indices для отрицательных индексов
                    start, end = playlist_range
                    if start < 0 and end < 0:
                        if abs(start) < abs(end):
                            indices = list(range(start, end - 1, -1))
                        else:
                            indices = list(range(start, end + 1, 1))
                    elif start > end:
                        indices = list(range(start, end - 1, -1))
                    else:
                        indices = list(range(start, end + 1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
                    button_text = f"{icon}{quality_key}{subs_available}{postfix}"
                else:
                    # Check if we're in Always Ask mode
                    is_always_ask_mode = is_subs_always_ask(user_id)
                    
                    if is_always_ask_mode:
                        # In Always Ask menu, show 💬 if any subtitles found, regardless of auto_mode
                        need_subs = (subs_enabled and found_type is not None)  # True if any subtitles found
                    else:
                        # In manual mode, respect user's auto_mode setting
                        need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    
                    # Проверяем кэш для одиночного видео
                    is_cached = quality_key in cached_qualities
                    # Дополнительно проверяем кэш по уникальной ссылке видео, если это видео из плейлиста
                    if not is_cached:
                        # Извлекаем уникальную ссылку текущего видео
                        video_page_url = (
                            info.get("webpage_url")
                            or info.get("original_url")
                            or info.get("url")
                            or info.get("canonical_url")
                            or url
                        )
                        # Если это не URL плейлиста, проверяем кэш по уникальной ссылке
                        if video_page_url != url and video_page_url:
                            try:
                                single_video_cached = get_cached_message_ids(video_page_url, quality_key)
                                if single_video_cached:
                                    is_cached = True
                                    logger.info(f"🔍 [CACHE] Найдено одиночное видео в кэше по уникальной ссылке: {video_page_url}, quality: {quality_key}")
                            except Exception as e:
                                logger.warning(f"⚠️ [CACHE] Ошибка при проверке кэша для одиночного видео: {e}")
                    
                    icon = "🚀" if (is_cached and not need_subs and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    button_text = f"{icon}{quality_key}{subs_available}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        else:
            # Show only detected qualities derived from formats (one per quality)
            detected_ordered = sorted(quality_map.keys(), key=sort_quality_key)
            for quality_key in detected_ordered:
                entry = quality_map[quality_key]
                w, h, size_val = entry['w'], entry['h'], entry['size_mb']
                size_str = f"{round(size_val/1024, 1)}GB" if size_val and size_val >= 1024 else (f"{size_val}MB" if size_val else '—')
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and size_val:
                    video_bytes = size_val * 1024 * 1024
                    if video_bytes and video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"

                if is_playlist and playlist_range:
                    # Правильное формирование indices для отрицательных индексов
                    start, end = playlist_range
                    if start < 0 and end < 0:
                        if abs(start) < abs(end):
                            indices = list(range(start, end - 1, -1))
                        else:
                            indices = list(range(start, end + 1, 1))
                    elif start > end:
                        indices = list(range(start, end - 1, -1))
                    else:
                        indices = list(range(start, end + 1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
                    button_text = f"{icon}{quality_key}{postfix}"
                else:
                    # Проверяем кэш для одиночного видео
                    is_cached = quality_key in cached_qualities
                    # Дополнительно проверяем кэш по уникальной ссылке видео, если это видео из плейлиста
                    if not is_cached:
                        try:
                            cached_info = load_ask_info(user_id, url)
                            if cached_info:
                                video_page_url = (
                                    cached_info.get("webpage_url")
                                    or cached_info.get("original_url")
                                    or cached_info.get("url")
                                    or cached_info.get("canonical_url")
                                )
                                # Если это не URL плейлиста, проверяем кэш по уникальной ссылке
                                if video_page_url and video_page_url != url:
                                    single_video_cached = get_cached_message_ids(video_page_url, quality_key)
                                    if single_video_cached:
                                        is_cached = True
                                        logger.info(f"🔍 [CACHE] Найдено одиночное видео в кэше по уникальной ссылке: {video_page_url}, quality: {quality_key}")
                        except Exception as e:
                            logger.warning(f"⚠️ [CACHE] Ошибка при проверке кэша для одиночного видео: {e}")
                    
                    icon = "🚀" if (is_cached and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
                    button_text = f"{icon}{quality_key}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))

        # Always add {safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} Quality button
        quality_key = "best"
        if is_playlist and playlist_range:
            # Правильное формирование indices для отрицательных индексов
            start, end = playlist_range
            if start < 0 and end < 0:
                if abs(start) < abs(end):
                    indices = list(range(start, end - 1, -1))
                else:
                    indices = list(range(start, end + 1, 1))
            elif start > end:
                indices = list(range(start, end - 1, -1))
            else:
                indices = list(range(start, end + 1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
            total = len(indices)
            icon = "🚀" if (n_cached > 0 and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            postfix = f" ({n_cached}/{total})" if total and total > 1 else ""
            button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG}{postfix}"
        else:
            icon = "🚀" if (quality_key in cached_qualities and not is_nsfw) else ("1⭐️" if (is_nsfw and is_private_chat) else "📹")
            button_text = f"{icon}{safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        
        # Always add Other Qualities button
        other_label = f"{safe_get_messages(user_id).ALWAYS_ASK_OTHER_LABEL_MSG}" if not is_nsfw else f"{safe_get_messages(user_id).ALWAYS_ASK_OTHER_LABEL_MSG}"
        buttons.append(InlineKeyboardButton(other_label, callback_data=f"askq|other_qualities"))
        
        if not found_quality_keys:
            # Add explanation when automatic quality detection fails
            autodiscovery_note = safe_get_messages(user_id).QUALITIES_NOT_AUTO_DETECTED_NOTE
            cap += f"\n{autodiscovery_note}\n"

        # --- Form rows of 3 buttons ---
        keyboard_rows = []
        # Add filter rows first
        filter_rows, filter_action_buttons = build_filter_rows(user_id, url, is_private_chat)
        keyboard_rows.extend(filter_rows)
        
        # Collect all action buttons to group them by 3 in a row
        action_buttons = []
        
        # Add filter action buttons (DUBS, SUBS)
        action_buttons.extend(filter_action_buttons)
        
        # Add LINK button - always available
        logger.info(f"Adding LINK button for user {user_id}")
        action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_LINK_BUTTON_MSG, callback_data="askq|link"))
        # Add LIST button - always available
        action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).LIST_BUTTON_TEXT, callback_data="askq|list"))
        # Add IMAGE button only if qualities were NOT auto-detected
        if not found_quality_keys:
            action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).IMAGE_BUTTON_TEXT, callback_data="askq|image"))        
        # Add Quick Embed button for supported services (but not for ranges)
        if (is_instagram_url(url) or is_twitter_url(url) or is_reddit_url(url)) and not is_playlist_with_range(original_text):
            action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_EMBED_BUTTON_MSG, callback_data="askq|quick_embed"))
        
        # Smart grouping of quality buttons - prefer 3 per row, then 2, avoid single buttons
        if buttons:
            total_quality_buttons = len(buttons)
            if total_quality_buttons % 3 == 0:
                # Perfect grouping by 3
                for i in range(0, total_quality_buttons, 3):
                    keyboard_rows.append(buttons[i:i+3])
            elif total_quality_buttons % 3 == 1 and total_quality_buttons > 1:
                # Group by 3, then make last two rows with 2 buttons each
                for i in range(0, total_quality_buttons - 4, 3):
                    keyboard_rows.append(buttons[i:i+3])
                # Last two rows with 2 buttons each
                keyboard_rows.append(buttons[-4:-2])
                keyboard_rows.append(buttons[-2:])
            else:
                # Group by 3, last group might be 1 or 2
                for i in range(0, total_quality_buttons, 3):
                    keyboard_rows.append(buttons[i:i+3])
        
        # Add WATCH button for YouTube links - always add to action_buttons for consistent placement
        try:
            if is_youtube_url(url):
                logger.info(f"Processing YouTube URL for WATCH button: {url}")
                piped_url = youtube_to_piped_url(url)
                logger.info(f"Converted to Piped URL: {piped_url}")
                # Check if this is a group (negative user_id)
                try:
                    is_group = isinstance(user_id, int) and user_id < 0
                except Exception:
                    is_group = False
                if is_group:
                    action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_WATCH_BUTTON_MSG, url=piped_url))
                else:
                    wa = WebAppInfo(url=piped_url)
                    action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_WATCH_BUTTON_MSG, web_app=wa))
                logger.info(f"Added WATCH button to action_buttons for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding WATCH button for user {user_id}: {e}")
            pass
        
        # --- button subtitles only ---
        # Show the button only if subtitles are turned on and it is youtube
        subs_enabled = is_subs_enabled(user_id)
        if subs_enabled and is_youtube_url(url):
            # Check if we're in Always Ask mode
            is_always_ask_mode = is_subs_always_ask(user_id)
            
            if is_always_ask_mode:
                # In Always Ask menu, show button if any subtitles found, regardless of auto_mode
                need_subs = found_type is not None  # True if any subtitles found (auto or normal)
            else:
                # manual mode, respect user's auto_mode setting
                need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            
            if need_subs:
                action_buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_SUB_ONLY_BUTTON_MSG, callback_data="askq|subs_only"))
        
        # Smart grouping of action buttons - prefer 3 buttons per row, then 2, avoid single buttons
        logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_SMART_GROUPING_MSG} {len(action_buttons)} action buttons for user {user_id}")
        if action_buttons:
            # Calculate optimal grouping
            total_buttons = len(action_buttons)
            if total_buttons % 3 == 0:
                # Perfect grouping by 3
                for i in range(0, total_buttons, 3):
                    row = action_buttons[i:i+3]
                    keyboard_rows.append(row)
                    logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_ADDED_ACTION_BUTTON_ROW_3_MSG}: {[btn.text for btn in row]}")
            elif total_buttons % 3 == 1 and total_buttons > 1:
                # Group by 3, then take 2 from last group to make 2+2
                for i in range(0, total_buttons - 4, 3):
                    row = action_buttons[i:i+3]
                    keyboard_rows.append(row)
                    logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_ADDED_ACTION_BUTTON_ROW_3_MSG}: {[btn.text for btn in row]}")
                # Last two rows with 2 buttons each
                keyboard_rows.append(action_buttons[-4:-2])
                keyboard_rows.append(action_buttons[-2:])
                logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_ADDED_ACTION_BUTTON_ROWS_2_2_MSG}: {[btn.text for btn in action_buttons[-4:-2]]}, {[btn.text for btn in action_buttons[-2:]]}")
            else:
                # Group by 3, last group might be 1 or 2
                for i in range(0, total_buttons, 3):
                    row = action_buttons[i:i+3]
                    keyboard_rows.append(row)
                    logger.info(f"Added action button row: {[btn.text for btn in row]}")
        
        # Smart grouping for bottom row - try to combine with action buttons if possible
        bottom_buttons = []
        if bool(filters_state.get('visible', False)):
            bottom_buttons = [InlineKeyboardButton(safe_get_messages(user_id).BACK_BUTTON_TEXT, callback_data="askf|toggle|off"), InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askq|close")]
        else:
            bottom_buttons = [InlineKeyboardButton(safe_get_messages(user_id).CLOSE_BUTTON_TEXT, callback_data="askq|close")]
        
        # Try to add bottom buttons to last action row if it has space
        if keyboard_rows and len(keyboard_rows[-1]) < 3 and len(bottom_buttons) <= (3 - len(keyboard_rows[-1])):
            # Add to existing row
            keyboard_rows[-1].extend(bottom_buttons)
            logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_ADDED_BOTTOM_BUTTONS_TO_EXISTING_ROW_MSG}: {[btn.text for btn in bottom_buttons]}")
        else:
            # Create new row
            keyboard_rows.append(bottom_buttons)
            logger.info(f"{safe_get_messages(user_id).ALWAYS_ASK_CREATED_NEW_BOTTOM_ROW_MSG}: {[btn.text for btn in bottom_buttons]}")
        
        # Log final keyboard structure
        logger.info(f"Final keyboard structure for user {user_id}: {len(keyboard_rows)} rows")
        for i, row in enumerate(keyboard_rows):
            logger.info(f"Row {i}: {[btn.text for btn in row]}")
        
        # Now that we have all action_buttons, create dynamic hints
        # Extract emojis from all buttons to determine which hints to show
        used_emojis = set()
        
        # Check action_buttons
        for button in action_buttons:
            if hasattr(button, 'text') and button.text:
                text = button.text
                if text and len(text) > 0:
                    first_char = text[0]
                    if ord(first_char) > 127:  # Simple emoji detection
                        used_emojis.add(first_char)
        
        # Check quality buttons
        for button in buttons:
            if hasattr(button, 'text') and button.text:
                text = button.text
                if text and len(text) > 0:
                    first_char = text[0]
                    if ord(first_char) > 127:  # Simple emoji detection
                        used_emojis.add(first_char)
        
        # Check filter buttons
        for row in filter_rows:
            for button in row:
                if hasattr(button, 'text') and button.text:
                    text = button.text
                    if text and len(text) > 0:
                        first_char = text[0]
                        if ord(first_char) > 127:  # Simple emoji detection
                            used_emojis.add(first_char)
        
        # Log detected emojis for debugging
        logger.info(f"Detected emojis in menu for user {user_id}: {sorted(used_emojis)}")
        
        # Create dynamic hints based on actually used emojis
        dynamic_hints = []
        
        # Always show format change hint (📼) - this is always available
        dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_CHANGE_VIDEO_EXT_MSG)
        
        # Quality hint (📹) - always sh
        # own unless NSFW
        if is_nsfw and is_private_chat:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_NSFW_PAID_MSG)
        else:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_DOWNLOAD_QUALITY_MSG)
        
        # Repost hint (🚀) - only if show_repost_hint is True AND there are cached qualities
        # Also check if any button has rocket emoji (including Other button)
        has_rocket_button = "🚀" in used_emojis
        if show_repost_hint and cached_qualities and has_rocket_button:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_INSTANT_REPOST_MSG)
        
        # Watch hint (👁) - only for YouTube and if button is present
        if is_youtube_url(url) and "👁" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_WATCH_VIDEO_MSG)
        
        # Link hint (🔗) - always present
        if "🔗" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_GET_DIRECT_LINK_MSG)
        
        # List hint (📃) - always present
        if "📃" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_SHOW_AVAILABLE_FORMATS_MSG)
        
        # Image hint (🖼) - only if no quality keys found and button is present
        if not found_quality_keys and "🖼" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_DOWNLOAD_IMAGE_MSG)
        
        # Audio hint (🎧) - if audio button is present
        if "🎧" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_EXTRACT_AUDIO_MSG)
        
        # Subs hints
        if subs_hint:
            dynamic_hints.append(subs_hint.strip())
        if subs_warn:
            dynamic_hints.append(subs_warn.strip())
        
        # Dubs hint (🗣) - only if available and button is present
        if get_filters(user_id).get("has_dubs") and "🗣" in used_emojis:
            dynamic_hints.append(safe_get_messages(user_id).ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG)
        
        # Replace the old hint in cap with dynamic one
        dynamic_hint_text = "<pre language=\"info\">" + "\n".join(dynamic_hints) + "</pre>"
        
        # Log final hints for debugging
        logger.info(f"Final dynamic hints for user {user_id}: {dynamic_hints}")
        
        # Find and replace the old hint in cap
        import re
        # Remove old hint block
        cap = re.sub(r'<pre language="info">.*?</pre>', '', cap, flags=re.DOTALL)
        # Add new dynamic hint with reduced spacing
        cap += f"{dynamic_hint_text}\n"
        
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        # cap now contains dynamic hints based on actual buttons
        # Replace current menu in-place if possible
        if cb is not None and getattr(cb, 'message', None):
            # Edit caption or text in place
            try:
                if cb.message.photo:
                    cb.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                else:
                    cb.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            except Exception as e:
                logger.warning(f"Failed to edit message for callback: {e}")
                # Fallback: send new message if edit fails
                try:
                    if thumb_path and os.path.exists(thumb_path):
                        app.send_photo(
                            user_id,
                            thumb_path,
                            caption=cap,
                            parse_mode=enums.ParseMode.HTML,
                            reply_markup=keyboard,
                            reply_parameters=ReplyParameters(message_id=message.id),
                            has_spoiler=should_apply_spoiler(user_id, is_nsfw, getattr(message.chat, "type", None) == enums.ChatType.PRIVATE)
                        )
                    else:
                        app.send_message(user_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_parameters=ReplyParameters(message_id=message.id))
                except Exception as fallback_error:
                    logger.error(f"Failed to send fallback message: {fallback_error}")
            # Remove processing message quietly
            if proc_msg:
                try:
                    safe_delete_messages(chat_id=cb.message.chat.id, message_ids=[proc_msg.id])
                except Exception:
                    pass
                proc_msg = None
        else:
            # Fallback: send new message
            if proc_msg:
                try:
                    safe_delete_messages(chat_id=user_id, message_ids=[proc_msg.id])
                except Exception:
                    pass
                proc_msg = None
            # Try to send with keyboard first
            try:
                if thumb_path and os.path.exists(thumb_path):
                    app.send_photo(
                        user_id,
                        thumb_path,
                        caption=cap,
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=keyboard,
                        reply_parameters=ReplyParameters(message_id=message.id),
                        has_spoiler=should_apply_spoiler(user_id, is_nsfw, getattr(message.chat, "type", None) == enums.ChatType.PRIVATE)
                    )
                else:
                    app.send_message(user_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_parameters=ReplyParameters(message_id=message.id))
            except Exception as keyboard_error:
                # If keyboard fails (e.g., BUTTON_TYPE_INVALID), try without keyboard
                logger.warning(f"Failed to send with keyboard, retrying without: {keyboard_error}")
                if thumb_path and os.path.exists(thumb_path):
                    app.send_photo(
                        user_id,
                        thumb_path,
                        caption=cap,
                        parse_mode=enums.ParseMode.HTML,
                        reply_parameters=ReplyParameters(message_id=message.id),
                        has_spoiler=should_apply_spoiler(user_id, is_nsfw, getattr(message.chat, "type", None) == enums.ChatType.PRIVATE)
                    )
                else:
                    app.send_message(user_id, cap, parse_mode=enums.ParseMode.HTML, reply_parameters=ReplyParameters(message_id=message.id))
        send_to_logger(message, safe_get_messages(user_id).ALWAYS_ASK_MENU_SENT_LOG_MSG.format(url=url))
    except FloodWait as e:
        wait_time = e.value
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")
        with open(flood_time_file, 'w') as f:
            f.write(str(wait_time))
        hours = wait_time // 3600
        minutes = (wait_time % 3600) // 60
        seconds = wait_time % 60
        time_str = f"{hours}h {minutes}m {seconds}s"
        flood_msg = safe_get_messages(user_id).AA_FLOOD_WAIT_MSG.format(time_str=time_str)
        if proc_msg:
            try:
                app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=flood_msg)
            except Exception as e:
                if 'MESSAGE_ID_INVALID' not in str(e):
                    logger.warning(f"Failed to edit message: {e}")
            proc_msg = None
        else:
            try:
                app.send_message(user_id, flood_msg, reply_parameters=ReplyParameters(message_id=message.id))
            except FloodWait:
                # Невозможно отправить даже уведомление о FloodWait — просто выходим, время уже сохранено
                pass
            except Exception as e:
                logger.warning(f"Failed to send flood notice: {e}")
        return
    except Exception as e:
        import traceback
        logger.error(f"Error retrieving video information for user {user_id}: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        # ГЛОБАЛЬНАЯ ЗАЩИТА: messages уже инициализирована в начале функции
        # Если по какой-то причине она не инициализирована, используем safe_get_messages
        if 'messages' not in locals():
            try:
                messages = safe_get_messages(user_id)
            except Exception:
                # Если все не удается, создаем минимальную защиту
                # Используем правильную систему переводов
                messages = safe_get_messages(user_id)
        
        # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: Убедимся, что messages инициализирована
        try:
            _ = safe_get_messages(user_id).ALWAYS_ASK_NO_VIDEOS_FOUND_IN_PLAYLIST_MSG
        except (NameError, AttributeError):
            # Если messages все еще не инициализирована, создаем экстренную версию
            # Используем правильную систему переводов
            messages = safe_get_messages(user_id)
        # If this looks like a non-video URL, try gallery-dl fallback first
        try:
            emsg = str(e)
            if (
                safe_get_messages(user_id).ALWAYS_ASK_NO_VIDEOS_FOUND_IN_PLAYLIST_MSG in emsg
                or safe_get_messages(user_id).ALWAYS_ASK_UNSUPPORTED_URL_MSG in emsg
                or safe_get_messages(user_id).ALWAYS_ASK_NO_VIDEO_COULD_BE_FOUND_MSG in emsg
                or safe_get_messages(user_id).ALWAYS_ASK_NO_VIDEO_FOUND_MSG in emsg
                or safe_get_messages(user_id).ALWAYS_ASK_NO_MEDIA_FOUND_MSG in emsg
                or safe_get_messages(user_id).ALWAYS_ASK_THIS_TWEET_DOES_NOT_CONTAIN_MSG in emsg
            ):
                try:
                    from COMMANDS.image_cmd import image_command
                    from HELPERS.safe_messeger import fake_message
                except Exception as imp_e:
                    logger.error(f"Failed to import gallery-dl fallback handlers (menu): {imp_e}")
                else:
                    try:
                        safe_edit_message_text(user_id, proc_msg.id if proc_msg else None,
                            safe_get_messages(user_id).AA_NO_VIDEO_FORMATS_FOUND_MSG)
                    except Exception:
                        pass
                    try:
                        # Check if content is NSFW for fallback
                        from HELPERS.porn import is_porn
                        is_nsfw = is_porn(url, "", "", None)
                        logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_IS_PORN_CHECK_LOG_MSG} {url}: {is_nsfw}")
                        
                        # Check for explicit NSFW tags
                        user_forced_nsfw = any(t.lower() in ("#nsfw", "#porn") for t in (tags or []))
                        if user_forced_nsfw:
                            is_nsfw = True
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_USER_FORCED_NSFW_TAG_DETECTED_LOG_MSG} {url}")
                        
                        # ЖЕСТКО: Используем оригинальный текст сообщения
                        original_text = message.text or message.caption or ""
                        logger.info(f"[ASKQ FALLBACK DEBUG] original_text: {original_text}")
                        
                        # Ищем URL с диапазоном *start*end
                        import re
                        range_url_match = re.search(r'(https?://[^\s\*#]+)\*(\d+)\*(\d+)', original_text)
                        if range_url_match:
                            parsed_url = range_url_match.group(1)
                            start_range = int(range_url_match.group(2))
                            end_range = int(range_url_match.group(3))
                            logger.info(f"[ASKQ FALLBACK DEBUG] FOUND RANGE: {parsed_url} with range {start_range}-{end_range}")
                        else:
                            # Fallback к обычному URL
                            m = re.search(r'https?://[^\s\*#]+', original_text)
                            parsed_url = m.group(0) if m else original_text
                            start_range = 1
                            end_range = 1
                            logger.info(f"[ASKQ FALLBACK DEBUG] NO RANGE FOUND, using url: {parsed_url}")
                        
                        # Build fallback command converting *1*10 to 1-10 format
                        if start_range and end_range and (start_range != 1 or end_range != 1):
                            # Convert *1*10 format to 1-10 format
                            fallback_text = f"/img {start_range}-{end_range} {parsed_url}"
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_CONVERTING_RANGE_LOG_MSG}: *{start_range}*{end_range} -> {start_range}-{end_range}, fallback_text: {fallback_text}")
                        else:
                            fallback_text = f"/img {parsed_url}"
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_NO_RANGE_DETECTED_LOG_MSG}: {fallback_text}")
                        
                        if tags:
                            tags_text = ' '.join(tags)
                            fallback_text += f" {tags_text}"
                        
                        # Add NSFW tag if content is detected as NSFW
                        if is_nsfw and "#nsfw" not in fallback_text.lower():
                            fallback_text += " #nsfw"
                            logger.info(f"{LoggerMsg.ALWAYS_ASK_FALLBACK_ADDED_NSFW_TAG_LOG_MSG}: {url}")
                        
                        # For groups, preserve original chat_id and message_thread_id
                        original_chat_id = user_id
                        message_thread_id = None  # This is for private chat fallback
                        image_command(app, fake_message(fallback_text, user_id, original_chat_id=original_chat_id, message_thread_id=message_thread_id, original_message=None))
                        logger.info(f"Triggered gallery-dl fallback via /img from Always Ask menu, is_nsfw={is_nsfw}, range={start_range}-{end_range}")
                        return
                    except Exception as call_e:
                        logger.error(f"Failed to trigger gallery-dl fallback from Always Ask menu: {call_e}")
        except Exception:
            pass
        
        # Сначала пробуем создать меню из кэшированных качеств
        try:
            logger.info(f"Attempting to create menu from cached qualities for user {user_id}")
            if create_cached_qualities_menu(app, message, url, tags, proc_msg, user_id, original_text, is_playlist, playlist_range):
                logger.info(f"Successfully created cached qualities menu for user {user_id}")
                send_to_logger(message, safe_get_messages(user_id).CACHED_QUALITIES_MENU_CREATED_LOG_MSG.format(user_id=user_id, error=str(e)))
                return
            else:
                logger.info(f"No cached qualities available for user {user_id}, showing error message")
        except Exception as cache_error:
            logger.error(f"Error creating cached qualities menu: {cache_error}")
        
        # Если кэшированных качеств нет, показываем ошибку
        error_text = f"{safe_get_messages(user_id).ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_MSG}\n<blockquote>{safe_get_messages(user_id).ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_SHORT_MSG}</blockquote>\n\n{safe_get_messages(user_id).ALWAYS_ASK_TRY_CLEAN_COMMAND_MSG}"
        
        # Try to edit the processing message to show error first
        try:
            if proc_msg:
                result = app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=error_text, parse_mode=enums.ParseMode.HTML)
                if result is not None:
                    # Successfully edited the processing message, now log to channel
                    log_error_to_channel(message, safe_get_messages(user_id).ALWAYS_ASK_MENU_ERROR_LOG_MSG.format(url=url, error=safe_get_messages(user_id).ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_SHORT_MSG), url)
                    return
        except Exception as e2:
            logger.error(f"Error editing processing message: {e2}")
        
        # If editing failed or no proc_msg, send new message to user
        logger.error(f"Always Ask menu error for user {user_id}: {safe_get_messages(user_id).ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_SHORT_MSG}")
        from HELPERS.safe_messeger import safe_send_message
        safe_send_message(user_id, error_text, parse_mode=enums.ParseMode.HTML, message=message)
        log_error_to_channel(message, safe_get_messages(user_id).ALWAYS_ASK_MENU_ERROR_LOG_MSG.format(url=url, error=safe_get_messages(user_id).ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_SHORT_MSG), url)
        return

def askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs, proc_msg=None):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    tags = tags_text.split() if tags_text else []
    
    # Check if LINK mode is enabled
    if get_link_mode(user_id):
        # Get direct link instead of downloading
        try:
            callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_GETTING_DIRECT_LINK_MSG)
        except Exception:
            pass
        
        # Import link function
        from COMMANDS.link_cmd import get_direct_link
        
        # Convert quality key to quality argument
        quality_arg = None
        if data != "best" and data != "mp3":
            quality_arg = data
        
        # Get direct link - use proxy only if user has proxy enabled and domain requires it
        result = get_direct_link(url, user_id, quality_arg, cookies_already_checked=True, use_proxy=False)
        
        if result.get('success'):
            title = result.get('title', 'Unknown')
            duration = result.get('duration', 0)
            video_url = result.get('video_url')
            audio_url = result.get('audio_url')
            format_spec = result.get('format', 'best')
            
            # Form response
            response = f"{safe_get_messages(user_id).ALWAYS_ASK_DIRECT_LINK_OBTAINED_MSG}\n\n"
            response += f"{safe_get_messages(user_id).ALWAYS_ASK_TITLE_MSG} {title}\n"
            if duration and duration > 0:
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_DURATION_SEC_MSG} {duration} sec\n"
            response += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_CODE_MSG} <code>{format_spec}</code>\n\n"
            
            if video_url:
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_VIDEO_STREAM_MSG}\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
            
            if audio_url:
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_AUDIO_STREAM_MSG}\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
            
            if not video_url and not audio_url:
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_FAILED_TO_GET_STREAM_LINKS_MSG}"
            
            # Send response
            app.send_message(
                user_id, 
                response, 
                reply_parameters=ReplyParameters(message_id=original_message.id),
                parse_mode=enums.ParseMode.HTML
            )
            
            send_to_logger(original_message, safe_get_messages(user_id).DIRECT_LINK_EXTRACTED_ALWAYS_ASK_LOG_MSG.format(user_id=user_id, url=url))
            
        else:
            error_msg = result.get('error', 'Unknown error')
            app.send_message(
                user_id,
                safe_get_messages(user_id).AA_ERROR_GETTING_LINK_MSG.format(error_msg=error_msg),
                reply_parameters=ReplyParameters(message_id=original_message.id),
                parse_mode=enums.ParseMode.HTML
            )
            
            log_error_to_channel(original_message, safe_get_messages(user_id).DIRECT_LINK_FAILED_ALWAYS_ASK_LOG_MSG.format(user_id=user_id, url=url, error=error_msg), url)
        
        return
    # Read current filters to build correct format strings and container override
    try:
        filters_state = get_filters(user_id)
    except Exception:
        filters_state = {"codec": "avc1", "ext": "mp4"}
    sel_codec = filters_state.get("codec", "avc1")
    sel_ext = filters_state.get("ext", "mp4")
    sel_audio_lang = filters_state.get("audio_lang")
    
    # Get selected subtitle language from filters (for Always Ask mode)
    selected_subs_lang = filters_state.get("selected_subs_lang")
    if selected_subs_lang:
        # Temporarily save the selected subtitle language for this download
        from COMMANDS.subtitles_cmd import save_user_subs_language, save_user_subs_auto_mode
        save_user_subs_language(user_id, selected_subs_lang)
        # If user picks explicit language from SUBS menu – assume manual, not auto
        save_user_subs_auto_mode(user_id, False)
        logger.info(f"Using selected subtitle language from Always Ask: {selected_subs_lang}")
    try:
        set_session_mkv_override(user_id, sel_ext == "mkv")
    except Exception:
        pass
    if data == "mp3":
        try:
            callback_query.answer("🎧 Downloading audio...")
        except Exception:
            pass
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        # Правильное вычисление video_count для отрицательных индексов
        if video_start_with < 0 and video_end_with < 0:
            video_count = abs(video_end_with) - abs(video_start_with) + 1
        elif video_start_with > video_end_with:
            video_count = abs(video_start_with - video_end_with) + 1
        else:
            video_count = video_end_with - video_start_with + 1
        # Delete processing message before starting download
        delete_processing_message(app, user_id, proc_msg)
        down_and_audio(app, original_message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with, format_override="ba", cookies_already_checked=True, cached_video_info=None)
        return
    
    if data == "subs_only":
        try:
            callback_query.answer("💬 Downloading subtitles only...")
        except Exception:
            pass
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        # Правильное вычисление video_count для отрицательных индексов
        if video_start_with < 0 and video_end_with < 0:
            video_count = abs(video_end_with) - abs(video_start_with) + 1
        elif video_start_with > video_end_with:
            video_count = abs(video_start_with - video_end_with) + 1
        else:
            video_count = video_end_with - video_start_with + 1
        download_subtitles_only(app, original_message, url, tags, available_langs, playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    # Logic for forming the format with the real height
    if data == "best":
        try:
            callback_query.answer(safe_get_messages(user_id).ALWAYS_ASK_DOWNLOADING_BEST_QUALITY_MSG)
        except Exception:
            pass
        # Use format with AVC codec and MP4 container priority for {safe_get_messages(user_id).ALWAYS_ASK_BEST_BUTTON_MSG} quality
        # with fallback to bv+ba/best if no AVC+MP4 available
        audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
        fmt = f"bv*[vcodec*={sel_codec}][ext={sel_ext}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba{audio_filter}/bv*[ext={sel_ext}]+ba{audio_filter}/bv+ba/best"
        quality_key = "best"
    else:
        try:
            # Get information about the video to determine the sizes - try cached info first
            cached_info = load_ask_info(user_id, url)
            if cached_info:
                info = cached_info
                logger.info(f"✅ [OPTIMIZATION] Using cached video info for size determination")
            else:
                info = get_video_formats(url, user_id, cookies_already_checked=True)
                logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info for size determination")
            formats = info.get('formats', [])
            
            # Find the format with the highest quality to determine the sizes
            max_width = 0
            max_height = 0
            for f in formats:
                if f.get('width') and f.get('height'):
                    if f['width'] > max_width:
                        max_width = f['width']
                    if f['height'] > max_height:
                        max_height = f['height']
            
            # If the sizes are not found, use the standard logic
            if max_width == 0 or max_height == 0:
                quality_str = data.replace('p', '')
                quality_val = int(quality_str)
                # choose previous rung for lower bound
                if quality_val and quality_val >= 4320:
                    prev = 2160
                elif quality_val and quality_val >= 2160:
                    prev = 1440
                elif quality_val and quality_val >= 1440:
                    prev = 1080
                elif quality_val and quality_val >= 1080:
                    prev = 720
                elif quality_val and quality_val >= 720:
                    prev = 480
                elif quality_val and quality_val >= 480:
                    prev = 360
                elif quality_val and quality_val >= 360:
                    prev = 240
                elif quality_val and quality_val >= 240:
                    prev = 144
                else:
                    prev = 0
                audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                fmt = f"bv*[vcodec*={sel_codec}][height<={quality_val}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={quality_val}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
            else:
                # Determine the quality by the smaller side
                min_side_quality = get_quality_by_min_side(max_width, max_height)
                
                # If the selected quality does not match the smaller side, use the standard logic
                if data != min_side_quality:
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    if quality_val and quality_val >= 4320:
                        prev = 2160
                    elif quality_val and quality_val >= 2160:
                        prev = 1440
                    elif quality_val and quality_val >= 1440:
                        prev = 1080
                    elif quality_val and quality_val >= 1080:
                        prev = 720
                    elif quality_val and quality_val >= 720:
                        prev = 480
                    elif quality_val and quality_val >= 480:
                        prev = 360
                    elif quality_val and quality_val >= 360:
                        prev = 240
                    elif quality_val and quality_val >= 240:
                        prev = 144
                    else:
                        prev = 0
                    audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                    fmt = f"bv*[vcodec*={sel_codec}][height<={quality_val}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={quality_val}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
                else:
                    # Use the real height to form the format
                    real_height = get_real_height_for_quality(data, max_width, max_height)
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    if quality_val and quality_val >= 4320:
                        prev = 2160
                    elif quality_val and quality_val >= 2160:
                        prev = 1440
                    elif quality_val and quality_val >= 1440:
                        prev = 1080
                    elif quality_val and quality_val >= 1080:
                        prev = 720
                    elif quality_val and quality_val >= 720:
                        prev = 480
                    elif quality_val and quality_val >= 480:
                        prev = 360
                    elif quality_val and quality_val >= 360:
                        prev = 240
                    elif quality_val and quality_val >= 240:
                        prev = 144
                    else:
                        prev = 0
                    audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                    fmt = f"bv*[vcodec*={sel_codec}][height<={real_height}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={real_height}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
            
            quality_key = data
            try:
                callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOADING_QUALITY_MSG} {data}...")
            except Exception:
                pass
        except ValueError:
            callback_query.answer("Unknown quality.")
            return
    
    # Delete processing message before starting download
    delete_processing_message(app, user_id, proc_msg)
    down_and_up_with_format(app, original_message, url, fmt, tags_text, quality_key=quality_key, proc_msg=proc_msg)

def analyze_format_type(format_info):
    """
    Analyze format info to determine if it's audio-only, video-only, or full format
    Returns: 'audio_only', 'video_only', or 'full'
    """
    vcodec = format_info.get('vcodec', 'none')
    acodec = format_info.get('acodec', 'none')
    
    # Check if it's audio only
    if vcodec == 'none' and acodec != 'none':
        return 'audio_only'
    
    # Check if it's video only
    if vcodec != 'none' and acodec == 'none':
        return 'video_only'
    
    # Full format (both video and audio)
    return 'full'

def get_complementary_audio_format(video_format_info, all_formats):
    """
    Find the best complementary audio format for a video-only format
    Returns the best audio format or None
    """
    video_height = video_format_info.get('height', 0)
    video_width = video_format_info.get('width', 0)
    
    best_audio = None
    best_quality = 0
    
    for f in all_formats:
        # Look for audio-only formats
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
            # Prefer audio with similar quality to video
            audio_height = f.get('height', 0)
            audio_width = f.get('width', 0)
            
            # Calculate quality score (prefer higher bitrate/quality)
            quality_score = 0
            if f.get('abr'):
                quality_score += float(f['abr'])
            if f.get('tbr'):
                quality_score += float(f['tbr'])
            
            # Bonus for matching resolution
            if audio_height == video_height and audio_width == video_width:
                quality_score += 1000
            
            if quality_score and quality_score > best_quality:
                best_quality = quality_score
                best_audio = f
    
    return best_audio

# --- an auxiliary function for downloading with the format ---
# @reply_with_keyboard
def down_and_up_with_format(app, message, url, fmt, tags_text, quality_key=None, proc_msg=None):
    messages = safe_get_messages(message.chat.id)
    user_id = message.chat.id

    # We extract the range and other parameters from the original user message
    full_string = message.text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)

    # This mistake should have already been caught earlier, but for safety
    if tag_error:
        wrong, example = tag_error
        error_msg = safe_get_messages(user_id).AA_TAG_FORBIDDEN_CHARS_MSG.format(wrong=wrong, example=example)
        app.send_message(message.chat.id, error_msg, reply_parameters=ReplyParameters(message_id=message.id))
        log_error_to_channel(message, error_msg, url)
        return

    # Правильное вычисление video_count для отрицательных индексов
    if video_start_with < 0 and video_end_with < 0:
        video_count = abs(video_end_with) - abs(video_start_with) + 1
    elif video_start_with > video_end_with:
        video_count = abs(video_start_with - video_end_with) + 1
    else:
        video_count = video_end_with - video_start_with + 1
    
    # Check if there is a link to Tiktok
    is_tiktok = is_tiktok_url(url)
    
    # Check if LINK mode is enabled - if yes, get direct link instead of downloading
    user_id = message.chat.id
    try:
        if get_link_mode(user_id):
            logger.info(f"LINK mode enabled for user {user_id}, getting direct link instead of downloading")
            
            # Import link function
            from COMMANDS.link_cmd import get_direct_link
            
            # Convert quality key to quality argument
            quality_arg = None
            if quality_key and quality_key != "best" and quality_key != "mp3":
                quality_arg = quality_key
            
            # Get direct link
            result = get_direct_link(url, user_id, quality_arg, cookies_already_checked=True, use_proxy=True)
            
            if result.get('success'):
                title = result.get('title', 'Unknown')
                duration = result.get('duration', 0)
                video_url = result.get('video_url')
                audio_url = result.get('audio_url')
                format_spec = result.get('format', 'best')
                
                # Form response
                response = f"{safe_get_messages(user_id).ALWAYS_ASK_DIRECT_LINK_OBTAINED_MSG}\n\n"
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_TITLE_MSG} {title}\n"
                if duration and duration > 0:
                    response += f"{safe_get_messages(user_id).ALWAYS_ASK_DURATION_SEC_MSG} {duration} sec\n"
                response += f"{safe_get_messages(user_id).ALWAYS_ASK_FORMAT_CODE_MSG} <code>{format_spec}</code>\n\n"
                
                if video_url:
                    response += f"{safe_get_messages(user_id).ALWAYS_ASK_VIDEO_STREAM_MSG}\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
                
                if audio_url:
                    response += f"{safe_get_messages(user_id).ALWAYS_ASK_AUDIO_STREAM_MSG}\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
                
                if not video_url and not audio_url:
                    response += f"{safe_get_messages(user_id).ALWAYS_ASK_FAILED_TO_GET_STREAM_LINKS_MSG}"
                
                # Send response
                app.send_message(
                    user_id, 
                    response, 
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                send_to_logger(message, safe_get_messages(user_id).DIRECT_LINK_EXTRACTED_DOWN_UP_LOG_MSG.format(user_id=user_id, url=url))
                
            else:
                error_msg = result.get('error', 'Unknown error')
                app.send_message(
                    user_id,
                    f"❌ <b>Error getting link:</b>\n{error_msg}",
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                log_error_to_channel(message, safe_get_messages(user_id).DIRECT_LINK_FAILED_DOWN_UP_LOG_MSG.format(user_id=user_id, url=url, error=error_msg), url)
            
            return
    except Exception as e:
        logger.error(f"Error checking LINK mode for user {user_id}: {e}")
        # Continue with normal download if LINK mode check fails

    # Check if format contains /bestaudio (audio-only format)
    logger.info(f"Checking format: {fmt} for /bestaudio")
    if fmt and '/bestaudio' in fmt:
        logger.info(f"Audio-only format detected: {fmt}, redirecting to down_and_audio")
        # Delete processing message before starting download
        delete_processing_message(app, user_id, proc_msg)
        down_and_audio(app, message, url, tags_text, quality_key=quality_key, format_override=fmt, cookies_already_checked=True, cached_video_info=None)
        return

    # Analyze the format to determine if it's audio-only, video-only, or full
    format_type = None
    complementary_format = None
    info = None  # Initialize info variable
    
    try:
        # Get video info to analyze the selected format
        user_id = message.chat.id
        # Try to load cached info first to avoid redundant API calls
        cached_info = load_ask_info(user_id, url)
        if cached_info:
            info = cached_info
            logger.info(f"✅ [OPTIMIZATION] Using cached video info for format analysis")
        else:
            info = get_video_formats(url, user_id, cookies_already_checked=True)
            logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info again - consider improving caching")
        
        if quality_key and info and 'formats' in info:
            # Find the selected format
            selected_format = None
            for f in info['formats']:
                if f.get('format_id') == quality_key:
                    selected_format = f
                    break
            
            if selected_format:
                format_type = analyze_format_type(selected_format)
                
                # If it's audio-only, convert to user's preferred audio format
                if format_type == 'audio_only':
                    # Use audio download function with the selected format
                    # Pass cookies_already_checked=True since we already checked cookies in get_video_formats
                    # Delete processing message before starting download
                    delete_processing_message(app, user_id, proc_msg)
                    down_and_audio(app, message, url, tags_text, quality_key=quality_key, format_override=fmt, cookies_already_checked=True, cached_video_info=info)
                    return
                
                # If it's video-only, find complementary audio
                elif format_type == 'video_only':
                    complementary_format = get_complementary_audio_format(selected_format, info['formats'])
                    if complementary_format:
                        # Create a format string that merges video-only with best audio
                        video_format_id = selected_format.get('format_id', '')
                        audio_format_id = complementary_format.get('format_id', '')
                        fmt = f"{video_format_id}+{audio_format_id}/bv+ba/best"
                    else:
                        # If no complementary audio found, use best audio
                        fmt = f"{selected_format.get('format_id', '')}+bestaudio/bv+ba/best"
                
                # If it's full format, use as is
                else:
                    # Use the original format
                    pass
    except Exception as e:
        logger.warning(f"Error analyzing format type: {e}")
        # Continue with original format if analysis fails
        # info remains None if there was an error

    # We call the main function of loading with the correct parameters of the playlist
    # Pass cookies_already_checked=True since we already checked cookies in get_video_formats
    # Pass cached video info to avoid redundant API calls
    # Delete processing message before starting download
    delete_processing_message(app, user_id, proc_msg)
    down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=is_tiktok, format_override=fmt, quality_key=quality_key, cookies_already_checked=True, cached_video_info=info)
    # Cleanup temp subs languages cache after we kicked off download
    try:
        delete_subs_langs_cache(message.chat.id, url)
    except Exception:
        pass

    # Save detected qualities per filters to a per-user file for all services
    try:
        # Use download directory if available, otherwise fallback to user directory
        download_dir = get_user_download_dir(user_id)
        if download_dir and os.path.exists(download_dir):
            qfile = os.path.join(download_dir, "available_qualities.txt")
            logger.info(f"Saving available_qualities.txt to download directory: {qfile}")
        else:
            user_dir = os.path.join("users", str(user_id))
            create_directory(user_dir)
            qfile = os.path.join(user_dir, "available_qualities.txt")
            logger.info(f"Saving available_qualities.txt to user directory: {qfile}")
        
        # Get current filters
        filters_state = get_filters(user_id)
        sel_codec = filters_state.get("codec", "avc1")
        sel_ext = filters_state.get("ext", "mp4")
        
        # Build quality map from available formats (only if info is available)
        quality_map = {}
        if info and 'formats' in info:
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                    w = f['width']
                    h = f['height']
                    quality_key = get_quality_by_min_side(w, h)
                    if quality_key != "best":
                        quality_map[quality_key] = f
        
        payload = {
            "url": info.get('webpage_url') if info else url,
            "sel_codec": sel_codec,
            "sel_ext": sel_ext,
            "qualities": sorted(list(quality_map.keys()), key=sort_quality_key)
        }
        import json as _json
        with open(qfile, "w", encoding="utf-8") as f:
            f.write(_json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.warning(f"Failed to save available_qualities.txt: {e}")
    