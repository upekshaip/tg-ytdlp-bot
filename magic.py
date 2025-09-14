# Version 4.0.0 # split monolith code into multiple modules
###########################################################
#        GLOBAL IMPORTS
###########################################################
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

print("✅ All modules are loaded")

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
from COMMANDS.cookies_cmd import cookies_from_browser

def _wrap_group(fn):
    def _inner(app, message):
        if not ensure_group_admin(app, message):
            return
        return fn(app, message)
    return _inner

# Register group equivalents where applicable
_allowed_groups = tuple(getattr(Config, 'ALLOWED_GROUP', []))

def _is_allowed_group(message):
    try:
        gid = int(getattr(message.chat, 'id', 0))
        allowed = gid in _allowed_groups
        try:
            # Explicit log once per check
            from HELPERS.logger import logger
            logger.info(f"[ALLOWED_GROUP_CHECK] chat_id={gid} allowed={allowed} list={list(_allowed_groups)}")
        except Exception:
            pass
        return allowed
    except Exception:
        return False

if _allowed_groups:
    app.on_message(filters.group & filters.command("img"))(_wrap_group(lambda a, m: image_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("mediainfo"))(_wrap_group(lambda a, m: mediainfo_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("nsfw"))(_wrap_group(lambda a, m: nsfw_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("proxy"))(_wrap_group(lambda a, m: proxy_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("settings"))(_wrap_group(lambda a, m: settings_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("format"))(_wrap_group(lambda a, m: set_format(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("split"))(_wrap_group(lambda a, m: split_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("link"))(_wrap_group(lambda a, m: link_command_handler(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("tags"))(_wrap_group(lambda a, m: tags_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("audio"))(_wrap_group(lambda a, m: audio_command_handler(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("playlist"))(_wrap_group(lambda a, m: playlist_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("subs"))(_wrap_group(lambda a, m: subs_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("args"))(_wrap_group(lambda a, m: args_cmd.args_command(a, m) if _is_allowed_group(m) else None))
    app.on_message(filters.group & filters.command("cookies_from_browser"))(_wrap_group(lambda a, m: cookies_from_browser(a, m) if _is_allowed_group(m) else None))

    # Text/url handler in allowed groups (topic-aware)
    # Text/url handler in allowed groups (topic-aware) including mentions
    def _guarded_text(a, m):
        if _is_allowed_group(m):
            return url_distractor(a, m)
        # If not allowed, do nothing (deny service silently)
        return None
    app.on_message(filters.group & filters.text)(_wrap_group(_guarded_text))

    # Map basic commands to url_distractor to mimic private behavior
    for _cmd in ("start", "help", "keyboard", "clean", "search", "usage", "check_cookie", "save_as_cookie"):
        app.on_message(filters.group & filters.command(_cmd))(_wrap_group(lambda a, m, __c=_cmd: url_distractor(a, m) if _is_allowed_group(m) else None))

###########################################################
#        /vid command (private and groups)
###########################################################
def _vid_handler(app, message):
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
            return url_distractor(app, message)
        else:
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔚Close", callback_data="vid_help|close")]])
            help_text = (
                "<b>🎬 Video Download Command</b>\n\n"
                "Usage: <code>/vid URL</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/vid https://youtube.com/watch?v=123abc</code>\n"
                "• <code>/vid https://youtube.com/playlist?list=123abc*1*5</code>\n"
                "• <code>/vid 3-7 https://youtube.com/playlist?list=123abc</code>\n\n"
                "Also see: /audio, /img, /help, /playlist, /settings"
            )
            safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb, message=message)
    except Exception:
        from HELPERS.safe_messeger import safe_send_message
        from pyrogram import enums
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔚Close", callback_data="vid_help|close")]])
        help_text = (
            "<b>🎬 Video Download Command</b>\n\n"
            "Usage: <code>/vid URL</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/vid https://youtube.com/watch?v=123abc</code>\n"
            "• <code>/vid https://youtube.com/playlist?list=123abc*1*5</code>\n"
            "• <code>/vid 3-7 https://youtube.com/playlist?list=123abc</code>\n\n"
            "Also see: /audio, /img, /help, /playlist, /settings"
        )
        safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb, message=message)

# Register /vid in private and allowed groups
app.on_message(filters.command("vid") & filters.private)(_vid_handler)
if _allowed_groups:
    app.on_message(filters.group & filters.command("vid"))(_wrap_group(lambda a, m: _vid_handler(a, m) if _is_allowed_group(m) else None))

# Help close handler for /vid
@app.on_callback_query(filters.regex(r"^vid_help\|"))
def vid_help_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            try:
                callback_query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
        try:
            callback_query.answer("Help closed.")
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
    """Cleanup function to close Firebase connections and logger on exit"""
    try:
        from DATABASE.cache_db import close_all_firebase_connections
        close_all_firebase_connections()
        
        # Close logger handlers
        try:
            from HELPERS.logger import close_logger
            close_logger()
        except Exception as e:
            print(f"❌ Error closing logger: {e}")
        
        print("✅ Cleanup completed on exit")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)

# Register signal handlers for graceful shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {sig}, shutting down gracefully...")
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

app.run()
