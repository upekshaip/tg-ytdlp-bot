# PO Token Helper for YouTube
# Adds PO token provider support for YouTube domains

import requests
import time
import re
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.logger import logger

# Cache for PO token provider availability checks
_pot_provider_cache = {
    'available': None,
    'last_check': 0,
    'check_interval': 30  # Check every 30 seconds
}

def check_pot_provider_availability(base_url: str) -> bool:
    """
    Check PO token provider availability.
    
    Args:
        base_url (str): Provider URL
        
    Returns:
        bool: True if the provider is available, otherwise False
    """
    current_time = time.time()
    
    # Check cache
    if (_pot_provider_cache['available'] is not None and 
        current_time - _pot_provider_cache['last_check'] < _pot_provider_cache['check_interval']):
        return _pot_provider_cache['available']
    
    try:
        # Fast availability check
        # The PO token provider may return 404 for the root path, which still means the service is running.
        response = requests.get(base_url, timeout=5)
        is_available = response.status_code in [200, 404]  # 404 means service is up but endpoint not found
        
        # Update cache
        _pot_provider_cache['available'] = is_available
        _pot_provider_cache['last_check'] = current_time
        
        if is_available:
            logger.info(f"PO token provider is available at {base_url} (status: {response.status_code})")
        else:
            logger.warning(f"PO token provider returned status {response.status_code} at {base_url}")
        
        return is_available
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"PO token provider is not available at {base_url}: {e}")
        
        # Update cache
        _pot_provider_cache['available'] = False
        _pot_provider_cache['last_check'] = current_time
        
        return False

def add_pot_to_ytdl_opts(ytdl_opts: dict, url: str) -> dict:
    """
    Add PO token arguments to yt-dlp options for YouTube domains.
    
    Args:
        ytdl_opts (dict): yt-dlp options dict
        url (str): URL to check
        
    Returns:
        dict: Updated yt-dlp options dict
    """
    # Check whether the PO token provider is enabled
    if not getattr(Config, 'YOUTUBE_POT_ENABLED', False):
        messages = safe_get_messages()
        logger.info(messages.HELPER_POT_PROVIDER_DISABLED_MSG)
        return ytdl_opts
    
    # Check whether URL is a YouTube domain
    if not is_youtube_url(url):
        messages = safe_get_messages()
        logger.info(messages.HELPER_POT_URL_NOT_YOUTUBE_MSG.format(url=url))
        return ytdl_opts
    
    # Get provider base URL
    base_url = getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')
    disable_innertube = getattr(Config, 'YOUTUBE_POT_DISABLE_INNERTUBE', False)
    
    # Check PO token provider availability
    if not check_pot_provider_availability(base_url):
        messages = safe_get_messages()
        logger.warning(messages.HELPER_POT_PROVIDER_NOT_AVAILABLE_MSG.format(base_url=base_url))
        return ytdl_opts

    # Add extractor_args to yt-dlp options
    if 'extractor_args' not in ytdl_opts:
        ytdl_opts['extractor_args'] = {}
    
    # Add YouTube PO token provider args in the correct format (nightly ≥ 2025-09-13)
    # Structure:
    # extractor_args: {
    #   'youtubepot': {
    #       'providers': ['bgutilhttp'],
    #       'bgutilhttp': { 'base_url': ['http://...'] },
    #       'disable_innertube': ['1']  # optional
    #   }
    # }
    pot_args = ytdl_opts['extractor_args'].get('youtubepot', {})
    pot_args['providers'] = list(dict.fromkeys((pot_args.get('providers') or []) + ['bgutilhttp']))
    bg_cfg = pot_args.get('bgutilhttp', {})
    bg_cfg['base_url'] = [base_url]
    pot_args['bgutilhttp'] = bg_cfg
    if disable_innertube:
        pot_args['disable_innertube'] = ["1"]
    ytdl_opts['extractor_args']['youtubepot'] = pot_args
    
    # Enable verbose for detailed PO token logging
    ytdl_opts['verbose'] = True
    
    # Add a debug hook for PO tokens
    ytdl_opts = add_pot_debug_hook(ytdl_opts)
    
    # Explicit logs to show active providers
    active_providers = ytdl_opts['extractor_args'].get('youtubepot', {}).get('providers', [])
    logger.info(f"🔑 PO TOKEN PROVIDER ENABLED for YouTube URL: {url}")
    logger.info(f"🔗 PO Token Base URL: {base_url}")
    logger.info(f"🧩 PO Token Providers: {active_providers}")
    logger.info(f"⚙️  PO Token Config: disable_innertube={disable_innertube}")
    logger.info(f"📋 extractor_args.youtubepot: {ytdl_opts['extractor_args'].get('youtubepot')}")
    
    return ytdl_opts

def is_pot_enabled() -> bool:
    """
    Check whether the PO token provider is enabled in config.
    
    Returns:
        bool: True if enabled, otherwise False
    """
    return getattr(Config, 'YOUTUBE_POT_ENABLED', False)

def get_pot_base_url() -> str:
    """
    Return the PO token provider base URL.
    
    Returns:
        str: Provider base URL
    """
    return getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')

def clear_pot_provider_cache():
    messages = safe_get_messages(None)
    """
    Reset the PO token provider availability cache.
    Useful to force a re-check after provider recovery.
    """
    global _pot_provider_cache
    _pot_provider_cache['available'] = None
    _pot_provider_cache['last_check'] = 0
    messages = safe_get_messages()
    logger.info(messages.HELPER_POT_PROVIDER_CACHE_CLEARED_MSG)

def is_pot_provider_available() -> bool:
    """
    Check whether the PO token provider is available (with caching).
    
    Returns:
        bool: True if available, otherwise False
    """
    base_url = getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')
    return check_pot_provider_availability(base_url)

def create_pot_debug_hook():
    messages = safe_get_messages(None)
    """
    Create a yt-dlp hook that intercepts and logs PO tokens.
    
    Returns:
        function: Hook function for yt-dlp
    """
    def pot_debug_hook(d):
        messages = safe_get_messages(None)
        """
        Hook to intercept PO tokens in yt-dlp.
        
        Args:
            d (dict): Download info dict
        """
        if d['status'] == 'downloading':
            # Look for PO tokens in URL or headers
            if 'url' in d:
                url = d['url']
                # Look for PO tokens in URL
                pot_patterns = [
                    r'po_token=([^&]+)',
                    r'popt=([^&]+)',
                    r'pot=([^&]+)',
                    r'proof_of_origin=([^&]+)'
                ]
                
                for pattern in pot_patterns:
                    match = re.search(pattern, url)
                    if match:
                        token = match.group(1)
                        logger.info(f"🎯 PO TOKEN DETECTED in URL: {token[:20]}...")
                        logger.info(f"🔗 Full URL with PO token: {url}")
                        break
                
                # Check headers for PO tokens
                if 'http_headers' in d:
                    headers = d['http_headers']
                    for header_name, header_value in headers.items():
                        if 'po' in header_name.lower() or 'token' in header_name.lower():
                            logger.info(f"🎯 PO TOKEN in header {header_name}: {header_value}")
        
        elif d['status'] == 'finished':
            # Log successful completion with PO tokens
            messages = safe_get_messages()
            logger.info(messages.HELPER_DOWNLOAD_FINISHED_PO_MSG)
            
    return pot_debug_hook

def add_pot_debug_hook(ytdl_opts: dict) -> dict:
    """
    Add a PO token debug hook to yt-dlp options.
    
    Args:
        ytdl_opts (dict): yt-dlp options dict
        
    Returns:
        dict: Updated yt-dlp options dict
    """
    if 'progress_hooks' not in ytdl_opts:
        ytdl_opts['progress_hooks'] = []
    
    # Add our PO token debug hook
    ytdl_opts['progress_hooks'].append(create_pot_debug_hook())
    
    return ytdl_opts

def build_cli_extractor_args(url: str) -> list[str]:
    """
    Build yt-dlp CLI args (--extractor-args) with PO token support.
    Returns ["--extractor-args", VALUE] or an empty list when not needed.
    """
    try:
        # Check enablement and domain
        if not getattr(Config, 'YOUTUBE_POT_ENABLED', False):
            return []
        if not is_youtube_url(url):
            return []
        base_url = getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')
        disable_innertube = getattr(Config, 'YOUTUBE_POT_DISABLE_INNERTUBE', False)

        # CLI syntax for sub-provider: youtubepot-bgutilhttp:base_url=...;disable_innertube=1
        pot_segment = f"youtubepot-bgutilhttp:base_url={base_url}"
        if disable_innertube:
            pot_segment += ";disable_innertube=1"

        # Extra extractor-args (comma-separated namespaces)
        messages = safe_get_messages()
        generic_args = messages.HELPER_POT_GENERIC_ARGS_MSG
        value = ",".join([pot_segment, generic_args])
        logger.info(f"🧱 CLI extractor-args built for POT: {value}")
        return ['--extractor-args', value]
    except Exception as e:
        logger.warning(f"Failed to build CLI extractor-args for POT: {e}")
        return []
