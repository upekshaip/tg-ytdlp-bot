#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаления неуникальных строк из файла porn_keywords.txt
Удаляет строки, которые содержатся как полные слова в других строках
"""

import sys
import os
import re
from typing import List, Set, Dict

def remove_duplicate_keywords(input_file: str, output_file: str = None) -> None:
    """
    Удаляет строки, которые содержатся как полные слова в других строках.
    Например, если есть строки "porn" и "free porn video", то "porn" будет удалена,
    так как она содержится как полное слово в "free porn video".
    Но "porn" НЕ будет удалена из-за строк типа "4porn" или "eporn", так как
    в них "porn" не является отдельным словом.
    
    Args:
        input_file: Путь к входному файлу
        output_file: Путь к выходному файлу (если None, перезаписывает входной файл)
    """
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл {input_file} не найден")
        return
    
    print(f"Читаю файл {input_file}...")
    
    # Читаем все строки из файла
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"Найдено {len(lines)} строк")
    
    # Создаем резервную копию оригинального файла
    backup_file = input_file + '.backup'
    print(f"Создаю резервную копию: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        with open(input_file, 'r', encoding='utf-8') as original:
            f.write(original.read())
    
    # Сортируем строки по длине (сначала короткие, потом длинные)
    # Это важно для правильной работы алгоритма
    lines_sorted = sorted(lines, key=len)
    
    unique_lines = []
    removed_count = 0
    removed_details = []  # Детальная информация об удаленных строках
    
    print("Обрабатываю строки...")
    
    # Создаем индекс для быстрого поиска
    print("Создаю индекс для быстрого поиска...")
    line_index = {}
    for line in lines_sorted:
        if line not in line_index:
            line_index[line] = []
        line_index[line].append(line)
    
    for i, current_line in enumerate(lines_sorted):
        is_duplicate = False
        duplicate_reason = ""
        
        # Проверяем только строки длиннее текущей
        for other_line in lines_sorted:
            if current_line != other_line and len(other_line) > len(current_line):
                # Создаем регулярное выражение для поиска полного слова
                # \b - граница слова, re.escape - экранируем специальные символы
                pattern = r'\b' + re.escape(current_line) + r'\b'
                if re.search(pattern, other_line):
                    is_duplicate = True
                    duplicate_reason = f"содержится в '{other_line}'"
                    break
        
        if not is_duplicate:
            unique_lines.append(current_line)
        else:
            removed_count += 1
            removed_details.append({
                'removed': current_line,
                'reason': duplicate_reason
            })
        
        # Показываем прогресс каждые 1000 строк
        if (i + 1) % 1000 == 0:
            print(f"Обработано {i + 1}/{len(lines_sorted)} строк, удалено {removed_count}")
    
    print(f"Обработка завершена. Удалено {removed_count} дубликатов")
    print(f"Осталось {len(unique_lines)} уникальных строк")
    
    # Создаем подробный отчет
    report_file = input_file + '.removal_report.txt'
    print(f"Создаю подробный отчет: {report_file}")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ ОБ УДАЛЕНИИ ДУБЛИКАТОВ\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Исходный файл: {input_file}\n")
        f.write(f"Исходное количество строк: {len(lines)}\n")
        f.write(f"Количество удаленных строк: {removed_count}\n")
        f.write(f"Итоговое количество строк: {len(unique_lines)}\n")
        f.write(f"Процент удаленных: {(removed_count / len(lines) * 100):.2f}%\n\n")
        
        f.write("ДЕТАЛЬНЫЙ СПИСОК УДАЛЕННЫХ СТРОК:\n")
        f.write("-" * 50 + "\n")
        
        for i, detail in enumerate(removed_details, 1):
            f.write(f"{i:3d}. '{detail['removed']}' - {detail['reason']}\n")
        
        f.write(f"\nВсего удалено: {removed_count} строк\n")
    
    # Показываем примеры удаленных строк в консоли
    if removed_details:
        print(f"\nПримеры удаленных строк:")
        for i, detail in enumerate(removed_details[:10]):  # Показываем первые 10
            print(f"  {i+1:2d}. '{detail['removed']}' - {detail['reason']}")
        if len(removed_details) > 10:
            print(f"  ... и еще {len(removed_details) - 10} строк")
        print(f"\nПолный отчет сохранен в: {report_file}")
    
    # Определяем выходной файл
    if output_file is None:
        output_file = input_file
    
    # Записываем результат
    print(f"Записываю результат в {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in unique_lines:
            f.write(line + '\n')
    
    print("Готово!")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python remove_duplicate_keywords.py <input_file> [output_file]")
        print("Пример: python remove_duplicate_keywords.py TXT/porn_keywords.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    remove_duplicate_keywords(input_file, output_file)

if __name__ == "__main__":
    main()
