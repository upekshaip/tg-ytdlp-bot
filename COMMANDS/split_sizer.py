from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.limitter import humanbytes, is_user_in_channel
import re

def parse_size_argument(arg):
    """
    Parse size argument and return size in bytes
    
    Args:
        arg (str): Size argument (e.g., "250mb", "1.5gb", "2GB")
        
    Returns:
        int: Size in bytes or None if invalid
    """
    if not arg:
        return None
    
    # Remove spaces and convert to lowercase
    arg = arg.lower().replace(" ", "")
    
    # Match patterns like "250mb", "1.5gb", "2GB"
    match = re.match(r'^(\d+(?:\.\d+)?)(mb|gb)$', arg)
    if not match:
        return None
    
    number = float(match.group(1))
    unit = match.group(2)
    
    if unit == "mb":
        return int(number * 1024 * 1024)
    elif unit == "gb":
        return int(number * 1024 * 1024 * 1024)
    
    return None

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("split") & filters.private)
# @reply_with_keyboard
def split_command(app, message):
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
            
            safe_send_message(user_id, f"✅ Split part size set to: {humanbytes(size)}")
            send_to_logger(message, f"Split size set to {size} bytes via argument.")
            return
        else:
            safe_send_message(user_id, 
                "❌ **Invalid size!**\n\n"
                "Valid formats:\n"
                "• `250mb` or `250MB`\n"
                "• `500mb` or `500MB`\n"
                "• `1gb` or `1GB`\n"
                "• `1.5gb` or `1.5GB`\n"
                "• `2gb` or `2GB`\n\n"
                "Example: `/split 500mb`"
            )
            return
    
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    # 2-3 row buttons
    sizes = [
        ("250 MB", 250 * 1024 * 1024),
        ("500 MB", 500 * 1024 * 1024),
        ("1 GB", 1024 * 1024 * 1024),
        ("1.5 GB", 1536 * 1024 * 1024),
        ("2 GB (default)", 1950 * 1024 * 1024)
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
    buttons.append([InlineKeyboardButton("🔚Close", callback_data="split_size|close")])
    keyboard = InlineKeyboardMarkup(buttons)
    safe_send_message(user_id, "Choose max part size for video splitting:\n\nOr use: `/split 250mb`, `/split 1gb`, etc.", reply_markup=keyboard)
    send_to_logger(message, "User opened /split menu.")

@app.on_callback_query(filters.regex(r"^split_size\|"))
# @reply_with_keyboard
def split_size_callback(app, callback_query):
    logger.info(f"[SPLIT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer("Menu closed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, "Split selection closed.")
        return
    try:
        size = int(data)
    except Exception:
        callback_query.answer("Invalid size.")
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    split_file = os.path.join(user_dir, "split.txt")
    with open(split_file, "w", encoding="utf-8") as f:
        f.write(str(size))
    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"✅ Split part size set to: {humanbytes(size)}")
    send_to_logger(callback_query.message, f"Split size set to {size} bytes.")

# --- Function for reading split.txt ---
def get_user_split_size(user_id):
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

