# ===================== /settings =====================
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import enums
from HELPERS.logger import send_to_logger

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message
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
        [InlineKeyboardButton("🔚 Close", callback_data="help_msg|close")]
    ])
    app.send_message(message.chat.id, (Config.HELP_MSG),
                     parse_mode=enums.ParseMode.HTML,
                     reply_markup=keyboard)
    send_to_logger(message, f"Send help txt to user")

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("settings") & filters.private)
# @reply_with_keyboard
def settings_command(app, message):
    user_id = message.chat.id
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
        [InlineKeyboardButton("🔚 Close", callback_data="settings__menu__close")]
    ])
    app.send_message(
        user_id,
        "<b>Bot Settings</b>\n\nChoose a category:",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
        reply_to_message_id=message.id
    )
    send_to_logger(message, "Opened /settings menu")


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
        callback_query.answer("Menu closed.")
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
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🧹 Clean Options</b>\n\nChoose what to clean:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "cookies":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 /download_cookie - Download my 5 cookies",
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton("🌐 /cookies_from_browser - Get browser's YT-cookie",
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton("🔎 /check_cookie - Validate your cookie file",
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton("🔖 /save_as_cookie - Upload custom cookie",
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🍪 COOKIES</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "media":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📼 /format - Change quality & format", callback_data="settings__cmd__format")],
            [InlineKeyboardButton("📊 /mediainfo - Turn ON / OFF MediaInfo", callback_data="settings__cmd__mediainfo")],
            [InlineKeyboardButton("✂️ /split - Change split video part size", callback_data="settings__cmd__split")],
            [InlineKeyboardButton("🎧 /audio - Download video as audio", callback_data="settings__cmd__audio")],
            [InlineKeyboardButton("💬 /subs - Subtitles language settings", callback_data="settings__cmd__subs")],
            [InlineKeyboardButton("📋 /playlist - How to download playlists", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🎞 MEDIA</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "logs":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("#️⃣ /tags - Send your #tags", callback_data="settings__cmd__tags")],
            [InlineKeyboardButton("🆘 /help - Get instructions", callback_data="settings__cmd__help")],
            [InlineKeyboardButton("📃 /usage -Send your logs", callback_data="settings__cmd__usage")],
            [InlineKeyboardButton("📋 /playlist - Playlist's help", callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>📖 INFO</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
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
            [InlineKeyboardButton("🔚 Close", callback_data="settings__menu__close")]
        ])
        callback_query.edit_message_text(
            "<b>Bot Settings</b>\n\nChoose a category:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
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
                InlineKeyboardButton("🗑  All files", callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🧹 Clean Options</b>\n\nChoose what to clean:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
    if data == "download_cookie":
        url_distractor(app, fake_message("/download_cookie", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "cookies_from_browser":
        cookies_from_browser(app, fake_message("/cookies_from_browser", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "check_cookie":
        url_distractor(app, fake_message("/check_cookie", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "save_as_cookie":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="save_as_cookie_hint|close")]
        ])
        app.send_message(user_id, Config.SAVE_AS_COOKIE_HINT, reply_to_message_id=callback_query.message.id,
                         parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        callback_query.answer("Hint sent.")
        return
    if data == "format":
        # Add the command attribute for set_format to work correctly
        set_format(app, fake_message("/format", user_id, command=["format"]))
        callback_query.answer("Command executed.")
        return
        
    # /Subs Command
    if data == "subs":
        subs_command(app, fake_message("/subs", user_id))
        callback_query.answer("Command executed.")
        return

    if data == "mediainfo":
        mediainfo_command(app, fake_message("/mediainfo", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "split":
        split_command(app, fake_message("/split", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "audio":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="audio_hint|close")]
        ])
        app.send_message(user_id,
                         "Download only audio from video source.\n\nUsage: /audio + URL \n\n(ex. /audio https://youtu.be/abc123)\n(ex. /audio https://youtu.be/playlist?list=abc123*1*10)",
                         reply_to_message_id=callback_query.message.id,
                         reply_markup=keyboard)
        callback_query.answer("Hint sent.")
        return
    if data == "tags":
        tags_command(app, fake_message("/tags", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "help":
        command2(app, fake_message("/help", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "usage":
        url_distractor(app, fake_message("/usage", user_id))
        callback_query.answer("Command executed.")
        return
    if data == "playlist":
        playlist_command(app, fake_message("/playlist", user_id))
        callback_query.answer("Command executed.")
        return
    callback_query.answer("Unknown command.", show_alert=True)
