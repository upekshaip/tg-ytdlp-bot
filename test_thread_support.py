#!/usr/bin/env python3
"""
Скрипт для проверки поддержки топиков (threads) в боте
"""

import os
import re
from pathlib import Path

def check_thread_support():
    """Проверить поддержку топиков в коде"""
    print("🔍 Проверка поддержки топиков (threads) в боте...")
    
    # Ключевые файлы для проверки
    key_files = [
        "HELPERS/safe_messeger.py",
        "COMMANDS/image_cmd.py", 
        "DOWN_AND_UP/down_and_up.py",
        "DOWN_AND_UP/down_and_audio.py",
        "DOWN_AND_UP/always_ask_menu.py"
    ]
    
    thread_support_score = 0
    total_checks = 0
    
    for file_path in key_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Файл не найден: {file_path}")
            continue
            
        print(f"\n📁 Проверка {file_path}:")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверки поддержки топиков
        checks = [
            ("message_thread_id", "Использование message_thread_id"),
            ("get_message_thread_id", "Функция извлечения thread_id"),
            ("fake_message.*message_thread_id", "fake_message с thread_id"),
            ("safe_send_message.*message_thread_id", "safe_send_message с thread_id"),
            ("ReplyParameters.*message_thread_id", "ReplyParameters с thread_id"),
            ("send_media_group.*message_thread_id", "send_media_group с thread_id"),
            ("forward_messages.*message_thread_id", "forward_messages с thread_id")
        ]
        
        file_score = 0
        for pattern, description in checks:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"  ✅ {description}")
                file_score += 1
            else:
                print(f"  ❌ {description}")
        
        thread_support_score += file_score
        total_checks += len(checks)
        print(f"  📊 Оценка файла: {file_score}/{len(checks)}")
    
    print(f"\n📊 Общая оценка поддержки топиков: {thread_support_score}/{total_checks}")
    
    if thread_support_score >= total_checks * 0.8:
        print("✅ Отличная поддержка топиков!")
    elif thread_support_score >= total_checks * 0.6:
        print("⚠️  Хорошая поддержка топиков, но есть места для улучшения")
    else:
        print("❌ Слабая поддержка топиков, требуется доработка")

def check_specific_patterns():
    """Проверить конкретные паттерны поддержки топиков"""
    print("\n🔍 Проверка конкретных паттернов...")
    
    patterns_to_check = [
        {
            "pattern": r"getattr\([^,]+,\s*['\"]message_thread_id['\"][^)]*\)",
            "description": "Извлечение message_thread_id из сообщений",
            "files": ["COMMANDS", "DOWN_AND_UP", "HELPERS"]
        },
        {
            "pattern": r"message_thread_id\s*=\s*getattr",
            "description": "Присваивание message_thread_id",
            "files": ["COMMANDS", "DOWN_AND_UP", "HELPERS"]
        },
        {
            "pattern": r"kwargs\['message_thread_id'\]",
            "description": "Передача message_thread_id в kwargs",
            "files": ["COMMANDS", "DOWN_AND_UP", "HELPERS"]
        },
        {
            "pattern": r"fake_message.*original_message",
            "description": "fake_message с original_message",
            "files": ["COMMANDS", "DOWN_AND_UP", "URL_PARSERS"]
        }
    ]
    
    for pattern_info in patterns_to_check:
        pattern = pattern_info["pattern"]
        description = pattern_info["description"]
        files = pattern_info["files"]
        
        found_count = 0
        for file_dir in files:
            if os.path.exists(file_dir):
                for file_path in Path(file_dir).rglob("*.py"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if re.search(pattern, content, re.IGNORECASE):
                            found_count += 1
                    except Exception:
                        continue
        
        print(f"  {'✅' if found_count > 0 else '❌'} {description}: найдено {found_count} использований")

if __name__ == "__main__":
    check_thread_support()
    check_specific_patterns()
