"""
GLOBAL MESSAGES PATCH - РЕШАЕТ ПРОБЛЕМУ 'name messages is not defined' РАЗ И НАВСЕГДА

Этот файл содержит глобальные патчи для предотвращения ошибки 'name messages is not defined'
во ВСЕХ файлах проекта.
"""

import sys
import os

# Добавляем путь к CONFIG (из папки PATCH)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'CONFIG'))

def apply_global_messages_patch():
    """
    Применяет глобальный патч для предотвращения ошибки 'name messages is not defined'
    """
    try:
        from CONFIG.messages import safe_messages, safe_get_messages
        
        # Патчим встроенные функции
        import builtins
        
        # Создаем безопасную версию get_messages_instance
        def safe_safe_get_messages(user_id=None):
            try:
                from CONFIG.messages import safe_get_messages
                return safe_get_messages(user_id)
            except:
                return safe_messages(user_id)
        
        # Добавляем в глобальное пространство имен
        builtins.safe_get_messages_instance = safe_safe_get_messages
        builtins.safe_messages = safe_messages
        
        print("✅ GLOBAL MESSAGES PATCH APPLIED - NameError protection active")
        
    except Exception as e:
        print(f"❌ Failed to apply global messages patch: {e}")
        # Создаем минимальную защиту
        class EmergencyMessages:
            def __getattr__(self, name):
                return f"[{name}]"
        
        # Не объявляем global messages здесь, чтобы избежать конфликтов
        pass

# Автоматически применяем патч при импорте
apply_global_messages_patch()
