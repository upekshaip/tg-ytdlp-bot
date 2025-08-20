# Messages Configuration

class MessagesConfig(object):
    #######################################################
    # Messages and errors
    #######################################################
    CREDITS_MSG = "<i>Developed by</i> @upekshaip"
    TO_USE_MSG = "<i>To use this bot you need to subscribe to @upekshaip Telegram channel.</i>\nAfter you join the channel, <b>resend your video link again and I will download it for you</b> ❤️  "
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means my own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with <b>https://</b> or <b>http://</b>"
    INDEX_ERROR = "You did not give a valid information. Try again..."
    PLAYLIST_HELP_MSG = """
📋 <b>How to download playlists:</b>

To download playlists send its URL with <code>*start*end</code> ranges in the end.

<b>Examples:</b>

🟥 <b>Video range from YouTube playlist:</b> (need 🍪)
<code>https://youtu.be/playlist?list=PL...*1*5</code>
(downloads videos from 1 to 5 inclusive)
🟥 <b>Single video from YouTube playlist:</b> (need 🍪)
<code>https://youtu.be/playlist?list=PL...*3*3</code>
(downloads only the 3rd video)

⬛️ <b>TikTok profile:</b> (need your 🍪)
<code>https://www.tiktok.com/@USERNAME*1*10</code>
(downloads first 10 videos from user profile)

🟪 <b>Instagram stories:</b> (need your 🍪)
<code>https://www.instagram.com/stories/USERNAME*1*3</code>
(downloads first 3 stories)
<code>https://www.instagram.com/stories/highlights/123...*1*10</code>
(downloads first 10 stories from album)

🟦 <b>VK videos:</b>
<code>https://vkvideo.ru/@PAGE_NAME*1*3</code>
(downloads first 3 videos from user/group profile)

⬛️<b>Rutube channels:</b>
<code>https://rutube.ru/channel/CHANNEL_ID/videos*2*4</code>
(downloads videos from 2 to 4 inclusive from channel)

🟪 <b>Twitch clips:</b>
<code>https://www.twitch.tv/USERNAME/clips*1*3</code>
(downloads first 3 clips from channel)

🟦 <b>Vimeo groups:</b>
<code>https://vimeo.com/groups/GROUP_NAME/videos*1*2</code>
(downloads first 2 videos from group)

🟧 <b>Pornhub models:</b>
<code>https://www.pornhub.org/model/MODEL_NAME*1*2</code>
(downloads first 2 video from model profile)
<code>https://www.pornhub.com/video/search?search=YOUR+PROMPT*1*3</code>
(downloads first 3 video from search results by your prompt)

and so on...
see <a href="https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md">supported sites list</a>
"""
    HELP_MSG = """
🎬 <b>Video Download Bot - Help</b>

📥 <b>Basic Usage:</b>
• Send any video link and the bot will download it
• For audio extraction, use <code>/audio URL</code>
• Reply to any video with text to change its caption

📋 <b>Playlists:</b>
• <code>URL*1*5</code> - Download videos 1-5 from playlist
• <code>URL*1*5*My Playlist</code> - With custom name

🍪 <b>Cookies & Private Content:</b>
• Upload *.txt cookie file for private videos downloading
• <code>/download_cookie</code> - Get my YouTube cookie
• <code>/cookies_from_browser</code> - Extract from browser
• <code>/check_cookie</code> - Verify your cookie
• <code>/save_as_cookie</code> - Save text as cookie

🧹 <b>Cleaning:</b>
• <code>/clean</code> - Remove media files only
• <code>/clean all</code> - Remove everything
• <code>/clean cookies</code> - Remove cookie file
• <code>/clean logs</code> - Remove logs file
• <code>/clean tags</code> - Remove tags file
• <code>/clean format</code> - Remove format settings
• <code>/clean split</code> - Remove split settings
• <code>/clean mediainfo</code> - Remove mediainfo settings
• <code>/clean sub</code> - Remove subtitle settings

⚙️ <b>Settings:</b>
• <code>/settings</code> - Open settings menu
• <code>/format</code> - Change video quality & format
• <code>/split</code> - Set max part size (250MB-2GB)
• <code>/mediainfo</code> - Enable/disable file info
• <code>/tags</code> - View your saved tags
• <code>/sub</code> - Turn on/off subtitles

🏷️ <b>Tags System:</b>
• Add <code>#tag1#tag2</code> after any URL
• Tags appear in captions and are saved
• Use <code>/tags</code> to view all your tags

📊 <b>Information:</b>
• <code>/usage</code> - View your download history
• <code>/help</code> - Show this help message

<blockquote expandable>🇷🇺 <b>Бот для скачивания видео - Помощь</b>
(нажми, чтобы развернуть 👇)

📥 <b>Основное использование:</b>
• Отправьте ссылку на видео для загрузки
• <code>/audio URL</code> - Извлечь аудио
• Ответьте на видео текстом для изменения подписи

📋 <b>Плейлисты:</b>
• <code>URL*1*5</code> - Скачать видео 1-5 из плейлиста
• <code>URL*1*5*Мой плейлист</code> - С собственным названием

🍪 <b>Cookies и приватный контент:</b>
• Загрузите *.txt cookie для скачивания приватных видео
• <code>/download_cookie</code> - Получить мой YouTube cookie
• <code>/cookies_from_browser</code> - Извлечь из браузера
• <code>/check_cookie</code> - Проверить ваш cookie
• <code>/save_as_cookie</code> - Сохранить текст как cookie

🧹 <b>Очистка:</b>
• <code>/clean</code> - Удалить только медиа файлы
• <code>/clean all</code> - Удалить всё
• <code>/clean cookies</code> - Удалить cookie файл
• <code>/clean logs</code> - Удалить файл логов
• <code>/clean tags</code> - Удалить файл тегов
• <code>/clean format</code> - Удалить настройки формата
• <code>/clean split</code> - Удалить настройки нарезки
• <code>/clean mediainfo</code> - Удалить настройки mediainfo
• <code>/clean sub</code> - Удалить настройки субтитров

⚙️ <b>Настройки:</b>
• <code>/settings</code> - Открыть меню настроек
• <code>/format</code> - Изменить качество и формат
• <code>/split</code> - Установить размер части (250MB-2GB)
• <code>/mediainfo</code> - Включить/выключить информацию о файле
• <code>/tags</code> - Посмотреть ваши теги
• <code>/sub</code> - Включить/выключить субтитры

🏷️ <b>Система тегов:</b>
• Добавьте <code>#тег1#тег2</code> после любой ссылки
• Теги появляются в подписях и сохраняются
• <code>/tags</code> - Посмотреть все ваши теги

📊 <b>Информация:</b>
• <code>/usage</code> - История загрузок
• <code>/help</code> - Показать эту справку
</blockquote>
👨‍💻 <i>Developer:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Contributor:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
    """
    
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
