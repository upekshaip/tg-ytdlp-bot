# Enterprise конфигурация для 10000+ пользователей
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EnterpriseConfig:
    """Конфигурация для enterprise-уровня масштабирования"""
    
    # Основные лимиты
    MAX_USERS = 10000
    MAX_PROCESSES = 200
    MAX_THREADS_PER_PROCESS = 50
    MAX_GLOBAL_WORKERS = 10000
    
    # Приоритетные пулы
    VIP_PROCESSES = 20      # VIP пользователи
    HIGH_PROCESSES = 50     # HIGH приоритет
    NORMAL_PROCESSES = 100  # NORMAL приоритет
    LOW_PROCESSES = 30      # LOW приоритет
    
    # Лимиты на пользователя
    MAX_DOWNLOADS_PER_USER = 1
    MAX_CONCURRENT_GLOBAL = 10000
    
    # Firebase лимиты
    FIREBASE_POOL_SIZE = 1000
    FIREBASE_TIMEOUT = 30
    
    # Telegram API лимиты
    TELEGRAM_POOL_SIZE = 1000
    TELEGRAM_TIMEOUT = 30
    
    # Мониторинг
    RESOURCE_CHECK_INTERVAL = 5  # секунд
    AUTO_SCALE_THRESHOLD = 80    # % использования ресурсов
    
    # Очереди
    QUEUE_SIZE = 50000
    QUEUE_TIMEOUT = 300  # секунд
    
    @classmethod
    def get_optimal_config(cls, expected_users: int) -> Dict[str, Any]:
        """Получить оптимальную конфигурацию для ожидаемого количества пользователей"""
        
        if expected_users <= 1000:
            return {
                'max_processes': 50,
                'max_threads_per_process': 20,
                'max_global_workers': 1000,
                'max_concurrent_global': 1000
            }
        elif expected_users <= 5000:
            return {
                'max_processes': 100,
                'max_threads_per_process': 50,
                'max_global_workers': 5000,
                'max_concurrent_global': 5000
            }
        elif expected_users <= 10000:
            return {
                'max_processes': 200,
                'max_threads_per_process': 50,
                'max_global_workers': 10000,
                'max_concurrent_global': 10000
            }
        else:  # 10000+
            return {
                'max_processes': 500,
                'max_threads_per_process': 20,
                'max_global_workers': 10000,
                'max_concurrent_global': 10000
            }
    
    @classmethod
    def get_system_requirements(cls, expected_users: int) -> Dict[str, Any]:
        """Получить системные требования для ожидаемого количества пользователей"""
        
        if expected_users <= 1000:
            return {
                'cpu_cores': 4,
                'ram_gb': 8,
                'disk_gb': 100,
                'network_mbps': 100
            }
        elif expected_users <= 5000:
            return {
                'cpu_cores': 8,
                'ram_gb': 16,
                'disk_gb': 500,
                'network_mbps': 500
            }
        elif expected_users <= 10000:
            return {
                'cpu_cores': 16,
                'ram_gb': 32,
                'disk_gb': 1000,
                'network_mbps': 1000
            }
        else:  # 10000+
            return {
                'cpu_cores': 32,
                'ram_gb': 64,
                'disk_gb': 2000,
                'network_mbps': 2000
            }
    
    @classmethod
    def get_scaling_strategy(cls, current_users: int) -> str:
        """Получить стратегию масштабирования"""
        
        if current_users < 100:
            return "single_process"
        elif current_users < 1000:
            return "multi_thread"
        elif current_users < 5000:
            return "multi_process"
        elif current_users < 10000:
            return "enterprise_scale"
        else:
            return "distributed_scale"

# Глобальная конфигурация
ENTERPRISE_CONFIG = EnterpriseConfig()

# Переменные окружения для настройки
def load_enterprise_config():
    """Загрузить конфигурацию из переменных окружения"""
    
    config = {
        'max_users': int(os.getenv('MAX_USERS', '10000')),
        'max_processes': int(os.getenv('MAX_PROCESSES', '200')),
        'max_threads_per_process': int(os.getenv('MAX_THREADS_PER_PROCESS', '50')),
        'max_global_workers': int(os.getenv('MAX_GLOBAL_WORKERS', '10000')),
        'max_concurrent_global': int(os.getenv('MAX_CONCURRENT_GLOBAL', '10000')),
        'firebase_pool_size': int(os.getenv('FIREBASE_POOL_SIZE', '1000')),
        'telegram_pool_size': int(os.getenv('TELEGRAM_POOL_SIZE', '1000')),
        'resource_check_interval': int(os.getenv('RESOURCE_CHECK_INTERVAL', '5')),
        'auto_scale_threshold': int(os.getenv('AUTO_SCALE_THRESHOLD', '80')),
        'queue_size': int(os.getenv('QUEUE_SIZE', '50000')),
        'queue_timeout': int(os.getenv('QUEUE_TIMEOUT', '300'))
    }
    
    logger.info("Loaded enterprise config: %s", config)
    return config

# Загружаем конфигурацию при импорте
ENTERPRISE_SETTINGS = load_enterprise_config()
