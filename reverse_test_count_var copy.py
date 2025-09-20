#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ищет во всех *.py файлах (и выбранных скриптах)
идентификаторы формата КАПС_КАПС (A-Z0-9 + минимум одно подчеркивание)
в указанных директориях/файлах и выводит те,
которых нет в CONFIG/messages.py.

Настройки:
  • CONFIG_FILE      – путь к файлу с исходными переменными
  • SEARCH_DIRS      – папки для сканирования
  • EXTRA_FILES      – отдельные файлы для сканирования
  • IGNORE_DIRS      – каталоги, которые полностью исключаются
  • IGNORE_FILES     – файлы, которые полностью исключаются
  • SHOW_PATHS       – True/False, выводить ли пути к файлам
"""

import os
import re
import tokenize
from pathlib import Path
from collections import defaultdict

# ===== НАСТРОЙКИ =====
CONFIG_FILE = Path('CONFIG/messages.py')

# Папки и отдельные файлы, где ищем
SEARCH_DIRS = [
    '.',                 # текущая папка
    'COMMANDS',
    #'CONFIG',
    'DATABASE',
    'DOWN_AND_UP',
    'HELPERS',
    'URL_PARSERS'
]
EXTRA_FILES = [
    'UPDATE.sh',
    'magic.py',
    'restore_from_backup.py',
    'update_from_repo.py'
]

# Папки/файлы, которые нужно исключить из обхода
IGNORE_DIRS = {'__pycache__', 'venv', '.venv', '.env', '.tox', 'CONFIG'}
IGNORE_FILES = {CONFIG_FILE.name, 'CONFIG/messages.py'}  # можно добавлять другие

# Показывать ли пути к файлам в выводе
SHOW_PATHS = True
# =====================


def extract_config_vars(config_path: Path) -> set:
    """Собирает все имена переменных из MessagesConfig."""
    var_pattern = re.compile(r'^\s*([A-Z0-9_]+)\s*=')
    names = set()
    with config_path.open('r', encoding='utf-8') as f:
        for line in f:
            m = var_pattern.match(line)
            if m:
                names.add(m.group(1))
    return names


def find_uppercase_identifiers(paths: list[Path], config_abs: Path) -> dict[str, set[str]]:
    """
    Ищет идентификаторы вида КАПС_КАПС только в коде Python
    (без строковых литералов/комментариев).
    Возвращает dict: {имя: set(путей)}
    """
    pattern = re.compile(r'^[A-Z0-9]+_[A-Z0-9_]*[A-Z0-9]$')
    found: dict[str, set[str]] = defaultdict(set)

    for p in paths:
        if p.is_dir():
            for root, dirs, files in os.walk(p):
                # исключаем служебные каталоги
                dirs[:] = [
                    d for d in dirs
                    if d not in IGNORE_DIRS and not d.startswith('_')
                ]
                for fname in files:
                    if not fname.endswith('.py') or fname.startswith('_') or fname in IGNORE_FILES:
                        continue
                    full = Path(root) / fname
                    if full.resolve() == config_abs.resolve():
                        continue
                    try:
                        with open(full, 'rb') as f:
                            tokens = tokenize.tokenize(f.readline)
                            for tok_type, tok_str, *_ in tokens:
                                if tok_type == tokenize.NAME and pattern.match(tok_str):
                                    found[tok_str].add(str(full))
                    except Exception as e:
                        print(f"[WARN] Can't read {full}: {e}")
        else:
            # отдельные файлы: только *.py и не начинающиеся на "_"
            if p.exists() and p.suffix == '.py' and not p.name.startswith('_') and p.name not in IGNORE_FILES:
                if p.resolve() == config_abs.resolve():
                    continue
                try:
                    with open(p, 'rb') as f:
                        tokens = tokenize.tokenize(f.readline)
                        for tok_type, tok_str, *_ in tokens:
                            if tok_type == tokenize.NAME and pattern.match(tok_str):
                                found[tok_str].add(str(p))
                except Exception as e:
                    print(f"[WARN] Can't read {p}: {e}")
    return found


def main():
    config_abs = CONFIG_FILE.resolve()
    if not config_abs.exists():
        print(f"Файл {CONFIG_FILE} не найден!")
        return

    config_vars = extract_config_vars(config_abs)
    search_paths = [Path(d) for d in SEARCH_DIRS] + [Path(f) for f in EXTRA_FILES]
    code_vars_map = find_uppercase_identifiers(search_paths, config_abs)

    # то, что есть в коде, но отсутствует в MessagesConfig
    missing = {name: paths for name, paths in code_vars_map.items()
               if name not in config_vars}

    print(f"Найдено в коде КАПС-идентификаторов: {len(code_vars_map)}")
    print(f"Найдено в CONFIG/messages.py: {len(config_vars)}")
    print("\nОтсутствуют в CONFIG/messages.py:\n")
    if missing:
        for name, paths in sorted(missing.items()):
            if SHOW_PATHS:
                print(f"{name}:")
                for p in sorted(paths):
                    print(f"    {p}")
            else:
                print(name)
    else:
        print("✅ Все идентификаторы из кода присутствуют в CONFIG/messages.py")


if __name__ == "__main__":
    main()
