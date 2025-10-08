#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Отладочный скрипт для проверки парсинга команды /split
"""

import re

def parse_size_argument(arg):
    """
    Parse size argument and return size in bytes
    """
    print(f"DEBUG: parse_size_argument получил аргумент: '{arg}'")
    
    if not arg:
        print("DEBUG: Аргумент пустой")
        return None
    
    # Remove spaces and convert to lowercase
    original_arg = arg
    arg = arg.lower().replace(" ", "")
    print(f"DEBUG: После обработки: '{arg}'")
    
    # Match patterns like "250mb", "1.5gb", "2GB", "100MB", "2000MB"
    match = re.match(r'^(\d+(?:\.\d+)?)(mb|gb)$', arg)
    if not match:
        print("DEBUG: Регулярное выражение не сработало")
        return None
    
    number = float(match.group(1))
    unit = match.group(2)
    print(f"DEBUG: Извлечено число: {number}, единица: '{unit}'")
    
    # Convert to bytes
    if unit.lower() == "mb":
        size_bytes = int(number * 1024 * 1024)
        print(f"DEBUG: Конвертировано в MB: {size_bytes} bytes")
    elif unit.lower() == "gb":
        size_bytes = int(number * 1024 * 1024 * 1024)
        print(f"DEBUG: Конвертировано в GB: {size_bytes} bytes")
    else:
        print(f"DEBUG: Неизвестная единица: '{unit}'")
        return None
    
    # Check limits: 100MB to 2GB
    min_size = 100 * 1024 * 1024  # 100MB
    max_size = 2 * 1024 * 1024 * 1024  # 2GB
    
    if size_bytes < min_size:
        print(f"DEBUG: Слишком маленький размер: {size_bytes} < {min_size}")
        return None  # Too small
    elif size_bytes > max_size:
        print(f"DEBUG: Слишком большой размер: {size_bytes} > {max_size}")
        return None  # Too large
    
    print(f"DEBUG: Успешно обработано: {size_bytes} bytes")
    return size_bytes

def humanbytes(B):
    """Return the given bytes as a human readable KB/MB/GB/TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B / TB)

# Симулируем обработку команды /split 100mb
print("=== Тест 1: /split 100mb ===")
text = "/split 100mb"
parts = text.strip().split()
print(f"Разделенные части: {parts}")

if len(parts) > 1:
    cmd = parts[0][1:] if len(parts[0]) > 1 else ''
    args = parts[1:] if len(parts) > 1 else []
    print(f"Команда: '{cmd}', аргументы: {args}")
    
    if len(args) > 0:
        arg = args[0].lower()  # Это происходит в split_command
        print(f"Аргумент после .lower(): '{arg}'")
        result = parse_size_argument(arg)
        if result:
            print(f"✅ Результат: {humanbytes(result)}")
        else:
            print("❌ Ошибка парсинга")

print("\n=== Тест 2: /split 100MB ===")
text = "/split 100MB"
parts = text.strip().split()
print(f"Разделенные части: {parts}")

if len(parts) > 1:
    cmd = parts[0][1:] if len(parts[0]) > 1 else ''
    args = parts[1:] if len(parts) > 1 else []
    print(f"Команда: '{cmd}', аргументы: {args}")
    
    if len(args) > 0:
        arg = args[0].lower()  # Это происходит в split_command
        print(f"Аргумент после .lower(): '{arg}'")
        result = parse_size_argument(arg)
        if result:
            print(f"✅ Результат: {humanbytes(result)}")
        else:
            print("❌ Ошибка парсинга")
