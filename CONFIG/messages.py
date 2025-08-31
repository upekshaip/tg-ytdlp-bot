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
• For direct links, use <code>/link [quality] URL</code>
• Reply to any video with text to change its caption

📋 <b>Playlists:</b>
• <code>URL*1*5</code> - Download videos 1-5 from playlist
• <code>URL*1*5*My Playlist</code> - With custom name

🍪 <b>Cookies & Private Content:</b>
• Upload *.txt cookie file for private videos downloading
• <code>/cookie</code> - Get my YouTube cookie
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
• <code>/clean keyboard</code> - Remove keyboard settings

⚙️ <b>Settings:</b>
• <code>/settings</code> - Open settings menu
• <code>/format</code> - Change video quality & format
• <code>/split</code> - Set max part size (250MB-2GB)
• <code>/mediainfo on/off</code> - Enable/disable file info
• <code>/tags</code> - View your saved tags
• <code>/sub on/off</code> - Turn on/off subtitles
• <code>/keyboard</code> - Manage keyboard settings (OFF/1x3/2x3)

🏷️ <b>Tags System:</b>
• Add <code>#tag1#tag2</code> after any URL
• Tags appear in captions and are saved
• Use <code>/tags</code> to view all your tags

🔗 <b>Direct Links:</b>
• <code>/link URL</code> - Get direct link (best quality)
• <code>/link 720 URL</code> - Get direct link (720p or lower)
• <code>/link 4k URL</code> - Get direct link (4K or lower)
• <code>/link 8k URL</code> - Get direct link (8K or lower)

⚙️ <b>Advanced Commands with Arguments:</b>
• <code>/format 720</code> - Set quality to 720p
• <code>/format 4k</code> - Set quality to 4K
• <code>/format 8k</code> - Set quality to 8K
• <code>/keyboard off</code> - Hide keyboard
• <code>/keyboard 1x3</code> - Set 1x3 keyboard layout
• <code>/keyboard 2x3</code> - Set 2x3 keyboard layout
• <code>/keyboard full</code> - Set emoji keyboard
• <code>/split 250mb</code> - Set split size to 250MB
• <code>/split 1gb</code> - Set split size to 1GB
• <code>/split 2gb</code> - Set split size to 2GB
• <code>/subs off</code> - Disable subtitles
• <code>/subs ru</code> - Set subtitle language to Russian
• <code>/subs en auto</code> - Set subtitle language to English with AUTO/TRANS

📊 <b>Information:</b>
• <code>/usage</code> - View your download history
• <code>/help</code> - Show this help message

🔍 <b>Search:</b>
• <code>/search</code> - Activate inline search via @vid bot

<blockquote expandable>🇷🇺 <b>Бот для скачивания видео - Помощь</b>
(нажми, чтобы развернуть 👇)

📥 <b>Основное использование:</b>
• Отправьте ссылку на видео для загрузки
• <code>/audio URL</code> - Извлечь аудио
• <code>/link [качество] URL</code> - Получить прямую ссылку
• Ответьте на видео текстом для изменения подписи

📋 <b>Плейлисты:</b>
• <code>URL*1*5</code> - Скачать видео 1-5 из плейлиста
• <code>URL*1*5*Мой плейлист</code> - С собственным названием

🍪 <b>Cookies и приватный контент:</b>
• Загрузите *.txt cookie для скачивания приватных видео
• <code>/cookie</code> - Получить мой YouTube cookie
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
• <code>/clean keyboard</code> - Удалить настройки клавиатуры

⚙️ <b>Настройки:</b>
• <code>/settings</code> - Открыть меню настроек
• <code>/format</code> - Изменить качество и формат
• <code>/split</code> - Установить размер части (250MB-2GB)
• <code>/mediainfo on/off</code> - Включить/выключить информацию о файле
• <code>/tags</code> - Посмотреть ваши теги
• <code>/sub on/off</code> - Включить/выключить субтитры
• <code>/keyboard</code> - Управление настройками клавиатуры (OFF/1x3/2x3)

🏷️ <b>Система тегов:</b>
• Добавьте <code>#тег1#тег2</code> после любой ссылки
• Теги появляются в подписях и сохраняются
• <code>/tags</code> - Посмотреть все ваши теги

🔗 <b>Прямые ссылки:</b>
• <code>/link URL</code> - Получить прямую ссылку (лучшее качество)
• <code>/link 720 URL</code> - Получить прямую ссылку (720p или ниже)
• <code>/link 4k URL</code> - Получить прямую ссылку (4K или ниже)
• <code>/link 8k URL</code> - Получить прямую ссылку (8K или ниже)

⚙️ <b>Расширенные команды с аргументами:</b>
• <code>/format 720</code> - Установить качество 720p
• <code>/format 4k</code> - Установить качество 4K
• <code>/format 8k</code> - Установить качество 8K
• <code>/keyboard off</code> - Скрыть клавиатуру
• <code>/keyboard 1x3</code> - Установить клавиатуру 1x3
• <code>/keyboard 2x3</code> - Установить клавиатуру 2x3
• <code>/keyboard full</code> - Установить эмодзи клавиатуру
• <code>/split 250mb</code> - Установить размер части 250MB
• <code>/split 1gb</code> - Установить размер части 1GB
• <code>/split 2gb</code> - Установить размер части 2GB
• <code>/subs off</code> - Отключить субтитры
• <code>/subs ru</code> - Установить язык субтитров русский
• <code>/subs en auto</code> - Установить язык субтитров английский с AUTO/TRANS

📊 <b>Информация:</b>
• <code>/usage</code> - История загрузок
• <code>/help</code> - Показать эту справку

🔍 <b>Поиск:</b>
• <code>/search</code> - Активировать inline поиск через @vid бота
</blockquote>
👨‍💻 <i>Developer:</i> @upekshaip 
<a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Contributor:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl 
<a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
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
    
    # Search command message (English)
    SEARCH_MSG = """
🔍 <b>Video search</b>

Press the button below to activate inline search via @vid.

<blockquote>
This helps you quickly find and download videos from various platforms.
</blockquote>
    """
    #######################################################
