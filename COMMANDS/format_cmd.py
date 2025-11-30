
# Command /Format Handler
from pyrogram import filters
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_logger, logger
from HELPERS.filesystem_hlp import create_directory
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.decorators import background_handler
from urllib.parse import urlparse
import os
import json
import re

# Session-scoped overrides (not persisted)
_SESSION_MKV_OVERRIDE = {}

# Per-user format preferences (persisted in users/<id>/format_prefs.json)
def _prefs_path(user_id):
    messages = safe_get_messages(user_id)
    return os.path.join("users", str(user_id), "format_prefs.json")

def _default_prefs():
    # codec: avc1 | av01 | vp9
    # mkv: True -> remux to mkv container, False -> default to mp4
    return {"codec": "avc1", "mkv": False}

def parse_quality_argument(quality_arg):
    """
    Parses quality argument and returns format for yt-dlp
    
    Args:
        quality_arg (str): Quality argument (e.g., "720", "720p", "4k", "8K")
        
    Returns:
        str: Format for yt-dlp
    """
    if not quality_arg:
        return "best"
    
    quality_arg = quality_arg.lower().strip()
    
    # Remove 'p' or 'P' if present
    if quality_arg.endswith('p'):
        quality_arg = quality_arg[:-1]
    
    # Special cases for 4K and 8K
    if quality_arg in ['4k', '4']:
        return "bv*[height<=2160]+ba/bv*[height<=2160]/bv+ba/best"
    elif quality_arg in ['8k', '8']:
        return "bv*[height<=4320]+ba/bv*[height<=4320]/bv+ba/best"
    
    # Check if this is a number from 1 to 10000
    try:
        quality_num = int(quality_arg)
        if 1 <= quality_num <= 10000:
            return f"bv*[height<={quality_num}]+ba/bv*[height<={quality_num}]/bv+ba/best"
        else:
            return "best"
    except ValueError:
        return "best"

def load_user_prefs(user_id):
    messages = safe_get_messages(user_id)
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
    messages = safe_get_messages(user_id)
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    try:
        with open(_prefs_path(user_id), "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_user_codec_preference(user_id):
    messages = safe_get_messages(user_id)
    prefs = load_user_prefs(user_id)
    return prefs.get("codec", "avc1")

def set_user_codec_preference(user_id, codec):
    messages = safe_get_messages(user_id)
    prefs = load_user_prefs(user_id)
    prefs["codec"] = codec
    save_user_prefs(user_id, prefs)

def get_user_mkv_preference(user_id):
    messages = safe_get_messages(user_id)
    # Session override takes precedence
    key = str(user_id)
    if key in _SESSION_MKV_OVERRIDE:
        return bool(_SESSION_MKV_OVERRIDE[key])
    prefs = load_user_prefs(user_id)
    return bool(prefs.get("mkv", False))

def toggle_user_mkv_preference(user_id):
    messages = safe_get_messages(user_id)
    prefs = load_user_prefs(user_id)
    prefs["mkv"] = not bool(prefs.get("mkv", False))
    save_user_prefs(user_id, prefs)
    return prefs["mkv"]

def set_session_mkv_override(user_id, value):
    messages = safe_get_messages(user_id)
    _SESSION_MKV_OVERRIDE[str(user_id)] = bool(value)

def clear_session_mkv_override(user_id):
    messages = safe_get_messages(user_id)
    _SESSION_MKV_OVERRIDE.pop(str(user_id), None)

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("format") & filters.private)
# @reply_with_keyboard
@background_handler(label="format_command")
def set_format(app, message):
    messages = safe_get_messages(message.chat.id)
    user_id = message.chat.id
    # For non-admins, we check the subscription
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    send_to_logger(message, safe_get_messages(user_id).FORMAT_CHANGE_REQUESTED_LOG_MSG)
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)  # Ensure The User's Folder Exists

    # If the additional text is transmitted, we save it as Custom Format or Quality
    if len(message.command) > 1:
        arg = message.text.split(" ", 1)[1].strip()
        
        # Check for special arguments
        if arg.lower() == "ask":
            # Set to Always Ask mode
            with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
                f.write("ALWAYS_ASK")
            safe_send_message(user_id, safe_get_messages(user_id).FORMAT_ALWAYS_ASK_SET_MSG, message=message)
            send_to_logger(message, safe_get_messages(user_id).FORMAT_ALWAYS_ASK_SET_LOG_MSG)
            return
        elif arg.lower() == "best":
            # Set to best format with AVC codec and MP4 container priority
            # with fallback to bv+ba/best if no AVC+MP4 available
            custom_format = "bv*[vcodec*=avc1][ext=mp4]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv*[ext=mp4]+ba/bv+ba/best"
            safe_send_message(user_id, safe_get_messages(user_id).FORMAT_BEST_UPDATED_MSG.format(format=custom_format), message=message)
            send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_BEST_LOG_MSG.format(format=custom_format))
        # Check if it's a format ID (e.g., "id 401", "id401")
        elif re.match(r'^id\s*\d+$', arg, re.IGNORECASE):
            # Extract the ID number
            format_id = re.search(r'\d+', arg).group()
            
            # Check if this is an audio-only format by analyzing the URL
            # We need to get the last URL from user's history or ask them to provide URL
            try:
                # Try to get URL from user's last message or session
                from DOWN_AND_UP.always_ask_menu import get_video_formats, analyze_format_type
                
                # Use format ID with fallback for both audio and video
                # This works for audio-only, video-only, and full formats
                custom_format = f"{format_id}+bestaudio/bv+ba/best"
                
                # Check if we can determine if it's audio-only by looking at recent URL
                # This is a simplified approach - in a real scenario, you might want to store the last URL
                safe_send_message(user_id, safe_get_messages(user_id).FORMAT_ID_UPDATED_MSG.format(id=format_id, format=custom_format), message=message)
                send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_ID_LOG_MSG.format(format_id=format_id, format=custom_format))
                
            except Exception as e:
                # Fallback to original behavior
                custom_format = f"{format_id}+bestaudio/bv+ba/best"
                safe_send_message(user_id, safe_get_messages(user_id).FORMAT_ID_UPDATED_MSG.format(id=format_id, format=custom_format), message=message)
                send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_ID_LOG_MSG.format(format_id=format_id, format=custom_format))
        
        # Check if it's a format ID with audio flag (e.g., "id 140 audio", "id140 audio")
        elif re.match(r'^id\s*\d+\s+audio$', arg, re.IGNORECASE):
            # Extract the ID number
            format_id = re.search(r'\d+', arg).group()
            
            # Use format ID with bestaudio fallback for audio-only formats
            custom_format = f"{format_id}/bestaudio"
            
            safe_send_message(user_id, safe_get_messages(user_id).FORMAT_ID_AUDIO_UPDATED_MSG.format(id=format_id, format=custom_format), message=message)
            send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_ID_AUDIO_LOG_MSG.format(format_id=format_id, format=custom_format))
        
        # Check if it's a quality argument (number, number+p, 4k, 8k)
        elif re.match(r'^(\d+p?|4k|8k|4K|8K)$', arg, re.IGNORECASE):
            # It's a quality argument, convert to format
            custom_format = parse_quality_argument(arg)
            safe_send_message(user_id, safe_get_messages(user_id).FORMAT_QUALITY_UPDATED_MSG.format(quality=arg, format=custom_format), message=message)
            send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_QUALITY_LOG_MSG.format(quality=arg, format=custom_format))
        else:
            # It's a custom format string
            custom_format = arg
            safe_send_message(user_id, safe_get_messages(user_id).FORMAT_CUSTOM_UPDATED_MSG.format(format=custom_format), message=message)
            send_to_logger(message, safe_get_messages(user_id).FORMAT_UPDATED_CUSTOM_LOG_MSG.format(format=custom_format))
        
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write(custom_format)
    else:
        # Main Menu with A Few Popular Options, Plus The Others Button
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_ALWAYS_ASK_BUTTON_MSG, callback_data="format_option|alwaysask")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_OTHERS_BUTTON_MSG, callback_data="format_option|others")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_4K_PC_BUTTON_MSG, callback_data="format_option|bv2160")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_FULLHD_MOBILE_BUTTON_MSG, callback_data="format_option|bv1080")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_BESTVIDEO_BUTTON_MSG, callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_CUSTOM_BUTTON_MSG, callback_data="format_option|custom")],
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_option|close")]
        ])
        safe_send_message(
            user_id,
safe_get_messages(user_id).FORMAT_MENU_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_CUSTOM_FORMAT_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_720P_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_4K_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_8K_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_ID_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_ASK_MSG + "\n"
            + safe_get_messages(user_id).FORMAT_BEST_MSG,
            reply_markup=main_keyboard,
            message=message
        )
        send_to_logger(message, safe_get_messages(user_id).FORMAT_MENU_SENT_LOG_MSG)


# Callbackquery Handler for /Format Menu Selection
@app.on_callback_query(filters.regex(r"^format_option\|"))
# @reply_with_keyboard
def format_option_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    logger.info(LoggerMsg.FORMAT_CALLBACK_LOG_MSG.format(callback_data=callback_query.data))
    data = callback_query.data.split("|")[1]

    # If you press the close button
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer(safe_get_messages(user_id).FORMAT_CHOICE_UPDATED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_SELECTION_CLOSED_LOG_MSG)
        return

    # If the Custom button is pressed
    if data == "custom":
        # Sending a message with the Close button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_custom|close")]
        ])
        safe_send_message(
            user_id,
safe_get_messages(user_id).FORMAT_CUSTOM_HINT_MSG,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
            reply_markup=keyboard
        )
        callback_query.answer(safe_get_messages(user_id).FORMAT_HINT_SENT_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_CUSTOM_HINT_SENT_LOG_MSG)
        return

    # If the Others button is pressed - we display the second set of options
    if data == "others":
        # Get current codec preference
        current_codec = get_user_codec_preference(user_id)
        mkv_on = get_user_mkv_preference(user_id)
        
        # Create codec selection buttons with active state indicators
        avc1_button = safe_get_messages(user_id).FORMAT_AVC1_BUTTON_MSG if current_codec == "avc1" else safe_get_messages(user_id).FORMAT_AVC1_BUTTON_INACTIVE_MSG
        av01_button = safe_get_messages(user_id).FORMAT_AV01_BUTTON_MSG if current_codec == "av01" else safe_get_messages(user_id).FORMAT_AV01_BUTTON_INACTIVE_MSG
        vp9_button = safe_get_messages(user_id).FORMAT_VP9_BUTTON_MSG if current_codec == "vp9" else safe_get_messages(user_id).FORMAT_VP9_BUTTON_INACTIVE_MSG
        mkv_button = safe_get_messages(user_id).FORMAT_MKV_ON_BUTTON_MSG if mkv_on else safe_get_messages(user_id).FORMAT_MKV_OFF_BUTTON_MSG
        
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
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_BACK_BUTTON_MSG, callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_option|close")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).FORMAT_RESOLUTION_MENU_MSG, reply_markup=full_res_keyboard)
        try:
            callback_query.answer()
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_RESOLUTION_MENU_SENT_LOG_MSG)
        return

    # If the Back button is pressed - we return to the main menu
    if data == "back":
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_ALWAYS_ASK_BUTTON_MSG, callback_data="format_option|alwaysask")],
            [InlineKeyboardButton("🎛Others (144p - 4320p)", callback_data="format_option|others")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_4K_PC_BUTTON_MSG, callback_data="format_option|bv2160")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_FULLHD_MOBILE_BUTTON_MSG, callback_data="format_option|bv1080")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_BESTVIDEO_BUTTON_MSG, callback_data="format_option|bestvideo")],
            # [InlineKeyboardButton("📉best (no ffmpeg) (bad)", callback_data="format_option|best")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_CUSTOM_BUTTON_MSG, callback_data="format_option|custom")],
            [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_option|close")]
        ])
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).FORMAT_MENU_MSG + "\n" + safe_get_messages(user_id).FORMAT_MENU_ADDITIONAL_MSG + "\n" + safe_get_messages(user_id).FORMAT_8K_QUALITY_MSG, reply_markup=main_keyboard)
        try:
            callback_query.answer()
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_RETURNED_MAIN_MENU_LOG_MSG)
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
            chosen_format = "bv*[vcodec*=av01][ext=mp4]+ba[acodec*=mp4a]/bv*[vcodec*=av01]+ba[acodec*=opus]/bv*[vcodec*=av01]+ba/bv+ba/best"
        elif user_codec == "vp9":
            chosen_format = "bv*[vcodec*=vp9][ext=mp4]+ba[acodec*=mp4a]/bv*[vcodec*=vp9]+ba[acodec*=opus]/bv*[vcodec*=vp9]+ba/bv+ba/best"
        else:  # avc1
            chosen_format = "bv*[vcodec*=avc1][ext=mp4]+ba[acodec*=mp4a]/bv*[vcodec*=avc1]+ba/bv*[vcodec*=avc1]+ba/bv+ba/best"
    else:
        chosen_format = data

    # Save The Selected Format
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
        f.write(chosen_format)
    safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).FORMAT_UPDATED_MSG.format(format=chosen_format))
    try:
        callback_query.answer(safe_get_messages(user_id).FORMAT_SAVED_MSG)
    except Exception:
        pass
    send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_UPDATED_CALLBACK_LOG_MSG.format(format=chosen_format))

    if data == "alwaysask":
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        with open(os.path.join(user_dir, "format.txt"), "w", encoding="utf-8") as f:
            f.write("ALWAYS_ASK")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id,
                               safe_get_messages(user_id).FORMAT_ALWAYS_ASK_CONFIRM_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_ALWAYS_ASK_SET_CALLBACK_LOG_MSG)
        return

# Callback processor for codec selection
@app.on_callback_query(filters.regex(r"^format_codec\|"))
def format_codec_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    data = callback_query.data.split("|")[1]
    
    if data in ["avc1", "av01", "vp9"]:
        set_user_codec_preference(user_id, data)
        callback_query.answer(safe_get_messages(user_id).FORMAT_CODEC_SET_MSG.format(codec=data.upper()))
        
        # Refresh the menu to show updated codec selection
        current_codec = get_user_codec_preference(user_id)
        mkv_on = get_user_mkv_preference(user_id)
        avc1_button = safe_get_messages(user_id).FORMAT_AVC1_BUTTON_MSG if current_codec == "avc1" else safe_get_messages(user_id).FORMAT_AVC1_BUTTON_INACTIVE_MSG
        av01_button = safe_get_messages(user_id).FORMAT_AV01_BUTTON_MSG if current_codec == "av01" else safe_get_messages(user_id).FORMAT_AV01_BUTTON_INACTIVE_MSG
        vp9_button = safe_get_messages(user_id).FORMAT_VP9_BUTTON_MSG if current_codec == "vp9" else safe_get_messages(user_id).FORMAT_VP9_BUTTON_INACTIVE_MSG
        mkv_button = safe_get_messages(user_id).FORMAT_MKV_ON_BUTTON_MSG if mkv_on else safe_get_messages(user_id).FORMAT_MKV_OFF_BUTTON_MSG
        
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
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_BACK_BUTTON_MSG, callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_option|close")]
        ])
        try:
            callback_query.edit_message_reply_markup(reply_markup=full_res_keyboard)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_CODEC_SET_LOG_MSG.format(codec=data))

@app.on_callback_query(filters.regex(r"^format_container\|"))
def format_container_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    data = callback_query.data.split("|")[1]
    if data == "mkv_toggle":
        mkv_on = toggle_user_mkv_preference(user_id)
        # Re-render Others menu
        current_codec = get_user_codec_preference(user_id)
        avc1_button = safe_get_messages(user_id).FORMAT_AVC1_BUTTON_MSG if current_codec == "avc1" else safe_get_messages(user_id).FORMAT_AVC1_BUTTON_INACTIVE_MSG
        av01_button = safe_get_messages(user_id).FORMAT_AV01_BUTTON_MSG if current_codec == "av01" else safe_get_messages(user_id).FORMAT_AV01_BUTTON_INACTIVE_MSG
        vp9_button = safe_get_messages(user_id).FORMAT_VP9_BUTTON_MSG if current_codec == "vp9" else safe_get_messages(user_id).FORMAT_VP9_BUTTON_INACTIVE_MSG
        mkv_button = safe_get_messages(user_id).FORMAT_MKV_ON_BUTTON_MSG if mkv_on else safe_get_messages(user_id).FORMAT_MKV_OFF_BUTTON_MSG
        full_res_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("144p (256×144)", callback_data="format_option|bv144"), InlineKeyboardButton("240p (426×240)", callback_data="format_option|bv240"), InlineKeyboardButton("360p (640×360)", callback_data="format_option|bv360")],
            [InlineKeyboardButton("480p (854×480)", callback_data="format_option|bv480"), InlineKeyboardButton("720p (1280×720)", callback_data="format_option|bv720"), InlineKeyboardButton("1080p (1920×1080)", callback_data="format_option|bv1080")],
            [InlineKeyboardButton("1440p (2560×1440)", callback_data="format_option|bv1440"), InlineKeyboardButton("2160p (3840×2160)", callback_data="format_option|bv2160"), InlineKeyboardButton("4320p (7680×4320)", callback_data="format_option|bv4320")],
            [InlineKeyboardButton(avc1_button, callback_data="format_codec|avc1"), InlineKeyboardButton(av01_button, callback_data="format_codec|av01"), InlineKeyboardButton(vp9_button, callback_data="format_codec|vp9")],
            [InlineKeyboardButton(safe_get_messages(user_id).FORMAT_BACK_BUTTON_MSG, callback_data="format_option|back"), InlineKeyboardButton(mkv_button, callback_data="format_container|mkv_toggle"), InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="format_option|close")]
        ])
        try:
            callback_query.edit_message_reply_markup(reply_markup=full_res_keyboard)
        except Exception:
            pass
        try:
            callback_query.answer(safe_get_messages(user_id).FORMAT_MKV_TOGGLE_MSG.format(status='ON' if mkv_on else 'OFF'))
        except Exception:
            pass

# Callback processor to close the message
@app.on_callback_query(filters.regex(r"^format_custom\|"))
def format_custom_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(safe_get_messages(user_id).FORMAT_CUSTOM_MENU_CLOSED_MSG)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).FORMAT_CUSTOM_MENU_CLOSED_LOG_MSG)
        return
# ####################################################################################
