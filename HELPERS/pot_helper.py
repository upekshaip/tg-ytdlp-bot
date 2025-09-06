# PO Token Helper for YouTube
# Adds PO token provider support for YouTube domains

from CONFIG.config import Config
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.logger import logger

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
    
    # Формируем аргументы для экстрактора
    extractor_args = f"youtubepot-bgutilhttp:base_url={base_url}"
    
    if disable_innertube:
        extractor_args += ";disable_innertube=1"
    
    # Добавляем extractor_args к опциям yt-dlp
    if 'extractor_args' not in ytdl_opts:
        ytdl_opts['extractor_args'] = {}
    
    # Добавляем аргументы для YouTube PO token провайдера
    ytdl_opts['extractor_args']['youtubepot-bgutilhttp'] = {
        'base_url': base_url,
        'disable_innertube': disable_innertube
    }
    
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
