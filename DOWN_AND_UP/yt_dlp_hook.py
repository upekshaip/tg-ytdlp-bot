# --- receiving formats and metadata via yt-dlp ---
import os
import yt_dlp
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.logger import logger, send_error_to_user
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
from URL_PARSERS.filter_check import is_no_filter_domain
from URL_PARSERS.filter_utils import create_smart_match_filter, create_legacy_match_filter
from HELPERS.pot_helper import add_pot_to_ytdl_opts
from CONFIG.limits import LimitsConfig
from HELPERS.fallback_helper import should_fallback_to_gallery_dl

async def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False):
    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
    logger.info(f"🔍 [DEBUG] get_video_formats вызвана с параметрами:")
    logger.info(f"   url: {url}")
    logger.info(f"   user_id: {user_id}")
    logger.info(f"   playlist_start_index: {playlist_start_index}")
    logger.info(f"   cookies_already_checked: {cookies_already_checked}")
    logger.info(f"   use_proxy: {use_proxy}")
    
    messages = safe_get_messages(user_id)
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
        logger.info(safe_get_messages(user_id).YTDLP_SKIPPING_MATCH_FILTER_MSG.format(url=url))
    
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
                logger.info(safe_get_messages(user_id).YTDLP_CHECKING_EXISTING_YOUTUBE_COOKIES_MSG.format(user_id=user_id))
                if await test_youtube_cookies_on_url(user_cookie_path, url):
                    cookie_file = user_cookie_path
                    logger.info(safe_get_messages(user_id).YTDLP_EXISTING_YOUTUBE_COOKIES_WORK_MSG.format(user_id=user_id))
                else:
                    logger.info(safe_get_messages(user_id).YTDLP_EXISTING_YOUTUBE_COOKIES_FAILED_MSG.format(user_id=user_id))
                    cookie_urls = await get_youtube_cookie_urls()
                    if cookie_urls:
                        success = False
                        for i, cookie_url in enumerate(cookie_urls, 1):
                            logger.info(safe_get_messages(user_id).YTDLP_TRYING_YOUTUBE_COOKIE_SOURCE_MSG.format(i=i, user_id=user_id))
                            try:

                                ok, status_code, content, error = await _download_content(cookie_url)
                            except Exception as download_e:
                                logger.error(f"Error processing cookie source {i} for user {user_id}: {download_e}")
                                continue
                            if ok and content and len(content) <= 100 * 1024:
                                with open(user_cookie_path, "wb") as cf:
                                    cf.write(content)
                                if await test_youtube_cookies_on_url(user_cookie_path, url):
                                    cookie_file = user_cookie_path
                                    logger.info(safe_get_messages(user_id).YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_WORK_MSG.format(i=i, user_id=user_id))
                                    success = True
                                    break
                                else:
                                    logger.warning(safe_get_messages(user_id).YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_DONT_WORK_MSG.format(i=i, user_id=user_id))
                            else:
                                logger.warning(safe_get_messages(user_id).YTDLP_FAILED_DOWNLOAD_YOUTUBE_COOKIES_MSG.format(i=i, user_id=user_id))
                        
                        if not success:
                            logger.warning(safe_get_messages(user_id).YTDLP_ALL_YOUTUBE_COOKIE_SOURCES_FAILED_MSG.format(user_id=user_id))
                            cookie_file = None
                    else:
                        logger.warning(safe_get_messages(user_id).YTDLP_NO_YOUTUBE_COOKIE_SOURCES_CONFIGURED_MSG.format(user_id=user_id))
                        cookie_file = None
            else:
                logger.info(safe_get_messages(user_id).YTDLP_NO_YOUTUBE_COOKIES_FOUND_MSG.format(user_id=user_id))
                cookie_urls = await get_youtube_cookie_urls()
                if cookie_urls:
                    success = False
                    for i, cookie_url in enumerate(cookie_urls, 1):
                        logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                        try:
                            ok, status_code, content, error = await _download_content(cookie_url)
                        except Exception as download_e:
                            logger.error(f"Error processing cookie source {i} for user {user_id}: {download_e}")
                            continue
                        if ok and content and len(content) <= 100 * 1024:
                            with open(user_cookie_path, "wb") as cf:
                                cf.write(content)
                            if await test_youtube_cookies_on_url(user_cookie_path, url):
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
                logger.info(safe_get_messages(user_id).YTDLP_USING_YOUTUBE_COOKIES_ALREADY_VALIDATED_MSG.format(user_id=user_id))
            else:
                # Cookies were deleted - try to restore them on user's URL
                logger.info(safe_get_messages(user_id).YTDLP_NO_YOUTUBE_COOKIES_FOUND_ATTEMPTING_RESTORE_MSG.format(user_id=user_id))
                from COMMANDS.cookies_cmd import get_youtube_cookie_urls, test_youtube_cookies_on_url, _download_content
                cookie_urls = await get_youtube_cookie_urls()
                if cookie_urls:
                    success = False
                    for i, cookie_url in enumerate(cookie_urls, 1):
                        logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                        try:
                            ok, status_code, content, error = await _download_content(cookie_url)
                        except Exception as download_e:
                            logger.error(f"Error processing cookie source {i} for user {user_id}: {download_e}")
                            continue
                        if ok and content and len(content) <= 100 * 1024:
                            with open(user_cookie_path, "wb") as cf:
                                cf.write(content)
                            if await test_youtube_cookies_on_url(user_cookie_path, url):
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
                        logger.info(safe_get_messages(user_id).YTDLP_COPIED_GLOBAL_COOKIE_FILE_MSG.format(user_id=user_id))
                        cookie_file = user_cookie_path
                    except Exception as e:
                        logger.error(safe_get_messages(user_id).YTDLP_FAILED_COPY_GLOBAL_COOKIE_FILE_MSG.format(user_id=user_id, error=e))
                        cookie_file = None
                else:
                    cookie_file = None
        
        # We check whether to use —no-Cookies for this domain
        if is_no_cookie_domain(url):
            ytdl_opts['cookiefile'] = None  # Equivalent-No-Cookies
            logger.info(safe_get_messages(user_id).YTDLP_USING_NO_COOKIES_FOR_DOMAIN_MSG.format(url=url))
        elif cookie_file:
            ytdl_opts['cookiefile'] = cookie_file
            logger.info(f"[YTDLP DEBUG] Using cookies for {url}: {cookie_file}")
        else:
            logger.info(f"[YTDLP DEBUG] No cookies available for {url}")
        
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
            ytdl_opts = await add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)
    
    # Add PO token provider for YouTube domains
    ytdl_opts = await add_pot_to_ytdl_opts(ytdl_opts, url)
    
    # Try with proxy fallback if user proxy is enabled
    async def extract_info_operation(opts):
        try:
            logger.info(f"🔍 [DEBUG] extract_info_operation: начинаем извлечение информации")
            logger.info(f"   url: {url}")
            logger.info(f"   opts keys: {list(opts.keys())}")
            
            from HELPERS.async_ytdlp import async_extract_info
            info = await async_extract_info(opts, url, user_id)
            
            logger.info(f"✅ [DEBUG] extract_info_operation: извлечение завершено")
            logger.info(f"   info type: {type(info)}")
            if isinstance(info, dict):
                logger.info(f"   info keys: {list(info.keys())}")
                if 'duration' in info:
                    logger.info(f"   duration: {info['duration']} (тип: {type(info['duration'])})")
                if 'is_live' in info:
                    logger.info(f"   is_live: {info['is_live']} (тип: {type(info['is_live'])})")
            
            # Normalize info to a dict
            if isinstance(info, list):
                info = (info[0] if len(info) > 0 else {})
                logger.info(f"🔍 [DEBUG] info был списком, взяли первый элемент")
            elif isinstance(info, dict) and 'entries' in info:
                entries = info.get('entries')
                if isinstance(entries, list) and len(entries) > 0:
                    info = entries[0]
                    logger.info(f"🔍 [DEBUG] info содержал entries, взяли первый элемент")
            
            # Check for live stream after extraction
            if info and info.get('is_live', False):
                logger.warning(f"Live stream detected in get_video_formats: {url}")
                return {'error': 'LIVE_STREAM_DETECTED'}
            
            logger.info(f"✅ [DEBUG] extract_info_operation: возвращаем info")
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
                    retry_result = await retry_download_with_different_cookies(
                        user_id, url, extract_info_operation, opts
                    )
                    
                    if retry_result is not None:
                        logger.info(f"get_video_formats retry with different cookies successful for user {user_id}")
                        return retry_result
                    else:
                        logger.warning(f"All cookie retry attempts failed in get_video_formats for user {user_id}")
            
            # Check for TikTok private account error
            if "tiktok.com" in url.lower() and "private" in error_text.lower() and "account" in error_text.lower():
                logger.info(f"TikTok private account detected for {url}, recommending gallery-dl fallback")
                return {'error': 'TIKTOK_PRIVATE_ACCOUNT', 'original_error': error_text}
            
            # Check if we should fallback to gallery-dl
            if should_fallback_to_gallery_dl(error_text, url):
                logger.info(f"Fallback to gallery-dl recommended for {url} due to error: {error_text[:200]}...")
                return {'error': 'FALLBACK_TO_GALLERY_DL', 'original_error': error_text}
            
            # Re-raise other DownloadErrors
            raise e
        except Exception as e:
            logger.error(f"Error extracting info for {url}: {e}")
            raise e
    
    # Try with proxy fallback if user proxy is enabled
    from HELPERS.proxy_helper import try_with_proxy_fallback
    result = await try_with_proxy_fallback(ytdl_opts, url, user_id, extract_info_operation)
    if result is None:
        return {'error': 'Failed to extract video information with all available proxies'}
    return result


# YT-DLP HOOK

def ytdlp_hook(d):
    logger.info(d['status'])
