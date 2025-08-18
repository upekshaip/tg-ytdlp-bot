# ############################################################################################
import logging
import time
import threading
try:
    from sdnotify import SystemdNotifier
    SDNOTIFY_AVAILABLE = True
except ImportError:
    SDNOTIFY_AVAILABLE = False
    SystemdNotifier = None
from pyrogram import enums
from CONFIG.config import Config
from HELPERS.safe_messeger import safe_send_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# WatchDog
if SDNOTIFY_AVAILABLE:
    notifier = SystemdNotifier()
    
    def watchdog_loop():
        while True:
            notifier.notify("WATCHDOG=1")
            logger.info("[Watchdog] Sent WATCHDOG=1")
            time.sleep(30)  # Frequency is less than WatchdogSec

    # Start watchdog thread
    threading.Thread(target=watchdog_loop, daemon=True).start()

    # At the beginning of initialization
    notifier.notify("READY=1")
    logger.info("[Watchdog] Sent READY=1")
else:
    logger.info("[Watchdog] SystemdNotifier not available - watchdog disabled")
# Send Message to Logger

def send_to_logger(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # Print (user_id, "-", msg)
    safe_send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.HTML)

# Send Message to User Only

def send_to_user(message, msg):
    user_id = message.chat.id
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)

# Send Message to All ...

def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    safe_send_message(Config.LOGS_ID, msg_with_id, parse_mode=enums.ParseMode.HTML)
    safe_send_message(user_id, msg, parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)
