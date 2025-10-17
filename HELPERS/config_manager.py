# Менеджер конфигурации для удобного управления масштабированием
import os
import logging
from typing import Dict, Any, Optional
from CONFIG.limits import LimitsConfig

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration manager for dynamic scaling management"""
    
    @staticmethod
    def get_current_config() -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'max_users': LimitsConfig.MAX_USERS,
            'max_processes': LimitsConfig.MAX_PROCESSES,
            'max_threads_per_process': LimitsConfig.MAX_THREADS_PER_PROCESS,
            'max_global_workers': LimitsConfig.MAX_GLOBAL_WORKERS,
            'max_concurrent_global': LimitsConfig.MAX_CONCURRENT_GLOBAL,
            'vip_processes': LimitsConfig.VIP_PROCESSES,
            'high_processes': LimitsConfig.HIGH_PROCESSES,
            'normal_processes': LimitsConfig.NORMAL_PROCESSES,
            'low_processes': LimitsConfig.LOW_PROCESSES,
            'firebase_pool_size': LimitsConfig.FIREBASE_POOL_SIZE,
            'telegram_pool_size': LimitsConfig.TELEGRAM_POOL_SIZE,
            'guard_semaphore_limit': LimitsConfig.GUARD_SEMAPHORE_LIMIT
        }
    
    @staticmethod
    def get_scale_config(scale_type: str) -> Dict[str, Any]:
        """Get predefined configuration"""
        configs = {
            'small': LimitsConfig.SMALL_SCALE_CONFIG,
            'medium': LimitsConfig.MEDIUM_SCALE_CONFIG,
            'large': LimitsConfig.LARGE_SCALE_CONFIG,
            'enterprise': LimitsConfig.ENTERPRISE_SCALE_CONFIG,
            'extreme': LimitsConfig.EXTREME_SCALE_CONFIG,
            'oracle_cloud': LimitsConfig.ORACLE_CLOUD_CONFIG
        }
        return configs.get(scale_type, LimitsConfig.ORACLE_CLOUD_CONFIG)
    
    @staticmethod
    def get_system_requirements(scale_type: str) -> Dict[str, Any]:
        """Get system requirements for scaling type"""
        return LimitsConfig.SYSTEM_REQUIREMENTS.get(scale_type, LimitsConfig.SYSTEM_REQUIREMENTS['oracle_cloud'])
    
    @staticmethod
    def apply_scale_config(scale_type: str) -> bool:
        """Apply predefined configuration"""
        try:
            config = ConfigManager.get_scale_config(scale_type)
            
            # Update configuration via environment variables
            os.environ['MAX_PROCESSES'] = str(config['max_processes'])
            os.environ['MAX_THREADS_PER_PROCESS'] = str(config['max_threads_per_process'])
            os.environ['MAX_GLOBAL_WORKERS'] = str(config['max_global_workers'])
            os.environ['MAX_CONCURRENT_GLOBAL'] = str(config['max_concurrent_global'])
            os.environ['FIREBASE_POOL_SIZE'] = str(config['firebase_pool_size'])
            os.environ['TELEGRAM_POOL_SIZE'] = str(config['telegram_pool_size'])
            
            logger.info("Applied scale configuration: %s", scale_type)
            return True
            
        except Exception as e:
            logger.error("Failed to apply scale configuration: %s", e)
            return False
    
    @staticmethod
    def get_optimal_config(expected_users: int) -> Dict[str, Any]:
        """Get optimal configuration for expected number of users"""
        if expected_users <= 100:
            return ConfigManager.get_scale_config('small')
        elif expected_users <= 1000:
            return ConfigManager.get_scale_config('medium')
        elif expected_users <= 5000:
            return ConfigManager.get_scale_config('large')
        elif expected_users <= 10000:
            return ConfigManager.get_scale_config('enterprise')
        else:
            return ConfigManager.get_scale_config('extreme')
    
    @staticmethod
    def print_config_info():
        """Print current configuration information"""
        config = ConfigManager.get_current_config()
        
        print("🔧 Current scaling configuration:")
        print(f"   👥 Users: {config['max_users']}")
        print(f"   🔄 Processes: {config['max_processes']}")
        print(f"   🧵 Threads per process: {config['max_threads_per_process']}")
        print(f"   📊 Total threads: {config['max_global_workers']}")
        print(f"   ⬇️ Concurrent downloads: {config['max_concurrent_global']}")
        print(f"   🔥 Firebase pool: {config['firebase_pool_size']}")
        print(f"   📱 Telegram pool: {config['telegram_pool_size']}")
        print(f"   🛡️ Semaphore: {config['guard_semaphore_limit']}")
        
        print("\n📈 Priority pools:")
        print(f"   👑 VIP: {config['vip_processes']} processes")
        print(f"   ⭐ HIGH: {config['high_processes']} processes")
        print(f"   📋 NORMAL: {config['normal_processes']} processes")
        print(f"   📄 LOW: {config['low_processes']} processes")
    
    @staticmethod
    def print_scale_options():
        """Print available scaling options"""
        print("🎯 Available scaling options:")
        
        scales = [
            ('small', 'Small loads (< 100 users)'),
            ('medium', 'Medium loads (< 1000 users)'),
            ('large', 'Large loads (< 5000 users)'),
            ('enterprise', 'Enterprise loads (10000+ users)'),
            ('extreme', 'Extreme loads (50000+ users)')
        ]
        
        for scale_type, description in scales:
            config = ConfigManager.get_scale_config(scale_type)
            requirements = ConfigManager.get_system_requirements(scale_type)
            
            print(f"\n   {scale_type.upper()}: {description}")
            print(f"      🔄 Processes: {config['max_processes']}")
            print(f"      🧵 Threads: {config['max_threads_per_process']}")
            print(f"      📊 Total threads: {config['max_global_workers']}")
            print(f"      💻 CPU: {requirements['cpu_cores']} cores")
            print(f"      🧠 RAM: {requirements['ram_gb']} GB")
            print(f"      💾 Disk: {requirements['disk_gb']} GB")
            print(f"      🌐 Network: {requirements['network_mbps']} Mbps")

# Global manager instance
config_manager = ConfigManager()
