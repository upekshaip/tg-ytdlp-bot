# ===================== /settings =====================
from pyrogram import filters
from CONFIG.config import Config
from CONFIG.messages import Messages
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
        [
            InlineKeyboardButton(Messages.SETTINGS_DEV_GITHUB_BUTTON_MSG, url="https://github.com/upekshaip/tg-ytdlp-bot"),
            InlineKeyboardButton(Messages.SETTINGS_CONTR_GITHUB_BUTTON_MSG, url="https://github.com/chelaxian/tg-ytdlp-bot")
        ],
        [InlineKeyboardButton(Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="help_msg|close")]
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
            InlineKeyboardButton(Messages.SETTINGS_CLEAN_BUTTON_MSG, callback_data="settings__menu__clean"),
            InlineKeyboardButton(Messages.SETTINGS_COOKIES_BUTTON_MSG, callback_data="settings__menu__cookies"),
        ],
        [
            InlineKeyboardButton(Messages.SETTINGS_MEDIA_BUTTON_MSG, callback_data="settings__menu__media"),
            InlineKeyboardButton(Messages.SETTINGS_INFO_BUTTON_MSG, callback_data="settings__menu__logs"),
        ],
        [
            InlineKeyboardButton(Messages.SETTINGS_MORE_BUTTON_MSG, callback_data="settings__menu__more"),
            InlineKeyboardButton(Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="settings__menu__close"),
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
                InlineKeyboardButton(Messages.SETTINGS_COOKIES_ONLY_BUTTON_MSG, callback_data="clean_option|cookies"),
                InlineKeyboardButton(Messages.SETTINGS_LOGS_BUTTON_MSG, callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_TAGS_BUTTON_MSG, callback_data="clean_option|tags"),
                InlineKeyboardButton(Messages.SETTINGS_FORMAT_BUTTON_MSG, callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_SPLIT_BUTTON_MSG, callback_data="clean_option|split"),
                InlineKeyboardButton(Messages.SETTINGS_MEDIAINFO_BUTTON_MSG, callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_SUBTITLES_BUTTON_MSG, callback_data="clean_option|subs"),
                InlineKeyboardButton(Messages.SETTINGS_KEYBOARD_BUTTON_MSG, callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_ARGS_BUTTON_MSG, callback_data="clean_option|args"),
                InlineKeyboardButton(Messages.SETTINGS_NSFW_BUTTON_MSG, callback_data="clean_option|nsfw"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_PROXY_BUTTON_MSG, callback_data="clean_option|proxy"),
                InlineKeyboardButton(Messages.SETTINGS_FLOOD_WAIT_BUTTON_MSG, callback_data="clean_option|flood_wait"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_ALL_FILES_BUTTON_MSG, callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
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
            [InlineKeyboardButton(Messages.SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(Messages.SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(Messages.SETTINGS_CHECK_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(Messages.SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
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
            [InlineKeyboardButton(Messages.SETTINGS_FORMAT_CMD_BUTTON_MSG, callback_data="settings__cmd__format")],
            [InlineKeyboardButton(Messages.SETTINGS_MEDIAINFO_CMD_BUTTON_MSG, callback_data="settings__cmd__mediainfo")],
            [InlineKeyboardButton(Messages.SETTINGS_SPLIT_CMD_BUTTON_MSG, callback_data="settings__cmd__split")],
            [InlineKeyboardButton(Messages.SETTINGS_AUDIO_CMD_BUTTON_MSG, callback_data="settings__cmd__audio")],
            [InlineKeyboardButton(Messages.SETTINGS_SUBS_CMD_BUTTON_MSG, callback_data="settings__cmd__subs")],
            [InlineKeyboardButton(Messages.SETTINGS_PLAYLIST_CMD_BUTTON_MSG, callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton(Messages.SETTINGS_IMG_CMD_BUTTON_MSG, callback_data="settings__cmd__img")],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
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
            [InlineKeyboardButton(Messages.SETTINGS_TAGS_CMD_BUTTON_MSG, callback_data="settings__cmd__tags")],
            [InlineKeyboardButton(Messages.SETTINGS_HELP_CMD_BUTTON_MSG, callback_data="settings__cmd__help")],
            [InlineKeyboardButton(Messages.SETTINGS_USAGE_CMD_BUTTON_MSG, callback_data="settings__cmd__usage")],
            [InlineKeyboardButton(Messages.SETTINGS_PLAYLIST_HELP_CMD_BUTTON_MSG, callback_data="settings__cmd__playlist")],
            [InlineKeyboardButton(Messages.SETTINGS_ADD_BOT_CMD_BUTTON_MSG, callback_data="settings__cmd__add_bot_to_group")],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
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
            [InlineKeyboardButton(Messages.SETTINGS_LINK_CMD_BUTTON_MSG, callback_data="settings__cmd__link")],
            [InlineKeyboardButton(Messages.SETTINGS_PROXY_CMD_BUTTON_MSG, callback_data="settings__cmd__proxy")],
            [InlineKeyboardButton(Messages.SETTINGS_KEYBOARD_CMD_BUTTON_MSG, callback_data="settings__cmd__keyboard")],
            [InlineKeyboardButton(Messages.SETTINGS_SEARCH_CMD_BUTTON_MSG, callback_data="settings__cmd__search_menu")],
            [InlineKeyboardButton(Messages.SETTINGS_ARGS_CMD_BUTTON_MSG, callback_data="settings__cmd__args")],
            [InlineKeyboardButton(Messages.SETTINGS_NSFW_CMD_BUTTON_MSG, callback_data="settings__cmd__nsfw")],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
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
                InlineKeyboardButton(Messages.SETTINGS_CLEAN_BUTTON_MSG, callback_data="settings__menu__clean"),
                InlineKeyboardButton(Messages.SETTINGS_COOKIES_BUTTON_MSG, callback_data="settings__menu__cookies"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_MEDIA_BUTTON_MSG, callback_data="settings__menu__media"),
                InlineKeyboardButton(Messages.SETTINGS_INFO_BUTTON_MSG, callback_data="settings__menu__logs"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_MORE_BUTTON_MSG, callback_data="settings__menu__more"),
                InlineKeyboardButton(Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="settings__menu__close"),
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
                InlineKeyboardButton(Messages.SETTINGS_COOKIES_ONLY_BUTTON_MSG, callback_data="clean_option|cookies"),
                InlineKeyboardButton(Messages.SETTINGS_LOGS_BUTTON_MSG, callback_data="clean_option|logs"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_TAGS_BUTTON_MSG, callback_data="clean_option|tags"),
                InlineKeyboardButton(Messages.SETTINGS_FORMAT_BUTTON_MSG, callback_data="clean_option|format"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_SPLIT_BUTTON_MSG, callback_data="clean_option|split"),
                InlineKeyboardButton(Messages.SETTINGS_MEDIAINFO_BUTTON_MSG, callback_data="clean_option|mediainfo"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_SUBTITLES_BUTTON_MSG, callback_data="clean_option|subs"),
                InlineKeyboardButton(Messages.SETTINGS_KEYBOARD_BUTTON_MSG, callback_data="clean_option|keyboard"),
            ],
            [
                InlineKeyboardButton(Messages.SETTINGS_ALL_FILES_BUTTON_MSG, callback_data="clean_option|all"),
            ],
            [InlineKeyboardButton(Messages.SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
        try:
            callback_query.edit_message_text(
                Messages.SETTINGS_CLEAN_OPTIONS_MSG,
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
            [InlineKeyboardButton(Messages.URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG, callback_data="save_as_cookie_hint|close")]
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
            [InlineKeyboardButton(Messages.OTHER_AUDIO_HINT_CLOSE_BUTTON_MSG, callback_data="audio_hint|close")]
        ])
        safe_send_message(user_id,
                          Messages.AUDIO_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),

                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice=Messages.FLOOD_LIMIT_TRY_LATER_MSG)
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
            [InlineKeyboardButton(Messages.COMMAND_IMAGE_HELP_CLOSE_BUTTON_MSG, callback_data="img_hint|close")]
        ])
        safe_send_message(
            user_id,
            Messages.IMG_HELP_MSG,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            reply_markup=keyboard,
            _callback_query=callback_query,
            _fallback_notice=Messages.FLOOD_LIMIT_TRY_LATER_MSG,
            parse_mode=enums.ParseMode.HTML,
        )
        try:
            callback_query.answer(Messages.SETTINGS_HINT_SENT_MSG)
        except Exception:
            pass
        return
    if data == "link":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="link_hint|close")]
        ])
        safe_send_message(user_id,
                          Messages.LINK_HINT_MSG,
                          reply_parameters=ReplyParameters(message_id=callback_query.message.id),
                          reply_markup=keyboard,
                          _callback_query=callback_query,
                          _fallback_notice=Messages.FLOOD_LIMIT_TRY_LATER_MSG)
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
                    Messages.SETTINGS_MOBILE_ACTIVATE_SEARCH_MSG,
                    url=f"tg://msg?text=%40vid%20%E2%80%8B&to=%40{bot_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    Messages.URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG,
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
            _fallback_notice=Messages.FLOOD_LIMIT_TRY_LATER_MSG
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
