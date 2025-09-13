# Main Configuration
# This file combines all configuration classes into one unified Config class

from CONFIG.commands import CommandsConfig
from CONFIG.messages import MessagesConfig
from CONFIG.domains import DomainsConfig
from CONFIG.limits import LimitsConfig

###########################################################
#        START FILL IN YOUR CUSTOM VALUES HERE
###########################################################
class Config(object):
    #######################################################    
    # Your bot name - Required (str)
    BOT_NAME = "tgytdlp_test_bot"
    # A name for users - Required (str)
    BOT_NAME_FOR_USERS = "tgytdlp_bot" #name in database
    # Список ID администраторов
    ADMIN = [00000000, 111111111111]
    STAR_RECEIVER = 7360853
    # Add allowed group IDs - Only these groups will be served by the bot
    ALLOWED_GROUP = [-100111111111111, -1002222222222222]
    # API ID Telegram
    API_ID = 00000000000000
    # API HASH Telegram
    API_HASH = "abc0000000000000000000"
    # Токен бота
    BOT_TOKEN = "00000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    # ID канала для логов
    LOGS_ID = -100111111111111  # ID канала для логов
    LOGS_VIDEO_ID = -100111111111111  # ID канала для логов видео
    LOGS_NSFW_ID = -100111111111111  # ID канала для логов видео с тэгами NSWF
    LOGS_IMG_ID = -100111111111111  # ID канала для логов медиа команды /img     
    LOGS_PAID_ID = -100111111111111  # ID канала для логов платных медиа
    LOG_EXCEPTION = -100111111111111  # ID канала для логов исключений
    # ID канала для подписки
    SUBSCRIBE_CHANNEL = -100222222222222222222
    # Add subscription channel - Required (str)
    SUBSCRIBE_CHANNEL_URL = "https://t.me/+abcdef"
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
    YOUTUBE_COOKIE_TEST_URL = "https://youtu.be/XqZsoesa55w"  # Short video
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
    RELOAD_CACHE_EVERY = 4 # in hours
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
    #######################################################
    # Firebase initialization
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME_FOR_USERS}/"
    VIDEO_CACHE_DB_PATH = f"bot/video_cache"
    PLAYLIST_CACHE_DB_PATH = f"bot/video_cache/playlists"
    IMAGE_CACHE_DB_PATH = f"bot/video_cache/images"    
    # Firebase Config - Required (str for all)
    # Firebase настройки
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
    ###########################################################
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
    
    # Messages configuration
    CREDITS_MSG = MessagesConfig.CREDITS_MSG
    TO_USE_MSG = MessagesConfig.TO_USE_MSG
    MSG1 = MessagesConfig.MSG1
    MSG2 = MessagesConfig.MSG2
    ERROR1 = MessagesConfig.ERROR1
    INDEX_ERROR = MessagesConfig.INDEX_ERROR
    PLAYLIST_HELP_MSG = MessagesConfig.PLAYLIST_HELP_MSG
    HELP_MSG = MessagesConfig.HELP_MSG
    SEARCH_MSG = MessagesConfig.SEARCH_MSG
    ADD_BOT_TO_GROUP_MSG = MessagesConfig.ADD_BOT_TO_GROUP_MSG
    AUDIO_HINT_MSG = MessagesConfig.AUDIO_HINT_MSG
    IMG_HELP_MSG = MessagesConfig.IMG_HELP_MSG
    LINK_HINT_MSG = MessagesConfig.LINK_HINT_MSG
    NSFW_ON_MSG = MessagesConfig.NSFW_ON_MSG
    NSFW_OFF_MSG = MessagesConfig.NSFW_OFF_MSG
    NSFW_INVALID_MSG = MessagesConfig.NSFW_INVALID_MSG
    
    # UI Messages - Status and Progress
    CHECKING_CACHE_MSG = MessagesConfig.CHECKING_CACHE_MSG
    PROCESSING_MSG = MessagesConfig.PROCESSING_MSG
    DOWNLOADING_MSG = MessagesConfig.DOWNLOADING_MSG
    DOWNLOADING_VIDEO_MSG = MessagesConfig.DOWNLOADING_VIDEO_MSG
    DOWNLOADING_IMAGE_MSG = MessagesConfig.DOWNLOADING_IMAGE_MSG
    UPLOAD_COMPLETE_MSG = MessagesConfig.UPLOAD_COMPLETE_MSG
    DOWNLOAD_COMPLETE_MSG = MessagesConfig.DOWNLOAD_COMPLETE_MSG
    VIDEO_PROCESSING_MSG = MessagesConfig.VIDEO_PROCESSING_MSG
    WAITING_HOURGLASS_MSG = MessagesConfig.WAITING_HOURGLASS_MSG
    
    # Cache Messages
    SENT_FROM_CACHE_MSG = MessagesConfig.SENT_FROM_CACHE_MSG
    VIDEO_SENT_FROM_CACHE_MSG = MessagesConfig.VIDEO_SENT_FROM_CACHE_MSG
    PLAYLIST_SENT_FROM_CACHE_MSG = MessagesConfig.PLAYLIST_SENT_FROM_CACHE_MSG
    CACHE_PARTIAL_MSG = MessagesConfig.CACHE_PARTIAL_MSG
    CACHE_FAILED_VIDEO_MSG = MessagesConfig.CACHE_FAILED_VIDEO_MSG
    CACHE_FAILED_GENERIC_MSG = MessagesConfig.CACHE_FAILED_GENERIC_MSG
    
    # Error Messages
    INVALID_URL_MSG = MessagesConfig.INVALID_URL_MSG
    FAILED_ANALYZE_MSG = MessagesConfig.FAILED_ANALYZE_MSG
    ERROR_OCCURRED_MSG = MessagesConfig.ERROR_OCCURRED_MSG
    ERROR_DOWNLOAD_MSG = MessagesConfig.ERROR_DOWNLOAD_MSG
    ERROR_SENDING_VIDEO_MSG = MessagesConfig.ERROR_SENDING_VIDEO_MSG
    ERROR_UNKNOWN_MSG = MessagesConfig.ERROR_UNKNOWN_MSG
    ERROR_NO_DISK_SPACE_MSG = MessagesConfig.ERROR_NO_DISK_SPACE_MSG
    ERROR_FILE_SIZE_LIMIT_MSG = MessagesConfig.ERROR_FILE_SIZE_LIMIT_MSG
    ERROR_NO_VIDEOS_PLAYLIST_MSG = MessagesConfig.ERROR_NO_VIDEOS_PLAYLIST_MSG
    ERROR_TIKTOK_API_MSG = MessagesConfig.ERROR_TIKTOK_API_MSG
    ERROR_FFMPEG_NOT_FOUND_MSG = MessagesConfig.ERROR_FFMPEG_NOT_FOUND_MSG
    ERROR_CONVERSION_FAILED_MSG = MessagesConfig.ERROR_CONVERSION_FAILED_MSG
    ERROR_GETTING_LINK_MSG = MessagesConfig.ERROR_GETTING_LINK_MSG
    ERROR_AV1_NOT_AVAILABLE_MSG = MessagesConfig.ERROR_AV1_NOT_AVAILABLE_MSG
    ERROR_AV1_NOT_AVAILABLE_SHORT_MSG = MessagesConfig.ERROR_AV1_NOT_AVAILABLE_SHORT_MSG
    
    # Telegram Rate Limit Messages
    RATE_LIMIT_WITH_TIME_MSG = MessagesConfig.RATE_LIMIT_WITH_TIME_MSG
    RATE_LIMIT_NO_TIME_MSG = MessagesConfig.RATE_LIMIT_NO_TIME_MSG
    
    # Subtitles Messages
    SUBTITLES_FAILED_MSG = MessagesConfig.SUBTITLES_FAILED_MSG
    SUBTITLES_NOT_FOUND_MSG = MessagesConfig.SUBTITLES_NOT_FOUND_MSG
    SUBTITLES_EMBEDDING_MSG = MessagesConfig.SUBTITLES_EMBEDDING_MSG
    SUBTITLES_SUCCESS_MSG = MessagesConfig.SUBTITLES_SUCCESS_MSG
    SUBTITLES_NOT_FOUND_VIDEO_MSG = MessagesConfig.SUBTITLES_NOT_FOUND_VIDEO_MSG
    SUBTITLES_SIZE_LIMIT_MSG = MessagesConfig.SUBTITLES_SIZE_LIMIT_MSG
    
    # Video Processing Messages
    HLS_STREAM_MSG = MessagesConfig.HLS_STREAM_MSG
    DOWNLOADING_FORMAT_MSG = MessagesConfig.DOWNLOADING_FORMAT_MSG
    DOWNLOADED_PROCESSING_MSG = MessagesConfig.DOWNLOADED_PROCESSING_MSG
    FILE_TOO_LARGE_MSG = MessagesConfig.FILE_TOO_LARGE_MSG
    SPLIT_PART_UPLOADED_MSG = MessagesConfig.SPLIT_PART_UPLOADED_MSG
    
    # Stream/Link Messages
    STREAM_LINKS_TITLE_MSG = MessagesConfig.STREAM_LINKS_TITLE_MSG
    STREAM_TITLE_MSG = MessagesConfig.STREAM_TITLE_MSG
    STREAM_DURATION_MSG = MessagesConfig.STREAM_DURATION_MSG
    STREAM_FORMAT_MSG = MessagesConfig.STREAM_FORMAT_MSG
    STREAM_BROWSER_MSG = MessagesConfig.STREAM_BROWSER_MSG
    VLC_PLAYER_IOS_MSG = MessagesConfig.VLC_PLAYER_IOS_MSG
    VLC_PLAYER_ANDROID_MSG = MessagesConfig.VLC_PLAYER_ANDROID_MSG
    
    # Download Progress Messages
    DOWNLOADING_FORMAT_ID_MSG = MessagesConfig.DOWNLOADING_FORMAT_ID_MSG
    DOWNLOADING_QUALITY_MSG = MessagesConfig.DOWNLOADING_QUALITY_MSG
    
    # Quality Selection Messages
    MANUAL_QUALITY_TITLE_MSG = MessagesConfig.MANUAL_QUALITY_TITLE_MSG
    MANUAL_QUALITY_DESC_MSG = MessagesConfig.MANUAL_QUALITY_DESC_MSG
    ALL_FORMATS_TITLE_MSG = MessagesConfig.ALL_FORMATS_TITLE_MSG
    ALL_FORMATS_PAGE_MSG = MessagesConfig.ALL_FORMATS_PAGE_MSG
    CACHED_QUALITIES_TITLE_MSG = MessagesConfig.CACHED_QUALITIES_TITLE_MSG
    CACHED_QUALITIES_DESC_MSG = MessagesConfig.CACHED_QUALITIES_DESC_MSG
    ERROR_GETTING_FORMATS_MSG = MessagesConfig.ERROR_GETTING_FORMATS_MSG
    
    # NSFW Paid Content Messages
    NSFW_PAID_WARNING_MSG = MessagesConfig.NSFW_PAID_WARNING_MSG
    NSFW_PAID_INFO_MSG = MessagesConfig.NSFW_PAID_INFO_MSG
    
    # Callback Error Messages
    ERROR_ORIGINAL_NOT_FOUND_MSG = MessagesConfig.ERROR_ORIGINAL_NOT_FOUND_MSG
    ERROR_ORIGINAL_NOT_FOUND_DELETED_MSG = MessagesConfig.ERROR_ORIGINAL_NOT_FOUND_DELETED_MSG
    ERROR_URL_NOT_FOUND_MSG = MessagesConfig.ERROR_URL_NOT_FOUND_MSG
    ERROR_ORIGINAL_URL_NOT_FOUND_MSG = MessagesConfig.ERROR_ORIGINAL_URL_NOT_FOUND_MSG
    ERROR_URL_NOT_EMBEDDABLE_MSG = MessagesConfig.ERROR_URL_NOT_EMBEDDABLE_MSG
    ERROR_CODEC_NOT_AVAILABLE_MSG = MessagesConfig.ERROR_CODEC_NOT_AVAILABLE_MSG
    ERROR_FORMAT_NOT_AVAILABLE_MSG = MessagesConfig.ERROR_FORMAT_NOT_AVAILABLE_MSG
    
    # Tags Error Messages
    TAG_FORBIDDEN_CHARS_MSG = MessagesConfig.TAG_FORBIDDEN_CHARS_MSG
    
    # Playlist Messages
    PLAYLIST_SENT_MSG = MessagesConfig.PLAYLIST_SENT_MSG
    PLAYLIST_CACHE_SENT_MSG = MessagesConfig.PLAYLIST_CACHE_SENT_MSG
    
    # Failed Stream Messages
    FAILED_STREAM_LINKS_MSG = MessagesConfig.FAILED_STREAM_LINKS_MSG
    
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
    # Messages configuration (additional)
    SAVE_AS_COOKIE_HINT = MessagesConfig.SAVE_AS_COOKIE_HINT
    
    # Limits configuration
    MAX_FILE_SIZE_GB = LimitsConfig.MAX_FILE_SIZE_GB
    DOWNLOAD_TIMEOUT = LimitsConfig.DOWNLOAD_TIMEOUT
    MAX_SUB_QUALITY = LimitsConfig.MAX_SUB_QUALITY
    MAX_SUB_DURATION = LimitsConfig.MAX_SUB_DURATION
    MAX_SUB_SIZE = LimitsConfig.MAX_SUB_SIZE
    MAX_PLAYLIST_COUNT = LimitsConfig.MAX_PLAYLIST_COUNT
    MAX_TIKTOK_COUNT = LimitsConfig.MAX_TIKTOK_COUNT
    
    # PO Token Provider configuration - these are defined above in the main config
    # No need to duplicate them here as they are already accessible
    #######################################################