# ===================== /img command =====================
import os
import re
import subprocess
import tempfile
import threading
import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters, InputMediaPhoto, InputMediaVideo, InputPaidMediaPhoto, InputPaidMediaVideo
from pyrogram import enums
from pyrogram.errors import FloodWait
from HELPERS.logger import send_to_logger, logger, get_log_channel, log_error_to_channel
from CONFIG.logger_msg import LoggerMsg
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.domains import DomainsConfig
from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.decorators import background_handler
import HELPERS.safe_messeger as sm
from DOWN_AND_UP.gallery_dl_hook import (
    get_image_info,
    download_image,
    get_total_media_count,
    download_image_range,
    download_image_range_cli,
)
from HELPERS.filesystem_hlp import create_directory
from COMMANDS.proxy_cmd import is_proxy_enabled
from CONFIG.limits import LimitsConfig
from CONFIG.config import Config
from HELPERS.limitter import is_user_in_channel
from HELPERS.porn import is_porn
from COMMANDS.nsfw_cmd import should_apply_spoiler
from DATABASE.cache_db import save_to_image_cache, get_cached_image_posts, get_cached_image_post_indices
import json
from URL_PARSERS.tags import save_user_tags, extract_url_range_tags
from URL_PARSERS.service_api_info import get_service_account_info, build_tags

# Unified helpers to create thumbnails/covers for videos
def _get_file_mb(file_path):
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0

def _get_video_duration_seconds(video_path):
    try:
        # Minimal ffprobe to get duration
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'format=duration', '-of', 'json', video_path
        ], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return 0.0
        data = json.loads(result.stdout or '{}')
        dur = float(data.get('format', {}).get('duration', 0.0))
        return dur if dur and dur > 0 else 0.0
    except Exception:
        return 0.0

def _should_generate_cover(video_path):
    """Generate cover unless both duration<60s AND size<10MB (i.e., generate if duration and duration >= 60s OR size>=10MB)."""
    try:
        duration = _get_video_duration_seconds(video_path)
        size_mb = _get_file_mb(video_path)
        return (duration >= 60.0) or (size_mb >= 10.0)
    except Exception:
        return False

def _probe_video_info(video_path):
    """Return dict with width,height,duration (seconds, int) using ffprobe."""
    info = {"width": None, "height": None, "duration": None}
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout or '{}')
        # Duration
        dur = None
        try:
            dur = float(data.get('format', {}).get('duration', 0) or 0)
        except Exception:
            dur = 0.0
        info["duration"] = int(dur) if dur and dur > 0 else None
        # Resolution
        streams = data.get('streams', []) or []
        if streams:
            w = streams[0].get('width')
            h = streams[0].get('height')
            info["width"] = int(w) if w else None
            info["height"] = int(h) if h else None
    except Exception:
        pass
    return info

def generate_video_thumbnail(video_path):
    """Generate a JPEG thumbnail for /img command. Named specially and skipped from sending. Returns path or None."""
    try:
        if not video_path or not _should_generate_cover(video_path):
            return None
        base_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        thumb_path = os.path.join(base_dir, base_name + '.__tgthumb.jpg')
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'thumbnail,scale=640:-1',
            '-frames:v', '1', thumb_path
        ], capture_output=True, text=True, timeout=30)
        return thumb_path if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0 else None
    except Exception:
        return None

def ensure_paid_cover_embedded(video_path, existing_thumb=None):
    """Ensure a small JPEG cover (~<=320x320) with сохранением пропорций (паддинг), для платных медиа."""
    try:
        if not _should_generate_cover(video_path):
            return None
        # Prefer an existing thumb if available
        if existing_thumb and os.path.exists(existing_thumb) and os.path.getsize(existing_thumb) > 0:
            return existing_thumb
        base_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        cover_path = os.path.join(base_dir, base_name + '.__tgcover_paid.jpg')
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
            return cover_path
        # 320x320 максимум: уменьшаем c сохранением пропорций, затем pad до 320x320; стараемся держать файл маленьким
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'scale=320:320:force_original_aspect_ratio=decrease,pad=320:320:(ow-iw)/2:(oh-ih)/2:black',
            '-vframes', '1', '-q:v', '4', cover_path
        ], capture_output=True, text=True, timeout=30)
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
            return cover_path
        # Fallback to regular thumb if padding failed
        reg_thumb = generate_video_thumbnail(video_path)
        return reg_thumb if reg_thumb and os.path.getsize(reg_thumb) > 0 else None
    except Exception:
        return None

def ensure_paid_cover_embedded(video_path, existing_thumb=None):
    """Ensure a small JPEG cover (~<=320x320) with сохранением пропорций (паддинг), для платных медиа.
    For videos >60s or >10MB, also embed the cover into the video file itself."""
    try:
        if not _should_generate_cover(video_path):
            return None
        
        # First, generate the cover image
        cover_path = _generate_paid_cover_image(video_path, existing_thumb)
        if not cover_path:
            return None
            
        # For videos that need cover embedding (long duration or large size), embed the cover
        try:
            duration = _get_video_duration_seconds(video_path)
            size_mb = _get_file_mb(video_path)
            
            if (duration >= 60.0) or (size_mb >= 10.0):
                # Create embedded version
                base_dir = os.path.dirname(video_path)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                embedded_path = os.path.join(base_dir, base_name + '.__embedded_cover.mp4')
                
                # Embed cover into video using ffmpeg
                subprocess.run([
                    'ffmpeg', '-y', '-i', video_path, '-i', cover_path,
                    '-map', '0:v', '-map', '0:a', '-map', '1:v',
                    '-c:v', 'libx264', '-c:a', 'copy',
                    '-disposition:v:0', 'default',
                    '-disposition:v:1', 'attached_pic',
                    '-metadata:s:v:1', 'title=Cover',
                    '-metadata:s:v:1', 'comment=Cover (front)',
                    embedded_path
                ], capture_output=True, text=True, timeout=120)
                
                if os.path.exists(embedded_path) and os.path.getsize(embedded_path) > 0:
                    # Replace original with embedded version
                    os.replace(embedded_path, video_path)
                    logger.info(LoggerMsg.IMG_PAID_EMBEDDED_COVER_LOG_MSG.format(video_path=video_path))
        except Exception as e:
            logger.warning(LoggerMsg.IMG_PAID_FAILED_EMBED_COVER_LOG_MSG.format(video_path=video_path, e=e))
            # Continue with just the cover file
        
        return cover_path
    except Exception:
        return None

def _generate_paid_cover_image(video_path, existing_thumb=None):
    """Generate the cover image file (internal helper for ensure_paid_cover_embedded)."""
    try:
        # Prefer an existing thumb if available
        if existing_thumb and os.path.exists(existing_thumb) and os.path.getsize(existing_thumb) > 0:
            return existing_thumb
        base_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        cover_path = os.path.join(base_dir, base_name + '.__tgcover_paid.jpg')
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
            return cover_path
        # 320x320 максимум: уменьшаем c сохранением пропорций, затем pad до 320x320; стараемся держать файл маленьким
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'scale=320:320:force_original_aspect_ratio=decrease,pad=320:320:(ow-iw)/2:(oh-ih)/2:black',
            '-vframes', '1', '-q:v', '4', cover_path
        ], capture_output=True, text=True, timeout=30)
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
            return cover_path
        # Fallback to regular thumb if padding failed
        reg_thumb = generate_video_thumbnail(video_path)
        return reg_thumb if reg_thumb and os.path.getsize(reg_thumb) > 0 else None
    except Exception:
        return None

# removed unused embed_poster_into_mp4

# Get app instance for decorators
app = get_app()

def _send_open_copy_to_nsfw_channel(file_path: str, caption: str, user_id: int, message_id: int, is_video: bool = False):
    messages = safe_get_messages(user_id)
    """Send open copy of media to NSFW channel for history"""
    try:
        # Use explicit NSFW channel to avoid any fallback to LOGS_ID
        log_channel_nsfw = get_log_channel("video", nsfw=True)
        
        if is_video:
            # Send as video
            open_msg = app.send_video(
                chat_id=log_channel_nsfw,
                video=file_path,
                caption=caption,
                reply_parameters=ReplyParameters(message_id=message_id)
            )
        else:
            # Send as photo
            open_msg = app.send_photo(
                chat_id=log_channel_nsfw,
                photo=file_path,
                caption=caption,
                reply_parameters=ReplyParameters(message_id=message_id)
            )
        
        logger.info(LoggerMsg.IMG_LOG_OPEN_COPY_SENT_LOG_MSG.format(file_path=file_path))
        return open_msg
    except Exception as e:
        logger.error(LoggerMsg.IMG_LOG_FAILED_SEND_OPEN_COPY_LOG_MSG.format(e=e))
        return None

def _save_album_now(url: str, album_index: int, message_ids: list):
    try:
        # Determine channel type for logging
        try:
            is_nsfw = bool(is_porn(url, "", "", None))
            channel_type = "NSFW" if is_nsfw else "regular"
        except Exception:
            channel_type = "unknown"
        
        # Don't cache NSFW content
        if is_nsfw:
            logger.info(LoggerMsg.IMG_CACHE_SKIP_NSFW_LOG_MSG.format(album_index=album_index, channel_type=channel_type))
            return
        
        logger.info(LoggerMsg.IMG_CACHE_SAVE_ALBUM_LOG_MSG.format(album_index=album_index, message_ids=message_ids, channel_type=channel_type))
        save_to_image_cache(url, album_index, message_ids)
        logger.info(LoggerMsg.IMG_CACHE_SAVE_REQUESTED_LOG_MSG.format(album_index=album_index, channel_type=channel_type))
    except Exception as e:
        logger.error(LoggerMsg.IMG_CACHE_SAVE_FAILED_LOG_MSG.format(album_index=album_index, e=e))

def extract_profile_name(url):
    """Получить имя аккаунта по API/OG для генерации хэштега (без #)."""
    try:
        info = get_service_account_info(url)
        _service_tag, account_tag = build_tags(info)
        if account_tag:
            return account_tag.lstrip('#')
    except Exception:
        pass
    return None

def extract_site_name(url):
    """Получить имя площадки (service) по API/OG для генерации хэштега (без #)."""
    try:
        info = get_service_account_info(url)
        service = info.get('service')
        if service:
            return service
    except Exception:
        pass
    return None

def get_emoji_number(index):
    """Get emoji number for given index (1-based)"""
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    if 1 <= index <= 10:
        return emoji_numbers[index - 1]
    else:
        return f"{index}."

def get_file_date(file_path, original_url=None, user_id=None):
    messages = safe_get_messages(user_id)
    """Get file creation date in DD.MM.YYYY format from EXIF data or filename"""
    try:
        from datetime import datetime
        import re
        
        # Получаем текущую дату для проверки
        now = datetime.now()
        today_str = now.strftime("%d.%m.%Y")
        invalid_date_str = "01.01.1970"
        
        def is_valid_date(date_str, source_context=""):
            """Проверяет, что дата валидна (не сегодняшняя и не 01.01.1970)"""
            if not date_str:
                return False
            if date_str == invalid_date_str:
                logger.info(LoggerMsg.IMG_FILE_DATE_UNIX_EPOCH_INVALID_LOG_MSG.format(date_str=date_str))
                return False
            if date_str == today_str:
                # Сегодняшняя дата валидна только если она извлечена из надежных источников
                # (EXIF, метаданные видео, API) и НЕ из времени модификации файла
                if source_context in ["exif", "video_metadata", "api"]:
                    logger.info(LoggerMsg.IMG_FILE_DATE_TODAY_VALID_LOG_MSG.format(date_str=date_str, source_context=source_context))
                    return True
                else:
                    logger.info(LoggerMsg.IMG_FILE_DATE_TODAY_LIKELY_INVALID_LOG_MSG.format(date_str=date_str, source_context=source_context))
                    return False
            return True
        
        # First, try to extract date from filename (Instagram format: timestamp.jpg)
        filename = os.path.basename(file_path)
        logger.info(LoggerMsg.IMG_FILE_DATE_EXTRACT_FROM_FILENAME_LOG_MSG.format(filename=filename))
        
        # Instagram files often have timestamp as filename (e.g., 3732982640044472150.jpg)
        # This is usually a Unix timestamp in microseconds
        if filename and '.' in filename:
            name_without_ext = filename.split('.')[0]
            
            # Try to extract timestamp from filename patterns like "3608469449724736561._fast.mp4"
            # Remove ._fast suffix if present
            clean_name = name_without_ext.replace('._fast', '')
            logger.info(LoggerMsg.IMG_FILE_DATE_CLEANED_NAME_LOG_MSG.format(clean_name=clean_name, isdigit=clean_name.isdigit(), length=len(clean_name)))
            if clean_name.isdigit() and len(clean_name) > 10:
                # Instagram IDs don't contain reliable timestamp information
                # Instagram uses Snowflake-like IDs but they don't encode upload dates
                # Return None to group as 'unknown' date
                logger.info(LoggerMsg.IMG_FILE_DATE_INSTAGRAM_ID_DETECTED_LOG_MSG.format(clean_name=clean_name))
                return None
            
            # Check if it's a numeric timestamp (Instagram format) - original name
            logger.info(LoggerMsg.IMG_FILE_DATE_ORIGINAL_NAME_LOG_MSG.format(name_without_ext=name_without_ext, isdigit=name_without_ext.isdigit(), length=len(name_without_ext)))
            if name_without_ext.isdigit() and len(name_without_ext) > 10:
                # Instagram IDs don't contain reliable timestamp information
                # Instagram uses Snowflake-like IDs but they don't encode upload dates
                # Return None to group as 'unknown' date
                logger.info(LoggerMsg.IMG_FILE_DATE_ORIGINAL_INSTAGRAM_ID_DETECTED_LOG_MSG.format(name_without_ext=name_without_ext))
                return None
            
            # Try to extract date from gallery-dl filename patterns
            # Gallery-dl often uses patterns like: 2024-10-30_15-47-00_filename.jpg
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
                r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
                r'(\d{2}_\d{2}_\d{4})',  # DD_MM_YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, filename)
                if match:
                    try:
                        date_str = match.group(1)
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%Y_%m_%d', '%d-%m-%Y', '%d_%m_%Y']:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                date_str = dt.strftime("%d.%m.%Y")
                                logger.info(LoggerMsg.IMG_FILE_DATE_FOUND_IN_FILENAME_LOG_MSG.format(date_str=date_str))
                                if is_valid_date(date_str, "filename"):
                                    return date_str
                                else:
                                    logger.info(LoggerMsg.IMG_FILE_DATE_INVALID_CONTINUING_SEARCH_LOG_MSG.format(date_str=date_str))
                            except ValueError:
                                continue
                    except Exception:
                        continue
        
        # Try to get date from EXIF data
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(file_path) as img:
                exifdata = img.getexif()
                if exifdata:
                    # Try different EXIF date fields
                    for tag_id, value in exifdata.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if 'date' in str(tag).lower() and value:
                                        try:
                                            # Parse EXIF date format (YYYY:MM:DD HH:MM:SS)
                                            if ':' in str(value):
                                                dt = datetime.strptime(str(value).split()[0], '%Y:%m:%d')
                                                date_str = dt.strftime("%d.%m.%Y")
                                                if is_valid_date(date_str, "exif"):
                                                    return date_str
                                        except ValueError:
                                            continue
        except ImportError:
            # PIL not available, skip EXIF
            pass
        except Exception:
            # EXIF reading failed, continue to next method
            pass
        
        # Try to get date from file metadata using ffprobe (for videos)
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                    '-show_entries', 'format_tags=creation_time',
                    '-of', 'json', file_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout or '{}')
                    creation_time = data.get('format', {}).get('tags', {}).get('creation_time')
                    if creation_time:
                        # Parse ISO format (2024-10-30T15:47:00.000000Z)
                                try:
                                    dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
                                    date_str = dt.strftime("%d.%m.%Y")
                                    if is_valid_date(date_str, "video_metadata"):
                                        return date_str
                                except ValueError:
                                    pass
            except Exception:
                pass
        
        # If all else fails, try to use file modification time as fallback
        # But only if it's not a recently downloaded file (to avoid today's date for fake messages)
        try:
            stat = os.stat(file_path)
            mtime = stat.st_mtime
            dt = datetime.fromtimestamp(mtime)
            
            # Check if file was created today (likely a fake message fallback)
            # Only reject today's date if we couldn't extract date from metadata
            now = datetime.now()
            if dt.date() == now.date():
                logger.info(LoggerMsg.IMG_FILE_DATE_CREATED_TODAY_LOG_MSG)
                return None
            
            date_str = dt.strftime("%d.%m.%Y")
            logger.info(LoggerMsg.IMG_FILE_DATE_USING_MODIFICATION_TIME_LOG_MSG.format(date_str=date_str))
            if is_valid_date(date_str, "file_modification"):
                return date_str
            else:
                logger.info(LoggerMsg.IMG_FILE_DATE_MODIFICATION_INVALID_LOG_MSG.format(date_str=date_str))
        except Exception:
            pass
        
        # Try to get date from service API (Instagram, etc.)
        if original_url:
            try:
                from URL_PARSERS.service_api_info import get_service_date
                logger.info(f"[FILE_DATE] Trying to get date from service API for URL: {original_url}")
                api_date = get_service_date(original_url, user_id)
                if api_date:
                    logger.info(f"[FILE_DATE] Got date from service API: {api_date}")
                    if is_valid_date(api_date, "api"):
                        return api_date
                    else:
                        logger.info(f"[FILE_DATE] API date {api_date} is invalid")
                else:
                    logger.info(f"[FILE_DATE] No date found in service API")
            except Exception as e:
                logger.info(f"[FILE_DATE] Error in service API date extraction: {e}")
        else:
            logger.info(f"[FILE_DATE] No original URL provided for API date extraction")
        
        # If all else fails, return None (will be grouped as 'unknown')
        logger.info(f"[FILE_DATE] Could not extract date from file: {file_path}")
        return None
        
    except Exception:
        return None

def create_unique_download_path(user_id, url):
    messages = safe_get_messages(user_id)
    """Create unique download path based on user ID and URL structure"""
    try:
        import time
        import random
        from urllib.parse import urlparse
        
        # Parse URL to extract domain and path
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Clean domain name (remove www, etc.)
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract path components
        path_parts = [part for part in parsed.path.split('/') if part and part != '']
        
        # Create safe directory name
        if path_parts:
            # Use first path component as username/profile
            profile_name = path_parts[0]
            # Remove special characters that might cause issues
            import re
            profile_name = re.sub(r'[^\w\-_.]', '_', profile_name)
        else:
            profile_name = 'unknown'
        
        # Create unique timestamp-based directory with microsecond precision and random component
        timestamp = int(time.time() * 1000000)  # Microsecond precision
        random_suffix = random.randint(1000, 9999)  # Random 4-digit number
        
        # Structure: users/{user_id}/{domain}/{profile_name}_{timestamp}_{random}/
        unique_dir = os.path.join("users", str(user_id), domain, f"{profile_name}_{timestamp}_{random_suffix}")
        
        return unique_dir
    except Exception as e:
        logger.error(f"Failed to create unique download path: {e}")
        # Fallback to simple timestamp-based directory
        return os.path.join("users", str(user_id), f"download_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}")

def create_album_caption_with_dates(media_group, url, tags_text_norm, profile_name, site_name, user_id=None):
    messages = safe_get_messages(user_id)
    """Create album caption with emoji numbers and dates grouped by date"""
    try:
        # Group media by date
        date_groups = {}
        for i, media in enumerate(media_group, 1):
            file_path = media.media
            date = get_file_date(file_path, url, user_id)
            if date:
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(i)
            else:
                # If no date, add to a special group
                if 'unknown' not in date_groups:
                    date_groups['unknown'] = []
                date_groups['unknown'].append(i)
        
        # Create caption lines
        caption_lines = []
        
        # Add emoji numbers with dates
        # Sort dates chronologically (unknown dates go last)
        sorted_dates = []
        unknown_dates = []
        for date in date_groups.keys():
            if date == 'unknown':
                unknown_dates.append(date)
            else:
                sorted_dates.append(date)
        
        # Sort dates chronologically
        def parse_date(date_str):
            messages = safe_get_messages(user_id)
            try:
                from datetime import datetime
                return datetime.strptime(date_str, "%d.%m.%Y")
            except:
                return datetime.min
        
        sorted_dates.sort(key=parse_date)
        
        # Add unknown dates at the end
        all_dates = sorted_dates + unknown_dates
        
        for date in all_dates:
            if date == 'unknown':
                # For files without date, just add emojis
                emojis = [get_emoji_number(i) for i in date_groups[date]]
                caption_lines.append(" ".join(emojis))
            else:
                emojis = [get_emoji_number(i) for i in date_groups[date]]
                caption_lines.append(" ".join(emojis) + f" {date}")
        
        # Add profile and site hashtags
        hashtags = []
        if profile_name:
            hashtags.append(f"#{profile_name}")
        if site_name:
            hashtags.append(f"#{site_name}")
        if hashtags:
            caption_lines.append(" ".join(hashtags))
        
        # Add user tags if any
        if tags_text_norm:
            caption_lines.append(tags_text_norm)
        
        # Add URL with paperclip emoji
        caption_lines.append(f"{safe_get_messages(user_id).IMAGE_URL_CAPTION_MSG.format(url=url)} @{Config.BOT_NAME}")
        
        return "\n".join(caption_lines)
    except Exception as e:
        logger.error(f"Failed to create album caption with dates: {e}")
        # Fallback to simple caption
        return f"{safe_get_messages(user_id).IMAGE_URL_CAPTION_MSG.format(url=url)} @{Config.BOT_NAME}"

def is_image_url(url):
    """Check if URL is likely an image URL"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg']
    url_lower = url.lower()
    
    # Check for image extensions
    for ext in image_extensions:
        if ext in url_lower:
            return True
    
    # Check for common image hosting domains
    image_domains = [
        'imgur.com', 'i.imgur.com', 'flickr.com', 'deviantart.com',
        'pinterest.com', 'instagram.com', 'twitter.com', 'x.com',
        'reddit.com', 'imgbb.com', 'postimg.cc', 'ibb.co',
        'drive.google.com', 'dropbox.com', 'mega.nz'
    ]
    
    for domain in image_domains:
        if domain in url_lower:
            return True
    
    return False

def convert_file_to_telegram_format(file_path):
    """
    Convert unsupported file formats to Telegram-supported formats
    Returns the converted file path or original path if no conversion needed
    """
    if not os.path.exists(file_path):
        return file_path
    
    file_ext = os.path.splitext(file_path)[1].lower()
    file_dir = os.path.dirname(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    try:
        # Convert WebP images to JPEG
        if file_ext == '.webp':
            output_path = os.path.join(file_dir, f"{file_name}.jpg")
            cmd = [
                'ffmpeg', '-i', file_path, 
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure dimensions are divisible by 2
                '-c:v', 'mjpeg', '-q:v', '2',  # Use MJPEG codec for JPEG output
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(LoggerMsg.IMG_CONVERTED_WEBP_JPEG_LOG_MSG.format(file_path=file_path, output_path=output_path))
                return output_path
            else:
                logger.warning(LoggerMsg.IMG_FAILED_CONVERT_WEBP_LOG_MSG.format(result_stderr=result.stderr))
                return file_path
        
        # Convert WebM videos to MP4 (add thumbnail to avoid black preview)
        elif file_ext == '.webm':
            output_path = os.path.join(file_dir, f"{file_name}.mp4")
            # We will generate/send thumbnail later during sending
            cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(LoggerMsg.IMG_CONVERTED_WEBM_MP4_LOG_MSG.format(file_path=file_path, output_path=output_path))
                return output_path
            else:
                logger.warning(LoggerMsg.IMG_FAILED_CONVERT_WEBM_LOG_MSG.format(result_stderr=result.stderr))
                return file_path
        
        # Faststart remux for MP4 to improve metadata parsing
        elif file_ext == '.mp4':
            output_path = os.path.join(file_dir, f"{file_name}._fast.mp4")
            cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'copy', '-c:a', 'copy',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(LoggerMsg.IMG_REMUXED_MP4_FASTSTART_LOG_MSG.format(file_path=file_path, output_path=output_path))
                return output_path
            else:
                logger.warning(LoggerMsg.IMG_FAILED_REMUX_MP4_LOG_MSG.format(result_stderr=result.stderr))
                return file_path

        # Convert/Remux other video formats to MP4
        elif file_ext in ['.avi', '.mov', '.mkv', '.flv', '.m4v']:
            output_path = os.path.join(file_dir, f"{file_name}.mp4")
            # Prefer stream copy for .m4v (usually MP4 container variant), else re-encode
            if file_ext == '.m4v':
                cmd = [
                    'ffmpeg', '-i', file_path,
                    '-c:v', 'copy', '-c:a', 'copy',
                    '-movflags', '+faststart',
                    '-y', output_path
                ]
            else:
                # We will generate/send thumbnail later during sending
                cmd = [
                    'ffmpeg', '-i', file_path,
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-movflags', '+faststart',
                    '-y', output_path
                ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(LoggerMsg.IMG_CONVERTED_TO_MP4_LOG_MSG.format(file_ext=file_ext, file_path=file_path, output_path=output_path))
                return output_path
            else:
                logger.warning(LoggerMsg.IMG_FAILED_CONVERT_TO_MP4_LOG_MSG.format(file_ext=file_ext, result_stderr=result.stderr))
                return file_path
        
        # Convert other unsupported image formats to JPEG
        elif file_ext in ['.bmp', '.tiff']:
            output_path = os.path.join(file_dir, f"{file_name}.jpg")
            cmd = [
                'ffmpeg', '-i', file_path,
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure dimensions are divisible by 2
                '-c:v', 'mjpeg', '-q:v', '2',  # Use MJPEG codec for JPEG output
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(LoggerMsg.IMG_CONVERTED_TO_JPEG_LOG_MSG.format(file_ext=file_ext, file_path=file_path, output_path=output_path))
                return output_path
            else:
                logger.warning(LoggerMsg.IMG_FAILED_CONVERT_TO_JPEG_LOG_MSG.format(file_ext=file_ext, result_stderr=result.stderr))
                return file_path
        
        # No conversion needed
        else:
            return file_path
            
    except subprocess.TimeoutExpired:
        logger.error(LoggerMsg.IMG_CONVERSION_TIMEOUT_LOG_MSG.format(file_path=file_path))
        return file_path
    except Exception as e:
        logger.error(LoggerMsg.IMG_CONVERSION_ERROR_LOG_MSG.format(file_path=file_path, e=e))
        return file_path

def get_message_thread_id(message):
    """Extract message_thread_id from message, handling fake messages with original message reference"""
    if hasattr(message, '_is_fake_message') and hasattr(message, '_original_message') and message._original_message is not None:
        return getattr(message._original_message, 'message_thread_id', None)
    else:
        return getattr(message, 'message_thread_id', None)

def get_reply_message_id(message):
    """Get the correct message ID for replies, handling fake messages with original message reference"""
    if hasattr(message, '_is_fake_message') and hasattr(message, '_original_message') and message._original_message is not None:
        return message._original_message.id
    else:
        return message.id

@background_handler(label="image_command")
def image_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Handle /img command for downloading images"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Initialize image_info to avoid undefined variable errors
    image_info = None
    
    # Log the command execution
    logger.info(f"image_command called for user {user_id} in chat {chat_id} with text: {text}")
    # Get message_thread_id (handles fake messages)
    message_thread_id = get_message_thread_id(message)
    logger.info(f"[IMG DEBUG] message.chat.id={message.chat.id}, message_thread_id={message_thread_id}")
    
    # For fake messages, chat_id is already set correctly in fake_message
    
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        logger.info(f"User {user_id} not authorized, returning")
        return
    
    # Extract URL from command
    if len(text.split()) < 2:
        # Show help if no URL provided
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).COMMAND_IMAGE_HELP_CLOSE_BUTTON_MSG, callback_data="img_help|close")]
        ])
        safe_send_message(
            chat_id,
            safe_get_messages(user_id).IMG_HELP_MSG + " /audio, /vid, /help, /playlist, /settings",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
            message=message
        )
        send_to_logger(message, LoggerMsg.IMG_HELP_SHOWN)
        return
    
    # Extract optional range and URL from command
    # Allow: /img URL  OR  /img 11-20 URL  OR  /img 11- URL
    manual_range = None  # tuple (start:int, end:int|None)
    rest = text.split(' ', 1)[1].strip()
    parts = rest.split()
    if len(parts) >= 2:
        rng_candidate = parts[0]
        if re.fullmatch(r"-?\d+-\d*", rng_candidate):
            start_str, end_str = rng_candidate.split('-', 1)
            # Если первое число отрицательное, добавляем минус ко второму числу: /img -1-7 URL -> (-1, -7)
            if start_str.startswith("-") and end_str != "":
                end_str = f"-{end_str}"
            try:
                start_val = int(start_str)
                end_val = int(end_str) if end_str != '' else None
                # Убираем проверку >= 1, так как отрицательные числа тоже валидны
                manual_range = (start_val, end_val)
                url = ' '.join(parts[1:]).strip()
            except Exception:
                url = rest
        else:
            url = rest
    else:
        url = rest
    
    # Use common tag/url extractor to get clean URL and tags from the whole message
    try:
        parsed_url, _s, _e, _plist, user_tags, user_tags_text, _err = extract_url_range_tags(text)
        logger.info(LoggerMsg.IMG_DEBUG_EXTRACT_URL_RANGE_LOG_MSG.format(parsed_url=parsed_url, _s=_s, _e=_e, text=text))
        if parsed_url:
            url = parsed_url
            # Check if range was specified in URL*start*end format
            if _s != 1 or _e != 1:
                manual_range = (_s, _e)
                logger.info(LoggerMsg.IMG_DEBUG_RANGE_DETECTED_LOG_MSG.format(_s=_s, _e=_e))
            else:
                logger.info(LoggerMsg.IMG_DEBUG_NO_RANGE_LOG_MSG)
    except Exception:
        user_tags = []
        user_tags_text = ''
    # Normalize tags: remove duplicates while preserving order
    def _dedupe_tags_text(tags_text: str) -> str:
        try:
            seen = set()
            result = []
            for tok in (tags_text or '').split():
                if not tok:
                    continue
                if tok.startswith('#'):
                    low = tok.lower()
                    if low not in seen:
                        seen.add(low)
                        result.append(tok)
            return ' '.join(result)
        except Exception:
            return tags_text or ''
    tags_text_norm = _dedupe_tags_text(user_tags_text)
    # Persist user tags
    try:
        if user_tags:
            save_user_tags(user_id, user_tags)
    except Exception:
        pass
    
    user_forced_nsfw = any(t.lower() in {'#nsfw', '#porn'} for t in (user_tags or []))
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        safe_send_message(
            chat_id,
            safe_get_messages(user_id).INVALID_URL_MSG,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
            message=message
        )
        log_error_to_channel(message, LoggerMsg.INVALID_URL_PROVIDED.format(url=url), url)
        return
    
    # Check if user is admin
    is_admin = int(user_id) in Config.ADMIN
    
    # Check range limits if manual range is specified (BEFORE cache check)
    if manual_range:
        # Handle case where end range is None (e.g., "1-" means from 1 to end)
        if manual_range[1] is None:
            # For open-ended ranges, we can't check limits here - skip validation
            range_count = None
        else:
            range_count = manual_range[1] - manual_range[0] + 1
        
        # Only check limits if we have a specific range count
        if range_count is not None:
            # Use TikTok limit if URL is TikTok, otherwise use general image limit
            if 'tiktok.com' in url.lower():
                max_img_files = LimitsConfig.MAX_TIKTOK_COUNT
            else:
                max_img_files = LimitsConfig.MAX_IMG_FILES
            # Apply group multiplier for groups/channels
            try:
                if message and getattr(message.chat, 'type', None) != enums.ChatType.PRIVATE:
                    mult = getattr(LimitsConfig, 'GROUP_MULTIPLIER', 1)
                    max_img_files = int(max_img_files * mult)
            except Exception:
                pass
            
            if range_count and range_count > max_img_files:
                # Create alternative commands preserving the original start range
                start_range = manual_range[0]
                end_range = start_range + max_img_files - 1
                suggested_command_url_format = f"{url}*{start_range}*{end_range}"
                
                safe_send_message(
                    chat_id,
                    safe_get_messages(user_id).IMG_RANGE_LIMIT_EXCEEDED_MSG.format(
                        range_count=range_count,
                        max_img_files=max_img_files,
                        start_range=start_range,
                        end_range=end_range,
                        url=url,
                        suggested_command_url_format=suggested_command_url_format
                    ),
                    parse_mode=enums.ParseMode.HTML,
                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                    message=message
                )
                return
    
    # Check if user has proxy enabled
    use_proxy = is_proxy_enabled(user_id)
    
    # Send initial message
    logger.info(f"[IMG STATUS] About to send status message to chat_id={chat_id}, message_thread_id={message_thread_id}")
    status_msg = safe_send_message(
        chat_id,
        safe_get_messages(user_id).CHECKING_CACHE_MSG.format(url=url),
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
        message=message
    )
    logger.info(f"[IMG STATUS] Status message sent, ID={status_msg.id if status_msg else 'None'}")
    # Pin the status message for visibility
    try:
        app.pin_chat_message(user_id, status_msg.id, disable_notification=True)
    except Exception:
        pass

    # Determine NSFW flag based on URL for cache operations
    try:
        nsfw_flag = bool(is_porn(url, "", "", None))
    except Exception:
        nsfw_flag = False
    # Force NSFW if user explicitly tagged it
    if user_forced_nsfw:
        nsfw_flag = True
    
    # Early cache serve before any analysis/downloading (only for non-NSFW content)
    cached_map = {}
    if not nsfw_flag:
        try:
            requested_indices = None
            if manual_range is not None:
                start_i, end_i = manual_range
                if end_i is not None:
                    # Обработка отрицательных индексов и обратного порядка
                    if start_i < 0 or end_i < 0:
                        # Для отрицательных индексов нужно получить общее количество постов
                        # Пока используем прямую логику, преобразование будет в функции скачивания
                        if start_i < end_i:
                            requested_indices = list(range(int(start_i), int(end_i) + 1))
                        else:
                            # Обратный порядок: от start_i до end_i включительно в обратном порядке
                            requested_indices = list(range(int(start_i), int(end_i) - 1, -1))
                    elif start_i > end_i:
                        # Обратный порядок для положительных индексов
                        requested_indices = list(range(int(start_i), int(end_i) - 1, -1))
                    else:
                        # Прямой порядок
                        requested_indices = list(range(int(start_i), int(end_i) + 1))
                else:
                    cached_all = sorted(list(get_cached_image_post_indices(url)))
                    if start_i < 0:
                        # Для отрицательных индексов берем последние |start_i| постов
                        requested_indices = cached_all[start_i:] if abs(start_i) <= len(cached_all) else []
                    else:
                        requested_indices = [i for i in cached_all if i >= int(start_i)]
            else:
                # No manual range specified, get all cached indices
                requested_indices = None
            cached_map = get_cached_image_posts(url, requested_indices)
        except Exception as e:
            logger.error(LoggerMsg.IMG_ERROR_GET_CACHED_POSTS_LOG_MSG.format(e=e))
            cached_map = {}
    
    # Process cached content and determine if we need to download more
    cached_sent = 0
    need_download = True
    
    try:
        if cached_map:
            for album_idx in sorted(cached_map.keys()):
                ids = cached_map[album_idx]
                try:
                    kwargs = {}
                    thread_id = message_thread_id
                    if thread_id:
                        kwargs['message_thread_id'] = thread_id
                    # For cached content, always use regular channel (no NSFW/PAID in cache)
                    from_chat_id = get_log_channel("image")
                    channel_type = "regular"
                    
                    logger.info(LoggerMsg.IMG_CACHE_REPOSTING_ALBUM_LOG_MSG.format(album_idx=album_idx, from_chat_id=from_chat_id, user_id=user_id, ids=ids))
                    sm.safe_forward_messages(chat_id, from_chat_id, ids, **kwargs)
                    cached_sent += len(ids)
                except Exception:
                    logger.info(LoggerMsg.IMG_CACHE_FALLBACK_REPOSTING_LOG_MSG.format(album_idx=album_idx, from_chat_id=from_chat_id, user_id=user_id, ids=ids))
                    app.forward_messages(chat_id, from_chat_id, ids, **kwargs)
                    cached_sent += len(ids)
                except Exception as _e:
                    logger.warning(LoggerMsg.IMG_CACHE_FAILED_FORWARD_ALBUM_LOG_MSG.format(album_idx=album_idx, _e=_e))
            
            # Check if we have all requested content in cache
            if manual_range is not None:
                start_i, end_i = manual_range
                if end_i is not None:
                    # Правильный расчет количества для отрицательных индексов и обратного порядка
                    if start_i < 0 and end_i < 0:
                        requested_count = abs(end_i) - abs(start_i) + 1
                    elif start_i > end_i:
                        requested_count = abs(start_i - end_i) + 1
                    else:
                        requested_count = end_i - start_i + 1
                    # Check if we have all requested indices in cache
                    cached_indices = set(cached_map.keys())
                    # Формируем правильный список запрошенных индексов
                    if start_i < 0 or end_i < 0:
                        # Для отрицательных индексов пока используем прямую логику
                        # Преобразование будет в функции скачивания
                        if start_i < end_i:
                            requested_indices = set(range(int(start_i), int(end_i) + 1))
                        else:
                            requested_indices = set(range(int(start_i), int(end_i) - 1, -1))
                    elif start_i > end_i:
                        requested_indices = set(range(int(start_i), int(end_i) - 1, -1))
                    else:
                        requested_indices = set(range(int(start_i), int(end_i) + 1))
                    missing_indices = requested_indices - cached_indices
                    
                    if not missing_indices:
                        # We have all requested content in cache
                        need_download = False
                        try:
                            safe_edit_message_text(
                                user_id, status_msg.id,
                                safe_get_messages(user_id).SENT_FROM_CACHE_MSG.format(count=cached_sent),
                                parse_mode=enums.ParseMode.HTML,
                            )
                        except Exception:
                            pass
                        send_to_logger(message, LoggerMsg.REPOSTED_CACHED_ALBUMS.format(count=cached_sent, url=url))
                        return
                    else:
                        # We have partial content, need to download the rest
                        cached_count = len(cached_indices)
                        missing_count = len(missing_indices)
                        logger.info(f"Cache has {cached_count} indices {sorted(cached_indices)}, missing {missing_count} indices {sorted(missing_indices)}, downloading remaining {missing_count} items")
                        # Update manual_range to start from the first missing index
                        first_missing = min(missing_indices)
                        last_missing = max(missing_indices)
                        manual_range = (first_missing, last_missing)
                        logger.info(f"Continuing download from index {first_missing} to {last_missing} (cached: {cached_count}/{requested_count}, missing: {sorted(missing_indices)})")
                        try:
                            safe_edit_message_text(
                                user_id, status_msg.id,
                                safe_get_messages(user_id).CACHE_CONTINUING_DOWNLOAD_MSG.format(cached=cached_sent),
                                parse_mode=enums.ParseMode.HTML,
                            )
                        except Exception:
                            pass
                else:
                    # Open-ended range, continue downloading
                    try:
                        safe_edit_message_text(
                            user_id, status_msg.id,
                            safe_get_messages(user_id).CACHE_CONTINUING_DOWNLOAD_MSG.format(cached=cached_sent),
                            parse_mode=enums.ParseMode.HTML,
                        )
                    except Exception:
                        pass
            else:
                # No manual range, we have some cached content, continue downloading
                # Set manual range to continue from the last cached index
                if cached_map:
                    cached_indices = sorted(cached_map.keys())
                    max_cached_index = max(cached_indices)
                    cached_count = len(cached_indices)
                    
                    # Count total cached images (not just album indices)
                    total_cached_images = sum(len(ids) for ids in cached_map.values())
                    
                    logger.info(f"Cache contains {cached_count} album indices: {cached_indices} with {total_cached_images} total images")
                    
                    # Try to determine the total count to set proper end index
                    total_count = None
                    if image_info and isinstance(image_info, dict):
                        for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                            if key in image_info and image_info[key]:
                                total_count = int(image_info[key])
                                break
                    
                    if total_count and total_count > total_cached_images:
                        # We know the total count, set proper end index based on image count
                        start_from = total_cached_images + 1
                        manual_range = (start_from, total_count)
                        logger.info(f"No manual range specified, continuing from image {start_from} to {total_count} (cached: {total_cached_images}/{total_count} images)")
                    else:
                        # Fallback: try to get total count from detected_total_value
                        detected_total_value = locals().get('detected_total', None)
                        if detected_total_value and detected_total_value > total_cached_images:
                            start_from = total_cached_images + 1
                            manual_range = (start_from, detected_total_value)
                            logger.info(f"No manual range specified, using detected total {detected_total_value}, continuing from image {start_from} to {detected_total_value} (cached: {total_cached_images}/{detected_total_value} images)")
                        else:
                            # Last resort: continue from next image to end
                            start_from = total_cached_images + 1
                            manual_range = (start_from, None)
                            logger.info(f"No manual range specified, continuing from image {start_from} to end (cached: {total_cached_images} images)")
                try:
                    safe_edit_message_text(
                        user_id, status_msg.id,
                        safe_get_messages(user_id).CACHE_CONTINUING_DOWNLOAD_MSG.format(cached=cached_sent),
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass
    except Exception as _e:
        logger.warning(LoggerMsg.IMG_CACHE_FORWARD_EARLY_FAILED_LOG_MSG.format(_e=_e))
    
    # If we don't need to download more, return
    if not need_download:
        return
    
    try:
        # Get image information first
        image_info = get_image_info(url, user_id, use_proxy)
        # NSFW detection using domain and metadata
        try:
            info_title = (image_info or {}).get('title') if isinstance(image_info, dict) else None
            info_desc = (image_info or {}).get('description') if isinstance(image_info, dict) else None
            info_caption = (image_info or {}).get('caption') if isinstance(image_info, dict) else None
        except Exception:
            info_title = info_desc = info_caption = None
        try:
            nsfw_detected = bool(is_porn(url, "", "", None))
        except Exception:
            nsfw_detected = False
        # Respect explicit user tags overriding detection
        nsfw_flag = user_forced_nsfw or nsfw_detected
        
        # Get detected_total value safely
        detected_total_value = locals().get('detected_total', None)
        
        if not image_info:
            # If we have detected_total but no image_info, create a minimal info object
            if detected_total_value and detected_total_value > 0:
                logger.info(f"Creating minimal image_info for {detected_total_value} media items")
                image_info = {
                    'title': f'Media Collection ({detected_total_value} items)',
                    'description': f'Found {detected_total_value} media items',
                    'url': url
                }
            else:
                # Fallback: if no image_info and no detected_total, use max allowed range
                # BUT ONLY if manual_range is not already set by user
                if manual_range is None:
                    # Calculate total_limit for fallback
                    fallback_limit = LimitsConfig.MAX_IMG_FILES
                    try:
                        if message and getattr(message.chat, 'type', None) != enums.ChatType.PRIVATE:
                            mult = getattr(LimitsConfig, 'GROUP_MULTIPLIER', 1)
                            fallback_limit = int(fallback_limit * mult)
                    except Exception:
                        pass
                    
                    logger.info(f"[IMG FALLBACK] No image_info and no detected_total, using fallback with max range: {fallback_limit}")
                    
                    # Update status message to show we're proceeding with fallback
                    safe_edit_message_text(
                        user_id, status_msg.id,
                        safe_get_messages(user_id).FALLBACK_ANALYZE_MEDIA_MSG.format(fallback_limit=fallback_limit),
                        parse_mode=enums.ParseMode.HTML
                    )
                    
                    # Set manual range to max allowed range for fallback only if not already set
                    if manual_range is None:
                        manual_range = (1, fallback_limit)
                        logger.info(f"[IMG FALLBACK] Using manual range for fallback: {manual_range}")
                    else:
                        logger.info(f"[IMG FALLBACK] Manual range already set from cache: {manual_range}")
                    
                    # Create minimal image_info for fallback
                    image_info = {
                        'title': f'Media Collection (up to {fallback_limit} items)',
                        'description': f'Fallback mode - downloading up to {fallback_limit} items',
                        'url': url
                    }
                else:
                    # User already specified a range, don't override it
                    logger.info(f"[IMG FALLBACK] User specified range {manual_range}, not overriding with fallback")
                    # Create minimal image_info for user-specified range
                    image_info = {
                        'title': f'Media Collection (range {manual_range[0]}-{manual_range[1] if manual_range[1] else "end"})',
                        'description': f'User-specified range: {manual_range[0]}-{manual_range[1] if manual_range[1] else "end"}',
                        'url': url
                    }
        
        # Update status message
        title = image_info.get('title', 'Unknown')
        safe_edit_message_text(
            user_id, status_msg.id,
            safe_get_messages(user_id).DOWNLOADING_IMAGE_MSG +
            f"<b>{safe_get_messages(user_id).TITLE_LABEL_MSG}</b> {title}\n"
            f"<b>URL:</b> <code>{url}</code>\n"
            f"<b>{safe_get_messages(user_id).MEDIA_COUNT_LABEL_MSG}</b> {detected_total_value if detected_total_value else 'Unknown'}",
            parse_mode=enums.ParseMode.HTML
        )
        
        # Create user directory
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        # All users have MAX_IMG_FILES limit (including admins for testing)
        total_limit = LimitsConfig.MAX_IMG_FILES
        
        # Apply group multiplier for groups/channels
        try:
            if message and getattr(message.chat, 'type', None) != enums.ChatType.PRIVATE:
                mult = getattr(LimitsConfig, 'GROUP_MULTIPLIER', 1)
                total_limit = int(total_limit * mult)
        except Exception:
            pass
        
        # Check if domain should skip simulation and go to fallback (before any other logic)
        should_skip_simulation = any(domain in url.lower() for domain in DomainsConfig.GALLERYDL_FALLBACK_DOMAINS)
        
        # If manual range specified, skip simulation and counting - work directly with range
        if manual_range is not None:
            logger.info(f"[IMG MANUAL RANGE] User specified range {manual_range}, skipping simulation and counting")
            # Skip all simulation and counting logic, go directly to download
        else:
            # If no manual range specified, show range selection menu
            logger.info(f"[IMG RANGE DEBUG] manual_range={manual_range}, will show range menu: {manual_range is None}")
            # Get total count from image_info
            total_count = None
            for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                if isinstance(image_info.get(key), int) and image_info.get(key) > 0:
                    total_count = image_info.get(key)
                    break
            
            if total_count is None or total_count <= 0:
                # Try to get count via gallery-dl (already imported at top of file)
                try:
                    count_info = get_image_info(url, user_id, use_proxy)
                    if count_info:
                        for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                            if isinstance(count_info.get(key), int) and count_info.get(key) > 0:
                                total_count = count_info.get(key)
                                break
                except Exception:
                    pass
            
            if total_count is None or total_count <= 0:
                # Fallback: try to get count via gallery-dl CLI
                try:
                    import subprocess
                    import tempfile
                    import json
                    
                    # Create temp config
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        config = {
                            "extractor": {"timeout": 30, "retries": 3},
                            "output": {"mode": "info"}
                        }
                        json.dump(config, f)
                        config_path = f.name
                    
                    try:
                        # Get count via --get-urls
                        result = subprocess.run([
                            '/mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW/venv/bin/python', '-m', 'gallery_dl',
                            '--config', config_path, '--get-urls', url
                        ], capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            total_count = len([line for line in lines if line.strip() and not line.startswith('#')])
                    finally:
                        os.unlink(config_path)
                except Exception:
                    pass
            
            if total_count is None or total_count <= 0:
                # Still no count, use fallback - start downloading with max allowed range
                logger.info(f"[IMG RANGE DEBUG] Could not determine media count, using fallback with max range: {total_limit}")
                
                # Update status message to show we're proceeding with fallback
                safe_edit_message_text(
                    user_id, status_msg.id,
                    safe_get_messages(user_id).FALLBACK_DETERMINE_COUNT_MSG.format(total_limit=total_limit),
                    parse_mode=enums.ParseMode.HTML
                )
                
                # Set manual range to max allowed range for fallback only if not already set
                if manual_range is None:
                    manual_range = (1, total_limit)
                    logger.info(f"[IMG FALLBACK] Using manual range for fallback: {manual_range}")
                else:
                    logger.info(f"[IMG FALLBACK] Manual range already set from cache: {manual_range}")
            
            # Create range selection menu only if we have a valid count
            if total_count and total_count > 0:
                logger.info(f"[IMG RANGE DEBUG] Creating range buttons: total_count={total_count}, total_limit={total_limit}")
                
                # Calculate ranges based on total_count and limits
            ranges = []
            current_start = 1
            batch_size = total_limit
            
            while current_start <= total_count:
                current_end = min(current_start + batch_size - 1, total_count)
                ranges.append((current_start, current_end))
                current_start = current_end + 1
            
            logger.info(f"[IMG RANGE DEBUG] Created {len(ranges)} range buttons: {ranges}")
            
            # Create keyboard
            keyboard = []
            for start, end in ranges:
                if end == total_count and start == 1:
                    # Single range covering all
                    button_text = f"📥 Download all ({total_count})"
                else:
                    button_text = f"📥 {start}-{end} ({end - start + 1})"
                
                callback_data = f"img_range|{start}|{end}|{url}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
                # Add cancel button
                keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="img_range|cancel")])
                
                safe_edit_message_text(
                    user_id, status_msg.id,
                    f"{safe_get_messages(user_id).IMG_FOUND_MEDIA_ITEMS_MSG.format(count=total_count)}\n\n"
                    f"{safe_get_messages(user_id).IMG_SELECT_DOWNLOAD_RANGE_MSG}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=enums.ParseMode.HTML
                )
                return
            else:
                # Fallback case - we already set manual_range above
                logger.info(f"[IMG FALLBACK] Skipping range menu creation, using manual_range: {manual_range}")
            
        limit_text = 'unlimited' if is_admin else total_limit
        logger.info(LoggerMsg.IMG_USER_ADMIN_LIMIT_LOG_MSG.format(user_id=user_id, is_admin=is_admin, limit_text=limit_text))
        
        # Check if domain should skip simulation and go to fallback (BEFORE any other logic)
        if should_skip_simulation and manual_range is None:
            logger.info(f"[IMG FALLBACK DOMAIN] Domain in GALLERYDL_FALLBACK_DOMAINS, skipping simulation, using fallback")
            # Use fallback immediately for these domains
            fallback_limit = LimitsConfig.MAX_IMG_FILES
            try:
                if message and getattr(message.chat, 'type', None) != enums.ChatType.PRIVATE:
                    mult = getattr(LimitsConfig, 'GROUP_MULTIPLIER', 1)
                    fallback_limit = int(fallback_limit * mult)
            except Exception:
                pass
            
            # Set manual range to max allowed range for fallback only if not already set
            if manual_range is None:
                manual_range = (1, fallback_limit)
                logger.info(f"[IMG FALLBACK DOMAIN] Using manual range for fallback: {manual_range}")
            else:
                logger.info(f"[IMG FALLBACK DOMAIN] Manual range already set from cache: {manual_range}")
            
            # Create minimal image_info for fallback
            image_info = {
                'title': f'Media Collection (up to {fallback_limit} items)',
                'description': f'Fallback mode - downloading up to {fallback_limit} items',
                'url': url
            }
            
            # Skip total detection for fallback domains
            detected_total = None
        else:
            # Determine expected total via --get-urls analog
            detected_total = None
            if manual_range is None:
                detected_total = get_total_media_count(url, user_id, use_proxy)
            else:
                # If manual range is specified, skip total detection and proceed with download
                logger.info(f"[IMG MANUAL RANGE] Skipping total detection, using manual range: {manual_range}")
                detected_total = None  # Will be handled by fallback logic later
        
        # Check limits after detecting total media count
        if detected_total and detected_total > 0:
            # Use TikTok limit if URL is TikTok, otherwise use general image limit
            if 'tiktok.com' in url.lower():
                max_img_files = LimitsConfig.MAX_TIKTOK_COUNT
            else:
                max_img_files = LimitsConfig.MAX_IMG_FILES
            # Apply group multiplier for groups/channels
            try:
                if message and getattr(message.chat, 'type', None) != enums.ChatType.PRIVATE:
                    mult = getattr(LimitsConfig, 'GROUP_MULTIPLIER', 1)
                    max_img_files = int(max_img_files * mult)
            except Exception:
                pass
            
            # If total exceeds limit, show error and suggest manual range
            if detected_total and detected_total > max_img_files:
                # Create alternative commands preserving the original start range if manual_range exists
                if manual_range and manual_range[0] is not None:
                    start_range = manual_range[0]
                    end_range = start_range + max_img_files - 1
                else:
                    start_range = 1
                    end_range = max_img_files
                
                suggested_command_url_format = f"{url}*{start_range}*{end_range}"
                
                safe_send_message(
                    chat_id,
                    safe_get_messages(user_id).COMMAND_IMAGE_MEDIA_LIMIT_EXCEEDED_MSG.format(count=detected_total, max_count=max_img_files, start_range=start_range, end_range=end_range, url=url, suggested_command_url_format=f"/img {start_range}-{end_range} {url}") +
                    f"<code>{suggested_command_url_format}</code>",
                    parse_mode=enums.ParseMode.HTML,
                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                    message=message
                )
                return
            
            total_expected = min(detected_total, max_img_files)
        elif detected_total and detected_total > 0:
            total_expected = detected_total
        # Pre-cleanup: remove media files from user directory before starting
        # IMPORTANT: Preserve user's cookies file if present (Instagram/TikTok auth)
        try:
            logger.info(LoggerMsg.IMG_PRE_CLEANUP_START_LOG_MSG.format(user_id=user_id))
            # Preserve cookies before cleanup
            preserved_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
            preserved_cookie_data = None
            try:
                if os.path.exists(preserved_cookie_path):
                    with open(preserved_cookie_path, "rb") as _cf:
                        preserved_cookie_data = _cf.read()
            except Exception:
                preserved_cookie_data = None

            from HELPERS.filesystem_hlp import remove_media
            remove_media(message)  # Should only remove media; some installs could be aggressive

            # Restore cookies if cleanup removed them
            try:
                if preserved_cookie_data is not None and not os.path.exists(preserved_cookie_path):
                    os.makedirs(os.path.dirname(preserved_cookie_path), exist_ok=True)
                    with open(preserved_cookie_path, "wb") as _cfw:
                        _cfw.write(preserved_cookie_data)
                    logger.info("[IMG PRE-CLEANUP] Restored user's cookie.txt after cleanup")
            except Exception:
                pass

            logger.info(LoggerMsg.IMG_PRE_CLEANUP_COMPLETED_LOG_MSG)
        except Exception as e:
            logger.warning(LoggerMsg.IMG_PRE_CLEANUP_FAILED_LOG_MSG.format(e=e))

        # Streaming download: run range-based batches (1-10, 11-20, ...) scoped to a unique per-run directory
        run_dir = create_unique_download_path(user_id, url)
        create_directory(run_dir)
        
        # Create protection file for parallel downloads
        from HELPERS.filesystem_hlp import is_parallel_download_allowed, create_protection_file
        if is_parallel_download_allowed(message):
            create_protection_file(run_dir)
        
        files_to_cleanup = []

        # We'll not start full download thread; we'll pull ranges to enforce batching
        completion_sent = False  # Guard to ensure we exit after first completion announcement

        batch_size = 10
        # If total is small (<=10), download all at once without batching
        if detected_total and detected_total <= 10:
            batch_size = detected_total
        sent_message_ids = []
        seen_files = set()
        photos_videos_buffer = []  # store (converted_path, type, original_path)
        others_buffer = []  # store (converted_path, original_path)
        total_downloaded = 0
        total_sent = 0
        # Initialize album_index based on existing cache
        album_index = 0  # index of posts we send (albums only)
        if cached_map:
            max_cached_album_index = max(cached_map.keys())
            album_index = max_cached_album_index  # Start from the last cached album index
            logger.info(f"[IMG CACHE] Starting album_index from cached max: {album_index}")
        # is_admin and total_limit already defined above
        # Using detected_total if present; else metadata-based fallback
        total_expected = locals().get('total_expected') or None
        try:
            for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                if isinstance(image_info.get(key), int) and image_info.get(key) > 0:
                    total_expected = image_info.get(key) if is_admin else min(image_info.get(key), total_limit)
                    break
        except Exception:
            pass

        def update_status():
            messages = safe_get_messages(user_id)
            try:
                safe_edit_message_text(
                    user_id,
                    status_msg.id,
                    safe_get_messages(user_id).DOWNLOADING_MSG +
                    f"{safe_get_messages(user_id).DOWNLOADED_STATUS_MSG} <b>{total_downloaded}</b> / <b>{total_expected or total_limit}</b>\n"
                    f"{safe_get_messages(user_id).SENT_STATUS_MSG} <b>{total_sent}</b>\n"
                    f"{safe_get_messages(user_id).PENDING_TO_SEND_STATUS_MSG} <b>{len(photos_videos_buffer) + len(others_buffer)}</b>",
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass

        gallery_dl_dir = run_dir
        last_status_update = 0.0
        # Seed current_start and upper bound from manual range if provided
        current_start = 1
        manual_end_cap = None
        is_reverse_order_img = False  # Флаг для обратного порядка скачивания изображений
        # Removed failed_attempts logic - using only timeout-based stopping
        if manual_range is not None:
            original_current_start = manual_range[0]
            original_manual_end_cap = manual_range[1]
            current_start = original_current_start
            
            # Upper cap: if user provided end, respect it (but not above limit for non-admins)
            if original_manual_end_cap is not None:
                manual_end_cap = original_manual_end_cap if is_admin else min(original_manual_end_cap, total_limit)
                
                # Для отрицательных индексов нужно получить общее количество постов и преобразовать их
                if current_start < 0 or manual_end_cap < 0:
                    is_reverse_order_img = True
                    # Получаем общее количество постов для преобразования отрицательных индексов
                    total_media_count = detected_total
                    if not total_media_count:
                        # Пытаемся получить через get_total_media_count
                        try:
                            total_media_count = get_total_media_count(url, user_id, use_proxy)
                        except Exception:
                            total_media_count = None
                    
                    if total_media_count and total_media_count > 0:
                        # Преобразуем отрицательные индексы в положительные
                        # -1 = последний пост (total_media_count), -2 = предпоследний (total_media_count - 1), и т.д.
                        # Формула: positive_index = total_media_count + negative_index + 1
                        if current_start < 0:
                            current_start = total_media_count + current_start + 1
                        if manual_end_cap < 0:
                            manual_end_cap = total_media_count + manual_end_cap + 1
                        logger.info(f"[IMG] Converted negative indices: {original_current_start}->{current_start}, {original_manual_end_cap}->{manual_end_cap} (total={total_media_count})")
                        # После преобразования отрицательных индексов current_start > manual_end_cap - это нормально для обратного порядка
                        # Например: -1 до -7 -> 7 до 1, скачиваем в порядке 7, 6, 5, 4, 3, 2, 1
                        total_expected = abs(current_start - manual_end_cap) + 1
                    else:
                        # Если не удалось получить общее количество, используем абсолютные значения
                        logger.warning(f"[IMG] Could not get total media count for negative indices conversion, using absolute values")
                        total_expected = abs(manual_end_cap) - abs(current_start) + 1
                elif current_start > manual_end_cap:
                    is_reverse_order_img = True
                    total_expected = abs(current_start - manual_end_cap) + 1
                else:
                    # Calculate correct expected count for range (end - start + 1)
                    total_expected = manual_end_cap - current_start + 1
            else:
                # Open-ended range
                if current_start < 0:
                    # Для отрицательных индексов без конца используем разумное значение
                    total_expected = abs(current_start) if is_admin else min(abs(current_start), total_limit)
                else:
                    total_expected = total_limit
        
        # For small totals, set end cap to avoid range issues
        if detected_total and detected_total <= 10 and manual_range is None:
            manual_end_cap = detected_total
            total_expected = detected_total
            logger.info(LoggerMsg.IMG_BATCH_SMALL_TOTAL_LOG_MSG.format(detected_total=detected_total, manual_end_cap=manual_end_cap))
        
        # Fallback: if no total detected but manual range specified, use the range
        if manual_range is not None and total_expected is None:
            if manual_range[1] is not None:
                # Правильный расчет для отрицательных индексов и обратного порядка
                if manual_range[0] < 0 and manual_range[1] < 0:
                    total_expected = abs(manual_range[1]) - abs(manual_range[0]) + 1
                elif manual_range[0] > manual_range[1]:
                    total_expected = abs(manual_range[0] - manual_range[1]) + 1
                else:
                    total_expected = manual_range[1] - manual_range[0] + 1
            else:
                # Open-ended range, use a reasonable default
                if manual_range[0] < 0:
                    total_expected = abs(manual_range[0]) if is_admin else min(abs(manual_range[0]), total_limit)
                else:
                    total_expected = total_limit
            logger.info(f"[IMG FALLBACK] Using manual range for total_expected: {total_expected}")
            
            # Update status message to show we're proceeding with manual range
            try:
                safe_edit_message_text(
                    user_id, status_msg.id,
                    safe_get_messages(user_id).FALLBACK_SPECIFIED_RANGE_MSG.format(
                        start=manual_range[0], 
                        end=manual_range[1] if manual_range[1] else 'end'
                    ),
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                logger.warning(f"Failed to update status message: {e}")
        # Timeout tracking variables
        range_start_time = time.time()
        max_range_wait_time = LimitsConfig.MAX_IMG_RANGE_WAIT_TIME
        max_total_wait_time = LimitsConfig.MAX_IMG_TOTAL_WAIT_TIME
        total_start_time = time.time()
        last_activity_time = time.time()  # Track last time we found new files
        max_inactivity_time = LimitsConfig.MAX_IMG_INACTIVITY_TIME
        
        # helper to run one range and wait for files to appear
        def run_and_collect(next_end: int):
            messages = safe_get_messages(user_id)
            # For single item or when total is small, use range 1-1 to avoid API issues
            # Only use 1-1 when we're actually starting from 1 and it's a single item
            if (current_start == next_end and current_start == 1) or (detected_total and detected_total <= 10 and current_start == 1):
                logger.info(LoggerMsg.IMG_DOWNLOADING_RANGE_1_1_LOG_MSG.format(detected_total=detected_total, current_start=current_start, next_end=next_end))
                result = download_image_range_cli(url, "1-1", user_id, use_proxy, output_dir=run_dir)
                if isinstance(result, str):  # 401 Unauthorized error message
                    return result
                if not result:
                    logger.warning(LoggerMsg.IMG_CLI_DOWNLOAD_FAILED_LOG_MSG)
                    result = download_image_range(url, "1-1", user_id, use_proxy, run_dir)
                    if isinstance(result, str):  # 401 Unauthorized error message
                        return result
                    return result
            else:
                # Формируем правильный range_expr с учетом порядка
                if current_start > next_end:
                    # Обратный порядок: gallery-dl обычно не поддерживает, скачиваем по одному
                    range_expr = f"{next_end}-{current_start}"
                else:
                    range_expr = f"{current_start}-{next_end}"
                # Prefer CLI to enforce strict range behavior across gallery-dl versions
                logger.info(LoggerMsg.IMG_PREPARED_RANGE_LOG_MSG.format(range_expr=range_expr))
                result = download_image_range_cli(url, range_expr, user_id, use_proxy, output_dir=run_dir)
                if isinstance(result, str):  # 401 Unauthorized error message
                    return result
                if not result:
                    logger.warning(LoggerMsg.IMG_CLI_RANGE_FAILED_LOG_MSG.format(range_expr=range_expr))
                    result = download_image_range(url, range_expr, user_id, use_proxy, run_dir)
                    if isinstance(result, str):  # 401 Unauthorized error message
                        return result
                    return result
            return True
        
        # helper to run ranges in reverse order (for negative indices)
        def run_and_collect_reverse(start: int, end: int, batch_size: int):
            """Скачивает диапазон в обратном порядке, по одному элементу
            ВАЖНО: start и end должны быть уже преобразованы в положительные индексы"""
            messages = safe_get_messages(user_id)
            # Для обратного порядка скачиваем по одному элементу от start до end (в обратном порядке)
            # start > end после преобразования отрицательных индексов
            if start > end:
                # Скачиваем от большего к меньшему: start, start-1, ..., end+1, end
                for idx in range(start, end - 1, -1):
                    range_expr = f"{idx}-{idx}"
                    logger.info(f"[IMG REVERSE] Downloading single item: {range_expr}")
                    result = download_image_range_cli(url, range_expr, user_id, use_proxy, output_dir=run_dir)
                    if isinstance(result, str):  # 401 Unauthorized error message
                        return result
                    if not result:
                        logger.warning(f"[IMG REVERSE] CLI download failed for {range_expr}, trying fallback")
                        result = download_image_range(url, range_expr, user_id, use_proxy, run_dir)
                        if isinstance(result, str):  # 401 Unauthorized error message
                            return result
                    # Небольшая задержка между запросами
                    time.sleep(0.5)
            else:
                # Если start <= end, это не обратный порядок (не должно происходить)
                logger.warning(f"[IMG REVERSE] start ({start}) <= end ({end}), this should not happen for reverse order")
            return True

        consecutive_empty_searches = 0  # Counter for consecutive searches with no new files
        max_consecutive_empty_searches = 3  # Exit after 3 consecutive searches with no new files
        
        while True:
            # Check total timeout
            total_elapsed = time.time() - total_start_time
            if total_elapsed and total_elapsed > max_total_wait_time:
                logger.warning(LoggerMsg.IMG_BATCH_TOTAL_TIMEOUT_LOG_MSG.format(max_total_wait_time=max_total_wait_time, total_elapsed=total_elapsed))
                break
                
            # Check inactivity timeout - if no new files found for too long
            inactivity_elapsed = time.time() - last_activity_time
            if inactivity_elapsed and inactivity_elapsed > max_inactivity_time:
                logger.warning(LoggerMsg.IMG_BATCH_INACTIVITY_TIMEOUT_LOG_MSG.format(max_inactivity_time=max_inactivity_time, inactivity_elapsed=inactivity_elapsed))
                break
                
            # Only download next range if buffer is empty (strict batching)
            if len(photos_videos_buffer) == 0:
                upper_cap = manual_end_cap or total_expected
                # Проверка для обратного порядка (отрицательные индексы или start > end)
                if is_reverse_order_img:
                    # Для обратного порядка проверяем, не дошли ли мы до конца
                    if upper_cap and current_start < upper_cap:
                        break
                else:
                    # Для прямого порядка
                    if upper_cap and current_start > upper_cap:
                        break
                
                if is_reverse_order_img:
                    # Для обратного порядка: скачиваем от большего к меньшему
                    next_end = current_start - batch_size + 1
                    if upper_cap:
                        next_end = max(next_end, upper_cap)
                else:
                    # Для прямого порядка
                    next_end = current_start + batch_size - 1
                    if upper_cap:
                        next_end = min(next_end, upper_cap)
                logger.info(LoggerMsg.IMG_BATCH_STARTING_DOWNLOAD_RANGE_LOG_MSG.format(current_start=current_start, next_end=next_end))
                
                # Для обратного порядка формируем range_expr правильно
                if is_reverse_order_img and current_start > next_end:
                    range_expr = f"{next_end}-{current_start}"
                else:
                    range_expr = f"{current_start}-{next_end}"
                
                # Reset range timer
                range_start_time = time.time()
                
                # Count files before download
                files_before = len(seen_files)
                # Сохраняем исходное значение current_start для расчета expected_files
                original_current_start = current_start
                # Используем правильный range_expr для скачивания
                if is_reverse_order_img:
                    # Для обратного порядка gallery-dl может не поддерживать напрямую
                    # Скачиваем по одному элементу в обратном порядке
                    result = run_and_collect_reverse(current_start, next_end, batch_size)
                    # Обновляем current_start для обратного порядка
                    current_start = next_end - 1
                else:
                    result = run_and_collect(next_end)
                    # Обновляем current_start для прямого порядка
                    current_start = next_end + 1
                    
                    # Debug: Log the result type and content
                    logger.info(f"[IMG DEBUG] run_and_collect result: type={type(result)}, value={result}")
                    
                    # Check for fatal errors
                    if isinstance(result, str) and ":" in result and any(error_type in result for error_type in [
                        "Authentication Error", "Account Not Found", "Account Unavailable", 
                        "Rate Limit Exceeded", "Network Error", "Content Unavailable",
                        "Geographic Restrictions", "Verification Required", "Policy Violation",
                        "Unknown Error", "Fatal Error", "Critical Error", "Unexpected Error"
                    ]):
                        logger.error(LoggerMsg.IMG_FATAL_ERROR_DETECTED_LOG_MSG.format(result=result))
                        logger.info(f"[IMG DEBUG] Processing fatal error: status_msg={status_msg}, status_msg.id={status_msg.id if status_msg else 'None'}")
                        # Send error message to user and stop downloading
                        error_type = result.split(':')[0]
                        error_details = result.split(':', 1)[1].strip()
                        
                        # Use appropriate error message based on error type
                        if "Instagram" in error_details or "instagram" in error_details.lower():
                            error_msg = safe_get_messages(user_id).IMG_INSTAGRAM_AUTH_ERROR_MSG.format(
                                error_type=error_type,
                                url=url,
                                error_details=error_details
                            )
                        else:
                            # Generic error message for other platforms
                            error_msg = f"❌ <b>{error_type}</b>\n\n<b>URL:</b> <code>{url}</code>\n\n<b>Details:</b> {error_details}\n\nDownload stopped due to critical error."
                        
                        logger.info(f"[IMG DEBUG] Updating status message with error: {error_msg[:100]}...")
                        safe_edit_message_text(
                            status_msg.chat.id, status_msg.id,
                            error_msg,
                            parse_mode=enums.ParseMode.HTML
                        )
                        log_error_to_channel(message, f"Fatal error in image download: {result}", url)
                        return
                    
                    # Wait for download to complete before processing files
                    time.sleep(2)
                    
                    # Give additional time for file processing if this is the first range
                    if current_start == 1:
                        time.sleep(3)  # Extra wait for first range
                    
                    # Count files after download
                    files_after = len(seen_files)
                    files_downloaded_in_range = files_after - files_before
                    # Правильный расчет expected_files для обратного порядка
                    # Используем исходное значение original_current_start, сохраненное выше
                    if is_reverse_order_img:
                        expected_files = abs(original_current_start - next_end) + 1
                    else:
                        expected_files = next_end - original_current_start + 1
                    
                    elapsed_time = time.time() - range_start_time
                    logger.info(LoggerMsg.IMG_BATCH_DOWNLOADED_FILES_LOG_MSG.format(files_downloaded_in_range=files_downloaded_in_range, current_start=original_current_start, next_end=next_end, expected_files=expected_files, elapsed_time=elapsed_time))
                    
                    # Check if we got no files at all (gallery-dl found nothing)
                    # Always proceed to file search - don't break early
                    # current_start уже обновлен выше (строки 1729 или 1733), не обновляем повторно
                    if files_downloaded_in_range == 0:
                        logger.info(LoggerMsg.IMG_BATCH_NO_FILES_DOWNLOADED_LOG_MSG.format(current_start=original_current_start, next_end=next_end))
                    else:
                        logger.info(LoggerMsg.IMG_BATCH_FOUND_FILES_LOG_MSG.format(files_downloaded_in_range=files_downloaded_in_range))
                    
                    # Check if we got significantly fewer files than expected (less than 50% of expected)
                    # This indicates the media has ended
                    # current_start уже обновлен выше, не обновляем повторно
                    if files_downloaded_in_range and files_downloaded_in_range < expected_files * 0.5 and files_downloaded_in_range > 0:
                        logger.info(LoggerMsg.IMG_BATCH_MEDIA_ENDED_LOG_MSG.format(files_downloaded_in_range=files_downloaded_in_range, expected_files=expected_files))
            
            # Find new files - search in the actual download directory structure
            # gallery-dl creates subdirectories like instagram/username/ so we need to search deeper
            search_dir = gallery_dl_dir
            logger.info(LoggerMsg.IMG_BATCH_SEARCHING_FILES_LOG_MSG.format(search_dir=search_dir))
            
            files_found_in_this_search = 0  # Count files found in this search iteration
            
            if os.path.exists(search_dir):
                # Debug: list all subdirectories
                for root, dirs, files in os.walk(search_dir):
                    if files:
                        logger.info(LoggerMsg.IMG_BATCH_FOUND_FILES_IN_DIR_LOG_MSG.format(file_count=len(files), root=root))
                    if dirs:
                        logger.info(LoggerMsg.IMG_BATCH_FOUND_SUBDIRS_LOG_MSG.format(dirs=dirs))
                for root, _, files in os.walk(search_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Skip special thumbs/covers generated for Telegram
                        try:
                            base = os.path.basename(file_path)
                            if base.endswith('.__tgthumb.jpg') or base.endswith('.__tgcover_paid.jpg'):
                                continue
                        except Exception:
                            pass
                        if file_path in seen_files:
                            continue
                        # Only consider media-like files
                        if not file.lower().endswith((
                            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
                            '.mp4', '.m4v', '.avi', '.mov', '.mkv', '.webm', '.flv',
                            '.mp3', '.wav', '.ogg', '.m4a',
                            '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z'
                        )):
                            continue
                        # Skip incomplete/zero-byte files
                        try:
                            if os.path.getsize(file_path) == 0:
                                logger.info(LoggerMsg.IMG_BATCH_SKIPPING_ZERO_FILE_LOG_MSG.format(file_path=file_path))
                                continue
                        except Exception:
                            continue
                        seen_files.add(file_path)
                        total_downloaded += 1
                        files_found_in_this_search += 1  # Count files found in this search
                        last_activity_time = time.time()  # Update activity time when we find new files

                        # Enforce cap (but not for admins)
                        if not is_admin and total_downloaded > total_limit:
                            continue

                        # Convert if needed, then classify
                        original_path = file_path
                        converted = convert_file_to_telegram_format(file_path)
                        files_to_cleanup.append(converted)
                        if converted != original_path:
                            files_to_cleanup.append(original_path)
                        ext = os.path.splitext(converted)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                            photos_videos_buffer.append((converted, 'photo', original_path))
                        elif ext in ['.mp4']:
                            photos_videos_buffer.append((converted, 'video', original_path))
                        elif ext in ['.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']:
                            # Try to convert to mp4 if not already
                            converted = convert_file_to_telegram_format(converted)
                            ext2 = os.path.splitext(converted)[1].lower()
                            if ext2 != '.mp4':
                                # keep as document if still not mp4
                                others_buffer.append((converted, original_path))
                            else:
                                photos_videos_buffer.append((converted, 'video', original_path))
                        else:
                            others_buffer.append((converted, original_path))
                        
                        # Don't delete files immediately - wait until after sending
                        # This prevents Telegram from not finding files to send

                        # Send status occasionally
                        now = time.time()
                        if now - last_status_update > 1.5:
                            update_status()
                            last_status_update = now

                        # If we have 10 media for album, send immediately (strict batching)
                        if len(photos_videos_buffer) >= batch_size:
                            media_group = []
                            group_items = photos_videos_buffer[:batch_size]
                            for p, t, _orig in group_items:
                                if t == 'photo':
                                    # No spoiler in groups, only in private chats for paid media
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    # Изначально не ставим caption, чтобы избежать дублирования тегов; добавим их только первому элементу ниже
                                    media_group.append(InputMediaPhoto(p, caption=None, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                                else:
                                    # probe metadata
                                    vinfo = _probe_video_info(p)
                                    # generate thumbnail for better preview if needed (old behavior for free media)
                                    thumb = generate_video_thumbnail(p)
                                    # No spoiler in groups, only in private chats for paid media
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    if thumb and os.path.exists(thumb):
                                        media_group.append(InputMediaVideo(
                                            p,
                                            thumb=thumb,
                                            width=vinfo.get('width'),
                                            height=vinfo.get('height'),
                                            duration=vinfo.get('duration'),
                                            caption=None,
                                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                        ))
                                    else:
                                        media_group.append(InputMediaVideo(
                                            p,
                                            width=vinfo.get('width'),
                                            height=vinfo.get('height'),
                                            duration=vinfo.get('duration'),
                                            caption=None,
                                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                        ))
                            # Initialize sent variable
                            sent = []
                            # For paid media, only send in private chats (not groups/channels)
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            #  При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                            if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                original_chat_id = getattr(message, '_original_chat_id', user_id)
                                # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                logger.info(LoggerMsg.IMG_MAIN_FAKE_MESSAGE_LOG_MSG.format(original_chat_id=original_chat_id, is_private_chat=is_private_chat))
                            logger.info(LoggerMsg.IMG_MAIN_NSFW_FLAG_LOG_MSG.format(nsfw_flag=nsfw_flag, is_private_chat=is_private_chat, media_group_len=len(media_group)))
                            
                            # MAIN SENDING LOGIC - separate try-catch to prevent logging errors from triggering fallback
                            try:
                                if nsfw_flag and is_private_chat:
                                    logger.info(LoggerMsg.IMG_MAIN_PAID_LOGIC_LOG_MSG.format(item_count=len(media_group)))
                                    # Send as paid media album (up to 10 media files)
                                    try:
                                        # Convert media group to paid media format
                                        paid_media_list = []
                                        for m in media_group:
                                            if isinstance(m, InputMediaPhoto):
                                                paid_media_list.append(InputPaidMediaPhoto(media=m.media))
                                            else:
                                                # Ensure cover for paid media and pass explicit metadata
                                                media_path = m.media
                                                vinfo_paid = _probe_video_info(media_path)
                                                _cover = ensure_paid_cover_embedded(media_path, getattr(m, 'thumb', None))
                                                try:
                                                    paid_media_list.append(InputPaidMediaVideo(
                                                            media=media_path,
                                                            cover=_cover,
                                                            width=vinfo_paid.get('width'),
                                                            height=vinfo_paid.get('height'),
                                                            duration=vinfo_paid.get('duration'),
                                                            supports_streaming=True
                                                    ))
                                                except TypeError:
                                                    paid_media_list.append(InputPaidMediaVideo(media=media_path))
                                        
                                        # Send as single paid media album
                                        logger.info(LoggerMsg.IMG_PAID_SENDING_ALBUM_LOG_MSG.format(item_count=len(paid_media_list)))
                                        logger.info(LoggerMsg.IMG_PAID_MEDIA_TYPES_LOG_MSG.format(media_types=[type(item).__name__ for item in paid_media_list]))
                                        # Try to send as multiple albums (max 10 files per album), if that fails, send individually
                                        max_album_size = 10
                                        for album_start in range(0, len(paid_media_list), max_album_size):
                                            album_end = min(album_start + max_album_size, len(paid_media_list))
                                            album_items = paid_media_list[album_start:album_end]
                                            
                                            try:
                                                logger.info(f"{LoggerMsg.IMG_PAID_ATTEMPTING_ALBUM_LOG_MSG}")
                                                logger.info(f"{LoggerMsg.IMG_PAID_ALBUM_DETAILS_LOG_MSG}")
                                                
                                                paid_msg = app.send_paid_media(
                                                    user_id,
                                                    media=album_items,
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                
                                                logger.info(f"[IMG PAID] SUCCESS: send_paid_media returned: {type(paid_msg)}")
                                                logger.info(f"[IMG PAID] SUCCESS: Response details: {paid_msg}")
                                                
                                                if isinstance(paid_msg, list):
                                                    logger.info(f"[IMG PAID] SUCCESS: Received list of {len(paid_msg)} messages")
                                                    sent.extend(paid_msg)
                                                elif paid_msg is not None:
                                                    logger.info(f"[IMG PAID] SUCCESS: Received single message with ID: {getattr(paid_msg, 'id', 'unknown')}")
                                                    sent.append(paid_msg)
                                                else:
                                                    logger.warning(f"[IMG PAID] SUCCESS: Received None response from send_paid_media")
                                                
                                            except Exception as e:
                                                logger.error(f"[IMG PAID] Album {album_start//max_album_size + 1} failed: {e}")
                                                # Fallback: send individually as paid media with same reply_parameters
                                                for i, paid_media in enumerate(album_items):
                                                    try:
                                                        # Use same reply_parameters for all to group them
                                                        individual_msg = app.send_paid_media(
                                                            user_id,
                                                            media=[paid_media],
                                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                                            payload=str(Config.STAR_RECEIVER),
                                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                        )
                                                        if isinstance(individual_msg, list):
                                                            sent.extend(individual_msg)
                                                        elif individual_msg is not None:
                                                            sent.append(individual_msg)
                                                        # Small delay between messages to help grouping
                                                        if i and i < len(album_items) - 1:
                                                            time.sleep(0.1)
                                                    except Exception as e2:
                                                        logger.error(f"[IMG PAID] Individual paid media failed: {e2}")
                                        
                                        # Note: LOGS_PAID_ID forwarding is handled in main logic, not in fallback
                                        
                                        # Send open copy to LOGS_NSFW_ID for history
                                        try:
                                            # Create media group for open copy with proper caption
                                            open_media_group = []
                                            bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                            caption_lines = []
                                            if tags_text_norm:
                                                caption_lines.append(tags_text_norm)
                                            caption_lines.append(f"[Image URL]({url}) @{Config.BOT_NAME}")
                                            full_caption = "\n".join(caption_lines)
                                            
                                            for idx, m in enumerate(media_group):
                                                caption = full_caption if idx == 0 else None  # Only first item gets caption
                                                if isinstance(m, InputMediaPhoto):
                                                    open_media_group.append(InputMediaPhoto(
                                                        media=m.media,
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                                else:
                                                    open_media_group.append(InputMediaVideo(
                                                        media=m.media,
                                                        thumb=getattr(m, 'thumb', None),
                                                        width=getattr(m, 'width', None),
                                                        height=getattr(m, 'height', None),
                                                        duration=getattr(m, 'duration', None),
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                            
                                            # Send open copy as album to NSFW channel
                                            log_channel_nsfw = get_log_channel("video", nsfw=True)
                                            if log_channel_nsfw:
                                                open_sent = app.send_media_group(
                                                    chat_id=log_channel_nsfw,
                                                    media=open_media_group,
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                logger.info(f"[IMG LOG] Open copy album sent to LOGS_NSFW_ID for history: {len(open_media_group)} items")
                                        except Exception as e:
                                            logger.error(f"[IMG LOG] Failed to send open copy album to LOGS_NSFW_ID: {e}")
                                            
                                    except Exception as e:
                                        logger.error(LoggerMsg.IMG_FAILED_SEND_PAID_MEDIA_ALBUM_LOG_MSG.format(e=e))
                                        # Send as paid media album with fallback to individual with grouping
                                        sent = []
                                        logger.info(f"[IMG MAIN FALLBACK] Attempting to send {len(media_group)} media as paid album")
                                        
                                        # Convert media group to paid media format
                                        paid_media_list = []
                                        for m in media_group:
                                            if isinstance(m, InputMediaPhoto):
                                                paid_media_list.append(InputPaidMediaPhoto(media=m.media))
                                            else:
                                                # Ensure cover for paid media and pass explicit metadata
                                                media_path = m.media
                                                vinfo_paid = _probe_video_info(media_path)
                                                _cover = ensure_paid_cover_embedded(media_path, getattr(m, 'thumb', None))
                                                try:
                                                    paid_media_list.append(InputPaidMediaVideo(
                                                        media=media_path,
                                                        cover=_cover,
                                                        width=vinfo_paid.get('width'),
                                                        height=vinfo_paid.get('height'),
                                                        duration=vinfo_paid.get('duration'),
                                                        supports_streaming=True
                                                    ))
                                                except TypeError:
                                                    paid_media_list.append(InputPaidMediaVideo(media=media_path))
                                        
                                        # Try to send as multiple albums (max 10 files per album), if that fails, send individually with grouping
                                        max_album_size = 10
                                        for album_start in range(0, len(paid_media_list), max_album_size):
                                            album_end = min(album_start + max_album_size, len(paid_media_list))
                                            album_items = paid_media_list[album_start:album_end]
                                            
                                            try:
                                                logger.info(f"[IMG MAIN FALLBACK] Attempting album {album_start//max_album_size + 1} with {len(album_items)} items to user {user_id}")
                                                logger.info(f"[IMG MAIN FALLBACK] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                                
                                                paid_msg = app.send_paid_media(
                                                        user_id,
                                                    media=album_items,
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                    )
                                                
                                                logger.info(f"[IMG MAIN FALLBACK] SUCCESS: send_paid_media returned: {type(paid_msg)}")
                                                logger.info(f"[IMG MAIN FALLBACK] SUCCESS: Response details: {paid_msg}")
                                                
                                                if isinstance(paid_msg, list):
                                                    logger.info(f"[IMG MAIN FALLBACK] SUCCESS: Received list of {len(paid_msg)} messages")
                                                    sent.extend(paid_msg)
                                                elif paid_msg is not None:
                                                    logger.info(f"[IMG MAIN FALLBACK] SUCCESS: Received single message with ID: {getattr(paid_msg, 'id', 'unknown')}")
                                                    sent.append(paid_msg)
                                                else:
                                                    logger.warning(f"[IMG MAIN FALLBACK] SUCCESS: Received None response from send_paid_media")
                                                
                                            except Exception as e:
                                                logger.error(f"[IMG MAIN FALLBACK] Album {album_start//max_album_size + 1} failed: {e}")
                                                # Fallback: send individually as paid media with same reply_parameters for grouping
                                                for i, paid_media in enumerate(album_items):
                                                    try:
                                                        # Use same reply_parameters for all to group them
                                                        individual_msg = app.send_paid_media(
                                                        user_id,
                                                            media=[paid_media],
                                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                                            payload=str(Config.STAR_RECEIVER),
                                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                        )
                                                        if isinstance(individual_msg, list):
                                                            sent.extend(individual_msg)
                                                        elif individual_msg is not None:
                                                            sent.append(individual_msg)
                                                        # Small delay between messages to help grouping
                                                        if i and i < len(album_items) - 1:
                                                            time.sleep(0.1)
                                                    except Exception as e2:
                                                        logger.error(f"[IMG MAIN FALLBACK] Individual paid media failed: {e2}")
                                        
                                        # Send open copy to NSFW channel for history as album
                                        try:
                                            open_media_group = []
                                            for m in media_group:
                                                caption = (tags_text_norm or "") if len(open_media_group) == 0 else None
                                                if isinstance(m, InputMediaPhoto):
                                                    open_media_group.append(InputMediaPhoto(
                                                        media=m.media,
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                                else:
                                                    open_media_group.append(InputMediaVideo(
                                                        media=m.media,
                                                        thumb=getattr(m, 'thumb', None),
                                                        width=getattr(m, 'width', None),
                                                        height=getattr(m, 'height', None),
                                                        duration=getattr(m, 'duration', None),
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                            
                                            # Send open copy as album to NSFW channel
                                            log_channel_nsfw = get_log_channel("video", nsfw=True)
                                            open_sent = app.send_media_group(
                                                chat_id=log_channel_nsfw,
                                                media=open_media_group,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                            logger.info(f"[IMG LOG] Open copy album sent to NSFW channel for history: {len(open_media_group)} items")
                                        except Exception as e:
                                            logger.error(f"[IMG LOG] Failed to send open copy album to NSFW channel: {e}")
                                else:
                                    # In groups/channels or non-NSFW content, send as regular media group
                                    attempts = 0
                                    last_exc = None
                                    while attempts < 5:
                                        try:
                                            # Ensure album-level caption: put user tags on the first item only
                                            try:
                                                if media_group:
                                                    _first = media_group[0]
                                                    _exist = getattr(_first, 'caption', None) or ''
                                                    
                                                    # Create user caption with emoji numbers and dates
                                                    profile_name = extract_profile_name(url)
                                                    site_name = extract_site_name(url)
                                                    user_caption = create_album_caption_with_dates(media_group, url, tags_text_norm, profile_name, site_name, user_id)
                                                    
                                                    _sep = (' ' if _exist and not _exist.endswith('\n') else '')
                                                    # Если у первого уже стоит эта подпись, не дублируем
                                                    if _exist.strip() == user_caption.strip():
                                                        _first.caption = _exist.strip()
                                                    else:
                                                        _first.caption = (_exist + _sep + user_caption).strip()
                                                    # Avoid duplicating tags on the rest of items
                                                    for _itm in media_group[1:]:
                                                        if getattr(_itm, 'caption', None) == tags_text_norm:
                                                            _itm.caption = None
                                            except Exception as _e:
                                                logger.debug(LoggerMsg.IMG_ALBUM_CAPTION_NORMALIZATION_SKIPPED_LOG_MSG.format(_e=_e))
                                            # DEBUG: Log media group sending
                                            # message_thread_id already extracted above
                                            logger.info(f"[IMG MEDIA_GROUP] About to send media group to chat_id={chat_id}, message_thread_id={message_thread_id}")
                                            
                                            sent = app.send_media_group(
                                                chat_id,
                                                media=media_group,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                                message_thread_id=message_thread_id
                                            )
                                            logger.info(f"[IMG MEDIA_GROUP] Media group sent successfully")
                                            break
                                        except FloodWait as fw:
                                            wait_s = int(getattr(fw, 'value', 0) or 0)
                                            logger.warning(LoggerMsg.IMG_FLOODWAIT_SEND_MEDIA_GROUP_LOG_MSG.format(wait_s=wait_s, attempts=attempts))
                                            time.sleep(wait_s + 1)
                                            attempts += 1
                                            last_exc = fw
                                        except Exception as ex:
                                            last_exc = ex
                                            break
                                    if attempts and attempts >= 5 and last_exc is not None:
                                        raise last_exc
                                sent_message_ids.extend([m.id for m in sent])
                                total_sent += len(media_group)
                                # Forward album to logs and save forwarded IDs to cache
                                try:
                                    orig_ids = [m.id for m in sent]
                                    logger.info(LoggerMsg.IMG_CACHE_COPYING_ALBUM_LOG_MSG.format(orig_ids=orig_ids))
                                    f_ids = []
                                    
                                    # Determine correct log channel based on media type and chat type
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    #  При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                                    if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                        original_chat_id = getattr(message, '_original_chat_id', user_id)
                                        # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                        is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                        logger.info(LoggerMsg.IMG_LOG_FAKE_MESSAGE_DETECTED_LOG_MSG.format(original_chat_id=original_chat_id, is_private_chat=is_private_chat))
                                    is_paid_media = nsfw_flag and is_private_chat
                                    
                                    #  Отправка в лог-каналы должна быть ВНЕ цикла, только один раз для всего альбома
                                    if is_paid_media:
                                        # For NSFW content in private chat, send to both channels but don't cache
                                        # Add delay to allow Telegram to process paid media before sending to log channels
                                        time.sleep(2.0)
                                        
                                        # Send to LOGS_PAID_ID (for paid content) - forward the paid message
                                        log_channel_paid = getattr(Config, "LOGS_PAID_ID", 0)
                                        if log_channel_paid:
                                            try:
                                                # Forward the paid message to paid log channel
                                                for msg in sent:
                                                    if msg is not None:
                                                        app.forward_messages(
                                                            chat_id=log_channel_paid,
                                                            from_chat_id=user_id,
                                                            message_ids=[msg.id]
                                                        )
                                                        time.sleep(0.1)  # Small delay between forwards
                                                logger.info(f"[IMG LOG] Paid media forwarded to LOGS_PAID_ID: {len(sent)} messages")
                                            except Exception as fe:
                                                logger.error(f"[IMG LOG] Failed to forward paid media to LOGS_PAID_ID: {fe}")
                                        
                                        # Don't cache NSFW content
                                        logger.info(f"[IMG LOG] NSFW content sent to LOGS_PAID_ID, not cached")
                                    
                                    elif nsfw_flag and not is_private_chat:
                                        # NSFW content in groups -> LOGS_NSFW_ID only - send as album
                                        log_channel_nsfw = get_log_channel("video", nsfw=True)
                                        if log_channel_nsfw:
                                            try:
                                                # Create media group for NSFW log channel with proper caption
                                                nsfw_log_media_group = []
                                                bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                                caption_lines = []
                                                if tags_text_norm:
                                                    caption_lines.append(tags_text_norm)
                                                caption_lines.append(f"[Image URL]({url}) @{Config.BOT_NAME}")
                                                full_caption = "\n".join(caption_lines)
                                                
                                                for _idx, _media_obj in enumerate(media_group):
                                                    caption = full_caption if _idx == 0 else None  # Only first item gets caption
                                                    if isinstance(_media_obj, InputMediaPhoto):
                                                        nsfw_log_media_group.append(InputMediaPhoto(
                                                            media=_media_obj.media,
                                                            caption=caption,
                                                            has_spoiler=True
                                                        ))
                                                    else:
                                                        nsfw_log_media_group.append(InputMediaVideo(
                                                            media=_media_obj.media,
                                                            caption=caption,
                                                            duration=getattr(_media_obj, 'duration', None),
                                                            width=getattr(_media_obj, 'width', None),
                                                            height=getattr(_media_obj, 'height', None),
                                                            thumb=getattr(_media_obj, 'thumb', None),
                                                            has_spoiler=True
                                                        ))
                                                
                                                # Send as album to NSFW log channel
                                                nsfw_log_sent = app.send_media_group(
                                                    chat_id=log_channel_nsfw,
                                                    media=nsfw_log_media_group,
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                logger.info(f"[IMG LOG] NSFW media album sent to LOGS_NSFW_ID: {len(nsfw_log_media_group)} items")
                                            except Exception as fe:
                                                logger.error(f"[IMG LOG] Failed to send NSFW media album to LOGS_NSFW_ID: {fe}")
                                        
                                        # Don't cache NSFW content
                                        logger.info(f"[IMG LOG] NSFW content sent to LOGS_NSFW_ID, not cached")
                                        
                                    else:
                                        # Regular content -> LOGS_IMG_ID and cache - send as album
                                        log_channel = get_log_channel("image", nsfw=False, paid=False)
                                        try:
                                            # Create media group for regular log channel
                                            regular_log_media_group = []
                                            # Prefer original first-item caption (from user album) to preserve full formatting
                                            original_caption = None
                                            try:
                                                if media_group and getattr(media_group[0], 'caption', None):
                                                    original_caption = media_group[0].caption
                                            except Exception:
                                                original_caption = None
                                            # Fallback: build caption as before if original caption is missing
                                            if not original_caption:
                                                bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                                log_caption_lines = []
                                                if tags_text_norm:
                                                    log_caption_lines.append(tags_text_norm)
                                                # Add profile and site hashtags first
                                                profile_name = extract_profile_name(url)
                                                site_name = extract_site_name(url)
                                                hashtags = []
                                                if profile_name:
                                                    hashtags.append(f"#{profile_name}")
                                                if site_name:
                                                    hashtags.append(f"#{site_name}")
                                                if hashtags:
                                                    log_caption_lines.append(" ".join(hashtags))
                                                # Add URL with paperclip emoji
                                                log_caption_lines.append(f"{safe_get_messages(user_id).IMAGE_URL_CAPTION_MSG.format(url=url)} @{Config.BOT_NAME}")
                                                log_caption = "\n".join(log_caption_lines)
                                            else:
                                                log_caption = original_caption
                                            
                                            for _idx, _media_obj in enumerate(media_group):
                                                caption = log_caption if _idx == 0 else None  # Only first item gets caption
                                                if isinstance(_media_obj, InputMediaPhoto):
                                                    regular_log_media_group.append(InputMediaPhoto(
                                                        media=_media_obj.media,
                                                        caption=caption
                                                    ))
                                                else:
                                                    regular_log_media_group.append(InputMediaVideo(
                                                        media=_media_obj.media,
                                                        caption=caption,
                                                        duration=getattr(_media_obj, 'duration', None),
                                                        width=getattr(_media_obj, 'width', None),
                                                        height=getattr(_media_obj, 'height', None),
                                                        thumb=getattr(_media_obj, 'thumb', None)
                                                    ))
                                            
                                            # Send as album to regular log channel
                                            regular_log_sent = app.send_media_group(
                                                chat_id=log_channel,
                                                media=regular_log_media_group,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                            logger.info(f"[IMG LOG] Regular media album sent to IMG channel: {len(regular_log_media_group)} items")
                                            
                                            # Cache regular content
                                            f_ids = [m.id for m in regular_log_sent]
                                            logger.info(f"[IMG CACHE] Regular content cached with IDs: {f_ids}")
                                            
                                        except Exception as fe:
                                            logger.error(f"[IMG LOG] Failed to send regular media album to IMG channel: {fe}")
                                    
                                    album_index += 1
                                    # Only cache regular content (not NSFW)
                                    if f_ids and not nsfw_flag:
                                        logger.info(f"[IMG CACHE] Album index={album_index} collected log_ids={f_ids}")
                                        _save_album_now(url, album_index, f_ids)
                                    elif nsfw_flag:
                                        logger.info(f"[IMG CACHE] Skipping cache save for NSFW content, album index={album_index}")
                                    else:
                                        logger.error("[IMG CACHE] No log IDs collected; skipping cache save for this album")
                                except Exception as e_copy:
                                    logger.error(f"[IMG CACHE] Unexpected error while copying album to logs: {e_copy}")
                                # Delete files immediately after sending (strict batching)
                                def delete_file(path):
                                    messages = safe_get_messages(user_id)
                                    try:
                                        if os.path.exists(path):
                                            # Delete file to prevent re-processing
                                            os.remove(path)
                                            logger.info(f"[IMG BATCH] Deleted file: {path}")
                                    except Exception as e:
                                        logger.warning(f"[IMG BATCH] Failed to delete {path}: {e}")
                                for p, _t, orig in group_items:
                                    delete_file(p)
                                    delete_file(orig)
                                photos_videos_buffer = photos_videos_buffer[batch_size:]
                                update_status()
                                # Delete generated special thumbs/covers
                                try:
                                    for m in media_group:
                                        tpath = getattr(m, 'thumb', None)
                                        if tpath and isinstance(tpath, str) and (tpath.endswith('.__tgthumb.jpg') or tpath.endswith('.__tgcover_paid.jpg')):
                                            try:
                                                if os.path.exists(tpath):
                                                    os.remove(tpath)
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                            except Exception as e:
                                logger.error(f"Failed to send media group: {e}")
                                logger.info(f"[IMG FALLBACK] Entering fallback logic, nsfw_flag={nsfw_flag}, media_group_len={len(media_group)}")
                                # fallback: send individually
                                fallback = photos_videos_buffer[:batch_size]
                                photos_videos_buffer = photos_videos_buffer[batch_size:]
                                sent = []
                                
                                # Check if we should send as paid media album
                                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                #  При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                                if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                    original_chat_id = getattr(message, '_original_chat_id', user_id)
                                    # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                    is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                    logger.info(f"[IMG FALLBACK] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                                logger.info(f"[IMG FALLBACK] nsfw_flag={nsfw_flag}, is_private_chat={is_private_chat}, len(fallback)={len(fallback)}")
                                if nsfw_flag and is_private_chat and len(fallback) > 1:
                                    # Try to send as paid media album first
                                    try:
                                        paid_media_list = []
                                        for p, t, orig in fallback:
                                            if t == 'photo':
                                                paid_media_list.append(InputPaidMediaPhoto(media=p))
                                            else:
                                                # For videos, ensure cover
                                                thumb = generate_video_thumbnail(p)
                                                _cover = ensure_paid_cover_embedded(p, thumb)
                                                try:
                                                    vinfo = _probe_video_info(p)
                                                    paid_media_list.append(InputPaidMediaVideo(
                                                        media=p,
                                                        cover=_cover,
                                                        width=vinfo.get('width'),
                                                        height=vinfo.get('height'),
                                                        duration=vinfo.get('duration'),
                                                        supports_streaming=True
                                                    ))
                                                except TypeError:
                                                    paid_media_list.append(InputPaidMediaVideo(media=p))
                                        
                                        # Send as multiple paid media albums (max 10 files per album)
                                        logger.info(f"[IMG FALLBACK PAID] Sending paid media albums with {len(paid_media_list)} items total")
                                        max_album_size = 10
                                        for album_start in range(0, len(paid_media_list), max_album_size):
                                            album_end = min(album_start + max_album_size, len(paid_media_list))
                                            album_items = paid_media_list[album_start:album_end]
                                            
                                            try:
                                                logger.info(f"[IMG FALLBACK PAID] Attempting album {album_start//max_album_size + 1} with {len(album_items)} items to user {user_id}")
                                                logger.info(f"[IMG FALLBACK PAID] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                                
                                                paid_msg = app.send_paid_media(
                                                    user_id,
                                                    media=album_items,
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                
                                                logger.info(f"[IMG FALLBACK PAID] SUCCESS: send_paid_media returned: {type(paid_msg)}")
                                                logger.info(f"[IMG FALLBACK PAID] SUCCESS: Response details: {paid_msg}")
                                                
                                                if isinstance(paid_msg, list):
                                                    logger.info(f"[IMG FALLBACK PAID] SUCCESS: Received list of {len(paid_msg)} messages")
                                                    sent.extend(paid_msg)
                                                elif paid_msg is not None:
                                                    logger.info(f"[IMG FALLBACK PAID] SUCCESS: Received single message with ID: {getattr(paid_msg, 'id', 'unknown')}")
                                                    sent.append(paid_msg)
                                                else:
                                                    logger.warning(f"[IMG FALLBACK PAID] SUCCESS: Received None response from send_paid_media")
                                                    
                                            except Exception as e:
                                                logger.error(f"[IMG FALLBACK PAID] Album {album_start//max_album_size + 1} failed: {e}")
                                                # Fallback: send individually as paid media with same reply_parameters
                                                for i, paid_media in enumerate(album_items):
                                                    try:
                                                        # Use same reply_parameters for all to group them
                                                        individual_msg = app.send_paid_media(
                                                            user_id,
                                                            media=[paid_media],
                                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                                            payload=str(Config.STAR_RECEIVER),
                                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                        )
                                                        if isinstance(individual_msg, list):
                                                            sent.extend(individual_msg)
                                                        elif individual_msg is not None:
                                                            sent.append(individual_msg)
                                                        # Small delay between messages to help grouping
                                                        if i and i < len(album_items) - 1:
                                                            time.sleep(0.1)
                                                    except Exception as e2:
                                                        logger.error(f"[IMG FALLBACK PAID] Individual paid media failed: {e2}")
                                        
                                        # Send open copy to NSFW channel for history
                                        try:
                                            open_media_group = []
                                            for p, t, orig in fallback:
                                                caption = (tags_text_norm or "") if len(open_media_group) == 0 else None
                                                if t == 'photo':
                                                    open_media_group.append(InputMediaPhoto(
                                                        media=p,
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                                else:
                                                    thumb = generate_video_thumbnail(p)
                                                    vinfo = _probe_video_info(p)
                                                    open_media_group.append(InputMediaVideo(
                                                        media=p,
                                                        thumb=thumb,
                                                        width=vinfo.get('width'),
                                                        height=vinfo.get('height'),
                                                        duration=vinfo.get('duration'),
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                            
                                            # Send open copy as album to NSFW channel
                                            log_channel_nsfw = get_log_channel("video", nsfw=True)
                                            open_sent = app.send_media_group(
                                                chat_id=log_channel_nsfw,
                                                media=open_media_group,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                            logger.info(f"[IMG LOG] Open copy album sent to NSFW channel for history: {len(open_media_group)} items")
                                        except Exception as e:
                                            logger.error(f"[IMG LOG] Failed to send open copy album to NSFW channel: {e}")
                                        
                                        # Skip individual sending since we sent as album
                                        continue
                                        
                                    except Exception as e:
                                        logger.error(f"Failed to send paid media album in fallback: {e}")
                                        # Continue with individual sending
                                
                                # Individual sending (fallback or single items) - group with reply_parameters
                                #  При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                                if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                    original_chat_id = getattr(message, '_original_chat_id', user_id)
                                    # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                    is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                    logger.info(f"[IMG INDIVIDUAL] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                                if nsfw_flag and is_private_chat and len(fallback) > 1:
                                    # Send as paid media album with same reply_parameters for grouping
                                    try:
                                        paid_media_list = []
                                        for p, t, orig in fallback:
                                            if t == 'photo':
                                                paid_media_list.append(InputPaidMediaPhoto(media=p))
                                            else:
                                                # For videos, ensure cover
                                                thumb = generate_video_thumbnail(p)
                                                _cover = ensure_paid_cover_embedded(p, thumb)
                                                try:
                                                    vinfo = _probe_video_info(p)
                                                    paid_media_list.append(InputPaidMediaVideo(
                                                        media=p,
                                                        cover=_cover,
                                                        width=vinfo.get('width'),
                                                        height=vinfo.get('height'),
                                                        duration=vinfo.get('duration'),
                                                        supports_streaming=True
                                                    ))
                                                except TypeError:
                                                    paid_media_list.append(InputPaidMediaVideo(media=p))
                                        
                                        # Try to send as album first, if that fails, send individually
                                        try:
                                            logger.info(f"[IMG FALLBACK PAID] Attempting to send album with {len(paid_media_list)} items to user {user_id}")
                                            logger.info(f"[IMG FALLBACK PAID] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                            
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=paid_media_list,
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                            
                                            logger.info(f"[IMG FALLBACK PAID] SUCCESS: send_paid_media returned: {type(paid_msg)}")
                                            logger.info(f"[IMG FALLBACK PAID] SUCCESS: Response details: {paid_msg}")
                                            
                                            if isinstance(paid_msg, list):
                                                logger.info(f"[IMG FALLBACK PAID] SUCCESS: Received list of {len(paid_msg)} messages")
                                                sent.extend(paid_msg)
                                            elif paid_msg is not None:
                                                logger.info(f"[IMG FALLBACK PAID] SUCCESS: Received single message with ID: {getattr(paid_msg, 'id', 'unknown')}")
                                                sent.append(paid_msg)
                                            else:
                                                logger.warning(f"[IMG FALLBACK PAID] SUCCESS: Received None response from send_paid_media")
                                                
                                        except Exception as e:
                                            logger.error(f"{LoggerMsg.IMG_PAID_SEND_PAID_MEDIA_ALBUM_FAILED_LOG_MSG}")
                                            logger.error(f"{LoggerMsg.IMG_PAID_ERROR_TYPE_LOG_MSG}")
                                            logger.error(f"{LoggerMsg.IMG_PAID_ERROR_DETAILS_LOG_MSG}")
                                            # Fallback: send individually as paid media with same reply_parameters
                                            for i, paid_media in enumerate(paid_media_list):
                                                try:
                                                    # Use same reply_parameters for all to group them
                                                    individual_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[paid_media],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                    )
                                                    if isinstance(individual_msg, list):
                                                        sent.extend(individual_msg)
                                                    elif individual_msg is not None:
                                                        sent.append(individual_msg)
                                                    # Small delay between messages to help grouping
                                                    if i and i < len(paid_media_list) - 1:
                                                        time.sleep(0.1)
                                                except Exception as e2:
                                                    logger.error(f"[IMG FALLBACK PAID] Individual paid media failed: {e2}")
                                        
                                        # Note: LOGS_PAID_ID forwarding is handled in main logic, not in fallback
                                        
                                        # Send open copy to LOGS_NSFW_ID for history
                                        try:
                                            # Create media group for open copy with proper caption
                                            open_media_group = []
                                            bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                            caption_lines = []
                                            if tags_text_norm:
                                                caption_lines.append(tags_text_norm)
                                            caption_lines.append(f"[Image URL]({url}) @{Config.BOT_NAME}")
                                            full_caption = "\n".join(caption_lines)
                                            
                                            for idx, (p, t, orig) in enumerate(fallback):
                                                caption = full_caption if idx == 0 else None
                                                if t == 'photo':
                                                    open_media_group.append(InputMediaPhoto(
                                                        media=p,
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                                else:
                                                    thumb = generate_video_thumbnail(p)
                                                    vinfo = _probe_video_info(p)
                                                    open_media_group.append(InputMediaVideo(
                                                        media=p,
                                                        thumb=thumb,
                                                        width=vinfo.get('width'),
                                                        height=vinfo.get('height'),
                                                        duration=vinfo.get('duration'),
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                            
                                            # Send open copy as album to NSFW channel
                                            log_channel_nsfw = get_log_channel("video", nsfw=True)
                                            if log_channel_nsfw:
                                                open_sent = app.send_media_group(
                                                    chat_id=log_channel_nsfw,
                                                    media=open_media_group,
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                logger.info(f"[IMG LOG] Open copy album sent to LOGS_NSFW_ID for history: {len(open_media_group)} items")
                                        except Exception as e:
                                            logger.error(f"[IMG LOG] Failed to send open copy album to LOGS_NSFW_ID: {e}")
                                        
                                        # Skip individual sending since we sent as album
                                        continue
                                        
                                    except Exception as e:
                                        logger.error(f"Failed to send paid media album in fallback: {e}")
                                        # Continue with individual sending
                                
                                # Album sending (fallback) - send as albums of max 10 items
                                logger.info(f"[IMG FALLBACK ALBUM] Starting album sending for {len(fallback)} items, nsfw_flag={nsfw_flag}, is_private_chat={is_private_chat}")
                                
                                # Group fallback items into albums of max 10 items
                                fallback_album_size = 10
                                for album_start in range(0, len(fallback), fallback_album_size):
                                    album_end = min(album_start + fallback_album_size, len(fallback))
                                    album_items = fallback[album_start:album_end]
                                    
                                    # Create media group for this album
                                    try:
                                        if nsfw_flag and is_private_chat:
                                            # NSFW content in private chat - send as paid media album
                                            paid_media_list = []
                                            for p, t, orig in album_items:
                                                if t == 'photo':
                                                    paid_media_list.append(InputPaidMediaPhoto(media=p))
                                                else:
                                                    try:
                                                        _cover = ensure_paid_cover_embedded(p, generate_video_thumbnail(p))
                                                        paid_media_list.append(InputPaidMediaVideo(media=p, cover=_cover))
                                                    except:
                                                        paid_media_list.append(InputPaidMediaVideo(media=p))
                                            
                                            sent_msg = app.send_paid_media(
                                                user_id,
                                                media=paid_media_list,
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                            if isinstance(sent_msg, list):
                                                sent.extend(sent_msg)
                                            elif sent_msg is not None:
                                                sent.append(sent_msg)
                                        else:
                                            # Regular content - send as media group
                                            media_group = []
                                            for idx, (p, t, orig) in enumerate(album_items):
                                                caption = (tags_text_norm if album_start == 0 and idx == 0 else '')
                                                if t == 'photo':
                                                    media_group.append(InputMediaPhoto(
                                                        media=p,
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                                else:
                                                    thumb = generate_video_thumbnail(p)
                                                    vinfo = _probe_video_info(p)
                                                    media_group.append(InputMediaVideo(
                                                        media=p,
                                                        thumb=thumb,
                                                        width=vinfo.get('width'),
                                                        height=vinfo.get('height'),
                                                        duration=vinfo.get('duration'),
                                                        caption=caption,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                                    ))
                                            
                                            sent_msg = app.send_media_group(
                                                chat_id,
                                                media=media_group,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                                message_thread_id=message_thread_id
                                            )
                                            if isinstance(sent_msg, list):
                                                sent.extend(sent_msg)
                                            elif sent_msg is not None:
                                                sent.append(sent_msg)
                                        
                                        logger.info(f"[IMG FALLBACK ALBUM] Successfully sent album {album_start+1}-{album_end} ({len(album_items)} items)")
                                        
                                        # Small delay between albums
                                        if album_end and album_end < len(fallback):
                                            time.sleep(0.5)
                                        
                                    except Exception as album_exc:
                                        logger.error(f"[IMG FALLBACK ALBUM] Failed to send album {album_start+1}-{album_end}: {album_exc}")
                                        # Individual sending as last resort only
                                        logger.info(f"[IMG INDIVIDUAL] Fallback to individual sending for {len(album_items)} items")
                                        continue  # Skip this album and continue with next one
                                # Forward fallback album and save forwarded IDs
                                try:
                                    if sent:
                                        orig_ids = [m.id for m in sent]
                                        logger.info(f"[IMG CACHE] Copying fallback album to logs, orig_ids={orig_ids}")
                                        f_ids = []
                                        
                                        # Determine correct log channel based on media type and chat type
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        is_paid_media = nsfw_flag and is_private_chat
                                        
                                        for _mid in orig_ids:
                                            try:
                                                if is_paid_media:
                                                    # For NSFW content in private chat, send to both channels but don't cache
                                                    # Add delay to allow Telegram to process paid media before sending to log channels
                                                    time.sleep(2.0)
                                                    
                                                    # Send to LOGS_PAID_ID (for paid content) - forward the paid message
                                                    log_channel_paid = get_log_channel("image", nsfw=False, paid=True)
                                                    try:
                                                        app.forward_messages(chat_id=log_channel_paid, from_chat_id=user_id, message_ids=[_mid])
                                                        time.sleep(0.05)
                                                    except Exception as fe:
                                                        logger.error(f"[IMG LOG] forward_messages (fallback) failed for paid media id={_mid}: {fe}")
                                                    
                                                    # Send to LOGS_NSFW_ID (for history) - send open copy as album
                                                    log_channel_nsfw = get_log_channel("image", nsfw=True, paid=False)
                                                    try:
                                                        # Create media group for NSFW log channel (open copy)
                                                        nsfw_log_media_group = []
                                                        for _idx, _media_obj in enumerate(media_group):
                                                            caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                                            if isinstance(_media_obj, InputMediaPhoto):
                                                                nsfw_log_media_group.append(InputMediaPhoto(
                                                                    media=_media_obj.media,
                                                                    caption=caption
                                                                ))
                                                            else:
                                                                nsfw_log_media_group.append(InputMediaVideo(
                                                                    media=_media_obj.media,
                                                                    caption=caption,
                                                                    duration=getattr(_media_obj, 'duration', None),
                                                                    width=getattr(_media_obj, 'width', None),
                                                                    height=getattr(_media_obj, 'height', None),
                                                                    thumb=getattr(_media_obj, 'thumb', None)
                                                                ))
                                                        
                                                        # Send as album to NSFW log channel
                                                        nsfw_log_sent = app.send_media_group(
                                                            chat_id=log_channel_nsfw,
                                                            media=nsfw_log_media_group,
                                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                        )
                                                        logger.info(f"[IMG LOG] Open copy album sent to NSFW channel: {len(nsfw_log_media_group)} items")
                                                    except Exception as fe:
                                                        logger.error(f"[IMG LOG] Failed to send open copy album to NSFW channel: {fe}")
                                                    
                                                    # Don't cache NSFW content
                                                    logger.info(f"[IMG LOG] NSFW content sent to both channels (paid + history), not cached")
                                                    
                                                elif nsfw_flag and not is_private_chat:
                                                    # NSFW content in groups -> LOGS_NSFW_ID only - send as album
                                                    log_channel = get_log_channel("image", nsfw=True, paid=False)
                                                    try:
                                                        # Create media group for NSFW log channel
                                                        nsfw_media_group = []
                                                        for _idx, _media_obj in enumerate(media_group):
                                                            caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                                            if isinstance(_media_obj, InputMediaPhoto):
                                                                nsfw_media_group.append(InputMediaPhoto(
                                                                    media=_media_obj.media,
                                                                    caption=caption,
                                                                    has_spoiler=True
                                                                ))
                                                            else:
                                                                nsfw_media_group.append(InputMediaVideo(
                                                                    media=_media_obj.media,
                                                                    caption=caption,
                                                                    duration=getattr(_media_obj, 'duration', None),
                                                                    width=getattr(_media_obj, 'width', None),
                                                                    height=getattr(_media_obj, 'height', None),
                                                                    thumb=getattr(_media_obj, 'thumb', None),
                                                                    has_spoiler=True
                                                                ))
                                                        
                                                        if nsfw_media_group:
                                                            # Only add caption to first item
                                                            if nsfw_media_group:
                                                                nsfw_media_group[0].caption = f"NSFW Content (Album {len(nsfw_media_group)} items)"
                                                            
                                                            app.send_media_group(chat_id=log_channel, media=nsfw_media_group)
                                                            logger.info(f"[IMG LOG] NSFW media album sent to NSFW channel: {len(nsfw_media_group)} items")
                                                        time.sleep(0.05)
                                                    except Exception as fe:
                                                        logger.error(f"[IMG LOG] send_media_group (fallback) failed for NSFW media: {fe}")
                                                    
                                                    # Don't cache NSFW content
                                                    logger.info(f"[IMG LOG] NSFW content sent to NSFW channel, not cached")
                                                    
                                                else:
                                                    # Regular content -> LOGS_IMG_ID and cache
                                                    log_channel = get_log_channel("image", nsfw=False, paid=False)
                                                    try:
                                                        # Create media group for regular log channel (open copy)
                                                        regular_log_media_group = []
                                                        # Prefer original first-item caption to preserve full formatting
                                                        original_caption = None
                                                        try:
                                                            if media_group and getattr(media_group[0], 'caption', None):
                                                                original_caption = media_group[0].caption
                                                        except Exception:
                                                            original_caption = None
                                                        # Fallback: previous constructed caption
                                                        if not original_caption:
                                                            bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                                            log_caption_lines = []
                                                            if tags_text_norm:
                                                                log_caption_lines.append(tags_text_norm)
                                                            log_caption_lines.append(f"{safe_get_messages(user_id).IMAGE_URL_CAPTION_MSG.format(url=url)} @{Config.BOT_NAME}")
                                                            # Add profile hashtag
                                                            profile_name = extract_profile_name(url)
                                                            if profile_name:
                                                                log_caption_lines.append(f"#{profile_name}")
                                                            log_caption = "\n".join(log_caption_lines)
                                                        else:
                                                            log_caption = original_caption
                                                        
                                                        for _idx, _media_obj in enumerate(media_group):
                                                            caption = log_caption if _idx == 0 else None  # Only first item gets caption
                                                            if isinstance(_media_obj, InputMediaPhoto):
                                                                regular_log_media_group.append(InputMediaPhoto(
                                                                    media=_media_obj.media,
                                                                    caption=caption
                                                                ))
                                                            else:
                                                                regular_log_media_group.append(InputMediaVideo(
                                                                    media=_media_obj.media,
                                                                    caption=caption,
                                                                    duration=getattr(_media_obj, 'duration', None),
                                                                    width=getattr(_media_obj, 'width', None),
                                                                    height=getattr(_media_obj, 'height', None),
                                                                    thumb=getattr(_media_obj, 'thumb', None)
                                                                ))
                                                        
                                                        # Send as album to regular log channel
                                                        regular_log_sent = app.send_media_group(
                                                            chat_id=log_channel,
                                                            media=regular_log_media_group,
                                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                        )
                                                        logger.info(f"[IMG LOG] Regular media album sent to IMG channel (fallback): {len(regular_log_media_group)} items")
                                                        
                                                        # Cache regular content
                                                        f_ids = [m.id for m in regular_log_sent]
                                                        logger.info(f"[IMG CACHE] Regular content cached with IDs (fallback): {f_ids}")
                                                    except Exception as fe:
                                                        logger.error(f"[IMG LOG] Failed to send regular media album to IMG channel (fallback): {fe}")
                                                        # Fallback to original ID if sending fails
                                                        f_ids.append(_mid)
                                                        time.sleep(0.05)
                                            except Exception as ce:
                                                logger.error(f"[IMG LOG] forward_messages (fallback) failed for id={_mid}: {ce}")
                                        album_index += 1
                                        # Only cache regular content (not NSFW)
                                        if f_ids and not nsfw_flag:
                                            logger.info(f"[IMG CACHE] Fallback album index={album_index} collected log_ids={f_ids}")
                                            _save_album_now(url, album_index, f_ids)
                                        elif nsfw_flag:
                                            logger.info(f"[IMG CACHE] Fallback: Skipping cache save for NSFW content, album index={album_index}")
                                        else:
                                            logger.error("[IMG CACHE] No log IDs collected in fallback; skipping cache save for this album")
                                except Exception as e_copy2:
                                    logger.error(f"[IMG CACHE] Unexpected error while copying fallback album to logs: {e_copy2}")

                        # Send non-groupable immediately
                        while others_buffer:
                            p, orig = others_buffer.pop(0)
                            try:
                                with open(p, 'rb') as f:
                                    attempts = 0
                                    last_exc = None
                                    while attempts < 5:
                                        try:
                                            sent_msg = app.send_document(
                                                user_id,
                                                document=f,
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                                message_thread_id=message_thread_id
                                            )
                                            break
                                        except FloodWait as fw:
                                            wait_s = int(getattr(fw, 'value', 0) or 0)
                                            logger.warning(f"FloodWait while send_document: waiting {wait_s}s and retrying (attempt {attempts+1}/5)")
                                            time.sleep(wait_s + 1)
                                            attempts += 1
                                            last_exc = fw
                                        except Exception as ex:
                                            last_exc = ex
                                            break
                                    if attempts and attempts >= 5 and last_exc is not None:
                                        raise last_exc
                                sent_message_ids.append(sent_msg.id)
                                total_sent += 1
                                update_status()
                                # Delete files immediately after sending (strict batching others)
                                try:
                                    if os.path.exists(p):
                                        # Delete file to prevent re-processing
                                        os.remove(p)
                                        logger.info(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_DELETED_FILE_LOG_MSG")
                                except Exception as e:
                                    logger.warning(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_FAILED_DELETE_LOG_MSG")
                                try:
                                    if os.path.exists(orig):
                                        # Delete file to prevent re-processing
                                        os.remove(orig)
                                        logger.info(f"[IMG BATCH OTHERS] Zeroed out original: {orig}")
                                except Exception as e:
                                    logger.warning(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_FAILED_ZERO_LOG_MSG")
                            except Exception as e:
                                logger.error(f"Failed to send document: {e}")

                        # Stop if limit reached (but not for admins)
                        if not is_admin and total_sent >= total_limit:
                            break

            # Flush remainder if no more ranges pending
            upper_cap = manual_end_cap or total_expected
            if (upper_cap and (total_sent >= upper_cap or current_start > upper_cap)) or (not is_admin and total_sent >= total_limit):
                # Send remaining media groups
                if photos_videos_buffer:
                    group = photos_videos_buffer[:batch_size]
                    media_group = []
                    for p, t, _orig in group:
                        if t == 'photo':
                            # No spoiler in groups, only in private chats for paid media
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            # Не ставим подпись тут, добавим теги только первому ниже
                            media_group.append(InputMediaPhoto(p, caption=None, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                        else:
                            # probe metadata
                            vinfo = _probe_video_info(p)
                            # generate thumbnail for better preview (old behavior for free media)
                            thumb = generate_video_thumbnail(p)
                            # No spoiler in groups, only in private chats for paid media
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            if thumb and os.path.exists(thumb):
                                media_group.append(InputMediaVideo(
                                    p,
                                    thumb=thumb,
                                    width=vinfo.get('width'),
                                    height=vinfo.get('height'),
                                    duration=vinfo.get('duration'),
                                    caption=None,
                                    has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                ))
                            else:
                                media_group.append(InputMediaVideo(
                                    p,
                                    width=vinfo.get('width'),
                                    height=vinfo.get('height'),
                                    duration=vinfo.get('duration'),
                                    caption=None,
                                    has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                ))
                    try:
                        # For paid media, only send in private chats (not groups/channels)
                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                        #  При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                        if hasattr(message, '_is_fake_message') and message._is_fake_message:
                            original_chat_id = getattr(message, '_original_chat_id', user_id)
                            # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                            is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                            logger.info(f"[IMG TAIL] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                        if nsfw_flag and is_private_chat:
                            # Send as paid media album (up to 10 media files)
                            sent = []  # Initialize sent variable
                            try:
                                # Convert media group to paid media format
                                paid_media_list = []
                                for m in media_group:
                                    if isinstance(m, InputMediaPhoto):
                                        paid_media_list.append(InputPaidMediaPhoto(media=m.media))
                                    else:
                                        # Ensure cover for paid media and pass explicit metadata
                                        media_path = m.media
                                        vinfo_paid = _probe_video_info(media_path)
                                        _cover = ensure_paid_cover_embedded(media_path, getattr(m, 'thumb', None))
                                        try:
                                            paid_media_list.append(InputPaidMediaVideo(
                                                    media=media_path,
                                                    cover=_cover,
                                                    width=vinfo_paid.get('width'),
                                                    height=vinfo_paid.get('height'),
                                                    duration=vinfo_paid.get('duration'),
                                                    supports_streaming=True
                                            ))
                                        except TypeError:
                                            paid_media_list.append(InputPaidMediaVideo(media=media_path))
                                
                                # Send as multiple paid media albums (max 10 files per album)
                                max_album_size = 10
                                for album_start in range(0, len(paid_media_list), max_album_size):
                                    album_end = min(album_start + max_album_size, len(paid_media_list))
                                    album_items = paid_media_list[album_start:album_end]
                                    
                                    logger.info(f"[IMG TAIL PAID] Sending paid media album {album_start//max_album_size + 1} with {len(album_items)} items")
                                    try:
                                        paid_msg = app.send_paid_media(
                                            user_id,
                                            media=album_items,
                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                            payload=str(Config.STAR_RECEIVER),
                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                        )
                                        
                                        if isinstance(paid_msg, list):
                                            sent.extend(paid_msg)
                                        elif paid_msg is not None:
                                            sent.append(paid_msg)
                                            
                                    except Exception as e:
                                        logger.error(f"[IMG TAIL PAID] send_paid_media album failed: {e}")
                                        # Ensure sent variable is initialized
                                        if 'sent' not in locals():
                                            sent = []
                                        # Fallback: send individually as paid media
                                        for paid_media in album_items:
                                            try:
                                                individual_msg = app.send_paid_media(
                                                    user_id,
                                                    media=[paid_media],
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                                if isinstance(individual_msg, list):
                                                    sent.extend(individual_msg)
                                                elif individual_msg is not None:
                                                    sent.append(individual_msg)
                                            except Exception as e2:
                                                logger.error(f"[IMG TAIL PAID] Individual paid media failed: {e2}")
                                
                                # Note: LOGS_PAID_ID forwarding is handled in main logic, not in tail
                                
                                # Send open copy to LOGS_NSFW_ID for history
                                try:
                                    # Create media group for open copy with proper caption
                                    open_media_group = []
                                    bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                    caption_lines = []
                                    if tags_text_norm:
                                        caption_lines.append(tags_text_norm)
                                    caption_lines.append(f"[Image URL]({url}) @{Config.BOT_NAME}")
                                    full_caption = "\n".join(caption_lines)
                                    
                                    for idx, m in enumerate(media_group):
                                        caption = full_caption if idx == 0 else None  # Only first item gets caption
                                        if isinstance(m, InputMediaPhoto):
                                            open_media_group.append(InputMediaPhoto(
                                                media=m.media,
                                                caption=caption,
                                                has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                            ))
                                        else:
                                            open_media_group.append(InputMediaVideo(
                                                media=m.media,
                                                thumb=getattr(m, 'thumb', None),
                                                width=getattr(m, 'width', None),
                                                height=getattr(m, 'height', None),
                                                duration=getattr(m, 'duration', None),
                                                caption=caption,
                                                has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                                            ))
                                    
                                    # Send open copy as album to NSFW channel
                                    log_channel_nsfw = get_log_channel("video", nsfw=True)
                                    if log_channel_nsfw:
                                        open_sent = app.send_media_group(
                                            chat_id=log_channel_nsfw,
                                            media=open_media_group,
                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                        )
                                        logger.info(f"[IMG LOG] Open copy album sent to LOGS_NSFW_ID for history: {len(open_media_group)} items")
                                except Exception as e:
                                    logger.error(f"[IMG LOG] Failed to send open copy album to LOGS_NSFW_ID: {e}")
                                    
                            except Exception as e:
                                logger.error(f"Failed to send paid media album in tail: {e}")
                                # Fallback to individual sending
                                sent = []
                                for m in media_group:
                                    try:
                                        if isinstance(m, InputMediaPhoto):
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=[InputPaidMediaPhoto(media=m.media)],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                            )
                                        else:
                                            # Ensure cover for video
                                            video_path = m.media if not hasattr(m.media, 'name') else m.media.name
                                            _cover = ensure_paid_cover_embedded(video_path, getattr(m, 'thumb', None))
                                            try:
                                                paid_msg = app.send_paid_media(
                                                    user_id,
                                                    media=[InputPaidMediaVideo(media=m.media, cover=_cover)],
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                            except TypeError:
                                                paid_msg = app.send_paid_media(
                                                    user_id,
                                                    media=[InputPaidMediaVideo(media=m.media)],
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                )
                                        if isinstance(paid_msg, list):
                                            sent.extend(paid_msg)
                                        elif paid_msg is not None:
                                            sent.append(paid_msg)
                                    except Exception as e:
                                        logger.error(f"Failed to send individual paid media: {e}")
                        else:
                            # In groups/channels or non-NSFW content, send as regular media group
                            attempts = 0
                            last_exc = None
                            while attempts < 5:
                                try:
                                    # Ensure album-level caption: put user tags on the first item only
                                    try:
                                        if media_group:
                                            _first = media_group[0]
                                            _exist = getattr(_first, 'caption', None) or ''
                                            
                                            # Create user caption with emoji numbers and dates
                                            profile_name = extract_profile_name(url)
                                            site_name = extract_site_name(url)
                                            user_caption = create_album_caption_with_dates(media_group, url, tags_text_norm, profile_name, site_name, user_id)
                                            
                                            _sep = (' ' if _exist and not _exist.endswith('\n') else '')
                                            _first.caption = (_exist + _sep + user_caption).strip()
                                            # Avoid duplicating tags on the rest of items
                                            for _itm in media_group[1:]:
                                                if getattr(_itm, 'caption', None) == tags_text_norm:
                                                    _itm.caption = None
                                    except Exception as _e:
                                        logger.debug(f"{LoggerMsg.IMG_TAIL_ALBUM_CAPTION_NORMALIZATION_SKIPPED_LOG_MSG}")
                                    sent = app.send_media_group(
                                        chat_id,
                                        media=media_group,
                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                        message_thread_id=message_thread_id
                                    )
                                    break
                                except FloodWait as fw:
                                    wait_s = int(getattr(fw, 'value', 0) or 0)
                                    logger.warning(f"FloodWait while send_media_group (tail): waiting {wait_s}s and retrying (attempt {attempts+1}/5)")
                                    time.sleep(wait_s + 1)
                                    attempts += 1
                                    last_exc = fw
                                except Exception as ex:
                                    last_exc = ex
                                    break
                            if attempts and attempts >= 5 and last_exc is not None:
                                raise last_exc
                        sent_message_ids.extend([m.id for m in sent])
                        total_sent += len(media_group)
                        # Forward tail album and save forwarded IDs
                        try:
                            orig_ids2 = [m.id for m in sent]
                            logger.info(f"[IMG CACHE] Copying tail album to logs, orig_ids={orig_ids2}")
                            f_ids = []
                            
                            # Determine correct log channel based on media type and chat type
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            is_paid_media = nsfw_flag and is_private_chat
                            
                            if is_paid_media:
                                # For NSFW content in private chat, send to both channels but don't cache
                                # Add delay to allow Telegram to process paid media before sending to log channels
                                time.sleep(2.0)
                                
                                # Send to LOGS_PAID_ID (for paid content) - forward the paid messages
                                log_channel_paid = get_log_channel("image", nsfw=False, paid=True)
                                try:
                                    for _mid in orig_ids2:
                                        app.forward_messages(chat_id=log_channel_paid, from_chat_id=user_id, message_ids=[_mid])
                                        time.sleep(0.05)
                                except Exception as fe:
                                    logger.error(f"[IMG LOG] forward_messages (tail) failed for paid media: {fe}")
                                
                                # Send to LOGS_NSFW_ID (for history) - send open copy as album
                                log_channel_nsfw = get_log_channel("image", nsfw=True, paid=False)
                                try:
                                    # Create media group for NSFW log channel (open copy)
                                    nsfw_log_media_group = []
                                    for _idx, _media_obj in enumerate(media_group):
                                        caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                        if isinstance(_media_obj, InputMediaPhoto):
                                            nsfw_log_media_group.append(InputMediaPhoto(
                                                media=_media_obj.media,
                                                caption=caption
                                            ))
                                        else:
                                            nsfw_log_media_group.append(InputMediaVideo(
                                                media=_media_obj.media,
                                                caption=caption,
                                                duration=getattr(_media_obj, 'duration', None),
                                                width=getattr(_media_obj, 'width', None),
                                                height=getattr(_media_obj, 'height', None),
                                                thumb=getattr(_media_obj, 'thumb', None)
                                            ))
                                    
                                    # Send as album to NSFW log channel
                                    nsfw_log_sent = app.send_media_group(
                                        chat_id=log_channel_nsfw,
                                        media=nsfw_log_media_group,
                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                    )
                                    logger.info(f"[IMG LOG] Open copy album sent to NSFW channel: {len(nsfw_log_media_group)} items")
                                except Exception as fe:
                                    logger.error(f"[IMG LOG] Failed to send open copy album to NSFW channel: {fe}")
                                
                                # Don't cache NSFW content
                                logger.info(f"[IMG LOG] NSFW content sent to both channels (paid + history), not cached")
                                
                            elif nsfw_flag and not is_private_chat:
                                # NSFW content in groups -> LOGS_NSFW_ID only - send as album
                                log_channel = get_log_channel("image", nsfw=True, paid=False)
                                try:
                                    # Create media group for NSFW log channel
                                    nsfw_media_group = []
                                    for _idx, _media_obj in enumerate(media_group):
                                        caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                        if isinstance(_media_obj, InputMediaPhoto):
                                            nsfw_media_group.append(InputMediaPhoto(
                                                media=_media_obj.media,
                                                caption=caption,
                                                has_spoiler=True
                                            ))
                                        else:
                                            nsfw_media_group.append(InputMediaVideo(
                                                media=_media_obj.media,
                                                caption=caption,
                                                duration=getattr(_media_obj, 'duration', None),
                                                width=getattr(_media_obj, 'width', None),
                                                height=getattr(_media_obj, 'height', None),
                                                thumb=getattr(_media_obj, 'thumb', None),
                                                has_spoiler=True
                                            ))
                                    
                                    if nsfw_media_group:
                                        # Only add caption to first item
                                        if nsfw_media_group:
                                            nsfw_media_group[0].caption = f"NSFW Content (Album {len(nsfw_media_group)} items)"
                                        
                                        app.send_media_group(chat_id=log_channel, media=nsfw_media_group)
                                        logger.info(f"[IMG LOG] NSFW media album sent to NSFW channel: {len(nsfw_media_group)} items")
                                except Exception as fe:
                                    logger.error(f"[IMG LOG] send_media_group (tail) failed for NSFW media: {fe}")
                                
                                # Don't cache NSFW content
                                logger.info(f"[IMG LOG] NSFW content sent to NSFW channel, not cached")
                                
                            else:
                                # Regular content -> LOGS_IMG_ID and cache
                                log_channel = get_log_channel("image", nsfw=False, paid=False)
                                try:
                                    # Create media group for regular log channel (open copy)
                                    regular_log_media_group = []
                                    # Prefer original first-item caption to preserve full formatting (dates/emojis/tags)
                                    original_caption = None
                                    try:
                                        if media_group and getattr(media_group[0], 'caption', None):
                                            original_caption = media_group[0].caption
                                    except Exception:
                                        original_caption = None
                                    # Fallback: construct caption as before
                                    if not original_caption:
                                        bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                        log_caption_lines = []
                                        if tags_text_norm:
                                            log_caption_lines.append(tags_text_norm)
                                        log_caption_lines.append(f"{safe_get_messages(user_id).IMAGE_URL_CAPTION_MSG.format(url=url)} @{Config.BOT_NAME}")
                                        log_caption = "\n".join(log_caption_lines)
                                    else:
                                        log_caption = original_caption
                                    
                                    for _idx, _media_obj in enumerate(media_group):
                                        caption = log_caption if _idx == 0 else None  # Only first item gets caption
                                        if isinstance(_media_obj, InputMediaPhoto):
                                            regular_log_media_group.append(InputMediaPhoto(
                                                media=_media_obj.media,
                                                caption=caption
                                            ))
                                        else:
                                            regular_log_media_group.append(InputMediaVideo(
                                                media=_media_obj.media,
                                                caption=caption,
                                                duration=getattr(_media_obj, 'duration', None),
                                                width=getattr(_media_obj, 'width', None),
                                                height=getattr(_media_obj, 'height', None),
                                                thumb=getattr(_media_obj, 'thumb', None)
                                            ))
                                    
                                    # Send as album to regular log channel
                                    regular_log_sent = app.send_media_group(
                                        chat_id=log_channel,
                                        media=regular_log_media_group,
                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                    )
                                    logger.info(f"[IMG LOG] Regular media album sent to IMG channel (tail): {len(regular_log_media_group)} items")
                                    
                                    # Cache regular content
                                    f_ids = [m.id for m in regular_log_sent]
                                    logger.info(f"[IMG CACHE] Regular content cached with IDs (tail): {f_ids}")
                                except Exception as fe:
                                    logger.error(f"[IMG LOG] Failed to send regular media album to IMG channel (tail): {fe}")
                                    # Fallback to original IDs if sending fails
                                    f_ids = orig_ids2
                            album_index += 1
                            # Only cache regular content (not NSFW)
                            if f_ids and not nsfw_flag:
                                logger.info(f"[IMG CACHE] Tail album index={album_index} collected log_ids={f_ids}")
                                _save_album_now(url, album_index, f_ids)
                            elif nsfw_flag:
                                logger.info(f"[IMG CACHE] Tail: Skipping cache save for NSFW content, album index={album_index}")
                            else:
                                logger.error("[IMG CACHE] No log IDs collected in tail; skipping cache save for this album")
                        except Exception as e_tail:
                            logger.error(f"[IMG CACHE] Unexpected error while copying tail album to logs: {e_tail}")
                        # Delete files immediately after sending (strict batching fallback)
                        for p, _t, orig in group:
                            try:
                                if os.path.exists(p):
                                    # Delete file to prevent re-processing
                                    os.remove(p)
                                    logger.info(f"[IMG BATCH FALLBACK] Deleted file: {p}")
                            except Exception as e:
                                logger.warning(f"[IMG BATCH FALLBACK] Failed to delete {p}: {e}")
                            try:
                                if os.path.exists(orig):
                                    # Delete file to prevent re-processing
                                    os.remove(orig)
                                    logger.info(f"[IMG BATCH FALLBACK] Deleted original: {orig}")
                            except Exception as e:
                                logger.warning(f"[IMG BATCH FALLBACK] Failed to delete original {orig}: {e}")
                    except Exception:
                        tmp_ids2 = []
                        for p, t, orig in group:
                            try:
                                with open(p, 'rb') as f:
                                    if t == 'photo':
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        attempts = 0
                                        last_exc = None
                                        while attempts < 5:
                                            try:
                                                if nsfw_flag and is_private_chat:
                                                    sent_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[InputPaidMediaPhoto(media=f)],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                    )
                                                else:
                                                    sent_msg = app.send_photo(
                                                        user_id,
                                                        photo=f,
                                                        caption=(tags_text_norm or ''),
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                                        message_thread_id=message_thread_id
                                                    )
                                                break
                                            except FloodWait as fw:
                                                wait_s = int(getattr(fw, 'value', 0) or 0)
                                                logger.warning(f"FloodWait while send_photo (tail): waiting {wait_s}s and retrying (attempt {attempts+1}/5)")
                                                time.sleep(wait_s + 1)
                                                attempts += 1
                                                last_exc = fw
                                            except Exception as ex:
                                                last_exc = ex
                                                break
                                        if attempts and attempts >= 5 and last_exc is not None:
                                            raise last_exc
                                    else:
                                        # try generate thumbnail
                                        thumb = generate_video_thumbnail(p)
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        attempts = 0
                                        last_exc = None
                                        while attempts < 5:
                                            try:
                                                if nsfw_flag and is_private_chat:
                                                    _cover = ensure_paid_cover_embedded(p, thumb)
                                                    try:
                                                        media_item = InputPaidMediaVideo(media=f, cover=_cover)
                                                    except TypeError:
                                                        media_item = InputPaidMediaVideo(media=f)
                                                    sent_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[media_item],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                                    )
                                                else:
                                                    sent_msg = app.send_video(
                                                        user_id,
                                                        video=f,
                                                        thumb=thumb if thumb and os.path.exists(thumb) else None,
                                                        caption=(tags_text_norm or ''),
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                                        message_thread_id=message_thread_id
                                                    )
                                                break
                                            except FloodWait as fw:
                                                wait_s = int(getattr(fw, 'value', 0) or 0)
                                                logger.warning(f"FloodWait while send_video (tail): waiting {wait_s}s and retrying (attempt {attempts+1}/5)")
                                                time.sleep(wait_s + 1)
                                                attempts += 1
                                                last_exc = fw
                                            except Exception as ex:
                                                last_exc = ex
                                                break
                                        if attempts and attempts >= 5 and last_exc is not None:
                                            raise last_exc
                                    sent_message_ids.append(sent_msg.id)
                                    tmp_ids2.append(sent_msg.id)
                                    total_sent += 1
                                # Delete files immediately after sending (strict batching individual)
                                try:
                                    if os.path.exists(p):
                                        # Delete file to prevent re-processing
                                        os.remove(p)
                                        logger.info(f"[IMG BATCH INDIVIDUAL] Deleted file: {p}")
                                except Exception as e:
                                    logger.warning(f"[IMG BATCH INDIVIDUAL] Failed to delete {p}: {e}")
                                try:
                                    if os.path.exists(orig):
                                        # Delete file to prevent re-processing
                                        os.remove(orig)
                                        logger.info(f"[IMG BATCH INDIVIDUAL] Deleted original: {orig}")
                                except Exception as e:
                                    logger.warning(f"[IMG BATCH INDIVIDUAL] Failed to delete original {orig}: {e}")
                            except Exception:
                                pass
                        # Forward tail fallback album and save forwarded IDs
                        try:
                            if tmp_ids2:
                                logger.info(f"[IMG CACHE] Copying tail-fallback album to logs, orig_ids={tmp_ids2}")
                                f_ids = []
                                
                                # Determine correct log channel based on media type and chat type
                                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                is_paid_media = nsfw_flag and is_private_chat
                                
                                if is_paid_media:
                                    # For NSFW content in private chat, send to both channels but don't cache
                                    # Add delay to allow Telegram to process paid media before sending to log channels
                                    time.sleep(2.0)
                                    
                                    # Send to LOGS_PAID_ID (for paid content) - forward the paid messages
                                    log_channel_paid = get_log_channel("image", nsfw=False, paid=True)
                                    try:
                                        for _mid in tmp_ids2:
                                            app.forward_messages(chat_id=log_channel_paid, from_chat_id=user_id, message_ids=[_mid])
                                            time.sleep(0.05)
                                    except Exception as fe:
                                        logger.error(f"[IMG LOG] forward_messages (tail-fallback) failed for paid media: {fe}")
                                    
                                    # Send to LOGS_NSFW_ID (for history) - send open copy as album
                                    log_channel_nsfw = get_log_channel("image", nsfw=True, paid=False)
                                    try:
                                        # Create media group for NSFW log channel (open copy)
                                        nsfw_log_media_group = []
                                        for _idx, _media_obj in enumerate(media_group):
                                            caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                            if isinstance(_media_obj, InputMediaPhoto):
                                                nsfw_log_media_group.append(InputMediaPhoto(
                                                    media=_media_obj.media,
                                                    caption=caption
                                                ))
                                            else:
                                                nsfw_log_media_group.append(InputMediaVideo(
                                                    media=_media_obj.media,
                                                    caption=caption,
                                                    duration=getattr(_media_obj, 'duration', None),
                                                    width=getattr(_media_obj, 'width', None),
                                                    height=getattr(_media_obj, 'height', None),
                                                    thumb=getattr(_media_obj, 'thumb', None)
                                                ))
                                        
                                        # Send as album to NSFW log channel
                                        nsfw_log_sent = app.send_media_group(
                                            chat_id=log_channel_nsfw,
                                            media=nsfw_log_media_group,
                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                        )
                                        logger.info(f"[IMG LOG] Open copy album sent to NSFW channel: {len(nsfw_log_media_group)} items")
                                    except Exception as fe:
                                        logger.error(f"[IMG LOG] Failed to send open copy album to NSFW channel: {fe}")
                                    
                                    # Don't cache NSFW content
                                    logger.info(f"[IMG LOG] NSFW content sent to both channels (paid + history), not cached")
                                    
                                elif nsfw_flag and not is_private_chat:
                                    # NSFW content in groups -> LOGS_NSFW_ID only - send as album
                                    log_channel = get_log_channel("image", nsfw=True, paid=False)
                                    try:
                                        # Create media group for NSFW log channel
                                        nsfw_media_group = []
                                        for _idx, _media_obj in enumerate(media_group):
                                            caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                            if isinstance(_media_obj, InputMediaPhoto):
                                                nsfw_media_group.append(InputMediaPhoto(
                                                    media=_media_obj.media,
                                                    caption=caption,
                                                    has_spoiler=True
                                                ))
                                            else:
                                                nsfw_media_group.append(InputMediaVideo(
                                                    media=_media_obj.media,
                                                    caption=caption,
                                                    duration=getattr(_media_obj, 'duration', None),
                                                    width=getattr(_media_obj, 'width', None),
                                                    height=getattr(_media_obj, 'height', None),
                                                    thumb=getattr(_media_obj, 'thumb', None),
                                                    has_spoiler=True
                                                ))
                                        
                                        if nsfw_media_group:
                                            # Only add caption to first item
                                            if nsfw_media_group:
                                                nsfw_media_group[0].caption = f"NSFW Content (Album {len(nsfw_media_group)} items)"
                                            
                                            app.send_media_group(chat_id=log_channel, media=nsfw_media_group)
                                            logger.info(f"[IMG LOG] NSFW media album sent to NSFW channel: {len(nsfw_media_group)} items")
                                    except Exception as fe:
                                        logger.error(f"[IMG LOG] send_media_group (tail-fallback) failed for NSFW media: {fe}")
                                    
                                    # Don't cache NSFW content
                                    logger.info(f"[IMG LOG] NSFW content sent to NSFW channel, not cached")
                                    
                                else:
                                    # Regular content -> LOGS_IMG_ID and cache
                                    log_channel = get_log_channel("image", nsfw=False, paid=False)
                                    try:
                                        # Create media group for regular log channel (open copy)
                                        regular_log_media_group = []
                                        for _idx, _media_obj in enumerate(media_group):
                                            caption = (tags_text_norm or "") if _idx == 0 else None  # Only first item gets caption
                                            if isinstance(_media_obj, InputMediaPhoto):
                                                regular_log_media_group.append(InputMediaPhoto(
                                                    media=_media_obj.media,
                                                    caption=caption
                                                ))
                                            else:
                                                regular_log_media_group.append(InputMediaVideo(
                                                    media=_media_obj.media,
                                                    caption=caption,
                                                    duration=getattr(_media_obj, 'duration', None),
                                                    width=getattr(_media_obj, 'width', None),
                                                    height=getattr(_media_obj, 'height', None),
                                                    thumb=getattr(_media_obj, 'thumb', None)
                                                ))
                                        
                                        # Send as album to regular log channel
                                        regular_log_sent = app.send_media_group(
                                            chat_id=log_channel,
                                            media=regular_log_media_group,
                                            reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                                        )
                                        logger.info(f"[IMG LOG] Regular media album sent to IMG channel (tail-fallback): {len(regular_log_media_group)} items")
                                        
                                        # Cache regular content
                                        f_ids = [m.id for m in regular_log_sent]
                                        logger.info(f"[IMG CACHE] Regular content cached with IDs (tail-fallback): {f_ids}")
                                    except Exception as fe:
                                        logger.error(f"[IMG LOG] Failed to send regular media album to IMG channel (tail-fallback): {fe}")
                                        # Fallback to original IDs if sending fails
                                        f_ids = tmp_ids2
                                album_index += 1
                                # Only cache regular content (not NSFW)
                                if f_ids and not nsfw_flag:
                                    logger.info(f"[IMG CACHE] Tail-fallback album index={album_index} collected log_ids={f_ids}")
                                    _save_album_now(url, album_index, f_ids)
                                elif nsfw_flag:
                                    logger.info(f"[IMG CACHE] Tail-fallback: Skipping cache save for NSFW content, album index={album_index}")
                                else:
                                    logger.error("[IMG CACHE] No log IDs collected in tail-fallback; skipping cache save for this album")
                        except Exception as e_tail2:
                            logger.error(f"[IMG CACHE] Unexpected error while copying tail-fallback album to logs: {e_tail2}")
                    photos_videos_buffer = photos_videos_buffer[len(group):]

                # Send remaining others
                while others_buffer:
                    p, orig = others_buffer.pop(0)
                    try:
                        with open(p, 'rb') as f:
                            sent_msg = app.send_document(
                                user_id,
                                document=f,
                                reply_parameters=ReplyParameters(message_id=get_reply_message_id(message)),
                                message_thread_id=message_thread_id
                            )
                        sent_message_ids.append(sent_msg.id)
                        total_sent += 1
                        # Delete files immediately after sending (strict batching others)
                        try:
                            if os.path.exists(p):
                                # Delete file to prevent re-processing
                                os.remove(p)
                                logger.info(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_DELETED_FILE_LOG_MSG")
                        except Exception as e:
                            logger.warning(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_FAILED_DELETE_LOG_MSG")
                        try:
                            if os.path.exists(orig):
                                # Delete file to prevent re-processing
                                os.remove(orig)
                                logger.info(f"[IMG BATCH OTHERS] Zeroed out original: {orig}")
                        except Exception as e:
                            logger.warning(f"safe_get_messages(user_id).IMG_BATCH_OTHERS_FAILED_ZERO_LOG_MSG")
                    except Exception:
                        pass
                # Final update and replace header to 'Download complete'
                final_expected = total_expected or min(total_downloaded, total_limit)
                try:
                    if not completion_sent:
                        safe_edit_message_text(
                            user_id,
                            status_msg.id,
                            safe_get_messages(user_id).DOWNLOAD_COMPLETE_MSG +
                            f"{safe_get_messages(user_id).DOWNLOADED_STATUS_MSG} <b>{total_downloaded}</b> / <b>{final_expected}</b>\n"
                            f"{safe_get_messages(user_id).SENT_STATUS_MSG} <b>{total_sent}</b>",
                            parse_mode=enums.ParseMode.HTML,
                        )
                        completion_sent = True
                except Exception:
                    pass
                return

            if not is_admin and total_sent >= total_limit:
                break

            # Check if we've been waiting too long for files in current range
            # Only apply this timeout if we haven't found any files in this range yet
            if time.time() - range_start_time > max_range_wait_time:
                logger.warning(f"[IMG BATCH] Range timeout reached ({max_range_wait_time}s), no new files found in current range")
                break

            # Check if we found any new files in this search iteration
            if files_found_in_this_search == 0:
                consecutive_empty_searches += 1
                logger.info(f"[IMG BATCH] No new files found in search iteration {consecutive_empty_searches}/{max_consecutive_empty_searches}")
                if consecutive_empty_searches >= max_consecutive_empty_searches:
                    logger.info(f"[IMG BATCH] Exiting loop after {consecutive_empty_searches} consecutive empty searches")
                    break
            else:
                consecutive_empty_searches = 0  # Reset counter when we find files
                logger.info(f"[IMG BATCH] Found {files_found_in_this_search} new files, resetting empty search counter")

            time.sleep(0.5)

        # Update status to show completion
        try:
            if not completion_sent:
                final_expected = total_expected or min(total_downloaded, total_limit)
                safe_edit_message_text(
                    user_id,
                    status_msg.id,
                    safe_get_messages(user_id).DOWNLOAD_COMPLETE_MSG +
                    f"{safe_get_messages(user_id).DOWNLOADED_STATUS_MSG} <b>{total_downloaded}</b> / <b>{final_expected}</b>\n"
                    f"{safe_get_messages(user_id).SENT_STATUS_MSG} <b>{total_sent}</b>",
                    parse_mode=enums.ParseMode.HTML,
                )
                completion_sent = True
        except Exception:
            pass
        if completion_sent:
            return

        # Send remaining files in buffer as final album
        if photos_videos_buffer:
            media_group = []
            for p, t, _orig in photos_videos_buffer:
                if t == 'photo':
                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                    media_group.append(InputMediaPhoto(p, caption=None, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                else:
                    vinfo = _probe_video_info(p)
                    thumb = generate_video_thumbnail(p)
                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                    if thumb and os.path.exists(thumb):
                        media_group.append(InputMediaVideo(
                            p,
                            thumb=thumb,
                            width=vinfo.get('width'),
                            height=vinfo.get('height'),
                            duration=vinfo.get('duration'),
                            caption=None,
                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                        ))
                    else:
                        media_group.append(InputMediaVideo(
                            p,
                            width=vinfo.get('width'),
                            height=vinfo.get('height'),
                            duration=vinfo.get('duration'),
                            caption=None,
                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)
                        ))
            
            if media_group:
                try:
                    # Add caption to first item
                    if media_group:
                        _first = media_group[0]
                        if hasattr(_first, 'caption'):
                            # Create user caption with emoji numbers and dates
                            profile_name = extract_profile_name(url)
                            site_name = extract_site_name(url)
                            user_caption = create_album_caption_with_dates(media_group, url, tags_text_norm, profile_name, site_name, user_id)
                            _first.caption = user_caption
                        # Clear captions from other items
                        for _itm in media_group[1:]:
                            if hasattr(_itm, 'caption'):
                                _itm.caption = None
                    
                    sent = app.send_media_group(
                        user_id,
                        media=media_group,
                        reply_parameters=ReplyParameters(message_id=get_reply_message_id(message))
                    )
                    sent_message_ids.extend([m.id for m in sent])
                    total_sent += len(media_group)
                    
                    # Forward to logs and cache
                    try:
                        orig_ids = [m.id for m in sent]
                        f_ids = []
                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                        is_paid_media = nsfw_flag and is_private_chat
                        
                        for _mid in orig_ids:
                            try:
                                if is_paid_media:
                                    log_channel_paid = get_log_channel("image", nsfw=False, paid=True)
                                    try:
                                        _sent = app.forward_messages(log_channel_paid, user_id, [_mid])
                                        f_ids.append(_sent.id if not isinstance(_sent, list) else _sent[0].id)
                                        time.sleep(0.05)
                                    except Exception as fe:
                                        logger.error(f"[IMG CACHE] forward_messages failed for paid media id={_mid}: {fe}")
                                        f_ids.append(_mid)
                                        time.sleep(0.05)
                                else:
                                    log_channel = get_log_channel("image", nsfw=nsfw_flag, paid=False)
                                    try:
                                        _sent = app.forward_messages(log_channel, user_id, [_mid])
                                        f_ids.append(_sent.id if not isinstance(_sent, list) else _sent[0].id)
                                        time.sleep(0.05)
                                    except Exception as fe:
                                        logger.error(f"[IMG CACHE] forward_messages failed for regular media id={_mid}: {fe}")
                                        f_ids.append(_mid)
                                        time.sleep(0.05)
                            except Exception as ce:
                                logger.error(f"[IMG LOG] forward_messages failed for id={_mid}: {ce}")
                        
                        album_index += 1
                        if f_ids and not nsfw_flag:
                            _save_album_now(url, album_index, f_ids)
                    except Exception as e_copy:
                        logger.error(f"[IMG CACHE] Unexpected error while copying final album to logs: {e_copy}")
                    
                    # Delete files immediately after sending (strict batching final)
                    for p, _t, orig in photos_videos_buffer:
                        try:
                            if os.path.exists(p):
                                # Delete file to prevent re-processing
                                os.remove(p)
                                logger.info(f"[IMG BATCH FINAL] Deleted file: {p}")
                            if os.path.exists(orig):
                                # Delete file to prevent re-processing
                                os.remove(orig)
                                logger.info(f"[IMG BATCH FINAL] Deleted original: {orig}")
                        except Exception as e:
                            logger.warning(f"[IMG BATCH FINAL] Failed to delete files: {e}")
                    
                    photos_videos_buffer = []
                except Exception as e:
                    logger.error(f"Failed to send final media group: {e}")

        # Messages are already forwarded to log channels during caching process above

        # Cleanup files: удаляем только нулевые плейсхолдеры (уже отправленные),
        # чтобы не потерять неотправленные файлы при FLOOD_WAIT
        try:
            for file_path in files_to_cleanup:
                try:
                    if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                        file_dir = os.path.dirname(file_path)
                        os.remove(file_path)
                        if os.path.exists(file_dir) and not os.listdir(file_dir):
                            os.rmdir(file_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up file {file_path}: {e}")
        except Exception:
            pass

        # Final cleanup: remove all media files from user directory
        try:
            logger.info(f"safe_get_messages(user_id).IMG_CLEANUP_START_LOG_MSG")
            if os.path.exists(run_dir):
                for root, dirs, files in os.walk(run_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Remove all media files (including zero-size placeholders)
                            if file.lower().endswith((
                                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
                                '.mp4', '.m4v', '.avi', '.mov', '.mkv', '.webm', '.flv',
                                '.mp3', '.wav', '.ogg', '.m4a',
                                '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z'
                            )):
                                os.remove(file_path)
                                logger.info(f"safe_get_messages(user_id).IMG_CLEANUP_REMOVED_FILE_LOG_MSG")
                        except Exception as e:
                            logger.warning(f"safe_get_messages(user_id).IMG_CLEANUP_FAILED_REMOVE_LOG_MSG")
                    
                    # Remove empty directories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if os.path.exists(dir_path) and not os.listdir(dir_path):
                                os.rmdir(dir_path)
                                logger.info(f"safe_get_messages(user_id).IMG_CLEANUP_REMOVED_DIR_LOG_MSG")
                        except Exception as e:
                            logger.warning(f"[IMG CLEANUP] Failed to remove directory {dir_path}: {e}")
            
            # Remove the entire run directory if empty
            try:
                if os.path.exists(run_dir) and not os.listdir(run_dir):
                    os.rmdir(run_dir)
                    logger.info(f"[IMG CLEANUP] Removed empty run directory: {run_dir}")
            except Exception as e:
                logger.warning(f"[IMG CLEANUP] Failed to remove run directory {run_dir}: {e}")
                
            logger.info(f"[IMG CLEANUP] Final cleanup completed")
        except Exception as e:
            logger.warning(f"[IMG CLEANUP] Failed to perform final cleanup: {e}")

        # Remove protection file after successful download
        from HELPERS.filesystem_hlp import remove_protection_file
        remove_protection_file(run_dir)
        
        send_to_logger(message, LoggerMsg.STREAMED_AND_SENT_MEDIA.format(total_sent=total_sent, url=url))
            
    except Exception as e:
        logger.error(f"Error in image command: {e}")
        
        # Clean up only the specific media files that were downloaded on general error
        try:
            # Try to find and clean up any recently downloaded files
            current_time = time.time()
            gallery_dl_dir = "gallery-dl"
            if os.path.exists(gallery_dl_dir):
                for root, _, files in os.walk(gallery_dl_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_time = os.path.getctime(file_path)
                        time_diff = current_time - file_time
                        # Clean up files created in the last 5 minutes
                        if time_diff and time_diff < 300:
                            try:
                                # Check if file still exists before trying to remove it
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    logger.info(f"Cleaned up file after general error: {file_path}")
                                    
                                    # If directory is empty after removing file, remove it too
                                    try:
                                        if os.path.exists(root) and not os.listdir(root):
                                            os.rmdir(root)
                                            logger.info(f"Removed empty directory after general error: {root}")
                                    except:
                                        pass  # Directory not empty or other error
                                else:
                                    logger.info(f"File already removed after general error: {file_path}")
                            except Exception as e:
                                logger.warning(f"Failed to clean up file after general error {file_path}: {e}")
        except Exception as cleanup_e:
            logger.warning(f"Failed to clean up downloaded files after general error: {cleanup_e}")
        
        # Final cleanup on error: remove all media files from user directory
        try:
            logger.info(f"[IMG CLEANUP ERROR] Starting final cleanup of user directory: {run_dir}")
            if os.path.exists(run_dir):
                for root, dirs, files in os.walk(run_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Remove all media files (including zero-size placeholders)
                            if file.lower().endswith((
                                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
                                '.mp4', '.m4v', '.avi', '.mov', '.mkv', '.webm', '.flv',
                                '.mp3', '.wav', '.ogg', '.m4a',
                                '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z'
                            )):
                                os.remove(file_path)
                                logger.info(f"[IMG CLEANUP ERROR] Removed file: {file_path}")
                        except Exception as e:
                            logger.warning(f"[IMG CLEANUP ERROR] Failed to remove {file_path}: {e}")
                    
                    # Remove empty directories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if os.path.exists(dir_path) and not os.listdir(dir_path):
                                os.rmdir(dir_path)
                                logger.info(f"[IMG CLEANUP ERROR] Removed empty directory: {dir_path}")
                        except Exception as e:
                            logger.warning(f"[IMG CLEANUP ERROR] Failed to remove directory {dir_path}: {e}")
            
            # Remove the entire run directory if empty
            try:
                if os.path.exists(run_dir) and not os.listdir(run_dir):
                    os.rmdir(run_dir)
                    logger.info(f"[IMG CLEANUP ERROR] Removed empty run directory: {run_dir}")
            except Exception as e:
                logger.warning(f"[IMG CLEANUP ERROR] Failed to remove run directory {run_dir}: {e}")
                
            logger.info(f"[IMG CLEANUP ERROR] Final cleanup completed")
        except Exception as cleanup_final_e:
            logger.warning(f"[IMG CLEANUP ERROR] Failed to perform final cleanup: {cleanup_final_e}")
        
        safe_edit_message_text(
            user_id, status_msg.id,
            safe_get_messages(user_id).ERROR_OCCURRED_MSG.format(url=url, error=str(e)),
            parse_mode=enums.ParseMode.HTML
        )
        from HELPERS.logger import send_error_to_user
        send_error_to_user(message, safe_get_messages(user_id).ERROR_OCCURRED_MSG.format(url=url, error=str(e)))
        log_error_to_channel(message, LoggerMsg.IMAGE_COMMAND_ERROR.format(url=url, error=e), url)

@app.on_callback_query(filters.regex(r"^img_help\|"))
def img_help_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(None)
    """Handle img help callback"""
    data = callback_query.data.split("|")[-1]
    
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(safe_get_messages(user_id).IMG_HELP_CLOSED_MSG)
        except Exception:
            pass
        return
    
    try:
        callback_query.answer()
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^img_range\|"))
def img_range_callback(app, callback_query: CallbackQuery):
    messages = safe_get_messages(None)
    """Handle img range selection callback"""
    try:
        user_id = callback_query.from_user.id
        logger.info(f"[IMG_RANGE_CALLBACK] Received callback: {callback_query.data}")
        data_parts = callback_query.data.split("|")
        logger.info(f"[IMG_RANGE_CALLBACK] Data parts: {data_parts}")
        
        if len(data_parts) < 2:
            callback_query.answer("❌ Data error")
            return
        
        if data_parts[1] == "cancel":
            try:
                callback_query.message.delete()
            except Exception:
                callback_query.edit_message_reply_markup(reply_markup=None)
            try:
                callback_query.answer("❌ Cancelled")
            except Exception:
                pass
            return
        
        if len(data_parts) < 4:
            callback_query.answer("❌ Invalid data format")
            return
        
        start = int(data_parts[1])
        end = int(data_parts[2])
        url = data_parts[3]
        
        logger.info(f"[IMG_RANGE_CALLBACK] Parsed: start={start}, end={end}, url={url}")
        
        # Answer callback
        callback_query.answer(f"{safe_get_messages(user_id).ALWAYS_ASK_DOWNLOADING_IMAGES_MSG} {start}-{end}")
        
        # Delete the original message with the buttons immediately
        try:
            callback_query.message.delete()
            logger.info(f"[IMG_RANGE_CALLBACK] Deleted message with ID: {callback_query.message.message_id}")
        except Exception as e:
            logger.error(f"[IMG_RANGE_CALLBACK] Failed to delete message: {e}")
        
        # Create new message with range command
        range_command = f"/img {start}-{end} {url}"
        logger.info(f"[IMG_RANGE_CALLBACK] Created command: {range_command}")
        
        # Send the command as if user typed it
        from pyrogram.types import Message
        from pyrogram.types import Message as MessageType
        
        # Create a mock message object
        mock_message = MessageType(
            id=callback_query.message.id + 1,
            from_user=callback_query.from_user,
            chat=callback_query.message.chat,
            text=range_command,
            date=callback_query.message.date,
            reply_to_message=None
        )
        
        # Call the image command function
        logger.info(f"[IMG_RANGE_CALLBACK] Calling image_command with mock_message")
        image_command(app, mock_message)
        logger.info(f"[IMG_RANGE_CALLBACK] image_command completed")
        
    except Exception as e:
        try:
            callback_query.answer(f"{safe_get_messages(user_id).IMAGE_ERROR_MSG}")
        except Exception:
            pass