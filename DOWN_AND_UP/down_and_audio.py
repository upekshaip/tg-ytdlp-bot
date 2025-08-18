
# ########################################
# Down_and_audio function
# ########################################

import os
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
from CONFIG.config import Config
from COMMANDS.subtitles_cmd import is_subs_enabled, check_subs_availability, get_user_subs_auto_mode, _subs_check_cache, download_subtitles_ytdlp
from COMMANDS.mediainfo_cmd import send_mediainfo_if_enabled
from URL_PARSERS.youtube import is_youtube_url
from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.normalizer import get_clean_playlist_url
from DATABASE.cache_db import get_cached_playlist_videos, get_cached_message_ids, save_to_video_cache, save_to_playlist_cache

# Get app instance for decorators
app = get_app()

# @reply_with_keyboard
def down_and_audio(app, message, url, tags, quality_key=None, playlist_name=None, video_count=1, video_start_with=1):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    playlist_indices = []
    playlist_msg_ids = []  
        
    user_id = message.chat.id
    logger.info(f"down_and_audio called: url={url}, quality_key={quality_key}, video_count={video_count}, video_start_with={video_start_with}")
    
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
                        logger.error(f"down_and_audio: error reposting cached audio index={index}: {e}")
            if len(uncached_indices) == 0:
                app.send_message(user_id, f"✅ Playlist audio sent from cache ({len(cached_videos)}/{len(requested_indices)} files).", reply_to_message_id=message.id)
                send_to_logger(message, f"Playlist audio sent from cache (quality={quality_key}) to user{user_id}")
                return
            else:
                app.send_message(user_id, f"📥 {len(cached_videos)}/{len(requested_indices)} audio sent from cache, downloading missing ones...", reply_to_message_id=message.id)
    elif quality_key and not is_playlist:
        cached_ids = get_cached_message_ids(url, quality_key)
        if cached_ids:
            try:
                app.forward_messages(
                    chat_id=user_id,
                    from_chat_id=Config.LOGS_ID,
                    message_ids=cached_ids
                )
                app.send_message(user_id, "✅ Audio sent from cache.", reply_to_message_id=message.id)
                send_to_logger(message, f"Audio sent from cache (quality={quality_key}) to user{user_id}")
                return
            except Exception as e:
                logger.error(f"Error reposting audio from cache: {e}")
                save_to_video_cache(url, quality_key, [], clear=True)
                app.send_message(user_id, "⚠️ Failed to get audio from cache, starting new download...", reply_to_message_id=message.id)
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
        proc_msg = app.send_message(user_id, "🔄 Processing...", reply_to_message_id=message.id)
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
        current_total_process = ""
        successful_uploads = 0

        def progress_hook(d):
            nonlocal last_update
            # Check the timeout
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            if current_time - last_update < 0.2:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
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

        def try_download_audio(url, current_index):
            nonlocal current_total_process
            ytdl_opts = {
               'format': 'ba',
               'postprocessors': [{
                  'key': 'FFmpegExtractAudio',
                  'preferredcodec': 'mp3',
                  'preferredquality': '192',
               },
               {
                  'key': 'EmbedThumbnail'   # equivalent to --embed-thumbnail
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
                  'generic': ['impersonate=chrome']
               },
               'referer': url,
               'geo_bypass': True,
               'check_certificate': False,
               'live_from_start': True,
            }
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                ytdl_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                ytdl_opts['cookiefile'] = cookie_file   
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
                        f"{current_total_process}\n> <i>📥 Downloading audio using format: ba...</i>")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    ydl.download([url])
                
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                error_text = str(e)
                logger.error(f"DownloadError: {error_text}")
                # Send full error message with instructions immediately
                send_to_all(
                    message,
                    "<blockquote>Check <a href='https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites'>here</a> if your site supported</blockquote>\n"
                    "<blockquote>You may need <code>cookie</code> for downloading this audio. First, clean your workspace via <b>/clean</b> command</blockquote>\n"
                    "<blockquote>For Youtube - get <code>cookie</code> via <b>/download_cookie</b> command. For any other supported site - send your own cookie (<a href='https://t.me/c/2303231066/18'>guide1</a>) (<a href='https://t.me/c/2303231066/22'>guide2</a>) and after that send your audio link again.</blockquote>\n"
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
                else:
                    send_to_user(message, f"❌ Unknown error: {e}")
                return None

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
                audio_msg = app.send_audio(chat_id=user_id, audio=audio_file, caption=caption_with_link, reply_to_message_id=message.id)
                forwarded_msg = safe_forward_messages(Config.LOGS_ID, user_id, [audio_msg.id])
                
                # Save to cache after sending audio
                if quality_key and forwarded_msg:
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
                threading.Event().wait(2)

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
            app.send_message(user_id, f"✅Playlist audio sent: {total_sent}/{len(requested_indices)} files.", reply_to_message_id=message.id)
            send_to_logger(message, f"Playlist audio sent: {total_sent}/{len(requested_indices)} files (quality={quality_key}) to user{user_id}")

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, "⏰ Download cancelled due to timeout (2 hours)")
            send_to_logger(message, "Download cancelled due to timeout")
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
