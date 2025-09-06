# PO Token Helper for YouTube
# Adds PO token provider support for YouTube domains

import requests
import time
from CONFIG.config import Config
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.logger import logger

# Кэш для проверки доступности PO token провайдера
_pot_provider_cache = {
    'available': None,
    'last_check': 0,
    'check_interval': 30  # Проверяем каждые 30 секунд
}

def check_pot_provider_availability(base_url: str) -> bool:
    """
    Проверяет доступность PO token провайдера
    
    Args:
        base_url (str): URL провайдера
        
    Returns:
        bool: True если провайдер доступен, False иначе
    """
    current_time = time.time()
    
    # Проверяем кэш
    if (_pot_provider_cache['available'] is not None and 
        current_time - _pot_provider_cache['last_check'] < _pot_provider_cache['check_interval']):
        return _pot_provider_cache['available']
    
    try:
        # Быстрая проверка доступности провайдера
        response = requests.get(base_url, timeout=5)
        is_available = response.status_code == 200
        
        # Обновляем кэш
        _pot_provider_cache['available'] = is_available
        _pot_provider_cache['last_check'] = current_time
        
        if is_available:
            logger.info(f"PO token provider is available at {base_url}")
        else:
            logger.warning(f"PO token provider returned status {response.status_code} at {base_url}")
        
        return is_available
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"PO token provider is not available at {base_url}: {e}")
        
        # Обновляем кэш
        _pot_provider_cache['available'] = False
        _pot_provider_cache['last_check'] = current_time
        
        return False

def add_pot_to_ytdl_opts(ytdl_opts: dict, url: str) -> dict:
    """
    Добавляет PO token аргументы к yt-dlp опциям для YouTube доменов
    
    Args:
        ytdl_opts (dict): Словарь опций yt-dlp
        url (str): URL для проверки
        
    Returns:
        dict: Обновленный словарь опций yt-dlp
    """
    # Проверяем, включен ли PO token провайдер
    if not getattr(Config, 'YOUTUBE_POT_ENABLED', False):
        logger.info("PO token provider disabled in config")
        return ytdl_opts
    
    # Проверяем, является ли URL YouTube доменом
    if not is_youtube_url(url):
        logger.info(f"URL {url} is not a YouTube domain, skipping PO token")
        return ytdl_opts
    
    # Получаем базовый URL провайдера
    base_url = getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')
    disable_innertube = getattr(Config, 'YOUTUBE_POT_DISABLE_INNERTUBE', False)
    
    # Проверяем доступность PO token провайдера
    if not check_pot_provider_availability(base_url):
        logger.warning(f"PO token provider is not available at {base_url}, falling back to standard YouTube extraction")
        return ytdl_opts
    
    # Добавляем extractor_args к опциям yt-dlp
    if 'extractor_args' not in ytdl_opts:
        ytdl_opts['extractor_args'] = {}
    
    # Добавляем аргументы для YouTube PO token провайдера в правильном формате
    # Для Python API: словарь -> словарь -> список строк
    ytdl_opts['extractor_args']['youtubepot-bgutilhttp'] = {
        'base_url': [base_url]
    }
    
    # Добавляем disable_innertube только если включен (строка "1" в списке)
    if disable_innertube:
        ytdl_opts['extractor_args']['youtubepot-bgutilhttp']['disable_innertube'] = ["1"]
    
    logger.info(f"Added PO token provider for YouTube URL: {url} with base_url: {base_url}")
    
    return ytdl_opts

def is_pot_enabled() -> bool:
    """
    Проверяет, включен ли PO token провайдер в конфигурации
    
    Returns:
        bool: True если включен, False иначе
    """
    return getattr(Config, 'YOUTUBE_POT_ENABLED', False)

def get_pot_base_url() -> str:
    """
    Возвращает базовый URL PO token провайдера
    
    Returns:
        str: Базовый URL провайдера
    """
    return getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')

def clear_pot_provider_cache():
    """
    Сбрасывает кэш проверки доступности PO token провайдера
    Полезно для принудительной повторной проверки после восстановления провайдера
    """
    global _pot_provider_cache
    _pot_provider_cache['available'] = None
    _pot_provider_cache['last_check'] = 0
    logger.info("PO token provider cache cleared, will check availability on next request")

def is_pot_provider_available() -> bool:
    """
    Проверяет, доступен ли PO token провайдер (с учетом кэша)
    
    Returns:
        bool: True если провайдер доступен, False иначе
    """
    base_url = getattr(Config, 'YOUTUBE_POT_BASE_URL', 'http://127.0.0.1:4416')
    return check_pot_provider_availability(base_url)
