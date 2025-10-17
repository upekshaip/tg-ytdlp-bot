# Гибридный executor: асинхронность + изоляция процессов для 2000+ пользователей
import asyncio
import concurrent.futures
import multiprocessing
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
import os
import signal

logger = logging.getLogger(__name__)

class HybridExecutor:
    def __init__(self, max_processes: int = 100, max_threads_per_process: int = 100):
        """
        Гибридный executor для масштабирования до 10000+ пользователей
        
        Args:
            max_processes: Количество процессов (100 процессов)
            max_threads_per_process: Потоков на процесс (100 потоков)
        """
        self.max_processes = max_processes
        self.max_threads_per_process = max_threads_per_process
        
        # Процессный пул для изоляции (100 процессов = 10000 пользователей)
        self.process_pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=max_processes,
            mp_context=multiprocessing.get_context('spawn')  # Безопасный контекст
        )
        
        # Потоковые пулы внутри процессов
        self.thread_pools: Dict[int, concurrent.futures.ThreadPoolExecutor] = {}
        self.lock = threading.Lock()
        
        logger.info("Initialized hybrid executor: %s processes, %s threads per process", 
                   max_processes, max_threads_per_process)
    
    def get_process_id_for_user(self, user_id: int) -> int:
        """Получить ID процесса для пользователя"""
        return user_id % self.max_processes
    
    async def submit_user_task(self, user_id: int, func: Callable, *args, **kwargs):
        """
        Отправить задачу пользователя в изолированный процесс
        """
        process_id = self.get_process_id_for_user(user_id)
        
        def process_wrapper():
            """Обертка для выполнения в процессе"""
            try:
                # Инициализация в процессе
                import sys
                import os
                
                # Добавляем путь к проекту
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                # Выполняем функцию
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                logger.error("Process error for user %s: %s", user_id, e)
                raise
        
        # Отправляем в процесс
        future = asyncio.get_event_loop().run_in_executor(
            self.process_pool, 
            process_wrapper
        )
        
        return await future
    
    async def submit_light_task(self, func: Callable, *args, **kwargs):
        """
        Отправить легкую задачу в потоковый пул (для быстрых операций)
        """
        # Используем дефолтный ThreadPoolExecutor для легких задач
        return await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)
    
    def get_status(self) -> Dict:
        """Получить статус executor'а"""
        with self.lock:
            return {
                'max_processes': self.max_processes,
                'max_threads_per_process': self.max_threads_per_process,
                'total_capacity': self.max_processes * self.max_threads_per_process,
                'active_thread_pools': len(self.thread_pools)
            }
    
    def shutdown(self, wait=True):
        """Завершить все пулы"""
        logger.info("Shutting down hybrid executor...")
        
        # Завершаем процессный пул
        self.process_pool.shutdown(wait=wait)
        
        # Завершаем потоковые пулы
        with self.lock:
            for pool in self.thread_pools.values():
                pool.shutdown(wait=wait)
            self.thread_pools.clear()
        
        logger.info("Hybrid executor shutdown completed")

# Global hybrid executor (configuration from limits.py)
from CONFIG.limits import LimitsConfig

hybrid_executor = HybridExecutor(
    max_processes=LimitsConfig.MAX_PROCESSES,
    max_threads_per_process=LimitsConfig.MAX_THREADS_PER_PROCESS
)
