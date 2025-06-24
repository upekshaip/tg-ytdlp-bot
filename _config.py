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
    SUBSCRIBE_CHANNEL_URL = "https://t.me/upekshaip"
    # Download timeout in seconds (2 hours = 7200 seconds)
    DOWNLOAD_TIMEOUT = 7200
    # Cookie file URL
    # EX: "https://path/to/your/cookie-file.txt"
    COOKIE_URL = ""
    # Do not chanege this
    COOKIE_FILE_PATH = "cookies.txt"
    # Do not chanege this
    PIC_FILE_PATH = "pic.jpg"
    #######################################################
    # Firebase initialization
    # your firebase DB path
    BOT_DB_PATH = f"bot/{BOT_NAME}/"
    VIDEO_CACHE_DB_PATH = f"bot/video_cache"
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
    TAGS_COMMAND = "/tags"
    BROADCAST_MESSAGE = "/broadcast"
    # this is a main cmd - to user /get_user_details_users
    GET_USER_DETAILS_COMMAND = "/all"
    SPLIT_COMMAND = "/split"
    #######################################################
    # Messages and errors
    CREDITS_MSG = "__Developed by__ @upekshaip"
    TO_USE_MSG = "__To use this bot you need to subscribe to @upekshaip Telegram channel.__\nAfter you join the channel, **resend your video link again and I will download it for you** ❤️  "
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means my own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with **https://** or **http://**"
    INDEX_ERROR = "You did not give a valid information. Try again..."
    HELP_MSG = """
    <b>This bot allows you to download videos and audio, and also work with playlists.</b><br><br>
    • Simply send a video link and the bot will start downloading.<br>
    • For playlists, specify the range of indexes separated by asterisks (e.g. <code>https://example.com*1*4</code>) to download videos from position 1 to 4.<br>
    • You can set a custom playlist name by adding it after the range (e.g. <code>https://example.com*1*4*My Playlist</code>).<br><br>
    • To change the caption of a video, reply to the video with your message – the bot will send the video with your caption.<br>
    • To extract audio from a video, use the <b>/audio</b> command (e.g. <code>/audio https://example.com</code>).<br>
    • Upload a cookie file to download private videos and playlists.<br>
    • Check or update your cookie file with <b>/check_cookie</b>, <b>/download_cookie</b>, <b>/save_as_cookie</b> and <b>/cookies_from_browser</b> commands.<br>
    • To clean your workspace on server from bad files (e.g. old cookies or media) use <b>/clean</b> command.<br>
    • You can also use <b>/clean cookies</b>, <b>/clean logs</b>, <b>/clean tags</b>, <b>/clean format</b>, <b>/clean split</b> to remove only cookies, logs, tags, split or format file.<br>
    • See your usage statistics and logs by sending the <b>/usage</b> command.<br>
    • You can add tags to any link: just add #tag1#tag2 after the URL (e.g. https://youtu.be/xxxx#mytag#music). Tags will appear in the caption and are saved for navigation. See all your tags with /tags.<br>
    • You can also use <b>/split</b> to set the maximum part size for video splitting (250MB, 500MB, 1GB, 2GB).<br><br>
    <blockquote expandable>
    <b>Бот позволяет скачивать видео и аудио, а также работать с плейлистами.</b><br><br>
    • Просто отправьте ссылку на видео, и бот начнет загрузку.<br>
    • Для плейлистов укажите диапазон индексов через символы <code>*</code> (например, <code>https://example.com*1*4</code>), чтобы загрузить видео с 1 по 4 позицию.<br>
    • Вы можете задать своё название плейлиста, добавив его после диапазона (например, <code>https://example.com*1*4*Мой плейлист</code>).<br><br>
    • Чтобы изменить подпись к видео, ответьте на него своим сообщением – бот отправит видео с вашей подписью.<br>
    • Для извлечения аудио из видео используйте команду <b>/audio</b> (например, <code>/audio https://example.com</code>).<br>
    • Загрузите файл cookie – это позволит скачивать приватные видео и плейлисты.<br>
    • Проверьте или обновите cookie с помощью команд <b>/check_cookie</b>, <b>/download_cookie</b>, <b>/save_as_cookie</b> и <b>/cookies_from_browser</b>.<br>
    • Чтобы очистить свою папку на сервере от лишних файлов (например от старых cookies или медиа) используйте команду <b>/clean</b>.<br>
    • Также доступны <b>/clean cookies</b>, <b>/clean logs</b>, <b>/clean tags</b>, <b>/clean format</b>, <b>/clean split</b> — для удаления только cookies, логов, тегов, размера обрезки или файла формата.<br>
    • Узнайте свою статистику использования и логи командой <b>/usage</b>.<br>
    • Можно добавлять теги к любой ссылке: просто добавьте #тег1#тег2 после URL (например, https://youtu.be/xxxx#mytag#music). Теги появятся в подписи и сохраняются для навигации. Посмотреть все свои теги — командой /tags.<br>
    • Также доступна <b>/split</b> — для выбора максимального размера части при нарезке видео (250MB, 500MB, 1GB, 2GB).<br>
    </blockquote>
    <br>
    <i>Developed by</i> @upekshaip
    <i>Contributor</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
    """
    #######################################################
    # Restricted content site lists
    BLACK_LIST = []
    #BLACK_LIST = ["pornhub", "phncdn.com", "xvideos", "xhcdn.com", "xhamster"]
        # Paths to domain and keyword lists
    PORN_DOMAINS_FILE = "porn_domains.txt"
    PORN_KEYWORDS_FILE = "porn_keywords.txt"
    SUPPORTED_SITES_FILE = "supported_sites.txt"
    #PORN_SITES = "https://raw.githubusercontent.com/4skinSkywalker/Anti-Porn-HOSTS-File/refs/heads/master/HOSTS.txt"
    # --- Whitelist of domains that are not considered porn ---
    WHITELIST = [
        'dailymotion.com', 'ok.ru', 'kaspersky.com', 'sky.com', 'xbox.com', 
        'youtube.com', 'youtu.be', 'tiktok.ru', 'rutube.ru', '1tv.ru',
        'x.com', 'tiktok.com', 'facebook.com', 'x.ai', 'vk.ru',
        'vk.com', 'm.vk.com', 'vkvideo.ru', 'vkontakte.ru'
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
        'vk.com', 'vk.com', 'vkvideo.ru', 'vkontakte.ru',
        'tiktok.com', 'tiktok.com', 'vimeo.com', 'twitch.tv', 'twitch.tv',
        'instagram.com', 'instagram.com', 'dailymotion.com',
        'twitter.com', 'x.com', 't.co', 'ok.ru', 'mail.ru'
        # Add here other domains where query and fragment are not needed for video uniqueness
    ]       
