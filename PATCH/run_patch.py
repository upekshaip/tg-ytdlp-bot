#!/usr/bin/env python3
"""
Запуск глобального патча из папки PATCH
"""

import sys
import os

# Добавляем корневую папку проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Применяем глобальный патч
from GLOBAL_MESSAGES_PATCH import apply_global_messages_patch

if __name__ == "__main__":
    print("🔧 Запуск глобального патча...")
    apply_global_messages_patch()
    print("✅ Патч применен успешно!")
