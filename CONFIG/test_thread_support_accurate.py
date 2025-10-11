#!/usr/bin/env python3
"""
Точный тест поддержки топиков (threads) в боте
"""

import os
import re
from pathlib import Path

def check_thread_support_accurate():
    """Точная проверка поддержки топиков"""
    print("🔍 Точная проверка поддержки топиков (threads) в боте...")
    
    # Ключевые файлы для проверки
    key_files = [
        "HELPERS/safe_messeger.py",
        "COMMANDS/image_cmd.py", 
        "DOWN_AND_UP/down_and_up.py",
        "DOWN_AND_UP/down_and_audio.py",
        "DOWN_AND_UP/always_ask_menu.py"
    ]
    
    total_score = 0
    max_score = 0
    
    for file_path in key_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Файл не найден: {file_path}")
            continue
            
        print(f"\n📁 Проверка {file_path}:")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_score = 0
        file_max = 0
        
        # 1. Проверка использования message_thread_id
        file_max += 1
        if 'message_thread_id' in content:
            print("  ✅ Использование message_thread_id")
            file_score += 1
        else:
            print("  ❌ Использование message_thread_id")
        
        # 2. Проверка извлечения thread_id
        file_max += 1
        if 'getattr.*message_thread_id' in content or 'get_message_thread_id' in content:
            print("  ✅ Извлечение thread_id")
            file_score += 1
        else:
            print("  ❌ Извлечение thread_id")
        
        # 3. Проверка передачи в API функции
        file_max += 1
        api_patterns = [
            'send_media_group.*message_thread_id',
            'forward_messages.*message_thread_id',
            'send_message.*message_thread_id',
            'message_thread_id.*kwargs'
        ]
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in api_patterns):
            print("  ✅ Передача в API функции")
            file_score += 1
        else:
            print("  ❌ Передача в API функции")
        
        # 4. Проверка обработки fake сообщений
        file_max += 1
        if 'fake_message.*message_thread_id' in content or 'original_message' in content:
            print("  ✅ Обработка fake сообщений")
            file_score += 1
        else:
            print("  ❌ Обработка fake сообщений")
        
        # 5. Проверка ReplyParameters
        file_max += 1
        if 'ReplyParameters.*message_thread_id' in content or 'reply_parameters.*message_thread_id' in content:
            print("  ✅ ReplyParameters с thread_id")
            file_score += 1
        else:
            print("  ❌ ReplyParameters с thread_id")
        
        total_score += file_score
        max_score += file_max
        print(f"  📊 Оценка файла: {file_score}/{file_max}")
    
    print(f"\n📊 Общая оценка: {total_score}/{max_score} ({total_score/max_score*100:.1f}%)")
    
    if total_score >= max_score * 0.8:
        print("✅ Отличная поддержка топиков!")
    elif total_score >= max_score * 0.6:
        print("✅ Хорошая поддержка топиков!")
    elif total_score >= max_score * 0.4:
        print("⚠️  Удовлетворительная поддержка топиков")
    else:
        print("❌ Слабая поддержка топиков")

def check_specific_implementations():
    """Проверить конкретные реализации"""
    print("\n🔍 Проверка конкретных реализаций...")
    
    implementations = [
        {
            "name": "Извлечение message_thread_id",
            "pattern": r"getattr\([^,]+,\s*['\"]message_thread_id['\"][^)]*\)",
            "files": ["COMMANDS", "DOWN_AND_UP", "HELPERS"]
        },
        {
            "name": "Передача в kwargs",
            "pattern": r"kwargs\['message_thread_id'\]|message_thread_id.*kwargs",
            "files": ["COMMANDS", "DOWN_AND_UP", "HELPERS"]
        },
        {
            "name": "API функции с thread_id",
            "pattern": r"(send_media_group|forward_messages|send_message).*message_thread_id",
            "files": ["COMMANDS", "DOWN_AND_UP"]
        },
        {
            "name": "fake_message с контекстом",
            "pattern": r"fake_message.*original_message|fake_message.*message_thread_id",
            "files": ["COMMANDS", "DOWN_AND_UP", "URL_PARSERS"]
        }
    ]
    
    for impl in implementations:
        found_count = 0
        for file_dir in impl["files"]:
            if os.path.exists(file_dir):
                for file_path in Path(file_dir).rglob("*.py"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if re.search(impl["pattern"], content, re.IGNORECASE):
                            found_count += 1
                    except Exception:
                        continue
        
        status = "✅" if found_count > 0 else "❌"
        print(f"  {status} {impl['name']}: {found_count} использований")

def check_critical_functions():
    """Проверить критические функции"""
    print("\n🔍 Проверка критических функций...")
    
    critical_functions = [
        {
            "file": "COMMANDS/image_cmd.py",
            "function": "image_command",
            "checks": ["message_thread_id", "get_message_thread_id", "send_media_group"]
        },
        {
            "file": "DOWN_AND_UP/down_and_up.py", 
            "function": "down_and_up",
            "checks": ["message_thread_id", "forward_messages", "fake_message"]
        },
        {
            "file": "HELPERS/safe_messeger.py",
            "function": "safe_send_message",
            "checks": ["message_thread_id", "kwargs", "original_message"]
        }
    ]
    
    for func_info in critical_functions:
        file_path = func_info["file"]
        if not os.path.exists(file_path):
            print(f"  ⚠️  Файл не найден: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найти функцию
        func_pattern = rf"def\s+{func_info['function']}\s*\("
        func_match = re.search(func_pattern, content)
        
        if func_match:
            print(f"  📁 {file_path}::{func_info['function']}:")
            for check in func_info["checks"]:
                if check in content:
                    print(f"    ✅ {check}")
                else:
                    print(f"    ❌ {check}")
        else:
            print(f"  ❌ Функция {func_info['function']} не найдена в {file_path}")

if __name__ == "__main__":
    check_thread_support_accurate()
    check_specific_implementations()
    check_critical_functions()
