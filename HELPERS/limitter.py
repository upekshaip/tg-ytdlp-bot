from HELPERS.app_instance import get_app
from CONFIG.config import Config
from HELPERS.logger import logger
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
import os

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2 ** 10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") +\
        ((str(hours) + "h, ") if hours else "") +\
        ((str(minutes) + "m, ") if minutes else "") +\
        ((str(seconds) + "s, ") if seconds else "") +\
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

# Check the USAGE of the BOT

def is_user_in_channel(app, message):
    try:
        cht_member = app.get_chat_member(
            Config.SUBSCRIBE_CHANNEL, message.chat.id)
        if cht_member.status == ChatMemberStatus.MEMBER or cht_member.status == ChatMemberStatus.OWNER or cht_member.status == ChatMemberStatus.ADMINISTRATOR:
            return True

    except:

        text = f"{Config.TO_USE_MSG}\n \n{Config.CREDITS_MSG}"
        button = InlineKeyboardButton(
            "Join Channel", url=Config.SUBSCRIBE_CHANNEL_URL)
        keyboard = InlineKeyboardMarkup([[button]])
        # Use the send_message () Method to send the message with the button
        app.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        return False


def check_user(message):
    """Check if user is in channel and create user directory"""
    user_id_str = str(message.chat.id)
    
    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    # Check if user is in channel (for non-admins)
    if int(message.chat.id) not in Config.ADMIN:
        app = get_app()
        if app is None:
            logger.error("App instance is None in check_user")
            return False
        return is_user_in_channel(app, message)
    return True

def check_file_size_limit(info_dict, max_size_bytes=None):
    """
    Checks if the size of the file is the global limit.
    Returns True if the size is within the limit, otherwise false.
    """
    if max_size_bytes is None:
        max_size_gb = getattr(Config, 'MAX_FILE_SIZE_GB', 10)  # GiB
        max_size_bytes = int(max_size_gb * 1024 ** 3)

    # Check if info_dict is None
    if info_dict is None:
        logger.warning("check_file_size_limit: info_dict is None, allowing download")
        return True

    filesize = info_dict.get('filesize') or info_dict.get('filesize_approx')
    if filesize and filesize > 0:
        size_bytes = int(filesize)
    else:
        # Try to estimate by bitrate (kbit/s) and duration (s)
        tbr = info_dict.get('tbr')
        duration = info_dict.get('duration')
        if tbr and duration:
            size_bytes = float(tbr) * float(duration) * 125  # kbit/s -> bytes
        else:
            # Very rough estimate by resolution and duration
            width = info_dict.get('width')
            height = info_dict.get('height')
            duration = info_dict.get('duration')
            if width and height and duration:
                size_bytes = int(width) * int(height) * float(duration) * 0.07
            else:
                # Could not estimate, allow download
                return True

    return size_bytes <= max_size_bytes

    
def check_subs_limits(info_dict, quality_key=None):
    """
    Checks restrictions for embedding subtitles
    Returns True if subtitles can be built, false if limits are exceeded
    """
    try:
        # Check if info_dict is None
        if info_dict is None:
            logger.warning("check_subs_limits: info_dict is None, allowing subtitle embedding")
            return True
            
        # We get the parameters from the config
        max_quality = Config.MAX_SUB_QUALITY
        max_duration = Config.MAX_SUB_DURATION
        max_size = Config.MAX_SUB_SIZE
        
        logger.info(f"check_subs_limits: checking limits - max_quality={max_quality}p, max_duration={max_duration}s, max_size={max_size}MB")
        logger.info(f"check_subs_limits: info_dict keys: {list(info_dict.keys()) if info_dict else 'None'}")
        
        # Check the duration
        duration = info_dict.get('duration')
        if duration and duration > max_duration:
            logger.info(f"Subtitle embedding skipped: duration {duration}s exceeds limit {max_duration}s")
            return False
        
        # Check the file size (only if it is accurately known)
        filesize = info_dict.get('filesize') or info_dict.get('filesize_approx')
        if filesize and filesize > 0:  # Check that the size is larger than 0
            size_mb = filesize / (1024 * 1024)  # Fixed: use division instead of integer division
            if size_mb > max_size:
                logger.info(f"Subtitle embedding skipped: size {size_mb:.2f}MB exceeds limit {max_size}MB")
                return False
        
        # Check quality (only if width and height are available)
        width = info_dict.get('width')
        height = info_dict.get('height')
        if width and height:
            min_side = min(width, height)
            if min_side > max_quality:
                logger.info(f"Subtitle embedding skipped: quality {width}x{height} (min side {min_side}p) exceeds limit {max_quality}p")
                return False
        
        logger.info(f"Subtitle limits check passed: duration={duration}s, size={filesize} bytes, quality={width}x{height}")
        return True
    except Exception as e:
        logger.error(f"Error checking subtitle limits: {e}")
        return False

def check_playlist_range_limits(url, video_start_with, video_end_with, app, message):
    """
    Checks the limits of the download range for playlists, Tiktok and Instagram.
    For single videos, True always returns.
    If the range exceeds the limit, it sends a warning and returns false.
    """
    # If a single video (no range) - always true
    if video_start_with == 1 and video_end_with == 1:
        return True

    url_l = str(url).lower() if url else ''
    if 'tiktok.com' in url_l:
        max_count = Config.MAX_TIKTOK_COUNT
        service = 'TikTok'
    elif 'instagram.com' in url_l:
        max_count = Config.MAX_TIKTOK_COUNT
        service = 'Instagram'
    else:
        max_count = Config.MAX_PLAYLIST_COUNT
        service = 'playlist'

    count = video_end_with - video_start_with + 1
    if count > max_count:
        app.send_message(
            message.chat.id,
            f"❗️ Range limit exceeded for {service}: {count} (maximum {max_count}).\nReduce the range and try again.",
            reply_to_message_id=getattr(message, 'id', None)
        )
        # We send a notification to the log channel
        app.send_message(
            Config.LOGS_ID,
            f"❗️ Range limit exceeded for {service}: {count} (maximum {max_count})\nUser ID: {message.chat.id}",
        )
        return False
    return True
