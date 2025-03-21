import pyrebase
import re
import os
import shutil
import logging
import threading
from pyrogram import Client, filters
from pyrogram import enums
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import requests
import math
import time
import threading
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import subprocess
import signal
import sys
from config import Config

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

################################################################################################
# Global starting point list (do not modify)
starting_point = []

# Global dictionary to track active downloads and lock for thread-safe access
active_downloads = {}
active_downloads_lock = threading.Lock()

# Global dictionary to track playlist errors and lock for thread-safe access
playlist_errors = {}
playlist_errors_lock = threading.Lock()

# Helper function to check available disk space
def check_disk_space(path, required_bytes):
    """
    Check if there's enough disk space available at the specified path.

    Args:
        path (str): Path to check
        required_bytes (int): Required bytes of free space

    Returns:
        bool: True if enough space is available, False otherwise
    """
    try:
        total, used, free = shutil.disk_usage(path)
        if free < required_bytes:
            logger.warning(f"Not enough disk space. Required: {humanbytes(required_bytes)}, Available: {humanbytes(free)}")
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

################################################################################################

# Pyrogram App Initialization
app = Client(
    "magic",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

##############################################################################################################################
##############################################################################################################################

@app.on_message(filters.command("start") & filters.private)

def command1(app, message):
    if int(message.chat.id) in Config.ADMIN:
        send_to_user(message, "Welcome Master 🥷")
    else:
        check_user(message)
        app.send_message(
            message.chat.id, f"Hello {message.chat.first_name},\n \n__This bot🤖 can download any videos into telegram directly.😊 For more information press **/help**__ 👈\n \n {Config.CREDITS_MSG}")
        send_to_logger(message, f"{message.chat.id} - user started the bot")

@app.on_message(filters.command("help"))

def command2(app, message):
    app.send_message(message.chat.id, (Config.HELP_MSG),
                     parse_mode=enums.ParseMode.MARKDOWN)
    send_to_logger(message, f"Send help txt to user")

def create_directory(path):
    # Create The Directory (And All Intermediate Directories) IF Its Not Exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# Command to Set Browser Cooks
@app.on_message(filters.command("cookies_from_browser") & filters.private)

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
        "safari": None,  # Not support on linux
        "vivaldi": "~/.config/vivaldi/",
        "whale": ["~/.config/Whale/", "~/.config/naver-whale/"]
    }

    buttons = []
    for browser, path in browsers.items():
        if browser == "safari":
            exists = False
        elif isinstance(path, list):
            exists = any(os.path.exists(os.path.expanduser(p)) for p in path)
        else:
            exists = os.path.exists(os.path.expanduser(path))
        emoji = "✅" if exists else "☑️"
        display_name = browser.capitalize()  # Capitalize the first letter
        button = InlineKeyboardButton(f"{emoji} {display_name}", callback_data=f"browser_choice|{browser}")
        buttons.append([button])

    # Add a Cancel Button to Cancel The Selection
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="browser_choice|cancel")])
    keyboard = InlineKeyboardMarkup(buttons)

    app.send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard
    )
    send_to_logger(message, "Browser selection keyboard sent.")

# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))

def browser_choice_callback(app, callback_query):
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
        "safari": None,
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
            send_to_logger(callback_query.message, f"Failed to save cookies using browser {browser_option}: {result.stderr}")
    else:
        callback_query.edit_message_text(f"✅ Cookies saved using browser: {browser_option}")
        send_to_logger(callback_query.message, f"Cookies saved using browser: {browser_option}")

    callback_query.answer("✅ Browser choice updated.")

# Command to Download Audio from a Video url
@app.on_message(filters.command("audio") & filters.private)

def audio_command_handler(app, message):
    user_id = message.chat.id
    # If the user has already been launched by the process, we answer the rein and go out
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return

    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # Command expects: /audio <url>
    if len(message.command) < 2:
        send_to_user(message, "Please provide the URL of the video to download the audio.")
        return
    url = message.command[1]  # We take the URL from the arguments of Command
    down_and_audio(app, message, url)

# Command /Format Handler
@app.on_message(filters.command("format") & filters.private)

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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💻<=4k (best for desktop TG app)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱<=FullHD (best for mobile TG app)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈bestvideo+bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            [InlineKeyboardButton("📉best (no ffmpeg)", callback_data="format_option|best")],
            [InlineKeyboardButton("Others", callback_data="format_option|others")],
            [InlineKeyboardButton("🎚 custom", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="format_option|cancel")]
        ])
        app.send_message(
            user_id,
            "Select a format option or send a custom one using `/format <format_string>`:",
            reply_markup=keyboard
        )
        send_to_logger(message, "Format menu sent.")

# Callbackquery Handler for /Format Menu Selection
@app.on_callback_query(filters.regex(r"^format_option\|"))

def format_option_callback(app, callback_query):
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
            [InlineKeyboardButton("💻<=4k (best for desktop TG app)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱<=FullHD (best for mobile TG app)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈bestvideo+bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            [InlineKeyboardButton("📉best (no ffmpeg)", callback_data="format_option|best")],
            [InlineKeyboardButton("Others", callback_data="format_option|others")],
            [InlineKeyboardButton("🎚 custom", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="format_option|cancel")]
        ])
        callback_query.edit_message_text("Select a format option or send a custom one using `/format <format_string>`:", reply_markup=main_keyboard)
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
        chosen_format = "bestvideo+bestaudio/best"
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

#####################################################################################

# Checking user is Blocked or not

def is_user_blocked(message):
    blocked = db.child("bot").child("tgytdlp_bot").child("blocked_users").get().each()
    blocked_users = [int(b_user.key()) for b_user in blocked]
    if int(message.chat.id) in blocked_users:
        send_to_user(message, "🚫 You are banned from the bot!")
        return True
    else:
        return False

# Cheking Users are in Main User Directory in DB

def check_user(message):
    user_id_str = str(message.chat.id)
    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
    create_directory(user_dir)

    # Copy Cookie.txt from the Project Root to the User's Folder If Not Alread Present
    cookie_src = os.path.join(os.getcwd(), "cookie.txt")
    cookie_dest = os.path.join(user_dir, os.path.basename(Config.COOKIE_FILE_PATH))
    if os.path.exists(cookie_src) and not os.path.exists(cookie_dest):
        import shutil
        shutil.copy(cookie_src, cookie_dest)

    # Register the User in the Database If Not Alread Registered
    user_db = db.child("bot").child("tgytdlp_bot").child("users").get().each()
    users = [user.key() for user in user_db] if user_db else []
    if user_id_str not in users:
        data = {"ID": message.chat.id, "timestamp": math.floor(time.time())}
        db.child("bot").child("tgytdlp_bot").child("users").child(user_id_str).set(data)

#####################################################################################

# Checking Actions
# Text Message Handler for General Commands
@app.on_message(filters.text & filters.private)

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

    # /Clean Command
    if Config.CLEAN_COMMAND in text:
        remove_media(message)
        send_to_all(message, "🗑 All files are removed.")
        return

    # /USAGE Command
    if Config.USAGE_COMMAND in text:
        get_user_log(app, message)
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

def remove_media(message):
    dir = f'./users/{str(message.chat.id)}'
    if not os.path.exists(dir):
        logger.warning(f"Directory {dir} does not exist, nothing to remove")
        return

    allfiles = os.listdir(dir)

    file_extensions = [
        '.mp4', '.mkv', '.mp3', '.m4a', '.jpg', '.jpeg', '.part', '.ytdl',
        '.txt', '.ts', '.m3u8', '.webm', '.wmv', '.avi', '.mpeg', '.wav'
    ]

    for extension in file_extensions:
        if isinstance(extension, tuple):
            # Handle multiple extensions
            files = [fname for fname in allfiles if any(fname.endswith(ext) for ext in extension)]
        else:
            # Handle single extension
            files = [fname for fname in allfiles if fname.endswith(extension)]

        for file in files:
            # Skip special files like cookie.txt and logs.txt and format.txt
            if extension == '.txt' and file in ['cookie.txt', 'logs.txt', 'format.txt']:
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
        txt_format = f"Logs of {Config.BOT_NAME_FOR_USERS}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n \n" +\
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
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " +\
            path +\
            f":\n \n" +\
            '\n'.join(modified_lst)
    else:
        temp = []
        for j in range(no_of_users_to_display):
            temp.append(modified_lst[((j+1) * -1)])
        temp.sort(key=str.lower)
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " +\
            path +\
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
            send_to_user(message, "🚫 Admin cannot delete an admin")
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
        send_to_user(message, "🚫 Sorry! You are not an admin")

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
        send_to_user(message, "🚫 Sorry! You are not an admin")

# Check Runtime

def check_runtime(message):
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        now = TimeFormatter(now)
        send_to_user(message, f"⏳ __Bot running time -__ **{now}**")
    pass

# SEND COOKIE VIA Document
@app.on_message(filters.document & filters.private)

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
        send_to_all(message, "**✅ Cookie file downloaded and saved in your folder.**")
        send_to_logger(message, f"Cookie file downloaded for user {user_id}.")
    else:
        send_to_all(message, "❌ Cookie URL is not available!")
        send_to_logger(message, f"Failed to download cookie file for user {user_id}.")

# Caption Editor for Videos
@app.on_message(filters.text & filters.private)

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

def checking_cookie_file(app, message):
    user_id = str(message.chat.id)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    file_path = os.path.join("users", user_id, cookie_filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as cookie:
            cookie_content = cookie.read()
        if cookie_content.startswith("# Netscape HTTP Cookie File"):
            send_to_all(message, "✅ Cookie file exists and has correct format")
            send_to_logger(message, "Cookie file exists and has correct format.")
        else:
            send_to_all(message, "⚠️ Cookie file exists but has incorrect format")
            send_to_logger(message, "Cookie file exists but has incorrect format.")
    else:
        send_to_all(message, "❌ Cookie file is not found.")
        send_to_logger(message, "Cookie file not found.")

# Updating The Cookie File.

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
        send_to_all(message, f"**✅ Cookie successfully updated:**\n`{final_cookie}`")
        send_to_logger(message, f"Cookie file updated for user {user_id}.")
    else:
        send_to_all(message, "**❌ Not a valid cookie.**")
        send_to_logger(message, f"Invalid cookie content provided by user {user_id}.")

# URL Extractor
@app.on_message(filters.text & filters.private)

def video_url_extractor(app, message):
    global active_downloads
    check_user(message)
    user_id = message.chat.id
    with playlist_errors_lock:
        keys_to_remove = [k for k in playlist_errors if k.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del playlist_errors[key]

    # If the user has already been launched by the process, we answer the rein and go out
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
    full_string = message.text
    if ("https://" in full_string) or ("http://" in full_string):
        users_first_name = message.chat.first_name
        send_to_logger(message, f"User entered a **url**\n **user's name:** {users_first_name}\nURL: {full_string}")
        for j in range(len(Config.PORN_LIST)):
            if Config.PORN_LIST[j] in full_string:
                send_to_all(message, "User entered a porn content. Cannot be downloaded.")
                return
        url_with_everything = full_string.split("*")
        url = url_with_everything[0]
        if len(url_with_everything) < 3:
            video_count = 1
            video_start_with = 1
            playlist_name = False
        elif len(url_with_everything) == 3:
            video_count = (int(url_with_everything[2]) - int(url_with_everything[1]) + 1)
            video_start_with = int(url_with_everything[1])
            playlist_name = False
        else:
            video_start_with = int(url_with_everything[1])
            playlist_name = f"{url_with_everything[3]}"
            video_count = (int(url_with_everything[2]) - int(url_with_everything[1]) + 1)

        # Сброс флага ошибок для нового запроса по плейлисту
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        down_and_up(app, message, url, playlist_name, video_count, video_start_with)
    else:
        send_to_all(message, f"**User entered like this:** {full_string}\n{Config.ERROR1}")

#############################################################################################

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
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)

# Send Message to All ...

def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # Print (user_id, "-", msg)
    safe_send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)

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

def send_videos(message, video_abs_path, caption, duration, thumb_file_path, info_text, msg_id):
    """
    Sends the video using send_video (not as document) with streaming support.
    Updates progress via the progress_bar callback.
    """
    stage = "Uploading Video... 📤"
    send_to_logger(message, info_text)
    user_id = message.chat.id
    video_msg = app.send_video(
        chat_id=user_id,
        video=video_abs_path,
        caption=caption,
        duration=duration,
        width=640,
        height=360,
        supports_streaming=True,
        thumb=thumb_file_path,
        progress=progress_bar,
        progress_args=(user_id, msg_id, f"{info_text}\n**Video duration:** __{TimeFormatter(duration * 1000)}__\n\n__{stage}__")
    )
    return video_msg

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
    clip.save_frame(thumb_dir, t=2)
    clip.close()
    return duration, thumb_dir

def get_duration_thumb(message, dir_path, video_path, thumb_name):
    """
    Captures a thumbnail at 2 seconds into the video and retrieves video duration.
    Forces overwriting existing thumbnail with the '-y' flag.

    Args:
        message: The message object
        dir_path: Directory path for the thumbnail
        video_path: Path to the video file
        thumb_name: Name for the thumbnail

    Returns:
        tuple: (duration, thumbnail_path) or None if error
    """
    thumb_dir = os.path.abspath(os.path.join(dir_path, thumb_name + ".jpg"))

    # FFMPEG Command with -y Flag to overwrite Thumbnail File
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ss", "2",         # Seek to 2 Seconds
        "-vframes", "1",    # Capture 1 Frame
        thumb_dir
    ]

    # FFPROBE COMMAND to GET Video Duration
    ffprobe_command = [
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

        # Run ffmpeg command to create thumbnail
        ffmpeg_result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        if ffmpeg_result.returncode != 0:
            logger.error(f"Error creating thumbnail: {ffmpeg_result.stderr}")

        # Run ffprobe command to get duration
        result = subprocess.check_output(ffprobe_command, stderr=subprocess.STDOUT, universal_newlines=True)

        try:
            duration = int(float(result))
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing video duration: {e}, result was: {result}")
            duration = 0

        # Verify thumbnail was created
        if not os.path.exists(thumb_dir):
            logger.warning(f"Thumbnail not created at {thumb_dir}, using default")
            # Create a blank thumbnail as fallback
            create_default_thumbnail(thumb_dir)

        return duration, thumb_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"Command execution error: {e.stderr if hasattr(e, 'stderr') else e}")
        send_to_all(message, f"❌ Error processing video: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing video: {e}")
        send_to_all(message, f"❌ Error processing video: {e}")
        return None

def create_default_thumbnail(thumb_path):
    """Create a default thumbnail when normal thumbnail creation fails"""
    try:
        # Create a 640x360 black image
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=640x360",
            "-frames:v", "1",
            thumb_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Created default thumbnail at {thumb_path}")
    except Exception as e:
        logger.error(f"Failed to create default thumbnail: {e}")

def write_logs(message, video_url, video_title):
    ts = str(math.floor(time.time()))
    data = {"ID": str(message.chat.id), "timestamp": ts,
            "name": message.chat.first_name, "urls": str(video_url), "title": video_title}
    db.child("bot").child("tgytdlp_bot").child("logs").child(str(message.chat.id)).child(str(ts)).set(data)
    logger.info("Log for user added")
#####################################################################################
#####################################################################################

#########################################
# Down_and_audio function
#########################################

def down_and_audio(app, message, url):
    user_id = message.chat.id
    # Logging a request for downloading audio
    send_to_logger(message, f"Audio download requested:\nURL: {url}")

    # Checking the active process and sending a reference if loading is already underway
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return

    set_active_download(user_id, True)
    proc_msg = None
    proc_msg_id = None
    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    anim_thread = None
    stop_anim = threading.Event()
    audio_file = None  # Initialize audio_file variable

    try:
        # Check if there's enough disk space (estimate 500MB per audio file)
        user_folder = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_folder)

        if not check_disk_space(user_folder, 500 * 1024 * 1024):
            send_to_user(message, "❌ Not enough disk space to download the audio.")
            return

        proc_msg = app.send_message(user_id, "Processing... ♻️")
        proc_msg_id = proc_msg.id
        check_user(message)

        status_msg = app.send_message(user_id, "🎧 Audio is processing...")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages at once
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        anim_thread = start_hourglass_animation(user_id, hourglass_msg_id, stop_anim)

        cookie_file = os.path.join(user_folder, os.path.basename(Config.COOKIE_FILE_PATH))
        ytdl_opts = {
            'format': 'ba',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'extractaudio': True,
            'noplaylist': True,
            'cookiefile': cookie_file,
            'outtmpl': os.path.join(user_folder, "%(title)s.%(ext)s"),
            'progress_hooks': [],
        }
        last_update = 0
        def progress_hook(d):
            nonlocal last_update
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
                    safe_edit_message_text(user_id, proc_msg_id, f"Downloading audio:\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "finished":
                try:
                    full_bar = "🟩" * 10
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"Downloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "error":
                try:
                    safe_edit_message_text(user_id, proc_msg_id, "Error occurred during audio download.")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
                last_update = current_time

        ytdl_opts['progress_hooks'].append(progress_hook)

        try:
            with YoutubeDL(ytdl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as ytdl_error:
            logger.error(f"YouTube-DL error: {ytdl_error}")
            send_to_user(message, f"❌ Failed to download audio: {ytdl_error}")
            return

        audio_title = info.get("title", "audio")
        # Sanitize the audio title for file naming
        audio_title = sanitize_filename(audio_title)
        audio_file = os.path.join(user_folder, audio_title + ".mp3")
        if not os.path.exists(audio_file):
            files = [f for f in os.listdir(user_folder) if f.endswith(".mp3")]
            if files:
                audio_file = os.path.join(user_folder, files[0])
            else:
                send_to_user(message, "Audio file not found after download.")
                return

        try:
            full_bar = "🟩" * 10
            safe_edit_message_text(user_id, proc_msg_id, f"Uploading audio file...\n{full_bar}   100.0%")
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")

        # Send audio and save the message object for repost
        try:
            audio_msg = app.send_audio(chat_id=user_id, audio=audio_file, caption=f"{audio_title}")
            # Reposting final audio message to the log channel
            safe_forward_messages(Config.LOGS_ID, user_id, [audio_msg.id])
        except Exception as send_error:
            logger.error(f"Error sending audio: {send_error}")
            send_to_user(message, f"❌ Failed to send audio: {send_error}")
            return

        try:
            full_bar = "🟩" * 10
            success_msg = f"✅ Audio successfully downloaded and sent.\n\n{Config.CREDITS_MSG}"
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
        except Exception as e:
            logger.error(f"Error updating final status: {e}")

        send_to_logger(message, success_msg)

    except Exception as e:
        logger.error(f"Error in audio download: {e}")
        send_to_user(message, f"❌ Failed to download audio: {e}")
        try:
            if proc_msg_id:
                safe_edit_message_text(user_id, proc_msg_id, f"Error: {e}")
        except Exception as edit_error:
            logger.error(f"Error editing message on exception: {edit_error}")
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

        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            logger.error(f"Failed to delete file {audio_file}: {e}")

        set_active_download(user_id, False)

#########################################
# Download_and_up function
#########################################

def down_and_up(app, message, url, playlist_name, video_count, video_start_with):
    user_id = message.chat.id
    # Logging a video download request
    send_to_logger(message, f"Video download requested:\nURL: {url}\nPlaylist: {playlist_name}\nCount: {video_count}, Start: {video_start_with}")

    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return

    set_active_download(user_id, True)
    error_message = ""
    proc_msg = None
    proc_msg_id = None
    status_msg = None
    status_msg_id = None
    hourglass_msg = None
    hourglass_msg_id = None
    anim_thread = None
    stop_anim = threading.Event()

    try:
        # Check if there's enough disk space (estimate 2GB per video)
        user_dir_name = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_dir_name)

        # We only need disk space for one video at a time, since files are deleted after upload
        if not check_disk_space(user_dir_name, 2 * 1024 * 1024 * 1024):
            send_to_user(message, f"❌ Not enough disk space to download videos.")
            return

        proc_msg = app.send_message(user_id, "Processing... ♻️")
        proc_msg_id = proc_msg.id
        check_user(message)

        # Сброс флага ошибок для нового запуска плейлиста
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]


        custom_format_path = os.path.join(user_dir_name, "format.txt")
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
                {'format': 'bestvideo+bestaudio/best',
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

        def progress_func(d):
            nonlocal last_update
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
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{bar}   {percent:.1f}%")
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            elif d.get("status") == "error":
                logger.error("Error occurred during download.")
                send_to_all(message, "❌ Sorry... Some error occurred during download.")
            last_update = current_time

        successful_uploads = 0

        def try_download(url, attempt_opts):
            nonlocal current_total_process
            common_opts = {
                'cookiefile': os.path.join("users", str(user_id), os.path.basename(Config.COOKIE_FILE_PATH)),
                'playlist_items': str(current_index + video_start_with),
                'outtmpl': os.path.join(user_dir_name, "%(title)s.%(ext)s")
            }
            is_hls = ("m3u8" in url.lower())
            if not is_hls:
                common_opts['progress_hooks'] = [progress_func]
            ytdl_opts = {**common_opts, **attempt_opts}
            try:
                with YoutubeDL(ytdl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                if "entries" in info_dict:
                    entries = info_dict["entries"]
                    if len(entries) > 1:  # Если видео в плейлисте больше одного
                        if current_index < len(entries):
                            info_dict = entries[current_index]
                        else:
                            raise Exception(f"Video index {current_index} out of range (total {len(entries)})")
                    else:
                        # Если всего одно видео в плейлисте, просто скачиваем его
                        info_dict = entries[0]  # Просто берём первое видео

                if ("m3u8" in url.lower()) or (info_dict.get("protocol") == "m3u8_native"):
                    is_hls = True
                    if "format" in ytdl_opts:
                        del ytdl_opts["format"]
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
                with YoutubeDL(ytdl_opts) as ydl:
                    if is_hls:
                        cycle_stop = threading.Event()
                        cycle_thread = start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop)
                        try:
                            with YoutubeDL(ytdl_opts) as ydl:
                                ydl.download([url])
                        finally:
                            cycle_stop.set()
                            cycle_thread.join(timeout=1)
                    else:
                        with YoutubeDL(ytdl_opts) as ydl:
                            ydl.download([url])
                try:
                    safe_edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    logger.error(f"Final progress update error: {e}")
                return info_dict
            except Exception as e:
                nonlocal error_message
                error_message = str(e)
                logger.error(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
                return None


        for x in range(video_count):
            current_index = x
            total_process = f"""
**📶 Total Progress**
> **Video:** {x + 1} / {video_count}
"""

            current_total_process = total_process

            # Определяем rename_name на основе входящего playlist_name:
            if playlist_name and playlist_name.strip():
                # Явно задано новое имя для плейлиста – используем его
                rename_name = sanitize_filename(f"{playlist_name.strip()} - Part {x + video_start_with}")
            else:
                # Новое имя не задано – извлекаем название из метаданных
                rename_name = None

            info_dict = None
            for attempt in attempts:
                info_dict = try_download(url, attempt)
                if info_dict is not None:
                    break

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
            video_title = info_dict.get("title", None)
            video_title = sanitize_filename(video_title) if video_title else "video"

            # Если rename_name не задано, устанавливаем его равным video_title
            if rename_name is None:
                rename_name = video_title

            info_text = f"""
{total_process}

**📋 Video Info**
> **Number:** {x + video_start_with}
> **Title:** {video_title}
> **Caption:** {rename_name}
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
                send_to_all(message, "❌ File not found after download.")
                break

            downloaded_file = files[0]
            write_logs(message, url, downloaded_file)

            if rename_name == video_title:
                caption_name = video_title
                final_name = downloaded_file
            else:
                ext = os.path.splitext(downloaded_file)[1]
                final_name = rename_name + ext
                caption_name = rename_name
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
                    caption_name = video_title

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
            result = get_duration_thumb(message, dir_path, user_vid_path, sanitize_filename(caption_name))
            if result is None:
                send_to_all(message, "❌ Failed to get video duration and thumbnail.")
                break
            duration, thumb_dir = result

            video_size_in_bytes = os.path.getsize(user_vid_path)
            video_size = humanbytes(int(video_size_in_bytes))
            max_size = 1950000000  # 1.95 GB - close to Telegram's 2GB limit with 50MB safety margin
            if int(video_size_in_bytes) > max_size:
                safe_edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n\n{full_bar}   100.0%\n__⚠️ Your video size ({video_size}) is too large.__\n__Splitting file...__ ✂️")
                returned = split_video_2(dir_path, sanitize_filename(caption_name), after_rename_abs_path, int(video_size_in_bytes), max_size, duration)
                caption_lst = returned.get("video")
                path_lst = returned.get("path")
                for p in range(len(caption_lst)):
                    part_result = get_duration_thumb(message, dir_path, path_lst[p], sanitize_filename(caption_lst[p]))
                    if part_result is None:
                        continue
                    part_duration, splited_thumb_dir = part_result
                    video_msg = send_videos(message, path_lst[p], caption_lst[p], part_duration, splited_thumb_dir, info_text, proc_msg.id)
                    try:
                        safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                    except Exception as e:
                        logger.error(f"Error forwarding video to logger: {e}")
                    safe_edit_message_text(user_id, proc_msg_id,
                                          f"{info_text}\n\n{full_bar}   100.0%\n__Splitted part {p + 1} file uploaded__")
                    if p < len(caption_lst) - 1:
                        threading.Event().wait(2)
                    os.remove(splited_thumb_dir)
                    os.remove(path_lst[p])
                os.remove(thumb_dir)
                os.remove(user_vid_path)
                success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
                safe_edit_message_text(user_id, proc_msg_id, success_msg)
                send_to_logger(message, "Video upload completed with file splitting.")
                break
            else:
                if final_name:
                    video_msg = send_videos(message, after_rename_abs_path, caption_name, duration, thumb_dir, info_text, proc_msg.id)
                    try:
                        safe_forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                    except Exception as e:
                        logger.error(f"Error forwarding video to logger: {e}")
                    safe_edit_message_text(user_id, proc_msg_id,
                        f"{info_text}\n{full_bar}   100.0%\n\n**🎞 Video duration:** __{TimeFormatter(duration * 1000)}__\n\n1 file uploaded.")
                    os.remove(after_rename_abs_path)
                    os.remove(thumb_dir)
                    threading.Event().wait(2)
                else:
                    send_to_all(message, "❌ Some error occurred during processing. 😢")
        if successful_uploads == video_count:
            success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
            safe_edit_message_text(user_id, proc_msg_id, success_msg)
            send_to_logger(message, success_msg)
    finally:
        set_active_download(user_id, False)
        if playlist_name:
            with playlist_errors_lock:
                error_key = f"{user_id}_{playlist_name}"
                if error_key in playlist_errors:
                    del playlist_errors[error_key]

        try:
            if status_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            if hourglass_msg_id:
                safe_delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}")



#####################################################################################
#####################################################################################
#####################################################################################

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

    # Remove invalid characters (Windows and Linux safe)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name = re.sub(invalid_chars, '', name)

    # Replace multiple spaces with single space and strip
    name = re.sub(r'\s+', ' ', name).strip()

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
    """
    Safely send a message with flood wait handling

    Args:
        chat_id: The chat ID to send to
        text: The text to send
        **kwargs: Additional arguments for send_message

    Returns:
        The message object or None if sending failed
    """
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

app.run()
