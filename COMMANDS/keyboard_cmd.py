# Keyboard Command Module
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_all, send_to_logger
from CONFIG.config import Config
from CONFIG.messages import MessagesConfig as Messages
from HELPERS.safe_messeger import safe_send_message

def keyboard_command(app, message):
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
            with open(keyboard_file, 'w') as f:
                f.write(arg.upper())
            
            # Show confirmation
            safe_send_message(
                message.chat.id,
Messages.KEYBOARD_UPDATED_MSG.format(setting=arg.upper()),
                message=message
            )
            
            # Apply visual keyboard immediately
            apply_keyboard_setting(app, message.chat.id, arg.upper())
            
            # Log the action
            send_to_logger(message, Messages.KEYBOARD_SET_LOG_MSG.format(user_id=user_id, setting=arg.upper()))
            return
        else:
            safe_send_message(
                message.chat.id,
Messages.KEYBOARD_INVALID_ARG_MSG,
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
        [InlineKeyboardButton("🔴 OFF", callback_data=f"keyboard|OFF"), InlineKeyboardButton("🔣 FULL", callback_data=f"keyboard|FULL")],
        [InlineKeyboardButton("📱 1x3", callback_data=f"keyboard|1x3"), InlineKeyboardButton("📱 2x3", callback_data=f"keyboard|2x3")]
    ])
    
    status_text = Messages.KEYBOARD_SETTINGS_MSG.format(current=current_setting)
    
    # Send the settings message
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
    safe_send_message(message.chat.id, Messages.KEYBOARD_ACTIVATED_MSG, reply_markup=reply_markup, message=message)

def keyboard_callback_handler(app, callback_query):
    """Handle keyboard setting callbacks"""
    user_id = str(callback_query.from_user.id)
    setting = callback_query.data.split("|")[1]
    
    user_dir = f'./users/{user_id}'
    keyboard_file = os.path.join(user_dir, 'keyboard.txt')
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Save or apply the setting and show corresponding keyboard instantly
    try:
        # Persist modes including FULL
        if setting in ["OFF", "1x3", "2x3", "FULL"]:
            with open(keyboard_file, 'w') as f:
                f.write(setting)

        # Prepare status text
        status_text = f"🎹 **Keyboard setting updated!**\n\nNew setting: **{setting}**"

        app.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            text=status_text,
            parse_mode=enums.ParseMode.MARKDOWN
        )

        # Answer callback query
        callback_query.answer(Messages.KEYBOARD_SET_TO_MSG.format(setting=setting))

        # Apply visual keyboard immediately
        if setting == "OFF":
            try:
                safe_send_message(
                    callback_query.message.chat.id,
Messages.KEYBOARD_HIDDEN_MSG,
                    reply_markup=ReplyKeyboardRemove(selective=False),
                    reply_parameters=ReplyParameters(message_id=callback_query.message.id)
                )
            except Exception as e:
                from HELPERS.logger import logger
                logger.warning(f"Failed to hide keyboard: {e}")
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            safe_send_message(
                callback_query.message.chat.id,
Messages.KEYBOARD_1X3_ACTIVATED_MSG,
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
Messages.KEYBOARD_2X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗"]
            ]
            safe_send_message(
                callback_query.message.chat.id,
Messages.KEYBOARD_EMOJI_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )

        # Log the action
        send_to_logger(callback_query.message, Messages.KEYBOARD_SET_CALLBACK_LOG_MSG.format(user_id=user_id, setting=setting))

    except Exception as e:
        callback_query.answer(Messages.KEYBOARD_ERROR_PROCESSING_MSG, show_alert=True)
        from HELPERS.logger import logger
        logger.error(f"Error processing keyboard setting: {e}")

def apply_keyboard_setting(app, chat_id, setting):
    """Apply keyboard setting immediately"""
    try:
        if setting == "OFF":
            safe_send_message(
                chat_id,
                "⌨️ Keyboard hidden",
                reply_markup=ReplyKeyboardRemove(selective=False)
            )
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            safe_send_message(
                chat_id,
Messages.KEYBOARD_1X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            safe_send_message(
                chat_id,
Messages.KEYBOARD_2X3_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗"]
            ]
            safe_send_message(
                chat_id,
Messages.KEYBOARD_EMOJI_ACTIVATED_MSG,
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True)
            )
    except Exception as e:
        from HELPERS.logger import logger
        logger.error(Messages.KEYBOARD_ERROR_APPLYING_MSG.format(setting=setting, error=e))
