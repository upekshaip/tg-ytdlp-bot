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
    # Health monitoring
    try:
        from HELPERS.health_monitor import health_monitor
        task_name = f"extract_info_{user_id}_{url[:50]}"
        health_monitor.start_task(task_name)
    except Exception:
        pass
    
    def sync_extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    try:
        # Add timeout to prevent hanging
        import asyncio
        result = await asyncio.wait_for(
            enterprise_scaler.submit_user_task(user_id, sync_extract_info),
            timeout=300  # 5 minutes timeout
        )
        
        # Mark task as completed
        try:
            health_monitor.end_task(task_name)
        except Exception:
            pass
        
        return result
    except asyncio.TimeoutError:
        logger.error("async_extract_info timeout for user %s, url: %s", user_id, url)
        try:
            health_monitor.mark_hanging_task(task_name)
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error("Error in async_extract_info: %s", e)
        try:
            health_monitor.end_task(task_name)
        except Exception:
            pass
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
        # Add timeout to prevent hanging
        import asyncio
        return await asyncio.wait_for(
            enterprise_scaler.submit_user_task(user_id, sync_download),
            timeout=1800  # 30 minutes timeout for downloads
        )
    except asyncio.TimeoutError:
        logger.error("async_download timeout for user %s, urls: %s", user_id, urls)
        raise
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
        # Add timeout to prevent hanging
        import asyncio
        return await asyncio.wait_for(
            enterprise_scaler.submit_user_task(user_id, sync_extract_info),
            timeout=300  # 5 minutes timeout
        )
    except asyncio.TimeoutError:
        logger.error("async_extract_info_with_progress timeout for user %s, url: %s", user_id, url)
        raise
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
        # Add timeout to prevent hanging
        import asyncio
        return await asyncio.wait_for(
            enterprise_scaler.submit_user_task(user_id, sync_download),
            timeout=1800  # 30 minutes timeout for downloads
        )
    except asyncio.TimeoutError:
        logger.error("async_download_with_progress timeout for user %s, urls: %s", user_id, urls)
        raise
    except Exception as e:
        logger.error("Error in async_download_with_progress: %s", e)
        raise
