from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message
from HELPERS.logger import logger
from CONFIG.messages import MessagesConfig as Messages
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
        callback_query.answer(Messages.CLEAN_COOKIES_CLEANED_MSG)
        return
    elif data == "logs":
        url_distractor(app, fake_message("/clean logs", user_id))
        callback_query.answer(Messages.CLEAN_LOGS_CLEANED_MSG)
        return
    elif data == "tags":
        url_distractor(app, fake_message("/clean tags", user_id))
        callback_query.answer(Messages.CLEAN_TAGS_CLEANED_MSG)
        return
    elif data == "format":
        url_distractor(app, fake_message("/clean format", user_id))
        callback_query.answer(Messages.CLEAN_FORMAT_CLEANED_MSG)
        return
    elif data == "split":
        url_distractor(app, fake_message("/clean split", user_id))
        callback_query.answer(Messages.CLEAN_SPLIT_CLEANED_MSG)
        return
    elif data == "mediainfo":
        url_distractor(app, fake_message("/clean mediainfo", user_id))
        callback_query.answer(Messages.CLEAN_MEDIAINFO_CLEANED_MSG)
        return
    elif data == "subs":
        url_distractor(app, fake_message("/clean subs", user_id))
        callback_query.answer(Messages.CLEAN_SUBS_CLEANED_MSG)
        return
    elif data == "keyboard":
        url_distractor(app, fake_message("/clean keyboard", user_id))
        callback_query.answer(Messages.CLEAN_KEYBOARD_CLEANED_MSG)
        return
    elif data == "args":
        url_distractor(app, fake_message("/clean args", user_id))
        callback_query.answer(Messages.CLEAN_ARGS_CLEANED_MSG)
        return
    elif data == "nsfw":
        url_distractor(app, fake_message("/clean nsfw", user_id))
        callback_query.answer(Messages.CLEAN_NSFW_CLEANED_MSG)
        return
    elif data == "proxy":
        url_distractor(app, fake_message("/clean proxy", user_id))
        callback_query.answer(Messages.CLEAN_PROXY_CLEANED_MSG)
        return
    elif data == "flood_wait":
        url_distractor(app, fake_message("/clean flood_wait", user_id))
        callback_query.answer(Messages.CLEAN_FLOOD_WAIT_CLEANED_MSG)
        return
    elif data == "all":
        url_distractor(app, fake_message("/clean all", user_id))
        callback_query.answer(Messages.CLEAN_ALL_CLEANED_MSG)
        return
    elif data == "back":
        # Back to the cookies menu
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
        callback_query.edit_message_text(
            Messages.CLEAN_COOKIES_MENU_TITLE_MSG,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
