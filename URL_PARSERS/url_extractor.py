# ####################################################################################

# Checking Actions
# Text Message Handler for General Commands
from HELPERS.app_instance import get_app
from HELPERS.decorators import reply_with_keyboard
from HELPERS.limitter import is_user_in_channel, check_user
from HELPERS.logger import send_to_all, send_to_logger, send_to_user
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
from COMMANDS.admin_cmd import get_user_log, send_promo_message, block_user, unblock_user, check_runtime, get_user_details, uncache_command, reload_firebase_cache_command
from DATABASE.cache_db import auto_cache_command
from DATABASE.firebase_init import is_user_blocked
import os
from URL_PARSERS.video_extractor import video_url_extractor
from URL_PARSERS.playlist_utils import is_playlist_with_range
from pyrogram import filters
from CONFIG.config import Config
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
    }

    if text in emoji_to_command:
        mapped = emoji_to_command[text]
        # Special case: headphones emoji should show audio usage hint
        if mapped == "/audio":
            from pyrogram.types import ReplyParameters
            app.send_message(
                message.chat.id,
                "Download only audio from video source.\n\nUsage: /audio + URL \n\n(ex. /audio https://youtu.be/abc123)\n(ex. /audio https://youtu.be/playlist?list=abc123*1*10)",
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            return
        # Emulate a user command for the mapped emoji
        return url_distractor(app, fake_message(mapped, user_id))

    # For non-admin users, if they haven't Joined the Channel, Exit ImmediaTely.
    if not is_admin and not is_user_in_channel(app, message):
        return

    # ----- Basic Commands -----
    # /Start Command
    if text == "/start":
        if is_admin:
            send_to_user(message, "Welcome Master 🥷")
        else:
            check_user(message)
            app.send_message(
                message.chat.id,
                f"Hello {message.chat.first_name},\n \n<i>This bot🤖 can download any videos into telegram directly.😊 For more information press <b>/help</b></i> 👈\n \n {Config.CREDITS_MSG}")
            send_to_logger(message, f"{message.chat.id} - user started the bot")
        return

    # /Help Command
    if text == "/help":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="help_msg|close")]
        ])
        app.send_message(message.chat.id, (Config.HELP_MSG),
                         parse_mode=enums.ParseMode.HTML,
                         reply_markup=keyboard)
        send_to_logger(message, f"Send help txt to user")
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

    # /cookie Command (exact or with arguments only). Avoid matching '/cookies_from_browser'.
    if text == Config.DOWNLOAD_COOKIE_COMMAND or text.startswith(Config.DOWNLOAD_COOKIE_COMMAND + " "):
        raw_args = text[len(Config.DOWNLOAD_COOKIE_COMMAND):].strip()
        cookie_args = raw_args.lower()
        
        # Handle direct arguments
        if cookie_args.startswith("youtube"):
            # Support optional index: /cookie youtube <n>
            selected_index = None
            try:
                parts = raw_args.split()
                if len(parts) >= 1 and parts[0].lower() == "youtube":
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
            
        elif cookie_args == "tiktok":
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
            
        elif cookie_args in ["x", "twitter"]:
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
            
        elif cookie_args == "custom":
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
                [InlineKeyboardButton("🔚Close", callback_data="save_as_cookie_hint|close")]
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
        elif clean_args == "subs":
            remove_media(message, only=["subs.txt"])
            send_to_all(message, "🗑 Subtitle settings removed.")
            clear_subs_check_cache()
            return
        elif clean_args == "keyboard":
            remove_media(message, only=["keyboard.txt"])
            send_to_all(message, "🗑 Keyboard settings removed.")
            return
        elif clean_args == "all":
            # Delete all files and display the list of deleted ones
            user_dir = f'./users/{str(message.chat.id)}'
            if not os.path.exists(user_dir):
                send_to_all(message, "🗑 No files to remove.")
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
                send_to_all(message, f"🗑 All files removed successfully!\n\nRemoved files:\n{files_list}")
            else:
                send_to_all(message, "🗑 No files to remove.")
            return
        else:
            # Regular command /clean - delete only media files with filtering
            remove_media(message)
            send_to_all(message, "🗑 All media files are removed.")
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
            send_to_all(message, "❌ This command is only available for administrators.")
        return

    # If the Message Contains a URL, Launch The Video Download Function.
    if ("https://" in text) or ("http://" in text):
        if not is_user_blocked(message):
            # Clean the cache of subtitles before processing the new URL
            clear_subs_check_cache()
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
######################################################  
