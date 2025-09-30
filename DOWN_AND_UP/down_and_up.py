# ########################################
# Download_and_up function
# ########################################

from HELPERS.logger import send_to_all  # Импорт в самом начале для гарантии видимости
import os
import glob
import threading
import time
import subprocess
import traceback
import yt_dlp
import re
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_logger, send_to_user, send_to_all, send_error_to_user, get_log_channel, log_error_to_channel
from CONFIG.logger_msg import LoggerMsg
from CONFIG.messages import Messages
from HELPERS.limitter import TimeFormatter, humanbytes, check_user, check_file_size_limit, check_subs_limits
from HELPERS.download_status import set_active_download, clear_download_start_time, check_download_timeout, start_hourglass_animation, start_cycle_progress, playlist_errors_lock, playlist_errors
from HELPERS.safe_messeger import safe_delete_messages, safe_edit_message_text, safe_forward_messages
from HELPERS.filesystem_hlp import sanitize_filename, cleanup_user_temp_files, cleanup_subtitle_files, create_directory, check_disk_space
from DOWN_AND_UP.ffmpeg import get_duration_thumb, get_video_info_ffprobe, embed_subs_to_video, create_default_thumbnail, split_video_2
from DOWN_AND_UP.sender import send_videos
from DATABASE.firebase_init import write_logs
from URL_PARSERS.tags import generate_final_tags, save_user_tags
from URL_PARSERS.youtube import is_youtube_url, download_thumbnail
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.filter_check import is_no_filter_domain
from URL_PARSERS.filter_utils import create_smart_match_filter, create_legacy_match_filter
from URL_PARSERS.thumbnail_downloader import download_thumbnail as download_universal_thumbnail
from HELPERS.pot_helper import add_pot_to_ytdl_opts
from CONFIG.config import Config
from CONFIG.messages import Messages
from CONFIG.limits import LimitsConfig
from COMMANDS.subtitles_cmd import is_subs_enabled, check_subs_availability, get_user_subs_auto_mode, _subs_check_cache, download_subtitles_ytdlp, get_user_subs_language, clear_subs_check_cache, is_subs_always_ask
from COMMANDS.split_sizer import get_user_split_size
from COMMANDS.mediainfo_cmd import send_mediainfo_if_enabled
from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.normalizer import get_clean_playlist_url
from DATABASE.cache_db import get_cached_playlist_videos, get_cached_message_ids, save_to_video_cache, save_to_playlist_cache
from HELPERS.qualifier import get_quality_by_min_side
from HELPERS.logger import send_to_all  # Импорт в самом конце для гарантии видимости
from HELPERS.safe_messeger import safe_forward_messages  # Дублирующий импорт для устранения ошибки видимости
from pyrogram import enums
from pyrogram.types import ReplyParameters
from HELPERS.safe_messeger import safe_send_message
from URL_PARSERS.tags import extract_url_range_tags
from HELPERS.fallback_helper import should_fallback_to_gallery_dl

# Get app instance for decorators
app = get_app()


def _save_video_cache_with_logging(url: str, quality_key: str, message_ids: list, original_text: str = None, user_id: int = None):
    """Save video to cache with channel type logging."""
    try:
        # Check if user has send_as_file enabled
        if user_id is not None:
            from COMMANDS.args_cmd import get_user_args
            user_args = get_user_args(user_id)
            send_as_file = user_args.get("send_as_file", False)
            if send_as_file:
                logger.info(f"[VIDEO CACHE] Skipping cache save for user {user_id} with send_as_file enabled: url={url}, quality={quality_key}")
                return
        
        # Determine channel type for logging
        from HELPERS.porn import is_porn
        is_nsfw = is_porn(url, "", "", None)
        logger.info(f"[FALLBACK] is_porn check for {url}: {is_nsfw}")
        channel_type = "NSFW" if is_nsfw else "regular"
        
        # Don't cache NSFW content
        if is_nsfw:
            logger.info(f"[VIDEO CACHE] Skipping cache save for NSFW content: url={url}, quality={quality_key}, channel_type={channel_type}")
            return
        
        logger.info(f"[VIDEO CACHE] About to save video: url={url}, quality={quality_key}, message_ids={message_ids}, channel_type={channel_type}")
        save_to_video_cache(url, quality_key, message_ids, original_text=original_text)
        logger.info(f"[VIDEO CACHE] Save requested for quality={quality_key}, channel_type={channel_type}")
    except Exception as e:
        logger.error(f"[VIDEO CACHE] Save failed for quality={quality_key}: {e}")


def determine_need_subs(subs_enabled, found_type, user_id):
    """
    Helper function to determine if subtitles are needed based on user settings and found type.
    Returns True if subtitles should be embedded, False otherwise.
    """
    if not subs_enabled or found_type is None:
        return False
    
    # Check if we're in Always Ask mode
    is_always_ask_mode = is_subs_always_ask(user_id)
    
    if is_always_ask_mode:
        # In Always Ask mode, always consider subtitles if found, regardless of auto_mode
        return True  # True if any subtitles found (auto or normal)
    else:
        # In manual mode, respect user's auto_mode setting
        auto_mode = get_user_subs_auto_mode(user_id)
        return (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")

#@reply_with_keyboard
def down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=None, quality_key=None, cookies_already_checked=False, use_proxy=False):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    # Import required modules at the beginning
    from URL_PARSERS.youtube import is_youtube_url
    from COMMANDS.cookies_cmd import is_youtube_cookie_error, is_youtube_geo_error, retry_download_with_different_cookies, retry_download_with_proxy
    
    playlist_indices = []
    playlist_msg_ids = []    
    found_type = None
    need_subs = False  # Will be determined once at the beginning
    user_id = message.chat.id
    logger.info(f"down_and_up called: url={url}, quality_key={quality_key}, format_override={format_override}, video_count={video_count}, video_start_with={video_start_with}")
    
    # ЖЕСТКО: Сохраняем оригинальный текст с диапазоном для фоллбэка
    original_message_text = message.text or message.caption or ""
    logger.info(f"[ORIGINAL TEXT] Saved for fallback: {original_message_text}")
    
    # Initialize retry guards early to avoid UnboundLocalError
    did_proxy_retry = False
    did_cookie_retry = False
    is_hls = False
    error_message_sent = False  # Flag to prevent duplicate error messages
    
    # Determine forced NSFW via user tags
    try:
        _u, _s, _e, _p, _tags, _tags_text, _err = extract_url_range_tags(original_message_text)
        user_forced_nsfw = any(t.lower() in ("#nsfw", "#porn") for t in (_tags or []))
    except Exception:
        user_forced_nsfw = False
    
    # Check if format contains /bestaudio (audio-only format)
    if format_override and '/bestaudio' in format_override:
        logger.info(f"Audio-only format detected in down_and_up: {format_override}, redirecting to down_and_audio")
        from DOWN_AND_UP.down_and_audio import down_and_audio
        down_and_audio(app, message, url, tags_text, quality_key=quality_key, format_override=format_override, cookies_already_checked=cookies_already_checked)
        return
    
    # Check if LINK mode is enabled - if yes, get direct link instead of downloading
    try:
        from DOWN_AND_UP.always_ask_menu import get_link_mode
        if get_link_mode(user_id):
            logger.info(f"LINK mode enabled for user {user_id}, getting direct link instead of downloading")
            
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
                response = Messages.DIRECT_LINK_OBTAINED_MSG
                response += Messages.TITLE_FIELD_MSG.format(title=title)
                if duration > 0:
                    response += Messages.DURATION_FIELD_MSG.format(duration=duration)
                response += Messages.FORMAT_FIELD_MSG.format(format_spec=format_spec)
                
                if video_url:
                    response += Messages.VIDEO_STREAM_FIELD_MSG.format(video_url=video_url)
                
                if audio_url:
                    response += Messages.AUDIO_STREAM_FIELD_MSG.format(audio_url=audio_url)
                
                if not video_url and not audio_url:
                    response += Config.FAILED_STREAM_LINKS_MSG
                
                # Send response
                app.send_message(
                    user_id, 
                    response, 
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                send_to_logger(message, Messages.DIRECT_LINK_EXTRACTED_DOWN_UP_LOG_MSG.format(user_id=user_id, url=url))
                
            else:
                error_msg = result.get('error', 'Unknown error')
                app.send_message(
                    user_id,
                    Config.ERROR_GETTING_LINK_MSG.format(error=error_msg),
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                
                log_error_to_channel(message, Messages.DIRECT_LINK_FAILED_DOWN_UP_LOG_MSG.format(user_id=user_id, url=url, error=error_msg), url)
            
            return
    except Exception as e:
        logger.error(f"Error checking LINK mode for user {user_id}: {e}")
        # Continue with normal download if LINK mode check fails
    subs_enabled = is_subs_enabled(user_id)
    if subs_enabled and is_youtube_url(url):
        found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        # Determine subtitle availability once here
        need_subs = determine_need_subs(subs_enabled, found_type, user_id)
        
        if need_subs:
            available_langs = _subs_check_cache.get(
                f"{url}_{user_id}_{'auto' if found_type == 'auto' else 'normal'}_langs",
                []
            )
            # First, download the subtitles separately
            user_dir = os.path.join("users", str(user_id))
            video_dir = user_dir
            subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                        
            if not subs_path:
                app.send_message(user_id, Config.SUBTITLES_FAILED_MSG, reply_parameters=ReplyParameters(message_id=message.id))
                need_subs = False  # Reset if download failed

    # We define a playlist not only by the number of videos, but also by the presence of a range in the URL
    original_text = message.text or message.caption or ""
    is_playlist = video_count > 1 or is_playlist_with_range(original_text)
    requested_indices = list(range(video_start_with, video_start_with + video_count)) if is_playlist else []
    cached_videos = {}
    uncached_indices = []
    if quality_key and is_playlist:
        # Check if Always Ask mode is enabled - if yes, skip cache completely
        if not is_subs_always_ask(user_id):
            # Check if content is NSFW before looking in cache
            from HELPERS.porn import is_porn
            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
            
            if not is_nsfw:
                cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, requested_indices)
                logger.info(f"[VIDEO CACHE] Checking cache for regular playlist: url={url}, quality={quality_key}")
            else:
                logger.info(f"[VIDEO CACHE] Skipping cache check for NSFW playlist: url={url}, quality={quality_key}")
        
        uncached_indices = [i for i in requested_indices if i not in cached_videos]
        # First, repost the cached ones (skip if send_as_file is enabled)
        if cached_videos:
            # Check if send_as_file is enabled - if so, skip cache repost
            from COMMANDS.args_cmd import get_user_args
            user_args = get_user_args(user_id)
            send_as_file = user_args.get("send_as_file", False)
            
            if not send_as_file:
                for index in requested_indices:
                    if index in cached_videos:
                        try:
                            # For cached content, always use regular channel (no NSFW/PAID in cache)
                            from_chat_id = get_log_channel("video")
                            channel_type = "regular"
                            
                            logger.info(f"[VIDEO CACHE] Reposting video {index} from channel {from_chat_id} to user {user_id}, message_id={cached_videos[index]}")
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
                            logger.error(f"down_and_up: error reposting cached video index={index}: {e}")
            else:
                # If send_as_file is enabled, treat all indices as uncached
                logger.info(f"[VIDEO CACHE] send_as_file enabled for user {user_id}, skipping cache repost for playlist")
                uncached_indices = requested_indices
            
            if len(uncached_indices) == 0:
                app.send_message(user_id, Config.PLAYLIST_SENT_FROM_CACHE_MSG.format(cached=len(cached_videos), total=len(requested_indices)), reply_parameters=ReplyParameters(message_id=message.id))
                send_to_logger(message, LoggerMsg.PLAYLIST_VIDEOS_SENT_FROM_CACHE.format(quality=quality_key, user_id=user_id))
                return
            else:
                app.send_message(user_id, Config.CACHE_PARTIAL_MSG.format(cached=len(cached_videos), total=len(requested_indices)), reply_parameters=ReplyParameters(message_id=message.id))
        else:
            logger.info(f"[VIDEO CACHE] Skipping cache check for playlist because Always Ask mode is enabled: url={url}, quality={quality_key}")
            # Set all indices as uncached when Always Ask mode is enabled
            uncached_indices = requested_indices
    elif quality_key and not is_playlist:
        #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        subs_enabled = is_subs_enabled(user_id)
        # Use the already determined subtitle availability
        if not need_subs and not is_subs_always_ask(user_id):
            # Check if content is NSFW before looking in cache
            from HELPERS.porn import is_porn
            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
            
            cached_ids = None
            if not is_nsfw:
                cached_ids = get_cached_message_ids(url, quality_key)
                logger.info(f"[VIDEO CACHE] Checking cache for regular content: url={url}, quality={quality_key}")
            else:
                logger.info(f"[VIDEO CACHE] Skipping cache check for NSFW content: url={url}, quality={quality_key}")
            
            if cached_ids:
                # Check if send_as_file is enabled - if so, skip cache repost
                from COMMANDS.args_cmd import get_user_args
                user_args = get_user_args(user_id)
                send_as_file = user_args.get("send_as_file", False)
                
                if not send_as_file:
                    #found_type = None
                    try:
                        # For cached content, always use regular channel (no NSFW/PAID in cache)
                        from_chat_id = get_log_channel("video")
                        channel_type = "regular"
                        
                        logger.info(f"[VIDEO CACHE] Reposting video from channel {from_chat_id} to user {user_id}, message_ids={cached_ids}")
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
                        app.send_message(user_id, Config.VIDEO_SENT_FROM_CACHE_MSG, reply_parameters=ReplyParameters(message_id=message.id))
                        send_to_logger(message, LoggerMsg.VIDEO_SENT_FROM_CACHE.format(quality=quality_key, user_id=user_id))
                        return
                    except Exception as e:
                        logger.error(f"Error reposting video from cache: {e}")
                        # Use the already determined subtitle availability
                        if not need_subs:
                            _save_video_cache_with_logging(url, quality_key, [], original_text="", user_id=user_id)
                        else:
                            logger.info("Video with subs (subs.txt found) is not cached!")
                        # Don't show error message if we successfully got video from cache
                        # The video was already sent successfully in the try block
                else:
                    # If send_as_file is enabled, skip cache repost and continue with download
                    logger.info(f"[VIDEO CACHE] send_as_file enabled for user {user_id}, skipping cache repost for single video")
        else:
            if is_subs_always_ask(user_id):
                logger.info(f"[VIDEO CACHE] Skipping cache check because Always Ask mode is enabled: url={url}, quality={quality_key}")
            else:
                logger.info(f"[VIDEO CACHE] Skipping cache check because need_subs=True: url={url}, quality={quality_key}")
    else:
        logger.info(f"down_and_up: quality_key is None, skipping cache check")

    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    anim_thread = None
    stop_anim = threading.Event()
    download_started_msg_id = None
    proc_msg = None
    proc_msg_id = None
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
                proc_msg = safe_send_message(user_id, Config.RATE_LIMIT_WITH_TIME_MSG.format(time=time_str), message=message)
        else:
            proc_msg = safe_send_message(user_id, Config.RATE_LIMIT_NO_TIME_MSG, message=message)

        # We are trying to replace with "Download started"
        try:
            app.edit_message_text(
                chat_id=user_id,
                message_id=proc_msg.id,
                text=Messages.DOWNLOAD_STARTED_MSG,
                parse_mode=enums.ParseMode.HTML
            )
            try:
                from HELPERS.safe_messeger import schedule_delete_message
                download_started_msg_id = proc_msg.id
                schedule_delete_message(user_id, download_started_msg_id, delete_after_seconds=5)
            except Exception:
                pass
            # If you managed to replace, then there is no flood error
            if os.path.exists(flood_time_file):
                os.remove(flood_time_file)
        except FloodWait as e:
            # Update the counter
            wait_time = e.value
            os.makedirs(user_dir, exist_ok=True)
            with open(flood_time_file, 'w') as f:
                f.write(str(wait_time))
            return
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return

        # If there is no flood error, send a normal message
        proc_msg = app.send_message(user_id, Config.PROCESSING_MSG, reply_parameters=ReplyParameters(message_id=message.id))
        # Pin proc/status message for visibility
        try:
            app.pin_chat_message(user_id, proc_msg.id, disable_notification=True)
        except Exception:
            pass
        proc_msg_id = proc_msg.id
        error_message = ""
        status_msg = None
        status_msg_id = None
        hourglass_msg = None
        hourglass_msg_id = None
        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Check if there's enough disk space (estimate 2GB per video)
        user_dir_name = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_dir_name)

        # Оценка требуемого места: сначала берём из yt-dlp точный/приблизительный размер,
        # затем оцениваем по битрейту и длительности, в крайнем случае 2 ГБ.
        required_bytes = 2 * 1024 * 1024 * 1024
        try:
            from DOWN_AND_UP.yt_dlp_hook import get_video_formats
            info_probe = get_video_formats(url, user_id, cookies_already_checked=cookies_already_checked)
            size = 0
            if isinstance(info_probe, dict):
                size = info_probe.get('filesize') or info_probe.get('filesize_approx') or 0
                if not size:
                    # fallback по tbr*duration
                    tbr = info_probe.get('tbr') or 0  # total bitrate in Kbps
                    duration = info_probe.get('duration') or 0
                    if tbr and duration:
                        # tbr Kbps -> bytes/sec: tbr*1000/8, *duration
                        size = int((float(tbr) * 1000.0 / 8.0) * float(duration))
                    else:
                        # последний шанс: взять максимальный tbr из форматов
                        formats = info_probe.get('formats') or []
                        best_tbr = 0
                        for f in formats:
                            ftbr = f.get('tbr') or 0
                            if ftbr and ftbr > best_tbr:
                                best_tbr = ftbr
                        if best_tbr and duration:
                            size = int((float(best_tbr) * 1000.0 / 8.0) * float(duration))
            if size and size > 0:
                required_bytes = int(size * 1.2)  # 20% запас
        except Exception:
            pass

        if not check_disk_space(user_dir_name, required_bytes):
            send_to_user(message, Config.ERROR_NO_DISK_SPACE_MSG)
            return

        # Create user directory (subscription already checked in video_extractor)
        user_dir = os.path.join("users", str(user_id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir, exist_ok=True)

        # Reset of the flag of errors for the new launch of the playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # if use_default_format is True, then do not take from format.txt, but use default ones
        custom_format_path = os.path.join(user_dir_name, "format.txt")
        use_default_format = False
        if not format_override and os.path.exists(custom_format_path):
            with open(custom_format_path, "r", encoding="utf-8") as f:
                custom_format = f.read().strip()
            if custom_format == "ALWAYS_ASK":
                use_default_format = True
        if use_default_format:
            format_override = None

        # Get user's merge_output_format preference once
        from COMMANDS.args_cmd import get_user_ytdlp_args
        user_args = get_user_ytdlp_args(user_id, url)
        user_merge_format = user_args.get('merge_output_format', 'mp4')
        
        if format_override:
            attempts = [{'format': format_override, 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format}]
        else:
            # if use_default_format is True, then do not take from format.txt, but use default ones
            if use_default_format:
                attempts = [
                    {'format': 'bv*[vcodec*=avc1][height<=1080][height>720]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best', 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format, 'extract_flat': False},
                    {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                ]
            else:
                if os.path.exists(custom_format_path):
                    with open(custom_format_path, "r", encoding="utf-8") as f:
                        custom_format = f.read().strip()
                    if custom_format.lower() == "best":
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': False}]
                    else:
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format}]
                else:
                    attempts = [
                        {'format': 'bv*[vcodec*=avc1][height<=1080][height>720]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best',
                        'prefer_ffmpeg': True, 'merge_output_format': user_merge_format, 'extract_flat': False},
                        {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best/bv+ba/best',
                        'prefer_ffmpeg': True, 'merge_output_format': user_merge_format, 'extract_flat': False},
                        {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                    ]

        status_msg = safe_send_message(user_id, Config.VIDEO_PROCESSING_MSG, message=message)
        hourglass_msg = safe_send_message(user_id, Messages.PLEASE_WAIT_MSG, message=message)
        try:
            from HELPERS.safe_messeger import schedule_delete_message
            if status_msg and hasattr(status_msg, 'id'):
                schedule_delete_message(user_id, status_msg.id, delete_after_seconds=5)
        except Exception:
            pass
        # We save ID status messages
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Get info_dict to estimate the size of the selected quality
        try:
            ydl_opts = {
                'quiet': True,
                'extractor_args': {
                    'youtubetab': {'skip': ['authcheck']}
                }
            }
            user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
            if os.path.exists(user_cookie_path):
                ydl_opts['cookiefile'] = user_cookie_path
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                pre_info = ydl.extract_info(url, download=False)
            # Check that pre_info is not None
            if pre_info is None:
                logger.warning("pre_info is None, skipping size check")
                pre_info = {}
            elif 'entries' in pre_info and isinstance(pre_info['entries'], list) and pre_info['entries']:
                pre_info = pre_info['entries'][0]
        except Exception as e:
            logger.warning(f"Failed to extract info for size check: {e}")
            pre_info = {}

        # Find format for selected quality_key
        selected_format = None
        for f in pre_info.get('formats', []):
            w = f.get('width')
            h = f.get('height')
            if w and h:
                qk = get_quality_by_min_side(w, h)
                if str(qk) == str(quality_key):
                    selected_format = f
                    break

        # If you did not find the format, STOP downloading!
        #if not selected_format:
            #logger.warning(f"[SIZE CHECK] Could not determine format for quality_key={quality_key}. Download will not start.")
            #app.send_message(
                #user_id,
                #"Unable to determine the file size for the selected quality. Please try another quality or check your cookies.",
                #reply_to_message_id=message.id
            #)
            #return

        
        # Checking the limit
        #from _config import Config
        BYTES_IN_GIB = 1024 ** 3
        max_size_gb = getattr(Config, 'MAX_FILE_SIZE', 10)
        max_size_bytes = int(max_size_gb * BYTES_IN_GIB)
        # Get the file size
        if selected_format is None:
            logger.warning("selected_format is None, skipping size check")
            filesize = 0
            allowed = True  # Allow download if we can't determine the size
        else:
            filesize = selected_format.get('filesize') or selected_format.get('filesize_approx')
            if not filesize:
                # fallback on rating
                tbr = selected_format.get('tbr')
                duration = selected_format.get('duration')
                if tbr and duration:
                    filesize = float(tbr) * float(duration) * 125
                else:
                    width = selected_format.get('width')
                    height = selected_format.get('height')
                    duration = selected_format.get('duration')
                    if width and height and duration:
                        filesize = int(width) * int(height) * float(duration) * 0.07
                    else:
                        filesize = 0

            allowed = check_file_size_limit(selected_format, max_size_bytes=max_size_bytes, message=message)
        
        # Secure file size logging
        if filesize > 0:
            size_gb = filesize/(1024**3)
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, determined size={size_gb:.2f} GB, limit={max_size_gb} GB, allowed={allowed}")
        else:
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, size unknown, limit={max_size_gb} GB, allowed={allowed}")

        if not allowed:
            app.send_message(
                user_id,
                Config.ERROR_FILE_SIZE_LIMIT_MSG.format(limit=max_size_gb),
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            log_error_to_channel(message, Messages.SIZE_LIMIT_EXCEEDED.format(max_size_gb=max_size_gb), url)
            logger.warning(f"[SIZE CHECK] Download for quality_key={quality_key} was blocked due to size limit.")
            return
        else:
            logger.info(f"[SIZE CHECK] Download for quality_key={quality_key} is allowed and will proceed.")

        current_total_process = ""
        last_update = 0
        full_bar = "🟩" * 10
        first_progress_update = True  # Flag for tracking the first update
        progress_start_time = time.time()
        # One-time retry guards to avoid infinite retry loops across attempts
        # (already initialized at the beginning of the function)
        
        # Check if this is an HLS stream (needed for progress_func)
        # This will be updated later based on actual format detection
        is_hls = ("m3u8" in url.lower())

        def progress_func(d):
            nonlocal last_update, first_progress_update, is_hls
            # Check the timeout
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            
            # Calculate elapsed time and minutes passed
            elapsed = max(0, current_time - progress_start_time)
            minutes_passed = int(elapsed // 60)
            
            # Adaptive throttle: linear slow-down; after 1h fixed 90s
            if minutes_passed >= 60:
                interval = 90.0
            else:
                # 0-4 min: 3s, 5-9: 4s, ..., 55-59: 14s
                interval = 3.0 + max(0, minutes_passed // 5)
            
            if current_time - last_update < interval:
                return
                
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                # yt-dlp may provide only total_bytes_estimate for some sites
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                
                # For HLS, update progress data for cycle animation
                if is_hls and hasattr(progress_func, 'progress_data') and progress_func.progress_data:
                    progress_func.progress_data['downloaded_bytes'] = downloaded
                    progress_func.progress_data['total_bytes'] = total
                try:
                    # With the first renewal of progress, we delete the first posts Processing
                    if first_progress_update:
                        try:
                            # Боты не могут использовать get_chat_history, поэтому просто логируем
                            logger.info("Skipping message cleanup - bots cannot use get_chat_history")
                        except Exception as e:
                            logger.error(f"Error in message cleanup: {e}")
                        first_progress_update = False

                    progress_text = f"{current_total_process}\n{bar}   {percent:.1f}%"
                    logger.info(f"Updating progress for user {user_id}, message {proc_msg_id}: {progress_text}")
                    result = safe_edit_message_text(user_id, proc_msg_id, progress_text)
                    if result is None:
                        logger.warning(f"Failed to update progress message {proc_msg_id} for user {user_id} - message may have been deleted")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            elif d.get("status") == "finished":
                try:
                    safe_edit_message_text(user_id, proc_msg_id, Messages.VIDEO_DOWNLOAD_COMPLETE_MSG.format(process=current_total_process, bar=full_bar))
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            elif d.get("status") == "error":
                logger.error("Error occurred during download.")
                send_error_to_user(message, Messages.DOWNLOAD_ERROR_GENERIC)
            last_update = current_time

        successful_uploads = 0

        def try_download(url, attempt_opts):
            nonlocal current_total_process, error_message, did_cookie_retry, did_proxy_retry, is_hls, error_message_sent
            
            # Use original filename for first attempt
            original_outtmpl = os.path.join(user_dir_name, "%(title)s.%(ext)s")
            
            # First try with original filename
            common_opts = {
                'playlist_items': str(current_index),
                'outtmpl': original_outtmpl,
                'postprocessors': [
                    {'key': 'EmbedThumbnail'},
                    {'key': 'FFmpegMetadata'}
                ],
                # Add restrictfilenames to sanitize output filename
                'restrictfilenames': True,
                'extractor_args': {
                    'generic': {'impersonate': ['chrome']},
                    'youtubetab': {'skip': ['authcheck']}
                },
                'referer': url,
                'geo_bypass': True,
                'check_certificate': False,
                'live_from_start': True
                #'socket_timeout': 60,  # Increase socket timeout
                #'retries': 15,  # Increase retries
                #'fragment_retries': 15,  # Increase fragment retries
                #'http_chunk_size': 5242880,  # 5MB chunks for better stability
                #'buffersize': 2048,  # Increase buffer size
                #'sleep_interval': 2,  # Sleep between requests
                #'max_sleep_interval': 10,  # Max sleep between requests
                #'read_timeout': 60,  # Read timeout
                #'connect_timeout': 30  # Connect timeout
            }
            
            # Add match_filter only if domain is not in NO_FILTER_DOMAINS
            if not is_no_filter_domain(url):
                # Use smart filter that allows downloads when duration is unknown
                common_opts['match_filter'] = create_smart_match_filter()
            else:
                logger.info(f"Skipping match_filter for domain in NO_FILTER_DOMAINS: {url}")
            
            # Add user's custom yt-dlp arguments
            from COMMANDS.args_cmd import get_user_ytdlp_args, log_ytdlp_options
            user_args = get_user_ytdlp_args(user_id, url)
            if user_args:
                common_opts.update(user_args)
            
            # Log final yt-dlp options for debugging
            log_ytdlp_options(user_id, common_opts, "video_download")
            
            # Check subtitle availability for YouTube videos (but don't download them here)
            if is_youtube_url(url):
                subs_lang = get_user_subs_language(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                if subs_lang and subs_lang not in ["OFF"]:
                    # Check availability with AUTO mode
                    #available_langs = get_available_subs_languages(url, user_id, auto_only=auto_mode)
                    # Flexible check: search for an exact match or any language from the group
                    lang_prefix = subs_lang.split('-')[0]
                    found = False
                    for l in available_langs:
                        if l == subs_lang or l.startswith(subs_lang + '-') or l.startswith(subs_lang + '.') \
                           or l == lang_prefix or l.startswith(lang_prefix + '-') or l.startswith(lang_prefix + '.'):
                            found = True
                            break
                    if not found:
                        app.send_message(
                            user_id,
                            f"⚠️ Subtitles for {LANGUAGES[subs_lang]['flag']} {LANGUAGES[subs_lang]['name']} not found for this video. Download without subtitles.",
                            reply_parameters=ReplyParameters(message_id=message.id)
                        )
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                common_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                # Check if cookie.txt exists in the user's folder
                user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
                
                # For YouTube URLs, use optimized cookie logic - check existing first on user's URL, then retry if needed
                if is_youtube_url(url):
                    from COMMANDS.cookies_cmd import get_youtube_cookie_urls, test_youtube_cookies_on_url, _download_content
                    
                    # Always check existing cookies first on user's URL for maximum speed
                    if os.path.exists(user_cookie_path):
                        logger.info(f"Checking existing YouTube cookies on user's URL for user {user_id}")
                        if test_youtube_cookies_on_url(user_cookie_path, url):
                            common_opts['cookiefile'] = user_cookie_path
                            logger.info(f"Existing YouTube cookies work on user's URL for user {user_id} - using them")
                        else:
                            logger.info(f"Existing YouTube cookies failed on user's URL, trying to get new ones for user {user_id}")
                            cookie_urls = get_youtube_cookie_urls()
                            if cookie_urls:
                                success = False
                                for i, cookie_url in enumerate(cookie_urls, 1):
                                    try:
                                        logger.info(f"Trying YouTube cookie source {i}/{len(cookie_urls)} for user {user_id}")
                                        ok, status, content, err = _download_content(cookie_url, timeout=30)
                                        if ok and content and len(content) <= 100 * 1024:
                                            with open(user_cookie_path, "wb") as cf:
                                                cf.write(content)
                                            if test_youtube_cookies_on_url(user_cookie_path, url):
                                                common_opts['cookiefile'] = user_cookie_path
                                                logger.info(f"YouTube cookies from source {i} work on user's URL for user {user_id} - saved to user folder")
                                                success = True
                                                break
                                            else:
                                                if os.path.exists(user_cookie_path):
                                                    os.remove(user_cookie_path)
                                    except Exception as e:
                                        logger.error(f"Error processing YouTube cookie source {i} for user {user_id}: {e}")
                                        continue
                                if not success:
                                    common_opts['cookiefile'] = None
                                    logger.warning(f"All YouTube cookie sources failed for user {user_id}, will try without cookies")
                            else:
                                common_opts['cookiefile'] = None
                                logger.warning(f"No YouTube cookie sources configured for user {user_id}, will try without cookies")
                    else:
                        logger.info(f"No YouTube cookies found for user {user_id}, attempting to get new ones")
                        cookie_urls = get_youtube_cookie_urls()
                        if cookie_urls:
                            success = False
                            for i, cookie_url in enumerate(cookie_urls, 1):
                                try:
                                    logger.info(f"Trying YouTube cookie source {i}/{len(cookie_urls)} for user {user_id}")
                                    ok, status, content, err = _download_content(cookie_url, timeout=30)
                                    if ok and content and len(content) <= 100 * 1024:
                                        with open(user_cookie_path, "wb") as cf:
                                            cf.write(content)
                                        if test_youtube_cookies_on_url(user_cookie_path, url):
                                            common_opts['cookiefile'] = user_cookie_path
                                            logger.info(f"YouTube cookies from source {i} work on user's URL for user {user_id} - saved to user folder")
                                            success = True
                                            break
                                        else:
                                            if os.path.exists(user_cookie_path):
                                                os.remove(user_cookie_path)
                                except Exception as e:
                                    logger.error(f"Error processing YouTube cookie source {i} for user {user_id}: {e}")
                                    continue
                            if not success:
                                common_opts['cookiefile'] = None
                                logger.warning(f"All YouTube cookie sources failed for user {user_id}, will try without cookies")
                        else:
                            common_opts['cookiefile'] = None
                            logger.warning(f"No YouTube cookie sources configured for user {user_id}, will try without cookies")
                else:
                    # For non-YouTube URLs, use existing logic
                    if os.path.exists(user_cookie_path):
                        common_opts['cookiefile'] = user_cookie_path
                    else:
                        # If not in the user's folder, copy from the global folder
                        global_cookie_path = Config.COOKIE_FILE_PATH
                        if os.path.exists(global_cookie_path):
                            try:
                                user_dir = os.path.join("users", str(user_id))
                                create_directory(user_dir)
                                import shutil
                                shutil.copy2(global_cookie_path, user_cookie_path)
                                logger.info(f"Copied global cookie file to user {user_id} folder")
                                common_opts['cookiefile'] = user_cookie_path
                            except Exception as e:
                                logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                                common_opts['cookiefile'] = None
                        else:
                            common_opts['cookiefile'] = None
            
            # If this is not a playlist with a range, add --no-playlist to the URL with the list parameter
            if not is_playlist and 'list=' in url:
                common_opts['noplaylist'] = True
            
            # Always use progress_hooks, even for HLS
            common_opts['progress_hooks'] = [progress_func]
            # Respect MKV toggle: remux to mkv when MKV is ON; otherwise prefer mp4
            try:
                from COMMANDS.format_cmd import get_user_mkv_preference
                mkv_on = get_user_mkv_preference(user_id)
            except Exception:
                mkv_on = False

            # Adjust attempts' merge_output_format based on WEBM preference
            try:
                if mkv_on:
                    for _attempt in attempts:
                        if isinstance(_attempt, dict):
                            _attempt['merge_output_format'] = 'mkv'
                else:
                    for _attempt in attempts:
                        if isinstance(_attempt, dict) and 'merge_output_format' not in _attempt:
                            # Use user's preferred format
                            _attempt['merge_output_format'] = user_merge_format
            except Exception:
                pass

            ytdl_opts = {**common_opts, **attempt_opts}
            
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
                    logger.info(f"Force using proxy for download: {proxy_url}")
                else:
                    logger.warning("Proxy requested but proxy configuration is incomplete")
            else:
                # Add proxy configuration if needed for this domain
                from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
                ytdl_opts = add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)
            
            # Add PO token provider for YouTube domains
            ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
            
            # If MKV is ON, remux to mkv; else to mp4
            if mkv_on:
                ytdl_opts['remux_video'] = 'mkv'
            else:
                ytdl_opts['remux_video'] = 'mp4'
            try:
                logger.info(f"Starting yt-dlp extraction for URL: {url}")
                logger.info(f"yt-dlp options: {ytdl_opts}")
                
                # First, check if the requested format is available using the same method as always_ask_menu
                from DOWN_AND_UP.yt_dlp_hook import get_video_formats
                
                logger.info("Checking available formats...")
                check_info = get_video_formats(url, user_id, cookies_already_checked=cookies_already_checked, use_proxy=use_proxy)
                logger.info("Format check completed")
                
                # Check if requested format exists
                requested_format = attempt_opts.get('format', '')
                if requested_format and requested_format != 'best':
                    available_formats = check_info.get('formats', [])
                    format_found = False
                    
                    # Check if requested format is available
                    if requested_format.startswith('id:'):
                        # Check for specific format ID
                        requested_id = requested_format.split(':', 1)[1]
                        for fmt in available_formats:
                            if fmt.get('format_id') == requested_id:
                                format_found = True
                                logger.info(f"Format ID {requested_id} found: {fmt.get('ext', 'unknown')} {fmt.get('resolution', 'unknown')}")
                                break
                        
                        if not format_found:
                            logger.warning(f"Format ID {requested_id} not found for this video")
                            # Notify user and stop download
                            try:
                                available_ids = [fmt.get('format_id', 'unknown') for fmt in available_formats[:10]]
                                logger.info(f"Available format IDs: {available_ids}")
                                send_error_to_user(
                                    message,
                                    Messages.FORMAT_ID_NOT_FOUND_MSG.format(format_id=requested_id, available_ids=', '.join(available_ids[:10])) +
                                    f"Use /list command to see all available formats."
                                )
                                return None
                            except Exception as e:
                                logger.error(f"Error sending format not found message: {e}")
                            return None
                    elif 'av01' in requested_format:
                        # Check for AV1 format specifically
                        for fmt in available_formats:
                            vcodec = fmt.get('vcodec')
                            if vcodec and vcodec.startswith('av01'):
                                format_found = True
                                break
                        
                        if not format_found:
                            logger.warning(f"AV1 format requested but not available for this video")
                            
                            # Also check if there are any video formats at all
                            video_formats = [fmt for fmt in available_formats if fmt.get('vcodec') and not fmt.get('vcodec').startswith('images')]
                            if not video_formats:
                                logger.warning(f"No video formats available at all for this video")
                            # Notify user and stop download
                            try:
                                # Filter out non-video formats (like storyboards)
                                video_formats = [fmt for fmt in available_formats if fmt.get('vcodec') and not fmt.get('vcodec').startswith('images')]
                                
                                available_formats_list = []
                                for fmt in video_formats[:5]:
                                    vcodec = fmt.get('vcodec', 'unknown')
                                    height = fmt.get('height', 'unknown')
                                    if vcodec and vcodec != 'unknown':
                                        available_formats_list.append(f"• {vcodec} {height}p")
                                
                                formats_text = "\n".join(available_formats_list) if available_formats_list else "• No video formats available"
                                
                                safe_edit_message_text(user_id, proc_msg_id, 
                                    f"{current_total_process}\n{Messages.DOWN_UP_AV1_NOT_AVAILABLE_MSG.format(formats_text=formats_text)}")
                            except Exception as e:
                                logger.error(f"Failed to notify user about format unavailability: {e}")
                            
                            # Send error message to user
                            # Filter out non-video formats (like storyboards)
                            video_formats = [fmt for fmt in available_formats if fmt.get('vcodec') and not fmt.get('vcodec').startswith('images')]
                            
                            available_formats_list = []
                            for fmt in video_formats[:5]:
                                vcodec = fmt.get('vcodec', 'unknown')
                                height = fmt.get('height', 'unknown')
                                if vcodec and vcodec != 'unknown':
                                    available_formats_list.append(f"• {vcodec} {height}p")
                            
                            formats_text = "\n".join(available_formats_list) if available_formats_list else "• No video formats available"
                            
                            send_to_user(message, 
                                Messages.AV1_FORMAT_NOT_AVAILABLE_MSG.format(formats_text=formats_text) +
                                Messages.AV1_NOT_AVAILABLE_FORMAT_SELECT_MSG)
                            
                            return None
                
                # Try with proxy fallback if user proxy is enabled
                def extract_info_operation(opts):
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        logger.info("yt-dlp instance created, starting extract_info...")
                        info_dict = ydl.extract_info(url, download=False)
                        logger.info("extract_info completed successfully")
                        return info_dict
                
                from HELPERS.proxy_helper import try_with_proxy_fallback
                info_dict = try_with_proxy_fallback(ytdl_opts, url, user_id, extract_info_operation)
                if info_dict is None:
                    raise Exception("Failed to extract video information with all available proxies")
                if "entries" in info_dict:
                    entries = info_dict["entries"]
                    if not entries:
                        raise Exception(f"No videos found in playlist at index {current_index}")
                    if len(entries) > 1:  # If the video in the playlist is more than one
                        if current_index < len(entries):
                            info_dict = entries[current_index]
                        else:
                            raise Exception(f"Video index {current_index} out of range (total {len(entries)})")
                    else:
                        # If there is only one video in the playlist, just download it
                        info_dict = entries[0]  # Just take the first video

                # Detect HLS not only by URL/top-level protocol, but by requested formats too
                requested_formats = []
                try:
                    requested_formats = info_dict.get('requested_formats') or []
                except Exception:
                    requested_formats = []

                hls_in_requested = False
                for _rf in requested_formats:
                    proto = (_rf.get('protocol') or '').lower()
                    if 'm3u8' in proto or 'hls' in proto:
                        hls_in_requested = True
                        break

                if ("m3u8" in url.lower()) or (info_dict and info_dict.get("protocol") in ("m3u8", "m3u8_native")) or hls_in_requested:
                    is_hls = True
                    # Force ffmpeg for HLS and disable chunked HTTP to avoid Conflicting range on fragments
                    ytdl_opts["downloader"] = "ffmpeg"
                    ytdl_opts["hls_prefer_native"] = False
                    ytdl_opts["hls_use_mpegts"] = True
                    ytdl_opts.pop("http_chunk_size", None)
                    # Reduce parallelism for fragile HLS endpoints
                    ytdl_opts["concurrent_fragment_downloads"] = 1
                try:
                    if is_hls:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n<i>Detected HLS stream.\n📥 Downloading with progress tracking...</i>")
                    else:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n> <i>📥 Downloading using format: {ytdl_opts.get('format', 'default')}...</i>")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                
                logger.info("Starting download phase...")
                # Try with proxy fallback if user proxy is enabled
                def download_operation(opts):
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        if is_hls:
                            # For HLS, start cycle progress as fallback, but progress_func will override it if percentages are available
                            cycle_stop = threading.Event()
                            progress_data = {'downloaded_bytes': 0, 'total_bytes': 0}
                            cycle_thread = start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop, progress_data)
                            # Pass cycle_stop and progress_data to progress_func so it can update the cycle animation
                            progress_func.cycle_stop = cycle_stop
                            progress_func.progress_data = progress_data
                            try:
                                ydl.download([url])
                            finally:
                                cycle_stop.set()
                                cycle_thread.join(timeout=1)
                        else:
                            ydl.download([url])
                        return True
                
                from HELPERS.proxy_helper import try_with_proxy_fallback
                result = try_with_proxy_fallback(ytdl_opts, url, user_id, download_operation)
                if result is None:
                    raise Exception("Failed to download video with all available proxies")
                try:
                    safe_edit_message_text(user_id, proc_msg_id, Messages.VIDEO_DOWNLOAD_COMPLETE_MSG.format(process=current_total_process, bar=full_bar))
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                
                logger.info("Download completed successfully")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                nonlocal error_message
                error_message = str(e)
                logger.error(f"DownloadError: {error_message}")
                
                # Check for live stream detection
                if "LIVE_STREAM_DETECTED" in error_message:
                    live_stream_message = (
                        Messages.LIVE_STREAM_DETECTED_MSG +
                        "• You can see the final video length\n\n"
                        "Once the stream is completed, you'll be able to download it as a regular video."
                    )
                    send_error_to_user(message, live_stream_message)
                    return "LIVE_STREAM"
                
                # Check for postprocessing errors
                if "Postprocessing" in error_message and "Error opening output files" in error_message:
                    postprocessing_message = (
                        Messages.FILE_PROCESSING_ERROR_INVALID_CHARS_MSG +
                        "**Solutions:**\n"
                        "• Try downloading again - the system will use a safer filename\n"
                        "• If the problem persists, the video title may contain unsupported characters\n"
                        "• Consider using a different video source if available\n\n"
                        "The download will be retried automatically with a cleaned filename."
                    )
                    send_error_to_user(message, postprocessing_message)
                    logger.error(f"Postprocessing error: {error_message}")
                    return "POSTPROCESSING_ERROR"
                
                # Check for postprocessing errors with Invalid argument
                if "Postprocessing" in error_message and "Invalid argument" in error_message:
                    postprocessing_message = (
                        Messages.FILE_PROCESSING_ERROR_INVALID_ARG_MSG +
                        "**Possible causes:**\n"
                        "• Corrupted or incomplete download\n"
                        "• Unsupported file format or codec\n"
                        "• File system permissions issue\n"
                        "• Insufficient disk space\n\n"
                        "**Solutions:**\n"
                        "• Try downloading again - the system will retry with different settings\n"
                        "• Check if you have enough disk space\n"
                        "• Try a different quality or format\n"
                        "• If the problem persists, the video source may be corrupted\n\n"
                        "The download will be retried automatically."
                    )
                    send_error_to_user(message, postprocessing_message)
                    logger.error(f"Postprocessing error (Invalid argument): {error_message}")
                    return "POSTPROCESSING_ERROR"
                
                # Check for format not available error
                if "Requested format is not available" in error_message:
                    format_error_message = (
                        Messages.FORMAT_NOT_AVAILABLE_MSG +
                        "**Possible causes:**\n"
                        "• The video doesn't have the requested format (e.g., webm, mp4)\n"
                        "• The video quality is not available in the requested format\n"
                        "• The video source has limited format options\n\n"
                        "**Solutions:**\n"
                        "• Try downloading with a different quality setting\n"
                        "• Use the 'Always Ask' menu to see available formats\n"
                        "• Try changing your format preferences in /args settings\n"
                        "• The system will automatically try alternative formats\n\n"
                        "The download will be retried with available formats."
                    )
                    send_error_to_user(message, format_error_message)
                    logger.error(f"Format not available error: {error_message}")
                    return "FORMAT_NOT_AVAILABLE"
                
                
                
                # Auto-fallback to gallery-dl (/img) for all supported errors
                if should_fallback_to_gallery_dl(error_message, url):
                    try:
                        from COMMANDS.image_cmd import image_command
                        from HELPERS.safe_messeger import fake_message
                    except Exception as imp_e:
                        logger.error(f"Failed to import gallery-dl fallback handlers: {imp_e}")
                    else:
                        try:
                            safe_edit_message_text(user_id, proc_msg_id,
                                f"{current_total_process}\n🔄 yt-dlp failed, trying gallery-dl…")
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
                            
                            if tags_text:
                                fallback_text += f" {tags_text}"
                            
                            # Add NSFW tag if content is detected as NSFW
                            if is_nsfw and "#nsfw" not in fallback_text.lower():
                                fallback_text += " #nsfw"
                                logger.info(f"[FALLBACK] Added #nsfw tag for NSFW content: {url}")
                            
                            image_command(app, fake_message(fallback_text, user_id, original_chat_id=user_id))
                            logger.info(f"Triggered gallery-dl fallback via /img, is_nsfw={is_nsfw}, range={start_range}-{end_range}")
                            return "IMG"
                        except Exception as call_e:
                            logger.error(f"Failed to trigger gallery-dl fallback: {call_e}")
                
                # Проверяем, связана ли ошибка с региональными ограничениями YouTube
                if is_youtube_url(url):
                    if is_youtube_geo_error(error_message) and not did_proxy_retry:
                        logger.info(f"YouTube geo-blocked error detected for user {user_id}, attempting retry with proxy")
                        
                        # Пробуем скачать через прокси
                        retry_result = retry_download_with_proxy(
                            user_id, url, try_download, url, attempt_opts
                        )
                        
                        if retry_result is not None:
                            logger.info(f"Download retry with proxy successful for user {user_id}")
                            did_proxy_retry = True
                            return retry_result
                        else:
                            logger.warning(f"Download retry with proxy failed for user {user_id}")
                            did_proxy_retry = True
                
                # Send full error message with instructions immediately (only once)
                if not error_message_sent:
                    send_error_to_user(
                        message,                   
                        "<blockquote>Check <a href='https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites'>here</a> if your site supported</blockquote>\n"
                        "<blockquote>You may need <code>cookie</code> for downloading this video. First, clean your workspace via <b>/clean</b> command</blockquote>\n"
                        "<blockquote>For Youtube - get <code>cookie</code> via <b>/cookie</b> command. For any other supported site - send your own cookie (<a href='https://t.me/c/2303231066/18'>guide1</a>) (<a href='https://t.me/c/2303231066/22'>guide2</a>) and after that send your video link again.</blockquote>\n"
                        f"────────────────\n{Messages.DOWN_UP_ERROR_DOWNLOADING_MSG.format(error_message=error_message)}"
                    )
                    error_message_sent = True
                return None
            except Exception as e:
                error_message = str(e)
                logger.error(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
                # Auto-fallback to gallery-dl for obvious non-video cases
                emsg = str(e)
                if (
                    "No videos found in playlist" in emsg
                    or "Unsupported URL" in emsg
                ):
                    try:
                        from COMMANDS.image_cmd import image_command
                        from HELPERS.safe_messeger import fake_message
                    except Exception as imp_e:
                        logger.error(f"Failed to import gallery-dl fallback handlers (generic): {imp_e}")
                    else:
                        try:
                            safe_edit_message_text(user_id, proc_msg_id,
                                f"{current_total_process}\n🔄 yt-dlp failed, trying gallery-dl…")
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
                            
                            if tags_text:
                                fallback_text += f" {tags_text}"
                            
                            # Add NSFW tag if content is detected as NSFW
                            if is_nsfw and "#nsfw" not in fallback_text.lower():
                                fallback_text += " #nsfw"
                                logger.info(f"[FALLBACK] Added #nsfw tag for NSFW content: {url}")
                            
                            image_command(app, fake_message(fallback_text, user_id, original_chat_id=user_id))
                            logger.info(f"Triggered gallery-dl fallback via /img (generic), is_nsfw={is_nsfw}, range={start_range}-{end_range}")
                            return "IMG"
                        except Exception as call_e:
                            logger.error(f"Failed to trigger gallery-dl fallback (generic): {call_e}")
				
                # Check if this is a "No videos found in playlist" error
                if "No videos found in playlist" in str(e):
                    error_message = Messages.DOWN_UP_NO_VIDEOS_PLAYLIST_MSG.format(index=current_index + 1)
                    send_error_to_user(message, error_message)
                    logger.info(f"Stopping download: playlist item at index {current_index} (no video found)")
                    return "STOP"  # New special value for full stop
                
                # Check if this is a TikTok infinite loop error
                if "TikTok API keeps sending the same page" in str(e) and "infinite loop" in str(e):
                    error_message = Messages.VIDEO_TIKTOK_API_ERROR_SKIP_MSG.format(index=current_index + 1)
                    send_to_user(message, error_message)
                    logger.info(f"Skipping TikTok video at index {current_index} due to API error")
                    return "SKIP"  # Skip this video and continue with next

                send_to_user(message, Messages.UNKNOWN_ERROR_MSG.format(error=e))
                return None

        if is_playlist and quality_key:
            indices_to_download = uncached_indices
        else:
            indices_to_download = range(video_count)
        for idx, current_index in enumerate(indices_to_download):
            x = current_index - video_start_with  # Don't add quality if size is unknown
            total_process = f"""
<b>📶 Total Progress</b>
<blockquote><b>Video:</b> {idx + 1} / {len(indices_to_download)}</blockquote>
"""
            current_total_process = total_process

            # Determine rename_name based on the incoming playlist_name:
            if playlist_name and playlist_name.strip():
                # A new name for the playlist is explicitly set - let's use it
                rename_name = sanitize_filename(f"{playlist_name.strip()} - Part {idx + video_start_with}")
            else:
                # No new name set - extract name from metadata
                rename_name = None

            # Reset retry flags for each new item in playlist
            did_cookie_retry = False
            did_proxy_retry = False
            error_message_sent = False  # Reset error message flag for each playlist item

            info_dict = None
            skip_item = False
            stop_all = False
            
            # Define safe filename template for fallback
            timestamp = int(time.time())
            safe_outtmpl = os.path.join(user_dir_name, f"download_{timestamp}.%(ext)s")
            
            for attempt in attempts:
                result = try_download(url, attempt)
                
                # If download failed and it's a YouTube URL, try automatic cookie retry
                if result is None and is_youtube_url(url) and not did_cookie_retry:
                    logger.info(f"Video download failed for user {user_id}, attempting automatic cookie retry")
                    
                    # Try retry with different cookies
                    retry_result = retry_download_with_different_cookies(
                        user_id, url, try_download, url, attempt
                    )
                    
                    if retry_result is not None:
                        logger.info(f"Video download retry with different cookies successful for user {user_id}")
                        result = retry_result
                        did_cookie_retry = True
                    else:
                        logger.warning(f"All cookie retry attempts failed for user {user_id}")
                        did_cookie_retry = True
                if result == "STOP":
                    stop_all = True
                    break
                elif result == "SKIP":
                    skip_item = True
                    break
                elif result == "IMG":
                    # Gallery-dl fallback has been triggered; stop further video processing
                    logger.info("Stopping video workflow after gallery-dl fallback trigger")
                    return
                elif result is not None and isinstance(result, dict):
                    info_dict = result
                    break
                elif result is not None and isinstance(result, str):
                    # Handle string return values (like "POSTPROCESSING_ERROR")
                    logger.info(f"Download attempt returned string result: {result}")
                    if result == "POSTPROCESSING_ERROR":
                        # Try again with safe filename if this was the first attempt
                        if attempt == attempts[0]:  # First attempt failed
                            logger.info("First attempt failed with postprocessing error, retrying with safe filename")
                            # Modify the attempt to use safe filename
                            safe_attempt = attempt.copy()
                            safe_attempt['outtmpl'] = safe_outtmpl
                            safe_result = try_download(url, safe_attempt)
                            if safe_result is not None and isinstance(safe_result, dict):
                                info_dict = safe_result
                                break
                            elif safe_result is not None and isinstance(safe_result, str):
                                logger.info(f"Safe filename attempt also failed: {safe_result}")
                                continue
                        else:
                            # Already tried safe filename, skip this attempt
                            continue
                    else:
                        # Other string results, skip this attempt
                        continue

            if stop_all:
                logger.info(f"Stopping all downloads due to playlist error at index {current_index}")
                break

            if skip_item:
                logger.info(f"Skipping item at index {current_index} (no video content)")
                continue

            if info_dict is None:
                with playlist_errors_lock:
                    error_key = f"{user_id}_{playlist_name}"
                    if error_key not in playlist_errors:
                        playlist_errors[error_key] = True

                break

            successful_uploads += 1

            video_id = info_dict.get("id", None)
            original_video_title = info_dict.get("title", None)  # Original title with emojis
            full_video_title = info_dict.get("description", original_video_title)
            video_title = sanitize_filename(original_video_title) if original_video_title else "video"  # Sanitized for file operations

            # --- Use new centralized function for all tags ---
            tags_list = tags_text.split() if tags_text else []
            tags_text_final = generate_final_tags(url, tags_list, info_dict)
            save_user_tags(user_id, tags_text_final.split())

           # If rename_name is not set, set it equal to video_title
            if rename_name is None:
                rename_name = video_title

            dir_path = os.path.join("users", str(user_id))

            # Save the full name to a file
            full_title_path = os.path.join(dir_path, "full_title.txt")
            try:
                with open(full_title_path, "w", encoding="utf-8") as f:
                    f.write(full_video_title if full_video_title else original_video_title)
            except Exception as e:
                logger.error(f"Error saving full title: {e}")

            info_text = f"""
{total_process}
<b>📋 Video Info</b>
<blockquote><b>Number:</b> {idx + video_start_with}</blockquote>
<blockquote><b>Title:</b> {original_video_title}</blockquote>
<blockquote><b>ID:</b> {video_id}</blockquote>
"""

            try:
                safe_edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n{full_bar}   100.0%\n<i>☑️ Downloaded video.\n📤 Processing for upload...</i>")
            except Exception as e:
                logger.error(f"Status update error after download: {e}")

            dir_path = os.path.join("users", str(user_id))
            allfiles = os.listdir(dir_path)
            
            # Get user's preferred video format to determine file extensions
            from COMMANDS.args_cmd import get_user_ytdlp_args
            user_args = get_user_ytdlp_args(user_id, url)
            user_video_format = user_args.get('video_format', 'mp4')
            user_merge_format = user_args.get('merge_output_format', 'mp4')
            
            # Determine which format to look for based on user preferences
            # Priority: video_format > merge_output_format > default
            target_format = user_video_format if user_video_format != 'mp4' else user_merge_format
            
            # Define supported video extensions based on user preference
            if target_format == 'mp4':
                video_extensions = ('.mp4', '.m4v')
            elif target_format == 'webm':
                video_extensions = ('.webm',)
            elif target_format == 'mkv':
                video_extensions = ('.mkv',)
            elif target_format == 'avi':
                video_extensions = ('.avi',)
            elif target_format == 'mov':
                video_extensions = ('.mov',)
            elif target_format == 'flv':
                video_extensions = ('.flv',)
            elif target_format == '3gp':
                video_extensions = ('.3gp', '.3g2')
            elif target_format == 'ogv':
                video_extensions = ('.ogv', '.ogg')
            elif target_format == 'wmv':
                video_extensions = ('.wmv',)
            elif target_format == 'asf':
                video_extensions = ('.asf',)
            else:
                # Fallback to all supported formats
                video_extensions = ('.mp4', '.mkv', '.webm', '.ts', '.avi', '.mov', '.flv', '.3gp', '.ogv', '.wmv', '.asf')
            
            files = [fname for fname in allfiles if fname.endswith(video_extensions)]
            files.sort()
            
            # Log all found files for debugging
            logger.info(f"Found video files in {dir_path}: {files}")
            
            # If no files found with preferred format, try to find any video file
            if not files:
                logger.warning(f"No files found with preferred format {target_format}, searching for any video file")
                fallback_extensions = ('.mp4', '.mkv', '.webm', '.ts', '.avi', '.mov', '.flv', '.3gp', '.ogv', '.wmv', '.asf', '.m4v')
                files = [fname for fname in allfiles if fname.endswith(fallback_extensions)]
                files.sort()
                logger.info(f"Found video files with fallback search: {files}")
            
            if not files:
                send_error_to_user(message, Messages.SKIPPING_UNSUPPORTED_FILE_TYPE_MSG.format(index=idx + video_start_with))
                continue

            downloaded_file = files[0]
            logger.info(f"Selected downloaded file: {downloaded_file}")
            write_logs(message, url, downloaded_file)
            
            # Save original filename for subtitle search
            original_video_filename = downloaded_file
            original_video_path = os.path.join(dir_path, original_video_filename)

            if rename_name == video_title:
                caption_name = original_video_title  # Original title for caption
                # Clean up the filename by removing common subtitle indicators
                cleaned_title = original_video_title
                # Remove common subtitle indicators from the title
                subtitle_indicators = [
                    " (English subtitles)",
                    " (English)",
                    " (Subtitles)",
                    " (Subs)",
                    " [English subtitles]",
                    " [English]",
                    " [Subtitles]",
                    " [Subs]",
                    " - English subtitles",
                    " - English",
                    " - Subtitles",
                    " - Subs"
                ]
                for indicator in subtitle_indicators:
                    cleaned_title = cleaned_title.replace(indicator, "")
                
                # Use cleaned title for filename
                final_name = sanitize_filename(cleaned_title + os.path.splitext(downloaded_file)[1])
                if final_name != downloaded_file:
                    old_path = os.path.join(dir_path, downloaded_file)
                    new_path = os.path.join(dir_path, final_name)
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
                old_path = os.path.join(dir_path, downloaded_file)
                new_path = os.path.join(dir_path, final_name)

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
                    caption_name = original_video_title  # Original title for caption

            user_vid_path = os.path.join(dir_path, final_name)
            if final_name.lower().endswith((".webm", ".ts")):
                try:
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{info_text}\n{full_bar}   100.0%\nConverting video using ffmpeg... ⏳")
                except Exception as e:
                    logger.error(f"Error updating status before conversion: {e}")

                mp4_basename = sanitize_filename(os.path.splitext(final_name)[0]) + ".mp4"
                mp4_file = os.path.join(dir_path, mp4_basename)

                # Get FFmpeg path using the common function
                from DOWN_AND_UP.ffmpeg import get_ffmpeg_path
                ffmpeg_path = get_ffmpeg_path()
                if not ffmpeg_path:
                    send_error_to_user(message, Messages.FFMPEG_NOT_FOUND_MSG)
                    break
                
                ffmpeg_cmd = [
                    ffmpeg_path,
                    "-y",
                    "-i", user_vid_path,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    mp4_file
                ]
                try:
                    result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    os.remove(user_vid_path)
                    user_vid_path = mp4_file
                    final_name = mp4_basename
                except subprocess.CalledProcessError as e:
                    error_details = f"Return code: {e.returncode}"
                    if e.stderr:
                        error_details += f"\nError output: {e.stderr[:500]}"
                    if e.stdout:
                        error_details += f"\nStandard output: {e.stdout[:500]}"
                    
                    # Check for specific FFmpeg errors
                    if "Invalid argument" in str(e.stderr):
                        error_message = Messages.DOWN_UP_VIDEO_CONVERSION_FAILED_INVALID_MSG
                        error_message += (
                            "**Possible causes:**\n"
                            "• Unsupported video codec or format\n"
                            "• Corrupted source file\n"
                            "• Incompatible video parameters\n"
                            "• Insufficient system resources\n\n"
                            "**Solutions:**\n"
                            "• Try downloading with a different quality\n"
                            "• Check if the source video is corrupted\n"
                            "• Try a different video source if available\n"
                            "• The original file will be sent without conversion\n\n"
                            f"**Technical details:** {error_details}"
                        )
                    else:
                        error_message = Messages.DOWN_UP_VIDEO_CONVERSION_FAILED_MSG
                        error_message += (
                            "**Solutions:**\n"
                            "• Try downloading with a different quality\n"
                            "• The original file will be sent without conversion\n"
                            "• If the problem persists, try a different video source\n\n"
                            f"**Technical details:** {error_details}"
                        )
                    
                    send_error_to_user(message, error_message)
                    logger.error(f"FFmpeg conversion failed: {error_details}")
                    break
                except Exception as e:
                    send_error_to_user(message, Messages.CONVERSION_TO_MP4_FAILED_MSG.format(error=e))
                    break

            after_rename_abs_path = os.path.abspath(user_vid_path)
            # --- YouTube thumbnail logic (priority over ffmpeg) ---
            youtube_thumb_path = None
            thumb_dir = None
            duration = 0
            
            # Try to download YouTube thumbnail first
            if ("youtube.com" in url or "youtu.be" in url):
                try:
                    yt_id = video_id or None
                    if not yt_id:
                        try:
                            yt_id = extract_youtube_id(url)
                        except Exception:
                            yt_id = None
                    if yt_id:
                        youtube_thumb_path = os.path.join(dir_path, f"yt_thumb_{yt_id}.jpg")
                        download_thumbnail(yt_id, youtube_thumb_path, url)
                        if os.path.exists(youtube_thumb_path):
                            thumb_dir = youtube_thumb_path
                            logger.info(f"Using YouTube thumbnail: {youtube_thumb_path}")
                except Exception as e:
                    logger.warning(f"YouTube thumbnail download failed: {e}")
            # If not YouTube or YouTube thumb not found, try universal thumbnail downloader
            if not thumb_dir:
                try:
                    universal_thumb_path = os.path.join(dir_path, "universal_thumb.jpg")
                    if download_universal_thumbnail(url, universal_thumb_path):
                        if os.path.exists(universal_thumb_path):
                            thumb_dir = universal_thumb_path
                            logger.info(f"Using universal thumbnail: {universal_thumb_path}")
                except Exception as e:
                    logger.info(f"Universal thumbnail not available: {e}")
            
            # Get video duration (always needed)
            try:
                width, height, duration = get_video_info_ffprobe(user_vid_path)
                if duration == 0:
                    logger.warning("Failed to get video duration via get_video_info_ffprobe, trying direct ffmpeg")
                    # Get FFmpeg path using the common function
                    from DOWN_AND_UP.ffmpeg import get_ffmpeg_path
                    ffmpeg_path = get_ffmpeg_path()
                    if not ffmpeg_path:
                        logger.error("ffmpeg not found in PATH or project directory.")
                        duration = 0
                    else:
                        ffmpeg_duration_command = [
                            ffmpeg_path, "-i", user_vid_path, "-f", "null", "-"
                        ]
                        result = subprocess.run(ffmpeg_duration_command, capture_output=True, text=True, timeout=int(30), encoding='utf-8', errors='replace')
                        output = result.stderr  # ffmpeg outputs info to stderr
                        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
                        if duration_match:
                            hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
                            duration = int(hours * 3600 + minutes * 60 + seconds + centiseconds / 100)
            except Exception as e:
                logger.warning(f"Failed to get video duration: {e}")
                duration = 0
            
            # Use ffmpeg thumbnail only as fallback (when both YouTube/universal thumbnails failed)
            if not thumb_dir:
                result = get_duration_thumb(message, dir_path, user_vid_path, sanitize_filename(caption_name))
                if result is None:
                    logger.warning("Failed to create ffmpeg thumbnail fallback")
                    thumb_dir = None
                else:
                    duration_from_ffmpeg, thumb_dir_ffmpeg = result
                    thumb_dir = thumb_dir_ffmpeg
                    if duration == 0:  # Use duration from ffmpeg if we couldn't get it with ffprobe
                        duration = duration_from_ffmpeg
                    logger.info(f"Using ffmpeg thumbnail fallback: {thumb_dir}")
            
            # Check for the existence of a preview and create a default one if needed
            if thumb_dir and not os.path.exists(thumb_dir):
                logger.warning(f"Thumbnail not found at {thumb_dir}, creating default")
                create_default_thumbnail(os.path.join(dir_path, "default_thumb.jpg"))
                thumb_dir = os.path.join(dir_path, "default_thumb.jpg")
                if not os.path.exists(thumb_dir):
                    logger.warning("Failed to create default thumbnail, continuing without thumbnail")
                    thumb_dir = None

            video_size_in_bytes = os.path.getsize(user_vid_path)
            video_size = humanbytes(int(video_size_in_bytes))
            max_size = get_user_split_size(user_id)  # 1.95 GB - close to Telegram's 2GB limit with 50MB safety margin
            if int(video_size_in_bytes) > max_size:
                safe_edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n{full_bar}   100.0%\n<i>⚠️ Your video size ({video_size}) is too large.</i>\n<i>Splitting file...</i> ✂️")
                returned = split_video_2(dir_path, sanitize_filename(caption_name), after_rename_abs_path, int(video_size_in_bytes), max_size, int(duration))
                caption_lst = returned.get("video")
                path_lst = returned.get("path")
                # Accumulate all IDs of split video parts
                split_msg_ids = []
                for p in range(len(caption_lst)):
                    part_result = get_duration_thumb(message, dir_path, path_lst[p], sanitize_filename(caption_lst[p]))
                    if part_result is None:
                        continue
                    part_duration, splited_thumb_dir = part_result
                    # --- TikTok: Don't Pass Title ---
                    video_msg = send_videos(message, path_lst[p], '' if force_no_title else caption_lst[p], part_duration, splited_thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                    if not video_msg:
                        logger.error("send_videos returned None for split part; skipping cache save for this part")
                        continue
                    #found_type = None
                    # Note: Forwarding to log channels is now handled in send_videos function
                    # We need to get the forwarded message IDs from the log channel for caching
                    try:
                        # Determine the correct log channel based on content type
                        from HELPERS.porn import is_porn
                        is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                        logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                        is_paid = is_nsfw and is_private_chat
                        logger.info(f"[VIDEO CACHE] URL analysis: url={url}, is_nsfw={is_nsfw}, is_private_chat={is_private_chat}, is_paid={is_paid}")
                        already_forwarded_to_log = False
                        
                        # Handle different content types according to new logic
                        if is_paid:
                            # For NSFW content in private chat, send to both channels but don't cache
                            # For NSFW content in private chat, send_videos already sent paid media to user
                            # We need to send paid copy to LOGS_PAID_ID and open copy to LOGS_NSWF_ID for history
                            
                            # Send to LOGS_NSFW_ID (for history) - send open copy, not paid media
                            # Send paid copy to LOGS_PAID_ID
                            log_channel_paid = get_log_channel("video", paid=True)
                            try:
                                # Forward the paid video to LOGS_PAID_ID
                                safe_forward_messages(log_channel_paid, user_id, [video_msg.id])
                                logger.info(f"down_and_up: NSFW content paid copy sent to PAID channel")
                            except Exception as e:
                                logger.error(f"down_and_up: failed to send paid copy to PAID channel: {e}")
                            
                            # Send open copy to LOGS_NSWF_ID for history
                            log_channel_nsfw = Config.LOGS_NSFW_ID
                            try:
                                # Get video dimensions for proper aspect ratio
                                try:
                                    v_w, v_h, v_dur = get_video_info_ffprobe(path_lst[p])
                                except Exception:
                                    v_w, v_h, v_dur = width, height, part_duration
                                
                                # Create open copy for history (without stars) - send directly to NSFW channel
                                open_video_msg = app.send_video(
                                    chat_id=log_channel_nsfw,
                                    video=path_lst[p],
                                    caption=caption_lst[p],
                                    duration=int(v_dur) if v_dur else part_duration,
                                    width=int(v_w) if v_w else width,
                                    height=int(v_h) if v_h else height,
                                    thumb=splited_thumb_dir,
                                    reply_parameters=ReplyParameters(message_id=message.id)
                                )
                                logger.info(f"down_and_up: NSFW content open copy sent to NSFW channel for history")
                                already_forwarded_to_log = True
                            except Exception as e:
                                logger.error(f"down_and_up: failed to send open copy to NSFW channel: {e}")
                            
                            # Don't cache NSFW content
                            logger.info(f"down_and_up: NSFW content sent to user (paid) and NSFW channel (open copy), not cached")
                            forwarded_msgs = None
                            
                        elif is_nsfw:
                            # NSFW content in groups -> LOGS_NSFW_ID only
                            log_channel = Config.LOGS_NSFW_ID
                            try:
                                safe_forward_messages(log_channel, user_id, [video_msg.id])
                                logger.info(f"down_and_up: NSFW content sent to NSFW channel")
                                already_forwarded_to_log = True
                            except Exception as e:
                                logger.error(f"down_and_up: failed to forward to NSFW channel: {e}")
                            
                            # Don't cache NSFW content
                            logger.info(f"down_and_up: NSFW content sent to NSFW channel, not cached")
                            forwarded_msgs = None
                            
                        else:
                            # Regular content -> LOGS_VIDEO_ID and cache
                            log_channel = get_log_channel("video")
                            forwarded_msgs = safe_forward_messages(log_channel, user_id, [video_msg.id])
                        logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                        if forwarded_msgs:
                            logger.info(f"down_and_up: collecting forwarded message IDs for split video: {[m.id for m in forwarded_msgs]}")
                            if is_playlist:
                                # For playlists, save to playlist cache with index
                                current_video_index = x + video_start_with
                                rounded_quality_key = quality_key
                                try:
                                    if quality_key.endswith('p'):
                                        rounded_quality_key = f"{ceil_to_popular(int(quality_key[:-1]))}p"
                                except Exception:
                                    pass
                                # Use the already determined subtitle availability
                                if not need_subs:
                                    # Only cache regular content (not NSFW)
                                    if not is_nsfw:
                                        save_to_playlist_cache(get_clean_playlist_url(url), rounded_quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info(f"NSFW content not cached (found_type={found_type}, auto_mode={auto_mode})")
                                else:
                                    logger.info(f"Video with subtitles is not cached (found_type={found_type}, auto_mode={auto_mode})")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), rounded_quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                            else:
                                # Accumulate IDs of parts for split video
                                split_msg_ids.extend([m.id for m in forwarded_msgs])
                        else:
                            logger.info(f"down_and_up: collecting video_msg.id for split video: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # Accumulate IDs of parts for split video
                                split_msg_ids.append(video_msg.id)
                    except Exception as e:
                        logger.error(f"Error forwarding video to logger: {e}")
                        logger.info(f"down_and_up: collecting video_msg.id after error for split video: {video_msg.id}")
                        if is_playlist:
                            # For playlists, save to playlist cache with video index
                            current_video_index = x + video_start_with
                            #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                            subs_enabled = is_subs_enabled(user_id)
                            auto_mode = get_user_subs_auto_mode(user_id)
                            need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                            if not need_subs:
                                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                            else:
                                logger.info("Video with subtitles (subs.txt found) is not cached!")
                            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                            logger.info(f"Checking the cache immediately after writing: {cached_check}")
                            playlist_indices.append(current_video_index)
                            playlist_msg_ids.append(video_msg.id)
                        else:
                            # Accumulate IDs of parts for split video
                            split_msg_ids.append(video_msg.id)
                            safe_edit_message_text(user_id, proc_msg_id,
                                f"{info_text}\n{full_bar}   100.0%\n<i>📤 Splitted part {p + 1} file uploaded</i>")
                    if p < len(caption_lst) - 1:
                        pass
                    if os.path.exists(splited_thumb_dir):
                        os.remove(splited_thumb_dir)
                    send_mediainfo_if_enabled(user_id, path_lst[p], message)
                    if os.path.exists(path_lst[p]):
                        os.remove(path_lst[p])
                
                # Save all parts of split video to cache after the loop is completed
                if split_msg_ids and not is_playlist:
                    # Remove duplicates
                    split_msg_ids = list(dict.fromkeys(split_msg_ids))
                    logger.info(f"down_and_up: saving all split video parts to cache: {split_msg_ids}")
                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                    subs_enabled = is_subs_enabled(user_id)
                    auto_mode = get_user_subs_auto_mode(user_id)
                    need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                    if not need_subs:
                        _save_video_cache_with_logging(url, quality_key, split_msg_ids, original_text=message.text or message.caption or "", user_id=user_id)
                    else:
                        logger.info(f"Split video with subtitles is not cached (found_type={found_type}, auto_mode={auto_mode})")
                if os.path.exists(thumb_dir):
                    os.remove(thumb_dir)
                if os.path.exists(user_vid_path):
                    os.remove(user_vid_path)
                success_msg = f"<b>✅ Upload complete</b> - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
                safe_edit_message_text(user_id, proc_msg_id, success_msg)
                send_to_logger(message, Messages.VIDEO_UPLOAD_COMPLETED_SPLITTING_LOG_MSG)
                break
            else:
                if final_name:
                    # Read the full name from the file
                    full_caption = caption_name
                    try:
                        if os.path.exists(full_title_path):
                            with open(full_title_path, "r", encoding="utf-8") as f:
                                full_caption = f.read().strip()
                    except Exception as e:
                        logger.error(f"Error reading full title: {e}")

                    # Check for preview existence before sending
                    if thumb_dir and not os.path.exists(thumb_dir):
                        logger.warning(f"Thumbnail not found before sending, creating default")
                        create_default_thumbnail(os.path.join(dir_path, "default_thumb.jpg"))
                        thumb_dir = os.path.join(dir_path, "default_thumb.jpg")
                        if not os.path.exists(thumb_dir):
                            logger.warning("Failed to create default thumbnail before sending, continuing without thumbnail")
                            thumb_dir = None

                    try:
                        # --- TikTok: Don't Pass Title ---
                        # Embed subtitles if needed (only for single videos, not playlists)
                        is_playlist_mode = video_count > 1 or is_playlist_with_range(original_text)
                        if not is_playlist_mode:
                            # Check the limits for subtitles
                            subs_enabled = is_subs_enabled(user_id)
                            # Get the real size of the video
                            try:
                                width, height, _ = get_video_info_ffprobe(after_rename_abs_path)
                                real_file_size = min(width, height)
                            except Exception as e:
                                logger.error(f"[FFPROBE BYPASS] Error while processing video {after_rename_abs_path}: {e}")
                                logger.error(traceback.format_exc())
                                width, height = 0, 0
                                real_file_size = 0
                            auto_mode = get_user_subs_auto_mode(user_id)
                            if subs_enabled and is_youtube_url(url) and min(width, height) <= Config.MAX_SUB_QUALITY:
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                # Use the helper function to determine subtitle availability
                                need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                if need_subs:
                                    
                                    # First, download the subtitles separately
                                    video_dir = os.path.dirname(after_rename_abs_path)
                                    subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                    
                                    if not subs_path:
                                        app.send_message(user_id, Config.SUBTITLES_FAILED_MSG, reply_parameters=ReplyParameters(message_id=message.id))
                                        #continue
                                    
                                    # Get the real size of the file after downloading
                                    real_file_size = os.path.getsize(after_rename_abs_path) if os.path.exists(after_rename_abs_path) else 0
                                    
                                    # Create info_dict with real data
                                    real_info = {
                                        'duration': duration,  # Real duration
                                        'filesize': real_file_size,  # Real file size
                                        'filesize_approx': real_file_size
                                    }
                                    
                                    if check_subs_limits(real_info, quality_key):
                                        status_msg = app.send_message(user_id, Messages.EMBEDDING_SUBTITLES_WARNING_MSG)
                                        def tg_update_callback(progress, eta):
                                            blocks = int(progress * 10)
                                            bar = '🟩' * blocks + '⬜️' * (10 - blocks)
                                            percent = int(progress * 100)
                                            try:
                                                app.edit_message_text(
                                                    chat_id=user_id,
                                                    message_id=status_msg.id,
                                                    text=f"🔥 Embedding subtitles...\n{bar} {percent}%\nETA: {eta} min"
                                                )
                                            except Exception as e:
                                                logger.error(f"Failed to update subtitle progress: {e}")
                                        # Embed subtitles and get the result
                                        logger.info(f"Calling embed_subs_to_video with path: {after_rename_abs_path}")
                                        logger.info(f"File exists check: {os.path.exists(after_rename_abs_path)}")
                                        logger.info(f"Original video path for subtitle search: {original_video_path}")
                                        # Use renamed path for video processing
                                        embed_result = embed_subs_to_video(after_rename_abs_path, user_id, tg_update_callback, app=app, message=message)
                                        try:
                                            if embed_result:
                                                app.edit_message_text(
                                                    chat_id=user_id,
                                                    message_id=status_msg.id,
                                                    text="Subtitles successfully embedded! ✅"
                                                )
                                            else:
                                                # Check if there are subtitle files
                                                video_dir = os.path.dirname(after_rename_abs_path)
                                                video_name = os.path.splitext(os.path.basename(after_rename_abs_path))[0]
                                                subs_files = glob.glob(os.path.join(video_dir, f"{video_name}*.srt"))
                                                
                                                if not subs_files:
                                                    app.edit_message_text(
                                                        chat_id=user_id,
                                                        message_id=status_msg.id,
                                                        text="⚠️ Subtitles not found for this video"
                                                    )
                                                else:
                                                    app.edit_message_text(
                                                        chat_id=user_id,
                                                        message_id=status_msg.id,
                                                        text="⚠️ Subtitles not embedded: exceeded size/duration limits"
                                                    )
                                        except Exception as e:
                                            logger.error(f"Failed to update subtitle progress (final): {e}")
                                    else:
                                        app.send_message(user_id, Messages.SUBTITLES_CANNOT_EMBED_LIMITS_MSG, reply_parameters=ReplyParameters(message_id=message.id))
                                else:
                                    app.send_message(user_id, Messages.SUBTITLES_NOT_AVAILABLE_LANGUAGE_MSG, reply_parameters=ReplyParameters(message_id=message.id))
                            
                            # Clean up subtitle files after embedding attempt
                            try:
                                cleanup_subtitle_files(user_id)
                            except Exception as e:
                                logger.error(f"Error cleaning up subtitle files: {e}")
                            
                            # Clear
                            clear_subs_check_cache()
                        video_msg = send_videos(message, after_rename_abs_path, '' if force_no_title else original_video_title, duration, thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                        if not video_msg:
                            logger.error("send_videos returned None for single video; aborting cache save for this item")
                            continue
                        
                        #found_type = None
                        try:
                            # Determine the correct log channel based on content type
                            from HELPERS.porn import is_porn
                            is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                            logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            # Detect if actually sent as paid media
                            try:
                                msg_is_paid = (
                                    getattr(video_msg, "media", None) == enums.MessageMediaType.PAID_MEDIA
                                ) or (getattr(video_msg, "paid_media", None) is not None)
                            except Exception:
                                msg_is_paid = False
                            is_paid = msg_is_paid or (is_nsfw and is_private_chat)
                            
                            # Handle different content types according to new logic
                            if is_paid:
                                # For NSFW content in private chat, send_videos already sent paid media to user
                                # We need to send paid copy to LOGS_PAID_ID and open copy to LOGS_NSWF_ID for history
                                
                                # Send paid copy to LOGS_PAID_ID
                                log_channel_paid = get_log_channel("video", paid=True)
                                try:
                                    # Forward the paid video to LOGS_PAID_ID
                                    safe_forward_messages(log_channel_paid, user_id, [video_msg.id])
                                    logger.info(f"down_and_up: NSFW content paid copy sent to PAID channel")
                                except Exception as e:
                                    logger.error(f"down_and_up: failed to send paid copy to PAID channel: {e}")
                                
                                # Send open copy to LOGS_NSWF_ID for history
                                log_channel_nsfw = Config.LOGS_NSFW_ID
                                try:
                                    # Get video dimensions for proper aspect ratio
                                    try:
                                        v_w, v_h, v_dur = get_video_info_ffprobe(after_rename_abs_path)
                                    except Exception:
                                        v_w, v_h, v_dur = width, height, duration
                                    
                                    # Create open copy for history (without stars) - send directly to NSFW channel
                                    open_video_msg = app.send_video(
                                        chat_id=log_channel_nsfw,
                                        video=after_rename_abs_path,
                                        caption='' if force_no_title else original_video_title,
                                        duration=int(v_dur) if v_dur else duration,
                                        width=int(v_w) if v_w else width,
                                        height=int(v_h) if v_h else height,
                                        thumb=thumb_dir,
                                        reply_parameters=ReplyParameters(message_id=message.id)
                                    )
                                    logger.info(f"down_and_up: NSFW content open copy sent to NSFW channel for history")
                                except Exception as e:
                                    logger.error(f"down_and_up: failed to send open copy to NSFW channel: {e}")
                                
                                # Don't cache NSFW content
                                logger.info(f"down_and_up: NSFW content sent to user (paid), PAID channel (paid copy), and NSFW channel (open copy), not cached")
                                forwarded_msgs = None
                                
                            elif is_nsfw:
                                # NSFW content in groups -> LOGS_NSFW_ID only
                                log_channel = Config.LOGS_NSFW_ID
                                forwarded_msgs = safe_forward_messages(log_channel, user_id, [video_msg.id])
                                # Don't cache NSFW content
                                logger.info(f"down_and_up: NSFW content sent to NSFW channel, not cached")
                                # Mark that we've already forwarded to log to avoid duplicates if return value is None
                                try:
                                    already_forwarded_to_log = True
                                except Exception:
                                    pass
                                forwarded_msgs = None
                            else:
                                # Regular content -> LOGS_VIDEO_ID and cache (but never for paid media)
                                if (
                                    getattr(video_msg, "media", None) == enums.MessageMediaType.PAID_MEDIA
                                ) or (getattr(video_msg, "paid_media", None) is not None):
                                    logger.info("down_and_up: skipping forward to LOGS_VIDEO_ID for paid media")
                                    forwarded_msgs = None
                                else:
                                    log_channel = get_log_channel("video")
                                    forwarded_msgs = safe_forward_messages(log_channel, user_id, [video_msg.id])
                            logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                            if forwarded_msgs:
                                logger.info(f"down_and_up: saving to cache with forwarded message IDs: {[m.id for m in forwarded_msgs]}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                    if not need_subs:
                                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                                else:
                                    # For single videos, save to regular cache
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                    if not need_subs:
                                        # Only cache regular content (not NSFW)
                                        if not is_nsfw:
                                            _save_video_cache_with_logging(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "", user_id=user_id)
                                        else:
                                            logger.info("NSFW content not cached")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                            else:
                                # If forwarding failed, try to forward manually and get log channel IDs
                                if 'already_forwarded_to_log' in locals() and already_forwarded_to_log:
                                    logger.info("down_and_up: already forwarded to log; skipping manual forward duplicate")
                                else:
                                    logger.info(f"down_and_up: forwarding failed, trying manual forward for video: {video_msg.id}")
                                    try:
                                        # Determine the correct log channel based on content type
                                        from HELPERS.porn import is_porn
                                        is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                                        logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        try:
                                            msg_is_paid = (
                                                getattr(video_msg, "media", None) == enums.MessageMediaType.PAID_MEDIA
                                            ) or (getattr(video_msg, "paid_media", None) is not None)
                                        except Exception:
                                            msg_is_paid = False
                                        is_paid = msg_is_paid or (is_nsfw and is_private_chat)
                                        
                                        # Handle different content types according to new logic
                                        if is_paid:
                                            # For NSFW content in private chat, send to both channels but don't cache
                                            # For NSFW content in private chat, send_videos already sent paid media to user
                                            # No need to forward to LOGS_PAID_ID as it's already sent
                                            
                                            # Send to LOGS_NSFW_ID (for history) - send open copy, not paid media
                                            # LOGS_PAID_ID and LOGS_NSWF_ID were already handled in the main logic above
                                            # No need to send again in manual forward
                                            
                                            # Don't cache NSFW content
                                            logger.info(f"down_and_up: NSFW content already sent to user (paid), PAID channel (paid copy), and NSFW channel (open copy), not cached (manual)")
                                            forwarded_msgs = None
                                            
                                        elif is_nsfw:
                                            # NSFW content in groups -> LOGS_NSFW_ID only
                                            log_channel = Config.LOGS_NSFW_ID
                                            try:
                                                safe_forward_messages(log_channel, user_id, [video_msg.id])
                                                logger.info(f"down_and_up: NSFW content sent to NSFW channel (manual)")
                                            except Exception as e:
                                                logger.error(f"down_and_up: failed to forward to NSFW channel (manual): {e}")
                                            
                                            # Don't cache NSFW content
                                            logger.info(f"down_and_up: NSFW content sent to NSFW channel, not cached (manual)")
                                            forwarded_msgs = None
                                            
                                        else:
                                            # Regular content -> LOGS_VIDEO_ID and cache (but never for paid media)
                                            if (
                                                getattr(video_msg, "media", None) == enums.MessageMediaType.PAID_MEDIA
                                            ) or (getattr(video_msg, "paid_media", None) is not None):
                                                logger.info("down_and_up: skipping forward to LOGS_VIDEO_ID for paid media (manual)")
                                                forwarded_msgs = None
                                            else:
                                                log_channel = get_log_channel("video")
                                                forwarded_msgs = safe_forward_messages(log_channel, user_id, [video_msg.id])
                                        if forwarded_msgs:
                                            logger.info(f"down_and_up: manual forward successful, got IDs: {[m.id for m in forwarded_msgs]}")
                                            if is_playlist:
                                                # For playlists, save to playlist cache with video index
                                                current_video_index = x + video_start_with
                                                subs_enabled = is_subs_enabled(user_id)
                                                auto_mode = get_user_subs_auto_mode(user_id)
                                                need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                                if not need_subs:
                                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                                else:
                                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                                playlist_indices.append(current_video_index)
                                                playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                                            else:
                                                # For single videos, save to regular cache
                                                subs_enabled = is_subs_enabled(user_id)
                                                auto_mode = get_user_subs_auto_mode(user_id)
                                                need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                                if not need_subs:
                                                    # Only cache regular content (not NSFW)
                                                    if not is_nsfw:
                                                        _save_video_cache_with_logging(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "", user_id=user_id)
                                                    else:
                                                        logger.info("NSFW content not cached (manual)")
                                                else:
                                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                        else:
                                            logger.error("Manual forward also failed, cannot cache video")
                                    except Exception as e:
                                        logger.error(f"Error in manual forward: {e}")
                        except Exception as e:
                            logger.error(f"Error forwarding video to logger: {e}")
                            # Try to forward manually even after error
                            try:
                                # Determine the correct log channel based on content type
                                from HELPERS.porn import is_porn
                                is_nsfw = is_porn(url, "", "", None) or user_forced_nsfw
                                logger.info(f"[FALLBACK] is_porn check for {url}: {is_porn(url, '', '', None)}, user_forced_nsfw: {user_forced_nsfw}, final is_nsfw: {is_nsfw}")
                                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                is_paid = is_nsfw and is_private_chat
                                
                                # Handle different content types according to new logic
                                if is_paid:
                                    # For NSFW content in private chat, send to both channels but don't cache
                                    # For NSFW content in private chat, send_videos already sent paid media to user
                                    # No need to forward to LOGS_PAID_ID as it's already sent
                                    
                                    # Send to LOGS_NSFW_ID (for history) - send open copy, not paid media
                                    # LOGS_PAID_ID was already handled in the main logic above
                                    # No need to send again in error recovery
                                    
                                    # Send open copy to LOGS_NSWF_ID for history
                                    log_channel_nsfw = Config.LOGS_NSFW_ID
                                    try:
                                        # Get video dimensions for proper aspect ratio
                                        try:
                                            v_w, v_h, v_dur = get_video_info_ffprobe(after_rename_abs_path)
                                        except Exception:
                                            v_w, v_h, v_dur = width, height, duration
                                        
                                        # Create open copy for history (without stars) - send directly to NSFW channel
                                        open_video_msg = app.send_video(
                                            chat_id=log_channel_nsfw,
                                            video=after_rename_abs_path,
                                            caption='' if force_no_title else original_video_title,
                                            duration=int(v_dur) if v_dur else duration,
                                            width=int(v_w) if v_w else width,
                                            height=int(v_h) if v_h else height,
                                            thumb=thumb_dir,
                                            reply_parameters=ReplyParameters(message_id=message.id)
                                        )
                                        logger.info(f"down_and_up: NSFW content open copy sent to NSFW channel for history (error recovery)")
                                    except Exception as e:
                                        logger.error(f"down_and_up: failed to send open copy to NSFW channel (error recovery): {e}")
                                    
                                    # Don't cache NSFW content
                                    logger.info(f"down_and_up: NSFW content already sent to user (paid), PAID channel (paid copy), and NSFW channel (open copy), not cached (error recovery)")
                                    forwarded_msgs = None
                                    
                                elif is_nsfw:
                                    # NSFW content in groups -> LOGS_NSFW_ID only
                                    log_channel = Config.LOGS_NSFW_ID
                                    try:
                                        safe_forward_messages(log_channel, user_id, [video_msg.id])
                                        logger.info(f"down_and_up: NSFW content sent to NSFW channel (error recovery)")
                                    except Exception as e:
                                        logger.error(f"down_and_up: failed to forward to NSFW channel (error recovery): {e}")
                                    
                                    # Don't cache NSFW content
                                    logger.info(f"down_and_up: NSFW content sent to NSFW channel, not cached (error recovery)")
                                    forwarded_msgs = None
                                    
                                else:
                                    # Regular content -> LOGS_VIDEO_ID and cache
                                    log_channel = get_log_channel("video")
                                    forwarded_msgs = safe_forward_messages(log_channel, user_id, [video_msg.id])
                                if forwarded_msgs:
                                    logger.info(f"down_and_up: manual forward after error successful, got IDs: {[m.id for m in forwarded_msgs]}")
                                    if is_playlist:
                                        # For playlists, save to playlist cache with video index
                                        current_video_index = x + video_start_with
                                        subs_enabled = is_subs_enabled(user_id)
                                        auto_mode = get_user_subs_auto_mode(user_id)
                                        need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                        if not need_subs:
                                            save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                        else:
                                            logger.info("Video with subtitles (subs.txt found) is not cached!")
                                        cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                        logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                        playlist_indices.append(current_video_index)
                                        playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                                    else:
                                        # For single videos, save to regular cache
                                        subs_enabled = is_subs_enabled(user_id)
                                        auto_mode = get_user_subs_auto_mode(user_id)
                                        need_subs = determine_need_subs(subs_enabled, found_type, user_id)
                                        if not need_subs:
                                            # Only cache regular content (not NSFW)
                                            if not is_nsfw:
                                                _save_video_cache_with_logging(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "", user_id=user_id)
                                            else:
                                                logger.info("NSFW content not cached (error recovery)")
                                        else:
                                            logger.info("Video with subtitles (subs.txt found) is not cached!")
                                else:
                                    logger.error("Manual forward after error also failed, cannot cache video")
                            except Exception as e2:
                                logger.error(f"Error in manual forward after error: {e2}")
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{info_text}\n{full_bar}   100.0%\n<b>🎞 Video duration:</b> <i>{TimeFormatter(duration * 1000)}</i>\n1 file uploaded.")
                        send_mediainfo_if_enabled(user_id, after_rename_abs_path, message)
                        
                        # Clean up video file and thumbnail
                        if os.path.exists(after_rename_abs_path):
                            os.remove(after_rename_abs_path)
                        if thumb_dir and os.path.exists(thumb_dir):
                            os.remove(thumb_dir)
                        pass
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        logger.error(traceback.format_exc())
                        send_error_to_user(message, Messages.ERROR_SENDING_VIDEO_MSG.format(error=str(e)))
                        continue
        if successful_uploads == len(indices_to_download):
            success_msg = f"<b>✅ Upload complete</b> - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
            send_to_logger(message, success_msg)

        if is_playlist and quality_key:
            total_sent = len(cached_videos) + successful_uploads
            app.send_message(user_id, Messages.PLAYLIST_VIDEOS_SENT_MSG.format(sent=total_sent, total=len(requested_indices)), reply_parameters=ReplyParameters(message_id=message.id))
            send_to_logger(message, Messages.PLAYLIST_VIDEOS_SENT_LOG_MSG.format(sent=total_sent, total=len(requested_indices), quality=quality_key, user_id=user_id))

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, Messages.DOWNLOAD_CANCELLED_TIMEOUT_MSG)
            log_error_to_channel(message, LoggerMsg.DOWNLOAD_TIMEOUT_LOG, url)
        else:
            logger.error(f"Error in video download: {e}")
            send_to_user(message, Messages.FAILED_DOWNLOAD_VIDEO_MSG.format(error=e))
        
        # Immediate cleanup of temporary status messages on error
        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
            if download_started_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[download_started_msg_id], revoke=True)
            stop_anim.set()
        except Exception:
            pass
        
        # Clean up temporary files on error
        try:
            cleanup_user_temp_files(user_id)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temp files after error for user {user_id}: {cleanup_error}")
    finally:
        set_active_download(user_id, False)
        clear_download_start_time(user_id)  # Clear the download start time
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # Clean up temporary files
        try:
            cleanup_user_temp_files(user_id)
        except Exception as e:
            logger.error(f"Error cleaning up temp files for user {user_id}: {e}")

        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}")
        # Also try to delete the 'Download started' message if it still exists
        try:
            if download_started_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[download_started_msg_id], revoke=True)
        except Exception:
            pass

        # --- ADDED: summary of cache after cycle ---
        if is_playlist and playlist_indices and playlist_msg_ids:
            #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
            subs_enabled = is_subs_enabled(user_id)
            auto_mode = get_user_subs_auto_mode(user_id)
            need_subs = determine_need_subs(subs_enabled, found_type, user_id)
            if not need_subs:
                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, playlist_indices, playlist_msg_ids, original_text=message.text or message.caption or "")
            else:
                logger.info("Video with subtitles (subs.txt found) is not cached!")
            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, playlist_indices)
            summary = "\n".join([f"Index {idx}: msg_id={cached_check.get(idx, '-')}" for idx in playlist_indices])
            logger.info(f"[SUMMARY] Playlist cache (quality {quality_key}):\n{summary}")

#########################################
