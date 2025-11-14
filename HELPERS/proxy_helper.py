import yt_dlp
import logging
import os
from urllib.parse import quote
from COMMANDS.proxy_cmd import get_proxy_config
from CONFIG.messages import Messages, safe_get_messages

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
            messages = safe_get_messages(user_id)
            logger.warning(messages.HELPER_PROXY_CONFIG_INCOMPLETE_MSG)
        
        # Add cookie file for YouTube if user_id is provided
        #if user_id and 'youtube.com' in url or 'youtu.be' in url:
        if user_id:
            messages = safe_get_messages(user_id)
            cookie_path = messages.HELPER_PROXY_COOKIE_PATH_MSG.format(user_id=user_id)
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

def build_proxy_url(proxy_config):
    """Build proxy URL from configuration"""
    if not proxy_config or 'type' not in proxy_config or 'ip' not in proxy_config or 'port' not in proxy_config:
        return None
    
    if proxy_config['type'] == 'http':
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"http://{proxy_config['ip']}:{proxy_config['port']}"
    elif proxy_config['type'] == 'https':
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"https://{proxy_config['ip']}:{proxy_config['port']}"
    elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
    else:
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"http://{proxy_config['ip']}:{proxy_config['port']}"

def add_proxy_to_ytdl_opts(ytdl_opts: dict, url: str, user_id: int = None) -> dict:
    """Add proxy to yt-dlp options if proxy is enabled for user or domain requires it"""
    logger.info(f"add_proxy_to_ytdl_opts called: user_id={user_id}, url={url}")
    
    # ГЛОБАЛЬНАЯ ЗАЩИТА: Инициализируем messages
    messages = safe_get_messages(user_id)
    
    # Priority 1: Check if user has proxy enabled (/proxy on)
    if user_id:
        try:
            from COMMANDS.proxy_cmd import is_proxy_enabled
            proxy_enabled = is_proxy_enabled(user_id)
            logger.info(f"User {user_id} proxy enabled: {proxy_enabled}")
            if proxy_enabled:
                # Use round-robin/random selection for user proxy
                proxy_config = select_proxy_for_user()
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        ytdl_opts['proxy'] = proxy_url
                        logger.info(f"Added user proxy for {user_id}: {proxy_url}")
                        return ytdl_opts
        except Exception as e:
            logger.warning(f"Error checking proxy for user {user_id}: {e}")
            pass
    
    # Priority 2: Check if domain requires specific proxy (only if user proxy is OFF)
    logger.info(f"Checking domain-specific proxy for {url}")
    proxy_config = select_proxy_for_domain(url)
    if proxy_config:
        proxy_url = build_proxy_url(proxy_config)
        if proxy_url:
            ytdl_opts['proxy'] = proxy_url
            logger.info(f"Added domain-specific proxy for {url}: {proxy_url}")
        else:
            logger.warning(f"Failed to build proxy URL from config: {proxy_config}")
    else:
        logger.info(f"No domain-specific proxy found for {url}")
    
    return ytdl_opts

def try_with_proxy_fallback(ytdl_opts: dict, url: str, user_id: int = None, operation_func=None, *args, **kwargs):
    """
    Try operation with different proxies in case of failure when user proxy is enabled
    
    Args:
        ytdl_opts: yt-dlp options
        url: URL to process
        user_id: User ID
        operation_func: Function to call with ytdl_opts
        *args, **kwargs: Additional arguments for operation_func
    
    Returns:
        Result of operation_func or None if all proxies failed
    """
    messages = safe_get_messages(user_id)
    if not operation_func:
        return None
    
    # Check if user has proxy enabled
    if not user_id:
        # No user ID, try without proxy fallback
        return operation_func(ytdl_opts, *args, **kwargs)
    
    try:
        from COMMANDS.proxy_cmd import is_proxy_enabled
        proxy_enabled = is_proxy_enabled(user_id)
        if not proxy_enabled:
            # User proxy is disabled, try without proxy fallback
            return operation_func(ytdl_opts, *args, **kwargs)
    except Exception as e:
        logger.warning(f"Error checking proxy for user {user_id}: {e}")
        return operation_func(ytdl_opts, *args, **kwargs)
    
    # User proxy is enabled, get all available proxies
    all_configs = get_all_proxy_configs()
    if not all_configs:
        logger.info(f"No proxies available for {url}, trying without proxy")
        return operation_func(ytdl_opts, *args, **kwargs)
    
    # Try with each proxy
    for i, proxy_config in enumerate(all_configs):
        try:
            # Update proxy in options
            current_opts = ytdl_opts.copy()
            proxy_url = build_proxy_url(proxy_config)
            if proxy_url:
                current_opts['proxy'] = proxy_url
                logger.info(f"Trying {url} with proxy {i+1}/{len(all_configs)}: {proxy_url}")
                result = operation_func(current_opts, *args, **kwargs)
                
                if result is not None:
                    logger.info(f"Success with proxy {i+1}/{len(all_configs)}: {proxy_url}")
                    return result
                else:
                    logger.warning(f"Operation returned None with proxy {i+1}/{len(all_configs)}: {proxy_url}")
            else:
                logger.warning(f"Failed to build proxy URL for config {i+1}/{len(all_configs)}: {proxy_config}")
                
        except Exception as e:
            logger.warning(f"Failed with proxy {i+1}/{len(all_configs)} ({proxy_url}): {e}")
            continue
    
    # Try without proxy as last resort
    try:
        logger.info(f"All proxies failed for {url}, trying without proxy")
        current_opts = ytdl_opts.copy()
        if 'proxy' in current_opts:
            del current_opts['proxy']
        return operation_func(current_opts, *args, **kwargs)
    except Exception as e:
        logger.error(f"Failed without proxy for {url}: {e}")
        return None

def is_proxy_domain(url: str) -> bool:
    """Check if the domain is in PROXY_DOMAINS or PROXY_2_DOMAINS"""
    from CONFIG.domains import DomainsConfig
    
    domain = extract_domain_from_url(url)
    
    # Check PROXY_DOMAINS
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS):
            return True
    
    # Check PROXY_2_DOMAINS
    if hasattr(DomainsConfig, 'PROXY_2_DOMAINS') and DomainsConfig.PROXY_2_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_2_DOMAINS):
            return True
    
    return False

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

def get_proxy_2_config():
    """Get second proxy configuration from config"""
    from CONFIG.config import Config
    
    return {
        'type': Config.PROXY_2_TYPE,
        'ip': Config.PROXY_2_IP,
        'port': Config.PROXY_2_PORT,
        'user': Config.PROXY_2_USER,
        'password': Config.PROXY_2_PASSWORD
    }

def get_all_proxy_configs():
    """Get all available proxy configurations"""
    from CONFIG.config import Config
    
    configs = []
    
    # First proxy
    if hasattr(Config, 'PROXY_TYPE') and hasattr(Config, 'PROXY_IP') and hasattr(Config, 'PROXY_PORT'):
        if Config.PROXY_IP and Config.PROXY_PORT:
            configs.append({
                'type': Config.PROXY_TYPE,
                'ip': Config.PROXY_IP,
                'port': Config.PROXY_PORT,
                'user': Config.PROXY_USER,
                'password': Config.PROXY_PASSWORD
            })
    
    # Second proxy
    if hasattr(Config, 'PROXY_2_TYPE') and hasattr(Config, 'PROXY_2_IP') and hasattr(Config, 'PROXY_2_PORT'):
        if Config.PROXY_2_IP and Config.PROXY_2_PORT:
            configs.append({
                'type': Config.PROXY_2_TYPE,
                'ip': Config.PROXY_2_IP,
                'port': Config.PROXY_2_PORT,
                'user': Config.PROXY_2_USER,
                'password': Config.PROXY_2_PASSWORD
            })
    
    return configs

def extract_domain_from_url(url):
    """Extract domain from URL, handling subdomains properly"""
    if '://' in url:
        domain = url.split('://')[1].split('/')[0]
    else:
        domain = url.split('/')[0]
    
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

def is_domain_in_list(domain, domain_list):
    """Check if domain or any of its subdomains match entries in domain_list"""
    if not domain_list:
        return False
    
    # Direct match
    if domain in domain_list:
        return True
    
    # Check if any domain in the list is a subdomain of the current domain
    for listed_domain in domain_list:
        if domain.endswith('.' + listed_domain):
            return True
    
    return False

def select_proxy_for_domain(url):
    """Select appropriate proxy for domain based on PROXY_DOMAINS and PROXY_2_DOMAINS"""
    from CONFIG.domains import DomainsConfig
    
    domain = extract_domain_from_url(url)
    
    logger.info(f"select_proxy_for_domain: URL={url}, extracted_domain={domain}")
    logger.info(f"PROXY_2_DOMAINS: {getattr(DomainsConfig, 'PROXY_2_DOMAINS', 'NOT_FOUND')}")
    logger.info(f"PROXY_DOMAINS: {getattr(DomainsConfig, 'PROXY_DOMAINS', 'NOT_FOUND')}")
    
    # Check PROXY_2_DOMAINS first
    if hasattr(DomainsConfig, 'PROXY_2_DOMAINS') and DomainsConfig.PROXY_2_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_2_DOMAINS):
            logger.info(f"Domain {domain} found in PROXY_2_DOMAINS, using proxy 2")
            return get_proxy_2_config()
    
    # Check PROXY_DOMAINS
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS):
            logger.info(f"Domain {domain} found in PROXY_DOMAINS, using proxy 1")
            return get_proxy_config()
    
    logger.info(f"Domain {domain} not found in any proxy domain lists")
    return None

def select_proxy_for_user():
    """Select proxy for user based on PROXY_SELECT method"""
    from CONFIG.config import Config
    import random
    
    configs = get_all_proxy_configs()
    if not configs:
        return None
    
    if len(configs) == 1:
        return configs[0]
    
    # Select method based on PROXY_SELECT
    if hasattr(Config, 'PROXY_SELECT') and Config.PROXY_SELECT == "random":
        return random.choice(configs)
    else:  # default to round_robin
        # Simple round-robin using a global counter
        if not hasattr(select_proxy_for_user, 'counter'):
            select_proxy_for_user.counter = 0
        selected = configs[select_proxy_for_user.counter % len(configs)]
        select_proxy_for_user.counter += 1
        return selected

def add_proxy_to_gallery_dl_config(config: dict, url: str, user_id: int = None) -> dict:
    """Add proxy to gallery-dl config if proxy is enabled for user or domain requires it"""
    logger.info(f"add_proxy_to_gallery_dl_config called: user_id={user_id}, url={url}")
    
    # Priority 1: Check if user has proxy enabled (/proxy on)
    if user_id:
        try:
            from COMMANDS.proxy_cmd import is_proxy_enabled
            proxy_enabled = is_proxy_enabled(user_id)
            logger.info(f"User {user_id} proxy enabled: {proxy_enabled}")
            if proxy_enabled:
                # Use round-robin/random selection for user proxy
                proxy_config = select_proxy_for_user()
                if proxy_config:
                    proxy_url = build_proxy_url(proxy_config)
                    if proxy_url:
                        config['extractor']['proxy'] = proxy_url
                        logger.info(f"Added user proxy for {user_id}: {proxy_url}")
                        return config
        except Exception as e:
            logger.warning(f"Error checking proxy for user {user_id}: {e}")
            pass
    
    # Priority 2: Check if domain requires specific proxy (only if user proxy is OFF)
    logger.info(f"Checking domain-specific proxy for {url}")
    proxy_config = select_proxy_for_domain(url)
    if proxy_config:
        proxy_url = build_proxy_url(proxy_config)
        if proxy_url:
            config['extractor']['proxy'] = proxy_url
            logger.info(f"Added domain-specific proxy for {url}: {proxy_url}")
        else:
            logger.warning(f"Failed to build proxy URL from config: {proxy_config}")
    else:
        logger.info(f"No domain-specific proxy found for {url}")
    
    return config
