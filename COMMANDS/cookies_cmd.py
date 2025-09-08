
# Command to Set Browser Cookies and Auto-Update YouTube Cookies
from pyrogram import filters, enums
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app

from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel
from HELPERS.logger import send_to_logger, logger, send_to_user, send_to_all
from HELPERS.filesystem_hlp import create_directory
from HELPERS.safe_messeger import fake_message, safe_send_message, safe_edit_message_text
from pyrogram.errors import FloodWait
import subprocess
import os
import requests
import re
import time
from requests import Session
from requests.adapters import HTTPAdapter
import yt_dlp
import random
from HELPERS.pot_helper import add_pot_to_ytdl_opts

# Get app instance for decorators
app = get_app()

# Cache for YouTube cookie validation results
# Format: {user_id: {'result': bool, 'timestamp': float, 'cookie_path': str}}
_youtube_cookie_cache = {}
_CACHE_DURATION = 30  # Cache results for 30 seconds

# Round-robin pointer for YouTube cookie sources
_yt_round_robin_index = 0

@app.on_message(filters.command("cookies_from_browser") & filters.private)
# @reply_with_keyboard
def cookies_from_browser(app, message):
    """
    Позволяет пользователю выбрать браузер для извлечения куки.
    
    Функционал:
    - Определяет установленные браузеры
    - Показывает меню выбора
    - Fallback на COOKIE_URL если браузеры не найдены
    
    Args:
        app: Экземпляр приложения
        message: Сообщение команды
    """
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

    # If there are no installed browsers, fallback: download from COOKIE_URL
    if not installed_browsers:
        fallback_url = getattr(Config, "COOKIE_URL", None)
        if not fallback_url:
            safe_send_message(
                user_id,
                "❌ No supported browsers found and no COOKIE_URL configured. Use /cookie or upload cookie.txt.",
                message=message
            )
            send_to_logger(message, "No installed browsers found. COOKIE_URL is not configured.")
            return

        user_dir = os.path.join(".", "users", str(user_id))
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_dir, cookie_filename)

        try:
            ok, status, content, err = _download_content(fallback_url, timeout=30)
            if ok:
                # basic validation
                if not fallback_url.lower().endswith('.txt'):
                    safe_send_message(user_id, "❌ Fallback COOKIE_URL must point to a .txt file.", message=message)
                    send_to_logger(message, "COOKIE_URL does not end with .txt (hidden)")
                    return
                if len(content or b"") > 100 * 1024:
                    safe_send_message(user_id, "❌ Fallback cookie file is too large (>100KB).", message=message)
                    send_to_logger(message, "Fallback cookie too large (source hidden)")
                    return
                with open(cookie_file_path, "wb") as f:
                    f.write(content)
                safe_send_message(user_id, "✅ YouTube cookie file downloaded via fallback and saved as cookie.txt", message=message)
                send_to_logger(message, "Fallback COOKIE_URL used successfully (source hidden)")
            else:
                if status is not None:
                    safe_send_message(user_id, f"❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt.", message=message)
                    send_to_logger(message, f"Fallback COOKIE_URL failed: status={status} (hidden)")
                else:
                    safe_send_message(user_id, "❌ Error downloading fallback cookie. Try /cookie or upload cookie.txt.", message=message)
                    safe_err = _sanitize_error_detail(err or "", fallback_url)
                    send_to_logger(message, f"Fallback COOKIE_URL error: {safe_err}")
        except Exception as e:
            safe_send_message(user_id, "❌ Unexpected error during fallback cookie download.", message=message)
            send_to_logger(message, f"Fallback COOKIE_URL unexpected error: {type(e).__name__}: {e}")
        return

    # Create buttons only for installed browsers
    buttons = []
    for browser in installed_browsers:
        display_name = browser.capitalize()
        button = InlineKeyboardButton(f"✅ {display_name}", callback_data=f"browser_choice|{browser}")
        buttons.append([button])

    # Add a close button
    buttons.append([InlineKeyboardButton("🔚Close", callback_data="browser_choice|close")])
    keyboard = InlineKeyboardMarkup(buttons)

    safe_send_message(
        user_id,
        "Select a browser to download cookies from:",
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, "Browser selection keyboard sent with installed browsers only.")

# Callback Handler for Browser Selection
@app.on_callback_query(filters.regex(r"^browser_choice\|"))
# @reply_with_keyboard
def browser_choice_callback(app, callback_query):
    """
    Обрабатывает выбор браузера для извлечения куки.
    
    Функционал:
    - Извлекает куки из выбранного браузера
    - Проверяет работоспособность куки
    - Сохраняет только рабочие куки
    
    Args:
        app: Экземпляр приложения
        callback_query: Callback запрос с выбором браузера
    """
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
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"⚠️ {browser_option.capitalize()} browser not installed.")
        try:
            callback_query.answer("⚠️ Browser not installed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, f"Browser {browser_option} not installed.")
        return

    # Build the command for cookie extraction: yt-dlp --cookies "cookie.txt" --cookies-from-browser <browser_option>
    cmd = f'yt-dlp --cookies "{cookie_file}" --cookies-from-browser {browser_option}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')

    if result.returncode != 0:
        if "You must provide at least one URL" in result.stderr:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"✅ Cookies saved using browser: {browser_option}")
            send_to_logger(callback_query.message, f"Cookies saved using browser: {browser_option}")
        else:
            safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"❌ Failed to save cookies: {result.stderr}")
            send_to_logger(callback_query.message,
                           f"Failed to save cookies using browser {browser_option}: {result.stderr}")
    else:
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"✅ Cookies saved using browser: {browser_option}")
        send_to_logger(callback_query.message, f"Cookies saved using browser: {browser_option}")

    callback_query.answer("✅ Browser choice updated.")

#############################################################################################################################

# SEND COOKIE VIA Document
@app.on_message(filters.document & filters.private)
@reply_with_keyboard
def save_my_cookie(app, message):
    """
    Сохраняет куки, загруженные пользователем как документ.
    
    Проверяет:
    - Размер файла (максимум 100KB)
    - Расширение (.txt)
    - Формат (Netscape HTTP Cookie File)
    
    Args:
        app: Экземпляр приложения
        message: Сообщение с документом
    """
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
    """
    Обрабатывает выбор сервиса для скачивания куки.
    
    Поддерживаемые сервисы:
    - YouTube (с проверкой работоспособности)
    - Instagram, Twitter, TikTok, Facebook
    - Собственные куки пользователя
    - Извлечение из браузера
    
    Args:
        app: Экземпляр приложения
        callback_query: Callback запрос с выбором сервиса
    """
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "youtube":
        # Send initial message about starting the process
        safe_edit_message_text(
            callback_query.message.chat.id, 
            callback_query.message.id, 
            "🔄 Starting YouTube cookies test...\n\nPlease wait while I check and validate your cookies."
        )
        download_and_validate_youtube_cookies(app, callback_query)
    #elif data == "instagram":
        #download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "vk":
        download_and_save_cookie(app, callback_query, Config.VK_COOKIE_URL, "vk")
    elif data == "check_cookie":
        try:
            # Run cookie checking directly using a fake message
            checking_cookie_file(app, fake_message(Config.CHECK_COOKIE_COMMAND, user_id))
            try:
                app.answer_callback_query(callback_query.id)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to trigger check_cookie from cookie menu: {e}")
            try:
                app.answer_callback_query(callback_query.id, "❌ Failed to run /check_cookie", show_alert=False)
            except Exception:
                pass
    #elif data == "facebook":
        #download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
    elif data == "own":
        try:
            app.answer_callback_query(callback_query.id)
        except Exception:
            pass
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="save_as_cookie_hint|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        safe_send_message(
            callback_query.message.chat.id,
            Config.SAVE_AS_COOKIE_HINT,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id if hasattr(callback_query.message, 'id') else None),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice="⏳ Flood limit. Try later."
        )
    elif data == "from_browser":
        try:
            cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                app.answer_callback_query(callback_query.id, "⏳ Flood limit. Try later.", show_alert=False)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to start cookies_from_browser: {e}")
            try:
                app.answer_callback_query(callback_query.id, "❌ Failed to open browser cookie menu", show_alert=True)
            except Exception:
                pass
    elif data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Menu closed.")
        return

@app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))
def save_as_cookie_hint_callback(app, callback_query):
    """
    Обрабатывает закрытие подсказки о сохранении куки.
    
    Args:
        app: Экземпляр приложения
        callback_query: Callback запрос
    """
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
    """
    Проверяет существующий файл куки пользователя.
    
    Проверяет:
    - Существование файла куки
    - Правильность формата (Netscape HTTP Cookie File)
    - Наличие YouTube доменов
    - Работоспособность куки через test_youtube_cookies()
    """
    user_id = str(message.chat.id)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    file_path = os.path.join("users", user_id, cookie_filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as cookie:
            cookie_content = cookie.read()
        if cookie_content.startswith("# Netscape HTTP Cookie File"):
            # Check the functionality of YouTube cookies
            from HELPERS.safe_messeger import safe_send_message
            initial_msg = safe_send_message(message.chat.id, "✅ Cookie file exists and has correct format", parse_mode=enums.ParseMode.HTML)
            
            # Check if the file contains YouTube cookies (by domain column)
            def _has_youtube_domain(text: str) -> bool:
                for raw in text.split('\n'):
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Split by tabs or spaces, domain is the first column
                    parts = line.split('\t') if '\t' in line else line.split()
                    if not parts:
                        continue
                    domain = parts[0].lower()
                    if 'youtube.com' in domain:
                        return True
                return False
            if _has_youtube_domain(cookie_content):
                if test_youtube_cookies(file_path):
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        safe_edit_message_text(message.chat.id, initial_msg.id, "✅ YouTube cookies are working properly")
                    send_to_logger(message, "Cookie file exists, has correct format, and YouTube cookies are working.")
                else:
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        safe_edit_message_text(message.chat.id, initial_msg.id, "❌ YouTube cookies are expired or invalid\n\nUse /cookie to get new cookies")
                    send_to_logger(message, "Cookie file exists and has correct format, but YouTube cookies are expired.")
            else:
                send_to_user(message, "✅ Skipped validation for non-YouTube cookies")
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
    Показывает меню с кнопками для скачивания файлов куки с разных сервисов.
    
    Поддерживаемые сервисы:
    - YouTube, Instagram, Twitter/X, TikTok, Facebook
    - Собственные куки пользователя
    - Извлечение из браузера
    
    Args:
        app: Экземпляр приложения
        message: Сообщение команды
    """
    user_id = str(message.chat.id)
    
    # Check for fast command with arguments: /cookie youtube, /cookie youtube <n>, /cookie instagram, etc.
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            service = parts[1].lower()
            if service == "youtube":
                # Handle YouTube cookies directly
                user_id = str(message.chat.id)
                user_dir = os.path.join("users", user_id)
                create_directory(user_dir)
                cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
                cookie_file_path = os.path.join(user_dir, cookie_filename)
                
                # Send initial message
                send_to_user(message, "🔄 Starting YouTube cookies test...\n\nPlease wait while I check and validate your cookies.")
                
                # Check existing cookies first
                if os.path.exists(cookie_file_path):
                    if test_youtube_cookies(cookie_file_path):
                        send_to_user(message, "✅ Your existing YouTube cookies are working properly!\n\nNo need to download new ones.")
                        return
                    else:
                        send_to_user(message, "❌ Your existing YouTube cookies are expired or invalid.\n\n🔄 Downloading new cookies...")
                # Optional specific index: /cookie youtube <n>
                selected_index = None
                if len(parts) >= 3 and parts[2].isdigit():
                    try:
                        selected_index = int(parts[2])
                    except Exception:
                        selected_index = None
                # Download and validate new cookies (optionally a specific source)
                download_and_validate_youtube_cookies(app, message, selected_index=selected_index)
                return
            elif service in ["instagram", "twitter", "tiktok", "facebook", "own", "from_browser", "vk"]:
                # Fast command - directly call the callback
                fake_callback = fake_message(f"/cookie {service}", user_id)
                fake_callback.data = f"download_cookie|{service}"
                fake_callback.from_user = message.from_user
                fake_callback.message = message
                download_cookie_callback(app, fake_callback)
                return
    except Exception as e:
        logger.error(f"Error in fast command handling: {e}")
        pass
    
    # Buttons for services
    buttons = [
        [
            InlineKeyboardButton(
                f"📺 YouTube (1-{max(1, len(get_youtube_cookie_urls()))})",
                callback_data="download_cookie|youtube"
            ),
            InlineKeyboardButton("🌐 From Browser (YouTube)", callback_data="download_cookie|from_browser"),            
        ],
        [
            InlineKeyboardButton("🐦 Twitter/X", callback_data="download_cookie|twitter"),
            InlineKeyboardButton("🎵 TikTok", callback_data="download_cookie|tiktok"),
        ],
        [
            InlineKeyboardButton("📘 Vkontakte", callback_data="download_cookie|vk"),
            InlineKeyboardButton("✅ Check Cookie", callback_data="download_cookie|check_cookie"),
        ],
        #[
            #InlineKeyboardButton("📘 Facebook", callback_data="download_cookie|facebook"),
            #InlineKeyboardButton("📷 Instagram", callback_data="download_cookie|instagram"),
        #],
        [
            InlineKeyboardButton("📝 Your Own", callback_data="download_cookie|own"),            
            InlineKeyboardButton("🔚Close", callback_data="download_cookie|close")
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = f"""
🍪 <b>Download Cookie Files</b>

Choose a service to download the cookie file.
Cookie files will be saved as cookie.txt in your folder.

<blockquote>
Tip: You can also use direct command:
• <code>/cookie youtube</code> – download and validate cookies
• <code>/cookie youtube 1</code> – use a specific source by index (1–{len(get_youtube_cookie_urls())})
Then verify with <code>/check_cookie</code> (tests on RickRoll).
</blockquote>
"""
    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        reply_parameters=ReplyParameters(message_id=message.id)
    )




def _sanitize_error_detail(detail: str, url: str) -> str:
    """
    Очищает детали ошибки от чувствительной информации (URL).
    
    Args:
        detail (str): Детали ошибки
        url (str): URL для скрытия
        
    Returns:
        str: Очищенная строка ошибки
    """
    try:
        return (detail or "").replace(url or "", "<hidden-url>")
    except Exception:
        return "<hidden>"

def _download_content(url: str, timeout: int = 30):
    """Скачивает бинарный контент используя короткоживущую сессию с малым пулом и Connection: close.
    
    Args:
        url (str): URL для скачивания
        timeout (int): Таймаут в секундах
        
    Returns:
        tuple: (ok: bool, status_code: int|None, content: bytes|None, error: str|None)
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
    """
    Скачивает и сохраняет куки для указанного сервиса.
    
    Args:
        app: Экземпляр приложения
        callback_query: Callback запрос
        url (str): URL для скачивания куки
        service (str): Название сервиса (youtube, instagram, etc.)
    """
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
    """
    Сохраняет куки, предоставленные пользователем в текстовом виде.
    
    Обрабатывает:
    - Текст в блоках кода (```)
    - Обычный текст
    - Автоматически заменяет множественные пробелы на табуляцию
    
    Args:
        app: Экземпляр приложения
        message: Сообщение с куки
    """
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

def test_youtube_cookies(cookie_file_path: str) -> bool:
    """
    Тщательно проверяет работоспособность YouTube куки.
    
    Проверяет:
    - Получение полной информации о видео (title, duration, uploader, view_count, like_count, upload_date)
    - Наличие доступных форматов для скачивания
    - Качество полученной информации (длина заголовка, разумная длительность)
    - Минимальное количество форматов (не менее 3)
    
    Returns:
        bool: True если куки работают корректно, False если нет
    """
    try:
        # Test URL - use a short YouTube video for testing
        test_url = Config.YOUTUBE_COOKIE_TEST_URL
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'format': 'best',
            'ignore_no_formats_error': False,  # Changed to False to catch format errors
            'cookiefile': cookie_file_path,
            'extractor_args': {
                'youtube': {'player_client': ['tv']}
            },
            'retries': 3,
            'extractor_retries': 2,
        }
        
        # Add PO token provider for YouTube domains
        ydl_opts = add_pot_to_ytdl_opts(ydl_opts, test_url)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        # Проверяем, что получили полную информацию о видео
        required_fields = ['title', 'duration', 'uploader', 'view_count', 'like_count', 'upload_date']
        if not info:
            logger.warning(f"YouTube cookies test failed - no info returned for {cookie_file_path}")
            return False
            
        # Проверяем наличие обязательных полей
        missing_fields = [field for field in required_fields if field not in info or not info[field]]
        if missing_fields:
            logger.warning(f"YouTube cookies test failed - missing fields: {missing_fields} for {cookie_file_path}")
            logger.warning(f"Available fields: {list(info.keys())}")
            return False
            
        # Проверяем, что есть доступные форматы для скачивания
        if 'formats' not in info or not info['formats']:
            logger.warning(f"YouTube cookies test failed - no formats available for {cookie_file_path}")
            logger.warning(f"Info keys: {list(info.keys())}")
            return False
            
        # Проверяем качество полученной информации
        title = info.get('title', '')
        if len(title) < 5:  # Заголовок должен быть достаточно длинным
            logger.warning(f"YouTube cookies test failed - title too short: '{title}' for {cookie_file_path}")
            logger.warning(f"Title length: {len(title)}")
            return False
            
        # Проверяем, что duration разумная (не 0 и не слишком большая)
        duration = info.get('duration', 0)
        if duration <= 0 or duration > 86400:  # Больше 24 часов
            logger.warning(f"YouTube cookies test failed - invalid duration: {duration} for {cookie_file_path}")
            logger.warning(f"Duration in seconds: {duration}")
            return False
            
        # Проверяем количество форматов (должно быть достаточно для выбора)
        formats_count = len(info['formats'])
        if formats_count < 3:  # Минимум 3 формата для выбора
            logger.warning(f"YouTube cookies test failed - too few formats: {formats_count} for {cookie_file_path}")
            logger.warning(f"Available formats: {[f.get('format_id', 'unknown') for f in info['formats'][:5]]}")
            logger.warning(f"All format IDs: {[f.get('format_id', 'unknown') for f in info['formats']]}")
            return False
            
        logger.info(f"YouTube cookies test passed for {cookie_file_path} - {formats_count} formats available")
        logger.info(f"Title: '{title}'")
        logger.info(f"Duration: {duration}s")
        logger.info(f"Uploader: {info.get('uploader', 'N/A')}")
        logger.info(f"View count: {info.get('view_count', 'N/A')}")
        logger.info(f"Upload date: {info.get('upload_date', 'N/A')}")
        logger.info(f"Like count: {info.get('like_count', 'N/A')}")
        logger.info(f"Format IDs: {[f.get('format_id', 'unknown') for f in info['formats'][:10]]}")
        return True
            
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e).lower()
        logger.warning(f"YouTube cookies test failed with DownloadError: {e}")
        # Check for specific YouTube errors
        if any(keyword in error_text for keyword in [
            'sign in', 'login required', 'private video', 'age restricted',
            'video unavailable', 'cookies', 'authentication', 'format not found',
            'no formats found', 'unable to extract'
        ]):
            logger.warning(f"YouTube cookies test failed - authentication/format error: {e}")
            return False
        else:
            # Other errors may not be related to cookies
            logger.warning(f"YouTube cookies test - other error (may not be cookie-related): {e}")
            return False
            
    except Exception as e:
        logger.error(f"YouTube cookies test failed with exception: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

def get_youtube_cookie_urls() -> list:
    """
    Возвращает список URL для YouTube куки в порядке приоритета.
    
    Проверяет:
    - Основной YOUTUBE_COOKIE_URL
    - Пронумерованные YOUTUBE_COOKIE_URL_1, YOUTUBE_COOKIE_URL_2, etc.
    
    Returns:
        list: Список URL для скачивания куки
    """
    urls = []
    
    # Check the main URLs in order of priority
    if hasattr(Config, 'YOUTUBE_COOKIE_URL') and Config.YOUTUBE_COOKIE_URL:
        urls.append(Config.YOUTUBE_COOKIE_URL)
    
    # Add numbered URLs
    for i in range(1, 10):  # Support up to 9 URLs
        url_attr = f'YOUTUBE_COOKIE_URL_{i}'
        if hasattr(Config, url_attr):
            url_value = getattr(Config, url_attr)
            if url_value:
                urls.append(url_value)
    
    return urls

def download_and_validate_youtube_cookies(app, message, selected_index: int | None = None) -> bool:
    """
    Скачивает и проверяет YouTube куки из всех доступных источников.
    
    Процесс:
    1. Скачивает куки из каждого источника по очереди
    2. Тщательно проверяет их работоспособность через test_youtube_cookies()
    3. Сохраняет только рабочие куки
    4. Если ни один источник не работает, сообщает об ошибке
    
    Args:
        app: Экземпляр приложения
        message: Сообщение команды или callback_query
    
    Returns:
        bool: True если найдены рабочие куки, False если нет
    """
    # Handle both message and callback_query objects
    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
        user_id = str(message.chat.id)
    elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
        user_id = str(message.from_user.id)
    else:
        logger.error("Cannot determine user_id from message object")
        return False
    
    # Create a helper function to send messages safely
    def safe_send_to_user(msg):
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                # It's a Message object
                from HELPERS.logger import send_to_user
                send_to_user(message, msg)
            elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                # It's a CallbackQuery object
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(message.from_user.id, msg, parse_mode=enums.ParseMode.HTML)
            else:
                # Fallback - try to get user_id and send directly
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error sending message to user: {e}")
            # Try direct send as last resort
            try:
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
            except Exception as e2:
                logger.error(f"Final fallback send failed: {e2}")
    
    cookie_urls = get_youtube_cookie_urls()
    
    if not cookie_urls:
        safe_send_to_user("❌ YouTube cookie sources are not configured!")
        # Safe logging
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                send_to_logger(message, f"YouTube cookie URLs are empty for user {user_id}.")
            else:
                logger.error(f"YouTube cookie URLs are empty for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging: {e}")
        return False
    
    # Create user folder
    user_dir = os.path.join("users", user_id)
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Send initial message and store message ID for updates
    initial_msg = None
    try:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            # It's a Message object - send initial message
            from HELPERS.logger import send_to_user
            initial_msg = send_to_user(message, f"🔄 Downloading and checking YouTube cookies...\n\nAttempt 1 of {len(cookie_urls)}")
        elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
            # It's a CallbackQuery object - send initial message
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = safe_send_message(message.from_user.id, f"🔄 Downloading and checking YouTube cookies...\n\nAttempt 1 of {len(cookie_urls)}", parse_mode=enums.ParseMode.HTML)
        else:
            # Fallback - send directly
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = safe_send_message(user_id, f"🔄 Downloading and checking YouTube cookies...\n\nAttempt 1 of {len(cookie_urls)}", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error sending initial message: {e}")
    
    # Helper function to update the message (avoid MESSAGE_NOT_MODIFIED)
    _last_update_text = { 'text': None }
    def update_message(new_text):
        try:
            if new_text == _last_update_text['text']:
                return
            if initial_msg and hasattr(initial_msg, 'id'):
                if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                    app.edit_message_text(message.chat.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                    app.edit_message_text(message.from_user.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                else:
                    app.edit_message_text(user_id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                _last_update_text['text'] = new_text
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" in str(e):
                return
            logger.error(f"Error updating message: {e}")
    
    # Determine the order of attempts
    indices = list(range(len(cookie_urls)))
    global _yt_round_robin_index
    if selected_index is not None:
        # Use a specific 1-based index
        if 1 <= selected_index <= len(cookie_urls):
            indices = [selected_index - 1]
        else:
            update_message(f"❌ Invalid YouTube cookie index: {selected_index}. Available range is 1-{len(cookie_urls)}")
            return False
    else:
        order = getattr(Config, 'YOUTUBE_COOKIE_ORDER', 'round_robin')
        if not order:
            order = 'round_robin'
        logger.info(f"YouTube cookie order mode: {order}")
        if order == 'random':
            random.shuffle(indices)
        else:
            # round_robin: rotate starting position
            if len(indices) > 0:
                start = _yt_round_robin_index % len(indices)
                indices = indices[start:] + indices[:start]
                # advance pointer for next call
                _yt_round_robin_index = (start + 1) % len(indices)
        logger.info(f"YouTube cookie indices order: {[i+1 for i in indices]}")

    # Iterate over chosen order
    for attempt_number, idx in enumerate(indices, 1):
        url = cookie_urls[idx]
        try:
            # Update message about the current attempt
            update_message(f"🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt_number} of {len(indices)}")
            
            # Download cookies
            ok, status, content, err = _download_content(url, timeout=30)
            if not ok:
                logger.warning(f"Failed to download YouTube cookie from URL {idx + 1}: status={status}, error={err}")
                continue
            
            # Check the format and size
            if not url.lower().endswith('.txt'):
                logger.warning(f"YouTube cookie URL {idx + 1} is not .txt file")
                continue
                
            content_size = len(content or b"")
            if content_size > 100 * 1024:
                logger.warning(f"YouTube cookie file {idx + 1} is too large: {content_size} bytes")
                continue
            
            # Save cookies to a temporary file
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Update message about testing
            update_message(f"🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt_number} of {len(indices)}\n🔍 Testing cookies...")
            
            # Check the functionality of cookies
            if test_youtube_cookies(cookie_file_path):
                update_message(f"✅ YouTube cookies successfully downloaded and validated!\n\nUsed source {idx + 1} of {len(cookie_urls)}")
                # Safe logging
                try:
                    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                        send_to_logger(message, f"YouTube cookies downloaded and validated for user {user_id} from source {idx + 1}.")
                    else:
                        logger.info(f"YouTube cookies downloaded and validated for user {user_id} from source {idx + 1}")
                except Exception as e:
                    logger.error(f"Error logging: {e}")
                return True
            else:
                logger.warning(f"YouTube cookies from source {idx + 1} failed validation")
                # Remove non-working cookies
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing YouTube cookie URL {idx + 1}: {e}")
            # Remove the file in case of an error
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # If no source worked
    update_message("❌ All YouTube cookies are expired or unavailable!\n\nContact the bot administrator to replace them.")
    # Safe logging
    try:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            send_to_logger(message, f"All YouTube cookie sources failed for user {user_id}.")
        else:
            logger.error(f"All YouTube cookie sources failed for user {user_id}")
    except Exception as e:
        logger.error(f"Error logging: {e}")
    return False

def ensure_working_youtube_cookies(user_id: int) -> bool:
    """
    Обеспечивает наличие рабочих YouTube куки для пользователя.
    
    Процесс:
    1. Проверяет кеш результатов
    2. Проверяет существующие куки пользователя
    3. Если не работают - скачивает новые из всех источников
    4. Если ни один источник не работает - удаляет куки и возвращает False
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True если есть рабочие куки, False если нет
    """
    global _youtube_cookie_cache
    
    # Check cache first
    current_time = time.time()
    if user_id in _youtube_cookie_cache:
        cache_entry = _youtube_cookie_cache[user_id]
        if current_time - cache_entry['timestamp'] < _CACHE_DURATION:
            # Check if cookie file still exists and hasn't changed
            if os.path.exists(cache_entry['cookie_path']):
                logger.info(f"Using cached YouTube cookie validation result for user {user_id} (cache valid for {_CACHE_DURATION}s)")
                return cache_entry['result']
            else:
                # Cookie file was deleted, remove from cache
                del _youtube_cookie_cache[user_id]
    
    logger.info(f"Starting ensure_working_youtube_cookies for user {user_id}")
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Проверяем существующие куки
    if os.path.exists(cookie_file_path):
        logger.info(f"Checking existing YouTube cookies for user {user_id}")
        if test_youtube_cookies(cookie_file_path):
            logger.info(f"Existing YouTube cookies are working for user {user_id}")
            logger.info(f"Finished ensure_working_youtube_cookies for user {user_id} - existing cookies are working")
            # Cache the successful result
            _youtube_cookie_cache[user_id] = {
                'result': True,
                'timestamp': current_time,
                'cookie_path': cookie_file_path
            }
            return True
        else:
            logger.warning(f"Existing YouTube cookies failed test for user {user_id}, will try to update")
    
    # Если куки нет или не работают, пробуем скачать новые
    cookie_urls = get_youtube_cookie_urls()
    if not cookie_urls:
        logger.warning(f"No YouTube cookie sources configured for user {user_id}")
        # Удаляем нерабочие куки
        if os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)
        # Cache the failed result
        _youtube_cookie_cache[user_id] = {
            'result': False,
            'timestamp': current_time,
            'cookie_path': cookie_file_path
        }
        return False
    
    logger.info(f"Attempting to download working YouTube cookies for user {user_id} from {len(cookie_urls)} sources")
    
    for i, url in enumerate(cookie_urls, 1):
        try:
            logger.info(f"Trying YouTube cookie source {i}/{len(cookie_urls)} for user {user_id}")
            
            # Скачиваем куки
            ok, status, content, err = _download_content(url, timeout=30)
            if not ok:
                logger.warning(f"Failed to download YouTube cookie from URL {i}: status={status}, error={err}")
                continue
            
            # Проверяем формат и размер
            if not url.lower().endswith('.txt'):
                logger.warning(f"YouTube cookie URL {i} is not .txt file")
                continue
                
            content_size = len(content or b"")
            if content_size > 100 * 1024:
                logger.warning(f"YouTube cookie file {i} is too large: {content_size} bytes")
                continue
            
            # Сохраняем куки
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Проверяем работоспособность
            if test_youtube_cookies(cookie_file_path):
                logger.info(f"YouTube cookies from source {i} are working for user {user_id}")
                logger.info(f"Finished ensure_working_youtube_cookies for user {user_id} - working cookies found from source {i}")
                # Cache the successful result
                _youtube_cookie_cache[user_id] = {
                    'result': True,
                    'timestamp': current_time,
                    'cookie_path': cookie_file_path
                }
                return True
            else:
                logger.warning(f"YouTube cookies from source {i} failed validation for user {user_id}")
                # Удаляем нерабочие куки
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing YouTube cookie URL {i} for user {user_id}: {e}")
            # Удаляем файл в случае ошибки
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # Если ни один источник не сработал
    logger.warning(f"All YouTube cookie sources failed for user {user_id}, removing cookie file")
    if os.path.exists(cookie_file_path):
        os.remove(cookie_file_path)
    logger.info(f"Finished ensure_working_youtube_cookies for user {user_id} - no working cookies found")
    # Cache the failed result
    _youtube_cookie_cache[user_id] = {
        'result': False,
        'timestamp': current_time,
        'cookie_path': cookie_file_path
    }
    return False

def is_youtube_cookie_error(error_message: str) -> bool:
    """
    Определяет, связана ли ошибка скачивания с проблемами куков YouTube.
    
    Args:
        error_message (str): Сообщение об ошибке от yt-dlp
        
    Returns:
        bool: True если ошибка связана с куками, False если нет
    """
    error_lower = error_message.lower()
    
    # Ключевые слова, указывающие на проблемы с куками/авторизацией
    cookie_related_keywords = [
        'sign in', 'login required', 'private video', 'age restricted',
        'video unavailable', 'cookies', 'authentication', 'format not found',
        'no formats found', 'unable to extract', 'http error 403',
        'http error 401', 'forbidden', 'unauthorized', 'access denied',
        'this video is not available', 'video is private', 'members only',
        'premium content', 'subscription required', 'copyright', 'dmca'
    ]
    
    return any(keyword in error_lower for keyword in cookie_related_keywords)

def is_youtube_geo_error(error_message: str) -> bool:
    """
    Определяет, связана ли ошибка скачивания с региональными ограничениями YouTube.
    
    Args:
        error_message (str): Сообщение об ошибке от yt-dlp
        
    Returns:
        bool: True если ошибка связана с региональными ограничениями, False если нет
    """
    error_lower = error_message.lower()
    
    # Ключевые слова, указывающие на региональные ограничения
    geo_related_keywords = [
        'region blocked', 'geo-blocked', 'country restricted', 'not available in your country',
        'this video is not available in your country', 'video unavailable in your region',
        'blocked in your region', 'geographic restriction', 'location restricted',
        'not available in this region', 'country not supported', 'regional restriction'
    ]
    
    return any(keyword in error_lower for keyword in geo_related_keywords)

def retry_download_with_proxy(user_id: int, url: str, download_func, *args, **kwargs):
    """
    Повторяет скачивание через прокси при региональных ошибках.
    
    Args:
        user_id (int): ID пользователя
        url (str): URL для скачивания
        download_func: Функция скачивания для повторного вызова
        *args, **kwargs: Аргументы для функции скачивания
        
    Returns:
        Результат успешного скачивания или None если все попытки неудачны
    """
    from URL_PARSERS.youtube import is_youtube_url
    
    # Проверяем только для YouTube URL
    if not is_youtube_url(url):
        return None
    
    logger.info(f"Attempting to retry download with proxy for user {user_id}")
    
    # Получаем конфигурацию прокси
    try:
        from COMMANDS.proxy_cmd import get_proxy_config
        proxy_config = get_proxy_config()
        
        if not proxy_config or 'type' not in proxy_config or 'ip' not in proxy_config or 'port' not in proxy_config:
            logger.warning(f"No proxy configuration available for retry for user {user_id}")
            return None
        
        # Строим URL прокси
        if proxy_config['type'] == 'http':
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
        elif proxy_config['type'] == 'https':
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"https://{proxy_config['ip']}:{proxy_config['port']}"
        elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
        else:
            if proxy_config.get('user') and proxy_config.get('password'):
                proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
        
        logger.info(f"Retrying download with proxy: {proxy_url}")
        
        # Повторяем скачивание с прокси
        try:
            # Добавляем параметр use_proxy=True для функции скачивания
            kwargs['use_proxy'] = True
            result = download_func(*args, **kwargs)
            if result is not None:
                logger.info(f"Download retry with proxy successful for user {user_id}")
                return result
            else:
                logger.warning(f"Download retry with proxy failed for user {user_id}")
                return None
        except Exception as e:
            logger.warning(f"Download retry with proxy failed for user {user_id}: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error setting up proxy retry for user {user_id}: {e}")
        return None

def retry_download_with_different_cookies(user_id: int, url: str, download_func, *args, **kwargs):
    """
    Повторяет скачивание с разными куками при ошибках, связанных с куками.
    
    Args:
        user_id (int): ID пользователя
        url (str): URL для скачивания
        download_func: Функция скачивания для повторного вызова
        *args, **kwargs: Аргументы для функции скачивания
        
    Returns:
        Результат успешного скачивания или None если все попытки неудачны
    """
    from URL_PARSERS.youtube import is_youtube_url
    
    # Проверяем только для YouTube URL
    if not is_youtube_url(url):
        return None
    
    logger.info(f"Attempting to retry download with different cookies for user {user_id}")
    
    # Получаем список источников куков
    cookie_urls = get_youtube_cookie_urls()
    if not cookie_urls:
        logger.warning(f"No YouTube cookie sources available for retry for user {user_id}")
        return None
    
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Определяем порядок попыток
    indices = list(range(len(cookie_urls)))
    global _yt_round_robin_index
    order = getattr(Config, 'YOUTUBE_COOKIE_ORDER', 'round_robin')
    if order == 'random':
        import random
        random.shuffle(indices)
    else:
        # round_robin: начинаем со следующего источника
        if len(indices) > 0:
            start = _yt_round_robin_index % len(indices)
            indices = indices[start:] + indices[:start]
            _yt_round_robin_index = (start + 1) % len(indices)
    
    logger.info(f"Retrying download with cookie sources in order: {[i+1 for i in indices]}")
    
    # Пробуем каждый источник куков
    for attempt, idx in enumerate(indices, 1):
        try:
            logger.info(f"Retry attempt {attempt}/{len(indices)} with cookie source {idx + 1} for user {user_id}")
            
            # Скачиваем куки
            ok, status, content, err = _download_content(cookie_urls[idx], timeout=30)
            if not ok:
                logger.warning(f"Failed to download cookie from source {idx + 1}: status={status}, error={err}")
                continue
            
            # Проверяем формат и размер
            if not cookie_urls[idx].lower().endswith('.txt'):
                logger.warning(f"Cookie URL {idx + 1} is not .txt file")
                continue
                
            content_size = len(content or b"")
            if content_size > 100 * 1024:
                logger.warning(f"Cookie file {idx + 1} is too large: {content_size} bytes")
                continue
            
            # Сохраняем куки
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Проверяем работоспособность
            if test_youtube_cookies(cookie_file_path):
                logger.info(f"Cookie source {idx + 1} is working, retrying download for user {user_id}")
                
                # Обновляем кеш
                current_time = time.time()
                _youtube_cookie_cache[user_id] = {
                    'result': True,
                    'timestamp': current_time,
                    'cookie_path': cookie_file_path
                }
                
                # Повторяем скачивание
                try:
                    result = download_func(*args, **kwargs)
                    if result is not None:
                        logger.info(f"Download retry successful with cookie source {idx + 1} for user {user_id}")
                        return result
                    else:
                        logger.warning(f"Download retry failed with cookie source {idx + 1} for user {user_id}")
                except Exception as e:
                    logger.warning(f"Download retry failed with cookie source {idx + 1} for user {user_id}: {e}")
                    # Проверяем, связана ли ошибка с куками
                    if is_youtube_cookie_error(str(e)):
                        logger.info(f"Error is cookie-related, trying next source for user {user_id}")
                        continue
                    else:
                        logger.info(f"Error is not cookie-related, stopping retry for user {user_id}")
                        return None
            else:
                logger.warning(f"Cookie source {idx + 1} failed validation for user {user_id}")
                # Удаляем нерабочие куки
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing cookie source {idx + 1} for user {user_id}: {e}")
            # Удаляем файл в случае ошибки
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # Если все источники не сработали
    logger.warning(f"All cookie sources failed for retry download for user {user_id}")
    if os.path.exists(cookie_file_path):
        os.remove(cookie_file_path)
    
    # Обновляем кеш
    current_time = time.time()
    _youtube_cookie_cache[user_id] = {
        'result': False,
        'timestamp': current_time,
        'cookie_path': cookie_file_path
    }
    
    return None

def clear_youtube_cookie_cache(user_id: int = None):
    """
    Очищает кеш результатов проверки YouTube куки.
    
    Args:
        user_id (int, optional): ID пользователя для очистки. Если None, очищает весь кеш.
    """
    global _youtube_cookie_cache
    if user_id is None:
        _youtube_cookie_cache.clear()
        logger.info("Cleared all YouTube cookie validation cache")
    else:
        if user_id in _youtube_cookie_cache:
            del _youtube_cookie_cache[user_id]
            logger.info(f"Cleared YouTube cookie validation cache for user {user_id}")
        else:
            logger.info(f"No cache entry found for user {user_id}")
