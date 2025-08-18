
# Command /Format Handler
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_logger, logger
from HELPERS.filesystem_hlp import create_directory
from urllib.parse import urlparse
import os

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("format") & filters.private)
# @reply_with_keyboard
def set_format(app, message):
    user_id = message.chat.id
    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    send_to_logger(message, "User requested format change.")
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # If the additional text is transmitted, we save it as Custom Format
    if len(message.command) > 1:
        custom_format = message.text.split(" ", 1)[1].strip()
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write(custom_format)
        app.send_message(user_id, f"✅ Format updated to:\n{custom_format}")
        send_to_logger(message, f"Format updated to: {custom_format}")
    else:
        # Main Menu with A Few Popular Options, Plus The Others Button
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Always Ask (menu + buttons)", callback_data="format_option|alwaysask")],
            [InlineKeyboardButton("🎛 Others (144p - 4320p)", callback_data="format_option|others")],
            [InlineKeyboardButton("💻4k (best for PC/Mac Telegram)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱FullHD (best for mobile Telegram)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈Bestvideo+Bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton("🎚 Custom (enter your own)", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        app.send_message(
            user_id,
            "Select a format option or send a custom one using <code>/format &lt;format_string&gt;</code>:",
            reply_markup=main_keyboard
        )
        send_to_logger(message, "Format menu sent.")


# Callbackquery Handler for /Format Menu Selection
@app.on_callback_query(filters.regex(r"^format_option\|"))
# @reply_with_keyboard
def format_option_callback(app, callback_query):
    logger.info(f"[FORMAT] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]

    # If you press the close button
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("✅ Format choice updated.")
        send_to_logger(callback_query.message, "Format selection closed.")
        return

    # If the Custom button is pressed
    if data == "custom":
        # Sending a message with the Close button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚 Close", callback_data="format_custom|close")]
        ])
        app.send_message(
            user_id,
            "To use a custom format, send the command in the following form:\n\n<code>/format bestvideo+bestaudio/best</code>\n\nReplace <code>bestvideo+bestaudio/best</code> with your desired format string.",
            reply_to_message_id=callback_query.message.id,
            reply_markup=keyboard
        )
        callback_query.answer("Hint sent.")
        send_to_logger(callback_query.message, "Custom format hint sent.")
        return

    # If the Others button is pressed - we display the second set of options
    if data == "others":
        full_res_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("144p (256×144)", callback_data="format_option|bv144"),
                InlineKeyboardButton("240p (426×240)", callback_data="format_option|bv240"),
                InlineKeyboardButton("360p (640×360)", callback_data="format_option|bv360")
            ],
            [
                InlineKeyboardButton("480p (854×480)", callback_data="format_option|bv480"),
                InlineKeyboardButton("720p (1280×720)", callback_data="format_option|bv720"),
                InlineKeyboardButton("1080p (1920×1080)", callback_data="format_option|bv1080")
            ],
            [
                InlineKeyboardButton("1440p (2560×1440)", callback_data="format_option|bv1440"),
                InlineKeyboardButton("2160p (3840×2160)", callback_data="format_option|bv2160"),
                InlineKeyboardButton("4320p (7680×4320)", callback_data="format_option|bv4320")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back"), InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        callback_query.edit_message_text("Select your desired resolution:", reply_markup=full_res_keyboard)
        callback_query.answer()
        send_to_logger(callback_query.message, "Format resolution menu sent.")
        return

    # If the Back button is pressed - we return to the main menu
    if data == "back":
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Always Ask (menu + buttons)", callback_data="format_option|alwaysask")],
            [InlineKeyboardButton("🎛 Others (144p - 4320p)", callback_data="format_option|others")],
            [InlineKeyboardButton("💻4k (best for PC/Mac Telegram)", callback_data="format_option|bv2160")],
            [InlineKeyboardButton("📱FullHD (best for mobile Telegram)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("📈Bestvideo+Bestaudio (MAX quality)", callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton("🎚 Custom (enter your own)", callback_data="format_option|custom")],
            [InlineKeyboardButton("🔚 close", callback_data="format_option|close")]
        ])
        callback_query.edit_message_text("Select a format option or send a custom one using <code>/format &lt;format_string&gt;</code>:",
                                         reply_markup=main_keyboard)
        callback_query.answer()
        send_to_logger(callback_query.message, "Returned to main format menu.")
        return

    # Mapping for the Rest of the Options
    if data == "bv144":
        chosen_format = "bv*[vcodec*=avc1][height<=144]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv240":
        chosen_format = "bv*[vcodec*=avc1][height<=240]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv360":
        chosen_format = "bv*[vcodec*=avc1][height<=360]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv480":
        chosen_format = "bv*[vcodec*=avc1][height<=480]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv720":
        chosen_format = "bv*[vcodec*=avc1][height<=720]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv1080":
        chosen_format = "bv*[vcodec*=avc1][height<=1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv1440":
        chosen_format = "bv*[vcodec*=avc1][height<=1440]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv2160":
        chosen_format = "bv*[vcodec*=avc1][height<=2160]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bv4320":
        chosen_format = "bv*[vcodec*=avc1][height<=4320]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/best"
    elif data == "bestvideo":
        chosen_format = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bestvideo+bestaudio/best"
    elif data == "best":
        chosen_format = "best"
    else:
        chosen_format = data

    # Save The Selected Format
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
        f.write(chosen_format)
    callback_query.edit_message_text(f"✅ Format updated to:\n{chosen_format}")
    callback_query.answer("✅ Format saved.")
    send_to_logger(callback_query.message, f"Format updated to: {chosen_format}")

    if data == "alwaysask":
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write("ALWAYS_ASK")
        callback_query.edit_message_text(
            "✅ Format set to: Always Ask. Now you will be prompted for quality each time you send a URL.")
        send_to_logger(callback_query.message, "Format set to ALWAYS_ASK.")
        return

# Callback processor to close the message
@app.on_callback_query(filters.regex(r"^format_custom\|"))
def format_custom_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Custom format menu closed.")
        send_to_logger(callback_query.message, "Custom format menu closed")
        return
# ####################################################################################
