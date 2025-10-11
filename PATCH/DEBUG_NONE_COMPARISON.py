#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ ОШИБКИ NONE COMPARISON
===========================================================

Этот патч добавляет детальное логирование для отслеживания ошибки:
'>' not supported between instances of 'NoneType' and 'int'

Автор: AI Assistant
Дата: 11.10.2025
"""

import os
import re
import logging
from typing import Any, Optional

def apply_debug_none_comparison():
    """Применяет детальное логирование для отладки ошибки None comparison"""
    
    print("🔍 Применяем детальное логирование для отладки ошибки None comparison...")
    
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Создаем декоратор для отслеживания сравнений
    def debug_comparison_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Логируем входные параметры
                logger.debug(f"🔍 ВЫЗОВ ФУНКЦИИ: {func.__name__}")
                logger.debug(f"   Аргументы: {args}")
                logger.debug(f"   Ключевые аргументы: {kwargs}")
                
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем результат
                logger.debug(f"✅ ФУНКЦИЯ {func.__name__} ВЫПОЛНЕНА УСПЕШНО")
                return result
                
            except TypeError as e:
                if "'>' not supported between instances of 'NoneType' and 'int'" in str(e):
                    logger.error(f"❌ ОШИБКА NONE COMPARISON в функции {func.__name__}: {e}")
                    logger.error(f"   Аргументы: {args}")
                    logger.error(f"   Ключевые аргументы: {kwargs}")
                    
                    # Пытаемся найти проблемные переменные
                    for i, arg in enumerate(args):
                        if arg is None:
                            logger.error(f"   ⚠️  Аргумент {i} равен None: {arg}")
                        elif isinstance(arg, (int, float)):
                            logger.error(f"   ✅ Аргумент {i} - число: {arg}")
                        else:
                            logger.error(f"   ❓ Аргумент {i} - другой тип: {type(arg)} = {arg}")
                    
                    # Пытаемся найти проблемные ключевые аргументы
                    for key, value in kwargs.items():
                        if value is None:
                            logger.error(f"   ⚠️  Ключевой аргумент {key} равен None: {value}")
                        elif isinstance(value, (int, float)):
                            logger.error(f"   ✅ Ключевой аргумент {key} - число: {value}")
                        else:
                            logger.error(f"   ❓ Ключевой аргумент {key} - другой тип: {type(value)} = {value}")
                
                raise e
            except Exception as e:
                logger.error(f"❌ ОШИБКА в функции {func.__name__}: {e}")
                raise e
        
        return wrapper
    
    # Применяем декоратор к основным функциям
    try:
        from DOWN_AND_UP.always_ask_menu import ask_quality_menu
        ask_quality_menu = debug_comparison_decorator(ask_quality_menu)
        print("✅ Декоратор применен к ask_quality_menu")
    except Exception as e:
        print(f"⚠️  Не удалось применить декоратор к ask_quality_menu: {e}")
    
    try:
        from DOWN_AND_UP.yt_dlp_hook import get_video_formats
        get_video_formats = debug_comparison_decorator(get_video_formats)
        print("✅ Декоратор применен к get_video_formats")
    except Exception as e:
        print(f"⚠️  Не удалось применить декоратор к get_video_formats: {e}")
    
    # Создаем патч для отслеживания сравнений в коде
    def patch_comparison_operators():
        """Патчим операторы сравнения для отслеживания ошибок"""
        
        # Сохраняем оригинальные операторы
        original_gt = int.__gt__
        original_lt = int.__lt__
        original_ge = int.__ge__
        original_le = int.__le__
        
        def safe_gt(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ПЫТАЕМСЯ СРАВНИТЬ None: self={self}, other={other}")
                    logger.error(f"   Тип self: {type(self)}, Тип other: {type(other)}")
                    return False
                return original_gt(self, other)
            except Exception as e:
                logger.error(f"❌ ОШИБКА В СРАВНЕНИИ >: {e}")
                logger.error(f"   self={self} (тип: {type(self)})")
                logger.error(f"   other={other} (тип: {type(other)})")
                return False
        
        def safe_lt(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ПЫТАЕМСЯ СРАВНИТЬ None: self={self}, other={other}")
                    logger.error(f"   Тип self: {type(self)}, Тип other: {type(other)}")
                    return False
                return original_lt(self, other)
            except Exception as e:
                logger.error(f"❌ ОШИБКА В СРАВНЕНИИ <: {e}")
                logger.error(f"   self={self} (тип: {type(self)})")
                logger.error(f"   other={other} (тип: {type(other)})")
                return False
        
        def safe_ge(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ПЫТАЕМСЯ СРАВНИТЬ None: self={self}, other={other}")
                    logger.error(f"   Тип self: {type(self)}, Тип other: {type(other)}")
                    return False
                return original_ge(self, other)
            except Exception as e:
                logger.error(f"❌ ОШИБКА В СРАВНЕНИИ >=: {e}")
                logger.error(f"   self={self} (тип: {type(self)})")
                logger.error(f"   other={other} (тип: {type(other)})")
                return False
        
        def safe_le(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ПЫТАЕМСЯ СРАВНИТЬ None: self={self}, other={other}")
                    logger.error(f"   Тип self: {type(self)}, Тип other: {type(other)}")
                    return False
                return original_le(self, other)
            except Exception as e:
                logger.error(f"❌ ОШИБКА В СРАВНЕНИИ <=: {e}")
                logger.error(f"   self={self} (тип: {type(self)})")
                logger.error(f"   other={other} (тип: {type(other)})")
                return False
        
        # Применяем патчи
        try:
            int.__gt__ = safe_gt
            int.__lt__ = safe_lt
            int.__ge__ = safe_ge
            int.__le__ = safe_le
            print("✅ Патчи сравнений применены к int")
        except Exception as e:
            print(f"⚠️  Не удалось применить патчи к int: {e}")
        
        # Также патчим float
        try:
            float.__gt__ = safe_gt
            float.__lt__ = safe_lt
            float.__ge__ = safe_ge
            float.__le__ = safe_le
            print("✅ Патчи сравнений применены к float")
        except Exception as e:
            print(f"⚠️  Не удалось применить патчи к float: {e}")
    
    # Применяем патчи
    patch_comparison_operators()
    
    print("🎉 Детальное логирование применено успешно!")
    print("   Теперь все ошибки None comparison будут детально логироваться")

if __name__ == "__main__":
    apply_debug_none_comparison()
