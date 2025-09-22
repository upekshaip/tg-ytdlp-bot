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
from CONFIG.messages import Messages as Messages
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
        
        # Basic yt-dlp options
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
            'live_from_start': True
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
                logger.info(f"Using working YouTube cookies for link extraction for user {user_id}")
            else:
                ytdl_opts['cookiefile'] = None
                logger.info(f"No working YouTube cookies available for link extraction for user {user_id}")
        elif is_youtube_url(url) and cookies_already_checked:
            if os.path.exists(user_cookie_path):
                ytdl_opts['cookiefile'] = user_cookie_path
                logger.info(f"Using existing YouTube cookies for link extraction for user {user_id}")
            else:
                ytdl_opts['cookiefile'] = None
                logger.info(f"No YouTube cookies found for link extraction for user {user_id}")
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
                        logger.info(f"Copied global cookie file to user {user_id} folder for link extraction")
                    except Exception as e:
                        logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
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
                        logger.info(f"Using domain-specific proxy for link extraction: {proxy_url}")
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
                        logger.info(f"Using domain-specific proxy for link extraction: {proxy_url}")
                    else:
                        logger.warning("Failed to build proxy URL for domain-specific proxy")
                else:
                    logger.info(f"User proxy disabled and domain doesn't require proxy - using direct connection for {url}")
        
        # Add PO token provider for YouTube domains
        ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
        
        # Get video information
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            return {'error': 'Failed to extract video information'}
        
        # Get requested formats
        requested_formats = info.get('requested_formats', [])
        
        if requested_formats:
            # There are separate video and audio streams
            video_url = None
            audio_url = None
            
            for fmt in requested_formats:
                if fmt.get('vcodec') != 'none':
                    video_url = fmt.get('url')
                elif fmt.get('acodec') != 'none':
                    audio_url = fmt.get('url')
            
            if video_url and audio_url:
                return {
                    'success': True,
                    'video_url': video_url,
                    'audio_url': audio_url,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'format': format_spec
                }
            elif video_url:
                return {
                    'success': True,
                    'video_url': video_url,
                    'audio_url': None,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'format': format_spec
                }
            elif audio_url:
                return {
                    'success': True,
                    'video_url': None,
                    'audio_url': audio_url,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'format': format_spec
                }
        
        # Fallback: look for best format with video and audio
        formats = info.get('formats', [])
        best_format = None
        
        for fmt in formats:
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                if not best_format or fmt.get('height', 0) > best_format.get('height', 0):
                    best_format = fmt
        
        if best_format:
            return {
                'success': True,
                'video_url': best_format.get('url'),
                'audio_url': None,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'format': format_spec
            }
        
        # If nothing found, return error
        return {'error': 'No suitable format found'}
        
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e)
        logger.error(f"DownloadError in link extraction: {error_text}")
        return {'error': f'Download error: {error_text}'}
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
        
        # Subscription check for non-admins
        if int(user_id) not in is_user_in_channel(app, message):
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
            send_to_user(message, Messages.LINK_USAGE_MSG)
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
            send_to_user(message, Messages.LINK_INVALID_URL_MSG)
            return
        
        # Send processing start message
        from HELPERS.safe_messeger import safe_send_message
        status_msg = safe_send_message(user_id, Messages.LINK_PROCESSING_MSG, reply_to_message_id=message.id, message=message)
        
        # Get direct link - use proxy only if user has proxy enabled and domain requires it
        result = get_direct_link(url, user_id, quality_arg, use_proxy=False)
        
        if result.get('success'):
            title = result.get('title', 'Unknown')
            duration = result.get('duration', 0)
            video_url = result.get('video_url')
            audio_url = result.get('audio_url')
            format_spec = result.get('format', 'best')
            
            # Form response
            response = Messages.LINK_DIRECT_LINK_OBTAINED_MSG
            response += Messages.LINK_TITLE_MSG.format(title=title)
            if duration > 0:
                response += Messages.LINK_DURATION_MSG.format(duration=duration)
            response += Messages.LINK_FORMAT_INFO_MSG.format(format_spec=format_spec)
            
            if video_url:
                response += Messages.LINK_VIDEO_STREAM_MSG.format(video_url=video_url)
            
            if audio_url:
                response += Messages.LINK_AUDIO_STREAM_MSG.format(audio_url=audio_url)
            
            if not video_url and not audio_url:
                response += Messages.LINK_FAILED_GET_STREAMS_MSG
            
            # Update message
            app.edit_message_text(
                chat_id=user_id,
                message_id=status_msg.id,
                text=response,
                parse_mode=enums.ParseMode.HTML
            )
            
            send_to_logger(message, Messages.LINK_EXTRACTED_LOG_MSG.format(user_id=user_id, url=url))
            
        else:
            error_msg = result.get('error', 'Unknown error')
            app.edit_message_text(
                chat_id=user_id,
                message_id=status_msg.id,
                text=Messages.LINK_ERROR_GETTING_MSG.format(error_msg=error_msg),
                parse_mode=enums.ParseMode.HTML
            )
            
            send_to_logger(message, Messages.LINK_EXTRACTION_FAILED_LOG_MSG.format(user_id=user_id, url=url, error=error_msg))
            
    except Exception as e:
        logger.error(f"Error in link command: {e}")
        from HELPERS.logger import send_error_to_user
        send_error_to_user(message, Messages.LINK_ERROR_OCCURRED_MSG.format(error=str(e)))
        send_to_logger(message, Messages.LINK_COMMAND_ERROR_LOG_MSG.format(user_id=message.chat.id, error=str(e)))
