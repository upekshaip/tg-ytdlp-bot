# Keyboard Command Module
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_all, send_to_logger
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text

def keyboard_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Handle keyboard settings command"""
    user_id = str(message.chat.id)
    user_dir = f'./users/{user_id}'
    keyboard_file = os.path.join(user_dir, 'keyboard.txt')
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Check if arguments are provided
    if hasattr(message, 'command') and message.command and len(message.command) > 1:
        arg = message.command[1].lower()
        if arg in ["off", "1x3", "2x3", "full"]:
            # Apply setting directly
            with open(keyboard_file, 'w', encoding='utf-8') as f:
                f.write(arg.upper())
            
            # Show confirmation by editing the original message
            result = safe_edit_message_text(
                message.chat.id,
                message.id,
                safe_get_messages(user_id).KEYBOARD_UPDATED_MSG.format(setting=arg.upper()),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            # If editing failed, send new message as fallback
            if result is None:
                safe_send_message(
                    message.chat.id,
                    safe_get_messages(user_id).KEYBOARD_UPDATED_MSG.format(setting=arg.upper()),
                    message=message
                )
            
            # Apply visual keyboard immediately
            apply_keyboard_setting(app, message.chat.id, arg.upper(), user_id=user_id)
            
            # Log the action
            send_to_logger(message, safe_get_messages(user_id).KEYBOARD_SET_LOG_MSG.format(user_id=user_id, setting=arg.upper()))
            return
        else:
            result = safe_edit_message_text(
                message.chat.id,
                message.id,
                safe_get_messages(user_id).KEYBOARD_INVALID_ARG_MSG,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            # If editing failed, send new message as fallback
            if result is None:
                safe_send_message(
                    message.chat.id,
                    safe_get_messages(user_id).KEYBOARD_INVALID_ARG_MSG,
                    message=message
                )
            return
    
    # Read current keyboard setting
    current_setting = "2x3"  # Default setting
    if os.path.exists(keyboard_file):
        try:
            with open(keyboard_file, 'r') as f:
                setting = f.read().strip()
                if setting in ["OFF", "1x3", "2x3", "FULL"]:
                    current_setting = setting
                else:
                    current_setting = "2x3"  # Fallback to default
        except:
            current_setting = "2x3"  # Fallback to default
    
    # Create inline keyboard for options in 2 rows
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(safe_get_messages(user_id).KEYBOARD_OFF_BUTTON_MSG, callback_data="keyboard|OFF"), InlineKeyboardButton(safe_get_messages(user_id).KEYBOARD_FULL_BUTTON_MSG, callback_data="keyboard|FULL")],
        [InlineKeyboardButton(safe_get_messages(user_id).KEYBOARD_1X3_BUTTON_MSG, callback_data="keyboard|1x3"), InlineKeyboardButton(safe_get_messages(user_id).KEYBOARD_2X3_BUTTON_MSG, callback_data="keyboard|2x3")],
        [InlineKeyboardButton(safe_get_messages(user_id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="keyboard|close")]
    ])
    
    status_text = safe_get_messages(user_id).KEYBOARD_SETTINGS_MSG.format(current=current_setting)
    
    # Edit the original message instead of sending new one
    result = safe_edit_message_text(
        message.chat.id,
        message.id,
        status_text,
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    # If editing failed, send new message as fallback
    if result is None:
        safe_send_message(
            message.chat.id,
            status_text,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=keyboard,
            message=message
        )
    
    # Always show full keyboard when /keyboard command is used
    full_keyboard = [
        ["/clean", "/cookie", "/settings"],
        ["/playlist", "/search", "/help"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(full_keyboard, resize_keyboard=True)
    safe_send_message(message.chat.id, safe_get_messages(user_id).KEYBOARD_ACTIVATED_MSG, reply_markup=reply_markup, message=message)

def keyboard_callback_handler(app, callback_query):
    """Handle keyboard setting callbacks"""
    user_id = str(callback_query.from_user.id)
    messages = safe_get_messages(user_id)
    setting = callback_query.data.split("|")[1]
    
    # Handle close button
    if setting == "close":
        try:
            callback_query.message.delete()
            callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_CLOSED_MSG)
            return
        except Exception as e:
            callback_query.answer(safe_get_messages(user_id).URL_EXTRACTOR_ERROR_OCCURRED_MSG, show_alert=True)
            return
    
    user_dir = f'./users/{user_id}'
    keyboard_file = os.path.join(user_dir, 'keyboard.txt')
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Save or apply the setting and show corresponding keyboard instantly
    try:
        # Persist modes including FULL
        if setting in ["OFF", "1x3", "2x3", "FULL"]:
            with open(keyboard_file, 'w', encoding='utf-8') as f:
                f.write(setting)

        # Prepare status text
        status_text = safe_get_messages(user_id).KEYBOARD_SETTING_UPDATED_MSG.format(setting=setting)

        result = safe_edit_message_text(
            callback_query.message.chat.id,
            callback_query.message.id,
            status_text,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        # If editing failed, send new message as fallback
        if result is None:
            safe_send_message(
                callback_query.message.chat.id,
                status_text,
                parse_mode=enums.ParseMode.MARKDOWN,
                message=callback_query.message
            )

        # Answer callback query
        callback_query.answer(safe_get_messages(user_id).KEYBOARD_SET_TO_MSG.format(setting=setting))

        # Apply visual keyboard immediately
        if setting == "OFF":
            try:
                safe_send_message(
                    callback_query.message.chat.id,
safe_get_messages(user_id).KEYBOARD_HIDDEN_MSG,
                    reply_markup=ReplyKeyboardRemove(selective=False),
                    reply_parameters=ReplyParameters(message_id=callback_query.message.id)
                )
            except Exception as e:
                from HELPERS.logger import logger
                logger.warning(safe_get_messages(user_id).KEYBOARD_FAILED_HIDE_MSG.format(error=e))
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            safe_send_message(
                callback_query.message.chat.id,
safe_get_messages(user_id).KEYBOARD_1X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            safe_send_message(
                callback_query.message.chat.id,
safe_get_messages(user_id).KEYBOARD_2X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍", "🧰"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎", "🔞"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗", "🧾"]
            ]
            safe_send_message(
                callback_query.message.chat.id,
safe_get_messages(user_id).KEYBOARD_EMOJI_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )

        # Log the action
        send_to_logger(callback_query.message, safe_get_messages(user_id).KEYBOARD_SET_CALLBACK_LOG_MSG.format(user_id=user_id, setting=setting))

    except Exception as e:
        callback_query.answer(safe_get_messages(user_id).KEYBOARD_ERROR_PROCESSING_MSG, show_alert=True)
        from HELPERS.logger import logger
        logger.error(f"Error processing keyboard setting: {e}")

def apply_keyboard_setting(app, chat_id, setting, message_id=None, user_id=None):
    messages = safe_get_messages(user_id)
    """Apply keyboard setting immediately"""
    try:
        if setting == "OFF":
            # Send keyboard removal as a separate message since it's a visual change
            safe_send_message(
                chat_id,
                "⌨️ Keyboard hidden",
                reply_markup=ReplyKeyboardRemove(selective=False)
            )
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            # Send keyboard change as a separate message since it's a visual change
            safe_send_message(
                chat_id,
safe_get_messages(user_id).KEYBOARD_1X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            # Send keyboard change as a separate message since it's a visual change
            safe_send_message(
                chat_id,
safe_get_messages(user_id).KEYBOARD_2X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍", "🧰"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎", "🔞"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗", "🧾"]
            ]
            # Send keyboard change as a separate message since it's a visual change
            safe_send_message(
                chat_id,
safe_get_messages(user_id).KEYBOARD_EMOJI_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True)
            )
    except Exception as e:
        from HELPERS.logger import logger
        logger.error(safe_get_messages(user_id).KEYBOARD_ERROR_APPLYING_MSG.format(setting=setting, error=e))
