# Keyboard Command Module
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from pyrogram import enums
from HELPERS.logger import send_to_all, send_to_logger
from CONFIG.config import Config

def keyboard_command(app, message):
    """Handle keyboard settings command"""
    user_id = str(message.chat.id)
    user_dir = f'./users/{user_id}'
    keyboard_file = os.path.join(user_dir, 'keyboard.txt')
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Read current keyboard setting
    current_setting = "2x3"  # Default setting
    if os.path.exists(keyboard_file):
        try:
            with open(keyboard_file, 'r') as f:
                setting = f.read().strip()
                if setting in ["OFF", "1x3", "2x3"]:
                    current_setting = setting
                else:
                    current_setting = "2x3"  # Fallback to default
        except:
            current_setting = "2x3"  # Fallback to default
    
    # Create inline keyboard for options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 OFF", callback_data=f"keyboard|OFF")],
        [InlineKeyboardButton("📱 1x3", callback_data=f"keyboard|1x3")],
        [InlineKeyboardButton("📱 2x3", callback_data=f"keyboard|2x3")],
        [InlineKeyboardButton("🔣 FULL", callback_data=f"keyboard|FULL")]
    ])
    
    status_text = f"🎹 **Keyboard Settings**\n\nCurrent: **{current_setting}**\n\nChoose an option:"
    
    # Send the settings message
    app.send_message(
        message.chat.id,
        status_text,
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    # Always show full keyboard when /keyboard command is used
    full_keyboard = [
        ["/clean", "/cookie", "/settings"],
        ["/playlist", "/search", "/help"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(full_keyboard, resize_keyboard=True)
    app.send_message(message.chat.id, "🎹 keyboard activated!", reply_markup=reply_markup)

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
        callback_query.answer(f"Keyboard set to {setting}")

        # Apply visual keyboard immediately
        if setting == "OFF":
            try:
                app.send_message(
                    callback_query.message.chat.id,
                    "⌨️ Keyboard hidden",
                    reply_markup=ReplyKeyboardRemove(selective=False)
                )
            except Exception as e:
                from HELPERS.logger import logger
                logger.warning(f"Failed to hide keyboard: {e}")
        elif setting == "1x3":
            one_by_three = [["/clean", "/cookie", "/settings"]]
            app.send_message(
                callback_query.message.chat.id,
                "📱 1x3 keyboard activated!",
                reply_markup=ReplyKeyboardMarkup(one_by_three, resize_keyboard=True)
            )
        elif setting == "2x3":
            two_by_three = [
                ["/clean", "/cookie", "/settings"],
                ["/playlist", "/search", "/help"]
            ]
            app.send_message(
                callback_query.message.chat.id,
                "📱 2x3 keyboard activated!",
                reply_markup=ReplyKeyboardMarkup(two_by_three, resize_keyboard=True)
            )
        elif setting == "FULL":
            emoji_keyboard = [
                ["🧹", "🍪", "⚙️", "🔍", "🌐"],
                ["📼", "📊", "✂️", "🎧", "💬"],
                ["#️⃣", "🆘", "📃", "⏯️", "🎹"]
            ]
            app.send_message(
                callback_query.message.chat.id,
                "🔣 Emoji keyboard activated!",
                reply_markup=ReplyKeyboardMarkup(emoji_keyboard, resize_keyboard=True)
            )

        # Log the action
        send_to_logger(callback_query.message, f"User {user_id} set keyboard to {setting}")

    except Exception as e:
        callback_query.answer("Error processing setting", show_alert=True)
        from HELPERS.logger import logger
        logger.error(f"Error processing keyboard setting: {e}")
