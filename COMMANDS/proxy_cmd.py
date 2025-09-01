# /Proxy Command
import os
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

@app.on_message(filters.command("proxy") & filters.private)
def proxy_command(app, message):
    user_id = message.chat.id
    logger.info(f"[PROXY] User {user_id} requested proxy command")
    logger.info(f"[PROXY] User {user_id} is admin: {int(user_id) in Config.ADMIN}")
    logger.info(f"[PROXY] User {user_id} is in channel: {is_user_in_channel(app, message)}")
    
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
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
                with open(proxy_file, "w", encoding="utf-8") as f:
                    f.write("ON" if arg == "on" else "OFF")
                safe_send_message(user_id, f"✅ Proxy {'enabled' if arg=='on' else 'disabled'}.")
                send_to_logger(message, f"Proxy set via command: {arg}")
                return
    except Exception:
        pass
    
    buttons = [
        [InlineKeyboardButton("✅ ON", callback_data="proxy_option|on"), InlineKeyboardButton("❌ OFF", callback_data="proxy_option|off")],
        [InlineKeyboardButton("🔚Close", callback_data="proxy_option|close")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    safe_send_message(
        user_id,
        "Enable or disable using 🇩🇪 proxy (Germany) for all yt-dlp operations?",
        reply_markup=keyboard
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
        with open(proxy_file, "w", encoding="utf-8") as f:
            f.write("ON")
        safe_edit_message_text(callback_query.message.chat.id, callback_query.message.id, "✅ Proxy enabled. All yt-dlp operations will use proxy.")
        send_to_logger(callback_query.message, "Proxy enabled.")
        try:
            callback_query.answer("Proxy enabled.")
        except Exception:
            pass
        return
    
    if data == "off":
        with open(proxy_file, "w", encoding="utf-8") as f:
            f.write("OFF")
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
            return f.read().strip().upper() == "ON"
    except Exception:
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


def add_proxy_to_ytdl_opts(ytdl_opts, url, user_id=None):
    """Add proxy to yt-dlp options if proxy is enabled for user or domain requires it"""
    from CONFIG.domains import DomainsConfig
    
    logger.info(f"add_proxy_to_ytdl_opts called: user_id={user_id}, url={url}")
    
    # Check if user has proxy enabled
    if user_id:
        proxy_enabled = is_proxy_enabled(user_id)
        logger.info(f"Proxy check for user {user_id}: {proxy_enabled}")
        if proxy_enabled:
            proxy_config = get_proxy_config()
            if proxy_config and 'type' in proxy_config and 'ip' in proxy_config and 'port' in proxy_config:
                # Build proxy URL
                if proxy_config['type'] == 'http':
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
                elif proxy_config['type'] == 'https':
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"https://{proxy_config['ip']}:{proxy_config['port']}"
                elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
                else:
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
                
                ytdl_opts['proxy'] = proxy_url
                logger.info(f"Added proxy for user {user_id}: {proxy_url}")
                return ytdl_opts
    
    # Fallback: check if domain requires proxy (PROXY_DOMAINS logic)
    if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
        domain = None
        if '://' in url:
            domain = url.split('://')[1].split('/')[0]
        else:
            domain = url.split('/')[0]
        
        if domain in DomainsConfig.PROXY_DOMAINS:
            proxy_config = get_proxy_config()
            if proxy_config and 'type' in proxy_config and 'ip' in proxy_config and 'port' in proxy_config:
                # Build proxy URL
                if proxy_config['type'] == 'http':
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
                elif proxy_config['type'] == 'https':
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"https://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"https://{proxy_config['ip']}:{proxy_config['port']}"
                elif proxy_config['type'] in ['socks4', 'socks5', 'socks5h']:
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"{proxy_config['type']}://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"{proxy_config['type']}://{proxy_config['ip']}:{proxy_config['port']}"
                else:
                    if proxy_config.get('user') and proxy_config.get('password'):
                        proxy_url = f"http://{proxy_config['user']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
                    else:
                        proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
                
                ytdl_opts['proxy'] = proxy_url
                logger.info(f"Added proxy for domain {domain}: {proxy_url}")
    
    return ytdl_opts
