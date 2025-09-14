# /NSFW Command
import os
from pyrogram import filters, enums
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.limitter import is_user_in_channel

# Get app instance for decorators
app = get_app()

# Like mediainfo: handle private here; groups are registered/wrapped in magic.py
@app.on_message(filters.command("nsfw"))
def nsfw_command(app, message):
    chat_id = message.chat.id
    chat_type = getattr(message.chat, "type", None)
    # Store setting per-chat: in groups/channels use chat_id (negative), in private use user id (== chat_id)
    user_id = getattr(message.from_user, "id", None) or chat_id
    storage_id = chat_id
    logger.info(f"[NSFW] User {user_id} requested nsfw command")
    logger.info(f"[NSFW] User {user_id} is admin: {int(user_id) in Config.ADMIN}")
    logger.info(f"[NSFW] User {user_id} is in channel: {is_user_in_channel(app, message)}")
    
    # In private chats: require subscription (like mediainfo). In allowed groups: bypass (wrapper in magic.py filters groups).
    if chat_type == enums.ChatType.PRIVATE:
        if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
            logger.info(f"[NSFW] User {user_id} access denied - not admin and not in channel")
            try:
                safe_send_message(chat_id, Config.TO_USE_MSG, parse_mode=enums.ParseMode.HTML, message=message)
            except Exception:
                pass
            return
    
    logger.info(f"[NSFW] User {user_id} access granted")
    user_dir = os.path.join("users", str(storage_id))
    create_directory(user_dir)
    
    # Fast toggle via args: /nsfw on|off
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            arg = parts[1].lower()
            nsfw_file = os.path.join(user_dir, "nsfw_blur.txt")
            if arg in ("on", "off"):
                with open(nsfw_file, "w", encoding="utf-8") as f:
                    f.write("ON" if arg == "on" else "OFF")
                
                if arg == "on":
                    safe_send_message(chat_id, Config.NSFW_ON_MSG, parse_mode=enums.ParseMode.HTML, message=message)
                else:
                    safe_send_message(chat_id, Config.NSFW_OFF_MSG, parse_mode=enums.ParseMode.HTML, message=message)
                
                send_to_logger(message, f"NSFW blur set via command: {arg}")
                return
            else:
                safe_send_message(chat_id, Config.NSFW_INVALID_MSG, parse_mode=enums.ParseMode.HTML, message=message)
                return
    except Exception as e:
        logger.error(f"Error processing nsfw command: {e}")
        pass
    
    # Show menu if no args provided
    # Check current setting to show proper status
    current_setting = is_nsfw_blur_enabled(storage_id)
    on_text = "✅ ON (No Blur)" if not current_setting else "☑️ ON (No Blur)"
    off_text = "✅ OFF (Blur)" if current_setting else "☑️ OFF (Blur)"
    
    buttons = [
        [InlineKeyboardButton(on_text, callback_data="nsfw_option|on"), InlineKeyboardButton(off_text, callback_data="nsfw_option|off")],
        [InlineKeyboardButton("🔚Close", callback_data="nsfw_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    
    status_text = "currently blurred" if current_setting else "currently not blurred"
    safe_send_message(
        chat_id,
        f"🔞 <b>NSFW Blur Settings</b>\n\nNSFW content is <b>{status_text}</b>.\n\nChoose whether to blur NSFW content:",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
        message=message
    )
    send_to_logger(message, "User opened /nsfw menu.")


@app.on_callback_query(filters.regex(r"^nsfw_option\|"))
def nsfw_option_callback(app, callback_query):
    logger.info(f"[NSFW] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    chat = getattr(callback_query, "message", None).chat if getattr(callback_query, "message", None) else None
    chat_id = getattr(chat, "id", None) if chat else user_id
    # Store per-chat: in groups use chat_id (negative), in private chat_id == user id
    storage_id = chat_id
    user_dir = os.path.join("users", str(storage_id))
    create_directory(user_dir)
    nsfw_file = os.path.join(user_dir, "nsfw_blur.txt")
    
    if callback_query.data == "nsfw_option|close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer("Menu closed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, "NSFW: closed.")
        return
    
    if data == "on":
        with open(nsfw_file, "w", encoding="utf-8") as f:
            f.write("ON")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, Config.NSFW_ON_MSG, parse_mode=enums.ParseMode.HTML)
        send_to_logger(callback_query.message, "NSFW blur disabled.")
        try:
            callback_query.answer("NSFW blur disabled.")
        except Exception:
            pass
        return
    
    if data == "off":
        with open(nsfw_file, "w", encoding="utf-8") as f:
            f.write("OFF")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, Config.NSFW_OFF_MSG, parse_mode=enums.ParseMode.HTML)
        send_to_logger(callback_query.message, "NSFW blur enabled.")
        try:
            callback_query.answer("NSFW blur enabled.")
        except Exception:
            pass
        return


def is_nsfw_blur_enabled(user_id):
    """
    Check if NSFW blur is enabled for user.
    Returns True if blur should be applied (default behavior).
    Returns False if blur should be disabled.
    """
    user_dir = os.path.join("users", str(user_id))
    nsfw_file = os.path.join(user_dir, "nsfw_blur.txt")
    if not os.path.exists(nsfw_file):
        return True  # Default: blur enabled
    
    try:
        with open(nsfw_file, "r", encoding="utf-8") as f:
            content = f.read().strip().upper()
            return content != "ON"  # If file contains "ON", blur is disabled
    except Exception:
        return True  # Default: blur enabled on error


def should_apply_spoiler(user_id, is_nsfw, is_private_chat):
    """
    Determine if spoiler should be applied based on user settings and context.
    
    Args:
        user_id: User ID
        is_nsfw: Whether content is NSFW
        is_private_chat: Whether it's a private chat
    
    Returns:
        bool: True if spoiler should be applied
    """
    if not is_nsfw:
        return False
    
    # In groups, never apply spoiler for NSFW content
    if not is_private_chat:
        return False
    
    # In private chats, check user's blur setting
    return is_nsfw_blur_enabled(user_id)
