# Health Monitor для отслеживания состояния бота
import asyncio
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.active_tasks = {}
        self.hanging_tasks = {}
        self.monitor_task = None
        self.is_running = False
    
    async def start_monitoring(self):
        """Запустить мониторинг здоровья бота"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        if self.monitor_task:
            self.monitor_task.cancel()
        self.is_running = False
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        logger.info("Health monitor background loop started.")
        while self.is_running:
            try:
                await self._check_health()
                await asyncio.sleep(30)  # Проверка каждые 30 секунд
            except asyncio.CancelledError:
                logger.info("Health monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
        logger.info("Health monitor background loop stopped.")
    
    async def _check_health(self):
        """Проверить состояние бота"""
        current_time = time.time()
        
        # Проверяем, не завис ли бот
        if current_time - self.last_activity > 300:  # 5 минут без активности
            logger.warning(f"Bot appears to be hanging - no activity for {current_time - self.last_activity:.1f} seconds")
            
            # Проверяем зависшие задачи
            for task_name, start_time in self.hanging_tasks.items():
                if current_time - start_time > 600:  # 10 минут
                    logger.error(f"Hanging task detected: {task_name} running for {current_time - start_time:.1f} seconds")
        
        # Очищаем старые записи
        self._cleanup_old_tasks()
    
    def update_activity(self):
        """Обновить время последней активности"""
        self.last_activity = time.time()
    
    def start_task(self, task_name: str):
        """Отметить начало задачи"""
        current_time = time.time()
        self.active_tasks[task_name] = current_time
        self.update_activity()
        logger.debug(f"Task started: {task_name}")
    
    def end_task(self, task_name: str):
        """Отметить завершение задачи"""
        if task_name in self.active_tasks:
            duration = time.time() - self.active_tasks[task_name]
            del self.active_tasks[task_name]
            logger.debug(f"Task completed: {task_name} (duration: {duration:.1f}s)")
        
        if task_name in self.hanging_tasks:
            del self.hanging_tasks[task_name]
    
    def mark_hanging_task(self, task_name: str):
        """Отметить задачу как зависшую"""
        if task_name in self.active_tasks:
            del self.active_tasks[task_name]
        self.hanging_tasks[task_name] = time.time()
        logger.warning(f"Task marked as hanging: {task_name}")
    
    def _cleanup_old_tasks(self):
        """Очистить старые записи о задачах"""
        current_time = time.time()
        
        # Очищаем старые активные задачи (старше 1 часа)
        old_active = [name for name, start_time in self.active_tasks.items() 
                     if current_time - start_time > 3600]
        for name in old_active:
            del self.active_tasks[name]
        
        # Очищаем старые зависшие задачи (старше 2 часов)
        old_hanging = [name for name, start_time in self.hanging_tasks.items() 
                      if current_time - start_time > 7200]
        for name in old_hanging:
            del self.hanging_tasks[name]
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус мониторинга"""
        current_time = time.time()
        return {
            'is_running': self.is_running,
            'last_activity': self.last_activity,
            'seconds_since_activity': current_time - self.last_activity,
            'active_tasks': len(self.active_tasks),
            'hanging_tasks': len(self.hanging_tasks),
            'active_task_names': list(self.active_tasks.keys()),
            'hanging_task_names': list(self.hanging_tasks.keys())
        }

# Глобальный экземпляр монитора
health_monitor = HealthMonitor()
