# Version 3.1.0 # save firebase-cache localy to prevent exceeding no-cost limits on google firebase
import glob
from sdnotify import SystemdNotifier
from datetime import datetime, timedelta
import hashlib
import io
import json
import logging
import math
import os
import re
import requests
import shutil
import subprocess
import random
import sys
import threading
import time
from datetime import datetime
from PIL import Image
from types import SimpleNamespace
from typing import Tuple
from urllib.parse import urlparse, parse_qs, urlunparse, unquote, urlencode
import traceback
import pyrebase
import tldextract
# from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pyrogram import Client, filters
from pyrogram import enums
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyParameters
)
from yt_dlp import YoutubeDL
import yt_dlp

from config import Config

import chardet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

notifier = SystemdNotifier()

def watchdog_loop():
    while True:
        notifier.notify("WATCHDOG=1")
        logger.info("[Watchdog] Sent WATCHDOG=1")
        time.sleep(30)  # Frequency is less than WatchdogSec

# Start watchdog thread
threading.Thread(target=watchdog_loop, daemon=True).start()

# At the beginning of initialization
notifier.notify("READY=1")
logger.info("[Watchdog] Sent READY=1")

# Global variable for local cache Firebase
firebase_cache = {}

# Global variable to monitor the state of automatic loading cache
auto_cache_enabled = getattr(Config, 'AUTO_CACHE_RELOAD_ENABLED', True)
auto_cache_thread = None

def load_firebase_cache():
    """Load local Firebase cache from JSON file."""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            print(f"✅ Firebase cache loaded: {len(firebase_cache)} root nodes")
        else:
            print(f"⚠️ Firebase cache file not found, starting with empty cache: {cache_file}")
            firebase_cache = {}
    except Exception as e:
        print(f"❌ Failed to load firebase cache: {e}")
        firebase_cache = {}

def reload_firebase_cache():
    """Reloading the local Firebase cache from JSON file"""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            print(f"✅ Firebase cache reloaded: {len(firebase_cache)} root nodes")
            return True
        else:
            print(f"⚠️ Firebase cache file not found: {cache_file}")
            return False
    except Exception as e:
        print(f"❌ Failed to reload firebase cache: {e}")
        return False


def get_next_reload_time(interval_hours: int) -> datetime:
    """
    Returns Datetime the following reloading point,
    aligned according to the N-hour step from 00:00.
    """
    now = datetime.now()
    # Today's border is “midnight”
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    interval_seconds = interval_hours * 3600
    # How many full intervals have already passed since midnight
    intervals_passed = int(seconds_since_midnight // interval_seconds)
    # Next = midnight + (intervals_passed + 1) * step
    return midnight + timedelta(seconds=(intervals_passed + 1) * interval_seconds)

def auto_reload_firebase_cache():
    """A stream that every n clock restarts a local cache."""
    global auto_cache_enabled

    interval_hours = getattr(Config, 'RELOAD_CACHE_EVERY', 4)
    while auto_cache_enabled:
        next_exec = get_next_reload_time(interval_hours)
        now = datetime.now()
        wait_seconds = (next_exec - now).total_seconds()
        print(
            f"⏳ Waiting until {next_exec.strftime('%Y-%m-%d %H:%M:%S')} "
            f"to reload Firebase cache ({wait_seconds/3600:.2f} hours)"
        )
        # "Smart" Sleep
        end_time = time.time() + wait_seconds
        while auto_cache_enabled and time.time() < end_time:
            time.sleep(min(1, end_time - time.time()))
        if not auto_cache_enabled:
            print("🛑 Auto Firebase cache reloader stopped by admin")
            return
        # Run the reboot
        try:
            user_id = (
                Config.ADMIN[0]
                if isinstance(Config.ADMIN, (list, tuple))
                else Config.ADMIN
            )
            print(f"🔄 Triggering /reload_cache as admin (user_id={user_id})")
            msg = fake_message("/reload_cache", user_id)
            reload_firebase_cache_command(app, msg)
        except Exception as e:
            print(f"❌ Error running auto reload_cache: {e}")
            import traceback; traceback.print_exc()

def start_auto_cache_reloader():
    """The flow of auto -outload starts."""
    global auto_cache_thread, auto_cache_enabled
    if auto_cache_enabled and auto_cache_thread is None:
        auto_cache_thread = threading.Thread(
            target=auto_reload_firebase_cache,
            daemon=True
        )
        auto_cache_thread.start()
        print(
            f"🚀 Auto Firebase cache reloader started "
            f"(every {getattr(Config, 'RELOAD_CACHE_EVERY', 4)}h from 00:00)"
        )
    return auto_cache_thread

def stop_auto_cache_reloader():
    """Stops the flow of auto -transshipment."""
    global auto_cache_enabled, auto_cache_thread
    auto_cache_enabled = False
    if auto_cache_thread and auto_cache_thread.is_alive():
        print("🛑 Auto Firebase cache reloader stopped")
    auto_cache_thread = None

def toggle_auto_cache_reloader():
    """Switchs the transload mode."""
    global auto_cache_enabled
    auto_cache_enabled = not auto_cache_enabled
    if auto_cache_enabled:
        start_auto_cache_reloader()
    else:
        stop_auto_cache_reloader()
    return auto_cache_enabled

# We load the cache when importing module
load_firebase_cache()

def get_from_local_cache(path_parts):
    """
    Receives data from a local cache along the way, divided into parts
    For example: get_from_local_cache (['Bot', 'Video_cache', 'Hash123', '720p'])
    """
    global firebase_cache
    current = firebase_cache
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            log_firebase_access_attempt(path_parts, success=False)
            return None
    
    log_firebase_access_attempt(path_parts, success=True)
    return current

def log_firebase_access_attempt(path_parts, success=True):
    """
    Logs attempts to turn to a local cache (to track the remaining .get () calls)
    """
    # Show the path in JSON format for local cache
    path_str = ' -> '.join(path_parts)  # For example: "bot -> video_cache -> playlists -> url_hash -> quality"
    status = "SUCCESS" if success else "MISS"
    print(f"🔥 Firebase access attempt: {path_str} -> {status}")

def ensure_utf8_srt(srt_path):
    """
    The ultimatum function for correcting any encodings and cracked.
    Forcibly transcodes the file in the UTF-8, trying all possible encodings.
    """
    import chardet
    
    if not os.path.isfile(srt_path):
        logger.error(f"File {srt_path} does not exist!")
        return None
    if os.path.getsize(srt_path) == 0:
        logger.error(f"File {srt_path} is empty!")
        return None

    # We read raw bytes
    with open(srt_path, 'rb') as f:
        raw = f.read()
        if not raw:
            logger.error(f"File {srt_path} is empty (raw)!")
            return None

    # Determine the encoding through Chardet
    result = chardet.detect(raw)
    detected_encoding = result['encoding'] or 'utf-8'
    confidence = result.get('confidence', 0)
    logger.info(f"File encoding detected {srt_path}: {detected_encoding} (confidence: {confidence:.2f})")

    # List of coding for forced testing (in priority)
    encodings_to_try = [
        'utf-8',
        'utf-8-sig',  # UTF-8 с BOM
        'cp1256',     # Arabic Windows
        'iso-8859-6', # Arabic ISO
        'cp1252',     # Western European
        'iso-8859-1', # Latin-1
        'cp1250',     # Central European
        'cp1251',     # Cyrillic
        'cp874',      # Thai
        'tis-620',    # Thai
        'big5',       # Traditional Chinese
        'gbk',        # Simplified Chinese
        'shift_jis',  # Japanese
        'euc-kr',     # Korean
        'utf-16',
        'utf-16le',
        'utf-16be',
    ]

    # Add the detected encoding to the beginning of the list
    if detected_encoding.lower() not in [enc.lower() for enc in encodings_to_try]:
        encodings_to_try.insert(0, detected_encoding)

    # We try to decode with each encoding
    decoded_text = None
    successful_encoding = None
    
    for encoding in encodings_to_try:
        try:
            decoded_text = raw.decode(encoding)
            successful_encoding = encoding
            logger.info(f"Successfully decoded with encoding: {encoding}")
            break
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"Failed to decode with {encoding}: {e}")
            continue

    # If no encoding has worked, we use Force Decode
    if decoded_text is None:
        logger.warning("All encodings did not work, I use force decode")
        decoded_text = raw.decode('utf-8', errors='replace')
        successful_encoding = 'utf-8 (force)'

    # We check if there are spray bars in the text (replacement symbols)
    if '' in decoded_text or '?' in decoded_text:
        logger.warning(f"Replacement characters found in text, encoding {successful_encoding} may be incorrect")
        
        # We try again with other encodings, ignoring the already tried
        for encoding in ['cp1256', 'iso-8859-6', 'cp1252', 'utf-8-sig']:
            if encoding not in [enc.lower() for enc in encodings_to_try[:len(encodings_to_try)//2]]:
                try:
                    test_text = raw.decode(encoding)
                    if '' not in test_text and '?' not in test_text:
                        decoded_text = test_text
                        successful_encoding = encoding
                        logger.info(f"The best encoding has been found: {encoding}")
                        break
                except:
                    continue

    # Record the result in UTF-8
    try:
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        logger.info(f"File {srt_path} successfully encoded to UTF-8 (original encoding: {successful_encoding})")
        return srt_path
    except Exception as e:
        logger.error(f"Error writing file {srt_path}: {e}")
        return None

# Dictionary of languages with their emoji flags and native names
LANGUAGES = {
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "be": {"flag": "🇧🇾", "name": "Беларуская"},
    "bg": {"flag": "🇧🇬", "name": "Български"},
    "bn": {"flag": "🇧🇩", "name": "বাংলা"},
    "cs": {"flag": "🇨🇿", "name": "Čeština"},
    "da": {"flag": "🇩🇰", "name": "Dansk"},
    "de": {"flag": "🇩🇪", "name": "Deutsch"},
    "el": {"flag": "🇬🇷", "name": "Ελληνικά"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "en-US": {"flag": "🇺🇸", "name": "English (US)"},
    "en-GB": {"flag": "🇬🇧", "name": "English (UK)"},
    "es": {"flag": "🇪🇸", "name": "Español"},
    "es-419": {"flag": "🇲🇽", "name": "Español (Latinoamérica)"},
    "et": {"flag": "🇪🇪", "name": "Eesti"},
    "fa": {"flag": "🇮🇷", "name": "فارسی"},
    "fi": {"flag": "🇫🇮", "name": "Suomi"},
    "fr": {"flag": "🇫🇷", "name": "Français"},
    "he": {"flag": "🇮🇱", "name": "עברית"},
    "hi": {"flag": "🇮🇳", "name": "हिन्दी"},
    "hr": {"flag": "🇭🇷", "name": "Hrvatski"},
    "hu": {"flag": "🇭🇺", "name": "Magyar"},
    "hy": {"flag": "🇦🇲", "name": "Հայերեն"},
    "id": {"flag": "🇮🇩", "name": "Bahasa Indonesia"},
    "it": {"flag": "🇮🇹", "name": "Italiano"},
    "ja": {"flag": "🇯🇵", "name": "日本語"},
    "kk": {"flag": "🇰🇿", "name": "Қазақ тілі"},
    "ko": {"flag": "🇰🇷", "name": "한국어"},
    "lt": {"flag": "🇱🇹", "name": "Lietuvių"},
    "lv": {"flag": "🇱🇻", "name": "Latviešu"},
    "nl": {"flag": "🇳🇱", "name": "Nederlands"},
    "no": {"flag": "🇳🇴", "name": "Norsk"},
    "pl": {"flag": "🇵🇱", "name": "Polski"},
    "pt": {"flag": "🇵🇹", "name": "Português"},
    "pt-BR": {"flag": "🇧🇷", "name": "Português (Brasil)"},
    "ro": {"flag": "🇷🇴", "name": "Română"},
    "ru": {"flag": "🇷🇺", "name": "Русский"},
    "sk": {"flag": "🇸🇰", "name": "Slovenčina"},
    "sl": {"flag": "🇸🇮", "name": "Slovenščina"},
    "sr": {"flag": "🇷🇸", "name": "Српски"},
    "sv": {"flag": "🇸🇪", "name": "Svenska"},
    "th": {"flag": "🇹🇭", "name": "ไทย"},
    "tr": {"flag": "🇹🇷", "name": "Türkçe"},
    "uk": {"flag": "🇺🇦", "name": "Українська"},
    "vi": {"flag": "🇻🇳", "name": "Tiếng Việt"},
    "zh": {"flag": "🇨🇳", "name": "中文"},
    "zh-Hans": {"flag": "🇨🇳", "name": "中文(简体)"},
    "zh-Hant": {"flag": "🇹🇼", "name": "中文(繁體)"}
}

ITEMS_PER_PAGE = 10  # Number of languages per page

def get_user_subs_language(user_id):
    """Get user's preferred subtitle language"""
    user_dir = os.path.join("users", str(user_id))
    subs_file = os.path.join(user_dir, "subs.txt")
    if os.path.exists(subs_file):
        with open(subs_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def is_subs_enabled(user_id):
    lang = get_user_subs_language(user_id)
    return lang is not None and lang != "OFF"

def save_user_subs_language(user_id, lang_code):
    """Save user's subtitle language preference"""
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    subs_file = os.path.join(user_dir, "subs.txt")
    if lang_code in ["OFF", None]:
        if os.path.exists(subs_file):
            os.remove(subs_file)
        subs_auto_file = os.path.join(user_dir, "subs_auto.txt")
        if os.path.exists(subs_auto_file):
            os.remove(subs_auto_file)
        clear_subs_check_cache()
    else:
        with open(subs_file, "w", encoding="utf-8") as f:
            f.write(lang_code)
    clear_subs_check_cache()

def get_user_subs_auto_mode(user_id):
    """Get user's AUTO mode setting for subtitles"""
    user_dir = os.path.join("users", str(user_id))
    auto_file = os.path.join(user_dir, "subs_auto.txt")
    if os.path.exists(auto_file):
        with open(auto_file, "r", encoding="utf-8") as f:
            return f.read().strip() == "ON"
    return False

def save_user_subs_auto_mode(user_id, auto_enabled):
    """Save user's AUTO mode setting for subtitles"""
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    auto_file = os.path.join(user_dir, "subs_auto.txt")
    if auto_enabled:
        with open(auto_file, "w", encoding="utf-8") as f:
            f.write("ON")
    else:
        if os.path.exists(auto_file):
            os.remove(auto_file)
    clear_subs_check_cache()


def get_available_subs_languages(url, user_id=None, auto_only=False):
    """Returns a list of available languages of subtitles. Circrats 429 and 'Requested Format ...'."""
    # import os, random, time, yt_dlp

    MAX_RETRIES = 1
    def backoff(i):  # short, because the listing itself usually does not meet the limits
        return (3, 5, 10)[min(i, 2)] + random.uniform(0, 2)

    def extract_info_with_cookies():
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'format': 'best',
            'ignore_no_formats_error': True,
            'sleep-requests': 2,
            'min_sleep_interval': 1,
            'max_sleep_interval': 3,
            'retries': 6,
            'extractor_retries': 3,
        }
        # cookies
        if user_id:
            cf = os.path.join("users", str(user_id), "cookie.txt")
            if os.path.exists(cf):
                base_opts['cookiefile'] = cf
        elif hasattr(Config, "COOKIE_FILE_PATH") and os.path.exists(Config.COOKIE_FILE_PATH):
            base_opts['cookiefile'] = Config.COOKIE_FILE_PATH

        last_info, used_client = {}, None
        for client in ('web', 'android', 'tv', None):
            opts = dict(base_opts)
            if client:
                opts['extractor_args'] = {'youtube': {'player_client': [client]}}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as e:
                if 'Requested format is not available' in str(e):
                    continue
                raise
            if info.get('subtitles') or info.get('automatic_captions'):
                used_client = client or 'default'
                logger.info(f"youtube player_client={used_client} returned captions")
                _subs_check_cache[f"{url}_{user_id}_client"] = used_client
                return info
            logger.info(f"player_client={client or 'default'} has no captions, trying next...")
            last_info = info
        _subs_check_cache[f"{url}_{user_id}_client"] = used_client or 'default'
        return last_info

    for attempt in range(MAX_RETRIES):
        try:
            info = extract_info_with_cookies()
            normal = list(info.get('subtitles', {}).keys())
            auto   = list(info.get('automatic_captions', {}).keys())
            result = list(set(auto if auto_only else normal))
            logger.info(f"get_available_subs_languages: auto_only={auto_only}, result={result}")
            return result

        except yt_dlp.utils.DownloadError as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                delay = backoff(attempt)
                logger.warning(f"429 Too Many Requests (attempt {attempt+1}/{MAX_RETRIES}) sleep {delay:.1f}s")
                time.sleep(delay)
                continue
            logger.error(f"DownloadError while getting subtitles: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error getting subtitles: {e}")
            break

    return []


def force_fix_arabic_encoding(srt_path: str, lang: str | None = None):
    """Forced transcoding Arab/Pers/Urdu/Hebrew Sabov in UTF-8."""
    target_langs = {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}
    if lang is not None and lang not in target_langs:
        return srt_path
    if not os.path.exists(srt_path):
        return None

    try:
        with open(srt_path, 'rb') as f:
            raw = f.read()

        encodings = ['utf-8-sig', 'utf-8', 'cp1256', 'windows-1256', 'iso-8859-6', 'cp720', 'mac-arabic']
        best_text, best_enc, min_bad = None, None, float('inf')

        for enc in encodings:
            try:
                text = raw.decode(enc, errors='replace')
            except Exception:
                continue
            bad = text.count('?')  # simple heuristics
            if bad < min_bad:
                min_bad = bad
                best_text = text
                best_enc = enc

        if best_text is None:
            best_text = raw.decode('utf-8', errors='replace')
            best_enc  = 'utf-8(force)'

        best_text = best_text.replace('\r\n', '\n').replace('\r', '\n').replace('\ufeff', '')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(best_text)

        logger.info(f"force_fix_arabic_encoding: {srt_path} re-encoded from {best_enc} -> utf-8")
        return srt_path
    except Exception as e:
        logger.error(f"force_fix_arabic_encoding error {srt_path}: {e}")
        return None


def _clean_srt_text(text: str) -> str:
    # We remove Word-Level Tags
    text = re.sub(r'<\d{2}:\d{2}:\d{2}[.,]\d{3}>', '', text)
    text = re.sub(r'</?c[^>]*>', '', text)

    # We clean the webvt parameters in the timing line
    def _strip_settings(m):
        return m.group(1)
    text = re.sub(
        r'(^\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{1,3})(.*)$',
        _strip_settings,
        text,
        flags=re.MULTILINE
    )

    text = text.replace('\ufeff', '')
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # remove duplicate blocks
    blocks, cur = [], []
    for line in text.splitlines():
        if line.strip().isdigit() and not cur:
            cur = [line]
        elif line.strip() == '' and cur:
            blocks.append('\n'.join(cur))
            cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append('\n'.join(cur))

    cleaned, prev = [], ''
    for b in blocks:
        parts = b.split('\n', 2)
        if len(parts) < 3:
            cleaned.append(b)
            continue
        idx, timing, payload = parts[0], parts[1], parts[2]
        payload_stripped = payload.strip()
        if payload_stripped == prev:
            continue
        prev = payload_stripped
        cleaned.append('\n'.join([idx, timing, payload_stripped, '']))

    return '\n'.join(cleaned).strip() + '\n'


def _convert_vtt_to_srt(path: str) -> str:
    """VTT -> SRT (+ clean)."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
        if 'WEBVTT' not in raw:
            return path

        raw = raw.replace('\r', '')
        body = raw.split('WEBVTT', 1)[-1].strip()
        cues = re.split(r'\n\s*\n', body)

        out, idx = [], 1
        for cue in cues:
            if '-->' not in cue:
                continue
            lines = cue.splitlines()
            tc_line = next((l for l in lines if '-->' in l), None)
            if not tc_line:
                continue
            timing = re.sub(r'(\d{2}:\d{2}:\d{2})\.(\d{3})', r'\1,\2', tc_line)
            timing = re.sub(r'(-->.*?)(\s+.*)$', r'\1', timing)
            payload = '\n'.join(lines[lines.index(tc_line)+1:]).strip()
            if not payload:
                continue
            out += [str(idx), timing, payload, '']
            idx += 1

        srt_txt = _clean_srt_text('\n'.join(out))
        new_path = os.path.splitext(path)[0] + '.srt'
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(srt_txt)
        os.remove(path)
        return new_path
    except Exception as e:
        logger.warning(f"VTT->SRT convert fail: {e}")
        return path


def _convert_json3_srv3_to_srt(path: str) -> str:
    """YouTube JSON3/SRV3 conversion in SRT (minimally sufficient)."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()

        # json3
        try:
            data = json.loads(raw)
        except Exception:
            data = None

        lines = []
        idx = 1

        def ms2ts(ms: int) -> str:
            h = ms // 3600000
            ms %= 3600000
            m = ms // 60000
            ms %= 60000
            s = ms // 1000
            ms %= 1000
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        if isinstance(data, dict) and 'events' in data:
            for ev in data['events']:
                if not ev.get('segs'):
                    continue
                txt = ''.join(seg.get('utf8', '') for seg in ev['segs']).strip()
                if not txt:
                    continue
                start = int(ev.get('tStartMs', 0))
                dur   = int(ev.get('dDurationMs', 0))
                end   = start + dur
                lines += [str(idx), f"{ms2ts(start)} --> {ms2ts(end)}", txt, '']
                idx += 1
        else:
            # srv3 (xml-like)
            # <p t="12345" d="678">text</p>
            for m in re.finditer(r'<p[^>]*t="(\d+)"[^>]*d="(\d+)"[^>]*>(.*?)</p>', raw, flags=re.S):
                start = int(m.group(1))
                dur   = int(m.group(2))
                end   = start + dur
                text = re.sub(r'<[^>]+>', '', m.group(3))
                text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()
                if not text:
                    continue
                lines += [str(idx), f"{ms2ts(start)} --> {ms2ts(end)}", text, '']
                idx += 1

        if not lines:
            return path  # couldn't make out anything

        srt_txt = _clean_srt_text('\n'.join(lines))
        new_path = os.path.splitext(path)[0] + '.srt'
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(srt_txt)
        os.remove(path)
        return new_path
    except Exception as e:
        logger.warning(f"json3/srv3 -> SRT convert fail: {e}")
        return path


def download_subtitles_ytdlp(url, user_id, video_dir, available_langs):
    """
    One income Info, select 1 track. For URL with auto transmission (tlang =)
    We do not sort out the FMT so as not to catch 429. Json3/SRV3 convertibly locally.
    """
    MAX_RETRIES = 1
    RTL_CJK = {'ar', 'fa', 'ur', 'ps', 'iw', 'he', 'zh', 'zh-Hans', 'zh-Hant', 'ja', 'ko'}

    def _rand_jitter(base, spread=2.5):
        return base + random.uniform(0, spread)

    def _has_srt_timestamps(txt: str) -> bool:
        return re.search(r"\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}", txt) is not None

    UNICODE_RANGES = {
        'ar': r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
        'fa': r'[\u0600-\u06FF]',
        'ur': r'[\u0600-\u06FF]',
        'iw': r'[\u0590-\u05FF]',
        'he': r'[\u0590-\u05FF]',
        'zh': r'[\u4E00-\u9FFF\u3400-\u4DBF]',
        'ja': r'[\u3040-\u30FF\u31F0-\u31FF\uFF66-\uFF9D\u4E00-\u9FFF]',
        'ko': r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]',
    }
    ALPHABETS = {
        'ru': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
        'en': 'abcdefghijklmnopqrstuvwxyz',
        'es': 'abcdefghijklmnopqrstuvwxyzñáéíóúü',
        'fr': 'abcdefghijklmnopqrstuvwxyzàâäéèêëïîôöùûüÿç',
        'de': 'abcdefghijklmnopqrstuvwxyzäöüß',
        'it': 'abcdefghijklmnopqrstuvwxyzàèéìíîòóù',
        'pt': 'abcdefghijklmnopqrstuvwxyzàáâãçéêíóôõú',
        'el': 'αβγδεζηθικλμνξοπρστυφχψωΆΈΉΊΌΎΏϊϋΐΰόώήέά',  # Greek 
    }

    def _check_lang_text(lang: str, text: str) -> bool:
        if len(text) < 120:
            return False
        if lang in RTL_CJK:
            pat = UNICODE_RANGES.get(lang)
            return re.search(pat, text) is not None if pat else True
        if lang in ALPHABETS:
            alpha = ALPHABETS[lang]
            return any(ch.lower() in alpha for ch in text if ch.isalpha())
        return any(ord(ch) > 127 for ch in text if ch.isalpha())

    def _download_once(url_tt: str, dst_path: str, retries: int = 2) -> bool:
        global _LAST_TIMEDTEXT_TS
        sess = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/",
            "Origin":  "https://www.youtube.com",
        }
        for i in range(retries):
            # Simple global Trottling
            delta = time.time() - _LAST_TIMEDTEXT_TS
            if delta < 1.5:
                time.sleep(1.5 - delta)

            r = sess.get(url_tt, headers=headers, timeout=25)
            _LAST_TIMEDTEXT_TS = time.time()

            if r.status_code == 200 and r.content:
                with open(dst_path, "wb") as f:
                    f.write(r.content)
                return True

            if r.status_code == 429:
                logger.warning(f"timedtext 429 ({url_tt}), sleep a bit")
                time.sleep(_rand_jitter(12, 6))
                continue

            logger.error(f"timedtext HTTP {r.status_code} ({url_tt})")
            time.sleep(_rand_jitter(4))
        return False

    for attempt in range(MAX_RETRIES):
        try:
            subs_lang = get_user_subs_language(user_id)
            auto_mode = get_user_subs_auto_mode(user_id)
            if not subs_lang or subs_lang == "OFF":
                return None
            if not available_langs:
                logger.info(f"No subtitles available for {subs_lang}")
                return None

            found_lang = lang_match(subs_lang, available_langs)
            if not found_lang:
                logger.info(f"Language {subs_lang} not found in {available_langs}")
                return None

            client = _subs_check_cache.get(f"{url}_{user_id}_client", 'tv')

            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': True,
                'format': 'best',
                'ignore_no_formats_error': True,
                'sleep-requests': 2,
                'min_sleep_interval': 1,
                'max_sleep_interval': 3,
                'retries': 6,
                'extractor_retries': 3,
                'extractor_args': {'youtube': {'player_client': [client]}},
            }
            # cookies
            user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
            if os.path.exists(user_cookie_path):
                info_opts['cookiefile'] = user_cookie_path
            elif hasattr(Config, "COOKIE_FILE_PATH") and os.path.exists(Config.COOKIE_FILE_PATH):
                info_opts['cookiefile'] = Config.COOKIE_FILE_PATH

            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            subs_key = 'automatic_captions' if auto_mode else 'subtitles'
            subs_dict = info.get(subs_key, {})
            tracks = subs_dict.get(found_lang) or []
            if not tracks:
                alt = next((k for k in subs_dict if k.startswith(found_lang)), None)
                tracks = subs_dict.get(alt, []) if alt else []

            if not tracks:
                logger.error("No track URL found in info for selected language")
                return None

            # priority
            preferred = ('srt', 'vtt', 'ttml', 'json3', 'srv3')
            track = min(
                tracks,
                key=lambda t: preferred.index((t.get('ext') or '').lower())
                if (t.get('ext') or '').lower() in preferred else 999
            )

            ext = (track.get('ext') or 'txt').lower()
            track_url = track.get('url', '')
            # If the auto transmission (there is tlang =) - do not touch the FMT, make exactly one request
            is_translated = 'tlang=' in track_url

            base_name = f"{info.get('title','video')[:50]}.{found_lang}.{ext}"
            dst = os.path.join(video_dir, base_name)

            ok = False
            if is_translated:
                ok = _download_once(track_url, dst, retries=2)
            else:
                # You can try VTT first
                urls_try = [track_url]
                if 'fmt=' not in track_url and ext not in ('vtt', 'srt', 'ttml'):
                    # Add one FMT = VTT
                    q = '&' if '?' in track_url else '?'
                    urls_try.append(track_url + q + 'fmt=vtt')
                # We take it in turn
                for u in urls_try:
                    if _download_once(u, dst, retries=2):
                        ok = True
                        break

            if not ok or os.path.getsize(dst) < 200:
                try: os.remove(dst)
                except Exception: pass
                logger.warning("Could not download/too small -> None")
                return None

            # envelope
            if ext == 'vtt':
                dst = _convert_vtt_to_srt(dst)
            elif ext in ('json3', 'srv3'):
                dst = _convert_json3_srv3_to_srt(dst)

            with open(dst, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            cleaned = _clean_srt_text(content)
            if cleaned != content:
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(cleaned)
                content = cleaned

            ok_ts = _has_srt_timestamps(content)
            ok_lang = True
            if subs_lang in RTL_CJK or subs_lang == 'el':  # we'll check Greek too
                ok_lang = _check_lang_text(subs_lang, content)

            if ok_ts and ok_lang:
                if subs_lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
                    force_fix_arabic_encoding(dst, subs_lang)
                logger.info(f"Valid subtitles ({subs_lang}), size={os.path.getsize(dst)}")
                return dst

            logger.warning("Downloaded track invalid after clean/convert")
            try: os.remove(dst)
            except Exception: pass
            return None

        except yt_dlp.utils.DownloadError as e:
            if "429" in str(e):
                logger.warning(f"429 Too Many Requests (attempt {attempt+1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(_rand_jitter(25 * (attempt + 1)))
                    continue
                logger.error("Final attempt failed due to 429")
                return None
            logger.error(f"DownloadError: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(_rand_jitter(10))
                continue
            return None

    return None


def download_subtitles_only(app, message, url, tags, available_langs, playlist_name=None, video_count=1, video_start_with=1):
    """
    Downloads and sends only a subtitle file without a video
    """
    user_id = message.chat.id
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    
    try:
        # Check if subtitles are enabled
        subs_lang = get_user_subs_language(user_id)
        if not subs_lang or subs_lang == "OFF":
            app.send_message(user_id, "❌ Subtitles are disabled. Use /subs to configure.")
            return
        
        # Check if this is YouTube
        if not is_youtube_url(url):
            app.send_message(user_id, "❌ Subtitle downloading is only supported for YouTube.")
            return
        
        # Check subtitle availability
        auto_mode = get_user_subs_auto_mode(user_id)
        
        # Clean the cache before checking to avoid caching problems
        # clear_subs_check_cache()
        
        # found_type = check_subs_availability(url, user_id, return_type=True)
        # need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
        
        # if not need_subs:
            # app.send_message(user_id, "❌ Subtitles for selected language not found.")
            # return
        
        # Send message about download start
        status_msg = app.send_message(user_id, "💬 Downloading subtitles...", reply_to_message_id=message.id)
        
        # Download subtitles
        subs_path = download_subtitles_ytdlp(url, user_id, user_dir, available_langs)
        
        if subs_path and os.path.exists(subs_path):
            # Process subtitle file
            subs_path = ensure_utf8_srt(subs_path)
            if subs_path and subs_lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
                subs_path = force_fix_arabic_encoding(subs_path, subs_lang)
            
            if subs_path and os.path.exists(subs_path) and os.path.getsize(subs_path) > 0:
                # Get video information for caption
                try:
                    info = get_video_formats(url, user_id)
                    title = info.get('title', 'Video')
                except:
                    title = "Video"
                
                # Form caption
                caption = f"<b>💬 Subtitles</b>\n\n"
                caption += f"<b>Video:</b> {title}\n"
                caption += f"<b>Language:</b> {subs_lang}\n"
                caption += f"<b>Type:</b> {'Auto-generated' if auto_mode else 'Manual'}\n"
                
                if tags:
                    caption += f"\n<b>Tags:</b> {' '.join(tags)}"
                
                # Send subtitle file
                sent_msg = app.send_document(
                    chat_id=user_id,
                    document=subs_path,
                    caption=caption,
                    reply_to_message_id=message.id,
                    parse_mode=enums.ParseMode.HTML
                )
                # We send this message to the log channel
                safe_forward_messages(Config.LOGS_ID, user_id, [sent_msg.id])
                send_to_logger(message, "💬 Subtitles SRT-file sent to user.")
                # Remove temporary file
                try:
                    os.remove(subs_path)
                except Exception as e:
                    logger.error(f"Error deleting temporary subtitle file: {e}")
                
                # Delete status message
                try:
                    app.delete_messages(user_id, status_msg.id)
                except:
                    pass
            else:
                app.edit_message_text(user_id, status_msg.id, "❌ Error processing subtitle file.")
        else:
            app.edit_message_text(user_id, status_msg.id, "❌ Failed to download subtitles.")
            
    except Exception as e:
        logger.error(f"Error downloading subtitles: {e}")
        try:
            app.edit_message_text(user_id, status_msg.id, f"❌ Error: {str(e)}")
        except:
            app.send_message(user_id, f"❌ Error downloading subtitles: {str(e)}")


def get_language_keyboard(page=0, user_id=None):
    """Generate keyboard with language buttons in 3 columns"""
    keyboard = []
    LANGS_PER_ROW = 3
    ROWS_PER_PAGE = 5  # eg 5 lines of 3 = 15 languages per page

    # We get all languages
    all_langs = list(LANGUAGES.items())
    total_languages = len(all_langs)
    total_pages = math.ceil(total_languages / (LANGS_PER_ROW * ROWS_PER_PAGE))

    # Cut for the current page
    start_idx = page * LANGS_PER_ROW * ROWS_PER_PAGE
    end_idx = start_idx + LANGS_PER_ROW * ROWS_PER_PAGE
    current_page_langs = all_langs[start_idx:end_idx]

    # Current language and auto-mode
    current_lang = get_user_subs_language(user_id) if user_id else None
    auto_mode = get_user_subs_auto_mode(user_id) if user_id else False

    # Form buttons 3 in a row
    for i in range(0, len(current_page_langs), LANGS_PER_ROW):
        row = []
        for j in range(LANGS_PER_ROW):
            if i + j < len(current_page_langs):
                lang_code, lang_info = current_page_langs[i + j]
                checkmark = "✅ " if lang_code == current_lang else ""
                button_text = f"{checkmark}{lang_info['flag']} {lang_info['name']}"
                row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"subs_lang|{lang_code}"
                ))
        keyboard.append(row)

    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"subs_page|{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"subs_page|{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # Specialist. Options
    auto_emoji = "✅" if auto_mode else "☑️"
    keyboard.append([
        InlineKeyboardButton("🚫 OFF", callback_data="subs_lang|OFF"),
        InlineKeyboardButton(f"{auto_emoji} AUTO-GEN", callback_data=f"subs_auto|toggle|{page}")
    ])
    # Close button
    keyboard.append([
        InlineKeyboardButton("🔚 Close", callback_data="subs_lang_close|close")
    ])

    return InlineKeyboardMarkup(keyboard)



# --- Function for permanent reply-keyboard ---
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["/clean", "/download_cookie"],
            ["/playlist", "/settings", "/help"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


# eternal reply-keyboard and reliable work with files
reply_keyboard_msg_ids = {}  # user_id: message_id


def send_reply_keyboard_always(user_id):
    global reply_keyboard_msg_ids
    try:
        msg_id = reply_keyboard_msg_ids.get(user_id)
        if msg_id:
            try:
                app.edit_message_text(user_id, msg_id, "\u2063", reply_markup=get_main_reply_keyboard())
                return
            except Exception as e:
                # Log only if the error is not MESSAGE_ID_INVALID
                if 'MESSAGE_ID_INVALID' not in str(e):
                    logger.warning(f"Failed to edit persistent reply keyboard: {e}")
                # If it didn't work, we delete the id to avoid getting stuck
                reply_keyboard_msg_ids.pop(user_id, None)
        # Always after failure or if there is no id - send a new one
        msg = app.send_message(user_id, "\u2063", reply_markup=get_main_reply_keyboard())
        # If there was another service msg_id (and it is not equal to the new one), we try to delete the old message
        if msg_id and msg_id != msg.id:
            try:
                app.delete_messages(user_id, [msg_id])
            except Exception as e:
                logger.warning(f"Failed to delete old reply keyboard message: {e}")
        reply_keyboard_msg_ids[user_id] = msg.id
    except Exception as e:
        logger.warning(f"Failed to send persistent reply keyboard: {e}")


# --- Wrapper for any custom action ---
def reply_with_keyboard(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # Determine user_id from arguments (Pyrogram message/chat)
        user_id = None
        if 'message' in kwargs:
            user_id = getattr(kwargs['message'].chat, 'id', None)
        elif len(args) > 0 and hasattr(args[0], 'chat'):
            user_id = getattr(args[0].chat, 'id', None)
        elif len(args) > 1 and hasattr(args[1], 'chat'):
            user_id = getattr(args[1].chat, 'id', None)
        if user_id:
            send_reply_keyboard_always(user_id)
        return result

    return wrapper


# --- Example of using wrapper for any handler ---
# @reply_with_keyboard
# def your_handler(...):
# ...

# --- New function for cleaning URL only for tags ---
def get_clean_url_for_tagging(url: str) -> str:
    """
    Extracts the last (deepest nested) link from URL-wrappers.
    Used ONLY for generating tags.
    """
    if not isinstance(url, str):
        return ''
    last_http_pos = url.rfind('http://')
    last_https_pos = url.rfind('https://')

    start_of_real_url_pos = max(last_http_pos, last_https_pos)

    # If another http/https is found (not at the very beginning), this is the real link
    if start_of_real_url_pos > 0:
        return url[start_of_real_url_pos:]
    return url


def is_tiktok_url(url: str) -> bool:
    """
    Checks if URL is a TikTok link
    """
    try:
        clean_url = get_clean_url_for_tagging(url)
        parsed_url = urlparse(clean_url)
        return any(domain in parsed_url.netloc for domain in Config.TIKTOK_DOMAINS)
    except:
        return False


# --- Extracting TikTok profile name from URL ---
def extract_tiktok_profile(url: str) -> str:
    # Looking for @username after the domain
    import re
    clean_url = get_clean_url_for_tagging(url)
    m = re.search(r'/@([\w\.\-_]+)', clean_url)
    if m:
        return m.group(1)
    return ''


# --- New function to check if URL contains playlist range ---
def is_playlist_with_range(text: str) -> bool:
    """
    Checks if the text contains a playlist range pattern like *1*3, 1*1000, *5*10, or just * for full playlist.
    Returns True if a range is detected, False otherwise.
    """
    if not isinstance(text, str):
        return False

    # Look for patterns like *1*3, 1*1000, *5*10, or just * for full playlist
    range_pattern = r'\*[0-9]+\*[0-9]+|[0-9]+\*[0-9]+|\*'
    return bool(re.search(range_pattern, text))

# ###############################################################################################
# Global starting point list (do not modify)
starting_point = []

# Global dictionary to track active downloads and lock for thread-safe access
active_downloads = {}
active_downloads_lock = threading.Lock()

# Global dictionary to track playlist errors and lock for thread-safe access
playlist_errors = {}
playlist_errors_lock = threading.Lock()

# Add a global dictionary to track download start times
download_start_times = {}
download_start_times_lock = threading.Lock()


def set_download_start_time(user_id):
    """
    Sets the download start time for a user
    """
    with download_start_times_lock:
        download_start_times[user_id] = time.time()


def clear_download_start_time(user_id):
    """
    Clears the download start time for a user
    """
    with download_start_times_lock:
        if user_id in download_start_times:
            del download_start_times[user_id]


def check_download_timeout(user_id):
    """
    Checks if the download timeout has been exceeded. For admins, timeout does not apply.
    """
    # If the user is an admin, timeout does not apply
    if hasattr(Config, 'ADMIN') and int(user_id) in Config.ADMIN:
        return False
    with download_start_times_lock:
        if user_id in download_start_times:
            start_time = download_start_times[user_id]
            current_time = time.time()
            if current_time - start_time > Config.DOWNLOAD_TIMEOUT:
                return True
    return False


# Helper function to check available disk space
def check_disk_space(path, required_bytes):
    """
    Checks if there's enough disk space available at the specified path.

    Args:
        path (str): Path to check
        required_bytes (int): Required bytes of free space

    Returns:
        bool: True if enough space is available, False otherwise
    """
    try:
        total, used, free = shutil.disk_usage(path)
        if free < required_bytes:
            logger.warning(
                f"Not enough disk space. Required: {humanbytes(required_bytes)}, Available: {humanbytes(free)}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        # If we can't check, assume there's enough space
        return True


# Initialize Firebase
firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)
auth = firebase.auth()

# Authenticate user
try:
    user = auth.sign_in_with_email_and_password(Config.FIREBASE_USER, Config.FIREBASE_PASSWORD)
    logger.info("✅ Firebase signed in")
except Exception as e:
    logger.error(f"❌ Firebase authentication error: {e}")
    raise

# Extract idToken
id_token = user.get("idToken")
if not id_token:
    raise Exception("idToken is missing")

# Setup database with authentication
base_db = firebase.database()

class AuthedDB:
    def __init__(self, db, token):
        self.db = db
        self.token = token

    def child(self, *path_parts):
        db_ref = self.db
        for part in path_parts:
            db_ref = db_ref.child(part)
        return AuthedDB(db_ref, self.token)

    def set(self, data, *args, **kwargs):
        return self.db.set(data, self.token, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.db.get(self.token, *args, **kwargs)

    def push(self, data, *args, **kwargs):
        return self.db.push(data, self.token, *args, **kwargs)

    def update(self, data, *args, **kwargs):
        return self.db.update(data, self.token, *args, **kwargs)

    def remove(self, *args, **kwargs):
        return self.db.remove(self.token, *args, **kwargs)
	    

# Create authed db wrapper
db = AuthedDB(base_db, id_token)

# Optional write to verify it's working
try:
    db_path = Config.BOT_DB_PATH.rstrip("/")
    payload = {"ID": "0", "timestamp": math.floor(time.time())}
    db.child(f"{db_path}/users/0").set(payload)
    logger.info("✅ Initial Firebase write successful")
except Exception as e:
    logger.error(f"❌ Error writing to Firebase: {e}")
    raise

# Background thread to refresh idToken every 50 minutes
def token_refresher():
    global db, user
    while True:
        time.sleep(3000)  # 50 minutes
        try:
            new_user = auth.refresh(user["refreshToken"])
            new_id_token = new_user["idToken"]
            db.token = new_id_token
            user = new_user
            logger.info("🔁 Firebase token refreshed")
        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")

token_thread = threading.Thread(target=token_refresher, daemon=True)
token_thread.start()

# ###############################################################################################

# Pyrogram App Initialization
app = Client(
    "magic",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


# #############################################################################################################################
# #############################################################################################################################

@app.on_message(filters.command("reload_cache") & filters.private)
def reload_firebase_cache_command(app, message):
    """The processor of command for rebooting the local cache Firebase"""
    if int(message.chat.id) not in Config.ADMIN:
        send_to_user(message, "❌ Access denied. Admin only.")
        return
    try:
        # 1. First, start download_firebase.py along the way from the confusion
        script_path = getattr(Config, "DOWNLOAD_FIREBASE_SCRIPT_PATH", "download_firebase.py")
        send_to_user(message, f"⏳ Downloading fresh Firebase dump using {script_path} ...")
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if result.returncode != 0:
            send_to_user(message, f"❌ Error running {script_path}:\n{result.stdout}\n{result.stderr}")
            send_to_logger(message, f"Error running {script_path}: {result.stdout}\n{result.stderr}")
            return
        # 2. Now load the cache
        success = reload_firebase_cache()
        if success:
            send_to_user(message, "✅ Firebase cache reloaded successfully!")
            send_to_logger(message, "Firebase cache reloaded by admin.")
        else:
            cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
            send_to_user(message, f"❌ Failed to reload Firebase cache. Check if {cache_file} exists.")
    except Exception as e:
        send_to_user(message, f"❌ Error reloading cache: {str(e)}")
        send_to_logger(message, f"Error reloading Firebase cache: {str(e)}")


def auto_cache_command(app, message):
    """Command handler to control the automatic loading of the Firebase cache."""
    if int(message.chat.id) not in Config.ADMIN:
        send_to_user(message, "❌ Access denied. Admin only.")
        return

    new_state = toggle_auto_cache_reloader()
    interval = getattr(Config, 'RELOAD_CACHE_EVERY', 4)

    if new_state:
        next_exec = get_next_reload_time(interval)
        delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
        send_to_user(
            message,
            "🔄 Auto Firebase cache reloading started!\n\n"
            f"📊 Status: ✅ ENABLED\n"
            f"⏰ Schedule: every {interval} hours from 00:00\n"
            f"🕒 Next reload: {next_exec.strftime('%H:%M')} (in {delta_min} minutes)"
        )
        send_to_logger(message, f"Auto reload started; next at {next_exec}")
    else:
        send_to_user(
            message,
            "🛑 Auto Firebase cache reloading stopped!\n\n"
            "📊 Status: ❌ DISABLED\n"
            "💡 Use /auto_cache again to re-enable"
        )
        send_to_logger(message, "Auto reload stopped by admin.")
        

@app.on_callback_query(filters.regex(r"^subs_lang_close\|"))
def subs_lang_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Subtitle language menu closed.")
        send_to_logger(callback_query.message, "Subtitle language menu closed.")
        return

@app.on_message(filters.command("start") & filters.private)
@reply_with_keyboard
def command1(app, message):
    if int(message.chat.id) in Config.ADMIN:
        send_to_user(message, "Welcome Master 🥷")
    else:
        check_user(message)
        app.send_message(
            message.chat.id,
            f"Hello {message.chat.first_name},\n \n__This bot🤖 can download any videos into telegram directly.😊 For more information press **/help**__ 👈\n \n {Config.CREDITS_MSG}")
        send_to_logger(message, f"{message.chat.id} - user started the bot")


@app.on_message(filters.command("help"))
@reply_with_keyboard
def command2(app, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Close", callback_data="help_msg|close")]
    ])
    app.send_message(message.chat.id, (Config.HELP_MSG),
                     parse_mode=enums.ParseMode.HTML,
                     reply_markup=keyboard)
    send_to_logger(message, f"Send help txt to user")

@app.on_callback_query(filters.regex(r"^help_msg\|"))
def help_msg_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Help closed.")
        send_to_logger(callback_query.message, "Help message closed.")
        return

def create_directory(path):
    # Create The Directory (And All Intermediate Directories) IF Its Not Exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# Command to Set Browser Cooks
@app.on_message(filters.command("cookies_from_browser") & filters.private)
# @reply_with_keyboard
def cookies_from_browser(app, message):
    user_id = message.chat.id
    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    # Logging a request for cookies from browser
    send_to_logger(message, "User requested cookies from browser.")

    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # Dictionary with Browsers and Their Paths
    browsers = {
        "brave": "~/.config/BraveSoftware/Brave-Browser/",
        "chrome": "~/.config/google-chrome/",
        "chromium": "~/.config/chromium/",
        "edge": "~/.config/microsoft-edge/",
        "firefox": "~/.mozilla/firefox/",
        "opera": "~/.config/opera/",
        "safari": "~/Library/Safari/",
        "vivaldi": "~/.config/vivaldi/",
        "whale": ["~/.config/Whale/", "~/.config/naver-whale/"]
    }

    # Create a list of only installed browsers
    installed_browsers = []
    for browser, path in browsers.items():
        if browser == "safari":
            exists = False
        elif isinstance(path, list):
            exists = any(os.path.exists(os.path.expanduser(p)) for p in path)
        else:
            exists = os.path.exists(os.path.expanduser(path))
        if exists:
            installed_browsers.append(browser)

    # If there are no installed browsers, send a message about it
    if not installed_browsers:
        app.send_message(
            user_id,
            "❌ No supported browsers found on the server. Please install one of the supported browsers or use manual cookie upload."
        )
        send_to_logger(message, "No installed browsers found.")
        return

    # Create buttons only for installed browsers
    buttons = []
    for browser in installed_browsers:
        display_name = browser.capitalize()
        button = InlineKeyboardButton(f"✅ {display_name}", callback_data=f"browser_choice|{browser}")
        buttons.append([button])

    # Add a close button
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="browser_choice|close")])
    keyboard = InlineKeyboardMarkup(buttons)

    app.send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard
    )
    send_to_logger(message, "Browser selection keyboard sent with installed browsers only.")


# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
# @reply_with_keyboard
def browser_choice_callback(app, callback_query):
    logger.info(f"[BROWSER] callback: {callback_query.data}")
    import subprocess

    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]  # E.G. "Chromium", "Firefox", or "Close"
    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("✅ Browser choice updated.")
        send_to_logger(callback_query.message, "Browser selection closed.")
        return

    browser_option = data

    # Dictionary with Browsers and Their Paths (Same as ABOVE)
    browsers = {
        "brave": "~/.config/BraveSoftware/Brave-Browser/",
        "chrome": "~/.config/google-chrome/",
        "chromium": "~/.config/chromium/",
        "edge": "~/.config/microsoft-edge/",
        "firefox": "~/.mozilla/firefox/",
        "opera": "~/.config/opera/",
        "safari": "~/Library/Safari/",
        "vivaldi": "~/.config/vivaldi/",
        "whale": ["~/.config/Whale/", "~/.config/naver-whale/"]
    }
    path = browsers.get(browser_option)
    # If the browser is not installed, we inform the user and do not execute the command
    if (browser_option == "safari") or (
            isinstance(path, list) and not any(os.path.exists(os.path.expanduser(p)) for p in path)
    ) or (isinstance(path, str) and not os.path.exists(os.path.expanduser(path))):
        callback_query.edit_message_text(f"⚠️ {browser_option.capitalize()} browser not installed.")
        callback_query.answer("⚠️ Browser not installed.")
        send_to_logger(callback_query.message, f"Browser {browser_option} not installed.")
        return

    # Build the command for cookie extraction: yt-dlp --cookies "cookie.txt" --cookies-from-browser <browser_option>
    cmd = f'yt-dlp --cookies "{cookie_file}" --cookies-from-browser {browser_option}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        if "You must provide at least one URL" in result.stderr:
            callback_query.edit_message_text(f"✅ Cookies saved using browser: {browser_option}")
            send_to_logger(callback_query.message, f"Cookies saved using browser: {browser_option}")
        else:
            callback_query.edit_message_text(f"❌ Failed to save cookies: {result.stderr}")
            send_to_logger(callback_query.message,
                           f"Failed to save cookies using browser {browser_option}: {result.stderr}")
    else:
        callback_query.edit_message_text(f"✅ Cookies saved using browser: {browser_option}")
        send_to_logger(callback_query.message, f"Cookies saved using browser: {browser_option}")

    callback_query.answer("✅ Browser choice updated.")

def check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
    """
    Checks the limits of the download range for playlists, Tiktok and Instagram.
    For single videos, True always returns.
    If the range exceeds the limit, it sends a warning and returns false.
    """
    # If a single video (no range) - always true
    if video_start_with == 1 and video_end_with == 1:
        return True

    url_l = str(url).lower() if url else ''
    if 'tiktok.com' in url_l:
        max_count = Config.MAX_TIKTOK_COUNT
        service = 'TikTok'
    elif 'instagram.com' in url_l:
        max_count = Config.MAX_TIKTOK_COUNT
        service = 'Instagram'
    else:
        max_count = Config.MAX_PLAYLIST_COUNT
        service = 'playlist'

    count = video_end_with - video_start_with + 1
    if count > max_count:
        app.send_message(
            message.chat.id,
            f"❗️ Range limit exceeded for {service}: {count} (maximum {max_count}).\nReduce the range and try again.",
            reply_to_message_id=getattr(message, 'id', None)
        )
        # We send a notification to the log channel
        app.send_message(
            Config.LOGS_ID,
            f"❗️ Range limit exceeded for {service}: {count} (maximum {max_count})\nUser ID: {message.chat.id}",
        )
        return False
    return True

# Command to Download Audio from a Video url
@app.on_message(filters.command("audio") & filters.private)
# @reply_with_keyboard
def audio_command_handler(app, message):
    user_id = message.chat.id
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    text = message.text
    url, _, _, _, tags, tags_text, tag_error = extract_url_range_tags(text)
    if tag_error:
        wrong, example = tag_error
        app.send_message(user_id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_to_message_id=message.id)
        return
    if not url:
        send_to_user(message, "Please, send valid URL.")
        return
    save_user_tags(user_id, tags)
    
    # Extract playlist parameters from the message
    full_string = message.text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
    video_count = video_end_with - video_start_with + 1
    
    # Checking the range limit
    if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
        return
    
    down_and_audio(app, message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)


# /Playlist Command
@app.on_message(filters.command("playlist") & filters.private)
# @reply_with_keyboard
def playlist_command(app, message):
    user_id = message.chat.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Close", callback_data="playlist_help|close")]
    ])
    app.send_message(user_id, Config.PLAYLIST_HELP_MSG, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    send_to_logger(message, "User requested playlist help.")

@app.on_callback_query(filters.regex(r"^playlist_help\|"))
def playlist_help_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Playlist help closed.")
        send_to_logger(callback_query.message, "Playlist help closed.")
        return

# Command /Format Handler
@app.on_message(filters.command("format") & filters.private)
# @reply_with_keyboard
def set_format(app, message):
    user_id = message.chat.id
    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    send_to_logger(message, "User requested format change.")
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # If the additional text is transmitted, we save it as Custom Format
    if len(message.command) > 1:
        custom_format = message.text.split(" ", 1)[1].strip()
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write(custom_format)
        app.send_message(user_id, f"✅ Format updated to:\n{custom_format}")
        send_to_logger(message, f"Format updated to: {custom_format}")
    else:
        # Main Menu with A Few Popular Options, Plus The Others Button
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Always Ask (menu + buttons)", callback_data="format_option|alwaysask")],
            [InlineKeyboardButton("🎛 Others (144p - 4320p)", callback_data="format_option|others")],
            [InlineKeyboardButton("💻4k (best for PC/Mac Telegram)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱FullHD (best for mobile Telegram)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈Bestvideo+Bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton("🎚 Custom (enter your own)", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        app.send_message(
            user_id,
            "Select a format option or send a custom one using `/format <format_string>`:",
            reply_markup=main_keyboard
        )
        send_to_logger(message, "Format menu sent.")


# Callbackquery Handler for /Format Menu Selection
@app.on_callback_query(filters.regex(r"^format_option\|"))
# @reply_with_keyboard
def format_option_callback(app, callback_query):
    logger.info(f"[FORMAT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    # If you press the close button
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("✅ Format choice updated.")
        send_to_logger(callback_query.message, "Format selection closed.")
        return

    # If the Custom button is pressed
    if data == "custom":
        # Sending a message with the Close button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="format_custom|close")]
        ])
        app.send_message(
            user_id,
            "To use a custom format, send the command in the following form:\n\n`/format bestvideo+bestaudio/best`\n\nReplace `bestvideo+bestaudio/best` with your desired format string.",
            reply_to_message_id=callback_query.message.id,
            reply_markup=keyboard
        )
        callback_query.answer("Hint sent.")
        send_to_logger(callback_query.message, "Custom format hint sent.")
        return

    # If the Others button is pressed - we display the second set of options
    if data == "others":
        full_res_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("144p (256×144)", callback_data="format_option|bv144"),
                InlineKeyboardButton("240p (426×240)", callback_data="format_option|bv240"),
                InlineKeyboardButton("360p (640×360)", callback_data="format_option|bv360")
            ],
            [
                InlineKeyboardButton("480p (854×480)", callback_data="format_option|bv480"),
                InlineKeyboardButton("720p (1280×720)", callback_data="format_option|bv720"),
                InlineKeyboardButton("1080p (1920×1080)", callback_data="format_option|bv1080")
            ],
            [
                InlineKeyboardButton("1440p (2560×1440)", callback_data="format_option|bv1440"),
                InlineKeyboardButton("2160p (3840×2160)", callback_data="format_option|bv2160"),
                InlineKeyboardButton("4320p (7680×4320)", callback_data="format_option|bv4320")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back"), InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        callback_query.edit_message_text("Select your desired resolution:", reply_markup=full_res_keyboard)
        callback_query.answer()
        send_to_logger(callback_query.message, "Format resolution menu sent.")
        return

    # If the Back button is pressed - we return to the main menu
    if data == "back":
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Always Ask (menu + buttons)", callback_data="format_option|alwaysask")],
            [InlineKeyboardButton("🎛 Others (144p - 4320p)", callback_data="format_option|others")],
            [InlineKeyboardButton("💻4k (best for PC/Mac Telegram)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱FullHD (best for mobile Telegram)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈Bestvideo+Bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton("🎚 Custom (enter your own)", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔚 close", callback_data="format_option|close")]
        ])
        callback_query.edit_message_text("Select a format option or send a custom one using `/format <format_string>`:",
                                         reply_markup=main_keyboard)
        callback_query.answer()
        send_to_logger(callback_query.message, "Returned to main format menu.")
        return

    # Mapping for the Rest of the Options
    if data == "bv144":
        chosen_format = "bv*[vcodec*=avc1][height<=144]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv240":
        chosen_format = "bv*[vcodec*=avc1][height<=240]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv360":
        chosen_format = "bv*[vcodec*=avc1][height<=360]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv480":
        chosen_format = "bv*[vcodec*=avc1][height<=480]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv720":
        chosen_format = "bv*[vcodec*=avc1][height<=720]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv1080":
        chosen_format = "bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv1440":
        chosen_format = "bv*[vcodec*=avc1][height<=1440]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv2160":
        chosen_format = "bv*[vcodec*=avc1][height<=2160]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv4320":
        chosen_format = "bv*[vcodec*=avc1][height<=4320]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bestvideo":
        chosen_format = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best"
    elif data == "best":
        chosen_format = "best"
    else:
        chosen_format = data

    # Save The Selected Format
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
        f.write(chosen_format)
    callback_query.edit_message_text(f"✅ Format updated to:\n{chosen_format}")
    callback_query.answer("✅ Format saved.")
    send_to_logger(callback_query.message, f"Format updated to: {chosen_format}")

    if data == "alwaysask":
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write("ALWAYS_ASK")
        callback_query.edit_message_text(
            "✅ Format set to: Always Ask. Now you will be prompted for quality each time you send a URL.")
        send_to_logger(callback_query.message, "Format set to ALWAYS_ASK.")
        return

# Callback processor to close the message
@app.on_callback_query(filters.regex(r"^format_custom\|"))
def format_custom_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Custom format menu closed.")
        send_to_logger(callback_query.message, "Custom format menu closed")
        return
# ####################################################################################

# Checking user is Blocked or not

def is_user_blocked(message):
    blocked = db.child("bot").child("tgytdlp_bot").child("blocked_users").get().each()
    blocked_users = [int(b_user.key()) for b_user in blocked]
    if int(message.chat.id) in blocked_users:
        send_to_all(message, "🚫 You are banned from the bot!")
        return True
    else:
        return False


# Cheking Users are in Main User Directory in DB

def check_user(message):
    user_id_str = str(message.chat.id)

    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
    create_directory(user_dir)

    # Updated path for cookie.txt
    cookie_src = os.path.join(os.getcwd(), "cookies", "cookie.txt")
    cookie_dest = os.path.join(user_dir, os.path.basename(Config.COOKIE_FILE_PATH))

    # Copy Cookie.txt to the User's Folder if Not Already Present
    if os.path.exists(cookie_src) and not os.path.exists(cookie_dest):
        import shutil
        shutil.copy(cookie_src, cookie_dest)

    # Register the User in the Database if Not Already Registered
    user_db = db.child("bot").child("tgytdlp_bot").child("users").get().each()
    users = [user.key() for user in user_db] if user_db else []
    if user_id_str not in users:
        data = {"ID": message.chat.id, "timestamp": math.floor(time.time())}
        db.child("bot").child("tgytdlp_bot").child("users").child(user_id_str).set(data)


# ####################################################################################

# Checking Actions
# Text Message Handler for General Commands
@app.on_message(filters.text & filters.private)
@reply_with_keyboard
def url_distractor(app, message):
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN
    text = message.text.strip()

    # For non-admin users, if they haven't Joined the Channel, Exit ImmediaTely.
    if not is_admin and not is_user_in_channel(app, message):
        return

    # ----- User Commands -----
    # /Save_as_cookie Command
    if text.startswith(Config.SAVE_AS_COOKIE_COMMAND):
        save_as_cookie_file(app, message)
        return

    # /Subs Command
    if text.startswith(Config.SUBS_COMMAND):
        subs_command(app, message)
        return

    # /Download_cookie Command
    if text == Config.DOWNLOAD_COOKIE_COMMAND:
        download_cookie(app, message)
        return

    # /Check_cookie Command
    if text == Config.CHECK_COOKIE_COMMAND:
        checking_cookie_file(app, message)
        return

    # /cookies_from_browser Command
    if text.startswith(Config.COOKIES_FROM_BROWSER_COMMAND):
        cookies_from_browser(app, message)
        return

    # /Audio Command
    if text.startswith(Config.AUDIO_COMMAND):
        audio_command_handler(app, message)
        return

    # /Format Command
    if text.startswith(Config.FORMAT_COMMAND):
        set_format(app, message)
        return

    # /Mediainfo Command
    if text.startswith(Config.MEDIINFO_COMMAND):
        mediainfo_command(app, message)
        return

    # /Settings Command
    if text.startswith(Config.SETTINGS_COMMAND):
        settings_command(app, message)
        return

        # /Playlist Command
    if text.startswith(Config.PLAYLIST_COMMAND):
        settings_command(app, message)
        return

        # /Clean Command
    if text.startswith(Config.CLEAN_COMMAND):
        clean_args = text[len(Config.CLEAN_COMMAND):].strip().lower()
        if clean_args in ["cookie", "cookies"]:
            remove_media(message, only=["cookie.txt"])
            send_to_all(message, "🗑 Cookie file removed.")
            return
        elif clean_args in ["log", "logs"]:
            remove_media(message, only=["logs.txt"])
            send_to_all(message, "🗑 Logs file removed.")
            return
        elif clean_args in ["tag", "tags"]:
            remove_media(message, only=["tags.txt"])
            send_to_all(message, "🗑 Tags file removed.")
            return
        elif clean_args == "format":
            remove_media(message, only=["format.txt"])
            send_to_all(message, "🗑 Format file removed.")
            return
        elif clean_args == "split":
            remove_media(message, only=["split.txt"])
            send_to_all(message, "🗑 Split file removed.")
            return
        elif clean_args == "mediainfo":
            remove_media(message, only=["mediainfo.txt"])
            send_to_all(message, "🗑 Mediainfo file removed.")
            return
        elif clean_args == "subs":
            remove_media(message, only=["subs.txt"])
            send_to_all(message, "🗑 Subtitle settings removed.")
            clear_subs_check_cache()
            return
        elif clean_args == "all":
            # Delete all files and display the list of deleted ones
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                send_to_all(message, "🗑 No files to remove.")
                clear_subs_check_cache()
                return

            removed_files = []
            allfiles = os.listdir(user_dir)

            # Delete all files in the user folder
            for file in allfiles:
                file_path = os.path.join(user_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        removed_files.append(file)
                        logger.info(f"Removed file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file_path}: {e}")

            if removed_files:
                files_list = "\n".join([f"• {file}" for file in removed_files])
                send_to_all(message, f"🗑 All files removed successfully!\n\nRemoved files:\n{files_list}")
            else:
                send_to_all(message, "🗑 No files to remove.")
            return
        else:
            # Regular command /clean - delete only media files with filtering
            remove_media(message)
            send_to_all(message, "🗑 All media files are removed.")
            clear_subs_check_cache()
            return

    # /USAGE Command
    if Config.USAGE_COMMAND in text:
        get_user_log(app, message)
        return

    # /tags Command
    if Config.TAGS_COMMAND in text:
        tags_command(app, message)
        return

    # /Split Command
    if text.startswith(Config.SPLIT_COMMAND):
        split_command(app, message)
        return

    # /uncache Command - Clear cache for URL (for admins only)
    if text.startswith(Config.UNCACHE_COMMAND):
        if is_admin:
            uncache_command(app, message)
        else:
            send_to_all(message, "❌ This command is only available for administrators.")
        return

    # If the Message Contains a URL, Launch The Video Download Function.
    if ("https://" in text) or ("http://" in text):
        if not is_user_blocked(message):
            # Clean the cache of subtitles before processing the new URL
            clear_subs_check_cache()
            video_url_extractor(app, message)
        return

    # ----- Admin Commands -----
    if is_admin:
        # If the message begins with /BroadCast, we process it as BroadCast, regardless
        if text.startswith(Config.BROADCAST_MESSAGE):
            send_promo_message(app, message)
            return

        # /Block_user Command
        if Config.BLOCK_USER_COMMAND in text:
            block_user(app, message)
            return

        # /unblock_user Command
        if Config.UNBLOCK_USER_COMMAND in text:
            unblock_user(app, message)
            return

        # /Run_Time Command
        if Config.RUN_TIME in text:
            check_runtime(message)
            return

        # /All Command for User Details
        if Config.GET_USER_DETAILS_COMMAND in text:
            get_user_details(app, message)
            return

        # /log Command for User Logs
        if Config.GET_USER_LOGS_COMMAND in text:
            get_user_log(app, message)
            return

        # /uncache Command - Clear cache for URL
        if Config.UNCACHE_COMMAND in text:
            uncache_command(app, message)
            return

        # /reload_cache Command - Reload cache for URL
        if Config.RELOAD_CACHE_COMMAND in text:
            reload_firebase_cache_command(app, message)
            return

        # /auto_cache Command - Toggle automatic cache reloading
        if Config.AUTO_CACHE_COMMAND in text:
            auto_cache_command(app, message)
            return

    # Reframed processing for all users (admins and ordinary users)
    if message.reply_to_message:
        # If the reference text begins with /broadcast, then:
        if text.startswith(Config.BROADCAST_MESSAGE):
            # Only for admins we call send_promo_message
            if is_admin:
                send_promo_message(app, message)
        else:
            # Otherwise, if the reform contains video, we call Caption_EDITOR
            if not is_user_blocked(message):
                if message.reply_to_message.video:
                    caption_editor(app, message)
        return

    logger.info(f"{user_id} No matching command processed.")
    clear_subs_check_cache()


# Check the USAGE of the BOT

def is_user_in_channel(app, message):
    try:
        cht_member = app.get_chat_member(
            Config.SUBSCRIBE_CHANNEL, message.chat.id)
        if cht_member.status == ChatMemberStatus.MEMBER or cht_member.status == ChatMemberStatus.OWNER or cht_member.status == ChatMemberStatus.ADMINISTRATOR:
            return True

    except:

        text = f"{Config.TO_USE_MSG}\n \n{Config.CREDITS_MSG}"
        button = InlineKeyboardButton(
            "Join Channel", url=Config.SUBSCRIBE_CHANNEL_URL)
        keyboard = InlineKeyboardMarkup([[button]])
        # Use the send_message () Method to send the message with the button
        app.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        return False


# Remove All User Media Files

def remove_media(message, only=None):
    dir = f'./users/{str(message.chat.id)}'
    if not os.path.exists(dir):
        logger.warning(f"Directory {dir} does not exist, nothing to remove")
        return
    if only:
        for fname in only:
            file_path = os.path.join(dir, fname)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file_path}: {e}")
        return
    allfiles = os.listdir(dir)
    file_extensions = [
        '.mp4', '.mkv', '.mp3', '.m4a', '.jpg', '.jpeg', '.part', '.ytdl',
        '.txt', '.ts', '.m3u8', '.webm', '.wmv', '.avi', '.mpeg', '.wav'
    ]
    for extension in file_extensions:
        if isinstance(extension, tuple):
            files = [fname for fname in allfiles if any(fname.endswith(ext) for ext in extension)]
        else:
            files = [fname for fname in allfiles if fname.endswith(extension)]
        for file in files:
            if extension == '.txt' and file in ['logs.txt', 'tags.txt']:
                continue
            file_path = os.path.join(dir, file)
            try:
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove file {file_path}: {e}")
    logger.info(f"Media cleanup completed for user {message.chat.id}")


# SEND BRODCAST Message to All Users

def send_promo_message(app, message):
    # We get a list of users from the base
    user_lst = db.child("bot").child("tgytdlp_bot").child("users").get().each()
    user_lst = [int(user.key()) for user in user_lst]
    # Add administrators if they are not on the list
    for admin in Config.ADMIN:
        if admin not in user_lst:
            user_lst.append(admin)

    # We extract the text of Boadcast. If the message contains lines transfers, take all the lines after the first.
    lines = message.text.splitlines()
    if len(lines) > 1:
        broadcast_text = "\n".join(lines[1:]).strip()
    else:
        broadcast_text = message.text[len(Config.BROADCAST_MESSAGE):].strip()

    # If the message is a reference, we get it
    reply = message.reply_to_message if message.reply_to_message else None

    send_to_logger(message, f"Broadcast initiated. Text:\n{broadcast_text}")

    try:
        # We send a message to all users
        for user in user_lst:
            try:
                if user != 0:
                    # If the message is a reference, send it (depending on the type of content)
                    if reply:
                        if reply.text:
                            app.send_message(user, reply.text)
                        elif reply.video:
                            app.send_video(user, reply.video.file_id, caption=reply.caption)
                        elif reply.photo:
                            app.send_photo(user, reply.photo.file_id, caption=reply.caption)
                        elif reply.sticker:
                            app.send_sticker(user, reply.sticker.file_id)
                        elif reply.document:
                            app.send_document(user, reply.document.file_id, caption=reply.caption)
                        elif reply.audio:
                            app.send_audio(user, reply.audio.file_id, caption=reply.caption)
                        elif reply.animation:
                            app.send_animation(user, reply.animation.file_id, caption=reply.caption)
                    # If there is an additional text, we send it
                    if broadcast_text:
                        app.send_message(user, broadcast_text)
            except Exception as e:
                logger.error(f"Error sending broadcast to user {user}: {e}")
        send_to_all(message, "**✅ Promo message sent to all other users**")
        send_to_logger(message, "Broadcast message sent to all users.")
    except Exception as e:
        send_to_all(message, "**❌ Cannot send the promo message. Try replying to a message\nOr some error occurred**")
        send_to_logger(message, f"Failed to broadcast message: {e}")


# Getting the User Logs

def get_user_log(app, message):
    user_id = str(message.chat.id)
    if int(message.chat.id) in Config.ADMIN and Config.GET_USER_LOGS_COMMAND in message.text:
        user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    logs_dict = get_from_local_cache(["bot", "tgytdlp_bot", "logs", user_id])
    if not logs_dict:
        send_to_all(message, "**❌ User did not download any content yet...** Not exist in logs")
        return

    logs = list(logs_dict.values())
    data, data_tg = [], []

    for l in logs:
        ts = datetime.fromtimestamp(int(l["timestamp"]))
        row = f"{ts} | {l['ID']} | {l['name']} | {l['title']} | {l['urls']}"
        row_2 = f"**{ts}** | `{l['ID']}` | **{l['name']}`** | {l['title']} | {l['urls']}"
        data.append(row)
        data_tg.append(row_2)

    total = len(data_tg)
    least_10 = sorted(data_tg[-10:], key=str.lower) if total > 10 else sorted(data_tg, key=str.lower)
    format_str = "\n\n".join(least_10)
    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = f"Logs of {Config.BOT_NAME_FOR_USERS}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n\n" + '\n'.join(sorted(data, key=str.lower))

    user_dir = os.path.join("users", str(message.chat.id))
    os.makedirs(user_dir, exist_ok=True)
    log_path = os.path.join(user_dir, "logs.txt")
    with open(log_path, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔚 Close", callback_data="userlogs_close|close")]])
    app.send_message(message.chat.id, f"Total: **{total}**\n**{user_id}** - logs (Last 10):\n\n{format_str}", reply_markup=keyboard)
    app.send_document(message.chat.id, log_path, caption=f"{user_id} - all logs")
    app.send_document(Config.LOGS_ID, log_path, caption=f"{user_id} - all logs")


@app.on_callback_query(filters.regex(r"^userlogs_close\|"))
def userlogs_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Logs message closed.")
        send_to_logger(callback_query.message, "User logs message closed.")
        return


# Get All Kinds of Users (Users/ Blocked/ Unblocked)

def get_user_details(app, message):
    command = message.text.split(Config.GET_USER_DETAILS_COMMAND)[1].strip()
    path_map = {
        "_blocked": "blocked_users",
        "_unblocked": "unblocked_users",
        "_users": "users"
    }
    path = path_map.get(command)
    if not path:
        send_to_all(message, "❌ Invalid command")
        return

    # data_dict = get_from_local_cache([Config.BOT_DB_PATH, path])
    data_dict = get_from_local_cache(["bot", "tgytdlp_bot", path])
    if not data_dict:
        send_to_all(message, f"❌ No data found in cache for `{path}`")
        return

    modified_lst, txt_lst = [], []
    for user in data_dict.values():
        if user["ID"] != "0":
            ts = datetime.fromtimestamp(int(user["timestamp"]))
            txt_lst.append(f"TS: {ts} | ID: {user['ID']}")
            modified_lst.append(f"TS: **{ts}** | ID: `{user['ID']}`")

    modified_lst.sort(key=str.lower)
    txt_lst.sort(key=str.lower)
    display_list = modified_lst[-20:] if len(modified_lst) > 20 else modified_lst

    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = f"{Config.BOT_NAME_FOR_USERS} {path}\nTotal {path}: {len(modified_lst)}\nCurrent time: {now}\n\n" + '\n'.join(txt_lst)
    mod = f"__Total Users: {len(modified_lst)}__\nLast 20 {path}:\n\n" + '\n'.join(display_list)

    file = f"{path}.txt"
    with open(file, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    send_to_all(message, mod)
    app.send_document(message.chat.id, f"./{file}", caption=f"{Config.BOT_NAME_FOR_USERS} - all {path}")
    app.send_document(Config.LOGS_ID, f"./{file}", caption=f"{Config.BOT_NAME_FOR_USERS} - all {path}")
    logger.info(mod)

# Block User

def block_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        dt = math.floor(time.time())
        b_user_id = str((message.text).split(
            Config.BLOCK_USER_COMMAND + " ")[1])

        if int(b_user_id) in Config.ADMIN:
            send_to_all(message, "🚫 Admin cannot delete an admin")
        else:
            all_blocked_users = db.child(
                f"{Config.BOT_DB_PATH}/blocked_users").get().each()
            b_users = [b_user.key() for b_user in all_blocked_users]

            if b_user_id not in b_users:
                data = {"ID": b_user_id, "timestamp": str(dt)}
                db.child(
                    f"{Config.BOT_DB_PATH}/blocked_users/{b_user_id}").set(data)
                send_to_user(
                    message, f"User blocked 🔒❌\n \nID: `{b_user_id}`\nBlocked Date: {datetime.fromtimestamp(dt)}")

            else:
                send_to_user(message, f"`{b_user_id}` is already blocked ❌😐")
    else:
        send_to_all(message, "🚫 Sorry! You are not an admin")


# Unblock User

def unblock_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        ub_user_id = str((message.text).split(
            Config.UNBLOCK_USER_COMMAND + " ")[1])
        all_blocked_users = db.child(
            f"{Config.BOT_DB_PATH}/blocked_users").get().each()
        b_users = [b_user.key() for b_user in all_blocked_users]

        if ub_user_id in b_users:
            dt = math.floor(time.time())

            data = {"ID": ub_user_id, "timestamp": str(dt)}
            db.child(
                f"{Config.BOT_DB_PATH}/unblocked_users/{ub_user_id}").set(data)
            db.child(
                f"{Config.BOT_DB_PATH}/blocked_users/{ub_user_id}").remove()
            send_to_user(
                message, f"User unblocked 🔓✅\n \nID: `{ub_user_id}`\nUnblocked Date: {datetime.fromtimestamp(dt)}")

        else:
            send_to_user(message, f"`{ub_user_id}` is already unblocked ✅😐")
    else:
        send_to_all(message, "🚫 Sorry! You are not an admin")


# Check Runtime

def check_runtime(message):
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        now = TimeFormatter(now)
        send_to_user(message, f"⏳ __Bot running time -__ **{now}**")
    pass



def uncache_command(app, message):
    """
    Admin command to clear cache for a specific URL
    Usage: /uncache <URL>
    """
    user_id = message.chat.id
    text = message.text.strip()
    if len(text.split()) < 2:
        send_to_user(message, "❌ Please provide a URL to clear cache for.\nUsage: `/uncache <URL>`")
        return
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        send_to_user(message, "❌ Please provide a valid URL.\nUsage: `/uncache <URL>`")
        return
    removed_any = False
    try:
        # Clearing the cache by video
        normalized_url = normalize_url_for_cache(url)
        url_hash = get_url_hash(normalized_url)
        video_cache_path = f"{Config.VIDEO_CACHE_DB_PATH}/{url_hash}"
        db_child_by_path(db, video_cache_path).remove()
        removed_any = True
        # Clear cache by playlist (if any)
        playlist_url = get_clean_playlist_url(url)
        if playlist_url:
            playlist_normalized = normalize_url_for_cache(playlist_url)
            playlist_hash = get_url_hash(playlist_normalized)
            playlist_cache_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{playlist_hash}"
            db_child_by_path(db, playlist_cache_path).remove()
            removed_any = True
            # If there is a range (eg *1*5), clear the cache for each index
            import re
            m = re.search(r"\*(\d+)\*(\d+)", url)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                for idx in range(start, end + 1):
                    idx_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{playlist_hash}/{idx}"
                    db_child_by_path(db, idx_path).remove()
        # Clear cache for short/long YouTube links
        if is_youtube_url(url):
            short_url = youtube_to_short_url(url)
            long_url = youtube_to_long_url(url)
            for variant in [short_url, long_url]:
                norm = normalize_url_for_cache(variant)
                h = get_url_hash(norm)
                db_child_by_path(db, f"{Config.VIDEO_CACHE_DB_PATH}/{h}").remove()
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{h}").remove()
        if removed_any:
            send_to_user(message, f"✅ Cache cleared successfully for URL:\n`{url}`")
            send_to_logger(message, f"Admin {user_id} cleared cache for URL: {url}")
        else:
            send_to_user(message, "ℹ️ No cache found for this link.")
    except Exception as e:
        send_to_all(message, f"❌ Error clearing cache: {e}")


# ===================== /settings =====================
@app.on_message(filters.command("settings") & filters.private)
# @reply_with_keyboard
def settings_command(app, message):
    user_id = message.chat.id
    # Main settings menu
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean"),
            InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies"),
        ],
        [
            InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media"),
            InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs"),
        ],
        [InlineKeyboardButton("🔚 Close", callback_data="settings__menu__close")]
    ])
    app.send_message(
        user_id,
        "<b>Bot Settings</b>\n\nChoose a category:",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
        reply_to_message_id=message.id
    )
    send_to_logger(message, "Opened /settings menu")


@app.on_callback_query(filters.regex(r"^settings__menu__"))
# @reply_with_keyboard
def settings_menu_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[-1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        return
    if data == "clean":
        # Show the cleaning menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍪 Cookies only", callback_data="clean_option|cookies"),
                InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags"),
                InlineKeyboardButton("📼 Format", callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton("✂️ Split", callback_data="clean_option|split"),
                InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton("💬 Subtitles", callback_data="clean_option|subs"),
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🧹 Clean Options</b>\n\nChoose what to clean:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "cookies":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 /download_cookie - Download my 5 cookies",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get browser's YT-cookie",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Validate your cookie file",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Upload custom cookie",
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🍪 COOKIES</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "media":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📼 /format - Change quality & format", callback_data="settings__cmd__format")],
            [InlineKeyboardButton("📊 /mediainfo - Turn ON / OFF MediaInfo", callback_data="settings__cmd__mediainfo")],
            [InlineKeyboardButton("✂️ /split - Change split video part size", callback_data="settings__cmd__split")],
            [InlineKeyboardButton("🎧 /audio - Download video as audio", callback_data="settings__cmd__audio")],
            [InlineKeyboardButton("💬 /subs - Subtitles language settings", callback_data="settings__cmd__subs")],
            [InlineKeyboardButton("📋 /playlist - How to download playlists", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🎞 MEDIA</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "logs":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("#️⃣ /tags - Send your #tags", callback_data="settings__cmd__tags")],
            [InlineKeyboardButton("🆘 /help - Get instructions", callback_data="settings__cmd__help")],
            [InlineKeyboardButton("📃 /usage -Send your logs", callback_data="settings__cmd__usage")],
            [InlineKeyboardButton("📋 /playlist - Playlist's help", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>📖 INFO</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "back":
        # Return to main menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean"),
                InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies"),
            ],
            [
                InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media"),
                InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs"),
            ],
            [InlineKeyboardButton("🔚 Close", callback_data="settings__menu__close")]
        ])
        callback_query.edit_message_text(
            "<b>Bot Settings</b>\n\nChoose a category:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return

@app.on_callback_query(filters.regex(r"^audio_hint\|"))
def audio_hint_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Audio hint closed.")
        send_to_logger(callback_query.message, "Audio hint closed.")
        return

@app.on_callback_query(filters.regex(r"^settings__cmd__"))
# @reply_with_keyboard
def settings_cmd_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[2]

    # For commands that are processed only via url_distractor, create a temporary Message
    if data == "clean":
        # Show the cleaning menu instead of direct execution
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍪 Cookies only", callback_data="clean_option|cookies"),
                InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags"),
                InlineKeyboardButton("📼 Format", callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton("✂️ Split", callback_data="clean_option|split"),
                InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton("💬 Subtitles", callback_data="clean_option|subs"),
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🧹 Clean Options</b>\n\nChoose what to clean:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "download_cookie":
        url_distractor(app, fake_message("/download_cookie", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "cookies_from_browser":
        cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "check_cookie":
        url_distractor(app, fake_message("/check_cookie", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "save_as_cookie":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="save_as_cookie_hint|close")]
        ])
        app.send_message(user_id, Config.SAVE_AS_COOKIE_HINT, reply_to_message_id=callback_query.message.id,
                         parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        callback_query.answer("Hint sent.")
        return
    if data == "format":
        # Add the command attribute for set_format to work correctly
        set_format(app, fake_message("/format", user_id, command=["format"]))
        callback_query.answer("Command executed.")
        return
        
    # /Subs Command
    if data == "subs":
        subs_command(app, fake_message("/subs", user_id))
        callback_query.answer("Command executed.")
        return

    if data == "mediainfo":
        mediainfo_command(app, fake_message("/mediainfo", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "split":
        split_command(app, fake_message("/split", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "audio":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="audio_hint|close")]
        ])
        app.send_message(user_id,
                         "Download only audio from video source.\n\nUsage: /audio + URL \n\n(ex. /audio https://youtu.be/abc123)\n(ex. /audio https://youtu.be/playlist?list=abc123*1*10)",
                         reply_to_message_id=callback_query.message.id,
                         reply_markup=keyboard)
        callback_query.answer("Hint sent.")
        return
    if data == "tags":
        tags_command(app, fake_message("/tags", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "help":
        command2(app, fake_message("/help", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "usage":
        url_distractor(app, fake_message("/usage", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "playlist":
        playlist_command(app, fake_message("/playlist", user_id))
        callback_query.answer("Command executed.")
        return
    callback_query.answer("Unknown command.", show_alert=True)


@app.on_callback_query(filters.regex(r"^clean_option\|"))
# @reply_with_keyboard
def clean_option_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "cookies":
        url_distractor(app, fake_message("/clean cookie", user_id))
        callback_query.answer("Cookies cleaned.")
        return
    elif data == "logs":
        url_distractor(app, fake_message("/clean logs", user_id))
        callback_query.answer("logs cleaned.")
        return
    elif data == "tags":
        url_distractor(app, fake_message("/clean tags", user_id))
        callback_query.answer("tags cleaned.")
        return
    elif data == "format":
        url_distractor(app, fake_message("/clean format", user_id))
        callback_query.answer("format cleaned.")
        return
    elif data == "split":
        url_distractor(app, fake_message("/clean split", user_id))
        callback_query.answer("split cleaned.")
        return
    elif data == "mediainfo":
        url_distractor(app, fake_message("/clean mediainfo", user_id))
        callback_query.answer("mediainfo cleaned.")
        return
    elif data == "subs":
        url_distractor(app, fake_message("/clean subs", user_id))
        callback_query.answer("Subtitle settings cleaned.")
        return
    elif data == "all":
        url_distractor(app, fake_message("/clean all", user_id))
        callback_query.answer("All files cleaned.")
        return
    elif data == "back":
        # Back to the cookies menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 /download_cookie - Download my 5 cookies",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get browser's YT-cookie",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Validate your cookie file",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Upload custom cookie",
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🍪 COOKIES</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return


def fake_message(text, user_id, command=None):
    m = SimpleNamespace()
    m.chat = SimpleNamespace()
    m.chat.id = user_id
    m.chat.first_name = "User"
    m.text = text
    m.first_name = m.chat.first_name
    m.reply_to_message = None
    m.id = 0
    m.from_user = SimpleNamespace()
    m.from_user.id = user_id
    m.from_user.first_name = m.chat.first_name
    if command is not None:
        m.command = command
    return m


# /Mediainfo Command
@app.on_message(filters.command("mediainfo") & filters.private)
# @reply_with_keyboard
def mediainfo_command(app, message):
    user_id = message.chat.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    buttons = [
        [InlineKeyboardButton("✅ ON", callback_data="mediainfo_option|on"), InlineKeyboardButton("❌ OFF", callback_data="mediainfo_option|off")],
        [InlineKeyboardButton("🔚 Close", callback_data="mediainfo_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    app.send_message(
        user_id,
        "Enable or disable sending MediaInfo for downloaded files?",
        reply_markup=keyboard
    )
    send_to_logger(message, "User opened /mediainfo menu.")


@app.on_callback_query(filters.regex(r"^mediainfo_option\|"))
# @reply_with_keyboard
def mediainfo_option_callback(app, callback_query):
    logger.info(f"[MEDIAINFO] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
    if callback_query.data == "mediainfo_option|close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        send_to_logger(callback_query.message, "MediaInfo: closed.")
        return
    if data == "on":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("ON")
        callback_query.edit_message_text("✅ MediaInfo enabled. After downloading, file info will be sent.")
        send_to_logger(callback_query.message, "MediaInfo enabled.")
        callback_query.answer("MediaInfo enabled.")
        return
    if data == "off":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("OFF")
        callback_query.edit_message_text("❌ MediaInfo disabled.")
        send_to_logger(callback_query.message, "MediaInfo disabled.")
        callback_query.answer("MediaInfo disabled.")
        return


def is_mediainfo_enabled(user_id):
    user_dir = os.path.join("users", str(user_id))
    mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
    if not os.path.exists(mediainfo_file):
        return False
    try:
        with open(mediainfo_file, "r", encoding="utf-8") as f:
            return f.read().strip().upper() == "ON"
    except Exception:
        return False


def get_mediainfo_cli(file_path):
    try:
        result = subprocess.run(
            ["mediainfo", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        logger.error(f"mediainfo CLI error: {e}")
        return "MediaInfo CLI error: " + str(e)


def send_mediainfo_if_enabled(user_id, file_path, message):
    if is_mediainfo_enabled(user_id):
        try:
            # Extract msg_id safely
            msg_id = message.id if hasattr(message, "id") else message.get("message_id") or message.get("id")

            mediainfo_text = get_mediainfo_cli(file_path)
            mediainfo_text = mediainfo_text.replace(Config.USERS_ROOT, "")
            mediainfo_path = os.path.splitext(file_path)[0] + "_mediainfo.txt"

            with open(mediainfo_path, "w", encoding="utf-8") as f:
                f.write(mediainfo_text)

            app.send_document(user_id, mediainfo_path, caption="<blockquote>📊 MediaInfo</blockquote>",
                              reply_parameters=ReplyParameters(message_id=msg_id))
            app.send_document(Config.LOGS_ID, mediainfo_path,
                              caption=f"<blockquote>📊 MediaInfo</blockquote> for user {user_id}")

            if os.path.exists(mediainfo_path):
                os.remove(mediainfo_path)

        except Exception as e:
            logger.error(f"Error MediaInfo: {e}")
            send_to_all(message, f"❌ Error sending MediaInfo: {e}")


# SEND COOKIE VIA Document
@app.on_message(filters.document & filters.private)
@reply_with_keyboard
def save_my_cookie(app, message):
    user_id = str(message.chat.id)
    # Check file size
    if message.document.file_size > 100 * 1024:
        send_to_all(message, "❌ The file is too large. Maximum size is 100 KB.")
        return
    # Check extension
    if not message.document.file_name.lower().endswith('.txt'):
        send_to_all(message, "❌ Only files of the following format are allowed .txt.")
        return
    # Download the file to a temporary folder to check the contents
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, message.document.file_name)
        app.download_media(message, file_name=tmp_path)
        try:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # read only the first 4 KB
                if '# Netscape HTTP Cookie File' not in content:
                    send_to_all(message, "❌ The file does not look like cookie.txt (there is no line '# Netscape HTTP Cookie File').")
                    return
        except Exception as e:
            send_to_all(message, f"❌ Error reading file: {e}")
            return
        # If all checks are passed - save the file to the user's folder
        user_folder = f"./users/{user_id}"
        create_directory(user_folder)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_folder, cookie_filename)
        import shutil
        shutil.copyfile(tmp_path, cookie_file_path)
    send_to_user(message, "✅ Cookie file saved")
    send_to_logger(message, f"Cookie file saved for user {user_id}.")


# @reply_with_keyboard
def download_cookie(app, message):
    """
    Shows a menu with buttons to download cookie files from different services.
    """
    user_id = str(message.chat.id)
    
    # Buttons for services
    buttons = [
        [
            InlineKeyboardButton("📺 YouTube", callback_data="download_cookie|youtube"),
            InlineKeyboardButton("📷 Instagram", callback_data="download_cookie|instagram"),
        ],
        [
            InlineKeyboardButton("🐦 Twitter/X", callback_data="download_cookie|twitter"),
            InlineKeyboardButton("🎵 TikTok", callback_data="download_cookie|tiktok"),
        ],
        [
            InlineKeyboardButton("📘 Facebook", callback_data="download_cookie|facebook"),
            InlineKeyboardButton("📝 Your Own", callback_data="download_cookie|own"),
        ],
        [
            InlineKeyboardButton("🔚 Close", callback_data="download_cookie|close"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = """
🍪 **Download Cookie Files**

Choose a service to download the cookie file.
Cookie files will be saved as cookie.txt in your folder.
"""
    app.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        reply_to_message_id=message.id
    )

@app.on_callback_query(filters.regex(r"^download_cookie\|"))
# @reply_with_keyboard
def download_cookie_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "youtube":
        download_and_save_cookie(app, callback_query, Config.YOUTUBE_COOKIE_URL, "youtube")
    elif data == "instagram":
        download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "facebook":
        download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
    elif data == "own":
        app.answer_callback_query(callback_query.id)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="save_as_cookie_hint|close")]
        ])
        app.send_message(
            callback_query.message.chat.id,
            Config.SAVE_AS_COOKIE_HINT,
            reply_to_message_id=callback_query.message.id if hasattr(callback_query.message, 'id') else None,
            reply_markup=keyboard
        )
    elif data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        return

@app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))
def save_as_cookie_hint_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Cookie hint closed.")
        send_to_logger(callback_query.message, "Save as cookie hint closed.")
        return

def download_and_save_cookie(app, callback_query, url, service):
    user_id = str(callback_query.from_user.id)
    
    # Check if URL is not empty
    if not url:
        send_to_user(callback_query.message, f"❌ {service.capitalize()} Cookie URL is not configured!")
        send_to_logger(callback_query.message, f"{service.capitalize()} Cookie URL not configured for user {user_id}.")
        return
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Check if the file extension is .txt
            if not url.lower().endswith('.txt'):
                send_to_user(callback_query.message, f"❌ {service.capitalize()} Cookie URL must point to a .txt file!")
                send_to_logger(callback_query.message, f"{service.capitalize()} Cookie URL is not a .txt file for user {user_id}.")
                return
            
            # Check the file size (maximum 100KB)
            content_size = len(response.content)
            if content_size > 100 * 1024:  # 100KB in bytes
                send_to_user(callback_query.message, f"❌ {service.capitalize()} Cookie file is too large! Maximum size is 100KB, got {content_size // 1024}KB.")
                send_to_logger(callback_query.message, f"{service.capitalize()} Cookie file too large ({content_size} bytes) for user {user_id}.")
                return
            
            # Save the file in the user's folder as cookie.txt
            user_dir = os.path.join("users", user_id)
            create_directory(user_dir)
            cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
            file_path = os.path.join(user_dir, cookie_filename)
            with open(file_path, "wb") as cf:
                cf.write(response.content)
                
            send_to_user(callback_query.message, f"**✅ {service.capitalize()} cookie file downloaded and saved as cookie.txt in your folder.**")
            send_to_logger(callback_query.message, f"{service.capitalize()} cookie file downloaded for user {user_id}.")
        else:
            send_to_user(callback_query.message, f"❌ {service.capitalize()} Cookie URL is not available! (Status: {response.status_code})")
            send_to_logger(callback_query.message, f"Failed to download {service.capitalize()} cookie file for user {user_id}. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        send_to_user(callback_query.message, f"❌ Error downloading {service.capitalize()} cookie file: {str(e)}")
        send_to_logger(callback_query.message, f"Error downloading {service.capitalize()} cookie file for user {user_id}: {str(e)}")


# Caption Editor for Videos
@app.on_message(filters.text & filters.private)
# @reply_with_keyboard
def caption_editor(app, message):
    users_name = message.chat.first_name
    user_id = message.chat.id
    caption = message.text
    video_file_id = message.reply_to_message.video.file_id
    info_of_video = f"\n**Caption:** `{caption}`\n**User id:** `{user_id}`\n**User first name:** `{users_name}`\n**Video file id:** `{video_file_id}`"
    # Sending to logs
    send_to_logger(message, info_of_video)
    app.send_video(user_id, video_file_id, caption=caption)
    app.send_video(Config.LOGS_ID, video_file_id, caption=caption)


@app.on_message(filters.text & filters.private)
# @reply_with_keyboard
def checking_cookie_file(app, message):
    user_id = str(message.chat.id)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    file_path = os.path.join("users", user_id, cookie_filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as cookie:
            cookie_content = cookie.read()
        if cookie_content.startswith("# Netscape HTTP Cookie File"):
            send_to_user(message, "✅ Cookie file exists and has correct format")
            send_to_logger(message, "Cookie file exists and has correct format.")
        else:
            send_to_user(message, "⚠️ Cookie file exists but has incorrect format")
            send_to_logger(message, "Cookie file exists but has incorrect format.")
    else:
        send_to_user(message, "❌ Cookie file is not found.")
        send_to_logger(message, "Cookie file not found.")


# Updating The Cookie File.
# @reply_with_keyboard
def save_as_cookie_file(app, message):
    user_id = str(message.chat.id)
    content = message.text[len(Config.SAVE_AS_COOKIE_COMMAND):].strip()
    new_cookie = ""

    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            new_cookie = "\n".join(lines).strip()
        else:
            new_cookie = content
    else:
        new_cookie = content

    processed_lines = []
    for line in new_cookie.splitlines():
        if "\t" not in line:
            line = re.sub(r' {2,}', '\t', line)
        processed_lines.append(line)
    final_cookie = "\n".join(processed_lines)

    if final_cookie:
        send_to_all(message, "**✅ User provided a new cookie file.**")
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_cookie)
        send_to_user(message, f"**✅ Cookie successfully updated:**\n`{final_cookie}`")
        send_to_logger(message, f"Cookie file updated for user {user_id}.")
    else:
        send_to_user(message, "**❌ Not a valid cookie.**")
        send_to_logger(message, f"Invalid cookie content provided by user {user_id}.")

# URL Extractor
@app.on_message(filters.text & filters.private)
# @reply_with_keyboard
def video_url_extractor(app, message):
    global active_downloads
    check_user(message)
    user_id = message.chat.id
    user_dir = os.path.join("users", str(user_id))
    format_file = os.path.join(user_dir, "format.txt")

    # By default, ask for quality if a specific format is not selected
    should_ask = True
    saved_format = None
    if os.path.exists(format_file):
        with open(format_file, "r", encoding="utf-8") as f:
            fmt = f.read().strip()
        # Do not ask only if the format is set and it is NOT "ALWAYS_ASK"
        if fmt != "ALWAYS_ASK":
            should_ask = False
            saved_format = fmt

    if should_ask:
        url, video_start_with, _, _, tags, _, tag_error = extract_url_range_tags(message.text)
        # Add tag error check
        if tag_error:
            wrong, example = tag_error
            app.send_message(user_id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_to_message_id=message.id)
            return
        ask_quality_menu(app, message, url, tags, video_start_with)
        return

    # This code is executed only if the user has selected a specific format
    with playlist_errors_lock:
        keys_to_remove = [k for k in playlist_errors if k.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del playlist_errors[key]
            
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
        
    full_string = message.text
    # Also add tag error check here
    url, video_start_with, video_end_with, playlist_name, tags, tags_text, tag_error = extract_url_range_tags(full_string)
    if tag_error:
        wrong, example = tag_error
        app.send_message(user_id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_to_message_id=message.id)
        return
    
    # Checking the range limit
    if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
        return
    
    if url:
        users_first_name = message.chat.first_name
        send_to_logger(message, f"User entered a **url**\n **user's name:** {users_first_name}\nURL: {full_string}")
        for j in range(len(Config.BLACK_LIST)):
            if Config.BLACK_LIST[j] in full_string:
                send_to_all(message, "User entered a porn content. Cannot be downloaded.")
                return
        # --- TikTok: auto-tag profile and no title ---
        is_tiktok = is_tiktok_url(url)
        auto_tags = get_auto_tags(url, tags)
        all_tags = tags + auto_tags
        tags_text_full = ' '.join(all_tags)
        video_count = video_end_with - video_start_with + 1
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]
        save_user_tags(user_id, all_tags)
        
        # Create quality_key based on saved format for caching
        quality_key = None
        if saved_format:
            # Convert format to quality_key for caching
            if "height<=144" in saved_format:
                quality_key = "144p"
            elif "height<=240" in saved_format:
                quality_key = "240p"
            elif "height<=360" in saved_format:
                quality_key = "360p"
            elif "height<=480" in saved_format:
                quality_key = "480p"
            elif "height<=720" in saved_format:
                quality_key = "720p"
            elif "height<=1080" in saved_format:
                quality_key = "1080p"
            elif "height<=1440" in saved_format:
                quality_key = "1440p"
            elif "height<=2160" in saved_format:
                quality_key = "2160p"
            elif "height<=4320" in saved_format:
                quality_key = "4320p"
            elif "bestvideo+bestaudio" in saved_format or "bv*[vcodec*=avc1]+ba" in saved_format:
                quality_key = "bestvideo"
            elif saved_format == "best":
                quality_key = "best"
            else:
                # For custom formats, we use the format hash as quality_key
                quality_key = f"custom_{hashlib.md5(saved_format.encode()).hexdigest()[:8]}"
        
        logger.info(f"video_url_extractor: using saved format '{saved_format}', quality_key='{quality_key}'")
        
        # --- Pass title='' for TikTok, otherwise as usual ---
        if is_tiktok:
            down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text_full, force_no_title=True, format_override=saved_format, quality_key=quality_key)
        else:
            down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text_full, format_override=saved_format, quality_key=quality_key)
    else:
        send_to_all(message, f"**User entered like this:** {full_string}\n{Config.ERROR1}")

# ############################################################################################

# Send Message to Logger

def send_to_logger(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # Print (user_id, "-", msg)
    safe_send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)

# Send Message to User Only

def send_to_user(message, msg):
    user_id = message.chat.id
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN, reply_to_message_id=message.id)

# Send Message to All ...

def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    safe_send_message(Config.LOGS_ID, msg_with_id, parse_mode=enums.ParseMode.MARKDOWN)
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN, reply_to_message_id=message.id)

def progress_bar(*args):
    # It is expected that Pyrogram will cause Progress_BAR with five parameters:
    # Current, Total, Speed, ETA, File_SIZE, and then additionally your Progress_args (User_id, Msg_id, Status_text)
    if len(args) < 8:
        return
    current, total, speed, eta, file_size, user_id, msg_id, status_text = args[:8]
    try:
        app.edit_message_text(user_id, msg_id, status_text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")


def truncate_caption(
    title: str,
    description: str,
    url: str,
    tags_text: str = '',
    max_length: int = 1000  # Reduced from 1024 to be safe with encoding issues
) -> Tuple[str, str, str, str, str, bool]:
    """
    Returns: (title_html, pre_block, blockquote_content, tags_block, link_block, was_truncated)
    """
    title_html = f'<b>{title}</b>' if title else ''
    # Pattern for finding timestamps at the beginning of a line (00:00, 0:00:00, 0.00, etc.)
    timestamp_pattern = r'^\s*(\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}\.\d{2}(?:\.\d{2})?)\s+.*'

    lines = description.split('\n') if description else []
    pre_block_lines = []
    post_block_lines = []

    # Split lines into timestamps and main text
    for line in lines:
        if re.match(timestamp_pattern, line):
            pre_block_lines.append(line)
        else:
            post_block_lines.append(line)
    
    pre_block_str = '\n'.join(pre_block_lines)
    post_block_str = '\n'.join(post_block_lines).strip()

    tags_block = (tags_text.strip() + '\n') if tags_text and tags_text.strip() else ''
    # --- Add bot name next to the link ---
    bot_name = getattr(Config, 'BOT_NAME', None) or 'bot'
    bot_mention = f' @{bot_name}' if not bot_name.startswith('@') else f' {bot_name}'
    link_block = f'<a href="{url}">🔗 Video URL</a>{bot_mention}'
    
    was_truncated = False
    
    # Calculate constant overhead more accurately
    overhead = len(tags_block) + len(link_block)
    if title_html:
        overhead += len(title_html) + 2 # for '\n\n'
    if pre_block_str:
        overhead += len(pre_block_str) + 1 # for '\n'
    
    # Calculate limit for blockquote (taking into account <blockquote> tags)
    blockquote_overhead = len('<blockquote expandable></blockquote>') + 1 # for '\n'
    blockquote_limit = max_length - overhead - blockquote_overhead
    
    # Ensure we have some space for content
    if blockquote_limit <= 0:
        # If no space for blockquote, truncate everything except essential parts
        if title_html:
            title_html = title_html[:max_length-10] + '...'
        pre_block_str = ''
        blockquote_content = ''
        was_truncated = True
    else:
        blockquote_content = post_block_str
        if len(blockquote_content) > blockquote_limit:
            blockquote_content = blockquote_content[:blockquote_limit - 4] + '...'
            was_truncated = True

    # Final check and possible truncation of pre_block
    current_length = overhead + len(blockquote_content) + blockquote_overhead
    if current_length > max_length:
        # Calculate how much space we can give to pre_block
        pre_block_limit = max_length - (overhead - len(pre_block_str) - 1) - len(blockquote_content) - blockquote_overhead
        if pre_block_limit > 0 and pre_block_limit < len(pre_block_str):
            pre_block_str = pre_block_str[:pre_block_limit-4] + '...'
            was_truncated = True
        else: # if even with truncated pre_block it does not fit, truncate everything
             pre_block_str = ''

    if pre_block_str:
        pre_block_str += '\n'

    # Assembly caption
    cap = ''
    if title_html:
        cap += title_html + '\n\n'
    if pre_block_str:
        cap += pre_block_str + '\n'
    cap += f'<blockquote expandable>{blockquote_content}</blockquote>\n'
    if tags_block:
        cap += tags_block
    cap += link_block
    
    # Final safety check - ensure we never exceed max_length
    if len(cap) > max_length:
        # Emergency truncation - keep only essential parts
        essential_parts = []
        if title_html:
            essential_parts.append(title_html)
        if tags_block:
            essential_parts.append(tags_block.strip())
        if link_block:
            essential_parts.append(link_block)
        
        cap = '\n\n'.join(essential_parts)
        if len(cap) > max_length:
            # More aggressive truncation - remove HTML tags for calculation
            plain_text = re.sub(r'<[^>]+>', '', cap)
            if len(plain_text) > max_length:
                # Truncate plain text and rebuild HTML
                truncated_text = plain_text[:max_length-10] + '...'
                cap = truncated_text
            else:
                cap = cap[:max_length-3] + '...'
        was_truncated = True
    
    return title_html, pre_block_str, blockquote_content, tags_block, link_block, was_truncated

# @reply_with_keyboard
def send_videos(
    message,
    video_abs_path: str,
    caption: str,
    duration: int,
    thumb_file_path: str,
    info_text: str,
    msg_id: int,
    full_video_title: str,
    tags_text: str = '',
):
    import re
    import os
    user_id = message.chat.id
    text = message.text or ""
    m = re.search(r'https?://[^\s\*]+', text)
    video_url = m.group(0) if m else ""
    temp_desc_path = os.path.join(os.path.dirname(video_abs_path), "full_description.txt")
    was_truncated = False

    # --- Define the size of the preview/video ---
    width = None
    height = None
    if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
        if "youtube.com/shorts/" in video_url or "/shorts/" in video_url:
            width, height = 360, 640
        else:
            width, height = 640, 360
    else:
        # For the rest - define the size of the video dynamically
        try:
            width, height, _ = get_video_info_ffprobe(video_abs_path)
        except Exception as e:
            logger.error(f"[FFPROBE BYPASS] Error while processing video{video_abs_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            width, height = 0, 0

    try:
        # Logic simplified: use tags that were already generated in down_and_up.
        # Use original title for caption, but truncated description
        title_html, pre_block, blockquote_content, tags_block, link_block, was_truncated = truncate_caption(
            title=caption,  # Original title for caption
            description=full_video_title,  # Full description to be truncated
            url=video_url,
            tags_text=tags_text, # Use final tags for calculation
            max_length=1000  # Reduced for safety
        )
        # Form HTML caption: title outside the quote, timecodes outside the quote, description in the quote, tags and link outside the quote
        cap = ''
        if title_html:
            cap += title_html + '\n\n'
        if pre_block:
            cap += pre_block + '\n'
        cap += f'<blockquote expandable>{blockquote_content}</blockquote>\n'
        if tags_block:
            cap += tags_block
        cap += link_block

        try:
            # First try sending with full caption
            video_msg = app.send_video(
                chat_id=user_id,
                video=video_abs_path,
                caption=cap,
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,
                thumb=thumb_file_path,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n**Video duration:** __{TimeFormatter(duration*1000)}__\n\n__📤 Uploading Video...__"
                ),
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            if "MEDIA_CAPTION_TOO_LONG" in str(e):
                logger.info("Caption too long, trying with minimal caption")
                # If the caption is too long, try sending only with the main information
                minimal_cap = ''
                if title_html:
                    minimal_cap += title_html + '\n\n'
                minimal_cap += link_block
                
                try:
                    # Try sending with minimal caption
                    video_msg = app.send_video(
                        chat_id=user_id,
                        video=video_abs_path,
                        caption=minimal_cap,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        thumb=thumb_file_path,
                        progress=progress_bar,
                        progress_args=(
                            user_id,
                            msg_id,
                            f"{info_text}\n**Video duration:** __{TimeFormatter(duration*1000)}__\n__📤 Uploading Video...__"
                        ),
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Error sending video with minimal caption: {e}")
                    # If even the minimal caption does not work, send without caption
                    video_msg = app.send_video(
                        chat_id=user_id,
                        video=video_abs_path,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        thumb=thumb_file_path,
                        progress=progress_bar,
                        progress_args=(
                            user_id,
                            msg_id,
                            f"{info_text}\n**Video duration:** __{TimeFormatter(duration*1000)}__\n__📤 Uploading Video...__"
                        ),
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
            else:
                # If the error is not related to the length of the caption, pass it further
                raise e
        if was_truncated and full_video_title:
            with open(temp_desc_path, "w", encoding="utf-8") as f:
                f.write(full_video_title)
        if was_truncated and os.path.exists(temp_desc_path):
            try:
                user_doc_msg = app.send_document(
                    chat_id=user_id,
                    document=temp_desc_path,
                    caption="<blockquote>📝 if you want to change video caption - reply to video with new text</blockquote>",
                    reply_to_message_id=message.id,
                    parse_mode=enums.ParseMode.HTML
                )
                safe_forward_messages(Config.LOGS_ID, user_id, [user_doc_msg.id])
            except Exception as e:
                logger.error(f"Error sending full description file: {e}")
        return video_msg
    finally:
        if os.path.exists(temp_desc_path):
            try:
                os.remove(temp_desc_path)
            except Exception as e:
                logger.error(f"Error removing temporary description file: {e}")

# ####################################################################################

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2 ** 10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") +\
        ((str(hours) + "h, ") if hours else "") +\
        ((str(minutes) + "m, ") if minutes else "") +\
        ((str(seconds) + "s, ") if seconds else "") +\
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def split_video_2(dir, video_name, video_path, video_size, max_size, duration):
    """
    Split a video into multiple parts

    Args:
        dir: Directory path
        video_name: Name for the video
        video_path: Path to the video file
        video_size: Size of the video in bytes
        max_size: Maximum size for each part
        duration: Duration of the video

    Returns:
        dict: Dictionary with video parts information
    """
    rounds = (math.floor(video_size / max_size)) + 1
    n = duration / rounds
    caption_lst = []
    path_lst = []

    try:
        if rounds > 20:
            logger.warning(f"Video will be split into {rounds} parts, which may be excessive")

        for x in range(rounds):
            start_time = x * n
            end_time = (x * n) + n

            # Ensure end_time doesn't exceed duration
            end_time = min(end_time, duration)

            cap_name = video_name + " - Part " + str(x + 1)
            target_name = os.path.join(dir, cap_name + ".mp4")

            caption_lst.append(cap_name)
            path_lst.append(target_name)

            try:
                # Use progress logging
                logger.info(f"Splitting video part {x+1}/{rounds}: {start_time:.2f}s to {end_time:.2f}s")
                ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=target_name)

                # Verify the split was successful
                if not os.path.exists(target_name) or os.path.getsize(target_name) == 0:
                    logger.error(f"Failed to create split part {x+1}: {target_name}")
                else:
                    logger.info(f"Successfully created split part {x+1}: {target_name} ({os.path.getsize(target_name)} bytes)")

            except Exception as e:
                logger.error(f"Error splitting video part {x+1}: {e}")
                # If a part fails, we continue with the others

        split_vid_dict = {
            "video": caption_lst,
            "path": path_lst
        }

        logger.info(f"Video split into {len(path_lst)} parts successfully")
        return split_vid_dict

    except Exception as e:
        logger.error(f"Error in video splitting process: {e}")
        # Return what we have so far
        split_vid_dict = {
            "video": caption_lst,
            "path": path_lst,
            "duration": video_duration
        }
        return split_vid_dict

def get_duration_thumb_(dir, video_path, thumb_name):
    # Generate a short unique name for the thumbnail
    thumb_hash = hashlib.md5(thumb_name.encode()).hexdigest()[:10]
    thumb_dir = os.path.abspath(os.path.join(dir, thumb_hash + ".jpg"))
    try:
        _, _, duration = get_video_info_ffprobe(video_path)
        duration = int(duration)
    except Exception as e:
        logger.error(f"[FFPROBE BYPASS] Error while processing video {video_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        duration = 0
    
    # Get original video dimensions
    # orig_w, orig_h = clip.w, clip.h
    orig_w = int(str(clip.w).strip().split()[0]) if clip.w else 1920
    orig_h = int(str(clip.h).strip().split()[0]) if clip.h else 1080
    # Determine optimal thumbnail size based on video aspect ratio
    aspect_ratio = orig_w / orig_h
    max_dimension = 640  # Maximum width or height
    
    if aspect_ratio > 1.5:  # Wide/horizontal video (16:9, etc.)
        thumb_w = max_dimension
        thumb_h = int(max_dimension / aspect_ratio)
    elif aspect_ratio < 0.75:  # Tall/vertical video (9:16, etc.)
        thumb_h = max_dimension
        thumb_w = int(max_dimension * aspect_ratio)
    else:  # Square-ish video (1:1, 4:3, etc.)
        if orig_w >= orig_h:
            thumb_w = max_dimension
            thumb_h = int(max_dimension / aspect_ratio)
        else:
            thumb_h = max_dimension
            thumb_w = int(max_dimension * aspect_ratio)
    
    # Ensure minimum size
    thumb_w = max(thumb_w, 240)
    thumb_h = max(thumb_h, 240)
    
    # Create thumbnail frame
    frame = clip.get_frame(2)
    from PIL import Image
    
    # Convert frame to PIL Image and resize to exact thumbnail size
    img = Image.fromarray(frame)
    img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    
    # Save the thumbnail directly (no padding needed)
    img.save(thumb_dir, 'JPEG', quality=85)
    
    clip.close()
    return duration, thumb_dir

def get_duration_thumb(message, dir_path, video_path, thumb_name):
    """
    Captures a thumbnail at 2 seconds into the video and retrieves video duration.
    Creates thumbnail with same aspect ratio as video (no black bars).

    Args:
        message: The message object
        dir_path: Directory path for the thumbnail
        video_path: Path to the video file
        thumb_name: Name for the thumbnail

    Returns:
        tuple: (duration, thumbnail_path) or None if error
    """
    # Generate a short unique name for the thumbnail
    thumb_hash = hashlib.md5(thumb_name.encode()).hexdigest()[:10]
    thumb_dir = os.path.abspath(os.path.join(dir_path, thumb_hash + ".jpg"))

    # FFPROBE COMMAND to GET Video Dimensions and Duration
    ffprobe_size_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]
    
    ffprobe_duration_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        # First check if video file exists
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            send_to_all(message, f"❌ Video file not found: {os.path.basename(video_path)}")
            return None

        # Get video dimensions
        size_result = subprocess.check_output(ffprobe_size_command, stderr=subprocess.STDOUT, universal_newlines=True).strip()
        # if 'x' in size_result:
            # orig_w, orig_h = map(int, size_result.split('x'))
        if 'x' in size_result:
            dimensions = size_result.split('x')
            orig_w = int(str(dimensions[0]).strip().split()[0]) if dimensions[0] else 1920
            orig_h = int(str(dimensions[1]).strip().split()[0]) if dimensions[1] else 1080            
        else:
            # Fallback to default horizontal orientation
            orig_w, orig_h = 1920, 1080
            logger.warning(f"Could not determine video dimensions, using default: {orig_w}x{orig_h}")
        
        # Determine optimal thumbnail size based on video aspect ratio
        aspect_ratio = orig_w / orig_h
        max_dimension = 640  # Maximum width or height
        
        if aspect_ratio > 1.5:  # Wide/horizontal video (16:9, etc.)
            thumb_w = max_dimension
            thumb_h = int(max_dimension / aspect_ratio)
        elif aspect_ratio < 0.75:  # Tall/vertical video (9:16, etc.)
            thumb_h = max_dimension
            thumb_w = int(max_dimension * aspect_ratio)
        else:  # Square-ish video (1:1, 4:3, etc.)
            if orig_w >= orig_h:
                thumb_w = max_dimension
                thumb_h = int(max_dimension / aspect_ratio)
            else:
                thumb_h = max_dimension
                thumb_w = int(max_dimension * aspect_ratio)
        
        # Ensure minimum size
        thumb_w = max(thumb_w, 240)
        thumb_h = max(thumb_h, 240)
        
        # FFMPEG Command to create thumbnail with calculated dimensions
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", "2",         # Seek to 2 Seconds
            "-vframes", "1",    # Capture 1 Frame
            "-vf", f"scale={thumb_w}:{thumb_h}",  # Scale to exact thumbnail size
            thumb_dir
        ]

        # Run ffmpeg command to create thumbnail
        ffmpeg_result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        if ffmpeg_result.returncode != 0:
            logger.error(f"Error creating thumbnail: {ffmpeg_result.stderr}")

        # Run ffprobe command to get duration
        result = subprocess.check_output(ffprobe_duration_command, stderr=subprocess.STDOUT, universal_newlines=True)

        try:
            # duration = int(float(result))
            duration = int(float(str(result).strip().split()[0])) if result else 0
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing video duration: {e}, result was: {result}")
            duration = 0

        # Verify thumbnail was created
        if not os.path.exists(thumb_dir):
            logger.warning(f"Thumbnail not created at {thumb_dir}, using default")
            # Create a blank thumbnail as fallback
            create_default_thumbnail(thumb_dir, thumb_w, thumb_h)

        return duration, thumb_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"Command execution error: {e.stderr if hasattr(e, 'stderr') else e}")
        send_to_all(message, f"❌ Error processing video: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing video: {e}")
        send_to_all(message, f"❌ Error processing video: {e}")
        return None

def create_default_thumbnail(thumb_path, width=480, height=480):
    """Create a default thumbnail when normal thumbnail creation fails"""
    try:
        # Create a black image with specified dimensions (square by default)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}",
            "-frames:v", "1",
            thumb_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Created default {width}x{height} thumbnail at {thumb_path}")
    except Exception as e:
        logger.error(f"Failed to create default thumbnail: {e}")

def write_logs(message, video_url, video_title):
    ts = str(math.floor(time.time()))
    data = {"ID": str(message.chat.id), "timestamp": ts,
            "name": message.chat.first_name, "urls": str(video_url), "title": video_title}
    db.child("bot").child("tgytdlp_bot").child("logs").child(str(message.chat.id)).child(str(ts)).set(data)
    logger.info("Log for user added")
# ####################################################################################
# ####################################################################################

# ########################################
# Down_and_audio function
# ########################################

# @reply_with_keyboard
def down_and_audio(app, message, url, tags, quality_key=None, playlist_name=None, video_count=1, video_start_with=1):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    playlist_indices = []
    playlist_msg_ids = []  
        
    user_id = message.chat.id
    logger.info(f"down_and_audio called: url={url}, quality_key={quality_key}, video_count={video_count}, video_start_with={video_start_with}")
    
    # We define a playlist not only by the number of videos, but also by the presence of a range in the URL
    original_text = message.text or message.caption or ""
    is_playlist = video_count > 1 or is_playlist_with_range(original_text)
    requested_indices = list(range(video_start_with, video_start_with + video_count)) if is_playlist else []
    cached_videos = {}
    uncached_indices = []
    if quality_key and is_playlist:
        cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, requested_indices)
        uncached_indices = [i for i in requested_indices if i not in cached_videos]
        # First, repost the cached ones
        if cached_videos:
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        app.forward_messages(
                            chat_id=user_id,
                            from_chat_id=Config.LOGS_ID,
                            message_ids=[cached_videos[index]]
                        )
                    except Exception as e:
                        logger.error(f"down_and_audio: error reposting cached audio index={index}: {e}")
            if len(uncached_indices) == 0:
                app.send_message(user_id, f"✅ Playlist audio sent from cache ({len(cached_videos)}/{len(requested_indices)} files).", reply_to_message_id=message.id)
                send_to_logger(message, f"Playlist audio sent from cache (quality={quality_key}) to user{user_id}")
                return
            else:
                app.send_message(user_id, f"📥 {len(cached_videos)}/{len(requested_indices)} audio sent from cache, downloading missing ones...", reply_to_message_id=message.id)
    elif quality_key and not is_playlist:
        cached_ids = get_cached_message_ids(url, quality_key)
        if cached_ids:
            try:
                app.forward_messages(
                    chat_id=user_id,
                    from_chat_id=Config.LOGS_ID,
                    message_ids=cached_ids
                )
                app.send_message(user_id, "✅ Audio sent from cache.", reply_to_message_id=message.id)
                send_to_logger(message, f"Audio sent from cache (quality={quality_key}) to user{user_id}")
                return
            except Exception as e:
                logger.error(f"Error reposting audio from cache: {e}")
                save_to_video_cache(url, quality_key, [], clear=True)
                app.send_message(user_id, "⚠️ Failed to get audio from cache, starting new download...", reply_to_message_id=message.id)
    else:
        logger.info(f"down_and_audio: quality_key is None, skipping cache check")

    anim_thread = None
    stop_anim = threading.Event()
    proc_msg = None
    proc_msg_id = None
    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    audio_files = []
    try:
        # Check if there is a saved waiting time
        user_dir = os.path.join("users", str(user_id))
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")

        # We send the initial message
        if os.path.exists(flood_time_file):
            with open(flood_time_file, 'r') as f:
                wait_time = int(f.read().strip())
                hours = wait_time // 3600
                minutes = (wait_time % 3600) // 60
                seconds = wait_time % 60
                time_str = f"{hours}h {minutes}m {seconds}s"
                proc_msg = app.send_message(user_id, f"⚠️ Telegram has limited message sending.\n⏳ Please wait: {time_str}\nTo update timer send URL again 2 times.")
        else:
            proc_msg = app.send_message(user_id, "⚠️ Telegram has limited message sending.\n⏳ Please wait: \nTo update timer send URL again 2 times.")

        # We are trying to replace with "Download started"
        try:
            app.edit_message_text(
                chat_id=user_id,
                message_id=proc_msg.id,
                text="Download started"
            )
            if os.path.exists(flood_time_file):
                os.remove(flood_time_file)
        except FloodWait as e:
            wait_time = e.value
            os.makedirs(user_dir, exist_ok=True)
            with open(flood_time_file, 'w') as f:
                f.write(str(wait_time))
            return
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return

        # If there is no flood error, send a normal message (only once)
        proc_msg = app.send_message(user_id, "🔄 Processing...", reply_to_message_id=message.id)
        proc_msg_id = proc_msg.id
        status_msg = app.send_message(user_id, "🎙️ Audio is processing...")
        hourglass_msg = app.send_message(user_id, "⏳ Please wait...")
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id
        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Check if there's enough disk space (estimate 500MB per audio file)
        user_folder = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_folder)

        if not check_disk_space(user_folder, 500 * 1024 * 1024 * video_count):
            send_to_user(message, "❌ Not enough disk space to download the audio files.")
            return

        check_user(message)

        # Reset of the flag of errors for the new launch of the playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # Check if cookie.txt exists in the user's folder
        user_cookie_path = os.path.join(user_folder, "cookie.txt")
        if os.path.exists(user_cookie_path):
            cookie_file = user_cookie_path
        else:
            # If not in the user's folder, copy from the global folder
            global_cookie_path = Config.COOKIE_FILE_PATH
            if os.path.exists(global_cookie_path):
                try:
                    create_directory(user_folder)
                    import shutil
                    shutil.copy2(global_cookie_path, user_cookie_path)
                    logger.info(f"Copied global cookie file to user {user_id} folder for audio download")
                    cookie_file = user_cookie_path
                except Exception as e:
                    logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                    cookie_file = None
            else:
                cookie_file = None
        last_update = 0
        current_total_process = ""
        successful_uploads = 0

        def progress_hook(d):
            nonlocal last_update
            # Check the timeout
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            if current_time - last_update < 0.2:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                try:
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n📥 Downloading audio:\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "finished":
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\n📥 Downloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "error":
                try:
                    safe_edit_message_text(user_id, proc_msg_id, "Error occurred during audio download.")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time

        def try_download_audio(url, current_index):
            nonlocal current_total_process
            ytdl_opts = {
               'format': 'ba',
               'postprocessors': [{
                  'key': 'FFmpegExtractAudio',
                  'preferredcodec': 'mp3',
                  'preferredquality': '192',
               },
               {
                  'key': 'EmbedThumbnail'   # equivalent to --embed-thumbnail
               },
               {
                  'key': 'FFmpegMetadata'   # equivalent to --add-metadata
               }                  
                ],
               'prefer_ffmpeg': True,
               'extractaudio': True,
               'playlist_items': str(current_index + video_start_with),
               'outtmpl': os.path.join(user_folder, "%(title).50s.%(ext)s"),
               'progress_hooks': [progress_hook],
               'extractor_args': {
                  'generic': ['impersonate=chrome']
               },
               'referer': url,
               'geo_bypass': True,
               'check_certificate': False,
               'live_from_start': True,
            }
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                ytdl_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                ytdl_opts['cookiefile'] = cookie_file   
            try:
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                if "entries" in info_dict:
                    entries = info_dict["entries"]
                    if len(entries) > 1:  # If the video in the playlist is more than one
                        actual_index = current_index + video_start_with - 1  # -1 because indexes in entries start from 0
                        if actual_index < len(entries):
                            info_dict = entries[actual_index]
                        else:
                            raise Exception(f"Audio index {actual_index + 1} out of range (total {len(entries)})")
                    else:
                        # If there is only one video in the playlist, just download it
                        info_dict = entries[0]  # Just take the first video

                try:
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\n> __📥 Downloading audio using format: ba...__")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    ydl.download([url])
                
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                error_text = str(e)
                logger.error(f"DownloadError: {error_text}")
                # Send full error message with instructions immediately
                send_to_all(
                    message,
                    "> Check [here](https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites) if your site supported\n"
                    "> You may need `cookie` for downloading this audio. First, clean your workspace via **/clean** command\n"
                    "> For Youtube - get `cookie` via **/download_cookie** command. For any other supported site - send your own cookie ([guide1](https://t.me/c/2303231066/18)) ([guide2](https://t.me/c/2303231066/22)) and after that send your audio link again.\n"
                    f"────────────────\n❌ Error downloading: {error_text}"
                )
                return None
            except Exception as e:
                error_text = str(e)
                logger.error(f"Audio download attempt failed: {e}")
                
                # Check if this is a "No videos found in playlist" error
                if "No videos found in playlist" in error_text or "Story might have expired" in error_text:
                    error_message = f"❌ No content found at index {current_index + video_start_with}"
                    send_to_all(message, error_message)
                    logger.info(f"Skipping item at index {current_index} (no content found)")
                    return "SKIP"
                else:
                    send_to_user(message, f"❌ Unknown error: {e}")
                return None

        if is_playlist and quality_key:
            indices_to_download = uncached_indices
        else:
            indices_to_download = range(video_count)
        for idx, current_index in enumerate(indices_to_download):
            current_index = current_index - video_start_with  # for numbering/display
            total_process = f"""
**📶 Total Progress**
> **Audio:** {idx + 1} / {len(indices_to_download)}
"""

            current_total_process = total_process

            # Determine rename_name based on the incoming playlist_name:
            if playlist_name and playlist_name.strip():
                # A new name for the playlist is explicitly set - let's use it
                rename_name = sanitize_filename(f"{playlist_name.strip()} - Part {idx + video_start_with}")
            else:
                # No new name set - extract name from metadata
                rename_name = None

            info_dict = try_download_audio(url, current_index)

            if info_dict is None:
                with playlist_errors_lock:
                    error_key = f"{user_id}_{playlist_name}"
                    if error_key not in playlist_errors:
                        playlist_errors[error_key] = True

                break

            successful_uploads += 1

            # Check if info_dict is None before accessing it
            if info_dict is None:
                logger.error("info_dict is None, cannot proceed with audio processing")
                send_to_user(message, "❌ Failed to extract audio information")
                break

            audio_title = info_dict.get("title", "audio")
            audio_title = sanitize_filename(audio_title)
            
            # If rename_name is not set, set it equal to audio_title
            if rename_name is None:
                rename_name = audio_title

            # Find the downloaded audio file
            allfiles = os.listdir(user_folder)
            files = [fname for fname in allfiles if fname.endswith('.mp3')]
            files.sort()
            if not files:
                send_to_all(message, f"Skipping unsupported file type in playlist at index {idx + video_start_with}")
                continue

            downloaded_file = files[0]
            write_logs(message, url, downloaded_file)

            if rename_name == audio_title:
                caption_name = audio_title  # Original title for caption
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(downloaded_file)
                if final_name != downloaded_file:
                    old_path = os.path.join(user_folder, downloaded_file)
                    new_path = os.path.join(user_folder, final_name)
                    try:
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                    except Exception as e:
                        logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                        final_name = downloaded_file
            else:
                ext = os.path.splitext(downloaded_file)[1]
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(rename_name + ext)
                caption_name = rename_name  # Original title for caption
                old_path = os.path.join(user_folder, downloaded_file)
                new_path = os.path.join(user_folder, final_name)

                if os.path.exists(new_path):
                    try:
                        os.remove(new_path)
                    except Exception as e:
                        logger.error(f"Error removing existing file {new_path}: {e}")

                try:
                    os.rename(old_path, new_path)
                except Exception as e:
                    logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                    final_name = downloaded_file
                    caption_name = audio_title  # Original title for caption

            audio_file = os.path.join(user_folder, final_name)
            if not os.path.exists(audio_file):
                send_to_user(message, "Audio file not found after download.")
                continue

            audio_files.append(audio_file)

            try:
                full_bar = "🟩" * 10
                safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n📤 Uploading audio file...\n{full_bar}   100.0%")
            except Exception as e:
                logger.error(f"Error updating upload status: {e}")

            # We form a text with tags and a link for audio
            tags_for_final = tags if isinstance(tags, list) else (tags.split() if isinstance(tags, str) else [])
            tags_text_final = generate_final_tags(url, tags_for_final, info_dict)
            tags_block = (tags_text_final.strip() + '\n') if tags_text_final and tags_text_final.strip() else ''
            bot_name = getattr(Config, 'BOT_NAME', None) or 'bot'
            bot_mention = f' @{bot_name}' if not bot_name.startswith('@') else f' {bot_name}'
            # Use original audio_title for caption, not sanitized caption_name
            caption_with_link = f"{audio_title}\n{tags_block}[🔗 Audio URL]({url}){bot_mention}"
            
            try:
                audio_msg = app.send_audio(chat_id=user_id, audio=audio_file, caption=caption_with_link, reply_to_message_id=message.id)
                forwarded_msg = safe_forward_messages(Config.LOGS_ID, user_id, [audio_msg.id])
                
                # Save to cache after sending audio
                if quality_key and forwarded_msg:
                    if isinstance(forwarded_msg, list):
                        msg_ids = [m.id for m in forwarded_msg]
                    else:
                        msg_ids = [forwarded_msg.id]
                    
                    if is_playlist:
                        # For playlists, save to playlist cache with index
                        current_video_index = idx + video_start_with
                        logger.info(f"down_and_audio: saving to playlist cache: index={current_video_index}, msg_ids={msg_ids}")
                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], msg_ids, original_text=message.text or message.caption or "")
                        cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                        logger.info(f"Checking the cache immediately after writing: {cached_check}")
                        playlist_indices.append(current_video_index)
                        playlist_msg_ids.extend(msg_ids)  # We use msg_ids instead of forwarded_msgs
                    else:
                        # For single audios, save to regular cache
                        logger.info(f"down_and_audio: saving to video cache: msg_ids={msg_ids}")
                        save_to_video_cache(url, quality_key, msg_ids, original_text=message.text or message.caption or "", user_id=user_id)
            except Exception as send_error:
                logger.error(f"Error sending audio: {send_error}")
                send_to_user(message, f"❌ Failed to send audio: {send_error}")
                continue

            # Clean up the audio file after sending
            try:
                send_mediainfo_if_enabled(user_id, audio_file, message)
                os.remove(audio_file)
            except Exception as e:
                logger.error(f"Failed to delete audio file {audio_file}: {e}")

            # Add delay between uploads for playlists
            if idx < len(indices_to_download) - 1:
                threading.Event().wait(2)

        if successful_uploads == len(indices_to_download):
            success_msg = f"✅ Audio successfully downloaded and sent - {len(indices_to_download)} files uploaded.\n{Config.CREDITS_MSG}"
        else:
            success_msg = f"⚠️ Partially completed - {successful_uploads}/{len(indices_to_download)} audio files uploaded.\n{Config.CREDITS_MSG}"
            
        try:
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
        except Exception as e:
            logger.error(f"Error updating final status: {e}")

        send_to_logger(message, success_msg)

        if is_playlist and quality_key:
            total_sent = len(cached_videos) + successful_uploads
            app.send_message(user_id, f"✅Playlist audio sent: {total_sent}/{len(requested_indices)} files.", reply_to_message_id=message.id)
            send_to_logger(message, f"Playlist audio sent: {total_sent}/{len(requested_indices)} files (quality={quality_key}) to user{user_id}")

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, "⏰ Download cancelled due to timeout (2 hours)")
            send_to_logger(message, "Download cancelled due to timeout")
        else:
            logger.error(f"Error in audio download: {e}")
            send_to_user(message, f"❌ Failed to download audio: {e}")
    finally:
        # Always clean up resources
        stop_anim.set()
        if anim_thread:
            anim_thread.join(timeout=1)  # Wait for animation thread with timeout

        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}")

        # Clean up any remaining audio files
        for audio_file in audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                logger.error(f"Failed to delete file {audio_file}: {e}")

        set_active_download(user_id, False)
        clear_download_start_time(user_id)  # Cleaning the start time

        # Clean up temporary files
        try:
            cleanup_user_temp_files(user_id)
        except Exception as e:
            logger.error(f"Error cleaning up temp files for user {user_id}: {e}")

        # Reset playlist errors if this was a playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]



# ########################################
# Download_and_up function
# ########################################
#@reply_with_keyboard
def down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=None, quality_key=None):
    """
    Now if part of the playlist range is already cached, we first repost the cached indexes, then download and cache the missing ones, without finishing after reposting part of the range.
    """
    playlist_indices = []
    playlist_msg_ids = []    
    found_type = None
    user_id = message.chat.id
    logger.info(f"down_and_up called: url={url}, quality_key={quality_key}, format_override={format_override}, video_count={video_count}, video_start_with={video_start_with}")
    subs_enabled = is_subs_enabled(user_id)
    if subs_enabled and is_youtube_url(url):
        found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        available_langs = _subs_check_cache.get(
            f"{url}_{user_id}_{'auto' if found_type == 'auto' else 'normal'}_langs",
            []
        )
        # First, download the subtitles separately
        user_dir = os.path.join("users", str(user_id))
        video_dir = user_dir
        subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                    
        if not subs_path:
            app.send_message(user_id, "⚠️ Failed to download subtitles", reply_to_message_id=message.id)
            #continue

    # We define a playlist not only by the number of videos, but also by the presence of a range in the URL
    original_text = message.text or message.caption or ""
    is_playlist = video_count > 1 or is_playlist_with_range(original_text)
    requested_indices = list(range(video_start_with, video_start_with + video_count)) if is_playlist else []
    cached_videos = {}
    uncached_indices = []
    if quality_key and is_playlist:
        cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, requested_indices)
        uncached_indices = [i for i in requested_indices if i not in cached_videos]
        # First, repost the cached ones
        if cached_videos:
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        app.forward_messages(
                            chat_id=user_id,
                            from_chat_id=Config.LOGS_ID,
                            message_ids=[cached_videos[index]]
                        )
                    except Exception as e:
                        logger.error(f"down_and_up: error reposting cached video index={index}: {e}")
            if len(uncached_indices) == 0:
                app.send_message(user_id, f"✅ Playlist videos sent from cache ({len(cached_videos)}/{len(requested_indices)} files).", reply_to_message_id=message.id)
                send_to_logger(message, f"Playlist videos sent from cache (quality={quality_key}) to user {user_id}")
                return
            else:
                app.send_message(user_id, f"📥 {len(cached_videos)}/{len(requested_indices)} videos sent from cache, downloading missing ones...", reply_to_message_id=message.id)
    elif quality_key and not is_playlist:
        #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        subs_enabled = is_subs_enabled(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
        if not need_subs:
            cached_ids = get_cached_message_ids(url, quality_key)
            if cached_ids:
                #found_type = None
                try:
                    app.forward_messages(
                        chat_id=user_id,
                        from_chat_id=Config.LOGS_ID,
                        message_ids=cached_ids
                    )
                    app.send_message(user_id, "✅ Video sent from cache.", reply_to_message_id=message.id)
                    send_to_logger(message, f"Video sent from cache (quality={quality_key}) to user {user_id}")
                    return
                except Exception as e:
                    logger.error(f"Error reposting video from cache: {e}")
                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                    subs_enabled = is_subs_enabled(user_id)
                    auto_mode = get_user_subs_auto_mode(user_id)
                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    if not need_subs:
                        save_to_video_cache(url, quality_key, [], clear=True)
                    else:
                        logger.info("Video with subs (subs.txt found) is not cached!")
                    app.send_message(user_id, "⚠️ Unable to get video from cache, starting new download...", reply_to_message_id=message.id)
    else:
        logger.info(f"down_and_up: quality_key is None, skipping cache check")

    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    anim_thread = None
    stop_anim = threading.Event()
    proc_msg = None
    proc_msg_id = None
    try:
        # Check if there is a saved waiting time
        user_dir = os.path.join("users", str(user_id))
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")

        # We send the initial message
        if os.path.exists(flood_time_file):
            with open(flood_time_file, 'r') as f:
                wait_time = int(f.read().strip())
                hours = wait_time // 3600
                minutes = (wait_time % 3600) // 60
                seconds = wait_time % 60
                time_str = f"{hours}h {minutes}m {seconds}s"
                proc_msg = app.send_message(user_id, f"⚠️ Telegram has limited message sending.\n⏳ Please wait: {time_str}\nTo update timer send URL again 2 times.")
        else:
            proc_msg = app.send_message(user_id, "⚠️ Telegram has limited message sending.\n⏳ Please wait: \nTo update timer send URL again 2 times.")

        # We are trying to replace with "Download started"
        try:
            app.edit_message_text(
                chat_id=user_id,
                message_id=proc_msg.id,
                text="Download started"
            )
            # If you managed to replace, then there is no flood error
            if os.path.exists(flood_time_file):
                os.remove(flood_time_file)
        except FloodWait as e:
            # Update the counter
            wait_time = e.value
            os.makedirs(user_dir, exist_ok=True)
            with open(flood_time_file, 'w') as f:
                f.write(str(wait_time))
            return
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return

        # If there is no flood error, send a normal message
        proc_msg = app.send_message(user_id, "🔄 Processing...", reply_to_message_id=message.id)
        proc_msg_id = proc_msg.id
        error_message = ""
        status_msg = None
        status_msg_id = None
        hourglass_msg = None
        hourglass_msg_id = None
        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Check if there's enough disk space (estimate 2GB per video)
        user_dir_name = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_dir_name)

        # We only need disk space for one video at a time, since files are deleted after upload
        if not check_disk_space(user_dir_name, 2 * 1024 * 1024 * 1024):
            send_to_user(message, f"❌ Not enough disk space to download videos.")
            return

        check_user(message)

        # Reset of the flag of errors for the new launch of the playlist
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # if use_default_format is True, then do not take from format.txt, but use default ones
        custom_format_path = os.path.join(user_dir_name, "format.txt")
        use_default_format = False
        if not format_override and os.path.exists(custom_format_path):
            with open(custom_format_path, "r", encoding="utf-8") as f:
                custom_format = f.read().strip()
            if custom_format == "ALWAYS_ASK":
                use_default_format = True
        if use_default_format:
            format_override = None

        if format_override:
            attempts = [{'format': format_override, 'prefer_ffmpeg': True, 'merge_output_format': 'mp4'}]
        else:
            # if use_default_format is True, then do not take from format.txt, but use default ones
            if use_default_format:
                attempts = [
                    {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best', 'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                    {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                ]
            else:
                if os.path.exists(custom_format_path):
                    with open(custom_format_path, "r", encoding="utf-8") as f:
                        custom_format = f.read().strip()
                    if custom_format.lower() == "best":
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': False}]
                    else:
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': True, 'merge_output_format': output_format}]
                else:
                    attempts = [
                        {'format': 'bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best',
                        'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                        {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best',
                        'prefer_ffmpeg': True, 'merge_output_format': output_format, 'extract_flat': False},
                        {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                    ]

        status_msg = app.send_message(user_id, "📽 Video is processing...")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        # Get info_dict to estimate the size of the selected quality
        try:
            ydl_opts = {'quiet': True}
            user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
            if os.path.exists(user_cookie_path):
                ydl_opts['cookiefile'] = user_cookie_path
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                pre_info = ydl.extract_info(url, download=False)
            # Check that pre_info is not None
            if pre_info is None:
                logger.warning("pre_info is None, skipping size check")
                pre_info = {}
            elif 'entries' in pre_info and isinstance(pre_info['entries'], list) and pre_info['entries']:
                pre_info = pre_info['entries'][0]
        except Exception as e:
            logger.warning(f"Failed to extract info for size check: {e}")
            pre_info = {}

        # Find format for selected quality_key
        selected_format = None
        for f in pre_info.get('formats', []):
            w = f.get('width')
            h = f.get('height')
            if w and h:
                qk = get_quality_by_min_side(w, h)
                if str(qk) == str(quality_key):
                    selected_format = f
                    break

        # If you did not find the format, STOP downloading!
        #if not selected_format:
            #logger.warning(f"[SIZE CHECK] Could not determine format for quality_key={quality_key}. Download will not start.")
            #app.send_message(
                #user_id,
                #"Unable to determine the file size for the selected quality. Please try another quality or check your cookies.",
                #reply_to_message_id=message.id
            #)
            #return

        
        # Checking the limit
        #from _config import Config
        BYTES_IN_GIB = 1024 ** 3
        max_size_gb = getattr(Config, 'MAX_FILE_SIZE', 10)
        max_size_bytes = int(max_size_gb * BYTES_IN_GIB)
        # Get the file size
        if selected_format is None:
            logger.warning("selected_format is None, skipping size check")
            filesize = 0
            allowed = True  # Allow download if we can't determine the size
        else:
            filesize = selected_format.get('filesize') or selected_format.get('filesize_approx')
            if not filesize:
                # fallback on rating
                tbr = selected_format.get('tbr')
                duration = selected_format.get('duration')
                if tbr and duration:
                    filesize = float(tbr) * float(duration) * 125
                else:
                    width = selected_format.get('width')
                    height = selected_format.get('height')
                    duration = selected_format.get('duration')
                    if width and height and duration:
                        filesize = int(width) * int(height) * float(duration) * 0.07
                    else:
                        filesize = 0

            allowed = check_file_size_limit(selected_format, max_size_bytes=max_size_bytes)
        
        # Secure file size logging
        if filesize > 0:
            size_gb = filesize/(1024**3)
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, determined size={size_gb:.2f} GB, limit={max_size_gb} GB, allowed={allowed}")
        else:
            logger.info(f"[SIZE CHECK] quality_key={quality_key}, size unknown, limit={max_size_gb} GB, allowed={allowed}")

        if not allowed:
            app.send_message(
                user_id,
                f"❌ The file size exceeds the {max_size_gb} GB limit. Please select a smaller file within the allowed size.",
                reply_to_message_id=message.id
            )
            send_to_logger(message, f"❌ The file size exceeds the {max_size_gb} GB limit. Please select a smaller file within the allowed size.")
            logger.warning(f"[SIZE CHECK] Download for quality_key={quality_key} was blocked due to size limit.")
            return
        else:
            logger.info(f"[SIZE CHECK] Download for quality_key={quality_key} is allowed and will proceed.")

        current_total_process = ""
        last_update = 0
        full_bar = "🟩" * 10
        first_progress_update = True  # Flag for tracking the first update

        def progress_func(d):
            nonlocal last_update, first_progress_update
            # Check the timaut
            if check_download_timeout(user_id):
                raise Exception(f"Download timeout exceeded ({Config.DOWNLOAD_TIMEOUT // 3600} hours)")
            current_time = time.time()
            if current_time - last_update < 1.5:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                try:
                    # With the first renewal of progress, we delete the first posts Processing
                    if first_progress_update:
                        try:
                            # We get more messages to search for all Processing messages
                            messages = app.get_chat_history(user_id, limit=20)
                            processing_messages = []
                            download_started_messages = []
                            for msg in messages:
                                if msg.text == "🔄 Processing...":
                                    processing_messages.append(msg.id)
                                elif msg.text == "Download started":
                                    download_started_messages.append(msg.id)
                            # We delete the first 2 promission messages (if there are more than 1)
                            if len(processing_messages) >= 2:
                                safe_delete_messages(chat_id=user_id, message_ids=processing_messages[-2:], revoke=True)
                            # We delete the first 2 Download Started Message (if there are more than 1)
                            if len(download_started_messages) >= 2:
                                safe_delete_messages(chat_id=user_id, message_ids=download_started_messages[-2:], revoke=True)
                        except Exception as e:
                            logger.error(f"Error deleting first processing messages: {e}")
                        first_progress_update = False

                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            elif d.get("status") == "error":
                logger.error("Error occurred during download.")
                send_to_all(message, "❌ Sorry... Some error occurred during download.")
            last_update = current_time

        successful_uploads = 0

        def try_download(url, attempt_opts):
            nonlocal current_total_process, error_message
            common_opts = {
                'playlist_items': str(current_index),  # We use only current_index for playlists
                'outtmpl': os.path.join(user_dir_name, "%(title).50s.%(ext)s"),
                'postprocessors': [
                {
                   'key': 'EmbedThumbnail'   # equivalent to --embed-thumbnail
                },
                {
                   'key': 'FFmpegMetadata'   # equivalent to --add-metadata
                }                  
                ],                
                'extractor_args': {
                   'generic': ['impersonate=chrome']
                },
                'referer': url,
                'geo_bypass': True,
                'check_certificate': False,
                'live_from_start': True
            }
            
            # Check subtitle availability for YouTube videos (but don't download them here)
            if is_youtube_url(url):
                subs_lang = get_user_subs_language(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                if subs_lang and subs_lang not in ["OFF"]:
                    # Check availability with AUTO mode
                    #available_langs = get_available_subs_languages(url, user_id, auto_only=auto_mode)
                    # Flexible check: search for an exact match or any language from the group
                    lang_prefix = subs_lang.split('-')[0]
                    found = False
                    for l in available_langs:
                        if l == subs_lang or l.startswith(subs_lang + '-') or l.startswith(subs_lang + '.') \
                           or l == lang_prefix or l.startswith(lang_prefix + '-') or l.startswith(lang_prefix + '.'):
                            found = True
                            break
                    if not found:
                        app.send_message(
                            user_id,
                            f"⚠️ Subtitles for {LANGUAGES[subs_lang]['flag']} {LANGUAGES[subs_lang]['name']} not found for this video. Download without subtitles.",
                            reply_to_message_id=message.id
                        )
            
            # Check if we need to use --no-cookies for this domain
            if is_no_cookie_domain(url):
                common_opts['cookiefile'] = None  # Equivalent to --no-cookies
                logger.info(f"Using --no-cookies for domain: {url}")
            else:
                # Check if cookie.txt exists in the user's folder
                user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
                if os.path.exists(user_cookie_path):
                    common_opts['cookiefile'] = user_cookie_path
                else:
                    # If not in the user's folder, copy from the global folder
                    global_cookie_path = Config.COOKIE_FILE_PATH
                    if os.path.exists(global_cookie_path):
                        try:
                            user_dir = os.path.join("users", str(user_id))
                            create_directory(user_dir)
                            import shutil
                            shutil.copy2(global_cookie_path, user_cookie_path)
                            logger.info(f"Copied global cookie file to user {user_id} folder")
                            common_opts['cookiefile'] = user_cookie_path
                        except Exception as e:
                            logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                            common_opts['cookiefile'] = None
                    else:
                        common_opts['cookiefile'] = None
            
            # If this is not a playlist with a range, add --no-playlist to the URL with the list parameter
            if not is_playlist and 'list=' in url:
                common_opts['noplaylist'] = True
            
            is_hls = ("m3u8" in url.lower())
            if not is_hls:
                common_opts['progress_hooks'] = [progress_func]
            ytdl_opts = {**common_opts, **attempt_opts}
            try:
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                if "entries" in info_dict:
                    entries = info_dict["entries"]
                    if not entries:
                        raise Exception(f"No videos found in playlist at index {current_index}")
                    if len(entries) > 1:  # If the video in the playlist is more than one
                        if current_index < len(entries):
                            info_dict = entries[current_index]
                        else:
                            raise Exception(f"Video index {current_index} out of range (total {len(entries)})")
                    else:
                        # If there is only one video in the playlist, just download it
                        info_dict = entries[0]  # Just take the first video

                if ("m3u8" in url.lower()) or (info_dict and info_dict.get("protocol") == "m3u8_native"):
                    is_hls = True
                    # if "format" in ytdl_opts:
                    # del ytdl_opts["format"]
                    ytdl_opts["downloader"] = "ffmpeg"
                    ytdl_opts["hls_use_mpegts"] = True
                try:
                    if is_hls:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n__Detected HLS stream.\n📥 Downloading...__")
                    else:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n> __📥 Downloading using format: {ytdl_opts.get('format', 'default')}...__")
                except Exception as e:
                    logger.error(f"Status update error: {e}")
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    if is_hls:
                        cycle_stop = threading.Event()
                        cycle_thread = start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop)
                        try:
                            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                                ydl.download([url])
                        finally:
                            cycle_stop.set()
                            cycle_thread.join(timeout=1)
                    else:
                        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                            ydl.download([url])
                try:
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except yt_dlp.utils.DownloadError as e:
                nonlocal error_message
                error_message = str(e)
                logger.error(f"DownloadError: {error_message}")
                # Send full error message with instructions immediately
                send_to_all(
                    message,                   
                    "> Check [here](https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites) if your site supported\n"
                    "> You may need `cookie` for downloading this video. First, clean your workspace via **/clean** command\n"
                    "> For Youtube - get `cookie` via **/download_cookie** command. For any other supported site - send your own cookie ([guide1](https://t.me/c/2303231066/18)) ([guide2](https://t.me/c/2303231066/22)) and after that send your video link again.\n"
                    f"────────────────\n❌ Error downloading: {error_message}"
                )
                return None
            except Exception as e:
                error_message = str(e)
                logger.error(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
				
                # Check if this is a "No videos found in playlist" error
                if "No videos found in playlist" in str(e):
                    error_message = f"❌ No videos found in playlist at index {current_index + 1}."
                    send_to_all(message, error_message)
                    logger.info(f"Stopping download: playlist item at index {current_index} (no video found)")
                    return "STOP"  # New special value for full stop

                send_to_user(message, f"❌ Unknown error: {e}")
                return None

        if is_playlist and quality_key:
            indices_to_download = uncached_indices
        else:
            indices_to_download = range(video_count)
        for idx, current_index in enumerate(indices_to_download):
            x = current_index - video_start_with  # Don't add quality if size is unknown
            total_process = f"""
**📶 Total Progress**
> **Video:** {idx + 1} / {len(indices_to_download)}
"""
            current_total_process = total_process

            # Determine rename_name based on the incoming playlist_name:
            if playlist_name and playlist_name.strip():
                # A new name for the playlist is explicitly set - let's use it
                rename_name = sanitize_filename(f"{playlist_name.strip()} - Part {idx + video_start_with}")
            else:
                # No new name set - extract name from metadata
                rename_name = None

            info_dict = None
            skip_item = False
            stop_all = False
            for attempt in attempts:
                result = try_download(url, attempt)
                if result == "STOP":
                    stop_all = True
                    break
                elif result == "SKIP":
                    skip_item = True
                    break
                elif result is not None:
                    info_dict = result
                    break

            if stop_all:
                logger.info(f"Stopping all downloads due to playlist error at index {current_index}")
                break

            if skip_item:
                logger.info(f"Skipping item at index {current_index} (no video content)")
                continue

            if info_dict is None:
                with playlist_errors_lock:
                    error_key = f"{user_id}_{playlist_name}"
                    if error_key not in playlist_errors:
                        playlist_errors[error_key] = True

                break

            successful_uploads += 1

            video_id = info_dict.get("id", None)
            original_video_title = info_dict.get("title", None)  # Original title with emojis
            full_video_title = info_dict.get("description", original_video_title)
            video_title = sanitize_filename(original_video_title) if original_video_title else "video"  # Sanitized for file operations

            # --- Use new centralized function for all tags ---
            tags_list = tags_text.split() if tags_text else []
            tags_text_final = generate_final_tags(url, tags_list, info_dict)
            save_user_tags(user_id, tags_text_final.split())

           # If rename_name is not set, set it equal to video_title
            if rename_name is None:
                rename_name = video_title

            dir_path = os.path.join("users", str(user_id))

            # Save the full name to a file
            full_title_path = os.path.join(dir_path, "full_title.txt")
            try:
                with open(full_title_path, "w", encoding="utf-8") as f:
                    f.write(full_video_title if full_video_title else original_video_title)
            except Exception as e:
                logger.error(f"Error saving full title: {e}")

            info_text = f"""
{total_process}
**📋 Video Info**
> **Number:** {idx + video_start_with}
> **Title:** {original_video_title}
> **ID:** {video_id}
"""

            try:
                safe_edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n{full_bar}   100.0%\n__☑️ Downloaded video.\n📤 Processing for upload...__")
            except Exception as e:
                logger.error(f"Status update error after download: {e}")

            dir_path = os.path.join("users", str(user_id))
            allfiles = os.listdir(dir_path)
            files = [fname for fname in allfiles if fname.endswith(('.mp4', '.mkv', '.webm', '.ts'))]
            files.sort()
            if not files:
                send_to_all(message, f"Skipping unsupported file type in playlist at index {idx + video_start_with}")
                continue

            downloaded_file = files[0]
            write_logs(message, url, downloaded_file)

            if rename_name == video_title:
                caption_name = original_video_title  # Original title for caption
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(downloaded_file)
                if final_name != downloaded_file:
                    old_path = os.path.join(dir_path, downloaded_file)
                    new_path = os.path.join(dir_path, final_name)
                    try:
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                    except Exception as e:
                        logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                        final_name = downloaded_file
            else:
                ext = os.path.splitext(downloaded_file)[1]
                # Sanitize filename for disk storage while keeping original title for caption
                final_name = sanitize_filename(rename_name + ext)
                caption_name = rename_name  # Original title for caption
                old_path = os.path.join(dir_path, downloaded_file)
                new_path = os.path.join(dir_path, final_name)

                if os.path.exists(new_path):
                    try:
                        os.remove(new_path)
                    except Exception as e:
                        logger.error(f"Error removing existing file {new_path}: {e}")

                try:
                    os.rename(old_path, new_path)
                except Exception as e:
                    logger.error(f"Error renaming file from {old_path} to {new_path}: {e}")
                    final_name = downloaded_file
                    caption_name = original_video_title  # Original title for caption

            user_vid_path = os.path.join(dir_path, final_name)
            if final_name.lower().endswith((".webm", ".ts")):
                try:
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{info_text}\n{full_bar}   100.0%\nConverting video using ffmpeg... ⏳")
                except Exception as e:
                    logger.error(f"Error updating status before conversion: {e}")

                mp4_basename = sanitize_filename(os.path.splitext(final_name)[0]) + ".mp4"
                mp4_file = os.path.join(dir_path, mp4_basename)

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i", user_vid_path,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    mp4_file
                ]
                try:
                    subprocess.run(ffmpeg_cmd, check=True)
                    os.remove(user_vid_path)
                    user_vid_path = mp4_file
                    final_name = mp4_basename
                except Exception as e:
                    send_to_all(message, f"❌ Conversion to MP4 failed: {e}")
                    break

            after_rename_abs_path = os.path.abspath(user_vid_path)
            # --- YouTube thumbnail logic (priority over ffmpeg) ---
            youtube_thumb_path = None
            thumb_dir = None
            duration = 0
            
            # Try to download YouTube thumbnail first
            if ("youtube.com" in url or "youtu.be" in url):
                try:
                    yt_id = video_id or None
                    if not yt_id:
                        try:
                            yt_id = extract_youtube_id(url)
                        except Exception:
                            yt_id = None
                    if yt_id:
                        youtube_thumb_path = os.path.join(dir_path, f"yt_thumb_{yt_id}.jpg")
                        download_thumbnail(yt_id, youtube_thumb_path, url)
                        if os.path.exists(youtube_thumb_path):
                            thumb_dir = youtube_thumb_path
                            logger.info(f"Using YouTube thumbnail: {youtube_thumb_path}")
                except Exception as e:
                    logger.warning(f"YouTube thumbnail download failed: {e}")
            
            # Get video duration (always needed)
            try:
                ffprobe_duration_command = [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                    user_vid_path
                ]
                result = subprocess.check_output(ffprobe_duration_command, stderr=subprocess.STDOUT, universal_newlines=True)
                #duration = int(float(result))
                duration = int(float(str(result).strip().split()[0])) if result else 0
            except Exception as e:
                logger.warning(f"Failed to get video duration: {e}")
                duration = 0
            
            # Use ffmpeg thumbnail only as fallback (when YouTube thumbnail failed)
            if not thumb_dir:
                result = get_duration_thumb(message, dir_path, user_vid_path, sanitize_filename(caption_name))
                if result is None:
                    logger.warning("Failed to create ffmpeg thumbnail fallback")
                    thumb_dir = None
                else:
                    duration_from_ffmpeg, thumb_dir_ffmpeg = result
                    thumb_dir = thumb_dir_ffmpeg
                    if duration == 0:  # Use duration from ffmpeg if we couldn't get it with ffprobe
                        duration = duration_from_ffmpeg
                    logger.info(f"Using ffmpeg thumbnail fallback: {thumb_dir}")
            
            # Check for the existence of a preview and create a default one if needed
            if thumb_dir and not os.path.exists(thumb_dir):
                logger.warning(f"Thumbnail not found at {thumb_dir}, creating default")
                create_default_thumbnail(os.path.join(dir_path, "default_thumb.jpg"))
                thumb_dir = os.path.join(dir_path, "default_thumb.jpg")
                if not os.path.exists(thumb_dir):
                    logger.warning("Failed to create default thumbnail, continuing without thumbnail")
                    thumb_dir = None

            video_size_in_bytes = os.path.getsize(user_vid_path)
            video_size = humanbytes(int(video_size_in_bytes))
            max_size = get_user_split_size(user_id)  # 1.95 GB - close to Telegram's 2GB limit with 50MB safety margin
            if int(video_size_in_bytes) > max_size:
                safe_edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n{full_bar}   100.0%\n__⚠️ Your video size ({video_size}) is too large.__\n__Splitting file...__ ✂️")
                returned = split_video_2(dir_path, sanitize_filename(caption_name), after_rename_abs_path, int(video_size_in_bytes), max_size, duration)
                caption_lst = returned.get("video")
                path_lst = returned.get("path")
                # Accumulate all IDs of split video parts
                split_msg_ids = []
                for p in range(len(caption_lst)):
                    part_result = get_duration_thumb(message, dir_path, path_lst[p], sanitize_filename(caption_lst[p]))
                    if part_result is None:
                        continue
                    part_duration, splited_thumb_dir = part_result
                    # --- TikTok: Don't Pass Title ---
                    video_msg = send_videos(message, path_lst[p], '' if force_no_title else caption_lst[p], part_duration, splited_thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                    #found_type = None
                    try:
                        forwarded_msgs = safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                        logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                        if forwarded_msgs:
                            logger.info(f"down_and_up: collecting forwarded message IDs for split video: {[m.id for m in forwarded_msgs]}")
                            if is_playlist:
                                # For playlists, save to playlist cache with index
                                current_video_index = x + video_start_with
                                rounded_quality_key = quality_key
                                try:
                                    if quality_key.endswith('p'):
                                        rounded_quality_key = f"{ceil_to_popular(int(quality_key[:-1]))}p"
                                except Exception:
                                    pass
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), rounded_quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), rounded_quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                            else:
                                # Accumulate IDs of parts for split video
                                split_msg_ids.extend([m.id for m in forwarded_msgs])
                        else:
                            logger.info(f"down_and_up: collecting video_msg.id for split video: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # Accumulate IDs of parts for split video
                                split_msg_ids.append(video_msg.id)
                    except Exception as e:
                        logger.error(f"Error forwarding video to logger: {e}")
                        logger.info(f"down_and_up: collecting video_msg.id after error for split video: {video_msg.id}")
                        if is_playlist:
                            # For playlists, save to playlist cache with video index
                            current_video_index = x + video_start_with
                            #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                            subs_enabled = is_subs_enabled(user_id)
                            auto_mode = get_user_subs_auto_mode(user_id)
                            need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                            if not need_subs:
                                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                            else:
                                logger.info("Video with subtitles (subs.txt found) is not cached!")
                            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                            logger.info(f"Checking the cache immediately after writing: {cached_check}")
                            playlist_indices.append(current_video_index)
                            playlist_msg_ids.append(video_msg.id)
                        else:
                            # Accumulate IDs of parts for split video
                            split_msg_ids.append(video_msg.id)
                    safe_edit_message_text(user_id, proc_msg_id,
                                          f"{info_text}\n{full_bar}   100.0%\n__📤 Splitted part {p + 1} file uploaded__")
                    if p < len(caption_lst) - 1:
                        threading.Event().wait(2)
                    os.remove(splited_thumb_dir)
                    send_mediainfo_if_enabled(user_id, path_lst[p], message)
                    os.remove(path_lst[p])
                
                # Save all parts of split video to cache after the loop is completed
                if split_msg_ids and not is_playlist:
                    # Remove duplicates
                    split_msg_ids = list(dict.fromkeys(split_msg_ids))
                    logger.info(f"down_and_up: saving all split video parts to cache: {split_msg_ids}")
                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                    subs_enabled = is_subs_enabled(user_id)
                    auto_mode = get_user_subs_auto_mode(user_id)
                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    if not need_subs:
                        save_to_video_cache(url, quality_key, split_msg_ids, original_text=message.text or message.caption or "")
                    else:
                        logger.info("Split video with subtitles is not cached!")
                os.remove(thumb_dir)
                os.remove(user_vid_path)
                success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
                safe_edit_message_text(user_id, proc_msg_id, success_msg)
                send_to_logger(message, "Video upload completed with file splitting.")
                break
            else:
                if final_name:
                    # Read the full name from the file
                    full_caption = caption_name
                    try:
                        if os.path.exists(full_title_path):
                            with open(full_title_path, "r", encoding="utf-8") as f:
                                full_caption = f.read().strip()
                    except Exception as e:
                        logger.error(f"Error reading full title: {e}")

                    # Check for preview existence before sending
                    if thumb_dir and not os.path.exists(thumb_dir):
                        logger.warning(f"Thumbnail not found before sending, creating default")
                        create_default_thumbnail(os.path.join(dir_path, "default_thumb.jpg"))
                        thumb_dir = os.path.join(dir_path, "default_thumb.jpg")
                        if not os.path.exists(thumb_dir):
                            logger.warning("Failed to create default thumbnail before sending, continuing without thumbnail")
                            thumb_dir = None

                    try:
                        # --- TikTok: Don't Pass Title ---
                        # Embed subtitles if needed (only for single videos, not playlists)
                        is_playlist_mode = video_count > 1 or is_playlist_with_range(original_text)
                        if not is_playlist_mode:
                            # Check the limits for subtitles
                            subs_enabled = is_subs_enabled(user_id)
                            # Get the real size of the video
                            try:
                                width, height, _ = get_video_info_ffprobe(after_rename_abs_path)
                                real_file_size = min(width, height)
                            except Exception as e:
                                logger.error(f"[FFPROBE BYPASS] Error while processing video {after_rename_abs_path}: {e}")
                                import traceback
                                logger.error(traceback.format_exc())
                                width, height = 0, 0
                                real_file_size = 0
                            auto_mode = get_user_subs_auto_mode(user_id)
                            if subs_enabled and is_youtube_url(url) and min(width, height) <= Config.MAX_SUB_QUALITY:
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                                    
                                    # First, download the subtitles separately
                                    #video_dir = os.path.dirname(after_rename_abs_path)
                                    #subs_path = download_subtitles_ytdlp(url, user_id, video_dir, available_langs)
                                    
                                    #if not subs_path:
                                        #app.send_message(user_id, "⚠️ Failed to download subtitles", reply_to_message_id=message.id)
                                        #continue
                                    
                                    # Get the real size of the file after downloading
                                    real_file_size = os.path.getsize(after_rename_abs_path) if os.path.exists(after_rename_abs_path) else 0
                                    
                                    # Create info_dict with real data
                                    real_info = {
                                        'duration': duration,  # Real duration
                                        'filesize': real_file_size,  # Real file size
                                        'filesize_approx': real_file_size
                                    }
                                    
                                    if check_subs_limits(real_info, quality_key):
                                        status_msg = app.send_message(user_id, "⚠️ Embedding subtitles may take a long time (up to 1 min per 1 min of video)!\n🔥 Starting to burn subtitles...")
                                        def tg_update_callback(progress, eta):
                                            blocks = int(progress * 10)
                                            bar = '🟩' * blocks + '⬜️' * (10 - blocks)
                                            percent = int(progress * 100)
                                            try:
                                                app.edit_message_text(
                                                    chat_id=user_id,
                                                    message_id=status_msg.id,
                                                    text=f"🔥 Embedding subtitles...\n{bar} {percent}%\nETA: {eta} min"
                                                )
                                            except Exception as e:
                                                logger.error(f"Failed to update subtitle progress: {e}")
                                        # Embed subtitles and get the result
                                        embed_result = embed_subs_to_video(after_rename_abs_path, user_id, tg_update_callback, app=app, message=message)
                                        try:
                                            if embed_result:
                                                app.edit_message_text(
                                                    chat_id=user_id,
                                                    message_id=status_msg.id,
                                                    text="Subtitles successfully embedded! ✅"
                                                )
                                            else:
                                                # Check if there are subtitle files
                                                video_dir = os.path.dirname(after_rename_abs_path)
                                                video_name = os.path.splitext(os.path.basename(after_rename_abs_path))[0]
                                                subs_files = glob.glob(os.path.join(video_dir, f"{video_name}*.srt"))
                                                
                                                if not subs_files:
                                                    app.edit_message_text(
                                                        chat_id=user_id,
                                                        message_id=status_msg.id,
                                                        text="⚠️ Subtitles not found for this video"
                                                    )
                                                else:
                                                    app.edit_message_text(
                                                        chat_id=user_id,
                                                        message_id=status_msg.id,
                                                        text="⚠️ Subtitles not embedded: exceeded size/duration limits"
                                                    )
                                        except Exception as e:
                                            logger.error(f"Failed to update subtitle progress (final): {e}")
                                    else:
                                        app.send_message(user_id, "ℹ️ Subtitles cannot be embedded due to limits (quality/duration/size)", reply_to_message_id=message.id)
                                else:
                                    app.send_message(user_id, "ℹ️ Subtitles are not available for the selected language", reply_to_message_id=message.id)
                            # Clear
                            clear_subs_check_cache()
                        video_msg = send_videos(message, after_rename_abs_path, '' if force_no_title else original_video_title, duration, thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                        
                        #found_type = None
                        try:
                            forwarded_msgs = safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                            logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                            if forwarded_msgs:
                                logger.info(f"down_and_up: saving to cache with forwarded message IDs: {[m.id for m in forwarded_msgs]}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                                else:
                                    # For single videos, save to regular cache
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        save_to_video_cache(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                            else:
                                logger.info(f"down_and_up: saving to cache with video_msg.id: {video_msg.id}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.append(video_msg.id)
                                else:
                                    #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                    subs_enabled = is_subs_enabled(user_id)
                                    auto_mode = get_user_subs_auto_mode(user_id)
                                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                    if not need_subs:
                                        # For single videos, save to regular cache
                                        save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                                    else:
                                        logger.info("Video with subtitles (subs.txt found) is not cached!")
                        except Exception as e:
                            logger.error(f"Error forwarding video to logger: {e}")
                            logger.info(f"down_and_up: saving to cache with video_msg.id after error: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # For single videos, save to regular cache
                                #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                                subs_enabled = is_subs_enabled(user_id)
                                auto_mode = get_user_subs_auto_mode(user_id)
                                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                                if not need_subs:
                                    save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                                else:
                                    logger.info("Video with subtitles (subs.txt found) is not cached!")
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{info_text}\n{full_bar}   100.0%\n**🎞 Video duration:** __{TimeFormatter(duration * 1000)}__\n1 file uploaded.")
                        send_mediainfo_if_enabled(user_id, after_rename_abs_path, message)
                        os.remove(after_rename_abs_path)
                        if thumb_dir and os.path.exists(thumb_dir):
                            os.remove(thumb_dir)
                        threading.Event().wait(2)
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        logger.error(traceback.format_exc())
                        send_to_all(message, f"❌ Error sending video: {str(e)}")
                        continue
        if successful_uploads == len(indices_to_download):
            success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n{Config.CREDITS_MSG}"
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
            send_to_logger(message, success_msg)

        if is_playlist and quality_key:
            total_sent = len(cached_videos) + successful_uploads
            app.send_message(user_id, f"✅ Playlist videos sent: {total_sent}/{len(requested_indices)} files.", reply_to_message_id=message.id)
            send_to_logger(message, f"Playlist videos sent: {total_sent}/{len(requested_indices)} files (quality={quality_key}) to user {user_id}")

    except Exception as e:
        if "Download timeout exceeded" in str(e):
            send_to_user(message, "⏰ Download cancelled due to timeout (2 hours)")
            send_to_logger(message, "Download cancelled due to timeout")
        else:
            logger.error(f"Error in video download: {e}")
            send_to_user(message, f"❌ Failed to download video: {e}")
        
        # Clean up temporary files on error
        try:
            cleanup_user_temp_files(user_id)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temp files after error for user {user_id}: {cleanup_error}")
    finally:
        set_active_download(user_id, False)
        clear_download_start_time(user_id)  # Clear the download start time
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        # Clean up temporary files
        try:
            cleanup_user_temp_files(user_id)
        except Exception as e:
            logger.error(f"Error cleaning up temp files for user {user_id}: {e}")

        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}")

        # --- ADDED: summary of cache after cycle ---
        if is_playlist and playlist_indices and playlist_msg_ids:
            #found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
            subs_enabled = is_subs_enabled(user_id)
            auto_mode = get_user_subs_auto_mode(user_id)
            need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
            if not need_subs:
                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, playlist_indices, playlist_msg_ids, original_text=message.text or message.caption or "")
            else:
                logger.info("Video with subtitles (subs.txt found) is not cached!")
            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, playlist_indices)
            summary = "\n".join([f"Index {idx}: msg_id={cached_check.get(idx, '-')}" for idx in playlist_indices])
            logger.info(f"[SUMMARY] Playlist cache (quality {quality_key}):\n{summary}")

#########################################

# YT-DLP HOOK

def ytdlp_hook(d):
    logger.info(d['status'])

#####################################################################################
_format = {"ID": '0', "timestamp": math.floor(time.time())}
db.child("bot").child("tgytdlp_bot").child("users").child("0").set(_format)
db.child("bot").child("tgytdlp_bot").child("blocked_users").child("0").set(_format)
db.child("bot").child("tgytdlp_bot").child("unblocked_users").child("0").set(_format)
logger.info("db created")
starting_point.append(time.time())
logger.info("Bot started")

# Add signal processing for correct termination
import signal

def signal_handler(sig, frame):
    """
    Handler for system signals to ensure graceful shutdown

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {sig}, shutting down gracefully...")

    # Stop all active animations and threads
    active_threads = [t for t in threading.enumerate()
                     if t != threading.current_thread() and not t.daemon]

    if active_threads:
        logger.info(f"Waiting for {len(active_threads)} active threads to finish")
        for thread in active_threads:
            logger.info(f"Waiting for thread {thread.name} to finish...")
            thread.join(timeout=2)  # Wait with timeout to avoid hanging

    # Clean up temporary files
    try:
        cleanup_temp_files()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    # Finish the application
    logger.info("Shutting down Pyrogram client...")
    try:
        app.stop()
        logger.info("Pyrogram client stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping Pyrogram client: {e}")

    logger.info("Shutdown complete.")
    sys.exit(0)

def cleanup_temp_files():
    """Clean up temporary files across all user directories"""
    if not os.path.exists("users"):
        return

    logger.info("Cleaning up temporary files")
    for user_dir in os.listdir("users"):
        try:
            user_path = os.path.join("users", user_dir)
            if os.path.isdir(user_path):
                for filename in os.listdir(user_path):
                    if filename.endswith(('.part', '.ytdl', '.temp', '.tmp')):
                        try:
                            os.remove(os.path.join(user_path, filename))
                        except Exception as e:
                            logger.error(f"Failed to remove temp file {filename}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning user directory {user_dir}: {e}")

def cleanup_user_temp_files(user_id):
    """Clean up temporary files for a specific user"""
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        return
    
    logger.info(f"Cleaning up temporary files for user {user_id}")
    try:
        for filename in os.listdir(user_dir):
            file_path = os.path.join(user_dir, filename)
            # Remove temporary files
            if (filename.endswith(('.part', '.ytdl', '.temp', '.tmp', '.srt')) or  # Added .srt for subtitles
                filename.startswith('yt_thumb_') or  # YouTube thumbnails
                filename.endswith('.jpg') or  # Thumbnails
                filename == 'full_title.txt' or  # Full title file
                filename == 'full_description.txt'):  # Tags file
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.debug(f"Removed temp file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove temp file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning user directory {user_id}: {e}")

# Register handlers for the most common termination signals
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Helper function to safely get active download status
def get_active_download(user_id):
    """
    Thread-safe function to get the active download status for a user

    Args:
        user_id: The user ID

    Returns:
        bool: Whether the user has an active download
    """
    with active_downloads_lock:
        return active_downloads.get(user_id, False)

# Helper function to sanitize and shorten filenames
def sanitize_filename(filename, max_length=150):
    """
    Sanitize filename by removing invalid characters and shortening if needed
    Only allows letters (any language), numbers, and Linux-safe symbols

    Args:
        filename (str): Original filename
        max_length (int): Maximum allowed length for filename (excluding extension)

    Returns:
        str: Sanitized and shortened filename
    """
    # Exit early if None
    if filename is None:
        return "untitled"

    # Extract extension first
    name, ext = os.path.splitext(filename)

    # Remove all emoji and special Unicode characters
    # Keep only letters (any language), numbers, spaces, dots, dashes, underscores
    import unicodedata
    
    # Normalize Unicode characters
    name = unicodedata.normalize('NFKC', name)
    
    # Remove all emoji and special symbols, keep only:
    # - Letters (any language): \p{L}
    # - Numbers: \p{N}
    # - Spaces: \s
    # - Safe symbols: .-_()
    import re
    
    # Pattern to keep only safe characters
    # Remove all non-alphanumeric characters except safe symbols
    # \w includes [a-zA-Z0-9_] but we want to keep all Unicode letters
    import unicodedata
    
    # Keep only letters, numbers, spaces, and safe symbols
    cleaned_name = ''
    for char in name:
        if (char.isalnum() or  # letters and numbers
            char.isspace() or  # spaces
            char in '.-_()'):  # safe symbols
            cleaned_name += char
    
    name = cleaned_name
    
    # Remove invalid filesystem characters (Windows and Linux safe)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name = re.sub(invalid_chars, '', name)
    
    # Remove leading/trailing dots and spaces (not allowed in Linux)
    name = name.strip(' .')
    
    # Replace multiple spaces/dots with single ones
    name = re.sub(r'[\s.]+', ' ', name).strip()
    
    # If name is empty after cleaning, use default
    if not name:
        name = "untitled"
    
    # Shorten if too long
    full_name = name + ext
    max_total = 100
    if len(full_name) > max_total:
       max_name_length = max_total - len(ext)
       if max_name_length > 3:
          name = name[:max_name_length-3] + "..."
       else:
          name = name[:max_name_length]
       full_name = name + ext
    
    return full_name


# Helper function to safely set active download status
def set_active_download(user_id, status):
    """
    Thread-safe function to set the active download status for a user

    Args:
        user_id: The user ID
        status (bool): Whether the user has an active download
    """
    with active_downloads_lock:
        active_downloads[user_id] = status

# Helper function for safe message sending with flood wait handling
def safe_send_message(chat_id, text, **kwargs):
    # Add reply_to_message_id if message is passed
    if 'reply_to_message_id' not in kwargs and 'message' in kwargs:
        kwargs['reply_to_message_id'] = kwargs['message'].id
        del kwargs['message']
    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            return app.send_message(chat_id, text, **kwargs)
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)
                if attempt < max_retries - 1:
                    continue
            logger.error(f"Failed to send message after {max_retries} attempts: {e}")
            return None

# Helper function for safe message forwarding with flood wait handling
def safe_forward_messages(chat_id, from_chat_id, message_ids, **kwargs):
    """
    Safely forward messages with flood wait handling

    Args:
        chat_id: The chat ID to forward to
        from_chat_id: The chat ID to forward from
        message_ids: The message IDs to forward
        **kwargs: Additional arguments for forward_messages

    Returns:
        The message objects or None if forwarding failed
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            return app.forward_messages(chat_id, from_chat_id, message_ids, **kwargs)
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue

            logger.error(f"Failed to forward messages after {max_retries} attempts: {e}")
            return None

# Helper function for safely editing message text with flood wait handling
def safe_edit_message_text(chat_id, message_id, text, **kwargs):
    """
    Safely edit message text with flood wait handling

    Args:
        chat_id: The chat ID
        message_id: The message ID to edit
        text: The new text
        **kwargs: Additional arguments for edit_message_text

    Returns:
        The message object or None if editing failed
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            return app.edit_message_text(chat_id, message_id, text, **kwargs)
        except Exception as e:
            # If message ID is invalid, it means the message was deleted
            # No need to retry, just return immediately
            if "MESSAGE_ID_INVALID" in str(e):
                # We only log this once, not for every retry
                if attempt == 0:
                    logger.debug(f"Tried to edit message that was already deleted: {message_id}")
                return None

            # If message was not modified, also return immediately (not an error)
            elif "message is not modified" in str(e).lower() or "MESSAGE_NOT_MODIFIED" in str(e):
                return None

            # Handle flood wait errors
            elif "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue

            # Only log other errors as real errors
            if attempt == max_retries - 1:  # Log only on last attempt
                logger.error(f"Failed to edit message after {max_retries} attempts: {e}")
            return None

# Helper function for safely deleting messages with flood wait handling
def safe_delete_messages(chat_id, message_ids, **kwargs):
    """
    Safely delete messages with flood wait handling

    Args:
        chat_id: The chat ID
        message_ids: List of message IDs to delete
        **kwargs: Additional arguments for delete_messages

    Returns:
        True on success or None if deletion failed
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            return app.delete_messages(chat_id=chat_id, message_ids=message_ids, **kwargs)
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue

            logger.error(f"Failed to delete messages after {max_retries} attempts: {e}")
            return None

# Helper function to start the hourglass animation
def start_hourglass_animation(user_id, hourglass_msg_id, stop_anim):
    """
    Start an hourglass animation in a separate thread

    Args:
        user_id: The user ID
        hourglass_msg_id: The message ID to animate
        stop_anim: An event to signal when to stop the animation

    Returns:
        The animation thread
    """

    def animate_hourglass():
        """Animate an hourglass emoji by toggling between two hourglass emojis"""
        counter = 0
        emojis = ["⏳", "⌛"]
        active = True

        while active and not stop_anim.is_set():
            try:
                emoji = emojis[counter % len(emojis)]
                # Attempt to edit message but don't keep trying if message is invalid
                result = safe_edit_message_text(user_id, hourglass_msg_id, f"{emoji} Please wait...")

                # If message edit returns None due to MESSAGE_ID_INVALID, stop animation
                if result is None and counter > 0:  # Allow first attempt to fail
                    active = False
                    break

                counter += 1
                time.sleep(3.0)
            except Exception as e:
                logger.error(f"Error in hourglass animation: {e}")
                # Stop animation on error to prevent log spam
                active = False
                break

        logger.debug(f"Hourglass animation stopped for message {hourglass_msg_id}")

    # Start animation in a daemon thread so it will exit when the main thread exits
    hourglass_thread = threading.Thread(target=animate_hourglass, daemon=True)
    hourglass_thread.start()
    return hourglass_thread

# Helper function to start cycle progress animation
def start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop):
    """
    Start a progress animation for HLS downloads

    Args:
        user_id: The user ID
        proc_msg_id: The message ID to update with progress
        current_total_process: String describing the current process
        user_dir_name: Directory name where fragments are saved
        cycle_stop: Event to signal animation stop

    Returns:
        The animation thread
    """

    def cycle_progress():
        """Show progress animation for HLS downloads"""
        counter = 0
        active = True

        while active and not cycle_stop.is_set():
            counter = (counter + 1) % 11
            try:
                # Check for fragment files
                frag_files = []
                try:
                    frag_files = [f for f in os.listdir(user_dir_name) if 'Frag' in f]
                except (FileNotFoundError, PermissionError) as e:
                    logger.debug(f"Error checking fragment files: {e}")

                if frag_files:
                    last_frag = sorted(frag_files)[-1]
                    m = re.search(r'Frag(\d+)', last_frag)
                    frag_text = f"Frag{m.group(1)}" if m else "Frag?"
                else:
                    frag_text = "waiting for fragments"

                bar = "🟩" * counter + "⬜️" * (10 - counter)

                # Use safe_edit_message_text and check if message exists
                result = safe_edit_message_text(user_id, proc_msg_id,
                    f"{current_total_process}\n📥 Downloading HLS stream: {frag_text}\n{bar}")

                # If message was deleted (returns None), stop animation
                if result is None and counter > 2:  # Allow first few attempts to fail
                    active = False
                    break

            except Exception as e:
                logger.warning(f"Cycle progress error: {e}")
                # Stop animation on consistent errors to prevent log spam
                active = False
                break

            # Sleep with check for stop event
            if cycle_stop.wait(3.0):
                break

        logger.debug(f"Cycle progress animation stopped for message {proc_msg_id}")

    cycle_thread = threading.Thread(target=cycle_progress, daemon=True)
    cycle_thread.start()
    return cycle_thread

# --- Function for cleaning tags for Telegram ---
def clean_telegram_tag(tag: str) -> str:
    return '#' + re.sub(r'[^\w]', '', tag.lstrip('#'))

# --- a function for extracting the URL, the range and tags from the text ---
def extract_url_range_tags(text: str):
    # This function now always returns the full original download link
    if not isinstance(text, str):
        return None, 1, 1, None, [], '', None
    url_match = re.search(r'https?://[^\s\*#]+', text)
    if not url_match:
        return None, 1, 1, None, [], '', None
    url = url_match.group(0)

    after_url = text[url_match.end():]
    # Range
    range_match = re.match(r'\*([0-9]+)\*([0-9]+)', after_url)
    if range_match:
        video_start_with = int(range_match.group(1))
        video_end_with = int(range_match.group(2))
        after_range = after_url[range_match.end():]
    else:
        video_start_with = 1
        video_end_with = 1
        after_range = after_url
    playlist_name = None
    playlist_match = re.match(r'\*([^\s\*#]+)', after_range)
    if playlist_match:
        playlist_name = playlist_match.group(1)
        after_playlist = after_range[playlist_match.end():]
    else:
        after_playlist = after_range
    # New way: Looking for everything #tags throughout the text (multi -line)
    tags = []
    tags_text = ''
    error_tag = None
    error_tag_example = None
    # We collect everything #tags from the whole text (multi -line)
    for raw in re.finditer(r'#([^#\s]+)', text, re.UNICODE):
        tag = raw.group(1)
        if not re.fullmatch(r'[\w\d_]+', tag, re.UNICODE):
            error_tag = tag
            example = re.sub(r'[^\w\d_]', '_', tag, flags=re.UNICODE)
            error_tag_example = f'#{example}'
            break
        tags.append(f'#{tag}')
    tags_text = ' '.join(tags)
    # Return the error if there is
    return url, video_start_with, video_end_with, playlist_name, tags, tags_text, (error_tag, error_tag_example) if error_tag else None

def save_user_tags(user_id, tags):
    if not tags:
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    tags_file = os.path.join(user_dir, "tags.txt")
    # We read already saved tags
    existing = set()
    if os.path.exists(tags_file):
        with open(tags_file, "r", encoding="utf-8") as f:
            for line in f:
                tag = line.strip()
                if tag:
                    existing.add(tag.lower())
    # Add new tags (without registering and without repetitions)
    new_tags = [t for t in tags if t and t.lower() not in existing]
    if new_tags:
        with open(tags_file, "a", encoding="utf-8") as f:
            for tag in new_tags:
                f.write(tag + "\n")

@app.on_message(filters.command("tags") & filters.private)
# @reply_with_keyboard
def tags_command(app, message):
    user_id = message.chat.id
    user_dir = os.path.join("users", str(user_id))
    tags_file = os.path.join(user_dir, "tags.txt")
    if not os.path.exists(tags_file):
        reply_text = "You have no tags yet."
        app.send_message(user_id, reply_text, reply_to_message_id=message.id)
        send_to_logger(message, reply_text)
        return
    with open(tags_file, "r", encoding="utf-8") as f:
        tags = [line.strip() for line in f if line.strip()]
    if not tags:
        reply_text = "You have no tags yet."
        app.send_message(user_id, reply_text, reply_to_message_id=message.id)
        send_to_logger(message, reply_text)
        return
    # We form posts by 4096 characters
    msg = ''
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Close", callback_data="tags_close|close")]
    ])
    for tag in tags:
        if len(msg) + len(tag) + 1 > 4096:
            app.send_message(user_id, msg, reply_to_message_id=message.id, reply_markup=keyboard)
            send_to_logger(message, msg)
            msg = ''
        msg += tag + '\n'
    if msg:
        app.send_message(user_id, msg, reply_to_message_id=message.id, reply_markup=keyboard)
        send_to_logger(message, msg)

@app.on_callback_query(filters.regex(r"^tags_close\|"))
def tags_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Tags message closed.")
        send_to_logger(callback_query.message, "Tags message closed.")
        return

def extract_youtube_id(url: str) -> str:
    """
    It extracts YouTube Video ID from different link formats.
    """
    patterns = [
        r"youtu\.be/([^?&/]+)",
        r"v=([^?&/]+)",
        r"embed/([^?&/]+)",
        r"youtube\.com/watch\?[^ ]*v=([^?&/]+)"
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    raise ValueError("Failed to extract YouTube ID")


def download_thumbnail(video_id: str, dest: str, url: str = None) -> None:
    """
    Downloads YouTube (Maxresdefault/Hqdefault) to the disk in the original size.
    URL - it is needed to determine Shorts by link (but now it is not used).
    """
    base = f"https://img.youtube.com/vi/{video_id}"
    img_bytes = None
    for name in ("maxresdefault.jpg", "hqdefault.jpg"):
        r = requests.get(f"{base}/{name}", timeout=10)
        if r.status_code == 200 and len(r.content) <= 1024 * 1024:
            with open(dest, "wb") as f:
                f.write(r.content)
            img_bytes = r.content
            break
    if not img_bytes:
        raise RuntimeError("Failed to download thumbnail or it is too big")
    # We do nothing else - we keep the original size!

# --- global lists of domains and keywords ---
PORN_DOMAINS = set()
SUPPORTED_SITES = set()
PORN_KEYWORDS = set()

# --- loading lists at start ---
def load_domain_lists():
    global PORN_DOMAINS, SUPPORTED_SITES, PORN_KEYWORDS
    try:
        with open(Config.PORN_DOMAINS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            PORN_DOMAINS = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(PORN_DOMAINS)} domains from {Config.PORN_DOMAINS_FILE}. Example: {list(PORN_DOMAINS)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.PORN_DOMAINS_FILE}: {e}")
        PORN_DOMAINS = set()
    try:
        with open(Config.PORN_KEYWORDS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            PORN_KEYWORDS = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(PORN_KEYWORDS)} keywords from {Config.PORN_KEYWORDS_FILE}. Example: {list(PORN_KEYWORDS)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.PORN_KEYWORDS_FILE}: {e}")
        PORN_KEYWORDS = set()
    try:
        with open(Config.SUPPORTED_SITES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            SUPPORTED_SITES = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(SUPPORTED_SITES)} supported sites from {Config.SUPPORTED_SITES_FILE}. Example: {list(SUPPORTED_SITES)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.SUPPORTED_SITES_FILE}: {e}")
        SUPPORTED_SITES = set()

load_domain_lists()

# --- an auxiliary function for extracting a domain ---
def extract_domain_parts(url):
    try:
        ext = tldextract.extract(url)
        # We collect the domain: Domain.suffix (for example, xvideos.com)
        if ext.domain and ext.suffix:
            full_domain = f"{ext.domain}.{ext.suffix}".lower()
            subdomain = ext.subdomain.lower() if ext.subdomain else ''
            # We get all the suffixes: xvideos.com, b.xvideos.com, a.b.xvideos.com
            parts = [full_domain]
            if subdomain:
                sub_parts = subdomain.split('.')
                for i in range(len(sub_parts)):
                    parts.append('.'.join(sub_parts[i:] + [full_domain]))
            return parts, ext.domain.lower()
        elif ext.domain:
            return [ext.domain.lower()], ext.domain.lower()
        else:
            return [url.lower()], url.lower()
    except Exception:
        # Fallback for URLs without a clear domain, e.g., "localhost"
        parsed = urlparse(url)
        if parsed.netloc:
             return [parsed.netloc.lower()], parsed.netloc.lower()
        return [url.lower()], url.lower()

# --- an auxiliary function for searching for car tues ---
def get_auto_tags(url, user_tags):
    auto_tags = set()
    clean_url = get_clean_url_for_tagging(url)
    url_l = clean_url.lower()
    domain_parts, main_domain = extract_domain_parts(url_l)
    parsed = urlparse(clean_url)
    ext = tldextract.extract(clean_url)
    second_level = ext.domain.lower() if ext.domain else ''
    full_domain = f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else ''
    # 1. Porn Check (for all the suffixes of the domain, but taking into account the whitelist)
    if is_porn_domain(domain_parts):
        auto_tags.add(sanitize_autotag('porn'))
    # 2. YouTube Check (including YouTu.be)
    if ("youtube.com" in url_l or "youtu.be" in url_l):
        auto_tags.add("#youtube")
    # 3. Twitter/X check (exact domain match)
    twitter_domains = {"twitter.com", "x.com", "t.co"}
    domain = parsed.netloc.lower()
    if domain in twitter_domains:
        auto_tags.add("#twitter")
    # 4. Boosty check (boosty.to, boosty.com)
    if ("boosty.to" in url_l or "boosty.com" in url_l):
        auto_tags.add("#boosty")
        auto_tags.add("#porn")
    # 5. Service tag for supported sites (by full domain or 2nd level)
    for site in SUPPORTED_SITES:
        site_l = site.lower()
        if second_level == site_l or full_domain == site_l:
            service_tag = '#' + re.sub(r'[^\w\d_]', '', site_l)
            auto_tags.add(service_tag)
            break
    # Do not duplicate user tags
    user_tags_lower = set(t.lower() for t in user_tags)
    auto_tags = [t for t in auto_tags if t.lower() not in user_tags_lower]
    return auto_tags

# --- White list of domains that are not considered porn ---
# Now we take from config.py

def is_porn_domain(domain_parts):
    # If any suffix domain on a white list is not porn
    for dom in domain_parts:
        if dom in Config.WHITELIST:
            return False
    # If any suffix domain in the list of porn is porn
    for dom in domain_parts:
        if dom in PORN_DOMAINS:
            return True
    return False

# --- a new function for checking for porn ---
def is_porn(url, title, description, caption=None):
    """
    Checks content for pornography by domain and keywords (word-boundary regex search)
    in title, description and caption. Domain whitelist has highest priority.
    """
    # 1. Checking the domain
    clean_url = get_clean_url_for_tagging(url)
    domain_parts, _ = extract_domain_parts(clean_url)
    for dom in Config.WHITELIST:
        if dom in domain_parts:
            logger.info(f"is_porn: domain in WHITELIST: {dom}")
            return False
    if is_porn_domain(domain_parts):
        logger.info(f"is_porn: domain match: {domain_parts}")
        return True

    # 2. Preparation of the text
    title_lower       = title.lower()       if title       else ""
    description_lower = description.lower() if description else ""
    caption_lower     = caption.lower()     if caption     else ""
    if not (title_lower or description_lower or caption_lower):
        logger.info("is_porn: all text fields empty")
        return False

    # 3. We collect a single text for search
    combined = " ".join([title_lower, description_lower, caption_lower])
    logger.debug(f"is_porn combined text: '{combined}'")
    logger.debug(f"is_porn keywords: {PORN_KEYWORDS}")

    # 4. Preparing a regex pattern with a list of keywords
    kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not kws:
        # There is not a single valid key
        return False

    # The boundaries of words (\ b) + flag ignorecase
    pattern = re.compile(r"\b(" + "|".join(kws) + r")\b", flags=re.IGNORECASE)

    # 5. We are looking for a coincidence
    if pattern.search(combined):
        logger.info(f"is_porn: keyword match (regex): {pattern.pattern}")
        return True

    logger.info("is_porn: no keyword matches found")
    return False

@app.on_message(filters.command("split") & filters.private)
# @reply_with_keyboard
def split_command(app, message):
    user_id = message.chat.id
    # Subscription check for non-admines
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    # 2-3 row buttons
    sizes = [
        ("250 MB", 250 * 1024 * 1024),
        ("500 MB", 500 * 1024 * 1024),
        ("1 GB", 1024 * 1024 * 1024),
        ("1.5 GB", 1536 * 1024 * 1024),
        ("2 GB (default)", 1950 * 1024 * 1024)
    ]
    buttons = []
    # Pass the buttons in 2-3 rows
    for i in range(0, len(sizes), 2):
        row = []
        for j in range(2):
            if i + j < len(sizes):
                text, size = sizes[i + j]
                row.append(InlineKeyboardButton(text, callback_data=f"split_size|{size}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="split_size|close")])
    keyboard = InlineKeyboardMarkup(buttons)
    app.send_message(user_id, "Choose max part size for video splitting:", reply_markup=keyboard)
    send_to_logger(message, "User opened /split menu.")

@app.on_callback_query(filters.regex(r"^split_size\|"))
# @reply_with_keyboard
def split_size_callback(app, callback_query):
    logger.info(f"[SPLIT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        send_to_logger(callback_query.message, "Split selection closed.")
        return
    try:
        size = int(data)
    except Exception:
        callback_query.answer("Invalid size.")
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    split_file = os.path.join(user_dir, "split.txt")
    with open(split_file, "w", encoding="utf-8") as f:
        f.write(str(size))
    callback_query.edit_message_text(f"✅ Split part size set to: {humanbytes(size)}")
    send_to_logger(callback_query.message, f"Split size set to {size} bytes.")

# --- Function for reading split.txt ---
def get_user_split_size(user_id):
    user_dir = os.path.join("users", str(user_id))
    split_file = os.path.join(user_dir, "split.txt")
    if os.path.exists(split_file):
        try:
            with open(split_file, "r", encoding="utf-8") as f:
                size = int(f.read().strip())
                return size
        except Exception:
            pass
    return 1950 * 1024 * 1024  # default 1.95GB

# --- receiving formats and metadata via yt-dlp ---
def get_video_formats(url, user_id=None, playlist_start_index=1):
    ytdl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'no_warnings': True,
        'extract_flat': False,
        'simulate': True,
        'playlist_items': str(playlist_start_index),    
        'extractor_args': {
            'generic': ['impersonate=chrome']
        },
        'referer': url,
        'geo_bypass': True,
        'check_certificate': False,
        'live_from_start': True
    }
    if user_id is not None:
        user_dir = os.path.join("users", str(user_id))
        # Check the availability of cookie.txt in the user folder
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        if os.path.exists(user_cookie_path):
            cookie_file = user_cookie_path
        else:
            # If not in the user folder, we copy from the global folder
            global_cookie_path = Config.COOKIE_FILE_PATH
            if os.path.exists(global_cookie_path):
                try:
                    create_directory(user_dir)
                    import shutil
                    shutil.copy2(global_cookie_path, user_cookie_path)
                    logger.info(f"Copied global cookie file to user {user_id} folder for format detection")
                    cookie_file = user_cookie_path
                except Exception as e:
                    logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                    cookie_file = None
            else:
                cookie_file = None
        
        # We check whether to use —no-Cookies for this domain
        if is_no_cookie_domain(url):
            ytdl_opts['cookiefile'] = None  # Equivalent-No-Cookies
            logger.info(f"Using --no-cookies for domain in get_video_formats: {url}")
        elif cookie_file:
            ytdl_opts['cookiefile'] = cookie_file
    try:
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info and info.get('entries'):
            return info['entries'][0]
        return info
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e)
        return {'error': error_text}
    except Exception as e:
        return {'error': str(e)}

# --- Always ask processing ---
def sort_quality_key(quality_key):
    """Sort qualities by increasing resolution from lower to higher"""
    if quality_key == "best":
        return 999999  # best is always at the end
    elif quality_key == "mp3":
        return -1  # mp3 at the very beginning
    else:
        # Extract a number from a string (e.g. "720p" -> 720)
        try:
            return int(quality_key.replace('p', ''))
        except ValueError:
            return 0  # for unknown formats

# @reply_with_keyboard
def ask_quality_menu(app, message, url, tags, playlist_start_index=1):
    user_id = message.chat.id
    proc_msg = None
    found_type = None
    # Clean the cache of subtitles before checking to avoid caching problems
    clear_subs_check_cache()
    # --- checking the range of the range for Always ASK Menu ---
    original_text = message.text or message.caption or ""
    is_playlist = is_playlist_with_range(original_text)
    if is_playlist:
        _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
        if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
            return
    try:
        # Check if subtitles are included
        subs_enabled = is_subs_enabled(user_id)
        processing_text = "🔄 Processing... (wait 6 sec)" if subs_enabled else "🔄 Processing..."
        proc_msg = app.send_message(user_id, processing_text, reply_to_message_id=message.id, reply_markup=get_main_reply_keyboard())
        original_text = message.text or message.caption or ""
        is_playlist = is_playlist_with_range(original_text)
        playlist_range = None
        if is_playlist:
            _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
            playlist_range = (video_start_with, video_end_with)
            cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url))
        else:
            cached_qualities = get_cached_qualities(url)
        info = get_video_formats(url, user_id, playlist_start_index)
        title = info.get('title', 'Video')
        video_id = info.get('id')
        tags_text = generate_final_tags(url, tags, info)
        thumb_path = None
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        if ("youtube.com" in url or "youtu.be" in url) and video_id:
            thumb_path = os.path.join(user_dir, f"yt_thumb_{video_id}.jpg")
            try:
                download_thumbnail(video_id, thumb_path, url)
            except Exception:
                thumb_path = None
        # --- Table with qualities and sizes ---
        table_block = ''
        found_quality_keys = set()
        if ("youtube.com" in url or "youtu.be" in url):
            quality_map = {}
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                    w = f['width']
                    h = f['height']
                    quality_key = get_quality_by_min_side(w, h)
                    if quality_key == "best":
                        continue
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    if quality_key not in quality_map or (filesize and filesize > (quality_map[quality_key].get('filesize') or 0)):
                        quality_map[quality_key] = f
            table_lines = []
            for q in sorted(quality_map.keys(), key=sort_quality_key):
                f = quality_map[q]
                w = f.get('width')
                h = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                if filesize:
                    if filesize >= 1024*1024*1024:
                        size_str = f"{round(filesize/1024/1024/1024, 2)}GB"
                    else:
                        size_str = f"{round(filesize/1024/1024, 1)}MB"
                else:
                    size_str = '—'
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and filesize:
                    video_bytes = filesize
                    if video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                # Check the availability of subtitles for this quality
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                subs_available = ""
                if subs_enabled and is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
                    found_type = check_subs_availability(url, user_id, q, return_type=True)
                    if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                        temp_info = {
                            'duration': info.get('duration'),
                            'filesize': filesize,
                            'filesize_approx': filesize
                        }
                        if check_subs_limits(temp_info, q):
                            subs_available = "💬"
                # Cache/icon
                if is_playlist and playlist_range:
                    indices = list(range(playlist_range[0], playlist_range[1]+1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), q, indices)
                    total = len(indices)
                    postfix = f" ({n_cached}/{total})"
                    is_cached = n_cached > 0
                else:
                    is_cached = q in cached_qualities
                    postfix = ""
                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                emoji = "🚀" if is_cached and not need_subs else "📹"
                table_lines.append(f"{emoji}{q}{subs_available}:  {size_str}{dim_str}{scissors}{postfix}")
                found_quality_keys.add(q)
            table_block = "\n".join(table_lines)
        else:
            # --- The old logic for non-youutube ---
            minside_size_dim_map = {}
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                    w = f['width']
                    h = f['height']
                    quality_key = get_quality_by_min_side(w, h)
                    if quality_key != "best":
                        # Approximate size: if there is Filesize - we use, otherwise we think by Bitrate*Duration, otherwise ' -'
                        if f.get('filesize'):
                            size_mb = int(f['filesize']) // (1024*1024)
                        elif f.get('filesize_approx'):
                            size_mb = int(f['filesize_approx']) // (1024*1024)
                        elif f.get('tbr') and info.get('duration'):
                            size_mb = int(float(f['tbr']) * float(info['duration']) * 125 / (1024*1024))
                        else:
                            size_mb = None
                        if size_mb:
                            key = (quality_key, w, h)
                            minside_size_dim_map[key] = size_mb
            table_lines = []
            for (quality_key, w, h), size_val in sorted(minside_size_dim_map.items(), key=lambda x: sort_quality_key(x[0][0])):
                found_quality_keys.add(quality_key)
                size_str = f"{round(size_val/1024, 1)}GB" if size_val and size_val >= 1024 else (f"{size_val}MB" if size_val else '—')
                dim_str = f" ({w}×{h})"
                scissors = ""
                if get_user_split_size(user_id) and size_val:
                    video_bytes = size_val * 1024 * 1024
                    if video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                emoji = "📹"
                table_lines.append(f"{emoji}{quality_key}:  {size_str}{dim_str}{scissors}")
            table_block = "\n".join(table_lines)

        # --- Forming caption ---
        cap = f"<b>{title}</b>\n"
        # --- YouTube expanded block ---
        if ("youtube.com" in url or "youtu.be" in url):
            uploader = info.get('uploader') or ''
            channel_url = info.get('channel_url') or ''
            view_count = info.get('view_count')
            like_count = info.get('like_count')
            channel_follower_count = info.get('channel_follower_count')
            duration = info.get('duration')
            upload_date = info.get('upload_date')
            title_val = info.get('title') or ''
            # Formatting
            duration_str = TimeFormatter(duration*1000) if duration else ''
            upload_date_str = ''
            if upload_date and len(str(upload_date)) == 8:
                try:
                    dt = datetime.strptime(str(upload_date), '%Y%m%d')
                    upload_date_str = dt.strftime('%d.%m.%Y')
                except Exception:
                    upload_date_str = str(upload_date)
            # Emoji
            views_str = f'👁 {view_count:,}' if view_count is not None else ''
            likes_str = f'❤️ {like_count:,}' if like_count is not None else ''
            subs_str = f'👥 {channel_follower_count:,}' if channel_follower_count is not None else ''
            # First line: channel and subscribers
            meta_lines = []
            if uploader:
                ch_line = f"📺 <b>{uploader}</b>\n"
                if subs_str:
                    ch_line += f"<blockquote>{subs_str}</blockquote>\n"
                meta_lines.append(ch_line)
            # Second line: name
            t_line = ''
            if title_val:
                t_line = f"<b>{title_val}</b>"
            if t_line:
                meta_lines.append(t_line)
            # Third line: Date + Duration (in the quote)
            date_dur_line = ''
            if upload_date_str:
                date_dur_line += f"📅 {upload_date_str}"
            if duration_str:
                if date_dur_line:
                    date_dur_line += f"  ⏱️ {duration_str}"
                else:
                    date_dur_line = f"⏱️ {duration_str}"
            if date_dur_line:
                meta_lines.append(f"<blockquote>{date_dur_line}</blockquote>")
            # Fourth line: views + likes (in quote)
            stat_line = ''
            if views_str:
                stat_line += views_str
            if likes_str:
                if stat_line:
                    stat_line += f"  {likes_str}"
                else:
                    stat_line = likes_str
            if stat_line:
                meta_lines.append(f"<blockquote>{stat_line}</blockquote>")
            # Collect the block
            meta_block = '\n'.join(meta_lines)
            cap = meta_block + '\n\n'
        else:
            cap = ''
        # --- a table of qualities ---
        if table_block:
            cap += f"<blockquote>{table_block}</blockquote>\n"
        # --- tags ---
        if tags_text:
            cap += f"{tags_text}\n"
        # --- links at the very bottom ---
        # if ("youtube.com" in url or "youtu.be" in url):
            # webpage_url = info.get('webpage_url') or ''
            # video_url_link = f'<a href="{webpage_url}">[VIDEO]</a>' if webpage_url else ''
            # channel_url_link = f'<a href="{channel_url}">[CHANNEL]</a>' if channel_url else ''
            # thumbnail_url = info.get('thumbnail') or ''
            # thumb_link = f'<a href="{thumbnail_url}">[Thumbnail]</a>' if thumbnail_url else ''
            # links = '  '.join([x for x in [channel_url_link, thumb_link] if x])
            # if links:
                # cap += f"\n{links}"
        # --- Cutting by the limit ---
        if len(cap) > 1024:
            # We cut off by priority: likes, subscribers, views, date, duration, name, channel
            # 1. Likes
            cap1 = cap.replace(likes_str, '') if likes_str else cap
            if len(cap1) <= 1024:
                cap = cap1
            else:
                # 2. Subscribers
                cap2 = cap1.replace(subs_str, '') if subs_str else cap1
                if len(cap2) <= 1024:
                    cap = cap2
                else:
                    # 3. Views
                    cap3 = cap2.replace(views_str, '') if views_str else cap2
                    if len(cap3) <= 1024:
                        cap = cap3
                    else:
                        # 4. Date
                        cap4 = cap3.replace(upload_date_str, '') if upload_date_str else cap3
                        if len(cap4) <= 1024:
                            cap = cap4
                        else:
                            # 5. Duration
                            cap5 = cap4.replace(duration_str, '') if duration_str else cap4
                            if len(cap5) <= 1024:
                                cap = cap5
                            else:
                                # 6. Name
                                cap6 = cap5.replace(title_val, '') if title_val else cap5
                                if len(cap6) <= 1024:
                                    cap = cap6
                                else:
                                    # 7. Channel
                                    cap7 = cap6.replace(uploader, '') if uploader else cap6
                                    cap = cap7[:1021] + '...'
        # --- Hint ---
        subs_enabled = is_subs_enabled(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        subs_lang = get_user_subs_language(user_id)

        # We check for subtitles of the desired type for the selected language
        subs_hint = ""
        subs_warn = ""
        show_repost_hint = True

        if subs_enabled and is_youtube_url(url):
            # found_type = check_subs_availability(url, user_id, return_type=True)
            need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            if need_subs:
                subs_hint = "\n💬 — Subtitles are available"
                show_repost_hint = False  # 🚀 we don't show if subs really exist and are needed
            else:
                subs_warn = "\n⚠️ Subs not found & won't embed"

        repost_line = "\n🚀 — Instant repost from cache" if show_repost_hint else ""
        hint = "<pre language=\"info\">📹 — Choose download quality" + repost_line + subs_hint + subs_warn + "</pre>"
        cap += f"\n{hint}\n"
        buttons = []
        # Sort buttons by quality from lowest to highest
        if ("youtube.com" in url or "youtu.be" in url):
            for quality_key in sorted(quality_map.keys(), key=sort_quality_key):
                f = quality_map[quality_key]
                w = f.get('width')
                h = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                if filesize:
                    if filesize >= 1024*1024*1024:
                        size_str = f"{round(filesize/1024/1024/1024, 2)}GB"
                    else:
                        size_str = f"{round(filesize/1024/1024, 1)}MB"
                else:
                    size_str = '—'
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and filesize:
                    video_bytes = filesize
                    if video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"
                # Check the availability of subtitles for this quality
                subs_available = ""
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                if subs_enabled and is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
                    # Check the presence of subtitles of the desired type
                    # found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
                    if (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal"):
                        temp_info = {
                            'duration': info.get('duration'),
                            'filesize': filesize,
                            'filesize_approx': filesize
                        }
                        if check_subs_limits(temp_info, quality_key):
                            subs_available = "💬"
                
                if is_playlist and playlist_range:
                    indices = list(range(playlist_range[0], playlist_range[1]+1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if n_cached > 0 else "📹"
                    postfix = f" ({n_cached}/{total})" if total > 1 else ""
                    button_text = f"{icon}{quality_key}{subs_available}{postfix}"
                else:
                    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                    icon = "🚀" if quality_key in cached_qualities and not need_subs else "📹"
                    button_text = f"{icon}{quality_key}{subs_available}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        else:
            popular = [144, 240, 360, 480, 540, 576, 720, 1080, 1440, 2160, 4320]
            for height in popular:
                quality_key = f"{height}p"
                size_val = None
                w = h = None
                for (qk, ww, hh), size in minside_size_dim_map.items():
                    if qk == quality_key:
                        size_val = size
                        w = ww
                        h = hh
                        break
                if size_val is None:
                    continue
                size_str = f"{round(size_val/1024, 1)}GB" if size_val and size_val >= 1024 else (f"{size_val}MB" if size_val else '—')
                dim_str = f" ({w}×{h})" if w and h else ''
                scissors = ""
                if get_user_split_size(user_id) and size_val:
                    video_bytes = size_val * 1024 * 1024
                    if video_bytes > get_user_split_size(user_id):
                        n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                        scissors = f" ✂️{n_parts}"

                
                if is_playlist and playlist_range:
                    indices = list(range(playlist_range[0], playlist_range[1]+1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if n_cached > 0 else "📹"
                    postfix = f" ({n_cached}/{total})" if total > 1 else ""
                    button_text = f"{icon}{quality_key}{postfix}"
                else:
                    
                    icon = "🚀" if quality_key in cached_qualities else "📹"
                    button_text = f"{icon}{quality_key}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))

        if not buttons:
            quality_key = "best"
            
            if is_playlist and playlist_range:
                indices = list(range(playlist_range[0], playlist_range[1]+1))
                n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                total = len(indices)
                icon = "🚀" if n_cached > 0 else "📹"
                postfix = f" ({n_cached}/{total})" if total > 1 else ""
                button_text = f"{icon}Best Quality{postfix}"
            else:
                icon = "🚀" if quality_key in cached_qualities else "📹"
                button_text = f"{icon}Best Quality"
            buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
            
            # Add "Try Another Qualities" button when no automatic qualities detected
            buttons.append(InlineKeyboardButton("🎛 Force Quality", callback_data=f"askq|try_manual"))
            
            # Add explanation when automatic quality detection fails
            autodiscovery_note = "<blockquote>⚠️ Qualities not auto-detected\nYou can manually force quality.</blockquote>"
            cap += f"\n{autodiscovery_note}\n"
        # --- Form rows of 3 buttons ---
        keyboard_rows = []
        
        # Add Quick Embed button for supported services at the top (but not for ranges)
        if (is_instagram_url(url) or is_twitter_url(url) or is_reddit_url(url)) and not is_playlist_with_range(original_text):
            keyboard_rows.append([InlineKeyboardButton("🚀 Quick Embed", callback_data="askq|quick_embed")])
        for i in range(0, len(buttons), 3):
            keyboard_rows.append(buttons[i:i+3])
        # --- button mp3 ---
        quality_key = "mp3"
        if is_playlist and playlist_range:
            indices = list(range(playlist_range[0], playlist_range[1]+1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
            total = len(indices)
            icon = "🚀" if n_cached > 0 else "🎧"
            postfix = f" ({n_cached}/{total})" if total > 1 else ""
            button_text = f"{icon} audio (mp3){postfix}"
        else:
            icon = "🚀" if quality_key in cached_qualities else "🎧"
            button_text = f"{icon} audio (mp3)"
        keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}")])
        
        # --- button subtitles only ---
        # Show the button only if subtitles are turned on and it is youtube
        subs_enabled = is_subs_enabled(user_id)
        if subs_enabled and is_youtube_url(url):
            # We check for subtitles
            # found_type = check_subs_availability(url, user_id, return_type=True)
            auto_mode = get_user_subs_auto_mode(user_id)
            need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            
            if need_subs:
                keyboard_rows.append([InlineKeyboardButton("💬 Subtitles Only", callback_data="askq|subs_only")])
        
        keyboard_rows.append([InlineKeyboardButton("🔚 Close", callback_data="askq|close")])
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        # cap already contains a hint and a table
        try:
            app.delete_messages(user_id, proc_msg.id)
        except Exception as e:
            if 'MESSAGE_ID_INVALID' not in str(e):
                logger.warning(f"Failed to delete message: {e}")
            app.edit_message_reply_markup(chat_id=user_id, message_id=proc_msg.id, reply_markup=None)
        proc_msg = None
        if thumb_path and os.path.exists(thumb_path):
            app.send_photo(user_id, thumb_path, caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_to_message_id=message.id)
        else:
            app.send_message(user_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_to_message_id=message.id)
        send_to_logger(message, f"Always Ask menu sent for {url}")
    except FloodWait as e:
        wait_time = e.value
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        flood_time_file = os.path.join(user_dir, "flood_wait.txt")
        with open(flood_time_file, 'w') as f:
            f.write(str(wait_time))
        hours = wait_time // 3600
        minutes = (wait_time % 3600) // 60
        seconds = wait_time % 60
        time_str = f"{hours}h {minutes}m {seconds}s"
        flood_msg = f"⚠️ Telegram has limited message sending.\n⏳ Please wait: {time_str}\nTo update timer send URL again 2 times."
        if proc_msg:
            try:
                app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=flood_msg)
            except Exception as e:
                if 'MESSAGE_ID_INVALID' not in str(e):
                    logger.warning(f"Failed to edit message: {e}")
            proc_msg = None
        else:
            app.send_message(user_id, flood_msg, reply_to_message_id=message.id)
        return
    except Exception as e:
        error_text = f"❌ Error retrieving video information:\n{e}\n> Try the /clean command and try again. If the error persists, YouTube requires authorization. Update cookies.txt via /download_cookie or /cookies_from_browser and try again."
        try:
            if proc_msg:
                result = app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=error_text)
                if result is None:
                    app.send_message(user_id, error_text, reply_to_message_id=message.id)
            else:
                app.send_message(user_id, error_text, reply_to_message_id=message.id)
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")
            app.send_message(user_id, error_text, reply_to_message_id=message.id)
        send_to_logger(message, f"Always Ask menu error for {url}: {e}")
        return

# --- Callback Processor ---
@app.on_callback_query(filters.regex(r"^askq\|"))
# @reply_with_keyboard
def askq_callback(app, callback_query):
    logger.info(f"[ASKQ] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    found_type = None
    if data == "close":
        try:
            app.delete_messages(user_id, callback_query.message.id)
        except Exception:
            app.edit_message_reply_markup(chat_id=user_id, message_id=callback_query.message.id, reply_markup=None)
        callback_query.answer("Menu closed.")
        return
        
    if data == "quick_embed":
        # Get original URL from the reply message
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer("❌ Error: Original message not found.", show_alert=True)
            return
            
        url = original_message.text
        if not url:
            callback_query.answer("❌ Error: URL not found.", show_alert=True)
            return
            
        # Transform URL
        embed_url = transform_to_embed_url(url)
        if embed_url == url:
            callback_query.answer("❌ This URL cannot be embedded.", show_alert=True)
            return
            
        # Send transformed URL
        app.send_message(
            callback_query.message.chat.id,
            embed_url,
            reply_to_message_id=original_message.id
        )
        send_to_logger(original_message, f"Quick Embed: {embed_url}")
        app.delete_messages(user_id, callback_query.message.id)
        return
    
    # Handle manual quality selection menu
    if data == "try_manual":
        show_manual_quality_menu(app, callback_query)
        return
    
    if data == "manual_back":
        # Extract URL and tags to regenerate the original menu
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer("❌ Error: Original message not found.", show_alert=True)
            app.delete_messages(user_id, callback_query.message.id)
            return
        
        url = None
        if callback_query.message.caption_entities:
            for entity in callback_query.message.caption_entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                    url = entity.url
                    break
        if not url and callback_query.message.reply_to_message:
            url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
            if url_match:
                url = url_match.group(0)
        
        if url:
            tags = []
            caption_text = callback_query.message.caption
            if caption_text:
                tag_matches = re.findall(r'#\S+', caption_text)
                if tag_matches:
                    tags = tag_matches
            app.delete_messages(user_id, callback_query.message.id)
            ask_quality_menu(app, original_message, url, tags)
        else:
            callback_query.answer("❌ Error: URL not found.", show_alert=True)
            app.delete_messages(user_id, callback_query.message.id)
        return
    
    # Handle manual quality selection
    if data.startswith("manual_"):
        quality = data.replace("manual_", "")
        callback_query.answer(f"📥 Downloading {quality}...")
        
        original_message = callback_query.message.reply_to_message
        if not original_message:
            callback_query.answer("❌ Error: Original message not found.", show_alert=True)
            app.delete_messages(user_id, callback_query.message.id)
            return
        
        url = None
        if callback_query.message.caption_entities:
            for entity in callback_query.message.caption_entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                    url = entity.url
                    break
        if not url and callback_query.message.reply_to_message:
            url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
            if url_match:
                url = url_match.group(0)
        
        if not url:
            callback_query.answer("❌ Error: URL not found.", show_alert=True)
            app.delete_messages(user_id, callback_query.message.id)
            return
        
        # New method: always extract tags from the user's source message
        original_text = original_message.text or original_message.caption or ""
        _, _, _, _, tags, tags_text, _ = extract_url_range_tags(original_text)
        
        app.delete_messages(user_id, callback_query.message.id)
        
        # Force use specific quality format like in /format command
        if quality == "best":
            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best"
        elif quality == "mp3":
            down_and_audio(app, original_message, url, tags, quality_key="mp3")
            return
        else:
            try:
                quality_str = quality.replace('p', '')
                quality_val = int(quality_str)
                format_override = f"bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
            except ValueError:
                format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best"
        
        # Handle playlists
        original_text = original_message.text or original_message.caption or ""
        if is_playlist_with_range(original_text):
            _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(original_text)
            video_count = video_end_with - video_start_with + 1
            down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=quality)
        else:
            down_and_up_with_format(app, original_message, url, format_override, tags_text, quality_key=quality)
        return

    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer("❌ Error: Original message not found. It might have been deleted. Please send the link again.", show_alert=True)
        app.delete_messages(user_id, callback_query.message.id)
        return

    url = None
    if callback_query.message.caption_entities:
        for entity in callback_query.message.caption_entities:
            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                url = entity.url
                break
    if not url and callback_query.message.reply_to_message:
        url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    if not url:
        callback_query.answer("❌ Error: Original URL not found. Please send the link again.", show_alert=True)
        app.delete_messages(user_id, callback_query.message.id)
        return

    # We extract tags from the initial message of the user
    original_text = original_message.text or original_message.caption or ""
    _, _, _, _, tags, tags_text, _ = extract_url_range_tags(original_text)

    app.delete_messages(user_id, callback_query.message.id)

    original_text = original_message.text or original_message.caption or ""
    if is_playlist_with_range(original_text):
        logger.info(f"Playlist with range detected, checking playlist cache for URL: {url}")
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(original_text)
        video_count = video_end_with - video_start_with + 1
        requested_indices = list(range(video_start_with, video_start_with + video_count))
        
        # Check cache for selected quality
        cached_videos = get_cached_playlist_videos(get_clean_playlist_url(url), data, requested_indices)
        uncached_indices = [i for i in requested_indices if i not in cached_videos]
        used_quality_key = data
        
        # If there is no cache for the selected quality, try fallback to best
        if not cached_videos and data != "best":
            logger.info(f"askq_callback: no cache for quality_key={data}, trying fallback to best")
            best_cached = get_cached_playlist_videos(get_clean_playlist_url(url), "best", requested_indices)
            if best_cached:
                cached_videos = best_cached
                used_quality_key = "best"
                uncached_indices = [i for i in requested_indices if i not in cached_videos]
                logger.info(f"askq_callback: found cache with best quality, cached: {list(cached_videos.keys())}, uncached: {uncached_indices}")
        
        if cached_videos:
            # Reposting cached videos
            callback_query.answer("🚀 Found in cache! Reposting...", show_alert=False)
            for index in requested_indices:
                if index in cached_videos:
                    try:
                        app.forward_messages(
                            chat_id=user_id,
                            from_chat_id=Config.LOGS_ID,
                            message_ids=[cached_videos[index]]
                        )
                    except Exception as e:
                        logger.warning(f"askq_callback: cached video for index {index} not found: {e}")
            
            # If there are missing videos - download them
            if uncached_indices:
                logger.info(f"askq_callback: we start downloading the missing indexes: {uncached_indices}")
                new_start = uncached_indices[0]
                new_end = uncached_indices[-1]
                new_count = new_end - new_start + 1
                
                if data == "mp3":
                    down_and_audio(app, original_message, url, tags, quality_key=used_quality_key, playlist_name=playlist_name, video_count=new_count, video_start_with=new_start)
                else:
                    try:
                        # Form the correct format for the missing videos
                        if used_quality_key == "best":
                            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
                        else:
                            quality_str = used_quality_key.replace('p', '')
                            quality_val = int(quality_str)
                            format_override = f"bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
                    except Exception as e:
                        logger.error(f"askq_callback: error forming format: {e}")
                        format_override = "bestvideo+bestaudio/best"
                    
                    down_and_up(app, original_message, url, playlist_name, new_count, new_start, tags_text, force_no_title=False, format_override=format_override, quality_key=used_quality_key)
            else:
                # All videos were in the cache
                app.send_message(user_id, f"✅ Sent from cache: {len(cached_videos)}/{len(requested_indices)} files.", reply_to_message_id=original_message.id)
                media_type = "Audio" if data == "mp3" else "Video"
                log_msg = f"{media_type} playlist sent from cache to user.\nURL: {url}\nUser: {callback_query.from_user.first_name} ({user_id})"
                send_to_logger(original_message, log_msg)
            return
        else:
            # If there is no cache at all - download everything again
            logger.info(f"askq_callback: no cache found for any quality, starting new download")
            if data == "mp3":
                down_and_audio(app, original_message, url, tags, quality_key=data, playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
            else:
                try:
                    # Form the correct format for the new download
                    if data == "best":
                        format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
                    else:
                        quality_str = data.replace('p', '')
                        quality_val = int(quality_str)
                        format_override = f"bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
                except ValueError:
                    format_override = "bestvideo+bestaudio/best"
                
                down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=data)
            return
    # --- other logic for single files ---
    found_type = check_subs_availability(url, user_id, data, return_type=True)
    available_langs = _subs_check_cache.get(
        f"{url}_{user_id}_{'auto' if found_type == 'auto' else 'normal'}_langs",
        []
    )

    subs_enabled = is_subs_enabled(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)
    need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
    if not need_subs:

        message_ids = get_cached_message_ids(url, data)
        if message_ids:
            callback_query.answer("🚀 Found in cache! Forwarding instantly...", show_alert=False)
            # found_type = None
            try:
                app.forward_messages(
                    chat_id=user_id,
                    from_chat_id=Config.LOGS_ID,
                    message_ids=message_ids
                )
                app.send_message(user_id, "✅ Video successfully sent from cache.", reply_to_message_id=original_message.id)
                media_type = "Audio" if data == "mp3" else "Video"
                log_msg = f"{media_type} sent from cache to user.\nURL: {url}\nUser: {callback_query.from_user.first_name} ({user_id})"
                send_to_logger(original_message, log_msg)
                return
            except Exception as e:
                # found_type = check_subs_availability(url, user_id, data, return_type=True)
                subs_enabled = is_subs_enabled(user_id)
                auto_mode = get_user_subs_auto_mode(user_id)
                need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
                if not need_subs:
                    save_to_video_cache(url, data, [], clear=True)
                else:
                    logger.info("Video with subtitles (real subs found and needed) is not cached!")
                app.send_message(user_id, "⚠️ Failed to get video from cache, starting a new download...", reply_to_message_id=original_message.id)
                askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs)
            return
    askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs)


def askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs):
    user_id = callback_query.from_user.id
    tags = tags_text.split() if tags_text else []
    if data == "mp3":
        callback_query.answer("🎧 Downloading audio...")
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        video_count = video_end_with - video_start_with + 1
        down_and_audio(app, original_message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    if data == "subs_only":
        callback_query.answer("💬 Downloading subtitles only...")
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        video_count = video_end_with - video_start_with + 1
        download_subtitles_only(app, original_message, url, tags, available_langs, playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    # Logic for forming the format with the real height
    if data == "best":
        callback_query.answer("📥 Downloading best quality...")
        fmt = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best"
        quality_key = "best"
    else:
        try:
            # Get information about the video to determine the sizes
            info = get_video_formats(url, user_id)
            formats = info.get('formats', [])
            
            # Find the format with the highest quality to determine the sizes
            max_width = 0
            max_height = 0
            for f in formats:
                if f.get('width') and f.get('height'):
                    if f['width'] > max_width:
                        max_width = f['width']
                    if f['height'] > max_height:
                        max_height = f['height']
            
            # If the sizes are not found, use the standard logic
            if max_width == 0 or max_height == 0:
                quality_str = data.replace('p', '')
                quality_val = int(quality_str)
                fmt = f"bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo[height<={quality_val}]+bestaudio/best[height<={quality_val}]/best"
            else:
                # Determine the quality by the smaller side
                min_side_quality = get_quality_by_min_side(max_width, max_height)
                
                # If the selected quality does not match the smaller side, use the standard logic
                if data != min_side_quality:
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    fmt = f"bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo[height<={quality_val}]+bestaudio/best[height<={quality_val}]/best"
                else:
                    # Use the real height to form the format
                    real_height = get_real_height_for_quality(data, max_width, max_height)
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    fmt = f"bv*[vcodec*=avc1][height<={real_height}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo[height<={quality_val}]+bestaudio/best[height<={quality_val}]/best"
            
            quality_key = data
            callback_query.answer(f"📥 Downloading {data}...")
        except ValueError:
            callback_query.answer("Unknown quality.")
            return
    
    down_and_up_with_format(app, original_message, url, fmt, tags_text, quality_key=quality_key)

# @reply_with_keyboard
def show_manual_quality_menu(app, callback_query):
    """Show manual quality selection menu when automatic detection fails"""
    user_id = callback_query.from_user.id
    subs_available = ""
    found_type = None
    # Extract URL and tags from the callback
    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer("❌ Error: Original message not found.", show_alert=True)
        callback_query.message.delete()
        return
    
    url = None
    if callback_query.message.caption_entities:
        for entity in callback_query.message.caption_entities:
            if entity.type == enums.MessageEntityType.TEXT_LINK and entity.url:
                url = entity.url
                break
    if not url and callback_query.message.reply_to_message:
        url_match = re.search(r'https?://[^\s\*#]+', callback_query.message.reply_to_message.text)
        if url_match:
            url = url_match.group(0)
    
    if not url:
        callback_query.answer("❌ Error: URL not found.", show_alert=True)
        callback_query.message.delete()
        return
    
    tags = []
    caption_text = callback_query.message.caption
    if caption_text:
        tag_matches = re.findall(r'#\S+', caption_text)
        if tag_matches:
            tags = tag_matches
    tags_text = ' '.join(tags)
    
    # Check if it's a playlist
    original_text = original_message.text or original_message.caption or ""
    is_playlist = is_playlist_with_range(original_text)
    playlist_range = None
    if is_playlist:
        _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
        playlist_range = (video_start_with, video_end_with)
        cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url))
    else:
        cached_qualities = get_cached_qualities(url)
    
    # Create manual quality buttons
    manual_qualities = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p"]
    buttons = []
    
    for quality in manual_qualities:
        if is_playlist and playlist_range:
            indices = list(range(playlist_range[0], playlist_range[1]+1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality, indices)
            total = len(indices)
            icon = "🚀" if n_cached > 0 else "📹"
            postfix = f" ({n_cached}/{total})" if total > 1 else ""
            button_text = f"{icon}{quality}{postfix}"
        else:
            icon = "🚀" if quality in cached_qualities else "📹"
            button_text = f"{icon}{quality}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality}"))

    # Best Quality
    if is_playlist and playlist_range:
        indices = list(range(playlist_range[0], playlist_range[1]+1))
        n_cached = get_cached_playlist_count(get_clean_playlist_url(url), "best", indices)
        total = len(indices)
        icon = "🚀" if n_cached > 0 else "📹"
        postfix = f" ({n_cached}/{total})" if total > 1 else ""
        button_text = f"{icon}Best Quality{postfix}"
    else:
        icon = "🚀" if "best" in cached_qualities else "📹"
        button_text = f"{icon}Best Quality"
    buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|manual_best"))
    
    # Form rows of 3 buttons
    keyboard_rows = []
    for i in range(0, len(buttons), 3):
        keyboard_rows.append(buttons[i:i+3])
    
    # Add mp3 button
    quality_key = "mp3"
    if is_playlist and playlist_range:
        indices = list(range(playlist_range[0], playlist_range[1]+1))
        n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
        total = len(indices)
        icon = "🚀" if n_cached > 0 else "🎧"
        postfix = f" ({n_cached}/{total})" if total > 1 else ""
        button_text = f"{icon} audio (mp3){postfix}"
    else:
        icon = "🚀" if quality_key in cached_qualities else "🎧"
        button_text = f"{icon} audio (mp3)"
    keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality_key}")])
    
    # Add subtitles only button if enabled
    subs_enabled = is_subs_enabled(user_id)
    if subs_enabled and is_youtube_url(url):
        found_type = check_subs_availability(url, user_id, return_type=True)
        auto_mode = get_user_subs_auto_mode(user_id)
        need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
        
        if need_subs:
            keyboard_rows.append([InlineKeyboardButton("💬 Subtitles Only", callback_data="askq|subs_only")])
    
    # Add Back and close buttons
    keyboard_rows.append([
        InlineKeyboardButton("🔙 Back", callback_data="askq|manual_back"),
        InlineKeyboardButton("🔚 Close", callback_data="askq|close")
    ])
    
    keyboard = InlineKeyboardMarkup(keyboard_rows)
    
    # Get video title for caption
    try:
        info = get_video_formats(url, user_id)
        title = info.get('title', 'Video')
        video_title = title
    except:
        video_title = "Video"
    
    # Form caption
    cap = f"<b>{video_title}</b>\n"
    if tags_text:
        cap += f"{tags_text}\n"
    cap += f"\n<b>🎛 Manual Quality Selection</b>\n"
    cap += f"\n<i>Choose quality manually since automatic detection failed:</i>\n"
    
    # Update the message
    try:
        if callback_query.message.photo:
            callback_query.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        else:
            callback_query.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        callback_query.answer("Manual quality selection menu opened.")
    except Exception as e:
        logger.error(f"Error showing manual quality menu: {e}")
        callback_query.answer("❌ Error opening manual quality menu.", show_alert=True)


# --- an auxiliary function for downloading with the format ---
# @reply_with_keyboard
def down_and_up_with_format(app, message, url, fmt, tags_text, quality_key=None):

    # We extract the range and other parameters from the original user message
    full_string = message.text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)

    # This mistake should have already been caught earlier, but for safety
    if tag_error:
        wrong, example = tag_error
        app.send_message(message.chat.id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_to_message_id=message.id)
        return

    video_count = video_end_with - video_start_with + 1
    
    # Check if there is a link to Tiktok
    is_tiktok = is_tiktok_url(url)

    # We call the main function of loading with the correct parameters of the playlist
    down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=is_tiktok, format_override=fmt, quality_key=quality_key)


def sanitize_autotag(tag: str) -> str:
    # Leave only letters (any language), numbers and _
    return '#' + re.sub(r'[^\w\d_]', '_', tag.lstrip('#'), flags=re.UNICODE)

def generate_final_tags(url, user_tags, info_dict):
    """Tags now include #porn if found by title, description or caption."""
    final_tags = []
    seen = set()
    # 1. Custom tags
    for tag in user_tags:
        tag_l = tag.lower()
        if tag_l not in seen:
            final_tags.append(tag)
            seen.add(tag_l)
    # 2. Auto-tags (no duplicates)
    auto_tags = get_auto_tags(url, final_tags)
    for tag in auto_tags:
        tag_l = tag.lower()
        if tag_l not in seen:
            final_tags.append(tag)
            seen.add(tag_l)
    # 3. Profile/channel tags (tiktok/youtube)
    if is_tiktok_url(url):
        tiktok_profile = extract_tiktok_profile(url)
        if tiktok_profile:
            tiktok_tag = sanitize_autotag(tiktok_profile)
            if tiktok_tag.lower() not in seen:
                final_tags.append(tiktok_tag)
                seen.add(tiktok_tag.lower())
        if '#tiktok' not in seen:
            final_tags.append('#tiktok')
            seen.add('#tiktok')
    clean_url_for_check = get_clean_url_for_tagging(url)
    if ("youtube.com" in clean_url_for_check or "youtu.be" in clean_url_for_check) and info_dict:
        channel_name = info_dict.get("channel") or info_dict.get("uploader")
        if channel_name:
            channel_tag = sanitize_autotag(channel_name)
            if channel_tag.lower() not in seen:
                final_tags.append(channel_tag)
                seen.add(channel_tag.lower())
    # 4. #porn if defined by title, description or caption
    video_title = info_dict.get("title") if info_dict else None
    video_description = info_dict.get("description") if info_dict else None
    video_caption = info_dict.get("caption") if info_dict else None
    if is_porn(url, video_title, video_description, video_caption):
        if '#porn' not in seen:
            final_tags.append('#porn')
            seen.add('#porn')
    result = ' '.join(final_tags)
    # Check if info_dict is None before accessing it
    title = info_dict.get('title', 'N/A') if info_dict else 'N/A'
    logger.info(f"Generated final tags for '{title}': \"{result}\"")
    return result

# --- new functions for caching ---
def get_url_hash(url: str) -> str:
    """Returns a hash of the URL for use as a cache key."""
    import hashlib
    hash_result = hashlib.md5(url.encode()).hexdigest()
    logger.info(f"get_url_hash: '{url}' -> '{hash_result}'")
    return hashlib.md5(url.encode()).hexdigest()


def save_to_video_cache(url: str, quality_key: str, message_ids: list, clear: bool = False, original_text: str = None, user_id: int = None):
    """Saves message IDs to Firebase video cache after checking local cache to avoid duplication."""
    found_type = None
    if user_id is not None:
        found_type = check_subs_availability(url, user_id, quality_key, return_type=True)
        subs_enabled = is_subs_enabled(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
        if need_subs:
            logger.info("Video with subtitles is not cached!")
            return

    logger.info(f"save_to_video_cache called: url={url}, quality_key={quality_key}, message_ids={message_ids}, clear={clear}, original_text={original_text}")

    if not quality_key:
        logger.warning(f"save_to_video_cache: quality_key is empty, skipping cache save for URL: {url}")
        return

    if original_text and is_playlist_with_range(original_text):
        logger.info(f"Playlist with range detected, skipping cache save for URL: {url}")
        return

    try:
        urls = [normalize_url_for_cache(url)]
        if is_youtube_url(url):
            urls += [
                normalize_url_for_cache(youtube_to_short_url(url)),
                normalize_url_for_cache(youtube_to_long_url(url))
            ]
        
        logger.info(f"save_to_video_cache: normalized URLs: {urls}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            path_parts_local = ["bot", "video_cache", "playlists", url_hash]
            path_parts = [Config.VIDEO_CACHE_DB_PATH, url_hash]
            
            # === CLEAR MODE ===
            if clear:
                logger.info(f"Clearing cache for URL hash {url_hash}, quality {quality_key}")
                db.child(*path_parts).child(quality_key).remove()
                continue

            if not message_ids:
                logger.warning(f"save_to_video_cache: message_ids is empty for URL: {url}, quality: {quality_key}")
                continue

            # === LOCAL CACHE CHECK ===
            existing = get_from_local_cache(path_parts_local + [quality_key])
            if existing is not None:
                logger.info(f"Cache already exists for URL hash {url_hash}, quality {quality_key}, skipping save.")
                continue  # skip writing if already cached locally

            cache_ref = db.child(*path_parts)

            if len(message_ids) == 1:
                cache_ref.child(quality_key).set(str(message_ids[0]))
                logger.info(f"Saved single video to cache: hash={url_hash}, quality={quality_key}, msg_id={message_ids[0]}")
            else:
                ids_string = ",".join(map(str, message_ids))
                cache_ref.child(quality_key).set(ids_string)
                logger.info(f"Saved split video to cache: hash={url_hash}, quality={quality_key}, msg_ids={ids_string}")

    except Exception as e:
        logger.error(f"Failed to save to video cache: {e}")
        

def get_cached_message_ids(url: str, quality_key: str) -> list:
    """Searches cache for both versions of YouTube link (long/short)."""
    logger.info(f"get_cached_message_ids called: url={url}, quality_key={quality_key}")
    if not quality_key:
        logger.warning(f"get_cached_message_ids: quality_key is empty for URL: {url}")
        return None
    try:
        urls = [normalize_url_for_cache(url)]
        if is_youtube_url(url):
            short_url = youtube_to_short_url(url)
            long_url = youtube_to_long_url(url)
            urls.append(normalize_url_for_cache(short_url))
            urls.append(normalize_url_for_cache(long_url))
            logger.info(f"get_cached_message_ids: original={url}, short={short_url}, long={long_url}")
        logger.info(f"get_cached_message_ids: checking URLs: {urls}")
        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"get_cached_message_ids: checking hash {url_hash} for quality {quality_key}")
            
            # We use local cache instead of Firebase
            path_parts = ["bot", "video_cache", url_hash, quality_key]
            ids_string = get_from_local_cache(path_parts)
            
            logger.info(f"get_cached_message_ids: raw value from local cache: {ids_string} (type: {type(ids_string)})")
            if ids_string:
                result = [int(msg_id) for msg_id in ids_string.split(',')]
                logger.info(
                    f"get_cached_message_ids: found cached message_ids {result} for URL: {url}, quality: {quality_key}")
                return result
            else:
                logger.info(f"get_cached_message_ids: no cache found for hash {url_hash}, quality {quality_key}")
        logger.info(f"get_cached_message_ids: no cache found for any URL variant, returning None")
        return None
    except Exception as e:
        logger.error(f"Failed to get from cache: {e}")
        return None


def get_cached_qualities(url: str) -> set:
    """He gets all the castle qualities for the URL."""
    try:
        url_hash = get_url_hash(normalize_url_for_cache(url))
        
        # We use local cache instead of Firebase
        path_parts = ["bot", "video_cache", url_hash]
        data = get_from_local_cache(path_parts)
        
        if data and isinstance(data, dict):
            return set(data.keys())
        return set()
    except Exception as e:
        logger.error(f"Failed to get cached qualities: {e}")
        return set()


def normalize_url_for_cache(url: str) -> str:
    """
    Normalizes URLs for caching based on a set of specific rules,
    removing all non-essential query parameters.
    For youtube.com (without www) leave as is, for youtu.be always without www and without query.
    """
    if not isinstance(url, str):
        return ''

    original_url = url
    url = extract_real_url_if_google(url)
    clean_url = get_clean_url_for_tagging(url)
    parsed = urlparse(clean_url)
    domain = parsed.netloc.lower()
    path = parsed.path
    query_params = parse_qs(parsed.query)

    # --- YouTube/youtu.be: always from www.youtube.com and youtu.be ---
    if domain in ('youtube.com', 'www.youtube.com'):
        domain = 'www.youtube.com'
    if domain in ('youtu.be', 'www.youtu.be'):
        domain = 'youtu.be'

    # Pornhub: keep full path and query parameters for unique video identification
    if domain.endswith('.pornhub.com'):
        base_domain = 'pornhub.com'
        result = urlunparse((parsed.scheme, base_domain, path, parsed.params, parsed.query, parsed.fragment))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (pornhub)")
        return result

    # TikTok: always strip all params, keep only path
    if 'tiktok.com' in domain:
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (tiktok)")
        return result

    # Shorts and youtu.be: always strip all params
    if ("youtube.com" in domain and path.startswith('/shorts/')):
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (shorts)")
        return result
    if domain == 'youtu.be':
        # For youtu.be always remove query
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (youtu.be)")
        return result

    # /watch: only v
    if 'youtube.com' in domain and path == '/watch':
        v = None
        if 'v' in query_params:
            v = query_params['v'][0]
            # Fix: If v contains ? or &, only match up to those characters
            v = v.split('?')[0].split('&')[0]
        if v:
            new_query = urlencode({'v': v}, doseq=True)
            result = urlunparse((parsed.scheme, domain, path, '', new_query, ''))
            logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (watch)")
            return result
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (watch no v)")
        return result
    # /playlist: list only
    if 'youtube.com' in domain and path == '/playlist':
        if 'list' in query_params:
            new_query = urlencode({'list': query_params['list']}, doseq=True)
            result = urlunparse((parsed.scheme, domain, path, '', new_query, ''))
            logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (playlist)")
            return result
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (playlist no list)")
        return result
    # /embed: playlist only
    if 'youtube.com' in domain and path.startswith('/embed/'):
        allowed_params = {k: v for k, v in query_params.items() if k == 'playlist'}
        new_query = urlencode(allowed_params, doseq=True)
        result = urlunparse((parsed.scheme, domain, path, '', new_query, ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (embed)")
        return result
    # live: only way
    if 'youtube.com' in domain and (path.startswith('/live/') or path.endswith('/live')):
        result = urlunparse((parsed.scheme, domain, path, '', '', ''))
        logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (live)")
        return result
    # fallback for CLEAN_QUERY domains (suffix match)
    for clean_domain in getattr(Config, 'CLEAN_QUERY', []):
        if domain == clean_domain or domain.endswith('.' + clean_domain):
            result = urlunparse((parsed.scheme, domain, parsed.path, '', '', ''))
            logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (clean domain)")
            return result
    # For all other URLs, return them as they are
    result = urlunparse((parsed.scheme, domain, parsed.path, parsed.params, parsed.query, ''))
    logger.info(f"normalize_url_for_cache: '{original_url}' -> '{result}' (fallback)")
    return result


def extract_real_url_if_google(url: str) -> str:
    """
    If the link is a redirect via Google, returns the target link.
    Otherwise, returns the original link.
    """
    parsed = urlparse(url)
    if parsed.netloc.endswith('google.com') and parsed.path.startswith('/url'):
        qs = parse_qs(parsed.query)
        # Google may use either ?q= or ?url=
        real_url = qs.get('q') or qs.get('url')
        if real_url:
            # Take the first variant, decode if needed
            return unquote(real_url[0])
    return url


def youtube_to_short_url(url: str) -> str:
    """Converts youtube.com/watch?v=... to youtu.be/... while preserving query parameters."""
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc and parsed.path == '/watch':
        qs = parse_qs(parsed.query)
        v = qs.get('v', [None])[0]
        if v:
            # Collect query without v
            query = {k: v for k, v in qs.items() if k != 'v'}
            query_str = urlencode(query, doseq=True)
            base = f'https://youtu.be/{v}'
            if query_str:
                return f'{base}?{query_str}'
            return base
    elif 'youtube.com' in parsed.netloc and parsed.path.startswith('/shorts/'):
        # For YouTube Shorts, convert to youtu.be format
        video_id = parsed.path.split('/')[2]  # /shorts/VIDEO_ID
        if video_id:
            return f'https://youtu.be/{video_id}'
    return url


def youtube_to_long_url(url: str) -> str:
    """Converts youtu.be/... to youtube.com/watch?v=... while preserving query parameters."""
    parsed = urlparse(url)
    if 'youtu.be' in parsed.netloc:
        video_id = parsed.path.lstrip('/')
        if video_id:
            qs = parsed.query
            base = f'https://www.youtube.com/watch?v={video_id}'
            if qs:
                return f'{base}&{qs}'
            return base
    elif 'youtube.com' in parsed.netloc and parsed.path.startswith('/shorts/'):
        # For YouTube Shorts, convert to watch format
        video_id = parsed.path.split('/')[2]  # /shorts/VIDEO_ID
        if video_id:
            return f'https://www.youtube.com/watch?v={video_id}'
    return url


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc


# Added playlist caching - separate functions for saving and retrieving playlist cache
def save_to_playlist_cache(playlist_url: str, quality_key: str, video_indices: list, message_ids: list,
                           clear: bool = False, original_text: str = None):
    logger.info(
        f"save_to_playlist_cache called: playlist_url={playlist_url}, quality_key={quality_key}, video_indices={video_indices}, message_ids={message_ids}, clear={clear}")
    
    if not quality_key:
        logger.warning(f"quality_key is empty, skipping cache save for playlist: {playlist_url}")
        return

    if not hasattr(Config, 'PLAYLIST_CACHE_DB_PATH') or not Config.PLAYLIST_CACHE_DB_PATH or Config.PLAYLIST_CACHE_DB_PATH.strip() in ('', '/', '.'):
        logger.error(f"PLAYLIST_CACHE_DB_PATH is invalid, skipping write for: {playlist_url}")
        return

    try:
        # Normalize the URL (without the range) and form all link options
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.extend([
                normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))),
                normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))),
            ])
        logger.info(f"Normalized playlist URLs: {urls}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"Using playlist URL hash: {url_hash}")

            if clear:
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{quality_key}").remove()
                logger.info(f"Cleared playlist cache for hash={url_hash}, quality={quality_key}")
                continue

            if not message_ids or not video_indices:
                logger.warning(f"message_ids or video_indices is empty for playlist: {playlist_url}, quality: {quality_key}")
                continue

            for i, msg_id in zip(video_indices, message_ids):
                
                path_parts_local = ["bot", "video_cache", "playlists", url_hash, quality_key, str(i)]
                path_parts = [Config.PLAYLIST_CACHE_DB_PATH, url_hash, quality_key, str(i)]
                already_cached = get_from_local_cache(path_parts_local)

                if already_cached:
                    logger.info(f"Playlist part already cached: {path_parts_local}, skipping")
                    continue

                db_child_by_path(db, "/".join(path_parts)).set(str(msg_id))
                logger.info(f"Saved to playlist cache: path={path_parts}, msg_id={msg_id}")

        logger.info(f"✅ Saved to playlist cache for hash={url_hash}, quality={quality_key}, indices={video_indices}, message_ids={message_ids}")

    except Exception as e:
        logger.error(f"Failed to save to playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        

def get_cached_playlist_videos(playlist_url: str, quality_key: str, requested_indices: list) -> dict:
    logger.info(
        f"get_cached_playlist_videos called: playlist_url={playlist_url}, quality_key={quality_key}, requested_indices={requested_indices}")
    if not quality_key:
        logger.warning(f"get_cached_playlist_videos: quality_key is empty for playlist: {playlist_url}")
        return {}
    try:
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))))
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))))
        quality_keys = [quality_key]
        try:
            if quality_key.endswith('p'):
                h = int(quality_key[:-1])
                rounded = f"{ceil_to_popular(h)}p"
                if rounded != quality_key:
                    quality_keys.append(rounded)
        except Exception:
            pass
        found = {}
        logger.info(f"get_cached_playlist_videos: checking URLs: {urls}")
        logger.info(f"get_cached_playlist_videos: checking quality keys: {quality_keys}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"get_cached_playlist_videos: checking URL hash: {url_hash}")
            for qk in quality_keys:
                logger.info(f"get_cached_playlist_videos: checking quality: {qk}")

                # A new way for searching in Dump!
                arr = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if isinstance(arr, list):
                    for index in requested_indices:
                        try:
                            if index < len(arr) and arr[index]:
                                found[index] = int(arr[index])
                                logger.info(
                                    f"get_cached_playlist_videos: found cached video for index {index} (quality={qk}): {arr[index]}")
                        except Exception as e:
                            logger.error(
                                f"get_cached_playlist_videos: error reading cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                            continue
                    if found:
                        logger.info(
                            f"get_cached_playlist_videos: returning cached videos for indices {list(found.keys())}: {found}")
                        return found

        logger.info(f"get_cached_playlist_videos: no cache found for any URL/quality variant, returning empty dict")
        return {}
    except Exception as e:
        logger.error(f"Failed to get from playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


def get_cached_playlist_qualities(playlist_url: str) -> set:
    """Gets all available qualities for a cached playlist."""
    try:
        url_hash = get_url_hash(normalize_url_for_cache(strip_range_from_url(playlist_url)))
        data = get_from_local_cache(["bot", "video_cache", "playlists", url_hash])
        if data and isinstance(data, dict):
            return set(data.keys())
        return set()
    except Exception as e:
        logger.error(f"Failed to get cached playlist qualities: {e}")
        return set()


def is_any_playlist_index_cached(playlist_url, quality_key, indices):
    """Checks if at least one index from the range is in the playlist cache."""
    cached = get_cached_playlist_videos(playlist_url, quality_key, indices)
    return bool(cached)


def get_clean_playlist_url(url: str) -> str:
    """Returns the clean playlist URL for YouTube (https://www.youtube.com/playlist?list=...) or the original URL for other sites."""
    original_url = url
    m = re.search(r'list=([A-Za-z0-9_-]+)', url)
    if m:
        result = f"https://www.youtube.com/playlist?list={m.group(1)}"
        logger.info(f"get_clean_playlist_url: '{original_url}' -> '{result}'")
        return result
    logger.info(f"get_clean_playlist_url: '{original_url}' -> '{original_url}' (no list parameter)")
    return url


def strip_range_from_url(url: str) -> str:
    """Removes a range of the form *1*3 or *1*10000 from the end of the URL."""
    original_url = url
    result = re.sub(r'\*\d+\*\d+$', '', url)
    if original_url != result:
        logger.info(f"strip_range_from_url: '{original_url}' -> '{result}'")
    return result


def db_child_by_path(db, path):
    for part in path.strip("/").split("/"):
        db = db.child(part)
    return db


# round height to popular quality for cache only
# --- Round height to nearest higher popular quality ---
def ceil_to_popular(h):
    popular = [144, 240, 360, 480, 540, 576, 720, 1080, 1440, 2160, 4320]
    for p in popular:
        if h <= p:
            return p
    return popular[-1]


# --- Quickly get the number of cached videos for quality ---
def get_cached_playlist_count(playlist_url: str, quality_key: str, indices: list = None) -> int:
    """
    Returns the number of cached videos for the given quality (based on the number of keys in the database),
    considering and rounded quality_key (ceil_to_popular).
    If a list of indices is passed, it only counts their intersection with the cache.
    For large ranges (>100), it uses a fast count.
    """
    try:
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))))
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))))
        quality_keys = [quality_key]
        try:
            if quality_key.endswith('p'):
                h = int(quality_key[:-1])
                rounded = f"{ceil_to_popular(h)}p"
                if rounded != quality_key:
                    quality_keys.append(rounded)
        except Exception:
            pass

        cached_count = 0
        for u in set(urls):
            url_hash = get_url_hash(u)
            for qk in quality_keys:
                arr = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if not isinstance(arr, list):
                    continue
                if indices is not None:
                    # For large ranges, we use a fast count
                    if len(indices) > 100:
                        try:
                            cached_count = sum(1 for index in indices if index < len(arr) and arr[index] is not None)
                            logger.info(
                                f"get_cached_playlist_count: fast count for large range: {cached_count} cached videos")
                            return cached_count
                        except Exception as e:
                            logger.error(f"get_cached_playlist_count: error in fast count: {e}")
                            continue
                    else:
                        # For small ranges, check each index separately
                        for index in indices:
                            try:
                                if index < len(arr) and arr[index] is not None:
                                    cached_count += 1
                                    logger.info(
                                        f"get_cached_playlist_count: found cached video for index {index} (quality={qk}): {arr[index]}")
                            except Exception as e:
                                logger.error(
                                    f"get_cached_playlist_count: error reading cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                                continue
                else:
                    # Count all non-empty records
                    try:
                        cached_count = sum(1 for item in arr if item is not None)
                    except Exception as e:
                        logger.error(
                            f"get_cached_playlist_count: error reading cache for url_hash={url_hash}, quality={qk}: {e}")
                        continue

                if cached_count > 0:
                    logger.info(f"get_cached_playlist_count: returning {cached_count} cached videos for quality {qk}")
                    return cached_count

        logger.info(f"get_cached_playlist_count: no cached videos found, returning 0")
        return 0
    except Exception as e:
        logger.error(f"get_cached_playlist_count error: {e}")
        return 0

def get_quality_by_min_side(width: int, height: int) -> str:
    """
    Determines the quality by the smaller side of the video.
    Works for both horizontal and vertical videos.
    For example, for 1280×720 returns '720p', for 720×1280 also '720p'.
    """
    min_side = min(width, height)
    quality_map = {
        144: "144p", 256: "144p",
        240: "240p", 426: "240p",
        480: "480p", 854: "480p",
        540: "540p", 960: "540p",
        576: "576p", 1024: "576p",
        720: "720p", 1280: "720p",
        1080: "1080p", 1920: "1080p",
        1440: "1440p", 2560: "1440p",
        2160: "2160p", 3840: "2160p",
        4320: "4320p", 7680: "4320p"
    }
    return quality_map.get(min_side, "best")


def get_real_height_for_quality(quality: str, width: int, height: int) -> int:
    """
    Returns the real height for the given quality, considering the video orientation.
    For example, for quality '720p' and video 1280×720 returns 720, for 720×1280 returns 1280.
    """
    if quality == "best":
        return height  # For best, we use the real height

    try:
        quality_val = int(quality.replace('p', ''))
        # Determine which side corresponds to the selected quality
        if min(width, height) == quality_val:
            # If the smaller
            return height
        else:
            # Otherwise, find the corresponding height
            quality_map = {
                144: [144, 256],
                240: [240, 426],
                480: [480, 854],
                540: [540, 960],
                576: [576, 1024],
                720: [720, 1280],
                1080: [1080, 1920],
                1440: [1440, 2560],
                2160: [2160, 3840],
                4320: [4320, 7680]
            }
            heights = quality_map.get(quality_val, [quality_val])
            # Select the height that is closest to the real height of the video
            return min(heights, key=lambda h: abs(h - height))
    except ValueError:
        return height


def is_no_cookie_domain(url: str) -> bool:
    """
    Checks whether the domain is from the list no_cookie_domains.
    For such domains, you need to use —no-Cookies instead of-Cookies.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # We remove www. If there is
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Check the domain and its subdomain
        for no_cookie_domain in Config.NO_COOKIE_DOMAINS:
            if domain == no_cookie_domain or domain.endswith('.' + no_cookie_domain):
                logger.info(f"URL {url} matches NO_COOKIE_DOMAINS pattern: {no_cookie_domain}")
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking NO_COOKIE_DOMAINS for URL {url}: {e}")
        return False


def is_instagram_url(url: str) -> bool:
    """Check if URL is from Instagram"""
    return any(domain in url.lower() for domain in ['instagram.com', 'www.instagram.com'])


def is_twitter_url(url: str) -> bool:
    """Check if URL is from Twitter/X"""
    return any(domain in url.lower() for domain in ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'])


def is_reddit_url(url: str) -> bool:
    """Check if URL is from Reddit"""
    return any(domain in url.lower() for domain in ['reddit.com', 'www.reddit.com'])


def transform_to_embed_url(url: str) -> str:
    """Transform URL to embeddable format"""
    if is_instagram_url(url):
        # Replace instagram.com with ddinstagram.com
        return url.replace('instagram.com', 'instagramez.com').replace('www.instagramez.com', 'instagramez.com')
    elif is_twitter_url(url):
        # Replace twitter.com/x.com with fxtwitter.com
        return url.replace('twitter.com', 'fxtwitter.com').replace('x.com', 'fxtwitter.com').replace('www.fxtwitter.com', 'fxtwitter.com')
    elif is_reddit_url(url):
        # Replace reddit.com with rxddit.com
        return url.replace('reddit.com', 'rxddit.com').replace('www.rxddit.com', 'rxddit.com')
    return url


@app.on_message(filters.command("subs") & filters.private)
@reply_with_keyboard
def subs_command(app, message):
    """Handle /subs command - show language selection menu"""
    user_id = message.from_user.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    # Enable AUTO-GEN by default if not enabled before
    if not get_user_subs_auto_mode(user_id):
        save_user_subs_auto_mode(user_id, True)

    current_lang = get_user_subs_language(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)

    # Create status text
    if current_lang == "OFF" or current_lang is None:
        status_text = "🚫 Subtitles are disabled"
    else:
        lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
        auto_text = " (auto-subs)" if auto_mode else ""
        status_text = f"{lang_info['flag']} Selected language: {lang_info['name']}{auto_text}"

    app.send_message(
        message.chat.id,
        f"<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:\n\n"
        "<blockquote>❗️WARNING: due to high CPU impact this function is very slow (near real-time) and limited to:\n"
        "- 720p max quality\n"
        "- 1.5 hour max duration\n"
        "- 500mb max video size</blockquote>",
        reply_markup=get_language_keyboard(page=0, user_id=user_id),
        parse_mode=enums.ParseMode.HTML
    )
    send_to_logger(message, "User opened /subs menu.")


@app.on_callback_query(filters.regex(r"^subs_page\|"))
def subs_page_callback(app, callback_query):
    """Handle page navigation in subtitle language selection menu"""
    page = int(callback_query.data.split("|")[1])
    user_id = callback_query.from_user.id
    current_lang = get_user_subs_language(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)
    
    # Create status text
    if current_lang == "OFF" or current_lang is None:
        status_text = "🚫 Subtitles are disabled"
    else:
        lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
        auto_text = " (auto-subs)" if auto_mode else ""
        status_text = f"{lang_info['flag']} Selected language: {lang_info['name']}{auto_text}"
    
    callback_query.edit_message_text(
        f"**💬 Subtitle settings**\n\n{status_text}\n\nSelect subtitle language:",
        reply_markup=get_language_keyboard(page, user_id=user_id)
    )
    callback_query.answer()


@app.on_callback_query(filters.regex(r"^subs_lang\|"))
def subs_lang_callback(app, callback_query):
    """Handle language selection in subtitle language menu"""
    lang_code = callback_query.data.split("|")[1]
    user_id = callback_query.from_user.id
    
    save_user_subs_language(user_id, lang_code)
    
    if lang_code == "OFF":
        status = "🚫 Subtitles are disabled"
    else:
        status = f"✅ Subtitle language set: {LANGUAGES[lang_code]['flag']} {LANGUAGES[lang_code]['name']}"
    
    callback_query.edit_message_text(status)
    callback_query.answer("Subtitle language settings updated.")
    send_to_logger(callback_query.message, f"User set subtitle language to: {lang_code}")

@app.on_callback_query(filters.regex(r"^subs_auto\|"))
def subs_auto_callback(app, callback_query):
    """Handle AUTO-GEN mode toggle in subtitle language menu"""
    parts = callback_query.data.split("|")
    action = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0  # <- Here!
    user_id = callback_query.from_user.id
    
    if action == "toggle":
        current_auto = get_user_subs_auto_mode(user_id)
        new_auto = not current_auto
        save_user_subs_auto_mode(user_id, new_auto)
        
        # We show the notification to the user
        auto_text = "enabled" if new_auto else "disabled"
        notification = f"✅ Auto-subs mode {auto_text}"
        
        # We answer only by notification, do not close the menu
        callback_query.answer(notification, show_alert=False)
        
        # We update the menu with the new Auto state
        current_lang = get_user_subs_language(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        
        # Create status text
        if current_lang == "OFF" or current_lang is None:
            status_text = "🚫 Subtitles are disabled"
        else:
            lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
            auto_text = " (auto-subs)" if auto_mode else ""
            status_text = f"{lang_info['flag']} Selected language: {lang_info['name']}{auto_text}"
        
        # We update the message from the new menu
        callback_query.edit_message_text(
            f"**💬 Subtitle settings**\n\n{status_text}\n\nSelect subtitle language:",
            reply_markup=get_language_keyboard(page=page, user_id=user_id)
        )
        
        send_to_logger(callback_query.message, f"User toggled AUTO-GEN mode to: {new_auto}")

# ---------- GLOBAL ----------
_subs_check_cache = globals().get('_subs_check_cache', {})
_LAST_TIMEDTEXT_TS = globals().get('_LAST_TIMEDTEXT_TS', 0.0)

def clear_subs_check_cache():
    """Cleans the cache of subtitle checks"""
    global _subs_check_cache
    _subs_check_cache.clear()
    logger.info("Subs check cache cleared")

def check_subs_availability(url, user_id, quality_key=None, return_type=False):
    """
    Checks the availability of subtitles for the language chosen by the user.
    If Return_type = True, returns "Normal", "Auto" or None.
    If Return_type = False, returns True/False (are there any saba at all).

    Also caching lists of languages for Normal and Auto.
    """
    try:
        cache_key = f"{url}_{user_id}_{return_type}"
        if cache_key in _subs_check_cache:
            return _subs_check_cache[cache_key]

        subs_lang = get_user_subs_language(user_id)
        if not subs_lang or subs_lang == "OFF":
            _subs_check_cache[cache_key] = False if not return_type else None
            return _subs_check_cache[cache_key]

        # We check the usual subtitles
        available_normal = get_available_subs_languages(url, user_id, auto_only=False)
        has_normal = lang_match(subs_lang, available_normal) is not None
        logger.info(f"check_subs_availability: normal subs - available={available_normal}, has_normal={has_normal}")

        # Check auto -associated subtitles
        available_auto = get_available_subs_languages(url, user_id, auto_only=True)
        has_auto = lang_match(subs_lang, available_auto) is not None
        logger.info(f"check_subs_availability: auto subs - available={available_auto}, has_auto={has_auto}")

        # Cash the found lists of languages separately
        _subs_check_cache[f"{url}_{user_id}_normal_langs"] = available_normal
        _subs_check_cache[f"{url}_{user_id}_auto_langs"] = available_auto

        # Determine the type or presence of sub
        if return_type:
            result = "normal" if has_normal else "auto" if has_auto else None
        else:
            result = has_normal or has_auto

        _subs_check_cache[cache_key] = result
        return result

    except Exception as e:
        logger.error(f"Error checking subtitle availability: {e}")
        return False if not return_type else None


    except Exception as e:
        logger.error(f"Error checking subtitle availability: {e}")
        return False if not return_type else None

def lang_match(user_lang, available_langs):
    # user_lang: for example, 'en', 'en -us', 'zh', 'pt'
    # AVAILABLE_LANGS: a list of all available languages, for example ['en -us', 'EN-GB', 'FR', 'PT-BR']
    logger.info(f"lang_match: user_lang='{user_lang}', available_langs={available_langs}")
    
    if user_lang in available_langs:
        logger.info(f"lang_match: exact match found: {user_lang}")
        return user_lang
    
    # If the basic language is chosen, we look for any prefix with this
    if '-' not in user_lang:
        for lang in available_langs:
            if lang.startswith(user_lang + '-'):
                logger.info(f"lang_match: prefix match found: {lang} for {user_lang}")
                return lang
    
    # If a language with a hyphen is chosen, we are looking for a basic
    if '-' in user_lang:
        base = user_lang.split('-')[0]
        if base in available_langs:
            logger.info(f"lang_match: base match found: {base} for {user_lang}")
            return base
    
    # If the base is selected, we are looking for a duplicate code (ru-RU, EN-EN, etc.)
    if '-' not in user_lang:
        for lang in available_langs:
            if lang.lower() == f'{user_lang.lower()}-{user_lang.lower()}':
                logger.info(f"lang_match: duplicate match found: {lang} for {user_lang}")
                return lang
    
    # NEW: Look for auto-translated subtitles (e.g., 'ru-en' for user_lang='ru')
    if '-' not in user_lang:
        for lang in available_langs:
            if '-' in lang:
                parts = lang.split('-')
                if len(parts) == 2 and parts[0] == user_lang:
                    logger.info(f"lang_match: auto-translated match found: {lang} for {user_lang}")
                    return lang
    
    logger.info(f"lang_match: no match found for {user_lang}")
    return None

def check_file_size_limit(info_dict, max_size_bytes=None):
    """
    Checks if the size of the file is the global limit.
    Returns True if the size is within the limit, otherwise false.
    """
    if max_size_bytes is None:
        max_size_gb = getattr(Config, 'MAX_FILE_SIZE_GB', 10)  # GiB
        max_size_bytes = int(max_size_gb * 1024 ** 3)

    # Check if info_dict is None
    if info_dict is None:
        logger.warning("check_file_size_limit: info_dict is None, allowing download")
        return True

    filesize = info_dict.get('filesize') or info_dict.get('filesize_approx')
    if filesize and filesize > 0:
        size_bytes = int(filesize)
    else:
        # Try to estimate by bitrate (kbit/s) and duration (s)
        tbr = info_dict.get('tbr')
        duration = info_dict.get('duration')
        if tbr and duration:
            size_bytes = float(tbr) * float(duration) * 125  # kbit/s -> bytes
        else:
            # Very rough estimate by resolution and duration
            width = info_dict.get('width')
            height = info_dict.get('height')
            duration = info_dict.get('duration')
            if width and height and duration:
                size_bytes = int(width) * int(height) * float(duration) * 0.07
            else:
                # Could not estimate, allow download
                return True

    return size_bytes <= max_size_bytes

    
def check_subs_limits(info_dict, quality_key=None):
    """
    Checks restrictions for embedding subtitles
    Returns True if subtitles can be built, false if limits are exceeded
    """
    try:
        # Check if info_dict is None
        if info_dict is None:
            logger.warning("check_subs_limits: info_dict is None, allowing subtitle embedding")
            return True
            
        # We get the parameters from the config
        max_quality = Config.MAX_SUB_QUALITY
        max_duration = Config.MAX_SUB_DURATION
        max_size = Config.MAX_SUB_SIZE
        
        # Check the duration
        duration = info_dict.get('duration')
        if duration and duration > max_duration:
            logger.info(f"Subtitle embedding skipped: duration {duration}s exceeds limit {max_duration}s")
            return False
        
        # Check the file size (only if it is accurately known)
        filesize = info_dict.get('filesize') or info_dict.get('filesize_approx')
        if filesize and filesize > 0:  # Check that the size is larger than 0
            size_mb = filesize // (1024 * 1024)
            if size_mb > max_size:
                logger.info(f"Subtitle embedding skipped: size {size_mb}MB exceeds limit {max_size}MB")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking subtitle limits: {e}")
        return False

def get_video_info_ffprobe(video_path):
    import json
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-show_entries', 'format=duration',
            '-of', 'json', video_path
        ], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            width = data['streams'][0]['width'] if data['streams'] else 0
            height = data['streams'][0]['height'] if data['streams'] else 0
            duration = float(data['format']['duration']) if 'format' in data and 'duration' in data['format'] else 0
            return width, height, duration
    except Exception as e:
        logger.error(f'ffprobe error: {e}')
    return 0, 0, 0

def embed_subs_to_video(video_path, user_id, tg_update_callback=None, app=None, message=None):
    """
    Burning (hardcode) subtitles in a video file, if there is any .SRT file and subs.txt
    tg_update_callback (Progress: Float, ETA: StR) - Function for updating the status in Telegram
    """
    try:
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        user_dir = os.path.join("users", str(user_id))
        subs_file = os.path.join(user_dir, "subs.txt")
        if not os.path.exists(subs_file):
            logger.info(f"No subs.txt for user {user_id}, skipping embed_subs_to_video")
            return False
        
        with open(subs_file, "r", encoding="utf-8") as f:
            subs_lang = f.read().strip()
        if not subs_lang or subs_lang == "OFF":
            logger.info(f"Subtitles disabled for user {user_id}")
            return False
        
        video_dir = os.path.dirname(video_path)
        
        # We get video parameters via FFPRobe
        width, height, total_time = get_video_info_ffprobe(video_path)
        if width == 0 or height == 0:
            logger.error(f"Unable to determine video resolution via ffprobe: width={width}, height={height}")
            return False
        original_size = os.path.getsize(video_path)

        # Checking the duration of the video
        if total_time and total_time > Config.MAX_SUB_DURATION:
            logger.info(f"Video duration too long for subtitles: {total_time} sec")
            return False

        # Checking the file size
        original_size_mb = original_size / (1024 * 1024)
        if original_size_mb > Config.MAX_SUB_SIZE:
            logger.info(f"Video file too large for subtitles: {original_size_mb:.2f} MB")
            return False

        # Video quality testing on the smallest side
        # Logue video parameters before checking quality
        logger.info(f"Quality check: width={width}, height={height}, min_side={min(width, height)}, limit={Config.MAX_SUB_QUALITY}")
        if min(width, height) > Config.MAX_SUB_QUALITY:
            logger.info(f"Video quality too high for subtitles: {width}x{height}, min side: {min(width, height)}p > {Config.MAX_SUB_QUALITY}p")
            return False

        # --- Simplified search: take any .SRT file in the folder ---
        srt_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.srt')]
        if not srt_files:
            logger.info(f"No .srt files found in {video_dir}")
            return False
        
        subs_path = os.path.join(video_dir, srt_files[0])
        if not os.path.exists(subs_path):
            logger.error(f"Subtitle file not found: {subs_path}")
            return False

        # Always bring .SRT to UTF-8
        subs_path = ensure_utf8_srt(subs_path)
        if not subs_path or not os.path.exists(subs_path) or os.path.getsize(subs_path) == 0:
            logger.error(f"Subtitle file after ensure_utf8_srt is missing or empty: {subs_path}")
            return False

        # Forcibly correcting Arab cracies
        if subs_lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
            subs_path = force_fix_arabic_encoding(subs_path, subs_lang)
        if not subs_path or not os.path.exists(subs_path) or os.path.getsize(subs_path) == 0:
            logger.error(f"Subtitle file after force_fix_arabic_encoding is missing or empty: {subs_path}")
            return False
        
        video_base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_base}_with_subs_temp.mp4")
        
        # We get the duration of the video via FFPRobe
        def get_duration(path):
            try:
                import json
                result = subprocess.run([
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'json', path
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return float(data['format']['duration'])
            except Exception as e:
                logger.error(f"ffprobe error: {e}")
            return None
        
        # Field of subtitles with improved styling
        subs_path_escaped = subs_path.replace("'", "'\\''")
        # Add translucent black stroke like YouTube and an improved display of subtitles
        filter_arg = f"subtitles='{subs_path_escaped}':force_style='FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=25'"
        cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-vf', filter_arg,
            '-c:a', 'copy',
            output_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        progress = 0.0
        last_update = time.time()
        eta = "?"
        time_pattern = re.compile(r'time=([0-9:.]+)')
        
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            logger.info(line.strip())
            match = time_pattern.search(line)
            if match and total_time:
                t = match.group(1)
                # Transform T (hh: mm: ss.xx) in seconds
                h, m, s = 0, 0, 0.0
                parts = t.split(':')
                if len(parts) == 3:
                    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
                elif len(parts) == 2:
                    m, s = int(parts[0]), float(parts[1])
                elif len(parts) == 1:
                    s = float(parts[0])
                cur_sec = h * 3600 + m * 60 + s
                progress = min(cur_sec / total_time, 1.0)
                # ETA
                if progress > 0:
                    elapsed = time.time() - last_update
                    eta_sec = int((1.0 - progress) * (elapsed / progress)) if progress > 0 else 0
                    eta = f"{eta_sec//60}:{eta_sec%60:02d}"
                # Update every 10 seconds or with a change in progress> 1%
                if tg_update_callback and (time.time() - last_update > 10 or progress >= 1.0):
                    tg_update_callback(progress, eta)
                    last_update = time.time()
        
        proc.wait()
        
        if proc.returncode != 0:
            logger.error(f"FFmpeg error: process exited with code {proc.returncode}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Check that the file exists and is not empty
        if not os.path.exists(output_path):
            logger.error("Output file does not exist after ffmpeg")
            return False
        
        # We are waiting a little so that the file will definitely complete the recording
        time.sleep(1)
        
        output_size = os.path.getsize(output_path)
        original_size = os.path.getsize(video_path)
        
        if output_size == 0:
            logger.error("Output file is empty")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # We check that the final file is not too small (there should be at least 50% of the original)
        if output_size < original_size * 0.5:
            logger.error(f"Output file too small: {output_size} bytes (original: {original_size} bytes)")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Safely replace the file
        backup_path = video_path + ".backup"
        try:
            os.rename(video_path, backup_path)   # Create a backup
            os.rename(output_path, video_path)   # Rename the result
            os.remove(backup_path)               # Delete backup
        except Exception as e:
            logger.error(f"Error replacing video file: {e}")
            # Restore the source file
            if os.path.exists(backup_path):
                os.rename(backup_path, video_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Send .SRT to the user before removing
        if os.path.exists(subs_path):
            try:
                if app is not None and message is not None:
                    sent_msg = app.send_document(
                        chat_id=user_id,
                        document=subs_path,
                        caption="<blockquote>💬 Subtitles SRT-file</blockquote>",
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
                    safe_forward_messages(Config.LOGS_ID, user_id, [sent_msg.id])
                    send_to_logger(message, "💬 Subtitles SRT-file sent to user.") 
            except Exception as e:
                logger.error(f"Error sending srt file: {e}")
            try:
                os.remove(subs_path)
            except Exception as e:
                logger.error(f"Error deleting srt file: {e}")
        
        logger.info("Successfully burned-in subtitles")
        return True
        
    except Exception as e:
        logger.error(f"Error in embed_subs_to_video: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# Run the automatic loading of the Firebase cache
start_auto_cache_reloader()

app.run()
