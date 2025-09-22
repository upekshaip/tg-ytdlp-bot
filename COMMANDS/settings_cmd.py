# ===================== /settings =====================
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_logger
from HELPERS.limitter import is_user_in_channel

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message, safe_send_message, safe_edit_message_text
from pyrogram.errors import FloodWait
from CONFIG.messages import Messages as Messages
import os
# Lazy imports to avoid circular dependency - import url_distractor inside functions
from COMMANDS.cookies_cmd import cookies_from_browser
from COMMANDS.format_cmd import set_format
from COMMANDS.split_sizer import split_command
from COMMANDS.mediainfo_cmd import mediainfo_command
from COMMANDS.subtitles_cmd import subs_command
from COMMANDS.tag_cmd import tags_command
from COMMANDS.other_handlers import playlist_command

# Create command2 function for compatibility
def command2(app, message):
    """Help command - alias for compatibility"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from pyrogram import enums
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚Close", callback_data="help_msg|close")]
    ])

    result = safe_send_message(message.chat.id, (Messages.HELP_MSG),

                      parse_mode=enums.ParseMode.HTML,
                      reply_markup=keyboard)
    send_to_logger(message, Messages.SETTINGS_HELP_SENT_MSG)
    return result

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("settings") & filters.private)
# @reply_with_keyboard
def settings_command(app, message):
    user_id = message.chat.id
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    # Main settings menu
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean"),
            InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies"),
        ],
        [
            InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media"),
            InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs"),
        ],
        [
            InlineKeyboardButton("⚙️ MORE", callback_data="settings__menu__more"),
            InlineKeyboardButton("🔚Close", callback_data="settings__menu__close"),
        ]
    ])
    safe_send_message(
        user_id,
Messages.SETTINGS_TITLE_MSG,
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
    send_to_logger(message, Messages.SETTINGS_MENU_OPENED_MSG)


@app.on_callback_query(filters.regex(r"^settings__menu__"))
# @reply_with_keyboard
def settings_menu_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[-1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(Messages.SETTINGS_MENU_CLOSED_MSG)
        except Exception:
            pass
        return
    if data == "clean":
        # Show the cleaning menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍪 Cookies only", callback_data="clean_option|cookies"),
                InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags"),
                InlineKeyboardButton("📼 Format", callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton("✂️ Split", callback_data="clean_option|split"),
                InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton("💬 Subtitles", callback_data="clean_option|subs"),
                InlineKeyboardButton("🎹 Keyboard", callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton("⚙️ Args", callback_data="clean_option|args"),
                InlineKeyboardButton("🔞 NSFW", callback_data="clean_option|nsfw"),
            ],
            [
                InlineKeyboardButton("🌎 Proxy", callback_data="clean_option|proxy"),
                InlineKeyboardButton("🔄 Flood wait", callback_data="clean_option|flood_wait"),
            ],
            [
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
Messages.SETTINGS_CLEAN_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "cookies":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 /cookie - Download my 5 cookies",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get browser's YT-cookie",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Validate your cookie file",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Upload custom cookie",
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
Messages.SETTINGS_COOKIES_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "media":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📼 /format - Change quality & format", callback_data="settings__cmd__format")],
            [InlineKeyboardButton("📊 /mediainfo - Turn ON / OFF MediaInfo", callback_data="settings__cmd__mediainfo")],
            [InlineKeyboardButton("✂️ /split - Change split video part size", callback_data="settings__cmd__split")],
            [InlineKeyboardButton("🎧 /audio - Download video as audio", callback_data="settings__cmd__audio")],
            [InlineKeyboardButton("💬 /subs - Subtitles language settings", callback_data="settings__cmd__subs")],
            [InlineKeyboardButton("⏯️ /playlist - How to download playlists", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🖼 /img - Download images via gallery-dl", callback_data="settings__cmd__img")],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
Messages.SETTINGS_MEDIA_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "logs":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("#️⃣ /tags - Send your #tags", callback_data="settings__cmd__tags")],
            [InlineKeyboardButton("🆘 /help - Get instructions", callback_data="settings__cmd__help")],
            [InlineKeyboardButton("📃 /usage -Send your logs", callback_data="settings__cmd__usage")],
            [InlineKeyboardButton("⏯️ /playlist - Playlist's help", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🤖 /add_bot_to_group - howto", callback_data="settings__cmd__add_bot_to_group")],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
Messages.SETTINGS_LOGS_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "more":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 /link - Get direct video links", callback_data="settings__cmd__link")],
            [InlineKeyboardButton("🌍 /proxy - Enable/disable proxy", callback_data="settings__cmd__proxy")],
            [InlineKeyboardButton("🎹 /keyboard - Keyboard layout", callback_data="settings__cmd__keyboard")],
            [InlineKeyboardButton("🔍 /search - Inline search helper", callback_data="settings__cmd__search_menu")],
            [InlineKeyboardButton("⚙️ /args - yt-dlp arguments", callback_data="settings__cmd__args")],
            [InlineKeyboardButton("🔞 /nsfw - NSFW blur settings", callback_data="settings__cmd__nsfw")],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
Messages.SETTINGS_MORE_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "back":
        # Return to main menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🧹 CLEAN", callback_data="settings__menu__clean"),
                InlineKeyboardButton("🍪 COOKIES", callback_data="settings__menu__cookies"),
            ],
            [
                InlineKeyboardButton("🎞 MEDIA", callback_data="settings__menu__media"),
                InlineKeyboardButton("📖 INFO", callback_data="settings__menu__logs"),
            ],
            [
                InlineKeyboardButton("⚙️ MORE", callback_data="settings__menu__more"),
                InlineKeyboardButton("🔚Close", callback_data="settings__menu__close"),
            ]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
                       Messages.SETTINGS_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return

@app.on_callback_query(filters.regex(r"^settings__cmd__"))
# @reply_with_keyboard
def settings_cmd_callback(app, callback_query: CallbackQuery):
    # Lazy import to avoid circular dependency
    from URL_PARSERS.url_extractor import url_distractor
    
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[2]

    # For commands that are processed only via url_distractor, create a temporary Message
    if data == "clean":
        # Show the cleaning menu instead of direct execution
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍪 Cookies only", callback_data="clean_option|cookies"),
                InlineKeyboardButton("📃 Logs ", callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton("#️⃣ Tags", callback_data="clean_option|tags"),
                InlineKeyboardButton("📼 Format", callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton("✂️ Split", callback_data="clean_option|split"),
                InlineKeyboardButton("📊 Mediainfo", callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton("💬 Subtitles", callback_data="clean_option|subs"),
                InlineKeyboardButton("🎹 Keyboard", callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        try:
            callback_query.edit_message_text(
                "<b>🧹 Clean Options</b>\n\nChoose what to clean:",
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
        try:
            callback_query.answer()
        except Exception:
            pass
        return
    if data == "download_cookie":
        try:
            url_distractor(app, fake_message("/cookie", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "cookies_from_browser":
        try:
            cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "check_cookie":
        try:
            url_distractor(app, fake_message("/check_cookie", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "save_as_cookie":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="save_as_cookie_hint|close")]
        ])
        safe_send_message(user_id, Messages.SAVE_AS_COOKIE_HINT, reply_parameters=ReplyParameters(message_id=callback_query.message.id),
                          parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)

        try:
            callback_query.answer(Messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass

        return
    if data == "format":
        # Add the command attribute for set_format to work correctly
        try:
            set_format(app, fake_message("/format", user_id, command=["format"]))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            callback_query.answer(Messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return
        
    # /Subs Command
    if data == "subs":
        try:
            subs_command(app, fake_message("/subs", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            callback_query.answer(Messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return

    if data == "mediainfo":
        try:
            mediainfo_command(app, fake_message("/mediainfo", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            callback_query.answer(Messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return
    if data == "split":
        try:
            split_command(app, fake_message("/split", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            callback_query.answer(Messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return
        callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        return
    if data == "audio":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="audio_hint|close")]
        ])
        safe_send_message(user_id,
                          Messages.AUDIO_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),

                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice="⏳ Flood limit. Try later.")
        try:
            callback_query.answer(Messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass

        return
    if data == "tags":
        try:
            tags_command(app, fake_message("/tags", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            callback_query.answer(Messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "help":
        try:
            res = command2(app, fake_message("/help", user_id))

        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))

            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        # If safe_send_message returned None due to FloodWait, notify via callback
        if res is None:
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
        else:
            try:
                callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
            except Exception:
                pass

        return
    if data == "usage":
        try:
            url_distractor(app, fake_message("/usage", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))

            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return
    if data == "playlist":
        try:
            playlist_command(app, fake_message("/playlist", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))

            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return
    if data == "img":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="img_hint|close")]
        ])
        safe_send_message(
            user_id,
            Messages.IMG_HELP_MSG,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice="⏳ Flood limit. Try later.",
            parse_mode=enums.ParseMode.HTML,
        )
        try:
            callback_query.answer(Messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass
        return
    if data == "link":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="link_hint|close")]
        ])
        safe_send_message(user_id,
                          Messages.LINK_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),
                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice="⏳ Flood limit. Try later.")
        try:
            callback_query.answer(Messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass
        return
    if data == "proxy":
        try:
            url_distractor(app, fake_message("/proxy", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "keyboard":
        try:
            url_distractor(app, fake_message("/keyboard", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "search_menu":
        # Get bot name from config
        bot_name = Config.BOT_NAME
        
        # Create inline keyboard with mobile button and close button (same as search.py)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📱 Mobile: Activate @vid search",
                    url=f"tg://msg?text=%40vid%20%E2%80%8B&to=%40{bot_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔚Close",
                    callback_data="search_msg|close"
                )
            ]
        ])
        
        # Send message with search instructions (same as search.py)
        text = Messages.SEARCH_MSG
        
        safe_send_message(
            user_id,
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboard,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            _callback_query=callback_query,
            _fallback_notice="⏳ Flood limit. Try later."
        )
        
        try:
            callback_query.answer(Messages.SETTINGS_SEARCH_HELPER_OPENED_MSG)
        except Exception:
            pass
        return
    if data == "add_bot_to_group":
        try:
            url_distractor(app, fake_message("/add_bot_to_group", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "args":
        try:
            from COMMANDS.args_cmd import args_command
            args_command(app, fake_message("/args", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "nsfw":
        try:
            from COMMANDS.nsfw_cmd import nsfw_command
            nsfw_command(app, fake_message("/nsfw", user_id))
        except FloodWait as e:
            user_dir = os.path.join("users", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                f.write(str(e.value))
            try:
                callback_query.answer(Messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(Messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    try:
        callback_query.answer(Messages.SETTINGS_UNKNOWN_COMMAND_MSG, show_alert=True)
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^(img_hint|link_hint|search_hint|search_msg)\|"))
def hint_callback(app, callback_query: CallbackQuery):
    """Handle hint callback close buttons"""
    data = callback_query.data.split("|")[-1]
    
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(Messages.SETTINGS_HINT_CLOSED_MSG)
        except Exception:
            pass
        return
    
    try:
        callback_query.answer()
    except Exception:
        pass
