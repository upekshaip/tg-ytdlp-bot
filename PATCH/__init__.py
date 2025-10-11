"""
PATCH Module - Глобальные патчи для проекта
"""

# Автоматически применяем глобальный патч при импорте модуля
from .GLOBAL_MESSAGES_PATCH import apply_global_messages_patch

# Применяем патч
apply_global_messages_patch()
