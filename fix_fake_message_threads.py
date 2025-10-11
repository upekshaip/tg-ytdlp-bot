#!/usr/bin/env python3
"""
Скрипт для исправления вызовов fake_message, чтобы они правильно передавали message_thread_id
"""

import os
import re
from pathlib import Path

def fix_fake_message_calls(file_path):
    """Исправить вызовы fake_message в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Паттерн для поиска вызовов fake_message без message_thread_id
        # Ищем: fake_message(text, user_id) или fake_message(text, user_id, command)
        pattern = r'fake_message\(([^,]+),\s*([^,)]+)(?:,\s*([^)]+))?\)'
        
        def replace_fake_message(match):
            text = match.group(1).strip()
            user_id = match.group(2).strip()
            command = match.group(3).strip() if match.group(3) else None
            
            # Если это уже содержит message_thread_id, не трогаем
            if 'message_thread_id' in match.group(0):
                return match.group(0)
            
            # Если это callback_query контекст, используем callback_query.message
            if 'callback_query' in content[max(0, match.start()-200):match.start()]:
                if command:
                    return f'fake_message_with_context({text}, {user_id}, callback_query.message, {command})'
                else:
                    return f'fake_message_with_context({text}, {user_id}, callback_query.message)'
            
            # Если это message контекст, используем message
            if 'message' in content[max(0, match.start()-200):match.start()]:
                if command:
                    return f'fake_message_with_context({text}, {user_id}, message, {command})'
                else:
                    return f'fake_message_with_context({text}, {user_id}, message)'
            
            # По умолчанию оставляем как есть
            return match.group(0)
        
        # Применяем замены
        content = re.sub(pattern, replace_fake_message, content)
        
        # Если есть изменения, записываем файл
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                content.write(content)
            print(f"✅ Исправлен файл: {file_path}")
            return True
        else:
            print(f"⏭️  Файл не требует изменений: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при обработке {file_path}: {e}")
        return False

def main():
    """Основная функция"""
    # Файлы, которые нужно проверить
    files_to_check = [
        "COMMANDS/settings_cmd.py",
        "COMMANDS/clean_cmd.py", 
        "COMMANDS/cookies_cmd.py",
        "URL_PARSERS/url_extractor.py"
    ]
    
    print("🔧 Исправление вызовов fake_message для поддержки топиков...")
    
    fixed_count = 0
    for file_path in files_to_check:
        if os.path.exists(file_path):
            if fix_fake_message_calls(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Файл не найден: {file_path}")
    
    print(f"\n📊 Результат: исправлено {fixed_count} файлов")

if __name__ == "__main__":
    main()
