import re
from urllib.parse import urlparse
from CONFIG.config import Config
from HELPERS.logger import logger

def is_proxy_domain(url):
    """
    Проверяет, нужно ли использовать прокси для данного URL.
    
    Args:
        url (str): URL для проверки
        
    Returns:
        bool: True если домен находится в списке PROXY_DOMAINS
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Убираем www. если есть
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Проверяем точное совпадение домена
        if domain in Config.PROXY_DOMAINS:
            logger.info(f"Domain {domain} found in PROXY_DOMAINS list")
            return True
            
        # Проверяем поддомены
        for proxy_domain in Config.PROXY_DOMAINS:
            if domain.endswith('.' + proxy_domain) or domain == proxy_domain:
                logger.info(f"Domain {domain} matches proxy domain {proxy_domain}")
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking proxy domain for {url}: {e}")
        return False

def get_proxy_config():
    """
    Возвращает конфигурацию прокси из настроек.
    
    Returns:
        dict: Конфигурация прокси или None если прокси не настроен
    """
    try:
        # Проверяем, что все необходимые параметры прокси настроены
        if (hasattr(Config, 'PROXY_TYPE') and 
            hasattr(Config, 'PROXY_IP') and 
            hasattr(Config, 'PROXY_PORT') and
            Config.PROXY_IP and 
            Config.PROXY_PORT):
            
            proxy_config = {
                'proxy': f"{Config.PROXY_TYPE}://{Config.PROXY_IP}:{Config.PROXY_PORT}"
            }
            
            # Добавляем аутентификацию если указана
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

def add_proxy_to_ytdl_opts(ytdl_opts, url):
    """
    Добавляет настройки прокси к опциям yt-dlp если домен требует прокси.
    
    Args:
        ytdl_opts (dict): Опции yt-dlp
        url (str): URL для скачивания
        
    Returns:
        dict: Обновленные опции yt-dlp
    """
    if is_proxy_domain(url):
        proxy_config = get_proxy_config()
        if proxy_config:
            ytdl_opts.update(proxy_config)
            logger.info(f"Added proxy configuration for URL: {url}")
        else:
            logger.warning(f"Proxy required for {url} but proxy configuration is not available")
    
    return ytdl_opts
