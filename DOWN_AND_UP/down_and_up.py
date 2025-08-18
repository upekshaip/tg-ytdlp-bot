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
from HELPERS.logger import logger, send_to_logger, send_to_user, send_to_all
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
from CONFIG.config import Config
from COMMANDS.subtitles_cmd import is_subs_enabled, check_subs_availability, get_user_subs_auto_mode, _subs_check_cache, download_subtitles_ytdlp, get_user_subs_language, clear_subs_check_cache
from COMMANDS.split_sizer import get_user_split_size
from COMMANDS.mediainfo_cmd import send_mediainfo_if_enabled
from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.normalizer import get_clean_playlist_url
from DATABASE.cache_db import get_cached_playlist_videos, get_cached_message_ids, save_to_video_cache, save_to_playlist_cache
from HELPERS.qualifier import get_quality_by_min_side
from HELPERS.logger import send_to_all  # Импорт в самом конце для гарантии видимости
from HELPERS.safe_messeger import safe_forward_messages  # Дублирующий импорт для устранения ошибки видимости

# Get app instance for decorators
app = get_app()

#@reply_with_keyboard
def down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=None, quality_key=None):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    playlist_indices = []
    playlist_msg_ids = []    
    found_type = None
    user_id = message.chat.id
    logger.info(f"down_and_up called: url={url}, quality_key={quality_key}, format_override={format_override}, video_count={video_count}, video_start_with={video_start_with}")
    subs_enabled = is_subs_enabled(user_id)
    if subs_enabled and is_youtube_url(url):
        found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        available_langs = _subs_check_cache.get(
            f"{url}_{user_id}_{'auto' if found_type == 'auto' else 'normal'}_langs",
            []
        )
        # First, download the subtitles separately
        user_dir = os.path.join("users", str(user_id))
        video_dir = user_dir
        subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                    
        if not subs_path:
            app.send_message(user_id, "⚠️ Failed to download subtitles", reply_to_message_id=message.id)
            #continue

    # We define a playlist not only by the number of videos, but also by the presence of a range in the URL
    original_text = message.text or message.caption or ""
    is_playlist = video_count > 1 or is_playlist_with_range(original_text)
    requested_indices = list(range(video_start_with, video_start_with + video_count)) if is_playlist else []
    cached_videos = {}
    uncached_indices = []
    if quality_key and is_playlist:
        cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, requested_indices)
        uncached_indices = [i for i in requested_indices if i not in cached_videos]
        # First, repost the cached ones
        if cached_videos:
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        app.forward_messages(
                            chat_id=user_id,
                            from_chat_id=Config.LOGS_ID,
                            message_ids=[cached_videos[index]]
                        )
                    except Exception as e:
                        logger.error(f"down_and_up: error reposting cached video index={index}: {e}")
            if len(uncached_indices) == 0:
                app.send_message(user_id, f"✅ Playlist videos sent from cache ({len(cached_videos)}/{len(requested_indices)} files).", reply_to_message_id=message.id)
                send_to_logger(message, f"Playlist videos sent from cache (quality={quality_key}) to user {user_id}")
                return
            else:
                app.send_message(user_id, f"📥 {len(cached_videos)}/{len(requested_indices)} videos sent from cache, downloading missing ones...", reply_to_message_id=message.id)
    elif quality_key and not is_playlist:
        #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        subs_enabled = is_subs_enabled(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
        if not need_subs:
            cached_ids = get_cached_message_ids(url, quality_key)
            if cached_ids:
                #found_type = None
                try:
                    app.forward_messages(
                        chat_id=user_id,
                        from_chat_id=Config.LOGS_ID,
                        message_ids=cached_ids
                    )
                    app.send_message(user_id, "✅ Video sent from cache.", reply_to_message_id=message.id)
                    send_to_logger(message, f"Video sent from cache (quality={quality_key}) to user {user_id}")
                    return
                except Exception as e:
                    logger.error(f"Error reposting video from cache: {e}")
                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                    subs_enabled = is_subs_enabled(user_id)
                    auto_mode = get_user_subs_auto_mode(user_id)
                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    if not need_subs:
                        save_to_video_cache(url, quality_key, [], clear=True)
                    else:
                        logger.info("Video with subs (subs.txt found) is not cached!")
                    app.send_message(user_id, "⚠️ Unable to get video from cache, starting new download...", reply_to_message_id=message.id)
    else:
        logger.info(f"down_and_up: quality_key is None, skipping cache check")

    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    anim_thread = None
    stop_anim = threading.Event()
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
        proc_msg = app.send_message(user_id, "🔄 Processing...", reply_to_message_id=message.id)
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

        # We only need disk space for one video at a time, since files are deleted after upload
        if not check_disk_space(user_dir_name, 2 * 1024 * 1024 * 1024):
            send_to_user(message, f"❌ Not enough disk space to download videos.")
            return

        check_user(message)

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

        if format_override:
            attempts = [{'format': format_override, 'prefer_ffmpeg': True, 'merge_output_format': 'mp4'}]
        else:
            # if use_default_format is True, then do not take from format.txt, but use default ones
            if use_default_format:
                attempts = [
                    {'format': 'bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best', 'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                    {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                ]
            else:
                if os.path.exists(custom_format_path):
                    with open(custom_format_path, "r", encoding="utf-8") as f:
                        custom_format = f.read().strip()
                    if custom_format.lower() == "best":
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': False}]
                    else:
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': True, 'merge_output_format': output_format}]
                else:
                    attempts = [
                        {'format': 'bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best',
                        'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                        {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best',
                        'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                        {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                    ]

        status_msg = app.send_message(user_id, "📽 Video is processing...")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Get info_dict to estimate the size of the selected quality
        try:
            ydl_opts = {
                'quiet': True,
                'extractor_args': {
                    'youtubetab': ['skip=authcheck']
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

            allowed = check_file_size_limit(selected_format, max_size_bytes=max_size_bytes)
        
        # Secure file size logging
        if filesize > 0:
            size_gb = filesize/(1024**3)
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, determined size={size_gb:.2f} GB, limit={max_size_gb} GB, allowed={allowed}")
        else:
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, size unknown, limit={max_size_gb} GB, allowed={allowed}")

        if not allowed:
            app.send_message(
                user_id,
                f"❌ The file size exceeds the {max_size_gb} GB limit. Please select a smaller file within the allowed size.",
                reply_to_message_id=message.id
            )
            send_to_logger(message, f"❌ The file size exceeds the {max_size_gb} GB limit. Please select a smaller file within the allowed size.")
            logger.warning(f"[SIZE CHECK] Download for quality_key={quality_key} was blocked due to size limit.")
            return
        else:
            logger.info(f"[SIZE CHECK] Download for quality_key={quality_key} is allowed and will proceed.")

        current_total_process = ""
        last_update = 0
        full_bar = "🟩" * 10
        first_progress_update = True  # Flag for tracking the first update

        def progress_func(d):
            nonlocal last_update, first_progress_update
            # Check the timaut
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            if current_time - last_update < 1.5:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                try:
                    # With the first renewal of progress, we delete the first posts Processing
                    if first_progress_update:
                        try:
                            # Боты не могут использовать get_chat_history, поэтому просто логируем
                            logger.info("Skipping message cleanup - bots cannot use get_chat_history")
                        except Exception as e:
                            logger.error(f"Error in message cleanup: {e}")
                        first_progress_update = False

                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            elif d.get("status") == "error":
                logger.error("Error occurred during download.")
                send_to_all(message, "❌ Sorry... Some error occurred during download.")
            last_update = current_time

        successful_uploads = 0

        def try_download(url, attempt_opts):
            nonlocal current_total_process, error_message
            
            common_opts = {
                'playlist_items': str(current_index),  # We use only current_index for playlists
                'outtmpl': os.path.join(user_dir_name, "%(title).50s.%(ext)s"),
                'postprocessors': [
                {
                   'key': 'EmbedThumbnail'   # equivalent to --embed-thumbnail
                },
                {
                   'key': 'FFmpegMetadata'   # equivalent to --add-metadata
                }                  
                ],                
                'extractor_args': {
                   'generic': ['impersonate=chrome'],
                   'youtubetab': ['skip=authcheck']
                },
                'referer': url,
                'geo_bypass': True,
                'check_certificate': False,
                'live_from_start': True,
                'socket_timeout': 60,  # Increase socket timeout
                'retries': 15,  # Increase retries
                'fragment_retries': 15,  # Increase fragment retries
                'http_chunk_size': 5242880,  # 5MB chunks for better stability
                'buffersize': 2048,  # Increase buffer size
                'sleep_interval': 2,  # Sleep between requests
                'max_sleep_interval': 10,  # Max sleep between requests
                'read_timeout': 60,  # Read timeout
                'connect_timeout': 30  # Connect timeout
            }
            
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
                            reply_to_message_id=message.id
                        )
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                common_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                # Check if cookie.txt exists in the user's folder
                user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
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
            
            is_hls = ("m3u8" in url.lower())
            if not is_hls:
                common_opts['progress_hooks'] = [progress_func]
            ytdl_opts = {**common_opts, **attempt_opts}
            try:
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
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

                if ("m3u8" in url.lower()) or (info_dict and info_dict.get("protocol") == "m3u8_native"):
                    is_hls = True
                    # if "format" in ytdl_opts:
                    # del ytdl_opts["format"]
                    ytdl_opts["downloader"] = "ffmpeg"
                    ytdl_opts["hls_use_mpegts"] = True
                try:
                    if is_hls:
                                        safe_edit_message_text(user_id, proc_msg_id,
                    f"{current_total_process}\n<i>Detected HLS stream.\n📥 Downloading...</i>")
                    else:
                                            safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\n> <i>📥 Downloading using format: {ytdl_opts.get('format', 'default')}...</i>")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    if is_hls:
                        cycle_stop = threading.Event()
                        cycle_thread = start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop)
                        try:
                            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                                ydl.download([url])
                        finally:
                            cycle_stop.set()
                            cycle_thread.join(timeout=1)
                    else:
                        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                            ydl.download([url])
                try:
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                nonlocal error_message
                error_message = str(e)
                logger.error(f"DownloadError: {error_message}")
                # Send full error message with instructions immediately
                send_to_all(
                    message,                   
                    "<blockquote>Check <a href='https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites'>here</a> if your site supported</blockquote>\n"
                    "<blockquote>You may need <code>cookie</code> for downloading this video. First, clean your workspace via <b>/clean</b> command</blockquote>\n"
                    "<blockquote>For Youtube - get <code>cookie</code> via <b>/download_cookie</b> command. For any other supported site - send your own cookie (<a href='https://t.me/c/2303231066/18'>guide1</a>) (<a href='https://t.me/c/2303231066/22'>guide2</a>) and after that send your video link again.</blockquote>\n"
                    f"────────────────\n❌ Error downloading: {error_message}"
                )
                return None
            except Exception as e:
                error_message = str(e)
                logger.error(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
				
                # Check if this is a "No videos found in playlist" error
                if "No videos found in playlist" in str(e):
                    error_message = f"❌ No videos found in playlist at index {current_index + 1}."
                    send_to_all(message, error_message)
                    logger.info(f"Stopping download: playlist item at index {current_index} (no video found)")
                    return "STOP"  # New special value for full stop

                send_to_user(message, f"❌ Unknown error: {e}")
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

            info_dict = None
            skip_item = False
            stop_all = False
            for attempt in attempts:
                result = try_download(url, attempt)
                if result == "STOP":
                    stop_all = True
                    break
                elif result == "SKIP":
                    skip_item = True
                    break
                elif result is not None:
                    info_dict = result
                    break

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
            files = [fname for fname in allfiles if fname.endswith(('.mp4', '.mkv', '.webm', '.ts'))]
            files.sort()
            
            # Log all found files for debugging
            logger.info(f"Found video files in {dir_path}: {files}")
            
            if not files:
                send_to_all(message, f"Skipping unsupported file type in playlist at index {idx + video_start_with}")
                continue

            downloaded_file = files[0]
            logger.info(f"Selected downloaded file: {downloaded_file}")
            write_logs(message, url, downloaded_file)
            
            # Save original filename for subtitle search
            original_video_filename = downloaded_file
            original_video_path = os.path.join(dir_path, original_video_filename)

            if rename_name == video_title:
                caption_name = original_video_title  # Original title for caption
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(downloaded_file)
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
                    send_to_all(message, "❌ FFmpeg not found. Please install FFmpeg.")
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
                    subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    os.remove(user_vid_path)
                    user_vid_path = mp4_file
                    final_name = mp4_basename
                except Exception as e:
                    send_to_all(message, f"❌ Conversion to MP4 failed: {e}")
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
            
            # Use ffmpeg thumbnail only as fallback (when YouTube thumbnail failed)
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
                    #found_type = None
                    try:
                        forwarded_msgs = safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
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
                                # Проверяем, нужны ли субтитры для этого видео
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), rounded_quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
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
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
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
                            need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
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
                        threading.Event().wait(2)
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
                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    if not need_subs:
                        save_to_video_cache(url, quality_key, split_msg_ids, original_text=message.text or message.caption or "")
                    else:
                        logger.info(f"Split video with subtitles is not cached (found_type={found_type}, auto_mode={auto_mode})")
                if os.path.exists(thumb_dir):
                    os.remove(thumb_dir)
                if os.path.exists(user_vid_path):
                    os.remove(user_vid_path)
                success_msg = f"<b>✅ Upload complete</b> - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
                safe_edit_message_text(user_id, proc_msg_id, success_msg)
                send_to_logger(message, "Video upload completed with file splitting.")
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
                                if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                                    
                                    # First, download the subtitles separately
                                    video_dir = os.path.dirname(after_rename_abs_path)
                                    subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                    
                                    if not subs_path:
                                        app.send_message(user_id, "⚠️ Failed to download subtitles", reply_to_message_id=message.id)
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
                                        status_msg = app.send_message(user_id, "⚠️ Embedding subtitles may take a long time (up to 1 min per 1 min of video)!\n🔥 Starting to burn subtitles...")
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
                                        app.send_message(user_id, "ℹ️ Subtitles cannot be embedded due to limits (quality/duration/size)", reply_to_message_id=message.id)
                                else:
                                    app.send_message(user_id, "ℹ️ Subtitles are not available for the selected language", reply_to_message_id=message.id)
                            
                            # Clean up subtitle files after embedding attempt
                            try:
                                cleanup_subtitle_files(user_id)
                            except Exception as e:
                                logger.error(f"Error cleaning up subtitle files: {e}")
                            
                            # Clear
                            clear_subs_check_cache()
                        video_msg = send_videos(message, after_rename_abs_path, '' if force_no_title else original_video_title, duration, thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                        
                        #found_type = None
                        try:
                            forwarded_msgs = safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                            logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                            if forwarded_msgs:
                                logger.info(f"down_and_up: saving to cache with forwarded message IDs: {[m.id for m in forwarded_msgs]}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
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
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        save_to_video_cache(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                            else:
                                logger.info(f"down_and_up: saving to cache with video_msg.id: {video_msg.id}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.append(video_msg.id)
                                else:
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        # For single videos, save to regular cache
                                        save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                        except Exception as e:
                            logger.error(f"Error forwarding video to logger: {e}")
                            logger.info(f"down_and_up: saving to cache with video_msg.id after error: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # For single videos, save to regular cache
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{info_text}\n{full_bar}   100.0%\n<b>🎞 Video duration:</b> <i>{TimeFormatter(duration * 1000)}</i>\n1 file uploaded.")
                        send_mediainfo_if_enabled(user_id, after_rename_abs_path, message)
                        
                        # Clean up video file and thumbnail
                        if os.path.exists(after_rename_abs_path):
                            os.remove(after_rename_abs_path)
                        if thumb_dir and os.path.exists(thumb_dir):
                            os.remove(thumb_dir)
                        threading.Event().wait(2)
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        logger.error(traceback.format_exc())
                        send_to_all(message, f"❌ Error sending video: {str(e)}")
                        continue
        if successful_uploads == len(indices_to_download):
            success_msg = f"<b>✅ Upload complete</b> - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
            send_to_logger(message, success_msg)

        if is_playlist and quality_key:
            total_sent = len(cached_videos) + successful_uploads
            app.send_message(user_id, f"✅ Playlist videos sent: {total_sent}/{len(requested_indices)} files.", reply_to_message_id=message.id)
            send_to_logger(message, f"Playlist videos sent: {total_sent}/{len(requested_indices)} files (quality={quality_key}) to user {user_id}")

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, "⏰ Download cancelled due to timeout (2 hours)")
            send_to_logger(message, "Download cancelled due to timeout")
        else:
            logger.error(f"Error in video download: {e}")
            send_to_user(message, f"❌ Failed to download video: {e}")
        
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

        # --- ADDED: summary of cache after cycle ---
        if is_playlist and playlist_indices and playlist_msg_ids:
            #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
            subs_enabled = is_subs_enabled(user_id)
            auto_mode = get_user_subs_auto_mode(user_id)
            need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
            if not need_subs:
                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, playlist_indices, playlist_msg_ids, original_text=message.text or message.caption or "")
            else:
                logger.info("Video with subtitles (subs.txt found) is not cached!")
            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, playlist_indices)
            summary = "\n".join([f"Index {idx}: msg_id={cached_check.get(idx, '-')}" for idx in playlist_indices])
            logger.info(f"[SUMMARY] Playlist cache (quality {quality_key}):\n{summary}")

#########################################
