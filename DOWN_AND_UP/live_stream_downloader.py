# Live Stream Downloader
# Downloads live streams in chunks and sends them immediately

import os
import yt_dlp
import time
from datetime import datetime
from CONFIG.limits import LimitsConfig
from CONFIG.messages import safe_get_messages
from HELPERS.logger import logger
from DOWN_AND_UP.sender import send_videos
from DOWN_AND_UP.ffmpeg import get_duration_thumb, get_video_info_ffprobe


def download_live_stream_chunked(
    app, message, url, user_id, user_dir_name, info_dict, 
    proc_msg_id, current_total_process, tags_text="", 
    cookies_already_checked=False, use_proxy=False,
    format_override=None, quality_key=None
):
    """
    Download live stream in chunks and send each chunk immediately.
    
    Args:
        app: Pyrogram app instance
        message: Telegram message object
        url: Live stream URL
        user_id: User ID
        user_dir_name: Directory for downloads
        info_dict: Video info dict from yt-dlp
        proc_msg_id: Progress message ID
        current_total_process: Progress text
        tags_text: Tags text
        cookies_already_checked: Whether cookies were already checked
        use_proxy: Whether to use proxy
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get configuration
        split_hours = LimitsConfig.SPLIT_LIVE_STREAM_BY_HOURS
        max_duration = LimitsConfig.MAX_LIVE_STREAM_DURATION
        max_chunks = int(max_duration / (split_hours * 3600))
        
        logger.info(f"Starting live stream download: url={url}, split_hours={split_hours}, max_duration={max_duration}s, max_chunks={max_chunks}")
        
        # Get video title for filename
        video_title = info_dict.get('title', 'live_stream')
        if not video_title or video_title == 'live_stream':
            # Try to get channel name
            channel = info_dict.get('channel', 'live')
            video_title = f"{channel}_live_stream"
        
        # Sanitize title
        from HELPERS.filesystem_hlp import sanitize_filename_strict
        safe_title = sanitize_filename_strict(video_title)
        
        # Get upload date for filename
        upload_date = info_dict.get('upload_date')
        if upload_date:
            try:
                # Parse YYYYMMDD format
                date_obj = datetime.strptime(upload_date, '%Y%m%d')
                date_str = date_obj.strftime('%Y-%m-%d')
            except:
                date_str = datetime.now().strftime('%Y-%m-%d')
        else:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Get channel name
        channel = info_dict.get('channel', 'live')
        safe_channel = sanitize_filename_strict(channel)
        
        # Prepare base yt-dlp options
        base_opts = {
            'live_from_start': True,  # Start from beginning when DVR is available
            'concurrent_fragment_downloads': 4,  # -N 4
            'retries': float('inf'),  # -R infinite
            'fragment_retries': float('inf'),  # --fragment-retries infinite
            'retry_sleep': 'fragment:exp=1:30',  # --retry-sleep fragment:exp=1:30
            'continue_dl': True,  # --continue
            'noverwrites': True,  # --no-overwrites
            'hls_prefer_ffmpeg': True,  # --hls-prefer-ffmpeg
            'hls_use_mpegts': True,  # --hls-use-mpegts
            'downloader': 'ffmpeg',  # --downloader ffmpeg
            'quiet': False,
            'no_warnings': False,
        }
        
        # Add user's custom yt-dlp arguments from /args command
        from COMMANDS.args_cmd import get_user_ytdlp_args, log_ytdlp_options
        user_args = get_user_ytdlp_args(user_id, url)
        if user_args:
            # Update base_opts with user args, but preserve live stream specific settings
            # Don't override critical live stream options
            preserved_keys = {
                'live_from_start', 'concurrent_fragment_downloads', 'retries', 
                'fragment_retries', 'retry_sleep', 'continue_dl', 'noverwrites',
                'hls_prefer_ffmpeg', 'hls_use_mpegts', 'downloader', 'downloader_args'
            }
            for key, value in user_args.items():
                if key not in preserved_keys:
                    base_opts[key] = value
                    logger.info(f"Applied user arg for live stream: {key} = {value}")
        
        # Apply format_override if provided (from always_ask_menu or /format)
        if format_override:
            base_opts['format'] = format_override
            logger.info(f"Applied format_override for live stream: {format_override}")
        elif quality_key and quality_key != "best":
            # Convert quality_key to format if no format_override
            try:
                from DOWN_AND_UP.always_ask_menu import get_user_args
                user_args_local = get_user_args(user_id)
                user_codec = user_args_local.get('codec', 'avc1')
                
                # Build format based on quality_key and codec preference
                if quality_key.endswith('p'):
                    quality_val = int(quality_key[:-1])
                    # Determine previous quality
                    if quality_val >= 4320:
                        prev = 2160
                    elif quality_val >= 2160:
                        prev = 1440
                    elif quality_val >= 1440:
                        prev = 1080
                    elif quality_val >= 1080:
                        prev = 720
                    elif quality_val >= 720:
                        prev = 480
                    elif quality_val >= 480:
                        prev = 360
                    elif quality_val >= 360:
                        prev = 240
                    elif quality_val >= 240:
                        prev = 144
                    else:
                        prev = 0
                    
                    if user_codec == "av01":
                        format_str = f"bv*[vcodec*=av01][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<={quality_val}]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
                    elif user_codec == "vp9":
                        format_str = f"bv*[vcodec*=vp9][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<={quality_val}]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
                    else:  # avc1
                        format_str = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
                    base_opts['format'] = format_str
                    logger.info(f"Applied quality_key format for live stream: {format_str}")
            except Exception as e:
                logger.warning(f"Error converting quality_key to format: {e}")
        
        # Apply MKV preference from /format command
        try:
            from COMMANDS.format_cmd import get_user_mkv_preference
            mkv_on = get_user_mkv_preference(user_id)
            if mkv_on:
                base_opts['remux_video'] = 'mkv'
                logger.info(f"Applied MKV preference for live stream")
        except Exception as e:
            logger.debug(f"Could not get MKV preference: {e}")
        
        # Log final yt-dlp options for debugging
        log_ytdlp_options(user_id, base_opts, "live_stream_download")
        
        # Add cookies if available
        user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
        if os.path.exists(user_cookie_path):
            base_opts['cookiefile'] = user_cookie_path
        
        # Add proxy if needed
        if use_proxy:
            from COMMANDS.proxy_cmd import get_proxy_config
            proxy_config = get_proxy_config()
            if proxy_config and 'type' in proxy_config and 'ip' in proxy_config and 'port' in proxy_config:
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
                    proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
                base_opts['proxy'] = proxy_url
        else:
            from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
            base_opts = add_proxy_to_ytdl_opts(base_opts, url, user_id)
        
        # Add PO token provider for YouTube
        from HELPERS.pot_helper import add_pot_to_ytdl_opts
        base_opts = add_pot_to_ytdl_opts(base_opts, url)
        
        # Calculate segment time in seconds
        segment_time = split_hours * 3600  # Convert hours to seconds
        
        # Download chunks sequentially
        successful_chunks = 0
        start_time = time.time()
        
        for chunk_idx in range(max_chunks):
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_duration:
                logger.info(f"Reached max duration limit ({max_duration}s), stopping live stream download")
                break
            
            logger.info(f"Downloading live stream chunk {chunk_idx + 1}/{max_chunks}")
            
            # Update progress
            try:
                from HELPERS.safe_messeger import safe_edit_message_text
                progress_text = (
                    f"{current_total_process}\n"
                    f"📡 <b>Live Stream Download</b>\n"
                    f"Chunk {chunk_idx + 1}/{max_chunks}\n"
                    f"Duration: {split_hours} hour(s) per chunk"
                )
                safe_edit_message_text(user_id, proc_msg_id, progress_text)
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
            
            # Create yt-dlp options for this chunk
            chunk_opts = base_opts.copy()
            
            # Prepare output filename for this chunk
            chunk_filename = f"{date_str}_{safe_channel}_{safe_title}_{chunk_idx:03d}.ts"
            chunk_file = os.path.join(user_dir_name, chunk_filename)
            chunk_opts['outtmpl'] = chunk_file.replace('.ts', '.%(ext)s')
            
            # Prepare downloader args for ffmpeg to limit duration per chunk
            # Input: limit to segment_time for this chunk
            segment_hours = int(segment_time / 3600)
            segment_minutes = int((segment_time % 3600) / 60)
            segment_seconds = int(segment_time % 60)
            ffmpeg_input_args = f"-t {segment_hours:02d}:{segment_minutes:02d}:{segment_seconds:02d}"
            
            # Output: use mpegts format for live streams
            ffmpeg_output_args = "-f mpegts"
            
            chunk_opts['downloader_args'] = {
                'ffmpeg_i': ffmpeg_input_args,
                'ffmpeg_o': ffmpeg_output_args
            }
            
            try:
                with yt_dlp.YoutubeDL(chunk_opts) as ydl:
                    ydl.download([url])
                
                # Check if file was created (might have different extension)
                if not os.path.exists(chunk_file):
                    # Try to find file with any extension
                    import glob
                    chunk_pattern = os.path.join(
                        user_dir_name,
                        f"{date_str}_{safe_channel}_{safe_title}_{chunk_idx:03d}.*"
                    )
                    chunk_files = glob.glob(chunk_pattern)
                    if chunk_files:
                        chunk_file = chunk_files[0]
                    else:
                        logger.warning(f"Could not find chunk file for index {chunk_idx}")
                        continue
                
                if not os.path.exists(chunk_file):
                    logger.warning(f"Chunk file not found: {chunk_file}")
                    continue
                
                # Get video info for the chunk
                try:
                    _, _, duration = get_video_info_ffprobe(chunk_file)
                except Exception as e:
                    logger.error(f"Error getting video info: {e}")
                    duration = segment_time
                
                # Get or create thumbnail
                thumb_file = None
                try:
                    thumb_name = f"{safe_title}_chunk_{chunk_idx:03d}"
                    result = get_duration_thumb(message, user_dir_name, chunk_file, thumb_name)
                    if result:
                        duration_from_thumb, thumb_file = result
                        # Update duration if we got it from thumbnail extraction
                        if duration_from_thumb:
                            duration = duration_from_thumb
                except Exception as e:
                    logger.error(f"Error creating thumbnail: {e}")
                    # Try to use video thumbnail if available
                    thumb_path = os.path.join(user_dir_name, f"{safe_title}.jpg")
                    if os.path.exists(thumb_path):
                        thumb_file = thumb_path
                
                # Prepare caption
                chunk_caption = f"📡 <b>Live Stream - Chunk {chunk_idx + 1}/{max_chunks}</b>\n"
                chunk_caption += f"⏱ Duration: {split_hours} hour(s)\n"
                if tags_text:
                    chunk_caption += f"\n{tags_text}"
                
                # Send chunk immediately
                logger.info(f"Sending chunk {chunk_idx + 1} to user: {chunk_file}")
                
                chunk_msg = send_videos(
                    message,
                    chunk_file,
                    chunk_caption,
                    int(duration) if duration else segment_time,
                    thumb_file or "",
                    f"Chunk {chunk_idx + 1}/{max_chunks}",
                    proc_msg_id,
                    f"{video_title} - Chunk {chunk_idx + 1}",
                    tags_text
                )
                
                if chunk_msg:
                    successful_chunks += 1
                    logger.info(f"Successfully sent chunk {chunk_idx + 1}")
                else:
                    logger.warning(f"Failed to send chunk {chunk_idx + 1}")
                
                # Clean up chunk file after sending (optional, to save space)
                # Uncomment if you want to delete chunks after sending
                # try:
                #     os.remove(chunk_file)
                #     logger.info(f"Cleaned up chunk file: {chunk_file}")
                # except Exception as e:
                #     logger.error(f"Error cleaning up chunk file: {e}")
                
            except Exception as e:
                logger.error(f"Error downloading chunk {chunk_idx + 1}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with next chunk
                continue
            
            # Check if we've reached max duration
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_duration:
                logger.info(f"Reached max duration limit, stopping")
                break
        
        # Final progress update
        try:
            from HELPERS.safe_messeger import safe_edit_message_text
            final_text = (
                f"{current_total_process}\n"
                f"✅ <b>Live Stream Download Complete</b>\n"
                f"Downloaded {successful_chunks} chunk(s)"
            )
            safe_edit_message_text(user_id, proc_msg_id, final_text)
        except Exception as e:
            logger.error(f"Error updating final progress: {e}")
        
        logger.info(f"Live stream download completed: {successful_chunks} chunks downloaded")
        return successful_chunks > 0
        
    except Exception as e:
        logger.error(f"Error in download_live_stream_chunked: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

