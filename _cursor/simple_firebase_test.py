#!/usr/bin/env python3
"""
Простой тест Firebase соединений без инициализации Pyrogram
"""

import os
import sys
import time
import gc
from datetime import datetime

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_file_descriptors():
    """Получает количество файловых дескрипторов"""
    try:
        return len(os.listdir('/proc/self/fd'))
    except:
        return 0

def test_firebase_only():
    """Тестирует только Firebase соединения без Pyrogram"""
    try:
        # Импортируем только необходимые модули
        from CONFIG.config import Config
        from DATABASE.firebase_init import RestDBAdapter, _get_database_url
        
        print("🔍 Тестирование только Firebase соединений...")
        
        # Принудительная сборка мусора
        gc.collect()
        
        # Начальное количество файловых дескрипторов
        initial_fds = get_file_descriptors()
        print(f"📊 Начальное количество файловых дескрипторов: {initial_fds}")
        
        # Создаем Firebase соединение
        database_url = _get_database_url()
        api_key = getattr(Config, "FIREBASE_CONF", {}).get("apiKey")
        
        if not api_key:
            print("❌ FIREBASE_CONF.apiKey не найден")
            return False
            
        # Аутентификация
        import requests
        from requests import Session
        from requests.adapters import HTTPAdapter
        
        auth_session = Session()
        auth_session.headers.update({
            'User-Agent': 'tg-ytdlp-bot/1.0',
            'Connection': 'keep-alive'
        })
        
        auth_adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=3,
            pool_block=False
        )
        auth_session.mount('http://', auth_adapter)
        auth_session.mount('https://', auth_adapter)
        
        try:
            auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            resp = auth_session.post(auth_url, json={
                "email": getattr(Config, "FIREBASE_USER", None),
                "password": getattr(Config, "FIREBASE_PASSWORD", None),
                "returnSecureToken": True,
            }, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            id_token = payload.get("idToken")
            refresh_token = payload.get("refreshToken")
            
            if not id_token:
                print("❌ Не удалось получить idToken")
                return False
                
            print("✅ Аутентификация успешна")
            
        finally:
            auth_session.close()
        
        # Создаем Firebase адаптер
        db = RestDBAdapter(database_url, id_token, refresh_token, api_key, "/")
        
        # Выполняем тестовые операции
        for i in range(5):
            try:
                # Тест чтения
                result = db.child("bot").child("tgytdlp_bot").child("users").get()
                print(f"✅ Тест {i+1}: Чтение успешно")
                
                # Тест записи
                test_data = {"test": f"simple_test_{i}", "timestamp": int(time.time())}
                db.child("bot").child("tgytdlp_bot").child("simple_test").child(f"test_{i}").set(test_data)
                print(f"✅ Тест {i+1}: Запись успешно")
                
                time.sleep(0.2)
                
            except Exception as e:
                print(f"❌ Тест {i+1} failed: {e}")
        
        # Принудительная сборка мусора
        gc.collect()
        
        # Количество файловых дескрипторов после операций
        after_ops_fds = get_file_descriptors()
        print(f"📊 ФД после операций: {after_ops_fds}")
        print(f"📈 Разница: {after_ops_fds - initial_fds}")
        
        # Закрываем соединение
        db.close()
        print("✅ Firebase соединение закрыто")
        
        # Принудительная сборка мусора после закрытия
        gc.collect()
        time.sleep(1)
        
        # Финальное количество файловых дескрипторов
        final_fds = get_file_descriptors()
        print(f"📊 Финальное количество ФД: {final_fds}")
        print(f"📉 Утечка: {final_fds - initial_fds}")
        
        if final_fds - initial_fds <= 5:
            print("✅ Тест пройден: утечки в допустимых пределах")
            return True
        else:
            print("❌ Тест не пройден: значительная утечка")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Простой тест Firebase соединений")
    print("=" * 50)
    
    success = test_firebase_only()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Тест пройден успешно!")
    else:
        print("💥 Тест не пройден")
    
    print(f"⏰ Время завершения: {datetime.now()}")
