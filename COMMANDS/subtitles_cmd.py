# Subtitles command
import yt_dlp
import requests
import time
import re
import random
import json
from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.decorators import reply_with_keyboard, background_handler
from HELPERS.logger import logger, send_to_logger
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_forward_messages
from DOWN_AND_UP.yt_dlp_hook import get_video_formats
from URL_PARSERS.youtube import is_youtube_url
from HELPERS.pot_helper import add_pot_to_ytdl_opts
import math
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
import os
import glob

# Get app instance for decorators
app = get_app()

_subs_check_cache = globals().get('_subs_check_cache', {})
_LAST_TIMEDTEXT_TS = globals().get('_LAST_TIMEDTEXT_TS', 0.0)

# Per-session helpers to manage subtitle cache for a specific user+URL
def clear_subs_cache_for(user_id: int, url: str) -> int:
    """Clear subtitle availability cache entries for a specific user and URL.
    Returns number of removed entries."""
    global _subs_check_cache
    try:
        keys = list(_subs_check_cache.keys())
        removed = 0
        prefix = f"{url}_{user_id}"
        for k in keys:
            if isinstance(k, str) and k.startswith(prefix):
                _subs_check_cache.pop(k, None)
                removed += 1
        return removed
    except Exception as e:
        logger.debug(f"clear_subs_cache_for error: {e}")
        return 0

def get_or_compute_subs_langs(user_id: int, url: str):
    """Return (normal_langs, auto_langs) for URL, preferring per-session cache.
    Falls back to computing via yt-dlp once and persists to per-session cache file."""
    try:
        # Try session cache file first (managed by Always Ask)
        try:
            from DOWN_AND_UP.always_ask_menu import load_subs_langs_cache, save_subs_langs_cache
            cached = load_subs_langs_cache(user_id, url)
        except Exception:
            cached = None
        if cached and isinstance(cached, tuple) and len(cached) == 2:
            normal, auto = cached
            if (normal or auto):
                return list(normal or []), list(auto or [])

        # Otherwise compute once and persist
        normal = get_available_subs_languages(url, user_id, auto_only=False)
        auto   = get_available_subs_languages(url, user_id, auto_only=True)
        try:
            from DOWN_AND_UP.always_ask_menu import save_subs_langs_cache
            save_subs_langs_cache(user_id, url, normal, auto)
        except Exception:
            pass
        return list(normal or []), list(auto or [])
    except Exception as e:
        logger.debug(f"get_or_compute_subs_langs error: {e}")
        return [], []

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
    "zh-Hant": {"flag": "🇹🇼", "name": "中文(繁體)"},
    # Additional YouTube-supported languages
    "te": {"flag": "🇮🇳", "name": "తెలుగు"},
    "ta": {"flag": "🇮🇳", "name": "தமிழ்"},
    "mr": {"flag": "🇮🇳", "name": "मराठी"},
    "kn": {"flag": "🇮🇳", "name": "ಕನ್ನಡ"},
    "ml": {"flag": "🇮🇳", "name": "മലയാളം"},
    "gu": {"flag": "🇮🇳", "name": "ગુજરાતી"},
    "pa": {"flag": "🇮🇳", "name": "ਪੰਜਾਬੀ"},
    "ur": {"flag": "🇵🇰", "name": "اردو"},
    "ne": {"flag": "🇳🇵", "name": "नेपाली"},
    "si": {"flag": "🇱🇰", "name": "සිංහල"},
    "my": {"flag": "🇲🇲", "name": "မြန်မာ"},
    "km": {"flag": "🇰🇭", "name": "ភាសាខ្មែរ"},
    "lo": {"flag": "🇱🇦", "name": "ລາວ"},
    "ms": {"flag": "🇲🇾", "name": "Bahasa Melayu"},
    "fil": {"flag": "🇵🇭", "name": "Filipino"},
    "am": {"flag": "🇪🇹", "name": "አማርኛ"},
    "az": {"flag": "🇦🇿", "name": "Azərbaycan"},
    "ka": {"flag": "🇬🇪", "name": "ქართული"},
    "ky": {"flag": "🇰🇬", "name": "Кыргызча"},
    "uz": {"flag": "🇺🇿", "name": "Oʻzbekcha"},
    "tg": {"flag": "🇹🇯", "name": "Тоҷикӣ"},
    "tk": {"flag": "🇹🇲", "name": "Türkmen"},
    "mn": {"flag": "🇲🇳", "name": "Монгол"},
    "ps": {"flag": "🇦🇫", "name": "پښتو"},
    "or": {"flag": "🇮🇳", "name": "ଓଡ଼ିଆ"},
    "as": {"flag": "🇮🇳", "name": "অসমীয়া"},
    "ca": {"flag": "🇪🇸", "name": "Català"},
    "gl": {"flag": "🇪🇸", "name": "Galego"},
    "eu": {"flag": "🇪🇸", "name": "Euskara"},
    "af": {"flag": "🇿🇦", "name": "Afrikaans"},
    "sq": {"flag": "🇦🇱", "name": "Shqip"},
    "mk": {"flag": "🇲🇰", "name": "Македонски"},
    "bs": {"flag": "🇧🇦", "name": "Bosanski"},
    "is": {"flag": "🇮🇸", "name": "Íslenska"},
    "ga": {"flag": "🇮🇪", "name": "Gaeilge"},
    "cy": {"flag": "🇬🇧", "name": "Cymraeg"},
    "gd": {"flag": "🇬🇧", "name": "Gàidhlig"},
    "lb": {"flag": "🇱🇺", "name": "Lëtzebuergesch"},
    "mt": {"flag": "🇲🇹", "name": "Malti"},
    "sw": {"flag": "🇰🇪", "name": "Kiswahili"},
    "zu": {"flag": "🇿🇦", "name": "isiZulu"},
    "xh": {"flag": "🇿🇦", "name": "isiXhosa"},
    "ha": {"flag": "🇳🇬", "name": "Hausa"},
    "yo": {"flag": "🇳🇬", "name": "Yorùbá"},
    "ig": {"flag": "🇳🇬", "name": "Igbo"}
}


# Fallback flag for unknown/region languages
DEFAULT_FLAG = "🌐"

# Fallback flags for many 2-letter language codes not present in LANGUAGES
LANG_FALLBACK_FLAGS = {
    "aa": "🇩🇯",  # Afar → Djibouti
    "ab": "🇬🇪",  # Abkhaz → Georgia
    "ak": "🇬🇭",  # Akan → Ghana
    "am": "🇪🇹",
    "as": "🇮🇳",
    "ay": "🇧🇴",
    "ba": "🇷🇺",
    "bho": "🇮🇳",
    "bo": "🇨🇳",
    "br": "🇫🇷",
    "ceb": "🇵🇭",
    "co": "🇫🇷",
    "crs": "🇸🇨",
    "cy": "🇬🇧",
    "da": "🇩🇰",
    "dz": "🇧🇹",
    "gd": "🇬🇧",
    "gv": "🇮🇲",
    "ha": "🇳🇬",
    "haw": "🇺🇸",
    "hmn": "🌐",
    "ht": "🇭🇹",
    "ig": "🇳🇬",
    "iu": "🇨🇦",
    "jv": "🇮🇩",
    "kk": "🇰🇿",
    "kl": "🇬🇱",
    "km": "🇰🇭",
    "kn": "🇮🇳",
    "ky": "🇰🇬",
    "lb": "🇱🇺",
    "lg": "🇺🇬",
    "ln": "🇨🇩",
    "lo": "🇱🇦",
    "lt": "🇱🇹",
    "lv": "🇱🇻",
    "mk": "🇲🇰",
    "mn": "🇲🇳",
    "mt": "🇲🇹",
    "ne": "🇳🇵",
    "ny": "🇲🇼",
    "oc": "🇫🇷",
    "om": "🇪🇹",
    "or": "🇮🇳",
    "os": "🇷🇺",
    "pa": "🇮🇳",
    "ps": "🇦🇫",
    "qu": "🇵🇪",
    "rn": "🇧🇮",
    "rw": "🇷🇼",
    "sg": "🇨🇫",
    "si": "🇱🇰",
    "sm": "🇼🇸",
    "sn": "🇿🇼",
    "so": "🇸🇴",
    "sr": "🇷🇸",
    "ss": "🇿🇦",
    "st": "🇱🇸",
    "su": "🇮🇩",
    "ta": "🇮🇳",
    "te": "🇮🇳",
    "tg": "🇹🇯",
    "ti": "🇪🇷",
    "tk": "🇹🇲",
    "tn": "🇧🇼",
    "to": "🇹🇴",
    "ts": "🇿🇦",
    "tt": "🇷🇺",
    "ug": "🇨🇳",
    "ur": "🇵🇰",
    "uz": "🇺🇿",
    "ve": "🇿🇦",
    "vi": "🇻🇳",
    "wo": "🇸🇳",
    "xh": "🇿🇦",
    "yi": "🇺🇸",
    "yo": "🇳🇬",
    "zu": "🇿🇦",
}

def get_flag(lang_code: str, use_second_part: bool = False) -> str:
    """
    Get flag for language code.
    use_second_part: True for SUBS (use second part like DE from de-DE), False for DUBS (use first part like de from de-DE)
    """
    if lang_code in LANGUAGES:
        return LANGUAGES[lang_code]["flag"]
    
    # For SUBS: use second part (e.g., DE from de-DE)
    if use_second_part and '-' in lang_code:
        second_part = lang_code.split('-')[1]
        if second_part in LANGUAGES:
            return LANGUAGES[second_part]["flag"]
        # Try common country codes
        country_flags = {
            'DE': '🇩🇪', 'FR': '🇫🇷', 'US': '🇺🇸', 'GB': '🇬🇧', 'IT': '🇮🇹', 'BR': '🇧🇷',
            'ES': '🇪🇸', 'RU': '🇷🇺', 'CN': '🇨🇳', 'JP': '🇯🇵', 'KR': '🇰🇷', 'IN': '🇮🇳'
        }
        if second_part in country_flags:
            return country_flags[second_part]
    
    # For DUBS: use first part (e.g., de from de-DE)
    if not use_second_part and '-' in lang_code:
        first_part = lang_code.split('-')[0]
        if first_part in LANGUAGES:
            return LANGUAGES[first_part]["flag"]
    
    # Try fallback mapping directly
    base_try = lang_code.split('-')[0]
    if base_try in LANG_FALLBACK_FLAGS:
        return LANG_FALLBACK_FLAGS[base_try]

    # Try base code
    if '-' in lang_code:
        base = lang_code.split('-')[0]
        if base in LANGUAGES:
            return LANGUAGES[base]["flag"]
    
    return DEFAULT_FLAG


#ITEMS_PER_PAGE = 10  # Number of languages per page

#############################################################################################################################



@app.on_message(filters.command("subs") & filters.private)
@reply_with_keyboard
@background_handler(label="subs_command")
def subs_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Handle /subs command - show language selection menu"""
    user_id = message.from_user.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return


    # Fast args: /subs on|off|ru|ru auto  -> Various subtitle settings
    parts = (message.text or "").split()
    if len(parts) >= 2:
        arg = parts[1].lower()
        
        # /subs off
        if arg == "off":
            save_subs_always_ask(user_id, False)
            save_user_subs_language(user_id, "OFF")
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(user_id, safe_get_messages(user_id).SUBS_DISABLED_MSG, message=message)
            send_to_logger(message, safe_get_messages(user_id).SUBS_DISABLED_LOG_MSG.format(arg=arg))
            return
        
        # /subs on
        elif arg == "on":
            save_subs_always_ask(user_id, True)
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(user_id, safe_get_messages(user_id).SUBS_ALWAYS_ASK_ENABLED_MSG, message=message)
            send_to_logger(message, safe_get_messages(user_id).SUBS_ALWAYS_ASK_ENABLED_LOG_MSG.format(arg=arg))
            return
        
        # /subs ru (language code)
        elif arg in LANGUAGES:
            save_user_subs_language(user_id, arg)
            lang_info = LANGUAGES[arg]
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(user_id, safe_get_messages(user_id).SUBS_LANGUAGE_SET_MSG.format(flag=lang_info['flag'], name=lang_info['name']), message=message)
            send_to_logger(message, safe_get_messages(user_id).SUBS_LANGUAGE_SET_LOG_MSG.format(arg=arg))
            return
        
        # /subs ru auto (language + auto mode)
        elif len(parts) >= 3 and parts[2].lower() == "auto" and arg in LANGUAGES:
            save_user_subs_language(user_id, arg)
            save_user_subs_auto_mode(user_id, True)
            lang_info = LANGUAGES[arg]
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(user_id, safe_get_messages(user_id).SUBS_LANGUAGE_AUTO_SET_MSG.format(flag=lang_info['flag'], name=lang_info['name']), message=message)
            send_to_logger(message, safe_get_messages(user_id).SUBS_LANGUAGE_AUTO_SET_LOG_MSG.format(arg=arg))
            return
        
        # Invalid argument
        else:
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(user_id, 
                safe_get_messages(user_id).SUBS_INVALID_ARGUMENT_MSG +
                safe_get_messages(user_id).SUBS_VALID_OPTIONS_MSG + "\n" +
                safe_get_messages(user_id).SUBS_DISABLE_COMMAND_MSG +
                safe_get_messages(user_id).SUBS_ENABLE_ASK_MODE_MSG +
                safe_get_messages(user_id).SUBS_SET_LANGUAGE_MSG +
                safe_get_messages(user_id).SUBS_SET_LANGUAGE_AUTO_MSG +
                safe_get_messages(user_id).SUBS_EXAMPLE_AUTO_MSG,
                message=message
            )
            return


    # Enable AUTO/TRANS by default if not enabled before
    if not get_user_subs_auto_mode(user_id):
        save_user_subs_auto_mode(user_id, True)

    current_lang = get_user_subs_language(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)

    # Create status text
    if current_lang == "OFF" or current_lang is None:
        status_text = safe_get_messages(user_id).SUBS_DISABLED_STATUS_MSG
    else:
        lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
        auto_text = safe_get_messages(user_id).SUBS_AUTO_SUBS_TEXT if auto_mode else ""
        status_text = safe_get_messages(user_id).SUBS_SELECTED_LANGUAGE_MSG.format(flag=lang_info['flag'], name=lang_info['name'], auto_text=auto_text)

    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(
        message.chat.id,
        safe_get_messages(user_id).SUBS_SETTINGS_MENU_MSG.format(status_text=status_text) +
        safe_get_messages(user_id).SUBS_WARNING_MSG +
        safe_get_messages(user_id).SUBS_LIMITATIONS_MSG +
        safe_get_messages(user_id).SUBS_QUICK_COMMANDS_MSG +
        safe_get_messages(user_id).SUBS_SETTINGS_ADDITIONAL_MSG +
        safe_get_messages(user_id).SUBS_SET_LANGUAGE_CODE_MSG +
        "• <code>/subs ru</code> - set language\n" +
        "• <code>/subs ru auto</code> - set language with AUTO/TRANS",
        reply_markup=get_language_keyboard(page=0, user_id=user_id, per_page_rows=8),
        parse_mode=enums.ParseMode.HTML,
        message=message
    )
    send_to_logger(message, safe_get_messages(user_id).SUBS_MENU_OPENED_LOG_MSG)


@app.on_callback_query(filters.regex(r"^subs_page\|"))
def subs_page_callback(app, callback_query):
    """Handle page navigation in subtitle language selection menu"""
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    page = int(callback_query.data.split("|")[1])
    current_lang = get_user_subs_language(user_id)
    auto_mode = get_user_subs_auto_mode(user_id)
    
    # Create status text
    if current_lang == "OFF" or current_lang is None:
        status_text = safe_get_messages(user_id).SUBS_DISABLED_STATUS_MSG
    else:
        lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
        auto_text = safe_get_messages(user_id).SUBS_AUTO_SUBS_TEXT if auto_mode else ""
        status_text = safe_get_messages(user_id).SUBS_SELECTED_LANGUAGE_MSG.format(flag=lang_info['flag'], name=lang_info['name'], auto_text=auto_text)
    
    callback_query.edit_message_text(
        safe_get_messages(user_id).SUBS_SETTINGS_MENU_MSG.format(status_text=status_text) +
        safe_get_messages(user_id).SUBS_QUICK_COMMANDS_MSG +
        safe_get_messages(user_id).SUBS_SETTINGS_ADDITIONAL_MSG +
        safe_get_messages(user_id).SUBS_SET_LANGUAGE_CODE_MSG +
        "• <code>/subs ru</code> - set language\n" +
        "• <code>/subs ru auto</code> - set language with AUTO/TRANS",
        reply_markup=get_language_keyboard(page, user_id=user_id)
    )
    callback_query.answer()


@app.on_callback_query(filters.regex(r"^subs_lang\|"))
def subs_lang_callback(app, callback_query):
    """Handle language selection in subtitle language menu"""
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    lang_code = callback_query.data.split("|")[1]
    
    save_user_subs_language(user_id, lang_code)
    
    if lang_code == "OFF":
        status = safe_get_messages(user_id).SUBS_DISABLED_STATUS_MSG
    else:
        status = safe_get_messages(user_id).SUBS_LANGUAGE_SET_STATUS_MSG.format(flag=LANGUAGES[lang_code]['flag'], name=LANGUAGES[lang_code]['name'])
    
    callback_query.edit_message_text(status)
    callback_query.answer(safe_get_messages(user_id).SUBS_LANGUAGE_UPDATED_MSG)
    send_to_logger(callback_query.message, safe_get_messages(user_id).SUBS_LANGUAGE_SET_CALLBACK_LOG_MSG.format(lang_code=lang_code))

@app.on_callback_query(filters.regex(r"^subs_auto\|"))
def subs_auto_callback(app, callback_query):
    """Handle AUTO/TRANS mode toggle in subtitle language menu"""
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    parts = callback_query.data.split("|")
    action = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0  # <- Here!
    
    if action == "toggle":
        current_auto = get_user_subs_auto_mode(user_id)
        new_auto = not current_auto
        save_user_subs_auto_mode(user_id, new_auto)
        
        # We show the notification to the user
        auto_text = "enabled" if new_auto else "disabled"
        notification = safe_get_messages(user_id).SUBS_AUTO_MODE_TOGGLE_MSG.format(status=auto_text)
        
        # We answer only by notification, do not close the menu
        callback_query.answer(notification, show_alert=False)
        
        # We update the menu with the new Auto state
        current_lang = get_user_subs_language(user_id)
        auto_mode = get_user_subs_auto_mode(user_id)
        
        # Create status text
        if current_lang == "OFF" or current_lang is None:
            status_text = safe_get_messages(user_id).SUBS_DISABLED_STATUS_MSG
        else:
            lang_info = LANGUAGES.get(current_lang, {"name": current_lang, "flag": "🌐"})
            auto_text = safe_get_messages(user_id).SUBS_AUTO_SUBS_TEXT if auto_mode else ""
            status_text = safe_get_messages(user_id).SUBS_SELECTED_LANGUAGE_MSG.format(flag=lang_info['flag'], name=lang_info['name'], auto_text=auto_text)
        
        # We update the message from the new menu
        callback_query.edit_message_text(
            safe_get_messages(user_id).SUBS_AUTO_MENU_MSG.format(status_text=status_text),
            reply_markup=get_language_keyboard(page=page, user_id=user_id)
        )
        
        send_to_logger(callback_query.message, safe_get_messages(user_id).SUBS_AUTO_MODE_TOGGLED_LOG_MSG.format(new_auto=new_auto))


@app.on_callback_query(filters.regex(r"^subs_always_ask\|"))
def subs_always_ask_callback(app, callback_query):
    """Handle Always Ask mode toggle in subtitle language menu"""
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    parts = callback_query.data.split("|")
    action = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    
    if action == "toggle":
        current_always_ask = is_subs_always_ask(user_id)
        new_always_ask = not current_always_ask
        save_subs_always_ask(user_id, new_always_ask)
        
        # Show notification
        always_ask_text = "enabled" if new_always_ask else "disabled"
        notification = safe_get_messages(user_id).SUBS_ALWAYS_ASK_TOGGLE_MSG.format(status=always_ask_text)
        callback_query.answer(notification, show_alert=False)
        
        # Auto-close menu after toggling Always Ask
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        
        send_to_logger(callback_query.message, safe_get_messages(user_id).SUBS_ALWAYS_ASK_TOGGLED_LOG_MSG.format(new_always_ask=new_always_ask))


@app.on_callback_query(filters.regex(r"^subs_lang_close\|"))
def subs_lang_close_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).SUBS_MENU_CLOSED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).SUBS_LANGUAGE_MENU_CLOSED_MSG)
        return

#############################################################################################

def clear_subs_check_cache():
    """Cleans the cache of subtitle checks"""
    global _subs_check_cache
    _subs_check_cache.clear()
    
    # Also clean up temporary language cache files from Always Ask menu
    try:
        # Find all user directories
        if os.path.exists("users"):
            for user_dir in os.listdir("users"):
                user_path = os.path.join("users", user_dir)
                if os.path.isdir(user_path):
                    # Remove ask_subs_*.json files
                    pattern = os.path.join(user_path, "ask_subs_*.json")
                    for cache_file in glob.glob(pattern):
                        try:
                            os.remove(cache_file)
                            logger.info(f"Removed temp subs cache: {cache_file}")
                        except Exception as e:
                            logger.debug(f"Failed to remove {cache_file}: {e}")
    except Exception as e:
        logger.debug(f"Error cleaning temp subs cache files: {e}")
    
    logger.info("Subs check cache cleared")

def check_subs_availability(url, user_id, quality_key=None, return_type=False):
    messages = safe_get_messages(user_id)
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

def lang_match(user_lang, available_langs):
    # user_lang: for example, 'en', 'en -us', 'zh', 'pt'
    # AVAILABLE_LANGS: a list of all available languages, for example ['en -us', 'EN-GB', 'FR', 'PT-BR']
    logger.info(f"{LoggerMsg.SUBS_LANG_MATCH_USER_LANG_LOG_MSG}")
    
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
                logger.info(f"{LoggerMsg.SUBS_LANG_MATCH_DUPLICATE_LOG_MSG}")
                return lang
    
    # NEW: Look for auto-translated subtitles (e.g., 'ru-en' for user_lang='ru')
    if '-' not in user_lang:
        for lang in available_langs:
            if '-' in lang:
                parts = lang.split('-')
                if len(parts) == 2 and parts[0] == user_lang:
                    logger.info(f"{LoggerMsg.SUBS_LANG_MATCH_AUTO_TRANSLATED_LOG_MSG}")
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
            logger.info(f"{LoggerMsg.SUBS_SUCCESSFULLY_DECODED_LOG_MSG}")
            break
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"{LoggerMsg.SUBS_FAILED_TO_DECODE_LOG_MSG}")
            continue

    # If no encoding has worked, we use Force Decode
    if decoded_text is None:
        logger.warning("All encodings did not work, I use force decode")
        decoded_text = raw.decode('utf-8', errors='replace')
        successful_encoding = 'utf-8 (force)'

    # We check if there are replacement symbols in the text (Unicode replacement char or '?')
    if '\ufffd' in decoded_text or '?' in decoded_text:
        logger.warning(f"{LoggerMsg.SUBS_REPLACEMENT_CHARACTERS_FOUND_LOG_MSG}")
        
        # We try again with other encodings, ignoring the already tried
        for encoding in ['cp1256', 'iso-8859-6', 'cp1252', 'utf-8-sig']:
            if encoding not in [enc.lower() for enc in encodings_to_try[:len(encodings_to_try)//2]]:
                try:
                    test_text = raw.decode(encoding)
                    if '' not in test_text and '?' not in test_text:
                        decoded_text = test_text
                        successful_encoding = encoding
                        logger.info(f"{LoggerMsg.SUBS_BEST_ENCODING_FOUND_LOG_MSG}")
                        break
                except:
                    continue

    # Record the result in UTF-8
    try:
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        logger.info(f"{LoggerMsg.SUBS_FILE_SUCCESSFULLY_ENCODED_UTF8_LOG_MSG}")
        return srt_path
    except Exception as e:
        logger.error(f"Error writing file {srt_path}: {e}")
        return None

def get_user_subs_language(user_id):
    messages = safe_get_messages(user_id)
    """Get user's preferred subtitle language"""
    user_dir = os.path.join("users", str(user_id))
    subs_file = os.path.join(user_dir, "subs.txt")
    if os.path.exists(subs_file):
        with open(subs_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def is_subs_enabled(user_id):
    messages = safe_get_messages(user_id)
    lang = get_user_subs_language(user_id)
    return lang is not None and lang != "OFF"

def save_subs_always_ask(user_id, enabled: bool):
    messages = safe_get_messages(user_id)
    """Persist Always Ask mode for subtitles (controls 💬 SUBS button in Always Ask)."""
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    path = os.path.join(user_dir, "subs_always_ask.txt")
    if enabled:
        with open(path, "w", encoding="utf-8") as f:
            f.write("ON")
    else:
        if os.path.exists(path):
            os.remove(path)

def is_subs_always_ask(user_id) -> bool:
    user_dir = os.path.join("users", str(user_id))
    path = os.path.join(user_dir, "subs_always_ask.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip().upper() == "ON"
        except Exception:
            return False
    return False

def save_user_subs_language(user_id, lang_code):
    messages = safe_get_messages(user_id)
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
    messages = safe_get_messages(user_id)
    """Get user's AUTO mode setting for subtitles"""
    user_dir = os.path.join("users", str(user_id))
    auto_file = os.path.join(user_dir, "subs_auto.txt")
    if os.path.exists(auto_file):
        with open(auto_file, "r", encoding="utf-8") as f:
            return f.read().strip() == "ON"
    return False

def save_user_subs_auto_mode(user_id, auto_enabled):
    messages = safe_get_messages(user_id)
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
    messages = safe_get_messages(user_id)
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
        for client in ('tv', None):  # Only try tv client since it always works
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
                logger.info(f"{LoggerMsg.SUBS_YOUTUBE_PLAYER_CLIENT_RETURNED_CAPTIONS_LOG_MSG}")
                _subs_check_cache[f"{url}_{user_id}_client"] = used_client
                return info
            logger.info(f"{LoggerMsg.SUBS_PLAYER_CLIENT_NO_CAPTIONS_LOG_MSG}")
            last_info = info
        _subs_check_cache[f"{url}_{user_id}_client"] = used_client or 'default'
        return last_info

    def _list_via_timedtext(u: str):
        """Fallback: query YouTube timedtext list endpoint and split normal/auto (asr)."""
        try:
            import requests
            import re as _re
            # extract video id
            vid = None
            m = _re.search(r"[?&]v=([\w-]{11})", u)
            if m:
                vid = m.group(1)
            if not vid:
                m = _re.search(r"youtu\.be/([\w-]{11})", u)
                if m:
                    vid = m.group(1)
            if not vid:
                return [], []
            tt_url = f"https://www.youtube.com/api/timedtext?type=list&v={vid}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(tt_url, headers=headers, timeout=15)
            if r.status_code != 200 or not r.text:
                return [], []
            normal, auto = [], []
            # Parse simple XML lines
            for m in _re.finditer(r'<track[^>]*lang_code="([^"]+)"[^>]*>', r.text):
                tag = m.group(0)
                code = m.group(1)
                if 'kind="asr"' in tag or "kind='asr'" in tag:
                    auto.append(code)
                else:
                    normal.append(code)
            return list(set(normal)), list(set(auto))
        except Exception as _e:
            logger.warning(f"timedtext list fallback failed: {_e}")
            return [], []

    for attempt in range(MAX_RETRIES):
        try:
            info = extract_info_with_cookies()
            normal = list(info.get('subtitles', {}).keys())
            auto   = list(info.get('automatic_captions', {}).keys())
            result = list(set(auto if auto_only else normal))
            logger.info(f"get_available_subs_languages: auto_only={auto_only}, result={result}")
            # Fallback to timedtext list if nothing found
            if not normal and not auto:
                tt_normal, tt_auto = _list_via_timedtext(url)
                if tt_normal or tt_auto:
                    logger.info(f"get_available_subs_languages: timedtext fallback normal={tt_normal}, auto={tt_auto}")
                    _subs_check_cache[f"{url}_{user_id}_normal_langs"] = tt_normal
                    _subs_check_cache[f"{url}_{user_id}_auto_langs"] = tt_auto
                    return tt_auto if auto_only else tt_normal
            return result

        except yt_dlp.utils.DownloadError as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                delay = backoff(attempt)
                logger.warning(f"{LoggerMsg.SUBS_429_TOO_MANY_REQUESTS_SLEEP_LOG_MSG}")
                time.sleep(delay)
                continue
            logger.error(f"{LoggerMsg.SUBS_DOWNLOAD_ERROR_GETTING_SUBTITLES_LOG_MSG}")
            break
        except Exception as e:
            logger.error(f"{LoggerMsg.SUBS_UNEXPECTED_ERROR_GETTING_SUBTITLES_LOG_MSG}")
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
            if bad and bad < min_bad:
                min_bad = bad
                best_text = text
                best_enc = enc

        if best_text is None:
            best_text = raw.decode('utf-8', errors='replace')
            best_enc  = 'utf-8(force)'

        best_text = best_text.replace('\r\n', '\n').replace('\r', '\n').replace('\ufeff', '')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(best_text)

        logger.info(f"{LoggerMsg.SUBS_FORCE_FIX_ARABIC_ENCODING_LOG_MSG}")
        return srt_path
    except Exception as e:
        logger.error(f"{LoggerMsg.SUBS_FORCE_FIX_ARABIC_ENCODING_ERROR_LOG_MSG}")
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
    messages = safe_get_messages(user_id)
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
            if delta and delta < 1.5:
                time.sleep(1.5 - delta)

            r = sess.get(url_tt, headers=headers, timeout=25)
            _LAST_TIMEDTEXT_TS = time.time()

            if r.status_code == 200 and r.content:
                with open(dst_path, "wb") as f:
                    f.write(r.content)
                return True

            if r.status_code == 429:
                logger.warning(f"{LoggerMsg.SUBS_TIMEDTEXT_429_LOG_MSG}")
                time.sleep(_rand_jitter(12, 6))
                continue

            logger.error(f"{LoggerMsg.SUBS_TIMEDTEXT_HTTP_ERROR_LOG_MSG}")
            time.sleep(_rand_jitter(4))
        return False

    for attempt in range(MAX_RETRIES):
        try:
            subs_lang = get_user_subs_language(user_id)
            auto_mode = get_user_subs_auto_mode(user_id)
            if not subs_lang or subs_lang == "OFF":
                return None
            if not available_langs:
                logger.info(f"{LoggerMsg.SUBS_NO_SUBTITLES_AVAILABLE_LOG_MSG}")
                return None

            found_lang = lang_match(subs_lang, available_langs)
            if not found_lang:
                logger.info(f"{LoggerMsg.SUBS_LANGUAGE_NOT_FOUND_LOG_MSG}")
                return None

            client = _subs_check_cache.get(f"{url}_{user_id}_client", 'tv')  # tv is the only reliable client

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
            
            # Add proxy configuration if needed for this domain
            from HELPERS.proxy_helper import add_proxy_to_ytdl_opts
            info_opts = add_proxy_to_ytdl_opts(info_opts, url)
            
            # Add PO token provider for YouTube domains
            info_opts = add_pot_to_ytdl_opts(info_opts, url)

            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Prefer union view: sometimes only one dict is filled depending on client
            subs_dict = {}
            if not auto_mode:
                subs_dict = info.get('subtitles', {}) or {}
                # merge automatic as fallbacks for listing
                auto_dict = info.get('automatic_captions', {}) or {}
                for k, v in auto_dict.items():
                    subs_dict.setdefault(k, v)
            else:
                subs_dict = info.get('automatic_captions', {}) or {}
                normal_dict = info.get('subtitles', {}) or {}
                for k, v in normal_dict.items():
                    subs_dict.setdefault(k, v)
            tracks = subs_dict.get(found_lang) or []
            if not tracks:
                alt = next((k for k in subs_dict if k.startswith(found_lang)), None)
                tracks = subs_dict.get(alt, []) if alt else []

            if not tracks:
                logger.error(LoggerMsg.SUBS_NO_TRACK_URL_FOUND_LOG_MSG)
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
                logger.warning(LoggerMsg.SUBS_COULD_NOT_DOWNLOAD_LOG_MSG)
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
                logger.info(f"{LoggerMsg.SUBS_VALID_SUBTITLES_LOG_MSG}")
                return dst

            logger.warning(LoggerMsg.SUBS_DOWNLOADED_TRACK_INVALID_LOG_MSG)
            try: os.remove(dst)
            except Exception: pass
            return None

        except yt_dlp.utils.DownloadError as e:
            if "429" in str(e):
                logger.warning(f"{LoggerMsg.SUBS_429_TOO_MANY_REQUESTS_LOG_MSG}")
                if attempt and attempt < MAX_RETRIES - 1:
                    time.sleep(_rand_jitter(25 * (attempt + 1)))
                    continue
                logger.error(LoggerMsg.SUBS_FINAL_ATTEMPT_FAILED_429_LOG_MSG)
                return None
            logger.error(f"{LoggerMsg.SUBS_DOWNLOAD_ERROR_LOG_MSG}")
            return None
        except Exception as e:
            logger.error(f"{LoggerMsg.SUBS_UNEXPECTED_ERROR_LOG_MSG}")
            if attempt and attempt < MAX_RETRIES - 1:
                time.sleep(_rand_jitter(10))
                continue
            return None

    return None


def download_subtitles_only(app, message, url, tags, available_langs, playlist_name=None, video_count=1, video_start_with=1):
    messages = safe_get_messages(message.chat.id)
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
            from HELPERS.safe_messeger import safe_send_message
            error_msg = safe_get_messages(user_id).SUBS_DISABLED_ERROR_MSG
            safe_send_message(user_id, error_msg)
            from HELPERS.logger import log_error_to_channel
            log_error_to_channel(message, error_msg)
            return
        
        # Check if this is YouTube
        if not is_youtube_url(url):
            from HELPERS.safe_messeger import safe_send_message
            error_msg = safe_get_messages(user_id).SUBS_YOUTUBE_ONLY_MSG
            safe_send_message(user_id, error_msg)
            from HELPERS.logger import log_error_to_channel
            log_error_to_channel(message, error_msg)
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
        from HELPERS.safe_messeger import safe_send_message
        status_msg = safe_send_message(user_id, safe_get_messages(user_id).SUBS_DOWNLOADING_MSG, reply_parameters=ReplyParameters(message_id=message.id))
        
        # Download subtitles
        subs_path = download_subtitles_ytdlp(url, user_id, user_dir, available_langs)
        
        if subs_path and os.path.exists(subs_path):
            # Process subtitle file
            subs_path = ensure_utf8_srt(subs_path)
            if subs_path and subs_lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
                subs_path = force_fix_arabic_encoding(subs_path, subs_lang)
            
            if subs_path and os.path.exists(subs_path) and os.path.getsize(subs_path) > 0:
                # Get video information for caption - try cached info first
                try:
                    from DOWN_AND_UP.always_ask_menu import load_ask_info
                    cached_info = load_ask_info(user_id, url)
                    if cached_info:
                        title = cached_info.get('title', 'Video')
                        logger.info(f"✅ [OPTIMIZATION] Using cached title for subtitles caption")
                    else:
                        info = get_video_formats(url, user_id)
                        title = info.get('title', 'Video')
                        logger.info(f"⚠️ [OPTIMIZATION] Had to fetch video info for subtitles caption")
                except:
                    title = "Video"
                
                # Form caption
                caption = safe_get_messages(user_id).SUBS_CAPTION_MSG.format(
                    title=title,
                    lang=subs_lang,
                    type='AUTO/TRANSerated' if auto_mode else 'Manual',
                    tags=f"\n<b>Tags:</b> {' '.join(tags)}" if tags else ""
                )
                
                # Send subtitle file
                sent_msg = app.send_document(
                    chat_id=user_id,
                    document=subs_path,
                    caption=caption,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    parse_mode=enums.ParseMode.HTML
                )
                # We send this message to the log channel
                from HELPERS.logger import get_log_channel
                safe_forward_messages(get_log_channel("video"), user_id, [sent_msg.id])
                send_to_logger(message, safe_get_messages(user_id).SUBS_SENT_MSG)
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
                app.edit_message_text(user_id, status_msg.id, safe_get_messages(user_id).SUBS_ERROR_PROCESSING_MSG)
        else:
            app.edit_message_text(user_id, status_msg.id, safe_get_messages(user_id).SUBS_ERROR_DOWNLOAD_MSG)
            
    except Exception as e:
        logger.error(f"Error downloading subtitles: {e}")
        try:
            app.edit_message_text(user_id, status_msg.id, safe_get_messages(user_id).ERROR_SUBTITLES_NOT_FOUND_MSG.format(error=str(e)))
        except:
            from HELPERS.safe_messeger import safe_send_message
            error_msg = safe_get_messages(user_id).SUBS_ERROR_MSG.format(error=str(e))
            safe_send_message(user_id, error_msg)
            from HELPERS.logger import log_error_to_channel
            log_error_to_channel(message, error_msg)


def get_language_keyboard(page=0, user_id=None, langs_override=None, per_page_rows=8):
    messages = safe_get_messages(user_id)
    """Generate keyboard with language buttons in 3 columns. Supports paging and optional language override."""
    keyboard = []
    LANGS_PER_ROW = 3

    ROWS_PER_PAGE = per_page_rows  # default 8 -> 24 per page


    # We get all languages
    if langs_override is not None:
        # langs_override is list of codes
        all_langs = [(code, {"flag": get_flag(code), "name": code}) for code in langs_override]
    else:
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
                checkmark = safe_get_messages(user_id).SUBS_LANGUAGE_CHECKMARK_MSG if lang_code == current_lang else ""
                button_text = f"{checkmark}{lang_info.get('flag', get_flag(lang_code))} {lang_info.get('name', lang_code)}"
                row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"subs_lang|{lang_code}"
                ))
        keyboard.append(row)

    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).SUBS_PREV_BUTTON_MSG, callback_data=f"subs_page|{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).SUBTITLES_NEXT_BUTTON_MSG, callback_data=f"subs_page|{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # Specialist. Options
    auto_emoji = safe_get_messages(user_id).SUBS_AUTO_EMOJI_MSG if auto_mode else safe_get_messages(user_id).SUBS_AUTO_EMOJI_INACTIVE_MSG
    keyboard.append([
        InlineKeyboardButton(safe_get_messages(user_id).SUBS_OFF_BUTTON_MSG, callback_data="subs_lang|OFF"),
        InlineKeyboardButton(f"{auto_emoji} {safe_get_messages(user_id).SUBS_AUTO_TRANS_BUTTON_MSG}", callback_data=f"subs_auto|toggle|{page}")

    ])
    # Always Ask option
    always_ask_enabled = is_subs_always_ask(user_id) if user_id else False
    always_ask_emoji = safe_get_messages(user_id).SUBS_ALWAYS_ASK_EMOJI_MSG if always_ask_enabled else safe_get_messages(user_id).SUBS_ALWAYS_ASK_EMOJI_INACTIVE_MSG
    keyboard.append([
        InlineKeyboardButton(f"{always_ask_emoji} {safe_get_messages(user_id).SUBS_ALWAYS_ASK_BUTTON_MSG}", callback_data=f"subs_always_ask|toggle|{page}")

    ])
    # Close button
    keyboard.append([
        InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="subs_lang_close|close")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard_always_ask(page=0, user_id=None, langs_override=None, per_page_rows=8, normal_langs=None, auto_langs=None):
    messages = safe_get_messages(user_id)
    """Generate keyboard for Always Ask mode with (auto)/(trans) indicators."""
    keyboard = []
    LANGS_PER_ROW = 3
    ROWS_PER_PAGE = per_page_rows

    # We get all languages with type indicators
    if langs_override is not None:
        all_langs = []
        for code in langs_override:
            flag = get_flag(code, use_second_part=True)  # SUBS: use second part for flags
            name = code
            # Determine if it's auto or trans
            if normal_langs and code in normal_langs:
                suffix = ""
            elif auto_langs and code in auto_langs:
                # Check if it's translated (contains hyphen like 'en-ru')
                if '-' in code and len(code.split('-')) == 2:
                    suffix = " (trans)"
                else:
                    suffix = " (auto)"
            else:
                suffix = ""
            all_langs.append((code, {"flag": flag, "name": f"{name}{suffix}"}))
    else:
        all_langs = list(LANGUAGES.items())

    total_languages = len(all_langs)
    total_pages = math.ceil(total_languages / (LANGS_PER_ROW * ROWS_PER_PAGE))

    # Cut for the current page
    start_idx = page * LANGS_PER_ROW * ROWS_PER_PAGE
    end_idx = start_idx + LANGS_PER_ROW * ROWS_PER_PAGE
    current_page_langs = all_langs[start_idx:end_idx]

    # Form buttons 3 in a row
    for i in range(0, len(current_page_langs), LANGS_PER_ROW):
        row = []
        for j in range(LANGS_PER_ROW):
            if i + j < len(current_page_langs):
                lang_code, lang_info = current_page_langs[i + j]
                button_text = f"{lang_info['flag']} {lang_info['name']}"
                row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"askf|subs_lang|{lang_code}"
                ))
        keyboard.append(row)

    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).SUBS_PREV_BUTTON_MSG, callback_data=f"askf|subs_page|{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(safe_get_messages(user_id).SUBTITLES_NEXT_BUTTON_MSG, callback_data=f"askf|subs_page|{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # Back and Close buttons
    keyboard.append([
        InlineKeyboardButton(safe_get_messages(user_id).SUBS_BACK_BUTTON_MSG, callback_data="askf|subs|back"),
        InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="askf|subs|close")
    ])

    return InlineKeyboardMarkup(keyboard)

######################################################

