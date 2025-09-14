# ####################################################################################
# Args Command - Interactive yt-dlp parameters configuration
# ####################################################################################

import os
import json
import re
from typing import Dict, Any, Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters
from pyrogram import enums

from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user, send_error_to_user
from HELPERS.limitter import check_user, is_user_in_channel
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config

# Get app instance
app = get_app()

# Global dictionary to track user input states
user_input_states = {}  # {user_id: {"param": param_name, "type": param_type}}

# File to store user args settings
ARGS_FILE = "args.txt"

# Available yt-dlp parameters with their types and options
YTDLP_PARAMS = {
    "impersonate": {
        "type": "select",
        "description": "Browser impersonation",
        "options": ["chrome", "firefox", "safari", "edge", "opera"],
        "default": "chrome"
    },
    "referer": {
        "type": "text",
        "description": "Referer header",
        "placeholder": "https://example.com",
        "default": "",
        "validation": "url"
    },
    "user_agent": {
        "type": "text", 
        "description": "User-Agent header",
        "placeholder": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "default": "",
        "validation": "text"
    },
    "geo_bypass": {
        "type": "boolean",
        "description": "Bypass geographic restrictions",
        "default": True
    },
    "check_certificate": {
        "type": "boolean", 
        "description": "Check SSL certificate",
        "default": False
    },
    "live_from_start": {
        "type": "boolean",
        "description": "Download live streams from start",
        "default": True
    },
    "http_headers": {
        "type": "json",
        "description": "Custom HTTP headers (JSON)",
        "placeholder": '{"Authorization": "Bearer token", "X-API-Key": "key123"}',
        "default": "{}",
        "validation": "json"
    },
    "sleep_interval": {
        "type": "number",
        "description": "Sleep interval between requests (seconds)",
        "placeholder": "1",
        "default": 1,
        "min": 0,
        "max": 60
    },
    "max_sleep_interval": {
        "type": "number", 
        "description": "Maximum sleep interval (seconds)",
        "placeholder": "5",
        "default": 5,
        "min": 0,
        "max": 300
    },
    "retries": {
        "type": "number",
        "description": "Number of retries",
        "placeholder": "10",
        "default": 10,
        "min": 0,
        "max": 50
    }
}

def validate_input(value: str, param_name: str) -> tuple[bool, str]:
    """
    Validate user input based on parameter type and constraints
    Returns (is_valid, error_message)
    """
    param_config = YTDLP_PARAMS.get(param_name, {})
    validation_type = param_config.get("validation", "text")
    
    # Basic security checks - prevent SQL injection and other attacks
    dangerous_patterns = [
        r'[;\'"\\]',  # SQL injection patterns
        r'<script',   # XSS
        r'javascript:', # XSS
        r'data:',     # Data URI attacks
        r'vbscript:', # VBScript attacks
        r'<iframe',   # iframe injection
        r'<object',   # object injection
        r'<embed',    # embed injection
        r'<form',     # form injection
        r'<input',    # input injection
        r'<meta',     # meta injection
        r'<link',     # link injection
        r'<style',    # style injection
        r'<base',     # base injection
        r'<applet',   # applet injection
        r'<param',    # param injection
        r'<isindex',  # isindex injection
        r'<textarea', # textarea injection
        r'<select',   # select injection
        r'<option',   # option injection
        r'<button',   # button injection
        r'<fieldset', # fieldset injection
        r'<legend',   # legend injection
        r'<label',    # label injection
        r'<optgroup', # optgroup injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return False, f"❌ Input contains potentially dangerous content: {pattern}"
    
    # Length check
    if len(value) > 1000:
        return False, "❌ Input too long (max 1000 characters)"
    
    # Type-specific validation
    if validation_type == "url":
        if value and not re.match(r'^https?://[^\s]+$', value):
            return False, "❌ Invalid URL format. Must start with http:// or https://"
    
    elif validation_type == "json":
        if value:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return False, "❌ Invalid JSON format"
    
    elif validation_type == "number":
        try:
            num = float(value)
            min_val = param_config.get("min", 0)
            max_val = param_config.get("max", 999999)
            if num < min_val or num > max_val:
                return False, f"❌ Number must be between {min_val} and {max_val}"
        except ValueError:
            return False, "❌ Invalid number format"
    
    return True, ""

def get_user_args(user_id: int) -> Dict[str, Any]:
    """Get user's saved args settings"""
    user_dir = os.path.join("users", str(user_id))
    args_file = os.path.join(user_dir, ARGS_FILE)
    
    if not os.path.exists(args_file):
        return {}
    
    try:
        with open(args_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading user args for {user_id}: {e}")
        return {}

def save_user_args(user_id: int, args: Dict[str, Any]) -> bool:
    """Save user's args settings"""
    try:
        user_dir = os.path.join("users", str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        args_file = os.path.join(user_dir, ARGS_FILE)
        with open(args_file, 'w', encoding='utf-8') as f:
            json.dump(args, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving user args for {user_id}: {e}")
        return False

def get_args_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate main args menu keyboard"""
    user_args = get_user_args(user_id)
    
    buttons = []
    for param_name, param_config in YTDLP_PARAMS.items():
        current_value = user_args.get(param_name, param_config.get("default", ""))
        
        if param_config["type"] == "boolean":
            status = "✅" if current_value else "❌"
        elif param_config["type"] == "select":
            status = f"📋 {current_value}"
        elif param_config["type"] == "text":
            status = "📝" if current_value else "📝"
        elif param_config["type"] == "json":
            status = "🔧" if current_value and current_value != "{}" else "🔧"
        elif param_config["type"] == "number":
            status = f"🔢 {current_value}"
        else:
            status = "⚙️"
        
        buttons.append([InlineKeyboardButton(
            f"{status} {param_config['description']}",
            callback_data=f"args_set_{param_name}"
        )])
    
    # Add control buttons
    buttons.append([InlineKeyboardButton("🔄 Reset All", callback_data="args_reset_all")])
    buttons.append([InlineKeyboardButton("📋 View Current", callback_data="args_view_current")])
    buttons.append([InlineKeyboardButton("🔚 Close", callback_data="args_close")])
    
    return InlineKeyboardMarkup(buttons)

def get_boolean_menu_keyboard(param_name: str, current_value: bool) -> InlineKeyboardMarkup:
    """Generate boolean parameter menu keyboard"""
    buttons = [
        [InlineKeyboardButton(
            "✅ True",
            callback_data=f"args_bool_{param_name}_true"
        )],
        [InlineKeyboardButton(
            "❌ False", 
            callback_data=f"args_bool_{param_name}_false"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data="args_back")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_select_menu_keyboard(param_name: str, current_value: str) -> InlineKeyboardMarkup:
    """Generate select parameter menu keyboard"""
    param_config = YTDLP_PARAMS[param_name]
    options = param_config["options"]
    
    buttons = []
    for option in options:
        status = "✅" if option == current_value else "⚪"
        buttons.append([InlineKeyboardButton(
            f"{status} {option}",
            callback_data=f"args_select_{param_name}_{option}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="args_back")])
    return InlineKeyboardMarkup(buttons)

def get_text_input_message(param_name: str, current_value: str) -> str:
    """Generate text input message"""
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "")
    
    message = f"<b>📝 {param_config['description']}</b>\n\n"
    if current_value:
        message += f"<b>Current value:</b> <code>{current_value}</code>\n\n"
    if placeholder:
        message += f"<b>Example:</b> <code>{placeholder}</code>\n\n"
    message += "Please send your new value."
    
    return message

def get_number_input_message(param_name: str, current_value: Any) -> str:
    """Generate number input message"""
    param_config = YTDLP_PARAMS[param_name]
    min_val = param_config.get("min", 0)
    max_val = param_config.get("max", 999999)
    
    message = f"<b>🔢 {param_config['description']}</b>\n\n"
    if current_value is not None:
        message += f"<b>Current value:</b> <code>{current_value}</code>\n\n"
    message += f"<b>Range:</b> {min_val} - {max_val}\n\n"
    message += "Please send a number."
    
    return message

def get_json_input_message(param_name: str, current_value: str) -> str:
    """Generate JSON input message"""
    param_config = YTDLP_PARAMS[param_name]
    placeholder = param_config.get("placeholder", "{}")
    
    message = f"<b>🔧 {param_config['description']}</b>\n\n"
    if current_value and current_value != "{}":
        message += f"<b>Current value:</b>\n<code>{current_value}</code>\n\n"
    
    if param_name == "http_headers":
        message += f"<b>Examples:</b>\n"
        message += f"<code>{placeholder}</code>\n"
        message += f"<code>{{\"X-API-Key\": \"your-key\"}}</code>\n"
        message += f"<code>{{\"Authorization\": \"Bearer token\"}}</code>\n"
        message += f"<code>{{\"Accept\": \"application/json\"}}</code>\n"
        message += f"<code>{{\"X-Custom-Header\": \"value\"}}</code>\n\n"
        message += "<b>Note:</b> These headers will be added to existing Referer and User-Agent headers.\n\n"
    else:
        message += f"<b>Example:</b>\n<code>{placeholder}</code>\n\n"
    
    message += "Please send valid JSON."
    
    return message

def format_current_args(user_args: Dict[str, Any]) -> str:
    """Format current args for display"""
    if not user_args:
        return "No custom arguments set. All parameters use default values."
    
    message = "<b>📋 Current yt-dlp Arguments:</b>\n\n"
    
    for param_name, value in user_args.items():
        param_config = YTDLP_PARAMS.get(param_name, {})
        description = param_config.get("description", param_name)
        
        if isinstance(value, bool):
            display_value = "✅ True" if value else "❌ False"
        elif isinstance(value, (int, float)):
            display_value = str(value)
        else:
            display_value = str(value) if value else "Not set"
        
        message += f"<b>{description}:</b> <code>{display_value}</code>\n"
    
    return message

@app.on_message(filters.command("args") & filters.private)
def args_command(app, message):
    """Handle /args command"""
    user_id = message.chat.id
    
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return  # is_user_in_channel already sends subscription message
    
    # Create user directory after subscription check
    user_dir = os.path.join("users", str(user_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    keyboard = get_args_menu_keyboard(user_id)
    
    safe_send_message(
        user_id,
        "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
        "Configure custom parameters for yt-dlp downloads.\n"
        "These settings will be applied to all your downloads.",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^args_"))
def args_callback_handler(app, callback_query):
    """Handle args menu callbacks"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    try:
        if data == "args_close":
            callback_query.message.delete()
            callback_query.answer("Closed")
            return
        
        elif data == "args_back":
            # Clear user input state if exists
            if user_id in user_input_states:
                del user_input_states[user_id]
            
            keyboard = get_args_menu_keyboard(user_id)
            callback_query.edit_message_text(
                "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
                "Configure custom parameters for yt-dlp downloads.\n"
                "These settings will be applied to all your downloads.",
                reply_markup=keyboard
            )
            callback_query.answer()
            return
        
        elif data == "args_view_current":
            user_args = get_user_args(user_id)
            message = format_current_args(user_args)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="args_back")
            ]])
            callback_query.edit_message_text(message, reply_markup=keyboard)
            callback_query.answer()
            return
        
        elif data == "args_reset_all":
            if save_user_args(user_id, {}):
                keyboard = get_args_menu_keyboard(user_id)
                callback_query.edit_message_text(
                    "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
                    "✅ All arguments reset to defaults.\n\n"
                    "Configure custom parameters for yt-dlp downloads.\n"
                    "These settings will be applied to all your downloads.",
                    reply_markup=keyboard
                )
                callback_query.answer("✅ All arguments reset")
            else:
                callback_query.answer("❌ Error resetting arguments", show_alert=True)
            return
        
        elif data.startswith("args_set_"):
            param_name = data.replace("args_set_", "")
            if param_name not in YTDLP_PARAMS:
                callback_query.answer("❌ Invalid parameter", show_alert=True)
                return
            
            param_config = YTDLP_PARAMS[param_name]
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, param_config.get("default", ""))
            
            if param_config["type"] == "boolean":
                keyboard = get_boolean_menu_keyboard(param_name, current_value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {param_config['description']}</b>\n\n"
                    f"Current value: {'✅ True' if current_value else '❌ False'}",
                    reply_markup=keyboard
                )
            
            elif param_config["type"] == "select":
                keyboard = get_select_menu_keyboard(param_name, current_value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {param_config['description']}</b>\n\n"
                    f"Current value: <code>{current_value}</code>",
                    reply_markup=keyboard
                )
            
            elif param_config["type"] in ["text", "json", "number"]:
                # Set user input state
                user_input_states[user_id] = {
                    "param": param_name,
                    "type": param_config["type"]
                }
                
                if param_config["type"] == "text":
                    message = get_text_input_message(param_name, current_value)
                elif param_config["type"] == "json":
                    message = get_json_input_message(param_name, current_value)
                else:  # number
                    message = get_number_input_message(param_name, current_value)
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="args_back")
                ]])
                callback_query.edit_message_text(message, reply_markup=keyboard)
            
            callback_query.answer()
            return
        
        elif data.startswith("args_bool_"):
            # Parse: args_bool_{param_name}_{true/false}
            remaining = data.replace("args_bool_", "")
            if remaining.endswith("_true"):
                param_name = remaining[:-5]  # Remove "_true"
                value = True
            elif remaining.endswith("_false"):
                param_name = remaining[:-6]  # Remove "_false"
                value = False
            else:
                callback_query.answer("❌ Invalid boolean value", show_alert=True)
                return
            
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, YTDLP_PARAMS[param_name].get("default", False))
            
            # Always save the value (even if it's the same)
            user_args[param_name] = value
            save_user_args(user_id, user_args)
            
            # Only update message if value actually changed
            if current_value != value:
                keyboard = get_boolean_menu_keyboard(param_name, value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {YTDLP_PARAMS[param_name]['description']}</b>\n\n"
                    f"Current value: {'✅ True' if value else '❌ False'}",
                    reply_markup=keyboard
                )
                callback_query.answer(f"Set to {'True' if value else 'False'}")
            else:
                # Value is the same, just acknowledge
                callback_query.answer(f"Already set to {'True' if value else 'False'}")
            return
        
        elif data.startswith("args_select_"):
            # Parse: args_select_{param_name}_{value}
            remaining = data.replace("args_select_", "")
            # Find the last underscore to separate param_name and value
            last_underscore = remaining.rfind("_")
            if last_underscore == -1:
                callback_query.answer("❌ Invalid select value", show_alert=True)
                return
            param_name = remaining[:last_underscore]
            value = remaining[last_underscore + 1:]
            
            user_args = get_user_args(user_id)
            current_value = user_args.get(param_name, YTDLP_PARAMS[param_name].get("default", ""))
            
            # Always save the value (even if it's the same)
            user_args[param_name] = value
            save_user_args(user_id, user_args)
            
            # Only update message if value actually changed
            if current_value != value:
                keyboard = get_select_menu_keyboard(param_name, value)
                callback_query.edit_message_text(
                    f"<b>⚙️ {YTDLP_PARAMS[param_name]['description']}</b>\n\n"
                    f"Current value: <code>{value}</code>",
                    reply_markup=keyboard
                )
                callback_query.answer(f"Set to {value}")
            else:
                # Value is the same, just acknowledge
                callback_query.answer(f"Already set to {value}")
            return
        
    except Exception as e:
        logger.error(f"Error in args callback handler: {e}")
        callback_query.answer("❌ Error occurred", show_alert=True)

def handle_args_text_input(app, message):
    """Handle text input for args parameters"""
    user_id = message.chat.id
    text = message.text.strip()
    
    if user_id not in user_input_states:
        return
    
    state = user_input_states[user_id]
    param_name = state["param"]
    param_type = state["type"]
    
    try:
        # Validate and process input based on type
        if param_type == "text":
            # Basic validation for text input
            if len(text) > 500:
                error_msg = "❌ Text too long. Maximum 500 characters."
                safe_send_message(user_id, error_msg)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
            
            # Save the value
            user_args = get_user_args(user_id)
            user_args[param_name] = text
            save_user_args(user_id, user_args)
            
            # Clear state and show success
            del user_input_states[user_id]
            safe_send_message(
                user_id,
                f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{text}</code>",
                parse_mode=enums.ParseMode.HTML
            )
            
        elif param_type == "json":
            # Validate JSON input
            try:
                import json
                parsed_json = json.loads(text)
                if not isinstance(parsed_json, dict):
                    error_msg = "❌ JSON must be an object (dictionary)."
                    safe_send_message(user_id, error_msg)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
                
                # Save the value
                user_args = get_user_args(user_id)
                user_args[param_name] = text
                save_user_args(user_id, user_args)
                
                # Clear state and show success
                del user_input_states[user_id]
                safe_send_message(
                    user_id,
                    f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{text}</code>",
                    parse_mode=enums.ParseMode.HTML
                )
                
            except json.JSONDecodeError:
                error_msg = "❌ Invalid JSON format. Please provide valid JSON."
                safe_send_message(user_id, error_msg)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
                
        elif param_type == "number":
            # Validate number input
            try:
                value = int(text)
                param_config = YTDLP_PARAMS[param_name]
                min_val = param_config.get("min", 0)
                max_val = param_config.get("max", 999999)
                
                if value < min_val or value > max_val:
                    safe_send_message(
                        user_id,
                        f"❌ Value must be between {min_val} and {max_val}."
                    )
                    return
                
                # Save the value
                user_args = get_user_args(user_id)
                user_args[param_name] = value
                save_user_args(user_id, user_args)
                
                # Clear state and show success
                del user_input_states[user_id]
                safe_send_message(
                    user_id,
                    f"✅ {YTDLP_PARAMS[param_name]['description']} set to: <code>{value}</code>",
                    parse_mode=enums.ParseMode.HTML
                )
                
            except ValueError:
                error_msg = "❌ Please provide a valid number."
                safe_send_message(user_id, error_msg)
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                return
                
    except Exception as e:
        logger.error(f"Error handling args text input: {e}")
        error_msg = "❌ Error processing input. Please try again."
        safe_send_message(user_id, error_msg)
        from HELPERS.logger import log_error_to_channel
        log_error_to_channel(message, error_msg)
        # Clear state on error
        if user_id in user_input_states:
            del user_input_states[user_id]

@app.on_message(filters.text & filters.private)
def args_text_handler(app, message):
    """Handle text input for args configuration"""
    user_id = message.chat.id
    text = message.text.strip()
    
    # Check if user is in args input mode (we'll track this in a simple way)
    # For now, we'll check if the message is a reply to an args message
    if not message.reply_to_message:
        return
    
    reply_text = message.reply_to_message.text or ""
    if not reply_text.startswith("<b>📝") and not reply_text.startswith("<b>🔢") and not reply_text.startswith("<b>🔧"):
        return
    
    # Extract parameter name from the reply message
    # This is a simplified approach - in production you might want to store state
    param_name = None
    for pname, pconfig in YTDLP_PARAMS.items():
        if pconfig["description"] in reply_text:
            param_name = pname
            break
    
    if not param_name:
        send_error_to_user(message, "❌ Could not determine parameter. Please use the menu.")
        return
    
    
    # Validate input
    is_valid, error_msg = validate_input(text, param_name)
    if not is_valid:
        send_error_to_user(message, error_msg)
        return
    
    # Save the value
    user_args = get_user_args(user_id)
    param_config = YTDLP_PARAMS[param_name]
    
    if param_config["type"] == "number":
        try:
            user_args[param_name] = float(text)
        except ValueError:
            send_error_to_user(message, "❌ Invalid number format")
            return
    else:
        user_args[param_name] = text
    
    if save_user_args(user_id, user_args):
        # Show success and return to menu
        keyboard = get_args_menu_keyboard(user_id)
        app.edit_message_text(
            message.chat.id,
            message.reply_to_message.id,
            "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
            f"✅ {param_config['description']} set to: <code>{text}</code>\n\n"
            "Configure custom parameters for yt-dlp downloads.\n"
            "These settings will be applied to all your downloads.",
            reply_markup=keyboard
        )
        message.delete()
    else:
        send_error_to_user(message, "❌ Error saving setting")

def get_user_ytdlp_args(user_id: int, url: str = None) -> Dict[str, Any]:
    """Get user's yt-dlp arguments for use in download functions"""
    user_args = get_user_args(user_id)
    if not user_args:
        return {}
    
    # Convert user args to yt-dlp format
    ytdlp_args = {}
    
    for param_name, value in user_args.items():
        if param_name == "impersonate":
            ytdlp_args["extractor_args"] = ytdlp_args.get("extractor_args", {})
            ytdlp_args["extractor_args"]["generic"] = {"impersonate": [value]}
        
        elif param_name == "referer":
            if value:
                # For all services, use both http_headers and referer for maximum compatibility
                ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                ytdlp_args["http_headers"]["Referer"] = value
                ytdlp_args["referer"] = value
                logger.info(f"Setting Referer for all services: {value}")
        
        elif param_name == "user_agent":
            if value:
                ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                ytdlp_args["http_headers"]["User-Agent"] = value
        
        elif param_name == "http_headers":
            if value and value != "{}":
                try:
                    custom_headers = json.loads(value)
                    ytdlp_args["http_headers"] = ytdlp_args.get("http_headers", {})
                    ytdlp_args["http_headers"].update(custom_headers)
                except json.JSONDecodeError:
                    pass
        
        elif param_name in ["geo_bypass", "check_certificate", "live_from_start"]:
            ytdlp_args[param_name] = value
        
        elif param_name in ["sleep_interval", "max_sleep_interval", "retries"]:
            ytdlp_args[param_name] = int(value)
    
    return ytdlp_args

def log_ytdlp_options(user_id: int, ytdlp_opts: dict, operation: str = "download"):
    """Log the final yt-dlp options for debugging"""
    try:
        # Create a copy to avoid modifying the original
        opts_copy = ytdlp_opts.copy()
        
        # Remove sensitive information
        if 'cookiefile' in opts_copy:
            opts_copy['cookiefile'] = '[REDACTED]'
        
        # Format the options nicely
        import json
        opts_str = json.dumps(opts_copy, indent=2, ensure_ascii=False)
        
        logger.info(f"User {user_id} - Final yt-dlp options for {operation}:\n{opts_str}")
        
    except Exception as e:
        logger.error(f"Error logging yt-dlp options: {e}")
