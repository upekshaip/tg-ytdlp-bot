#!/usr/bin/env python3
"""
Ультимативный скрипт для замены всех оставшихся переменных с 0 вхождений
"""

import os
import re
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append('/mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW')
from CONFIG.messages import MessagesConfig as Messages

def get_variables_with_zero_occurrences():
    """Получить список переменных с 0 вхождений"""
    import subprocess
    result = subprocess.run(['python3', 'test_count_var.py'], 
                          cwd='/mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW/_backup',
                          capture_output=True, text=True)
    
    zero_vars = []
    for line in result.stdout.split('\n'):
        if line.strip().endswith(' 0'):
            var_name = line.strip().split()[0]
            zero_vars.append(var_name)
    
    return zero_vars

def get_message_text(var_name):
    """Получить текст сообщения для переменной"""
    try:
        return getattr(Messages, var_name)
    except AttributeMessages.ERROR_UNKNOWN_MSG.format(error=error):
        return None

def create_comprehensive_patterns(text):
    """Создать всевозможные паттерны для поиска"""
    patterns = []
    
    # 1. Точный текст
    patterns.append(text)
    
    # 2. Текст без переносов строк
    patterns.append(text.replace('\n', ' '))
    
    # 3. Текст с экранированными переносами
    patterns.append(text.replace('\n', '\\n'))
    
    # 4. Текст с двойными переносами
    patterns.append(text.replace('\n', '\n\n'))
    
    # 5. Текст с нормализованными пробелами
    patterns.append(re.sub(r'\s+', ' ', text))
    
    # 6. Извлекаем ключевые слова
    words = re.findall(r'\b\w+\b', text)
    for word in words:
        if len(word) > 3:
            patterns.append(word)
    
    # 7. Извлекаем фразы
    phrases = re.findall(r'[^.!?\n]+', text)
    for phrase in phrases:
        phrase = phrase.strip()
        if len(phrase) > 8:
            patterns.append(phrase)
    
    # 8. Извлекаем HTML теги и их содержимое
    html_matches = re.findall(r'<[^>]+>[^<]*</[^>]+>', text)
    for html in html_matches:
        patterns.append(html)
    
    # 9. Извлекаем эмодзи и текст после них
    emoji_matches = re.findall(r'[^\w\s][^\w\s]*\s*[^.!?\n]*', text)
    for emoji_text in emoji_matches:
        if len(emoji_text.strip()) > 4:
            patterns.append(emoji_text.strip())
    
    # 10. Извлекаем части текста для сложных случаев
    if len(text) > 30:
        # Берем первые 30 символов
        patterns.append(text[:30])
    if len(text) > 50:
        # Берем первые 50 символов
        patterns.append(text[:50])
    if len(text) > 100:
        # Берем первые 100 символов
        patterns.append(text[:100])
    
    # 11. Извлекаем строки отдельно
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) > 5:
            patterns.append(line)
    
    # 12. Извлекаем предложения
    sentences = re.findall(r'[^.!?]+[.!?]', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:
            patterns.append(sentence)
    
    # Убираем дубликаты и сортируем по длине
    patterns = list(set(patterns))
    patterns.sort(key=len, reverse=True)
    
    return patterns

def find_and_replace_in_file(file_path, var_name, message_text):
    """Найти и заменить переменную в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements_made = []
        
        # Создаем паттерны для поиска
        patterns = create_comprehensive_patterns(message_text)
        
        for pattern in patterns:
            if len(pattern) < 4:  # Пропускаем слишком короткие паттерны
                continue
                
            # Ищем все вхождения паттерна
            matches = list(re.finditer(re.escape(pattern), content, re.IGNORECASE | re.MULTILINE | re.DOTALL))
            
            for match in reversed(matches):  # Обрабатываем с конца
                start, end = match.span()
                matched_text = match.group()
                
                # Проверяем, что это действительно наш текст
                if len(matched_text) < len(message_text) * 0.2:  # Если совпадение слишком короткое
                    continue
                
                # Создаем замену
                if '{' in message_text and '}' in message_text:
                    params = re.findall(r'\{(\w+)\}', message_text)
                    if params:
                        param_str = ', '.join([f"{param}={param}" for param in params])
                        replacement = f"Messages.{var_name}.format({param_str})"
                    else:
                        replacement = f"Messages.{var_name}"
                else:
                    replacement = f"Messages.{var_name}"
                
                # Заменяем
                content = content[:start] + replacement + content[end:]
                replacements_made.append(f"Заменен: {matched_text[:50]}... -> {replacement}")
        
        # Если были изменения, записываем файл
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, replacements_made
        else:
            return False, []
            
    except Exception as e:
        return False, [f"Ошибка обработки файла {file_path}: {e}"]

def add_import_if_needed(file_path):
    """Добавить импорт Messages если нужно"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Messages.' in content and 'from CONFIG.messages import MessagesConfig as Messages' not in content:
            lines = content.split('\n')
            import_line = 'from CONFIG.messages import MessagesConfig as Messages'
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                else:
                    lines.insert(i, import_line)
                    break
            else:
                lines.insert(0, import_line)
            
            content = '\n'.join(lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        return False
        
    except Exception as e:
        print(f"❌ Ошибка добавления импорта в {file_path}: {e}")
        return False

def main():
    print("🔍 Ультимативный поиск и замена всех оставшихся переменных...")
    
    zero_vars = get_variables_with_zero_occurrences()
    print(f"📋 Найдено переменных с 0 вхождений: {len(zero_vars)}")
    
    base_dir = '/mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW'
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', '_backup', '_cursor', '.cursor', 'node_modules'}
    
    total_replacements = 0
    files_processed = set()
    
    for var_name in zero_vars:
        print(f"\n🔍 Ультимативно ищем {var_name}...")
        message_text = get_message_text(var_name)
        
        if not message_text:
            print(f"❌ Переменная {var_name} не найдена в MessagesConfig")
            continue
        
        print(f"📝 Текст: {message_text[:100]}...")
        
        # Создаем паттерны для поиска
        patterns = create_comprehensive_patterns(message_text)
        print(f"🔍 Создано {len(patterns)} паттернов для поиска")
        
        # Обрабатываем все файлы
        files_changed = 0
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py') and file != 'messages.py':
                    file_path = os.path.join(root, file)
                    
                    success, replacements = find_and_replace_in_file(file_path, var_name, message_text)
                    
                    if success:
                        files_changed += 1
                        files_processed.add(file_path)
                        total_replacements += len(replacements)
                        print(f"  ✅ {os.path.basename(file_path)}: {len(replacements)} замен")
                        for replacement in replacements[:2]:  # Показываем только первые 2
                            print(f"      {replacement}")
                        if len(replacements) > 2:
                            print(f"      ... и еще {len(replacements) - 2} замен")
        
        if files_changed == 0:
            print(f"  ❌ Не найдено совпадений для {var_name}")
    
    # Добавляем импорты в измененные файлы
    for file_path in files_processed:
        if add_import_if_needed(file_path):
            print(f"  ✅ Добавлен импорт Messages в {file_path}")
    
    print(f"\n📊 Результат:")
    print(f"Обработано файлов: {len(files_processed)}")
    print(f"Всего замен: {total_replacements}")

if __name__ == "__main__":
    main()
