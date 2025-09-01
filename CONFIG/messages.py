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
• Send video link → download
• <code>/audio URL</code> → extract audio
• <code>/link [quality] URL</code> → get direct links
• <code>/proxy</code> → enable/disable proxy for all downloads
• Reply to video with text → change caption

📋 <b>Playlists:</b>
• <code>URL*1*5</code> → download videos 1-5

🍪 <b>Cookies & Private:</b>
• Upload *.txt cookie for private videos
• <code>/cookie [service]</code> → download cookies (youtube/instagram/tiktok/x/facebook/custom)
• <code>/cookies_from_browser</code> → extract from browser
• <code>/check_cookie</code> → verify cookie
• <code>/save_as_cookie</code> → save text as cookie

🧹 <b>Cleaning:</b>
• <code>/clean</code> → media files only
• <code>/clean all</code> → everything
• <code>/clean cookies/logs/tags/format/split/mediainfo/sub/keyboard</code>

⚙️ <b>Settings:</b>
• <code>/settings</code> → settings menu
• <code>/format</code> → quality & format
• <code>/split</code> → part size (250MB-2GB)
• <code>/mediainfo on/off</code> → media info
• <code>/tags</code> → view saved tags
• <code>/sub on/off</code> → subtitles
• <code>/keyboard</code> → keyboard (OFF/1x3/2x3)

🏷️ <b>Tags:</b>
• Add <code>#tag1#tag2</code> after URL
• Tags appear in captions
• <code>/tags</code> → view all tags

🔗 <b>Direct Links:</b>
• <code>/link URL</code> → best quality
• <code>/link [144-4320]/720p/1080p/4k/8k URL</code> → specific quality

⚙️ <b>Quick Commands:</b>
• <code>/format [144-4320]/720p/1080p/4k/8k</code> → set quality
• <code>/keyboard off/1x3/2x3/full</code> → keyboard layout
• <code>/split 250mb/500mb/1gb/1.5gb/2gb</code> → part size
• <code>/subs off/ru/en auto</code> → subtitle language
• <code>/mediainfo on/off</code> → on/off media info
• <code>/proxy on/off</code> → enable/disable proxy for all downloads

📊 <b>Info:</b>
• <code>/usage</code> → download history
• <code>/search</code> → inline search via @vid

<blockquote expandable>🇷🇺 <b>Бот для скачивания видео - Помощь</b>

📥 <b>Основное:</b>
• Отправьте ссылку → скачать
• <code>/audio URL</code> → аудио
• <code>/link [качество] URL</code> → прямые ссылки
• <code>/proxy</code> → включить/выключить прокси для всех загрузок
• Ответьте на видео текстом → изменить подпись

📋 <b>Плейлисты:</b>
• <code>URL*1*5</code> → скачать видео 1-5

🍪 <b>Cookies:</b>
• Загрузите *.txt для приватных видео
• <code>/cookie [сервис]</code> → скачать куки (youtube/instagram/tiktok/x/facebook/custom)
• <code>/cookies_from_browser</code> → из браузера
• <code>/check_cookie</code> → проверить cookie
• <code>/save_as_cookie</code> → сохранить текст как cookie

🧹 <b>Очистка:</b>
• <code>/clean</code> → медиа файлы
• <code>/clean all</code> → всё
• <code>/clean cookies/logs/tags/format/split/mediainfo/sub/keyboard</code>

⚙️ <b>Настройки:</b>
• <code>/settings</code> → меню настроек
• <code>/format</code> → качество и формат
• <code>/split</code> → размер части (250MB-2GB)
• <code>/mediainfo on/off</code> → информация о файле
• <code>/tags</code> → ваши теги
• <code>/sub on/off</code> → субтитры
• <code>/keyboard</code> → клавиатура (OFF/1x3/2x3)

🏷️ <b>Теги:</b>
• Добавьте <code>#тег1#тег2</code> после ссылки
• Теги появляются в подписях
• <code>/tags</code> → все теги

🔗 <b>Прямые ссылки:</b>
• <code>/link URL</code> → лучшее качество
• <code>/link [144-4320]/720p/1080p/4k/8k URL</code> → конкретное качество

⚙️ <b>Быстрые команды:</b>
• <code>/format [144-4320]/720p/1080p/4k/8k</code> → качество
• <code>/keyboard off/1x3/2x3/full</code> → клавиатура
• <code>/split 250mb/500mb/1gb/1.5gb/2gb</code> → размер части
• <code>/subs off/ru/en auto</code> → язык субтитров
• <code>/mediainfo on/off</code> → вкл/выкл медиаинфо
• <code>/proxy on/off</code> → включить/выключить прокси для всех загрузок

📊 <b>Информация:</b>
• <code>/usage</code> → история загрузок
• <code>/search</code> → поиск через @vid
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
