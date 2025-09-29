# ####################################################################################

# Checking Actions
# Text Message Handler for General Commands
from HELPERS.app_instance import get_app
from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel, check_user
from HELPERS.logger import send_to_all, send_to_logger, send_to_user
from CONFIG.logger_msg import LoggerMsg
from CONFIG.messages import Messages
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
from pyrogram import filters
import re
from CONFIG.config import Config
from CONFIG.messages import Messages
from HELPERS.logger import logger
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from HELPERS.safe_messeger import fake_message

# Get app instance for decorators
app = get_app()

@app.on_message(filters.text & filters.private)
@reply_with_keyboard
def url_distractor(app, message):
    user_id = message.chat.id
    is_admin = int(user_id) in Config.ADMIN
    text = message.text.strip()
    
    # Check if user is in args input state
    from COMMANDS.args_cmd import user_input_states, handle_args_text_input
    if user_id in user_input_states:
        handle_args_text_input(app, message)
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
        "🧰": "/args",
        "🔞": "/nsfw",
        "🧾": "/list",
    }

    if text in emoji_to_command:
        mapped = emoji_to_command[text]
        # Special case: headphones emoji should show audio usage hint
        if mapped == "/audio":
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(
                message.chat.id,
                Messages.URL_EXTRACTOR_AUDIO_HINT_MSG,
                message=message
            )
            return
        # Emulate a user command for the mapped emoji
        return url_distractor(app, fake_message(mapped, user_id))

    # ----- Admin-only denial for non-admins -----
    if not is_admin:
        # /uncache
        if text.startswith(Config.UNCACHE_COMMAND):
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /auto_cache
        if text.startswith(Config.AUTO_CACHE_COMMAND):
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /all_* (user details)
        if Config.GET_USER_DETAILS_COMMAND in text:
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /unblock_user
        if Config.UNBLOCK_USER_COMMAND in text:
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /block_user
        if Config.BLOCK_USER_COMMAND in text:
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /broadcast
        if text.startswith(Config.BROADCAST_MESSAGE):
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /log (user logs)
        if Config.GET_USER_LOGS_COMMAND in text:
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return
        # /reload_cache
        if text.startswith(Config.RELOAD_CACHE_COMMAND):
            send_to_user(message, LoggerMsg.ACCESS_DENIED_ADMIN)
            return

    # ----- Basic Commands -----
    # /Start Command
    if text == "/start":
        if is_admin:
            send_to_user(message, LoggerMsg.WELCOME_MASTER)
        else:
            # For non-admins, check subscription first
            if not is_user_in_channel(app, message):
                return  # is_user_in_channel already sends subscription message
            # User is subscribed, send welcome message
            from HELPERS.safe_messeger import safe_send_message
            safe_send_message(
                message.chat.id,
                Messages.URL_EXTRACTOR_WELCOME_MSG.format(first_name=message.chat.first_name, credits=Config.CREDITS_MSG),
                parse_mode=enums.ParseMode.HTML,
                message=message)
            send_to_logger(message, LoggerMsg.USER_STARTED_BOT.format(chat_id=message.chat.id))
        return

    # /Help Command
    if text == "/help":
        # For non-admins, check subscription first
        if not is_user_in_channel(app, message):
            return  # is_user_in_channel already sends subscription message
        # User is subscribed or admin, send help message
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="help_msg|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        try:
            safe_send_message(message.chat.id, (Config.HELP_MSG),
                             parse_mode=enums.ParseMode.HTML,
                             reply_markup=keyboard,
                             message=message)
        except Exception:
            # Fallback without parse_mode if enums shadowed unexpectedly
            safe_send_message(message.chat.id, (Config.HELP_MSG), reply_markup=keyboard, message=message)
        send_to_logger(message, LoggerMsg.HELP_SENT_TO_USER)
        return

    # /add_bot_to_group Command
    if text == Config.ADD_BOT_TO_GROUP_COMMAND:
        # For non-admins, check subscription first
        if not is_user_in_channel(app, message):
            return  # is_user_in_channel already sends subscription message
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(Messages.URL_EXTRACTOR_ADD_GROUP_CLOSE_BUTTON_MSG, callback_data="add_group_msg|close")]
        ])
        from HELPERS.safe_messeger import safe_send_message
        try:
            safe_send_message(
                message.chat.id,
                (Config.ADD_BOT_TO_GROUP_MSG),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboard,
                message=message,
            )
        except Exception:
            safe_send_message(message.chat.id, (Config.ADD_BOT_TO_GROUP_MSG), reply_markup=keyboard, message=message)
        send_to_logger(message, LoggerMsg.ADD_BOT_TO_GROUP_SENT)
        return

    # For non-admin users, if they haven't Joined the Channel, Exit ImmediaTely.
    # This check applies to all user commands below, but not to basic commands above.
    if not is_admin and not is_user_in_channel(app, message):
        return

    # ----- User Commands -----
    # /Search Command
    if text.startswith(Config.SEARCH_COMMAND):
        search_command(app, message)
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
        keyboard_command(app, message)
        return
        
    # /Save_as_cookie Command
    if text.startswith(Config.SAVE_AS_COOKIE_COMMAND):
        save_as_cookie_file(app, message)
        return

    # /Subs Command
    if text.startswith(Config.SUBS_COMMAND):
        subs_command(app, message)
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
        proxy_command(app, message)
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
        link_command(app, message)
        return

    # /Img Command
    if text.startswith(Config.IMG_COMMAND):
        image_command(app, message)
        return

    # /Args Command
    if text.startswith(Config.ARGS_COMMAND):
        from COMMANDS.args_cmd import args_command
        args_command(app, message)
        return

    # /List Command
    if text.startswith(Config.LIST_COMMAND):
        from COMMANDS.list_cmd import list_command
        list_command(app, message)
        return

    # /NSFW Command
    if text.startswith(Config.NSFW_COMMAND):
        from COMMANDS.nsfw_cmd import nsfw_command
        nsfw_command(app, message)
        return

    # /cookie Command (exact or with arguments only). Avoid matching '/cookies_from_browser'.
    if text == Config.DOWNLOAD_COOKIE_COMMAND or text.startswith(Config.DOWNLOAD_COOKIE_COMMAND + " "):
        raw_args = text[len(Config.DOWNLOAD_COOKIE_COMMAND):].strip()
        cookie_args = raw_args.lower()
        
        # Handle direct arguments
        if cookie_args.startswith(Messages.URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG):
            # Support optional index: /cookie youtube <n>
            selected_index = None
            try:
                parts = raw_args.split()
                if len(parts) >= 1 and parts[0].lower() == Messages.URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG:
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
            
        #elif cookie_args == "instagram":
            # Simulate Instagram button click
            #from pyrogram.types import CallbackQuery
            #from collections import namedtuple
            
            #FakeCallbackQuery = namedtuple('FakeCallbackQuery', ['from_user', 'message', 'data', 'id'])
            #FakeUser = namedtuple('FakeUser', ['id'])
            
            #fake_callback = FakeCallbackQuery(
                #from_user=FakeUser(id=user_id),
                #message=message,
                #data="download_cookie|instagram",
                #id="fake_callback_id"
            #)
            
            #from COMMANDS.cookies_cmd import download_and_save_cookie
            #download_and_save_cookie(app, fake_callback, Config.INSTAGRAM_COOKIE_URL, "instagram")
            #return
            
        elif cookie_args == Messages.URL_EXTRACTOR_COOKIE_ARGS_TIKTOK_MSG:
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
            
        elif cookie_args in ["x", Messages.URL_EXTRACTOR_COOKIE_ARGS_TWITTER_MSG]:
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
            
        elif cookie_args == Messages.URL_EXTRACTOR_COOKIE_ARGS_CUSTOM_MSG:
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
                app.answer_callback_query(fake_callback.id)
            except Exception:
                pass
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(Messages.URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
            ])
            from HELPERS.safe_messeger import safe_send_message
            from pyrogram.types import ReplyParameters
            safe_send_message(
                fake_callback.message.chat.id,
                Config.SAVE_AS_COOKIE_HINT,
                reply_parameters=ReplyParameters(message_id=fake_callback.message.id if hasattr(fake_callback.message, 'id') else None),
                reply_markup=keyboard,
                _callback_query=fake_callback,
                _fallback_notice="⏳ Flood limit. Try later."
            )
            return
            
        elif cookie_args == "" or cookie_args is None:
            # No arguments - show regular menu
            download_cookie(app, message)
            return
        else:
            # Invalid argument - show usage message
            from pyrogram.types import ReplyParameters
            usage_text = """
<b>🍪 Cookie Command Usage</b>

<code>/cookie</code> - Show cookie menu
<code>/cookie youtube</code> - Download YouTube cookies
<code>/cookie instagram</code> - Download Instagram cookies
<code>/cookie tiktok</code> - Download TikTok cookies
<code>/cookie x</code> or <code>/cookie twitter</code> - Download Twitter/X cookies
<code>/cookie facebook</code> - Download Facebook cookies
<code>/cookie custom</code> - Show custom cookie instructions

<i>Available services depend on bot configuration.</i>
"""
            app.send_message(
                message.chat.id,
                usage_text,
                parse_mode=enums.ParseMode.HTML,
                reply_parameters=ReplyParameters(message_id=message.id)
            )
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

    # (handled via Config.LINK_COMMAND and Config.PROXY_COMMAND branches above)

        # /Playlist Command
    if text.startswith(Config.PLAYLIST_COMMAND):
        playlist_command(app, message)
        return

        # /Clean Command
    if text.startswith(Config.CLEAN_COMMAND):
        clean_args = text[len(Config.CLEAN_COMMAND):].strip().lower()
        if clean_args in ["cookie", "cookies"]:
            remove_media(message, only=["cookie.txt"])
            # Clear YouTube cookie validation cache for this user
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(f"Failed to clear YouTube cookie cache: {e}")
            send_to_all(message, "🗑 Cookie file removed and cache cleared.")
            return
        elif clean_args in ["log", "logs"]:
            remove_media(message, only=["logs.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_LOGS_FILE_REMOVED_MSG)
            return
        elif clean_args in ["tag", "tags"]:
            remove_media(message, only=["tags.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_TAGS_FILE_REMOVED_MSG)
            return
        elif clean_args == "format":
            remove_media(message, only=["format.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_FORMAT_FILE_REMOVED_MSG)
            return
        elif clean_args == "split":
            remove_media(message, only=["split.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_SPLIT_FILE_REMOVED_MSG)
            return
        elif clean_args == "mediainfo":
            remove_media(message, only=["mediainfo.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_MEDIAINFO_FILE_REMOVED_MSG)
            return
        elif clean_args == "subs":
            remove_media(message, only=["subs.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_SUBS_SETTINGS_REMOVED_MSG)
            clear_subs_check_cache()
            return
        elif clean_args == "keyboard":
            remove_media(message, only=["keyboard.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_KEYBOARD_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "args":
            remove_media(message, only=["args.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_ARGS_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "nsfw":
            remove_media(message, only=["nsfw_blur.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_NSFW_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "proxy":
            remove_media(message, only=["proxy.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_PROXY_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "flood_wait":
            remove_media(message, only=["flood_wait.txt"])
            send_to_all(message, Messages.URL_EXTRACTOR_CLEAN_FLOOD_WAIT_SETTINGS_REMOVED_MSG)
            return
        elif clean_args == "all":
            # Delete all files and display the list of deleted ones
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                send_to_all(message, Messages.URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
                clear_subs_check_cache()
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

            # Clear YouTube cookie validation cache for this user
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(f"Failed to clear YouTube cookie cache: {e}")
            
            if removed_files:
                files_list = "\n".join([f"• {file}" for file in removed_files])
                send_to_all(message, Messages.URL_EXTRACTOR_ALL_FILES_REMOVED_MSG.format(files_list=files_list))
            else:
                send_to_all(message, Messages.URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG)
            return
        else:
            # Regular command /clean - delete only media files with filtering
            remove_media(message)
            send_to_all(message, Messages.URL_EXTRACTOR_ALL_MEDIA_FILES_REMOVED_MSG)
            try:
                from COMMANDS.cookies_cmd import clear_youtube_cookie_cache
                clear_youtube_cookie_cache(message.chat.id)
            except Exception as e:
                logger.error(f"Failed to clear YouTube cookie cache: {e}")
            clear_subs_check_cache()
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
        split_command(app, message)
        return

    # /Search Command
    if text.startswith(Config.SEARCH_COMMAND):
        search_command(app, message)
        return

    # /uncache Command - Clear cache for URL (for admins only)
    if text.startswith(Config.UNCACHE_COMMAND):
        if is_admin:
            uncache_command(app, message)
        else:
            send_to_all(message, Messages.URL_PARSER_ADMIN_ONLY_MSG)
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
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(Messages.URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG, callback_data="vid_help|close")]])
                help_text = (
                    f"<b>{Messages.URL_EXTRACTOR_VID_HELP_TITLE_MSG}</b>\n\n"
                    f"{Messages.URL_EXTRACTOR_VID_HELP_USAGE_MSG}\n\n"
                    f"<b>{Messages.URL_EXTRACTOR_VID_HELP_EXAMPLES_MSG}</b>\n"
                    f"{Messages.URL_EXTRACTOR_VID_HELP_EXAMPLE_1_MSG}\n\n"
                    f"{Messages.URL_EXTRACTOR_VID_HELP_ALSO_SEE_MSG}"
                )
                safe_send_message(message.chat.id, help_text, parse_mode=enums.ParseMode.HTML, reply_markup=kb, message=message)
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
        if not is_user_blocked(message):
            clear_subs_check_cache()
            try:
                video_url_extractor(app, message)
            except Exception as e:
                logger.error(f"video_url_extractor failed, fallback to gallery-dl: {e}")
                try:
                    image_command(app, message)
                except Exception as e2:
                    logger.error(f"gallery-dl fallback also failed: {e2}")
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

        # /reload_cache Command - Reload cache for URL
        if Config.RELOAD_CACHE_COMMAND in text:
            reload_firebase_cache_command(app, message)
            return

        # /auto_cache Command - Toggle automatic cache reloading
        if Config.AUTO_CACHE_COMMAND in text:
            auto_cache_command(app, message)
            return

        # /Search Command (for admins too)
        if text.startswith(Config.SEARCH_COMMAND):
            search_command(app, message)
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
                if message.reply_to_message and message.reply_to_message.video:
                    caption_editor(app, message)
        return

    logger.info(f"{user_id} No matching command processed.")
    clear_subs_check_cache()

@app.on_callback_query(filters.regex("^keyboard\\|"))
def keyboard_callback_handler_wrapper(app, callback_query):
    """Handle keyboard setting callbacks"""
    keyboard_callback_handler(app, callback_query)

# The function is_playlist_with_range is now imported from URL_PARSERS.playlist_utils

# Callback handler for add_bot_to_group close button
@app.on_callback_query(filters.regex(r"^add_group_msg\|"))
def add_group_msg_callback(app, callback_query):
    """Handle add_bot_to_group command callback queries"""
    try:
        data = callback_query.data.split("|")[1]
        user_id = callback_query.from_user.id
        
        if data == "close":
            # Delete the message with add_bot_to_group instructions
            try:
                app.delete_messages(
                    callback_query.message.chat.id,
                    callback_query.message.id
                )
            except Exception:
                # If can't delete, just edit to show closed message
                app.edit_message_text(
                    callback_query.message.chat.id,
                    callback_query.message.id,
                    "🤖 Add bot to group helper closed"
                )
            
            # Answer callback query
            callback_query.answer(Messages.URL_EXTRACTOR_CLOSED_MSG)
            
            # Log the action
            send_to_logger(callback_query.message, Messages.URL_EXTRACTOR_ADD_GROUP_USER_CLOSED_MSG.format(user_id=user_id))
            
    except Exception as e:
        # Log error and answer callback
        send_to_logger(callback_query.message, f"Error in add_group_msg callback handler: {e}")
        callback_query.answer(Messages.URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)

######################################################  
