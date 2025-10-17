# Ограничитель одновременных операций для предотвращения перегрузки
import asyncio
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class ConcurrentLimiter:
    def __init__(self, max_per_user: int = 2, max_global: int = 50):
        """
        Ограничивает количество одновременных операций загрузки с изоляцией по пользователям
        
        Args:
            max_per_user: Максимальное количество одновременных загрузок на пользователя
            max_global: Максимальное количество одновременных загрузок всего
        """
        self.max_per_user = max_per_user
        self.max_global = max_global
        self.global_semaphore = asyncio.Semaphore(max_global)
        
        # Семафор на каждого пользователя
        self.user_semaphores: Dict[int, asyncio.Semaphore] = {}
        self.user_active: Dict[int, Set[str]] = {}  # user_id -> set of URLs
        self.lock = asyncio.Lock()
    
    async def acquire(self, user_id: int, url: str) -> bool:
        """
        Получает разрешение на загрузку (теперь всегда ждет, не отклоняет)
        
        Args:
            user_id: ID пользователя
            url: URL для загрузки
            
        Returns:
            True (всегда, но может ждать)
        """
        async with self.lock:
            # Создать семафор для пользователя если нет
            if user_id not in self.user_semaphores:
                self.user_semaphores[user_id] = asyncio.Semaphore(self.max_per_user)
                self.user_active[user_id] = set()
        
        # Проверка глобального лимита (логирование)
        if getattr(self.global_semaphore, '_value', 0) == 0:
            logger.warning("Global limit reached (%s), user %s queued", self.max_global, user_id)
        
        # Получить глобальный семафор (будет ждать если нужно)
        await self.global_semaphore.acquire()
        
        # Получить пользовательский семафор (будет ждать если нужно)
        await self.user_semaphores[user_id].acquire()
        
        async with self.lock:
            self.user_active[user_id].add(url)
        
        logger.info("User %s acquired slot for %s", user_id, url)
        return True
    
    async def release(self, user_id: int, url: str = None):
        """
        Освобождает слот загрузки для пользователя
        
        Args:
            user_id: ID пользователя
            url: URL который освобождается (опционально)
        """
        async with self.lock:
            if user_id in self.user_active and url:
                self.user_active[user_id].discard(url)
        
        if user_id in self.user_semaphores:
            self.user_semaphores[user_id].release()
        
        self.global_semaphore.release()
        logger.info("User %s released slot", user_id)
    
    async def get_status(self) -> Dict:
        """
        Возвращает текущий статус ограничителя
        
        Returns:
            Словарь с информацией о текущих загрузках
        """
        async with self.lock:
            total_active = sum(len(tasks) for tasks in self.user_active.values())
            return {
                'active_downloads': total_active,
                'max_global': self.max_global,
                'max_per_user': self.max_per_user,
                'available_global_slots': getattr(self.global_semaphore, '_value', 0),
                'users': list(self.user_active.keys()),
                'user_details': {
                    user_id: {
                        'active_tasks': len(tasks),
                        'max_tasks': self.max_per_user
                    } for user_id, tasks in self.user_active.items()
                }
            }

# Global limiter instance (configuration from limits.py)
from CONFIG.limits import LimitsConfig

concurrent_limiter = ConcurrentLimiter(
    max_per_user=LimitsConfig.MAX_DOWNLOADS_PER_USER,
    max_global=LimitsConfig.MAX_CONCURRENT_GLOBAL
)
