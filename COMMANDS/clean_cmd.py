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
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean cookie", user_id))
        callback_query.answer(Messages.CLEAN_COOKIES_CLEANED_MSG)
        return
    elif data == "logs":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean logs", user_id))
        callback_query.answer(Messages.CLEAN_LOGS_CLEANED_MSG)
        return
    elif data == "tags":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean tags", user_id))
        callback_query.answer(Messages.CLEAN_TAGS_CLEANED_MSG)
        return
    elif data == "format":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean format", user_id))
        callback_query.answer(Messages.CLEAN_FORMAT_CLEANED_MSG)
        return
    elif data == "split":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean split", user_id))
        callback_query.answer(Messages.CLEAN_SPLIT_CLEANED_MSG)
        return
    elif data == "mediainfo":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean mediainfo", user_id))
        callback_query.answer(Messages.CLEAN_MEDIAINFO_CLEANED_MSG)
        return
    elif data == "subs":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean subs", user_id))
        callback_query.answer(Messages.CLEAN_SUBS_CLEANED_MSG)
        return
    elif data == "keyboard":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean keyboard", user_id))
        callback_query.answer(Messages.CLEAN_KEYBOARD_CLEANED_MSG)
        return
    elif data == "args":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean args", user_id))
        callback_query.answer(Messages.CLEAN_ARGS_CLEANED_MSG)
        return
    elif data == "nsfw":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean nsfw", user_id))
        callback_query.answer(Messages.CLEAN_NSFW_CLEANED_MSG)
        return
    elif data == "proxy":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean proxy", user_id))
        callback_query.answer(Messages.CLEAN_PROXY_CLEANED_MSG)
        return
    elif data == "flood_wait":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean flood_wait", user_id))
        callback_query.answer(Messages.CLEAN_FLOOD_WAIT_CLEANED_MSG)
        return
    elif data == "all":
        from CONFIG.messages import MessagesConfig as Messages
        url_distractor(app, fake_message("/clean all", user_id))
        callback_query.answer(Messages.CLEAN_ALL_FILES_CLEANED_MSG)
        return
    elif data == "back":
        # Back to the cookies menu
        from CONFIG.messages import MessagesConfig as Messages
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(Messages.CLEAN_BTN_COOKIE,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(Messages.CLEAN_BTN_COOKIES_FROM_BROWSER,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(Messages.CLEAN_BTN_CHECK_COOKIE,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(Messages.CLEAN_BTN_SAVE_AS_COOKIE,
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton(Messages.CLEAN_BTN_BACK, callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            "<b>🍪 COOKIES</b>\n\nChoose an action:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        callback_query.answer()
        return
