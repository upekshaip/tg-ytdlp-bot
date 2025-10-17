
# Command to Set Browser Cookies and Auto-Update YouTube Cookies
from pyrogram import filters, enums
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app

from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel
from HELPERS.logger import send_to_logger, logger, send_to_user, send_to_all
from HELPERS.filesystem_hlp import create_directory
from HELPERS.safe_messeger import fake_message, safe_send_message, safe_edit_message_text
from pyrogram.errors import FloodWait
import subprocess
from HELPERS.guard import async_subprocess
import os
import requests
from requests import Session
from requests.adapters import HTTPAdapter
import re
import time
import aiohttp
import asyncio
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

# @app.on_message(filters.command("cookies_from_browser") & filters.private)
# @reply_with_keyboard
async def cookies_from_browser(app, message):
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
    if int(user_id) not in Config.ADMIN and not await is_user_in_channel(app, message):
        return

    # Logging a request for cookies from browser
    await send_to_logger(message, safe_get_messages(user_id).COOKIES_BROWSER_REQUESTED_LOG_MSG)

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

    # Always show menu, even if no browsers found

    # Create buttons for installed browsers
    buttons = []
    for browser in installed_browsers:
        display_name = browser.capitalize()
        button = InlineKeyboardButton(safe_get_messages(user_id).COOKIES_BROWSER_BUTTON_MSG.format(browser_name=display_name), callback_data=f"browser_choice|{browser}")
        buttons.append([button])

    # Add a button to download from remote URL (always available)
    fallback_url = getattr(Config, "COOKIE_URL", None)
    if fallback_url:
        buttons.append([InlineKeyboardButton(safe_get_messages(user_id).DOWNLOAD_FROM_URL_BUTTON_MSG, callback_data="browser_choice|download_from_url")])

    # Add a button to open browser monitoring page
    miniapp_url = getattr(Config, 'MINIAPP_URL', None)
    # Use the URL as a regular link instead of WebApp
    if miniapp_url and miniapp_url.startswith('https://t.me/'):
        logger.info(safe_get_messages(user_id).COOKIES_ADDING_BROWSER_MONITORING_MSG.format(miniapp_url=miniapp_url))
        buttons.append([InlineKeyboardButton(safe_get_messages(user_id).BROWSER_OPEN_BUTTON_MSG, url=miniapp_url)])
    else:
        logger.warning(safe_get_messages(user_id).COOKIES_BROWSER_MONITORING_URL_NOT_CONFIGURED_MSG.format(miniapp_url=miniapp_url))

    # Add a close button
    buttons.append([InlineKeyboardButton(safe_get_messages(user_id).BTN_CLOSE, callback_data="browser_choice|close")])
    keyboard = InlineKeyboardMarkup(buttons)

    # Choose message based on whether browsers are found
    if installed_browsers:
        message_text = safe_get_messages(user_id).SELECT_BROWSER_MSG
    else:
        message_text = safe_get_messages(user_id).SELECT_BROWSER_NO_BROWSERS_MSG
    
    if miniapp_url and miniapp_url.startswith('https://t.me/'):
        message_text += f"\n\n{safe_get_messages(user_id).BROWSER_MONITOR_HINT_MSG}"

    await safe_send_message(
        user_id,
        message_text,
        reply_markup=keyboard,
        message=message
    )
    await send_to_logger(message, safe_get_messages(user_id).COOKIES_BROWSER_SELECTION_SENT_LOG_MSG)

# Callback Handler for Browser Selection
# @app.on_callback_query(filters.regex(r"^browser_choice\|"))
# @reply_with_keyboard
async def browser_choice_callback(app, callback_query):
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
    user_id = callback_query.from_user.id
    logger.info(safe_get_messages(user_id).COOKIES_BROWSER_CALLBACK_MSG.format(callback_data=callback_query.data))
    data = callback_query.data.split("|")[1]  # E.G. "Chromium", "Firefox", or "Close"
    # Path to the User's Directory, E.G. "./users/1234567"
    user_dir = os.path.join(".", "users", str(user_id))
    create_directory(user_dir)
    cookie_file = os.path.join(user_dir, "cookie.txt")

    if data == "close":
        try:
            await callback_query.message.delete()
        except Exception:
            await callback_query.edit_message_reply_markup(reply_markup=None)
        await callback_query.answer(safe_get_messages(user_id).COOKIES_MENU_CLOSED_MSG)
        await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_BROWSER_SELECTION_CLOSED_LOG_MSG)
        return

    if data == "download_from_url":
        # Handle download from remote URL
        fallback_url = getattr(Config, "COOKIE_URL", None)
        if not fallback_url:
            await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_NO_BROWSERS_NO_URL_MSG)
            await callback_query.answer(safe_get_messages(user_id).COOKIES_NO_REMOTE_URL_MSG)
            return

        # Update message to show downloading
        await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_DOWNLOADING_FROM_URL_MSG)
        
        try:
            ok, status, content, err = await _download_content(fallback_url, timeout=30)
            if ok:
                # basic validation
                if not fallback_url.lower().endswith('.txt'):
                    await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_URL_NOT_TXT_MSG)
                    await callback_query.answer(safe_get_messages(user_id).COOKIES_INVALID_FILE_FORMAT_MSG)
                    return
                if len(content or b"") > 100 * 1024:
                    await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_TOO_LARGE_MSG)
                    await callback_query.answer(safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_CALLBACK_MSG)
                    return
                with open(cookie_file, "wb") as f:
                    f.write(content)
                await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_YT_FALLBACK_SAVED_MSG)
                await callback_query.answer(safe_get_messages(user_id).COOKIES_DOWNLOADED_SUCCESSFULLY_MSG)
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_SUCCESS_LOG_MSG)
            else:
                if status is not None:
                    await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_UNAVAILABLE_MSG.format(status=status))
                    await callback_query.answer(safe_get_messages(user_id).COOKIES_SERVER_ERROR_MSG.format(status=status))
                else:
                    await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_ERROR_MSG)
                    await callback_query.answer(safe_get_messages(user_id).COOKIES_DOWNLOAD_FAILED_MSG)
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_FAILED_LOG_MSG.format(status=status))
        except Exception as e:
            await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIE_FALLBACK_UNEXPECTED_MSG)
            await callback_query.answer(safe_get_messages(user_id).COOKIES_UNEXPECTED_ERROR_MSG)
            await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_FALLBACK_UNEXPECTED_ERROR_LOG_MSG.format(error_type=type(e).__name__, error=str(e)))
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
        await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_MSG.format(browser=browser_option.capitalize()))
        try:
            await callback_query.answer(safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_CALLBACK_MSG)
        except Exception:
            pass
        await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_BROWSER_NOT_INSTALLED_LOG_MSG.format(browser=browser_option))
        return

    # Build the command for cookie extraction using the same yt-dlp as Python API
    import sys
    cmd = [sys.executable, '-m', 'yt_dlp', '--cookies', str(cookie_file), '--cookies-from-browser', str(browser_option)]
    stdout, stderr = await async_subprocess(*cmd, timeout=60)

    if stderr:
        stderr_text = stderr.decode('utf-8', errors='replace')
        if "You must provide at least one URL" in stderr_text:
            await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_SAVED_USING_BROWSER_MSG.format(browser=browser_option))
            await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SAVED_BROWSER_LOG_MSG.format(browser=browser_option))
        else:
            await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_FAILED_TO_SAVE_MSG.format(error=stderr_text))
            await send_to_logger(callback_query.message,
                           f"Failed to save cookies using browser {browser_option}: {stderr_text}")
    else:
        await safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).COOKIES_SAVED_USING_BROWSER_MSG.format(browser=browser_option))
        await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SAVED_BROWSER_LOG_MSG.format(browser=browser_option))

    await callback_query.answer(safe_get_messages(user_id).COOKIES_BROWSER_CHOICE_UPDATED_MSG)

#############################################################################################################################

# SEND COOKIE VIA Document
# Принимаем cookie.txt не только в личке, но и в группах/топиках
# @app.on_message(filters.document)
@reply_with_keyboard
async def save_my_cookie(app, message):
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
        await send_to_all(message, safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_MSG)
        return
    # Check extension
    if not message.document.file_name.lower().endswith('.txt'):
        await send_to_all(message, safe_get_messages(user_id).COOKIES_INVALID_FORMAT_MSG)
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
                    await send_to_all(message, safe_get_messages(user_id).COOKIES_INVALID_COOKIE_MSG)
                    return
        except Exception as e:
            await send_to_all(message, safe_get_messages(user_id).COOKIES_ERROR_READING_MSG.format(error=e))
            return
        # If all checks are passed - save the file to the user's folder
        user_folder = f"./users/{user_id}"
        create_directory(user_folder)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        cookie_file_path = os.path.join(user_folder, cookie_filename)
        import shutil
        shutil.copyfile(tmp_path, cookie_file_path)
    await send_to_user(message, safe_get_messages(user_id).COOKIES_FILE_SAVED_MSG)
    await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_SAVED_USER_LOG_MSG.format(user_id=user_id))

# @app.on_callback_query(filters.regex(r"^download_cookie\|"))
# @reply_with_keyboard
async def download_cookie_callback(app, callback_query):
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
        await safe_edit_message_text(
            callback_query.message.chat.id, 
            callback_query.message.id, 
            safe_get_messages(user_id).COOKIES_YOUTUBE_TEST_START_MSG
        )
        await download_and_validate_youtube_cookies(app, callback_query, user_id=user_id)
    elif data == "instagram":
        await download_and_save_cookie(app, callback_query, Config.INSTAGRAM_COOKIE_URL, "instagram")
    elif data == "twitter":
        await download_and_save_cookie(app, callback_query, Config.TWITTER_COOKIE_URL, "twitter")
    elif data == "tiktok":
        await download_and_save_cookie(app, callback_query, Config.TIKTOK_COOKIE_URL, "tiktok")
    elif data == "vk":
        await download_and_save_cookie(app, callback_query, Config.VK_COOKIE_URL, "vk")
    elif data == "check_cookie":
        try:
            # Run cookie checking directly using a fake message
            await checking_cookie_file(app, fake_message(Config.CHECK_COOKIE_COMMAND, user_id))
            try:
                await app.answer_callback_query(callback_query.id)
            except Exception:
                pass
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_FAILED_START_BROWSER_LOG_MSG.format(e=e))
            try:
                await app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FAILED_RUN_CHECK_MSG, show_alert=False)
            except Exception:
                pass
    #elif data == "facebook":
        #download_and_save_cookie(app, callback_query, Config.FACEBOOK_COOKIE_URL, "facebook")
    elif data == "own":
        try:
            await app.answer_callback_query(callback_query.id)
        except Exception:
            pass
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        await safe_send_message(
            callback_query.message.chat.id,
            safe_get_messages(user_id).SAVE_AS_COOKIE_HINT,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id if hasattr(callback_query.message, 'id') else None),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice=safe_get_messages(user_id).FLOOD_LIMIT_TRY_LATER_MSG
        )
    elif data == "from_browser":
        try:
            await cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                await app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_FAILED_START_BROWSER_LOG_MSG.format(e=e))
            try:
                await app.answer_callback_query(callback_query.id, safe_get_messages(user_id).COOKIES_FAILED_OPEN_BROWSER_MSG, show_alert=True)
            except Exception:
                pass
    elif data == "close":
        try:
            await callback_query.message.delete()
        except Exception:
            await callback_query.edit_message_reply_markup(reply_markup=None)
        await callback_query.answer(safe_get_messages(user_id).COOKIES_MENU_CLOSED_MSG)
        return

# @app.on_callback_query(filters.regex(r"^save_as_cookie_hint\|"))
async def save_as_cookie_hint_callback(app, callback_query):
    """
    Обрабатывает закрытие подсказки о сохранении куки.
    
    Args:
        app: Экземпляр приложения
        callback_query: Callback запрос
    """
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            await callback_query.message.delete()
        except Exception:
            await callback_query.edit_message_reply_markup(reply_markup=None)
        await callback_query.answer(messages.COOKIES_HINT_CLOSED_MSG)
        await send_to_logger(callback_query.message, messages.COOKIES_SAVE_AS_HINT_CLOSED_MSG)
        return

# Called from url_distractor - no decorator needed
async def checking_cookie_file(app, message):
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
            initial_msg = await safe_send_message(message.chat.id, safe_get_messages(user_id).COOKIES_FILE_EXISTS_MSG, parse_mode=enums.ParseMode.HTML)
            
            # Check if the file contains YouTube cookies (by domain column)
            async def _has_youtube_domain(text: str) -> bool:
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
            if await _has_youtube_domain(cookie_content):
                if await test_youtube_cookies(file_path):
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        await safe_edit_message_text(message.chat.id, initial_msg.id, safe_get_messages(user_id).COOKIES_YOUTUBE_WORKING_PROPERLY_MSG)
                    await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_WORKING_LOG_MSG)
                else:
                    if initial_msg is not None and hasattr(initial_msg, 'id'):
                        await safe_edit_message_text(message.chat.id, initial_msg.id, safe_get_messages(user_id).COOKIES_YOUTUBE_EXPIRED_INVALID_MSG)
                    await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_EXPIRED_LOG_MSG)
            else:
                await send_to_user(message, safe_get_messages(user_id).COOKIES_SKIPPED_VALIDATION_MSG)
                await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_CORRECT_FORMAT_LOG_MSG)
        else:
            await send_to_user(message, safe_get_messages(user_id).COOKIES_INCORRECT_FORMAT_MSG)
            await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_INCORRECT_FORMAT_LOG_MSG)
    else:
        await send_to_user(message, safe_get_messages(user_id).COOKIES_FILE_NOT_FOUND_MSG)
        await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_NOT_FOUND_LOG_MSG)


# @reply_with_keyboard
async def download_cookie(app, message):
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
                await send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_TEST_START_MSG)
                
                # Check existing cookies first
                if os.path.exists(cookie_file_path):
                    if await test_youtube_cookies(cookie_file_path):
                        await send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_WORKING_MSG)
                        return
                    else:
                        await send_to_user(message, safe_get_messages(user_id).COOKIES_YOUTUBE_EXPIRED_MSG)
                # Optional specific index: /cookie youtube <n>
                selected_index = None
                if len(parts) >= 3 and parts[2].isdigit():
                    try:
                        selected_index = int(parts[2])
                    except Exception:
                        selected_index = None
                # Download and validate new cookies (optionally a specific source)
                download_and_validate_youtube_cookies(app, message, selected_index=selected_index, user_id=user_id)
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
        logger.error(LoggerMsg.COOKIES_ERROR_FAST_COMMAND_LOG_MSG.format(e=e))
        pass
    
    # Get YouTube cookie URLs count
    youtube_urls = await get_youtube_cookie_urls()
    
    # Buttons for services
    buttons = [
        [
            InlineKeyboardButton(
                safe_get_messages(user_id).COOKIES_YOUTUBE_BUTTON_MSG.format(max=max(1, len(youtube_urls))),
                callback_data="download_cookie|youtube"
            ),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_FROM_BROWSER_BUTTON_MSG, callback_data="download_cookie|from_browser"),            
        ],
        [
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_TWITTER_BUTTON_MSG, callback_data="download_cookie|twitter"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_TIKTOK_BUTTON_MSG, callback_data="download_cookie|tiktok"),
        ],
        [
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_VK_BUTTON_MSG, callback_data="download_cookie|vk"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_INSTAGRAM_BUTTON_MSG, callback_data="download_cookie|instagram"),
        ],
        [

            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_CHECK_COOKIE_BUTTON_MSG, callback_data="download_cookie|check_cookie"),
            InlineKeyboardButton(safe_get_messages(user_id).COOKIES_YOUR_OWN_BUTTON_MSG, callback_data="download_cookie|own"),            
        ],
        [         
            InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="download_cookie|close")
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    messages = safe_get_messages(user_id)
    text = f"""
{messages.COOKIE_MENU_TITLE_MSG}

{messages.COOKIE_MENU_DESCRIPTION_MSG}
{messages.COOKIE_MENU_SAVE_INFO_MSG}

<blockquote>
{messages.COOKIE_MENU_TIP_HEADER_MSG}
{messages.COOKIE_MENU_TIP_YOUTUBE_MSG}
{messages.COOKIE_MENU_TIP_YOUTUBE_INDEX_MSG.format(max_index=len(youtube_urls))}
{messages.COOKIE_MENU_TIP_VERIFY_MSG}
</blockquote>
"""
    from HELPERS.safe_messeger import safe_send_message
    await safe_send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboard,
        reply_parameters=ReplyParameters(message_id=message.id),
        message=message
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

async def _download_content(url: str, timeout: int = 30):
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
    except Exception as e:
        return False, None, None, f"{type(e).__name__}: {e}"
    finally:
        try:
            sess.close()
        except Exception:
            pass

async def download_and_save_cookie(app, callback_query, url, service):
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
        await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_NOT_CONFIGURED_MSG.format(service=service.capitalize()))
        await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_URL_EMPTY_LOG_MSG.format(service=service.capitalize(), user_id=user_id))
        return

    try:
        ok, status, content, err = await _download_content(url, timeout=30)
        if ok:
            # Optional: validate extension (do not expose URL); keep internal check
            if not url.lower().endswith('.txt'):
                await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_MUST_BE_TXT_MSG.format(service=service.capitalize()))
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_URL_NOT_TXT_LOG_MSG.format(service=service.capitalize()))
                return
            # size check (max 100KB)
            content_size = len(content or b"")
            if content_size and content_size > 100 * 1024:
                await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_FILE_TOO_LARGE_DOWNLOAD_MSG.format(service=service.capitalize(), size=content_size // 1024))
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_FILE_TOO_LARGE_LOG_MSG.format(service=service.capitalize(), size=content_size))
                return
            # Save to user folder
            user_dir = os.path.join("users", user_id)
            create_directory(user_dir)
            cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
            file_path = os.path.join(user_dir, cookie_filename)
            with open(file_path, "wb") as cf:
                cf.write(content)
            await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_FILE_DOWNLOADED_MSG.format(service=service.capitalize()))
            await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_SERVICE_FILE_DOWNLOADED_LOG_MSG.format(service=service.capitalize(), user_id=user_id))
        else:
            # Do not leak URL in user-facing errors
            if status is not None:
                await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_SOURCE_UNAVAILABLE_MSG.format(service=service.capitalize(), status=status))
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_FAILED_LOG_MSG.format(service=service.capitalize(), status=status))
            else:
                await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_ERROR_DOWNLOADING_MSG.format(service=service.capitalize()))
                safe_err = _sanitize_error_detail(err or "", url)
                await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_ERROR_LOG_MSG.format(service=service.capitalize(), error=safe_err))
    except Exception as e:
        await send_to_user(callback_query.message, safe_get_messages(user_id).COOKIES_ERROR_DOWNLOADING_MSG.format(service=service.capitalize()))
        await send_to_logger(callback_query.message, safe_get_messages(user_id).COOKIES_DOWNLOAD_UNEXPECTED_ERROR_LOG_MSG.format(service=service.capitalize(), error_type=type(e).__name__, error=e))

# Updating The Cookie File.
# @reply_with_keyboard
async def save_as_cookie_file(app, message):
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
        await send_to_all(message, safe_get_messages(user_id).COOKIES_USER_PROVIDED_MSG)
        user_dir = os.path.join("users", user_id)
        create_directory(user_dir)
        cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
        file_path = os.path.join(user_dir, cookie_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_cookie)
        await send_to_user(message, safe_get_messages(user_id).COOKIES_SUCCESSFULLY_UPDATED_MSG.format(final_cookie=final_cookie))
        await send_to_logger(message, safe_get_messages(user_id).COOKIES_FILE_UPDATED_LOG_MSG.format(user_id=user_id))
    else:
        await send_to_user(message, safe_get_messages(user_id).COOKIES_NOT_VALID_MSG)
        await send_to_logger(message, safe_get_messages(user_id).COOKIES_INVALID_CONTENT_LOG_MSG.format(user_id=user_id))

async def test_youtube_cookies_on_url(cookie_file_path: str, url: str, user_id: int) -> bool:
    """
    Проверяет работоспособность YouTube куки на конкретном URL пользователя.
    
    Args:
        cookie_file_path (str): Путь к файлу куки
        url (str): URL для проверки
        
    Returns:
        bool: True если куки работают на этом URL, False если нет
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'format': 'best',
            'ignore_no_formats_error': False,
            'cookiefile': cookie_file_path,
            'extractor_args': {
                'youtube': {'player_client': ['tv']}
            },
            # Minimal timeout and retry settings
            'socket_timeout': 30,  # 30 seconds socket timeout
            'retries': 1,  # Minimal retries
            'extractor_retries': 1,  # Minimal extractor retries
            'fragment_retries': 3,  # Optimal fragment retries
            'retry_sleep_functions': {'http': lambda n: 3},  # Fixed 3 seconds delay
        }
        
        # Add PO token provider for YouTube domains
        ydl_opts = await add_pot_to_ytdl_opts(ydl_opts, url)
        
        from HELPERS.async_ytdlp import async_extract_info
        info = await async_extract_info(ydl_opts, url, user_id)
            
        # Проверяем, что получили информацию о видео
        if not info:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_INFO_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Проверяем наличие основных полей
        if not info.get('title') or not info.get('duration'):
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_MISSING_INFO_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Проверяем наличие форматов
        formats = info.get('formats', [])
        if len(formats) < 2:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INSUFFICIENT_FORMATS_LOG_MSG.format(formats_count=len(formats), cookie_file_path=cookie_file_path))
            return False
            
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIES_WORK_LOG_MSG.format(cookie_file_path=cookie_file_path))
        return True
        
    except Exception as e:
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_USER_URL_LOG_MSG.format(cookie_file_path=cookie_file_path, e=e))
        return False

async def test_youtube_cookies(cookie_file_path: str) -> bool:
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
            # Minimal timeout and retry settings
            'socket_timeout': 30,  # 30 seconds socket timeout
            'retries': 1,  # Minimal retries
            'extractor_retries': 1,  # Minimal extractor retries
            'fragment_retries': 3,  # Optimal fragment retries
            'retry_sleep_functions': {'http': lambda n: 3},  # Fixed 3 seconds delay
        }
        
        # Add PO token provider for YouTube domains
        ydl_opts = await add_pot_to_ytdl_opts(ydl_opts, test_url)
        
        from HELPERS.async_ytdlp import async_extract_info
        info = await async_extract_info(ydl_opts, test_url, user_id)
            
        # Проверяем, что получили полную информацию о видео
        required_fields = ['title', 'duration', 'uploader', 'view_count', 'like_count', 'upload_date']
        if not info:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_INFO_RETURNED_LOG_MSG.format(cookie_file_path=cookie_file_path))
            return False
            
        # Проверяем наличие обязательных полей
        missing_fields = [field for field in required_fields if field not in info or not info[field]]
        if missing_fields:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_MISSING_FIELDS_LOG_MSG.format(missing_fields=missing_fields, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_AVAILABLE_FIELDS_LOG_MSG.format(available_fields=list(info.keys())))
            return False
            
        # Проверяем, что есть доступные форматы для скачивания
        if 'formats' not in info or not info['formats']:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_NO_FORMATS_LOG_MSG.format(cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INFO_KEYS_LOG_MSG.format(info_keys=list(info.keys())))
            return False
            
        # Проверяем качество полученной информации
        title = info.get('title', '')
        if len(title) < 5:  # Заголовок должен быть достаточно длинным
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TITLE_TOO_SHORT_LOG_MSG.format(title=title, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TITLE_LENGTH_LOG_MSG.format(title_length=len(title)))
            return False
            
        # Проверяем, что duration разумная (не 0 и не слишком большая)
        duration = info.get('duration', 0)
        if duration and duration <= 0 or duration > 86400:  # Больше 24 часов
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_INVALID_DURATION_LOG_MSG.format(duration=duration, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_DURATION_SECONDS_LOG_MSG.format(duration=duration))
            return False
            
        # Проверяем количество форматов (должно быть достаточно для выбора)
        formats_count = len(info['formats'])
        if formats_count and formats_count < 3:  # Минимум 3 формата для выбора
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_TOO_FEW_FORMATS_LOG_MSG.format(formats_count=formats_count, cookie_file_path=cookie_file_path))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_AVAILABLE_FORMATS_LOG_MSG.format(available_formats=[f.get('format_id', 'unknown') for f in info['formats'][:5]]))
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_FAILED_ALL_FORMAT_IDS_LOG_MSG.format(all_format_ids=[f.get('format_id', 'unknown') for f in info['formats']]))
            return False
            
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_PASSED_LOG_MSG.format(cookie_file_path=cookie_file_path, formats_count=formats_count))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_TITLE_LOG_MSG.format(title=title))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_DURATION_LOG_MSG.format(duration=duration))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UPLOADER_LOG_MSG.format(uploader=info.get('uploader', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_VIEW_COUNT_LOG_MSG.format(view_count=info.get('view_count', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UPLOAD_DATE_LOG_MSG.format(upload_date=info.get('upload_date', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_LIKE_COUNT_LOG_MSG.format(like_count=info.get('like_count', 'N/A')))
        logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_FORMAT_IDS_LOG_MSG.format(format_ids=[f.get('format_id', 'unknown') for f in info['formats'][:10]]))
        return True
            
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e).lower()
        
        # Check for specific YouTube errors that are not cookie-related
        if any(keyword in error_text for keyword in [
            'video is private', 'private video', 'members only', 'premium content'
        ]):
            # These are content availability issues, not cookie issues
            logger.info(LoggerMsg.COOKIES_YOUTUBE_TEST_UNAVAILABLE_LOG_MSG.format(e=e))
            return False
        elif any(keyword in error_text for keyword in [
            'sign in', 'login required', 'age restricted', 'cookies', 
            'authentication', 'format not found', 'no formats found', 'unable to extract'
        ]):
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_AUTH_ERROR_LOG_MSG.format(e=e))
            return False
        else:
            # Other errors may not be related to cookies
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_TEST_OTHER_ERROR_LOG_MSG.format(e=e))
            return False
            
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_TEST_EXCEPTION_LOG_MSG.format(e=e))
        logger.error(LoggerMsg.COOKIES_YOUTUBE_TEST_EXCEPTION_TYPE_LOG_MSG.format(exception_type=type(e).__name__))
        return False

async def get_youtube_cookie_urls() -> list:
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

async def download_and_validate_youtube_cookies(app, message, selected_index: int | None = None, user_id: int = None) -> bool:
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
        logger.error(LoggerMsg.COOKIES_CANNOT_DETERMINE_USER_ID_LOG_MSG)
        return False
    
    # Create a helper function to send messages safely
    async def safe_send_to_user(msg):
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                # It's a Message object
                from HELPERS.logger import send_to_user
                await send_to_user(message, msg)
            elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                # It's a CallbackQuery object
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                await safe_send_message(message.from_user.id, msg, parse_mode=enums.ParseMode.HTML)
            else:
                # Fallback - try to get user_id and send directly
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                await safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_ERROR_SENDING_MESSAGE_LOG_MSG.format(e=e))
            # Try direct send as last resort
            try:
                from HELPERS.safe_messeger import safe_send_message
                from pyrogram import enums
                await safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML)
            except Exception as e2:
                logger.error(LoggerMsg.COOKIES_FINAL_FALLBACK_SEND_FAILED_LOG_MSG.format(e2=e2))
    
    cookie_urls = await get_youtube_cookie_urls()
    
    if not cookie_urls:
        await safe_send_to_user(safe_get_messages(user_id).COOKIES_YOUTUBE_SOURCES_NOT_CONFIGURED_MSG)
        # Safe logging
        try:
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                await send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG.format(user_id=user_id))
            else:
                logger.error(LoggerMsg.COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG.format(user_id=user_id))
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_ERROR_LOGGING_LOG_MSG.format(e=e))
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
            initial_msg = send_to_user(message, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)))
        elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
            # It's a CallbackQuery object - send initial message
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = await safe_send_message(message.from_user.id, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)), parse_mode=enums.ParseMode.HTML)
        else:
            # Fallback - send directly
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram import enums
            initial_msg = await safe_send_message(user_id, safe_get_messages(user_id).COOKIES_DOWNLOADING_YOUTUBE_MSG.format(attempt=1, total=len(cookie_urls)), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_ERROR_SENDING_INITIAL_MESSAGE_LOG_MSG.format(e=e))
    
    # Helper function to update the message (avoid MESSAGE_NOT_MODIFIED)
    _last_update_text = { 'text': None }
    async def update_message(new_text, user_id_param=None):
        try:
            if new_text == _last_update_text['text']:
                return
            if initial_msg and hasattr(initial_msg, 'id'):
                if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                    await app.edit_message_text(message.chat.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                elif hasattr(message, 'from_user') and hasattr(message.from_user, 'id'):
                    await app.edit_message_text(message.from_user.id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                else:
                    await app.edit_message_text(user_id_param or user_id, initial_msg.id, new_text, parse_mode=enums.ParseMode.HTML)
                _last_update_text['text'] = new_text
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" in str(e):
                return
            logger.error(LoggerMsg.COOKIES_ERROR_UPDATING_MESSAGE_LOG_MSG.format(e=e))
    
    # Determine the order of attempts
    indices = list(range(len(cookie_urls)))
    global _yt_round_robin_index
    if selected_index is not None:
        # Use a specific 1-based index
        if 1 <= selected_index <= len(cookie_urls):
            indices = [selected_index - 1]
        else:
            await update_message(safe_get_messages(user_id).COOKIES_INVALID_YOUTUBE_INDEX_MSG.format(selected_index=selected_index, total_urls=len(cookie_urls)), user_id)
            return False
    else:
        order = getattr(Config, 'YOUTUBE_COOKIE_ORDER', 'round_robin')
        if not order:
            order = 'round_robin'
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIE_ORDER_MODE_LOG_MSG.format(order=order))
        if order == 'random':
            random.shuffle(indices)
        else:
            # round_robin: rotate starting position
            if len(indices) > 0:
                start = _yt_round_robin_index % len(indices)
                indices = indices[start:] + indices[:start]
                # advance pointer for next call
                _yt_round_robin_index = (start + 1) % len(indices)
        logger.info(LoggerMsg.COOKIES_YOUTUBE_COOKIE_INDICES_ORDER_LOG_MSG.format(indices=[i+1 for i in indices]))

    # Iterate over chosen order
    for attempt_number, idx in enumerate(indices, 1):
        url = cookie_urls[idx]
        try:
            # Update message about the current attempt
            await update_message(safe_get_messages(user_id).COOKIES_DOWNLOADING_CHECKING_MSG.format(attempt=attempt_number, total=len(indices)), user_id)
            
            # Download cookies
            ok, status, content, err = await _download_content(url, timeout=30)
            if not ok:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_FAILED_LOG_MSG.format(url_index=idx + 1, status=status, error=err))
                continue
            
            # Check the format and size
            if not url.lower().endswith('.txt'):
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_URL_NOT_TXT_LOG_MSG.format(url_index=idx + 1))
                continue
                
            content_size = len(content or b"")
            if content_size and content_size > 100 * 1024:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_FILE_TOO_LARGE_LOG_MSG.format(url_index=idx + 1, file_size=content_size))
                continue
            
            # Save cookies to a temporary file
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Update message about testing
            await update_message(safe_get_messages(user_id).COOKIES_DOWNLOADING_TESTING_MSG.format(attempt=attempt_number, total=len(indices)), user_id)
            
            # Check the functionality of cookies
            if await test_youtube_cookies(cookie_file_path):
                await update_message(safe_get_messages(user_id).COOKIES_SUCCESS_VALIDATED_MSG.format(source=idx + 1, total=len(cookie_urls)), user_id)
                # Safe logging
                try:
                    if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                        await send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG.format(user_id=user_id, source=idx + 1))
                    else:
                        logger.info(LoggerMsg.COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG.format(user_id=user_id, source_index=idx + 1))
                except Exception as e:
                    logger.error(LoggerMsg.COOKIES_ERROR_LOGGING_LOG_MSG.format(e=e))
                return True
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_FROM_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=idx + 1))
                # Remove non-working cookies
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_EXCEPTION_LOG_MSG.format(e=e))
            # Remove the file in case of an error
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # If no source worked
    await update_message(safe_get_messages(user_id).COOKIES_ALL_EXPIRED_MSG, user_id)
    # Safe logging
    try:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            await send_to_logger(message, safe_get_messages(user_id).COOKIES_YOUTUBE_ALL_FAILED_LOG_MSG.format(user_id=user_id))
        else:
            logger.error(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_LOG_MSG.format(user_id=user_id))
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_ERROR_LOG_MSG.format(e=e))
    return False

async def ensure_working_youtube_cookies(user_id: int) -> bool:
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
                logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_VALID_LOG_MSG.format(user_id=user_id, cache_duration=_CACHE_DURATION))
                return cache_entry['result']
            else:
                # Cookie file was deleted, remove from cache
                del _youtube_cookie_cache[user_id]
    
    logger.info(LoggerMsg.COOKIES_YOUTUBE_STARTING_ENSURE_LOG_MSG.format(user_id=user_id))
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    cookie_filename = os.path.basename(Config.COOKIE_FILE_PATH)
    cookie_file_path = os.path.join(user_dir, cookie_filename)
    
    # Проверяем существующие куки
    if os.path.exists(cookie_file_path):
        logger.info(LoggerMsg.COOKIES_YOUTUBE_CHECKING_EXISTING_LOG_MSG.format(user_id=user_id))
        if test_youtube_cookies(cookie_file_path):
            logger.info(LoggerMsg.COOKIES_YOUTUBE_EXISTING_WORKING_LOG_MSG.format(user_id=user_id))
            logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_EXISTING_WORKING_LOG_MSG.format(user_id=user_id))
            # Cache the successful result
            _youtube_cookie_cache[user_id] = {
                'result': True,
                'timestamp': current_time,
                'cookie_path': cookie_file_path
            }
            return True
        else:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_EXISTING_FAILED_LOG_MSG.format(user_id=user_id))
    
    # Если куки нет или не работают, пробуем скачать новые
    cookie_urls = await get_youtube_cookie_urls()
    if not cookie_urls:
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_NO_SOURCES_CONFIGURED_LOG_MSG.format(user_id=user_id))
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
    
    logger.info(LoggerMsg.COOKIES_YOUTUBE_ATTEMPTING_DOWNLOAD_LOG_MSG.format(user_id=user_id, sources_count=len(cookie_urls)))
    
    for i, url in enumerate(cookie_urls, 1):
        try:
            logger.info(LoggerMsg.COOKIES_YOUTUBE_TRYING_SOURCE_LOG_MSG.format(source_index=i, total_sources=len(cookie_urls), user_id=user_id))
            
            # Скачиваем куки
            ok, status, content, err = await _download_content(url, timeout=30)
            if not ok:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_DOWNLOAD_FAILED_LOG_MSG.format(url_index=i, status=status, error=err))
                continue
            
            # Проверяем формат и размер
            if not url.lower().endswith('.txt'):
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_URL_NOT_TXT_LOG_MSG.format(url_index=i))
                continue
                
            content_size = len(content or b"")
            if content_size and content_size > 100 * 1024:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_FILE_TOO_LARGE_LOG_MSG.format(url_index=i, file_size=content_size))
                continue
            
            # Сохраняем куки
            with open(cookie_file_path, "wb") as cf:
                cf.write(content)
            
            # Проверяем работоспособность
            if await test_youtube_cookies(cookie_file_path):
                logger.info(LoggerMsg.COOKIES_YOUTUBE_SOURCE_WORKING_LOG_MSG.format(source_index=i, user_id=user_id))
                logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_WORKING_FOUND_LOG_MSG.format(user_id=user_id, source_index=i))
                # Cache the successful result
                _youtube_cookie_cache[user_id] = {
                    'result': True,
                    'timestamp': current_time,
                    'cookie_path': cookie_file_path
                }
                return True
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=i, user_id=user_id))
                # Удаляем нерабочие куки
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                    
        except Exception as e:
            logger.error(LoggerMsg.COOKIES_YOUTUBE_PROCESSING_ERROR_LOG_MSG.format(source_index=i, user_id=user_id, e=e))
            # Удаляем файл в случае ошибки
            if os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)
            continue
    
    # Если ни один источник не сработал
    logger.warning(LoggerMsg.COOKIES_YOUTUBE_ALL_SOURCES_FAILED_REMOVING_LOG_MSG.format(user_id=user_id))
    if os.path.exists(cookie_file_path):
        os.remove(cookie_file_path)
    logger.info(LoggerMsg.COOKIES_YOUTUBE_FINISHED_NO_WORKING_LOG_MSG.format(user_id=user_id))
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
    
    # Проверяем на ошибки недоступности контента, которые МОГУТ быть связаны с куками
    # "Video unavailable" может быть из-за невалидных cookies, поэтому пробуем перебор
    content_unavailable_keywords = [
        'video is private', 'private video', 'members only', 'premium content',
        'this video is not available', 'copyright', 'dmca'
    ]
    
    if any(keyword in error_lower for keyword in content_unavailable_keywords):
        return False  # Это точно не ошибка куков
    
    # "Video unavailable" и "content isn't available" МОГУТ быть из-за невалидных cookies
    # Поэтому НЕ исключаем их из перебора cookies
    
    # Ключевые слова, указывающие на проблемы с куками/авторизацией
    cookie_related_keywords = [
        'sign in', 'login required', 'age restricted', 'cookies', 
        'authentication', 'format not found', 'no formats found', 'unable to extract', 
        'http error 403', 'http error 401', 'forbidden', 'unauthorized', 'access denied',
        'subscription required'
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
    
    logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_LOG_MSG.format(user_id=user_id))
    
    # Получаем конфигурацию прокси
    try:
        from COMMANDS.proxy_cmd import get_proxy_config
        proxy_config = get_proxy_config()
        
        if not proxy_config or 'type' not in proxy_config or 'ip' not in proxy_config or 'port' not in proxy_config:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_NO_PROXY_CONFIG_LOG_MSG.format(user_id=user_id))
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
        
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_URL_LOG_MSG.format(proxy_url=proxy_url))
        
        # Повторяем скачивание с прокси
        try:
            # Добавляем параметр use_proxy=True для функции скачивания
            kwargs['use_proxy'] = True
            result = download_func(*args, **kwargs)
            if result is not None:
                logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_SUCCESS_LOG_MSG.format(user_id=user_id))
                return result
            else:
                logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_FAILED_LOG_MSG.format(user_id=user_id))
                return None
        except Exception as e:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_FAILED_ERROR_LOG_MSG.format(user_id=user_id, e=e))
            return None
            
    except Exception as e:
        logger.error(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROXY_SETUP_ERROR_LOG_MSG.format(user_id=user_id, e=e))
        return None

async def retry_download_with_different_cookies(user_id: int, url: str, download_func, *args, **kwargs):
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
    
    # Защита от рекурсивных вызовов - проверяем, не вызывается ли уже retry
    retry_key = f"{user_id}_{url}_retry"
    if retry_key in globals().get('_active_retries', set()):
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_ALREADY_IN_PROGRESS_LOG_MSG.format(user_id=user_id))
        return None
    
    # Добавляем ключ в активные retry
    if '_active_retries' not in globals():
        globals()['_active_retries'] = set()
    globals()['_active_retries'].add(retry_key)
    
    try:
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_DIFFERENT_COOKIES_LOG_MSG.format(user_id=user_id))
        
        # Получаем список источников куков
        cookie_urls = await get_youtube_cookie_urls()
        if not cookie_urls:
            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_NO_SOURCES_LOG_MSG.format(user_id=user_id))
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
        
        logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCES_ORDER_LOG_MSG.format(indices=[i+1 for i in indices]))
        
        # Пробуем каждый источник куков
        for attempt, idx in enumerate(indices, 1):
            try:
                logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ATTEMPT_LOG_MSG.format(attempt=attempt, total_attempts=len(indices), source_index=idx + 1, user_id=user_id))
                
                # Скачиваем куки
                try:
                    ok, status, content, err = await _download_content(cookie_urls[idx], timeout=30)
                except Exception as download_e:
                    logger.error(LoggerMsg.COOKIES_ERROR_PROCESSING_SOURCE_LOG_MSG.format(idx=idx + 1, user_id=user_id, error=download_e))
                    continue
                    
                if not ok:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_DOWNLOAD_FAILED_LOG_MSG.format(source_index=idx + 1, status=status, error=err))
                    continue
                
                # Проверяем формат и размер
                if not cookie_urls[idx].lower().endswith('.txt'):
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_URL_NOT_TXT_LOG_MSG.format(source_index=idx + 1))
                    continue
                    
                content_size = len(content or b"")
                if content_size and content_size > 100 * 1024:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FILE_TOO_LARGE_LOG_MSG.format(source_index=idx + 1, file_size=content_size))
                    continue
                
                # Сохраняем куки
                with open(cookie_file_path, "wb") as cf:
                    cf.write(content)
                
                # Проверяем работоспособность
                if await test_youtube_cookies(cookie_file_path):
                    logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCE_WORKING_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    
                    # Обновляем кеш
                    current_time = time.time()
                    _youtube_cookie_cache[user_id] = {
                        'result': True,
                        'timestamp': current_time,
                        'cookie_path': cookie_file_path
                    }
                    
                    # Повторяем скачивание
                    try:
                        result = await download_func(*args, **kwargs)
                        if result is not None:
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_SUCCESS_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                            return result
                        else:
                            logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FAILED_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    except Exception as e:
                        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_FAILED_ERROR_LOG_MSG.format(source_index=idx + 1, user_id=user_id, e=e))
                        # Проверяем, связана ли ошибка с куками
                        if is_youtube_cookie_error(str(e)):
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ERROR_COOKIE_RELATED_LOG_MSG.format(user_id=user_id))
                            continue
                        else:
                            logger.info(LoggerMsg.COOKIES_YOUTUBE_RETRY_ERROR_NOT_COOKIE_RELATED_LOG_MSG.format(user_id=user_id))
                            return None
                else:
                    logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_SOURCE_FAILED_VALIDATION_LOG_MSG.format(source_index=idx + 1, user_id=user_id))
                    # Удаляем нерабочие куки
                    if os.path.exists(cookie_file_path):
                        os.remove(cookie_file_path)
                        
            except Exception as e:
                logger.error(LoggerMsg.COOKIES_YOUTUBE_RETRY_PROCESSING_ERROR_LOG_MSG.format(source_index=idx + 1, user_id=user_id, e=e))
                # Удаляем файл в случае ошибки
                if os.path.exists(cookie_file_path):
                    os.remove(cookie_file_path)
                continue
        
        # Если все источники не сработали
        logger.warning(LoggerMsg.COOKIES_YOUTUBE_RETRY_ALL_SOURCES_FAILED_LOG_MSG.format(user_id=user_id))
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
    finally:
        # Удаляем ключ из активных retry
        if '_active_retries' in globals():
            globals()['_active_retries'].discard(retry_key)

def clear_youtube_cookie_cache(user_id: int = None):
    """
    Очищает кеш результатов проверки YouTube куки.
    
    Args:
        user_id (int, optional): ID пользователя для очистки. Если None, очищает весь кеш.
    """
    global _youtube_cookie_cache
    if user_id is None:
        _youtube_cookie_cache.clear()
        logger.info(LoggerMsg.COOKIES_CLEARED_CACHE_LOG_MSG)
    else:
        if user_id in _youtube_cookie_cache:
            del _youtube_cookie_cache[user_id]
            logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_CLEARED_LOG_MSG.format(user_id=user_id))
        else:
            logger.info(LoggerMsg.COOKIES_YOUTUBE_CACHE_NO_ENTRY_LOG_MSG.format(user_id=user_id))
