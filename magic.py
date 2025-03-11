import pyrebase
import re
import os
from pyrogram import Client, filters
from pyrogram import enums
from pyrogram import errors
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import requests
import math
import time
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import subprocess
from config import Config
################################################################################################
# this is the bot's starting point. do not touch this one
starting_point = []
################################################################################################

# Firebase initialization
firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)
db = firebase.database()

##############################################################################################################################
##############################################################################################################################


# App
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
    # Create the directory (and all intermediate directories) if it does not exist.
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# Command to set browser cookies
@app.on_message(filters.command("cookies_from_browser") & filters.private)
def cookies_from_browser(app, message):
    user_id = message.chat.id
    # For non-admin users, check if they are in the channel.
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    # Path to the user's directory, e.g. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)  # Ensure the user's folder exists

    # Dictionary with browsers and their paths
    browsers = {
        "brave": "~/.config/BraveSoftware/Brave-Browser/",
        "chrome": "~/.config/google-chrome/",
        "chromium": "~/.config/chromium/",
        "edge": "~/.config/microsoft-edge/",
        "firefox": "~/.mozilla/firefox/",
        "opera": "~/.config/opera/",
        "safari": None,  # Not supported on Linux
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

    # Add a Cancel button to cancel the selection
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="browser_choice|cancel")])
    keyboard = InlineKeyboardMarkup(buttons)

    app.send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard
    )

# Callback handler for browser selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
def browser_choice_callback(app, callback_query):
    import subprocess

    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]  # e.g. "chromium", "firefox", or "cancel"
    # Path to the user's directory, e.g. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "cancel":
        callback_query.edit_message_text("🔚 Browser selection canceled.")
        callback_query.answer("✅ Browser choice updated.")
        return

    browser_option = data

    # Dictionary with browsers and their paths (same as above)
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
    # If the browser is not installed, inform the user and do not execute the command
    if (browser_option == "safari") or (
        isinstance(path, list) and not any(os.path.exists(os.path.expanduser(p)) for p in path)
    ) or (isinstance(path, str) and not os.path.exists(os.path.expanduser(path))):
        callback_query.edit_message_text(f"⚠️ {browser_option.capitalize()} browser not installed.")
        callback_query.answer("⚠️ Browser not installed.")
        return

    # Build the command for cookie extraction: yt-dlp --cookies "cookie.txt" --cookies-from-browser <browser_option>
    cmd = f'yt-dlp --cookies "{cookie_file}" --cookies-from-browser {browser_option}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # If the return code is not 0, but the error is due to missing URL, consider the cookies as successfully extracted
    if result.returncode != 0:
        if "You must provide at least one URL" in result.stderr:
            callback_query.edit_message_text(f"✅ Cookies saved using browser: {browser_option}")
        else:
            callback_query.edit_message_text(f"❌ Failed to save cookies: {result.stderr}")
    else:
        callback_query.edit_message_text(f"✅ Cookies saved using browser: {browser_option}")

    callback_query.answer("✅ Browser choice updated.")



# Command to download audio from a video URL
@app.on_message(filters.command("audio") & filters.private)
def audio_command_handler(app, message):
    user_id = message.chat.id
    # For non-administrators, we're checking subscriptions
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Let's make sure the user folder exists

    # A command like this is expected: /audio <URL>
    if len(message.command) < 2:
        send_to_user(message, "Please provide the URL of the video to download the audio.")
        return
    url = message.command[1]  # Take the URL from the command arguments
    down_and_audio(app, message, url)


# Command /format handler
@app.on_message(filters.command("format") & filters.private)
def set_format(app, message):
    user_id = message.chat.id
    # For non-administrators, we're checking subscriptions
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Let's make sure the user folder exists

    # If additional text is passed, save it as a custom format
    if len(message.command) > 1:
        custom_format = message.text.split(" ", 1)[1].strip()
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write(custom_format)
        app.send_message(user_id, f"✅ Format updated to:\n{custom_format}")
    else:
        # Main menu with a few popular options, plus the Others button
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


# CallbackQuery handler for /format menu selection
@app.on_callback_query(filters.regex(r"^format_option\|"))
def format_option_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    # If the Cancel button is pressed
    if data == "cancel":
        callback_query.edit_message_text("🔚 Format selection canceled.")
        callback_query.answer("✅ Format choice updated.")
        return

    # When the Custom button is pressed
    if data == "custom":
        callback_query.edit_message_text(
            "To use a custom format, send the command in the following form:\n\n`/format bestvideo+bestaudio/best`\n\nReplace `bestvideo+bestaudio/best` with your desired format string."
        )
        callback_query.answer("Hint sent.")
        return

    # If the Others button is pressed, the second menu with the full set of permissions is displayed
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
        return

    # If the Back button is pressed in the second menu - return to the original menu
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
        return

    # Mapping for the rest of the options
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

    # Save the selected format
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
        f.write(chosen_format)
    callback_query.edit_message_text(f"✅ Format updated to:\n{chosen_format}")
    callback_query.answer("✅ Format saved.")




#####################################################################################

# checking user is blocked or not
def is_user_blocked(message):
    blocked = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get().each()
    blocked_users = [int(b_user.key()) for b_user in blocked]
    if int(message.chat.id) in blocked_users:
        send_to_user(message, "🚫 You are banned from the bot!")
        return True
    else:
        return False


# cheking users are in main user directory in db
def check_user(message):
    user_id_str = str(message.chat.id)
    # Create the user folder inside the "users" directory
    user_dir = os.path.join("users", user_id_str)
    create_directory(user_dir)

    # Copy cookie.txt from the project root to the user's folder if not already present
    cookie_src = os.path.join(os.getcwd(), "cookie.txt")
    cookie_dest = os.path.join(user_dir, os.path.basename(Config.COOKIE_FILE_PATH))
    if os.path.exists(cookie_src) and not os.path.exists(cookie_dest):
        import shutil
        shutil.copy(cookie_src, cookie_dest)

    # Register the user in the database if not already registered
    user_db = db.child(f"{Config.BOT_DB_PATH}/users").get().each()
    users = [user.key() for user in user_db] if user_db else []
    if user_id_str not in users:
        data = {"ID": message.chat.id, "timestamp": math.floor(time.time())}
        db.child(f"{Config.BOT_DB_PATH}/users/{user_id_str}").set(data)



#####################################################################################


def down_and_audio(app, message, url):
    user_id = message.chat.id
    # Send initial status message and get its id for editing
    status_message = app.send_message(user_id, "Processing audio... ♻️")
    status_message_id = status_message.id  # Use .id since .message_id might not exist

    # Form the absolute path to the user's directory (./users/<user_id>)
    user_folder = os.path.abspath(os.path.join("users", str(user_id)))
    create_directory(user_folder)

    # Form the path to the cookie file (filename taken from Config.COOKIE_FILE_PATH)
    cookie_file = os.path.join(user_folder, os.path.basename(Config.COOKIE_FILE_PATH))

    # Options for yt-dlp: download the best audio track and convert to mp3
    ytdl_opts = {
        'format': 'ba',  # choose the best audio track
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

    # Local function to update download status
    def progress_hook(d):
        if d.get("status") == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            try:
                app.edit_message_text(user_id, status_message_id, f"Downloading audio: {percent:.1f}%")
            except Exception as e:
                print(f"Error editing message: {e}")
        elif d.get("status") == "finished":
            try:
                app.edit_message_text(user_id, status_message_id, "Download finished, processing audio...")
            except Exception as e:
                print(f"Error editing message: {e}")
        elif d.get("status") == "error":
            try:
                app.edit_message_text(user_id, status_message_id, "Error occurred during audio download.")
            except Exception as e:
                print(f"Error editing message: {e}")

    ytdl_opts['progress_hooks'].append(progress_hook)

    try:
        # Download audio using yt-dlp
        with YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Form the expected filename (with .mp3 extension)
        audio_title = info.get("title", "audio")
        audio_file = os.path.join(user_folder, audio_title + ".mp3")
        if not os.path.exists(audio_file):
            files = [f for f in os.listdir(user_folder) if f.endswith(".mp3")]
            if files:
                audio_file = os.path.join(user_folder, files[0])
            else:
                send_to_user(message, "Audio file not found after download.")
                return

        # Update status before uploading the file
        app.edit_message_text(user_id, status_message_id, "Uploading audio file... 📤")
        app.send_audio(chat_id=user_id, audio=audio_file, caption=f"Audio downloaded: {audio_title}")
        app.edit_message_text(user_id, status_message_id, f"✅ Audio successfully downloaded and sent.\n\n{Config.CREDITS_MSG}")

        # Delete the audio file after sending to avoid disk clutter
        try:
            os.remove(audio_file)
        except Exception as e:
            print(f"Failed to delete file {audio_file}: {e}")

    except Exception as e:
        send_to_user(message, f"Failed to download audio: {e}")
        try:
            app.edit_message_text(user_id, status_message_id, f"Error: {e}")
        except Exception as e:
            print(f"Error editing message on exception: {e}")



# checking actions
# Text message handler for general commands
@app.on_message(filters.text & filters.private)
def url_distractor(app, message):
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN
    text = message.text.strip()

    # For non-admin users, if they haven't joined the channel, exit immediately.
    if not is_admin and not is_user_in_channel(app, message):
        return

    # ----- User commands -----
    # /save_as_cookie command
    if text.startswith(Config.SAVE_AS_COOKIE_COMMAND):
        save_as_cookie_file(app, message)
        return

    # /download_cookie command
    if text == Config.DOWNLOAD_COOKIE_COMMAND:
        download_cookie(app, message)
        return

    # /check_cookie command
    if text == Config.CHECK_COOKIE_COMMAND:
        checking_cookie_file(app, message)
        return

    # /cookies_from_browser command
    if text.startswith(Config.COOKIES_FROM_BROWSER_COMMAND):
        cookies_from_browser(app, message)
        return

    # /audio command
    if text.startswith(Config.AUDIO_COMMAND):
        audio_command_handler(app, message)
        return

    # /format command
    if text.startswith(Config.FORMAT_COMMAND):
        set_format(app, message)
        return

    # /clean command
    if Config.CLEAN_COMMAND in text:
        remove_media(message)
        send_to_all(message, "🗑 All files are removed.")
        return

    # /usage command
    if Config.USAGE_COMMAND in text:
        get_user_log(app, message)
        return

    # If the message contains a URL, launch the video download function.
    if ("https://" in text) or ("http://" in text):
        if not is_user_blocked(message):
            video_url_extractor(app, message)
        return

    # If the message is a reply to a video, call the caption editor.
    if message.reply_to_message:
        if not is_user_blocked(message):
            if message.reply_to_message.video:
                caption_editor(app, message)
        return

    # ----- Admin commands (only processed if user is admin) -----
    if is_admin:
        # Broadcast message: reply to a message and use /broadcast
        if message.reply_to_message and text == Config.BROADCAST_MESSAGE:
            send_promo_message(app, message)
            return

        # /block_user command
        if Config.BLOCK_USER_COMMAND in text:
            block_user(app, message)
            return

        # /unblock_user command
        if Config.UNBLOCK_USER_COMMAND in text:
            unblock_user(app, message)
            return

        # /run_time command
        if Config.RUN_TIME in text:
            check_runtime(message)
            return

        # /all command for user details
        if Config.GET_USER_DETAILS_COMMAND in text:
            get_user_details(app, message)
            return

        # /log command for user logs
        if Config.GET_USER_LOGS_COMMAND in text:
            get_user_log(app, message)
            return

    # If no matching command is processed, log the message.
    print(user_id, "No matching command processed.")





# Check the usage of the bot
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
        # Use the send_message() method to send the message with the button
        app.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        return False


# Remove all user media files
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
        if len(webm_files) > 0:
            for file in webm_files:
                os.remove(f"{dir}/{file}")

        print("All media removed.")


# Send messages to all the users
def send_promo_message(app, message):
    user_lst = db.child(f"{Config.BOT_DB_PATH}/users").get().each()
    user_lst = [int(user.key()) for user in user_lst]
    for admin in Config.ADMIN:
        user_lst.append(admin)
    try:
        reply = message.reply_to_message
        for user in user_lst:
            try:
                if user != 0:
                    if reply.text:
                        app.send_message(user, reply.text)
                    if reply.video:
                        app.send_video(user, reply.video.file_id,
                                       caption=reply.caption)
                    if reply.photo:
                        app.send_photo(user, reply.photo.file_id,
                                       caption=reply.caption)
                    if reply.sticker:
                        app.send_sticker(user, reply.sticker.file_id)
                    if reply.document:
                        app.send_document(user, reply.document.file_id,
                                          caption=reply.caption)
                    if reply.audio:
                        app.send_audio(user, reply.audio.file_id,
                                       caption=reply.caption)
                    if reply.animation:
                        app.send_animation(user, reply.animation.file_id,
                                           caption=reply.caption)
            except:
                pass

        send_to_all(message, "**✅ Promo message sent to all other users**")
    except:
        send_to_all(
            message, "**❌ Cannot send the promo message. Try repling to a massege\n Or some error occured**")


# Getting the user logs
def get_user_log(app, message):
    user_id = message.chat.id
    if int(message.chat.id) in Config.ADMIN:
        user_id = message.chat.id
        if Config.GET_USER_LOGS_COMMAND in message.text:
            user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    try:
        db_data = db.child(f"{Config.BOT_DB_PATH}/logs/{user_id}").get().each()
        lst = [user.val() for user in db_data]
        data = []
        data_tg = []
        least_10 = []
        topics = ["TS", "ID", "Name", "Video Title", "URL"]

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

# Get all kinds of users (users/ blocked/ unblocked)


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
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " + \
            path + \
            f":\n \n" + \
            '\n'.join(modified_lst)
    else:
        temp = []
        for j in range(no_of_users_to_display):
            temp.append(modified_lst[((j+1) * -1)])
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

    print(mod)


# Block user
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


# Unblock user
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


# Send cookie via document
@app.on_message(filters.document & filters.private)
def save_my_cookie(app, message):
    user_id = str(message.chat.id)
    # Define the user folder path (e.g., "./users/1234567")
    user_folder = f"./users/{user_id}"
    # Create the user directory if it doesn't exist
    create_directory(user_folder)
    # Extract only the filename (e.g., "cookie.txt") from the config path
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    # Construct the full path where the cookie file should be saved
    cookie_file_path = os.path.join(user_folder, cookie_filename)
    # Download the media and save it directly in the user's root folder
    app.download_media(message, file_name=cookie_file_path)
    send_to_user(message, "✅ Cookie file saved")


def download_cookie(app, message):
    # Convert the user's id to a string for proper path handling
    user_id = str(message.chat.id)
    response = requests.get(Config.COOKIE_URL)
    if response.status_code == 200:
        # Create the user directory inside "users" if it doesn't exist yet
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        # Extract the cookie filename from the full path specified in the config
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        # Construct the full path for saving the cookie file in the user's folder
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "wb") as cf:
            cf.write(response.content)
        send_to_all(message, "**✅ Cookie file downloaded and saved in your folder.**")
    else:
        send_to_all(message, "❌ Cookie URL is not available!")


# caption editor for videos
@app.on_message(filters.text & filters.private)
def caption_editor(app, message):
    users_name = message.chat.first_name
    user_id = message.chat.id
    caption = message.text
    video_file_id = message.reply_to_message.video.file_id
    info_of_video = f"\n**Caption:** `{caption}`\n**User id:** `{user_id}`\n**User first name:** `{users_name}`\n**Video file id:** `{video_file_id}`"
    # sending to logs
    send_to_logger(message, info_of_video)
    app.send_video(user_id, video_file_id, caption=caption)
    app.send_video(Config.LOGS_ID, video_file_id, caption=caption)


@app.on_message(filters.text & filters.private)
def checking_cookie_file(app, message):
    # Convert the user's id to a string for proper path handling
    user_id = str(message.chat.id)
    # Extract the cookie filename from the full path specified in the config
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    # Construct the path to the cookie file within the user's folder
    file_path = os.path.join("users", user_id, cookie_filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as cookie:
            cookie_content = cookie.read()
        # Check if the cookie file has the Netscape Navigator format
        if cookie_content.startswith("# Netscape HTTP Cookie File"):
            send_to_all(message, "✅ Cookie file exists and has correct format")
        else:
            send_to_all(message, "⚠️ Cookie file exists but has incorrect format")
    else:
        send_to_all(message, "❌ Cookie file is not found.")




# updating the cookie file.
# Function to save cookie file supporting code block
def save_as_cookie_file(app, message):
    # Convert the user's id to a string for proper path handling
    user_id = str(message.chat.id)
    # Extract the cookie content from the message text after the command
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
    else:
        send_to_all(message, "**❌ Not a valid cookie.**")


# url extractor
@app.on_message(filters.text & filters.private)
def video_url_extractor(app, message):
    # Ensure the user folder is created and the user is registered
    check_user(message)
    user_id = message.chat.id
    full_string = message.text
    if ("https://" in full_string) or ("http://" in full_string):
        # Logging the entered URL
        users_first_name = message.chat.first_name
        send_to_logger(
            message, f"User entered a **url**\n **user's name:** {users_first_name}\nURL: {full_string}")
        for j in range(len(Config.PORN_LIST)):
            if Config.PORN_LIST[j] in full_string:
                send_to_all(
                    message, "User entered a porn content. Cannot be downloaded.")
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

        # Downloading and uploading parts come here...
        down_and_up(app, message, url, playlist_name, video_count, video_start_with)
    else:
        send_to_all(
            message, f"**User entered like this:** {full_string}\n{Config.ERROR1}")



#############################################################################################

# send message to logger


def send_to_logger(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # print(user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)


# send message to user only
def send_to_user(message, msg):
    user_id = message.chat.id
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)


# send message to all...
def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # print(user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)


def progress_bar(*args):
    # Ожидается, что Pyrogram вызовет progress_bar с пятью параметрами:
    # current, total, speed, eta, file_size, а затем дополнительно ваши progress_args (user_id, msg_id, status_text)
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
    app.send_video(
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


#####################################################################################


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
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
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
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

    # ffmpeg command with -y flag to overwrite thumbnail file
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ss", "2",         # Seek to 2 seconds
        "-vframes", "1",    # Capture 1 frame
        thumb_dir
    ]

    # ffprobe command to get video duration
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
    db.child(f"{Config.BOT_DB_PATH}/logs/{str(message.chat.id)}/{ts}").set(data)
    print("Log for user added")
#####################################################################################
#####################################################################################


def down_and_up(app, message, url, playlist_name, video_count, video_start_with):
    user_id = message.chat.id
    msg_id = message.id
    plus_one = msg_id + 1
    app.send_message(user_id, "Processing... ♻️")
    check_user(message)

    # Create the user folder inside "users" using the absolute path
    user_dir_name = os.path.abspath(os.path.join("users", str(user_id)))
    create_directory(user_dir_name)  # Ensure the folder exists

    # If user has custom format saved, use it; otherwise use the default fallback cascade
    custom_format_path = f"{user_dir_name}/format.txt"
    if os.path.exists(custom_format_path):
        with open(custom_format_path, "r", encoding="utf-8") as f:
            custom_format = f.read().strip()
        # If user selected "best", then use prefer_ffmpeg False; otherwise True with merge_output_format mp4.
        if custom_format.lower() == "best":
            attempts = [{
                'format': custom_format,
                'prefer_ffmpeg': False
            }]
        else:
            attempts = [{
                'format': custom_format,
                'prefer_ffmpeg': True,
                'merge_output_format': 'mp4'
            }]
    else:
        # Default fallback cascade (if /format not set)
        attempts = [
            {
                'format': 'bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best',
                'prefer_ffmpeg': True,
                'merge_output_format': 'mp4'
            },
            {
                'format': 'bestvideo+bestaudio/best',
                'prefer_ffmpeg': True,
                'merge_output_format': 'mp4'
            },
            {
                'format': 'best',
                'prefer_ffmpeg': False
            }
        ]

    # Wrapper function for logging and attempting the download
    def try_download(url, attempt_opts, total_info_text):
        common_opts = {
            'cookiefile': os.path.join("users", str(user_id), os.path.basename(Config.COOKIE_FILE_PATH)),
            'progress_hooks': [my_hook],
            'playlist_items': str(current_index + video_start_with),
            'outtmpl': user_dir_name + "/%(title)s.%(ext)s"
        }
        ytdl_opts = {**common_opts, **attempt_opts}
        try:
            # First, extract video info (without downloading) for logging purposes
            with YoutubeDL(ytdl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
            app.edit_message_text(user_id, plus_one, f"{total_info_text}\n \n__Downloading using format: {ytdl_opts['format']}...__ 📥")
            with YoutubeDL(ytdl_opts) as ydl:
                ydl.download([url])
            return info_dict  # return the video information
        except Exception as e:
            print(f"Attempt with format {ytdl_opts['format']} failed: {e}")
            return None

    # Local function for progress hook (in case an error occurs during download)
    def my_hook(d):
        if d.get('status') == 'error':
            print('Some error occurred.')
            send_to_all(message, "❌ Sorry... Some error occurred during download.")

    successful_uploads = 0  # counter for successful downloads/uploads

    for x in range(video_count):
        current_index = x  # used in playlist_items
        j = ((x + 1) / video_count * 100)
        j_bar = f"{'🟩' * math.floor(j / 10)}{'⬜️' * (10 - math.floor(j / 10))}"
        total_process = f"""
**<<<** __Total progress__ **>>>**

**Video number:** __{x + 1}__
**Total videos:** __{video_count}__

            {j_bar}   __{math.floor(j)}%__"""
        defalt_name = "Defalt name will apply"
        if playlist_name and video_count > 1:
            rename_name = playlist_name + " - Part " + str(x + video_start_with)
        else:
            rename_name = defalt_name

        info_dict = None
        # Try each download option until one succeeds
        for attempt in attempts:
            info_dict = try_download(url, attempt, total_process)
            if info_dict is not None:
                # Video downloaded successfully
                break
        if info_dict is None:
            send_to_all(message, "❌ Failed to download video. Check if your site is suported [here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). If so - you may need `Cookie` for downloading this video. Please get Youtube's `cookie` via /download_cookie command or send your own cookie from any site ([guide1](https://t.me/c/2303231066/18)) ([guide2](https://t.me/c/2303231066/22)) and after that send your video link again.")
            continue  # move to the next video if available

        # Increment counter when download succeeds
        successful_uploads += 1

        # After download, continue with standard processing:
        video_id = info_dict.get("id", None)
        video_title = info_dict.get('title', None)
        # Determine the expected filename
        expected_video_name = str(video_title) + ".mp4"
        info_text = f"""
{total_process}

**<<<** __Info__ **>>>**

**Video number:** {x + video_start_with}
**Video Name:** __{video_title}__
**Caption Name:** __{rename_name}__
**Video id:** {video_id}"""

        app.edit_message_text(user_id, plus_one, f"{info_text}\n \n__Downloaded video. Processing for upload...__ ♻️")

        ###############################################################################################################################
        # Uploading part: locate the downloaded file
        dir_path = os.path.join("users", str(user_id))
        allfiles = os.listdir(dir_path)
        # Look for files with .mp4, .mkv, or .webm extensions
        files = [fname for fname in allfiles if fname.endswith(('.mp4', '.mkv', '.webm'))]
        files.sort()
        if not files:
            send_to_all(message, "❌ File not found after download.")
            continue

        downloaded_file = files[0]
        write_logs(message, url, downloaded_file)

        # If the filename does not match the expected name and a different name is provided, rename the file
        if rename_name == defalt_name:
            caption_name = os.path.splitext(downloaded_file)[0]
            final_name = downloaded_file
        else:
            # Preserve the original file extension
            ext = os.path.splitext(downloaded_file)[1]
            final_name = rename_name + ext
            caption_name = rename_name
            os.rename(os.path.join(dir_path, downloaded_file), os.path.join(dir_path, final_name))

        user_vid_path = os.path.join(dir_path, final_name)
        # If the file is in webm format, convert it to mp4 for inline playback
        if final_name.lower().endswith(".webm"):
            mp4_file = os.path.join(dir_path, os.path.splitext(final_name)[0] + ".mp4")
            ffmpeg_convert_cmd = [
                "ffmpeg",
                "-y",  # overwrite output file without asking
                "-i", user_vid_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                mp4_file
            ]
            try:
                subprocess.run(ffmpeg_convert_cmd, check=True)
                # Remove the original webm file after successful conversion
                os.remove(user_vid_path)
                # Update the path and filename to the converted file
                user_vid_path = mp4_file
                final_name = os.path.basename(mp4_file)
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
            app.edit_message_text(user_id, plus_one, f"{info_text}\n \n__⚠️ Your video size ({video_size}) is too large.__\n__Splitting file...__ ✂️")
            returned = split_video_2(dir_path, caption_name, after_rename_abs_path,
                                     int(video_size_in_bytes), max_size, duration)
            caption_lst = returned.get("video")
            path_lst = returned.get("path")
            for p in range(len(caption_lst)):
                part_duration, splited_thumb_dir = get_duration_thumb(message, dir_path, path_lst[p], caption_lst[p])
                send_videos(message, path_lst[p], caption_lst[p], part_duration, splited_thumb_dir, info_text, msg_id)
                app.edit_message_text(user_id, plus_one, f"{info_text}\n \n__Splitted part {p + 1} file uploaded__")
                app.forward_messages(Config.LOGS_ID, user_id, (msg_id + 2 + p))
                time.sleep(2)
                os.remove(splited_thumb_dir)
                os.remove(path_lst[p])
            os.remove(thumb_dir)
            os.remove(user_vid_path)
            success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n \n{Config.CREDITS_MSG}"
            app.edit_message_text(user_id, (msg_id + 1), success_msg)
            break
        else:
            if final_name:
                send_videos(message, after_rename_abs_path, caption_name,
                            duration, thumb_dir, info_text, msg_id)
                app.forward_messages(Config.LOGS_ID, user_id, (msg_id + 2 + x))
                app.edit_message_text(user_id, (msg_id + 1), f"{info_text}\n**Video duration:** __{TimeFormatter(duration * 1000)}__\n \n{x + 1} file uploaded.")
                os.remove(after_rename_abs_path)
                os.remove(thumb_dir)
                time.sleep(2)
            else:
                send_to_all(message, "❌ Some error occurred during processing. 😢")

    # Send final summary only if all videos were successfully downloaded/uploaded
    if successful_uploads == video_count:
        success_msg = f"**✅ Upload complete** - {video_count} files uploaded.\n \n{Config.CREDITS_MSG}"
        app.edit_message_text(user_id, (msg_id + 1), success_msg)





#####################################################################################
#####################################################################################
#####################################################################################


# yt-dlp hook
def ytdlp_hook(d):
    print(d['status'])


#####################################################################################
_format = {"ID": '0', "timestamp": math.floor(time.time())}
db.child(f"{Config.BOT_DB_PATH}/users/{str(0)}").set(_format)
db.child(f"{Config.BOT_DB_PATH}/blocked_users/{str(0)}").set(_format)
db.child(f"{Config.BOT_DB_PATH}/unblocked_users/{str(0)}").set(_format)
print("db created")
starting_point.append(time.time())
print("Bot started")
app.run()
