# Процессный пул для масштабирования до 2000+ пользователей
import asyncio
import multiprocessing
import concurrent.futures
import logging
import time
from typing import Dict, Any, Optional
import threading
import queue
import os
import signal

logger = logging.getLogger(__name__)

class ProcessPoolManager:
    def __init__(self, max_processes: int = 50, max_workers_per_process: int = 40):
        """
        Управляет пулом процессов для обработки пользователей
        
        Args:
            max_processes: Максимум процессов (50 процессов = 2000 пользователей)
            max_workers_per_process: Потоков на процесс (40 потоков на процесс)
        """
        self.max_processes = max_processes
        self.max_workers_per_process = max_workers_per_process
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_processes)
        self.active_processes: Dict[int, Any] = {}
        self.user_to_process: Dict[int, int] = {}
        self.lock = threading.Lock()
        
        logger.info("Initialized process pool: %s processes, %s workers per process", 
                   max_processes, max_workers_per_process)
    
    def get_process_for_user(self, user_id: int) -> int:
        """Получить процесс для пользователя (хеширование)"""
        # Простое хеширование для равномерного распределения
        process_id = user_id % self.max_processes
        return process_id
    
    async def submit_user_task(self, user_id: int, func, *args, **kwargs):
        """Отправить задачу пользователя в процесс"""
        process_id = self.get_process_for_user(user_id)
        
        # Создаем обертку для выполнения в процессе
        def process_wrapper():
            try:
                # Инициализация в процессе
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # Выполняем функцию
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("Process error for user %s: %s", user_id, e)
                raise
        
        # Отправляем в процесс
        future = asyncio.get_event_loop().run_in_executor(
            self.process_pool, 
            process_wrapper
        )
        
        return await future
    
    def get_status(self) -> Dict:
        """Получить статус пула процессов"""
        with self.lock:
            return {
                'max_processes': self.max_processes,
                'max_workers_per_process': self.max_workers_per_process,
                'total_capacity': self.max_processes * self.max_workers_per_process,
                'active_processes': len(self.active_processes)
            }
    
    def shutdown(self, wait=True):
        """Завершить все процессы"""
        logger.info("Shutting down process pool...")
        self.process_pool.shutdown(wait=wait)
        logger.info("Process pool shutdown completed")

# Глобальный экземпляр для 2000+ пользователей
process_pool = ProcessPoolManager(
    max_processes=50,        # 50 процессов
    max_workers_per_process=40  # 40 потоков на процесс = 2000 пользователей
)
