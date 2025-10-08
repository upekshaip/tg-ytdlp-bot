#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест реальной обработки команды /split
"""

import re

def parse_size_argument(arg):
    """
    Parse size argument and return size in bytes
    """
    if not arg:
        return None
    
    # Remove spaces and convert to lowercase
    arg = arg.lower().replace(" ", "")
    
    # Match patterns like "250mb", "1.5gb", "2GB", "100MB", "2000MB"
    match = re.match(r'^(\d+(?:\.\d+)?)(mb|gb)$', arg)
    if not match:
        return None
    
    number = float(match.group(1))
    unit = match.group(2)
    
    # Convert to bytes
    if unit.lower() == "mb":
        size_bytes = int(number * 1024 * 1024)
    elif unit.lower() == "gb":
        size_bytes = int(number * 1024 * 1024 * 1024)
    else:
        return None
    
    # Check limits: 100MB to 2GB
    min_size = 100 * 1024 * 1024  # 100MB
    max_size = 2 * 1024 * 1024 * 1024  # 2GB
    
    if size_bytes < min_size:
        return None  # Too small
    elif size_bytes > max_size:
        return None  # Too large
    
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

# Симулируем обработку как в url_extractor.py
def simulate_url_extractor_processing(text):
    print(f"=== Обработка текста: '{text}' ===")
    
    # Проверяем, начинается ли с /split
    if text.startswith("/split"):
        print("✅ Текст начинается с /split")
        
        # Парсим команду как в url_extractor.py
        parts = text.strip().split()
        print(f"Разделенные части: {parts}")
        
        if parts:
            cmd = parts[0][1:] if len(parts[0]) > 1 else ''
            args = parts[1:] if len(parts) > 1 else []
            print(f"Команда: '{cmd}', аргументы: {args}")
            
            # Создаем message.command как в коде
            message_command = [cmd] + args
            print(f"message.command: {message_command}")
            
            # Проверяем аргументы как в split_command
            if len(message_command) > 1:
                arg = message_command[1].lower()
                print(f"Аргумент после .lower(): '{arg}'")
                
                size = parse_size_argument(arg)
                if size:
                    print(f"✅ Успешно! Размер: {humanbytes(size)} ({size} bytes)")
                    return True
                else:
                    print("❌ parse_size_argument вернул None")
                    return False
            else:
                print("❌ Нет аргументов")
                return False
        else:
            print("❌ Пустой текст")
            return False
    else:
        print("❌ Текст не начинается с /split")
        return False

# Тестируем различные варианты
test_cases = [
    "/split 100mb",
    "/split 100MB", 
    "/split 100Mb",
    "/split 100mB",
    "/split 500mb",
    "/split 1gb",
    "/split 1GB",
    "/split 1.5gb",
    "/split 2gb",
    "/split 2000mb",
    "/split 50mb",  # Должно быть слишком мало
    "/split 3gb",   # Должно быть слишком много
    "/split invalid",
    "/split 100kb", # Неправильный формат
    "/split 100",   # Нет единицы измерения
]

print("Тестирование реальной обработки команды /split:")
print("=" * 60)

for test_case in test_cases:
    result = simulate_url_extractor_processing(test_case)
    print()

print("=" * 60)
print("Тест завершен!")
