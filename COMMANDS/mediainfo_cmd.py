# /Mediainfo Command
import os
import subprocess
from pyrogram import filters
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger, send_to_all, send_error_to_user
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.decorators import background_handler
from HELPERS.limitter import is_user_in_channel

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("mediainfo") & filters.private)
# @reply_with_keyboard
@background_handler(label="mediainfo_command")
def mediainfo_command(app, message):
    messages = safe_get_messages(message.chat.id)
    user_id = message.chat.id
    logger.info(safe_get_messages(user_id).MEDIAINFO_USER_REQUESTED_MSG.format(user_id=user_id))
    logger.info(safe_get_messages(user_id).MEDIAINFO_USER_IS_ADMIN_MSG.format(user_id=user_id, is_admin=int(user_id) in Config.ADMIN))
    
    is_in_channel = is_user_in_channel(app, message)
    logger.info(safe_get_messages(user_id).MEDIAINFO_USER_IS_IN_CHANNEL_MSG.format(user_id=user_id, is_in_channel=is_in_channel))
    
    if int(user_id) not in Config.ADMIN and not is_in_channel:
        logger.info(safe_get_messages(user_id).MEDIAINFO_ACCESS_DENIED_MSG.format(user_id=user_id))
        return
    
    logger.info(safe_get_messages(user_id).MEDIAINFO_ACCESS_GRANTED_MSG.format(user_id=user_id))
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    # Fast toggle via args: /mediainfo on|off
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            arg = parts[1].lower()
            mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
            if arg in ("on", "off"):
                with open(mediainfo_file, "w", encoding="utf-8") as f:
                    f.write("ON" if arg == "on" else "OFF")
                safe_send_message(user_id, safe_get_messages(user_id).MEDIAINFO_ENABLED_MSG.format(status='enabled' if arg=='on' else 'disabled'), message=message)
                send_to_logger(message, safe_get_messages(user_id).MEDIAINFO_SET_COMMAND_LOG_MSG.format(arg=arg))
                return
    except Exception:
        pass
    buttons = [
        [InlineKeyboardButton(safe_get_messages(user_id).MEDIAINFO_ON_BUTTON_MSG, callback_data="mediainfo_option|on"), InlineKeyboardButton(safe_get_messages(user_id).MEDIAINFO_OFF_BUTTON_MSG, callback_data="mediainfo_option|off")],
        [InlineKeyboardButton(safe_get_messages(user_id).MEDIAINFO_CLOSE_BUTTON_MSG, callback_data="mediainfo_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    safe_send_message(
        user_id,
safe_get_messages(user_id).MEDIAINFO_MENU_TITLE_MSG,
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, safe_get_messages(user_id).MEDIAINFO_MENU_OPENED_LOG_MSG)


@app.on_callback_query(filters.regex(r"^mediainfo_option\|"))
# @reply_with_keyboard
def mediainfo_option_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    logger.info(safe_get_messages(user_id).MEDIAINFO_CALLBACK_MSG.format(callback_data=callback_query.data))
    data = callback_query.data.split("|")[1]
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
    if callback_query.data == "mediainfo_option|close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(safe_get_messages(user_id).MEDIAINFO_MENU_CLOSED_MSG)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).MEDIAINFO_MENU_CLOSED_LOG_MSG)
        return
    if data == "on":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("ON")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).MEDIAINFO_ENABLED_CONFIRM_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).MEDIAINFO_ENABLED_LOG_MSG)
        try:
            callback_query.answer(safe_get_messages(user_id).MEDIAINFO_ENABLED_CALLBACK_MSG)
        except Exception:
            pass
        return
    if data == "off":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("OFF")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).MEDIAINFO_DISABLED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).MEDIAINFO_DISABLED_LOG_MSG)
        try:
            callback_query.answer(safe_get_messages(user_id).MEDIAINFO_DISABLED_CALLBACK_MSG)
        except Exception:
            pass
        return


def is_mediainfo_enabled(user_id):
    messages = safe_get_messages(user_id)
    user_dir = os.path.join("users", str(user_id))
    mediainfo_file = os.path.join(user_dir, "mediainfo.txt")
    if not os.path.exists(mediainfo_file):
        return False
    try:
        with open(mediainfo_file, "r", encoding="utf-8") as f:
            return f.read().strip().upper() == "ON"
    except Exception:
        return False


def get_mediainfo_cli(file_path):
    try:
        result = subprocess.run(
            ["mediainfo", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        logger.error(f"mediainfo CLI error: {e}")
        return "MediaInfo CLI error: " + str(e)


def send_mediainfo_if_enabled(user_id, file_path, message):
    messages = safe_get_messages(user_id)
    if is_mediainfo_enabled(user_id):
        try:
            # Extract msg_id safely
            msg_id = message.id if hasattr(message, "id") else message.get("message_id") or message.get("id")

            mediainfo_text = get_mediainfo_cli(file_path)
            # Remove any absolute paths from mediainfo output for security
            mediainfo_text = mediainfo_text.replace(os.path.abspath("users"), "users")
            mediainfo_path = os.path.splitext(file_path)[0] + "_mediainfo.txt"

            with open(mediainfo_path, "w", encoding="utf-8") as f:
                f.write(mediainfo_text)

            app.send_document(user_id, mediainfo_path, caption=safe_get_messages(user_id).MEDIAINFO_DOCUMENT_CAPTION_MSG,
                              reply_parameters=ReplyParameters(message_id=msg_id))
            # MediaInfo files are no longer sent to log channel to avoid polluting video cache
            # from HELPERS.logger import get_log_channel
            # app.send_document(get_log_channel("video"), mediainfo_path,
            #                   caption=f"<blockquote>📊 MediaInfo</blockquote> for user {user_id}")

            if os.path.exists(mediainfo_path):
                os.remove(mediainfo_path)

        except Exception as e:
            logger.error(f"Error MediaInfo: {e}")
            send_error_to_user(message, safe_get_messages(user_id).MEDIAINFO_ERROR_SENDING_MSG.format(error=e))
