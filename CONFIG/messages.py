# Messages Configuration

class MessagesConfig(object):
    #######################################################
    # Messages and errors
    #######################################################
    CREDITS_MSG = "<blockquote><i>Managed by</i> @iilililiiillliiliililliilliliiil\n🇮🇹 @tgytdlp_bot\n🇦🇪 @tgytdlp_uae_bot\n🇬🇧 @tgytdlp_uk_bot\n🇫🇷 @tgytdlp_fr_bot</blockquote>"
    TO_USE_MSG = "<i>To use this bot you need to subscribe to @tg_ytdlp Telegram channel.</i>\nAfter you join the channel, <b>resend your video link again and bot will download it for you</b> ❤️  "
    MSG1 = "Hello "
    MSG2 = "This is the second message. which means bot's own message... 😁"
    ERROR1 = "Did not found a url link. Please enter a url with <b>https://</b> or <b>http://</b>"
    INDEX_ERROR = "You did not give a valid information. Try again..."

    PLAYLIST_HELP_MSG = """
<blockquote expandable>📋 <b>Playlists (yt-dlp)</b>

To download playlists send its URL with <code>*start*end</code> ranges in the end. For example: <code>URL*1*5</code>.
Or you can use <code>/vid FROM-TO URL</code>. For example: <code>/vid 3-7 URL</code>. Also works for <code>/audio</code> command.

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
see <a href=\"https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md\">supported sites list</a>
</blockquote>

<blockquote expandable>🖼 <b>Images (gallery-dl)</b>

Use <code>/img URL</code> to download images/photos/albums from many platforms.

<b>Examples:</b>
<code>/img https://vk.com/wall-160916577_408508</code>
<code>/img https://2ch.hk/fd/res/1747651.html</code>
<code>/img https://x.com/username/status/1234567890123456789</code>
<code>/img https://imgur.com/a/abc123</code>

<b>Ranges:</b>
<code>/img 11-20 https://example.com/album</code> — items 11..20
<code>/img 11- https://example.com/album</code> — from 11 to the end (or bot limit)

<i>Supported platforms include vk, 2ch, 35photo, 4chan, 500px, ArtStation, Boosty, Civitai, Cyberdrop, DeviantArt, Discord, Facebook, Fansly, Instagram, Pinterest, Reddit, TikTok, Tumblr, Twitter/X, JoyReactor, etc. Full list:</i>
<a href=\"https://raw.githubusercontent.com/mikf/gallery-dl/refs/heads/master/docs/supportedsites.md\">gallery-dl supported sites</a>
</blockquote>
"""
    HELP_MSG = """
🎬 <b>Video Download Bot - Help</b>

📥 <b>Basic Usage:</b>
• Send any link → bot downloads it
  <blockquote>the bot automatically tries to download videos via yt-dlp and images via gallery-dl.</blockquote>
• <code>/audio URL</code> → extract audio
• <code>/link [quality] URL</code> → get direct links
• <code>/proxy</code> → enable/disable proxy for all downloads
• Reply to video with text → change caption

📋 <b>Playlists & Ranges:</b>
• <code>URL*1*5</code> → download videos 1-5
• <code>/vid 3-7 URL</code> → becomes <code>URL*3*7</code>

🍪 <b>Cookies & Private:</b>
• Upload *.txt cookie for private videos
• <code>/cookie [service]</code> → download cookies (youtube/tiktok/x/custom)
• <code>/cookie youtube 1</code> → pick source by index (1–N)
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
• <code>/split</code> → split video into parts
• <code>/mediainfo on/off</code> → media info
• <code>/nsfw on/off</code> → NSFW blur
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
• <code>/format [144-4320]/720p/1080p/4k/8k/best/ask/id 134</code> → set quality
• <code>/keyboard off/1x3/2x3/full</code> → keyboard layout
• <code>/split 100mb-2000mb</code> → change part size
• <code>/subs off/ru/en auto</code> → subtitle language
• <code>/list URL</code> → список доступных форматов
• <code>/mediainfo on/off</code> → on/off media info
• <code>/proxy on/off</code> → enable/disable proxy for all downloads

📊 <b>Info:</b>
• <code>/usage</code> → download history
• <code>/search</code> → inline search via @vid

🖼 <b>Images:</b>
• <code>URL</code> → download images URL
• <code>/img URL</code> → download images from URL
• <code>/img 11-20 URL</code> → download specific range
• <code>/img 11- URL</code> → download from 11th to the end

<blockquote expandable>🇷🇺 <b>Бот для скачивания видео - Помощь</b>

📥 <b>Основное:</b>
• Отправьте любую ссылку → бот скачает её
  <blockquote>бот автоматически попробует скачать видео через yt-dlp и изображения через gallery-dl.</blockquote>
• <code>/audio URL</code> → аудио
• <code>/link [качество] URL</code> → прямые ссылки
• <code>/proxy</code> → включить/выключить прокси для всех загрузок
• Ответьте на видео текстом → изменить подпись

📋 <b>Плейлисты:</b>
• <code>URL*1*5</code> → скачать видео 1-5
• <code>/vid 3-7 URL</code> → становится <code>URL*3*7</code>

🍪 <b>Cookies:</b>
• Загрузите *.txt для приватных видео
• <code>/cookie [сервис]</code> → скачать куки (youtube/tiktok/x/custom)
• <code>/cookie youtube 1</code> → выбрать источник по индексу (1–N)
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
• <code>/split</code> → резать видео на части
• <code>/mediainfo on/off</code> → информация о файле
• <code>/nsfw on/off</code> → размытие NSFW
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
• <code>/format [144-4320]/720p/1080p/4k/8k/best/ask/id 134</code> → качество
• <code>/keyboard off/1x3/2x3/full</code> → клавиатура
• <code>/split 100mb-2000mb</code> → резать видео на части
• <code>/subs off/ru/en auto</code> → язык субтитров
• <code>/list URL</code> → список доступных форматов
• <code>/mediainfo on/off</code> → вкл/выкл медиаинфо
• <code>/proxy on/off</code> → включить/выключить прокси для всех загрузок

📊 <b>Информация:</b>
• <code>/usage</code> → история загрузок
• <code>/search</code> → поиск через @vid

🖼 <b>Изображения:</b>
• <code>URL</code> → скачать изображения с URL
• <code>/img URL</code> → скачать изображения с URL
• <code>/img 11-20 URL</code> → скачать конкретный диапазон
• <code>/img 11- URL</code> → скачать с 11-го до конца
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

<blockquote>On PC just type <b>"@vid Your_Search_Query"</b> in any chat.</blockquote>
    """
    
    # Settings and Hints (English)
    
    AUDIO_HINT_MSG = (
        "Download only audio from video source.\n\n"
        "Usage: /audio + URL \n\n"
        "(ex. /audio https://youtu.be/abc123)\n"
        "(ex. /audio https://youtu.be/playlist?list=abc123*1*10)"
    )
    
    IMG_HELP_MSG = (
        "<b>🖼 Image Download Command</b>\n\n"
        "Usage: <code>/img URL</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/img https://example.com/image.jpg</code>\n"
        "• <code>/img 11-20 https://example.com/album</code>\n"
        "• <code>/img 11- https://example.com/album</code>\n"
        "• <code>/img https://vk.com/wall-160916577_408508</code>\n"
        "• <code>/img https://2ch.hk/fd/res/1747651.html</code>\n"
        "• <code>/img https://imgur.com/abc123</code>\n\n"
        "<b>Supported platforms (examples):</b>\n"
        "<blockquote>vk, 2ch, 35photo, 4chan, 500px, ArtStation, Boosty, Civitai, Cyberdrop, DeviantArt, Discord, Facebook, Fansly, Instagram, Patreon, Pinterest, Reddit, TikTok, Tumblr, Twitter/X, JoyReactor, etc. — <a href=\"https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md\">full list</a></blockquote>"
    )
    
    LINK_HINT_MSG = (
        "Get direct video links with quality selection.\n\n"
        "Usage: /link + URL \n\n"
        "(ex. /link https://youtu.be/abc123)\n"
        "(ex. /link 720 https://youtu.be/abc123)"
    )
    
    # Add bot to group command message
    ADD_BOT_TO_GROUP_MSG = """
🤖 <b>Add Bot to Group</b>

Add my bots to your groups to get enhanced features and higher limits!
————————————
📊 <b>Current FREE Limits (in Bot’s DM):</b>
<blockquote>•🗑 Messy junk from all the files unsorted 👎
• Max 1 file size: <b>8 GB </b>
• Max 1 file quality: <b>UNLIM</b>
• Max 1 file duration: <b>UNLIM</b>
• Max number of downloads: <b>UNLIM</b>
• Max playlist items per 1 time: <b>50</b>
• Max TikTok videos per 1 time: <b>500</b>
• Max images per 1 time: <b>1000</b>
• 1 Download max time: <b>2 hours</b>
• 🔞 NSFW content is paid! 1⭐️ = $0.02
• 🆓 ALL OTHER MEDIA ARE TOTALY FREE
• 📝 All content logs & caching to my log-channels for instant repost when re-downloading</blockquote>

💬<b>This limits only for video with subtitles:</b>
<blockquote>• Max video+subs duration: <b>1.5 hours</b>
• Max video+subs file size: <b>500 MB</b>
• Max video+subs quality: <b>720p</b></blockquote>
————————————
🚀 <b>Paid Group Benefits (2️⃣x Limits):</b>
<blockquote>•  🗂 Structured neat media vault sorted by topics 👍
•  📁 Bots reply in the topic you call them
•  📌 Auto pin status message with download progress
•  🖼 /img command downloads media as 10-item albums
• Max 1 file size: <b>16 GB</b> ⬆️
• Max playlist items per 1 time: <b>100</b> ⬆️
• Max TikTok videos per 1 time: 1000 ⬆️
• Max images per 1 time: 2000 ⬆️
• 1 Download max time: <b>4 hours</b> ⬆️
• 🔞 NSFW content: Free with full metadata 🆓
• 📢 No need to subscribe to my channel for groups
• 👥 All group members will have access to paid functions!
• 🗒 No logs / no cache to my log-channels! You can reject copy/repost in group settings</blockquote>

💬 <b>2️⃣x limits for video with subtitles:</b>
<blockquote>• Max video+subs duration: <b>3 hours</b> ⬆️
• Max video+subs file size: <b>1000 MB</b> ⬆️
• Max video+subs quality: <b>1080p</b> ⬆️</blockquote>
————————————
💰 <b>Pricing & Setup:</b>
<blockquote>• Price: <b>$5/month</b> per 1 bot in group
• Setup: Contact @iilililiiillliiliililliilliliiil
• Payment: 💎TON or other methods💲
• Support: Full technical support included</blockquote>
————————————
You can add my bots to your group to unblock free 🔞<b>NSFW</b> and to double (x2️⃣) all limits.
Contact me if you want me to allow your group to use my bots @iilililiiillliiliililliilliliiil
————————————
💡<b>TIP:</b> <blockquote>You can chip in money with any amount of your friends (for example 100 people) and made 1 purchase for whole group - ALL GROUP MEMBERS WILL HAVE FULL UNLIMITED ACCESS to all bots functions in that group for just <b>0.05$</b></blockquote>
    """
    
    # NSFW Command Messages
    NSFW_ON_MSG = """
🔞 <b>NSFW Mode: ON✅</b>

• NSFW content will be displayed without blurring.
• Spoilers will not apply to NSFW media.
• The content will be visible immediately

<i>Use /nsfw off to enable blur</i>
    """
    
    NSFW_OFF_MSG = """
🔞 <b>NSFW Mode: OFF</b>

⚠️ <b>Blur enabled</b>
• NSFW content will be hidden under spoiler   
• To view, you will need to click on the media
• Spoilers will apply to NSFW media.

<i>Use /nsfw on to disable blur</i>
    """
    
    NSFW_INVALID_MSG = """
❌ <b>Invalid parameter</b>

Use:
• <code>/nsfw on</code> - disable blur
• <code>/nsfw off</code> - enable blur
    """
    
    # UI Messages - Status and Progress
    CHECKING_CACHE_MSG = "🔄 <b>Checking cache...</b>\n\n<code>{url}</code>"
    PROCESSING_MSG = "🔄 Processing..."
    DOWNLOADING_MSG = "📥 <b>Downloading media...</b>\n\n"
    DOWNLOADING_VIDEO_MSG = "📥 <b>Downloading video...</b>\n\n"
    DOWNLOADING_IMAGE_MSG = "📥 <b>Downloading image...</b>\n\n"
    UPLOAD_COMPLETE_MSG = "✅ <b>Upload complete</b> - {count} files uploaded.\n{credits}"
    DOWNLOAD_COMPLETE_MSG = "✅ <b>Download complete</b>\n\n"
    VIDEO_PROCESSING_MSG = "📽 Video is processing..."
    WAITING_HOURGLASS_MSG = "⌛️"
    
    # Cache Messages
    SENT_FROM_CACHE_MSG = "✅ <b>Sent from cache</b>\n\nSent albums: <b>{count}</b>"
    VIDEO_SENT_FROM_CACHE_MSG = "✅ Video successfully sent from cache."
    PLAYLIST_SENT_FROM_CACHE_MSG = "✅ Playlist videos sent from cache ({cached}/{total} files)."
    CACHE_PARTIAL_MSG = "📥 {cached}/{total} videos sent from cache, downloading missing ones..."
    CACHE_FAILED_VIDEO_MSG = "⚠️ Unable to get video from cache, starting new download..."
    CACHE_FAILED_GENERIC_MSG = "⚠️ Failed to get video from cache, starting a new download..."
    
    # Error Messages
    INVALID_URL_MSG = "❌ <b>Invalid URL</b>\n\nPlease provide a valid URL starting with http:// or https://"
    FAILED_ANALYZE_MSG = "❌ <b>Failed to analyze image</b>\n\n<code>{url}</code>\n\n"
    ERROR_OCCURRED_MSG = "❌ <b>Error occurred</b>\n\n<code>{url}</code>\n\nError: {error}"
    ERROR_DOWNLOAD_MSG = "❌ Sorry... Some error occurred during download."
    ERROR_SENDING_VIDEO_MSG = "❌ Error sending video: {error}"
    ERROR_UNKNOWN_MSG = "❌ Unknown error: {error}"
    ERROR_NO_DISK_SPACE_MSG = "❌ Not enough disk space to download videos."
    ERROR_FILE_SIZE_LIMIT_MSG = "❌ The file size exceeds the {limit} GB limit. Please select a smaller file within the allowed size."
    ERROR_NO_VIDEOS_PLAYLIST_MSG = "❌ No videos found in playlist at index {index}."
    ERROR_TIKTOK_API_MSG = "⚠️ TikTok API error at index {index}, skipping to next video..."
    ERROR_FFMPEG_NOT_FOUND_MSG = "❌ FFmpeg not found. Please install FFmpeg."
    ERROR_CONVERSION_FAILED_MSG = "❌ Conversion to MP4 failed: {error}"
    ERROR_GETTING_LINK_MSG = "❌ <b>Error getting link:</b>\n{error}"
    ERROR_AV1_NOT_AVAILABLE_MSG = "❌ AV1 format is not available for this video.\n\nAvailable formats:\n{formats}"
    ERROR_AV1_NOT_AVAILABLE_SHORT_MSG = "❌ **AV1 format is not available for this video.**\n\n"
    
    # Telegram Rate Limit Messages
    RATE_LIMIT_WITH_TIME_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: {time}\nTo update timer send URL again 2 times."
    RATE_LIMIT_NO_TIME_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: \nTo update timer send URL again 2 times."
    
    # Subtitles Messages
    SUBTITLES_FAILED_MSG = "⚠️ Failed to download subtitles"
    SUBTITLES_NOT_FOUND_MSG = "⚠️ Subtitles for {flag} {name} not found for this video. Download without subtitles."
    SUBTITLES_EMBEDDING_MSG = "⚠️ Embedding subtitles may take a long time (up to 1 min per 1 min of video)!\n🔥 Starting to burn subtitles..."
    SUBTITLES_SUCCESS_MSG = "Subtitles successfully embedded! ✅"
    SUBTITLES_NOT_FOUND_VIDEO_MSG = "⚠️ Subtitles not found for this video"
    SUBTITLES_SIZE_LIMIT_MSG = "⚠️ Subtitles not embedded: exceeded size/duration limits"
    
    # Video Processing Messages
    HLS_STREAM_MSG = "Detected HLS stream.\n📥 Downloading..."
    DOWNLOADING_FORMAT_MSG = "> <i>📥 Downloading using format: {format}...</i>"
    DOWNLOADED_PROCESSING_MSG = "☑️ Downloaded video.\n📤 Processing for upload..."
    FILE_TOO_LARGE_MSG = "⚠️ Your video size ({size}) is too large.\nSplitting file... ✂️"
    SPLIT_PART_UPLOADED_MSG = "📤 Splitted part {part} file uploaded"
    
    # Stream/Link Messages
    STREAM_LINKS_TITLE_MSG = "🔗 <b>Direct Stream Links</b>\n\n"
    STREAM_TITLE_MSG = "📹 <b>Title:</b> {title}\n"
    STREAM_DURATION_MSG = "⏱ <b>Duration:</b> {duration} sec\n"
    STREAM_FORMAT_MSG = "🎛 <b>Format:</b> <code>bv+ba/best</code>\n\n"
    STREAM_BROWSER_MSG = "🌐 <b>Browser:</b> Open in web browser\n\n"
    VLC_PLAYER_IOS_MSG = "🎬 <b><a href=\"https://itunes.apple.com/app/apple-store/id650377962\">VLC Player (iOS)</a></b>\n\n<i>Click button to copy stream URL, then paste it in VLC app</i>"
    VLC_PLAYER_ANDROID_MSG = "🎬 <b><a href=\"https://play.google.com/store/apps/details?id=org.videolan.vlc\">VLC Player (Android)</a></b>\n\n<i>Click button to copy stream URL, then paste it in VLC app</i>"
    
    # Download Progress Messages
    DOWNLOADING_FORMAT_ID_MSG = "📥 Downloading format {format_id}..."
    DOWNLOADING_QUALITY_MSG = "📥 Downloading {quality}..."
    
    # Quality Selection Messages
    MANUAL_QUALITY_TITLE_MSG = "🎛 Manual Quality Selection"
    MANUAL_QUALITY_DESC_MSG = "Choose quality manually since automatic detection failed:"
    ALL_FORMATS_TITLE_MSG = "🎛 All Available Formats"
    ALL_FORMATS_PAGE_MSG = "Page {page}"
    CACHED_QUALITIES_TITLE_MSG = "📹 Available Qualities (from cache)"
    CACHED_QUALITIES_DESC_MSG = "⚠️ Using cached qualities - new formats may not be available"
    ERROR_GETTING_FORMATS_MSG = "❌ Error getting available formats.\nPlease try again later."
    
    # NSFW Paid Content Messages
    NSFW_PAID_WARNING_MSG = "⭐️ — 🔞NSFW is paid (⭐️$0.02)\nUse /add_bot_to_group to make NSFW free"
    NSFW_PAID_INFO_MSG = "⭐️ — 🔞NSFW is paid (⭐️$0.02)\nUse /add_bot_to_group to make NSFW free"
    
    # Callback Error Messages
    ERROR_ORIGINAL_NOT_FOUND_MSG = "❌ Error: Original message not found."
    ERROR_ORIGINAL_NOT_FOUND_DELETED_MSG = "❌ Error: Original message not found. It might have been deleted. Please send the link again."
    ERROR_URL_NOT_FOUND_MSG = "❌ Error: URL not found."
    ERROR_ORIGINAL_URL_NOT_FOUND_MSG = "❌ Error: Original URL not found. Please send the link again."
    ERROR_URL_NOT_EMBEDDABLE_MSG = "❌ This URL cannot be embedded."
    ERROR_CODEC_NOT_AVAILABLE_MSG = "❌ {codec} codec not available for this video"
    ERROR_FORMAT_NOT_AVAILABLE_MSG = "❌ {format} format not available for this video"
    
    # Tags Error Messages
    TAG_FORBIDDEN_CHARS_MSG = "❌ Tag #{tag} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}"
    
    # Playlist Messages
    PLAYLIST_SENT_MSG = "✅ Playlist videos sent: {sent}/{total} files."
    PLAYLIST_CACHE_SENT_MSG = "✅ Sent from cache: {cached}/{total} files."
    
    # Failed Stream Messages
    FAILED_STREAM_LINKS_MSG = "❌ Failed to get stream links"

    # new messages
    # Browser Cookie Messages
    SELECT_BROWSER_MSG = "Select a browser to download cookies from:"
    SELECT_BROWSER_NO_BROWSERS_MSG = "No browsers found on this system. You can download cookies from remote URL or monitor browser status:"
    BROWSER_MONITOR_HINT_MSG = "🌐 <b>Open Browser</b> - to monitor browser status in mini-app"
    BROWSER_OPEN_BUTTON_MSG = "🌐 Open Browser"
    DOWNLOAD_FROM_URL_BUTTON_MSG = "📥 Download from Remote URL"
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTube cookie file downloaded via fallback and saved as cookie.txt"
    BROWSER_CHOICE_UPDATED_MSG = "✅ Browser choice updated."
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ No supported browsers found and no COOKIE_URL configured. Use /cookie or upload cookie.txt."
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ Fallback COOKIE_URL must point to a .txt file."
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ Fallback cookie file is too large (>100KB)."
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_ERROR_MSG = "❌ Error downloading fallback cookie. Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ Unexpected error during fallback cookie download."
    BTN_CLOSE = "🔚Close"
    
    # Args command messages
    ARGS_INVALID_BOOL_MSG = "❌ Invalid boolean value"
    ARGS_CLOSED_MSG = "Closed"
    ARGS_ALL_RESET_MSG = "✅ All arguments reset"
    ARGS_RESET_ERROR_MSG = "❌ Error resetting arguments"
    ARGS_INVALID_PARAM_MSG = "❌ Invalid parameter"
    ARGS_BOOL_SET_MSG = "Set to {value}"
    ARGS_BOOL_ALREADY_SET_MSG = "Already set to {value}"
    ARGS_INVALID_SELECT_MSG = "❌ Invalid select value"
    ARGS_VALUE_SET_MSG = "Set to {value}"
    ARGS_VALUE_ALREADY_SET_MSG = "Already set to {value}"
    ARGS_PARAM_DESCRIPTION_MSG = "<b>📝 {description}</b>\n\n"
    ARGS_CURRENT_VALUE_MSG = "<b>Current value:</b> <code>{current_value}</code>\n\n"
    ARGS_XFF_EXAMPLES_MSG = "<b>Examples:</b>\n• <code>default</code> - Use default XFF strategy\n• <code>never</code> - Never use XFF header\n• <code>US</code> - United States country code\n• <code>GB</code> - United Kingdom country code\n• <code>DE</code> - Germany country code\n• <code>FR</code> - France country code\n• <code>JP</code> - Japan country code\n• <code>192.168.1.0/24</code> - IP block (CIDR)\n• <code>10.0.0.0/8</code> - Private IP range\n• <code>203.0.113.0/24</code> - Public IP block\n\n"
    ARGS_XFF_NOTE_MSG = "<b>Note:</b> This replaces --geo-bypass options. Use any 2-letter country code or IP block in CIDR notation.\n\n"
    ARGS_EXAMPLE_MSG = "<b>Example:</b> <code>{placeholder}</code>\n\n"
    ARGS_SEND_VALUE_MSG = "Please send your new value."
    ARGS_NUMBER_PARAM_MSG = "<b>🔢 {description}</b>\n\n"
    ARGS_RANGE_MSG = "<b>Range:</b> {min_val} - {max_val}\n\n"
    ARGS_SEND_NUMBER_MSG = "Please send a number."
    ARGS_JSON_PARAM_MSG = "<b>🔧 {description}</b>\n\n"
    ARGS_HTTP_HEADERS_EXAMPLES_MSG = "<b>Examples:</b>\n<code>{placeholder}</code>\n<code>{{\"X-API-Key\": \"your-key\"}}</code>\n<code>{{\"Authorization\": \"Bearer token\"}}</code>\n<code>{{\"Accept\": \"application/json\"}}</code>\n<code>{{\"X-Custom-Header\": \"value\"}}</code>\n\n"
    ARGS_HTTP_HEADERS_NOTE_MSG = "<b>Note:</b> These headers will be added to existing Referer and User-Agent headers.\n\n"
    ARGS_CURRENT_ARGS_MSG = "<b>📋 Current yt-dlp Arguments:</b>\n\n"
    ARGS_MENU_DESCRIPTION_MSG = "• ✅/❌ <b>Boolean</b> - True/False switches\n• 📋 <b>Select</b> - Choose from options\n• 🔢 <b>Numeric</b> - Number input\n• 📝🔧 <b>Text</b> - Text/JSON input</blockquote>\n\nThese settings will be applied to all your downloads."
    ARGS_CONFIG_TITLE_MSG = "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n<blockquote>📋 <b>Groups:</b>\n{groups_msg}"
    ARGS_MENU_TEXT = (
        "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
        "<blockquote>📋 <b>Groups:</b>\n"
        "• ✅/❌ <b>Boolean</b> - True/False switches\n"
        "• 📋 <b>Select</b> - Choose from options\n"
        "• 🔢 <b>Numeric</b> - Number input\n"
        "• 📝🔧 <b>Text</b> - Text/JSON input</blockquote>\n\n"
        "These settings will be applied to all your downloads."
    )
    
    # Additional missing messages
    PLEASE_WAIT_MSG = "⏳ Please wait..."
    ERROR_OCCURRED_SHORT_MSG = "❌ Error occurred"
    MANUAL_QUALITY_TITLE_MSG = "🎛 Manual Quality Selection"
    
    # Args command messages (continued)
    ARGS_INPUT_TIMEOUT_MSG = "⏰ Input mode automatically closed due to inactivity (5 minutes)."
    ARGS_INPUT_DANGEROUS_MSG = "❌ Input contains potentially dangerous content: {pattern}"
    ARGS_INPUT_TOO_LONG_MSG = "❌ Input too long (max 1000 characters)"
    ARGS_INVALID_URL_MSG = "❌ Invalid URL format. Must start with http:// or https://"
    ARGS_INVALID_JSON_MSG = "❌ Invalid JSON format"
    ARGS_NUMBER_RANGE_MSG = "❌ Number must be between {min_val} and {max_val}"
    ARGS_INVALID_NUMBER_MSG = "❌ Invalid number format"
    ARGS_DATE_FORMAT_MSG = "❌ Date must be in YYYYMMDD format (e.g., 20230930)"
    ARGS_YEAR_RANGE_MSG = "❌ Year must be between 1900 and 2100"
    ARGS_MONTH_RANGE_MSG = "❌ Month must be between 01 and 12"
    ARGS_DAY_RANGE_MSG = "❌ Day must be between 01 and 31"
    ARGS_INVALID_DATE_MSG = "❌ Invalid date format"
    ARGS_INVALID_XFF_MSG = "❌ XFF must be 'default', 'never', country code (e.g., US), or IP block (e.g., 192.168.1.0/24)"
    ARGS_NO_CUSTOM_MSG = "No custom arguments set. All parameters use default values."
    ARGS_RESET_SUCCESS_MSG = "✅ All arguments reset to defaults."
    ARGS_TEXT_TOO_LONG_MSG = "❌ Text too long. Maximum 500 characters."
    ARGS_JSON_OBJECT_MSG = "❌ JSON must be an object (dictionary)."
    ARGS_INVALID_JSON_INPUT_MSG = "❌ Invalid JSON format. Please provide valid JSON."
    ARGS_BOOL_INPUT_MSG = "❌ Please enter 'True' or 'False' for Send As File option."
    ARGS_VALUE_RANGE_MSG = "❌ Value must be between {min_val} and {max_val}."
    ARGS_INVALID_NUMBER_INPUT_MSG = "❌ Please provide a valid number."
    ARGS_ERROR_PROCESSING_MSG = "❌ Error processing input. Please try again."
    
    # Tags command messages
    TAGS_NO_TAGS_MSG = "You have no tags yet."
    TAGS_MESSAGE_CLOSED_MSG = "Tags message closed."
    
    # Subtitles command messages
    SUBS_DISABLED_MSG = "✅ Subtitles disabled and Always Ask mode turned off."
    SUBS_ALWAYS_ASK_ENABLED_MSG = "✅ SUBS Always Ask enabled."
    SUBS_LANGUAGE_SET_MSG = "✅ Subtitle language set to: {flag} {name}"
    SUBS_LANGUAGE_AUTO_SET_MSG = "✅ Subtitle language set to: {flag} {name} with AUTO/TRANS enabled."
    SUBS_INVALID_ARG_MSG = (
        "❌ **Invalid argument!**\n\n"
        "Valid options:\n"
        "• `/subs off` - disable subtitles\n"
        "• `/subs on` - enable Always Ask mode\n"
        "• `/subs ru` - set language (any language code)\n"
        "• `/subs ru auto` - set language with AUTO/TRANS enabled\n\n"
        "Example: `/subs en auto`"
    )
    SUBS_SETTINGS_TITLE_MSG = "<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:\n\n"
    SUBS_WARNING_MSG = (
        "<blockquote>❗️WARNING: due to high CPU impact this function is very slow (near real-time) and limited to:\n"
        "- 720p max quality\n"
        "- 1.5 hour max duration\n"
        "- 500mb max video size</blockquote>\n\n"
    )
    SUBS_QUICK_COMMANDS_MSG = (
        "<b>Quick commands:</b>\n"
        "• <code>/subs off</code> - disable subtitles\n"
        "• <code>/subs on</code> - enable Always Ask mode\n"
        "• <code>/subs ru</code> - set language\n"
        "• <code>/subs ru auto</code> - set language with AUTO/TRANS"
    )
    SUBS_DISABLED_STATUS_MSG = "🚫 Subtitles are disabled"
    SUBS_SELECTED_LANGUAGE_MSG = "{flag} Selected language: {name}{auto_text}"
    SUBS_AUTO_MODE_TOGGLED_MSG = "✅ Auto-subs mode {status}"
    SUBS_ALWAYS_ASK_TOGGLED_MSG = "✅ Always Ask mode {status}"
    SUBS_LANGUAGE_MENU_CLOSED_MSG = "Subtitle language menu closed."
    SUBS_DOWNLOADING_MSG = "💬 Downloading subtitles..."
    SUBS_DISABLED_ERROR_MSG = "❌ Subtitles are disabled. Use /subs to configure."
    SUBS_YOUTUBE_ONLY_MSG = "❌ Subtitle downloading is only supported for YouTube."
    SUBS_CAPTION_MSG = (
        "<b>💬 Subtitles</b>\n\n"
        "<b>Video:</b> {title}\n"
        "<b>Language:</b> {lang}\n"
        "<b>Type:</b> {type}\n\n"
        "{tags}"
    )
    SUBS_SENT_MSG = "💬 Subtitles SRT-file sent to user."
    SUBS_ERROR_PROCESSING_MSG = "❌ Error processing subtitle file."
    SUBS_ERROR_DOWNLOAD_MSG = "❌ Failed to download subtitles."
    SUBS_ERROR_MSG = "❌ Error downloading subtitles: {error}"
    
    # Split command messages
    SPLIT_SIZE_SET_MSG = "✅ Split part size set to: {size}"
    SPLIT_INVALID_SIZE_MSG = (
        "❌ **Invalid size!**\n\n"
        "**Valid range:** 100MB to 2GB\n\n"
        "**Valid formats:**\n"
        "• `100mb` to `2000mb` (megabytes)\n"
        "• `0.1gb` to `2gb` (gigabytes)\n\n"
        "**Examples:**\n"
        "• `/split 100mb` - 100 megabytes\n"
        "• `/split 500mb` - 500 megabytes\n"
        "• `/split 1.5gb` - 1.5 gigabytes\n"
        "• `/split 2gb` - 2 gigabytes\n"
        "• `/split 2000mb` - 2000 megabytes (2GB)\n\n"
        "**Presets:**\n"
        "• `/split 250mb`, `/split 500mb`, `/split 1gb`, `/split 1.5gb`, `/split 2gb`"
    )
    SPLIT_MENU_TITLE_MSG = (
        "🎬 **Choose max part size for video splitting:**\n\n"
        "**Range:** 100MB to 2GB\n\n"
        "**Quick commands:**\n"
        "• `/split 100mb` - `/split 2000mb`\n"
        "• `/split 0.1gb` - `/split 2gb`\n\n"
        "**Examples:** `/split 300mb`, `/split 1.2gb`, `/split 1500mb`"
    )
    SPLIT_MENU_CLOSED_MSG = "Menu closed."
    SPLIT_SELECTION_CLOSED_MSG = "Split selection closed."
    SPLIT_INVALID_SIZE_ERROR_MSG = "Invalid size."
    
    # Settings command messages
    SETTINGS_TITLE_MSG = "<b>Bot Settings</b>\n\nChoose a category:"
    SETTINGS_MENU_CLOSED_MSG = "Menu closed."
    SETTINGS_CLEAN_TITLE_MSG = "<b>🧹 Clean Options</b>\n\nChoose what to clean:"
    SETTINGS_COOKIES_TITLE_MSG = "<b>🍪 COOKIES</b>\n\nChoose an action:"
    SETTINGS_MEDIA_TITLE_MSG = "<b>🎞 MEDIA</b>\n\nChoose an action:"
    SETTINGS_LOGS_TITLE_MSG = "<b>📖 INFO</b>\n\nChoose an action:"
    SETTINGS_MORE_TITLE_MSG = "<b>⚙️ MORE COMMANDS</b>\n\nChoose an action:"
    SETTINGS_COMMAND_EXECUTED_MSG = "Command executed."
    SETTINGS_FLOOD_LIMIT_MSG = "⏳ Flood limit. Try later."
    SETTINGS_HINT_SENT_MSG = "Hint sent."
    SETTINGS_SEARCH_HELPER_OPENED_MSG = "Search helper opened."
    SETTINGS_UNKNOWN_COMMAND_MSG = "Unknown command."
    SETTINGS_HINT_CLOSED_MSG = "Hint closed."
    
    # Search command messages
    SEARCH_HELPER_CLOSED_MSG = "🔍 Search helper closed"
    SEARCH_CALLBACK_ERROR_MSG = "Search callback error: {error}"
    SEARCH_CLOSED_MSG = "Closed"
    
    # Proxy command messages
    PROXY_ENABLED_MSG = "✅ Proxy {status}."
    PROXY_ERROR_SAVING_MSG = "❌ Error saving proxy settings."
    PROXY_MENU_TEXT_MSG = "Enable or disable using proxy server for all yt-dlp operations?"
    PROXY_MENU_TEXT_MULTIPLE_MSG = "Enable or disable using proxy servers ({count} available) for all yt-dlp operations?\n\nWhen enabled, proxies will be selected using {method} method."
    PROXY_MENU_CLOSED_MSG = "Menu closed."
    PROXY_ENABLED_CONFIRM_MSG = "✅ Proxy enabled. All yt-dlp operations will use proxy."
    PROXY_ENABLED_MULTIPLE_MSG = "✅ Proxy enabled. All yt-dlp operations will use {count} proxy servers with {method} selection method."
    PROXY_DISABLED_MSG = "❌ Proxy disabled."
    PROXY_ERROR_SAVING_CALLBACK_MSG = "❌ Error saving proxy settings."
    PROXY_ENABLED_CALLBACK_MSG = "Proxy enabled."
    PROXY_DISABLED_CALLBACK_MSG = "Proxy disabled."
    
    # Other handlers messages
    AUDIO_WAIT_MSG = "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED"
    AUDIO_HELP_MSG = (
        "<b>🎧 Audio Download Command</b>\n\n"
        "Usage: <code>/audio URL</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/audio https://youtu.be/abc123</code>\n"
        "• <code>/audio https://www.youtube.com/watch?v=abc123</code>\n"
        "• <code>/audio https://www.youtube.com/playlist?list=PL123*1*10</code>\n"
        "• <code>/audio 1-10 https://www.youtube.com/playlist?list=PL123</code>\n\n"
        "Also see: /vid, /img, /help, /playlist, /settings"
    )
    AUDIO_HELP_CLOSED_MSG = "Audio hint closed."
    PLAYLIST_HELP_CLOSED_MSG = "Playlist help closed."
    USERLOGS_CLOSED_MSG = "Logs message closed."
    HELP_CLOSED_MSG = "Help closed."
    
    # NSFW command messages
    NSFW_BLUR_SETTINGS_TITLE_MSG = "🔞 <b>NSFW Blur Settings</b>\n\nNSFW content is <b>{status}</b>.\n\nChoose whether to blur NSFW content:"
    NSFW_MENU_CLOSED_MSG = "Menu closed."
    NSFW_BLUR_DISABLED_MSG = "NSFW blur disabled."
    NSFW_BLUR_ENABLED_MSG = "NSFW blur enabled."
    NSFW_BLUR_DISABLED_CALLBACK_MSG = "NSFW blur disabled."
    NSFW_BLUR_ENABLED_CALLBACK_MSG = "NSFW blur enabled."
    
    # MediaInfo command messages
    MEDIAINFO_ENABLED_MSG = "✅ MediaInfo {status}."
    MEDIAINFO_MENU_TITLE_MSG = "Enable or disable sending MediaInfo for downloaded files?"
    MEDIAINFO_MENU_CLOSED_MSG = "Menu closed."
    MEDIAINFO_ENABLED_CONFIRM_MSG = "✅ MediaInfo enabled. After downloading, file info will be sent."
    MEDIAINFO_DISABLED_MSG = "❌ MediaInfo disabled."
    MEDIAINFO_ENABLED_CALLBACK_MSG = "MediaInfo enabled."
    MEDIAINFO_DISABLED_CALLBACK_MSG = "MediaInfo disabled."
    MEDIAINFO_ERROR_MSG = "❌ Error sending MediaInfo: {error}"
    
    # List command messages
    LIST_HELP_MSG = (
        "<b>📃 List Available Formats</b>\n\n"
        "Get available video/audio formats for a URL.\n\n"
        "<b>Usage:</b>\n"
        "<code>/list URL</code>\n\n"
        "<b>Examples:</b>\n"
        "• <code>/list https://youtube.com/watch?v=123abc</code>\n"
        "• <code>/list https://youtube.com/playlist?list=123abc</code>\n\n"
        "<b>💡 How to use format IDs:</b>\n"
        "After getting the list, use specific format ID:\n"
        "• <code>/format id 401</code> - download format 401\n"
        "• <code>/format id401</code> - same as above\n\n"
        "This command will show all available formats that can be downloaded."
    )
    LIST_PROCESSING_MSG = "🔄 Getting available formats..."
    LIST_INVALID_URL_MSG = "❌ Please provide a valid URL starting with http:// or https://"
    LIST_CAPTION_MSG = (
        "📃 Available formats for:\n<code>{url}</code>\n\n"
        "💡 <b>How to set format:</b>\n"
        "• <code>/format id 134</code> - Download specific format ID\n"
        "• <code>/format 720p</code> - Download by quality\n"
        "• <code>/format best</code> - Download best quality\n"
        "• <code>/format ask</code> - Always ask for quality\n\n"
        "{audio_note}\n"
        "📋 Use format ID from the list above"
    )
    LIST_AUDIO_FORMATS_MSG = (
        "🎵 <b>Audio-only formats:</b> {formats}\n"
        "• <code>/format id 140 audio</code> - Download format 140 as MP3 audio\n"
        "• <code>/format id140 audio</code> - same as above\n"
        "These will be downloaded as MP3 audio files.\n\n"
    )
    LIST_ERROR_SENDING_MSG = "❌ Error sending formats file: {error}"
    LIST_ERROR_GETTING_MSG = "❌ Failed to get formats:\n<code>{error}</code>"
    LIST_ERROR_OCCURRED_MSG = "❌ An error occurred while processing the command"
    LIST_HELP_CLOSED_MSG = "Help closed"
    LIST_ERROR_CALLBACK_MSG = "Error occurred"
    
    # Link command messages
    LINK_USAGE_MSG = (
        "🔗 <b>Usage:</b>\n"
        "<code>/link [quality] URL</code>\n\n"
        "<b>Examples:</b>\n"
        "<blockquote>"
        "• /link https://youtube.com/watch?v=... - best quality\n"
        "• /link 720 https://youtube.com/watch?v=... - 720p or lower\n"
        "• /link 720p https://youtube.com/watch?v=... - same as above\n"
        "• /link 4k https://youtube.com/watch?v=... - 4K or lower\n"
        "• /link 8k https://youtube.com/watch?v=... - 8K or lower"
        "</blockquote>\n\n"
        "<b>Quality:</b> from 1 to 10000 (e.g., 144, 240, 720, 1080)"
    )
    LINK_INVALID_URL_MSG = "❌ Please provide a valid URL"
    LINK_PROCESSING_MSG = "🔗 Getting direct link..."
    LINK_SUCCESS_MSG = (
        "🔗 <b>Direct link obtained</b>\n\n"
        "📹 <b>Title:</b> {title}\n"
        "{duration}"
        "🎛 <b>Format:</b> <code>{format}</code>\n\n"
        "{video_url}"
        "{audio_url}"
        "{error}"
    )
    LINK_DURATION_MSG = "⏱ <b>Duration:</b> {duration} sec\n"
    LINK_VIDEO_STREAM_MSG = "🎬 <b>Video stream:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    LINK_AUDIO_STREAM_MSG = "🎵 <b>Audio stream:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    LINK_NO_STREAMS_MSG = "❌ Failed to get stream links"
    LINK_ERROR_MSG = "❌ <b>Error getting link:</b>\n{error}"
    LINK_ERROR_OCCURRED_MSG = "❌ An error occurred: {error}"
    
    # Keyboard command messages
    KEYBOARD_UPDATED_MSG = "🎹 **Keyboard setting updated!**\n\nNew setting: **{setting}**"
    KEYBOARD_INVALID_ARG_MSG = (
        "❌ **Invalid argument!**\n\n"
        "Valid options: `off`, `1x3`, `2x3`, `full`\n\n"
        "Example: `/keyboard off`"
    )
    KEYBOARD_SETTINGS_MSG = (
        "🎹 **Keyboard Settings**\n\n"
        "Current: **{current}**\n\n"
        "Choose an option:\n\n"
        "Or use: `/keyboard off`, `/keyboard 1x3`, `/keyboard 2x3`, `/keyboard full`"
    )
    KEYBOARD_ACTIVATED_MSG = "🎹 keyboard activated!"
    KEYBOARD_HIDDEN_MSG = "⌨️ Keyboard hidden"
    KEYBOARD_1X3_ACTIVATED_MSG = "📱 1x3 keyboard activated!"
    KEYBOARD_2X3_ACTIVATED_MSG = "📱 2x3 keyboard activated!"
    KEYBOARD_EMOJI_ACTIVATED_MSG = "🔣 Emoji keyboard activated!"
    KEYBOARD_ERROR_MSG = "Error processing setting"
    KEYBOARD_ERROR_APPLYING_MSG = "Error applying keyboard setting {setting}: {error}"
    
    # Format command messages
    FORMAT_ALWAYS_ASK_SET_MSG = "✅ Format set to: Always Ask. You will be prompted for quality each time you send a URL."
    FORMAT_BEST_UPDATED_MSG = "✅ Format updated to best quality (AVC+MP4 priority):\n{format}"
    FORMAT_ID_UPDATED_MSG = "✅ Format updated to ID {id}:\n{format}\n\n💡 <b>Note:</b> If this is an audio-only format, it will be downloaded as MP3 audio file."
    FORMAT_ID_AUDIO_UPDATED_MSG = "✅ Format updated to ID {id} (audio-only):\n{format}\n\n💡 This will be downloaded as MP3 audio file."
    FORMAT_QUALITY_UPDATED_MSG = "✅ Format updated to quality {quality}:\n{format}"
    FORMAT_CUSTOM_UPDATED_MSG = "✅ Format updated to:\n{format}"
    FORMAT_MENU_MSG = (
        "Select a format option or send a custom one using:\n"
        "• <code>/format &lt;format_string&gt;</code> - custom format\n"
        "• <code>/format 720</code> - 720p quality\n"
        "• <code>/format 4k</code> - 4K quality\n"
        "• <code>/format 8k</code> - 8K quality\n"
        "• <code>/format id 401</code> - specific format ID\n"
        "• <code>/format ask</code> - always show menu\n"
        "• <code>/format best</code> - bv+ba/best quality"
    )
    FORMAT_CUSTOM_HINT_MSG = (
        "To use a custom format, send the command in the following form:\n\n"
        "<code>/format bestvideo+bestaudio/best</code>\n\n"
        "Replace <code>bestvideo+bestaudio/best</code> with your desired format string."
    )
    FORMAT_RESOLUTION_MENU_MSG = "Select your desired resolution and codec:"
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "✅ Format set to: Always Ask. Now you will be prompted for quality each time you send a URL."
    FORMAT_UPDATED_MSG = "✅ Format updated to:\n{format}"
    FORMAT_SAVED_MSG = "✅ Format saved."
    FORMAT_CHOICE_UPDATED_MSG = "✅ Format choice updated."
    FORMAT_CUSTOM_MENU_CLOSED_MSG = "Custom format menu closed"
    FORMAT_CODEC_SET_MSG = "✅ Codec set to {codec}"
    FORMAT_MKV_TOGGLED_MSG = "MKV is now {status}"
    
    # Cookies command messages
    COOKIES_BROWSER_SELECTION_MSG = "Select a browser to download cookies from:"
    COOKIES_NO_BROWSERS_MSG = "No browsers found on this system. You can download cookies from remote URL or monitor browser status:"
    COOKIES_BROWSER_MONITOR_HINT_MSG = "🌐 <b>Open Browser</b> - to monitor browser status in mini-app"
    COOKIES_DOWNLOADING_MSG = "📥 Downloading cookies from remote URL..."
    COOKIES_DOWNLOADED_SUCCESS_MSG = "✅ YouTube cookie file downloaded via fallback and saved as cookie.txt"
    COOKIES_DOWNLOADED_ERROR_MSG = "❌ No COOKIE_URL configured. Use /cookie or upload cookie.txt."
    COOKIES_INVALID_FORMAT_MSG = "❌ Fallback COOKIE_URL must point to a .txt file."
    COOKIES_TOO_LARGE_MSG = "❌ Fallback cookie file is too large (>100KB)."
    COOKIES_UNAVAILABLE_MSG = "❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt."
    COOKIES_ERROR_MSG = "❌ Error downloading fallback cookie. Try /cookie or upload cookie.txt."
    COOKIES_UNEXPECTED_ERROR_MSG = "❌ Unexpected error during fallback cookie download."
    COOKIES_BROWSER_CHOICE_UPDATED_MSG = "✅ Browser choice updated."
    
    # Clean command messages
    CLEAN_COOKIES_MSG = "Cookies cleaned."
    CLEAN_LOGS_MSG = "logs cleaned."
    CLEAN_TAGS_MSG = "tags cleaned."
    CLEAN_FORMAT_MSG = "format cleaned."
    CLEAN_SPLIT_MSG = "split cleaned."
    CLEAN_MEDIAINFO_MSG = "mediainfo cleaned."
    CLEAN_SUBS_MSG = "Subtitle settings cleaned."
    CLEAN_KEYBOARD_MSG = "Keyboard settings cleaned."
    CLEAN_ARGS_MSG = "Args settings cleaned."
    CLEAN_NSFW_MSG = "NSFW settings cleaned."
    CLEAN_PROXY_MSG = "Proxy settings cleaned."
    CLEAN_FLOOD_WAIT_MSG = "Flood wait settings cleaned."
    CLEAN_ALL_MSG = "All files cleaned."
    
    # Admin command messages
    ADMIN_ACCESS_DENIED_MSG = "❌ Access denied. Admin only."
    ADMIN_SCRIPT_NOT_FOUND_MSG = "❌ Script not found: {script_path}"
    ADMIN_DOWNLOADING_MSG = "⏳ Downloading fresh Firebase dump using {script_path} ..."
    ADMIN_RELOADING_MSG = "🔄 Reloading Firebase cache into memory..."
    ADMIN_CACHE_RELOADED_MSG = "✅ Firebase cache reloaded successfully!"
    ADMIN_CACHE_FAILED_MSG = "❌ Failed to reload Firebase cache. Check if {cache_file} exists."
    ADMIN_ERROR_RELOADING_MSG = "❌ Error reloading cache: {error}"
    ADMIN_ERROR_SCRIPT_MSG = "❌ Error running {script_path}:\n{stdout}\n{stderr}"
    
    #######################################################
