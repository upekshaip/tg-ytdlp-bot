# Search Command Module
# This module handles the /search command to activate inline search via @vid bot

from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_all, send_to_logger
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums, filters

# Get app instance
app = get_app()

def search_command(app, message):
    """
    Handle the /search command to activate inline search via @vid bot
    """
    user_id = message.chat.id

    # Get bot name from config
    bot_name = Config.BOT_NAME

    # Create inline keyboard with mobile button only
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📱 Mobile: Activate @vid search",
                url=f"tg://msg?text=%40vid%20%E2%80%8B&to=%40{bot_name}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔚Close",
                callback_data="search_msg|close"
            )
        ]
    ])

    # Send single message with updated instructions (English)
    text = (
        "🔍 <b>YouTube Video search</b>\n\n"
        "📱 <b>For mobile:</b> tap button below and type your search query after text @vid.\n\n"
        "💻 <b>For PC:</b> type <code>@vid Your_Search_Query</code> in any chat\n\n"
        "<blockquote>For example: <b>@vid funny cats</b></blockquote>"
    )

    app.send_message(
        message.chat.id,
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboard
    )

    # Log the action
    send_to_logger(message, f"User {user_id} opened search helper")

# Callback handler for search command buttons
@app.on_callback_query(filters.regex(r"^search_msg\|"))
def handle_search_callback(client, callback_query):
    """Handle search command callback queries"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if data == "search_msg|close":
            # Delete the message with search instructions
            try:
                client.delete_messages(
                    callback_query.message.chat.id,
                    callback_query.message.id
                )
            except Exception:
                # If can't delete, just edit to show closed message
                client.edit_message_text(
                    callback_query.message.chat.id,
                    callback_query.message.id,
                    "🔍 Search helper closed"
                )
            
            # Answer callback query
            callback_query.answer("Closed")
            
            # Log the action (pass message object, not callback_query)
            send_to_logger(callback_query.message, f"User {user_id} closed search command")
            
    except Exception as e:
        # Log error and answer callback
        send_to_logger(callback_query.message, f"Error in search callback handler: {e}")
        callback_query.answer("Error occurred", show_alert=True)
