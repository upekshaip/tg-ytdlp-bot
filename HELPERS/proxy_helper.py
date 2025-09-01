import yt_dlp
import logging
import os
from urllib.parse import quote
from COMMANDS.proxy_cmd import get_proxy_config

logger = logging.getLogger(__name__)

def get_direct_link_with_proxy(url: str, format_spec: str = "bv+ba/best", user_id: int = None) -> dict:
    """
    Get direct stream link using proxy
    
    Args:
        url (str): Video URL
        format_spec (str): Format specification for yt-dlp
        
    Returns:
        dict: Dictionary with direct links for different players
    """
    try:
        # Get proxy configuration
        proxy_config = get_proxy_config()
        
        # Configure yt-dlp options with proxy
        ydl_opts = {
            'format': format_spec,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
        }
        
        # Add proxy configuration
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
                if proxy_config.get('user') and proxy_config.get('password'):
                    proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                else:
                    proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
            
            ydl_opts['proxy'] = proxy_url
            logger.info(f"Using proxy for yt-dlp: {proxy_url}")
        else:
            logger.warning("Proxy configuration incomplete, using direct connection")
        
        # Add cookie file for YouTube if user_id is provided
        #if user_id and 'youtube.com' in url or 'youtu.be' in url:
        if user_id:
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
        encoded_url = quote(direct_url, safe='')
        
        # Parse URL to get host and path for Android intent
        from urllib.parse import urlparse
        parsed_url = urlparse(direct_url)
        scheme = parsed_url.scheme
        host_path = f"{parsed_url.netloc}{parsed_url.path}"
        if parsed_url.query:
            host_path += f"?{parsed_url.query}"
        if parsed_url.fragment:
            host_path += f"#{parsed_url.fragment}"
        
        player_urls = {
            'direct': direct_url,
            'vlc_ios': f"vlc-x-callback://x-callback-url/stream?url={encoded_url}",
            'vlc_android': f"intent://{host_path}#Intent;scheme={scheme};package=org.videolan.vlc;type=video/*;end"
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

def add_proxy_to_ytdl_opts(ytdl_opts: dict, url: str, user_id: int = None) -> dict:
    """Add proxy to yt-dlp options if proxy is enabled for user or domain requires it"""
    # Direct implementation to avoid circular imports
    from CONFIG.domains import DomainsConfig
    
    # Check if user has proxy enabled
    if user_id:
        try:
            from COMMANDS.proxy_cmd import is_proxy_enabled
            if is_proxy_enabled(user_id):
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
                    logger.info(f"Added proxy for user {user_id}: {proxy_url}")
                    return ytdl_opts
        except Exception as e:
            logger.warning(f"Error checking proxy for user {user_id}: {e}")
            pass
    
    # Fallback: check if domain requires proxy (PROXY_DOMAINS logic)
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        domain = None
        if '://' in url:
            domain = url.split('://')[1].split('/')[0]
        else:
            domain = url.split('/')[0]
        
        if domain in DomainsConfig.PROXY_DOMAINS:
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
                logger.info(f"Added proxy for domain {domain}: {proxy_url}")
    
    return ytdl_opts

def is_proxy_domain(url: str) -> bool:
    """Check if the domain is in PROXY_DOMAINS"""
    from CONFIG.domains import DomainsConfig
    
    if not hasattr(DomainsConfig, 'PROXY_DOMAINS') or not DomainsConfig.PROXY_DOMAINS:
        return False
    
    # Extract domain from URL
    domain = None
    if '://' in url:
        domain = url.split('://')[1].split('/')[0]
    else:
        domain = url.split('/')[0]
    
    return domain in DomainsConfig.PROXY_DOMAINS

def get_proxy_config():
    """Get proxy configuration from config"""
    from CONFIG.config import Config
    
    return {
        'type': Config.PROXY_TYPE,
        'ip': Config.PROXY_IP,
        'port': Config.PROXY_PORT,
        'user': Config.PROXY_USER,
        'password': Config.PROXY_PASSWORD
    }
