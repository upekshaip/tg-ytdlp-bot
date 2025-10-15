# ####################################################################################

# Checking Actions
# Text Message Handler for General Commands
from HELPERS.app_instance import get_app
from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel, check_user
from HELPERS.logger import send_to_all, send_to_logger, send_to_user
from CONFIG.logger_msg import LoggerMsg, get_logger_msg
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.caption import caption_editor
from HELPERS.filesystem_hlp import remove_media
from COMMANDS.cookies_cmd import save_as_cookie_file, download_cookie, checking_cookie_file, cookies_from_browser
from COMMANDS.subtitles_cmd import subs_command, clear_subs_check_cache
from COMMANDS.other_handlers import audio_command_handler, playlist_command
from COMMANDS.format_cmd import set_format
from COMMANDS.mediainfo_cmd import mediainfo_command
from COMMANDS.settings_cmd import settings_command
from COMMANDS.split_sizer import split_command
from COMMANDS.tag_cmd import tags_command
from COMMANDS.search import search_command
from COMMANDS.keyboard_cmd import keyboard_command, keyboard_callback_handler
from COMMANDS.proxy_cmd import proxy_command
from COMMANDS.link_cmd import link_command
from COMMANDS.image_cmd import image_command
from COMMANDS.admin_cmd import get_user_log, send_promo_message, block_user, unblock_user, check_runtime, get_user_details, uncache_command, reload_firebase_cache_command
from DATABASE.cache_db import auto_cache_command
from DATABASE.firebase_init import is_user_blocked
import os
from URL_PARSERS.video_extractor import video_url_extractor
from URL_PARSERS.playlist_utils import is_playlist_with_range
from URL_PARSERS.tags import extract_url_range_tags
from pyrogram import filters
import re
from CONFIG.config import Config
from HELPERS.logger import logger
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from HELPERS.safe_messeger import fake_message

# Get app instance for decorators
app = get_app()

async def url_distractor(app, message):
    from HELPERS.logger import logger
    from HELPERS.concurrent_limiter import concurrent_limiter
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN
    text = message.text.strip()
    logger.info(f"🎯 URL distractor called with: {text}")
    
    # Проверяем лимит одновременных загрузок для URL (админы имеют приоритет)
    if ("https://" in text) or ("http://" in text):
        # Админы могут обходить лимит, но все равно проверяем
        if not is_admin and not await concurrent_limiter.acquire(user_id, text):
            from HELPERS.safe_messeger import safe_send_message
            from CONFIG.messages import safe_get_messages
            messages = safe_get_messages(user_id)
            status = await concurrent_limiter.get_status()
            await safe_send_message(
                user_id, 
                messages.URL_EXTRACTOR_TOO_MANY_DOWNLOADS_MSG.format(
                    active=status['active_downloads'],
                    max=status['max_concurrent']
                )
            )
            return
        elif is_admin:
            # Админы получают слот принудительно
            await concurrent_limiter.acquire(user_id, text)
    
    # Import get_messages_instance locally to avoid UnboundLocalError
    from CONFIG.messages import safe_get_messages
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from HELPERS.filesystem_hlp import remove_media
    from COMMANDS.cookies_cmd import download_cookie
    
    # Debug logging
    from HELPERS.logger import logger
    logger.info(LoggerMsg.URL_EXTRACTOR_DISTRACTOR_CALLED_LOG_MSG.format(text=text[:100]))
    
    # Prevent recursion for emoji commands
    if hasattr(message, '_is_emoji_command') and message._is_emoji_command:
        return
    
    # Check if user is in args input state
    from COMMANDS.args_cmd import user_input_states, handle_args_text_input, args_import_handler
    if user_id in user_input_states:
        handle_args_text_input(app, message)
        return
    
    # Check for args import (flexible recognition for forwarded messages)
    # Use localized messages for detection
    messages = safe_get_messages(user_id)
    args_header = safe_get_messages(user_id).ARGS_CURRENT_ARGUMENTS_HEADER_MSG
    
    if args_header in text:
        logger.info(LoggerMsg.URL_EXTRACTOR_FOUND_ARGS_TEMPLATE_LOG_MSG.format(user_id=user_id))
        # Additional checks to ensure it's a settings template
        has_settings_line = any(":" in line and ("✅" in line or "❌" in line or "True" in line or "False" in line or 
                               safe_get_messages(user_id).ARGS_STATUS_TRUE_DISPLAY_MSG in line or safe_get_messages(user_id).ARGS_STATUS_FALSE_DISPLAY_MSG in line) 
                               for line in text.split('\n'))
        has_forward_instruction = (safe_get_messages(user_id).ARGS_FORWARD_TEMPLATE_MSG in text or "apply these settings" in text)
        has_separator = ("---" in text or "-" in text)
        
        logger.info(LoggerMsg.URL_EXTRACTOR_SETTINGS_CHECK_LOG_MSG.format(has_settings_line=has_settings_line, has_forward_instruction=has_forward_instruction, has_separator=has_separator))
        
        if has_settings_line and (has_forward_instruction or has_separator):
            logger.info(LoggerMsg.URL_EXTRACTOR_CALLING_ARGS_IMPORT_LOG_MSG.format(user_id=user_id))
            args_import_handler(app, message)
            return
    # Normalize commands like /cmd@bot to /cmd for group mentions
    try:
        bot_mention = f"@{getattr(Config, 'BOT_NAME', '').strip()}"
        if bot_mention and bot_mention in text:
            text = text.replace(bot_mention, "").strip()
    except Exception:
        pass

    # Emoji keyboard mapping to commands (from FULL layout)
    emoji_to_command = {
        "🧹": Config.CLEAN_COMMAND,
        "🍪": Config.DOWNLOAD_COOKIE_COMMAND,
        "⚙️": Config.SETTINGS_COMMAND,
        "🔍": Config.SEARCH_COMMAND,
        "🌐": Config.COOKIES_FROM_BROWSER_COMMAND,
        "🔗": Config.LINK_COMMAND,
        "📼": Config.FORMAT_COMMAND,
        "📊": Config.MEDIINFO_COMMAND,
        "✂️": Config.SPLIT_COMMAND,
        "🎧": Config.AUDIO_COMMAND,
        "💬": Config.SUBS_COMMAND,
        "#️⃣": Config.TAGS_COMMAND,
        "🆘": "/help",
        "📃": Config.USAGE_COMMAND,
        "⏯️": Config.PLAYLIST_COMMAND,
        "🎹": Config.KEYBOARD_COMMAND,
        "🌎": Config.PROXY_COMMAND,
        "✅": Config.CHECK_COOKIE_COMMAND,
        "🖼": Config.IMG_COMMAND,
        "🧰": Config.ARGS_COMMAND,
        "🔞": Config.NSFW_COMMAND,
        "🧾": Config.LIST_COMMAND,
    }

    if text in emoji_to_command:
        mapped = emoji_to_command[text]
        logger.info(f"🎯 Emoji detected: {text} -> {mapped}")
        # Emulate a user command for the mapped emoji
        from HELPERS.safe_messeger import fake_message
        fake_msg = fake_message(mapped, user_id)
        fake_msg._is_emoji_command = True  # Mark as emoji command to prevent recursion
        
        # Special case: headphones emoji should work exactly like /audio command
        if mapped == Config.AUDIO_COMMAND:
            from COMMANDS.other_handlers import audio_command_handler
            return await audio_command_handler(app, fake_msg)
        
        # Import and call the appropriate command handler directly
        if mapped == Config.CLEAN_COMMAND:
            # For clean command, call the clean command without arguments - EXACT SAME LOGIC as /clean
            from COMMANDS.subtitles_cmd import clear_subs_check_cache
            from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
            from CONFIG.messages import safe_get_messages
            import os
            import shutil
            
            logger.info(get_logger_msg().EMOJI_CLEAN_TRIGGERED_LOG_MSG.format(user_id=user_id))
            
            # EXACT SAME LOGIC as /clean without arguments
            user_dir = f'./users/{str(fake_msg.chat.id)}'
            if not os.path.exists(user_dir):
                await send_to_all(fake_msg, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
                clear_subs_check_cache()
                return

            removed_items = []
            allitems = os.listdir(user_dir)

            # Delete all files and folders in the user folder (except protected files)
            def scan_and_remove_recursive_emoji(path, prefix=""):
                """Recursively scan and remove files/folders, building a detailed structure list (emoji version)"""
                items = []
                try:
                    if os.path.isfile(path):
                        if os.path.basename(path) not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                            os.remove(path)
                            items.append(f"{prefix}📄 {os.path.basename(path)}")
                            logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_FILE_LOG_MSG.format(file_path=path))
                    elif os.path.isdir(path):
                        # First, scan contents of the directory
                        dir_items = []
                        try:
                            for subitem in os.listdir(path):
                                subitem_path = os.path.join(path, subitem)
                                sub_items = scan_and_remove_recursive_emoji(subitem_path, prefix + "  ")
                                dir_items.extend(sub_items)
                        except Exception as e:
                            logger.error(get_logger_msg().URL_EXTRACTOR_ERROR_SCANNING_DIRECTORY_LOG_MSG.format(path=path, e=e))
                        
                        # Then remove the directory itself
                        shutil.rmtree(path)
                        items.append(f"{prefix}📁 {os.path.basename(path)}/")
                        items.extend(dir_items)
                        logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_DIRECTORY_LOG_MSG.format(path=path))
                except Exception as e:
                    logger.error(get_logger_msg().URL_EXTRACTOR_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=path, e=e))
                return items
            
            for item in allitems:
                item_path = os.path.join(user_dir, item)
                if item not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                    sub_items = scan_and_remove_recursive_emoji(item_path)
                    removed_items.extend(sub_items)

            # Clear YouTube cookie validation cache for this user
            try:
                clear_youtube_cookie_cache(fake_msg.chat.id)
            except Exception as e:
                logger.error(get_logger_msg().URL_EXTRACTOR_FAILED_CLEAR_YOUTUBE_CACHE_LOG_MSG.format(e=e))
            
            if removed_items:
                from HELPERS.text_helper import format_clean_output_as_html
                items_list = "\n".join([f"• {item}" for item in removed_items])
                formatted_output = format_clean_output_as_html(items_list, user_id)
                await send_to_all(fake_msg, formatted_output, parse_mode=enums.ParseMode.HTML)
            else:
                await send_to_all(fake_msg, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
            
            clear_subs_check_cache()
            logger.info(get_logger_msg().EMOJI_CLEAN_COMPLETED_LOG_MSG.format(user_id=user_id))
            return
        elif mapped == Config.DOWNLOAD_COOKIE_COMMAND:
            # For cookies command, we need to show the menu
            from COMMANDS.cookies_cmd import download_cookie
            return await download_cookie(app, fake_msg)
        elif mapped == Config.SETTINGS_COMMAND:
            from COMMANDS.settings_cmd import settings_command
            return await settings_command(app, fake_msg)
        elif mapped == Config.SEARCH_COMMAND:
            from COMMANDS.search import search_command
            return await search_command(app, fake_msg)
        elif mapped == Config.COOKIES_FROM_BROWSER_COMMAND:
            from COMMANDS.cookies_cmd import cookies_from_browser
            return await cookies_from_browser(app, fake_msg)
        elif mapped == Config.LINK_COMMAND:
            from COMMANDS.link_cmd import link_command
            return await link_command(app, fake_msg)
        elif mapped == Config.FORMAT_COMMAND:
            from COMMANDS.format_cmd import set_format
            return await set_format(app, fake_msg)
        elif mapped == Config.MEDIINFO_COMMAND:
            from COMMANDS.mediainfo_cmd import mediainfo_command
            return await mediainfo_command(app, fake_msg)
        elif mapped == Config.SPLIT_COMMAND:
            from COMMANDS.split_sizer import split_command
            return await split_command(app, fake_msg)
        elif mapped == Config.SUBS_COMMAND:
            from COMMANDS.subtitles_cmd import subs_command
            return await subs_command(app, fake_msg)
        elif mapped == Config.TAGS_COMMAND:
            from COMMANDS.tag_cmd import tags_command
            return await tags_command(app, fake_msg)
        elif mapped == Config.PLAYLIST_COMMAND:
            from COMMANDS.other_handlers import playlist_command
            return await playlist_command(app, fake_msg)
        elif mapped == Config.KEYBOARD_COMMAND:
            from COMMANDS.keyboard_cmd import keyboard_command
            return await keyboard_command(app, fake_msg)
        elif mapped == Config.PROXY_COMMAND:
            from COMMANDS.proxy_cmd import proxy_command
            return await proxy_command(app, fake_msg)
        elif mapped == Config.CHECK_COOKIE_COMMAND:
            from COMMANDS.cookies_cmd import checking_cookie_file
            return await checking_cookie_file(app, fake_msg)
        elif mapped == Config.IMG_COMMAND:
            from COMMANDS.image_cmd import image_command
            return await image_command(app, fake_msg)
        elif mapped == Config.ARGS_COMMAND:
            from COMMANDS.args_cmd import args_command
            return await args_command(app, fake_msg)
        elif mapped == Config.NSFW_COMMAND:
            from COMMANDS.nsfw_cmd import nsfw_command
            return await nsfw_command(app, fake_msg)
        elif mapped == Config.LIST_COMMAND:
            from COMMANDS.list_cmd import list_command
            return await list_command(app, fake_msg)
        elif mapped == Config.USAGE_COMMAND:
            from COMMANDS.admin_cmd import get_user_usage_stats
            logger.info(get_logger_msg().EMOJI_STATS_TRIGGERED_LOG_MSG.format(user_id=user_id))
            await get_user_usage_stats(app, fake_msg)
            logger.info(get_logger_msg().EMOJI_STATS_COMPLETED_LOG_MSG.format(user_id=user_id))
            return
        elif mapped == "/help":
            # Handle help command directly
            if not await is_user_in_channel(app, fake_msg):
                return
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from CONFIG.messages import safe_get_messages
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_DEV_GITHUB_BUTTON_MSG, url="https://github.com/upekshaip/tg-ytdlp-bot"),
                    InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_CONTR_GITHUB_BUTTON_MSG, url="https://github.com/chelaxian/tg-ytdlp-bot")
                ],
                [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="help_msg|close")]
            ])
            try:
                await safe_send_message(fake_msg.chat.id, (safe_get_messages(user_id).HELP_MSG),
                                 parse_mode=enums.ParseMode.HTML,
                                 reply_markup=keyboard,
                                 message=fake_msg)
            except Exception:
                await safe_send_message(fake_msg.chat.id, (safe_get_messages(user_id).HELP_MSG), reply_markup=keyboard)
            return
        else:
            # Unknown emoji command - do nothing
            logger.warning(get_logger_msg().EMOJI_UNKNOWN_COMMAND_LOG_MSG.format(mapped=mapped))
            return

    # ----- Admin-only denial for non-admins -----
    if not is_admin:
        # /uncache
        if text.startswith(Config.UNCACHE_COMMAND):
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /auto_cache
        if text.startswith(Config.AUTO_CACHE_COMMAND):
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /all_* (user details)
        if Config.GET_USER_DETAILS_COMMAND in text:
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /unblock_user
        if Config.UNBLOCK_USER_COMMAND in text:
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /block_user
        if Config.BLOCK_USER_COMMAND in text:
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /broadcast
        if text.startswith(Config.BROADCAST_MESSAGE):
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /log (user logs)
        if Config.GET_USER_LOGS_COMMAND in text:
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return
        # /reload_cache
        if text.startswith(Config.RELOAD_CACHE_COMMAND):
            await send_to_user(message, safe_get_messages(user_id).ACCESS_DENIED_ADMIN)
            return

    # ----- Basic Commands -----
    # /Start Command
    if text == "/start":
        if is_admin:
            await send_to_user(message, safe_get_messages(user_id).WELCOME_MASTER)
        else:
            # For non-admins, check subscription first
            if not await is_user_in_channel(app, message):
                return  # is_user_in_channel already sends subscription message
            # User is subscribed, send welcome message
            from HELPERS.safe_messeger import safe_send_message
            await safe_send_message(
                message.chat.id,
                safe_get_messages(user_id).URL_EXTRACTOR_WELCOME_MSG.format(first_name=message.chat.first_name, credits=safe_get_messages(user_id).CREDITS_MSG),
                parse_mode=enums.ParseMode.HTML)
            await send_to_logger(message, LoggerMsg.USER_STARTED_BOT.format(chat_id=message.chat.id))
        return

    # /Help Command
    if text == "/help":
        # For non-admins, check subscription first
        if not await is_user_in_channel(app, message):
            return  # is_user_in_channel already sends subscription message
        # User is subscribed or admin, send help message
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_DEV_GITHUB_BUTTON_MSG, url="https://github.com/upekshaip/tg-ytdlp-bot"),
                InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_CONTR_GITHUB_BUTTON_MSG, url="https://github.com/chelaxian/tg-ytdlp-bot")
            ],
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="help_msg|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        try:
            await safe_send_message(message.chat.id, (safe_get_messages(user_id).HELP_MSG),
                             parse_mode=enums.ParseMode.HTML,
                             reply_markup=keyboard)
        except Exception:
            # Fallback without parse_mode if enums shadowed unexpectedly
            await safe_send_message(message.chat.id, (safe_get_messages(user_id).HELP_MSG), reply_markup=keyboard)
        await send_to_logger(message, LoggerMsg.HELP_SENT_TO_USER)
        return

    # /add_bot_to_group Command
    if text == Config.ADD_BOT_TO_GROUP_COMMAND:
        # For non-admins, check subscription first
        if not await is_user_in_channel(app, message):
            return  # is_user_in_channel already sends subscription message
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_ADD_GROUP_CLOSE_BUTTON_MSG, callback_data="add_group_msg|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        try:
            await safe_send_message(
                message.chat.id,
                (safe_get_messages(user_id).ADD_BOT_TO_GROUP_MSG),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboard
            )
        except Exception:
            await safe_send_message(message.chat.id, (safe_get_messages(user_id).ADD_BOT_TO_GROUP_MSG), reply_markup=keyboard)
        await send_to_logger(message, LoggerMsg.ADD_BOT_TO_GROUP_SENT)
        return

    # /lang Command - Allow for all users (no subscription check)
    if text.startswith("/lang"):
        from COMMANDS.lang_cmd import lang_command
        await lang_command(app, message)
        return

    # For non-admin users, if they haven't Joined the Channel, Exit ImmediaTely.
    # This check applies to all user commands below, but not to basic commands above.
    if not is_admin and not await is_user_in_channel(app, message):
        return

    # ----- User Commands -----
    # /Search Command
    if text.startswith(Config.SEARCH_COMMAND):
        from COMMANDS.search import search_command
        await search_command(app, message)
        return
        
    # /Keyboard Command
    if text == Config.KEYBOARD_COMMAND:
        # Ensure message has command attribute
        if not hasattr(message, 'command') or message.command is None:
            # Parse command from text
            parts = text.strip().split()
            if parts:
                cmd = parts[0][1:] if len(parts[0]) > 1 else ''
                args = parts[1:] if len(parts) > 1 else []
                message.command = [cmd] + args
            else:
                message.command = []
        from COMMANDS.keyboard_cmd import keyboard_command
        await keyboard_command(app, message)
        return
        
    # /Save_as_cookie Command
    if text.startswith(Config.SAVE_AS_COOKIE_COMMAND):
        await save_as_cookie_file(app, message)
        return

    # /Subs Command
    if text.startswith(Config.SUBS_COMMAND):
        from COMMANDS.subtitles_cmd import subs_command
        await subs_command(app, message)
        return

    # /Proxy Command
    if text.startswith(Config.PROXY_COMMAND):
        # Ensure message has command attribute
        if not hasattr(message, 'command') or message.command is None:
            # Parse command from text
            parts = text.strip().split()
            if parts:
                cmd = parts[0][1:] if len(parts[0]) > 1 else ''
                args = parts[1:] if len(parts) > 1 else []
                message.command = [cmd] + args
            else:
                message.command = []
        from COMMANDS.proxy_cmd import proxy_command
        await proxy_command(app, message)
        return

    # /Link Command
    if text.startswith(Config.LINK_COMMAND):
        # Ensure message has command attribute
        if not hasattr(message, 'command') or message.command is None:
            # Parse command from text
            parts = text.strip().split()
            if parts:
                cmd = parts[0][1:] if len(parts[0]) > 1 else ''
                args = parts[1:] if len(parts) > 1 else []
                message.command = [cmd] + args
            else:
                message.command = []
        from COMMANDS.link_cmd import link_command
        await link_command(app, message)
        return

    # /Img Command
    if text.startswith(Config.IMG_COMMAND):
        from COMMANDS.image_cmd import image_command
        await image_command(app, message)
        return

    # /Args Command
    if text.startswith(Config.ARGS_COMMAND):
        from COMMANDS.args_cmd import args_command
        await args_command(app, message)
        return

    # /List Command
    if text.startswith(Config.LIST_COMMAND):
        from COMMANDS.list_cmd import list_command
        await list_command(app, message)
        return

    # /NSFW Command
    if text.startswith(Config.NSFW_COMMAND):
        from COMMANDS.nsfw_cmd import nsfw_command
        await nsfw_command(app, message)
        return

    # /cookie Command (exact or with arguments only). Avoid matching '/cookies_from_browser'.
    if text == Config.DOWNLOAD_COOKIE_COMMAND or text.startswith(Config.DOWNLOAD_COOKIE_COMMAND + " "):
        raw_args = text[len(Config.DOWNLOAD_COOKIE_COMMAND):].strip()
        cookie_args = raw_args.lower()
        
        # Handle direct arguments
        if cookie_args.startswith(safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG):
            # Support optional index: /cookie youtube <n>
            selected_index = None
            try:
                parts = raw_args.split()
                if len(parts) >= 1 and parts[0].lower() == safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG:
                    if len(parts) >= 2 and parts[1].isdigit():
                        selected_index = int(parts[1])
            except Exception:
                selected_index = None

            # Simulate YouTube button click or call handler directly when index provided
            from collections import namedtuple
            FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data', 'id'])
            FakeUser = namedtuple('FakeUser', ['id'])
            fake_callback = FakeCallbackQuery(
                from_user=FakeUser(id=user_id),
                message=message,
                data="download_cookie|youtube",
                id="fake_callback_id"
            )
            from COMMANDS.cookies_cmd import download_and_validate_youtube_cookies
            download_and_validate_youtube_cookies(app, fake_callback, selected_index=selected_index)
            return
            
        elif cookie_args == safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_INSTAGRAM_MSG:
            # Simulate Instagram button click
            from pyrogram.types import CallbackQuery
            from collections import namedtuple
            
            FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data', 'id'])
            FakeUser = namedtuple('FakeUser', ['id'])
            
            fake_callback = FakeCallbackQuery(
                from_user=FakeUser(id=user_id),
                message=message,
                data="download_cookie|instagram",
                id="fake_callback_id"
            )
            
            from COMMANDS.cookies_cmd import download_and_save_cookie
            download_and_save_cookie(app, fake_callback, Config.INSTAGRAM_COOKIE_URL, "instagram")
            return
            
        elif cookie_args == safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_TIKTOK_MSG:
            # Simulate TikTok button click
            from pyrogram.types import CallbackQuery
            from collections import namedtuple
            
            FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data'])
            FakeUser = namedtuple('FakeUser', ['id'])
            
            fake_callback = FakeCallbackQuery(
                from_user=FakeUser(id=user_id),
                message=message,
                data="download_cookie|tiktok"
            )
            
            from COMMANDS.cookies_cmd import download_and_save_cookie
            download_and_save_cookie(app, fake_callback, Config.TIKTOK_COOKIE_URL, "tiktok")
            return
            
        elif cookie_args in ["x", safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_TWITTER_MSG]:
            # Simulate Twitter/X button click
            from pyrogram.types import CallbackQuery
            from collections import namedtuple
            
            FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data'])
            FakeUser = namedtuple('FakeUser', ['id'])
            
            fake_callback = FakeCallbackQuery(
                from_user=FakeUser(id=user_id),
                message=message,
                data="download_cookie|twitter"
            )
            
            from COMMANDS.cookies_cmd import download_and_save_cookie
            download_and_save_cookie(app, fake_callback, Config.TWITTER_COOKIE_URL, "twitter")
            return
            
        #elif cookie_args == "facebook":
            # Simulate Facebook button click
            #from pyrogram.types import CallbackQuery
            #from collections import namedtuple
            
            #FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data'])
            #FakeUser = namedtuple('FakeUser', ['id'])
            
            #fake_callback = FakeCallbackQuery(
                #from_user=FakeUser(id=user_id),
                #message=message,
                #data="download_cookie|facebook"
            #)
            
            #from COMMANDS.cookies_cmd import download_and_save_cookie
            #download_and_save_cookie(app, fake_callback, Config.FACEBOOK_COOKIE_URL, "facebook")
            #return
            
        elif cookie_args == safe_get_messages(user_id).URL_EXTRACTOR_COOKIE_ARGS_CUSTOM_MSG:
            # Simulate "Your Own" button click
            from pyrogram.types import CallbackQuery
            from collections import namedtuple
            
            FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data'])
            FakeUser = namedtuple('FakeUser', ['id'])
            
            fake_callback = FakeCallbackQuery(
                from_user=FakeUser(id=user_id),
                message=message,
                data="download_cookie|own"
            )
            
            # Show custom cookie hint
            try:
                await app.answer_callback_query(fake_callback.id)
            except Exception:
                pass
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
            ])
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram.types import ReplyParameters
            await safe_send_message(
                fake_callback.message.chat.id,
                safe_get_messages(user_id).SAVE_AS_COOKIE_HINT,
                reply_parameters=ReplyParameters(message_id=fake_callback.message.id if hasattr(fake_callback.message, 'id') else None),
                reply_markup=keyboard,
                _callback_query=fake_callback,
                _fallback_notice=safe_get_messages(user_id).FLOOD_LIMIT_TRY_LATER_FALLBACK_MSG
            )
            return
            
        elif cookie_args == "" or cookie_args is None:
            # No arguments - show regular menu
            await download_cookie(app, message)
            return
        else:
            # Invalid argument - show usage message
            from pyrogram.types import ReplyParameters
            usage_text = safe_get_messages(user_id).COOKIE_COMMAND_USAGE_MSG
            await app.send_message(
                message.chat.id,
                usage_text,
                parse_mode=enums.ParseMode.HTML,
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            return

    # /Check_cookie Command
    if text == Config.CHECK_COOKIE_COMMAND:
        from COMMANDS.cookies_cmd import checking_cookie_file
        await checking_cookie_file(app, message)
        return

    # /cookies_from_browser Command
    if text.startswith(Config.COOKIES_FROM_BROWSER_COMMAND):
        from COMMANDS.cookies_cmd import cookies_from_browser
        await cookies_from_browser(app, message)
        return

    # /Audio Command
    if text.startswith(Config.AUDIO_COMMAND):
        from COMMANDS.other_handlers import audio_command_handler
        await audio_command_handler(app, message)
        return

    # /Format Command
    if text.startswith(Config.FORMAT_COMMAND):
        from COMMANDS.format_cmd import set_format
        await set_format(app, message)
        return

    # /Mediainfo Command
    if text.startswith(Config.MEDIINFO_COMMAND):
        from COMMANDS.mediainfo_cmd import mediainfo_command
        await mediainfo_command(app, message)
        return

    # /Settings Command
    if text.startswith(Config.SETTINGS_COMMAND):
        from COMMANDS.settings_cmd import settings_command
        await settings_command(app, message)
        return

    # (handled via Config.LINK_COMMAND and Config.PROXY_COMMAND branches above)

        # /Playlist Command
    if text.startswith(Config.PLAYLIST_COMMAND):
        from COMMANDS.other_handlers import playlist_command
        await playlist_command(app, message)
        return

    # /Clean Command
    if text.startswith(Config.CLEAN_COMMAND):
        clean_args = text[len(Config.CLEAN_COMMAND):].strip().lower()
        if not clean_args:
            # Default clean behavior - clean all files except protected ones (same as 🧹 emoji)
            from COMMANDS.subtitles_cmd import clear_subs_check_cache
            from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
            import os
            import shutil
            
            logger.info(get_logger_msg().EMOJI_CLEAN_TRIGGERED_LOG_MSG.format(user_id=user_id))
            
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
                clear_subs_check_cache()
                return

            removed_items = []
            allitems = os.listdir(user_dir)

            # Delete all files and folders in the user folder (except protected files)
            def scan_and_remove_recursive_clean(path, prefix=""):
                """Recursively scan and remove files/folders, building a detailed structure list (clean command version)"""
                items = []
                try:
                    if os.path.isfile(path):
                        if os.path.basename(path) not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                            os.remove(path)
                            items.append(f"{prefix}📄 {os.path.basename(path)}")
                            logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_FILE_LOG_MSG.format(file_path=path))
                    elif os.path.isdir(path):
                        # First, scan contents of the directory
                        dir_items = []
                        try:
                            for subitem in os.listdir(path):
                                subitem_path = os.path.join(path, subitem)
                                sub_items = scan_and_remove_recursive_clean(subitem_path, prefix + "  ")
                                dir_items.extend(sub_items)
                        except Exception as e:
                            logger.error(get_logger_msg().URL_EXTRACTOR_ERROR_SCANNING_DIRECTORY_LOG_MSG.format(path=path, e=e))
                        
                        # Then remove the directory itself
                        shutil.rmtree(path)
                        items.append(f"{prefix}📁 {os.path.basename(path)}/")
                        items.extend(dir_items)
                        logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_DIRECTORY_LOG_MSG.format(path=path))
                except Exception as e:
                    logger.error(get_logger_msg().URL_EXTRACTOR_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=path, e=e))
                return items
            
            for item in allitems:
                item_path = os.path.join(user_dir, item)
                if item not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                    sub_items = scan_and_remove_recursive_clean(item_path)
                    removed_items.extend(sub_items)

            # Clear YouTube cookie validation cache for this user
            try:
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(get_logger_msg().URL_EXTRACTOR_FAILED_CLEAR_YOUTUBE_CACHE_LOG_MSG.format(e=e))
            
            if removed_items:
                from HELPERS.text_helper import format_clean_output_as_html
                items_list = "\n".join([f"• {item}" for item in removed_items])
                formatted_output = format_clean_output_as_html(items_list, user_id)
                await send_to_all(message, formatted_output, parse_mode=enums.ParseMode.HTML)
            else:
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
            
            clear_subs_check_cache()
            logger.info(get_logger_msg().EMOJI_CLEAN_COMPLETED_LOG_MSG.format(user_id=user_id))
            return
        elif clean_args in ["cookie", "cookies"]:
            remove_media(message, only=["cookie.txt"])
            # Clear YouTube cookie validation cache for this user
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(LoggerMsg.URL_EXTRACTOR_FAILED_CLEAR_YOUTUBE_CACHE_LOG_MSG.format(e=e))
            await send_to_all(message, safe_get_messages(user_id).COOKIE_FILE_REMOVED_CACHE_CLEARED_MSG)
            return
        elif clean_args in ["log", "logs"]:
            remove_media(message, only=["logs.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_LOGS_FILE_REMOVED_MSG)
            return
        elif clean_args in ["tag", "tags"]:
            remove_media(message, only=["tags.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_TAGS_FILE_REMOVED_MSG)
            return
        elif clean_args == "format":
            remove_media(message, only=["format.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_FORMAT_FILE_REMOVED_MSG)
            return
        elif clean_args == "split":
            remove_media(message, only=["split.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_SPLIT_FILE_REMOVED_MSG)
            return
        elif clean_args == "mediainfo":
            remove_media(message, only=["mediainfo.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_MEDIAINFO_FILE_REMOVED_MSG)
            return
        elif clean_args == "subs":
            remove_media(message, only=["subs.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_SUBS_SETTINGS_REMOVED_MSG)
            from COMMANDS.subtitles_cmd import clear_subs_check_cache
            clear_subs_check_cache()
            return
        elif clean_args == "keyboard":
            remove_media(message, only=["keyboard.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_KEYBOARD_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "args":
            remove_media(message, only=["args.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_ARGS_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "nsfw":
            remove_media(message, only=["nsfw_blur.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_NSFW_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "proxy":
            remove_media(message, only=["proxy.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_PROXY_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "flood_wait":
            remove_media(message, only=["flood_wait.txt"])
            await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_CLEAN_FLOOD_WAIT_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "all":
            # Delete all files and folders and display the list of deleted ones (NO EXCEPTIONS)
            import os
            import shutil
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
                from COMMANDS.subtitles_cmd import clear_subs_check_cache
                clear_subs_check_cache()
                return

            removed_items = []
            allitems = os.listdir(user_dir)

            # Delete ALL files and folders in the user folder (NO EXCEPTIONS)
            async def scan_and_remove_recursive_all(path, prefix=""):
                """Recursively scan and remove files/folders, building a detailed structure list (NO EXCEPTIONS)"""
                items = []
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                        items.append(f"{prefix}📄 {os.path.basename(path)}")
                        logger.info(LoggerMsg.URL_EXTRACTOR_REMOVED_FILE_LOG_MSG.format(file_path=path))
                    elif os.path.isdir(path):
                        # First, scan contents of the directory
                        dir_items = []
                        try:
                            for subitem in os.listdir(path):
                                subitem_path = os.path.join(path, subitem)
                                sub_items = await scan_and_remove_recursive_all(subitem_path, prefix + "  ")
                                dir_items.extend(sub_items)
                        except Exception as e:
                            logger.error(get_logger_msg().URL_EXTRACTOR_ERROR_SCANNING_DIRECTORY_LOG_MSG.format(path=path, e=e))
                        
                        # Then remove the directory itself
                        shutil.rmtree(path)
                        items.append(f"{prefix}📁 {os.path.basename(path)}/")
                        items.extend(dir_items)
                        logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_DIRECTORY_LOG_MSG.format(path=path))
                except Exception as e:
                    logger.error(LoggerMsg.URL_EXTRACTOR_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=path, e=e))
                return items
            
            for item in allitems:
                item_path = os.path.join(user_dir, item)
                sub_items = await scan_and_remove_recursive_all(item_path)
                removed_items.extend(sub_items)

            # Clear YouTube cookie validation cache for this user
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(LoggerMsg.URL_EXTRACTOR_FAILED_CLEAR_YOUTUBE_CACHE_LOG_MSG.format(e=e))
            
            if removed_items:
                from HELPERS.text_helper import format_clean_output_as_html
                items_list = "\n".join([f"• {item}" for item in removed_items])
                formatted_output = format_clean_output_as_html(items_list, user_id)
                await send_to_all(message, formatted_output, parse_mode=enums.ParseMode.HTML)
            else:
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
            return
        else:
            # Regular command /clean - delete all files and folders (same as /clean all)
            import os
            import shutil
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
                from COMMANDS.subtitles_cmd import clear_subs_check_cache
                clear_subs_check_cache()
                return

            removed_items = []
            allitems = os.listdir(user_dir)

            # Delete all files and folders in the user folder (except protected files)
            async def scan_and_remove_recursive(path, prefix=""):
                """Recursively scan and remove files/folders, building a detailed structure list"""
                items = []
                try:
                    if os.path.isfile(path):
                        if os.path.basename(path) not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                            os.remove(path)
                            items.append(f"{prefix}📄 {os.path.basename(path)}")
                            logger.info(LoggerMsg.URL_EXTRACTOR_REMOVED_FILE_LOG_MSG.format(file_path=path))
                    elif os.path.isdir(path):
                        # First, scan contents of the directory
                        dir_items = []
                        try:
                            for subitem in os.listdir(path):
                                subitem_path = os.path.join(path, subitem)
                                sub_items = scan_and_remove_recursive(subitem_path, prefix + "  ")
                                dir_items.extend(sub_items)
                        except Exception as e:
                            logger.error(get_logger_msg().URL_EXTRACTOR_ERROR_SCANNING_DIRECTORY_LOG_MSG.format(path=path, e=e))
                        
                        # Then remove the directory itself
                        shutil.rmtree(path)
                        items.append(f"{prefix}📁 {os.path.basename(path)}/")
                        items.extend(dir_items)
                        logger.info(get_logger_msg().URL_EXTRACTOR_REMOVED_DIRECTORY_LOG_MSG.format(path=path))
                except Exception as e:
                    logger.error(LoggerMsg.URL_EXTRACTOR_FAILED_REMOVE_FILE_LOG_MSG.format(file_path=path, e=e))
                return items
            
            for item in allitems:
                item_path = os.path.join(user_dir, item)
                if item not in ["keyboard.txt", "tags.txt", "logs.txt", "lang.txt"]:
                    sub_items = scan_and_remove_recursive(item_path)
                    removed_items.extend(sub_items)

            # Clear YouTube cookie validation cache for this user
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(LoggerMsg.URL_EXTRACTOR_FAILED_CLEAR_YOUTUBE_CACHE_LOG_MSG.format(e=e))
            
            if removed_items:
                from HELPERS.text_helper import format_clean_output_as_html
                items_list = "\n".join([f"• {item}" for item in removed_items])
                formatted_output = format_clean_output_as_html(items_list, user_id)
                await send_to_all(message, formatted_output, parse_mode=enums.ParseMode.HTML)
            else:
                await send_to_all(message, safe_get_messages(user_id).URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
            
            from COMMANDS.subtitles_cmd import clear_subs_check_cache
            clear_subs_check_cache()
            return

    # /USAGE Command
    if Config.USAGE_COMMAND in text:
        from COMMANDS.admin_cmd import get_user_usage_stats
        logger.info(f"📃 Emoji triggered - showing usage stats for user {user_id}")
        await get_user_usage_stats(app, message)
        logger.info(f"📃 Emoji completed - usage stats shown for user {user_id}")
        return


    # /tags Command
    if Config.TAGS_COMMAND in text:
        from COMMANDS.tag_cmd import tags_command
        await tags_command(app, message)
        return

    # /Split Command
    if text.startswith(Config.SPLIT_COMMAND):
        # Ensure message has command attribute
        if not hasattr(message, 'command') or message.command is None:
            # Parse command from text
            parts = text.strip().split()
            if parts:
                cmd = parts[0][1:] if len(parts[0]) > 1 else ''
                args = parts[1:] if len(parts) > 1 else []
                message.command = [cmd] + args
            else:
                message.command = []
        from COMMANDS.split_sizer import split_command
        await split_command(app, message)
        return

    # /Keyboard Command
    if text.startswith(Config.KEYBOARD_COMMAND):
        from COMMANDS.keyboard_cmd import keyboard_command
        await keyboard_command(app, message)
        return

    # /Help Command
    if text == "/help":
        from COMMANDS.other_handlers import help_msg_callback
        help_msg_callback(app, message)
        return

    # /Search Command
    if text.startswith(Config.SEARCH_COMMAND):
        from COMMANDS.search import search_command
        await search_command(app, message)
        return

    # /uncache Command - Clear cache for URL (for admins only)
    if text.startswith(Config.UNCACHE_COMMAND):
        if is_admin:
            await uncache_command(app, message)
        else:
            await send_to_all(message, safe_get_messages(user_id).URL_PARSER_ADMIN_ONLY_MSG)
        return

    # /vid help & range transformation when handled by the text pipeline
    if text.strip().lower().startswith("/vid"):
        # Try to transform "/vid A-B URL" -> "URL*A*B" (B may be empty)
        parts_full = text.strip().split(maxsplit=2)
        if len(parts_full) >= 3 and re.match(r"^\d+-\d*$", parts_full[1]):
            a, b = parts_full[1].split('-', 1)
            url_only = parts_full[2]
            if b == "":
                new_text = f"{url_only}*{a}*"
            else:
                new_text = f"{url_only}*{a}*{b}"
            try:
                message.text = new_text
            except Exception:
                pass
            # fallthrough to standard URL flow below
        parts = text.strip().split(maxsplit=1)
        if len(parts) == 1:
            try:
                from HELPERS.safe_messeger import safe_send_message
                # Use top-level imports to avoid shadowing names in function scope
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG, callback_data="vid_help|close")]])
                help_text = (
                    f"<b>{safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_TITLE_MSG}</b>\n\n"
                    f"{safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_USAGE_MSG}\n\n"
                    f"<b>{safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_EXAMPLES_MSG}</b>\n"
                    f"{safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_EXAMPLE_1_MSG}\n\n"
                    f"{safe_get_messages(user_id).URL_EXTRACTOR_VID_HELP_ALSO_SEE_MSG}"
                )
                await safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
            return
        else:
            # Strip command and reuse the URL handler path when no range was provided
            try:
                if len(parts_full) < 3 or not re.match(r"^\d+-\d*$", parts_full[1]):
                    message.text = parts[1]
            except Exception:
                pass

    # If the message contains a URL, process without explicit commands:
    # 1) Try yt-dlp flow (video_url_extractor)
    # 2) On failure, fallback to gallery-dl (/img handler)
    if ("https://" in text) or ("http://" in text):
        if not await is_user_blocked(message):
            from COMMANDS.subtitles_cmd import clear_subs_check_cache
            clear_subs_check_cache()
            # Централизованный роутер на gallery-dl для некоторых ссылок
            try:
                try:
                    from .engine_router import route_if_gallerydl_only  # type: ignore
                except Exception:
                    from URL_PARSERS.engine_router import route_if_gallerydl_only  # type: ignore
                if await route_if_gallerydl_only(app, message):
                    return
            except Exception as route_e:
                logger.error(LoggerMsg.URL_EXTRACTOR_ENGINE_ROUTER_ERROR_LOG_MSG.format(error=route_e))
            try:
                await video_url_extractor(app, message)
            except Exception as e:
                logger.error(LoggerMsg.URL_EXTRACTOR_VIDEO_EXTRACTOR_FAILED_LOG_MSG.format(e=e))
            finally:
                # Освобождаем слот загрузки
                await concurrent_limiter.release(user_id)
                try:
                    # Create proper /img command from URL
                    from HELPERS.safe_messeger import fake_message
                    
                    # Extract URL and range from original message
                    url, video_start_with, video_end_with, playlist_name, tags, tags_text, tag_error = extract_url_range_tags(message.text)
                    
                    if url:
                        # Create fallback command with range if available
                        if video_start_with and video_end_with and (video_start_with != 1 or video_end_with != 1):
                            fallback_text = f"/img {video_start_with}-{video_end_with} {url}"
                        else:
                            fallback_text = f"/img {url}"
                        
                        # Add tags if available
                        if tags_text:
                            fallback_text += f" {tags_text}"
                        
                        # Create fake message for gallery-dl command
                        # For groups, preserve original chat_id and message_thread_id
                        original_chat_id = message.chat.id if hasattr(message, 'chat') else message.chat.id
                        message_thread_id = getattr(message, 'message_thread_id', None) if hasattr(message, 'message_thread_id') else None
                        fake_msg = fake_message(fallback_text, message.chat.id, original_chat_id=original_chat_id, message_thread_id=message_thread_id, original_message=message)
                        
                        # Execute gallery-dl command
                        image_command(app, fake_msg)
                        logger.info(get_logger_msg().URL_EXTRACTOR_GALLERY_DL_FALLBACK_LOG_MSG.format(fallback_text=fallback_text))
                    else:
                        logger.error("No URL found for gallery-dl fallback")
                        
                except Exception as e2:
                    logger.error(LoggerMsg.URL_EXTRACTOR_GALLERY_DL_FALLBACK_FAILED_LOG_MSG.format(e2=e2))
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
            await uncache_command(app, message)
            return

        # /reload_cache Command - Reload cache for URL
        if Config.RELOAD_CACHE_COMMAND in text:
            await reload_firebase_cache_command(app, message)
            return

        # /auto_cache Command - Toggle automatic cache reloading
        if Config.AUTO_CACHE_COMMAND in text:
            await auto_cache_command(app, message)
            return

        # /Search Command (for admins too)
        if text.startswith(Config.SEARCH_COMMAND):
            from COMMANDS.search import search_command
            await search_command(app, message)
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
            if not await is_user_blocked(message):
                if message.reply_to_message and message.reply_to_message.video:
                    caption_editor(app, message)
        return

    # Final check for args import (in case it wasn't caught earlier)
    # Use localized messages for detection
    messages = safe_get_messages(user_id)
    args_header = safe_get_messages(user_id).ARGS_CURRENT_ARGUMENTS_HEADER_MSG
    
    if args_header in text:
        logger.info(f"Final check: Found potential args import template in message from user {user_id}")
        # Check for settings lines with English parameter names and status indicators
        has_settings_line = any(":" in line and ("✅" in line or "❌" in line or "True" in line or "False" in line) 
                               for line in text.split('\n'))
        has_forward_instruction = (safe_get_messages(user_id).ARGS_FORWARD_TEMPLATE_MSG in text or "apply these settings" in text)
        has_separator = ("---" in text or "-" in text)
        
        logger.info(f"Final check: has_settings_line={has_settings_line}, has_forward_instruction={has_forward_instruction}, has_separator={has_separator}")
        
        if has_settings_line and (has_forward_instruction or has_separator):
            logger.info(f"Final check: Calling args_import_handler for user {user_id}")
            args_import_handler(app, message)
            return

    logger.info(LoggerMsg.URL_EXTRACTOR_NO_MATCHING_COMMAND_LOG_MSG.format(user_id=user_id))
    from COMMANDS.subtitles_cmd import clear_subs_check_cache
    clear_subs_check_cache()

# @app.on_callback_query(filters.regex("^keyboard\\|"))
async def keyboard_callback_handler_wrapper(app, callback_query):
    """Handle keyboard setting callbacks"""
    await keyboard_callback_handler(app, callback_query)

# The function is_playlist_with_range is now imported from URL_PARSERS.playlist_utils

# Callback handler for add_bot_to_group close button
# @app.on_callback_query(filters.regex(r"^add_group_msg\|"))
async def add_group_msg_callback(app, callback_query):
    """Handle add_bot_to_group command callback queries"""
    try:
        data = callback_query.data.split("|")[1]
        user_id = callback_query.from_user.id
        
        if data == "close":
            # Delete the message with add_bot_to_group instructions
            try:
                await app.delete_messages(
                    callback_query.message.chat.id,
                    callback_query.message.id
                )
            except Exception:
                # If can't delete, just edit to show closed message
                await app.edit_message_text(
                    callback_query.message.chat.id,
                    callback_query.message.id,
                    LoggerMsg.URL_EXTRACTOR_ADD_GROUP_HELPER_CLOSED_LOG_MSG
                )
            
            # Answer callback query
            await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_CLOSED_MSG)
            
            # Log the action
            await send_to_logger(callback_query.message, safe_get_messages(user_id).URL_EXTRACTOR_ADD_GROUP_USER_CLOSED_MSG.format(user_id=user_id))
            
    except Exception as e:
        # Log error and answer callback
        await send_to_logger(callback_query.message, LoggerMsg.URL_EXTRACTOR_ADD_GROUP_CALLBACK_ERROR_LOG_MSG.format(e=e))
        await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)

# Callback handler for audio hint close button
# @app.on_callback_query(filters.regex(r"^audio_hint\|"))
async def audio_hint_callback(app, callback_query):
    """Handle audio hint close button callback queries"""
    try:
        data = callback_query.data.split("|")[1]
        user_id = callback_query.from_user.id
        
        if data == "close":
            # Delete the message
            try:
                await callback_query.message.delete()
            except Exception:
                pass
            # Answer callback query
            await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_CLOSED_MSG)
            
            # Log the action
            await send_to_logger(callback_query.message, safe_get_messages(user_id).URL_EXTRACTOR_AUDIO_HINT_CLOSED_MSG.format(user_id=user_id))
            
    except Exception as e:
        # Log error and answer callback
        await send_to_logger(callback_query.message, LoggerMsg.URL_EXTRACTOR_AUDIO_HINT_CALLBACK_ERROR_LOG_MSG.format(e=e))
        await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)

# Callback handler for link hint close button
# @app.on_callback_query(filters.regex(r"^link_hint\|"))
async def link_hint_callback(app, callback_query):
    """Handle link hint close button callback queries"""
    try:
        data = callback_query.data.split("|")[1]
        user_id = callback_query.from_user.id
        
        if data == "close":
            # Delete the message
            try:
                await callback_query.message.delete()
            except Exception:
                pass
            # Answer callback query
            await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_CLOSED_MSG)
            
            # Log the action
            await send_to_logger(callback_query.message, safe_get_messages(user_id).URL_EXTRACTOR_LINK_HINT_CLOSED_MSG.format(user_id=user_id))
            
    except Exception as e:
        # Log error and answer callback
        await send_to_logger(callback_query.message, LoggerMsg.URL_EXTRACTOR_LINK_HINT_CALLBACK_ERROR_LOG_MSG.format(e=e))
        await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)

# Callback handler for language selection
# @app.on_callback_query(filters.regex(r"^lang_"))
async def lang_callback(app, callback_query):
    """Handle language selection callback queries"""
    from HELPERS.logger import send_to_logger, logger
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        logger.info(f"Language callback triggered: {data} for user {user_id}")
        
        if data.startswith('lang_select_'):
            # Extract language code
            lang_code = data.replace('lang_select_', '')
            
            # Set user language
            from CONFIG.LANGUAGES.language_router import set_user_language
            logger.info(f"Setting language {lang_code} for user {user_id}")
            success = set_user_language(user_id, lang_code)
            logger.info(f"Language set result: {success}")
            
            if success:
                # Get messages in new language for this user
                from CONFIG.LANGUAGES.language_router import get_messages
                new_messages = get_messages(user_id, lang_code)
                
                # Get language name
                from CONFIG.LANGUAGES.language_router import language_router
                available_languages = language_router.get_available_languages()
                lang_name = available_languages.get(lang_code, lang_code)
                
                # Send confirmation message
                confirmation_msg = getattr(new_messages, 'LANG_CHANGED_MSG', 
                    f"✅ Language changed to {lang_name}"
                )
                
                # Format the message with lang_name
                if '{lang_name}' in confirmation_msg:
                    confirmation_msg = confirmation_msg.format(lang_name=lang_name)
                
                await callback_query.answer(confirmation_msg)
                await callback_query.edit_message_text(
                    confirmation_msg,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                error_msg = safe_get_messages(user_id).LANG_ERROR_MSG if hasattr(safe_get_messages(user_id), 'LANG_ERROR_MSG') else "❌ Error changing language"
                await callback_query.answer(error_msg)
                
        elif data == 'lang_close':
            # Close language selection
            close_msg = safe_get_messages(user_id).LANG_CLOSED_MSG if hasattr(safe_get_messages(user_id), 'LANG_CLOSED_MSG') else "Language selection closed"
            await callback_query.answer(close_msg)
            await callback_query.edit_message_text(close_msg)
            
    except Exception as e:
        # Log error and answer callback
        from CONFIG.logger_msg import LoggerMsg
        await send_to_logger(callback_query.message, LoggerMsg.URL_EXTRACTOR_LANGUAGE_CALLBACK_ERROR_LOG_MSG.format(e=e))
        await callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)

######################################################  
