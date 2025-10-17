# Асинхронные обертки для yt-dlp операций
# Этот модуль обеспечивает неблокирующее выполнение yt-dlp операций

import yt_dlp
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Импортируем enterprise scaler для масштабирования до 10000+ пользователей
from HELPERS.enterprise_scaler import enterprise_scaler

async def async_extract_info(ydl_opts: Dict[str, Any], url: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Асинхронно извлекает информацию о видео/аудио без блокировки event loop
    """
    def sync_extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    try:
        return await enterprise_scaler.submit_user_task(user_id, sync_extract_info)
    except Exception as e:
        logger.error("Error in async_extract_info: %s", e)
        raise

async def async_download(ydl_opts: Dict[str, Any], urls: List[str], user_id: int) -> bool:
    """
    Асинхронно загружает видео/аудио без блокировки event loop
    """
    def sync_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        return True
    
    try:
        return await enterprise_scaler.submit_user_task(user_id, sync_download)
    except Exception as e:
        logger.error("Error in async_download: %s", e)
        raise

async def async_extract_info_with_progress(ydl_opts: Dict[str, Any], url: str, user_id: int, progress_callback=None) -> Optional[Dict[str, Any]]:
    """
    Асинхронно извлекает информацию с возможностью отслеживания прогресса
    """
    def sync_extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if progress_callback:
                ydl.add_progress_hook(progress_callback)
            return ydl.extract_info(url, download=False)
    
    try:
        return await enterprise_scaler.submit_user_task(user_id, sync_extract_info)
    except Exception as e:
        logger.error("Error in async_extract_info_with_progress: %s", e)
        raise

async def async_download_with_progress(ydl_opts: Dict[str, Any], urls: List[str], user_id: int, progress_callback=None) -> bool:
    """
    Асинхронно загружает с возможностью отслеживания прогресса
    """
    def sync_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if progress_callback:
                ydl.add_progress_hook(progress_callback)
            ydl.download(urls)
        return True
    
    try:
        return await enterprise_scaler.submit_user_task(user_id, sync_download)
    except Exception as e:
        logger.error("Error in async_download_with_progress: %s", e)
        raise
