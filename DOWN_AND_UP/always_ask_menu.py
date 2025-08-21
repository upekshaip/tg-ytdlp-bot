# --- Callback Processor ---
import os
import hashlib
import re
from datetime import datetime
import json
from pyrogram import filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.decorators import get_main_reply_keyboard
from HELPERS.logger import send_to_logger, logger
from HELPERS.filesystem_hlp import create_directory
from HELPERS.qualifier import get_quality_by_min_side, get_real_height_for_quality
from HELPERS.limitter import check_subs_limits, check_playlist_range_limits, TimeFormatter

from CONFIG.config import Config

from COMMANDS.subtitles_cmd import (
    clear_subs_check_cache, is_subs_enabled, check_subs_availability, 
    get_user_subs_auto_mode, download_subtitles_only, get_user_subs_language, _subs_check_cache,
    LANGUAGES, get_language_keyboard, is_subs_always_ask, save_subs_always_ask,
    get_language_keyboard_always_ask, get_available_subs_languages, get_flag,
    save_user_subs_language, save_user_subs_auto_mode,
)
from COMMANDS.split_sizer import get_user_split_size

from DATABASE.cache_db import (
    get_cached_qualities, get_cached_playlist_count, get_cached_playlist_videos, 
    get_cached_playlist_qualities, save_to_video_cache, get_cached_message_ids
)

from DOWN_AND_UP.yt_dlp_hook import get_video_formats
from COMMANDS.format_cmd import set_session_mkv_override
from DOWN_AND_UP.down_and_audio import down_and_audio
from DOWN_AND_UP.down_and_up import down_and_up

from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.tags import generate_final_tags, extract_url_range_tags
from URL_PARSERS.youtube import is_youtube_url, download_thumbnail
from URL_PARSERS.tiktok import is_tiktok_url
from URL_PARSERS.normalizer import get_clean_playlist_url
from URL_PARSERS.embedder import transform_to_embed_url, is_instagram_url, is_twitter_url, is_reddit_url

# Get app instance for decorators
app = get_app()

# In-memory filters for Always Ask (per user session)
_ASK_FILTERS = {}
_ASK_INFO_CACHE_FILE = "ask_formats.json"
_ASK_SUBS_LANGS_PREFIX = "ask_subs_"

def get_filters(user_id):
    f = _ASK_FILTERS.get(str(user_id))
    if not f:
        # defaults: filters hidden to keep UI simple
        f = {"codec": "avc1", "ext": "mp4", "visible": False, "audio_lang": None, "has_dubs": False, "available_dubs": []}
        _ASK_FILTERS[str(user_id)] = f
    return f

def set_filter(user_id, kind, value):
    f = get_filters(user_id)
    if kind == "codec":
        f["codec"] = value
    elif kind == "ext":
        f["ext"] = value
    elif kind == "audio_lang":
        f["audio_lang"] = value
    elif kind == "toggle":
        f["visible"] = (value == "on")
    _ASK_FILTERS[str(user_id)] = f

def save_filters(user_id, state):
    """Persist current in-memory filters back to the session map."""
    _ASK_FILTERS[str(user_id)] = dict(state)

def _ask_cache_path(user_id):
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    return os.path.join(user_dir, _ASK_INFO_CACHE_FILE)

def _subs_langs_cache_path(user_id, url: str) -> str:
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    h = hashlib.sha1((url or "").encode("utf-8", errors="ignore")).hexdigest()[:16]
    return os.path.join(user_dir, f"{_ASK_SUBS_LANGS_PREFIX}{h}.json")

def save_subs_langs_cache(user_id: int, url: str, normal_langs, auto_langs) -> None:
    try:
        path = _subs_langs_cache_path(user_id, url)
        data = {
            "url": url,
            "normal": list(normal_langs or []),
            "auto": list(auto_langs or []),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

def load_subs_langs_cache(user_id: int, url: str):
    try:
        path = _subs_langs_cache_path(user_id, url)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("normal", []), data.get("auto", [])
    except Exception:
        return [], []
    return [], []

def delete_subs_langs_cache(user_id: int, url: str) -> None:
    try:
        path = _subs_langs_cache_path(user_id, url)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def save_ask_info(user_id, url, info):
    try:
        path = _ask_cache_path(user_id)
        data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[url] = {
            "title": info.get("title"),
            "id": info.get("id"),
            "formats": info.get("formats", [])
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_ask_info(user_id, url):
    try:
        path = _ask_cache_path(user_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(url)
    except Exception:
        return None
    return None

# --- DUBS flag resolver (robust) ---
_DUBS_FLAG_OVERRIDES = {
    'de': '🇩🇪',
    'fr': '🇫🇷',
    'es': '🇪🇸',
    'it': '🇮🇹',
    'en': '🇬🇧',
    'pt': '🇵🇹',
}

def _dub_flag(lang_code: str) -> str:
    try:
        base = (lang_code or '').split('-', 1)[0].lower()
        if base in _DUBS_FLAG_OVERRIDES:
            return _DUBS_FLAG_OVERRIDES[base]
        # fallback to generic resolver by first part
        return get_flag(lang_code, use_second_part=False)
    except Exception:
        return '🌐'

@app.on_callback_query(filters.regex(r"^askf\|"))
def ask_filter_callback(app, callback_query):
    user_id = callback_query.from_user.id
    parts = callback_query.data.split("|")
    if len(parts) >= 3:
        _, kind, value = parts[:3]

        # --- SUBS handlers must run BEFORE generic filter rebuild ---
        if kind == "subs" and value == "open":
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            try:
                # warm up cache and collect languages
                check_subs_availability(url, user_id, return_type=True)
                normal = get_available_subs_languages(url, user_id, auto_only=False)
                auto = get_available_subs_languages(url, user_id, auto_only=True)
                # persist for stable paging
                save_subs_langs_cache(user_id, url, normal, auto)
                langs = sorted(set(normal) | set(auto))
            except Exception:
                # fallback to local cache if network check failed
                normal, auto = load_subs_langs_cache(user_id, url)
                langs = sorted(set(normal) | set(auto))
            if not langs:
                callback_query.answer("No subtitles detected", show_alert=True)
                return
            kb = get_language_keyboard_always_ask(page=0, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer("Choose subtitle language")
            return
        if kind == "subs_page":
            page = int(value)
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            # Prefer persisted cache to avoid list loss on edits
            n_cached, a_cached = load_subs_langs_cache(user_id, url)
            if n_cached or a_cached:
                normal, auto = n_cached, a_cached
            else:
                normal = _subs_check_cache.get(f"{url}_{user_id}_normal_langs") or []
                auto = _subs_check_cache.get(f"{url}_{user_id}_auto_langs") or []
            langs = sorted(set(normal) | set(auto))
            kb = get_language_keyboard_always_ask(page=page, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer(f"Page {page + 1}")
            return
        if kind == "subs" and value in ("back", "close"):
            if value == "back":
                original_message = callback_query.message.reply_to_message
                if original_message:
                    url_text = original_message.text or (original_message.caption or "")
                    import re as _re
                    m = _re.search(r'https?://[^\s\*#]+', url_text)
                    url = m.group(0) if m else url_text
                    ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
                return
            # close
            try:
                app.delete_messages(user_id, callback_query.message.id)
            except Exception:
                app.edit_message_reply_markup(chat_id=user_id, message_id=callback_query.message.id, reply_markup=None)
            callback_query.answer("Subtitle menu closed.")
            return
        if kind == "subs_lang":
            # Persist selected subtitle language as global setting used by embed logic
            try:
                save_user_subs_language(user_id, value)
                # If user picks explicit language from SUBS menu – assume manual, not auto
                save_user_subs_auto_mode(user_id, False)
            except Exception:
                pass
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                # Close subs keyboard and rebuild Always Ask menu with selected lang in summary
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer(f"Subtitle language set: {value}")
            except Exception:
                pass
            return
        # DUBS open: show languages grid with flags
        if kind == "dubs" and value == "open":
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            fstate = get_filters(user_id)
            langs = fstate.get("available_dubs", [])
            if not langs or len(langs) <= 1:
                callback_query.answer("No alternative audio languages", show_alert=True)
                return
            rows, row = [], []
            for i, lang in enumerate(sorted(langs)):
                # Use robust flag lookup for DUBS (strict overrides first)
                flag = _dub_flag(lang)
                label = f"{flag} {lang}" if flag else lang
                row.append(InlineKeyboardButton(label, callback_data=f"askf|audio_lang|{lang}"))
                if (i+1) % 3 == 0:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            rows.append([InlineKeyboardButton("🔙 Back", callback_data="askf|dubs|back"), InlineKeyboardButton("🔚 Close", callback_data="askf|dubs|close")])
            try:
                callback_query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
            except Exception:
                pass
            try:
                callback_query.answer("Choose audio language")
            except Exception:
                pass
            return
        if kind == "audio_lang":
            set_filter(user_id, kind, value)
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer(f"Audio set: {value}")
            except Exception:
                pass
            return
        if kind == "dubs" and value in ("back", "close"):
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            try:
                callback_query.answer("Filters updated")
            except Exception:
                pass
            return
        if kind in ("codec", "ext"):
            set_filter(user_id, kind, value)
            try:
                if kind == "ext":
                    set_session_mkv_override(user_id, value == "mkv")
            except Exception:
                pass
        elif kind == "toggle":
            set_filter(user_id, kind, value)
            # Reset codec/ext to defaults when closing CODEC menu via Back
            if value == "off":
                set_filter(user_id, "codec", "avc1")
                set_filter(user_id, "ext", "mp4")
        # Rebuild the same message in place (fast, using cache)
        original_message = callback_query.message.reply_to_message
        if original_message:
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            # After starting download from menu, we will remove temp subs cache in down_and_up_with_format
            try:
                callback_query.answer("Filters updated")
            except Exception:
                pass
            return
        try:
            callback_query.answer("Filters updated")
        except Exception:
            pass

def build_filter_rows(user_id):
    f = get_filters(user_id)
    codec = f.get("codec", "avc1")
    ext = f.get("ext", "mp4")
    visible = bool(f.get("visible", False))
    audio_lang = f.get("audio_lang")
    has_dubs = bool(f.get("has_dubs"))
    # When filters are hidden – show compact row with CODEC + audio (+ optional DUBS, SUBS)
    if not visible:
        row = [InlineKeyboardButton("📼 CODEC", callback_data="askf|toggle|on"), InlineKeyboardButton("🎧 audio (mp3)", callback_data="askq|mp3")]
        # Show DUBS button only if audio dubs are detected for this video (set elsewhere)
        if has_dubs:
            row.insert(1, InlineKeyboardButton("🗣 DUBS", callback_data="askf|dubs|open"))
        # Show SUBS button if Always Ask is enabled for this user
        try:
            if is_subs_always_ask(user_id):
                row.append(InlineKeyboardButton("💬 SUBS", callback_data="askf|subs|open"))
        except Exception:
            pass
        return [row]
    avc1_btn = ("✅ AVC" if codec == "avc1" else "☑️ AVC")
    av01_btn = ("✅ AV1" if codec == "av01" else "☑️ AV1")
    vp9_btn = ("✅ VP9" if codec == "vp9" else "☑️ VP9")
    mp4_btn = ("✅ MP4" if ext == "mp4" else "☑️ MP4")
    mkv_btn = ("✅ MKV" if ext == "mkv" else "☑️ MKV")
    rows = [
        [InlineKeyboardButton(avc1_btn, callback_data="askf|codec|avc1"), InlineKeyboardButton(av01_btn, callback_data="askf|codec|av01"), InlineKeyboardButton(vp9_btn, callback_data="askf|codec|vp9")],
        [InlineKeyboardButton(mp4_btn, callback_data="askf|ext|mp4"), InlineKeyboardButton(mkv_btn, callback_data="askf|ext|mkv"), InlineKeyboardButton("🎧 audio (mp3)", callback_data="askq|mp3")]
    ]
    act_row = []
    if has_dubs:
        act_row.append(InlineKeyboardButton("🗣 DUBS", callback_data="askf|dubs|open"))
    try:
        if is_subs_always_ask(user_id):
            act_row.append(InlineKeyboardButton("💬 SUBS", callback_data="askf|subs|open"))
    except Exception:
        pass
    if act_row:
        rows.insert(0, act_row)
    return rows

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
            reply_parameters=ReplyParameters(message_id=original_message.id)
        )
        send_to_logger(original_message, f"Quick Embed: {embed_url}")
        app.delete_messages(user_id, callback_query.message.id)
        return
    
    # Handle manual quality selection menu
    if data == "try_manual":
        show_manual_quality_menu(app, callback_query)
        return

    # Handle filter toggles
    if data.startswith("f|") or data.startswith("askf|"):
        parts = callback_query.data.split("|")
        # support both prefixes
        _, kind, value = parts[0], parts[1], parts[2]
        if kind in ("codec", "ext"):
            set_filter(callback_query.from_user.id, kind, value)
            callback_query.answer("Filters updated")
            # Reopen the menu with updated filters
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url = original_message.text or (original_message.caption or "")
            # try to extract url
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url)
            if m:
                url = m.group(0)
            ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "open":
            # Build and show dubs selection menu with flags
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            # Use precomputed list from filters state for speed/stability
            fstate = get_filters(callback_query.from_user.id)
            langs = fstate.get('available_dubs', [])
            # Build buttons 3 per row with flags
            rows = []
            row = []
            for i, lang in enumerate(sorted(langs)):
                # DUBS: use first part for flags (de from de-DE)
                flag = get_flag(lang, use_second_part=False)
                label = f"{flag} {lang}" if flag else lang
                row.append(InlineKeyboardButton(label, callback_data=f"askf|audio_lang|{lang}"))
                if (i+1) % 3 == 0:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            rows.append([InlineKeyboardButton("🔙 Back", callback_data="askf|dubs|back"), InlineKeyboardButton("🔚 Close", callback_data="askf|dubs|close")])
            kb = InlineKeyboardMarkup(rows)
            try:
                # Replace entire keyboard (keeping caption/text) to show dubs
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer("Choose audio language")
            return
        if kind == "subs" and value == "open":
            # Open SUBS language menu (Always Ask)
            logger.info(f"[ASKQ] Opening SUBS menu for user {user_id}")
            original_message = callback_query.message.reply_to_message
            if not original_message:
                logger.error(f"[ASKQ] No original message found for SUBS menu")
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            logger.info(f"[ASKQ] Extracted URL: {url}")
            
            # First, check subtitle availability to populate cache
            try:
                logger.info(f"[ASKQ] Checking subtitle availability for {url}")
                # Check availability and populate cache
                check_subs_availability(url, user_id, return_type=True)
                # Get available languages
                normal = get_available_subs_languages(url, user_id, auto_only=False)
                auto = get_available_subs_languages(url, user_id, auto_only=True)
                langs = sorted(set(normal) | set(auto))
                logger.info(f"[ASKQ] Found languages - normal: {normal}, auto: {auto}, total: {langs}")
            except Exception as e:
                logger.error(f"[ASKQ] Error checking subtitles: {e}")
                normal, auto, langs = [], [], []
            
            if not langs:
                logger.warning(f"[ASKQ] No subtitles found for {url}")
                callback_query.answer("No subtitles detected", show_alert=True)
                return
                
            logger.info(f"[ASKQ] Building keyboard with {len(langs)} languages")
            kb = get_language_keyboard_always_ask(page=0, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
                logger.info(f"[ASKQ] Successfully updated message with SUBS keyboard")
            except Exception as e:
                logger.error(f"[ASKQ] Error updating message: {e}")
                pass
            callback_query.answer("Choose subtitle language")
            return
        if kind == "subs_page":
            # Handle page navigation in Always Ask subtitle menu
            page = int(value)
            original_message = callback_query.message.reply_to_message
            if not original_message:
                callback_query.answer("❌ Error: Original message not found.", show_alert=True)
                return
            url_text = original_message.text or (original_message.caption or "")
            import re as _re
            m = _re.search(r'https?://[^\s\*#]+', url_text)
            url = m.group(0) if m else url_text
            try:
                normal = _subs_check_cache.get(f"{url}_{user_id}_normal_langs") or []
                auto = _subs_check_cache.get(f"{url}_{user_id}_auto_langs") or []
            except Exception:
                normal, auto = [], []
            langs = sorted(set(normal) | set(auto))
            kb = get_language_keyboard_always_ask(page=page, user_id=user_id, langs_override=langs, per_page_rows=8, normal_langs=normal, auto_langs=auto)
            try:
                callback_query.edit_message_reply_markup(reply_markup=kb)
            except Exception:
                pass
            callback_query.answer(f"Page {page + 1}")
            return
        if kind == "subs" and value == "back":
            # Go back to main Always Ask menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "subs" and value == "close":
            # Close subtitle menu
            try:
                app.delete_messages(user_id, callback_query.message.id)
            except Exception:
                app.edit_message_reply_markup(chat_id=user_id, message_id=callback_query.message.id, reply_markup=None)
            callback_query.answer("Subtitle menu closed.")
            return
        if kind == "subs_lang":
            # Handle subtitle language selection in Always Ask
            selected_lang = value
            # Store the selected subtitle language for this video
            fstate = get_filters(user_id)
            fstate['selected_subs_lang'] = selected_lang
            save_filters(user_id, fstate)
            callback_query.answer(f"Subtitle language set: {selected_lang}")
            # Return to main Always Ask menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "close":
            # Close dubs menu without changing audio_lang
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "audio_lang":
            set_filter(callback_query.from_user.id, kind, value)
            callback_query.answer(f"Audio set: {value}")
            # Return to main menu with updated summary
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
            return
        if kind == "dubs" and value == "back":
            # Go back to main menu
            original_message = callback_query.message.reply_to_message
            if original_message:
                url_text = original_message.text or (original_message.caption or "")
                import re as _re
                m = _re.search(r'https?://[^\s\*#]+', url_text)
                url = m.group(0) if m else url_text
                ask_quality_menu(app, original_message, url, [], playlist_start_index=1, cb=callback_query)
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
            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best"
        elif quality == "mp3":
            down_and_audio(app, original_message, url, tags, quality_key="mp3")
            return
        else:
            try:
                quality_str = quality.replace('p', '')
                quality_val = int(quality_str)
                # choose previous rung for lower bound
                if quality_val >= 4320:
                    prev = 2160
                elif quality_val >= 2160:
                    prev = 1440
                elif quality_val >= 1440:
                    prev = 1080
                elif quality_val >= 1080:
                    prev = 720
                elif quality_val >= 720:
                    prev = 480
                elif quality_val >= 480:
                    prev = 360
                elif quality_val >= 360:
                    prev = 240
                elif quality_val >= 240:
                    prev = 144
                else:
                    prev = 0
                format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
            except ValueError:
                format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv+ba/best"
        
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
                            format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                        else:
                            quality_str = used_quality_key.replace('p', '')
                            quality_val = int(quality_str)
                            if quality_val >= 4320:
                                prev = 2160
                            elif quality_val >= 2160:
                                prev = 1440
                            elif quality_val >= 1440:
                                prev = 1080
                            elif quality_val >= 1080:
                                prev = 720
                            elif quality_val >= 720:
                                prev = 480
                            elif quality_val >= 480:
                                prev = 360
                            elif quality_val >= 360:
                                prev = 240
                            elif quality_val >= 240:
                                prev = 144
                            else:
                                prev = 0
                            format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                    except Exception as e:
                        logger.error(f"askq_callback: error forming format: {e}")
                        format_override = "bestvideo+bestaudio/best/bv+ba/best"
                    
                    down_and_up(app, original_message, url, playlist_name, new_count, new_start, tags_text, force_no_title=False, format_override=format_override, quality_key=used_quality_key)
            else:
                # All videos were in the cache
                app.send_message(user_id, f"✅ Sent from cache: {len(cached_videos)}/{len(requested_indices)} files.", reply_parameters=ReplyParameters(message_id=original_message.id))
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
                        format_override = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                    else:
                        quality_str = data.replace('p', '')
                        quality_val = int(quality_str)
                        if quality_val >= 4320:
                            prev = 2160
                        elif quality_val >= 2160:
                            prev = 1440
                        elif quality_val >= 1440:
                            prev = 1080
                        elif quality_val >= 1080:
                            prev = 720
                        elif quality_val >= 720:
                            prev = 480
                        elif quality_val >= 480:
                            prev = 360
                        elif quality_val >= 360:
                            prev = 240
                        elif quality_val >= 240:
                            prev = 144
                        else:
                            prev = 0
                        format_override = f"bv*[vcodec*=avc1][height<={quality_val}][height>{prev}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<={quality_val}]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best/bv+ba/best"
                except ValueError:
                    format_override = "bestvideo+bestaudio/best/bv+ba/best"
                
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
                app.send_message(user_id, "✅ Video successfully sent from cache.", reply_parameters=ReplyParameters(message_id=original_message.id))
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
                app.send_message(user_id, "⚠️ Failed to get video from cache, starting a new download...", reply_parameters=ReplyParameters(message_id=original_message.id))
                askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs)
            return
    askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs)

###########################

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
    
    # Обновление текущего меню; при ошибке MESSAGE_ID_INVALID отправляем новое сообщение
    if callback_query and getattr(callback_query, 'message', None):
        try:
            if callback_query.message.photo:
                callback_query.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            else:
                callback_query.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
            callback_query.answer("Меню выбора качества открыто.")
            return
        except Exception as ee:
            # Если не получилось отредактировать (например, MESSAGE_ID_INVALID) — шлём новое сообщение
            if 'MESSAGE_ID_INVALID' not in str(ee):
                logger.warning(f"Manual menu edit failed, fallback to new message: {ee}")
    # Fallback: отправляем новое сообщение, привязанное к исходному
    try:
        chat_id = callback_query.message.chat.id if callback_query and getattr(callback_query, 'message', None) else user_id
        ref_id = original_message.id if original_message else None
        app.send_message(chat_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard,
                         reply_parameters=ReplyParameters(message_id=ref_id))
        if callback_query:
            callback_query.answer("Меню выбора качества открыто.")
    except Exception as e2:
        logger.error(f"Error showing manual quality menu (fallback): {e2}")
        if callback_query:
            callback_query.answer("❌ Не удалось открыть меню выбора качества.", show_alert=True)

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
def ask_quality_menu(app, message, url, tags, playlist_start_index=1, cb=None):
    user_id = message.chat.id
    proc_msg = None
    found_type = None
    # Clean the cache of subtitles only on initial open (when no callback provided).
    # On filter toggles (when cb is not None), we KEEP the cache to avoid re-fetching subtitles.
    if cb is None:
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
        proc_msg = app.send_message(user_id, processing_text, reply_parameters=ReplyParameters(message_id=message.id), reply_markup=get_main_reply_keyboard())
        original_text = message.text or message.caption or ""
        is_playlist = is_playlist_with_range(original_text)
        playlist_range = None
        if is_playlist:
            _, video_start_with, video_end_with, _, _, _, _ = extract_url_range_tags(original_text)
            playlist_range = (video_start_with, video_end_with)
            cached_qualities = get_cached_playlist_qualities(get_clean_playlist_url(url))
        else:
            cached_qualities = get_cached_qualities(url)
        # Try load cached info first to make UI instant
        info = load_ask_info(user_id, url)
        if not info:
            info = get_video_formats(url, user_id, playlist_start_index)
            # Save minimal info to cache
            try:
                save_ask_info(user_id, url, info)
            except Exception:
                pass
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
        # --- Detect available audio dubs (languages) once per menu open ---
        filters_state = get_filters(user_id)
        sel_codec = filters_state.get("codec", "avc1")
        sel_ext = filters_state.get("ext", "mp4")
        # Build list of available audio languages from formats
        available_dubs = []
        lang_seen = set()
        for f in info.get('formats', []):
            if (f.get('vcodec') == 'none' and f.get('acodec') and f.get('language')):
                lang = f.get('language')
                if lang and lang not in lang_seen:
                    lang_seen.add(lang)
                    available_dubs.append(lang)
        # Save dubs availability per-user (show only if 2+ languages exist)
        fstate = get_filters(user_id)
        has_dubs = len(available_dubs) > 1
        fstate["has_dubs"] = has_dubs
        fstate["available_dubs"] = sorted(available_dubs)
        if not has_dubs:
            # If only one or zero languages, reset audio selection
            fstate["audio_lang"] = None
        _ASK_FILTERS[str(user_id)] = fstate
        # If user selected MKV container, reflect this to the download session preference
        try:
            set_session_mkv_override(user_id, sel_ext == "mkv")
        except Exception:
            pass
        # --- Table with qualities and sizes ---
        table_block = ''
        found_quality_keys = set()
        if ("youtube.com" in url or "youtu.be" in url):
            quality_map = {}
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                    vcodec = f.get('vcodec') or ''
                    ext = f.get('ext') or ''
                    # Filter by codec
                    if sel_codec == 'avc1' and 'avc1' not in vcodec:
                        continue
                    if sel_codec == 'av01' and not vcodec.startswith('av01'):
                        continue
                    if sel_codec == 'vp9' and 'vp9' not in vcodec:
                        continue
                    # Filter by extension: mp4 exact; mkv acts as "not mp4"
                    if sel_ext == 'mp4' and ext != 'mp4':
                        continue
                    if sel_ext == 'mkv' and ext == 'mp4':
                        continue
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
                # Audio language marker for rows (keep UI light; summary shows selection)
                if subs_enabled:
                    if sel_ext == 'mkv':
                        # Для MKV при включённых субтитрах показываем без ограничений
                        subs_available = "💬"
                    elif is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
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
                # Show selected audio language if any
                sel_audio_lang = get_filters(user_id).get("audio_lang")
                audio_mark = f" 🗣{sel_audio_lang}" if sel_audio_lang else ""
                table_lines.append(f"{emoji}{q}{subs_available}{audio_mark}:  {size_str}{dim_str}{scissors}{postfix}")
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
        # Audio/subs selection summary line
        fstate = get_filters(user_id)
        sel_audio_lang = fstate.get("audio_lang")
        subs_enabled = is_subs_enabled(user_id)
        subs_lang = get_user_subs_language(user_id) if subs_enabled else None
        summary_parts = []
        if sel_audio_lang:
            summary_parts.append(f"🗣 {sel_audio_lang}")
        # Always show chosen subtitle language if subs are enabled
        if subs_enabled and subs_lang:
            summary_parts.append(f"💬 {subs_lang}")
        if summary_parts:
            cap += "<blockquote>" + " | ".join(summary_parts) + "</blockquote>\n"
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
            found_type = check_subs_availability(url, user_id, return_type=True)
            # Check if we're in Always Ask mode (user will choose language manually)
            is_always_ask_mode = is_subs_always_ask(user_id)
            
            if is_always_ask_mode:
                # In Always Ask menu, always show subtitles as available if found, regardless of auto_mode
                # User will choose language and type manually
                need_subs = found_type is not None  # True if any subtitles found (auto or normal)
            else:
                # In manual mode, respect user's auto_mode setting
                need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            
            logger.info(f"Always Ask menu: subs_enabled={subs_enabled}, auto_mode={auto_mode}, found_type={found_type}, is_always_ask={is_always_ask_mode}, need_subs={need_subs}")
            if need_subs:
                subs_hint = "\n💬 — Subtitles are available"
                show_repost_hint = False  # 🚀 we don't show if subs really exist and are needed
            else:
                subs_warn = "\n⚠️ Subs not found & won't embed"

        repost_line = "\n🚀 — Instant repost from cache" if show_repost_hint else ""
        # Add DUBS hint if available
        dubs_hint = "\n🗣 — Choose audio language" if get_filters(user_id).get("has_dubs") else ""
        hint = "<pre language=\"info\">📼 — Сhange video ext/codec\n📹 — Choose download quality" + repost_line + subs_hint + subs_warn + dubs_hint + "</pre>"
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
                if subs_enabled:
                    if sel_ext == 'mkv':
                        subs_available = "💬"
                    elif is_youtube_url(url) and w is not None and h is not None and min(int(w), int(h)) <= Config.MAX_SUB_QUALITY:
                        # Check if we're in Always Ask mode
                        is_always_ask_mode = is_subs_always_ask(user_id)
                        
                        if is_always_ask_mode:
                            # In Always Ask menu, show 💬 if any subtitles found, regardless of auto_mode
                            if found_type is not None:  # Any subtitles found (auto or normal)
                                temp_info = {
                                    'duration': info.get('duration'),
                                    'filesize': filesize,
                                    'filesize_approx': filesize
                                }
                                if check_subs_limits(temp_info, quality_key):
                                    subs_available = "💬"
                        else:
                            # In manual mode, respect user's auto_mode setting
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
                    # Check if we're in Always Ask mode
                    is_always_ask_mode = is_subs_always_ask(user_id)
                    
                    if is_always_ask_mode:
                        # In Always Ask menu, show 💬 if any subtitles found, regardless of auto_mode
                        need_subs = (subs_enabled and found_type is not None)  # True if any subtitles found
                    else:
                        # In manual mode, respect user's auto_mode setting
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
        # Add filter rows first
        keyboard_rows.extend(build_filter_rows(user_id))
        
        # Add Quick Embed button for supported services at the top (but not for ranges)
        if (is_instagram_url(url) or is_twitter_url(url) or is_reddit_url(url)) and not is_playlist_with_range(original_text):
            keyboard_rows.append([InlineKeyboardButton("🚀 Quick Embed", callback_data="askq|quick_embed")])
        for i in range(0, len(buttons), 3):
            keyboard_rows.append(buttons[i:i+3])
        # Insert DUBS button into filter row is handled in build_filter_rows
        
        # --- button subtitles only ---
        # Show the button only if subtitles are turned on and it is youtube
        subs_enabled = is_subs_enabled(user_id)
        if subs_enabled and is_youtube_url(url):
            # Check if we're in Always Ask mode
            is_always_ask_mode = is_subs_always_ask(user_id)
            
            if is_always_ask_mode:
                # In Always Ask menu, show button if any subtitles found, regardless of auto_mode
                need_subs = found_type is not None  # True if any subtitles found (auto or normal)
            else:
                # In manual mode, respect user's auto_mode setting
                need_subs = (auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")
            
            if need_subs:
                keyboard_rows.append([InlineKeyboardButton("💬 Subtitles Only", callback_data="askq|subs_only")])
        
        # Нижний ряд: если фильтры раскрыты – показываем Back + Close, иначе только Close
        if bool(filters_state.get('visible', False)):
            keyboard_rows.append([InlineKeyboardButton("🔙 Back", callback_data="askf|toggle|off"), InlineKeyboardButton("🔚 Close", callback_data="askq|close")])
        else:
            keyboard_rows.append([InlineKeyboardButton("🔚 Close", callback_data="askq|close")])
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        # cap already contains a hint and a table
        # Replace current menu in-place if possible
        if cb is not None and getattr(cb, 'message', None):
                # Edit caption or text in place
                try:
                    if cb.message.photo:
                        cb.edit_message_caption(caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                    else:
                        cb.edit_message_text(text=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
                except Exception:
                    pass
                # Remove processing message quietly
                if proc_msg:
                    try:
                        app.delete_messages(user_id, proc_msg.id)
                    except Exception:
                        pass
                proc_msg = None
        else:
            # Fallback: send new message
            if proc_msg:
                try:
                    app.delete_messages(user_id, proc_msg.id)
                except Exception:
                    pass
                proc_msg = None
            if thumb_path and os.path.exists(thumb_path):
                app.send_photo(user_id, thumb_path, caption=cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_parameters=ReplyParameters(message_id=message.id))
            else:
                app.send_message(user_id, cap, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard, reply_parameters=ReplyParameters(message_id=message.id))
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
            app.send_message(user_id, flood_msg, reply_parameters=ReplyParameters(message_id=message.id))
        return
    except Exception as e:
        error_text = f"❌ Error retrieving video information:\n{e}\n> Try the /clean command and try again. If the error persists, YouTube requires authorization. Update cookies.txt via /download_cookie or /cookies_from_browser and try again."
        try:
            if proc_msg:
                result = app.edit_message_text(chat_id=user_id, message_id=proc_msg.id, text=error_text)
                if result is None:
                    app.send_message(user_id, error_text, reply_parameters=ReplyParameters(message_id=message.id))
            else:
                app.send_message(user_id, error_text, reply_parameters=ReplyParameters(message_id=message.id))
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")
            app.send_message(user_id, error_text, reply_parameters=ReplyParameters(message_id=message.id))
        send_to_logger(message, f"Always Ask menu error for {url}: {e}")
        return

def askq_callback_logic(app, callback_query, data, original_message, url, tags_text, available_langs):
    user_id = callback_query.from_user.id
    tags = tags_text.split() if tags_text else []
    # Read current filters to build correct format strings and container override
    try:
        filters_state = get_filters(user_id)
    except Exception:
        filters_state = {"codec": "avc1", "ext": "mp4"}
    sel_codec = filters_state.get("codec", "avc1")
    sel_ext = filters_state.get("ext", "mp4")
    sel_audio_lang = filters_state.get("audio_lang")
    try:
        set_session_mkv_override(user_id, sel_ext == "mkv")
    except Exception:
        pass
    if data == "mp3":
        try:
            callback_query.answer("🎧 Downloading audio...")
        except Exception:
            pass
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        video_count = video_end_with - video_start_with + 1
        down_and_audio(app, original_message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    if data == "subs_only":
        try:
            callback_query.answer("💬 Downloading subtitles only...")
        except Exception:
            pass
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        video_count = video_end_with - video_start_with + 1
        download_subtitles_only(app, original_message, url, tags, available_langs, playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    # Logic for forming the format with the real height
    if data == "best":
        try:
            callback_query.answer("📥 Downloading best quality...")
        except Exception:
            pass
        audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
        fmt = f"bv*[vcodec*={sel_codec}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba"
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
                # choose previous rung for lower bound
                if quality_val >= 4320:
                    prev = 2160
                elif quality_val >= 2160:
                    prev = 1440
                elif quality_val >= 1440:
                    prev = 1080
                elif quality_val >= 1080:
                    prev = 720
                elif quality_val >= 720:
                    prev = 480
                elif quality_val >= 480:
                    prev = 360
                elif quality_val >= 360:
                    prev = 240
                elif quality_val >= 240:
                    prev = 144
                else:
                    prev = 0
                audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                fmt = f"bv*[vcodec*={sel_codec}][height<={quality_val}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={quality_val}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
            else:
                # Determine the quality by the smaller side
                min_side_quality = get_quality_by_min_side(max_width, max_height)
                
                # If the selected quality does not match the smaller side, use the standard logic
                if data != min_side_quality:
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    if quality_val >= 4320:
                        prev = 2160
                    elif quality_val >= 2160:
                        prev = 1440
                    elif quality_val >= 1440:
                        prev = 1080
                    elif quality_val >= 1080:
                        prev = 720
                    elif quality_val >= 720:
                        prev = 480
                    elif quality_val >= 480:
                        prev = 360
                    elif quality_val >= 360:
                        prev = 240
                    elif quality_val >= 240:
                        prev = 144
                    else:
                        prev = 0
                    audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                    fmt = f"bv*[vcodec*={sel_codec}][height<={quality_val}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={quality_val}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
                else:
                    # Use the real height to form the format
                    real_height = get_real_height_for_quality(data, max_width, max_height)
                    quality_str = data.replace('p', '')
                    quality_val = int(quality_str)
                    if quality_val >= 4320:
                        prev = 2160
                    elif quality_val >= 2160:
                        prev = 1440
                    elif quality_val >= 1440:
                        prev = 1080
                    elif quality_val >= 1080:
                        prev = 720
                    elif quality_val >= 720:
                        prev = 480
                    elif quality_val >= 480:
                        prev = 360
                    elif quality_val >= 360:
                        prev = 240
                    elif quality_val >= 240:
                        prev = 144
                    else:
                        prev = 0
                    audio_filter = f"[language^={sel_audio_lang}]" if sel_audio_lang else ""
                    fmt = f"bv*[vcodec*={sel_codec}][height<={real_height}][height>{prev}]+ba{audio_filter}/bv*[vcodec*={sel_codec}][height<={real_height}]+ba{audio_filter}/bv*[vcodec*={sel_codec}]+ba/bv+ba/best"
            
            quality_key = data
            try:
                callback_query.answer(f"📥 Downloading {data}...")
            except Exception:
                pass
        except ValueError:
            callback_query.answer("Unknown quality.")
            return
    
    down_and_up_with_format(app, original_message, url, fmt, tags_text, quality_key=quality_key)

# --- an auxiliary function for downloading with the format ---
# @reply_with_keyboard
def down_and_up_with_format(app, message, url, fmt, tags_text, quality_key=None):

    # We extract the range and other parameters from the original user message
    full_string = message.text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)

    # This mistake should have already been caught earlier, but for safety
    if tag_error:
        wrong, example = tag_error
        app.send_message(message.chat.id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_parameters=ReplyParameters(message_id=message.id))
        return

    video_count = video_end_with - video_start_with + 1
    
    # Check if there is a link to Tiktok
    is_tiktok = is_tiktok_url(url)

    # We call the main function of loading with the correct parameters of the playlist
    down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=is_tiktok, format_override=fmt, quality_key=quality_key)
    # Cleanup temp subs languages cache after we kicked off download
    try:
        delete_subs_langs_cache(message.chat.id, url)
    except Exception:
        pass
