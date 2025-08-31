
# Command to Set Browser Cookies and Auto-Update YouTube Cookies
from pyrogram import filters
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
from requests import Session
from requests.adapters import HTTPAdapter
import yt_dlp
import time

# Get app instance for decorators
app = get_app()

# Cache for YouTube cookie validation results
# Format: {user_id: {'result': bool, 'timestamp': float, 'cookie_path': str}}
_youtube_cookie_cache = {}
_CACHE_DURATION = 30  # Cache results for 30 seconds

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
                "❌ No supported browsers found and no COOKIE_URL configured. Use /cookie or upload cookie.txt."
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
                    safe_send_message(user_id, "❌ Fallback COOKIE_URL must point to a .txt file.")
                    send_to_logger(message, "COOKIE_URL does not end with .txt (hidden)")
                    return
                if len(content or b"") > 100 * 1024:
                    safe_send_message(user_id, "❌ Fallback cookie file is too large (>100KB).")
                    send_to_logger(message, "Fallback cookie too large (source hidden)")
                    return
                with open(cookie_file_path, "wb") as f:
                    f.write(content)
                safe_send_message(user_id, "✅ YouTube cookie file downloaded via fallback and saved as cookie.txt")
                send_to_logger(message, "Fallback COOKIE_URL used successfully (source hidden)")
            else:
                if status is not None:
                    safe_send_message(user_id, f"❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt.")
                    send_to_logger(message, f"Fallback COOKIE_URL failed: status={status} (hidden)")
                else:
                    safe_send_message(user_id, "❌ Error downloading fallback cookie. Try /cookie or upload cookie.txt.")
                    safe_err = _sanitize_error_detail(err or "", fallback_url)
                    send_to_logger(message, f"Fallback COOKIE_URL error: {safe_err}")
        except Exception as e:
            safe_send_message(user_id, "❌ Unexpected error during fallback cookie download.")
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
        reply_markup=keyboard
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
        download_and_validate_youtube_cookies(app, callback_query)
    elif data == "instagram":
        download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "facebook":
        download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
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
            send_to_user(message, "✅ Cookie file exists and has correct format\n\n🔄 Checking YouTube cookies...")
            
            # Check if the file contains YouTube cookies
            if any(line.strip().endswith('.youtube.com') for line in cookie_content.split('\n') if line.strip() and not line.startswith('#')):
                if test_youtube_cookies(file_path):
                    send_to_user(message, "✅ Cookie file exists and has correct format\n✅ YouTube cookies are working properly")
                    send_to_logger(message, "Cookie file exists, has correct format, and YouTube cookies are working.")
                else:
                    send_to_user(message, "✅ Cookie file exists and has correct format\n❌ YouTube cookies are expired or invalid\n\nUse /cookie to get new cookies")
                    send_to_logger(message, "Cookie file exists and has correct format, but YouTube cookies are expired.")
            else:
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
            InlineKeyboardButton("🌐 From Browser (YouTube)", callback_data="download_cookie|from_browser"),
        ],
        [
            InlineKeyboardButton("🔚Close", callback_data="download_cookie|close"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = """
🍪 <b>Download Cookie Files</b>

Choose a service to download the cookie file.
Cookie files will be saved as cookie.txt in your folder.
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
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video
        
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

def download_and_validate_youtube_cookies(app, callback_query) -> bool:
    """
    Скачивает и проверяет YouTube куки из всех доступных источников.
    
    Процесс:
    1. Скачивает куки из каждого источника по очереди
    2. Тщательно проверяет их работоспособность через test_youtube_cookies()
    3. Сохраняет только рабочие куки
    4. Если ни один источник не работает, сообщает об ошибке
    
    Returns:
        bool: True если найдены рабочие куки, False если нет
    """
    user_id = str(callback_query.from_user.id)
    cookie_urls = get_youtube_cookie_urls()
    
    if not cookie_urls:
        send_to_user(callback_query.message, "❌ YouTube cookie sources are not configured!")
        send_to_logger(callback_query.message, f"YouTube cookie URLs are empty for user {user_id}.")
        return False
    
    # Create user folder
    user_dir = os.path.join("users", user_id)
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Update the message about the start of the process
    safe_edit_message_text(
        callback_query.message.chat.id, 
        callback_query.message.id, 
        "🔄 Downloading and checking YouTube cookies...\n\nAttempt 1 of {len(cookie_urls)}"
    )
    
    for i, url in enumerate(cookie_urls, 1):
        try:
            # Update the message about the current attempt
            safe_edit_message_text(
                callback_query.message.chat.id, 
                callback_query.message.id, 
                f"🔄 Downloading and checking YouTube cookies...\n\nAttempt {i} of {len(cookie_urls)}"
            )
            
            # Download cookies
            ok, status, content, err = _download_content(url, timeout=30)
            if not ok:
                logger.warning(f"Failed to download YouTube cookie from URL {i}: status={status}, error={err}")
                continue
            
            # Check the format and size
            if not url.lower().endswith('.txt'):
                logger.warning(f"YouTube cookie URL {i} is not .txt file")
                continue
                
            content_size = len(content or b"")
            if content_size > 100 * 1024:
                logger.warning(f"YouTube cookie file {i} is too large: {content_size} bytes")
                continue
            
            # Save cookies to a temporary file
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Update message to show testing
            safe_edit_message_text(
                callback_query.message.chat.id, 
                callback_query.message.id, 
                f"🔄 Downloading and checking YouTube cookies...\n\nAttempt {i} of {len(cookie_urls)}\n🔍 Testing cookies..."
            )
            
            # Check the functionality of cookies
            if test_youtube_cookies(cookie_file_path):
                safe_edit_message_text(
                    callback_query.message.chat.id, 
                    callback_query.message.id, 
                    f"✅ YouTube cookies successfully downloaded and validated!\n\nUsed source {i} of {len(cookie_urls)}"
                )
                send_to_logger(callback_query.message, f"YouTube cookies downloaded and validated for user {user_id} from source {i}.")
                return True
            else:
                logger.warning(f"YouTube cookies from source {i} failed validation")
                # Remove non-working cookies
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing YouTube cookie URL {i}: {e}")
            # Remove the file in case of an error
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # If no source worked
    safe_edit_message_text(
        callback_query.message.chat.id, 
        callback_query.message.id, 
        "❌ All YouTube cookies are expired or unavailable!\n\nContact the bot administrator to replace them."
    )
    send_to_logger(callback_query.message, f"All YouTube cookie sources failed for user {user_id}.")
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
