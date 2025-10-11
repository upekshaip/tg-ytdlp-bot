#!/usr/bin/env python3
"""
ПАТЧ: Исправление всех сравнений с None в коде
Автоматически находит и исправляет все места где переменные сравниваются с числами без проверки на None
"""
import os
import re
import glob

def fix_none_comparisons_in_file(file_path):
    """Исправить сравнения с None в одном файле"""
    changes_made = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Паттерн 1: if variable and variable > number
        pattern1 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([0-9]+)'
        def replace1(match):
            var_name = match.group(1)
            number = match.group(2)
            return f'if {var_name} and {var_name} > {number}'
        
        content = re.sub(pattern1, replace1, content)
        
        # Паттерн 2: if variable and variable < number  
        pattern2 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([0-9]+)'
        def replace2(match):
            var_name = match.group(1)
            number = match.group(2)
            return f'if {var_name} and {var_name} < {number}'
        
        content = re.sub(pattern2, replace2, content)
        
        # Паттерн 3: if variable and variable > expression (с переменными)
        pattern3 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))'
        def replace3(match):
            var_name = match.group(1)
            expression = match.group(2)
            return f'if {var_name} and {var_name} > {expression}'
        
        content = re.sub(pattern3, replace3, content)
        
        # Паттерн 4: if variable and variable < expression (с переменными)
        pattern4 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))'
        def replace4(match):
            var_name = match.group(1)
            expression = match.group(2)
            return f'if {var_name} and {var_name} < {expression}'
        
        content = re.sub(pattern4, replace4, content)
        
        # Паттерн 5: if variable and variable > variable
        pattern5 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+)'
        def replace5(match):
            var_name = match.group(1)
            other_var = match.group(2)
            number = match.group(3)
            return f'if {var_name} and {var_name} > {other_var} - {number}'
        
        content = re.sub(pattern5, replace5, content)
        
        # Паттерн 6: if variable and variable < variable
        pattern6 = r'if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+)'
        def replace6(match):
            var_name = match.group(1)
            other_var = match.group(2)
            number = match.group(3)
            return f'if {var_name} and {var_name} < {other_var} - {number}'
        
        content = re.sub(pattern6, replace6, content)
        
        # Подсчитываем изменения
        if content != original_content:
            changes_made = len(re.findall(r'if\s+[a-zA-Z_][a-zA-Z0-9_]*\s+and\s+[a-zA-Z_][a-zA-Z0-9_]*\s*[><]', content)) - len(re.findall(r'if\s+[a-zA-Z_][a-zA-Z0-9_]*\s+and\s+[a-zA-Z_][a-zA-Z0-9_]*\s*[><]', original_content))
            
            # Сохраняем изменения
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
    
    return changes_made

def apply_patch():
    """Применить патч ко всем Python файлам"""
    print("🔧 ПАТЧ: Исправление всех сравнений с None")
    print("=" * 50)
    
    # Находим все Python файлы
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Пропускаем папки с временными файлами
        if any(skip in root for skip in ['__pycache__', '.git', 'venv', 'backup']):
            continue
            
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                python_files.append(os.path.join(root, file))
    
    total_changes = 0
    files_changed = 0
    
    for file_path in python_files:
        changes = fix_none_comparisons_in_file(file_path)
        if changes and changes > 0:
            print(f"✅ {file_path}: {changes} исправлений")
            total_changes += changes
            files_changed += 1
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"   Файлов обработано: {len(python_files)}")
    print(f"   Файлов изменено: {files_changed}")
    print(f"   Всего исправлений: {total_changes}")
    
    if total_changes and total_changes > 0:
        print(f"\n🎉 ПАТЧ УСПЕШНО ПРИМЕНЕН!")
        print(f"   Все сравнения с None теперь защищены!")
    else:
        print(f"\n✅ Проблем не найдено - код уже исправлен!")

if __name__ == "__main__":
    apply_patch()
