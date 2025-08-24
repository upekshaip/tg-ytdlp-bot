
# Command /Format Handler
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_logger, logger
from HELPERS.filesystem_hlp import create_directory
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from urllib.parse import urlparse
import os
import json

# Session-scoped overrides (not persisted)
_SESSION_MKV_OVERRIDE = {}

# Per-user format preferences (persisted in users/<id>/format_prefs.json)
def _prefs_path(user_id):
    return os.path.join("users", str(user_id), "format_prefs.json")

def _default_prefs():
    # codec: avc1 | av01 | vp9
    # mkv: True -> remux to mkv container, False -> default to mp4
    return {"codec": "avc1", "mkv": False}

def load_user_prefs(user_id):
    try:
        path = _prefs_path(user_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Backward/forward compatibility
                if not isinstance(data, dict):
                    return _default_prefs()
                data.setdefault("codec", "avc1")
                # Backward compatibility: migrate from old 'webm' to new 'mkv' (default OFF)
                data.setdefault("mkv", False)
                return data
    except Exception:
        pass
    return _default_prefs()

def save_user_prefs(user_id, prefs):
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    try:
        with open(_prefs_path(user_id), "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_user_codec_preference(user_id):
    prefs = load_user_prefs(user_id)
    return prefs.get("codec", "avc1")

def set_user_codec_preference(user_id, codec):
    prefs = load_user_prefs(user_id)
    prefs["codec"] = codec
    save_user_prefs(user_id, prefs)

def get_user_mkv_preference(user_id):
    # Session override takes precedence
    key = str(user_id)
    if key in _SESSION_MKV_OVERRIDE:
        return bool(_SESSION_MKV_OVERRIDE[key])
    prefs = load_user_prefs(user_id)
    return bool(prefs.get("mkv", False))

def toggle_user_mkv_preference(user_id):
    prefs = load_user_prefs(user_id)
    prefs["mkv"] = not bool(prefs.get("mkv", False))
    save_user_prefs(user_id, prefs)
    return prefs["mkv"]

def set_session_mkv_override(user_id, value):
    _SESSION_MKV_OVERRIDE[str(user_id)] = bool(value)

def clear_session_mkv_override(user_id):
    _SESSION_MKV_OVERRIDE.pop(str(user_id), None)

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
        safe_send_message(user_id, f"✅ Format updated to:\n{custom_format}")
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
        safe_send_message(
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
        safe_send_message(
            user_id,
            "To use a custom format, send the command in the following form:\n\n<code>/format bestvideo+bestaudio/best</code>\n\nReplace <code>bestvideo+bestaudio/best</code> with your desired format string.",
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            reply_markup=keyboard
        )
        callback_query.answer("Hint sent.")
        send_to_logger(callback_query.message, "Custom format hint sent.")
        return

    # If the Others button is pressed - we display the second set of options
    if data == "others":
        # Get current codec preference
        current_codec = get_user_codec_preference(user_id)
        mkv_on = get_user_mkv_preference(user_id)
        
        # Create codec selection buttons with active state indicators
        avc1_button = "✅ avc1 (H.264)" if current_codec == "avc1" else "☑️ avc1 (H.264)"
        av01_button = "✅ av01 (AV1)" if current_codec == "av01" else "☑️ av01 (AV1)"
        vp9_button = "✅ vp09 (VP9)" if current_codec == "vp9" else "☑️ vp09 (VP9)"
        mkv_button = "✅ MKV: ON" if mkv_on else "☑️ MKV: OFF"
        
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
            [
                InlineKeyboardButton(avc1_button, callback_data="format_codec|avc1"),
                InlineKeyboardButton(av01_button, callback_data="format_codec|av01"),
                InlineKeyboardButton(vp9_button, callback_data="format_codec|vp9"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "Select your desired resolution and codec:", reply_markup=full_res_keyboard)
        try:
            callback_query.answer()
        except Exception:
            pass
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
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "Select a format option or send a custom one using <code>/format &lt;format_string&gt;</code>:", reply_markup=main_keyboard)
        try:
            callback_query.answer()
        except Exception:
            pass
        send_to_logger(callback_query.message, "Returned to main format menu.")
        return

    # Get user's codec preference
    user_codec = get_user_codec_preference(user_id)
    
    # Mapping for the Rest of the Options based on selected codec
    if data == "bv144":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=144]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=144]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=144]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=144]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=144]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=144]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv240":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=240][height>144]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=240][height>144]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=240][height>144]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=240][height>144]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=240][height>144]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=240]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv360":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=360][height>240]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=360][height>240]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=360][height>240]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=360][height>240]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=360][height>240]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=360]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv480":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=480][height>360]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=480][height>360]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=480][height>360]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=480][height>360]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=480][height>360]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=480]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv720":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=720][height>480]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=720][height>480]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=720][height>480]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=720][height>480]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=720][height>480]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=720]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv1080":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=1080][height>720]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=1080][height>720]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=1080][height>720]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=1080][height>720]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=1080][height>720]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=1080]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv1440":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=1440][height>1080]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=1440][height>1080]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=1440][height>1080]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=1440][height>1080]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=1440][height>1080]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=1440]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv2160":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=2160][height>1440]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=2160][height>1440]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=2160][height>1440]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=2160][height>1440]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=2160][height>1440]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=2160]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bv4320":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01][height<=4320][height>2160]+ba[acodec*=mp4a]/bv*[vcodec*=av01][height<=4320][height>2160]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][height<=4320][height>2160]+ba[acodec*=mp4a]/bv*[vcodec*=vp9][height<=4320][height>2160]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][height<=4320][height>2160]+ba[acodec*=mp4a]/bv*[vcodec*=avc1][height<=4320]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "bestvideo":
        if user_codec == "av01":
            chosen_format = "bv*[vcodec*=av01]+ba[acodec*=mp4a]/bv*[vcodec*=av01]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9]+ba[acodec*=mp4a]/bv*[vcodec*=vp9]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    elif data == "best":
        if user_codec == "av01":
            chosen_format = "bestvideo[vcodec*=av01]+bestaudio/bv*[vcodec*=av01]+ba"
        elif user_codec == "vp9":
            chosen_format = "bestvideo[vcodec*=vp9]+bestaudio/bv*[vcodec*=vp9]+ba"
        else:  # avc1
            chosen_format = "bestvideo[vcodec*=avc1]+bestaudio/bv*[vcodec*=avc1]+ba"
    else:
        chosen_format = data

    # Save The Selected Format
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
        f.write(chosen_format)
    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, f"✅ Format updated to:\n{chosen_format}")
    try:
        callback_query.answer("✅ Format saved.")
    except Exception:
        pass
    send_to_logger(callback_query.message, f"Format updated to: {chosen_format}")

    if data == "alwaysask":
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write("ALWAYS_ASK")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
                               "✅ Format set to: Always Ask. Now you will be prompted for quality each time you send a URL.")
        send_to_logger(callback_query.message, "Format set to ALWAYS_ASK.")
        return

# Callback processor for codec selection
@app.on_callback_query(filters.regex(r"^format_codec\|"))
def format_codec_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    
    if data in ["avc1", "av01", "vp9"]:
        set_user_codec_preference(user_id, data)
        callback_query.answer(f"✅ Codec set to {data.upper()}")
        
        # Refresh the menu to show updated codec selection
        current_codec = get_user_codec_preference(user_id)
        mkv_on = get_user_mkv_preference(user_id)
        avc1_button = "✅ avc1 (H.264)" if current_codec == "avc1" else "☑️ avc1 (H.264)"
        av01_button = "✅ av01 (AV1)" if current_codec == "av01" else "☑️ av01 (AV1)"
        vp9_button = "✅ vp09 (VP9)" if current_codec == "vp9" else "☑️ vp09 (VP9)"
        mkv_button = "✅ MKV: ON" if mkv_on else "☑️ MKV: OFF"
        
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
            [
                InlineKeyboardButton(avc1_button, callback_data="format_codec|avc1"),
                InlineKeyboardButton(av01_button, callback_data="format_codec|av01"),
                InlineKeyboardButton(vp9_button, callback_data="format_codec|vp9")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        try:
            callback_query.edit_message_reply_markup(reply_markup=full_res_keyboard)
        except Exception:
            pass
        send_to_logger(callback_query.message, f"Codec preference set to {data}")

@app.on_callback_query(filters.regex(r"^format_container\|"))
def format_container_callback(app, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("|")[1]
    if data == "mkv_toggle":
        mkv_on = toggle_user_mkv_preference(user_id)
        # Re-render Others menu
        current_codec = get_user_codec_preference(user_id)
        avc1_button = "✅ avc1 (H.264)" if current_codec == "avc1" else "☑️ avc1 (H.264)"
        av01_button = "✅ av01 (AV1)" if current_codec == "av01" else "☑️ av01 (AV1)"
        vp9_button = "✅ vp09 (VP9)" if current_codec == "vp9" else "☑️ vp09 (VP9)"
        mkv_button = "✅ MKV: ON" if mkv_on else "☑️ MKV: OFF"
        full_res_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("144p (256×144)", callback_data="format_option|bv144"), InlineKeyboardButton("240p (426×240)", callback_data="format_option|bv240"), InlineKeyboardButton("360p (640×360)", callback_data="format_option|bv360")],
            [InlineKeyboardButton("480p (854×480)", callback_data="format_option|bv480"), InlineKeyboardButton("720p (1280×720)", callback_data="format_option|bv720"), InlineKeyboardButton("1080p (1920×1080)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("1440p (2560×1440)", callback_data="format_option|bv1440"), InlineKeyboardButton("2160p (3840×2160)", callback_data="format_option|bv2160"), InlineKeyboardButton("4320p (7680×4320)", callback_data="format_option|bv4320")],
            [InlineKeyboardButton(avc1_button, callback_data="format_codec|avc1"), InlineKeyboardButton(av01_button, callback_data="format_codec|av01"), InlineKeyboardButton(vp9_button, callback_data="format_codec|vp9")],
            [InlineKeyboardButton("🔙 Back", callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton("🔚 Close", callback_data="format_option|close")]
        ])
        try:
            callback_query.edit_message_reply_markup(reply_markup=full_res_keyboard)
        except Exception:
            pass
        try:
            callback_query.answer(f"MKV is now {'ON' if mkv_on else 'OFF'}")
        except Exception:
            pass

# Callback processor to close the message
@app.on_callback_query(filters.regex(r"^format_custom\|"))
def format_custom_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer("Custom format menu closed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, "Custom format menu closed")
        return
# ####################################################################################
