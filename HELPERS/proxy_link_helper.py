import re
from urllib.parse import urlparse
from CONFIG.config import Config
from HELPERS.logger import logger

def is_proxy_domain(url):
    """
    Check whether a proxy should be used for the given URL.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if the domain is in PROXY_DOMAINS or PROXY_2_DOMAINS
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Strip "www." if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Check PROXY_DOMAINS
        if hasattr(Config, 'PROXY_DOMAINS') and Config.PROXY_DOMAINS:
            # Exact domain match
            if domain in Config.PROXY_DOMAINS:
                logger.info(f"Domain {domain} found in PROXY_DOMAINS list")
                return True
                
            # Subdomain match
            for proxy_domain in Config.PROXY_DOMAINS:
                if domain.endswith('.' + proxy_domain) or domain == proxy_domain:
                    logger.info(f"Domain {domain} matches proxy domain {proxy_domain}")
                    return True
        
        # Check PROXY_2_DOMAINS
        if hasattr(Config, 'PROXY_2_DOMAINS') and Config.PROXY_2_DOMAINS:
            # Exact domain match
            if domain in Config.PROXY_2_DOMAINS:
                logger.info(f"Domain {domain} found in PROXY_2_DOMAINS list")
                return True
                
            # Subdomain match
            for proxy_domain in Config.PROXY_2_DOMAINS:
                if domain.endswith('.' + proxy_domain) or domain == proxy_domain:
                    logger.info(f"Domain {domain} matches proxy_2 domain {proxy_domain}")
                    return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking proxy domain for {url}: {e}")
        return False

def get_proxy_config():
    """
    Return configuration for the first proxy from settings.
    
    Returns:
        dict: Proxy configuration or None if not configured
    """
    try:
        # Ensure all required proxy settings are present
        if (hasattr(Config, 'PROXY_TYPE') and 
            hasattr(Config, 'PROXY_IP') and 
            hasattr(Config, 'PROXY_PORT') and
            Config.PROXY_IP and 
            Config.PROXY_PORT):
            
            proxy_config = {
                'proxy': f"{Config.PROXY_TYPE}://{Config.PROXY_IP}:{Config.PROXY_PORT}"
            }
            
            # Add authentication if provided
            if (hasattr(Config, 'PROXY_USER') and 
                hasattr(Config, 'PROXY_PASSWORD') and
                Config.PROXY_USER and 
                Config.PROXY_PASSWORD):
                proxy_config['proxy'] = f"{Config.PROXY_TYPE}://{Config.PROXY_USER}:{Config.PROXY_PASSWORD}@{Config.PROXY_IP}:{Config.PROXY_PORT}"
            
            logger.info(f"Proxy configuration loaded: {Config.PROXY_TYPE}://{Config.PROXY_IP}:{Config.PROXY_PORT}")
            return proxy_config
        else:
            logger.warning("Proxy configuration incomplete or missing")
            return None
    except Exception as e:
        logger.error(f"Error getting proxy configuration: {e}")
        return None

def get_proxy_2_config():
    """
    Return configuration for the second proxy from settings.
    
    Returns:
        dict: Proxy configuration or None if not configured
    """
    try:
        # Ensure all required proxy settings are present
        if (hasattr(Config, 'PROXY_2_TYPE') and 
            hasattr(Config, 'PROXY_2_IP') and 
            hasattr(Config, 'PROXY_2_PORT') and
            Config.PROXY_2_IP and 
            Config.PROXY_2_PORT):
            
            proxy_config = {
                'proxy': f"{Config.PROXY_2_TYPE}://{Config.PROXY_2_IP}:{Config.PROXY_2_PORT}"
            }
            
            # Add authentication if provided
            if (hasattr(Config, 'PROXY_2_USER') and 
                hasattr(Config, 'PROXY_2_PASSWORD') and
                Config.PROXY_2_USER and 
                Config.PROXY_2_PASSWORD):
                proxy_config['proxy'] = f"{Config.PROXY_2_TYPE}://{Config.PROXY_2_USER}:{Config.PROXY_2_PASSWORD}@{Config.PROXY_2_IP}:{Config.PROXY_2_PORT}"
            
            logger.info(f"Proxy 2 configuration loaded: {Config.PROXY_2_TYPE}://{Config.PROXY_2_IP}:{Config.PROXY_2_PORT}")
            return proxy_config
        else:
            logger.warning("Proxy 2 configuration incomplete or missing")
            return None
    except Exception as e:
        logger.error(f"Error getting proxy 2 configuration: {e}")
        return None

def select_proxy_for_domain(url):
    """Select appropriate proxy for domain based on PROXY_DOMAINS and PROXY_2_DOMAINS"""
    try:
        from CONFIG.domains import DomainsConfig
        from HELPERS.proxy_helper import extract_domain_from_url, is_domain_in_list
        
        domain = extract_domain_from_url(url)
        
        # Check PROXY_2_DOMAINS first
        if hasattr(DomainsConfig, 'PROXY_2_DOMAINS') and DomainsConfig.PROXY_2_DOMAINS:
            if is_domain_in_list(domain, DomainsConfig.PROXY_2_DOMAINS):
                return get_proxy_2_config()
        
        # Check PROXY_DOMAINS
        if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
            if is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS):
                return get_proxy_config()
        
        return None
    except Exception as e:
        logger.error(f"Error selecting proxy for domain {url}: {e}")
        return None

def add_proxy_to_ytdl_opts(ytdl_opts, url):
    """
    Add proxy settings to yt-dlp options if the domain requires a proxy.
    
    Args:
        ytdl_opts (dict): yt-dlp options
        url (str): Download URL
        
    Returns:
        dict: Updated yt-dlp options
    """
    if is_proxy_domain(url):
        proxy_config = select_proxy_for_domain(url)
        if proxy_config:
            ytdl_opts.update(proxy_config)
            logger.info(f"Added proxy configuration for URL: {url}")
        else:
            logger.warning(f"Proxy required for {url} but proxy configuration is not available")
    
    return ytdl_opts

def get_direct_link_with_proxy(url: str, format_spec: str = "bv+ba/best", user_id: int = None) -> dict:
    """
    Get direct stream link using proxy
    
    Args:
        url (str): Video URL
        format_spec (str): Format specification for yt-dlp
        user_id (int): User ID for cookies
        
    Returns:
        dict: Dictionary with direct links for different players
    """
    try:
        import yt_dlp
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_spec,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
        }
        
        # Add proxy configuration if enabled for user or domain requires it
        from COMMANDS.proxy_cmd import add_proxy_to_ytdl_opts
        ydl_opts = add_proxy_to_ytdl_opts(ydl_opts, url, user_id)
        
        # Add cookie file for YouTube if user_id is provided
        if user_id:
            import os
            cookie_path = f"users/{user_id}/cookie.txt"
            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path
        
        # Extract video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if not info:
            raise Exception("Failed to extract video information")
            
        # Get the best format URL
        if 'url' in info:
            direct_url = info['url']
        elif 'formats' in info and info['formats']:
            # Get the best format
            best_format = None
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    best_format = fmt
                    break
            if not best_format:
                best_format = info['formats'][0]
            direct_url = best_format['url']
        else:
            raise Exception("No direct URL found")
            
        # Create player-specific URLs
        from urllib.parse import quote, urlparse
        
        # Encode URL for iOS VLC (single encoding)
        encoded_url = quote(direct_url, safe='')
        
        # Parse URL to get host and path for Android intent
        parsed_url = urlparse(direct_url)
        scheme = parsed_url.scheme
        
        # For Android VLC: remove scheme and encode URL properly
        # intent:// expects just host/path without https:// or http://, but needs proper encoding
        android_url_clean = direct_url.replace('https://', '').replace('http://', '')
        android_url_encoded = quote(android_url_clean, safe='')
        
        # For iOS VLC: use encoded URL (prevents issues with special characters)
        # For Android VLC: use intent format with properly encoded URL
        player_urls = {
            'direct': direct_url,
            'vlc_ios': f"https://vlc.ratu.sh/?url=vlc-x-callback://x-callback-url/stream?url={encoded_url}",
            'vlc_android': f"https://vlc.ratu.sh/?url=intent://{android_url_clean}#Intent;scheme={scheme};package=org.videolan.vlc;type=video/*;end"
        }
        
        return {
            'success': True,
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'player_urls': player_urls
        }
        
    except Exception as e:
        logger.error(f"Error getting direct link with proxy: {e}")
        return {
            'success': False,
            'error': str(e)
        }
