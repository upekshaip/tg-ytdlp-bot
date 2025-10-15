from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message
from HELPERS.logger import logger
from CONFIG.messages import Messages, safe_get_messages
# Lazy import to avoid circular dependency - import url_distractor inside functions

# Get app instance for decorators
app = get_app()

@app.on_callback_query(filters.regex(r"^clean_option\|"))
# @reply_with_keyboard
async def clean_option_callback(app, callback_query):
    # Get user_id first
    user_id = getattr(callback_query, 'from_user', None)
    if user_id is None:
        user_id = getattr(callback_query, 'user', None)
    if user_id is None:
        return
    user_id = getattr(user_id, 'id', None)
    if user_id is None:
        return
    
    messages = safe_get_messages(user_id)
    # Lazy import to avoid circular dependency
    from URL_PARSERS.url_extractor import url_distractor
    data = callback_query.data.split("|")[1]

    if data == "cookies":
        await url_distractor(app, fake_message("/clean cookie", user_id))
        await callback_query.answer(messages.CLEAN_COOKIES_CLEANED_MSG)
        return
    elif data == "logs":
        await url_distractor(app, fake_message("/clean logs", user_id))
        await callback_query.answer(messages.CLEAN_LOGS_CLEANED_MSG)
        return
    elif data == "tags":
        await url_distractor(app, fake_message("/clean tags", user_id))
        await callback_query.answer(messages.CLEAN_TAGS_CLEANED_MSG)
        return
    elif data == "format":
        await url_distractor(app, fake_message("/clean format", user_id))
        await callback_query.answer(messages.CLEAN_FORMAT_CLEANED_MSG)
        return
    elif data == "split":
        await url_distractor(app, fake_message("/clean split", user_id))
        await callback_query.answer(messages.CLEAN_SPLIT_CLEANED_MSG)
        return
    elif data == "mediainfo":
        await url_distractor(app, fake_message("/clean mediainfo", user_id))
        await callback_query.answer(messages.CLEAN_MEDIAINFO_CLEANED_MSG)
        return
    elif data == "subs":
        await url_distractor(app, fake_message("/clean subs", user_id))
        await callback_query.answer(messages.CLEAN_SUBS_CLEANED_MSG)
        return
    elif data == "keyboard":
        await url_distractor(app, fake_message("/clean keyboard", user_id))
        await callback_query.answer(messages.CLEAN_KEYBOARD_CLEANED_MSG)
        return
    elif data == "args":
        await url_distractor(app, fake_message("/clean args", user_id))
        await callback_query.answer(messages.CLEAN_ARGS_CLEANED_MSG)
        return
    elif data == "nsfw":
        await url_distractor(app, fake_message("/clean nsfw", user_id))
        await callback_query.answer(messages.CLEAN_NSFW_CLEANED_MSG)
        return
    elif data == "proxy":
        await url_distractor(app, fake_message("/clean proxy", user_id))
        await callback_query.answer(messages.CLEAN_PROXY_CLEANED_MSG)
        return
    elif data == "flood_wait":
        await url_distractor(app, fake_message("/clean flood_wait", user_id))
        await callback_query.answer(messages.CLEAN_FLOOD_WAIT_CLEANED_MSG)
        return
    elif data == "all":
        await url_distractor(app, fake_message("/clean all", user_id))
        await callback_query.answer(messages.CLEAN_ALL_CLEANED_MSG)
        return
    elif data == "back":
        # Back to the cookies menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.CLEAN_COOKIE_DOWNLOAD_BUTTON_MSG,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(messages.CLEAN_COOKIES_FROM_BROWSER_BUTTON_MSG,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(messages.CLEAN_CHECK_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(messages.CLEAN_SAVE_AS_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton("🔙Back", callback_data="settings__menu__back")]
        ])
        callback_query.edit_message_text(
            messages.CLEAN_COOKIES_MENU_TITLE_MSG,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
        return
