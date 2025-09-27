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
from HELPERS.logger import send_to_logger, logger, get_log_channel
from CONFIG.logger_msg import LoggerMsg
from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
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
from CONFIG.messages import Messages as Messages
from DATABASE.cache_db import save_to_image_cache, get_cached_image_posts, get_cached_image_post_indices
import json
from URL_PARSERS.tags import save_user_tags, extract_url_range_tags

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
    """Generate cover unless both duration<60s AND size<10MB (i.e., generate if duration>=60s OR size>=10MB)."""
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
                    logger.info(f"[IMG PAID] Embedded cover into video: {video_path}")
        except Exception as e:
            logger.warning(f"[IMG PAID] Failed to embed cover into video {video_path}: {e}")
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
    """Send open copy of media to NSFW channel for history"""
    try:
        # Use explicit NSFW channel to avoid any fallback to LOGS_ID
        log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
        
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
        
        logger.info(f"[IMG LOG] Open copy sent to NSFW channel for history: {file_path}")
        return open_msg
    except Exception as e:
        logger.error(f"[IMG LOG] Failed to send open copy to NSFW channel: {e}")
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
            logger.info(f"[IMG CACHE] Skipping cache save for NSFW content: index={album_index}, channel_type={channel_type}")
            return
        
        logger.info(f"[IMG CACHE] About to save album: index={album_index}, ids={message_ids}, channel_type={channel_type}")
        save_to_image_cache(url, album_index, message_ids)
        logger.info(f"[IMG CACHE] Save requested for index={album_index}, channel_type={channel_type}")
    except Exception as e:
        logger.error(f"[IMG CACHE] Save failed for index={album_index}: {e}")
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
                logger.info(f"Converted WebP to JPEG: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert WebP: {result.stderr}")
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
                logger.info(f"Converted WebM to MP4: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert WebM: {result.stderr}")
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
                logger.info(f"Remuxed MP4 with faststart: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to remux MP4 faststart: {result.stderr}")
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
                logger.info(f"Converted {file_ext} to MP4: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert {file_ext}: {result.stderr}")
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
                logger.info(f"Converted {file_ext} to JPEG: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert {file_ext}: {result.stderr}")
                return file_path
        
        # No conversion needed
        else:
            return file_path
            
    except subprocess.TimeoutExpired:
        logger.error(f"Conversion timeout for {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Conversion error for {file_path}: {e}")
        return file_path

@app.on_message(filters.command("img") & filters.private)
def image_command(app, message):
    """Handle /img command for downloading images"""
    user_id = message.chat.id
    text = message.text.strip()
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    
    # Extract URL from command
    if len(text.split()) < 2:
        # Show help if no URL provided
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="img_help|close")]
        ])
        safe_send_message(
            user_id,
            Messages.IMG_HELP_MSG + " /audio, /vid, /help, /playlist, /settings",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id)
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
        if re.fullmatch(r"\d+-\d*", rng_candidate):
            start_str, end_str = rng_candidate.split('-', 1)
            try:
                start_val = int(start_str)
                end_val = int(end_str) if end_str != '' else None
                if start_val >= 1:
                    manual_range = (start_val, end_val)
                    url = ' '.join(parts[1:]).strip()
                else:
                    url = rest
            except Exception:
                url = rest
        else:
            url = rest
    else:
        url = rest
    
    # Use common tag/url extractor to get clean URL and tags from the whole message
    try:
        parsed_url, _s, _e, _plist, user_tags, user_tags_text, _err = extract_url_range_tags(text)
        logger.info(f"[IMG DEBUG] extract_url_range_tags result: parsed_url={parsed_url}, _s={_s}, _e={_e}, text={text}")
        if parsed_url:
            url = parsed_url
            # Check if range was specified in URL*start*end format
            if _s != 1 or _e != 1:
                manual_range = (_s, _e)
                logger.info(f"[IMG DEBUG] Range detected: {_s}-{_e}")
            else:
                logger.info(f"[IMG DEBUG] No range detected in URL*start*end format")
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
            user_id,
            Messages.INVALID_URL_MSG,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id)
        )
        send_to_logger(message, LoggerMsg.INVALID_URL_PROVIDED.format(url=url))
        return
    
    # Check if user has proxy enabled
    use_proxy = is_proxy_enabled(user_id)
    
    # Send initial message
    status_msg = safe_send_message(
        user_id,
        Messages.CHECKING_CACHE_MSG.format(url=url),
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
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
                    requested_indices = list(range(int(start_i), int(end_i) + 1))
                else:
                    cached_all = sorted(list(get_cached_image_post_indices(url)))
                    requested_indices = [i for i in cached_all if i >= int(start_i)]
            cached_map = get_cached_image_posts(url, requested_indices)
        except Exception as e:
            logger.error(f"Error getting cached image posts: {e}")
            cached_map = {}
    
    try:
        if cached_map:
            for album_idx in sorted(cached_map.keys()):
                ids = cached_map[album_idx]
                try:
                    kwargs = {}
                    thread_id = getattr(message, 'message_thread_id', None)
                    if thread_id:
                        kwargs['message_thread_id'] = thread_id
                    # For cached content, always use regular channel (no NSFW/PAID in cache)
                    from_chat_id = get_log_channel("image")
                    channel_type = "regular"
                    
                    logger.info(f"[IMG CACHE] Reposting album {album_idx} from channel {from_chat_id} to user {user_id}, message_ids={ids}")
                    sm.safe_forward_messages(user_id, from_chat_id, ids, **kwargs)
                except Exception:
                    logger.info(f"[IMG CACHE] Fallback reposting album {album_idx} from channel {from_chat_id} to user {user_id}, message_ids={ids}")
                    app.forward_messages(user_id, from_chat_id, ids, **kwargs)
                except Exception as _e:
                    logger.warning(f"Failed to forward cached album {album_idx}: {_e}")
            
            try:
                safe_edit_message_text(
                    user_id, status_msg.id,
                    Messages.SENT_FROM_CACHE_MSG.format(count=len(cached_map)),
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
            send_to_logger(message, LoggerMsg.REPOSTED_CACHED_ALBUMS.format(count=len(cached_map), url=url))
            return
    except Exception as _e:
        logger.warning(f"Image cache forward (early) failed: {_e}")
    
    # Check if user is admin
    is_admin = int(user_id) in Config.ADMIN
    
    # Check range limits if manual range is specified (before URL analysis)
    if manual_range:
        range_count = manual_range[1] - manual_range[0] + 1
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
        
        if range_count > max_img_files:
            # Create alternative commands preserving the original start range
            start_range = manual_range[0]
            end_range = start_range + max_img_files - 1
            suggested_command_url_format = f"{url}*{start_range}*{end_range}"
            
            safe_send_message(
                user_id,
                Messages.IMG_RANGE_LIMIT_EXCEEDED_MSG.format(
                    range_count=range_count,
                    max_img_files=max_img_files,
                    start_range=start_range,
                    end_range=end_range,
                    url=url,
                    suggested_command_url_format=suggested_command_url_format
                ),
                parse_mode=enums.ParseMode.HTML,
                reply_parameters=ReplyParameters(message_id=message.id)
            )
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
        
        if not image_info:
            safe_edit_message_text(
                user_id, status_msg.id,
                Config.FAILED_ANALYZE_MSG.format(url=url) +
                "The URL might not be accessible or not contain a valid image.",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, LoggerMsg.FAILED_ANALYZE_IMAGE.format(url=url))
            return
        
        # Update status message
        title = image_info.get('title', 'Unknown')
        safe_edit_message_text(
            user_id, status_msg.id,
            Config.DOWNLOADING_IMAGE_MSG +
            f"<b>Title:</b> {title}\n"
            f"<b>URL:</b> <code>{url}</code>",
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
            
        logger.info(f"[IMG] User {user_id} is admin: {is_admin}, limit: {'unlimited' if is_admin else total_limit}")
        
        # Determine expected total via --get-urls analog
        detected_total = None
        if manual_range is None or manual_range[1] is None:
            detected_total = get_total_media_count(url, user_id, use_proxy)
        
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
            if detected_total > max_img_files:
                # Create alternative commands preserving the original start range if manual_range exists
                if manual_range and manual_range[0] is not None:
                    start_range = manual_range[0]
                    end_range = start_range + max_img_files - 1
                else:
                    start_range = 1
                    end_range = max_img_files
                
                suggested_command_url_format = f"{url}*{start_range}*{end_range}"
                
                safe_send_message(
                    user_id,
                    f"❗️ Media limit exceeded: {detected_total} files found (maximum {max_img_files}).\n\n"
                    f"Use one of these commands to download maximum available files:\n\n"
                    f"<code>/img {start_range}-{end_range} {url}</code>\n\n"
                    f"<code>{suggested_command_url_format}</code>",
                    parse_mode=enums.ParseMode.HTML,
                    reply_parameters=ReplyParameters(message_id=message.id)
                )
                return
            
            total_expected = min(detected_total, max_img_files)
        elif detected_total and detected_total > 0:
            total_expected = detected_total
        # Streaming download: run range-based batches (1-10, 11-20, ...) scoped to a unique per-run directory
        run_dir = os.path.join("users", str(user_id), f"run_{int(time.time())}")
        create_directory(run_dir)
        files_to_cleanup = []

        # We'll not start full download thread; we'll pull ranges to enforce batching

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
        album_index = 0  # index of posts we send (albums only)
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
            try:
                safe_edit_message_text(
                    user_id,
                    status_msg.id,
                    Config.DOWNLOADING_MSG +
                    f"Downloaded: <b>{total_downloaded}</b> / <b>{total_expected or total_limit}</b>\n"
                    f"Sent: <b>{total_sent}</b>\n"
                    f"Pending to send: <b>{len(photos_videos_buffer) + len(others_buffer)}</b>",
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass

        gallery_dl_dir = run_dir
        last_status_update = 0.0
        # Seed current_start and upper bound from manual range if provided
        current_start = 1
        manual_end_cap = None
        if manual_range is not None:
            current_start = manual_range[0]
            # Upper cap: if user provided end, respect it (but not above limit for non-admins)
            if manual_range[1] is not None:
                manual_end_cap = manual_range[1] if is_admin else min(manual_range[1], total_limit)
                total_expected = manual_end_cap  # show as expected
        
        # For small totals, set end cap to avoid range issues
        if detected_total and detected_total <= 10 and manual_range is None:
            manual_end_cap = detected_total
            total_expected = detected_total
            logger.info(f"[IMG BATCH] Small total detected: {detected_total}, setting end cap to {manual_end_cap}")
        # helper to run one range and wait for files to appear
        def run_and_collect(next_end: int):
            # For single item or when total is small, use range 1-1 to avoid API issues
            if (current_start == next_end and next_end == 1) or (detected_total and detected_total <= 10):
                logger.info(f"Downloading with range 1-1 (total={detected_total}, start={current_start}, end={next_end})")
                ok = download_image_range_cli(url, "1-1", user_id, use_proxy, output_dir=run_dir)
                if not ok:
                    logger.warning(f"CLI download failed, trying Python API.")
                    return download_image_range(url, "1-1", user_id, use_proxy, run_dir)
            else:
                range_expr = f"{current_start}-{next_end}"
                # Prefer CLI to enforce strict range behavior across gallery-dl versions
                logger.info(f"Prepared range: {range_expr}")
                ok = download_image_range_cli(url, range_expr, user_id, use_proxy, output_dir=run_dir)
                if not ok:
                    logger.warning(f"CLI range download failed or rejected for {range_expr}, trying Python API.")
                    return download_image_range(url, range_expr, user_id, use_proxy, run_dir)
            return True

        while True:
            # Only download next range if buffer is empty (strict batching)
            if len(photos_videos_buffer) == 0:
                upper_cap = manual_end_cap or total_expected
                if upper_cap and current_start > upper_cap:
                    break
                else:
                    next_end = current_start + batch_size - 1
                    if upper_cap:
                        next_end = min(next_end, upper_cap)
                    logger.info(f"[IMG BATCH] Starting download range {current_start}-{next_end}")
                    run_and_collect(next_end)
                    current_start = next_end + 1
                    # Wait for download to complete before processing files
                    time.sleep(2)
            # Find new files
            if os.path.exists(gallery_dl_dir):
                for root, _, files in os.walk(gallery_dl_dir):
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
                                continue
                        except Exception:
                            continue
                        seen_files.add(file_path)
                        total_downloaded += 1

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
                            # ЖЕСТКО: При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                            if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                original_chat_id = getattr(message, '_original_chat_id', user_id)
                                # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                logger.info(f"[IMG MAIN] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                            logger.info(f"[IMG MAIN] nsfw_flag={nsfw_flag}, is_private_chat={is_private_chat}, media_group_len={len(media_group)}")
                            
                            # MAIN SENDING LOGIC - separate try-catch to prevent logging errors from triggering fallback
                            try:
                                if nsfw_flag and is_private_chat:
                                    logger.info(f"[IMG MAIN] Entering paid media logic for {len(media_group)} items")
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
                                        logger.info(f"[IMG PAID] Sending paid media album with {len(paid_media_list)} items")
                                        logger.info(f"[IMG PAID] Media types: {[type(item).__name__ for item in paid_media_list]}")
                                        # Try to send as album first, if that fails, send individually
                                        try:
                                            logger.info(f"[IMG PAID] Attempting to send album with {len(paid_media_list)} items to user {user_id}")
                                            logger.info(f"[IMG PAID] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                            
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=paid_media_list,
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                            logger.error(f"[IMG PAID] FAILED: send_paid_media album failed with error: {e}")
                                            logger.error(f"[IMG PAID] FAILED: Error type: {type(e)}")
                                            logger.error(f"[IMG PAID] FAILED: Error details: {str(e)}")
                                            # Fallback: send individually as paid media with same reply_parameters
                                            for i, paid_media in enumerate(paid_media_list):
                                                try:
                                                    # Use same reply_parameters for all to group them
                                                    individual_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[paid_media],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                    if isinstance(individual_msg, list):
                                                        sent.extend(individual_msg)
                                                    elif individual_msg is not None:
                                                        sent.append(individual_msg)
                                                    # Small delay between messages to help grouping
                                                    if i < len(paid_media_list) - 1:
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
                                            log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
                                            if log_channel_nsfw:
                                                open_sent = app.send_media_group(
                                                    chat_id=log_channel_nsfw,
                                                    media=open_media_group,
                                                    reply_parameters=ReplyParameters(message_id=message.id)
                                                )
                                                logger.info(f"[IMG LOG] Open copy album sent to LOGS_NSFW_ID for history: {len(open_media_group)} items")
                                        except Exception as e:
                                            logger.error(f"[IMG LOG] Failed to send open copy album to LOGS_NSFW_ID: {e}")
                                            
                                    except Exception as e:
                                        logger.error(f"Failed to send paid media album: {e}")
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
                                        
                                        # Try to send as album first, if that fails, send individually with grouping
                                        try:
                                            logger.info(f"[IMG MAIN FALLBACK] Attempting to send album with {len(paid_media_list)} items to user {user_id}")
                                            logger.info(f"[IMG MAIN FALLBACK] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                            
                                            paid_msg = app.send_paid_media(
                                                    user_id,
                                                media=paid_media_list,
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=message.id)
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
                                            logger.error(f"[IMG MAIN FALLBACK] FAILED: send_paid_media album failed with error: {e}")
                                            logger.error(f"[IMG MAIN FALLBACK] FAILED: Error type: {type(e)}")
                                            logger.error(f"[IMG MAIN FALLBACK] FAILED: Error details: {str(e)}")
                                            # Fallback: send individually as paid media with same reply_parameters for grouping
                                            for i, paid_media in enumerate(paid_media_list):
                                                try:
                                                    # Use same reply_parameters for all to group them
                                                    individual_msg = app.send_paid_media(
                                                    user_id,
                                                        media=[paid_media],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                    if isinstance(individual_msg, list):
                                                        sent.extend(individual_msg)
                                                    elif individual_msg is not None:
                                                        sent.append(individual_msg)
                                                    # Small delay between messages to help grouping
                                                    if i < len(paid_media_list) - 1:
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
                                            log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
                                            open_sent = app.send_media_group(
                                                chat_id=log_channel_nsfw,
                                                media=open_media_group,
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                                    
                                                    # Create user caption with URL
                                                    user_caption_lines = []
                                                    if tags_text_norm:
                                                        user_caption_lines.append(tags_text_norm)
                                                    user_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                                                    user_caption = "\n".join(user_caption_lines)
                                                    
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
                                                logger.debug(f"[IMG] Album caption normalization skipped: { _e }")
                                            sent = app.send_media_group(
                                                user_id,
                                                media=media_group,
                                                reply_parameters=ReplyParameters(message_id=message.id)
                                            )
                                            break
                                        except FloodWait as fw:
                                            wait_s = int(getattr(fw, 'value', 0) or 0)
                                            logger.warning(f"FloodWait while send_media_group: waiting {wait_s}s and retrying (attempt {attempts+1}/5)")
                                            time.sleep(wait_s + 1)
                                            attempts += 1
                                            last_exc = fw
                                        except Exception as ex:
                                            last_exc = ex
                                            break
                                    if attempts >= 5 and last_exc is not None:
                                        raise last_exc
                                sent_message_ids.extend([m.id for m in sent])
                                total_sent += len(media_group)
                                # Forward album to logs and save forwarded IDs to cache
                                try:
                                    orig_ids = [m.id for m in sent]
                                    logger.info(f"[IMG CACHE] Copying album to logs, orig_ids={orig_ids}")
                                    f_ids = []
                                    
                                    # Determine correct log channel based on media type and chat type
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    # ЖЕСТКО: При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                                    if hasattr(message, '_is_fake_message') and message._is_fake_message:
                                        original_chat_id = getattr(message, '_original_chat_id', user_id)
                                        # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                                        is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                                        logger.info(f"[IMG LOG] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                                    is_paid_media = nsfw_flag and is_private_chat
                                    
                                    # ЖЕСТКО: Отправка в лог-каналы должна быть ВНЕ цикла, только один раз для всего альбома
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
                                        log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
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
                                                    reply_parameters=ReplyParameters(message_id=message.id)
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
                                            # Create caption for log channel
                                            bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                            log_caption_lines = []
                                            if tags_text_norm:
                                                log_caption_lines.append(tags_text_norm)
                                            log_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                                            log_caption = "\n".join(log_caption_lines)
                                            
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
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                    try:
                                        if os.path.exists(path):
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
                                # ЖЕСТКО: При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
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
                                        
                                        # Send as paid media album
                                        logger.info(f"[IMG FALLBACK PAID] Sending paid media album with {len(paid_media_list)} items")
                                        # Try to send as album first, if that fails, send individually
                                        try:
                                            logger.info(f"[IMG FALLBACK PAID] Attempting to send album with {len(paid_media_list)} items to user {user_id}")
                                            logger.info(f"[IMG FALLBACK PAID] Album details: star_count={LimitsConfig.NSFW_STAR_COST}, payload={Config.STAR_RECEIVER}")
                                            
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=paid_media_list,
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: send_paid_media album failed with error: {e}")
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: Error type: {type(e)}")
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: Error details: {str(e)}")
                                            # Fallback: send individually as paid media with same reply_parameters
                                            for i, paid_media in enumerate(paid_media_list):
                                                try:
                                                    # Use same reply_parameters for all to group them
                                                    individual_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[paid_media],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                    if isinstance(individual_msg, list):
                                                        sent.extend(individual_msg)
                                                    elif individual_msg is not None:
                                                        sent.append(individual_msg)
                                                    # Small delay between messages to help grouping
                                                    if i < len(paid_media_list) - 1:
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
                                            log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
                                            open_sent = app.send_media_group(
                                                chat_id=log_channel_nsfw,
                                                media=open_media_group,
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                # ЖЕСТКО: При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
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
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: send_paid_media album failed with error: {e}")
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: Error type: {type(e)}")
                                            logger.error(f"[IMG FALLBACK PAID] FAILED: Error details: {str(e)}")
                                            # Fallback: send individually as paid media with same reply_parameters
                                            for i, paid_media in enumerate(paid_media_list):
                                                try:
                                                    # Use same reply_parameters for all to group them
                                                    individual_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[paid_media],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                    if isinstance(individual_msg, list):
                                                        sent.extend(individual_msg)
                                                    elif individual_msg is not None:
                                                        sent.append(individual_msg)
                                                    # Small delay between messages to help grouping
                                                    if i < len(paid_media_list) - 1:
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
                                            log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
                                            if log_channel_nsfw:
                                                open_sent = app.send_media_group(
                                                    chat_id=log_channel_nsfw,
                                                    media=open_media_group,
                                                    reply_parameters=ReplyParameters(message_id=message.id)
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
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                                user_id,
                                                media=media_group,
                                                reply_parameters=ReplyParameters(message_id=message.id),
                                                message_thread_id=getattr(message, 'message_thread_id', None)
                                            )
                                            if isinstance(sent_msg, list):
                                                sent.extend(sent_msg)
                                            elif sent_msg is not None:
                                                sent.append(sent_msg)
                                        
                                        logger.info(f"[IMG FALLBACK ALBUM] Successfully sent album {album_start+1}-{album_end} ({len(album_items)} items)")
                                        
                                        # Small delay between albums
                                        if album_end < len(fallback):
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
                                                            reply_parameters=ReplyParameters(message_id=message.id)
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
                                                        # Create caption for log channel
                                                        bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                                        log_caption_lines = []
                                                        if tags_text_norm:
                                                            log_caption_lines.append(tags_text_norm)
                                                        log_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                                                        log_caption = "\n".join(log_caption_lines)
                                                        
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
                                                            reply_parameters=ReplyParameters(message_id=message.id)
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
                                                reply_parameters=ReplyParameters(message_id=message.id),
                                                message_thread_id=getattr(message, 'message_thread_id', None)
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
                                    if attempts >= 5 and last_exc is not None:
                                        raise last_exc
                                sent_message_ids.append(sent_msg.id)
                                total_sent += 1
                                update_status()
                                # Delete files immediately after sending (strict batching others)
                                try:
                                    if os.path.exists(p):
                                        os.remove(p)
                                        logger.info(f"[IMG BATCH OTHERS] Deleted file: {p}")
                                except Exception as e:
                                    logger.warning(f"[IMG BATCH OTHERS] Failed to delete {p}: {e}")
                                try:
                                    if os.path.exists(orig):
                                        os.remove(orig)
                                        logger.info(f"[IMG BATCH OTHERS] Deleted original: {orig}")
                                except Exception as e:
                                    logger.warning(f"[IMG BATCH OTHERS] Failed to delete original {orig}: {e}")
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
                        # ЖЕСТКО: При фоллбэке через fake_message определяем is_private_chat по оригинальному chat_id
                        if hasattr(message, '_is_fake_message') and message._is_fake_message:
                            original_chat_id = getattr(message, '_original_chat_id', user_id)
                            # Если chat_id начинается с -100, это группа/канал (не приватный чат)
                            is_private_chat = not (str(original_chat_id).startswith('-100') or str(original_chat_id).startswith('-'))
                            logger.info(f"[IMG TAIL] FAKE MESSAGE DETECTED - original_chat_id={original_chat_id}, is_private_chat={is_private_chat}")
                        if nsfw_flag and is_private_chat:
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
                                logger.info(f"[IMG TAIL PAID] Sending paid media album with {len(paid_media_list)} items")
                                try:
                                    paid_msg = app.send_paid_media(
                                        user_id,
                                        media=paid_media_list,
                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                        payload=str(Config.STAR_RECEIVER),
                                        reply_parameters=ReplyParameters(message_id=message.id)
                                    )
                                    
                                    if isinstance(paid_msg, list):
                                        sent.extend(paid_msg)
                                    elif paid_msg is not None:
                                        sent.append(paid_msg)
                                        
                                except Exception as e:
                                    logger.error(f"[IMG TAIL PAID] send_paid_media album failed: {e}")
                                    # Fallback: send individually as paid media
                                    for paid_media in paid_media_list:
                                        try:
                                            individual_msg = app.send_paid_media(
                                                user_id,
                                                media=[paid_media],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                    log_channel_nsfw = getattr(Config, "LOGS_NSFW_ID", 0)
                                    if log_channel_nsfw:
                                        open_sent = app.send_media_group(
                                            chat_id=log_channel_nsfw,
                                            media=open_media_group,
                                            reply_parameters=ReplyParameters(message_id=message.id)
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
                                                reply_parameters=ReplyParameters(message_id=message.id)
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
                                                    reply_parameters=ReplyParameters(message_id=message.id)
                                                )
                                            except TypeError:
                                                paid_msg = app.send_paid_media(
                                                    user_id,
                                                    media=[InputPaidMediaVideo(media=m.media)],
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=message.id)
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
                                            
                                            # Create user caption with URL
                                            user_caption_lines = []
                                            if tags_text_norm:
                                                user_caption_lines.append(tags_text_norm)
                                            user_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                                            user_caption = "\n".join(user_caption_lines)
                                            
                                            _sep = (' ' if _exist and not _exist.endswith('\n') else '')
                                            _first.caption = (_exist + _sep + user_caption).strip()
                                            # Avoid duplicating tags on the rest of items
                                            for _itm in media_group[1:]:
                                                if getattr(_itm, 'caption', None) == tags_text_norm:
                                                    _itm.caption = None
                                    except Exception as _e:
                                        logger.debug(f"[IMG] Tail album caption normalization skipped: { _e }")
                                    sent = app.send_media_group(
                                        user_id,
                                        media=media_group,
                                        reply_parameters=ReplyParameters(message_id=message.id),
                                        message_thread_id=getattr(message, 'message_thread_id', None)
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
                            if attempts >= 5 and last_exc is not None:
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
                                        reply_parameters=ReplyParameters(message_id=message.id)
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
                                    # Create caption for log channel
                                    bot_username = getattr(Config, "BOT_USERNAME", "bot")
                                    log_caption_lines = []
                                    if tags_text_norm:
                                        log_caption_lines.append(tags_text_norm)
                                    log_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                                    log_caption = "\n".join(log_caption_lines)
                                    
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
                                        reply_parameters=ReplyParameters(message_id=message.id)
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
                                    os.remove(p)
                                    logger.info(f"[IMG BATCH FALLBACK] Deleted file: {p}")
                            except Exception as e:
                                logger.warning(f"[IMG BATCH FALLBACK] Failed to delete {p}: {e}")
                            try:
                                if os.path.exists(orig):
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
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                else:
                                                    sent_msg = app.send_photo(
                                                        user_id,
                                                        photo=f,
                                                        caption=(tags_text_norm or ''),
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=message.id),
                                                        message_thread_id=getattr(message, 'message_thread_id', None)
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
                                        if attempts >= 5 and last_exc is not None:
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
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                else:
                                                    sent_msg = app.send_video(
                                                        user_id,
                                                        video=f,
                                                        thumb=thumb if thumb and os.path.exists(thumb) else None,
                                                        caption=(tags_text_norm or ''),
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=message.id),
                                                        message_thread_id=getattr(message, 'message_thread_id', None)
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
                                        if attempts >= 5 and last_exc is not None:
                                            raise last_exc
                                    sent_message_ids.append(sent_msg.id)
                                    tmp_ids2.append(sent_msg.id)
                                    total_sent += 1
                                # Delete files immediately after sending (strict batching individual)
                                try:
                                    if os.path.exists(p):
                                        os.remove(p)
                                        logger.info(f"[IMG BATCH INDIVIDUAL] Deleted file: {p}")
                                except Exception as e:
                                    logger.warning(f"[IMG BATCH INDIVIDUAL] Failed to delete {p}: {e}")
                                try:
                                    if os.path.exists(orig):
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
                                            reply_parameters=ReplyParameters(message_id=message.id)
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
                                            reply_parameters=ReplyParameters(message_id=message.id)
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
                                reply_parameters=ReplyParameters(message_id=message.id),
                                message_thread_id=getattr(message, 'message_thread_id', None)
                            )
                        sent_message_ids.append(sent_msg.id)
                        total_sent += 1
                        # Delete files immediately after sending (strict batching others)
                        try:
                            if os.path.exists(p):
                                os.remove(p)
                                logger.info(f"[IMG BATCH OTHERS] Deleted file: {p}")
                        except Exception as e:
                            logger.warning(f"[IMG BATCH OTHERS] Failed to delete {p}: {e}")
                        try:
                            if os.path.exists(orig):
                                os.remove(orig)
                                logger.info(f"[IMG BATCH OTHERS] Deleted original: {orig}")
                        except Exception as e:
                            logger.warning(f"[IMG BATCH OTHERS] Failed to delete original {orig}: {e}")
                    except Exception:
                        pass
                # Final update and replace header to 'Download complete'
                final_expected = total_expected or min(total_downloaded, total_limit)
                try:
                    safe_edit_message_text(
                        user_id,
                        status_msg.id,
                        Config.DOWNLOAD_COMPLETE_MSG +
                        f"Downloaded: <b>{total_downloaded}</b> / <b>{final_expected}</b>\n"
                        f"Sent: <b>{total_sent}</b>",
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass
                break

            if not is_admin and total_sent >= total_limit:
                break

            time.sleep(0.5)

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
                            # Create user caption with URL
                            user_caption_lines = []
                            if tags_text_norm:
                                user_caption_lines.append(tags_text_norm)
                            user_caption_lines.append(f"[Images URL]({url}) @{Config.BOT_NAME}")
                            user_caption = "\n".join(user_caption_lines)
                            _first.caption = user_caption
                        # Clear captions from other items
                        for _itm in media_group[1:]:
                            if hasattr(_itm, 'caption'):
                                _itm.caption = None
                    
                    sent = app.send_media_group(
                        user_id,
                        media=media_group,
                        reply_parameters=ReplyParameters(message_id=message.id)
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
                                os.remove(p)
                                logger.info(f"[IMG BATCH FINAL] Deleted file: {p}")
                            if os.path.exists(orig):
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
                        if time_diff < 300:
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
        
        safe_edit_message_text(
            user_id, status_msg.id,
            Config.ERROR_OCCURRED_MSG.format(url=url, error=str(e)),
            parse_mode=enums.ParseMode.HTML
        )
        from HELPERS.logger import send_error_to_user
        send_error_to_user(message, Config.ERROR_OCCURRED_MSG.format(url=url, error=str(e)))
        send_to_logger(message, LoggerMsg.IMAGE_COMMAND_ERROR.format(url=url, error=e))

@app.on_callback_query(filters.regex(r"^img_help\|"))
def img_help_callback(app, callback_query: CallbackQuery):
    """Handle img help callback"""
    data = callback_query.data.split("|")[-1]
    
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(Messages.IMG_HELP_CLOSED_MSG)
        except Exception:
            pass
        return
    
    try:
        callback_query.answer()
    except Exception:
        pass
