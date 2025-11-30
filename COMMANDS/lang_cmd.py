"""
Language Selection Command
Handles /lang command for user language selection
"""

import sys
import os

# Add the parent directory to the path to import CONFIG
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from CONFIG.LANGUAGES.language_router import language_router, get_messages, set_user_language
except ImportError:
    # Fallback for development
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'CONFIG', 'LANGUAGES'))
    from language_router import language_router, get_messages, set_user_language # type: ignore

def lang_command_handler(update, context):
    """
    Handle /lang command - show language selection menu or quick language switch
    """
    user_id = update.effective_user.id
    
    # Parse command arguments
    args = context.args
    
    # Check if language argument is provided
    if args and len(args) >= 1:
        lang_arg = args[0].lower()
        
        # Supported language codes
        supported_langs = {
            'en': 'English',
            'ru': 'Русский', 
            'ar': 'العربية',
            'in': 'हिन्दी'
        }
        
        if lang_arg in supported_langs:
            # Quick language switch
            success = set_user_language(user_id, lang_arg)
            
            if success:
                # Get messages in new language
                new_messages = get_messages(language_code=lang_arg)
                lang_name = supported_langs[lang_arg]
                
                # Send confirmation message
                confirmation_msg = getattr(new_messages, 'LANG_CHANGED_MSG', 
                    f"✅ Language changed to {lang_name}"
                )
                
                # Format the message with lang_name
                if '{lang_name}' in confirmation_msg:
                    confirmation_msg = confirmation_msg.format(lang_name=lang_name)
                
                update.message.reply_text(
                    confirmation_msg,
                    parse_mode='HTML'
                )
            else:
                # Get current messages for error
                messages = get_messages(user_id)
                error_msg = getattr(messages, 'LANG_ERROR_MSG', 
                    "❌ Error changing language"
                )
                update.message.reply_text(error_msg)
            return
        else:
            # Invalid language code
            messages = get_messages(user_id)
            error_msg = getattr(messages, 'LANG_INVALID_ARGUMENT_MSG', 
                "❌ Invalid language code. Supported: en, ru, ar, in"
            )
            update.message.reply_text(error_msg)
            return
    
    # No arguments - show language selection menu
    # Get messages in current user's language
    messages = get_messages(user_id)
    
    # Create language selection keyboard
    keyboard = []
    available_languages = language_router.get_available_languages()
    
    # Create buttons for each language (2 per row)
    lang_items = list(available_languages.items())
    for i in range(0, len(lang_items), 2):
        row = []
        for j in range(2):
            if i + j < len(lang_items):
                lang_code, lang_name = lang_items[i + j]
                row.append({
                    'text': lang_name,
                    'callback_data': f'lang_select_{lang_code}'
                })
        keyboard.append(row)
    
    # Add close button
    keyboard.append([{
        'text': getattr(messages, 'BTN_CLOSE', '🔚Close'),
        'callback_data': 'lang_close'
    }])
    
    reply_markup = {
        'inline_keyboard': keyboard
    }
    
    # Send language selection message
    lang_selection_msg = getattr(messages, 'LANG_SELECTION_MSG', 
        "🌍 <b>Выберите язык / Select Language</b>\n\n"
        "🇺🇸 English\n"
        "🇷🇺 Русский\n" 
        "🇸🇦 العربية\n"
        "🇮🇳 हिन्दी"
    )
    
    update.message.reply_text(
        lang_selection_msg,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

def lang_command(app, message):
    """
    Handle /lang command for pyrogram - show language selection menu or quick language switch
    """
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from HELPERS.safe_messeger import safe_send_message
    from CONFIG.messages import safe_get_messages
    from pyrogram import enums
    
    user_id = message.chat.id
    
    # Parse command arguments
    parts = (message.text or "").split()
    
    # Check if language argument is provided
    if len(parts) >= 2:
        lang_arg = parts[1].lower()
        
        # Supported language codes
        supported_langs = {
            'en': 'English',
            'ru': 'Русский', 
            'ar': 'العربية',
            'in': 'हिन्दी'
        }
        
        if lang_arg in supported_langs:
            # Quick language switch
            success = set_user_language(user_id, lang_arg)
            
            if success:
                # Get messages in new language
                new_messages = safe_get_messages(user_id)
                lang_name = supported_langs[lang_arg]
                
                # Send confirmation message
                confirmation_msg = getattr(new_messages, 'LANG_CHANGED_MSG', 
                    f"✅ Language changed to {lang_name}"
                )
                
                # Format the message with lang_name
                if '{lang_name}' in confirmation_msg:
                    confirmation_msg = confirmation_msg.format(lang_name=lang_name)
                
                safe_send_message(
                    user_id,
                    confirmation_msg,
                    parse_mode=enums.ParseMode.HTML,
                    message=message
                )
            else:
                # Get current messages for error
                messages = safe_get_messages(user_id)
                error_msg = getattr(messages, 'LANG_ERROR_MSG', 
                    "❌ Error changing language"
                )
                safe_send_message(user_id, error_msg, message=message)
            return
        else:
            # Invalid language code
            messages = safe_get_messages(user_id)
            error_msg = getattr(messages, 'LANG_INVALID_ARGUMENT_MSG', 
                "❌ Invalid language code. Supported: en, ru, ar, in"
            )
            safe_send_message(user_id, error_msg, message=message)
            return
    
    # No arguments - show language selection menu
    # Get messages in current user's language
    messages = safe_get_messages(user_id)
    
    # Create language selection keyboard
    keyboard = []
    available_languages = language_router.get_available_languages()
    
    # Create buttons for each language (2 per row)
    lang_items = list(available_languages.items())
    for i in range(0, len(lang_items), 2):
        row = []
        for j in range(2):
            if i + j < len(lang_items):
                lang_code, lang_name = lang_items[i + j]
                row.append(InlineKeyboardButton(
                    text=lang_name,
                    callback_data=f'lang_select_{lang_code}'
                ))
        keyboard.append(row)
    
    # Add close button
    keyboard.append([InlineKeyboardButton(
        text=getattr(messages, 'BTN_CLOSE', '🔚Close'),
        callback_data='lang_close'
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send language selection message
    lang_selection_msg = getattr(messages, 'LANG_SELECTION_MSG', 
        "🌍 <b>Выберите язык / Select Language</b>\n\n"
        "🇺🇸 English\n"
        "🇷🇺 Русский\n" 
        "🇸🇦 العربية\n"
        "🇮🇳 हिन्दी"
    )
    
    safe_send_message(
        message.chat.id,
        lang_selection_msg,
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML,
        message=message
    )

def lang_callback_handler(update, context):
    """
    Handle language selection callback
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get current user's language for messages
    messages = get_messages(user_id)
    
    if query.data.startswith('lang_select_'):
        # Extract language code
        lang_code = query.data.replace('lang_select_', '')
        
        # Set user language
        success = set_user_language(user_id, lang_code)
        
        if success:
            # Get messages in new language
            new_messages = get_messages(language_code=lang_code)
            
            # Get language name
            available_languages = language_router.get_available_languages()
            lang_name = available_languages.get(lang_code, lang_code)
            
            # Send confirmation message
            confirmation_msg = getattr(new_messages, 'LANG_CHANGED_MSG', 
                f"✅ Language changed to {lang_name}"
            )
            
            # Format the message with lang_name
            if '{lang_name}' in confirmation_msg:
                confirmation_msg = confirmation_msg.format(lang_name=lang_name)
            
            query.answer(confirmation_msg)
            query.edit_message_text(
                confirmation_msg,
                parse_mode='HTML'
            )
        else:
            error_msg = getattr(messages, 'LANG_ERROR_MSG', 
                "❌ Error changing language"
            )
            query.answer(error_msg)
            
    elif query.data == 'lang_close':
        # Close language selection
        close_msg = getattr(messages, 'LANG_CLOSED_MSG', "Language selection closed")
        query.answer(close_msg)
        query.edit_message_text(close_msg)

def register_lang_handlers(application):
    """
    Register language command handlers
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler
    
    # Register command handler
    application.add_handler(CommandHandler("lang", lang_command_handler))
    
    # Register callback handler
    application.add_handler(CallbackQueryHandler(lang_callback_handler, pattern=r'^lang_'))
