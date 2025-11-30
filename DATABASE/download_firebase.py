#!/usr/bin/env python3
"""
Script for downloading Firebase Realtime Database dump
Run this script once a day to update the local cache
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports BEFORE importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from HELPERS.logger import logger
    from CONFIG.messages import safe_get_messages
except ImportError:
    # Fallback logger if HELPERS is not available
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    # Fallback for messages
    class FallbackMessages:
        ALWAYS_ASK_DOWNLOADING_DATABASE_MSG = "📥 Downloading database dump..."
    def safe_get_messages(user_id):
        return FallbackMessages()

try:
    from CONFIG.config import Config
    from CONFIG.messages import Messages, safe_get_messages
except ImportError as e:
    print(f"Import error: {e}")
    print("Config not found")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    print("Check syntax")
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

# All parameters are taken from config.py
FIREBASE_CONFIG = getattr(Config, 'FIREBASE_CONF', None)
FIREBASE_USER = getattr(Config, 'FIREBASE_USER', None)
FIREBASE_PASSWORD = getattr(Config, 'FIREBASE_PASSWORD', None)
OUTPUT_FILE = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')

if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
    print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
    sys.exit(1)

def download_firebase_dump():
    messages = safe_get_messages(None)
    """Downloads the entire Firebase Realtime Database dump"""
    if requests is None or Session is None:
        print(safe_get_messages().DB_DEPENDENCY_NOT_AVAILABLE_MSG)
        return False

    # Create managed session for connection pooling
    from HELPERS.http_manager import get_managed_session
    session_manager = get_managed_session("firebase-download")
    session = session_manager.get_session()
    
    try:
        print(safe_get_messages().DB_STARTING_FIREBASE_DUMP_MSG.format(datetime=datetime.now()))

        database_url = FIREBASE_CONFIG.get("databaseURL")
        if not database_url:
            print(safe_get_messages().DB_DATABASE_URL_NOT_SET_MSG)
            return False

        # For downloading dump we use REST API and custom token/ID token.
        # Preferably ID token via REST signInWithPassword.
        key = FIREBASE_CONFIG.get("apiKey")
        if not key:
            print(safe_get_messages().DB_API_KEY_NOT_SET_MSG)
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

        # Downloading data
        print(safe_get_messages().ALWAYS_ASK_DOWNLOADING_DATABASE_MSG)
        url = f"{database_url}/.json?auth={id_token}"
        response = session.get(url, timeout=300)
        response.raise_for_status()

        # Saving to file without loading entire dump into memory
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for chunk in response.iter_content(chunk_size=1024 * 512, decode_unicode=True):
                if chunk:
                    f.write(chunk)

        data = None
        file_size = os.path.getsize(OUTPUT_FILE)
        if file_size <= 50 * 1024 * 1024:  # only parse stats for reasonably sized dumps
            try:
                with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as stats_err:
                logger.warning(f"Failed to parse Firebase dump for stats: {stats_err}")

        if data:
            total_keys = len(data)
            print("✅ Firebase database downloaded successfully!")
            print(f"📊 Total root nodes: {total_keys}")
            print(f"💾 Saved to: {OUTPUT_FILE}")
            print(f"📏 File size: {file_size} bytes")

            print("\n📋 Database structure:")
            for key in data.keys():
                if isinstance(data[key], dict):
                    sub_keys = len(data[key])
                    print(f"  - {key}: {sub_keys} sub-nodes")
                else:
                    print(f"  - {key}: {type(data[key]).__name__}")
        else:
            print(safe_get_messages().DB_DATABASE_EMPTY_MSG)
            print(f"💾 Saved to: {OUTPUT_FILE}")
            print(f"📏 File size: {file_size} bytes")

        return True

    except Exception as e:
        print(safe_get_messages().DB_ERROR_DOWNLOADING_DUMP_MSG.format(error=e))
        return False
    finally:
        # Always close the managed session
        session_manager.close()

def main():
    messages = safe_get_messages(None)
    print("🚀 Firebase Database Dumper (config-driven)")
    print("=" * 40)
    
    # Check config
    if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
        print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
        return False
    
    # Download dump
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
