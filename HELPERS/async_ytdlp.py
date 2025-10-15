# Асинхронные обертки для yt-dlp операций
# Этот модуль обеспечивает неблокирующее выполнение yt-dlp операций

import asyncio
import yt_dlp
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

async def async_extract_info(ydl_opts: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
    """
    Асинхронно извлекает информацию о видео/аудио без блокировки event loop
    """
    def sync_extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_extract_info)
    except Exception as e:
        logger.error(f"Error in async_extract_info: {e}")
        raise

async def async_download(ydl_opts: Dict[str, Any], urls: List[str]) -> bool:
    """
    Асинхронно загружает видео/аудио без блокировки event loop
    """
    def sync_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        return True
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_download)
    except Exception as e:
        logger.error(f"Error in async_download: {e}")
        raise

async def async_extract_info_with_progress(ydl_opts: Dict[str, Any], url: str, progress_callback=None) -> Optional[Dict[str, Any]]:
    """
    Асинхронно извлекает информацию с возможностью отслеживания прогресса
    """
    def sync_extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if progress_callback:
                ydl.add_progress_hook(progress_callback)
            return ydl.extract_info(url, download=False)
    
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_extract_info)
    except Exception as e:
        logger.error(f"Error in async_extract_info_with_progress: {e}")
        raise

async def async_download_with_progress(ydl_opts: Dict[str, Any], urls: List[str], progress_callback=None) -> bool:
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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_download)
    except Exception as e:
        logger.error(f"Error in async_download_with_progress: {e}")
        raise
