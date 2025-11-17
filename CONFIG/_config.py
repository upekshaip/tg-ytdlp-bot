# Main Configuration
# This file combines all configuration classes into one unified Config class

from CONFIG.commands import CommandsConfig
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.domains import DomainsConfig
from CONFIG.limits import LimitsConfig

###########################################################
#        START FILL IN YOUR CUSTOM VALUES HERE
###########################################################
class Config(object):
    #######################################################    
    # IMPORTANT (REQUIRED) SETTINGS - start filling settings here
    #######################################################        
    # Your bot name - Required (str)
    BOT_NAME = "tgytdlp_test_bot"
    # A name for users - Required (str)
    BOT_NAME_FOR_USERS = "tgytdlp_bot" #name in database
    # List of administrator IDs
    ADMIN = [00000000, 111111111111]
    # Add allowed group IDs - Only these groups will be served by the bot
    ALLOWED_GROUP = [-100111111111111, -1002222222222222]
    # API ID Telegram
    API_ID = 00000000000000
    # API HASH Telegram
    API_HASH = "abc0000000000000000000"
    # Bot token
    BOT_TOKEN = "00000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    # Mini-app URL
    MINIAPP_URL = "https://t.me/tgytdlp_test_bot/?startapp"
    # Channel ID for logs (you can use the same 1 channel ID for all LOGS)
    LOGS_ID = -100111111111111  # Channel ID for logs
    LOGS_VIDEO_ID = -100111111111111  # Channel ID for video logs
    LOGS_NSFW_ID = -100111111111111  # Channel ID for video logs with NSWF tags
    LOGS_IMG_ID = -100111111111111  # Channel ID for media command logs /img 
    LOGS_PAID_ID = -100111111111111  # Channel ID for paid media logs
    LOG_EXCEPTION = -100111111111111  # Channel ID for exception logs
    # Channel ID to subscribe to
    SUBSCRIBE_CHANNEL = -100222222222222222222
    # Add subscription channel - Required (str)
    SUBSCRIBE_CHANNEL_URL = "https://t.me/+abcdef"
    #######################################################
    # Firebase initialization
    USE_FIREBASE = True
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME_FOR_USERS}/"
    VIDEO_CACHE_DB_PATH = f"bot/video_cache"
    PLAYLIST_CACHE_DB_PATH = f"bot/video_cache/playlists"
    IMAGE_CACHE_DB_PATH = f"bot/video_cache/images"    
    # Firebase Config - Required (str for all)
    # Firebase settings
    FIREBASE_USER = "XXX@gmail.com"
    FIREBASE_PASSWORD = "XXXXXXXXXXXXXXXxx"
    FIREBASE_CONF = {
        "apiKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "authDomain": "XXXXXXXXXXXX.firebaseapp.com",
        "projectId": "XXXXXXXXXX-0000000000",
        "storageBucket": "XXXXXXXXXXXXXX-0000000000.firebasestorage.app",
        "messagingSenderId": "0000000000000000",
        "appId": "1:0000000000000:web:00000000000000a",
        "databaseURL": "https://XXXXXXXXXXXXXX-000000000-default-rtdb.europe-west1.firebasedatabase.app"
    }
    ########################################################    
    ########################################################
    # OPTIONAL (NOT REQUIRED) SETTINGS - you can stop here
    ########################################################    
    # Cookie file URL
    # EX: "https://path/to/your/cookie-file.txt"
    COOKIE_URL = "https://XXX/cookie.txt"
    # YouTube cookies URLs - main URL and backups
    # The bot will check cookies in the order: YOUTUBE_COOKIE_URL, YOUTUBE_COOKIE_URL_1, YOUTUBE_COOKIE_URL_2, etc. up to 10
    # If one URL does not work or the cookies are expired, the bot will automatically try the next one
    YOUTUBE_COOKIE_URL = "https://XXX/youtube_cookie.txt"
    YOUTUBE_COOKIE_URL_1 = "https://XXX/cookie1.txt"
    YOUTUBE_COOKIE_URL_2 = "https://XXX/cookie2.txt"
    YOUTUBE_COOKIE_URL_3 = "https://XXX/cookie3.txt"
    #YOUTUBE_COOKIE_URL_4 = "https://XXX/cookie4.txt"
    #YOUTUBE_COOKIE_URL_10 = "https://XXX/cookie10.txt"
    YOUTUBE_COOKIE_ORDER = "round_robin" # random, round_robin
    # YouTube test URL for cookie validation
    YOUTUBE_COOKIE_TEST_URL = "https://www.youtube.com/watch?v=_GuOjXYl5ew" #youtube official video
    #YOUTUBE_COOKIE_TEST_URL = "https://youtu.be/XqZsoesa55w"  # Baby Shark Dance
    #YOUTUBE_COOKIE_TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video
    #INSTAGRAM_COOKIE_URL = "https://XXX/instagram_cookie.txt"
    TIKTOK_COOKIE_URL = "https://XXX/tiktok_cookie.txt"
    #FACEBOOK_COOKIE_URL = "https://XXX/facebook_cookie.txt"
    TWITTER_COOKIE_URL = "https://XXX/twitter_cookie.txt"
    VK_COOKIE_URL = "https://XXX/vk_cookie.txt"
    # Do not chanege this
    COOKIE_FILE_PATH = "TXT/cookie.txt"
    # Do not chanege this
    PIC_FILE_PATH = "pic.jpg"
    FIREBASE_CACHE_FILE = "dump.json"
    RELOAD_CACHE_EVERY = 1 # in hours
    DOWNLOAD_FIREBASE_SCRIPT_PATH = "DATABASE/download_firebase.py"
    AUTO_CACHE_RELOAD_ENABLED = True # Enable/disable automatic cache reloading
    ########################################################
    # Proxy configuration
    PROXY_TYPE="http" # http, https, socks4, socks5, socks5h
    PROXY_IP="X.X.X.X"
    PROXY_PORT=3128
    PROXY_USER="XXXXXXXX"
    PROXY_PASSWORD="XXXXXXXXX"
    # Additional Proxy configuration  
    PROXY_2_TYPE="socks5" # http, https, socks4, socks5, socks5h
    PROXY_2_IP="X.X.X.X"
    PROXY_2_PORT=3128
    PROXY_2_USER="XXXXXXXX"
    PROXY_2_PASSWORD="XXXXXXXXX"
    # Proxy selection method for /proxy on command
    PROXY_SELECT = "round_robin" # random, round_robin
    ########################################################
    # PO Token Provider configuration for YouTube
    # Enable PO token provider for YouTube domains
    YOUTUBE_POT_ENABLED = True
    # PO token provider server URL (Docker container)
    YOUTUBE_POT_BASE_URL = "http://127.0.0.1:4416"
    # Disable innertube if tokens stop working
    YOUTUBE_POT_DISABLE_INNERTUBE = False
    ###########################################################
    #        STOP FILL IN YOUR CUSTOM VALUES HERE
    ###########################################################
    # Commands configuration
    DOWNLOAD_COOKIE_COMMAND = CommandsConfig.DOWNLOAD_COOKIE_COMMAND
    PROXY_COMMAND = CommandsConfig.PROXY_COMMAND
    SUBS_COMMAND = CommandsConfig.SUBS_COMMAND
    CHECK_COOKIE_COMMAND = CommandsConfig.CHECK_COOKIE_COMMAND
    SAVE_AS_COOKIE_COMMAND = CommandsConfig.SAVE_AS_COOKIE_COMMAND
    AUDIO_COMMAND = CommandsConfig.AUDIO_COMMAND
    UNCACHE_COMMAND = CommandsConfig.UNCACHE_COMMAND
    PLAYLIST_COMMAND = CommandsConfig.PLAYLIST_COMMAND
    FORMAT_COMMAND = CommandsConfig.FORMAT_COMMAND
    MEDIINFO_COMMAND = CommandsConfig.MEDIINFO_COMMAND
    SETTINGS_COMMAND = CommandsConfig.SETTINGS_COMMAND
    COOKIES_FROM_BROWSER_COMMAND = CommandsConfig.COOKIES_FROM_BROWSER_COMMAND
    BLOCK_USER_COMMAND = CommandsConfig.BLOCK_USER_COMMAND
    UNBLOCK_USER_COMMAND = CommandsConfig.UNBLOCK_USER_COMMAND
    RUN_TIME = CommandsConfig.RUN_TIME
    GET_USER_LOGS_COMMAND = CommandsConfig.GET_USER_LOGS_COMMAND
    CLEAN_COMMAND = CommandsConfig.CLEAN_COMMAND
    USAGE_COMMAND = CommandsConfig.USAGE_COMMAND
    TAGS_COMMAND = CommandsConfig.TAGS_COMMAND
    BROADCAST_MESSAGE = CommandsConfig.BROADCAST_MESSAGE
    GET_USER_DETAILS_COMMAND = CommandsConfig.GET_USER_DETAILS_COMMAND
    SPLIT_COMMAND = CommandsConfig.SPLIT_COMMAND
    RELOAD_CACHE_COMMAND = CommandsConfig.RELOAD_CACHE_COMMAND
    AUTO_CACHE_COMMAND = CommandsConfig.AUTO_CACHE_COMMAND
    SEARCH_COMMAND = CommandsConfig.SEARCH_COMMAND
    KEYBOARD_COMMAND = CommandsConfig.KEYBOARD_COMMAND
    LINK_COMMAND = CommandsConfig.LINK_COMMAND
    IMG_COMMAND = CommandsConfig.IMG_COMMAND
    ADD_BOT_TO_GROUP_COMMAND = CommandsConfig.ADD_BOT_TO_GROUP_COMMAND
    NSFW_COMMAND = CommandsConfig.NSFW_COMMAND
    ARGS_COMMAND = CommandsConfig.ARGS_COMMAND
    LIST_COMMAND = CommandsConfig.LIST_COMMAND
    
    # Messages configuration - using dynamic loading
    @classmethod
    def get_messages(cls, user_id=None, language_code=None):
        """Get messages instance for user or language"""
        return safe_get_messages(user_id, language_code)
    
    @classmethod
    def get_message(cls, message_key, user_id=None, language_code=None):
        """Get specific message for user or language"""
        messages = cls.get_messages(user_id, language_code)
        return getattr(messages, message_key, f"[{message_key}]")
    
    # Domains configuration
    GREYLIST = DomainsConfig.GREYLIST
    BLACK_LIST = DomainsConfig.BLACK_LIST
    PORN_DOMAINS_FILE = DomainsConfig.PORN_DOMAINS_FILE
    PORN_KEYWORDS_FILE = DomainsConfig.PORN_KEYWORDS_FILE
    SUPPORTED_SITES_FILE = DomainsConfig.SUPPORTED_SITES_FILE
    UPDATE_PORN_SCRIPT_PATH = DomainsConfig.UPDATE_PORN_SCRIPT_PATH
    WHITELIST = DomainsConfig.WHITELIST
    NO_COOKIE_DOMAINS = DomainsConfig.NO_COOKIE_DOMAINS
    PROXY_DOMAINS = DomainsConfig.PROXY_DOMAINS    
    PROXY_2_DOMAINS = DomainsConfig.PROXY_2_DOMAINS    
    TIKTOK_DOMAINS = DomainsConfig.TIKTOK_DOMAINS
    CLEAN_QUERY = DomainsConfig.CLEAN_QUERY
    PIPED_DOMAIN = DomainsConfig.PIPED_DOMAIN
    # Messages configuration (additional) - now handled dynamically
    
    # Limits configuration
    MAX_FILE_SIZE_GB = LimitsConfig.MAX_FILE_SIZE_GB
    DOWNLOAD_TIMEOUT = LimitsConfig.DOWNLOAD_TIMEOUT
    MAX_SUB_QUALITY = LimitsConfig.MAX_SUB_QUALITY
    MAX_SUB_DURATION = LimitsConfig.MAX_SUB_DURATION
    MAX_SUB_SIZE = LimitsConfig.MAX_SUB_SIZE
    MAX_PLAYLIST_COUNT = LimitsConfig.MAX_PLAYLIST_COUNT
    MAX_TIKTOK_COUNT = LimitsConfig.MAX_TIKTOK_COUNT
    MAX_VIDEO_DURATION = LimitsConfig.MAX_VIDEO_DURATION
    MAX_IMG_FILES = LimitsConfig.MAX_IMG_FILES
    GROUP_MULTIPLIER = LimitsConfig.GROUP_MULTIPLIER
    NSFW_STAR_COST = LimitsConfig.NSFW_STAR_COST

    STAR_RECEIVER = 7360853    
    # PO Token Provider configuration - these are defined above in the main config
    # No need to duplicate them here as they are already accessible
    #######################################################