from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.decorators import background_handler
from HELPERS.limitter import humanbytes, is_user_in_channel
from CONFIG.messages import Messages, safe_get_messages
import re

def parse_size_argument(arg):
    """
    Parse size argument and return size in bytes
    
    Args:
        arg (str): Size argument (e.g., "250mb", "1.5gb", "2GB", "100mb", "2000mb")
        
    Returns:
        int: Size in bytes or None if invalid
    """
    if not arg:
        return None
    
    # Remove spaces and convert to lowercase
    arg = arg.lower().replace(" ", "")
    
    # Match patterns like "250mb", "1.5gb", "2GB", "100mb", "2000mb"
    match = re.match(r'^(\d+(?:\.\d+)?)(mb|gb)$', arg)
    if not match:
        return None
    
    number = float(match.group(1))
    unit = match.group(2)
    
    # Convert to bytes
    if unit.lower() == "mb":
        size_bytes = int(number * 1024 * 1024)
    elif unit.lower() == "gb":
        size_bytes = int(number * 1024 * 1024 * 1024)
    else:
        return None
    
    # Check limits: 100MB to 2GB
    min_size = 100 * 1024 * 1024  # 100MB
    max_size = 2 * 1024 * 1024 * 1024  # 2GB
    
    if size_bytes and size_bytes < min_size:
        return None  # Too small
    elif size_bytes and size_bytes > max_size:
        return None  # Too large
    
    return size_bytes

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("split") & filters.private)
# @reply_with_keyboard
@background_handler(label="split_command")
def split_command(app, message):
    messages = safe_get_messages(message.chat.id)
    user_id = message.chat.id
    # Subscription check for non-admines
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    
    # Check if arguments are provided
    if len(message.command) > 1:
        arg = message.command[1].lower()
        size = parse_size_argument(arg)
        if size:
            # Apply size directly
            user_dir = os.path.join("users", str(user_id))
            create_directory(user_dir)
            split_file = os.path.join(user_dir, "split.txt")
            with open(split_file, "w", encoding="utf-8") as f:
                f.write(str(size))
            
            safe_send_message(user_id, safe_get_messages(user_id).SPLIT_SIZE_SET_MSG.format(size=humanbytes(size)), message=message)
            send_to_logger(message, safe_get_messages(user_id).SPLIT_SIZE_SET_ARGUMENT_LOG_MSG.format(size=size))
            return
        else:
            safe_send_message(user_id, safe_get_messages(user_id).SPLIT_INVALID_SIZE_MSG, message=message)
            return
    
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    # 2-3 row buttons with more presets
    sizes = [
        ("100 MB", 100 * 1024 * 1024),
        ("250 MB", 250 * 1024 * 1024),
        ("500 MB", 500 * 1024 * 1024),
        ("750 MB", 750 * 1024 * 1024),
        ("1 GB", 1024 * 1024 * 1024),
        ("1.5 GB", 1536 * 1024 * 1024),
        ("2 GB (max)", 2 * 1024 * 1024 * 1024)
    ]
    buttons = []
    # Pass the buttons in 2-3 rows
    for i in range(0, len(sizes), 2):
        row = []
        for j in range(2):
            if i + j < len(sizes):
                text, size = sizes[i + j]
                row.append(InlineKeyboardButton(text, callback_data=f"split_size|{size}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(safe_get_messages(user_id).SPLIT_CLOSE_BUTTON_MSG, callback_data="split_size|close")])
    keyboard = InlineKeyboardMarkup(buttons)
    safe_send_message(user_id, 
safe_get_messages(user_id).SPLIT_MENU_TITLE_MSG, 
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, safe_get_messages(user_id).SPLIT_MENU_OPENED_LOG_MSG)

@app.on_callback_query(filters.regex(r"^split_size\|"))
# @reply_with_keyboard
def split_size_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    logger.info(f"[SPLIT] callback: {callback_query.data}")
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            # Fallback: clear inline keyboard safely (works in topics)
            try:
                from HELPERS.safe_messeger import safe_edit_reply_markup
                safe_edit_reply_markup(callback_query.message.chat.id, callback_query.message.id, reply_markup=None, _callback_query=callback_query)
            except Exception:
                try:
                    callback_query.edit_message_reply_markup(reply_markup=None)
                except Exception:
                    pass
        try:
            callback_query.answer(safe_get_messages(user_id).SPLIT_MENU_CLOSED_MSG)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).SPLIT_SELECTION_CLOSED_LOG_MSG)
        return
    try:
        size = int(data)
    except Exception:
        callback_query.answer(safe_get_messages(user_id).SPLIT_INVALID_SIZE_CALLBACK_MSG)
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    split_file = os.path.join(user_dir, "split.txt")
    with open(split_file, "w", encoding="utf-8") as f:
        f.write(str(size))
    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).SPLIT_SIZE_SET_MSG.format(size=humanbytes(size)))
    send_to_logger(callback_query.message, safe_get_messages(user_id).SPLIT_SIZE_SET_CALLBACK_LOG_MSG.format(size=size))

# --- Function for reading split.txt ---
def get_user_split_size(user_id):
    messages = safe_get_messages(user_id)
    user_dir = os.path.join("users", str(user_id))
    split_file = os.path.join(user_dir, "split.txt")
    if os.path.exists(split_file):
        try:
            with open(split_file, "r", encoding="utf-8") as f:
                size = int(f.read().strip())
                return size
        except Exception:
            pass
    return 1950 * 1024 * 1024  # default 1.95GB

