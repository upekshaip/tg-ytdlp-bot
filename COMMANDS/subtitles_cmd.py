# Subtitles command
import yt_dlp
import requests
import time
import re
from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.decorators import reply_with_keyboard
from HELPERS.logger import logger, send_to_logger
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_forward_messages
from DOWN_AND_UP.yt_dlp_hook import get_video_formats
from URL_PARSERS.youtube import is_youtube_url
import math
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from CONFIG.config import Config
import os

# Get app instance for decorators
app = get_app()

_subs_check_cache = globals().get('_subs_check_cache', {})
_LAST_TIMEDTEXT_TS = globals().get('_LAST_TIMEDTEXT_TS', 0.0)

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

#############################################################################################################################



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
                    f"<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:",
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
            f"<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:",
            reply_markup=get_language_keyboard(page=page, user_id=user_id)
        )
        
        send_to_logger(callback_query.message, f"User toggled AUTO-GEN mode to: {new_auto}")

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

#############################################################################################

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

            # Clean filename for Windows compatibility
            title = info.get('title', 'video')
            # Remove/replace invalid characters for Windows filenames
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                title = title.replace(char, '_')
            # Also replace other problematic characters
            title = title.replace('|', '_').replace('\\', '_').replace('/', '_')
            base_name = f"{title[:50]}.{found_lang}.{ext}"
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

######################################################

