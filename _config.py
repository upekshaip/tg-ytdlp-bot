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
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means my own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with **https://** or **http://**"
    INDEX_ERROR = "You did not give a valid information. Try again..."
    HELP_MSG = """
**You can enter any video link. Also you can enter youtube playlist link with the range. 
If you entered a playlist link you must provide a range**


• You can download videos with this bot. Just send the link like this:

    `https://blabla.blaa`


• If you want to download youtube playlist give a range like this: 
__separate the --link--, --start-- and --end-- playlist index numbers in `*` mark.__

    `https://blabla.blaa*1*4` 

__this will download all videos from --index 1-- to --index 4-- on that playlist.__


• If you need a coustom playlist name send like this:

    `https://blabla.blaa*1*4*coustom name`

• __If you want to change the caption of a video reply to the video with your caption.__ **Bot will send your video with your caption.**

• To clean your working space send /clean command. If you get any download errors, you can try this out. Then send the link again. It will fix the issue.

• You can also download any private video with a cookie file. Just send your cookies.txt file to the bot.

• To check the cookie file run /check_cookie command. After setting the cookie file, you can enter your video url as usual. If you need to download private playlist it will also work as usual.

• To see your logs and your usage, send /usage command. 



__Developed by__ @upekshaip
"""

# Firebase initialization
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME}/"
    # Firebase Config - Required (str for all)
    FIREBASE_CONF = {
        'apiKey': "",
        'authDomain': "",
        'projectId': "",
        'storageBucket': "",
        'messagingSenderId': "",
        'appId': "",
        'databaseURL': ""
    }
