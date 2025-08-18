from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger
from HELPERS.limitter import humanbytes

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("split") & filters.private)
# @reply_with_keyboard
def split_command(app, message):
    user_id = message.chat.id
    # Subscription check for non-admines
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
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
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="split_size|close")])
    keyboard = InlineKeyboardMarkup(buttons)
    app.send_message(user_id, "Choose max part size for video splitting:", reply_markup=keyboard)
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
        callback_query.answer("Menu closed.")
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
    callback_query.edit_message_text(f"✅ Split part size set to: {humanbytes(size)}")
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

