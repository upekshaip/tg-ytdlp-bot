
# Command to Set Browser Cooks
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app

from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel
from HELPERS.logger import send_to_logger, logger, send_to_user
from HELPERS.filesystem_hlp import create_directory
import subprocess
import os
import requests
import re
from requests import Session
from requests.adapters import HTTPAdapter

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("cookies_from_browser") & filters.private)
# @reply_with_keyboard
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

    # Add a close button
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="browser_choice|close")])
    keyboard = InlineKeyboardMarkup(buttons)

    app.send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard
    )
    send_to_logger(message, "Browser selection keyboard sent with installed browsers only.")

# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
# @reply_with_keyboard
def browser_choice_callback(app, callback_query):
    logger.info(f"[BROWSER] callback: {callback_query.data}")

    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]  # E.G. "Chromium", "Firefox", or "Close"
    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("✅ Browser choice updated.")
        send_to_logger(callback_query.message, "Browser selection closed.")
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
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')

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

#############################################################################################################################

# SEND COOKIE VIA Document
@app.on_message(filters.document & filters.private)
@reply_with_keyboard
def save_my_cookie(app, message):
    user_id = str(message.chat.id)
    # Check file size
    if message.document.file_size > 100 * 1024:
        send_to_all(message, "❌ The file is too large. Maximum size is 100 KB.")
        return
    # Check extension
    if not message.document.file_name.lower().endswith('.txt'):
        send_to_all(message, "❌ Only files of the following format are allowed .txt.")
        return
    # Download the file to a temporary folder to check the contents
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, message.document.file_name)
        app.download_media(message, file_name=tmp_path)
        try:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # read only the first 4 KB
                if '# Netscape HTTP Cookie File' not in content:
                    send_to_all(message, "❌ The file does not look like cookie.txt (there is no line '# Netscape HTTP Cookie File').")
                    return
        except Exception as e:
            send_to_all(message, f"❌ Error reading file: {e}")
            return
        # If all checks are passed - save the file to the user's folder
        user_folder = f"./users/{user_id}"
        create_directory(user_folder)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_folder, cookie_filename)
        import shutil
        shutil.copyfile(tmp_path, cookie_file_path)
    send_to_user(message, "✅ Cookie file saved")
    send_to_logger(message, f"Cookie file saved for user {user_id}.")

@app.on_callback_query(filters.regex(r"^download_cookie\|"))
# @reply_with_keyboard
def download_cookie_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "youtube":
        download_and_save_cookie(app, callback_query, Config.YOUTUBE_COOKIE_URL, "youtube")
    elif data == "instagram":
        download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "facebook":
        download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
    elif data == "own":
        app.answer_callback_query(callback_query.id)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="save_as_cookie_hint|close")]
        ])
        app.send_message(
            callback_query.message.chat.id,
            Config.SAVE_AS_COOKIE_HINT,
            reply_to_message_id=callback_query.message.id if hasattr(callback_query.message, 'id') else None,
            reply_markup=keyboard
        )
    elif data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        return

@app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))
def save_as_cookie_hint_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Cookie hint closed.")
        send_to_logger(callback_query.message, "Save as cookie hint closed.")
        return

# Called from url_distractor - no decorator needed
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


# @reply_with_keyboard
def download_cookie(app, message):
    """
    Shows a menu with buttons to download cookie files from different services.
    """
    user_id = str(message.chat.id)
    
    # Buttons for services
    buttons = [
        [
            InlineKeyboardButton("📺 YouTube", callback_data="download_cookie|youtube"),
            InlineKeyboardButton("📷 Instagram", callback_data="download_cookie|instagram"),
        ],
        [
            InlineKeyboardButton("🐦 Twitter/X", callback_data="download_cookie|twitter"),
            InlineKeyboardButton("🎵 TikTok", callback_data="download_cookie|tiktok"),
        ],
        [
            InlineKeyboardButton("📘 Facebook", callback_data="download_cookie|facebook"),
            InlineKeyboardButton("📝 Your Own", callback_data="download_cookie|own"),
        ],
        [
            InlineKeyboardButton("🔚 Close", callback_data="download_cookie|close"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = """
🍪 <b>Download Cookie Files</b>

Choose a service to download the cookie file.
Cookie files will be saved as cookie.txt in your folder.
"""
    app.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        reply_to_message_id=message.id
    )




def _sanitize_error_detail(detail: str, url: str) -> str:
    try:
        return (detail or "").replace(url or "", "<hidden-url>")
    except Exception:
        return "<hidden>"

def _download_content(url: str, timeout: int = 30):
    """Download binary content using a short-lived Session with small pool and Connection: close.
    Returns (ok: bool, status_code: int|None, content: bytes|None, error: str|None)
    """
    if not url:
        return False, None, None, "empty-url"
    sess = Session()
    try:
        sess.headers.update({'User-Agent': 'tg-ytdlp-bot/1.0', 'Connection': 'close'})
        adapter = HTTPAdapter(pool_connections=2, pool_maxsize=4, max_retries=2, pool_block=False)
        sess.mount('http://', adapter)
        sess.mount('https://', adapter)
        resp = sess.get(url, timeout=timeout)
        status = resp.status_code
        if status == 200:
            data = resp.content
            resp.close()
            return True, status, data, None
        else:
            resp.close()
            return False, status, None, f"http-status-{status}"
    except requests.exceptions.RequestException as e:
        return False, None, None, f"{type(e).__name__}: {e}"
    finally:
        try:
            sess.close()
        except Exception:
            pass

def download_and_save_cookie(app, callback_query, url, service):
    user_id = str(callback_query.from_user.id)

    # Validate config
    if not url:
        send_to_user(callback_query.message, f"❌ {service.capitalize()} cookie source is not configured!")
        send_to_logger(callback_query.message, f"{service.capitalize()} cookie URL is empty for user {user_id}.")
        return

    try:
        ok, status, content, err = _download_content(url, timeout=30)
        if ok:
            # Optional: validate extension (do not expose URL); keep internal check
            if not url.lower().endswith('.txt'):
                send_to_user(callback_query.message, f"❌ {service.capitalize()} cookie source must be a .txt file!")
                send_to_logger(callback_query.message, f"{service.capitalize()} cookie URL is not .txt (hidden)")
                return
            # size check (max 100KB)
            content_size = len(content or b"")
            if content_size > 100 * 1024:
                send_to_user(callback_query.message, f"❌ {service.capitalize()} cookie file is too large! Max 100KB, got {content_size // 1024}KB.")
                send_to_logger(callback_query.message, f"{service.capitalize()} cookie file too large: {content_size} bytes (source hidden)")
                return
            # Save to user folder
            user_dir = os.path.join("users", user_id)
            create_directory(user_dir)
            cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
            file_path = os.path.join(user_dir, cookie_filename)
            with open(file_path, "wb") as cf:
                cf.write(content)
            send_to_user(callback_query.message, f"<b>✅ {service.capitalize()} cookie file downloaded and saved as cookie.txt in your folder.</b>")
            send_to_logger(callback_query.message, f"{service.capitalize()} cookie file downloaded for user {user_id} (source hidden).")
        else:
            # Do not leak URL in user-facing errors
            if status is not None:
                send_to_user(callback_query.message, f"❌ {service.capitalize()} cookie source is unavailable (status {status}). Please try again later.")
                send_to_logger(callback_query.message, f"Failed to download {service.capitalize()} cookie: status={status} (url hidden)")
            else:
                send_to_user(callback_query.message, f"❌ Error downloading {service.capitalize()} cookie file. Please try again later.")
                safe_err = _sanitize_error_detail(err or "", url)
                send_to_logger(callback_query.message, f"Error downloading {service.capitalize()} cookie: {safe_err} (url hidden)")
    except Exception as e:
        send_to_user(callback_query.message, f"❌ Error downloading {service.capitalize()} cookie file. Please try again later.")
        send_to_logger(callback_query.message, f"Unexpected error while downloading {service.capitalize()} cookie (url hidden): {type(e).__name__}: {e}")

# Updating The Cookie File.
# @reply_with_keyboard
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
        send_to_all(message, "<b>✅ User provided a new cookie file.</b>")
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_cookie)
        send_to_user(message, f"<b>✅ Cookie successfully updated:</b>\n<code>{final_cookie}</code>")
        send_to_logger(message, f"Cookie file updated for user {user_id}.")
    else:
        send_to_user(message, "<b>❌ Not a valid cookie.</b>")
        send_to_logger(message, f"Invalid cookie content provided by user {user_id}.")
