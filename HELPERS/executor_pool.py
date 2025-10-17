# Изолированные пулы потоков для предотвращения блокировок между пользователями
import concurrent.futures
import asyncio
import logging
from typing import Dict, Set
import threading
import time

logger = logging.getLogger(__name__)

class UserIsolatedExecutorPool:
    def __init__(self, max_workers_per_user: int = 2, max_global_workers: int = 100):
        """
        Создает изолированные пулы потоков для каждого пользователя
        
        Args:
            max_workers_per_user: Максимум потоков на пользователя
            max_global_workers: Максимум потоков всего
        """
        # Глобальный пул для тяжелых операций
        self.global_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_global_workers,
            thread_name_prefix='bot_global'
        )
        
        # Пулы на пользователя для изоляции
        self.user_executors: Dict[int, concurrent.futures.ThreadPoolExecutor] = {}
        self.user_active_tasks: Dict[int, Set[str]] = {}  # user_id -> set of task_ids
        self.max_workers_per_user = max_workers_per_user
        self.lock = asyncio.Lock()
        self.shutdown_event = threading.Event()
        
        logger.info("Initialized executor pool: global=%s, per_user=%s", max_global_workers, max_workers_per_user)
    
    async def get_user_executor(self, user_id: int) -> concurrent.futures.ThreadPoolExecutor:
        """Получить или создать executor для пользователя"""
        async with self.lock:
            if user_id not in self.user_executors:
                self.user_executors[user_id] = concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.max_workers_per_user,
                    thread_name_prefix=f'user_{user_id}'
                )
                self.user_active_tasks[user_id] = set()
                logger.info("Created isolated executor for user %s", user_id)
            return self.user_executors[user_id]
    
    async def submit_to_user(self, user_id: int, func, *args, **kwargs):
        """Отправить задачу в пул пользователя"""
        if self.shutdown_event.is_set():
            raise RuntimeError("Executor pool is shutting down")
            
        executor = await self.get_user_executor(user_id)
        loop = asyncio.get_event_loop()
        
        # Генерируем уникальный ID задачи
        task_id = f"{user_id}_{int(time.time() * 1000)}"
        
        async with self.lock:
            self.user_active_tasks[user_id].add(task_id)
        
        try:
            result = await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
            return result
        finally:
            async with self.lock:
                self.user_active_tasks[user_id].discard(task_id)
                if not self.user_active_tasks[user_id] and user_id in self.user_executors:
                    # Если у пользователя нет активных задач, можно освободить ресурсы
                    pass
    
    async def submit_to_global(self, func, *args, **kwargs):
        """Отправить задачу в глобальный пул"""
        if self.shutdown_event.is_set():
            raise RuntimeError("Executor pool is shutting down")
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.global_executor, lambda: func(*args, **kwargs))
    
    async def get_user_status(self, user_id: int) -> Dict:
        """Получить статус пользователя"""
        async with self.lock:
            active_tasks = len(self.user_active_tasks.get(user_id, set()))
            return {
                'user_id': user_id,
                'active_tasks': active_tasks,
                'max_tasks': self.max_workers_per_user,
                'has_executor': user_id in self.user_executors
            }
    
    async def get_global_status(self) -> Dict:
        """Получить глобальный статус"""
        async with self.lock:
            total_users = len(self.user_executors)
            total_active = sum(len(tasks) for tasks in self.user_active_tasks.values())
            return {
                'total_users': total_users,
                'total_active_tasks': total_active,
                'max_global_workers': getattr(self.global_executor, '_max_workers', 100),
                'users': list(self.user_executors.keys())
            }
    
    def shutdown(self, wait=True):
        """Завершить работу всех пулов"""
        logger.info("Shutting down all executor pools...")
        self.shutdown_event.set()
        
        # Завершаем глобальный пул
        self.global_executor.shutdown(wait=wait)
        
        # Завершаем пользовательские пулы
        for user_id, executor in self.user_executors.items():
            executor.shutdown(wait=wait)
            logger.info("Shutdown executor for user %s", user_id)
        
        logger.info("All executor pools shutdown completed")

# Global instance (configuration from limits.py)
from CONFIG.limits import LimitsConfig

executor_pool = UserIsolatedExecutorPool(
    max_workers_per_user=1,   # 1 thread per user (for resource efficiency)
    max_global_workers=LimitsConfig.MAX_GLOBAL_WORKERS
)
