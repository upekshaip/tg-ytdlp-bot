from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message
from HELPERS.logger import logger
# Lazy import to avoid circular dependency - import url_distractor inside functions

# Get app instance for decorators
app = get_app()

@app.on_callback_query(filters.regex(r"^clean_option\|"))
# @reply_with_keyboard
def clean_option_callback(app, callback_query):
    # Lazy import to avoid circular dependency
    from URL_PARSERS.url_extractor import url_distractor
    
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    if data == "cookies":
        url_distractor(app, fake_message("/clean cookie", user_id))
        callback_query.answer("Cookies cleaned.")
        return
    elif data == "logs":
        url_distractor(app, fake_message("/clean logs", user_id))
        callback_query.answer("logs cleaned.")
        return
    elif data == "tags":
        url_distractor(app, fake_message("/clean tags", user_id))
        callback_query.answer("tags cleaned.")
        return
    elif data == "format":
        url_distractor(app, fake_message("/clean format", user_id))
        callback_query.answer("format cleaned.")
        return
    elif data == "split":
        url_distractor(app, fake_message("/clean split", user_id))
        callback_query.answer("split cleaned.")
        return
    elif data == "mediainfo":
        url_distractor(app, fake_message("/clean mediainfo", user_id))
        callback_query.answer("mediainfo cleaned.")
        return
    elif data == "subs":
        url_distractor(app, fake_message("/clean subs", user_id))
        callback_query.answer("Subtitle settings cleaned.")
        return
    elif data == "all":
        url_distractor(app, fake_message("/clean all", user_id))
        callback_query.answer("All files cleaned.")
        return
    elif data == "back":
        # Back to the cookies menu
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
