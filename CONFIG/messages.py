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
    ERROR_NO_DISK_SPACE_AUDIO_MSG = "❌ Not enough disk space to download the audio files."
    ERROR_FILE_SIZE_LIMIT_MSG = "❌ The file size exceeds the {limit} GB limit. Please select a smaller file within the allowed size."
    ERROR_NO_VIDEOS_PLAYLIST_MSG = "❌ No videos found in playlist at index {index}."
    ERROR_TIKTOK_API_MSG = "⚠️ TikTok API error at index {index}, skipping to next video..."
    ERROR_FFMPEG_NOT_FOUND_MSG = "❌ FFmpeg not found. Please install FFmpeg."
    ERROR_CONVERSION_FAILED_MSG = "❌ Conversion to MP4 failed: {error}"
    ERROR_GETTING_LINK_MSG = "❌ <b>Error getting link:</b>\n{error}"
    ERROR_AV1_NOT_AVAILABLE_MSG = "❌ AV1 format is not available for this video.\n\nAvailable formats:\n{formats}"
    ERROR_AV1_NOT_AVAILABLE_SHORT_MSG = "❌ **AV1 format is not available for this video.**\n\n"

    # Generic/Unknown Errors
    UNKNOWN_ERROR_MSG = "❌ Unknown error: {error}"
    ERROR_RUNNING_SCRIPT_MSG = "❌ Error running script: {error}"
    SCRIPT_NOT_FOUND_MSG = "❌ Script not found: {path}"
    SCRIPT_FAILED_WITH_CODE_MSG = "❌ Script failed with return code {code}:\n<code>{error}</code>"
    SCRIPT_COMPLETED_WITH_OUTPUT_MSG = "✅ Script completed successfully!\n\nOutput:\n<code>{output}</code>"
    SCRIPT_COMPLETED_SUCCESS_MSG = "✅ Script completed successfully!"
    
    # Telegram Rate Limit Messages
    RATE_LIMIT_WITH_TIME_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: {time}\nTo update timer send URL again 2 times."
    RATE_LIMIT_NO_TIME_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: \nTo update timer send URL again 2 times."
    PLEASE_WAIT_MSG = "⏳ Please wait..."
    HOURGLASS_PLEASE_WAIT_MSG = "⌛️ Please wait..."
    WAIT_PREV_DOWNLOAD_MSG = "⏰ WAIT UNTIL YOUR PREVIOUS DOWNLOAD IS FINISHED"
    
    # Subtitles Messages
    SUBTITLES_FAILED_MSG = "⚠️ Failed to download subtitles"
    SUBTITLES_DOWNLOAD_IN_PROGRESS_MSG = "💬 Downloading subtitles..."
    SUBTITLES_NOT_FOUND_MSG = "⚠️ Subtitles for {flag} {name} not found for this video. Download without subtitles."
    SUBTITLES_EMBEDDING_MSG = "⚠️ Embedding subtitles may take a long time (up to 1 min per 1 min of video)!\n🔥 Starting to burn subtitles..."
    SUBTITLES_SUCCESS_MSG = "Subtitles successfully embedded! ✅"
    SUBTITLES_NOT_FOUND_VIDEO_MSG = "⚠️ Subtitles not found for this video"
    SUBTITLES_SIZE_LIMIT_MSG = "⚠️ Subtitles not embedded: exceeded size/duration limits"
    SUBTITLES_PROCESSING_FILE_ERROR_MSG = "❌ Error processing subtitle file."

    # Audio Download Messages
    AUDIO_PROCESSING_MSG = "🎙️ Audio is processing..."
    AUDIO_DOWNLOADING_MSG = "📥 Downloading audio:"
    AUDIO_UPLOAD_PROGRESS_MSG = "📤 Uploading audio file..."
    AUDIO_INFO_EXTRACT_FAILED_MSG = "❌ Failed to extract audio information"
    AUDIO_FILE_NOT_FOUND_MSG = "Audio file not found after download."
    AUDIO_SEND_FAILED_MSG = "❌ Failed to send audio: {error}"
    AUDIO_DOWNLOAD_TIMEOUT_MSG = "⏰ Download cancelled due to timeout (2 hours)"
    AUDIO_DOWNLOAD_FAILED_MSG = "❌ Failed to download audio: {error}"
    PLAYLIST_AUDIO_SENT_MSG = "✅Playlist audio sent: {sent}/{total} files."
    
    # Video Processing Messages
    HLS_STREAM_MSG = "Detected HLS stream.\n📥 Downloading..."
    DOWNLOADING_FORMAT_MSG = "> <i>📥 Downloading using format: {format}...</i>"
    DOWNLOADED_PROCESSING_MSG = "☑️ Downloaded video.\n📤 Processing for upload..."
    FILE_TOO_LARGE_MSG = "⚠️ Your video size ({size}) is too large.\nSplitting file... ✂️"
    SPLIT_PART_UPLOADED_MSG = "📤 Splitted part {part} file uploaded"
    DOWNLOAD_STARTED_MSG = "<b>▶️ Download started</b>"
    PROCESSING_GENERIC_MSG = "🔄 Processing..."
    
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
    PLAYLIST_VIDEOS_SENT_MSG = "✅ Playlist videos sent: {sent}/{total} files."
    PLAYLIST_AUDIO_SENT_MSG = "✅ Playlist audio sent: {sent}/{total} files."
    PLAYLIST_AUDIO_SENT_FROM_CACHE_MSG = "✅ Playlist audio sent from cache ({cached}/{total} files)."
    AUDIO_SENT_FROM_CACHE_MSG = "✅ Audio sent from cache."
    AUDIO_CACHE_PARTIAL_MSG = "📥 {cached}/{total} audio sent from cache, downloading missing ones..."
    
    # Failed Stream Messages
    FAILED_STREAM_LINKS_MSG = "❌ Failed to get stream links"

    # Admin and Access Messages
    ACCESS_DENIED_ADMIN_MSG = "❌ Access denied. Admin only."
    BOT_RUNNING_TIME_MSG = "⏳ <i>Bot running time -</i> <b>{uptime}</b>"
    USAGE_BLOCK_USER_MSG = "❌ Usage: /block_user <user_id>"
    USER_BLOCKED_MSG = "User blocked 🔒❌\n \nID: <code>{user_id}</code>\nBlocked Date: {blocked_date}"
    USER_ALREADY_BLOCKED_MSG = "<code>{user_id}</code> is already blocked ❌😐"
    USAGE_UNBLOCK_USER_MSG = "❌ Usage: /unblock_user <user_id>"
    USER_ALREADY_UNBLOCKED_MSG = "<code>{user_id}</code> is already unblocked ✅😐"
    UNCACHE_USAGE_MSG = "❌ Please provide a URL to clear cache for.\nUsage: <code>/uncache &lt;URL&gt;</code>"
    UNCACHE_URL_INVALID_MSG = "❌ Please provide a valid URL.\nUsage: <code>/uncache &lt;URL&gt;</code>"
    UNCACHE_CLEARED_MSG = "✅ Cache cleared successfully for URL:\n<code>{url}</code>"
    UNCACHE_NOT_FOUND_MSG = "ℹ️ No cache found for this link."
    RELOADING_FIREBASE_MSG = "🔄 Reloading Firebase cache into memory..."
    RELOADING_PORN_CACHE_MSG = "⏳ Reloading porn and domain-related caches..."
    RUNNING_PORN_UPDATE_SCRIPT_MSG = "⏳ Running porn list update script: {path}"
    CHECKING_URL_NSFW_MSG = "🔍 Checking URL for NSFW content...\n<code>{url}</code>"
    CHECK_PORN_USAGE_MSG = "❌ Please provide a URL to check.\nUsage: <code>/check_porn &lt;URL&gt;</code>"
    CHECK_PORN_URL_INVALID_MSG = "❌ Please provide a valid URL.\nUsage: <code>/check_porn &lt;URL&gt;</code>"

    # Command Responses
    DIRECT_LINK_GETTING_MSG = "🔗 Getting direct link..."
    KEYBOARD_ACTIVATED_MSG = "🎹 keyboard activated!"
    SPLIT_SIZE_SET_MSG = "✅ Split part size set to: {size}"
    MEDIINFO_SET_MSG = "✅ MediaInfo {state}."
    PROXY_SET_MSG = "✅ Proxy {state}."
    COOKIES_WORKING_OK_MSG = "✅ YouTube cookies are working properly"
    COOKIES_EXPIRED_MSG = "❌ YouTube cookies are expired or invalid\n\nUse /cookie to get new cookies"
    COOKIES_SAVED_BROWSER_MSG = "✅ Cookies saved using browser: {browser}"
    BROWSER_NOT_INSTALLED_MSG = "⚠️ {browser} browser not installed."
    VALID_URL_REQUIRED_MSG = "❌ Please provide a valid URL"

    # Cookies and Browser Messages
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ No supported browsers found and no COOKIE_URL configured. Use /cookie or upload cookie.txt."
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ Fallback COOKIE_URL must point to a .txt file."
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ Fallback cookie file is too large (>100KB)."
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_ERROR_MSG = "❌ Error downloading fallback cookie. Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ Unexpected error during fallback cookie download."
    SELECT_BROWSER_MSG = "Select a browser to download cookies from:"
    BROWSER_NOT_INSTALLED_EDIT_MSG = "⚠️ {browser} browser not installed."
    COOKIES_SAVED_USING_BROWSER_MSG = "✅ Cookies saved using browser: {browser}"
    COOKIES_SAVE_FAILED_MSG = "❌ Failed to save cookies: {error}"
    COOKIE_SOURCE_NOT_CONFIGURED_MSG = "❌ {service} cookie source is not configured!"
    COOKIE_SOURCE_MUST_BE_TXT_MSG = "❌ {service} cookie source must be a .txt file!"
    COOKIE_TOO_LARGE_MSG = "❌ {service} cookie file is too large! Max 100KB, got {size}KB."
    COOKIE_DOWNLOADED_SAVED_MSG = "<b>✅ {service} cookie file downloaded and saved as cookie.txt in your folder.</b>"
    COOKIE_SOURCE_UNAVAILABLE_MSG = "❌ {service} cookie source is unavailable (status {status}). Please try again later."
    COOKIE_DOWNLOAD_ERROR_MSG = "❌ Error downloading {service} cookie file. Please try again later."
    COOKIE_UPDATED_MSG = "<b>✅ Cookie successfully updated:</b>\n<code>{cookie}</code>"
    COOKIE_NOT_VALID_TEXT_MSG = "<b>❌ Not a valid cookie.</b>"
    COOKIE_EXISTS_OK_MSG = "✅ Cookie file exists and has correct format"
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTube cookie file downloaded via fallback and saved as cookie.txt"
    COOKIE_YT_SOURCES_NOT_CONFIGURED_MSG = "❌ YouTube cookie sources are not configured!"
    COOKIE_YT_INVALID_INDEX_MSG = "❌ Invalid YouTube cookie index: {index}. Available range is 1-{total}"
    COOKIE_TEST_START_MSG = "🔄 Starting YouTube cookies test...\n\nPlease wait while I check and validate your cookies."
    COOKIE_YT_DOWNLOADING_CHECKING_MSG = "🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt} of {total}"
    COOKIE_YT_DOWNLOADING_CHECKING_TESTING_MSG = "🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt} of {total}\n🔍 Testing cookies..."
    COOKIE_YT_VALIDATED_MSG = "✅ YouTube cookies successfully downloaded and validated!\n\nUsed source {source} of {total}"
    COOKIE_YT_ALL_FAILED_MSG = "❌ All YouTube cookies are expired or unavailable!\n\nContact the bot administrator to replace them."

    # Subtitles extra
    SUBTITLES_NOT_AVAILABLE_SELECTED_MSG = "ℹ️ Subtitles are not available for the selected language"
    
    # Image command messages
    IMAGES_MEDIA_LIMIT_EXCEEDED_MSG = (
        "❗️ Media limit exceeded: {detected} files found (maximum {max}).\n\n"
        "Use one of these commands to download maximum available files:\n\n"
        "<code>/img {start}-{end} {url}</code>\n\n"
        "<code>{suggest}</code>"
    )
    IMAGES_PROGRESS_MSG = (
        "{downloading}"
        "Downloaded: <b>{downloaded}</b> / <b>{total}</b>\n"
        "Sent: <b>{sent}</b>\n"
        "Pending to send: <b>{pending}</b>"
    )
    
    # Cache/Auto-cache messages
    AUTO_CACHE_UPDATED_MSG = (
        "⏱️ Auto Firebase cache interval updated!\n\n"
        "📊 Status: {status}\n"
        "⏰ Schedule: every {interval} hours from 00:00\n"
        "🕒 Next reload: {next_time} (in {delta_min} minutes)"
    )
    
    # Args command messages
    ARGS_INVALID_BOOL_MSG = "❌ Invalid boolean value"
    ARGS_MENU_TEXT = (
        "<b>⚙️ yt-dlp Arguments Configuration</b>\n\n"
        "<blockquote>📋 <b>Groups:</b>\n"
        "• ✅/❌ <b>Boolean</b> - True/False switches\n"
        "• 📋 <b>Select</b> - Choose from options\n"
        "• 🔢 <b>Numeric</b> - Number input\n"
        "• 📝🔧 <b>Text</b> - Text/JSON input</blockquote>\n\n"
        "These settings will be applied to all your downloads."
    )
    
    # Clean command messages and buttons
    CLEAN_COOKIES_CLEANED_MSG = "Cookies cleaned."
    CLEAN_LOGS_CLEANED_MSG = "logs cleaned."
    CLEAN_TAGS_CLEANED_MSG = "tags cleaned."
    CLEAN_FORMAT_CLEANED_MSG = "format cleaned."
    CLEAN_SPLIT_CLEANED_MSG = "split cleaned."
    CLEAN_MEDIAINFO_CLEANED_MSG = "mediainfo cleaned."
    CLEAN_SUBS_CLEANED_MSG = "Subtitle settings cleaned."
    CLEAN_KEYBOARD_CLEANED_MSG = "Keyboard settings cleaned."
    CLEAN_ARGS_CLEANED_MSG = "Args settings cleaned."
    CLEAN_NSFW_CLEANED_MSG = "NSFW settings cleaned."
    CLEAN_PROXY_CLEANED_MSG = "Proxy settings cleaned."
    CLEAN_FLOOD_WAIT_CLEANED_MSG = "Flood wait settings cleaned."
    CLEAN_ALL_FILES_CLEANED_MSG = "All files cleaned."
    CLEAN_BTN_COOKIE = "📥 /cookie - Download my 5 cookies"
    CLEAN_BTN_COOKIES_FROM_BROWSER = "🌐 /cookies_from_browser - Get browser's YT-cookie"
    CLEAN_BTN_CHECK_COOKIE = "🔎 /check_cookie - Validate your cookie file"
    CLEAN_BTN_SAVE_AS_COOKIE = "🔖 /save_as_cookie - Upload custom cookie"
    CLEAN_BTN_BACK = "🔙Back"

    # Format/Quality Messages
    FORMAT_ALWAYS_ASK_SET_MSG = "✅ Format set to: Always Ask. You will be prompted for quality each time you send a URL."
    FORMAT_UPDATED_BEST_MSG = "✅ Format updated to best quality:\n{format}"
    FORMAT_UPDATED_ID_NOTE_AUDIO_MSG = "✅ Format updated to ID {format_id}:\n{format}\n\n💡 <b>Note:</b> If this is an audio-only format, it will be downloaded as MP3 audio file."
    FORMAT_UPDATED_ID_AUDIO_ONLY_MSG = "✅ Format updated to ID {format_id} (audio-only):\n{format}\n\n💡 This will be downloaded as MP3 audio file."
    FORMAT_UPDATED_QUALITY_MSG = "✅ Format updated to quality {quality}:\n{format}"
    FORMAT_UPDATED_GENERIC_MSG = "✅ Format updated to:\n{format}"
    FORMAT_SELECT_RESOLUTION_MSG = "Select your desired resolution and codec:"
    FORMAT_SELECT_OPTIONS_MSG = "Select a format option or send a custom one using:\n• <code>/format &lt;format_string&gt;</code> - custom format\n"
    FORMAT_UPDATED_INLINE_MSG = "✅ Format updated to:\n{format}"
    #######################################################
