# Keyboard Command Module
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_all, send_to_logger
from CONFIG.config import Config
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
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                message.chat.id,
                getattr(Messages, 'KEYBOARD_SETTING_UPDATED_MSG', "🎹 **Keyboard setting updated!**\n\nNew setting: **{setting}**").format(setting=arg.upper()),
                message=message
            )
            
            # Apply visual keyboard immediately
            apply_keyboard_setting(app, message.chat.id, arg.upper())
            
            # Log the action
            send_to_logger(message, f"User {user_id} set keyboard to {arg.upper()}")
            return
        else:
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                message.chat.id,
                getattr(Messages, 'KEYBOARD_INVALID_ARG_MSG', "❌ **Invalid argument!**\n\nValid options: `off`, `1x3`, `2x3`, `full`\n\nExample: `/keyboard off`"),
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
    
    from CONFIG.messages import MessagesConfig as Messages
    status_text = getattr(Messages, 'KEYBOARD_SETTINGS_STATUS_MSG', "🎹 **Keyboard Settings**\n\nCurrent: **{current}**\n\nChoose an option:\n\nOr use: `/keyboard off`, `/keyboard 1x3`, `/keyboard 2x3`, `/keyboard full`").format(current=current_setting)
    
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
    from CONFIG.messages import MessagesConfig as Messages
    safe_send_message(message.chat.id, Messages.KEYBOARD_ACTIVATED_MSG if hasattr(Messages, 'KEYBOARD_ACTIVATED_MSG') else "🎹 keyboard activated!", reply_markup=reply_markup, message=message)

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
        from CONFIG.messages import MessagesConfig as Messages
        status_text = getattr(Messages, 'KEYBOARD_SETTING_UPDATED_MSG', "🎹 **Keyboard setting updated!**\n\nNew setting: **{setting}**").format(setting=setting)

        app.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            text=status_text,
            parse_mode=enums.ParseMode.MARKDOWN
        )

        # Answer callback query
        from CONFIG.messages import MessagesConfig as Messages
        callback_query.answer(Messages.KEYBOARD_SET_MSG.format(setting=setting))

        # Apply visual keyboard immediately
        if setting == "OFF":
            try:
                from CONFIG.messages import MessagesConfig as Messages
                safe_send_message(
                    callback_query.message.chat.id,
                    getattr(Messages, 'KEYBOARD_HIDDEN_MSG', "⌨️ Keyboard hidden"),
                    reply_markup=ReplyKeyboardRemove(selective=False),
                    reply_parameters=ReplyParameters(message_id=callback_query.message.id)
                )
            except Exception as e:
                from HELPERS.logger import logger
                logger.warning(f"Failed to hide keyboard: {e}")
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                callback_query.message.chat.id,
                getattr(Messages, 'KEYBOARD_1X3_ACTIVATED_MSG', "📱 1x3 keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                callback_query.message.chat.id,
                getattr(Messages, 'KEYBOARD_2X3_ACTIVATED_MSG', "📱 2x3 keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗"]
            ]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                callback_query.message.chat.id,
                getattr(Messages, 'KEYBOARD_EMOJI_ACTIVATED_MSG', "🔣 Emoji keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True),
                reply_parameters=ReplyParameters(message_id=callback_query.message.id)
            )

        # Log the action
        send_to_logger(callback_query.message, f"User {user_id} set keyboard to {setting}")

    except Exception as e:
        from CONFIG.messages import MessagesConfig as Messages
        callback_query.answer(Messages.KEYBOARD_SETTING_ERROR_MSG, show_alert=True)
        from HELPERS.logger import logger
        logger.error(f"Error processing keyboard setting: {e}")

def apply_keyboard_setting(app, chat_id, setting):
    """Apply keyboard setting immediately"""
    try:
        if setting == "OFF":
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                chat_id,
                getattr(Messages, 'KEYBOARD_HIDDEN_MSG', "⌨️ Keyboard hidden"),
                reply_markup=ReplyKeyboardRemove(selective=False)
            )
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                chat_id,
                getattr(Messages, 'KEYBOARD_1X3_ACTIVATED_MSG', "📱 1x3 keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                chat_id,
                getattr(Messages, 'KEYBOARD_2X3_ACTIVATED_MSG', "📱 2x3 keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍"],
                ["📼", "📊", "✂️", "🎧", "💬", "🌎"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗"]
            ]
            from CONFIG.messages import MessagesConfig as Messages
            safe_send_message(
                chat_id,
                getattr(Messages, 'KEYBOARD_EMOJI_ACTIVATED_MSG', "🔣 Emoji keyboard activated!"),
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True)
            )
    except Exception as e:
        from HELPERS.logger import logger
        logger.error(f"Error applying keyboard setting {setting}: {e}")
