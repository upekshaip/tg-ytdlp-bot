#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сканирует проект (кроме CONFIG/messages.py и папок, начинающихся с '_')
и ищет идентификаторы формата КАПС_КАПС (A-Z0-9 + минимум одно подчёркивание)
во всех *.py файлах. Выводит те, которых нет в CONFIG/messages.py.
"""

import os
import re

CONFIG_FILE = 'CONFIG/messages.py'   # путь к файлу-источнику


def extract_config_vars(path: str) -> set:
    """Собирает все имена переменных из MessagesConfig."""
    var_pattern = re.compile(r'^\s*([A-Z0-9_]+)\s*=')
    names = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            m = var_pattern.match(line)
            if m:
                names.add(m.group(1))
    return names


def find_uppercase_identifiers(base_dir: str, config_abs: str) -> set:
    """
    Ищет идентификаторы вида КАПС_КАПС только в *.py файлах,
    исключая config_abs и каталоги, начинающиеся на "_".
    """
    # хотя бы две группы капса, разделённые подчёркиванием
    pattern = re.compile(r'\b[A-Z0-9]+_[A-Z0-9_]*[A-Z0-9]\b')
    found = set()

    for root, dirs, files in os.walk(base_dir):
        # исключаем каталоги, начинающиеся с "_"
        dirs[:] = [d for d in dirs if not d.startswith('_')]

        for fname in files:
            if not fname.endswith('.py'):
                continue
            full_path = os.path.join(root, fname)
            if os.path.abspath(full_path) == config_abs:
                continue
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                for match in pattern.findall(text):
                    found.add(match)
            except Exception as e:
                print(f"[WARN] Can't read {full_path}: {e}")
    return found


def main():
    config_abs = os.path.abspath(CONFIG_FILE)
    if not os.path.exists(config_abs):
        print(f"Файл {CONFIG_FILE} не найден!")
        return

    config_vars = extract_config_vars(config_abs)
    code_vars = find_uppercase_identifiers(os.getcwd(), config_abs)

    # то, что есть в коде, но отсутствует в MessagesConfig
    missing = sorted(code_vars - config_vars)

    print(f"Найдено в коде КАПС-идентификаторов: {len(code_vars)}")
    print(f"Найдено в CONFIG/messages.py: {len(config_vars)}")
    print("\nОтсутствуют в CONFIG/messages.py:\n")
    if missing:
        for name in missing:
            print(name)
    else:
        print("✅ Все идентификаторы из кода присутствуют в CONFIG/messages.py")


if __name__ == "__main__":
    main()
