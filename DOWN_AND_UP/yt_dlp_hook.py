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

def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):
    # Detailed debug logging
    logger.info("🔍 [DEBUG] get_video_formats called with parameters:")
    logger.info(f"   url: {url}")
    logger.info(f"   user_id: {user_id}")
    logger.info(f"   playlist_start_index: {playlist_start_index}")
    logger.info(f"   playlist_end_index: {playlist_end_index}")
    logger.info(f"   cookies_already_checked: {cookies_already_checked}")
    logger.info(f"   use_proxy: {use_proxy}")
    
    # Reset the "checked cookie sources" cache for a new task
    if user_id is not None:
        from COMMANDS.cookies_cmd import reset_checked_cookie_sources
        reset_checked_cookie_sources(user_id)
        logger.info(f"🔄 [DEBUG] Reset checked cookie sources for new task for user {user_id}")
    
    messages = safe_get_messages(user_id)
    
    # Build playlist_items taking the range into account
    if playlist_end_index is not None and playlist_end_index != playlist_start_index:
        # For ranges, use START:END or START:END:-1 for reverse order
        if playlist_start_index < 0 or playlist_end_index < 0:
            # For negative indices determine reverse order
            is_reverse = (playlist_start_index < 0 and playlist_end_index < 0 and abs(playlist_start_index) < abs(playlist_end_index)) or (playlist_start_index > playlist_end_index)
            if is_reverse:
                playlist_items_str = f"{playlist_start_index}:{playlist_end_index}:-1"
            else:
                playlist_items_str = f"{playlist_start_index}:{playlist_end_index}"
        elif playlist_start_index > playlist_end_index:
            # Reverse order with positive indices
            playlist_items_str = f"{playlist_start_index}:{playlist_end_index}:-1"
        else:
            # Forward order
            playlist_items_str = f"{playlist_start_index}:{playlist_end_index}"
    else:
        # Single item
        playlist_items_str = str(playlist_start_index)
    
    ytdl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'no_warnings': True,
        'extract_flat': False,
        'simulate': True,
        'playlist_items': playlist_items_str,    
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
                if test_youtube_cookies_on_url(user_cookie_path, url, user_id):
                    cookie_file = user_cookie_path
                    logger.info(safe_get_messages(user_id).YTDLP_EXISTING_YOUTUBE_COOKIES_WORK_MSG.format(user_id=user_id))
                else:
                    logger.info(safe_get_messages(user_id).YTDLP_EXISTING_YOUTUBE_COOKIES_FAILED_MSG.format(user_id=user_id))
                    cookie_urls = get_youtube_cookie_urls()
                    if cookie_urls:
                        # Use only unchecked sources for this user
                        from COMMANDS.cookies_cmd import get_unchecked_cookie_sources, mark_cookie_source_checked
                        unchecked_indices = get_unchecked_cookie_sources(user_id, cookie_urls)
                        if not unchecked_indices:
                            logger.warning(f"All cookie sources have been checked for user {user_id}, no more sources to try")
                            cookie_file = None
                        else:
                            success = False
                            for i, idx in enumerate(unchecked_indices, 1):
                                cookie_url = cookie_urls[idx]
                                logger.info(safe_get_messages(user_id).YTDLP_TRYING_YOUTUBE_COOKIE_SOURCE_MSG.format(i=idx + 1, user_id=user_id))
                                
                                # Mark the source as checked
                                mark_cookie_source_checked(user_id, idx)
                                
                                try:
                                    ok, status_code, content, error = _download_content(cookie_url, user_id=user_id)
                                except Exception as download_e:
                                    logger.error(f"Error processing cookie source {idx + 1} for user {user_id}: {download_e}")
                                    continue
                                if ok and content and len(content) <= 100 * 1024:
                                    with open(user_cookie_path, "wb") as cf:
                                        cf.write(content)
                                    if test_youtube_cookies_on_url(user_cookie_path, url, user_id):
                                        cookie_file = user_cookie_path
                                        logger.info(safe_get_messages(user_id).YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_WORK_MSG.format(i=idx + 1, user_id=user_id))
                                        success = True
                                        break
                                    else:
                                        logger.warning(safe_get_messages(user_id).YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_DONT_WORK_MSG.format(i=idx + 1, user_id=user_id))
                                        if os.path.exists(user_cookie_path):
                                            os.remove(user_cookie_path)
                                else:
                                    logger.warning(safe_get_messages(user_id).YTDLP_FAILED_DOWNLOAD_YOUTUBE_COOKIES_MSG.format(i=idx + 1, user_id=user_id))
                        
                        if not success:
                            logger.warning(safe_get_messages(user_id).YTDLP_ALL_YOUTUBE_COOKIE_SOURCES_FAILED_MSG.format(user_id=user_id))
                            cookie_file = None
                    else:
                        logger.warning(safe_get_messages(user_id).YTDLP_NO_YOUTUBE_COOKIE_SOURCES_CONFIGURED_MSG.format(user_id=user_id))
                        cookie_file = None
            else:
                logger.info(safe_get_messages(user_id).YTDLP_NO_YOUTUBE_COOKIES_FOUND_MSG.format(user_id=user_id))
                cookie_urls = get_youtube_cookie_urls()
                if cookie_urls:
                    # Use only unchecked sources for this user
                    from COMMANDS.cookies_cmd import get_unchecked_cookie_sources, mark_cookie_source_checked
                    unchecked_indices = get_unchecked_cookie_sources(user_id, cookie_urls)
                    if not unchecked_indices:
                        logger.warning(f"All cookie sources have been checked for user {user_id}, no more sources to try")
                        cookie_file = None
                    else:
                        success = False
                        for i, idx in enumerate(unchecked_indices, 1):
                            cookie_url = cookie_urls[idx]
                            logger.info(f"Trying YouTube cookie source {idx + 1} for format detection for user {user_id}")
                            
                            # Mark the source as checked
                            mark_cookie_source_checked(user_id, idx)
                            
                            try:
                                ok, status_code, content, error = _download_content(cookie_url, user_id=user_id)
                            except Exception as download_e:
                                logger.error(f"Error processing cookie source {idx + 1} for user {user_id}: {download_e}")
                                continue
                            if ok and content and len(content) <= 100 * 1024:
                                with open(user_cookie_path, "wb") as cf:
                                    cf.write(content)
                                if test_youtube_cookies_on_url(user_cookie_path, url, user_id):
                                    cookie_file = user_cookie_path
                                    logger.info(f"YouTube cookies from source {idx + 1} work on user's URL for format detection for user {user_id} - saved to user folder")
                                    success = True
                                    break
                                else:
                                    logger.warning(f"YouTube cookies from source {idx + 1} don't work on user's URL for format detection for user {user_id}")
                                    if os.path.exists(user_cookie_path):
                                        os.remove(user_cookie_path)
                            else:
                                logger.warning(f"Failed to download YouTube cookies from source {idx + 1} for format detection for user {user_id}")
                        
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
                cookie_urls = get_youtube_cookie_urls()
                if cookie_urls:
                    success = False
                    for i, cookie_url in enumerate(cookie_urls, 1):
                        logger.info(f"Trying YouTube cookie source {i} for format detection for user {user_id}")
                        try:
                            ok, status_code, content, error = _download_content(cookie_url, user_id=user_id)
                        except Exception as download_e:
                            logger.error(f"Error processing cookie source {i} for user {user_id}: {download_e}")
                            continue
                        if ok and content and len(content) <= 100 * 1024:
                            with open(user_cookie_path, "wb") as cf:
                                cf.write(content)
                            if test_youtube_cookies_on_url(user_cookie_path, url, user_id):
                                cookie_file = user_cookie_path
                                logger.info(f"YouTube cookies from source {i} work on user's URL for format detection for user {user_id} - saved to user folder")
                                success = True
                                break
                            else:
                                logger.warning(f"YouTube cookies from source {i} don't work on user's URL for format detection for user {user_id}")
                                if os.path.exists(user_cookie_path):
                                    os.remove(user_cookie_path)
                        else:
                            logger.warning(f"Failed to download YouTube cookies from source {i} for format detection for user {user_id}")
                    
                    if not success:
                        logger.warning(f"All YouTube cookie sources failed for format detection for user {user_id}, will try without cookies")
                        cookie_file = None
                else:
                    logger.warning(f"No YouTube cookie sources configured for format detection for user {user_id}, will try without cookies")
                    cookie_file = None
        else:
            # For non-YouTube URLs, use new cookie fallback system
            from COMMANDS.cookies_cmd import get_cookie_cache_result, try_non_youtube_cookie_fallback
            cache_result = get_cookie_cache_result(user_id, url)
            
            if cache_result and cache_result['result']:
                # Use cached successful cookies
                cookie_file = cache_result['cookie_path']
                logger.info(f"Using cached cookies for non-YouTube format detection: {url}")
            else:
                # Try user cookies first
                if os.path.exists(user_cookie_path):
                    cookie_file = user_cookie_path
                    logger.info(f"Using user cookies for non-YouTube format detection: {url}")
                else:
                    # No user cookies, will try fallback during format detection
                    cookie_file = None
                    logger.info(f"No user cookies found for non-YouTube format detection: {url}, will try fallback")
        
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
            ytdl_opts = add_proxy_to_ytdl_opts(ytdl_opts, url, user_id)
    
    # Add PO token provider for YouTube domains
    ytdl_opts = add_pot_to_ytdl_opts(ytdl_opts, url)
    
    # Try with proxy fallback if user proxy is enabled
    def extract_info_operation(opts):
        try:
            logger.info("🔍 [DEBUG] extract_info_operation: starting extraction")
            logger.info(f"   url: {url}")
            logger.info(f"   opts keys: {list(opts.keys())}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            logger.info("✅ [DEBUG] extract_info_operation: extraction finished")
            logger.info(f"   info type: {type(info)}")
            if isinstance(info, dict):
                logger.info(f"   info keys: {list(info.keys())}")
                if 'duration' in info:
                    logger.info(f"   duration: {info['duration']} (type: {type(info['duration'])})")
                if 'is_live' in info:
                    logger.info(f"   is_live: {info['is_live']} (type: {type(info['is_live'])})")
            
            # Normalize info to a dict
            # For playlists, keep all entries to download thumbnails/covers
            playlist_entries = None
            if isinstance(info, list):
                info = (info[0] if len(info) > 0 else {})
                logger.info("🔍 [DEBUG] info was a list; using the first element")
            elif isinstance(info, dict) and 'entries' in info:
                entries = info.get('entries')
                if isinstance(entries, list) and len(entries) > 0:
                    # Keep all entries for thumbnail/cover downloads
                    playlist_entries = entries
                    info = entries[0]
                    logger.info(f"🔍 [DEBUG] info contained entries; using the first element. Total entries: {len(entries)}")
                    # Attach entries for ask_quality_menu
                    info['_playlist_entries'] = playlist_entries
            
            # Check for live stream after extraction (only if detection is enabled)
            if info and info.get('is_live', False) and LimitsConfig.ENABLE_LIVE_STREAM_BLOCKING:
                logger.warning(f"Live stream detected in get_video_formats: {url}")
                return {'error': 'LIVE_STREAM_DETECTED'}
            
            # Cache successful cookie result for future use
            if not is_youtube_url(url) and user_id is not None:
                from COMMANDS.cookies_cmd import set_cookie_cache_result
                cookie_file_path = opts.get('cookiefile')
                if cookie_file_path and os.path.exists(cookie_file_path):
                    set_cookie_cache_result(user_id, url, True, cookie_file_path)
                    logger.info(f"Cached successful cookie result for format detection {url}")
            
            logger.info("✅ [DEBUG] extract_info_operation: returning info")
            return info
        except yt_dlp.utils.DownloadError as e:
            error_text = str(e)
            logger.error(f"DownloadError in get_video_formats: {error_text}")
            
            # Check for live stream detection (only if detection is enabled)
            if "LIVE_STREAM_DETECTED" in error_text and LimitsConfig.ENABLE_LIVE_STREAM_BLOCKING:
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
            elif not is_youtube_url(url) and user_id is not None:
                # For non-YouTube sites, try cookie fallback
                logger.info(f"Non-YouTube error detected in get_video_formats for user {user_id}, attempting cookie fallback")
                
                # Check if error is cookie-related
                error_str = error_text.lower()
                if any(keyword in error_str for keyword in ['cookie', 'auth', 'login', 'sign in', '403', '401', 'forbidden', 'unauthorized']):
                    logger.info(f"Error appears to be cookie-related for {url}, trying cookie fallback")
                    
                    # Try cookie fallback with new system
                    from COMMANDS.cookies_cmd import try_non_youtube_cookie_fallback
                    retry_result = try_non_youtube_cookie_fallback(
                        user_id, url, extract_info_operation, opts
                    )
                    
                    if retry_result is not None:
                        logger.info(f"get_video_formats retry with cookie fallback successful for user {user_id}")
                        return retry_result
                    else:
                        logger.warning(f"get_video_formats retry with cookie fallback failed for user {user_id}")
                else:
                    logger.info(f"Error appears to be non-cookie-related for {url}, skipping cookie fallback")
            
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
    
    from HELPERS.proxy_helper import try_with_proxy_fallback
    result = try_with_proxy_fallback(ytdl_opts, url, user_id, extract_info_operation)
    if result is None:
        return {'error': 'Failed to extract video information with all available proxies'}
    return result


# YT-DLP HOOK

def ytdlp_hook(d):
    logger.info(d['status'])
