# Version 4.0.0 # split monolith code into multiple modules
###########################################################
#        GLOBAL IMPORTS
###########################################################

# ГЛОБАЛЬНЫЙ ПАТЧ ДЛЯ ПРЕДОТВРАЩЕНИЯ ОШИБКИ 'name messages is not defined'
try:
    from PATCH.GLOBAL_MESSAGES_PATCH import apply_global_messages_patch
    apply_global_messages_patch()
except Exception as e:
    print(f"⚠️  Global messages patch failed: {e}")
    # Минимальная защита уже встроена в safe_get_messages функции

# ПАТЧ NONE ОТКЛЮЧЕН - ОШИБКА УЖЕ ИСПРАВЛЕНА В КОДЕ
# try:
#     from PATCH.FIX_NONE_COMPARISONS_PATCH import apply_patch
#     apply_patch()
# except Exception as e:
#     print(f"⚠️  None comparisons patch failed: {e}")

# DEBUG ПАТЧИ ОТКЛЮЧЕНЫ - ОШИБКА NONE ИСПРАВЛЕНА
# try:
#     from PATCH.DEBUG_NONE_COMPARISON import apply_debug_none_comparison
#     apply_debug_none_comparison()
# except Exception as e:
#     print(f"⚠️  Debug None comparison failed: {e}")
import glob
try:
    from sdnotify import SystemdNotifier  # optional, used for watchdog
except Exception:
    SystemdNotifier = None
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
import signal
import atexit
from datetime import datetime
from PIL import Image
from types import SimpleNamespace
from typing import Tuple
from urllib.parse import urlparse, parse_qs, urlunparse, unquote, urlencode
import traceback
# removed pyrebase (migrated to firebase_admin)
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
    ReplyKeyboardMarkup
)
from yt_dlp import YoutubeDL
import yt_dlp

# Config is now imported from CONFIG.config

import chardet
###########################################################
#        MODULE IMPORTS
###########################################################
# CONFIG
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
# from test_config import Config

# HELPERS (только те, что не содержат обработчики)
from HELPERS.app_instance import set_app
from HELPERS.download_status import *
from HELPERS.filesystem_hlp import *
from HELPERS.limitter import *
from HELPERS.limitter import ensure_group_admin
from HELPERS.logger import *
from HELPERS.porn import *
from HELPERS.qualifier import *
from HELPERS.safe_messeger import *
from HELPERS.guard import guarded
from CONFIG.limits import LimitsConfig
from HELPERS.http_client import close_all_sessions

###########################################################
#        APP INITIALIZATION
###########################################################
# Pyrogram App Initialization
app = Client(
    "magic",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Set global app instance BEFORE importing handlers
set_app(app)

# DATABASE (без обработчиков)
from DATABASE.cache_db import *
from DATABASE.download_firebase import *
from DATABASE.firebase_init import *

# URL_PARSERS (без обработчиков)
from URL_PARSERS.embedder import *
from URL_PARSERS.nocookie import *
from URL_PARSERS.normalizer import *
from URL_PARSERS.tags import *
from URL_PARSERS.tiktok import *
from URL_PARSERS.url_extractor import *
from URL_PARSERS.video_extractor import *
from URL_PARSERS.youtube import *

# DOWN_AND_UP (без обработчиков)
from DOWN_AND_UP.down_and_audio import *
from DOWN_AND_UP.down_and_up import *
from DOWN_AND_UP.ffmpeg import *
from DOWN_AND_UP.sender import *
from DOWN_AND_UP.yt_dlp_hook import *

# HELPERS (с обработчиками - импортируем после установки app)
from HELPERS.caption import *

# COMMANDS (импортируем после установки app)
from COMMANDS.admin_cmd import *
from COMMANDS.clean_cmd import *
from COMMANDS.cookies_cmd import *
from COMMANDS.format_cmd import *
from COMMANDS.link_cmd import *
from COMMANDS.mediainfo_cmd import *
from COMMANDS.other_handlers import *
from COMMANDS.proxy_cmd import *
from COMMANDS.settings_cmd import *
from COMMANDS.split_sizer import *
from COMMANDS.subtitles_cmd import *
from COMMANDS.tag_cmd import *
# Register handlers via their own modules' decorators only (avoid global catch-all)
from COMMANDS.proxy_cmd import proxy_command
from COMMANDS.cookies_cmd import download_cookie

# DOWN_AND_UP (с обработчиками - импортируем после установки app)
from DOWN_AND_UP.always_ask_menu import *

# Инициализируем глобальную переменную messages
messages = safe_get_messages(None)

print(messages.MAGIC_ALL_MODULES_LOADED_MSG)

###########################################################
#        BOT KEYBOARD
###########################################################
# Import decorators from HELPERS
from HELPERS.decorators import reply_with_keyboard, get_main_reply_keyboard, send_reply_keyboard_always

###########################################################
#        GROUP HANDLERS FOR ALLOWED GROUPS
###########################################################
from COMMANDS.image_cmd import image_command
from COMMANDS.mediainfo_cmd import mediainfo_command
from COMMANDS.nsfw_cmd import nsfw_command
from COMMANDS.settings_cmd import settings_command
from COMMANDS.format_cmd import set_format
from COMMANDS.split_sizer import split_command
from COMMANDS.other_handlers import link_command_handler
from COMMANDS.other_handlers import audio_command_handler, playlist_command
from COMMANDS.tag_cmd import tags_command
from URL_PARSERS.url_extractor import url_distractor
from COMMANDS.subtitles_cmd import subs_command
from COMMANDS import args_cmd
from COMMANDS.list_cmd import list_command
from COMMANDS.cookies_cmd import cookies_from_browser

async def _wrap_group(fn):
    async def _inner(app, message):
        if not await ensure_group_admin(app, message):
            return
        return await fn(app, message)
    return _inner

# Register group equivalents where applicable
_allowed_groups = tuple(getattr(Config, 'ALLOWED_GROUP', []))

async def _is_allowed_group(message):
    messages = safe_get_messages(None)
    try:
        gid = int(getattr(message.chat, 'id', 0))
        allowed = gid in _allowed_groups
        try:
            # Explicit log once per check
            from HELPERS.logger import logger
            logger.info(messages.MAGIC_ALLOWED_GROUP_CHECK_LOG_MSG.format(chat_id=gid, allowed=allowed, list=list(_allowed_groups)))
        except Exception:
            pass
        return allowed
    except Exception:
        return False

if _allowed_groups:
    # Group command handlers
    @guarded(timeout=LimitsConfig.MAX_IMG_TOTAL_WAIT_TIME)  # Use proper image timeout from limits.py
    async def _group_img_handler(a, m):
        if _is_allowed_group(m):
            return await image_command(a, m)
        return None
    
    @guarded(timeout=LimitsConfig.MAX_IMG_RANGE_WAIT_TIME)  # Use proper media timeout from limits.py
    async def _group_mediainfo_handler(a, m):
        if _is_allowed_group(m):
            return await mediainfo_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for nsfw command
    async def _group_nsfw_handler(a, m):
        if _is_allowed_group(m):
            return await nsfw_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for proxy command
    async def _group_proxy_handler(a, m):
        if _is_allowed_group(m):
            return await proxy_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for settings command
    async def _group_settings_handler(a, m):
        if _is_allowed_group(m):
            return await settings_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for format command
    async def _group_format_handler(a, m):
        if _is_allowed_group(m):
            return await set_format(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for split command
    async def _group_split_handler(a, m):
        if _is_allowed_group(m):
            return await split_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for link command
    async def _group_link_handler(a, m):
        if _is_allowed_group(m):
            return await link_command_handler(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for tags command
    async def _group_tags_handler(a, m):
        if _is_allowed_group(m):
            return await tags_command(a, m)
        return None
    
    @guarded(timeout=LimitsConfig.DOWNLOAD_TIMEOUT)  # Use proper download timeout from limits.py
    async def _group_audio_handler(a, m):
        if _is_allowed_group(m):
            return await audio_command_handler(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for playlist command
    async def _group_playlist_handler(a, m):
        if _is_allowed_group(m):
            return await playlist_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for subs command
    async def _group_subs_handler(a, m):
        if _is_allowed_group(m):
            return await subs_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for args command
    async def _group_args_handler(a, m):
        if _is_allowed_group(m):
            return await args_cmd.args_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for list command
    async def _group_list_handler(a, m):
        if _is_allowed_group(m):
            return await list_command(a, m)
        return None
    
    @guarded(timeout=60)  # 1 minute timeout for cookies command
    async def _group_cookies_handler(a, m):
        if _is_allowed_group(m):
            return await cookies_from_browser(a, m)
        return None
    
    app.on_message(filters.group & filters.command("img"))(guarded(timeout=60)(_wrap_group(_group_img_handler)))
    app.on_message(filters.group & filters.command("mediainfo"))(guarded(timeout=60)(_wrap_group(_group_mediainfo_handler)))
    app.on_message(filters.group & filters.command("nsfw"))(guarded(timeout=60)(_wrap_group(_group_nsfw_handler)))
    app.on_message(filters.group & filters.command("proxy"))(guarded(timeout=60)(_wrap_group(_group_proxy_handler)))
    app.on_message(filters.group & filters.command("settings"))(guarded(timeout=60)(_wrap_group(_group_settings_handler)))
    app.on_message(filters.group & filters.command("format"))(guarded(timeout=60)(_wrap_group(_group_format_handler)))
    app.on_message(filters.group & filters.command("split"))(guarded(timeout=60)(_wrap_group(_group_split_handler)))
    app.on_message(filters.group & filters.command("link"))(guarded(timeout=60)(_wrap_group(_group_link_handler)))
    app.on_message(filters.group & filters.command("tags"))(guarded(timeout=60)(_wrap_group(_group_tags_handler)))
    app.on_message(filters.group & filters.command("audio"))(guarded(timeout=60)(_wrap_group(_group_audio_handler)))
    app.on_message(filters.group & filters.command("playlist"))(guarded(timeout=60)(_wrap_group(_group_playlist_handler)))
    app.on_message(filters.group & filters.command("subs"))(guarded(timeout=60)(_wrap_group(_group_subs_handler)))
    app.on_message(filters.group & filters.command("args"))(guarded(timeout=60)(_wrap_group(_group_args_handler)))
    app.on_message(filters.group & filters.command("list"))(guarded(timeout=60)(_wrap_group(_group_list_handler)))
    app.on_message(filters.group & filters.command("cookies_from_browser"))(guarded(timeout=60)(_wrap_group(_group_cookies_handler)))

    # Text/url handler in allowed groups (topic-aware)
    # Text/url handler in allowed groups (topic-aware) including mentions
@guarded(timeout=LimitsConfig.DOWNLOAD_TIMEOUT)  # Use proper download timeout from limits.py
async def _guarded_text(a, m):
    # Update health monitor activity
    try:
        from HELPERS.health_monitor import health_monitor
        health_monitor.update_activity()
    except Exception:
        pass
    
    if _is_allowed_group(m):
        return await url_distractor(a, m)
    # If not allowed, do nothing (deny service silently)
    return None

app.on_message(filters.group & filters.text)(guarded(timeout=60)(_wrap_group(_guarded_text)))

# Text/url/emoji handler for private chats
@app.on_message(filters.private & filters.text)
@guarded(timeout=LimitsConfig.DOWNLOAD_TIMEOUT)  # Use proper download timeout from limits.py
async def _private_text_handler(app, message):
    from HELPERS.logger import logger
    logger.info(f"🎯 Private text handler: {message.text}")
    
    # Update health monitor activity
    try:
        from HELPERS.health_monitor import health_monitor
        health_monitor.update_activity()
    except Exception:
        pass
    
    # Check if it's a command first
    text = message.text.strip()
    if text.startswith('/'):
        # It's a command, let other handlers process it
        logger.info(f"🎯 Command detected: {text}")
        return
    
    # Process as URL
    await url_distractor(app, message)

    # Map basic commands to url_distractor to mimic private behavior
    @guarded(timeout=60)  # 1 minute timeout for basic commands
    async def _group_basic_handler(a, m, cmd):
        if _is_allowed_group(m):
            return await url_distractor(a, m)
        return None
    
    for _cmd in ("start", "help", "keyboard", "clean", "search", "usage", "check_cookie", "save_as_cookie"):
        app.on_message(filters.group & filters.command(_cmd))(guarded(timeout=60)(_wrap_group(_group_basic_handler)))

###########################################################
#        /vid command (private and groups)
###########################################################
@guarded(timeout=60)  # 15 minutes timeout for heavy operations
async def _vid_handler(app, message):
    messages = safe_get_messages(message.chat.id)
    # Transform "/vid [url]" into plain URL text for url_distractor
    try:
        txt = (message.text or "").strip()
        parts = txt.split()
        url = ""
        # Support syntax: /vid 1-10 https://...  -> append *1*10 to URL
        if len(parts) >= 3 and re.match(r"^\d+-\d*$", parts[1]):
            rng = parts[1]
            url = " ".join(parts[2:])
            a, b = rng.split("-", 1)
            b = b if b != "" else None
            if url:
                url = f"{url}*{a}*{b}" if b is not None else f"{url}*{a}*"
        else:
            # Fallback: /vid URL
            url = parts[1] if len(parts) > 1 else ""
        # Remove @bot mention if present in command
        if url.startswith("@"):  # case of "/vid @bot url"
            url = " ".join(url.split()[1:])
        if url:
            # Reuse original message for thread/reply context
            message.text = url
            return await url_distractor(app, message)
        else:
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(messages.URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG, callback_data="vid_help|close")]])
            help_text = (
                messages.MAGIC_VID_HELP_TITLE_MSG +
                messages.MAGIC_VID_HELP_USAGE_MSG +
                messages.MAGIC_VID_HELP_EXAMPLES_MSG +
                messages.MAGIC_VID_HELP_EXAMPLE_1_MSG +
                messages.MAGIC_VID_HELP_EXAMPLE_2_MSG +
                messages.MAGIC_VID_HELP_EXAMPLE_3_MSG +
                messages.MAGIC_VID_HELP_ALSO_SEE_MSG
            )
            await safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)
    except Exception:
        from HELPERS.safe_messeger import safe_send_message
        from pyrogram import enums
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(messages.URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG, callback_data="vid_help|close")]])
        help_text = (
            messages.MAGIC_VID_HELP_TITLE_MSG +
            messages.MAGIC_VID_HELP_USAGE_MSG +
            messages.MAGIC_VID_HELP_EXAMPLES_MSG +
            messages.MAGIC_VID_HELP_EXAMPLE_1_MSG +
            messages.MAGIC_VID_HELP_EXAMPLE_2_MSG +
            messages.MAGIC_VID_HELP_EXAMPLE_3_MSG +
            messages.MAGIC_VID_HELP_ALSO_SEE_MSG
        )
        await safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)

# Register /vid in private and allowed groups
app.on_message(filters.command("vid") & filters.private)(guarded(timeout=60)(_vid_handler))
if _allowed_groups:
    @guarded(timeout=60)  # 15 minutes timeout for vid command
    async def _group_vid_handler(a, m):
        if _is_allowed_group(m):
            return await _vid_handler(a, m)
        return None
    
    app.on_message(filters.group & filters.command("vid"))(guarded(timeout=60)(_wrap_group(_group_vid_handler)))

# Register private command handlers
@app.on_message(filters.command("start") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for start command
async def _private_start_handler(app, message):
    from HELPERS.logger import logger
    logger.info(f"🎯 /start command received: {message.text}")
    await url_distractor(app, message)

@app.on_message(filters.command("help") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for help command
async def _private_help_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("settings") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for settings command
async def _private_settings_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("audio") & filters.private)
@guarded(timeout=60)  # 15 minutes timeout for audio command
async def _private_audio_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("format") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for format command
async def _private_format_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("split") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for split command
async def _private_split_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("subs") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for subs command
async def _private_subs_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("proxy") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for proxy command
async def _private_proxy_handler(app, message):
    await url_distractor(app, message)

# Health command for admins (must be registered early)
@app.on_message(filters.command("health") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for health command
async def _private_health_handler(app, message):
    from COMMANDS.health_cmd import health_command
    await health_command(app, message)

@app.on_message(filters.command("tags") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for tags command
async def _private_tags_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("nsfw") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for nsfw command
async def _private_nsfw_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("keyboard") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for keyboard command
async def _private_keyboard_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("clean") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for clean command
async def _private_clean_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("img") & filters.private)
@guarded(timeout=60)  # 30 minutes timeout for img command (heavy operation)
async def _private_img_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("search") & filters.private)
@guarded(timeout=60)  # 5 minutes timeout for search command
async def _private_search_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("list") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for list command
async def _private_list_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("check_cookie") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for check_cookie command
async def _private_check_cookie_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("save_as_cookie") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for save_as_cookie command
async def _private_save_as_cookie_handler(app, message):
    await url_distractor(app, message)

@app.on_message(filters.command("usage") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for usage command
async def _private_usage_handler(app, message):
    await url_distractor(app, message)

# Admin commands
@app.on_message(filters.command("reload_cache") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for reload_cache command
async def _private_reload_cache_handler(app, message):
    from COMMANDS.admin_cmd import reload_firebase_cache_command
    await reload_firebase_cache_command(app, message)

@app.on_message(filters.command("update_porn") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for update_porn command
async def _private_update_porn_handler(app, message):
    from COMMANDS.admin_cmd import update_porn_command
    await update_porn_command(app, message)

@app.on_message(filters.command("reload_porn") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for reload_porn command
async def _private_reload_porn_handler(app, message):
    from COMMANDS.admin_cmd import reload_porn_command
    await reload_porn_command(app, message)

@app.on_message(filters.command("check_porn") & filters.private)
@guarded(timeout=60)  # 1 minute timeout for check_porn command
async def _private_check_porn_handler(app, message):
    from COMMANDS.admin_cmd import check_porn_command
    await check_porn_command(app, message)

# Help close handler for /vid
@app.on_callback_query(filters.regex(r"^vid_help\|"))
@guarded(timeout=60)  # 1 minute timeout for callback
async def vid_help_callback(app, callback_query):
    messages = safe_get_messages(None)
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            await callback_query.message.delete()
        except Exception:
            try:
                callback_query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
        try:
            await callback_query.answer(messages.MAGIC_HELP_CLOSED_MSG)
        except Exception:
            pass
        return

###########################################################
#        APP STARTS
###########################################################
# ###############################################################################################
# Global starting point list (do not modify)
starting_point = []

# ###############################################################################################

# Run the automatic loading of the Firebase cache
start_auto_cache_reloader()

def cleanup_on_exit():
    messages = safe_get_messages(None)
    """Cleanup function to close Firebase connections, HTTP sessions and logger on exit"""
    try:
        from DATABASE.cache_db import close_all_firebase_connections
        close_all_firebase_connections()
        
        # Close HTTP sessions
        try:
            import asyncio
            # Use modern way to get event loop
            try:
                loop = asyncio.get_running_loop()
                # If loop is running, schedule the cleanup
                loop.create_task(close_all_sessions())
            except RuntimeError:
                # No running loop, create new one
                asyncio.run(close_all_sessions())
        except Exception as e:
            print(f"Error closing HTTP sessions: {e}")
        
        # Close logger handlers
        try:
            from HELPERS.logger import close_logger
            close_logger()
        except Exception as e:
            print(messages.MAGIC_ERROR_CLOSING_LOGGER_MSG.format(error=e))
        
        # ДОБАВИТЬ SHUTDOWN ENTERPRISE SCALER
        try:
            from HELPERS.enterprise_scaler import enterprise_scaler
            enterprise_scaler.shutdown(wait=True)
            logger.info("Enterprise scaler shutdown completed")
        except Exception as e:
            print(f"Error shutting down enterprise scaler: {e}")
        
        # ДОБАВИТЬ SHUTDOWN ГИБРИДНЫЙ EXECUTOR (для совместимости)
        try:
            from HELPERS.hybrid_executor import hybrid_executor
            hybrid_executor.shutdown(wait=True)
            logger.info("Hybrid executor shutdown completed")
        except Exception as e:
            print(f"Error shutting down hybrid executor: {e}")
        
        # ДОБАВИТЬ SHUTDOWN EXECUTOR POOL (для совместимости)
        try:
            from HELPERS.executor_pool import executor_pool
            executor_pool.shutdown(wait=True)
            logger.info("Executor pool shutdown completed")
        except Exception as e:
            print(f"Error shutting down executor pool: {e}")
        
        # ДОБАВИТЬ CLOSE ASYNC DB SESSIONS
        try:
            import asyncio
            from DATABASE.firebase_init import db
            
            # Use modern way to get event loop
            try:
                loop = asyncio.get_running_loop()
                # Schedule cleanup
                if hasattr(db, 'close_aio_session'):
                    loop.create_task(db.close_aio_session())
            except RuntimeError:
                # No running loop, create new one
                if hasattr(db, 'close_aio_session'):
                    asyncio.run(db.close_aio_session())
        except Exception as e:
            print(f"Error closing Firebase async sessions: {e}")
        
        print(messages.MAGIC_CLEANUP_COMPLETED_MSG)
    except Exception as e:
        print(messages.MAGIC_ERROR_DURING_CLEANUP_MSG.format(error=e))

# Register cleanup function
atexit.register(cleanup_on_exit)

# Register signal handlers for graceful shutdown
def signal_handler(sig, frame):
    messages = safe_get_messages(None)
    """Handle shutdown signals gracefully"""
    print(messages.MAGIC_SIGNAL_RECEIVED_MSG.format(signal=sig))
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register search callback handler
from COMMANDS.search import handle_search_callback
app.on_callback_query(filters.regex(r"^search_msg\|"))(guarded(timeout=60)(handle_search_callback))

# Register cookies handlers
from COMMANDS.cookies_cmd import cookies_from_browser, browser_choice_callback, save_my_cookie, download_cookie_callback, save_as_cookie_hint_callback
app.on_message(filters.command("cookies_from_browser") & filters.private)(guarded(timeout=60)(cookies_from_browser))
app.on_callback_query(filters.regex(r"^browser_choice\|"))(guarded(timeout=60)(browser_choice_callback))
app.on_message(filters.document)(guarded(timeout=60)(save_my_cookie))
app.on_callback_query(filters.regex(r"^download_cookie\|"))(guarded(timeout=60)(download_cookie_callback))
app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))(guarded(timeout=60)(save_as_cookie_hint_callback))

# Register lang handlers
from COMMANDS.lang_cmd import lang_command, lang_callback_handler
app.on_message(filters.command("lang") & filters.private)(guarded(timeout=60)(lang_command))
app.on_callback_query(filters.regex(r"^lang_select_"))(guarded(timeout=60)(lang_callback_handler))
app.on_callback_query(filters.regex(r"^lang_close"))(guarded(timeout=60)(lang_callback_handler))

# Register subtitles handlers
from COMMANDS.subtitles_cmd import subs_command, subs_page_callback, subs_lang_callback, subs_auto_callback, subs_always_ask_callback, subs_lang_close_callback
app.on_message(filters.command("subs") & filters.private)(guarded(timeout=60)(subs_command))
app.on_callback_query(filters.regex(r"^subs_page\|"))(guarded(timeout=60)(subs_page_callback))
app.on_callback_query(filters.regex(r"^subs_lang\|"))(guarded(timeout=60)(subs_lang_callback))
app.on_callback_query(filters.regex(r"^subs_auto\|"))(guarded(timeout=60)(subs_auto_callback))
app.on_callback_query(filters.regex(r"^subs_always_ask\|"))(guarded(timeout=60)(subs_always_ask_callback))

app.on_callback_query(filters.regex(r"^subs_lang_close\|"))(guarded(timeout=60)(subs_lang_close_callback))

# Register mediainfo handlers
from COMMANDS.mediainfo_cmd import mediainfo_command, mediainfo_option_callback
app.on_message(filters.command("mediainfo") & filters.private)(guarded(timeout=60)(mediainfo_command))
app.on_callback_query(filters.regex(r"^mediainfo_option\|"))(guarded(timeout=60)(mediainfo_option_callback))

# Register proxy handlers
from COMMANDS.proxy_cmd import proxy_command, proxy_option_callback
app.on_message(filters.command("proxy") & filters.private)(guarded(timeout=60)(proxy_command))
app.on_callback_query(filters.regex(r"^proxy_option\|"))(guarded(timeout=60)(proxy_option_callback))

# Register other handlers
from COMMANDS.other_handlers import help_msg_callback, audio_command_handler, link_command_handler, proxy_command_handler, playlist_command, playlist_help_callback, userlogs_close_callback, audio_hint_callback
app.on_callback_query(filters.regex(r"^help_msg\|"))(guarded(timeout=60)(help_msg_callback))
app.on_message(filters.command("audio") & filters.private)(guarded(timeout=60)(audio_command_handler))
app.on_message(filters.command("link") & filters.private)(guarded(timeout=60)(link_command_handler))
app.on_message(filters.command("proxy") & filters.private)(guarded(timeout=60)(proxy_command_handler))
app.on_message(filters.command("playlist") & filters.private)(guarded(timeout=60)(playlist_command))
app.on_callback_query(filters.regex(r"^playlist_help\|"))(guarded(timeout=60)(playlist_help_callback))
app.on_callback_query(filters.regex(r"^userlogs_close\|"))(guarded(timeout=60)(userlogs_close_callback))
app.on_callback_query(filters.regex(r"^audio_hint\|"))(guarded(timeout=60)(audio_hint_callback))

# Register format handlers
from COMMANDS.format_cmd import set_format, format_option_callback, format_codec_callback, format_container_callback, format_custom_callback
app.on_message(filters.command("format") & filters.private)(guarded(timeout=60)(set_format))
app.on_callback_query(filters.regex(r"^format_option\|"))(guarded(timeout=60)(format_option_callback))
app.on_callback_query(filters.regex(r"^format_codec\|"))(guarded(timeout=60)(format_codec_callback))
app.on_callback_query(filters.regex(r"^format_container\|"))(guarded(timeout=60)(format_container_callback))
app.on_callback_query(filters.regex(r"^format_custom\|"))(guarded(timeout=60)(format_custom_callback))

# Register split handlers
from COMMANDS.split_sizer import split_command, split_size_callback
app.on_message(filters.command("split") & filters.private)(guarded(timeout=60)(split_command))
app.on_callback_query(filters.regex(r"^split_size\|"))(guarded(timeout=60)(split_size_callback))

# Register tag handlers
from COMMANDS.tag_cmd import tags_command, tags_close_callback
app.on_message(filters.command("tags") & filters.private)(guarded(timeout=60)(tags_command))
app.on_callback_query(filters.regex(r"^tags_close\|"))(guarded(timeout=60)(tags_close_callback))

# Register settings handlers
from COMMANDS.settings_cmd import settings_command, settings_menu_callback, settings_cmd_callback, hint_callback
app.on_message(filters.command("settings") & filters.private)(guarded(timeout=60)(settings_command))
app.on_callback_query(filters.regex(r"^settings__menu__"))(guarded(timeout=60)(settings_menu_callback))
app.on_callback_query(filters.regex(r"^settings__cmd__"))(guarded(timeout=60)(settings_cmd_callback))
app.on_callback_query(filters.regex(r"^(img_hint|link_hint|search_hint|search_msg)\|"))(guarded(timeout=60)(hint_callback))

# Register nsfw handlers
from COMMANDS.nsfw_cmd import nsfw_command, nsfw_option_callback
app.on_message(filters.command("nsfw"))(guarded(timeout=60)(nsfw_command))
app.on_callback_query(filters.regex(r"^nsfw_option\|"))(guarded(timeout=60)(nsfw_option_callback))

# Register image handlers
from COMMANDS.image_cmd import img_help_callback, img_range_callback
app.on_callback_query(filters.regex(r"^img_help\|"))(guarded(timeout=60)(img_help_callback))
app.on_callback_query(filters.regex(r"^img_range\|"))(guarded(timeout=60)(img_range_callback))

# Register always ask handlers
from DOWN_AND_UP.always_ask_menu import ask_filter_callback, askq_callback, fallback_gallery_dl_callback
app.on_callback_query(filters.regex(r"^askf\|"))(guarded(timeout=60)(ask_filter_callback))
app.on_callback_query(filters.regex(r"^askq\|"))(guarded(timeout=60)(askq_callback))
app.on_callback_query(filters.regex(r"^fallback_gallery_dl\|"))(guarded(timeout=60)(fallback_gallery_dl_callback))

# Register url extractor handlers
from URL_PARSERS.url_extractor import keyboard_callback_handler_wrapper, add_group_msg_callback, audio_hint_callback, link_hint_callback, lang_callback
app.on_callback_query(filters.regex("^keyboard\\|"))(guarded(timeout=60)(keyboard_callback_handler_wrapper))
app.on_callback_query(filters.regex(r"^add_group_msg\|"))(guarded(timeout=60)(add_group_msg_callback))
app.on_callback_query(filters.regex(r"^audio_hint\|"))(guarded(timeout=60)(audio_hint_callback))
app.on_callback_query(filters.regex(r"^link_hint\|"))(guarded(timeout=60)(link_hint_callback))
app.on_callback_query(filters.regex(r"^lang_"))(guarded(timeout=60)(lang_callback))

# Register status command for admins
from COMMANDS.status_cmd import status_command, status_refresh_callback
app.on_message(filters.command("status") & filters.private)(guarded(timeout=60)(status_command))
app.on_callback_query(filters.regex(r"^status_refresh$"))(guarded(timeout=60)(status_refresh_callback))

# Register health command callbacks
from COMMANDS.health_cmd import health_callback
app.on_callback_query(filters.regex(r"^health_"))(guarded(timeout=60)(health_callback))

# Start health monitoring
try:
    from HELPERS.health_monitor import health_monitor
    import asyncio
    
    # Start health monitor in the main event loop
    async def start_health_monitor():
        await health_monitor.start_monitoring()
        print("✅ Health monitor started")
    
    # Schedule health monitor to start when app starts
    import threading
    def schedule_health_monitor():
        try:
            # Wait a bit for the app to start
            import time
            time.sleep(2)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_health_monitor())
        except Exception as e:
            print(f"⚠️  Health monitor failed to start: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    # Start in background thread
    health_thread = threading.Thread(target=schedule_health_monitor, daemon=True)
    health_thread.start()
except Exception as e:
    print(f"⚠️  Health monitor failed to start: {e}")

app.run()
