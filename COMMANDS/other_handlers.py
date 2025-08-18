# #############################################################################################################################

import os
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.decorators import reply_with_keyboard, send_reply_keyboard_always
from HELPERS.logger import send_to_logger, send_to_user
from HELPERS.limitter import is_user_in_channel, check_user, check_playlist_range_limits
from HELPERS.download_status import get_active_download
from HELPERS.filesystem_hlp import create_directory

from CONFIG.config import Config

from URL_PARSERS.tags import extract_url_range_tags, save_user_tags

from DOWN_AND_UP.down_and_audio import down_and_audio

# Get app instance for decorators
app = get_app()

# Command handlers moved to URL_PARSERS/url_extractor.py url_distractor function
# to avoid conflicts with the main text handler

# Keep only the callback handler for help close button
@app.on_callback_query(filters.regex(r"^help_msg\|"))
def help_msg_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Help closed.")
        send_to_logger(callback_query.message, "Help message closed.")
        return


#############################################################################################################################

# Command to Download Audio from a Video url
@app.on_message(filters.command("audio") & filters.private)
# @reply_with_keyboard
def audio_command_handler(app, message):
    user_id = message.chat.id
    if get_active_download(user_id):
        app.send_message(user_id, "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED", reply_to_message_id=message.id)
        return
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    text = message.text
    url, _, _, _, tags, tags_text, tag_error = extract_url_range_tags(text)
    if tag_error:
        wrong, example = tag_error
        app.send_message(user_id, f"❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}", reply_to_message_id=message.id)
        return
    if not url:
        send_to_user(message, "Please, send valid URL.")
        return
    save_user_tags(user_id, tags)
    
    # Extract playlist parameters from the message
    full_string = message.text or message.caption or ""
    _, video_start_with, video_end_with, playlist_name, _, _, tag_error = extract_url_range_tags(full_string)
    video_count = video_end_with - video_start_with + 1
    
    # Checking the range limit
    if not check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
        return
    
    down_and_audio(app, message, url, tags, quality_key="mp3", playlist_name=playlist_name, video_count=video_count, video_start_with=video_start_with)


# /Playlist Command
@app.on_message(filters.command("playlist") & filters.private)
# @reply_with_keyboard
def playlist_command(app, message):
    user_id = message.chat.id
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Close", callback_data="playlist_help|close")]
    ])
    app.send_message(user_id, Config.PLAYLIST_HELP_MSG, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    send_to_logger(message, "User requested playlist help.")

@app.on_callback_query(filters.regex(r"^playlist_help\|"))
def playlist_help_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Playlist help closed.")
        send_to_logger(callback_query.message, "Playlist help closed.")
        return


@app.on_callback_query(filters.regex(r"^userlogs_close\|"))
def userlogs_close_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Logs message closed.")
        send_to_logger(callback_query.message, "User logs message closed.")
        return

@app.on_callback_query(filters.regex(r"^audio_hint\|"))
def audio_hint_callback(app, callback_query):
    data = callback_query.data.split("|")[1]
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        callback_query.answer("Audio hint closed.")
        send_to_logger(callback_query.message, "Audio hint closed.")
        return




