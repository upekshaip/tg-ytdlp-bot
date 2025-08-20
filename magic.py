# Version 4.0.0 # split monolith code into multiple modules
###########################################################
#        GLOBAL IMPORTS
###########################################################
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
from COMMANDS.mediainfo_cmd import *
from COMMANDS.other_handlers import *
from COMMANDS.settings_cmd import *
from COMMANDS.split_sizer import *
from COMMANDS.subtitles_cmd import *
from COMMANDS.tag_cmd import *

# DOWN_AND_UP (с обработчиками - импортируем после установки app)
from DOWN_AND_UP.always_ask_menu import *

print("✅ All modules are loaded")

###########################################################
#        BOT KEYBOARD
###########################################################
# Import decorators from HELPERS
from HELPERS.decorators import reply_with_keyboard, get_main_reply_keyboard, send_reply_keyboard_always

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
    """Cleanup function to close Firebase connections on exit"""
    try:
        from DATABASE.cache_db import close_all_firebase_connections
        close_all_firebase_connections()
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
