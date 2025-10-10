# ===================== /settings =====================
from pyrogram import filters
from CONFIG.config import Config
from CONFIG.messages import Messages, get_messages_instance
from CONFIG.LANGUAGES.language_router import get_messages
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_logger
from HELPERS.limitter import is_user_in_channel

from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import fake_message, safe_send_message, safe_edit_message_text
from pyrogram.errors import FloodWait
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
    user_id = message.chat.id
    messages = get_messages_instance(user_id)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(messages.SETTINGS_DEV_GITHUB_BUTTON_MSG, url="https://github.com/upekshaip/tg-ytdlp-bot"),
            InlineKeyboardButton(messages.SETTINGS_CONTR_GITHUB_BUTTON_MSG, url="https://github.com/chelaxian/tg-ytdlp-bot")
        ],
        [InlineKeyboardButton(messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="help_msg|close")]
    ])

    result = safe_send_message(message.chat.id, (messages.HELP_MSG),

                      parse_mode=enums.ParseMode.HTML,
                      reply_markup=keyboard)
    send_to_logger(message, messages.SETTINGS_HELP_SENT_MSG)
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
    messages = get_messages_instance(user_id)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(messages.SETTINGS_CLEAN_BUTTON_MSG, callback_data="settings__menu__clean"),
            InlineKeyboardButton(messages.SETTINGS_COOKIES_BUTTON_MSG, callback_data="settings__menu__cookies"),
        ],
        [
            InlineKeyboardButton(messages.SETTINGS_MEDIA_BUTTON_MSG, callback_data="settings__menu__media"),
            InlineKeyboardButton(messages.SETTINGS_INFO_BUTTON_MSG, callback_data="settings__menu__logs"),
        ],
        [
            InlineKeyboardButton(messages.SETTINGS_MORE_BUTTON_MSG, callback_data="settings__menu__more"),
            InlineKeyboardButton(messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="settings__menu__close"),
        ]
    ])
    safe_send_message(
        user_id,
        messages.SETTINGS_TITLE_MSG,
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
    send_to_logger(message, messages.SETTINGS_MENU_OPENED_MSG)


@app.on_callback_query(filters.regex(r"^settings__menu__"))
# @reply_with_keyboard
def settings_menu_callback(app, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    messages = get_messages_instance(user_id)
    data = callback_query.data.split("__")[-1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(messages.SETTINGS_MENU_CLOSED_MSG)
        except Exception:
            pass
        return
    if data == "clean":
        # Show the cleaning menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(messages.SETTINGS_COOKIES_ONLY_BUTTON_MSG, callback_data="clean_option|cookies"),
                InlineKeyboardButton(messages.SETTINGS_LOGS_BUTTON_MSG, callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_TAGS_BUTTON_MSG, callback_data="clean_option|tags"),
                InlineKeyboardButton(messages.SETTINGS_FORMAT_BUTTON_MSG, callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_SPLIT_BUTTON_MSG, callback_data="clean_option|split"),
                InlineKeyboardButton(messages.SETTINGS_MEDIAINFO_BUTTON_MSG, callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_SUBTITLES_BUTTON_MSG, callback_data="clean_option|subs"),
                InlineKeyboardButton(messages.SETTINGS_KEYBOARD_BUTTON_MSG, callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_ARGS_BUTTON_MSG, callback_data="clean_option|args"),
                InlineKeyboardButton(messages.SETTINGS_NSFW_BUTTON_MSG, callback_data="clean_option|nsfw"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_PROXY_BUTTON_MSG, callback_data="clean_option|proxy"),
                InlineKeyboardButton(messages.SETTINGS_FLOOD_WAIT_BUTTON_MSG, callback_data="clean_option|flood_wait"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_ALL_FILES_BUTTON_MSG, callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
messages.SETTINGS_CLEAN_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "cookies":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(messages.SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(messages.SETTINGS_CHECK_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(messages.SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
messages.SETTINGS_COOKIES_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "media":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.SETTINGS_FORMAT_CMD_BUTTON_MSG, callback_data="settings__cmd__format")],
            [InlineKeyboardButton(messages.SETTINGS_MEDIAINFO_CMD_BUTTON_MSG, callback_data="settings__cmd__mediainfo")],
            [InlineKeyboardButton(messages.SETTINGS_SPLIT_CMD_BUTTON_MSG, callback_data="settings__cmd__split")],
            [InlineKeyboardButton(messages.SETTINGS_AUDIO_CMD_BUTTON_MSG, callback_data="settings__cmd__audio")],
            [InlineKeyboardButton(messages.SETTINGS_SUBS_CMD_BUTTON_MSG, callback_data="settings__cmd__subs")],
            [InlineKeyboardButton(messages.SETTINGS_PLAYLIST_CMD_BUTTON_MSG, callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton(messages.SETTINGS_IMG_CMD_BUTTON_MSG, callback_data="settings__cmd__img")],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
messages.SETTINGS_MEDIA_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "logs":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.SETTINGS_TAGS_CMD_BUTTON_MSG, callback_data="settings__cmd__tags")],
            [InlineKeyboardButton(messages.SETTINGS_HELP_CMD_BUTTON_MSG, callback_data="settings__cmd__help")],
            [InlineKeyboardButton(messages.SETTINGS_USAGE_CMD_BUTTON_MSG, callback_data="settings__cmd__usage")],
            [InlineKeyboardButton(messages.SETTINGS_PLAYLIST_HELP_CMD_BUTTON_MSG, callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton(messages.SETTINGS_ADD_BOT_CMD_BUTTON_MSG, callback_data="settings__cmd__add_bot_to_group")],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
messages.SETTINGS_LOGS_TITLE_MSG,
                               reply_markup=keyboard,
                               parse_mode=enums.ParseMode.HTML)

        try:
            callback_query.answer()
        except Exception:
            pass

        return
    if data == "more":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.SETTINGS_LINK_CMD_BUTTON_MSG, callback_data="settings__cmd__link")],
            [InlineKeyboardButton(messages.SETTINGS_PROXY_CMD_BUTTON_MSG, callback_data="settings__cmd__proxy")],
            [InlineKeyboardButton(messages.SETTINGS_KEYBOARD_CMD_BUTTON_MSG, callback_data="settings__cmd__keyboard")],
            [InlineKeyboardButton(messages.SETTINGS_SEARCH_CMD_BUTTON_MSG, callback_data="settings__cmd__search_menu")],
            [InlineKeyboardButton(messages.SETTINGS_ARGS_CMD_BUTTON_MSG, callback_data="settings__cmd__args")],
            [InlineKeyboardButton(messages.SETTINGS_NSFW_CMD_BUTTON_MSG, callback_data="settings__cmd__nsfw")],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
messages.SETTINGS_MORE_TITLE_MSG,
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
                InlineKeyboardButton(messages.SETTINGS_CLEAN_BUTTON_MSG, callback_data="settings__menu__clean"),
                InlineKeyboardButton(messages.SETTINGS_COOKIES_BUTTON_MSG, callback_data="settings__menu__cookies"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_MEDIA_BUTTON_MSG, callback_data="settings__menu__media"),
                InlineKeyboardButton(messages.SETTINGS_INFO_BUTTON_MSG, callback_data="settings__menu__logs"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_MORE_BUTTON_MSG, callback_data="settings__menu__more"),
                InlineKeyboardButton(messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="settings__menu__close"),
            ]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
                       messages.SETTINGS_TITLE_MSG,
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
    messages = get_messages_instance(user_id)
    # Lazy import to avoid circular dependency
    from URL_PARSERS.url_extractor import url_distractor
    
    user_id = callback_query.from_user.id
    data = callback_query.data.split("__")[2]

    # For commands that are processed only via url_distractor, create a temporary Message
    if data == "clean":
        # Show the cleaning menu instead of direct execution
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(messages.SETTINGS_COOKIES_ONLY_BUTTON_MSG, callback_data="clean_option|cookies"),
                InlineKeyboardButton(messages.SETTINGS_LOGS_BUTTON_MSG, callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_TAGS_BUTTON_MSG, callback_data="clean_option|tags"),
                InlineKeyboardButton(messages.SETTINGS_FORMAT_BUTTON_MSG, callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_SPLIT_BUTTON_MSG, callback_data="clean_option|split"),
                InlineKeyboardButton(messages.SETTINGS_MEDIAINFO_BUTTON_MSG, callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_SUBTITLES_BUTTON_MSG, callback_data="clean_option|subs"),
                InlineKeyboardButton(messages.SETTINGS_KEYBOARD_BUTTON_MSG, callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton(messages.SETTINGS_ALL_FILES_BUTTON_MSG, callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton(messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        try:
            callback_query.edit_message_text(
                messages.SETTINGS_CLEAN_OPTIONS_MSG,
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    if data == "save_as_cookie":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
        ])
        safe_send_message(user_id, messages.SAVE_AS_COOKIE_HINT, reply_parameters=ReplyParameters(message_id=callback_query.message.id),
                          parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)

        try:
            callback_query.answer(messages.SETTINGS_HINT_SENT_MSG)
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
            callback_query.answer(messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
            callback_query.answer(messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
            callback_query.answer(messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
            callback_query.answer(messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return
        callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
        return
    if data == "audio":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.OTHER_AUDIO_HINT_CLOSE_BUTTON_MSG, callback_data="audio_hint|close")]
        ])
        safe_send_message(user_id,
                          messages.AUDIO_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),

                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice=messages.FLOOD_LIMIT_TRY_LATER_MSG)
        try:
            callback_query.answer(messages.SETTINGS_HINT_SENT_MSG)
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
            callback_query.answer(messages.SETTINGS_FLOOD_WAIT_ACTIVE_MSG, show_alert=False)
            return

        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        # If safe_send_message returned None due to FloodWait, notify via callback
        if res is None:
            try:
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
        else:
            try:
                callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass

        return
    if data == "img":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.COMMAND_IMAGE_HELP_CLOSE_BUTTON_MSG, callback_data="img_hint|close")]
        ])
        safe_send_message(
            user_id,
            messages.IMG_HELP_MSG,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice=messages.FLOOD_LIMIT_TRY_LATER_MSG,
            parse_mode=enums.ParseMode.HTML,
        )
        try:
            callback_query.answer(messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass
        return
    if data == "link":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="link_hint|close")]
        ])
        safe_send_message(user_id,
                          messages.LINK_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),
                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice=messages.FLOOD_LIMIT_TRY_LATER_MSG)
        try:
            callback_query.answer(messages.SETTINGS_HINT_SENT_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                    messages.SETTINGS_MOBILE_ACTIVATE_SEARCH_MSG,
                    url=f"tg://msg?text=%40vid%20%E2%80%8B&to=%40{bot_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG,
                    callback_data="search_msg|close"
                )
            ]
        ])
        
        # Send message with search instructions (same as search.py)
        text = messages.SEARCH_MSG
        
        safe_send_message(
            user_id,
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboard,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            _callback_query=callback_query,
            _fallback_notice=messages.FLOOD_LIMIT_TRY_LATER_MSG
        )
        
        try:
            callback_query.answer(messages.SETTINGS_SEARCH_HELPER_OPENED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
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
                callback_query.answer(messages.SETTINGS_FLOOD_LIMIT_MSG, show_alert=False)
            except Exception:
                pass
            return
        try:
            callback_query.answer(messages.SETTINGS_COMMAND_EXECUTED_MSG)
        except Exception:
            pass
        return
    try:
        callback_query.answer(messages.SETTINGS_UNKNOWN_COMMAND_MSG, show_alert=True)
    except Exception:
        pass

@app.on_callback_query(filters.regex(r"^(img_hint|link_hint|search_hint|search_msg)\|"))
def hint_callback(app, callback_query: CallbackQuery):
    messages = get_messages_instance(None)
    """Handle hint callback close buttons"""
    data = callback_query.data.split("|")[-1]
    
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(messages.SETTINGS_HINT_CLOSED_MSG)
        except Exception:
            pass
        return
    
    try:
        callback_query.answer()
    except Exception:
        pass
