# Config
class Config(object):
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
    SUBSCRIBE_CHANNEL_URL = "https://t.me/upekshaip"

    # Cookie file URL
    # EX: "https://path/to/your/cookie-file.txt"
    COOKIE_URL = ""
    # Do not chanege this
    COOKIE_FILE_PATH = "cookies.txt"
    # Do not chanege this
    PIC_FILE_PATH = "pic.jpg"

    # Restricted content site lists
    PORN_LIST = ["pornhub", "phncdn.com", "xvideos", "xhcdn.com", "xhamster"]

    # Commands
    DOWNLOAD_COOKIE_COMMAND = "/download_cookie"
    CHECK_COOKIE_COMMAND = "/check_cookie"
    SAVE_AS_COOKIE_COMMAND = "/save_as_cookie"
    AUDIO_COMMAND = "/audio"
    FORMAT_COMMAND = "/format"
    COOKIES_FROM_BROWSER_COMMAND = "/cookies_from_browser"
    BLOCK_USER_COMMAND = "/block_user"
    UNBLOCK_USER_COMMAND = "/unblock_user"
    RUN_TIME = "/run_time"
    GET_USER_LOGS_COMMAND = "/log"
    CLEAN_COMMAND = "/clean"
    USAGE_COMMAND = "/usage"
    BROADCAST_MESSAGE = "/broadcast"
    # this is a main cmd - to user /get_user_details_users
    GET_USER_DETAILS_COMMAND = "/all"

    # Messages and errors
    CREDITS_MSG = "__Developed by__ @upekshaip"
    TO_USE_MSG = "__To use this bot you need to subscribe to @upekshaip Telegram channel.__\nAfter you join the channel, **resend your video link again and I will download it for you** ❤️  "
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means my own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with **https://** or **http://**"
    INDEX_ERROR = "You did not give a valid information. Try again..."
    HELP_MSG = """
> **This bot allows you to download videos and audio, and also work with playlists.**
> 
> • Simply send a video link and the bot will start downloading.
> • For playlists, specify the range of indexes separated by asterisks (e.g. `https://example.com*1*4`) to download videos from position 1 to 4.
> • You can set a custom playlist name by adding it after the range (e.g. `https://example.com*1*4*My Playlist`).
> 
> • To change the caption of a video, reply to the video with your message – the bot will send the video with your caption.
> • To extract audio from a video, use the **/audio** command (e.g. `/audio https://example.com`).
> • Upload a cookie file to download private videos and playlists.
> • Check or update your cookie file with **/check_cookie**, **/download_cookie**, **/save_as_cookie** and **/cookies_from_browser** commands.
> • To clean your workspace on server from bad files (e.g. old cookies or media) use **/clean** command (might be helpfull for get rid of errors).
> • See your usage statistics and logs by sending the **/usage** command.

__Developed by__ @upekshaip
__Contributor___ @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
"""

# Firebase initialization
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME}/"
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
