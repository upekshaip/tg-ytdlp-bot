# /Proxy Command
import os
import tempfile
from pyrogram import filters
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger, send_to_all
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from HELPERS.decorators import background_handler
from HELPERS.limitter import is_user_in_channel

# Get app instance for decorators
app = get_app()

def safe_write_file(file_path, content):
    """Safely write content to file with atomic operation"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to temporary file first, then rename (atomic operation)
        temp_dir = os.path.dirname(file_path)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=temp_dir, delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            temp_path = temp_file.name
        
        # Atomic rename
        os.rename(temp_path, file_path)
        return True
    except OSError as e:
        logger.error(LoggerMsg.PROXY_CMD_ERROR_WRITING_FILE_LOG_MSG.format(file_path=file_path, error=e))
        # Clean up temp file if it exists
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(LoggerMsg.PROXY_CMD_UNEXPECTED_ERROR_WRITING_FILE_LOG_MSG.format(file_path=file_path, error=e))
        return False

@app.on_message(filters.command("proxy") & filters.private)
@background_handler(label="proxy_command")
def proxy_command(app, message):
    messages = safe_get_messages(message.chat.id)
    user_id = message.chat.id
    logger.info(LoggerMsg.PROXY_CMD_USER_REQUESTED_LOG_MSG.format(user_id=user_id))
    logger.info(LoggerMsg.PROXY_CMD_USER_IS_ADMIN_LOG_MSG.format(user_id=user_id, is_admin=int(user_id) in Config.ADMIN))
    
    is_in_channel = is_user_in_channel(app, message)
    logger.info(LoggerMsg.PROXY_CMD_USER_IS_IN_CHANNEL_LOG_MSG.format(user_id=user_id, is_in_channel=is_in_channel))
    
    if int(user_id) not in Config.ADMIN and not is_in_channel:
        logger.info(LoggerMsg.PROXY_CMD_USER_ACCESS_DENIED_LOG_MSG.format(user_id=user_id))
        return
    
    logger.info(LoggerMsg.PROXY_CMD_USER_ACCESS_GRANTED_LOG_MSG.format(user_id=user_id))
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    
    # Fast toggle via args: /proxy on|off
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            arg = parts[1].lower()
            proxy_file = os.path.join(user_dir, "proxy.txt")
            if arg in ("on", "off"):
                if safe_write_file(proxy_file, "ON" if arg == "on" else "OFF"):
                    safe_send_message(user_id, safe_get_messages(user_id).PROXY_ENABLED_MSG.format(status='enabled' if arg=='on' else 'disabled'), message=message)
                    send_to_logger(message, safe_get_messages(user_id).PROXY_SET_COMMAND_LOG_MSG.format(arg=arg))
                    return
                else:
                    error_msg = safe_get_messages(user_id).PROXY_ERROR_SAVING_MSG
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
    except Exception:
        pass
    
    buttons = [
        [InlineKeyboardButton(safe_get_messages(user_id).PROXY_ON_BUTTON_MSG, callback_data="proxy_option|on"), InlineKeyboardButton(safe_get_messages(user_id).PROXY_OFF_BUTTON_MSG, callback_data="proxy_option|off")],
        [InlineKeyboardButton(safe_get_messages(user_id).PROXY_CLOSE_BUTTON_MSG, callback_data="proxy_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    # Get available proxy count
    configs = get_all_proxy_configs()
    proxy_count = len(configs)
    
    if proxy_count and proxy_count > 1:
        proxy_text = safe_get_messages(user_id).PROXY_MENU_TEXT_MULTIPLE_MSG.format(count=proxy_count, method=Config.PROXY_SELECT)
    else:
        proxy_text = safe_get_messages(user_id).PROXY_MENU_TEXT_MSG
    
    safe_send_message(
        user_id,
        proxy_text,
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, safe_get_messages(user_id).PROXY_MENU_OPENED_LOG_MSG)


@app.on_callback_query(filters.regex(r"^proxy_option\|"))
def proxy_option_callback(app, callback_query):
    user_id = callback_query.from_user.id
    messages = safe_get_messages(user_id)
    logger.info(LoggerMsg.PROXY_CMD_CALLBACK_LOG_MSG.format(callback_data=callback_query.data))
    data = callback_query.data.split("|")[1]
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    proxy_file = os.path.join(user_dir, "proxy.txt")
    
    if callback_query.data == "proxy_option|close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer(safe_get_messages(user_id).PROXY_MENU_CLOSED_MSG)
        except Exception:
            pass
        send_to_logger(callback_query.message, safe_get_messages(user_id).PROXY_MENU_CLOSED_LOG_MSG)
        return
    
    if data == "on":
        if not safe_write_file(proxy_file, "ON"):
            try:
                callback_query.answer(safe_get_messages(user_id).PROXY_ERROR_SAVING_CALLBACK_MSG)
            except Exception:
                pass
            return
        
        # Get available proxy count and selection method
        configs = get_all_proxy_configs()
        proxy_count = len(configs)
        
        if proxy_count and proxy_count > 1:
            message_text = safe_get_messages(user_id).PROXY_ENABLED_MULTIPLE_MSG.format(count=proxy_count, method=Config.PROXY_SELECT)
        else:
            message_text = safe_get_messages(user_id).PROXY_ENABLED_CONFIRM_MSG
        
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, message_text)
        send_to_logger(callback_query.message, safe_get_messages(user_id).PROXY_ENABLED_LOG_MSG)
        try:
            callback_query.answer(safe_get_messages(user_id).PROXY_ENABLED_CALLBACK_MSG)
        except Exception:
            pass
        return
    
    if data == "off":
        if not safe_write_file(proxy_file, "OFF"):
            try:
                callback_query.answer(safe_get_messages(user_id).PROXY_ERROR_SAVING_CALLBACK_MSG)
            except Exception:
                pass
            return
        
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, safe_get_messages(user_id).PROXY_DISABLED_MSG)
        send_to_logger(callback_query.message, safe_get_messages(user_id).PROXY_DISABLED_LOG_MSG)
        try:
            callback_query.answer(safe_get_messages(user_id).PROXY_DISABLED_CALLBACK_MSG)
        except Exception:
            pass
        return


def is_proxy_enabled(user_id):
    messages = safe_get_messages(user_id)
    """Check if proxy is enabled for user"""
    user_dir = os.path.join("users", str(user_id))
    proxy_file = os.path.join(user_dir, "proxy.txt")
    if not os.path.exists(proxy_file):
        return False
    try:
        with open(proxy_file, "r", encoding="utf-8") as f:
            content = f.read().strip().upper()
            return content == "ON"
    except OSError as e:
        logger.error(LoggerMsg.PROXY_CMD_ERROR_READING_FILE_LOG_MSG.format(proxy_file=proxy_file, error=e))
        return False
    except Exception as e:
        logger.error(LoggerMsg.PROXY_CMD_UNEXPECTED_ERROR_READING_FILE_LOG_MSG.format(proxy_file=proxy_file, error=e))
        return False


def get_proxy_config():
    """Get proxy configuration from config"""
    return {
        'type': Config.PROXY_TYPE,
        'ip': Config.PROXY_IP,
        'port': Config.PROXY_PORT,
        'user': Config.PROXY_USER,
        'password': Config.PROXY_PASSWORD
    }

def get_proxy_2_config():
    """Get second proxy configuration from config"""
    return {
        'type': Config.PROXY_2_TYPE,
        'ip': Config.PROXY_2_IP,
        'port': Config.PROXY_2_PORT,
        'user': Config.PROXY_2_USER,
        'password': Config.PROXY_2_PASSWORD
    }

def get_all_proxy_configs():
    """Get all available proxy configurations"""
    configs = []
    
    # First proxy
    if hasattr(Config, 'PROXY_TYPE') and hasattr(Config, 'PROXY_IP') and hasattr(Config, 'PROXY_PORT'):
        if Config.PROXY_IP and Config.PROXY_PORT:
            configs.append({
                'type': Config.PROXY_TYPE,
                'ip': Config.PROXY_IP,
                'port': Config.PROXY_PORT,
                'user': Config.PROXY_USER,
                'password': Config.PROXY_PASSWORD
            })
    
    # Second proxy
    if hasattr(Config, 'PROXY_2_TYPE') and hasattr(Config, 'PROXY_2_IP') and hasattr(Config, 'PROXY_2_PORT'):
        if Config.PROXY_2_IP and Config.PROXY_2_PORT:
            configs.append({
                'type': Config.PROXY_2_TYPE,
                'ip': Config.PROXY_2_IP,
                'port': Config.PROXY_2_PORT,
                'user': Config.PROXY_2_USER,
                'password': Config.PROXY_2_PASSWORD
            })
    
    return configs

def select_proxy_for_user():
    """Select proxy for user based on PROXY_SELECT method"""
    import random
    
    configs = get_all_proxy_configs()
    if not configs:
        return None
    
    if len(configs) == 1:
        return configs[0]
    
    # Select method based on PROXY_SELECT
    if hasattr(Config, 'PROXY_SELECT') and Config.PROXY_SELECT == "random":
        return random.choice(configs)
    else:  # default to round_robin
        # Simple round-robin using a global counter
        if not hasattr(select_proxy_for_user, 'counter'):
            select_proxy_for_user.counter = 0
        selected = configs[select_proxy_for_user.counter % len(configs)]
        select_proxy_for_user.counter += 1
        return selected


def build_proxy_url(proxy_config):
    """Build proxy URL from configuration"""
    if not proxy_config or 'type' not in proxy_config or 'ip' not in proxy_config or 'port' not in proxy_config:
        return None
    
    if proxy_config['type'] == 'http':
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"http://{proxy_config['ip']}:{proxy_config['port']}"
    elif proxy_config['type'] == 'https':
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"https://{proxy_config['ip']}:{proxy_config['port']}"
    elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
    else:
        if proxy_config.get('user') and proxy_config.get('password'):
            return f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
        else:
            return f"http://{proxy_config['ip']}:{proxy_config['port']}"

def select_proxy_for_domain(url):
    """Select appropriate proxy for domain based on PROXY_DOMAINS and PROXY_2_DOMAINS"""
    from CONFIG.domains import DomainsConfig
    
    # Extract domain from URL
    domain = None
    if '://' in url:
        domain = url.split('://')[1].split('/')[0]
    else:
        domain = url.split('/')[0]
    
    logger.info(LoggerMsg.PROXY_CMD_SELECT_PROXY_FOR_DOMAIN_LOG_MSG.format(url=url, domain=domain))
    logger.info(LoggerMsg.PROXY_CMD_PROXY_2_DOMAINS_LOG_MSG.format(domains=getattr(DomainsConfig, 'PROXY_2_DOMAINS', [])))
    logger.info(LoggerMsg.PROXY_CMD_PROXY_DOMAINS_LOG_MSG.format(domains=getattr(DomainsConfig, 'PROXY_DOMAINS', [])))
    
    # Helper function to check if domain matches any domain in the list (including subdomains)
    def is_domain_in_list(domain, domain_list):
        """Check if domain or any of its subdomains match entries in domain_list"""
        if not domain_list:
            return False
        
        # Direct match
        if domain in domain_list:
            return True
        
        # Check if any domain in the list is a subdomain of the current domain
        for listed_domain in domain_list:
            if domain.endswith('.' + listed_domain) or domain == listed_domain:
                return True
        
        return False
    
    # Check PROXY_2_DOMAINS first
    if hasattr(DomainsConfig, 'PROXY_2_DOMAINS') and DomainsConfig.PROXY_2_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_2_DOMAINS):
            logger.info(LoggerMsg.PROXY_CMD_DOMAIN_FOUND_IN_PROXY_2_LOG_MSG.format(domain=domain))
            return get_proxy_2_config()
    
    # Check PROXY_DOMAINS
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS):
            logger.info(LoggerMsg.PROXY_CMD_DOMAIN_FOUND_IN_PROXY_1_LOG_MSG.format(domain=domain))
            return get_proxy_config()
    
    logger.info(LoggerMsg.PROXY_CMD_DOMAIN_NOT_IN_LIST_LOG_MSG.format(domain=domain))
    return None

def resolve_proxy_config(user_id=None, url=None, allow_domain_fallback=True):
    """
    Determine which proxy configuration should be used for the current context.
    Priority:
    1. User-specific proxy toggle (/proxy on)
    2. Domain-specific proxy lists (if enabled and allowed)
    """
    reason = None
    proxy_config = None
    
    if user_id is not None:
        try:
            proxy_enabled = is_proxy_enabled(user_id)
            logger.info(LoggerMsg.PROXY_CMD_PROXY_CHECK_FOR_USER_LOG_MSG.format(user_id=user_id, proxy_enabled=proxy_enabled))
            if proxy_enabled:
                proxy_config = select_proxy_for_user()
                reason = "user"
        except Exception as e:
            logger.warning(LoggerMsg.PROXY_CMD_ERROR_CHECKING_PROXY_LOG_MSG.format(user_id=user_id, error=e))
    
    if proxy_config is None and allow_domain_fallback and url:
        proxy_config = select_proxy_for_domain(url)
        if proxy_config:
            reason = "domain"
    
    return proxy_config, reason


def get_proxy_url(user_id=None, url=None, allow_domain_fallback=True):
    """Return proxy URL string for current context or None."""
    proxy_config, reason = resolve_proxy_config(user_id, url, allow_domain_fallback)
    if not proxy_config:
        return None, None
    proxy_url = build_proxy_url(proxy_config)
    if not proxy_url:
        return None, None
    return proxy_url, reason


def get_requests_proxies(user_id=None, url=None, allow_domain_fallback=True):
    """
    Build a proxies dict suitable for requests when proxy mode is enabled.
    Returns dict or None.
    """
    proxy_url, reason = get_proxy_url(user_id, url, allow_domain_fallback)
    if not proxy_url:
        return None, None
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
        'HTTP': proxy_url,
        'HTTPS': proxy_url,
    }
    return proxies, reason


def add_proxy_to_ytdl_opts(ytdl_opts, url, user_id=None, allow_domain_fallback=True):
    """Add proxy to yt-dlp options if proxy is enabled for user or domain requires it"""
    logger.info(LoggerMsg.PROXY_CMD_ADD_PROXY_CALLED_LOG_MSG.format(user_id=user_id, url=url))
    
    proxy_url, reason = get_proxy_url(user_id=user_id, url=url, allow_domain_fallback=allow_domain_fallback)
    if proxy_url:
        ytdl_opts['proxy'] = proxy_url
        if reason == "user":
            logger.info(LoggerMsg.PROXY_CMD_ADDED_PROXY_FOR_USER_LOG_MSG.format(user_id=user_id, proxy_url=proxy_url))
        else:
            logger.info(LoggerMsg.PROXY_CMD_ADDED_DOMAIN_PROXY_LOG_MSG.format(url=url, proxy_url=proxy_url))
    
    return ytdl_opts
