#!/usr/bin/env python3
"""
Скрипт для скачивания дампа Firebase Realtime Database
Запускайте этот скрипт раз в день для обновления локального кэша
"""

import json
import os
import sys
from datetime import datetime

# Добавляем родительскую директорию в путь для импорта ПЕРЕД импортом модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from HELPERS.logger import logger
except ImportError:
    # Fallback logger если HELPERS недоступен
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

try:
    from CONFIG.config import Config
except ImportError:
    print("❌ Не найден CONFIG/config.py или класс Config! Все параметры должны быть в CONFIG/config.py.")
    sys.exit(1)

try:
    import requests
    from requests import Session
    from requests.adapters import HTTPAdapter
    import firebase_admin
    from firebase_admin import credentials
except ImportError:
    requests = None
    Session = None
    HTTPAdapter = None
    firebase_admin = None
    credentials = None

# Все параметры берём из config.py
FIREBASE_CONFIG = getattr(Config, 'FIREBASE_CONF', None)
FIREBASE_USER = getattr(Config, 'FIREBASE_USER', None)
FIREBASE_PASSWORD = getattr(Config, 'FIREBASE_PASSWORD', None)
OUTPUT_FILE = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')

if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
    print("❌ Не все параметры заданы в config.py (FIREBASE_CONF, FIREBASE_USER, FIREBASE_PASSWORD)")
    sys.exit(1)

def download_firebase_dump():
    """Скачивает весь дамп Firebase Realtime Database"""
    if requests is None or Session is None:
        print("⚠️ Dependency not available: requests or Session")
        return False

    # Create session for connection pooling
    session = Session()
    session.headers.update({
        'User-Agent': 'tg-ytdlp-bot/1.0',
        'Connection': 'keep-alive'
    })
    
    # Configure connection pool to prevent too many open files
    adapter = HTTPAdapter(
        pool_connections=5,   # Number of connection pools to cache
        pool_maxsize=10,      # Maximum number of connections in each pool
        max_retries=3,        # Number of retries for failed requests
        pool_block=False      # Don't block when pool is full
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        print(f"🔄 Starting Firebase dump download at {datetime.now()}")

        database_url = FIREBASE_CONFIG.get("databaseURL")
        if not database_url:
            print("❌ FIREBASE_CONF.databaseURL не задан")
            return False

        # Для скачивания дампа используем REST API и custom token/ID token. 
        # Предпочтительно ID токен через REST signInWithPassword.
        key = FIREBASE_CONFIG.get("apiKey")
        if not key:
            print("❌ FIREBASE_CONF.apiKey не задан для получения idToken")
            return False

        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}"
        resp = session.post(auth_url, json={
            "email": FIREBASE_USER,
            "password": FIREBASE_PASSWORD,
            "returnSecureToken": True,
        }, timeout=60)
        resp.raise_for_status()
        id_token = resp.json()["idToken"]
        print("✅ Authentication successful")

        # Скачивание данных
        print("📥 Downloading database dump...")
        url = f"{database_url}/.json?auth={id_token}"
        response = session.get(url, timeout=300)
        response.raise_for_status()

        # Сохранение в файл
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)

        data = response.json()
        if data:
            total_keys = len(data)
            print("✅ Firebase database downloaded successfully!")
            print(f"📊 Total root nodes: {total_keys}")
            print(f"💾 Saved to: {OUTPUT_FILE}")
            print(f"📏 File size: {os.path.getsize(OUTPUT_FILE)} bytes")

            print("\n📋 Database structure:")
            for key in data.keys():
                if isinstance(data[key], dict):
                    sub_keys = len(data[key])
                    print(f"  - {key}: {sub_keys} sub-nodes")
                else:
                    print(f"  - {key}: {type(data[key]).__name__}")
        else:
            print("⚠️ Database is empty")

        return True

    except Exception as e:
        print(f"❌ Error downloading Firebase dump: {e}")
        return False
    finally:
        # Always close the session
        session.close()

def main():
    print("🚀 Firebase Database Dumper (config-driven)")
    print("=" * 40)
    
    # Проверяем конфиг
    if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
        print("❌ Не все параметры заданы в config.py (FIREBASE_CONF, FIREBASE_USER, FIREBASE_PASSWORD)")
        return False
    
    # Скачиваем дамп
    success = download_firebase_dump()
    
    if success:
        print(f"\n🎉 Firebase dump completed at {datetime.now()}")
        print("💡 You can now restart your bot to use the updated cache")
    else:
        print(f"\n💥 Firebase dump failed at {datetime.now()}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
