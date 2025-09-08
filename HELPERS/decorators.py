# Decorators for automatic app usage
from functools import wraps
import os
# ####################################################################################
# Decorators for bot functionality
# ####################################################################################

from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.safe_messeger import safe_send_message

def app_handler(func):
    """Decorator to automatically inject app instance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # If first argument is not app, inject it
        if args and hasattr(args[0], 'send_message'):
            # First argument is already app
            return func(*args, **kwargs)
        else:
            # Inject app as first argument
            app = get_app()
            return func(app, *args, **kwargs)
    return wrapper
# Get app instance
app = get_app()

# eternal reply-keyboard and reliable work with files
reply_keyboard_msg_ids = {}  # user_id: message_id

def get_main_reply_keyboard(mode="2x3"):
    """Function for permanent reply-keyboard"""
    from pyrogram.types import ReplyKeyboardMarkup
    
    if mode == "1x3":
        keyboard = [
            ["/clean", "/cookie", "/settings"]
        ]
    elif mode == "FULL":
        keyboard = [
            ["🧹", "🍪", "⚙️", "🌐", "🖼", "🔍"],
            ["📼", "📊", "✂️", "🎧", "💬", "🌎"],
            ["#️⃣", "🆘", "📃", "⏯️", "🎹", "🔗"]
        ]
    else:  # 2x3 mode (default)
        keyboard = [
            ["/clean", "/cookie", "/settings"],
            ["/playlist", "/search", "/help"]
        ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def send_reply_keyboard_always(user_id, mode="2x3"):
    """Send persistent reply keyboard to user"""
    global reply_keyboard_msg_ids
    try:
        msg_id = reply_keyboard_msg_ids.get(user_id)
        if msg_id:
            try:
                app.edit_message_text(user_id, msg_id, "\u2063", reply_markup=get_main_reply_keyboard(mode))
                return
            except Exception as e:
                # Log only if the error is not MESSAGE_ID_INVALID
                if 'MESSAGE_ID_INVALID' not in str(e):
                    logger.warning(f"Failed to edit persistent reply keyboard: {e}")
                # If it didn't work, we delete the id to avoid getting stuck
                reply_keyboard_msg_ids.pop(user_id, None)
        # Always after failure or if there is no id - send a new one
        msg = safe_send_message(user_id, "\u2063", reply_markup=get_main_reply_keyboard(mode))
        # If sending failed (e.g., FloodWait), don't try to access msg.id
        if not msg or not hasattr(msg, "id"):
            return
        # If there was another service msg_id (and it is not equal to the new one), we try to delete the old message
        if msg_id and msg_id != msg.id:
            try:
                app.delete_messages(user_id, [msg_id])
            except Exception as e:
                logger.warning(f"Failed to delete old reply keyboard message: {e}")
        reply_keyboard_msg_ids[user_id] = msg.id
    except Exception as e:
        logger.warning(f"Failed to send persistent reply keyboard: {e}")

# Удаляем конфликтующую функцию on_message из decorators.py
# Она должна быть только в handler_registry.py 

def reply_with_keyboard(func):
    """Wrapper for any custom action that adds reply keyboard"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # Determine user_id from arguments (Pyrogram message/chat)
        user_id = None
        if 'message' in kwargs:
            user_id = getattr(kwargs['message'].chat, 'id', None)
        elif len(args) > 0 and hasattr(args[0], 'chat'):
            user_id = getattr(args[0].chat, 'id', None)
        elif len(args) > 1 and hasattr(args[1], 'chat'):
            user_id = getattr(args[1].chat, 'id', None)
        
        if user_id:
            # Check if keyboard is enabled for this user
            user_dir = f'./users/{user_id}'
            keyboard_file = f'{user_dir}/keyboard.txt'
            
            keyboard_enabled = True
            keyboard_mode = "2x3"  # Default mode
            
            if os.path.exists(keyboard_file):
                try:
                    with open(keyboard_file, 'r') as f:
                        setting = f.read().strip()
                        if setting == "OFF":
                            keyboard_enabled = False
                        elif setting in ["1x3", "2x3", "FULL"]:
                            keyboard_enabled = True
                            keyboard_mode = setting
                except:
                    pass
            
            # Only show keyboard if enabled and not /keyboard command
            if keyboard_enabled:
                # Check if this is a /keyboard command (exclude only /keyboard)
                is_keyboard_command = False
                if 'message' in kwargs and hasattr(kwargs['message'], 'text'):
                    is_keyboard_command = kwargs['message'].text == "/keyboard"
                elif len(args) > 1 and hasattr(args[1], 'text'):
                    is_keyboard_command = args[1].text == "/keyboard"
                
                if not is_keyboard_command:
                    send_reply_keyboard_always(user_id, keyboard_mode)
        
        return result

    return wrapper 

    