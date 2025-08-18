from HELPERS.app_instance import get_app
from pyrogram import filters
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from CONFIG.config import Config
from HELPERS.logger import send_to_logger

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("tags") & filters.private)
# @reply_with_keyboard
def tags_command(app, message):
    user_id = message.chat.id
    user_dir = os.path.join("users", str(user_id))
    tags_file = os.path.join(user_dir, "tags.txt")
    if not os.path.exists(tags_file):
        reply_text = "You have no tags yet."
        app.send_message(user_id, reply_text, reply_to_message_id=message.id)
        send_to_logger(message, reply_text)
        return
    with open(tags_file, "r", encoding="utf-8") as f:
        tags = [line.strip() for line in f if line.strip()]
    if not tags:
        reply_text = "You have no tags yet."
        app.send_message(user_id, reply_text, reply_to_message_id=message.id)
        send_to_logger(message, reply_text)
        return
    # We form posts by 4096 characters
    msg = ''
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Close", callback_data="tags_close|close")]
    ])
    for tag in tags:
        if len(msg) + len(tag) + 1 > 4096:
            app.send_message(user_id, msg, reply_to_message_id=message.id, reply_markup=keyboard)
            send_to_logger(message, msg)
            msg = ''
        msg += tag + '\n'
    if msg:
        app.send_message(user_id, msg, reply_to_message_id=message.id, reply_markup=keyboard)
        send_to_logger(message, msg)

@app.on_callback_query(filters.regex(r"^tags_close\|"))
def tags_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Tags message closed.")
        send_to_logger(callback_query.message, "Tags message closed.")
        return

    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Tags message closed.")
        send_to_logger(callback_query.message, "Tags message closed.")
        return