# --- receiving formats and metadata via yt-dlp ---
import os
import yt_dlp
from CONFIG.config import Config
from HELPERS.logger import logger
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
from URL_PARSERS.filter_check import is_no_filter_domain
from URL_PARSERS.filter_utils import create_smart_match_filter, create_legacy_match_filter
from HELPERS.pot_helper import add_pot_to_ytdl_opts
from CONFIG.limits import LimitsConfig

def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False):
    ytdl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'no_warnings': True,
        'extract_flat': False,
        'simulate': True,
        'playlist_items': str(playlist_start_index),    
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
    
    # Add match_filter only if domain is not in NO_FILTER_DOMAINS
    if not is_no_filter_domain(url):
        # Use smart filter that allows downloads when duration is unknown
        ytdl_opts['match_filter'] = create_smart_match_filter()
    else:
        logger.info(f"Skipping match_filter for domain in NO_FILTER_DOMAINS: {url}")
    
    # Add user's custom yt-dlp arguments (but exclude format to get all available formats)
    if user_id is not None:
        from COMMANDS.args_cmd import get_user_ytdlp_args, log_ytdlp_options
        user_args = get_user_ytdlp_args(user_id, url)
        if user_args:
            # Remove format parameter to get all available formats
            user_args_copy = user_args.copy()
            user_args_copy.pop('format', None)
            ytdl_opts.update(user_args_copy)
        
        # Log final yt-dlp options for debugging
        log_ytdlp_options(user_id, ytdl_opts, "get_video_formats")
    
    if user_id is not None:
        user_dir = os.path.join("users", str(user_id))
        # Check the availability of cookie.txt in the user folder
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        
        # For YouTube URLs, check cookies on user's URL first, then get new ones if needed
        if is_youtube_url(url) and not cookies_already_checked:
            from COMMANDS.cookies_cmd import get_youtube_cookie_urls, test_youtube_cookies_on_url, _download_content
            
            # Always check existing cookies first on user's URL for maximum speed
            if os.path.exists(user_cookie_path):
                logger.info(f"Checking existing YouTube cookies on user's URL for format detection for user {user_id}")
                if test_youtube_cookies_on_url(user_cookie_path, url):
                    cookie_file = user_cookie_path
                    logger.info(f"Existing YouTube cookies work on user's URL for format detection for user {user_id} - using them")
                else:
                    logger.info(f"Existing YouTube cookies failed on user's URL, trying to get new ones for format detection for user {user_id}")
                    cookie_urls = get_youtube_cookie_urls()
                    if cookie_urls:
                        success = False
                        for i, cookie_url in enumerate(cookie_urls, 1):
                            logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                            ok, status_code, content, error = _download_content(cookie_url)
                            if ok and content and len(content) <= 100 * 1024:
                                with open(user_cookie_path, "wb") as cf:
                                    cf.write(content)
                                if test_youtube_cookies_on_url(user_cookie_path, url):
                                    cookie_file = user_cookie_path
                                    logger.info(f"YouTube cookies from source {i} work on user's URL for format detection for user {user_id} - saved to user folder")
                                    success = True
                                    break
                                else:
                                    logger.warning(f"YouTube cookies from source {i} don't work on user's URL for format detection for user {user_id}")
                            else:
                                logger.warning(f"Failed to download YouTube cookies from source {i} for format detection for user {user_id}")
                        
                        if not success:
                            logger.warning(f"All YouTube cookie sources failed for format detection for user {user_id}, will try without cookies")
                            cookie_file = None
                    else:
                        logger.warning(f"No YouTube cookie sources configured for format detection for user {user_id}, will try without cookies")
                        cookie_file = None
            else:
                logger.info(f"No YouTube cookies found for format detection for user {user_id}, attempting to get new ones")
                cookie_urls = get_youtube_cookie_urls()
                if cookie_urls:
                    success = False
                    for i, cookie_url in enumerate(cookie_urls, 1):
                        logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                        ok, status_code, content, error = _download_content(cookie_url)
                        if ok and content and len(content) <= 100 * 1024:
                            with open(user_cookie_path, "wb") as cf:
                                cf.write(content)
                            if test_youtube_cookies_on_url(user_cookie_path, url):
                                cookie_file = user_cookie_path
                                logger.info(f"YouTube cookies from source {i} work on user's URL for format detection for user {user_id} - saved to user folder")
                                success = True
                                break
                            else:
                                logger.warning(f"YouTube cookies from source {i} don't work on user's URL for format detection for user {user_id}")
                        else:
                            logger.warning(f"Failed to download YouTube cookies from source {i} for format detection for user {user_id}")
                    
                    if not success:
                        logger.warning(f"All YouTube cookie sources failed for format detection for user {user_id}, will try without cookies")
                        cookie_file = None
                else:
                    logger.warning(f"No YouTube cookie sources configured for format detection for user {user_id}, will try without cookies")
                    cookie_file = None
        elif is_youtube_url(url) and cookies_already_checked:
            # Cookies already checked in Always Ask menu - use them directly without verification
            if os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
                logger.info(f"Using YouTube cookies for format detection for user {user_id} (already validated in Always Ask menu)")
            else:
                # Cookies were deleted - try to restore them on user's URL
                logger.info(f"No YouTube cookies found for format detection for user {user_id}, attempting to restore...")
                from COMMANDS.cookies_cmd import get_youtube_cookie_urls, test_youtube_cookies_on_url, _download_content
                cookie_urls = get_youtube_cookie_urls()
                if cookie_urls:
                    success = False
                    for i, cookie_url in enumerate(cookie_urls, 1):
                        logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                        ok, status_code, content, error = _download_content(cookie_url)
                        if ok and content and len(content) <= 100 * 1024:
                            with open(user_cookie_path, "wb") as cf:
                                cf.write(content)
                            if test_youtube_cookies_on_url(user_cookie_path, url):
                                cookie_file = user_cookie_path
                                logger.info(f"YouTube cookies from source {i} work on user's URL for format detection for user {user_id} - saved to user folder")
                                success = True
                                break
                            else:
                                logger.warning(f"YouTube cookies from source {i} don't work on user's URL for format detection for user {user_id}")
                        else:
                            logger.warning(f"Failed to download YouTube cookies from source {i} for format detection for user {user_id}")
                    
                    if not success:
                        logger.warning(f"All YouTube cookie sources failed for format detection for user {user_id}, will try without cookies")
                        cookie_file = None
                else:
                    logger.warning(f"No YouTube cookie sources configured for format detection for user {user_id}, will try without cookies")
                    cookie_file = None
        else:
            # For non-YouTube URLs, use existing logic
            if os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
            else:
                # If not in the user folder, we copy from the global folder
                global_cookie_path = Config.COOKIE_FILE_PATH
                if os.path.exists(global_cookie_path):
                    try:
                        create_directory(user_dir)
                        import shutil
                        shutil.copy2(global_cookie_path, user_cookie_path)
                        logger.info(f"Copied global cookie file to user {user_id} folder for format detection")
                        cookie_file = user_cookie_path
                    except Exception as e:
                        logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                        cookie_file = None
                else:
                    cookie_file = None
        
        # We check whether to use —no-Cookies for this domain
        if is_no_cookie_domain(url):
            ytdl_opts['cookiefile'] = None  # Equivalent-No-Cookies
            logger.info(f"Using --no-cookies for domain in get_video_formats: {url}")
        elif cookie_file:
            ytdl_opts['cookiefile'] = cookie_file
        
        # Add proxy configuration if needed for this domain
        if use_proxy:
            # Force proxy for this request
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
                logger.info(f"Force using proxy for format detection: {proxy_url}")
            else:
                logger.warning("Proxy requested but proxy configuration is incomplete")
        else:
            # Add proxy configuration if needed for this domain
            from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
            ytdl_opts = add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)
    
    # Add PO token provider for YouTube domains
    ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
    
    # Try with proxy fallback if user proxy is enabled
    def extract_info_operation(opts):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if 'entries' in info and info.get('entries'):
                info = info['entries'][0]
            
            # Check for live stream after extraction
            if info and info.get('is_live', False):
                logger.warning(f"Live stream detected in get_video_formats: {url}")
                return {'error': 'LIVE_STREAM_DETECTED'}
            
            return info
        except yt_dlp.utils.DownloadError as e:
            error_text = str(e)
            logger.error(f"DownloadError in get_video_formats: {error_text}")
            
            # Check for live stream detection
            if "LIVE_STREAM_DETECTED" in error_text:
                return {'error': 'LIVE_STREAM_DETECTED'}
            
            # Check for YouTube cookie errors and try automatic retry
            if is_youtube_url(url) and user_id is not None:
                from COMMANDS.cookies_cmd import is_youtube_cookie_error, retry_download_with_different_cookies
                
                if is_youtube_cookie_error(error_text):
                    logger.info(f"YouTube cookie error detected in get_video_formats for user {user_id}, attempting automatic retry")
                    
                    # Try retry with different cookies
                    retry_result = retry_download_with_different_cookies(
                        user_id, url, extract_info_operation, opts
                    )
                    
                    if retry_result is not None:
                        logger.info(f"get_video_formats retry with different cookies successful for user {user_id}")
                        return retry_result
                    else:
                        logger.warning(f"All cookie retry attempts failed in get_video_formats for user {user_id}")
            
            # Re-raise other DownloadErrors
            raise e
        except Exception as e:
            logger.error(f"Error extracting info for {url}: {e}")
            raise e
    
    from HELPERS.proxy_helper import try_with_proxy_fallback
    result = try_with_proxy_fallback(ytdl_opts, url, user_id, extract_info_operation)
    if result is None:
        return {'error': 'Failed to extract video information with all available proxies'}
    return result


# YT-DLP HOOK

def ytdlp_hook(d):
    logger.info(d['status'])
