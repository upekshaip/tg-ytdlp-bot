# --- receiving formats and metadata via yt-dlp ---
import os
import yt_dlp
from CONFIG.config import Config
from HELPERS.logger import logger
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.pot_helper import add_pot_to_ytdl_opts

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
    
    # Add user's custom yt-dlp arguments
    if user_id is not None:
        from COMMANDS.args_cmd import get_user_ytdlp_args, log_ytdlp_options
        user_args = get_user_ytdlp_args(user_id, url)
        if user_args:
            ytdl_opts.update(user_args)
        
        # Log final yt-dlp options for debugging
        log_ytdlp_options(user_id, ytdl_opts, "get_video_formats")
    
    if user_id is not None:
        user_dir = os.path.join("users", str(user_id))
        # Check the availability of cookie.txt in the user folder
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        
        # For YouTube URLs, ensure working cookies (skip if already checked)
        if is_youtube_url(url) and not cookies_already_checked:
            from COMMANDS.cookies_cmd import ensure_working_youtube_cookies
            has_working_cookies = ensure_working_youtube_cookies(user_id)
            if has_working_cookies and os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
                logger.info(f"Using working YouTube cookies for format detection for user {user_id}")
            else:
                cookie_file = None
                logger.info(f"No working YouTube cookies available for format detection for user {user_id}, will try without cookies")
        elif is_youtube_url(url) and cookies_already_checked:
            # Cookies already checked in Always Ask menu - use them directly without verification
            if os.path.exists(user_cookie_path):
                cookie_file = user_cookie_path
                logger.info(f"Using YouTube cookies for format detection for user {user_id} (already validated in Always Ask menu)")
            else:
                # Cookies were deleted - try to restore them
                logger.info(f"No YouTube cookies found for format detection for user {user_id}, attempting to restore...")
                from COMMANDS.cookies_cmd import ensure_working_youtube_cookies
                has_working_cookies = ensure_working_youtube_cookies(user_id)
                if has_working_cookies and os.path.exists(user_cookie_path):
                    cookie_file = user_cookie_path
                    logger.info(f"Successfully restored working YouTube cookies for format detection for user {user_id}")
                else:
                    cookie_file = None
                    logger.info(f"Failed to restore YouTube cookies for format detection for user {user_id}, will try without cookies")
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
                return info['entries'][0]
            return info
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
