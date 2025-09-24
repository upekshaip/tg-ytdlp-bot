# /Proxy Command
import os
import tempfile
from pyrogram import filters
from CONFIG.config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters

from HELPERS.app_instance import get_app
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_logger, logger, send_to_all
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
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
        logger.error(f"Error writing file {file_path}: {e}")
        # Clean up temp file if it exists
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Unexpected error writing file {file_path}: {e}")
        return False

@app.on_message(filters.command("proxy") & filters.private)
def proxy_command(app, message):
    user_id = message.chat.id
    logger.info(f"[PROXY] User {user_id} requested proxy command")
    logger.info(f"[PROXY] User {user_id} is admin: {int(user_id) in Config.ADMIN}")
    
    is_in_channel = is_user_in_channel(app, message)
    logger.info(f"[PROXY] User {user_id} is in channel: {is_in_channel}")
    
    if int(user_id) not in Config.ADMIN and not is_in_channel:
        logger.info(f"[PROXY] User {user_id} access denied - not admin and not in channel")
        return
    
    logger.info(f"[PROXY] User {user_id} access granted")
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
                    safe_send_message(user_id, f"✅ Proxy {'enabled' if arg=='on' else 'disabled' }.", message=message)
                    send_to_logger(message, f"Proxy set via command: {arg}")
                    return
                else:
                    error_msg = "❌ Error saving proxy settings."
                    safe_send_message(user_id, error_msg, message=message)
                    from HELPERS.logger import log_error_to_channel
                    log_error_to_channel(message, error_msg)
                    return
    except Exception:
        pass
    
    buttons = [
        [InlineKeyboardButton("✅ ON", callback_data="proxy_option|on"), InlineKeyboardButton("❌ OFF", callback_data="proxy_option|off")],
        [InlineKeyboardButton("🔚Close", callback_data="proxy_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    # Get available proxy count
    configs = get_all_proxy_configs()
    proxy_count = len(configs)
    
    if proxy_count > 1:
        proxy_text = f"Enable or disable using proxy servers ({proxy_count} available) for all yt-dlp operations?\n\nWhen enabled, proxies will be selected using {Config.PROXY_SELECT} method."
    else:
        proxy_text = "Enable or disable using proxy server for all yt-dlp operations?"
    
    safe_send_message(
        user_id,
        proxy_text,
        reply_markup=keyboard,
        message=message
    )
    send_to_logger(message, "User opened /proxy menu.")


@app.on_callback_query(filters.regex(r"^proxy_option\|"))
def proxy_option_callback(app, callback_query):
    logger.info(f"[PROXY] callback: {callback_query.data}")
    user_id = callback_query.from_user.id
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
            callback_query.answer("Menu closed.")
        except Exception:
            pass
        send_to_logger(callback_query.message, "Proxy: closed.")
        return
    
    if data == "on":
        if not safe_write_file(proxy_file, "ON"):
            try:
                callback_query.answer("❌ Error saving proxy settings.")
            except Exception:
                pass
            return
        
        # Get available proxy count and selection method
        configs = get_all_proxy_configs()
        proxy_count = len(configs)
        
        if proxy_count > 1:
            message_text = f"✅ Proxy enabled. All yt-dlp operations will use {proxy_count} proxy servers with {Config.PROXY_SELECT} selection method."
        else:
            message_text = "✅ Proxy enabled. All yt-dlp operations will use proxy."
        
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, message_text)
        send_to_logger(callback_query.message, "Proxy enabled.")
        try:
            callback_query.answer("Proxy enabled.")
        except Exception:
            pass
        return
    
    if data == "off":
        if not safe_write_file(proxy_file, "OFF"):
            try:
                callback_query.answer("❌ Error saving proxy settings.")
            except Exception:
                pass
            return
        
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "❌ Proxy disabled.")
        send_to_logger(callback_query.message, "Proxy disabled.")
        try:
            callback_query.answer("Proxy disabled.")
        except Exception:
            pass
        return


def is_proxy_enabled(user_id):
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
        logger.error(f"Error reading proxy file {proxy_file}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error reading proxy file {proxy_file}: {e}")
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
    
    logger.info(f"select_proxy_for_domain: URL={url}, extracted_domain={domain}")
    logger.info(f"PROXY_2_DOMAINS: {getattr(DomainsConfig, 'PROXY_2_DOMAINS', [])}")
    logger.info(f"PROXY_DOMAINS: {getattr(DomainsConfig, 'PROXY_DOMAINS', [])}")
    
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
            logger.info(f"Domain {domain} found in PROXY_2_DOMAINS (or is subdomain), using proxy 2")
            return get_proxy_2_config()
    
    # Check PROXY_DOMAINS
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        if is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS):
            logger.info(f"Domain {domain} found in PROXY_DOMAINS (or is subdomain), using proxy 1")
            return get_proxy_config()
    
    logger.info(f"Domain {domain} not found in any proxy domain list")
    return None

def add_proxy_to_ytdl_opts(ytdl_opts, url, user_id=None):
    """Add proxy to yt-dlp options if proxy is enabled for user or domain requires it"""
    logger.info(f"add_proxy_to_ytdl_opts called: user_id={user_id}, url={url}")
    
    # Check if user has proxy enabled
    if user_id:
        proxy_enabled = is_proxy_enabled(user_id)
        logger.info(f"Proxy check for user {user_id}: {proxy_enabled}")
        if proxy_enabled:
            # Use round-robin/random selection for user proxy
            proxy_config = select_proxy_for_user()
            if proxy_config:
                proxy_url = build_proxy_url(proxy_config)
                if proxy_url:
                    ytdl_opts['proxy'] = proxy_url
                    logger.info(f"Added proxy for user {user_id}: {proxy_url}")
                    return ytdl_opts
    
    # Check if domain requires specific proxy
    proxy_config = select_proxy_for_domain(url)
    if proxy_config:
        proxy_url = build_proxy_url(proxy_config)
        if proxy_url:
            ytdl_opts['proxy'] = proxy_url
            logger.info(f"Added domain-specific proxy for {url}: {proxy_url}")
    
    return ytdl_opts
