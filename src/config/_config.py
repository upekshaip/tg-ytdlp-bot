# Config

class Config(object):
    #######################################################    
    # Your bot name - Required (str)
    BOT_NAME = "public"
    # A name for users - Required (str)
    BOT_NAME_FOR_USERS = "Video Downloader bot by upekshaip"
    # Add all admin id's as a list - Required (lst[int])
    ADMIN = [0000000000]
    # Add your telegram API ID - Required (int)
    API_ID = 0000000
    # Add your Telegram API HASH - Required (str)
    API_HASH = ""
    # Add your telegram bot token (str)
    BOT_TOKEN = ""
    # Add telegram Log channel Id - Required (int)
    LOGS_ID = -0000000000000 
    # Add main channel to subscribe - Required (int)
    SUBSCRIBE_CHANNEL = -0000000000000
    # Add subscription channel - Required (str)
    SUBSCRIBE_CHANNEL_URL = "https://t.me/YOUR_CHANNEL_NAME"
    MAX_FILE_SIZE_GB = 10  # GiB
    # Download timeout in seconds (2 hours = 7200 seconds)
    DOWNLOAD_TIMEOUT = 7200 # in seconds
    MAX_SUB_QUALITY = 720 # 720p
    MAX_SUB_DURATION = 5400 # in seconds
    MAX_SUB_SIZE = 500 # in MB      
    MAX_PLAYLIST_COUNT = 50
    MAX_TIKTOK_COUNT = 500        
    # Cookie file URL
    # EX: "https://path/to/your/cookie-file.txt"
    COOKIE_URL = ""
    YOUTUBE_COOKIE_URL = ""
    INSTAGRAM_COOKIE_URL = ""
    TWITTER_COOKIE_URL = ""
    TIKTOK_COOKIE_URL = ""
    FACEBOOK_COOKIE_URL = ""
    # Do not chanege this
    COOKIE_FILE_PATH = "cookies/cookie.txt"
    # Do not chanege this
    PIC_FILE_PATH = "pic.jpg"
    FIREBASE_CACHE_FILE = "dump.json"
    RELOAD_CACHE_COMMAND = "/reload_cache"
    AUTO_CACHE_COMMAND = "/auto_cache"
    RELOAD_CACHE_EVERY = 4 # in hours
    DOWNLOAD_FIREBASE_SCRIPT_PATH = "download_firebase.py"
    AUTO_CACHE_RELOAD_ENABLED = True # Enable/disable automatic cache reloading
    #######################################################
    # Firebase initialization
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME}/"
    VIDEO_CACHE_DB_PATH = f"{BOT_DB_PATH}/video_cache"
    PLAYLIST_CACHE_DB_PATH = f"{BOT_DB_PATH}/video_cache/playlists"
    # Firebase Config - Required (str for all)
    FIREBASE_USER = "YOUR@E.MAIL"
    FIREBASE_PASSWORD = "YOUR_PASSWORD"
    FIREBASE_CONF = {
        'apiKey': "",
        'authDomain': "",
        'projectId': "",
        'storageBucket': "",
        'messagingSenderId': "",
        'appId': "",
        'databaseURL': ""
    }
    #######################################################
    # Commands
    START_COMMAND = "/start"
    HELP_COMMAND = "/help"
    LANGUAGE_COMMAND = "/language"
    DOWNLOAD_COOKIE_COMMAND = "/download_cookie"
    SUBS_COMMAND = "/subs"
    CHECK_COOKIE_COMMAND = "/check_cookie"
    SAVE_AS_COOKIE_COMMAND = "/save_as_cookie"
    AUDIO_COMMAND = "/audio"
    UNCACHE_COMMAND = "/uncache"    
    PLAYLIST_COMMAND = "/playlist"    
    FORMAT_COMMAND = "/format"
    MEDIINFO_COMMAND = "/mediainfo"
    SETTINGS_COMMAND = "/settings"
    COOKIES_FROM_BROWSER_COMMAND = "/cookies_from_browser"
    BLOCK_USER_COMMAND = "/block_user"
    UNBLOCK_USER_COMMAND = "/unblock_user"
    RUN_TIME = "/run_time"
    GET_USER_LOGS_COMMAND = "/log"
    CLEAN_COMMAND = "/clean"
    USAGE_COMMAND = "/usage"
    TAGS_COMMAND = "/tags"
    BROADCAST_MESSAGE = "/broadcast"
    # this is a main cmd - to user /get_user_details_users
    GET_USER_DETAILS_COMMAND = "/all"
    SPLIT_COMMAND = "/split"
    RELOAD_CACHE_COMMAND = "/reload_cache"
    AUTO_CACHE_COMMAND = "/auto_cache"

    # admin commands
    ADMIN_COMMANDS = [
        START_COMMAND,
        HELP_COMMAND,
        BLOCK_USER_COMMAND,
        UNBLOCK_USER_COMMAND,
        UNBLOCK_USER_COMMAND,
        GET_USER_LOGS_COMMAND,
        BROADCAST_MESSAGE,
        GET_USER_DETAILS_COMMAND,
        AUTO_CACHE_COMMAND,
        UNCACHE_COMMAND,
        RELOAD_CACHE_COMMAND,
        ]
        
    #######################################################
    # Messages and errors
    CREDITS_MSG = "__Developed by__ @upekshaip"
    TO_USE_MSG = "__To use this bot you need to subscribe to @upekshaip Telegram channel.__\nAfter you join the channel, **resend your video link again and I will download it for you** ❤️  "
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means my own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with **https://** or **http://**"
    INDEX_ERROR = "You did not give a valid information. Try again..."
    #######################################################
    # Restricted content site lists
    BLACK_LIST = []
    #BLACK_LIST = ["pornhub", "phncdn.com", "xvideos", "xhcdn.com", "xhamster"]
    # Paths to domain and keyword lists
    PORN_DOMAINS_FILE = "txts/porn_domains.txt"
    PORN_KEYWORDS_FILE = "txts/porn_keywords.txt"
    SUPPORTED_SITES_FILE = "txts/supported_sites.txt"
    # --- Whitelist of domains that are not considered porn ---
    WHITELIST = [
        'dailymotion.com', 'sky.com', 'xbox.com', 'youtube.com', 'youtu.be', '1tv.ru', 'x.ai',
        'twitch.tv', 'vimeo.com', 'facebook.com', 'tiktok.com', 'instagram.com', 'fb.com', 'ig.me'
        # Other secure domains can be added
    ]
    NO_COOKIE_DOMAINS = [
        'dailymotion.com'
        # Other secure domains can be added
    ]    
    # TikTok Domain List
    TIKTOK_DOMAINS = [
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com',
        'www.tiktok.com', 'm.tiktok.com', 'tiktokv.com',
        'www.tiktokv.com', 'tiktok.ru', 'www.tiktok.ru'
    ]
    # Added CLEAN_QUERY array for domains where query and fragment can be safely cleared
    CLEAN_QUERY = [
        'vk.com', 'vkvideo.ru', 'vkontakte.ru',
        'tiktok.com', 'vimeo.com', 'twitch.tv',
        'instagram.com', 'ig.me', 'dailymotion.com',
        'twitter.com', 'x.com',
        'ok.ru', 'mail.ru', 'my.mail.ru',
        'rutube.ru', 'youku.com', 'bilibili.com',
        'tv.kakao.com', 'tudou.com', 'coub.com',
        'fb.watch', '9gag.com', 'streamable.com',
        'veoh.com', 'archive.org', 'ted.com',
        'mediasetplay.mediaset.it', 'ndr.de', 'zdf.de', 'arte.tv',
        'video.yandex.ru', 'video.sibnet.ru', 'pladform.ru', 'pikabu.ru',
        'redtube.com', 'youporn.com', 'xhamster.com',
        'spankbang.com', 'xnxx.com', 'xvideos.com',
        'bitchute.com', 'rumble.com', 'peertube.tv',
        'aparat.com', 'nicovideo.jp', 
        'disk.yandex.net', 'streaming.disk.yandex.net',
        # Add here other domains where query and fragment are not needed for video uniqueness
    ]
    # Version 1.0.0 - Добавлен SAVE_AS_COOKIE_HINT для подсказки по /save_as_cookie
    SAVE_AS_COOKIE_HINT = (
        "Just save your cookie as <b><u>cookie.txt</u></b> and send it to bot as a document.\n\n"
        "You can also send cookies as plain text with <b><u>/save_as_cookie</u></b> command.\n"
        "<b>Usage of <b><u>/save_as_cookie</u></b>:</b>\n\n"
        "<pre>"
        "/save_as_cookie\n"
        "# Netscape HTTP Cookie File\n"
        "# http://curl.haxx.se/rfc/cookie_spec.html\n"
        "# This file was generated by Cookie-Editor\n"
        ".youtube.com  TRUE  /  FALSE  111  ST-xxxxx  session_logininfo=AAA\n"
        ".youtube.com  TRUE  /  FALSE  222  ST-xxxxx  session_logininfo=BBB\n"
        ".youtube.com  TRUE  /  FALSE  33333  ST-xxxxx  session_logininfo=CCC\n"
        "</pre>\n"
        "<blockquote>"
        "<b><u>Instructions:</u></b>\n"
        "https://t.me/c/2303231066/18 \n"
        "https://t.me/c/2303231066/22 "
        "</blockquote>"
    )
    #######################################################