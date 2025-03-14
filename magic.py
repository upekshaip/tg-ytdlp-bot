import pyrebase
import re
import os
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
from config import Config

################################################################################################
# Global starting point list (do not modify)
starting_point = []

# Global dictionary to track active downloads
active_downloads = {}

# Firebase Initialization with Authentication
firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)

# Create auth object from pyrebase
auth = firebase.auth()

# Sign in using email and password (ensure these credentials are set in your Config)
try:
    user = auth.sign_in_with_email_and_password(Config.FIREBASE_USER, Config.FIREBASE_PASSWORD)
    # Debug: Print essential details of the user object
    print("User signed in successfully.")
    print("User email:", user.get("email"))
    print("User localId:", user.get("localId"))
    # If available, check email verification status
    if "emailVerified" in user:
        print("Email verified:", user["emailVerified"])
    else:
        print("Email verification status not available in user object.")
except Exception as e:
    print("Error during Firebase authentication:", e)
    raise

# Debug: Print a portion of idToken
idToken = user.get("idToken")
if idToken:
    print("Firebase idToken (first 20 chars):", idToken[:20])
else:
    print("No idToken received!")
    raise Exception("idToken is empty.")

# Get the base database object
base_db = firebase.database()

# Additional check: Execute a test GET request to the root node
try:
    test_data = base_db.get(idToken)
    print("Test GET operation succeeded. Data:", test_data.val())
except Exception as e:
    print("Test GET operation failed:", e)

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
    print("Data written successfully. Result:", result)
except Exception as e:
    print("Error writing data to Firebase:", e)
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
            print("Firebase idToken refreshed successfully. New token (first 20 chars):", new_idToken[:20])
        except Exception as e:
            print("Error refreshing Firebase idToken:", e)

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
    if active_downloads.get(user_id, False):
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

    print(user_id, "No matching command processed.")

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
    if os.path.exists(dir):

        allfiles = os.listdir(dir)

        mp4_files = [fname for fname in allfiles if fname.endswith(('.mp4', '.mkv'))]
        mp3_files = [fname for fname in allfiles if fname.endswith('.mp3')]
        jpg_files = [fname for fname in allfiles if fname.endswith('.jpg')]
        part_files = [fname for fname in allfiles if fname.endswith('.part')]
        ytdl_files = [fname for fname in allfiles if fname.endswith('.ytdl')]
        txt_files = [fname for fname in allfiles if fname.endswith('.txt')]
        ts_files = [fname for fname in allfiles if fname.endswith('.ts')]
        webm_files = [fname for fname in allfiles if fname.endswith('.webm')]

        if len(mp4_files) > 0:
            for file in mp4_files:
                os.remove(f"{dir}/{file}")
        if len(mp3_files) > 0:
            for file in mp3_files:
                os.remove(f"{dir}/{file}")
        if len(jpg_files) > 0:
            for file in jpg_files:
                os.remove(f"{dir}/{file}")
        if len(part_files) > 0:
            for file in part_files:
                os.remove(f"{dir}/{file}")
        if len(ytdl_files) > 0:
            for file in ytdl_files:
                os.remove(f"{dir}/{file}")
        if len(txt_files) > 0:
            for file in txt_files:
                os.remove(f"{dir}/{file}")
        if len(ts_files) > 0:
            for file in ts_files:
                os.remove(f"{dir}/{file}")
        if len(webm_files) > 0:
            for file in webm_files:
                os.remove(f"{dir}/{file}")

        print("All media removed.")

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
                print(f"Error sending broadcast to user {user}: {e}")
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

    print(mod)

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
    # If the user has already been launched by the process, we answer the rein and go out
    if active_downloads.get(user_id, False):
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
        down_and_up(app, message, url, playlist_name, video_count, video_start_with)
    else:
        send_to_all(message, f"**User entered like this:** {full_string}\n{Config.ERROR1}")

#############################################################################################

# Send Message to Logger

def send_to_logger(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # Print (user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)

# Send Message to User Only

def send_to_user(message, msg):
    user_id = message.chat.id
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)

# Send Message to All ...

def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # Print (user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)

def progress_bar(*args):
    # It is expected that Pyrogram will cause Progress_BAR with five parameters:
    # Current, Total, Speed, ETA, File_SIZE, and then additionally your Progress_args (User_id, Msg_id, Status_text)
    if len(args) < 8:
        return
    current, total, speed, eta, file_size, user_id, msg_id, status_text = args[:8]
    try:
        app.edit_message_text(user_id, msg_id, status_text)
    except Exception as e:
        print(f"Error updating progress: {e}")

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

    rounds = (math.floor(video_size / max_size)) + 1
    n = duration / rounds
    caption_lst = []
    path_lst = []
    for x in range(rounds):
        start_time = x * n
        end_time = (x * n) + n
        cap_name = video_name + " - Part " + str(x + 1)
        target_name = dir + "/" + cap_name + ".mp4"
        video = video_path
        caption_lst.append(cap_name)
        path_lst.append(target_name)
        ffmpeg_extract_subclip(
            video, start_time, end_time, targetname=target_name)
    split_vid_dict = {
        "video": caption_lst,
        "path": path_lst
    }
    print("convert successfull")
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
        subprocess.run(ffmpeg_command, check=True)
        result = subprocess.check_output(ffprobe_command, stderr=subprocess.STDOUT, universal_newlines=True)
        duration = int(float(result))
        return duration, thumb_dir
    except subprocess.CalledProcessError as e:
        send_to_all(message, f"❌ Error capturing thumbnail or getting video duration: {e}")
        return None

def write_logs(message, video_url, video_title):
    ts = str(math.floor(time.time()))
    data = {"ID": str(message.chat.id), "timestamp": ts,
            "name": message.chat.first_name, "urls": str(video_url), "title": video_title}
    db.child("bot").child("tgytdlp_bot").child("logs").child(str(message.chat.id)).child(str(ts)).set(data)
    print("Log for user added")
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
    if active_downloads.get(user_id, False):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
    active_downloads[user_id] = True
    try:
        proc_msg = app.send_message(user_id, "Processing... ♻️")
        proc_msg_id = proc_msg.id
        check_user(message)

        status_msg = app.send_message(user_id, "Processing audio, wait... ♻️")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages at once
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        stop_anim = threading.Event()
        def animate_hourglass():
            current = True
            while not stop_anim.is_set():
                emoji = "⌛️" if current else "⏳"
                try:
                    app.edit_message_text(user_id, hourglass_msg_id, emoji)
                except Exception as e:
                    print("Hourglass animation error:", e)
                current = not current
                if stop_anim.wait(3):
                    break
        anim_thread = threading.Thread(target=animate_hourglass)
        anim_thread.start()

        user_folder = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_folder)
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
            'cookiefile': cookie_file,
            'outtmpl': os.path.join(user_folder, "%(title)s.%(ext)s"),
            'progress_hooks': [],
        }
        last_update = 0
        def progress_hook(d):
            nonlocal last_update
            current_time = time.time()
            if current_time - last_update < 0.1:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                blocks = int(percent // 10)
                bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                try:
                    app.edit_message_text(user_id, proc_msg_id, f"Downloading audio:\n{bar}   {percent:.1f}%")
                except Exception as e:
                    print(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "finished":
                try:
                    full_bar = "🟩" * 10
                    app.edit_message_text(user_id, proc_msg_id,
                        f"Downloading audio:\n{full_bar}   100.0%\nDownload finished, processing audio...")
                except Exception as e:
                    print(f"Error updating progress: {e}")
                last_update = current_time
            elif d.get("status") == "error":
                try:
                    app.edit_message_text(user_id, proc_msg_id, "Error occurred during audio download.")
                except Exception as e:
                    print(f"Error updating progress: {e}")
                last_update = current_time

        ytdl_opts['progress_hooks'].append(progress_hook)

        with YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        audio_title = info.get("title", "audio")
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
            app.edit_message_text(user_id, proc_msg_id, f"Uploading audio file...\n{full_bar}   100.0%")
        except Exception as e:
            print(f"Error updating upload status: {e}")

        # Send audio and save the message object for repost
        audio_msg = app.send_audio(chat_id=user_id, audio=audio_file, caption=f"{audio_title}")
        # Reposting final audio message to the log channel (replacement .Message_id -> .id)
        try:
            app.forward_messages(Config.LOGS_ID, user_id, [audio_msg.id])
        except Exception as e:
            print("Error forwarding audio to logger:", e)

        try:
            full_bar = "🟩" * 10
            success_msg = f"✅ Audio successfully downloaded and sent.\n\n{Config.CREDITS_MSG}"
            app.edit_message_text(user_id, proc_msg_id, success_msg)

        except Exception as e:
            print(f"Error updating final status: {e}")
        send_to_logger(message, success_msg)

        stop_anim.set()
        anim_thread.join()
        try:
            app.delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            app.delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            print("Error deleting status messages:", e)

        try:
            os.remove(audio_file)
        except Exception as e:
            print(f"Failed to delete file {audio_file}: {e}")

    except Exception as e:
        send_to_user(message, f"❌ Failed to download audio: {e}")
        send_to_logger(message, f"Error in audio download: {e}")
        try:
            app.edit_message_text(user_id, proc_msg_id, f"Error: {e}")
        except Exception as e:
            print(f"Error editing message on exception: {e}")
    finally:
        active_downloads[user_id] = False

#########################################
# Download_and_up function
#########################################

def down_and_up(app, message, url, playlist_name, video_count, video_start_with):
    user_id = message.chat.id
    # Logging a video download request
    send_to_logger(message, f"Video download requested:\nURL: {url}\nPlaylist: {playlist_name}\nCount: {video_count}, Start: {video_start_with}")

    if active_downloads.get(user_id, False):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
    active_downloads[user_id] = True
    error_message = ""
    try:
        proc_msg = app.send_message(user_id, "Processing... ♻️")
        proc_msg_id = proc_msg.id
        check_user(message)

        user_dir_name = os.path.abspath(os.path.join("users", str(user_id)))
        create_directory(user_dir_name)

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
                 'prefer_ffmpeg': True, 'merge_output_format': 'mp4'},
                {'format': 'bestvideo+bestaudio/best',
                 'prefer_ffmpeg': True, 'merge_output_format': 'mp4'},
                {'format': 'best', 'prefer_ffmpeg': False}
            ]

        status_msg = app.send_message(user_id, "Processing video, wait... ♻️")
        hourglass_msg = app.send_message(user_id, "⌛️")
        # We save ID status messages
        status_msg_id = status_msg.id
        hourglass_msg_id = hourglass_msg.id

        stop_anim = threading.Event()
        def animate_hourglass():
            current = True
            while not stop_anim.is_set():
                emoji = "⌛️" if current else "⏳"
                try:
                    app.edit_message_text(user_id, hourglass_msg_id, emoji)
                except Exception as e:
                    print("Hourglass animation error:", e)
                current = not current
                if stop_anim.wait(3):
                    break
        anim_thread = threading.Thread(target=animate_hourglass)
        anim_thread.start()

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
                    app.edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{bar}   {percent:.1f}%")
                except Exception as e:
                    print(f"Error updating progress: {e}")
            elif d.get("status") == "error":
                print("Error occurred during download.")
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
                if ("m3u8" in url.lower()) or (info_dict.get("protocol") == "m3u8_native"):
                    is_hls = True
                    if "format" in ytdl_opts:
                        del ytdl_opts["format"]
                    ytdl_opts["downloader"] = "ffmpeg"
                    ytdl_opts["hls_use_mpegts"] = True
                try:
                    if is_hls:
                        app.edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n\n__Detected HLS stream. Downloading...__ 📥")
                    else:
                        app.edit_message_text(user_id, proc_msg_id,
                            f"{current_total_process}\n\n__Downloading using format: {ytdl_opts.get('format', 'default')}...__ 📥")
                except Exception as e:
                    print(f"Status update error: {e}")
                with YoutubeDL(ytdl_opts) as ydl:
                    if is_hls:
                        cycle_stop = threading.Event()
                        def cycle_progress():
                            nonlocal cycle_stop
                            counter = 0
                            while not cycle_stop.is_set():
                                counter = (counter + 1) % 11
                                frag_files = [f for f in os.listdir(user_dir_name) if ".part-Frag" in f and f.endswith(".part")]
                                if frag_files:
                                    last_frag = sorted(frag_files)[-1]
                                    m = re.search(r'Frag(\d+)', last_frag)
                                    frag_text = f"Frag{m.group(1)}" if m else "Frag?"
                                else:
                                    frag_text = "waiting for fragments"
                                bar = "🟩" * counter + "⬜️" * (10 - counter)
                                try:
                                    app.edit_message_text(user_id, proc_msg_id,
                                        f"{current_total_process}\nDownloading HLS stream: {frag_text}\n{bar}")
                                except Exception as e:
                                    print("Cycle progress error:", e)
                                if cycle_stop.wait(1.5):
                                    break
                        cycle_thread = threading.Thread(target=cycle_progress)
                        cycle_thread.start()
                        with YoutubeDL(ytdl_opts) as ydl:
                            ydl.download([url])
                        cycle_stop.set()
                        cycle_thread.join()
                    else:
                        with YoutubeDL(ytdl_opts) as ydl:
                            ydl.download([url])
                try:
                    app.edit_message_text(user_id, proc_msg_id, f"{current_total_process}\n{full_bar}   100.0%")
                except Exception as e:
                    print("Final progress update error:", e)
                return info_dict
            except Exception as e:
                nonlocal error_message
                error_message = str(e)
                print(f"Attempt with format {ytdl_opts.get('format', 'default')} failed: {e}")
                return None

        for x in range(video_count):
            current_index = x
            total_process = f"""
**<<<** __Total progress__ **>>>**

**Video number:** {x + 1} / {video_count}
"""
            current_total_process = total_process

            if playlist_name and video_count > 1:
                rename_name = f"{playlist_name} - Part {x + video_start_with}"
            else:
                rename_name = None

            info_dict = None

            for attempt in attempts:
                info_dict = try_download(url, attempt)
                if info_dict is not None:
                    break
            if info_dict is None:
                send_to_all(message, f"❌ Failed to download video: {error_message}\n────────────────\nCheck [here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) if your site supported\nYou may need `cookie` for downloading this video.\nFor Youtube - get `cookie` via /download_cookie command. For any other supported site - send your own cookie ([guide1](https://t.me/c/2303231066/18)) ([guide2](https://t.me/c/2303231066/22)) and after that send your video link again.")
                continue  # Move to the Next Video If Availble

            successful_uploads += 1

            video_id = info_dict.get("id", None)
            video_title = info_dict.get("title", None)
            if rename_name is None:
                rename_name = video_title

            info_text = f"""
{total_process}

**<<<** __Info__ **>>>**

**Video number:** {x + video_start_with}
**Video Name:** __{video_title}__
**Caption Name:** __{rename_name}__
**Video id:** {video_id}"""
            try:
                app.edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n\n{full_bar}   100.0%\n__Downloaded video. Processing for upload...__ ♻️")
            except Exception as e:
                print(f"Status update error after download: {e}")

            dir_path = os.path.join("users", str(user_id))
            allfiles = os.listdir(dir_path)
            files = [fname for fname in allfiles if fname.endswith(('.mp4', '.mkv', '.webm', '.ts'))]
            files.sort()
            if not files:
                send_to_all(message, "❌ File not found after download.")
                continue

            downloaded_file = files[0]
            write_logs(message, url, downloaded_file)

            if rename_name == video_title:
                caption_name = video_title
                final_name = downloaded_file
            else:
                ext = os.path.splitext(downloaded_file)[1]
                final_name = rename_name + ext
                caption_name = rename_name
                os.rename(os.path.join(dir_path, downloaded_file), os.path.join(dir_path, final_name))

            user_vid_path = os.path.join(dir_path, final_name)
            if final_name.lower().endswith((".webm", ".ts")):
                try:
                    app.edit_message_text(user_id, proc_msg_id,
                        f"{info_text}\n\n{full_bar}   100.0%\nConverting video using ffmpeg... ⏳")
                except Exception as e:
                    print(f"Error updating status before conversion: {e}")
                mp4_file = os.path.join(dir_path, os.path.splitext(final_name)[0] + ".mp4")
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
                except Exception as e:
                    send_to_all(message, f"❌ Conversion to MP4 failed: {e}")
                    continue

            after_rename_abs_path = os.path.abspath(user_vid_path)
            result = get_duration_thumb(message, dir_path, user_vid_path, caption_name)
            if result is None:
                send_to_all(message, "❌ Failed to get video duration and thumbnail.")
                continue
            duration, thumb_dir = result

            video_size_in_bytes = os.path.getsize(user_vid_path)
            video_size = humanbytes(int(video_size_in_bytes))
            max_size = 1850000000
            if int(video_size_in_bytes) > max_size:
                app.edit_message_text(user_id, proc_msg_id,
                    f"{info_text}\n\n{full_bar}   100.0%\n__⚠️ Your video size ({video_size}) is too large.__\n__Splitting file...__ ✂️")
                returned = split_video_2(dir_path, caption_name, after_rename_abs_path, int(video_size_in_bytes), max_size, duration)
                caption_lst = returned.get("video")
                path_lst = returned.get("path")
                # For each split video part, send the part and immediately forward it to the log channel
                for p in range(len(caption_lst)):
                    part_result = get_duration_thumb(message, dir_path, path_lst[p], caption_lst[p])
                    if part_result is None:
                        continue
                    part_duration, splited_thumb_dir = part_result
                    # Send the split video part and save the message object
                    video_msg = send_videos(message, path_lst[p], caption_lst[p], part_duration, splited_thumb_dir, info_text, proc_msg.id)
                    # Immediately forward the sent video message to the log channel using its id
                    try:
                        app.forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                    except Exception as e:
                        print("Error forwarding video to logger:", e)
                    # Update progress message for this part
                    app.edit_message_text(user_id, proc_msg_id,
                                          f"{info_text}\n\n{full_bar}   100.0%\n__Splitted part {p + 1} file uploaded__")
                    if p < len(caption_lst) - 1:
                        threading.Event().wait(2)
                    os.remove(splited_thumb_dir)
                    os.remove(path_lst[p])
                os.remove(thumb_dir)
                os.remove(user_vid_path)
                success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
                app.edit_message_text(user_id, proc_msg_id, success_msg)
                send_to_logger(message, "Video upload completed with file splitting.")
                break
            else:
                if final_name:
                    video_msg = send_videos(message, after_rename_abs_path, caption_name, duration, thumb_dir, info_text, proc_msg.id)
                    try:
                        app.forward_messages(Config.LOGS_ID, user_id, [video_msg.id])
                    except Exception as e:
                        print("Error forwarding video to logger:", e)
                    app.edit_message_text(user_id, proc_msg_id,
                        f"{info_text}\n{full_bar}   100.0%\n**Video duration:** __{TimeFormatter(duration * 1000)}__\n\n1 file uploaded.")
                    os.remove(after_rename_abs_path)
                    os.remove(thumb_dir)
                    threading.Event().wait(2)
                else:
                    send_to_all(message, "❌ Some error occurred during processing. 😢")
        if successful_uploads == video_count:
            success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n\n{Config.CREDITS_MSG}"
            app.edit_message_text(user_id, proc_msg_id, success_msg)
            send_to_logger(message, success_msg)
    finally:
        active_downloads[user_id] = False
        try:
            app.delete_messages(chat_id=user_id, message_ids=[status_msg_id], revoke=True)
            app.delete_messages(chat_id=user_id, message_ids=[hourglass_msg_id], revoke=True)
        except Exception as e:
            print("Error deleting status messages:", e)

#####################################################################################
#####################################################################################
#####################################################################################

# YT-DLP HOOK

def ytdlp_hook(d):
    print(d['status'])

#####################################################################################
_format = {"ID": '0', "timestamp": math.floor(time.time())}
db.child("bot").child("tgytdlp_bot").child("users").child("0").set(_format)
db.child("bot").child("tgytdlp_bot").child("blocked_users").child("0").set(_format)
db.child("bot").child("tgytdlp_bot").child("unblocked_users").child("0").set(_format)
print("db created")
starting_point.append(time.time())
print("Bot started")
app.run()
