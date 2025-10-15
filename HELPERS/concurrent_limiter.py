# Ограничитель одновременных операций для предотвращения перегрузки
import asyncio
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class ConcurrentLimiter:
    def __init__(self, max_concurrent: int = 3):
        """
        Ограничивает количество одновременных операций загрузки
        
        Args:
            max_concurrent: Максимальное количество одновременных загрузок
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_downloads: Dict[int, str] = {}  # user_id -> url
        self.lock = asyncio.Lock()
    
    async def acquire(self, user_id: int, url: str) -> bool:
        """
        Пытается получить разрешение на загрузку
        
        Args:
            user_id: ID пользователя
            url: URL для загрузки
            
        Returns:
            True если разрешение получено, False если превышен лимит
        """
        async with self.lock:
            # Проверяем, не загружает ли уже этот пользователь что-то
            if user_id in self.active_downloads:
                logger.warning(f"User {user_id} already has an active download: {self.active_downloads[user_id]}")
                return False
            
            # Проверяем общий лимит
            if len(self.active_downloads) >= self.max_concurrent:
                logger.warning(f"Max concurrent downloads reached ({self.max_concurrent}), rejecting user {user_id}")
                return False
            
            # Получаем семафор
            await self.semaphore.acquire()
            self.active_downloads[user_id] = url
            logger.info(f"Download slot acquired for user {user_id}, active downloads: {len(self.active_downloads)}")
            return True
    
    async def release(self, user_id: int):
        """
        Освобождает слот загрузки для пользователя
        
        Args:
            user_id: ID пользователя
        """
        async with self.lock:
            if user_id in self.active_downloads:
                url = self.active_downloads.pop(user_id)
                self.semaphore.release()
                logger.info(f"Download slot released for user {user_id} (was downloading: {url}), active downloads: {len(self.active_downloads)}")
            else:
                logger.warning(f"Attempted to release slot for user {user_id} who has no active download")
    
    async def get_status(self) -> Dict:
        """
        Возвращает текущий статус ограничителя
        
        Returns:
            Словарь с информацией о текущих загрузках
        """
        async with self.lock:
            return {
                'active_downloads': len(self.active_downloads),
                'max_concurrent': self.max_concurrent,
                'available_slots': self.max_concurrent - len(self.active_downloads),
                'users': list(self.active_downloads.keys())
            }

# Глобальный экземпляр ограничителя
# Можно настроить количество одновременных загрузок
concurrent_limiter = ConcurrentLimiter(max_concurrent=3)  # Максимум 3 одновременные загрузки
