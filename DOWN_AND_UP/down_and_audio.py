
# ########################################
# Down_and_audio function
# ########################################

import os
from HELPERS.logger import get_log_channel
from CONFIG.logger_msg import LoggerMsg
import threading
import time
import yt_dlp
from pyrogram.errors import FloodWait
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_logger, send_to_user, send_to_all
from HELPERS.limitter import TimeFormatter, humanbytes, check_user
from HELPERS.download_status import set_active_download, clear_download_start_time, check_download_timeout, start_hourglass_animation, playlist_errors, playlist_errors_lock
from HELPERS.safe_messeger import safe_delete_messages, safe_edit_message_text, safe_forward_messages
from HELPERS.filesystem_hlp import sanitize_filename, create_directory, check_disk_space, cleanup_user_temp_files
from DATABASE.firebase_init import write_logs
from URL_PARSERS.tags import generate_final_tags
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url, download_thumbnail
from URL_PARSERS.thumbnail_downloader import download_thumbnail as download_universal_thumbnail
from HELPERS.pot_helper import add_pot_to_ytdl_opts
import subprocess
from PIL import Image
import io
from CONFIG.config import Config
from COMMANDS.subtitles_cmd import is_subs_enabled, check_subs_availability, get_user_subs_auto_mode, _subs_check_cache, download_subtitles_ytdlp, is_subs_always_ask
from COMMANDS.mediainfo_cmd import send_mediainfo_if_enabled
from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.normalizer import get_clean_playlist_url
from DATABASE.cache_db import get_cached_playlist_videos, get_cached_message_ids, save_to_video_cache, save_to_playlist_cache
from pyrogram.types import ReplyParameters
from pyrogram import enums
from URL_PARSERS.tags import extract_url_range_tags

# Get app instance for decorators
app = get_app()

def create_telegram_thumbnail(cover_path, output_path, size=320):
    """Create a Telegram-compliant thumbnail from cover image using center crop (no black bars)."""
    try:
        logger.info(f"Creating Telegram thumbnail: {cover_path} -> {output_path}")
        
        # Open image with PIL
        with Image.open(cover_path) as img:
            # Convert to RGB (handles CMYK and other color spaces)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Center-crop to a square (no padding)
            width, height = img.size
            side = min(width, height)
            left = (width - side) // 2
            top = (height - side) // 2
            right = left + side
            bottom = top + side
            img_cropped = img.crop((left, top, right, bottom))
            
            # Resize to required size
            img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as JPEG with baseline encoding and quality 0.8
            img_resized.save(output_path, 'JPEG', quality=80, optimize=True, progressive=False)
            
            # Check file size and reduce quality if needed (<200KB)
            file_size = os.path.getsize(output_path)
            logger.info(f"Telegram thumbnail created: {output_path}, size: {file_size} bytes")
            
            if file_size > 200 * 1024:  # 200KB
                logger.warning(f"Thumbnail size ({file_size} bytes) exceeds 200KB limit, reducing quality")
                img_resized.save(output_path, 'JPEG', quality=60, optimize=True, progressive=False)
                new_size = os.path.getsize(output_path)
                logger.info(f"Reduced quality thumbnail size: {new_size} bytes")
            
            return True
            
    except Exception as e:
        logger.error(f"Error creating Telegram thumbnail: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def embed_cover_mp3(mp3_path, cover_path, title=None, artist=None, album=None):
    """Embed cover into MP3 using ID3v2 APIC via ffmpeg."""
    try:
        logger.info(f"Starting cover embedding: MP3={mp3_path}, Cover={cover_path}")
        
        # Check if files exist
        if not os.path.exists(mp3_path):
            logger.error(f"MP3 file not found: {mp3_path}")
            return False
        if not os.path.exists(cover_path):
            logger.error(f"Cover file not found: {cover_path}")
            return False
        
        # Convert cover to JPEG if needed
        if cover_path.lower().endswith(('.webp', '.png')):
            jpeg_path = cover_path.rsplit('.', 1)[0] + '.jpg'
            logger.info(f"Converting cover to JPEG: {cover_path} -> {jpeg_path}")
            result = subprocess.run([
                "ffmpeg", "-y", "-i", cover_path, jpeg_path
            ], check=True, capture_output=True, text=True)
            cover_path = jpeg_path
        
        out_path = mp3_path.rsplit('.', 1)[0] + '_tagged.mp3'
        
        # Build ffmpeg command for MP3 cover embedding
        cmd = [
            "ffmpeg", "-y",
            "-i", mp3_path,
            "-i", cover_path,
            "-map", "0:a:0", "-map", "1:v:0",
            "-c:a", "copy",
            "-c:v", "mjpeg",
            "-id3v2_version", "3",
            "-metadata:s:v", "title=Album cover",
            "-metadata:s:v", "comment=Cover (front)",
            "-disposition:v", "attached_pic"
        ]
        
        # Add metadata if provided
        if title:
            cmd.extend(["-metadata", f"title={title}"])
        if artist:
            cmd.extend(["-metadata", f"artist={artist}"])
        if album:
            cmd.extend(["-metadata", f"album={album}"])
        
        cmd.append(out_path)
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        # Run ffmpeg command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        logger.info(f"FFmpeg stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"FFmpeg stderr: {result.stderr}")
        
        # Replace original file with tagged version
        if os.path.exists(out_path):
            os.replace(out_path, mp3_path)
            logger.info(f"Successfully embedded cover in MP3: {mp3_path}")
            return True
        else:
            logger.error(f"Failed to create tagged MP3 file: {out_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error embedding cover: {e.stderr}")
        logger.error(f"FFmpeg command that failed: {' '.join(cmd) if 'cmd' in locals() else 'Unknown'}")
        return False
    except Exception as e:
        logger.error(f"Error embedding cover: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# @reply_with_keyboard
def down_and_audio(app, message, url, tags, quality_key=None, playlist_name=None, video_count=1, video_start_with=1, format_override=None, cookies_already_checked=False, use_proxy=False, http_headers=None):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    # Import required modules at the beginning
    from COMMANDS.cookies_cmd import is_youtube_cookie_error, is_youtube_geo_error, retry_download_with_different_cookies, retry_download_with_proxy
    
    playlist_indices = []
    playlist_msg_ids = []  
        
    user_id = message.chat.id
    logger.info(f"down_and_audio called: url={url}, quality_key={quality_key}, video_count={video_count}, video_start_with={video_start_with}")
    
    # ЖЕСТКО: Сохраняем оригинальный текст с диапазоном для фоллбэка
    original_message_text = message.text or message.caption or ""
    logger.info(f"[ORIGINAL TEXT] Saved for fallback: {original_message_text}")
    
    # Determine forced NSFW via user tags
    try:
        _u, _s, _e, _p, _tags, _tags_text, _err = extract_url_range_tags(original_message_text)
        user_forced_nsfw = any(t.lower() in ("#nsfw", "#porn") for t in (_tags or []))
    except Exception:
        user_forced_nsfw = False
    
    # Check if LINK mode is enabled - if yes, get direct link instead of downloading
    try:
        from DOWN_AND_UP.always_ask_menu import get_link_mode
        if get_link_mode(user_id):
            logger.info(f"LINK mode enabled for user {user_id}, getting direct link instead of downloading audio")
            
            # Import link function
            from COMMANDS.link_cmd import get_direct_link
            
            # Convert quality key to quality argument
            quality_arg = None
            if quality_key and quality_key != "best" and quality_key != "mp3":
                quality_arg = quality_key
            
            # Get direct link
            result = get_direct_link(url, user_id, quality_arg, cookies_already_checked=cookies_already_checked, use_proxy=True)
            
            if result.get('success'):
                title = result.get('title', 'Unknown')
                duration = result.get('duration', 0)
                video_url = result.get('video_url')
                audio_url = result.get('audio_url')
                format_spec = result.get('format', 'best')
                
                # Form response
                response = f"🔗 <b>Direct link obtained</b>\n\n"
                response += f"📹 <b>Title:</b> {title}\n"
                if duration > 0:
                    response += f"⏱ <b>Duration:</b> {duration} sec\n"
                response += f"🎛 <b>Format:</b> <code>{format_spec}</code>\n\n"
                
                if video_url:
                    response += f"🎬 <b>Video stream:</b>\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
                
                if audio_url:
                    response += f"🎵 <b>Audio stream:</b>\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
                
                if not video_url and not audio_url:
                    response += "❌ Failed to get stream links"
                
                # Send response
                app.send_message(
                    user_id, 
                    response, 
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                send_to_logger(message, LoggerMsg.DIRECT_LINK_EXTRACTED.format(source="down_and_audio", user_id=user_id, url=url))
                
            else:
                error_msg = result.get('error', 'Unknown error')
                app.send_message(
                    user_id,
                    f"❌ <b>Error getting link:</b>\n{error_msg}",
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                send_to_logger(message, LoggerMsg.DIRECT_LINK_FAILED.format(source="down_and_audio", user_id=user_id, url=url, error=error_msg))
            
            return
    except Exception as e:
        logger.error(f"Error checking LINK mode for user {user_id}: {e}")
        # Continue with normal download if LINK mode check fails
    
    # We define a playlist not only by the number of videos, but also by the presence of a range in the URL
    original_text = message.text or message.caption or ""
    is_playlist = video_count > 1 or is_playlist_with_range(original_text)
    requested_indices = list(range(video_start_with, video_start_with + video_count)) if is_playlist else []
    cached_videos = {}
    uncached_indices = []
    if quality_key and is_playlist:
        # Check if Always Ask mode is enabled - if yes, skip cache completely
        if not is_subs_always_ask(user_id):
            # Check if content is NSFW - if so, skip cache lookup
            from HELPERS.porn import is_porn
            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
            if not is_nsfw:
                cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, requested_indices)
                uncached_indices = [i for i in requested_indices if i not in cached_videos]
            else:
                logger.info(f"down_and_audio: skipping cache lookup for NSFW playlist content (url={url})")
                cached_videos = {}
                uncached_indices = requested_indices
        else:
            logger.info(f"[AUDIO CACHE] Skipping cache check for playlist because Always Ask mode is enabled: url={url}, quality={quality_key}")
            cached_videos = {}
            uncached_indices = requested_indices
        # First, repost the cached ones
        if cached_videos:
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        # Determine the correct log channel based on content type
                        from HELPERS.porn import is_porn
                        is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                        logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                        is_paid = is_nsfw and is_private_chat
                        
                        # Get the correct log channel for reposting
                        if is_paid:
                            from_chat_id = get_log_channel("video", paid=True)
                        elif is_nsfw:
                            from_chat_id = get_log_channel("video", nsfw=True)
                        else:
                            from_chat_id = get_log_channel("video")
                        
                        # Verify we're reposting from a valid log channel
                        valid_channels = [
                            get_log_channel("video"),
                            get_log_channel("video", nsfw=True),
                            get_log_channel("video", paid=True)
                        ]
                        if from_chat_id not in valid_channels:
                            logger.error(f"CRITICAL: Attempting to repost from wrong channel {from_chat_id}")
                            continue
                        
                        logger.info(f"[AUDIO CACHE] Reposting audio {index} from channel {from_chat_id} to user {user_id}, message_id={cached_videos[index]}")
                        forward_kwargs = {
                            'chat_id': user_id,
                            'from_chat_id': from_chat_id,
                            'message_ids': [cached_videos[index]]
                        }
                        # Only apply thread_id in groups/channels, not in private chats
                        if getattr(message.chat, "type", None) != enums.ChatType.PRIVATE:
                            thread_id = getattr(message, 'message_thread_id', None)
                            if thread_id:
                                forward_kwargs['message_thread_id'] = thread_id
                        app.forward_messages(**forward_kwargs)
                    except Exception as e:
                        logger.error(f"down_and_audio: error reposting cached audio index={index}: {e}")
            if len(uncached_indices) == 0:
                app.send_message(user_id, f"✅ Playlist audio sent from cache ({len(cached_videos)}/{len(requested_indices)} files).", reply_parameters=ReplyParameters(message_id=message.id))
                send_to_logger(message, LoggerMsg.PLAYLIST_AUDIO_SENT_FROM_CACHE.format(quality=quality_key, user_id=user_id))
                return
            else:
                app.send_message(user_id, f"📥 {len(cached_videos)}/{len(requested_indices)} audio sent from cache, downloading missing ones...", reply_parameters=ReplyParameters(message_id=message.id))
    elif quality_key and not is_playlist:
        # Check if Always Ask mode is enabled - if yes, skip cache completely
        if not is_subs_always_ask(user_id):
            # Check if content is NSFW - if so, skip cache lookup
            from HELPERS.porn import is_porn
            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
            if not is_nsfw:
                cached_ids = get_cached_message_ids(url, quality_key)
            else:
                logger.info(f"down_and_audio: skipping cache lookup for NSFW single audio content (url={url})")
                cached_ids = None
        else:
            logger.info(f"[AUDIO CACHE] Skipping cache check because Always Ask mode is enabled: url={url}, quality={quality_key}")
            cached_ids = None
        
        if cached_ids:
            try:
                # Determine the correct log channel based on content type
                # is_nsfw already determined above
                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                is_paid = is_nsfw and is_private_chat
                
                # Get the correct log channel for reposting
                if is_paid:
                    from_chat_id = get_log_channel("video", paid=True)
                elif is_nsfw:
                    from_chat_id = get_log_channel("video", nsfw=True)
                else:
                    from_chat_id = get_log_channel("video")
                
                # Verify we're reposting from a valid log channel
                valid_channels = [
                    get_log_channel("video"),
                    get_log_channel("video", nsfw=True),
                    get_log_channel("video", paid=True)
                ]
                if from_chat_id not in valid_channels:
                    logger.error(f"CRITICAL: Attempting to repost from wrong channel {from_chat_id}")
                    raise Exception("Wrong channel for repost")
                
                logger.info(f"[AUDIO CACHE] Reposting audio from channel {from_chat_id} to user {user_id}, message_ids={cached_ids}")
                forward_kwargs = {
                    'chat_id': user_id,
                    'from_chat_id': from_chat_id,
                    'message_ids': cached_ids
                }
                # Only apply thread_id in groups/channels, not in private chats
                if getattr(message.chat, "type", None) != enums.ChatType.PRIVATE:
                    thread_id = getattr(message, 'message_thread_id', None)
                    if thread_id:
                        forward_kwargs['message_thread_id'] = thread_id
                app.forward_messages(**forward_kwargs)
                app.send_message(user_id, "✅ Audio sent from cache.", reply_parameters=ReplyParameters(message_id=message.id))
                send_to_logger(message, LoggerMsg.AUDIO_SENT_FROM_CACHE.format(quality=quality_key, user_id=user_id))
                return
            except Exception as e:
                logger.error(f"Error reposting audio from cache: {e}")
                save_to_video_cache(url, quality_key, [], clear=True)
                # Don't show error message if we successfully got audio from cache
                # The audio was already sent successfully in the try block
    else:
        logger.info(f"down_and_audio: quality_key is None, skipping cache check")

    anim_thread = None
    stop_anim = threading.Event()
    proc_msg = None
    proc_msg_id = None
    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    audio_files = []
    try:
        # Check if there is a saved waiting time
        user_dir = os.path.join("users", str(user_id))
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")

        # We send the initial message
        if os.path.exists(flood_time_file):
            with open(flood_time_file, 'r') as f:
                wait_time = int(f.read().strip())
                hours = wait_time // 3600
                minutes = (wait_time % 3600) // 60
                seconds = wait_time % 60
                time_str = f"{hours}h {minutes}m {seconds}s"
                proc_msg = app.send_message(user_id, f"⚠️ Telegram has limited message sending.\n⏳ Please wait: {time_str}\nTo update timer send URL again 2 times.")
        else:
            proc_msg = app.send_message(user_id, "⚠️ Telegram has limited message sending.\n⏳ Please wait: \nTo update timer send URL again 2 times.")

        # We are trying to replace with "Download started"
        try:
            app.edit_message_text(
                chat_id=user_id,
                message_id=proc_msg.id,
                text="Download started"
            )
            if os.path.exists(flood_time_file):
                os.remove(flood_time_file)
        except FloodWait as e:
            wait_time = e.value
            os.makedirs(user_dir, exist_ok=True)
            with open(flood_time_file, 'w') as f:
                f.write(str(wait_time))
            return
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return

        # If there is no flood error, send a normal message (only once)
        proc_msg = app.send_message(user_id, "🔄 Processing...", reply_parameters=ReplyParameters(message_id=message.id))
        # Pin proc/status message for visibility
        try:
            app.pin_chat_message(user_id, proc_msg.id, disable_notification=True)
        except Exception:
            pass
        proc_msg_id = proc_msg.id
        status_msg = app.send_message(user_id, "🎙️ Audio is processing...")
        hourglass_msg = app.send_message(user_id, "⏳ Please wait...")
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id
        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Check if there's enough disk space (estimate 500MB per audio file)
        user_folder = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_folder)

        if not check_disk_space(user_folder, 500 * 1024 * 1024 * video_count):
            send_to_user(message, "❌ Not enough disk space to download the audio files.")
            return

        check_user(message)

        # Reset of the flag of errors for the new launch of the playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # Check if cookie.txt exists in the user's folder
        user_cookie_path = os.path.join(user_folder, "cookie.txt")
        
        # For YouTube URLs, ensure working cookies (skip if already checked in Always Ask menu)
        if is_youtube_url(url) and not cookies_already_checked:
            from COMMANDS.cookies_cmd import ensure_working_youtube_cookies
            has_working_cookies = ensure_working_youtube_cookies(user_id)
            if has_working_cookies and os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
                logger.info(f"Using working YouTube cookies for user {user_id}")
            else:
                cookie_file = None
                logger.info(f"No working YouTube cookies available for user {user_id}, will try without cookies")
        elif is_youtube_url(url) and cookies_already_checked:
            # Cookies already checked in Always Ask menu - use them directly without verification
            if os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
                logger.info(f"Using YouTube cookies for user {user_id} (already validated in Always Ask menu)")
            else:
                # Cookies were deleted - try to restore them
                logger.info(f"No YouTube cookies found for user {user_id}, attempting to restore...")
                from COMMANDS.cookies_cmd import ensure_working_youtube_cookies
                has_working_cookies = ensure_working_youtube_cookies(user_id)
                if has_working_cookies and os.path.exists(user_cookie_path):
                    cookie_file = user_cookie_path
                    logger.info(f"Successfully restored working YouTube cookies for user {user_id}")
                else:
                    cookie_file = None
                    logger.info(f"Failed to restore YouTube cookies for user {user_id}, will try without cookies")
        else:
            # For non-YouTube URLs, use existing logic
            if os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
            else:
                # If not in the user's folder, copy from the global folder
                global_cookie_path = Config.COOKIE_FILE_PATH
                if os.path.exists(global_cookie_path):
                    try:
                        create_directory(user_folder)
                        import shutil
                        shutil.copy2(global_cookie_path, user_cookie_path)
                        logger.info(f"Copied global cookie file to user {user_id} folder for audio download")
                        cookie_file = user_cookie_path
                    except Exception as e:
                        logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                        cookie_file = None
                else:
                    cookie_file = None
        last_update = 0
        last_update = 0
        progress_start_time = time.time()
        current_total_process = ""
        successful_uploads = 0

        def progress_hook(d):
            nonlocal last_update
            # Check the timeout
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            
            # Calculate elapsed time and minutes passed
            elapsed = max(0, current_time - progress_start_time)
            minutes_passed = int(elapsed // 60)
            
            # After 1 hour (60 minutes), only show 0% and 100%
            if minutes_passed >= 60:
                if d.get("status") == "finished":
                    try:
                        full_bar = "🟩" * 10
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n📥 Downloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
                    except Exception as e:
                        logger.error(f"Error updating progress: {e}")
                elif d.get("status") == "error":
                    try:
                        safe_edit_message_text(user_id, proc_msg_id, "Error occurred during audio download.")
                    except Exception as e:
                        logger.error(f"Error updating progress: {e}")
                return
            
            # Adaptive throttle: base 1.5s, doubles each minute (cap 30s)
            base_interval = 1.5
            if minutes_passed < 5:
                # First 5 minutes: 1.5 seconds
                interval = base_interval
            else:
                # After 5 minutes: exponential backoff
                interval = base_interval * (2 ** (minutes_passed - 4))  # Start exponential after 5 minutes
                interval = min(interval, 30.0)
            
            if current_time - last_update < interval:
                return
                
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                try:
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n📥 Downloading audio:\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "finished":
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\n📥 Downloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "error":
                try:
                    safe_edit_message_text(user_id, proc_msg_id, "Error occurred during audio download.")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time

        # One-time retry guards to avoid infinite retry loops across attempts
        did_proxy_retry = False
        did_cookie_retry = False

        def try_download_audio(url, current_index):
            nonlocal current_total_process
            # Use format_override if provided, otherwise use default 'ba'
            download_format = format_override if format_override else 'ba'
            ytdl_opts = {
               'format': download_format,
               'postprocessors': [{
                  'key': 'FFmpegExtractAudio',
                  'preferredcodec': 'mp3',
                  'preferredquality': '192',
               },
               {
                  'key': 'FFmpegMetadata'   # equivalent to --add-metadata
               }                  
                ],
               'prefer_ffmpeg': True,
               'extractaudio': True,
               'playlist_items': str(current_index + video_start_with),
               'outtmpl': os.path.join(user_folder, "%(title).50s.%(ext)s"),
               'progress_hooks': [progress_hook],
               'extractor_args': {
                  'generic': {
                      'impersonate': ['chrome']
                  }
               },
               'referer': url,
               'geo_bypass': True,
               'check_certificate': False,
               'live_from_start': True,
               'writethumbnail': True,  # Enable thumbnail writing for manual embedding
               'writesubtitles': False,  # Disable subtitles for audio
               'writeautomaticsub': False,  # Disable auto subtitles for audio
            }
            
            # Add HTTP headers if provided
            if http_headers:
                from URL_PARSERS.http_headers import add_http_headers_to_ytdl_opts
                ytdl_opts = add_http_headers_to_ytdl_opts(ytdl_opts, http_headers)
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                ytdl_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                ytdl_opts['cookiefile'] = cookie_file
            
            # Add proxy configuration if needed
            if use_proxy:
                # Force proxy for this download
                from COMMANDS.proxy_cmd import get_proxy_config
                proxy_config = get_proxy_config()
                
                if proxy_config and 'type' in proxy_config and 'ip' in proxy_config and 'port' in proxy_config:
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
                    
                    ytdl_opts['proxy'] = proxy_url
                    logger.info(f"Force using proxy for audio download: {proxy_url}")
                else:
                    logger.warning("Proxy requested but proxy configuration is incomplete")
            else:
                # Add proxy configuration if needed for this domain
                from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
                ytdl_opts = add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)   
            
            # Add PO token provider for YouTube domains
            ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
            
            try:
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                if "entries" in info_dict:
                    entries = info_dict["entries"]
                    if len(entries) > 1:  # If the video in the playlist is more than one
                        actual_index = current_index + video_start_with - 1  # -1 because indexes in entries start from 0
                        if actual_index < len(entries):
                            info_dict = entries[actual_index]
                        else:
                            raise Exception(f"Audio index {actual_index + 1} out of range (total {len(entries)})")
                    else:
                        # If there is only one video in the playlist, just download it
                        info_dict = entries[0]  # Just take the first video

                try:
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\n> <i>📥 Downloading audio using format: {download_format}...</i>")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                
                # Try with proxy fallback if user proxy is enabled
                def download_operation(opts):
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    return True
                
                from HELPERS.proxy_helper import try_with_proxy_fallback
                result = try_with_proxy_fallback(ytdl_opts, url, user_id, download_operation)
                if result is None:
                    raise Exception("Failed to download audio with all available proxies")
                
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                error_text = str(e)
                logger.error(f"DownloadError: {error_text}")
                
                # Auto-fallback to gallery-dl (/img) for non-video posts (albums/images)
                if (
                    "No videos found in playlist" in error_text
                    or "Unsupported URL" in error_text
                    or "No video could be found" in error_text
                    or "No video found" in error_text
                    or "No media found" in error_text
                    or "This tweet does not contain" in error_text
                ):
                    try:
                        from COMMANDS.image_cmd import image_command
                        from HELPERS.safe_messeger import fake_message
                    except Exception as imp_e:
                        logger.error(f"Failed to import gallery-dl fallback handlers: {imp_e}")
                    else:
                        try:
                            safe_edit_message_text(user_id, proc_msg_id,
                                f"{current_total_process}\n❔ No audio formats found. Trying image downloader…")
                        except Exception:
                            pass
                        try:
                            # Check if content is NSFW for fallback
                            from HELPERS.porn import is_porn
                            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                            
                            # ЖЕСТКО: Используем сохраненный оригинальный текст с диапазоном
                            logger.info(f"[FALLBACK DEBUG] Using saved original_message_text: {original_message_text}")
                            
                            # Ищем URL с диапазоном *start*end
                            import re
                            range_url_match = re.search(r'(https?://[^\s\*#]+)\*(\d+)\*(\d+)', original_message_text)
                            if range_url_match:
                                parsed_url = range_url_match.group(1)
                                start_range = int(range_url_match.group(2))
                                end_range = int(range_url_match.group(3))
                                logger.info(f"[FALLBACK DEBUG] FOUND RANGE: {parsed_url} with range {start_range}-{end_range}")
                            else:
                                # Fallback к обычному URL
                                m = re.search(r'https?://[^\s\*#]+', original_message_text)
                                parsed_url = m.group(0) if m else original_message_text
                                start_range = 1
                                end_range = 1
                                logger.info(f"[FALLBACK DEBUG] NO RANGE FOUND, using url: {parsed_url}")
                            
                            # Build fallback command converting *1*10 to 1-10 format
                            if start_range and end_range and (start_range != 1 or end_range != 1):
                                # Convert *1*10 format to 1-10 format
                                fallback_text = f"/img {start_range}-{end_range} {parsed_url}"
                                logger.info(f"[FALLBACK] Converting range: *{start_range}*{end_range} -> {start_range}-{end_range}, fallback_text: {fallback_text}")
                            else:
                                fallback_text = f"/img {parsed_url}"
                                logger.info(f"[FALLBACK] No range detected, fallback_text: {fallback_text}")
                            
                            if tags:
                                tags_text = ' '.join(tags)
                                fallback_text += f" {tags_text}"
                            
                            # Add NSFW tag if content is detected as NSFW
                            if is_nsfw and "#nsfw" not in fallback_text.lower():
                                fallback_text += " #nsfw"
                                logger.info(f"[FALLBACK] Added #nsfw tag for NSFW content: {url}")
                            
                            image_command(app, fake_message(fallback_text, user_id, original_chat_id=user_id))
                            logger.info(f"Triggered gallery-dl fallback via /img from audio downloader, is_nsfw={is_nsfw}, range={start_range}-{end_range}")
                            return "IMG"
                        except Exception as call_e:
                            logger.error(f"Failed to trigger gallery-dl fallback from audio downloader: {call_e}")
                
                # Проверяем, связана ли ошибка с куками или региональными ограничениями YouTube
                if is_youtube_url(url):
                    if is_youtube_geo_error(error_text) and not did_proxy_retry:
                        logger.info(f"YouTube geo-blocked error detected for user {user_id}, attempting retry with proxy")
                        
                        # Пробуем скачать через прокси
                        retry_result = retry_download_with_proxy(
                            user_id, url, try_download_audio, url, current_index
                        )
                        
                        if retry_result is not None:
                            logger.info(f"Audio download retry with proxy successful for user {user_id}")
                            did_proxy_retry = True
                            return retry_result
                        else:
                            logger.warning(f"Audio download retry with proxy failed for user {user_id}")
                            did_proxy_retry = True
                    
                    elif is_youtube_cookie_error(error_text) and not did_cookie_retry:
                        logger.info(f"YouTube cookie-related error detected for user {user_id}, attempting retry with different cookies")
                        
                        # Пробуем скачать с другими куками
                        retry_result = retry_download_with_different_cookies(
                            user_id, url, try_download_audio, url, current_index
                        )
                        
                        if retry_result is not None:
                            logger.info(f"Audio download retry successful for user {user_id}")
                            did_cookie_retry = True
                            return retry_result
                        else:
                            logger.warning(f"All cookie retry attempts failed for user {user_id}")
                            did_cookie_retry = True
                
                # Send full error message with instructions immediately
                send_to_all(
                    message,
                    "<blockquote>Check <a href='https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites'>here</a> if your site supported</blockquote>\n"
                    "<blockquote>You may need <code>cookie</code> for downloading this audio. First, clean your workspace via <b>/clean</b> command</blockquote>\n"
                    "<blockquote>For Youtube - get <code>cookie</code> via <b>/cookie</b> command. For any other supported site - send your own cookie (<a href='https://t.me/c/2303231066/18'>guide1</a>) (<a href='https://t.me/c/2303231066/22'>guide2</a>) and after that send your audio link again.</blockquote>\n"
                    f"────────────────\n❌ Error downloading: {error_text}"
                )
                return None
            except Exception as e:
                error_text = str(e)
                logger.error(f"Audio download attempt failed: {e}")
                
                # Check if this is a "No videos found in playlist" error
                if "No videos found in playlist" in error_text or "Story might have expired" in error_text:
                    error_message = f"❌ No content found at index {current_index + video_start_with}"
                    send_to_all(message, error_message)
                    logger.info(f"Skipping item at index {current_index} (no content found)")
                    return "SKIP"
                
                # Check if this is a TikTok infinite loop error
                if "TikTok API keeps sending the same page" in error_text and "infinite loop" in error_text:
                    error_message = f"⚠️ TikTok API error at index {current_index + video_start_with}, skipping to next audio..."
                    send_to_user(message, error_message)
                    logger.info(f"Skipping TikTok audio at index {current_index} due to API error")
                    return "SKIP"  # Skip this audio and continue with next
                
                else:
                    send_to_user(message, f"❌ Unknown error: {e}")
                return None

        # Download thumbnail for embedding (only once for the URL)
        thumbnail_path = None
        try:
            logger.info(f"Downloading thumbnail for URL: {url}")
            # Try to download YouTube thumbnail first
            if ("youtube.com" in url or "youtu.be" in url):
                try:
                    # Extract YouTube video ID
                    import re
                    yt_id = None
                    if "youtube.com/watch?v=" in url:
                        yt_id = re.search(r'v=([^&]+)', url).group(1)
                    elif "youtu.be/" in url:
                        yt_id = re.search(r'youtu\.be/([^?]+)', url).group(1)
                    elif "youtube.com/shorts/" in url:
                        yt_id = re.search(r'shorts/([^?]+)', url).group(1)
                    
                    if yt_id:
                        youtube_thumb_path = os.path.join(user_folder, f"yt_thumb_{yt_id}.jpg")
                        download_thumbnail(yt_id, youtube_thumb_path, url)
                        if os.path.exists(youtube_thumb_path):
                            thumbnail_path = youtube_thumb_path
                            logger.info(f"Downloaded YouTube thumbnail: {youtube_thumb_path}")
                except Exception as e:
                    logger.warning(f"YouTube thumbnail download failed: {e}")
            
            # If not YouTube or YouTube thumb not found, try universal thumbnail downloader
            if not thumbnail_path:
                try:
                    universal_thumb_path = os.path.join(user_folder, "universal_thumb.jpg")
                    if download_universal_thumbnail(url, universal_thumb_path):
                        if os.path.exists(universal_thumb_path):
                            thumbnail_path = universal_thumb_path
                            logger.info(f"Downloaded universal thumbnail: {universal_thumb_path}")
                except Exception as e:
                    logger.info(f"Universal thumbnail not available: {e}")
        except Exception as e:
            logger.warning(f"Thumbnail download failed: {e}")

        if is_playlist and quality_key:
            indices_to_download = uncached_indices
        else:
            indices_to_download = range(video_count)
        for idx, current_index in enumerate(indices_to_download):
            current_index = current_index - video_start_with  # for numbering/display
            total_process = f"""
<b>📶 Total Progress</b>
<blockquote><b>Audio:</b> {idx + 1} / {len(indices_to_download)}</blockquote>
"""

            current_total_process = total_process

            # Determine rename_name based on the incoming playlist_name:
            if playlist_name and playlist_name.strip():
                # A new name for the playlist is explicitly set - let's use it
                rename_name = sanitize_filename(f"{playlist_name.strip()} - Part {idx + video_start_with}")
            else:
                # No new name set - extract name from metadata
                rename_name = None

            info_dict = try_download_audio(url, current_index)

            if info_dict is None:
                with playlist_errors_lock:
                    error_key = f"{user_id}_{playlist_name}"
                    if error_key not in playlist_errors:
                        playlist_errors[error_key] = True

                break

            successful_uploads += 1

            # Check if info_dict is None before accessing it
            if info_dict is None:
                logger.error("info_dict is None, cannot proceed with audio processing")
                send_to_user(message, "❌ Failed to extract audio information")
                break

            audio_title = info_dict.get("title", "audio")
            audio_title = sanitize_filename(audio_title)
            
            # If rename_name is not set, set it equal to audio_title
            if rename_name is None:
                rename_name = audio_title

            # Find the downloaded audio file
            allfiles = os.listdir(user_folder)
            files = [fname for fname in allfiles if fname.endswith('.mp3')]
            files.sort()
            if not files:
                send_to_all(message, f"Skipping unsupported file type in playlist at index {idx + video_start_with}")
                continue

            downloaded_file = files[0]
            write_logs(message, url, downloaded_file)

            if rename_name == audio_title:
                caption_name = audio_title  # Original title for caption
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(downloaded_file)
                if final_name != downloaded_file:
                    old_path = os.path.join(user_folder, downloaded_file)
                    new_path = os.path.join(user_folder, final_name)
                    try:
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                    except Exception as e:
                        logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                        final_name = downloaded_file
            else:
                ext = os.path.splitext(downloaded_file)[1]
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(rename_name + ext)
                caption_name = rename_name  # Original title for caption
                old_path = os.path.join(user_folder, downloaded_file)
                new_path = os.path.join(user_folder, final_name)

                if os.path.exists(new_path):
                    try:
                        os.remove(new_path)
                    except Exception as e:
                        logger.error(f"Error removing existing file {new_path}: {e}")

                try:
                    os.rename(old_path, new_path)
                except Exception as e:
                    logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                    final_name = downloaded_file
                    caption_name = audio_title  # Original title for caption

            audio_file = os.path.join(user_folder, final_name)
            if not os.path.exists(audio_file):
                send_to_user(message, "Audio file not found after download.")
                continue

            # Embed cover into MP3 file if thumbnail is available
            try:
                logger.info(f"Looking for thumbnails for audio file: {audio_file}")
                logger.info(f"User folder contents: {os.listdir(user_folder)}")
                
                # Use pre-downloaded thumbnail if available
                cover_path = None
                if thumbnail_path and os.path.exists(thumbnail_path):
                    cover_path = thumbnail_path
                    logger.info(f"Using pre-downloaded thumbnail: {cover_path}")
                else:
                    # Fallback: look for any thumbnail files
                    logger.info("Pre-downloaded thumbnail not found, searching for any thumbnails")
                    for file in os.listdir(user_folder):
                        if file.endswith(('.jpg', '.jpeg', '.png', '.webp')) and file != final_name:
                            thumb_path = os.path.join(user_folder, file)
                            if os.path.exists(thumb_path):
                                cover_path = thumb_path
                                logger.info(f"Found thumbnail: {cover_path}")
                                break
                
                # Embed cover if found
                if cover_path and os.path.exists(cover_path):
                    logger.info(f"Embedding cover {cover_path} into {audio_file}")
                    
                    # Extract metadata for embedding
                    title = info_dict.get("title", "")
                    artist = info_dict.get("artist") or info_dict.get("uploader") or info_dict.get("channel", "")
                    album = info_dict.get("album", "")
                    
                    logger.info(f"Metadata - Title: {title}, Artist: {artist}, Album: {album}")
                    
                    success = embed_cover_mp3(audio_file, cover_path, title=title, artist=artist, album=album)
                    if success:
                        logger.info(f"Successfully embedded cover in audio file: {audio_file}")
                    else:
                        logger.warning(f"Failed to embed cover in audio file: {audio_file}")
                else:
                    logger.warning(f"No thumbnail found for audio file: {audio_file}")
                    logger.warning(f"Available files in {user_folder}: {os.listdir(user_folder)}")
                    
            except Exception as e:
                logger.error(f"Error embedding cover in audio file {audio_file}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

            audio_files.append(audio_file)

            try:
                full_bar = "🟩" * 10
                safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n📤 Uploading audio file...\n{full_bar}   100.0%")
            except Exception as e:
                logger.error(f"Error updating upload status: {e}")

            # We form a text with tags and a link for audio
            tags_for_final = tags if isinstance(tags, list) else (tags.split() if isinstance(tags, str) else [])
            tags_text_final = generate_final_tags(url, tags_for_final, info_dict)
            tags_block = (tags_text_final.strip() + '\n') if tags_text_final and tags_text_final.strip() else ''
            bot_name = getattr(Config, 'BOT_NAME', None) or 'bot'
            bot_mention = f' @{bot_name}' if not bot_name.startswith('@') else f' {bot_name}'
            # Use original audio_title for caption, not sanitized caption_name
            caption_with_link = f"{audio_title}\n{tags_block}[🔗 Audio URL]({url}){bot_mention}"
            
            try:
                # Create Telegram-compliant thumbnail if cover is available
                telegram_thumb = None
                if cover_path and os.path.exists(cover_path):
                    telegram_thumb_path = os.path.join(user_folder, f"telegram_thumb_{idx}.jpg")
                    if create_telegram_thumbnail(cover_path, telegram_thumb_path):
                        telegram_thumb = telegram_thumb_path
                        logger.info(f"Using Telegram thumbnail: {telegram_thumb}")
                    else:
                        logger.warning("Failed to create Telegram thumbnail")
                
                # Determine if this is NSFW content in private chat (paid media)
                from HELPERS.porn import is_porn
                is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                is_paid = is_nsfw and is_private_chat
                
                # Send audio with appropriate method based on content type
                if is_paid:
                    # Send paid audio for NSFW content in private chats
                    try:
                        from pyrogram.types import InputPaidMediaAudio
                        from CONFIG.limits import LimitsConfig
                        
                        paid_audio = InputPaidMediaAudio(
                            media=audio_file,
                            thumb=telegram_thumb if telegram_thumb and os.path.exists(telegram_thumb) else None
                        )
                        
                        audio_msg = app.send_paid_media(
                            chat_id=user_id,
                            media=[paid_audio],
                            star_count=LimitsConfig.NSFW_STAR_COST,
                            payload=str(Config.STAR_RECEIVER),
                            reply_parameters=ReplyParameters(message_id=message.id),
                        )
                        logger.info("Paid NSFW audio sent to user")
                    except Exception as e:
                        logger.error(f"Failed to send paid audio, falling back to regular: {e}")
                        # Fallback to regular audio
                        if telegram_thumb and os.path.exists(telegram_thumb):
                            audio_msg = app.send_audio(
                                chat_id=user_id, 
                                audio=audio_file, 
                                caption=caption_with_link, 
                                reply_parameters=ReplyParameters(message_id=message.id),
                                thumb=telegram_thumb
                            )
                        else:
                            audio_msg = app.send_audio(
                                chat_id=user_id, 
                                audio=audio_file, 
                                caption=caption_with_link, 
                                reply_parameters=ReplyParameters(message_id=message.id)
                            )
                else:
                    # Send regular audio for non-NSFW content or group chats
                    if telegram_thumb and os.path.exists(telegram_thumb):
                        audio_msg = app.send_audio(
                            chat_id=user_id, 
                            audio=audio_file, 
                            caption=caption_with_link, 
                            reply_parameters=ReplyParameters(message_id=message.id),
                            thumb=telegram_thumb
                        )
                        logger.info(f"Audio sent with Telegram thumbnail: {telegram_thumb}")
                    else:
                        audio_msg = app.send_audio(
                            chat_id=user_id, 
                            audio=audio_file, 
                            caption=caption_with_link, 
                            reply_parameters=ReplyParameters(message_id=message.id)
                        )
                        logger.info("Audio sent without thumbnail")
                
                # Use already determined content type
                
                # Handle different content types according to new logic
                if is_paid:
                    # For NSFW content in private chat, paid audio already sent to user
                    # We need to send paid copy to LOGS_PAID_ID and open copy to LOGS_NSWF_ID for history
                    
                    # Send paid copy to LOGS_PAID_ID
                    log_channel_paid = get_log_channel("video", paid=True)
                    try:
                        # Forward the paid audio to LOGS_PAID_ID
                        safe_forward_messages(log_channel_paid, user_id, [audio_msg.id])
                        logger.info(f"down_and_audio: NSFW audio paid copy sent to PAID channel")
                    except Exception as e:
                        logger.error(f"down_and_audio: failed to send paid copy to PAID channel: {e}")
                    
                    # Send open copy to LOGS_NSWF_ID for history
                    log_channel_nsfw = get_log_channel("video", nsfw=True)
                    try:
                        # Create open copy for history (without stars)
                        open_audio_msg = app.send_audio(
                            chat_id=log_channel_nsfw,
                            audio=audio_file,
                            caption=caption_with_link,
                            reply_parameters=ReplyParameters(message_id=message.id),
                            thumb=telegram_thumb if telegram_thumb and os.path.exists(telegram_thumb) else None
                        )
                        logger.info(f"down_and_audio: NSFW audio open copy sent to NSFW channel for history")
                    except Exception as e:
                        logger.error(f"down_and_audio: failed to send open copy to NSFW channel: {e}")
                    
                    # Don't cache NSFW content
                    logger.info(f"down_and_audio: NSFW audio sent to user (paid), PAID channel (paid copy), and NSFW channel (open copy), not cached")
                    forwarded_msg = None
                    
                elif is_nsfw:
                    # NSFW content in groups -> LOGS_NSWF_ID only
                    log_channel = get_log_channel("video", nsfw=True)
                    forwarded_msg = safe_forward_messages(log_channel, user_id, [audio_msg.id])
                    # Don't cache NSFW content
                    logger.info(f"down_and_audio: NSFW audio sent to NSFW channel, not cached")
                    forwarded_msg = None
                else:
                    # Regular content -> LOGS_VIDEO_ID and cache
                    log_channel = get_log_channel("video")
                    forwarded_msg = safe_forward_messages(log_channel, user_id, [audio_msg.id])
                
                # Save to cache after sending audio (only for non-NSFW content)
                if quality_key and forwarded_msg and not is_nsfw:
                    if isinstance(forwarded_msg, list):
                        msg_ids = [m.id for m in forwarded_msg]
                    else:
                        msg_ids = [forwarded_msg.id]
                    
                    if is_playlist:
                        # For playlists, save to playlist cache with index
                        current_video_index = idx + video_start_with
                        logger.info(f"down_and_audio: saving to playlist cache: index={current_video_index}, msg_ids={msg_ids}")
                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], msg_ids, original_text=message.text or message.caption or "")
                        cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                        logger.info(f"Checking the cache immediately after writing: {cached_check}")
                        playlist_indices.append(current_video_index)
                        playlist_msg_ids.extend(msg_ids)  # We use msg_ids instead of forwarded_msgs
                    else:
                        # For single audios, save to regular cache
                        logger.info(f"down_and_audio: saving to video cache: msg_ids={msg_ids}")
                        save_to_video_cache(url, quality_key, msg_ids, original_text=message.text or message.caption or "", user_id=user_id)
                elif is_nsfw:
                    logger.info(f"down_and_audio: skipping cache for NSFW content (url={url})")
            except Exception as send_error:
                logger.error(f"Error sending audio: {send_error}")
                send_to_user(message, f"❌ Failed to send audio: {send_error}")
                continue

            # Clean up the audio file after sending
            try:
                send_mediainfo_if_enabled(user_id, audio_file, message)
                os.remove(audio_file)
            except Exception as e:
                logger.error(f"Failed to delete audio file {audio_file}: {e}")

            # Add delay between uploads for playlists
            if idx < len(indices_to_download) - 1:
                pass

        if successful_uploads == len(indices_to_download):
            success_msg = f"✅ Audio successfully downloaded and sent - {len(indices_to_download)} files uploaded.\n{Config.CREDITS_MSG}"
        else:
            success_msg = f"⚠️ Partially completed - {successful_uploads}/{len(indices_to_download)} audio files uploaded.\n{Config.CREDITS_MSG}"
            
        try:
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
        except Exception as e:
            logger.error(f"Error updating final status: {e}")

        send_to_logger(message, success_msg)

        if is_playlist and quality_key:
            total_sent = len(cached_videos) + successful_uploads
            app.send_message(user_id, f"✅Playlist audio sent: {total_sent}/{len(requested_indices)} files.", reply_parameters=ReplyParameters(message_id=message.id))
            send_to_logger(message, f"Playlist audio sent: {total_sent}/{len(requested_indices)} files (quality={quality_key}) to user{user_id}")

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, "⏰ Download cancelled due to timeout (2 hours)")
            send_to_logger(message, LoggerMsg.DOWNLOAD_TIMEOUT_LOG)
        else:
            logger.error(f"Error in audio download: {e}")
            send_to_user(message, f"❌ Failed to download audio: {e}")
    finally:
        # Always clean up resources
        stop_anim.set()
        if anim_thread:
            anim_thread.join(timeout=1)  # Wait for animation thread with timeout

        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}")

        # Clean up any remaining audio files
        for audio_file in audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                logger.error(f"Failed to delete file {audio_file}: {e}")
        
        # Clean up any downloaded thumbnails
        try:
            user_folder = os.path.join("users", str(user_id))
            if os.path.exists(user_folder):
                # Clean up YouTube thumbnails
                for thumb_file in os.listdir(user_folder):
                    if thumb_file.startswith("yt_thumb_") and thumb_file.endswith(".jpg"):
                        try:
                            os.remove(os.path.join(user_folder, thumb_file))
                        except Exception as e:
                            logger.error(f"Failed to delete thumbnail {thumb_file}: {e}")
                
                # Clean up universal thumbnails
                universal_thumb = os.path.join(user_folder, "universal_thumb.jpg")
                if os.path.exists(universal_thumb):
                    try:
                        os.remove(universal_thumb)
                    except Exception as e:
                        logger.error(f"Failed to delete universal thumbnail: {e}")
                
                # Clean up any yt-dlp generated thumbnails
                for thumb_file in os.listdir(user_folder):
                    if thumb_file.endswith(('.jpg', '.jpeg', '.png', '.webp')) and not thumb_file.startswith("yt_thumb_"):
                        try:
                            os.remove(os.path.join(user_folder, thumb_file))
                        except Exception as e:
                            logger.error(f"Failed to delete thumbnail {thumb_file}: {e}")
                
                # Clean up Telegram thumbnails
                for thumb_file in os.listdir(user_folder):
                    if thumb_file.startswith("telegram_thumb_") and thumb_file.endswith(".jpg"):
                        try:
                            os.remove(os.path.join(user_folder, thumb_file))
                        except Exception as e:
                            logger.error(f"Failed to delete Telegram thumbnail {thumb_file}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning up thumbnails: {e}")

        set_active_download(user_id, False)
        clear_download_start_time(user_id)  # Cleaning the start time

        # Clean up temporary files
        try:
            cleanup_user_temp_files(user_id)
        except Exception as e:
            logger.error(f"Error cleaning up temp files for user {user_id}: {e}")

        # Reset playlist errors if this was a playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]
