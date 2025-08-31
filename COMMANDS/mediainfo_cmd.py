# /Mediainfo Command
import os
import subprocess
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger, send_to_all
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text

# Get app instance for decorators
app = get_app()

def is_user_in_channel(app, message):
    """Check if user is member of the subscription channel"""
    try:
        user_id = message.chat.id
        member = app.get_chat_member(Config.SUBSCRIBE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

@app.on_message(filters.command("mediainfo") & filters.private)
# @reply_with_keyboard
def mediainfo_command(app, message):
    user_id = message.chat.id
    logger.info(f"[MEDIAINFO] User {user_id} requested mediainfo command")
    logger.info(f"[MEDIAINFO] User {user_id} is admin: {int(user_id) in Config.ADMIN}")
    logger.info(f"[MEDIAINFO] User {user_id} is in channel: {is_user_in_channel(app, message)}")
    
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        logger.info(f"[MEDIAINFO] User {user_id} access denied - not admin and not in channel")
        return
    
    logger.info(f"[MEDIAINFO] User {user_id} access granted")
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
                safe_send_message(user_id, f"✅ MediaInfo {'enabled' if arg=='on' else 'disabled'}.")
                send_to_logger(message, f"MediaInfo set via command: {arg}")
                return
    except Exception:
        pass
    buttons = [
        [InlineKeyboardButton("✅ ON", callback_data="mediainfo_option|on"), InlineKeyboardButton("❌ OFF", callback_data="mediainfo_option|off")],
        [InlineKeyboardButton("🔚 Close", callback_data="mediainfo_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    safe_send_message(
        user_id,
        "Enable or disable sending MediaInfo for downloaded files?",
        reply_markup=keyboard
    )
    send_to_logger(message, "User opened /mediainfo menu.")


@app.on_callback_query(filters.regex(r"^mediainfo_option\|"))
# @reply_with_keyboard
def mediainfo_option_callback(app, callback_query):
    logger.info(f"[MEDIAINFO] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
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
            callback_query.answer("Menu closed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, "MediaInfo: closed.")
        return
    if data == "on":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("ON")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "✅ MediaInfo enabled. After downloading, file info will be sent.")
        send_to_logger(callback_query.message, "MediaInfo enabled.")
        try:
            callback_query.answer("MediaInfo enabled.")
        except Exception:
            pass
        return
    if data == "off":
        with open(mediainfo_file, "w", encoding="utf-8") as f:
            f.write("OFF")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "❌ MediaInfo disabled.")
        send_to_logger(callback_query.message, "MediaInfo disabled.")
        try:
            callback_query.answer("MediaInfo disabled.")
        except Exception:
            pass
        return


def is_mediainfo_enabled(user_id):
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

            app.send_document(user_id, mediainfo_path, caption="<blockquote>📊 MediaInfo</blockquote>",
                              reply_parameters=ReplyParameters(message_id=msg_id))
            app.send_document(Config.LOGS_ID, mediainfo_path,
                              caption=f"<blockquote>📊 MediaInfo</blockquote> for user {user_id}")

            if os.path.exists(mediainfo_path):
                os.remove(mediainfo_path)

        except Exception as e:
            logger.error(f"Error MediaInfo: {e}")
            send_to_all(message, f"❌ Error sending MediaInfo: {e}")
