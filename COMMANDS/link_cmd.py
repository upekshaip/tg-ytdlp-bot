# ########################################
# Link command - get direct video links
# ########################################

import os
import re
import yt_dlp
from pyrogram.types import ReplyParameters
from pyrogram import enums
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_logger, send_to_user, send_to_all
from HELPERS.limitter import check_user, is_user_in_channel
from HELPERS.filesystem_hlp import create_directory
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
from HELPERS.pot_helper import add_pot_to_ytdl_opts
from COMMANDS.cookies_cmd import ensure_working_youtube_cookies

# Get app instance for decorators
app = get_app()

def parse_quality_argument(quality_arg):
    """
    Parses quality argument and returns format for yt-dlp
    
    Args:
        quality_arg (str): Quality argument (e.g., "720", "720p", "4k", "8K")
        
    Returns:
        str: Format for yt-dlp
    """
    if not quality_arg:
        return "best"
    
    quality_arg = quality_arg.lower().strip()
    
    # Remove 'p' or 'P' if present
    if quality_arg.endswith('p'):
        quality_arg = quality_arg[:-1]
    
    # Special cases for 4K and 8K
    if quality_arg in ['4k', '4']:
        return "bv*[height<=2160]+ba/bv*[height<=2160]/bv+ba/best"
    elif quality_arg in ['8k', '8']:
        return "bv*[height<=4320]+ba/bv*[height<=4320]/bv+ba/best"
    
    # Check if this is a number from 1 to 10000
    try:
        quality_num = int(quality_arg)
        if 1 <= quality_num <= 10000:
            return f"bv*[height<={quality_num}]+ba/bv*[height<={quality_num}]/bv+ba/best"
        else:
            return "best"
    except ValueError:
        return "best"

def get_direct_link(url, user_id, quality_arg=None, cookies_already_checked=False, use_proxy=False):
    # Сбрасываем кеш проверенных источников куки для новой задачи получения ссылки
    from COMMANDS.cookies_cmd import reset_checked_cookie_sources
    reset_checked_cookie_sources(user_id)
    logger.info(f"🔄 [DEBUG] Reset checked cookie sources for new link task for user {user_id}")
    
    messages = safe_get_messages(user_id)
    """
    Gets direct link to video using yt-dlp
    
            Args:
            url (str): Video URL
            user_id (int): User ID
            quality_arg (str): Quality argument
            cookies_already_checked (bool): Whether cookies are already checked
        
            Returns:
            dict: Result with links or error
    """
    try:
        # Parse quality
        format_spec = parse_quality_argument(quality_arg)
        
        # Basic yt-dlp options - use same parameters as down_and_up.py
        ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'format': format_spec,
            'extract_flat': False,
            'simulate': True,
            'extractor_args': {
                'generic': {
                    'impersonate': ['chrome']
                },
                'youtubetab': {
                    'skip': ['authcheck']
                }
            },
            'referer': url,
            'geo_bypass': True,
            'check_certificate': False,
            'live_from_start': True,
            # Add additional stability options
            'socket_timeout': 60,
            'retries': 15,
            'fragment_retries': 15,
            'http_chunk_size': 5242880,  # 5MB chunks
            'buffersize': 2048,
            'sleep_interval': 2,
            'max_sleep_interval': 10,
            'read_timeout': 60,
            'connect_timeout': 30
        }
        
        # Add user's custom yt-dlp arguments
        from COMMANDS.args_cmd import get_user_ytdlp_args, log_ytdlp_options
        user_args = get_user_ytdlp_args(user_id, url)
        if user_args:
            ytdl_opts.update(user_args)
        
        # Log final yt-dlp options for debugging
        log_ytdlp_options(user_id, ytdl_opts, "get_direct_link")
        
        # Cookie setup
        user_dir = os.path.join("users", str(user_id))
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        
        # For YouTube URL check cookies
        if is_youtube_url(url) and not cookies_already_checked:
            has_working_cookies = ensure_working_youtube_cookies(user_id)
            if has_working_cookies and os.path.exists(user_cookie_path):
                ytdl_opts['cookiefile'] = user_cookie_path
                logger.info(safe_get_messages(user_id).LINK_USING_WORKING_YOUTUBE_COOKIES_MSG.format(user_id=user_id))
            else:
                ytdl_opts['cookiefile'] = None
                logger.info(safe_get_messages(user_id).LINK_NO_WORKING_YOUTUBE_COOKIES_MSG.format(user_id=user_id))
        elif is_youtube_url(url) and cookies_already_checked:
            if os.path.exists(user_cookie_path):
                ytdl_opts['cookiefile'] = user_cookie_path
                logger.info(safe_get_messages(user_id).LINK_USING_EXISTING_YOUTUBE_COOKIES_MSG.format(user_id=user_id))
            else:
                ytdl_opts['cookiefile'] = None
                logger.info(safe_get_messages(user_id).LINK_NO_YOUTUBE_COOKIES_FOUND_MSG.format(user_id=user_id))
        else:
            # For non-YouTube URL use existing logic
            if os.path.exists(user_cookie_path):
                ytdl_opts['cookiefile'] = user_cookie_path
            else:
                global_cookie_path = Config.COOKIE_FILE_PATH
                if os.path.exists(global_cookie_path):
                    try:
                        create_directory(user_dir)
                        import shutil
                        shutil.copy2(global_cookie_path, user_cookie_path)
                        ytdl_opts['cookiefile'] = user_cookie_path
                        logger.info(safe_get_messages(user_id).LINK_COPIED_GLOBAL_COOKIE_FILE_MSG.format(user_id=user_id))
                    except Exception as e:
                        logger.error(f"{LoggerMsg.LINK_FAILED_COPY_GLOBAL_COOKIE_LOG_MSG}")
                        ytdl_opts['cookiefile'] = None
                else:
                    ytdl_opts['cookiefile'] = None
        
        # Check if we need to use --no-cookies for this domain
        if is_no_cookie_domain(url):
            ytdl_opts['cookiefile'] = None
            logger.info(f"Using --no-cookies for domain in link extraction: {url}")
        
        # Add proxy if needed
        if use_proxy:
            # Check if user has global proxy enabled first
            from COMMANDS.proxy_cmd import is_proxy_enabled, select_proxy_for_user, build_proxy_url
            proxy_enabled = is_proxy_enabled(user_id)
            
            if proxy_enabled:
                # User has global proxy enabled - use round-robin/random selection
                proxy_config = select_proxy_for_user()
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        ytdl_opts['proxy'] = proxy_url
                        logger.info(f"Using global proxy for link extraction: {proxy_url}")
                    else:
                        logger.warning("Failed to build proxy URL from global config")
                else:
                    logger.warning("Global proxy enabled but no proxy configuration available")
            else:
                # User doesn't have global proxy enabled - check domain-specific proxy
                from COMMANDS.proxy_cmd import select_proxy_for_domain
                proxy_config = select_proxy_for_domain(url)
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        ytdl_opts['proxy'] = proxy_url
                        logger.info(f"{LoggerMsg.LINK_USING_DOMAIN_SPECIFIC_PROXY_LOG_MSG}")
                    else:
                        logger.warning("Failed to build proxy URL from domain config")
                else:
                    logger.info(f"No domain-specific proxy required for {url}")
        else:
            # use_proxy=False: Check if user has global proxy enabled OR domain requires proxy
            from COMMANDS.proxy_cmd import is_proxy_enabled, select_proxy_for_user, select_proxy_for_domain, build_proxy_url
            
            # Check if user has global proxy enabled
            proxy_enabled = is_proxy_enabled(user_id)
            
            if proxy_enabled:
                # User has global proxy enabled - use proxy for ALL requests
                proxy_config = select_proxy_for_user()
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        ytdl_opts['proxy'] = proxy_url
                        logger.info(f"Using global proxy for link extraction (user enabled): {proxy_url}")
                    else:
                        logger.warning("Failed to build proxy URL from global config")
                else:
                    logger.warning("Global proxy enabled but no proxy configuration available")
            else:
                # User proxy disabled - check if domain requires specific proxy
                proxy_config = select_proxy_for_domain(url)
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        ytdl_opts['proxy'] = proxy_url
                        logger.info(f"{LoggerMsg.LINK_USING_DOMAIN_SPECIFIC_PROXY_LOG_MSG}")
                    else:
                        logger.warning(LoggerMsg.LINK_FAILED_BUILD_PROXY_URL_LOG_MSG)
                else:
                    logger.info(f"{LoggerMsg.LINK_USER_PROXY_DISABLED_LOG_MSG}")
        
        # Add proxy configuration if needed (same as down_and_up.py)
        from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
        ytdl_opts = add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)
        
        # Add PO token provider for YouTube domains
        ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
        
        # Get video information
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        # Normalize info to a dict
        if isinstance(info, list):
            info = (info[0] if len(info) > 0 else {})
        elif isinstance(info, dict) and 'entries' in info:
            entries = info.get('entries')
            if isinstance(entries, list) and len(entries) > 0:
                info = entries[0]
        
        if not info:
            return {'error': 'Failed to extract video information'}
        
        # Get the best direct URL for VLC players
        direct_url = None
        video_url = None
        audio_url = None
        
        # Get requested formats
        requested_formats = info.get('requested_formats', [])
        
        if requested_formats:
            # There are separate video and audio streams
            for fmt in requested_formats:
                if fmt.get('vcodec') != 'none':
                    video_url = fmt.get('url')
                    if not direct_url:  # Use first video URL as direct URL
                        direct_url = video_url
                elif fmt.get('acodec') != 'none':
                    audio_url = fmt.get('url')
            
            # Create player URLs for separate video/audio streams
            if video_url and audio_url:
                # Both video and audio available - use video as direct URL
                if not direct_url:
                    direct_url = video_url
            elif video_url:
                # Only video available
                if not direct_url:
                    direct_url = video_url
            elif audio_url:
                # Only audio available
                if not direct_url:
                    direct_url = audio_url
        else:
            # Fallback: look for best format with video and audio
            formats = info.get('formats', [])
            best_format = None
            
            for fmt in formats:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    if not best_format or fmt.get('height', 0) > best_format.get('height', 0):
                        best_format = fmt
            
            if best_format:
                direct_url = best_format.get('url')
                video_url = direct_url
        
        # If we have a direct URL, create VLC player URLs
        player_urls = {}
        if direct_url:
            from urllib.parse import quote, urlparse
            
            # Кодируем URL для iOS VLC (однократное кодирование)
            encoded_url = quote(direct_url, safe='')
            
            # Parse URL to get host and path for Android intent
            parsed_url = urlparse(direct_url)
            scheme = parsed_url.scheme
            
            # For Android VLC: remove scheme and encode URL properly
            android_url_clean = direct_url.replace('https://', '').replace('http://', '')
            
            # Create player URLs
            player_urls = {
                'direct': direct_url,
                'vlc_ios': f"https://vlc.ratu.sh/?url=vlc-x-callback://x-callback-url/stream?url={encoded_url}",
                'vlc_android': f"https://vlc.ratu.sh/?url=intent://{android_url_clean}#Intent;scheme={scheme};package=org.videolan.vlc;type=video/*;end"
            }
        
        if direct_url:
            return {
                'success': True,
                'video_url': video_url,
                'audio_url': audio_url,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'format': format_spec,
                'player_urls': player_urls
            }
        elif video_url:
            return {
                'success': True,
                'video_url': video_url,
                'audio_url': None,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'format': format_spec,
                'player_urls': player_urls
            }
        elif audio_url:
            return {
                'success': True,
                'video_url': None,
                'audio_url': audio_url,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'format': format_spec,
                'player_urls': player_urls
            }
        
        # If nothing found, return error
        return {'error': 'No suitable format found'}
        
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e)
        logger.error(f"DownloadError in link extraction: {error_text}")
        return {'error': f'Download error: {error_text}'}
    except KeyError as e:
        error_text = str(e)
        logger.error(f"KeyError in link extraction: {error_text}")
        logger.error("This may be due to missing or incomplete video information")
        return {'error': f'Missing information: {error_text}. The video may be unavailable or region-restricted.'}
    except Exception as e:
        error_text = str(e)
        logger.error(f"Error in link extraction: {error_text}")
        return {'error': f'Error: {error_text}'}

def link_command(app, message):
    """
    Handler for /link command
    """
    try:
        user_id = message.chat.id
        messages = safe_get_messages(user_id)
        
        # Subscription check for non-admins
        if not is_user_in_channel(app, message):
            return  # is_user_in_channel already sends subscription message
        
        # Create user directory after subscription check
        user_dir = os.path.join("users", str(user_id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir, exist_ok=True)
        
        # Get message text
        text = message.text or message.caption or ""
        
        # Parse command and arguments
        parts = text.strip().split()
        
        if len(parts) < 2:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from HELPERS.safe_messeger import safe_send_message
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="link_hint|close")]
            ])
            safe_send_message(message.chat.id, safe_get_messages(user_id).LINK_USAGE_MSG, reply_markup=keyboard, message=message)
            return
        
        # Determine URL and quality
        if len(parts) == 2:
            # Only URL, use best quality
            url = parts[1]
            quality_arg = None
        else:
            # Quality argument exists
            quality_arg = parts[1]
            url = ' '.join(parts[2:])
        
        # Check if this is a URL
        if not url.startswith(('http://', 'https://')):
            send_to_user(message, safe_get_messages(user_id).LINK_INVALID_URL_MSG)
            return
        
        # Send processing start message
        from HELPERS.safe_messeger import safe_send_message
        status_msg = safe_send_message(user_id, safe_get_messages(user_id).LINK_PROCESSING_MSG, reply_to_message_id=message.id, message=message)
        
        # Get direct link - use the same mechanisms as Always Ask Menu
        result = get_direct_link(url, user_id, quality_arg, cookies_already_checked=True, use_proxy=True)
        
        if result.get('success'):
            title = result.get('title', 'Unknown')
            duration = result.get('duration', 0)
            video_url = result.get('video_url')
            audio_url = result.get('audio_url')
            format_spec = result.get('format', 'best')
            player_urls = result.get('player_urls', {})
            
            # Form response using same format as Always Ask Menu
            response = safe_get_messages(user_id).LINK_DIRECT_LINK_OBTAINED_MSG
            response += safe_get_messages(user_id).LINK_TITLE_MSG.format(title=title)
            if duration and duration > 0:
                response += safe_get_messages(user_id).LINK_DURATION_MSG.format(duration=duration)
            response += safe_get_messages(user_id).LINK_FORMAT_INFO_MSG.format(format_spec=format_spec)
            
            if video_url:
                response += safe_get_messages(user_id).LINK_VIDEO_STREAM_MSG.format(video_url=video_url)
            
            if audio_url:
                response += safe_get_messages(user_id).LINK_AUDIO_STREAM_MSG.format(audio_url=audio_url)
            
            if not video_url and not audio_url:
                response += safe_get_messages(user_id).LINK_FAILED_GET_STREAMS_MSG
            
            # Create browser keyboard with direct URL
            direct_url = player_urls.get('direct', video_url or audio_url)
            if direct_url:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                browser_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_BROWSER_BUTTON_MSG, url=direct_url)],
                    [InlineKeyboardButton("🔚 Close", callback_data="askq|close")]
                ])
                
                # Update message with keyboard
                app.edit_message_text(
                    chat_id=user_id,
                    message_id=status_msg.id,
                    text=response,
                    reply_markup=browser_keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                # Fallback if no direct URL
                app.edit_message_text(
                    chat_id=user_id,
                    message_id=status_msg.id,
                    text=response,
                    parse_mode=enums.ParseMode.HTML
                )
            
            # Send VLC iOS message if available
            if 'vlc_ios' in player_urls:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                vlc_ios_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_VLC_IOS_BUTTON_MSG, url=player_urls['vlc_ios'])],
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_CLOSE_BUTTON_MSG, callback_data="askq|close")]
                ])
                app.send_message(
                    user_id,
                    safe_get_messages(user_id).AA_VLC_IOS_MSG,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    reply_markup=vlc_ios_keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            
            # Send VLC Android message if available
            if 'vlc_android' in player_urls:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                vlc_android_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_VLC_ANDROID_BUTTON_MSG, url=player_urls['vlc_android'])],
                    [InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_CLOSE_BUTTON_MSG, callback_data="askq|close")]
                ])
                app.send_message(
                    user_id,
                    safe_get_messages(user_id).AA_VLC_ANDROID_MSG,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    reply_markup=vlc_android_keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            
            send_to_logger(message, safe_get_messages(user_id).LINK_EXTRACTED_LOG_MSG.format(user_id=user_id, url=url))
            
        else:
            error_msg = result.get('error', 'Unknown error')
            app.edit_message_text(
                chat_id=user_id,
                message_id=status_msg.id,
                text=safe_get_messages(user_id).LINK_ERROR_GETTING_MSG.format(error_msg=error_msg),
                parse_mode=enums.ParseMode.HTML
            )
            
            send_to_logger(message, safe_get_messages(user_id).LINK_EXTRACTION_FAILED_LOG_MSG.format(user_id=user_id, url=url, error=error_msg))
            
    except Exception as e:
        logger.error(f"Error in link command: {e}")
        from HELPERS.logger import send_error_to_user
        send_error_to_user(message, safe_get_messages(user_id).LINK_ERROR_OCCURRED_MSG.format(error=str(e)))
        send_to_logger(message, safe_get_messages(user_id).LINK_COMMAND_ERROR_LOG_MSG.format(user_id=message.chat.id, error=str(e)))
