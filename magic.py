# Version 2.4.3
import logging
import math
import os
import re
import shutil
import subprocess
#import sys
import threading
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Tuple
from urllib.parse import urlparse, parse_qs, urlunparse, unquote, urlencode

import pyrebase
import tldextract
from moviepy.editor import VideoFileClip
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

import io
from PIL import Image
import requests


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
#     ...

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


# Firebase Initialization with Authentication
firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)

# Create auth object from pyrebase
auth = firebase.auth()

# Sign in using email and password (ensure these credentials are set in your Config)
try:
    user = auth.sign_in_with_email_and_password(Config.FIREBASE_USER, Config.FIREBASE_PASSWORD)
    # Debug: Print essential details of the user object
    logger.info("User signed in successfully.")
    logger.info(f"User email: {user.get('email')}")
    logger.info(f"User localId: {user.get('localId')}")
    # If available, check email verification status
    if "emailVerified" in user:
        logger.info(f"Email verified: {user['emailVerified']}")
    else:
        logger.info("Email verification status not available in user object.")
except Exception as e:
    logger.error(f"Error during Firebase authentication: {e}")
    raise

# Debug: Print a portion of idToken
idToken = user.get("idToken")
if idToken:
    logger.info(f"Firebase idToken (first 20 chars): {idToken[:20]}")
else:
    logger.error("No idToken received!")
    raise Exception("idToken is empty.")

# Get the base database object
base_db = firebase.database()

# Additional check: Execute a test GET request to the root node
try:
    test_data = base_db.get(idToken)
    logger.info("Test GET operation succeeded. Data:", test_data.val())
except Exception as e:
    logger.error("Test GET operation failed:", e)


# Define a wrapper class to automatically pass the idToken for all database operations
class AuthedDB:
    def __init__(self, db, token):
        self.db = db
        self.token = token

    def child(self, path):
        return AuthedDB(self.db.child(path), self.token)

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


# Let's use the rstrip() method directly in the f-string to form the correct path
db = AuthedDB(base_db, user["idToken"])
db_path = Config.BOT_DB_PATH.rstrip("/")
_format = {"ID": "0", "timestamp": math.floor(time.time())}
try:
    # Try writing data to the path: bot/tgytdlp_bot/users/0
    result = db.child(f"{db_path}/users/0").set(_format)
    logger.info("Data written successfully. Result:", result)
except Exception as e:
    logger.error("Error writing data to Firebase:", e)
    raise


# Function to periodically refresh the idToken using the refreshToken
def token_refresher():
    global db, user
    while True:
        # Sleep for 50 minutes (3000 seconds)
        time.sleep(3000)
        try:
            new_user = auth.refresh(user["refreshToken"])
            new_idToken = new_user["idToken"]
            db.token = new_idToken
            user = new_user
            logger.info("Firebase idToken refreshed successfully. New token (first 20 chars):", new_idToken[:20])
        except Exception as e:
            logger.error("Error refreshing Firebase idToken:", e)


# Start the token refresher thread as a daemon
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
    app.send_message(message.chat.id, (Config.HELP_MSG),
                     parse_mode=enums.ParseMode.HTML)
    send_to_logger(message, f"Send help txt to user")


def create_directory(path):
    # Create The Directory (And All Intermediate Directories) IF Its Not Exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# Command to Set Browser Cooks
@app.on_message(filters.command("cookies_from_browser") & filters.private)
#@reply_with_keyboard
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

    # Add a cancel button
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="browser_choice|cancel")])
    keyboard = InlineKeyboardMarkup(buttons)

    app.send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard
    )
    send_to_logger(message, "Browser selection keyboard sent with installed browsers only.")


# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
#@reply_with_keyboard
def browser_choice_callback(app, callback_query):
    logger.info(f"[BROWSER] callback: {callback_query.data}")
    import subprocess

    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]  # E.G. "Chromium", "Firefox", or "Cancel"
    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "cancel":
        callback_query.edit_message_text("🔚 Browser selection canceled.")
        callback_query.answer("✅ Browser choice updated.")
        send_to_logger(callback_query.message, "Browser selection canceled.")
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

# Command to Download Audio from a Video url
@app.on_message(filters.command("audio") & filters.private)
#@reply_with_keyboard
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
    
    down_and_audio(app, message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)


# /Playlist Command
@app.on_message(filters.command("playlist") & filters.private)
#@reply_with_keyboard
def playlist_command(app, message):
    user_id = message.chat.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    app.send_message(user_id, Config.PLAYLIST_HELP_MSG, parse_mode=enums.ParseMode.HTML)
    send_to_logger(message, "User requested playlist help.")


# Command /Format Handler
@app.on_message(filters.command("format") & filters.private)
#@reply_with_keyboard
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
            [InlineKeyboardButton("🔙 Cancel", callback_data="format_option|cancel")]
        ])
        app.send_message(
            user_id,
            "Select a format option or send a custom one using `/format <format_string>`:",
            reply_markup=main_keyboard
        )
        send_to_logger(message, "Format menu sent.")


# Callbackquery Handler for /Format Menu Selection
@app.on_callback_query(filters.regex(r"^format_option\|"))
#@reply_with_keyboard
def format_option_callback(app, callback_query):
    logger.info(f"[FORMAT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    # If you press the Cancel button
    if data == "cancel":
        callback_query.edit_message_text("🔚 Format selection canceled.")
        callback_query.answer("✅ Format choice updated.")
        send_to_logger(callback_query.message, "Format selection canceled.")
        return

    # If the Custom button is pressed
    if data == "custom":
        callback_query.edit_message_text(
            "To use a custom format, send the command in the following form:\n\n`/format bestvideo+bestaudio/best`\n\nReplace `bestvideo+bestaudio/best` with your desired format string."
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
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back")]
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
            [InlineKeyboardButton("🔙 Cancel", callback_data="format_option|cancel")]
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
        elif clean_args == "all":
            # Delete all files and display the list of deleted ones
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                send_to_all(message, "🗑 No files to remove.")
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
    user_id = message.chat.id
    if int(message.chat.id) in Config.ADMIN:
        user_id = message.chat.id
        if Config.GET_USER_LOGS_COMMAND in message.text:
            user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    try:
        db_data = db.child("bot").child("tgytdlp_bot").child("logs").child(user_id).get().each()
        lst = [user.val() for user in db_data]
        data = []
        data_tg = []
        least_10 = []

        for l in lst:
            ts = datetime.fromtimestamp(int(l["timestamp"]))
            row = f"""{ts} | {l["ID"]} | {l["name"]} | {l["title"]} | {l["urls"]}"""
            row_2 = f"""**{ts}** | `{l["ID"]}` | **{l["name"]}** | {l["title"]} | {l["urls"]}"""
            data.append(row)
            data_tg.append(row_2)
        total = len(data_tg)
        if total > 10:
            for i in range(10):
                info = data_tg[(total - 10) + i]
                least_10.append(info)
            least_10.sort(key=str.lower)
            format_str = '\n \n'.join(least_10)
        else:
            data_tg.sort(key=str.lower)
            format_str = '\n \n'.join(data_tg)
        data.sort(key=str.lower)
        now = datetime.fromtimestamp(math.floor(time.time()))
        txt_format = f"Logs of {Config.BOT_NAME_FOR_USERS}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n \n" + \
                     '\n'.join(data)

        user_dir = os.path.join("users", str(message.chat.id))
        create_directory(user_dir)
        log_path = os.path.join(user_dir, "logs.txt")
        with open(log_path, 'w', encoding="utf-8") as f:
            f.write(str(txt_format))

        send_to_all(message, f"Total: **{total}**\n**{user_id}** - logs (Last 10):\n \n \n{format_str}")
        app.send_document(message.chat.id, log_path,
                          caption=f"{user_id} - all logs")
        app.send_document(Config.LOGS_ID, log_path,
                          caption=f"{user_id} - all logs")
    except:
        send_to_all(message, "**❌ User did not download any content yet...** Not exist in logs")


# Get All Kinds of Users (Users/ Blocked/ Unblocked)

def get_user_details(app, message):
    global path
    command = message.text.split(Config.GET_USER_DETAILS_COMMAND)[1]
    if command == "_blocked":
        path = "blocked_users"
    if command == "_unblocked":
        path = "unblocked_users"
    if command == "_users":
        path = "users"
    modified_lst = []
    txt_lst = []
    raw_data = db.child(
        f"{Config.BOT_DB_PATH}/{path}").get().each()
    data_users = [user.val() for user in raw_data]
    for user in data_users:
        if user["ID"] != "0":
            id = user["ID"]
            ts = datetime.fromtimestamp(int(user["timestamp"]))
            txt_format = f"TS: {ts} | ID: {id}"
            id = f"TS: **{ts}** | ID: `{id}`"
            modified_lst.append(id)
            txt_lst.append(txt_format)

    modified_lst.sort(key=str.lower)
    txt_lst.sort(key=str.lower)
    no_of_users_to_display = 20
    if len(modified_lst) <= no_of_users_to_display:
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " + \
              path + \
              f":\n \n" + \
              '\n'.join(modified_lst)
    else:
        temp = []
        for j in range(no_of_users_to_display):
            temp.append(modified_lst[((j + 1) * -1)])
        temp.sort(key=str.lower)
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " + \
              path + \
              f":\n \n" + '\n'.join(temp)

    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = f"{Config.BOT_NAME} {path}\nTotal {path}: {len(modified_lst)}\nCurrent time: {now}\n \n" + '\n'.join(
        txt_lst)
    file = path + '.txt'
    with open(file, 'w', encoding="utf-8") as f:
        f.write(str(txt_format))
    send_to_all(message, mod)
    app.send_document(message.chat.id, "./" + file,
                      caption=f"{Config.BOT_NAME} - all {path}")
    app.send_document(Config.LOGS_ID, "./" + file,
                      caption=f"{Config.BOT_NAME} - all {path}")

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
        #Clearing the cache by video
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
#@reply_with_keyboard
def settings_command(app, message):
    user_id = message.chat.id
    # Main settings menu
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean")],
        [InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies")],
        [InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media")],
        [InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs")],
        [InlineKeyboardButton("🔙 Close", callback_data="settings__menu__close")]
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
#@reply_with_keyboard
def settings_menu_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[-1]
    if data == "close":
        callback_query.message.delete()
        callback_query.answer("Menu closed.")
        return
    if data == "clean":
        # Show the cleaning menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍪 Cookies", callback_data="clean_option|cookies")],
            [InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs")],
            [InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags")],
            [InlineKeyboardButton("📼 Format", callback_data="clean_option|format")],
            [InlineKeyboardButton("✂️ Split", callback_data="clean_option|split")],
            [InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo")],
            [InlineKeyboardButton("🗑  All files", callback_data="clean_option|all")],
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
            [InlineKeyboardButton("📥 /download_cookie - Download my YouTube cookie",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get cookies from browser",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Check cookie file in your folder",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Send text to save as cookie",
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
            [InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean")],
            [InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies")],
            [InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media")],
            [InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs")],
            [InlineKeyboardButton("🔙 Close", callback_data="settings__menu__close")]
        ])
        callback_query.edit_message_text(
            "<b>Bot Settings</b>\n\nChoose a category:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return


@app.on_callback_query(filters.regex(r"^settings__cmd__"))
#@reply_with_keyboard
def settings_cmd_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[2]

    # For commands that are processed only via url_distractor, create a temporary Message
    if data == "clean":
        # Show the cleaning menu instead of direct execution
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍪 Cookies only", callback_data="clean_option|cookies")],
            [InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs")],
            [InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags")],
            [InlineKeyboardButton("📼 Format", callback_data="clean_option|format")],
            [InlineKeyboardButton("✂️ Split", callback_data="clean_option|split")],
            [InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo")],
            [InlineKeyboardButton("🗑  All files", callback_data="clean_option|all")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__cookies")]
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
        app.send_message(user_id, Config.SAVE_AS_COOKIE_HINT, reply_to_message_id=callback_query.message.id,
                         parse_mode=enums.ParseMode.HTML)
        callback_query.answer("Hint sent.")
        return
    if data == "format":
        # Add the command attribute for set_format to work correctly
        set_format(app, fake_message("/format", user_id, command=["format"]))
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
        # We just send a hint on how to use it
        app.send_message(user_id,
                         "Download only audio from video source.\nUsage: /audio + URL (ex. /audio https://youtu.be/abc123)",
                         reply_to_message_id=callback_query.message.id)
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
#@reply_with_keyboard
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
    elif data == "all":
        url_distractor(app, fake_message("/clean all", user_id))
        callback_query.answer("All files cleaned.")
        return
    elif data == "back":
        # Back to the cookies menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 /download_cookie - Download my YouTube cookie",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get cookies from browser",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Check cookie file in your folder",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Send text to save as cookie",
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
    if command is not None:
        m.command = command
    return m


# /Mediainfo Command
@app.on_message(filters.command("mediainfo") & filters.private)
#@reply_with_keyboard
def mediainfo_command(app, message):
    user_id = message.chat.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    buttons = [
        [InlineKeyboardButton("✅ ON", callback_data="mediainfo_option|on")],
        [InlineKeyboardButton("❌ OFF", callback_data="mediainfo_option|off")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="mediainfo_option|cancel")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    app.send_message(
        user_id,
        "Enable or disable sending MediaInfo for downloaded files?",
        reply_markup=keyboard
    )
    send_to_logger(message, "User opened /mediainfo menu.")


@app.on_callback_query(filters.regex(r"^mediainfo_option\|"))
#@reply_with_keyboard
def mediainfo_option_callback(app, callback_query):
    logger.info(f"[MEDIAINFO] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
    if callback_query.data == "mediainfo_option|cancel":
        callback_query.edit_message_text("🔚 MediaInfo: cancelled.")
        callback_query.answer("Menu closed.")
        send_to_logger(callback_query.message, "MediaInfo: cancelled.")
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
    # We determine the path to the user folder (for example, "./users/1234567)
    user_folder = f"./users/{user_id}"
    create_directory(user_folder)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_folder, cookie_filename)
    app.download_media(message, file_name=cookie_file_path)
    send_to_user(message, "✅ Cookie file saved")
    send_to_logger(message, f"Cookie file saved for user {user_id}.")

#@reply_with_keyboard
def download_cookie(app, message):
    user_id = str(message.chat.id)
    response = requests.get(Config.COOKIE_URL)
    if response.status_code == 200:
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "wb") as cf:
            cf.write(response.content)
        send_to_user(message, "**✅ YouTube cookie file downloaded and saved in your folder.**")
        send_to_logger(message, f"YouTube cookie file downloaded for user {user_id}.")
    else:
        send_to_user(message, "❌ Cookie URL is not available!")
        send_to_logger(message, f"Failed to download cookie file for user {user_id}.")


# Caption Editor for Videos
@app.on_message(filters.text & filters.private)
#@reply_with_keyboard
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
#@reply_with_keyboard
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
#@reply_with_keyboard
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
#@reply_with_keyboard
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

#@reply_with_keyboard
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

    # --- Определяем размеры превью/видео ---
    width = None
    height = None
    if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
        if "youtube.com/shorts/" in video_url or "/shorts/" in video_url:
            width, height = 360, 640
        else:
            width, height = 640, 360
    else:
        # Для остальных — определяем размеры видео динамически
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_abs_path)
            width = int(str(clip.w).strip().split()[0]) if clip.w else 0
            height = int(str(clip.h).strip().split()[0]) if clip.h else 0
            clip.close()
        except Exception:
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
                f"{info_text}\n**Video duration:** __{TimeFormatter(duration*1000)}__\n\n__Uploading Video... 📤__"
            ),
            reply_to_message_id=message.id,
            parse_mode=enums.ParseMode.HTML
        )
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

#####################################################################################

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
    thumb_dir = os.path.abspath(dir + "/" + thumb_name + ".jpg")
    clip = VideoFileClip(video_path)
    duration = (int(clip.duration))
    
    # Get original video dimensions
    #orig_w, orig_h = clip.w, clip.h
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
    thumb_dir = os.path.abspath(os.path.join(dir_path, thumb_name + ".jpg"))

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
        #if 'x' in size_result:
            #orig_w, orig_h = map(int, size_result.split('x'))
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
            #duration = int(float(result))
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

#@reply_with_keyboard
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
                app.send_message(user_id, f"♻️ {len(cached_videos)}/{len(requested_indices)} audio sent from cache, downloading missing ones...", reply_to_message_id=message.id)
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
                proc_msg = app.send_message(user_id, f"⚠️ Telegram has limited message sending.\n\n⏳ Please wait: {time_str}\n\nTo update timer send URL again 2 times.")
        else:
            proc_msg = app.send_message(user_id, "⚠️ Telegram has limited message sending.\n\n⏳ Please wait: \n\nTo update timer send URL again 2 times.")

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
        proc_msg = app.send_message(user_id, "Processing... ♻️", reply_to_message_id=message.id)
        proc_msg_id = proc_msg.id
        status_msg = app.send_message(user_id, "🎧 Audio is processing...")
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

        cookie_file = os.path.join(user_folder, os.path.basename(Config.COOKIE_FILE_PATH))
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
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\nDownloading audio:\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "finished":
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{current_total_process}\nDownloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
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
                  'key': 'EmbedThumbnail'   # эквивалент --embed-thumbnail
               },
               {
                  'key': 'FFmpegMetadata'   # эквивалент --add-metadata
               }                  
                ],
               'prefer_ffmpeg': True,
               'extractaudio': True,
               'playlist_items': str(current_index + video_start_with),
               'cookiefile': cookie_file,
               'outtmpl': os.path.join(user_folder, "%(title)s.%(ext)s"),
               'progress_hooks': [progress_hook],
               'extractor_args': {
                  'generic': ['impersonate=chrome']
               },
               'referer': url,
               'geo_bypass': True,
               'check_certificate': False,
               'live_from_start': True,
            }   
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
                        f"{current_total_process}\n\n> __Downloading audio using format: ba...__ 📥")
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
                send_to_user(message, f"❌ Error downloading: {error_text}\n\nPerhaps cookie authorization is required. More information: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")
                logger.error(f"DownloadError: {error_text}")
                return None
            except Exception as e:
                logger.error(f"Audio download attempt failed: {e}")
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
                        send_to_all(
                            message,
                            f"❌ Failed to download audio: Check if your site is supported\n"
                            "> You may need `cookie` for downloading this audio. First, clean your workspace via **/clean** command\n"
                            "> For Youtube - get `cookie` via **/download_cookie** command. For any other supported site - send your own cookie and after that send your audio link again."
                        )
                break

            successful_uploads += 1

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
                safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\nUploading audio file...\n{full_bar}   100.0%")
            except Exception as e:
                logger.error(f"Error updating upload status: {e}")

            # We form a text with tags and a link for audio
            tags_for_final = tags if isinstance(tags, list) else (tags.split() if isinstance(tags, str) else [])
            tags_text_final = generate_final_tags(url, tags_for_final, info_dict)
            tags_block = (tags_text_final.strip() + '\n') if tags_text_final and tags_text_final.strip() else ''
            bot_name = getattr(Config, 'BOT_NAME', None) or 'bot'
            bot_mention = f' @{bot_name}' if not bot_name.startswith('@') else f' {bot_name}'
            # Use original audio_title for caption, not sanitized caption_name
            caption_with_link = f"{audio_title}\n\n{tags_block}[🔗 Audio URL]({url}){bot_mention}"
            
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
                        save_to_video_cache(url, quality_key, msg_ids, original_text=message.text or message.caption or "")
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
            success_msg = f"✅ Audio successfully downloaded and sent - {len(indices_to_download)} files uploaded.\n\n{Config.CREDITS_MSG}"
        else:
            success_msg = f"⚠️ Partially completed - {successful_uploads}/{len(indices_to_download)} audio files uploaded.\n\n{Config.CREDITS_MSG}"
            
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

    user_id = message.chat.id
    logger.info(f"down_and_up called: url={url}, quality_key={quality_key}, format_override={format_override}, video_count={video_count}, video_start_with={video_start_with}")
    
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
                app.send_message(user_id, f"♻️ {len(cached_videos)}/{len(requested_indices)} videos sent from cache, downloading missing ones...", reply_to_message_id=message.id)
    elif quality_key and not is_playlist:
        cached_ids = get_cached_message_ids(url, quality_key)
        if cached_ids:
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
                save_to_video_cache(url, quality_key, [], clear=True)
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
                proc_msg = app.send_message(user_id, f"⚠️ Telegram has limited message sending.\n\n⏳ Please wait: {time_str}\n\nTo update timer send URL again 2 times.")
        else:
            proc_msg = app.send_message(user_id, "⚠️ Telegram has limited message sending.\n\n⏳ Please wait: \n\nTo update timer send URL again 2 times.")

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
        proc_msg = app.send_message(user_id, "Processing... ♻️", reply_to_message_id=message.id)
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
                    {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best', 'prefer_ffmpeg': True, 'merge_output_format': 'mp4', 'extract_flat': False},
                    {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                ]
            else:
                if os.path.exists(custom_format_path):
                    with open(custom_format_path, "r", encoding="utf-8") as f:
                        custom_format = f.read().strip()
                    if custom_format.lower() == "best":
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': False}]
                    else:
                        attempts = [{'format': custom_format, 'prefer_ffmpeg': True, 'merge_output_format': 'mp4'}]
                else:
                    attempts = [
                        {'format': 'bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best',
                        'prefer_ffmpeg': True, 'merge_output_format': 'mp4', 'extract_flat': False},
                        {'format': 'bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best',
                        'prefer_ffmpeg': True, 'merge_output_format': 'mp4', 'extract_flat': False},
                        {'format': 'best', 'prefer_ffmpeg': False, 'extract_flat': False}
                    ]

        status_msg = app.send_message(user_id, "📹 Video is processing...")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

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
                                if msg.text == "Processing... ♻️":
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
                'cookiefile': os.path.join("users", str(user_id), os.path.basename(Config.COOKIE_FILE_PATH)),
                'playlist_items': str(current_index),  # We use only current_index for playlists
                'outtmpl': os.path.join(user_dir_name, "%(title)s.%(ext)s"),
                'postprocessors': [
                {
                   'key': 'EmbedThumbnail'   # эквивалент --embed-thumbnail
                },
                {
                   'key': 'FFmpegMetadata'   # эквивалент --add-metadata
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

                if ("m3u8" in url.lower()) or (info_dict.get("protocol") == "m3u8_native"):
                    is_hls = True
                    # if "format" in ytdl_opts:
                    # del ytdl_opts["format"]
                    ytdl_opts["downloader"] = "ffmpeg"
                    ytdl_opts["hls_use_mpegts"] = True
                try:
                    if is_hls:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n\n__Detected HLS stream. Downloading...__ 📥")
                    else:
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n\n> __Downloading using format: {ytdl_opts.get('format', 'default')}...__ 📥")
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
                send_to_user(message, f"❌ Error downloading: {error_message}\n\nPerhaps cookie authorization is required. More information: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")
                logger.error(f"DownloadError: {error_message}")
                return None
            except Exception as e:
                error_message = str(e)
                logger.error(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
                
                # Check if this is a "No videos found in playlist" error - skip it
                if "No videos found in playlist" in str(e):
                    logger.info(f"Skipping playlist item at index {current_index} (no video found)")
                    return "SKIP"  # Special return value to indicate skip
                
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
            for attempt in attempts:
                result = try_download(url, attempt)
                if result == "SKIP":
                    skip_item = True
                    break
                elif result is not None:
                    info_dict = result
                    break

            if skip_item:
                logger.info(f"Skipping item at index {current_index} (no video content)")
                continue

            if info_dict is None:
                with playlist_errors_lock:
                    error_key = f"{user_id}_{playlist_name}"
                    if error_key not in playlist_errors:
                        playlist_errors[error_key] = True
                        send_to_all(
                            message,
                            f"❌ Failed to download video: {error_message}\n────────────────\n"
                            "> Check [here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) if your site supported\n"
                            "> You may need `cookie` for downloading this video. First, clean your workspace via **/clean** command\n"
                            "> For Youtube - get `cookie` via **/download_cookie** command. For any other supported site - send your own cookie ([guide1](https://t.me/c/2303231066/18)) ([guide2](https://t.me/c/2303231066/22)) and after that send your video link again."
                        )
                break

            successful_uploads += 1

            video_id = info_dict.get("id", None)
            original_video_title = info_dict.get("title", None)  # Original title with emojis
            full_video_title = info_dict.get("description", original_video_title)
            video_title = sanitize_filename(original_video_title) if original_video_title else "video"  # Sanitized for file operations

            # --- Use new centralized function for all tags ---
            tags_text_final = generate_final_tags(url, tags_text.split(), info_dict)
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
                    f"{info_text}\n\n{full_bar}   100.0%\n\n__Downloaded video. Processing for upload...__ ♻️")
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
                        f"{info_text}\n\n{full_bar}   100.0%\nConverting video using ffmpeg... ⏳")
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
                    f"{info_text}\n\n{full_bar}   100.0%\n__⚠️ Your video size ({video_size}) is too large.__\n__Splitting file...__ ✂️")
                returned = split_video_2(dir_path, sanitize_filename(caption_name), after_rename_abs_path, int(video_size_in_bytes), max_size, duration)
                caption_lst = returned.get("video")
                path_lst = returned.get("path")
                # Накапливаем все ID частей split-видео
                split_msg_ids = []
                for p in range(len(caption_lst)):
                    part_result = get_duration_thumb(message, dir_path, path_lst[p], sanitize_filename(caption_lst[p]))
                    if part_result is None:
                        continue
                    part_duration, splited_thumb_dir = part_result
                    # --- TikTok: Don't Pass Title ---
                    video_msg = send_videos(message, path_lst[p], '' if force_no_title else caption_lst[p], part_duration, splited_thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
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
                                save_to_playlist_cache(get_clean_playlist_url(url), rounded_quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), rounded_quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                            else:
                                # Накапливаем ID частей для split видео
                                split_msg_ids.extend([m.id for m in forwarded_msgs])
                        else:
                            logger.info(f"down_and_up: collecting video_msg.id for split video: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # Накапливаем ID частей для split видео
                                split_msg_ids.append(video_msg.id)
                    except Exception as e:
                        logger.error(f"Error forwarding video to logger: {e}")
                        logger.info(f"down_and_up: collecting video_msg.id after error for split video: {video_msg.id}")
                        if is_playlist:
                            # For playlists, save to playlist cache with video index
                            current_video_index = x + video_start_with
                            save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                            cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                            logger.info(f"Checking the cache immediately after writing: {cached_check}")
                            playlist_indices.append(current_video_index)
                            playlist_msg_ids.append(video_msg.id)
                        else:
                            # Накапливаем ID частей для split видео
                            split_msg_ids.append(video_msg.id)
                    safe_edit_message_text(user_id, proc_msg_id,
                                          f"{info_text}\n\n{full_bar}   100.0%\n__Splitted part {p + 1} file uploaded__")
                    if p < len(caption_lst) - 1:
                        threading.Event().wait(2)
                    os.remove(splited_thumb_dir)
                    send_mediainfo_if_enabled(user_id, path_lst[p], message)
                    os.remove(path_lst[p])
                
                # Сохраняем все части split-видео в кэш после завершения цикла
                if split_msg_ids and not is_playlist:
                    # Удаляем дубликаты
                    split_msg_ids = list(dict.fromkeys(split_msg_ids))
                    logger.info(f"down_and_up: saving all split video parts to cache: {split_msg_ids}")
                    save_to_video_cache(url, quality_key, split_msg_ids, original_text=message.text or message.caption or "")
                os.remove(thumb_dir)
                os.remove(user_vid_path)
                success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
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
                        video_msg = send_videos(message, after_rename_abs_path, '' if force_no_title else original_video_title, duration, thumb_dir, info_text, proc_msg.id, full_video_title, tags_text_final)
                        try:
                            forwarded_msgs = safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                            logger.info(f"down_and_up: forwarded_msgs result: {forwarded_msgs}")
                            if forwarded_msgs:
                                logger.info(f"down_and_up: saving to cache with forwarded message IDs: {[m.id for m in forwarded_msgs]}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.extend([m.id for m in forwarded_msgs])
                                else:
                                    # For single videos, save to regular cache
                                    save_to_video_cache(url, quality_key, [m.id for m in forwarded_msgs], original_text=message.text or message.caption or "")
                            else:
                                logger.info(f"down_and_up: saving to cache with video_msg.id: {video_msg.id}")
                                if is_playlist:
                                    # For playlists, save to playlist cache with video index
                                    current_video_index = x + video_start_with
                                    save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                    cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                    logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                    playlist_indices.append(current_video_index)
                                    playlist_msg_ids.append(video_msg.id)
                                else:
                                    # For single videos, save to regular cache
                                    save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                        except Exception as e:
                            logger.error(f"Error forwarding video to logger: {e}")
                            logger.info(f"down_and_up: saving to cache with video_msg.id after error: {video_msg.id}")
                            if is_playlist:
                                # For playlists, save to playlist cache with video index
                                current_video_index = x + video_start_with
                                save_to_playlist_cache(get_clean_playlist_url(url), quality_key, [current_video_index], [video_msg.id], original_text=message.text or message.caption or "")
                                cached_check = get_cached_playlist_videos(get_clean_playlist_url(url), quality_key, [current_video_index])
                                logger.info(f"Checking the cache immediately after writing: {cached_check}")
                                playlist_indices.append(current_video_index)
                                playlist_msg_ids.append(video_msg.id)
                            else:
                                # For single videos, save to regular cache
                                save_to_video_cache(url, quality_key, [video_msg.id], original_text=message.text or message.caption or "")
                        safe_edit_message_text(user_id, proc_msg_id,
                            f"{info_text}\n{full_bar}   100.0%\n\n**🎞 Video duration:** __{TimeFormatter(duration * 1000)}__\n\n1 file uploaded.")
                        send_mediainfo_if_enabled(user_id, after_rename_abs_path, message)
                        os.remove(after_rename_abs_path)
                        if thumb_dir and os.path.exists(thumb_dir):
                            os.remove(thumb_dir)
                        threading.Event().wait(2)
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        send_to_all(message, f"❌ Error sending video: {str(e)}")
                        continue
        if successful_uploads == len(indices_to_download):
            success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
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
            save_to_playlist_cache(get_clean_playlist_url(url), quality_key, playlist_indices, playlist_msg_ids, original_text=message.text or message.caption or "")
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
            if (filename.endswith(('.part', '.ytdl', '.temp', '.tmp')) or
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
       allowed = max_total - len(ext)
       if allowed > 3:
          name = name[:allowed-3] + "..."
       else:
          name = name[:allowed]
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
                    f"{current_total_process}\nDownloading HLS stream: {frag_text}\n{bar}")

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
    tags = []
    tags_text = ''
    error_tag = None
    error_tag_example = None
    tag_part = after_playlist.strip()
    if tag_part:
        for raw in re.finditer(r'#([^#\s]+)', tag_part):
            tag = raw.group(1)
            # We check that the tag consists only of the permitted characters
            if not re.fullmatch(r'[\w\d_]+', tag, re.UNICODE):
                error_tag = tag
                # For example, show the user how the corrected tag would look like
                example = re.sub(r'[^\w\d_]', '_', tag, flags=re.UNICODE)
                error_tag_example = f'#{example}'
                break  # Interrupt the check after the first error
            tags.append(f'#{tag}')
        # We form Tags_text with spaces between tags
        tags_text = ' '.join(tags)
    # Return the motorcade with an error if it was found
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
#@reply_with_keyboard
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
    for tag in tags:
        if len(msg) + len(tag) + 1 > 4096:
            app.send_message(user_id, msg, reply_to_message_id=message.id)
            send_to_logger(message, msg)
            msg = ''
        msg += tag + '\n'
    if msg:
        app.send_message(user_id, msg, reply_to_message_id=message.id)
        send_to_logger(message, msg)

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
    Скачивает превью YouTube (maxresdefault/hqdefault) на диск в оригинальном размере.
    url — нужен для определения Shorts по ссылке (но теперь не используется).
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
    # Больше ничего не делаем — сохраняем оригинальный размер!

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
    # 1. Проверка домена
    clean_url = get_clean_url_for_tagging(url)
    domain_parts, _ = extract_domain_parts(clean_url)
    for dom in domain_parts:
        if dom in Config.WHITELIST:
            logger.info(f"is_porn: domain in WHITELIST: {dom}")
            return False
    if is_porn_domain(domain_parts):
        logger.info(f"is_porn: domain match: {domain_parts}")
        return True

    # 2. Подготовка текста
    title_lower       = title.lower()       if title       else ""
    description_lower = description.lower() if description else ""
    caption_lower     = caption.lower()     if caption     else ""
    if not (title_lower or description_lower or caption_lower):
        logger.info("is_porn: all text fields empty")
        return False

    # 3. Собираем единый текст для поиска
    combined = " ".join([title_lower, description_lower, caption_lower])
    logger.debug(f"is_porn combined text: '{combined}'")
    logger.debug(f"is_porn keywords: {PORN_KEYWORDS}")

    # 4. Готовим regex-паттерн со списком ключевых слов
    kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not kws:
        # нет ни одного валидного ключа
        return False

    # границы слов (\b) + флаг IGNORECASE
    pattern = re.compile(r"\b(" + "|".join(kws) + r")\b", flags=re.IGNORECASE)

    # 5. Ищем совпадение
    if pattern.search(combined):
        logger.info(f"is_porn: keyword match (regex): {pattern.pattern}")
        return True

    logger.info("is_porn: no keyword matches found")
    return False

@app.on_message(filters.command("split") & filters.private)
#@reply_with_keyboard
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
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="split_size|cancel")])
    keyboard = InlineKeyboardMarkup(buttons)
    app.send_message(user_id, "Choose max part size for video splitting:", reply_markup=keyboard)
    send_to_logger(message, "User opened /split menu.")

@app.on_callback_query(filters.regex(r"^split_size\|"))
#@reply_with_keyboard
def split_size_callback(app, callback_query):
    logger.info(f"[SPLIT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    if data == "cancel":
        callback_query.edit_message_text("🔚 Split size selection canceled.")
        callback_query.answer("✅ Split choice updated.")
        send_to_logger(callback_query.message, "Split selection canceled.")
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
        cookie_file = os.path.join(user_dir, os.path.basename(Config.COOKIE_FILE_PATH))
        if os.path.exists(cookie_file):
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

#@reply_with_keyboard
def ask_quality_menu(app, message, url, tags, playlist_start_index=1):
    user_id = message.chat.id
    proc_msg = None
    try:
        proc_msg = app.send_message(user_id, "Processing... ♻️", reply_to_message_id=message.id, reply_markup=get_main_reply_keyboard())
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
        popular = [144, 240, 360, 480, 540, 576, 720, 1080, 1440, 2160, 4320]
        # popular_sizes = [[256,144],[426,240],[640,360],[854,480],[960,540],[1024,576],[1280,720],[1920,1080],[2560,1440],[3840,2160],[7680,4320]]
        minside_size_dim_map = {}
        for f in info.get('formats', []):
            if f.get('vcodec', 'none') != 'none' and f.get('height') and f.get('width'):
                w = f['width']
                h = f['height']
                # Use the get_quality_by_min_side function to determine the quality
                quality_key = get_quality_by_min_side(w, h)
                if quality_key != "best":  # Exclude best from display
                    if f.get('filesize'):
                        size_mb = int(f['filesize']) // (1024*1024)
                    elif f.get('filesize_approx'):
                        size_mb = int(f['filesize_approx']) // (1024*1024)
                    else:
                        size_mb = None
                    if size_mb:
                        key = (quality_key, w, h)
                        minside_size_dim_map[key] = size_mb
        table_lines = []
        found_quality_keys = set()
        # Sort by quality from lowest to highest
        for (quality_key, w, h), size_val in sorted(minside_size_dim_map.items(), key=lambda x: sort_quality_key(x[0][0])):
            found_quality_keys.add(quality_key)
            size_str = f"{round(size_val/1024, 1)}GB" if size_val >= 1024 else f"{size_val}MB"
            dim_str = f" ({w}×{h})"
            scissors = ""
            if get_user_split_size(user_id):
                video_bytes = size_val * 1024 * 1024
                if video_bytes > get_user_split_size(user_id):
                    n_parts = (video_bytes + get_user_split_size(user_id) - 1) // get_user_split_size(user_id)
                    scissors = f" ✂️{n_parts}"
            if is_playlist and playlist_range:
                indices = list(range(playlist_range[0], playlist_range[1]+1))
                n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                total = len(indices)
                postfix = f" ({n_cached}/{total})"
                is_cached = n_cached > 0
            else:
                is_cached = quality_key in cached_qualities
                postfix = ""
            emoji = "🚀" if is_cached else "📹"
            table_lines.append(f"{emoji}  {quality_key}:  {size_str}{dim_str}{scissors}{postfix}")
        table_block = "\n".join(table_lines)
        # --- Forming caption ---
        cap = f"<b>{title}</b>\n"
        if tags_text:
            cap += f"{tags_text}\n"
        # Block with qualities
        if table_block:
            cap += f"\n<blockquote>{table_block}</blockquote>\n"
        # Hint as a separate code block at the very bottom
        hint = "<pre language=\"info\">📹 — Choose quality for new download.\n🚀 — Instant repost. Video is already saved.</pre>"
        cap += f"\n{hint}\n"
        buttons = []
        # Sort buttons by quality from lowest to highest
        for quality_key in sorted(found_quality_keys, key=sort_quality_key):
            if is_playlist and playlist_range:
                indices = list(range(playlist_range[0], playlist_range[1]+1))
                n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                total = len(indices)
                icon = "🚀" if n_cached > 0 else "📹"
                postfix = f" ({n_cached}/{total})" if total > 1 else ""
                button_text = f"{icon} {quality_key}{postfix}"
            else:
                icon = "🚀" if quality_key in cached_qualities else "📹"
                button_text = f"{icon} {quality_key}"
            buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        if not buttons and popular:
            for height in popular:
                quality_key = f"{height}p"
                # Find the file size for this quality
                size_val = None
                for (qk, w, h), size in minside_size_dim_map.items():
                    if qk == quality_key:
                        size_val = size
                        break
                
                if size_val is None:
                    continue
                    
                if is_playlist and playlist_range:
                    indices = list(range(playlist_range[0], playlist_range[1]+1))
                    n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                    total = len(indices)
                    icon = "🚀" if n_cached > 0 else "📹"
                    postfix = f" ({n_cached}/{total})" if total > 1 else ""
                    button_text = f"{icon} {quality_key}{postfix}"
                else:
                    icon = "🚀" if quality_key in cached_qualities else "📹"
                    button_text = f"{icon} {quality_key}"
                buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
        if not buttons:
            quality_key = "best"
            if is_playlist and playlist_range:
                indices = list(range(playlist_range[0], playlist_range[1]+1))
                n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
                total = len(indices)
                icon = "🚀" if n_cached > 0 else "📹"
                postfix = f" ({n_cached}/{total})" if total > 1 else ""
                button_text = f"{icon} Best Quality{postfix}"
            else:
                icon = "🚀" if quality_key in cached_qualities else "📹"
                button_text = f"{icon} Best Quality"
            buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}"))
            
            # Add "Try Another Qualities" button when no automatic qualities detected
            buttons.append(InlineKeyboardButton("🎛 Force Quality", callback_data=f"askq|try_manual"))
            
            # Add explanation when automatic quality detection fails
            autodiscovery_note = "<blockquote>⚠️ Available qualities could not be automatically detected. You can manually force a specific quality.</blockquote>"
            cap += f"\n{autodiscovery_note}\n"
        # --- Form rows of 3 buttons ---
        keyboard_rows = []
        for i in range(0, len(buttons), 3):
            keyboard_rows.append(buttons[i:i+3])
        # --- button mp3 ---
        quality_key = "mp3"
        if is_playlist and playlist_range:
            indices = list(range(playlist_range[0], playlist_range[1]+1))
            n_cached = get_cached_playlist_count(get_clean_playlist_url(url), quality_key, indices)
            total = len(indices)
            icon = "🚀" if n_cached > 0 else "🎵"
            postfix = f" ({n_cached}/{total})" if total > 1 else ""
            button_text = f"{icon} audio (mp3){postfix}"
        else:
            icon = "🚀" if quality_key in cached_qualities else "🎵"
            button_text = f"{icon} audio (mp3)"
        keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"askq|{quality_key}")])
        keyboard_rows.append([InlineKeyboardButton("🔙 Cancel", callback_data="askq|cancel")])
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        # cap already contains a hint and a table
        app.delete_messages(user_id, proc_msg.id)
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
        flood_msg = f"⚠️ Telegram has limited message sending.\n\n⏳ Please wait: {time_str}\n\nTo update timer send URL again 2 times."
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
#@reply_with_keyboard
def askq_callback(app, callback_query):
    logger.info(f"[ASKQ] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "cancel":
        callback_query.message.delete()
        callback_query.answer("Menu closed.")
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
        
        if url:
            tags = []
            caption_text = callback_query.message.caption
            if caption_text:
                tag_matches = re.findall(r'#\S+', caption_text)
                if tag_matches:
                    tags = tag_matches
            callback_query.message.delete()
            ask_quality_menu(app, original_message, url, tags)
        else:
            callback_query.answer("❌ Error: URL not found.", show_alert=True)
            callback_query.message.delete()
        return
    
    # Handle manual quality selection
    if data.startswith("manual_"):
        quality = data.replace("manual_", "")
        callback_query.answer(f"Downloading {quality}...")
        
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
        
        callback_query.message.delete()
        
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
            _, video_start_with, video_end_with, playlist_name, _, _, _ = extract_url_range_tags(original_text)
            video_count = video_end_with - video_start_with + 1
            down_and_up(app, original_message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=False, format_override=format_override, quality_key=quality)
        else:
            down_and_up_with_format(app, original_message, url, format_override, tags_text, quality_key=quality)
        return

    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer("❌ Error: Original message not found. It might have been deleted. Please send the link again.", show_alert=True)
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
        callback_query.answer("❌ Error: Original URL not found. Please send the link again.", show_alert=True)
        callback_query.message.delete()
        return

    tags = []
    caption_text = callback_query.message.caption
    if caption_text:
        tag_matches = re.findall(r'#\S+', caption_text)
        if tag_matches:
            tags = tag_matches
    tags_text = ' '.join(tags)

    callback_query.message.delete()

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
    message_ids = get_cached_message_ids(url, data)
    if message_ids:
        callback_query.answer("🚀 Found in cache! Forwarding instantly...", show_alert=False)
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
            logger.error(f"Error forwarding from cache: {e}")
            save_to_video_cache(url, data, [], clear=True)
            app.send_message(user_id, "⚠️ Failed to get video from cache, starting a new download...", reply_to_message_id=original_message.id)
            askq_callback_logic(app, callback_query, data, original_message, url, tags_text)
        return
    askq_callback_logic(app, callback_query, data, original_message, url, tags_text)


def askq_callback_logic(app, callback_query, data, original_message, url, tags_text):
    user_id = callback_query.from_user.id
    tags = tags_text.split() if tags_text else []
    if data == "mp3":
        callback_query.answer("Downloading audio...")
        # Extract playlist parameters from the original message
        full_string = original_message.text or original_message.caption or ""
        _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
        video_count = video_end_with - video_start_with + 1
        down_and_audio(app, original_message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)
        return
    
    # Logic for forming the format with the real height
    if data == "best":
        callback_query.answer("Downloading best quality...")
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
            callback_query.answer(f"Downloading {data}...")
        except ValueError:
            callback_query.answer("Unknown quality.")
            return
    
    down_and_up_with_format(app, original_message, url, fmt, tags_text, quality_key=quality_key)

#@reply_with_keyboard
def show_manual_quality_menu(app, callback_query):
    """Show manual quality selection menu when automatic detection fails"""
    user_id = callback_query.from_user.id
    
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
            button_text = f"{icon} {quality}{postfix}"
        else:
            icon = "🚀" if quality in cached_qualities else "📹"
            button_text = f"{icon} {quality}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality}"))
    
    # Add Best Quality button
    if is_playlist and playlist_range:
        indices = list(range(playlist_range[0], playlist_range[1]+1))
        n_cached = get_cached_playlist_count(get_clean_playlist_url(url), "best", indices)
        total = len(indices)
        icon = "🚀" if n_cached > 0 else "📹"
        postfix = f" ({n_cached}/{total})" if total > 1 else ""
        button_text = f"{icon} Best Quality{postfix}"
    else:
        icon = "🚀" if "best" in cached_qualities else "📹"
        button_text = f"{icon} Best Quality"
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
        icon = "🚀" if n_cached > 0 else "🎵"
        postfix = f" ({n_cached}/{total})" if total > 1 else ""
        button_text = f"{icon} audio (mp3){postfix}"
    else:
        icon = "🚀" if quality_key in cached_qualities else "🎵"
        button_text = f"{icon} audio (mp3)"
    keyboard_rows.append([InlineKeyboardButton(button_text, callback_data=f"askq|manual_{quality_key}")])
    
    # Add Back and Cancel buttons
    keyboard_rows.append([
        InlineKeyboardButton("🔙 Back", callback_data="askq|manual_back"),
        InlineKeyboardButton("❌ Cancel", callback_data="askq|cancel")
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
#@reply_with_keyboard
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
    video_title = info_dict.get("title")
    video_description = info_dict.get("description")
    video_caption = info_dict.get("caption") if info_dict else None
    if is_porn(url, video_title, video_description, video_caption):
        if '#porn' not in seen:
            final_tags.append('#porn')
            seen.add('#porn')
    result = ' '.join(final_tags)
    logger.info(f"Generated final tags for '{info_dict.get('title', 'N/A')}': \"{result}\"")
    return result

# --- new functions for caching ---
def get_url_hash(url: str) -> str:
    """Returns a hash of the URL for use as a cache key."""
    import hashlib
    hash_result = hashlib.md5(url.encode()).hexdigest()
    logger.info(f"get_url_hash: '{url}' -> '{hash_result}'")
    return hashlib.md5(url.encode()).hexdigest()


def save_to_video_cache(url: str, quality_key: str, message_ids: list, clear: bool = False, original_text: str = None):
    """Saves message IDs to cache for two YouTube link variants (long/short) at once."""
    logger.info(
        f"save_to_video_cache called: url={url}, quality_key={quality_key}, message_ids={message_ids}, clear={clear}, original_text={original_text}")
    if not quality_key:
        logger.warning(f"save_to_video_cache: quality_key is empty, skipping cache save for URL: {url}")
        return
    # Check if this is a playlist with range - if so, skip cache
    if original_text and is_playlist_with_range(original_text):
        logger.info(f"Playlist with range detected, skipping cache save for URL: {url}")
        return

    try:
        urls = [normalize_url_for_cache(url)]
        # If it's YouTube, add both options
        if is_youtube_url(url):
            urls.append(normalize_url_for_cache(youtube_to_short_url(url)))
            urls.append(normalize_url_for_cache(youtube_to_long_url(url)))
        logger.info(f"save_to_video_cache: normalized URLs: {urls}")
        for u in set(urls):
            url_hash = get_url_hash(u)
            cache_ref = db.child(Config.VIDEO_CACHE_DB_PATH).child(url_hash)
            if clear:
                cache_ref.child(quality_key).remove()
                logger.info(f"Cache cleared for URL hash {url_hash}, quality {quality_key}")
                continue
            if not message_ids:
                logger.warning(f"save_to_video_cache: message_ids is empty for URL: {url}, quality: {quality_key}")
                continue
            
            # Упрощенная логика для кэширования
            if len(message_ids) == 1:
                # Одиночное видео - сохраняем как есть
                cache_ref.child(quality_key).set(str(message_ids[0]))
                logger.info(f"Saved single video to cache for URL hash {url_hash}, quality {quality_key}, msg_id {message_ids[0]}")
            else:
                # Split видео (множественные части) - сохраняем все ID через запятую
                ids_string = ",".join(map(str, message_ids))
                cache_ref.child(quality_key).set(ids_string)
                logger.info(f"Saved split video to cache for URL hash {url_hash}, quality {quality_key}, msg_ids {ids_string} ({len(message_ids)} parts)")
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")


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
            ids_string = db.child(Config.VIDEO_CACHE_DB_PATH).child(url_hash).child(quality_key).get().val()
            logger.info(f"get_cached_message_ids: raw value from Firebase: {ids_string} (type: {type(ids_string)})")
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
        data = db.child(Config.VIDEO_CACHE_DB_PATH).child(url_hash).get().val()
        if data:
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
        logger.warning(
            f"save_to_playlist_cache: quality_key is empty, skipping cache save for playlist: {playlist_url}")
        return
    if not hasattr(Config,
                   'PLAYLIST_CACHE_DB_PATH') or not Config.PLAYLIST_CACHE_DB_PATH or Config.PLAYLIST_CACHE_DB_PATH.strip() in (
            '', '/', '.'):
        logger.error(
            f"save_to_playlist_cache: PLAYLIST_CACHE_DB_PATH is empty or invalid! Skipping cache write for playlist: {playlist_url}")
        return
    try:
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))))
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))))
        logger.info(f"save_to_playlist_cache: normalized URLs: {urls}")
        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"save_to_playlist_cache: using URL hash: {url_hash}")
            if clear:
                # Delete the entire quality branch
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{quality_key}").remove()
                logger.info(f"Playlist cache cleared for URL hash {url_hash}, quality {quality_key}")
                continue
            if not message_ids or not video_indices:
                logger.warning(
                    f"save_to_playlist_cache: message_ids or video_indices is empty for playlist: {playlist_url}, quality: {quality_key}")
                continue
            for i, msg_id in zip(video_indices, message_ids):
                cache_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{quality_key}/{str(i)}"
                logger.info(f"save_to_playlist_cache: saving to path: {cache_path}, msg_id: {msg_id}")
                db_child_by_path(db, cache_path).set(str(msg_id))
            logger.info(
                f"Saved to playlist cache for URL hash {url_hash}, quality {quality_key}, indices: {video_indices}, msg_ids: {message_ids}")
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
    if not hasattr(Config,
                   'PLAYLIST_CACHE_DB_PATH') or not Config.PLAYLIST_CACHE_DB_PATH or Config.PLAYLIST_CACHE_DB_PATH.strip() in (
            '', '/', '.'):
        logger.error(
            f"get_cached_playlist_videos: PLAYLIST_CACHE_DB_PATH is empty or invalid! Skipping cache read for playlist: {playlist_url}")
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

                # Check each requested index separately
                for index in requested_indices:
                    index_str = str(index)
                    try:
                        cache_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{qk}/{index_str}"
                        msg_id = db_child_by_path(db, cache_path).get().val()
                        if msg_id is not None:
                            found[index] = int(msg_id)
                            logger.info(
                                f"get_cached_playlist_videos: found cached video for index {index} (quality={qk}): {msg_id}")
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
        # Get all the quality keys inside the url_hash folder
        data = db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}").get().val()
        if data:
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
    for part in path.split("/"):
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
                if indices is not None:
                    # For large ranges, we use a fast count
                    if len(indices) > 100:
                        try:
                            data = db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{qk}").get().val()
                            if data and isinstance(data, dict):
                                # Count only indices from the requested range
                                cached_count = sum(
                                    1 for index in indices if str(index) in data and data[str(index)] is not None)
                                logger.info(
                                    f"get_cached_playlist_count: fast count for large range: {cached_count} cached videos")
                                return cached_count
                        except Exception as e:
                            logger.error(f"get_cached_playlist_count: error in fast count: {e}")
                            continue
                    else:
                        # For small ranges, check each index separately
                        for index in indices:
                            index_str = str(index)
                            val = db_child_by_path(db,
                                                   f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{qk}/{index_str}").get().val()
                            if val is not None:
                                cached_count += 1
                                logger.info(
                                    f"get_cached_playlist_count: found cached video for index {index} (quality={qk}): {val}")
                else:
                    # Get all quality data and count non-empty records
                    try:
                        data = db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{qk}").get().val()
                        if data:
                            if isinstance(data, dict):
                                cached_count = len(data)
                            elif isinstance(data, list):
                                # If the data is a list, count non-empty elements
                                cached_count = sum(1 for item in data if item is not None)
                            else:
                                logger.warning(
                                    f"get_cached_playlist_count: unexpected data type for url_hash={url_hash}, quality={qk}, type={type(data)}")
                                continue
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


app.run()
