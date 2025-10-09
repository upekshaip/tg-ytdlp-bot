# Messages Configuration

class Messages(object):
    #######################################################
    # Messages and errors
    #######################################################
    CREDITS_MSG = "<blockquote><i>Managed by</i> @iilililiiillliiliililliilliliiil\n🇮🇹 @tgytdlp_it_bot\n🇦🇪 @tgytdlp_uae_bot\n🇬🇧 @tgytdlp_uk_bot\n🇫🇷 @tgytdlp_fr_bot</blockquote>"
    TO_USE_MSG = "<i>इस बॉट का उपयोग करने के लिए आपको @tg_ytdlp Telegram चैनल की सदस्यता लेनी होगी।</i>\nचैनल में शामिल होने के बाद, <b>अपना वीडियो लिंक फिर से भेजें और बॉट आपके लिए इसे डाउनलोड कर देगा</b> ❤️  "

    ERROR1 = "URL लिंक नहीं मिला। कृपया <b>https://</b> या <b>http://</b> के साथ URL दर्ज करें"

    PLAYLIST_HELP_MSG = """
<blockquote expandable>📋 <b>प्लेलिस्ट (yt-dlp)</b>

प्लेलिस्ट डाउनलोड करने के लिए अंत में <code>*शुरुआत*अंत</code> रेंज के साथ इसका URL भेजें। उदाहरण: <code>URL*1*5</code>।
या आप <code>/vid FROM-TO URL</code> का उपयोग कर सकते हैं। उदाहरण: <code>/vid 3-7 URL</code>। <code>/audio</code> कमांड के लिए भी काम करता है।

<b>उदाहरण:</b>

🟥 <b>YouTube प्लेलिस्ट से वीडियो रेंज:</b> (🍪 की जरूरत)
<code>https://youtu.be/playlist?list=PL...*1*5</code>
(1 से 5 तक के वीडियो डाउनलोड करता है)
🟥 <b>YouTube प्लेलिस्ट से एकल वीडियो:</b> (🍪 की जरूरत)
<code>https://youtu.be/playlist?list=PL...*3*3</code>
(केवल 3rd वीडियो डाउनलोड करता है)

⬛️ <b>TikTok प्रोफाइल:</b> (आपके 🍪 की जरूरत)
<code>https://www.tiktok.com/@USERNAME*1*10</code>
(यूजर प्रोफाइल से पहले 10 वीडियो डाउनलोड करता है)

🟪 <b>Instagram स्टोरीज:</b> (आपके 🍪 की जरूरत)
<code>https://www.instagram.com/stories/USERNAME*1*3</code>
(पहली 3 स्टोरीज डाउनलोड करता है)
<code>https://www.instagram.com/stories/highlights/123...*1*10</code>
(एल्बम से पहली 10 स्टोरीज डाउनलोड करता है)

🟦 <b>VK वीडियो:</b>
<code>https://vkvideo.ru/@PAGE_NAME*1*3</code>
(यूजर/ग्रुप प्रोफाइल से पहले 3 वीडियो डाउनलोड करता है)

⬛️<b>Rutube चैनल:</b>
<code>https://rutube.ru/channel/CHANNEL_ID/videos*2*4</code>
(चैनल से 2 से 4 तक के वीडियो डाउनलोड करता है)

🟪 <b>Twitch क्लिप्स:</b>
<code>https://www.twitch.tv/USERNAME/clips*1*3</code>
(चैनल से पहले 3 क्लिप्स डाउनलोड करता है)

🟦 <b>Vimeo ग्रुप्स:</b>
<code>https://vimeo.com/groups/GROUP_NAME/videos*1*2</code>
(ग्रुप से पहले 2 वीडियो डाउनलोड करता है)

🟧 <b>Pornhub मॉडल्स:</b>
<code>https://www.pornhub.org/model/MODEL_NAME*1*2</code>
(मॉडल प्रोफाइल से पहले 2 वीडियो डाउनलोड करता है)
<code>https://www.pornhub.com/video/search?search=YOUR+PROMPT*1*3</code>
(आपके प्रॉम्प्ट के अनुसार सर्च रिजल्ट से पहले 3 वीडियो डाउनलोड करता है)

और इसी तरह...
देखें <a href=\"https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md\">समर्थित साइट्स की सूची</a>
</blockquote>

<blockquote expandable>🖼 <b>इमेजेस (gallery-dl)</b>

कई प्लेटफॉर्म से इमेज/फोटो/एल्बम डाउनलोड करने के लिए <code>/img URL</code> का उपयोग करें।

<b>उदाहरण:</b>
<code>/img https://vk.com/wall-160916577_408508</code>
<code>/img https://2ch.hk/fd/res/1747651.html</code>
<code>/img https://x.com/username/status/1234567890123456789</code>
<code>/img https://imgur.com/a/abc123</code>

<b>रेंज:</b>
<code>/img 11-20 https://example.com/album</code> — आइटम 11..20
<code>/img 11- https://example.com/album</code> — 11 से अंत तक (या बॉट लिमिट)

<i>समर्थित प्लेटफॉर्म में vk, 2ch, 35photo, 4chan, 500px, ArtStation, Boosty, Civitai, Cyberdrop, DeviantArt, Discord, Facebook, Fansly, Instagram, Pinterest, Reddit, TikTok, Tumblr, Twitter/X, JoyReactor, आदि शामिल हैं। पूरी सूची:</i>
<a href=\"https://raw.githubusercontent.com/mikf/gallery-dl/refs/heads/master/docs/supportedsites.md\">gallery-dl समर्थित साइट्स</a>
</blockquote>
"""
    HELP_MSG = """
🎬 <b>वीडियो डाउनलोड बॉट - सहायता</b>

📥 <b>मूल उपयोग:</b>
• कोई भी लिंक भेजें → बॉट इसे डाउनलोड करता है
  <i>बॉट स्वचालित रूप से yt-dlp के माध्यम से वीडियो और gallery-dl के माध्यम से इमेज डाउनलोड करने की कोशिश करता है।</i>
• <code>/audio URL</code> → ऑडियो निकालें
• <code>/link [गुणवत्ता] URL</code> → सीधे लिंक प्राप्त करें
• <code>/proxy</code> → सभी डाउनलोड के लिए प्रॉक्सी सक्षम/अक्षम करें
• वीडियो पर टेक्स्ट के साथ जवाब दें → कैप्शन बदलें

📋 <b>प्लेलिस्ट और रेंज:</b>
• <code>URL*1*5</code> → वीडियो 1-5 डाउनलोड करें
• <code>/vid 3-7 URL</code> → बन जाता है <code>URL*3*7</code>

🍪 <b>कुकीज और निजी:</b>
• निजी वीडियो के लिए *.txt कुकी अपलोड करें
• <code>/cookie [सेवा]</code> → कुकीज डाउनलोड करें (youtube/tiktok/x/custom)
• <code>/cookie youtube 1</code> → इंडेक्स द्वारा स्रोत चुनें (1–N)
• <code>/cookies_from_browser</code> → ब्राउज़र से निकालें
• <code>/check_cookie</code> → कुकी सत्यापित करें
• <code>/save_as_cookie</code> → टेक्स्ट को कुकी के रूप में सहेजें

🧹 <b>सफाई:</b>
• <code>/clean</code> → केवल मीडिया फाइलें
• <code>/clean all</code> → सब कुछ
• <code>/clean cookies/logs/tags/format/split/mediainfo/sub/keyboard</code>

⚙️ <b>सेटिंग्स:</b>
• <code>/settings</code> → सेटिंग्स मेनू
• <code>/format</code> → गुणवत्ता और प्रारूप
• <code>/split</code> → वीडियो को भागों में विभाजित करें
• <code>/mediainfo on/off</code> → मीडिया जानकारी
• <code>/nsfw on/off</code> → NSFW ब्लर
• <code>/tags</code> → सहेजे गए टैग देखें
• <code>/sub on/off</code> → उपशीर्षक
• <code>/keyboard</code> → कीबोर्ड (OFF/1x3/2x3)

🏷️ <b>टैग:</b>
• URL के बाद <code>#tag1#tag2</code> जोड़ें
• टैग कैप्शन में दिखाई देते हैं
• <code>/tags</code> → सभी टैग देखें

🔗 <b>सीधे लिंक:</b>
• <code>/link URL</code> → सर्वोत्तम गुणवत्ता
• <code>/link [144-4320]/720p/1080p/4k/8k URL</code> → विशिष्ट गुणवत्ता

⚙️ <b>त्वरित कमांड:</b>
• <code>/format [144-4320]/720p/1080p/4k/8k/best/ask/id 134</code> → गुणवत्ता सेट करें
• <code>/keyboard off/1x3/2x3/full</code> → कीबोर्ड लेआउट
• <code>/split 100mb-2000mb</code> → भाग का आकार बदलें
• <code>/subs off/ru/en auto</code> → उपशीर्षक भाषा
• <code>/list URL</code> → उपलब्ध प्रारूपों की सूची
• <code>/mediainfo on/off</code> → मीडिया जानकारी चालू/बंद
• <code>/proxy on/off</code> → सभी डाउनलोड के लिए प्रॉक्सी सक्षम/अक्षम करें

📊 <b>जानकारी:</b>
• <code>/usage</code> → डाउनलोड इतिहास
• <code>/search</code> → @vid के माध्यम से इनलाइन खोज

🖼 <b>इमेजेस:</b>
• <code>URL</code> → URL से इमेज डाउनलोड करें
• <code>/img URL</code> → URL से इमेज डाउनलोड करें
• <code>/img 11-20 URL</code> → विशिष्ट रेंज डाउनलोड करें
• <code>/img 11- URL</code> → 11वें से अंत तक डाउनलोड करें

<blockquote expandable>🇷🇺 <b>Бот для скачивания видео - Помощь</b>

📥 <b>Основное:</b>
• Отправьте любую ссылку → бот скачает её
  <i>бот автоматически попробует скачать видео через yt-dlp и изображения через gallery-dl.</i>
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
🤝 <i>Contributor:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
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
        "Also see: "
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
    PROCESSING_MSG = "🔄 प्रसंस्करण हो रहा है..."
    DOWNLOADING_MSG = "📥 <b>Downloading media...</b>\n\n"

    DOWNLOADING_IMAGE_MSG = "📥 <b>Downloading image...</b>\n\n"

    DOWNLOAD_COMPLETE_MSG = "✅ <b>Download complete</b>\n\n"
    VIDEO_PROCESSING_MSG = "📽 वीडियो is प्रसंस्करण हो रहा है..."
    WAITING_HOURGLASS_MSG = "⌛️"
    
    # Cache Messages
    SENT_FROM_CACHE_MSG = "✅ <b>Sent from cache</b>\n\nSent albums: <b>{count}</b>"
    VIDEO_SENT_FROM_CACHE_MSG = "✅ वीडियो successfully sent से cache."
    PLAYLIST_SENT_FROM_CACHE_MSG = "✅ Playlist videos sent from cache ({cached}/{total} files)."
    CACHE_PARTIAL_MSG = "📥 {cached}/{total} videos sent from cache, downloading missing ones..."

    # Error Messages
    INVALID_URL_MSG = "❌ <b>Invalid URL</b>\n\nPlease provide a valid URL starting with http:// or https://"

    ERROR_OCCURRED_MSG = "❌ <b>Error occurred</b>\n\n<code>{url}</code>\n\nError: {error}"

    ERROR_SENDING_VIDEO_MSG = "❌ Error sending video: {error}"
    ERROR_UNKNOWN_MSG = "❌ Unknown error: {error}"
    ERROR_NO_DISK_SPACE_MSG = "❌ Not पर्याप्त disk अंतरिक्ष को डाउनलोड videos."
    ERROR_FILE_SIZE_LIMIT_MSG = "❌ The file size exceeds the {limit} GB limit. Please select a smaller file within the allowed size."

    ERROR_GETTING_LINK_MSG = "❌ <b>Error getting link:</b>\n{error}"

    # Telegram Rate Limit Messages
    RATE_LIMIT_WITH_TIME_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: {time}\nTo update timer send URL again 2 times."
    RATE_LIMIT_NO_TIME_MSG = "⚠️ Telegram has limited संदेश sending.\n⏳ कृपया प्रतीक्षा करें: \nTo अपडेट timer भेजें यूआरएल again 2 times."
    
    # Subtitles Messages
    SUBTITLES_FAILED_MSG = "⚠️ असफल को डाउनलोड subtitles"

    # Video Processing Messages

    # Stream/Link Messages
    STREAM_LINKS_TITLE_MSG = "🔗 <b>Direct Stream Links</b>\n\n"
    STREAM_TITLE_MSG = "📹 <b>Title:</b> {title}\n"
    STREAM_DURATION_MSG = "⏱ <b>Duration:</b> {duration} sec\n"

    
    # Download Progress Messages

    # Quality Selection Messages

    # NSFW Paid Content Messages

    # Callback Error Messages
    ERROR_ORIGINAL_NOT_FOUND_MSG = "❌ त्रुटि: Original संदेश not found."

    # Tags Error Messages
    TAG_FORBIDDEN_CHARS_MSG = "❌ Tag #{tag} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}"
    
    # Playlist Messages
    PLAYLIST_SENT_MSG = "✅ Playlist videos sent: {sent}/{total} files."
    PLAYLIST_CACHE_SENT_MSG = "✅ Sent from cache: {cached}/{total} files."
    
    # Failed Stream Messages
    FAILED_STREAM_LINKS_MSG = "❌ असफल को get stream links"

    # new messages
    # Browser Cookie Messages
    SELECT_BROWSER_MSG = "चुनें a ब्राउज़र को डाउनलोड cookies से:"
    SELECT_BROWSER_NO_BROWSERS_MSG = "नहीं browsers found पर this सिस्टम. You can डाउनलोड cookies से दूरस्थ यूआरएल or monitor ब्राउज़र स्थिति:"
    BROWSER_MONITOR_HINT_MSG = "🌐 <b>Open Browser</b> - to monitor browser status in mini-app"
    BROWSER_OPEN_BUTTON_MSG = "🌐 खोलें ब्राउज़र"
    DOWNLOAD_FROM_URL_BUTTON_MSG = "📥 डाउनलोड से दूरस्थ यूआरएल"
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTube cookie फ़ाइल downloaded via fallback and saved as cookie.txt"
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ No supported browsers found and no COOKIE_URL configured. Use /cookie or upload cookie.txt."
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ Fallback COOKIE_URL must point to a .txt file."
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ Fallback cookie फ़ाइल is too large (>100KB)."
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_ERROR_MSG = "❌ त्रुटि डाउनलोड हो रहा है fallback cookie. Try /cookie or अपलोड cookie.txt."
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ Unexpected त्रुटि दौरान fallback cookie डाउनलोड."
    BTN_CLOSE = "🔚Close"
    
    # Args command messages
    ARGS_INVALID_BOOL_MSG = "❌ अमान्य बूलियन मूल्य"
    ARGS_CLOSED_MSG = "बंद"
    ARGS_ALL_RESET_MSG = "✅ सभी arguments रीसेट"
    ARGS_RESET_ERROR_MSG = "❌ त्रुटि resetting arguments"
    ARGS_INVALID_PARAM_MSG = "❌ अमान्य parameter"
    ARGS_BOOL_SET_MSG = "Set to {value}"
    ARGS_BOOL_ALREADY_SET_MSG = "Already set to {value}"
    ARGS_INVALID_SELECT_MSG = "❌ अमान्य चुनें मूल्य"
    ARGS_VALUE_SET_MSG = "Set to {value}"
    ARGS_VALUE_ALREADY_SET_MSG = "Already set to {value}"
    ARGS_PARAM_DESCRIPTION_MSG = "<b>📝 {description}</b>\n\n"
    ARGS_CURRENT_VALUE_MSG = "<b>Current value:</b> <code>{current_value}</code>\n\n"
    ARGS_XFF_EXAMPLES_MSG = "<b>Examples:</b>\n• <code>default</code> - Use default XFF strategy\n• <code>never</code> - Never use XFF header\n• <code>US</code> - United States country code\n• <code>GB</code> - United Kingdom country code\n• <code>DE</code> - Germany country code\n• <code>FR</code> - France country code\n• <code>JP</code> - Japan country code\n• <code>192.168.1.0/24</code> - IP block (CIDR)\n• <code>10.0.0.0/8</code> - Private IP range\n• <code>203.0.113.0/24</code> - Public IP block\n\n"
    ARGS_XFF_NOTE_MSG = "<b>Note:</b> This replaces --geo-bypass options. Use any 2-letter country code or IP block in CIDR notation.\n\n"
    ARGS_EXAMPLE_MSG = "<b>Example:</b> <code>{placeholder}</code>\n\n"
    ARGS_SEND_VALUE_MSG = "Please भेजें your नया मूल्य."
    ARGS_NUMBER_PARAM_MSG = "<b>🔢 {description}</b>\n\n"
    ARGS_RANGE_MSG = "<b>Range:</b> {min_val} - {max_val}\n\n"
    ARGS_SEND_NUMBER_MSG = "Please भेजें a संख्या."
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
    PLEASE_WAIT_MSG = "⏳ कृपया प्रतीक्षा करें..."
    ERROR_OCCURRED_SHORT_MSG = "❌ त्रुटि occurred"

    # Args command messages (continued)
    ARGS_INPUT_TIMEOUT_MSG = "⏰ Input बहुलक automatically बंद देय को inactivity (5 minutes)."
    ARGS_INPUT_DANGEROUS_MSG = "❌ Input contains potentially dangerous content: {pattern}"
    ARGS_INPUT_TOO_LONG_MSG = "❌ Input too long (max 1000 characters)"
    ARGS_INVALID_URL_MSG = "❌ Invalid URL format. Must start with http:// or https://"
    ARGS_INVALID_JSON_MSG = "❌ अमान्य JSON प्रारूप"
    ARGS_NUMBER_RANGE_MSG = "❌ Number must be between {min_val} and {max_val}"
    ARGS_INVALID_NUMBER_MSG = "❌ अमान्य संख्या प्रारूप"
    ARGS_DATE_FORMAT_MSG = "❌ तारीख must be में YYYYMMDD प्रारूप (e.g., 20230930)"
    ARGS_YEAR_RANGE_MSG = "❌ Year must be बीच में 1900 and 2100"
    ARGS_MONTH_RANGE_MSG = "❌ Month must be बीच में 01 and 12"
    ARGS_DAY_RANGE_MSG = "❌ Day must be बीच में 01 and 31"
    ARGS_INVALID_DATE_MSG = "❌ अमान्य तारीख प्रारूप"
    ARGS_INVALID_XFF_MSG = "❌ XFF must be 'डिफ़ॉल्ट', 'never', देश code (e.g., US), or IP ब्लॉक (e.g., 192.168.1.0/24)"
    ARGS_NO_CUSTOM_MSG = "नहीं कस्टम arguments सेट. सभी parameters use डिफ़ॉल्ट values."
    ARGS_RESET_SUCCESS_MSG = "✅ सभी arguments रीसेट को defaults."
    ARGS_TEXT_TOO_LONG_MSG = "❌ टेक्स्ट too long. अधिकतम 500 characters."
    ARGS_ERROR_PROCESSING_MSG = "❌ त्रुटि प्रसंस्करण हो रहा है input. कृपया पुनः प्रयास करें."
    ARGS_BOOL_INPUT_MSG = "❌ Please enter 'सत्य' or 'असत्य' for भेजें As फ़ाइल विकल्प."
    ARGS_INVALID_NUMBER_INPUT_MSG = "❌ Please provide a मान्य संख्या."
    ARGS_BOOL_VALUE_REQUEST_MSG = "Please send <code>True</code> or <code>False</code> to enable/disable this option."
    ARGS_JSON_VALUE_REQUEST_MSG = "Please भेजें मान्य JSON."
    
    # Tags command messages
    TAGS_NO_TAGS_MSG = "You have नहीं tags अभी तक."
    TAGS_MESSAGE_CLOSED_MSG = "Tags संदेश बंद."
    
    # Subtitles command messages
    SUBS_DISABLED_MSG = "✅ Subtitles अक्षम and Always Ask बहुलक turned बंद."
    SUBS_ALWAYS_ASK_ENABLED_MSG = "✅ SUBS Always Ask सक्षम."
    SUBS_LANGUAGE_SET_MSG = "✅ Subtitle language set to: {flag} {name}"
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
    SUBS_DISABLED_STATUS_MSG = "🚫 Subtitles are अक्षम"
    SUBS_SELECTED_LANGUAGE_MSG = "{flag} Selected language: {name}{auto_text}"
    SUBS_DOWNLOADING_MSG = "💬 डाउनलोड हो रहा है subtitles..."
    SUBS_DISABLED_ERROR_MSG = "❌ Subtitles are अक्षम. Use /subs को configure."
    SUBS_YOUTUBE_ONLY_MSG = "❌ Subtitle डाउनलोड हो रहा है is केवल supported for YouTube."
    SUBS_CAPTION_MSG = (
        "<b>💬 Subtitles</b>\n\n"
        "<b>Video:</b> {title}\n"
        "<b>Language:</b> {lang}\n"
        "<b>Type:</b> {type}\n\n"
        "{tags}"
    )
    SUBS_SENT_MSG = "💬 Subtitles SRT-फ़ाइल sent को उपयोगकर्ता."
    SUBS_ERROR_PROCESSING_MSG = "❌ त्रुटि प्रसंस्करण हो रहा है subtitle फ़ाइल."
    SUBS_ERROR_DOWNLOAD_MSG = "❌ असफल को डाउनलोड subtitles."
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
    SPLIT_MENU_CLOSED_MSG = "मेनू बंद."
    
    # Settings command messages
    SETTINGS_TITLE_MSG = "<b>Bot Settings</b>\n\nChoose a category:"
    SETTINGS_MENU_CLOSED_MSG = "मेनू बंद."
    SETTINGS_CLEAN_TITLE_MSG = "<b>🧹 Clean Options</b>\n\nChoose what to clean:"
    SETTINGS_COOKIES_TITLE_MSG = "<b>🍪 COOKIES</b>\n\nChoose an action:"
    SETTINGS_MEDIA_TITLE_MSG = "<b>🎞 MEDIA</b>\n\nChoose an action:"
    SETTINGS_LOGS_TITLE_MSG = "<b>📖 INFO</b>\n\nChoose an action:"
    SETTINGS_MORE_TITLE_MSG = "<b>⚙️ MORE COMMANDS</b>\n\nChoose an action:"
    SETTINGS_COMMAND_EXECUTED_MSG = "Command executed."
    SETTINGS_FLOOD_LIMIT_MSG = "⏳ Flood सीमा. Try बाद में."
    SETTINGS_HINT_SENT_MSG = "संकेत sent."
    SETTINGS_SEARCH_HELPER_OPENED_MSG = "खोजें helper opened."
    SETTINGS_UNKNOWN_COMMAND_MSG = "Unknown command."
    SETTINGS_HINT_CLOSED_MSG = "संकेत बंद."
    SETTINGS_HELP_SENT_MSG = "भेजें सहायता txt को उपयोगकर्ता"
    SETTINGS_MENU_OPENED_MSG = "Opened /सेटिंग्स मेनू"
    
    # Search command messages
    SEARCH_HELPER_CLOSED_MSG = "🔍 खोजें helper बंद"
    SEARCH_CLOSED_MSG = "बंद"
    
    # Proxy command messages
    PROXY_ENABLED_MSG = "✅ Proxy {status}."
    PROXY_ERROR_SAVING_MSG = "❌ त्रुटि saving proxy सेटिंग्स."
    PROXY_MENU_TEXT_MSG = "सक्षम करें or अक्षम करें using proxy सर्वर for सभी yt-dlp operations?"
    PROXY_MENU_TEXT_MULTIPLE_MSG = "Enable or disable using proxy servers ({count} available) for all yt-dlp operations?\n\nWhen enabled, proxies will be selected using {method} method."
    PROXY_MENU_CLOSED_MSG = "मेनू बंद."
    PROXY_ENABLED_CONFIRM_MSG = "✅ Proxy सक्षम. सभी yt-dlp operations will use proxy."
    PROXY_ENABLED_MULTIPLE_MSG = "✅ Proxy enabled. All yt-dlp operations will use {count} proxy servers with {method} selection method."
    PROXY_DISABLED_MSG = "❌ Proxy अक्षम."
    PROXY_ERROR_SAVING_CALLBACK_MSG = "❌ त्रुटि saving proxy सेटिंग्स."
    PROXY_ENABLED_CALLBACK_MSG = "Proxy सक्षम."
    PROXY_DISABLED_CALLBACK_MSG = "Proxy अक्षम."
    
    # Other handlers messages
    AUDIO_WAIT_MSG = "⏰ WAIT तक YOUR पिछला डाउनलोड IS FINISHED"
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
    AUDIO_HELP_CLOSED_MSG = "ऑडियो संकेत बंद."
    PLAYLIST_HELP_CLOSED_MSG = "Playlist सहायता बंद."
    USERLOGS_CLOSED_MSG = "लॉग्स संदेश बंद."
    HELP_CLOSED_MSG = "सहायता बंद."
    
    # NSFW command messages
    NSFW_BLUR_SETTINGS_TITLE_MSG = "🔞 <b>NSFW Blur Settings</b>\n\nNSFW content is <b>{status}</b>.\n\nChoose whether to blur NSFW content:"
    NSFW_MENU_CLOSED_MSG = "मेनू बंद."
    NSFW_BLUR_DISABLED_MSG = "NSFW blur अक्षम."
    NSFW_BLUR_ENABLED_MSG = "NSFW blur सक्षम."
    NSFW_BLUR_DISABLED_CALLBACK_MSG = "NSFW blur अक्षम."
    NSFW_BLUR_ENABLED_CALLBACK_MSG = "NSFW blur सक्षम."
    
    # MediaInfo command messages
    MEDIAINFO_ENABLED_MSG = "✅ MediaInfo {status}."
    MEDIAINFO_MENU_TITLE_MSG = "सक्षम करें or अक्षम करें sending MediaInfo for downloaded files?"
    MEDIAINFO_MENU_CLOSED_MSG = "मेनू बंद."
    MEDIAINFO_ENABLED_CONFIRM_MSG = "✅ MediaInfo सक्षम. बाद में डाउनलोड हो रहा है, फ़ाइल info will be sent."
    MEDIAINFO_DISABLED_MSG = "❌ MediaInfo अक्षम."
    MEDIAINFO_ENABLED_CALLBACK_MSG = "MediaInfo सक्षम."
    MEDIAINFO_DISABLED_CALLBACK_MSG = "MediaInfo अक्षम."
    
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
        "• <code>/format id401</code> - same as above\n"
        "• <code>/format id140 audio</code> - download format 140 as MP3 audio\n\n"
        "This command will show all available formats that can be downloaded."
    )
    LIST_PROCESSING_MSG = "🔄 Getting उपलब्ध formats..."
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
    LIST_ERROR_OCCURRED_MSG = "❌ An त्रुटि occurred जबकि प्रसंस्करण हो रहा है the command"
    LIST_ERROR_CALLBACK_MSG = "त्रुटि occurred"
    LIST_HOW_TO_USE_FORMAT_IDS_TITLE = "💡 How to use format IDs:\n"
    LIST_FORMAT_USAGE_INSTRUCTIONS = "After getting the list, use specific format ID:\n"
    LIST_FORMAT_EXAMPLE_401 = "• /format id 401 - download format 401\n"
    LIST_FORMAT_EXAMPLE_401_SHORT = "• /format id401 - same as above\n"
    LIST_FORMAT_EXAMPLE_140_AUDIO = "• /format id 140 audio - download format 140 as MP3 audio\n"
    LIST_FORMAT_EXAMPLE_140_AUDIO_SHORT = "• /format id140 audio - same as above\n"
    LIST_AUDIO_FORMATS_DETECTED = "🎵 Audio-only formats detected: {formats}\n"
    LIST_AUDIO_FORMATS_NOTE = "These formats will be downloaded as MP3 audio files.\n"
    
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
    LINK_INVALID_URL_MSG = "❌ Please provide a मान्य यूआरएल"
    LINK_PROCESSING_MSG = "🔗 Getting direct लिंक..."
    LINK_DURATION_MSG = "⏱ <b>Duration:</b> {duration} sec\n"
    LINK_VIDEO_STREAM_MSG = "🎬 <b>Video stream:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    LINK_AUDIO_STREAM_MSG = "🎵 <b>Audio stream:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    
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
    KEYBOARD_ERROR_APPLYING_MSG = "Error applying keyboard setting {setting}: {error}"
    
    # Format command messages
    FORMAT_ALWAYS_ASK_SET_MSG = "✅ प्रारूप सेट को: Always Ask. You will be prompted for गुणवत्ता each समय you भेजें a यूआरएल."
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "✅ प्रारूप सेट को: Always Ask. Now you will be prompted for गुणवत्ता each समय you भेजें a यूआरएल."
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
    FORMAT_RESOLUTION_MENU_MSG = "चुनें your desired resolution and codec:"
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "✅ प्रारूप सेट को: Always Ask. Now you will be prompted for गुणवत्ता each समय you भेजें a यूआरएल."
    FORMAT_UPDATED_MSG = "✅ Format updated to:\n{format}"
    FORMAT_SAVED_MSG = "✅ प्रारूप saved."
    FORMAT_CHOICE_UPDATED_MSG = "✅ प्रारूप विकल्प updated."
    FORMAT_CUSTOM_MENU_CLOSED_MSG = "कस्टम प्रारूप मेनू बंद"
    FORMAT_CODEC_SET_MSG = "✅ Codec set to {codec}"
    
    # Cookies command messages
    COOKIES_BROWSER_CHOICE_UPDATED_MSG = "✅ ब्राउज़र विकल्प updated."
    
    # Clean command messages
    
    # Admin command messages
    ADMIN_ACCESS_DENIED_MSG = "❌ Access denied. Admin only."
    ACCESS_DENIED_ADMIN = "❌ Access denied. Admin only."
    WELCOME_MASTER = "Welcome Master 🥷"
    DOWNLOAD_ERROR_GENERIC = "❌ Sorry... Some error occurred during download."
    SIZE_LIMIT_EXCEEDED = "❌ The file size exceeds the {max_size_gb} GB limit. Please select a smaller file within the allowed size."
    ADMIN_SCRIPT_NOT_FOUND_MSG = "❌ Script not found: {script_path}"
    ADMIN_DOWNLOADING_MSG = "⏳ Downloading fresh Firebase dump using {script_path} ..."
    ADMIN_CACHE_RELOADED_MSG = "✅ Firebase cache reloaded successfully!"
    ADMIN_CACHE_FAILED_MSG = "❌ Failed to reload Firebase cache. Check if {cache_file} exists."
    ADMIN_ERROR_RELOADING_MSG = "❌ Error reloading cache: {error}"
    ADMIN_ERROR_SCRIPT_MSG = "❌ Error running {script_path}:\n{stdout}\n{stderr}"
    ADMIN_SCRIPT_NOT_FOUND_MSG = "❌ Script not found: {script_path}"
    ADMIN_DOWNLOADING_MSG = "⏳ Downloading fresh Firebase dump using {script_path} ..."
    ADMIN_CACHE_RELOADED_MSG = "✅ Firebase cache reloaded successfully!"
    ADMIN_CACHE_FAILED_MSG = "❌ Failed to reload Firebase cache. Check if {cache_file} exists."
    ADMIN_ERROR_RELOADING_MSG = "❌ Error reloading cache: {error}"
    ADMIN_PROMO_SENT_MSG = "<b>✅ Promo message sent to all other users</b>"
    ADMIN_CANNOT_SEND_PROMO_MSG = "<b>❌ Cannot send the promo message. Try replying to a message\nOr some error occurred</b>"
    ADMIN_USER_NO_DOWNLOADS_MSG = "<b>❌ User did not download any content yet...</b> Not exist in logs"
    ADMIN_INVALID_COMMAND_MSG = "❌ Invalid command"
    ADMIN_NO_DATA_FOUND_MSG = f"❌ No data found in cache for <code>{{path}}</code>"
    ADMIN_BLOCK_USER_USAGE_MSG = "❌ Usage: /block_user <user_id>"
    ADMIN_CANNOT_DELETE_ADMIN_MSG = "🚫 Admin cannot delete an admin"
    ADMIN_USER_BLOCKED_MSG = "User blocked 🔒❌\n \nID: <code>{user_id}</code>\nBlocked Date: {date}"
    ADMIN_USER_ALREADY_BLOCKED_MSG = "<code>{user_id}</code> is already blocked ❌😐"
    ADMIN_NOT_ADMIN_MSG = "🚫 Sorry! You are not an admin"
    ADMIN_UNBLOCK_USER_USAGE_MSG = "❌ Usage: /unblock_user <user_id>"
    ADMIN_USER_UNBLOCKED_MSG = "User unblocked 🔓✅\n \nID: <code>{user_id}</code>\nUnblocked Date: {date}"
    ADMIN_USER_ALREADY_UNBLOCKED_MSG = "<code>{user_id}</code> is already unblocked ✅😐"
    ADMIN_BOT_RUNNING_TIME_MSG = "⏳ <i>Bot running time -</i> <b>{time}</b>"
    ADMIN_UNCACHE_USAGE_MSG = "❌ Please provide a URL to clear cache for.\nUsage: <code>/uncache &lt;URL&gt;</code>"
    ADMIN_UNCACHE_INVALID_URL_MSG = "❌ Please provide a valid URL.\nUsage: <code>/uncache &lt;URL&gt;</code>"
    ADMIN_CACHE_CLEARED_MSG = "✅ Cache cleared successfully for URL:\n<code>{url}</code>"
    ADMIN_NO_CACHE_FOUND_MSG = "ℹ️ No cache found for this link."
    ADMIN_ERROR_CLEARING_CACHE_MSG = "❌ Error clearing cache: {error}"
    ADMIN_ACCESS_DENIED_MSG = "❌ Access denied. Admin only."
    ADMIN_UPDATE_PORN_RUNNING_MSG = "⏳ Running porn list update script: {script_path}"
    ADMIN_SCRIPT_COMPLETED_MSG = "✅ Script completed successfully!"
    ADMIN_SCRIPT_COMPLETED_WITH_OUTPUT_MSG = "✅ Script completed successfully!\n\nOutput:\n<code>{output}</code>"
    ADMIN_SCRIPT_FAILED_MSG = "❌ Script failed with return code {returncode}:\n<code>{error}</code>"
    ADMIN_ERROR_RUNNING_SCRIPT_MSG = "❌ Error running script: {error}"
    ADMIN_RELOADING_PORN_MSG = "⏳ Reloading porn and domain-related caches..."
    ADMIN_PORN_CACHES_RELOADED_MSG = (
        "✅ Porn caches reloaded successfully!\n\n"
        "📊 Current cache status:\n"
        "• Porn domains: {porn_domains}\n"
        "• Porn keywords: {porn_keywords}\n"
        "• Supported sites: {supported_sites}\n"
        "• WHITELIST: {whitelist}\n"
        "• GREYLIST: {greylist}\n"
        "• BLACK_LIST: {black_list}\n"
        "• WHITE_KEYWORDS: {white_keywords}\n"
        "• PROXY_DOMAINS: {proxy_domains}\n"
        "• PROXY_2_DOMAINS: {proxy_2_domains}\n"
        "• CLEAN_QUERY: {clean_query}\n"
        "• NO_COOKIE_DOMAINS: {no_cookie_domains}"
    )
    ADMIN_ERROR_RELOADING_PORN_MSG = "❌ Error reloading porn cache: {error}"
    ADMIN_CHECK_PORN_USAGE_MSG = "❌ Please provide a URL to check.\nUsage: <code>/check_porn &lt;URL&gt;</code>"
    ADMIN_CHECK_PORN_INVALID_URL_MSG = "❌ Please provide a valid URL.\nUsage: <code>/check_porn &lt;URL&gt;</code>"
    ADMIN_CHECKING_URL_MSG = "🔍 Checking URL for NSFW content...\n<code>{url}</code>"
    ADMIN_PORN_CHECK_RESULT_MSG = (
        "{status_icon} <b>Porn Check Result</b>\n\n"
        "<b>URL:</b> <code>{url}</code>\n"
        "<b>Status:</b> <b>{status_text}</b>\n\n"
        "<b>Explanation:</b>\n{explanation}"
    )
    ADMIN_ERROR_CHECKING_URL_MSG = "❌ Error checking URL: {error}"
    
    # Clean command messages
    CLEAN_COOKIES_CLEANED_MSG = "Cookies cleaned."
    CLEAN_LOGS_CLEANED_MSG = "लॉग्स cleaned."
    CLEAN_TAGS_CLEANED_MSG = "tags cleaned."
    CLEAN_FORMAT_CLEANED_MSG = "प्रारूप cleaned."
    CLEAN_SPLIT_CLEANED_MSG = "split cleaned."
    CLEAN_MEDIAINFO_CLEANED_MSG = "mediainfo cleaned."
    CLEAN_SUBS_CLEANED_MSG = "Subtitle सेटिंग्स cleaned."
    CLEAN_KEYBOARD_CLEANED_MSG = "Keyboard सेटिंग्स cleaned."
    CLEAN_ARGS_CLEANED_MSG = "Args सेटिंग्स cleaned."
    CLEAN_NSFW_CLEANED_MSG = "NSFW सेटिंग्स cleaned."
    CLEAN_PROXY_CLEANED_MSG = "Proxy सेटिंग्स cleaned."
    CLEAN_FLOOD_WAIT_CLEANED_MSG = "Flood wait सेटिंग्स cleaned."
    CLEAN_ALL_CLEANED_MSG = "सभी files cleaned."
    CLEAN_COOKIES_MENU_TITLE_MSG = "<b>🍪 COOKIES</b>\n\nChoose an action:"
    
    # Cookies command messages
    COOKIES_FILE_SAVED_MSG = "✅ Cookie फ़ाइल saved"
    COOKIES_SKIPPED_VALIDATION_MSG = "✅ Skipped validation for non-YouTube cookies"
    COOKIES_INCORRECT_FORMAT_MSG = "⚠️ Cookie फ़ाइल exists but has गलत प्रारूप"
    COOKIES_FILE_NOT_FOUND_MSG = "❌ Cookie फ़ाइल is not found."
    COOKIES_YOUTUBE_TEST_START_MSG = "🔄 Starting YouTube cookies टेस्ट...\n\nPlease wait जबकि I जांच and मान्य करें your cookies."
    COOKIES_YOUTUBE_WORKING_MSG = "✅ Your existing YouTube cookies are working properly!\n\nNo आवश्यकता को डाउनलोड नया ones."
    COOKIES_YOUTUBE_EXPIRED_MSG = "❌ Your existing YouTube cookies are समाप्त or अमान्य.\n\n🔄 डाउनलोड हो रहा है नया cookies..."
    COOKIES_SOURCE_NOT_CONFIGURED_MSG = "❌ {service} cookie source is not configured!"
    COOKIES_SOURCE_MUST_BE_TXT_MSG = "❌ {service} cookie source must be a .txt file!"
    
    # Image command messages
    IMG_RANGE_LIMIT_EXCEEDED_MSG = "❗️ Range limit exceeded: {range_count} files requested (maximum {max_img_files}).\n\nUse one of these commands to download maximum available files:\n\n<code>/img {start_range}-{end_range} {url}</code>\n\n<code>/img {suggested_command_url_format}</code>"
    COMMAND_IMAGE_HELP_CLOSE_BUTTON_MSG = "🔚पास"
    COMMAND_IMAGE_MEDIA_LIMIT_EXCEEDED_MSG = "❗️ Media limit exceeded: {count} files requested (maximum {max_count}).\n\nUse one of these commands to download maximum available files:\n\n<code>/img {start_range}-{end_range} {url}</code>\n\n<code>/img {suggested_command_url_format}</code>"
    
    # Args command parameter descriptions
    ARGS_IMPERSONATE_DESC_MSG = "ब्राउज़र impersonation"
    ARGS_REFERER_DESC_MSG = "रेफरर हेडर"
    ARGS_USER_AGENT_DESC_MSG = "उपयोगकर्ता-Agent header"
    ARGS_GEO_BYPASS_DESC_MSG = "Bypass geographic restrictions"
    ARGS_CHECK_CERTIFICATE_DESC_MSG = "जांच SSL certificate"
    ARGS_LIVE_FROM_START_DESC_MSG = "डाउनलोड live streams से शुरू करें"
    ARGS_NO_LIVE_FROM_START_DESC_MSG = "Do not डाउनलोड live streams से शुरू करें"
    ARGS_HLS_USE_MPEGTS_DESC_MSG = "Use MPEG-TS container for HLS videos"
    ARGS_NO_PLAYLIST_DESC_MSG = "डाउनलोड केवल single वीडियो, not playlist"
    ARGS_NO_PART_DESC_MSG = "Do not use .भाग files"
    ARGS_NO_CONTINUE_DESC_MSG = "Do not जारी रखें आंशिक downloads"
    ARGS_AUDIO_FORMAT_DESC_MSG = "ऑडियो प्रारूप for extraction"
    ARGS_EMBED_METADATA_DESC_MSG = "Embed metadata में वीडियो फ़ाइल"
    ARGS_EMBED_THUMBNAIL_DESC_MSG = "Embed thumbnail में वीडियो फ़ाइल"
    ARGS_WRITE_THUMBNAIL_DESC_MSG = "Write thumbnail को फ़ाइल"
    ARGS_CONCURRENT_FRAGMENTS_DESC_MSG = "संख्या of concurrent fragments को डाउनलोड"
    ARGS_FORCE_IPV4_DESC_MSG = "बल IPv4 connections"
    ARGS_FORCE_IPV6_DESC_MSG = "बल IPv6 connections"
    ARGS_XFF_DESC_MSG = "X-Forwarded-For header रणनीति"
    ARGS_HTTP_CHUNK_SIZE_DESC_MSG = "HTTP chunk आकार (bytes)"
    ARGS_SLEEP_SUBTITLES_DESC_MSG = "Sleep पहले subtitle डाउनलोड (seconds)"
    ARGS_LEGACY_SERVER_CONNECT_DESC_MSG = "अनुमति legacy सर्वर connections"
    ARGS_NO_CHECK_CERTIFICATES_DESC_MSG = "Suppress HTTPS certificate validation"
    ARGS_USERNAME_DESC_MSG = "खाता उपयोगकर्ता नाम"
    ARGS_PASSWORD_DESC_MSG = "खाता पासवर्ड"
    ARGS_TWOFACTOR_DESC_MSG = "दो-कारक authentication code"
    ARGS_IGNORE_ERRORS_DESC_MSG = "Ignore डाउनलोड errors and जारी रखें"
    ARGS_MIN_FILESIZE_DESC_MSG = "न्यूनतम फ़ाइल आकार (MB)"
    ARGS_MAX_FILESIZE_DESC_MSG = "अधिकतम फ़ाइल आकार (MB)"
    ARGS_PLAYLIST_ITEMS_DESC_MSG = "Playlist items को डाउनलोड (e.g., 1,3,5 or 1-5)"
    ARGS_DATE_DESC_MSG = "डाउनलोड videos uploaded पर this तारीख (YYYYMMDD)"
    ARGS_DATEBEFORE_DESC_MSG = "डाउनलोड videos uploaded पहले this तारीख (YYYYMMDD)"
    ARGS_DATEAFTER_DESC_MSG = "डाउनलोड videos uploaded बाद में this तारीख (YYYYMMDD)"
    ARGS_HTTP_HEADERS_DESC_MSG = "कस्टम HTTP headers (JSON)"
    ARGS_SLEEP_INTERVAL_DESC_MSG = "Sleep अंतराल बीच में requests (seconds)"
    ARGS_MAX_SLEEP_INTERVAL_DESC_MSG = "अधिकतम sleep अंतराल (seconds)"
    ARGS_RETRIES_DESC_MSG = "संख्या of retries"
    ARGS_VIDEO_FORMAT_DESC_MSG = "वीडियो container प्रारूप"
    ARGS_MERGE_OUTPUT_FORMAT_DESC_MSG = "Output container प्रारूप for merging"
    ARGS_SEND_AS_FILE_DESC_MSG = "भेजें सभी मीडिया as document instead of मीडिया"
    
    # Args command short descriptions
    ARGS_IMPERSONATE_SHORT_MSG = "अनुकरण"
    ARGS_REFERER_SHORT_MSG = "रेफरर"
    ARGS_GEO_BYPASS_SHORT_MSG = "भौगोलिक बायपास"
    ARGS_CHECK_CERTIFICATE_SHORT_MSG = "जांच Cert"
    ARGS_LIVE_FROM_START_SHORT_MSG = "Live शुरू करें"
    ARGS_NO_LIVE_FROM_START_SHORT_MSG = "नहीं Live शुरू करें"
    ARGS_USER_AGENT_SHORT_MSG = "उपयोगकर्ता Agent"
    ARGS_HLS_USE_MPEGTS_SHORT_MSG = "HLS MPEG-TS"
    ARGS_NO_PLAYLIST_SHORT_MSG = "नहीं Playlist"
    ARGS_NO_PART_SHORT_MSG = "नहीं भाग"
    ARGS_NO_CONTINUE_SHORT_MSG = "नहीं जारी रखें"
    ARGS_AUDIO_FORMAT_SHORT_MSG = "ऑडियो प्रारूप"
    ARGS_EMBED_METADATA_SHORT_MSG = "एम्बेड मेटा"
    ARGS_EMBED_THUMBNAIL_SHORT_MSG = "एम्बेड थंबनेल"
    ARGS_WRITE_THUMBNAIL_SHORT_MSG = "लिखें थंबनेल"
    ARGS_CONCURRENT_FRAGMENTS_SHORT_MSG = "समवर्ती"
    ARGS_FORCE_IPV4_SHORT_MSG = "बल IPv4"
    ARGS_FORCE_IPV6_SHORT_MSG = "बल IPv6"
    ARGS_XFF_SHORT_MSG = "XFF Header"
    ARGS_HTTP_CHUNK_SIZE_SHORT_MSG = "Chunk आकार"
    ARGS_SLEEP_SUBTITLES_SHORT_MSG = "सबटाइटल प्रतीक्षा"
    ARGS_LEGACY_SERVER_CONNECT_SHORT_MSG = "पुराना कनेक्ट"
    ARGS_NO_CHECK_CERTIFICATES_SHORT_MSG = "नहीं जांच Cert"
    ARGS_USERNAME_SHORT_MSG = "उपयोगकर्ता नाम"
    ARGS_PASSWORD_SHORT_MSG = "पासवर्ड"
    ARGS_TWOFACTOR_SHORT_MSG = "2FA"
    ARGS_IGNORE_ERRORS_SHORT_MSG = "त्रुटियों को नजरअंदाज करें"
    ARGS_MIN_FILESIZE_SHORT_MSG = "Min आकार"
    ARGS_MAX_FILESIZE_SHORT_MSG = "Max आकार"
    ARGS_PLAYLIST_ITEMS_SHORT_MSG = "प्लेलिस्ट आइटम"
    ARGS_DATE_SHORT_MSG = "तारीख"
    ARGS_DATEBEFORE_SHORT_MSG = "तारीख पहले"
    ARGS_DATEAFTER_SHORT_MSG = "तारीख बाद में"
    ARGS_HTTP_HEADERS_SHORT_MSG = "HTTP Headers"
    ARGS_SLEEP_INTERVAL_SHORT_MSG = "Sleep अंतराल"
    ARGS_MAX_SLEEP_INTERVAL_SHORT_MSG = "अधिकतम प्रतीक्षा"
    ARGS_VIDEO_FORMAT_SHORT_MSG = "वीडियो प्रारूप"
    ARGS_MERGE_OUTPUT_FORMAT_SHORT_MSG = "Merge प्रारूप"
    ARGS_SEND_AS_FILE_SHORT_MSG = "भेजें As फ़ाइल"
    
    # Additional cookies command messages
    COOKIES_FILE_TOO_LARGE_MSG = "❌ The फ़ाइल is too large. अधिकतम आकार is 100 KB."
    COOKIES_INVALID_FORMAT_MSG = "❌ केवल files of the following प्रारूप are allowed .txt."
    COOKIES_INVALID_COOKIE_MSG = "❌ The फ़ाइल does not look पसंद cookie.txt (there is नहीं रेखा '# Netscape HTTP Cookie फ़ाइल')."
    COOKIES_ERROR_READING_MSG = "❌ Error reading file: {error}"
    COOKIES_FILE_EXISTS_MSG = "✅ Cookie फ़ाइल exists and has सही प्रारूप"
    COOKIES_FILE_TOO_LARGE_DOWNLOAD_MSG = "❌ {service} cookie file is too large! Max 100KB, got {size}KB."
    COOKIES_FILE_DOWNLOADED_MSG = "<b>✅ {service} cookie file downloaded and saved as cookie.txt in your folder.</b>"
    COOKIES_SOURCE_UNAVAILABLE_MSG = "❌ {service} cookie source is unavailable (status {status}). Please try again later."
    COOKIES_ERROR_DOWNLOADING_MSG = "❌ Error downloading {service} cookie file. Please try again later."
    COOKIES_USER_PROVIDED_MSG = "<b>✅ User provided a new cookie file.</b>"
    COOKIES_SUCCESSFULLY_UPDATED_MSG = "<b>✅ Cookie successfully updated:</b>\n<code>{final_cookie}</code>"
    COOKIES_NOT_VALID_MSG = "<b>❌ Not a valid cookie.</b>"
    COOKIES_YOUTUBE_SOURCES_NOT_CONFIGURED_MSG = "❌ YouTube cookie sources are not configured!"
    COOKIES_DOWNLOADING_YOUTUBE_MSG = "🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt} of {total}"
    
    # Additional admin command messages
    ADMIN_ACCESS_DENIED_AUTO_DELETE_MSG = "❌ Access denied. Admin only."
    ADMIN_USER_LOGS_TOTAL_MSG = "Total: <b>{total}</b>\n<b>{user_id}</b> - logs (Last 10):\n\n{format_str}"
    
    # Additional keyboard command messages
    KEYBOARD_ACTIVATED_MSG = "🎹 keyboard activated!"
    
    # Additional subtitles command messages
    SUBS_LANGUAGE_SET_MSG = "✅ Subtitle language set to: {flag} {name}"
    SUBS_LANGUAGE_AUTO_SET_MSG = "✅ Subtitle language set to: {flag} {name} with AUTO/TRANS enabled."
    SUBS_LANGUAGE_MENU_CLOSED_MSG = "Subtitle language मेनू बंद."
    SUBS_DOWNLOADING_MSG = "💬 डाउनलोड हो रहा है subtitles..."
    
    # Additional admin command messages
    ADMIN_RELOADING_CACHE_MSG = "🔄 Reloading Firebase cache into memory..."
    
    # Additional cookies command messages
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ No COOKIE_URL configured. Use /cookie or upload cookie.txt."
    COOKIES_DOWNLOADING_FROM_URL_MSG = "📥 डाउनलोड हो रहा है cookies से दूरस्थ यूआरएल..."
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ Fallback COOKIE_URL must point to a .txt file."
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ Fallback cookie फ़ाइल is too large (>100KB)."
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTube cookie फ़ाइल downloaded via fallback and saved as cookie.txt"
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ Fallback cookie source unavailable (status {status}). Try /cookie or upload cookie.txt."
    COOKIE_FALLBACK_ERROR_MSG = "❌ त्रुटि डाउनलोड हो रहा है fallback cookie. Try /cookie or अपलोड cookie.txt."
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ Unexpected त्रुटि दौरान fallback cookie डाउनलोड."
    COOKIES_BROWSER_NOT_INSTALLED_MSG = "⚠️ {browser} browser not installed."
    COOKIES_SAVED_USING_BROWSER_MSG = "✅ Cookies saved using browser: {browser}"
    COOKIES_FAILED_TO_SAVE_MSG = "❌ Failed to save cookies: {error}"
    COOKIES_YOUTUBE_WORKING_PROPERLY_MSG = "✅ YouTube cookies are working properly"
    COOKIES_YOUTUBE_EXPIRED_INVALID_MSG = "❌ YouTube cookies are समाप्त or अमान्य\n\nUse /cookie को get नया cookies"
    
    # Additional format command messages
    FORMAT_MENU_ADDITIONAL_MSG = "• <code>/format &lt;format_string&gt;</code> - custom format\n• <code>/format 720</code> - 720p quality\n• <code>/format 4k</code> - 4K quality"
    
    # Callback answer messages
    FORMAT_HINT_SENT_MSG = "संकेत sent."
    FORMAT_MKV_TOGGLE_MSG = "MKV is now {status}"
    COOKIES_NO_REMOTE_URL_MSG = "❌ नहीं दूरस्थ यूआरएल configured"
    COOKIES_INVALID_FILE_FORMAT_MSG = "❌ अमान्य फ़ाइल प्रारूप"
    COOKIES_FILE_TOO_LARGE_CALLBACK_MSG = "❌ फ़ाइल too large"
    COOKIES_DOWNLOADED_SUCCESSFULLY_MSG = "✅ Cookies downloaded successfully"
    COOKIES_SERVER_ERROR_MSG = "❌ Server error {status}"
    COOKIES_DOWNLOAD_FAILED_MSG = "❌ डाउनलोड असफल"
    COOKIES_UNEXPECTED_ERROR_MSG = "❌ Unexpected त्रुटि"
    COOKIES_BROWSER_NOT_INSTALLED_CALLBACK_MSG = "⚠️ ब्राउज़र not installed."
    COOKIES_MENU_CLOSED_MSG = "मेनू बंद."
    COOKIES_HINT_CLOSED_MSG = "Cookie संकेत बंद."
    IMG_HELP_CLOSED_MSG = "सहायता बंद."
    SUBS_LANGUAGE_UPDATED_MSG = "Subtitle language सेटिंग्स updated."
    SUBS_MENU_CLOSED_MSG = "Subtitle language मेनू बंद."
    KEYBOARD_SET_TO_MSG = "Keyboard set to {setting}"
    KEYBOARD_ERROR_PROCESSING_MSG = "त्रुटि प्रसंस्करण हो रहा है setting"
    MEDIAINFO_ENABLED_CALLBACK_MSG = "MediaInfo सक्षम."
    MEDIAINFO_DISABLED_CALLBACK_MSG = "MediaInfo अक्षम."
    NSFW_BLUR_DISABLED_CALLBACK_MSG = "NSFW blur अक्षम."
    NSFW_BLUR_ENABLED_CALLBACK_MSG = "NSFW blur सक्षम."
    SETTINGS_MENU_CLOSED_MSG = "मेनू बंद."
    SETTINGS_FLOOD_WAIT_ACTIVE_MSG = "Flood wait सक्रिय. Try बाद में."
    OTHER_HELP_CLOSED_MSG = "सहायता बंद."
    OTHER_LOGS_MESSAGE_CLOSED_MSG = "लॉग्स संदेश बंद."
    
    # Additional split command messages
    SPLIT_MENU_CLOSED_MSG = "मेनू बंद."
    SPLIT_INVALID_SIZE_CALLBACK_MSG = "अमान्य आकार."
    
    # Additional error messages
    MEDIAINFO_ERROR_SENDING_MSG = "❌ Error sending MediaInfo: {error}"
    LINK_ERROR_OCCURRED_MSG = "❌ An error occurred: {error}"
    
    # Additional document caption messages
    MEDIAINFO_DOCUMENT_CAPTION_MSG = "<blockquote>📊 MediaInfo</blockquote>"
    ADMIN_USER_LOGS_CAPTION_MSG = "{user_id} - all logs"
    ADMIN_BOT_DATA_CAPTION_MSG = "{bot_name} - all {path}"
    
    # Additional cookies command messages (missing ones)
    DOWNLOAD_FROM_URL_BUTTON_MSG = "📥 डाउनलोड से दूरस्थ यूआरएल"
    BROWSER_OPEN_BUTTON_MSG = "🌐 खोलें ब्राउज़र"
    SELECT_BROWSER_MSG = "चुनें a ब्राउज़र को डाउनलोड cookies से:"
    SELECT_BROWSER_NO_BROWSERS_MSG = "नहीं browsers found पर this सिस्टम. You can डाउनलोड cookies से दूरस्थ यूआरएल or monitor ब्राउज़र स्थिति:"
    BROWSER_MONITOR_HINT_MSG = "🌐 <b>Open Browser</b> - to monitor browser status in mini-app"
    COOKIES_YOUTUBE_TEST_START_MSG = "🔄 Starting YouTube cookies टेस्ट...\n\nPlease wait जबकि I जांच and मान्य करें your cookies."
    COOKIES_FAILED_RUN_CHECK_MSG = "❌ असफल को चलाएं /check_cookie"
    COOKIES_FLOOD_LIMIT_MSG = "⏳ Flood सीमा. Try बाद में."
    COOKIES_FAILED_OPEN_BROWSER_MSG = "❌ असफल को खोलें ब्राउज़र cookie मेनू"
    COOKIES_SAVE_AS_HINT_CLOSED_MSG = "सहेजें as cookie संकेत बंद."
    
    # Link command messages
    LINK_USAGE_MSG = "🔗 <b>Usage:</b>\n<code>/link [quality] URL</code>\n\n<b>Examples:</b>\n<blockquote>• /link https://youtube.com/watch?v=... - best quality\n• /link 720 https://youtube.com/watch?v=... - 720p or lower\n• /link 720p https://youtube.com/watch?v=... - same as above\n• /link 4k https://youtube.com/watch?v=... - 4K or lower\n• /link 8k https://youtube.com/watch?v=... - 8K or lower</blockquote>\n\n<b>Quality:</b> from 1 to 10000 (e.g., 144, 240, 720, 1080)"
    
    # Additional format command messages
    FORMAT_8K_QUALITY_MSG = "• <code>/format 8k</code> - 8K quality"
    
    # Additional link command messages
    LINK_DIRECT_LINK_OBTAINED_MSG = "🔗 <b>Direct link obtained</b>\n\n"
    LINK_FORMAT_INFO_MSG = "🎛 <b>Format:</b> <code>{format_spec}</code>\n\n"
    LINK_AUDIO_STREAM_MSG = "🎵 <b>Audio stream:</b>\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
    LINK_FAILED_GET_STREAMS_MSG = "❌ असफल को get stream links"
    LINK_ERROR_GETTING_MSG = "❌ <b>Error getting link:</b>\n{error_msg}"
    
    # Additional cookies command messages (more)
    COOKIES_INVALID_YOUTUBE_INDEX_MSG = "❌ Invalid YouTube cookie index: {selected_index}. Available range is 1-{total_urls}"
    COOKIES_DOWNLOADING_CHECKING_MSG = "🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt} of {total}"
    COOKIES_DOWNLOADING_TESTING_MSG = "🔄 Downloading and checking YouTube cookies...\n\nAttempt {attempt} of {total}\n🔍 Testing cookies..."
    COOKIES_SUCCESS_VALIDATED_MSG = "✅ YouTube cookies successfully downloaded and validated!\n\nUsed source {source} of {total}"
    COOKIES_ALL_EXPIRED_MSG = "❌ सभी YouTube cookies are समाप्त or अनुपलब्ध!\n\nContact the bot administrator को replace them."
    
    # Additional other command messages
    OTHER_TAG_ERROR_MSG = "❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}"
    
    # Additional subtitles command messages
    SUBS_INVALID_ARGUMENT_MSG = "❌ **अमान्य argument!**\n\n"
    SUBS_LANGUAGE_SET_STATUS_MSG = "✅ Subtitle language set: {flag} {name}"
    
    # Additional subtitles command messages (more)
    SUBS_EXAMPLE_AUTO_MSG = "Example: `/subs en auto`"
    
    # Additional subtitles command messages (more more)
    SUBS_SELECTED_LANGUAGE_MSG = "{flag} Selected language: {name}{auto_text}"
    SUBS_ALWAYS_ASK_TOGGLE_MSG = "✅ Always Ask mode {status}"
    
    # Additional subtitles menu messages
    SUBS_DISABLED_STATUS_MSG = "🚫 Subtitles are अक्षम"
    SUBS_SETTINGS_MENU_MSG = "<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:\n\n"
    SUBS_SETTINGS_ADDITIONAL_MSG = "• <code>/subs off</code> - disable subtitles\n"
    SUBS_AUTO_MENU_MSG = "<b>💬 Subtitle settings</b>\n\n{status_text}\n\nSelect subtitle language:"
    
    # Additional link command messages (more)
    LINK_TITLE_MSG = "📹 <b>Title:</b> {title}\n"
    LINK_DURATION_MSG = "⏱ <b>Duration:</b> {duration} sec\n"
    LINK_VIDEO_STREAM_MSG = "🎬 <b>Video stream:</b>\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
    
    # Additional subtitles limitation messages
    SUBS_LIMITATIONS_MSG = "- 720p max quality\n- 1.5 hour max duration\n- 500mb max video size</blockquote>\n\n"
    
    # Additional subtitles warning and command messages
    SUBS_WARNING_MSG = "<blockquote>❗️WARNING: due to high CPU impact this function is very slow (near real-time) and limited to:\n"
    SUBS_QUICK_COMMANDS_MSG = "<b>Quick commands:</b>\n"
    
    # Additional subtitles command description messages
    SUBS_DISABLE_COMMAND_MSG = "• `/subs off` - disable subtitles\n"
    SUBS_ENABLE_ASK_MODE_MSG = "• `/subs on` - enable Always Ask mode\n"
    SUBS_SET_LANGUAGE_MSG = "• `/subs ru` - set language\n"
    SUBS_SET_LANGUAGE_AUTO_MSG = "• `/subs ru auto` - set language with AUTO/TRANS enabled\n\n"
    SUBS_SET_LANGUAGE_CODE_MSG = "• <code>/subs on</code> - enable Always Ask mode\n"
    SUBS_AUTO_SUBS_TEXT = " (auto-subs)"
    SUBS_AUTO_MODE_TOGGLE_MSG = "✅ Auto-subs mode {status}"
    
    # Subtitles log messages
    SUBS_DISABLED_LOG_MSG = "SUBS disabled via command: {arg}"
    SUBS_ALWAYS_ASK_ENABLED_LOG_MSG = "SUBS Always Ask enabled via command: {arg}"
    SUBS_LANGUAGE_SET_LOG_MSG = "SUBS language set via command: {arg}"
    SUBS_LANGUAGE_AUTO_SET_LOG_MSG = "SUBS language + auto mode set via command: {arg} auto"
    SUBS_MENU_OPENED_LOG_MSG = "उपयोगकर्ता opened /subs मेनू."
    SUBS_LANGUAGE_SET_CALLBACK_LOG_MSG = "User set subtitle language to: {lang_code}"
    SUBS_AUTO_MODE_TOGGLED_LOG_MSG = "User toggled AUTO/TRANS mode to: {new_auto}"
    SUBS_ALWAYS_ASK_TOGGLED_LOG_MSG = "User toggled Always Ask mode to: {new_always_ask}"
    
    # Cookies log messages
    COOKIES_BROWSER_REQUESTED_LOG_MSG = "उपयोगकर्ता requested cookies से ब्राउज़र."
    COOKIES_BROWSER_SELECTION_SENT_LOG_MSG = "ब्राउज़र selection keyboard sent with installed browsers केवल."
    COOKIES_BROWSER_SELECTION_CLOSED_LOG_MSG = "ब्राउज़र selection बंद."
    COOKIES_FALLBACK_SUCCESS_LOG_MSG = "Fallback COOKIE_URL used successfully (source hidden)"
    COOKIES_FALLBACK_FAILED_LOG_MSG = "Fallback COOKIE_URL failed: status={status} (hidden)"
    COOKIES_FALLBACK_UNEXPECTED_ERROR_LOG_MSG = "Fallback COOKIE_URL unexpected error: {error_type}: {error}"
    COOKIES_BROWSER_NOT_INSTALLED_LOG_MSG = "Browser {browser} not installed."
    COOKIES_SAVED_BROWSER_LOG_MSG = "Cookies saved using browser: {browser}"
    COOKIES_FILE_SAVED_USER_LOG_MSG = "Cookie file saved for user {user_id}."
    COOKIES_FILE_WORKING_LOG_MSG = "Cookie फ़ाइल exists, has सही प्रारूप, and YouTube cookies are working."
    COOKIES_FILE_EXPIRED_LOG_MSG = "Cookie फ़ाइल exists and has सही प्रारूप, but YouTube cookies are समाप्त."
    COOKIES_FILE_CORRECT_FORMAT_LOG_MSG = "Cookie फ़ाइल exists and has सही प्रारूप."
    COOKIES_FILE_INCORRECT_FORMAT_LOG_MSG = "Cookie फ़ाइल exists but has गलत प्रारूप."
    COOKIES_FILE_NOT_FOUND_LOG_MSG = "Cookie फ़ाइल not found."
    COOKIES_SERVICE_URL_EMPTY_LOG_MSG = "{service} cookie URL is empty for user {user_id}."
    COOKIES_SERVICE_URL_NOT_TXT_LOG_MSG = "{service} cookie URL is not .txt (hidden)"
    COOKIES_SERVICE_FILE_TOO_LARGE_LOG_MSG = "{service} cookie file too large: {size} bytes (source hidden)"
    COOKIES_SERVICE_FILE_DOWNLOADED_LOG_MSG = "{service} cookie file downloaded for user {user_id} (source hidden)."
    
    # Admin log messages
    ADMIN_SCRIPT_NOT_FOUND_LOG_MSG = "Script not found: {script_path}"
    ADMIN_FAILED_SEND_STATUS_LOG_MSG = "Failed to send initial status message"
    ADMIN_ERROR_RUNNING_SCRIPT_LOG_MSG = "Error running {script_path}: {stdout}\n{stderr}"
    ADMIN_CACHE_RELOADED_AUTO_LOG_MSG = "Firebase cache reloaded by auto task."
    ADMIN_CACHE_RELOADED_ADMIN_LOG_MSG = "Firebase cache reloaded by admin."
    ADMIN_ERROR_RELOADING_CACHE_LOG_MSG = "Error reloading Firebase cache: {error}"
    ADMIN_BROADCAST_INITIATED_LOG_MSG = "Broadcast initiated. Text:\n{broadcast_text}"
    ADMIN_BROADCAST_SENT_LOG_MSG = "Broadcast message sent to all users."
    ADMIN_BROADCAST_FAILED_LOG_MSG = "Failed to broadcast message: {error}"
    ADMIN_CACHE_CLEARED_LOG_MSG = "Admin {user_id} cleared cache for URL: {url}"
    ADMIN_PORN_UPDATE_STARTED_LOG_MSG = "Admin {user_id} started porn list update script: {script_path}"
    ADMIN_PORN_UPDATE_COMPLETED_LOG_MSG = "Porn list update script completed successfully by admin {user_id}"
    ADMIN_PORN_UPDATE_FAILED_LOG_MSG = "Porn list update script failed by admin {user_id}: {error}"
    ADMIN_SCRIPT_NOT_FOUND_LOG_MSG = "Admin {user_id} tried to run non-existent script: {script_path}"
    ADMIN_PORN_UPDATE_ERROR_LOG_MSG = "Error running porn update script by admin {user_id}: {error}"
    ADMIN_PORN_CACHE_RELOAD_STARTED_LOG_MSG = "Admin {user_id} started porn cache reload"
    ADMIN_PORN_CACHE_RELOAD_ERROR_LOG_MSG = "Error reloading porn cache by admin {user_id}: {error}"
    ADMIN_PORN_CHECK_LOG_MSG = "Admin {user_id} checked URL for NSFW: {url} - Result: {status}"
    
    # Format log messages
    FORMAT_CHANGE_REQUESTED_LOG_MSG = "उपयोगकर्ता requested प्रारूप change."
    FORMAT_ALWAYS_ASK_SET_LOG_MSG = "Format set to ALWAYS_ASK."
    FORMAT_UPDATED_BEST_LOG_MSG = "Format updated to best: {format}"
    FORMAT_UPDATED_ID_LOG_MSG = "Format updated to ID {format_id}: {format}"
    FORMAT_UPDATED_ID_AUDIO_LOG_MSG = "Format updated to ID {format_id} (audio-only): {format}"
    FORMAT_UPDATED_QUALITY_LOG_MSG = "Format updated to quality {quality}: {format}"
    FORMAT_UPDATED_CUSTOM_LOG_MSG = "Format updated to: {format}"
    FORMAT_MENU_SENT_LOG_MSG = "प्रारूप मेनू sent."
    FORMAT_SELECTION_CLOSED_LOG_MSG = "प्रारूप selection बंद."
    FORMAT_CUSTOM_HINT_SENT_LOG_MSG = "कस्टम प्रारूप संकेत sent."
    FORMAT_RESOLUTION_MENU_SENT_LOG_MSG = "प्रारूप resolution मेनू sent."
    FORMAT_RETURNED_MAIN_MENU_LOG_MSG = "Returned को main प्रारूप मेनू."
    FORMAT_UPDATED_CALLBACK_LOG_MSG = "Format updated to: {format}"
    FORMAT_ALWAYS_ASK_SET_CALLBACK_LOG_MSG = "Format set to ALWAYS_ASK."
    FORMAT_CODEC_SET_LOG_MSG = "Codec preference set to {codec}"
    FORMAT_CUSTOM_MENU_CLOSED_LOG_MSG = "कस्टम प्रारूप मेनू बंद"
    
    # Link log messages
    LINK_EXTRACTED_LOG_MSG = "Direct link extracted for user {user_id} from {url}"
    LINK_EXTRACTION_FAILED_LOG_MSG = "Failed to extract direct link for user {user_id} from {url}: {error}"
    LINK_COMMAND_ERROR_LOG_MSG = "Error in link command for user {user_id}: {error}"
    
    # Keyboard log messages
    KEYBOARD_SET_LOG_MSG = "User {user_id} set keyboard to {setting}"
    KEYBOARD_SET_CALLBACK_LOG_MSG = "User {user_id} set keyboard to {setting}"
    
    # MediaInfo log messages
    MEDIAINFO_SET_COMMAND_LOG_MSG = "MediaInfo set via command: {arg}"
    MEDIAINFO_MENU_OPENED_LOG_MSG = "उपयोगकर्ता opened /mediainfo मेनू."
    MEDIAINFO_MENU_CLOSED_LOG_MSG = "MediaInfo: बंद."
    MEDIAINFO_ENABLED_LOG_MSG = "MediaInfo सक्षम."
    MEDIAINFO_DISABLED_LOG_MSG = "MediaInfo अक्षम."
    
    # Split log messages
    SPLIT_SIZE_SET_ARGUMENT_LOG_MSG = "Split size set to {size} bytes via argument."
    SPLIT_MENU_OPENED_LOG_MSG = "उपयोगकर्ता opened /split मेनू."
    SPLIT_SELECTION_CLOSED_LOG_MSG = "Split selection बंद."
    SPLIT_SIZE_SET_CALLBACK_LOG_MSG = "Split size set to {size} bytes."
    
    # Proxy log messages
    PROXY_SET_COMMAND_LOG_MSG = "Proxy set via command: {arg}"
    PROXY_MENU_OPENED_LOG_MSG = "उपयोगकर्ता opened /proxy मेनू."
    PROXY_MENU_CLOSED_LOG_MSG = "Proxy: बंद."
    PROXY_ENABLED_LOG_MSG = "Proxy सक्षम."
    PROXY_DISABLED_LOG_MSG = "Proxy अक्षम."
    
    # Other handlers log messages
    HELP_MESSAGE_CLOSED_LOG_MSG = "सहायता संदेश बंद."
    AUDIO_HELP_SHOWN_LOG_MSG = "Showed /ऑडियो सहायता"
    PLAYLIST_HELP_REQUESTED_LOG_MSG = "उपयोगकर्ता requested playlist सहायता."
    PLAYLIST_HELP_CLOSED_LOG_MSG = "Playlist सहायता बंद."
    AUDIO_HINT_CLOSED_LOG_MSG = "ऑडियो संकेत बंद."
    
    # Down and Up log messages
    DIRECT_LINK_MENU_CREATED_LOG_MSG = "Direct link menu created via LINK button for user {user_id} from {url}"
    DIRECT_LINK_EXTRACTION_FAILED_LOG_MSG = "Failed to extract direct link via LINK button for user {user_id} from {url}: {error}"
    LIST_COMMAND_EXECUTED_LOG_MSG = "LIST command executed for user {user_id}, url: {url}"
    QUICK_EMBED_LOG_MSG = "Quick Embed: {embed_url}"
    ALWAYS_ASK_MENU_SENT_LOG_MSG = "Always Ask menu sent for {url}"
    CACHED_QUALITIES_MENU_CREATED_LOG_MSG = "Created cached qualities menu for user {user_id} after error: {error}"
    ALWAYS_ASK_MENU_ERROR_LOG_MSG = "Always Ask menu error for {url}: {error}"
    ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG = "प्रारूप is fixed via /args सेटिंग्स"
    ALWAYS_ASK_AUDIO_TYPE_MSG = "ऑडियो"
    ALWAYS_ASK_VIDEO_TYPE_MSG = "वीडियो"
    ALWAYS_ASK_VIDEO_TITLE_MSG = "वीडियो"
    ALWAYS_ASK_NEXT_BUTTON_MSG = "अगला ▶️"
    SUBTITLES_NEXT_BUTTON_MSG = "अगला ➡️"
    PORN_ALL_TEXT_FIELDS_EMPTY_MSG = "ℹ️ सभी टेक्स्ट fields are खाली"
    SENDER_VIDEO_DURATION_MSG = "वीडियो अवधि:"
    SENDER_UPLOADING_FILE_MSG = "📤 Uploading फ़ाइल..."
    DOWN_UP_VIDEO_INFO_MSG = "📋 वीडियो Info"
    DOWN_UP_NUMBER_MSG = "संख्या"
    DOWN_UP_TITLE_MSG = "शीर्षक"
    DOWN_UP_ID_MSG = "ID"
    DOWN_UP_DOWNLOADED_VIDEO_MSG = "☑️ Downloaded वीडियो."
    DOWN_UP_PROCESSING_UPLOAD_MSG = "📤 प्रसंस्करण हो रहा है for अपलोड..."
    DOWN_UP_SPLITTED_PART_UPLOADED_MSG = "📤 Splitted part {part} file uploaded"
    DOWN_UP_UPLOAD_COMPLETE_MSG = "✅ अपलोड पूर्ण"
    DOWN_UP_FILES_UPLOADED_MSG = "files uploaded"
    
    # Always Ask Menu Button Messages
    ALWAYS_ASK_VLC_ANDROID_BUTTON_MSG = "🎬 VLC (Android)"
    ALWAYS_ASK_CLOSE_BUTTON_MSG = "🔚 पास"
    ALWAYS_ASK_CODEC_BUTTON_MSG = "📼CODEC"
    ALWAYS_ASK_DUBS_BUTTON_MSG = "🗣 DUBS"
    ALWAYS_ASK_SUBS_BUTTON_MSG = "💬 SUBS"
    ALWAYS_ASK_BROWSER_BUTTON_MSG = "🌐 ब्राउज़र"
    ALWAYS_ASK_VLC_IOS_BUTTON_MSG = "🎬 VLC (iOS)"
    
    # Always Ask Menu Callback Messages
    ALWAYS_ASK_GETTING_DIRECT_LINK_MSG = "🔗 Getting direct लिंक..."
    ALWAYS_ASK_GETTING_FORMATS_MSG = "📃 Getting उपलब्ध formats..."
    ALWAYS_ASK_STARTING_GALLERY_DL_MSG = "🖼 Starting gallery-dl…"
    
    # Always Ask Menu F-String Messages
    ALWAYS_ASK_DURATION_MSG = "⏱ <b>Duration:</b>"
    ALWAYS_ASK_FORMAT_MSG = "🎛 <b>Format:</b>"
    ALWAYS_ASK_BROWSER_MSG = "🌐 <b>Browser:</b> Open in web browser"
    ALWAYS_ASK_AVAILABLE_FORMATS_FOR_MSG = "उपलब्ध formats for"
    ALWAYS_ASK_HOW_TO_USE_FORMAT_IDS_MSG = "💡 How को use प्रारूप IDs:"
    ALWAYS_ASK_AFTER_GETTING_LIST_MSG = "बाद में getting the सूची, use specific प्रारूप ID:"
    ALWAYS_ASK_FORMAT_ID_401_MSG = "• /प्रारूप id 401 - डाउनलोड प्रारूप 401"
    ALWAYS_ASK_FORMAT_ID401_MSG = "• /प्रारूप id401 - same as ऊपर"
    ALWAYS_ASK_FORMAT_ID_140_AUDIO_MSG = "• /प्रारूप id 140 ऑडियो - डाउनलोड प्रारूप 140 as MP3 ऑडियो"
    ALWAYS_ASK_AUDIO_ONLY_FORMATS_DETECTED_MSG = "🎵 ऑडियो-केवल formats detected"
    ALWAYS_ASK_THESE_FORMATS_MP3_MSG = "These formats will be downloaded as MP3 ऑडियो files."
    ALWAYS_ASK_HOW_TO_SET_FORMAT_MSG = "💡 <b>How to set format:</b>"
    ALWAYS_ASK_FORMAT_ID_134_MSG = "• <code>/format id 134</code> - Download specific format ID"
    ALWAYS_ASK_FORMAT_720P_MSG = "• <code>/format 720p</code> - Download by quality"
    ALWAYS_ASK_FORMAT_BEST_MSG = "• <code>/format best</code> - Download best quality"
    ALWAYS_ASK_FORMAT_ASK_MSG = "• <code>/format ask</code> - Always ask for quality"
    ALWAYS_ASK_AUDIO_ONLY_FORMATS_MSG = "🎵 <b>Audio-only formats:</b>"
    ALWAYS_ASK_FORMAT_ID_140_AUDIO_CAPTION_MSG = "• <code>/format id 140 audio</code> - Download format 140 as MP3 audio"
    ALWAYS_ASK_THESE_WILL_BE_MP3_MSG = "These will be downloaded as MP3 ऑडियो files."
    ALWAYS_ASK_USE_FORMAT_ID_MSG = "📋 Use प्रारूप ID से the सूची ऊपर"
    ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_MSG = "❌ त्रुटि: Original संदेश not found."
    ALWAYS_ASK_FORMATS_PAGE_MSG = "Formats पेज"
    ALWAYS_ASK_ERROR_SHOWING_FORMATS_MENU_MSG = "❌ त्रुटि showing formats मेनू"
    ALWAYS_ASK_ERROR_GETTING_FORMATS_MSG = "❌ त्रुटि getting formats"
    ALWAYS_ASK_ERROR_GETTING_AVAILABLE_FORMATS_MSG = "❌ त्रुटि getting उपलब्ध formats."
    ALWAYS_ASK_PLEASE_TRY_AGAIN_LATER_MSG = "कृपया पुनः प्रयास करें बाद में."
    ALWAYS_ASK_YTDLP_CANNOT_PROCESS_MSG = "🔄 <b>yt-dlp cannot process this content"
    ALWAYS_ASK_SYSTEM_RECOMMENDS_GALLERY_DL_MSG = "The सिस्टम recommends using gallery-dl instead."
    ALWAYS_ASK_OPTIONS_MSG = "**विकल्प:**"
    ALWAYS_ASK_FOR_IMAGE_GALLERIES_MSG = "• For image galleries: <code>/img 1-10</code>"
    ALWAYS_ASK_FOR_SINGLE_IMAGES_MSG = "• For single images: <code>/img</code>"
    ALWAYS_ASK_GALLERY_DL_WORKS_BETTER_MSG = "Gallery-dl often works बेहतर for Instagram, Twitter, and other social मीडिया सामग्री."
    ALWAYS_ASK_TRY_GALLERY_DL_BUTTON_MSG = "🖼 Try Gallery-dl"
    ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG = "🔒 प्रारूप fixed via /args"
    ALWAYS_ASK_SUBTITLES_MSG = "🔤 Subtitles"
    ALWAYS_ASK_DUBBED_AUDIO_MSG = "🎧 Dubbed ऑडियो"
    ALWAYS_ASK_SUBTITLES_ARE_AVAILABLE_MSG = "💬 — Subtitles are उपलब्ध"
    ALWAYS_ASK_CHOOSE_SUBTITLE_LANGUAGE_MSG = "💬 — चुनें subtitle language"
    ALWAYS_ASK_SUBS_NOT_FOUND_MSG = "⚠️ Subs not found & won't embed"
    ALWAYS_ASK_INSTANT_REPOST_MSG = "🚀 — Instant repost से cache"
    ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG = "🗣 — चुनें ऑडियो language"
    ALWAYS_ASK_NSFW_IS_PAID_MSG = "⭐️ — 🔞NSFW is paid (⭐️$0.02)"
    ALWAYS_ASK_CHOOSE_DOWNLOAD_QUALITY_MSG = "📹 — चुनें डाउनलोड गुणवत्ता"
    ALWAYS_ASK_DOWNLOAD_IMAGE_MSG = "🖼 — डाउनलोड छवि (gallery-dl)"
    ALWAYS_ASK_WATCH_VIDEO_MSG = "👁 — Watch वीडियो में poketube"
    ALWAYS_ASK_GET_DIRECT_LINK_MSG = "🔗 — Get direct लिंक को वीडियो"
    ALWAYS_ASK_SHOW_AVAILABLE_FORMATS_MSG = "📃 — Show उपलब्ध formats सूची"
    ALWAYS_ASK_CHANGE_VIDEO_EXT_MSG = "📼 — Сhange वीडियो ext/codec"
    ALWAYS_ASK_OTHER_LABEL_MSG = "🎛Other"
    ALWAYS_ASK_SUB_ONLY_BUTTON_MSG = "📝sub केवल"
    ALWAYS_ASK_SMART_GROUPING_MSG = "स्मार्ट समूहीकरण"
    ALWAYS_ASK_ADDED_ACTION_BUTTON_ROW_3_MSG = "Added action बटन पंक्ति (3)"
    ALWAYS_ASK_ADDED_ACTION_BUTTON_ROWS_2_2_MSG = "Added action बटन rows (2+2)"
    ALWAYS_ASK_ADDED_BOTTOM_BUTTONS_TO_EXISTING_ROW_MSG = "Added bottom buttons को existing पंक्ति"
    ALWAYS_ASK_CREATED_NEW_BOTTOM_ROW_MSG = "Created नया bottom पंक्ति"
    ALWAYS_ASK_NO_VIDEOS_FOUND_IN_PLAYLIST_MSG = "नहीं videos found में playlist"
    ALWAYS_ASK_UNSUPPORTED_URL_MSG = "Unsupported यूआरएल"
    ALWAYS_ASK_NO_VIDEO_COULD_BE_FOUND_MSG = "नहीं वीडियो could be found"
    ALWAYS_ASK_NO_VIDEO_FOUND_MSG = "नहीं वीडियो found"
    ALWAYS_ASK_NO_MEDIA_FOUND_MSG = "नहीं मीडिया found"
    ALWAYS_ASK_THIS_TWEET_DOES_NOT_CONTAIN_MSG = "This tweet does not contain"
    ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_MSG = "❌ <b>Error retrieving video information:</b>"
    ALWAYS_ASK_TRY_CLEAN_COMMAND_MSG = "Try the <code>/clean</code> command and try again. If the error persists, YouTube requires authorization. Update cookies.txt via <code>/cookie</code> or <code>/cookies_from_browser</code> and try again."
    ALWAYS_ASK_MENU_CLOSED_MSG = "मेनू बंद."
    ALWAYS_ASK_MANUAL_QUALITY_SELECTION_MSG = "🎛 मैनुअल गुणवत्ता Selection"
    ALWAYS_ASK_CHOOSE_QUALITY_MANUALLY_MSG = "चुनें गुणवत्ता manually से स्वचालित detection असफल:"
    ALWAYS_ASK_ALL_AVAILABLE_FORMATS_MSG = "🎛 सभी उपलब्ध Formats"
    ALWAYS_ASK_AVAILABLE_QUALITIES_FROM_CACHE_MSG = "📹 उपलब्ध Qualities (से cache)"
    ALWAYS_ASK_USING_CACHED_QUALITIES_MSG = "⚠️ Using cached qualities - नया formats may not be उपलब्ध"
    ALWAYS_ASK_DOWNLOADING_FORMAT_MSG = "📥 डाउनलोड हो रहा है प्रारूप"
    ALWAYS_ASK_DOWNLOADING_QUALITY_MSG = "📥 डाउनलोड हो रहा है"
    ALWAYS_ASK_FORMATS_PAGE_FROM_CACHE_MSG = "Formats पेज"
    ALWAYS_ASK_FROM_CACHE_MSG = "(से cache)"
    ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_DETAILED_MSG = "❌ त्रुटि: Original संदेश not found. It might have been deleted. Please भेजें the लिंक again."
    ALWAYS_ASK_ERROR_ORIGINAL_URL_NOT_FOUND_MSG = "❌ त्रुटि: Original यूआरएल not found. Please भेजें the लिंक again."
    ALWAYS_ASK_DIRECT_LINK_OBTAINED_MSG = "🔗 <b>Direct link obtained</b>"
    ALWAYS_ASK_TITLE_MSG = "📹 <b>Title:</b>"
    ALWAYS_ASK_DURATION_SEC_MSG = "⏱ <b>Duration:</b>"
    ALWAYS_ASK_FORMAT_CODE_MSG = "🎛 <b>Format:</b>"
    ALWAYS_ASK_VIDEO_STREAM_MSG = "🎬 <b>Video stream:</b>"
    ALWAYS_ASK_AUDIO_STREAM_MSG = "🎵 <b>Audio stream:</b>"
    ALWAYS_ASK_FAILED_TO_GET_STREAM_LINKS_MSG = "❌ असफल को get stream links"
    DIRECT_LINK_EXTRACTED_ALWAYS_ASK_LOG_MSG = "Direct link extracted via Always Ask menu for user {user_id} from {url}"
    DIRECT_LINK_FAILED_ALWAYS_ASK_LOG_MSG = "Failed to extract direct link via Always Ask menu for user {user_id} from {url}: {error}"
    DIRECT_LINK_EXTRACTED_DOWN_UP_LOG_MSG = "Direct link extracted via down_and_up_with_format for user {user_id} from {url}"
    DIRECT_LINK_FAILED_DOWN_UP_LOG_MSG = "Failed to extract direct link via down_and_up_with_format for user {user_id} from {url}: {error}"
    DIRECT_LINK_EXTRACTED_DOWN_AUDIO_LOG_MSG = "Direct link extracted via down_and_audio for user {user_id} from {url}"
    DIRECT_LINK_FAILED_DOWN_AUDIO_LOG_MSG = "Failed to extract direct link via down_and_audio for user {user_id} from {url}: {error}"
    
    # Audio processing messages
    AUDIO_SENT_FROM_CACHE_MSG = "✅ ऑडियो sent से cache."
    AUDIO_PROCESSING_MSG = "🎙️ ऑडियो is प्रसंस्करण हो रहा है..."
    AUDIO_DOWNLOADING_PROGRESS_MSG = "{process}\n📥 Downloading audio:\n{bar}   {percent:.1f}%"
    AUDIO_DOWNLOAD_ERROR_MSG = "त्रुटि occurred दौरान ऑडियो डाउनलोड."
    AUDIO_DOWNLOAD_COMPLETE_MSG = "{process}\n{bar}   100.0%"
    AUDIO_EXTRACTION_FAILED_MSG = "❌ असफल को extract ऑडियो जानकारी"
    AUDIO_UNSUPPORTED_FILE_TYPE_MSG = "Skipping unsupported file type in playlist at index {index}"
    AUDIO_FILE_NOT_FOUND_MSG = "ऑडियो फ़ाइल not found बाद में डाउनलोड."
    AUDIO_UPLOADING_MSG = "{process}\n📤 Uploading audio file...\n{bar}   100.0%"
    AUDIO_SEND_FAILED_MSG = "❌ Failed to send audio: {error}"
    PLAYLIST_AUDIO_SENT_LOG_MSG = "Playlist audio sent: {sent}/{total} files (quality={quality}) to user{user_id}"
    AUDIO_DOWNLOAD_FAILED_MSG = "❌ Failed to download audio: {error}"
    DOWNLOAD_TIMEOUT_MSG = "⏰ डाउनलोड cancelled देय को टाइमआउट (2 hours)"
    VIDEO_DOWNLOAD_COMPLETE_MSG = "{process}\n{bar}   100.0%"
    
    # FFmpeg messages
    VIDEO_FILE_NOT_FOUND_MSG = "❌ Video file not found: {filename}"
    VIDEO_PROCESSING_ERROR_MSG = "❌ Error processing video: {error}"
    
    # Sender messages
    ERROR_SENDING_DESCRIPTION_FILE_MSG = "❌ Error sending description file: {error}"
    CHANGE_CAPTION_HINT_MSG = "<blockquote>📝 if you want to change video caption - reply to video with new text</blockquote>"
    
    # Always Ask Menu Messages
    NO_SUBTITLES_DETECTED_MSG = "नहीं subtitles detected"
    CHOOSE_SUBTITLE_LANGUAGE_MSG = "चुनें subtitle language"
    NO_ALTERNATIVE_AUDIO_LANGUAGES_MSG = "नहीं विकल्प ऑडियो languages"
    CHOOSE_AUDIO_LANGUAGE_MSG = "चुनें ऑडियो language"
    PAGE_NUMBER_MSG = "Page {page}"
    SUBTITLE_MENU_CLOSED_MSG = "Subtitle मेनू बंद."
    SUBTITLE_LANGUAGE_SET_MSG = "Subtitle language set: {value}"
    AUDIO_SET_MSG = "Audio set: {value}"
    FILTERS_UPDATED_MSG = "फिल्टर अपडेट किए गए"
    
    # Always Ask Menu Buttons
    BACK_BUTTON_TEXT = "🔙Back"
    CLOSE_BUTTON_TEXT = "🔚Close"
    LIST_BUTTON_TEXT = "📃List"
    IMAGE_BUTTON_TEXT = "🖼Image"
    
    # Always Ask Menu Notes
    QUALITIES_NOT_AUTO_DETECTED_NOTE = "<blockquote>⚠️ Qualities not auto-detected\nUse 'Other' button to see all available formats.</blockquote>"
    
    # Live Stream Messages
    LIVE_STREAM_DETECTED_MSG = "🚫 **Live Stream Detected**\n\nDownloading of ongoing or infinite live streams is not allowed.\n\nPlease wait for the stream को अंत and try डाउनलोड हो रहा है again when:\n• The stream अवधि is known\n• The stream has finished\n"
    AV1_NOT_AVAILABLE_FORMAT_SELECT_MSG = "Please select a different format using `/format` command."
    
    # Direct Link Messages
    DIRECT_LINK_OBTAINED_MSG = "🔗 <b>Direct link obtained</b>\n\n"
    TITLE_FIELD_MSG = "📹 <b>Title:</b> {title}\n"
    DURATION_FIELD_MSG = "⏱ <b>Duration:</b> {duration} sec\n"
    FORMAT_FIELD_MSG = "🎛 <b>Format:</b> <code>{format_spec}</code>\n\n"
    VIDEO_STREAM_FIELD_MSG = "🎬 <b>Video stream:</b>\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
    AUDIO_STREAM_FIELD_MSG = "🎵 <b>Audio stream:</b>\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
    
    # Processing Error Messages
    FILE_PROCESSING_ERROR_INVALID_CHARS_MSG = "❌ **फ़ाइल प्रसंस्करण हो रहा है त्रुटि**\n\nThe वीडियो was downloaded but couldn't be processed देय को अमान्य characters में the filename.\n\n"
    FILE_PROCESSING_ERROR_INVALID_ARG_MSG = "❌ **फ़ाइल प्रसंस्करण हो रहा है त्रुटि**\n\nThe वीडियो was downloaded but couldn't be processed देय को an अमान्य argument त्रुटि.\n\n"
    FORMAT_NOT_AVAILABLE_MSG = "❌ **प्रारूप Not उपलब्ध**\n\nThe requested वीडियो प्रारूप is not उपलब्ध for this वीडियो.\n\n"
    FORMAT_ID_NOT_FOUND_MSG = "❌ Format ID {format_id} not found for this video.\n\nAvailable format IDs: {available_ids}\n"
    AV1_FORMAT_NOT_AVAILABLE_MSG = "❌ **AV1 format is not available for this video.**\n\n**Available formats:**\n{formats_text}\n\n"
    
    # Additional Error Messages  
    AUDIO_FILE_PROCESSING_ERROR_INVALID_CHARS_MSG = "❌ **फ़ाइल प्रसंस्करण हो रहा है त्रुटि**\n\nThe ऑडियो was downloaded but couldn't be processed देय को अमान्य characters में the filename.\n\n"
    AUDIO_FILE_PROCESSING_ERROR_INVALID_ARG_MSG = "❌ **फ़ाइल प्रसंस्करण हो रहा है त्रुटि**\n\nThe ऑडियो was downloaded but couldn't be processed देय को an अमान्य argument त्रुटि.\n\n"
    
    # Keyboard Buttons
    CLEAN_EMOJI = "🧹"
    COOKIE_EMOJI = "🍪" 
    SETTINGS_EMOJI = "⚙️"
    PROXY_EMOJI = "🌐"
    IMAGE_EMOJI = "🖼"
    SEARCH_EMOJI = "🔍"
    VIDEO_EMOJI = "📼"
    USAGE_EMOJI = "📊"
    SPLIT_EMOJI = "✂️"
    AUDIO_EMOJI = "🎧"
    SUBTITLE_EMOJI = "💬"
    LANGUAGE_EMOJI = "🌎"
    TAG_EMOJI = "#️⃣"
    HELP_EMOJI = "🆘"
    LIST_EMOJI = "📃"
    PLAY_EMOJI = "⏯️"
    KEYBOARD_EMOJI = "🎹"
    LINK_EMOJI = "🔗"
    ARGS_EMOJI = "🧰"
    NSFW_EMOJI = "🔞"
    LIST_EMOJI = "📃"
    
    # NSFW Content Messages
    PORN_CONTENT_CANNOT_DOWNLOAD_MSG = "उपयोगकर्ता entered a porn सामग्री. Cannot be downloaded."
    
    # Additional Log Messages
    NSFW_BLUR_SET_COMMAND_LOG_MSG = "NSFW blur set via command: {arg}"
    NSFW_MENU_OPENED_LOG_MSG = "उपयोगकर्ता opened /nsfw मेनू."
    NSFW_MENU_CLOSED_LOG_MSG = "NSFW: बंद."
    COOKIES_DOWNLOAD_FAILED_LOG_MSG = "Failed to download {service} cookie: status={status} (url hidden)"
    COOKIES_DOWNLOAD_ERROR_LOG_MSG = "Error downloading {service} cookie: {error} (url hidden)"
    COOKIES_DOWNLOAD_UNEXPECTED_ERROR_LOG_MSG = "Unexpected error while downloading {service} cookie (url hidden): {error_type}: {error}"
    COOKIES_FILE_UPDATED_LOG_MSG = "Cookie file updated for user {user_id}."
    COOKIES_INVALID_CONTENT_LOG_MSG = "Invalid cookie content provided by user {user_id}."
    COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG = "YouTube cookie URLs are empty for user {user_id}."
    COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG = "YouTube cookies downloaded and validated for user {user_id} from source {source}."
    COOKIES_YOUTUBE_ALL_FAILED_LOG_MSG = "All YouTube cookie sources failed for user {user_id}."
    ADMIN_CHECK_PORN_ERROR_LOG_MSG = "Error in check_porn command by admin {admin_id}: {error}"
    SPLIT_SIZE_SET_CALLBACK_LOG_MSG = "Split part size set to {size} bytes."
    VIDEO_UPLOAD_COMPLETED_SPLITTING_LOG_MSG = "वीडियो अपलोड completed with फ़ाइल splitting."
    PLAYLIST_VIDEOS_SENT_LOG_MSG = "Playlist videos sent: {sent}/{total} files (quality={quality}) to user {user_id}"
    UNKNOWN_ERROR_MSG = "❌ Unknown error: {error}"
    SKIPPING_UNSUPPORTED_FILE_TYPE_MSG = "Skipping unsupported file type in playlist at index {index}"
    FFMPEG_NOT_FOUND_MSG = "❌ FFmpeg not found. Please इंस्टॉल FFmpeg."
    CONVERSION_TO_MP4_FAILED_MSG = "❌ Conversion to MP4 failed: {error}"
    EMBEDDING_SUBTITLES_WARNING_MSG = "⚠️ Embedding subtitles may take a long समय (up को 1 min per 1 min of वीडियो)!\n🔥 Starting को burn subtitles..."
    SUBTITLES_CANNOT_EMBED_LIMITS_MSG = "ℹ️ Subtitles cannot be embedded देय को limits (गुणवत्ता/अवधि/आकार)"
    SUBTITLES_NOT_AVAILABLE_LANGUAGE_MSG = "ℹ️ Subtitles are not उपलब्ध for the selected language"
    ERROR_SENDING_VIDEO_MSG = "❌ Error sending video: {error}"
    PLAYLIST_VIDEOS_SENT_MSG = "✅ Playlist videos sent: {sent}/{total} files."
    DOWNLOAD_CANCELLED_TIMEOUT_MSG = "⏰ डाउनलोड cancelled देय को टाइमआउट (2 hours)"
    FAILED_DOWNLOAD_VIDEO_MSG = "❌ Failed to download video: {error}"
    ERROR_SUBTITLES_NOT_FOUND_MSG = "❌ Error: {error}"
    
    # Args command error messages
    ARGS_JSON_MUST_BE_OBJECT_MSG = "❌ JSON must be an वस्तु (शब्दकोश)."
    ARGS_INVALID_JSON_FORMAT_MSG = "❌ अमान्य JSON प्रारूप. Please provide मान्य JSON."
    ARGS_VALUE_MUST_BE_BETWEEN_MSG = "❌ Value must be between {min_val} and {max_val}."
    ARGS_PARAM_SET_TO_MSG = "✅ {description} set to: <code>{value}</code>"
    
    # Args command button texts
    ARGS_TRUE_BUTTON_MSG = "✅ सत्य"
    ARGS_FALSE_BUTTON_MSG = "❌ असत्य"
    ARGS_BACK_BUTTON_MSG = "🔙 वापस"
    
    # Args command status texts
    ARGS_STATUS_TRUE_MSG = "✅"
    ARGS_STATUS_FALSE_MSG = "❌"
    ARGS_STATUS_TRUE_DISPLAY_MSG = "✅ सत्य"
    ARGS_STATUS_FALSE_DISPLAY_MSG = "❌ असत्य"
    
    # Args command status indicators
    ARGS_STATUS_SELECTED_MSG = "✅"
    ARGS_STATUS_UNSELECTED_MSG = "⚪"
    
    # Down and Up error messages
    DOWN_UP_AV1_NOT_AVAILABLE_MSG = "❌ AV1 format is not available for this video.\n\nAvailable formats:\n{formats_text}"
    DOWN_UP_ERROR_DOWNLOADING_MSG = "❌ Error downloading: {error_message}"
    DOWN_UP_NO_VIDEOS_PLAYLIST_MSG = "❌ No videos found in playlist at index {index}."
    DOWN_UP_VIDEO_CONVERSION_FAILED_INVALID_MSG = "❌ **वीडियो Conversion असफल**\n\nThe वीडियो couldn't be converted को MP4 देय को an अमान्य argument त्रुटि.\n\n"
    DOWN_UP_VIDEO_CONVERSION_FAILED_MSG = "❌ **वीडियो Conversion असफल**\n\nThe वीडियो couldn't be converted को MP4.\n\n"
    DOWN_UP_FAILED_STREAM_LINKS_MSG = "❌ असफल को get stream links"
    DOWN_UP_ERROR_GETTING_LINK_MSG = "❌ <b>Error getting link:</b>\n{error_msg}"
    DOWN_UP_NO_CONTENT_FOUND_MSG = "❌ No content found at index {index}"

    # Always Ask Menu error messages
    AA_ERROR_ORIGINAL_NOT_FOUND_MSG = "❌ त्रुटि: Original संदेश not found."
    AA_ERROR_URL_NOT_FOUND_MSG = "❌ त्रुटि: यूआरएल not found."
    AA_ERROR_URL_NOT_EMBEDDABLE_MSG = "❌ This यूआरएल cannot be embedded."
    AA_ERROR_CODEC_NOT_AVAILABLE_MSG = "❌ {codec} codec not available for this video"
    AA_ERROR_FORMAT_NOT_AVAILABLE_MSG = "❌ {format} format not available for this video"
    
    # Always Ask Menu button texts
    AA_AVC_BUTTON_MSG = "✅ AVC"
    AA_AVC_BUTTON_INACTIVE_MSG = "☑️ AVC"
    AA_AVC_BUTTON_UNAVAILABLE_MSG = "❌ AVC"
    AA_AV1_BUTTON_MSG = "✅ AV1"
    AA_AV1_BUTTON_INACTIVE_MSG = "☑️ AV1"
    AA_AV1_BUTTON_UNAVAILABLE_MSG = "❌ AV1"
    AA_VP9_BUTTON_MSG = "✅ VP9"
    AA_VP9_BUTTON_INACTIVE_MSG = "☑️ VP9"
    AA_VP9_BUTTON_UNAVAILABLE_MSG = "❌ VP9"
    AA_MP4_BUTTON_MSG = "✅ MP4"
    AA_MP4_BUTTON_INACTIVE_MSG = "☑️ MP4"
    AA_MP4_BUTTON_UNAVAILABLE_MSG = "❌ MP4"
    AA_MKV_BUTTON_MSG = "✅ MKV"
    AA_MKV_BUTTON_INACTIVE_MSG = "☑️ MKV"
    AA_MKV_BUTTON_UNAVAILABLE_MSG = "❌ MKV"

    # Flood limit messages
    FLOOD_LIMIT_TRY_LATER_MSG = "⏳ Flood सीमा. Try बाद में."
    
    # Cookies command button texts
    COOKIES_BROWSER_BUTTON_MSG = "✅ {browser_name}"
    COOKIES_CHECK_COOKIE_BUTTON_MSG = "✅ जांच Cookie"
    
    # Proxy command button texts
    PROXY_ON_BUTTON_MSG = "✅ पर"
    PROXY_OFF_BUTTON_MSG = "❌ बंद"
    PROXY_CLOSE_BUTTON_MSG = "🔚पास"
    
    # MediaInfo command button texts
    MEDIAINFO_ON_BUTTON_MSG = "✅ पर"
    MEDIAINFO_OFF_BUTTON_MSG = "❌ बंद"
    MEDIAINFO_CLOSE_BUTTON_MSG = "🔚पास"
    
    # Format command button texts
    FORMAT_AVC1_BUTTON_MSG = "✅ avc1 (H.264)"
    FORMAT_AVC1_BUTTON_INACTIVE_MSG = "☑️ avc1 (H.264)"
    FORMAT_AV01_BUTTON_MSG = "✅ av01 (AV1)"
    FORMAT_AV01_BUTTON_INACTIVE_MSG = "☑️ av01 (AV1)"
    FORMAT_VP9_BUTTON_MSG = "✅ vp09 (VP9)"
    FORMAT_VP9_BUTTON_INACTIVE_MSG = "☑️ vp09 (VP9)"
    FORMAT_MKV_ON_BUTTON_MSG = "✅ MKV: पर"
    FORMAT_MKV_OFF_BUTTON_MSG = "☑️ MKV: बंद"
    
    # Subtitles command button texts
    SUBS_LANGUAGE_CHECKMARK_MSG = "✅ "
    SUBS_AUTO_EMOJI_MSG = "✅"
    SUBS_AUTO_EMOJI_INACTIVE_MSG = "☑️"
    SUBS_ALWAYS_ASK_EMOJI_MSG = "✅"
    SUBS_ALWAYS_ASK_EMOJI_INACTIVE_MSG = "☑️"
    
    # NSFW command button texts
    NSFW_ON_NO_BLUR_MSG = "✅ पर (नहीं Blur)"
    NSFW_ON_NO_BLUR_INACTIVE_MSG = "☑️ पर (नहीं Blur)"
    NSFW_OFF_BLUR_MSG = "✅ बंद (Blur)"
    NSFW_OFF_BLUR_INACTIVE_MSG = "☑️ बंद (Blur)"
    
    # Admin command status texts
    ADMIN_STATUS_NSFW_MSG = "🔞"
    ADMIN_STATUS_CLEAN_MSG = "✅"
    ADMIN_STATUS_NSFW_TEXT_MSG = "NSFW"
    ADMIN_STATUS_CLEAN_TEXT_MSG = "साफ"
    
    # Admin command additional messages
    ADMIN_ERROR_PROCESSING_REPLY_MSG = "Error processing reply message for user {user}: {error}"
    ADMIN_ERROR_SENDING_BROADCAST_MSG = "Error sending broadcast to user {user}: {error}"
    ADMIN_LOGS_FORMAT_MSG = "Logs of {bot_name}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n\n{logs}"
    ADMIN_BOT_DATA_FORMAT_MSG = "{bot_name} {path}\nTotal {path}: {count}\nCurrent time: {now}\n\n{data}"
    ADMIN_TOTAL_USERS_MSG = "<i>Total Users: {count}</i>\nLast 20 {path}:\n\n{display_list}"
    ADMIN_PORN_CACHE_RELOADED_MSG = "Porn caches reloaded by admin {admin_id}. Domains: {domains}, Keywords: {keywords}, Sites: {sites}, WHITELIST: {whitelist}, GREYLIST: {greylist}, BLACK_LIST: {black_list}, WHITE_KEYWORDS: {white_keywords}, PROXY_DOMAINS: {proxy_domains}, PROXY_2_DOMAINS: {proxy_2_domains}, CLEAN_QUERY: {clean_query}, NO_COOKIE_DOMAINS: {no_cookie_domains}"
    
    # Args command additional messages
    ARGS_ERROR_SENDING_TIMEOUT_MSG = "टाइमआउट संदेश भेजने में त्रुटि: {error}"
    
    # Language selection messages
    LANG_SELECTION_MSG = "🌍 <b>भाषा चुनें</b>\n\n🇺🇸 English\n🇷🇺 Русский\n🇸🇦 العربية\n🇮🇳 हिन्दी"
    LANG_CHANGED_MSG = "✅ भाषा {lang_name} में बदल गई"
    LANG_ERROR_MSG = "❌ भाषा बदलने में त्रुटि"
    LANG_CLOSED_MSG = "भाषा चयन बंद हो गया"
    
    # Clean command additional messages
    
    # Cookies command additional messages
    COOKIES_BROWSER_CALLBACK_MSG = "[BROWSER] callback: {callback_data}"
    COOKIES_ADDING_BROWSER_MONITORING_MSG = "Adding browser monitoring button with URL: {miniapp_url}"
    COOKIES_BROWSER_MONITORING_URL_NOT_CONFIGURED_MSG = "Browser monitoring URL not configured: {miniapp_url}"
    
    # Format command additional messages
    
    # Keyboard command additional messages
    KEYBOARD_SETTING_UPDATED_MSG = "🎹 **Keyboard setting updated!**\n\nNew setting: **{setting}**"
    KEYBOARD_FAILED_HIDE_MSG = "Failed to hide keyboard: {error}"
    
    # Link command additional messages
    LINK_USING_WORKING_YOUTUBE_COOKIES_MSG = "Using working YouTube cookies for link extraction for user {user_id}"
    LINK_NO_WORKING_YOUTUBE_COOKIES_MSG = "No working YouTube cookies available for link extraction for user {user_id}"
    LINK_USING_EXISTING_YOUTUBE_COOKIES_MSG = "Using existing YouTube cookies for link extraction for user {user_id}"
    LINK_NO_YOUTUBE_COOKIES_FOUND_MSG = "No YouTube cookies found for link extraction for user {user_id}"
    LINK_COPIED_GLOBAL_COOKIE_FILE_MSG = "Copied global cookie file to user {user_id} folder for link extraction"
    
    # MediaInfo command additional messages
    MEDIAINFO_USER_REQUESTED_MSG = "[MEDIAINFO] User {user_id} requested mediainfo command"
    MEDIAINFO_USER_IS_ADMIN_MSG = "[MEDIAINFO] User {user_id} is admin: {is_admin}"
    MEDIAINFO_USER_IS_IN_CHANNEL_MSG = "[MEDIAINFO] User {user_id} is in channel: {is_in_channel}"
    MEDIAINFO_ACCESS_DENIED_MSG = "[MEDIAINFO] User {user_id} access denied - not admin and not in channel"
    MEDIAINFO_ACCESS_GRANTED_MSG = "[MEDIAINFO] User {user_id} access granted"
    MEDIAINFO_CALLBACK_MSG = "[MEDIAINFO] callback: {callback_data}"
    
    # URL Parser error messages
    URL_PARSER_ADMIN_ONLY_MSG = "❌ This command is only available for administrators."
    
    # Helper messages
    HELPER_DOWNLOAD_FINISHED_PO_MSG = "✅ डाउनलोड finished with PO token support"
    HELPER_FLOOD_LIMIT_TRY_LATER_MSG = "⏳ Flood सीमा. Try बाद में."
    
    # Database error messages
    DB_REST_TOKEN_REFRESH_ERROR_MSG = "❌ REST token refresh error: {error}"
    DB_ERROR_CLOSING_SESSION_MSG = "❌ Error closing Firebase session: {error}"
    DB_ERROR_INITIALIZING_BASE_MSG = "❌ Error initializing base db structure: {error}"

    DB_NOT_ALL_PARAMETERS_SET_MSG = "❌ Not all parameters are set in config.py (FIREBASE_CONF, FIREBASE_USER, FIREBASE_PASSWORD)"
    DB_DATABASE_URL_NOT_SET_MSG = "❌ FIREBASE_CONF.databaseURL is not set"
    DB_API_KEY_NOT_SET_MSG = "❌ FIREBASE_CONF.apiKey is not set for getting idToken"
    DB_ERROR_DOWNLOADING_DUMP_MSG = "❌ Error downloading Firebase dump: {error}"
    DB_FAILED_DOWNLOAD_DUMP_REST_MSG = "❌ Failed to download Firebase dump via REST"
    DB_ERROR_DOWNLOAD_RELOAD_CACHE_MSG = "❌ Error in _download_and_reload_cache: {error}"
    DB_ERROR_RUNNING_AUTO_RELOAD_MSG = "❌ Error running auto reload_cache (attempt {attempt}/{max_retries}): {error}"
    DB_ALL_RETRY_ATTEMPTS_FAILED_MSG = "❌ All retry attempts failed"
    DB_STARTING_FIREBASE_DUMP_MSG = "🔄 Starting Firebase dump download at {datetime}"
    DB_DEPENDENCY_NOT_AVAILABLE_MSG = "⚠️ Dependency not available: requests or Session"
    DB_DATABASE_EMPTY_MSG = "⚠️ Database is empty"
    
    # Magic.py error messages
    MAGIC_ERROR_CLOSING_LOGGER_MSG = "❌ Error closing logger: {error}"
    MAGIC_ERROR_DURING_CLEANUP_MSG = "❌ Error during cleanup: {error}"
    
    # Update from repo error messages
    UPDATE_CLONE_ERROR_MSG = "❌ Clone error: {error}"
    UPDATE_CLONE_TIMEOUT_MSG = "❌ Clone टाइमआउट"
    UPDATE_CLONE_EXCEPTION_MSG = "❌ Clone exception: {error}"
    UPDATE_CANCELED_BY_USER_MSG = "❌ अपडेट canceled by उपयोगकर्ता"

    # Update from repo success messages
    UPDATE_REPOSITORY_CLONED_SUCCESS_MSG = "✅ Repository cloned successfully"
    UPDATE_BACKUPS_MOVED_MSG = "✅ Backups moved को _backup/"
    
    # Magic.py success messages
    MAGIC_ALL_MODULES_LOADED_MSG = "✅ All modules are loaded"
    MAGIC_CLEANUP_COMPLETED_MSG = "✅ Cleanup completed on exit"
    MAGIC_SIGNAL_RECEIVED_MSG = "\n🛑 Received signal {signal}, shutting down gracefully..."
    
    # Removed duplicate logger messages - these are user messages, not logger messages
    
    # Download status messages
    DOWNLOAD_STATUS_PLEASE_WAIT_MSG = "कृपया प्रतीक्षा करें..."
    DOWNLOAD_STATUS_HOURGLASS_EMOJIS = ["⏳", "⌛"]
    DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG = "📥 डाउनलोड हो रहा है HLS stream:"
    DOWNLOAD_STATUS_WAITING_FRAGMENTS_MSG = "प्रतीक्षा for fragments"
    
    # Restore from backup messages
    RESTORE_BACKUP_NOT_FOUND_MSG = "❌ Backup {ts} not found in _backup/"
    RESTORE_FAILED_RESTORE_MSG = "❌ Failed to restore {src} -> {dest_path}: {e}"
    RESTORE_SUCCESS_RESTORED_MSG = "✅ Restored: {dest_path}"
    
    # Image command messages
    IMG_INSTAGRAM_AUTH_ERROR_MSG = "❌ <b>{error_type}</b>\n\n<b>URL:</b> <code>{url}</code>\n\n<b>Details:</b> {error_details}\n\nDownload stopped due to critical error.\n\n💡 <b>Tip:</b> If you're getting 401 Unauthorized error, try using <code>/cookie instagram</code> command or send your own cookies to authenticate with Instagram."
    
    # Porn filter messages
    PORN_DOMAIN_BLACKLIST_MSG = "❌ Domain in porn blacklist: {domain_parts}"
    PORN_KEYWORDS_FOUND_MSG = "❌ Found porn keywords: {keywords}"
    PORN_DOMAIN_WHITELIST_MSG = "✅ Domain in whitelist: {domain}"
    PORN_WHITELIST_KEYWORDS_MSG = "✅ Found whitelist keywords: {keywords}"
    PORN_NO_KEYWORDS_FOUND_MSG = "✅ नहीं porn keywords found"
    
    # Audio download messages
    AUDIO_TIKTOK_API_ERROR_SKIP_MSG = "⚠️ TikTok API error at index {index}, skipping to next audio..."
    
    # Video download messages  
    VIDEO_TIKTOK_API_ERROR_SKIP_MSG = "⚠️ TikTok API error at index {index}, skipping to next video..."
    
    # URL Parser messages
    URL_PARSER_USER_ENTERED_URL_LOG_MSG = "User entered a <b>url</b>\n <b>user's name:</b> {user_name}\nURL: {url}"
    URL_PARSER_USER_ENTERED_INVALID_MSG = "<b>User entered like this:</b> {input}\n{error_msg}"
    
    # Channel subscription messages
    CHANNEL_JOIN_BUTTON_MSG = "चैनल में शामिल हों"
    
    # Handler registry messages
    HANDLER_REGISTERING_MSG = "🔍 Registering handler: {handler_type} - {func_name}"
    
    # Clean command button messages
    CLEAN_COOKIE_DOWNLOAD_BUTTON_MSG = "📥 /cookie - डाउनलोड my 5 cookies"
    CLEAN_COOKIES_FROM_BROWSER_BUTTON_MSG = "🌐 /cookies_from_browser - Get ब्राउज़र's YT-cookie"
    CLEAN_CHECK_COOKIE_BUTTON_MSG = "🔎 /check_cookie - मान्य करें your cookie फ़ाइल"
    CLEAN_SAVE_AS_COOKIE_BUTTON_MSG = "🔖 /save_as_cookie - अपलोड कस्टम cookie"
    
    # List command messages
    LIST_CLOSE_BUTTON_MSG = "🔚 पास"
    LIST_AVAILABLE_FORMATS_HEADER_MSG = "Available formats for: {url}"
    LIST_FORMATS_FILE_NAME_MSG = "formats_{user_id}.txt"
    
    # Other handlers button messages
    OTHER_AUDIO_HINT_CLOSE_BUTTON_MSG = "🔚पास"
    OTHER_PLAYLIST_HELP_CLOSE_BUTTON_MSG = "🔚पास"
    
    # Search command button messages
    SEARCH_CLOSE_BUTTON_MSG = "🔚पास"
    
    # Tag command button messages
    TAG_CLOSE_BUTTON_MSG = "🔚पास"
    
    # Magic.py callback messages
    MAGIC_HELP_CLOSED_MSG = "सहायता बंद."
    
    # URL extractor callback messages
    URL_EXTRACTOR_CLOSED_MSG = "बंद"
    URL_EXTRACTOR_ERROR_OCCURRED_MSG = "त्रुटि occurred"
    
    # FFmpeg messages
    FFMPEG_NOT_FOUND_MSG = "ffmpeg not found में पथ or project निर्देशिका. Please इंस्टॉल FFmpeg."
    YTDLP_NOT_FOUND_MSG = "yt-dlp binary not found में पथ or project निर्देशिका. Please इंस्टॉल yt-dlp."
    FFMPEG_VIDEO_SPLIT_EXCESSIVE_MSG = "Video will be split into {rounds} parts, which may be excessive"
    FFMPEG_SPLITTING_VIDEO_PART_MSG = "Splitting video part {current}/{total}: {start_time:.2f}s to {end_time:.2f}s"
    FFMPEG_FAILED_CREATE_SPLIT_PART_MSG = "Failed to create split part {part}: {target_name}"
    FFMPEG_SUCCESSFULLY_CREATED_SPLIT_PART_MSG = "Successfully created split part {part}: {target_name} ({size} bytes)"
    FFMPEG_ERROR_SPLITTING_VIDEO_PART_MSG = "Error splitting video part {part}: {error}"
    FFMPEG_VIDEO_SPLIT_SUCCESS_MSG = "Video split into {count} parts successfully"
    FFMPEG_ERROR_VIDEO_SPLITTING_PROCESS_MSG = "Error in video splitting process: {error}"
    FFMPEG_FFPROBE_BYPASS_ERROR_MSG = "[FFPROBE BYPASS] Error while processing video {video_path}: {error}"
    FFMPEG_VIDEO_FILE_NOT_EXISTS_MSG = "Video file does not exist: {video_path}"
    FFMPEG_ERROR_PARSING_DIMENSIONS_MSG = "Error parsing dimensions '{size_result}': {error}"
    FFMPEG_COULD_NOT_DETERMINE_DIMENSIONS_MSG = "Could not determine video dimensions from '{size_result}', using default: {width}x{height}"
    FFMPEG_ERROR_CREATING_THUMBNAIL_MSG = "Error creating thumbnail: {stderr}"
    FFMPEG_ERROR_PARSING_DURATION_MSG = "Error parsing video duration: {error}, result was: {result}"
    FFMPEG_THUMBNAIL_NOT_CREATED_MSG = "Thumbnail not created at {thumb_dir}, using default"
    FFMPEG_COMMAND_EXECUTION_ERROR_MSG = "Command execution error: {error}"
    FFMPEG_ERROR_CREATING_THUMBNAIL_WITH_FFMPEG_MSG = "Error creating thumbnail with FFmpeg: {error}"
    
    # Gallery-dl messages
    GALLERY_DL_SKIPPING_NON_DICT_CONFIG_MSG = "Skipping non-dict config section: {section}={opts}"
    GALLERY_DL_SETTING_CONFIG_MSG = "Setting {section}.{key} = {value}"
    GALLERY_DL_USING_USER_COOKIES_MSG = "[gallery-dl] Using user cookies: {cookie_path}"
    GALLERY_DL_USING_YOUTUBE_COOKIES_MSG = "Using YouTube cookies for user {user_id}"
    GALLERY_DL_COPIED_GLOBAL_COOKIE_MSG = "Copied global cookie file to user {user_id} folder"
    GALLERY_DL_USING_COPIED_GLOBAL_COOKIES_MSG = "[gallery-dl] Using copied global cookies as user cookies: {cookie_path}"
    GALLERY_DL_FAILED_COPY_GLOBAL_COOKIE_MSG = "Failed to copy global cookie file for user {user_id}: {error}"
    GALLERY_DL_USING_NO_COOKIES_MSG = "Using --no-cookies for domain: {url}"
    GALLERY_DL_PROXY_REQUESTED_FAILED_MSG = "Proxy requested but failed to import/get config: {error}"
    GALLERY_DL_FORCE_USING_PROXY_MSG = "Force using proxy for gallery-dl: {proxy_url}"
    GALLERY_DL_PROXY_CONFIG_INCOMPLETE_MSG = "Proxy requested but proxy कॉन्फ़िगरेशन is अपूर्ण"
    GALLERY_DL_PROXY_HELPER_FAILED_MSG = "Proxy helper failed: {error}"
    GALLERY_DL_PARSING_EXTRACTOR_ITEMS_MSG = "Parsing extractor items..."
    GALLERY_DL_ITEM_COUNT_MSG = "Item {count}: {item}"
    GALLERY_DL_FOUND_METADATA_TAG2_MSG = "Found metadata (tag 2): {info}"
    GALLERY_DL_FOUND_URL_TAG3_MSG = "Found URL (tag 3): {url}, metadata: {metadata}"
    GALLERY_DL_FOUND_METADATA_LEGACY_MSG = "Found metadata (legacy): {info}"
    GALLERY_DL_FOUND_URL_LEGACY_MSG = "Found URL (legacy): {url}"
    GALLERY_DL_FOUND_FILENAME_MSG = "Found filename: {filename}"
    GALLERY_DL_FOUND_DIRECTORY_MSG = "Found directory: {directory}"
    GALLERY_DL_FOUND_EXTENSION_MSG = "Found extension: {extension}"
    GALLERY_DL_PARSED_ITEMS_MSG = "Parsed {count} items, info: {info}, fallback: {fallback}"
    GALLERY_DL_SETTING_CONFIG_MSG2 = "Setting gallery-dl config: {config}"
    GALLERY_DL_TRYING_STRATEGY_A_MSG = "Trying रणनीति A: extractor.find + items()"
    GALLERY_DL_EXTRACTOR_MODULE_NOT_FOUND_MSG = "gallery_dl.extractor module not found"
    GALLERY_DL_EXTRACTOR_FIND_NOT_AVAILABLE_MSG = "gallery_dl.extractor.find() not उपलब्ध में this बिल्ड"
    GALLERY_DL_CALLING_EXTRACTOR_FIND_MSG = "Calling extractor.find({url})"
    GALLERY_DL_NO_EXTRACTOR_MATCHED_MSG = "नहीं extractor matched the यूआरएल"
    GALLERY_DL_SETTING_COOKIES_ON_EXTRACTOR_MSG = "Setting cookies on extractor: {cookie_path}"
    GALLERY_DL_FAILED_SET_COOKIES_ON_EXTRACTOR_MSG = "Failed to set cookies on extractor: {error}"
    GALLERY_DL_EXTRACTOR_FOUND_CALLING_ITEMS_MSG = "Extractor found, calling items()"
    GALLERY_DL_STRATEGY_A_SUCCEEDED_MSG = "Strategy A succeeded, got info: {info}"
    GALLERY_DL_STRATEGY_A_NO_VALID_INFO_MSG = "रणनीति A: extractor.items() returned नहीं मान्य info"
    GALLERY_DL_STRATEGY_A_FAILED_MSG = "Strategy A (extractor.find) failed: {error}"
    GALLERY_DL_FALLBACK_METADATA_MSG = "Fallback metadata from --get-urls: total={total}"
    GALLERY_DL_ALL_STRATEGIES_FAILED_MSG = "सभी strategies असफल को obtain metadata"
    GALLERY_DL_FAILED_EXTRACT_IMAGE_INFO_MSG = "Failed to extract image info: {error}"
    GALLERY_DL_JOB_MODULE_NOT_FOUND_MSG = "gallery_dl.job module not found (broken इंस्टॉल?)"
    GALLERY_DL_DOWNLOAD_JOB_NOT_AVAILABLE_MSG = "gallery_dl.job.DownloadJob not उपलब्ध में this बिल्ड"
    GALLERY_DL_SEARCHING_DOWNLOADED_FILES_MSG = "Searching for downloaded files में gallery-dl निर्देशिका"
    GALLERY_DL_TRYING_FIND_FILES_BY_NAMES_MSG = "Trying को find files by names से extractor"
    
    # Sender messages
    SENDER_ERROR_READING_USER_ARGS_MSG = "Error reading user args for {user_id}: {error}"
    SENDER_FFPROBE_BYPASS_ERROR_MSG = "[FFPROBE BYPASS] Error while processing video{video_path}: {error}"
    SENDER_USER_SEND_AS_FILE_ENABLED_MSG = "User {user_id} has send_as_file enabled, sending as document"
    SENDER_SEND_VIDEO_TIMED_OUT_MSG = "send_video timed out repeatedly; falling वापस को send_document"
    SENDER_CAPTION_TOO_LONG_MSG = "Caption too long, trying with minimal caption"
    SENDER_SEND_VIDEO_MINIMAL_CAPTION_TIMED_OUT_MSG = "send_video (minimal caption) timed out; fallback को send_document"
    SENDER_ERROR_SENDING_VIDEO_MINIMAL_CAPTION_MSG = "Error sending video with minimal caption: {error}"
    SENDER_ERROR_SENDING_FULL_DESCRIPTION_FILE_MSG = "Error sending full description file: {error}"
    SENDER_ERROR_REMOVING_TEMP_DESCRIPTION_FILE_MSG = "Error removing temporary description file: {error}"
    
    # YT-DLP hook messages
    YTDLP_SKIPPING_MATCH_FILTER_MSG = "Skipping match_filter for domain in NO_FILTER_DOMAINS: {url}"
    YTDLP_CHECKING_EXISTING_YOUTUBE_COOKIES_MSG = "Checking existing YouTube cookies on user's URL for format detection for user {user_id}"
    YTDLP_EXISTING_YOUTUBE_COOKIES_WORK_MSG = "Existing YouTube cookies work on user's URL for format detection for user {user_id} - using them"
    YTDLP_EXISTING_YOUTUBE_COOKIES_FAILED_MSG = "Existing YouTube cookies failed on user's URL, trying to get new ones for format detection for user {user_id}"
    YTDLP_TRYING_YOUTUBE_COOKIE_SOURCE_MSG = "Trying YouTube cookie source {i} for format detection for user {user_id}"
    YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_WORK_MSG = "YouTube cookies from source {i} work on user's URL for format detection for user {user_id} - saved to user folder"
    YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_DONT_WORK_MSG = "YouTube cookies from source {i} don't work on user's URL for format detection for user {user_id}"
    YTDLP_FAILED_DOWNLOAD_YOUTUBE_COOKIES_MSG = "Failed to download YouTube cookies from source {i} for format detection for user {user_id}"
    YTDLP_ALL_YOUTUBE_COOKIE_SOURCES_FAILED_MSG = "All YouTube cookie sources failed for format detection for user {user_id}, will try without cookies"
    YTDLP_NO_YOUTUBE_COOKIE_SOURCES_CONFIGURED_MSG = "No YouTube cookie sources configured for format detection for user {user_id}, will try without cookies"
    YTDLP_NO_YOUTUBE_COOKIES_FOUND_MSG = "No YouTube cookies found for format detection for user {user_id}, attempting to get new ones"
    YTDLP_USING_YOUTUBE_COOKIES_ALREADY_VALIDATED_MSG = "Using YouTube cookies for format detection for user {user_id} (already validated in Always Ask menu)"
    YTDLP_NO_YOUTUBE_COOKIES_FOUND_ATTEMPTING_RESTORE_MSG = "No YouTube cookies found for format detection for user {user_id}, attempting to restore..."
    YTDLP_COPIED_GLOBAL_COOKIE_FILE_MSG = "Copied global cookie file to user {user_id} folder for format detection"
    YTDLP_FAILED_COPY_GLOBAL_COOKIE_FILE_MSG = "Failed to copy global cookie file for user {user_id}: {error}"
    YTDLP_USING_NO_COOKIES_FOR_DOMAIN_MSG = "Using --no-cookies for domain in get_video_formats: {url}"
    
    # App instance messages
    APP_INSTANCE_NOT_INITIALIZED_MSG = "App not initialized yet. Cannot access {name}"
    
    # Caption messages
    CAPTION_INFO_OF_VIDEO_MSG = "\n<b>Caption:</b> <code>{caption}</code>\n<b>User id:</b> <code>{user_id}</code>\n<b>User first name:</b> <code>{users_name}</code>\n<b>Video file id:</b> <code>{video_file_id}</code>"
    CAPTION_ERROR_IN_CAPTION_EDITOR_MSG = "Error in caption_editor: {error}"
    CAPTION_UNEXPECTED_ERROR_IN_CAPTION_EDITOR_MSG = "Unexpected error in caption_editor: {error}"
    CAPTION_VIDEO_URL_LINK_MSG = '<a href="{url}">🔗 Video URL</a>{bot_mention}'
    
    # Database messages
    DB_DATABASE_URL_MISSING_MSG = "FIREBASE_CONF.databaseURL отсутствует в Config"
    DB_FIREBASE_ADMIN_INITIALIZED_MSG = "✅ firebase_admin initialized"
    DB_REST_ID_TOKEN_REFRESHED_MSG = "🔁 REST idToken refreshed"
    DB_LOG_FOR_USER_ADDED_MSG = "Log for user added"
    DB_DATABASE_CREATED_MSG = "डेटाबेस बनाया गया"
    DB_BOT_STARTED_MSG = "बॉट शुरू किया गया"
    DB_RELOAD_CACHE_EVERY_PERSISTED_MSG = "RELOAD_CACHE_EVERY persisted to config.py: {hours}h"
    DB_PLAYLIST_PART_ALREADY_CACHED_MSG = "Playlist part already cached: {path_parts}, skipping"
    DB_GET_CACHED_PLAYLIST_VIDEOS_NO_CACHE_MSG = "get_cached_playlist_videos: no cache found for any URL/quality variant, returning empty dict"
    DB_GET_CACHED_PLAYLIST_COUNT_FAST_COUNT_MSG = "get_cached_playlist_count: fast count for large range: {cached_count} cached videos"
    DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_MSG = "get_cached_message_ids: no cache found for hash {url_hash}, quality {quality_key}"
    DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_ANY_VARIANT_MSG = "get_cached_message_ids: no cache found for any URL variant, returning None"
    
    # Database cache auto-reload messages
    DB_AUTO_CACHE_ACCESS_DENIED_MSG = "❌ Access denied. Admin only."
    DB_AUTO_CACHE_RELOADING_UPDATED_MSG = "🔄 Auto Firebase cache reloading updated!\n\n📊 Status: {status}\n⏰ Schedule: every {interval} hours from 00:00\n🕒 Next reload: {next_exec} (in {delta_min} minutes)"
    DB_AUTO_CACHE_RELOADING_STOPPED_MSG = "🛑 Auto Firebase cache reloading stopped!\n\n📊 Status: ❌ DISABLED\n💡 Use /auto_cache on to re-enable"
    DB_AUTO_CACHE_INVALID_ARGUMENT_MSG = "❌ Invalid argument. Use /auto_cache on | off | N (1..168)"
    DB_AUTO_CACHE_INTERVAL_RANGE_MSG = "❌ Interval must be between 1 and 168 hours"
    DB_AUTO_CACHE_FAILED_SET_INTERVAL_MSG = "❌ Failed to set interval"
    DB_AUTO_CACHE_INTERVAL_UPDATED_MSG = "⏱️ Auto Firebase cache interval updated!\n\n📊 Status: ✅ ENABLED\n⏰ Schedule: every {interval} hours from 00:00\n🕒 Next reload: {next_exec} (in {delta_min} minutes)"
    DB_AUTO_CACHE_RELOADING_STARTED_MSG = "🔄 Auto Firebase cache reloading started!\n\n📊 Status: ✅ ENABLED\n⏰ Schedule: every {interval} hours from 00:00\n🕒 Next reload: {next_exec} (in {delta_min} minutes)"
    DB_AUTO_CACHE_RELOADING_STOPPED_BY_ADMIN_MSG = "🛑 Auto Firebase cache reloading stopped!\n\n📊 Status: ❌ DISABLED\n💡 Use /auto_cache on to re-enable"
    DB_AUTO_CACHE_RELOAD_ENABLED_LOG_MSG = "Auto reload ENABLED; next at {next_exec}"
    DB_AUTO_CACHE_RELOAD_DISABLED_LOG_MSG = "Auto reload DISABLED by admin."
    DB_AUTO_CACHE_INTERVAL_SET_LOG_MSG = "Auto reload interval set to {interval}h; next at {next_exec}"
    DB_AUTO_CACHE_RELOAD_STARTED_LOG_MSG = "Auto reload started; next at {next_exec}"
    DB_AUTO_CACHE_RELOAD_STOPPED_LOG_MSG = "Auto reload stopped by admin."
    
    # Database cache messages (console output)
    DB_FIREBASE_CACHE_LOADED_MSG = "✅ Firebase cache loaded: {count} root nodes"
    DB_FIREBASE_CACHE_NOT_FOUND_MSG = "⚠️ Firebase cache file not found, starting with empty cache: {cache_file}"
    DB_FAILED_LOAD_FIREBASE_CACHE_MSG = "❌ Failed to load firebase cache: {error}"
    DB_FIREBASE_CACHE_RELOADED_MSG = "✅ Firebase cache reloaded: {count} root nodes"
    DB_FIREBASE_CACHE_FILE_NOT_FOUND_MSG = "⚠️ Firebase cache file not found: {cache_file}"
    DB_FAILED_RELOAD_FIREBASE_CACHE_MSG = "❌ Failed to reload firebase cache: {error}"
    
    # Database user ban messages
    DB_USER_BANNED_MSG = "🚫 You are banned from the bot!"
    
    # Always Ask Menu messages
    AA_NO_VIDEO_FORMATS_FOUND_MSG = "❔ नहीं वीडियो formats found. Trying छवि downloader…"
    AA_FLOOD_WAIT_MSG = "⚠️ Telegram has limited message sending.\n⏳ Please wait: {time_str}\nTo update timer send URL again 2 times."
    AA_VLC_IOS_MSG = "🎬 <b><a href=\"https://itunes.apple.com/app/apple-store/id650377962\">VLC Player (iOS)</a></b>\n\n<i>Click button to copy stream URL, then paste it in VLC app</i>"
    AA_VLC_ANDROID_MSG = "🎬 <b><a href=\"https://play.google.com/store/apps/details?id=org.videolan.vlc\">VLC Player (Android)</a></b>\n\n<i>Click button to copy stream URL, then paste it in VLC app</i>"
    AA_ERROR_GETTING_LINK_MSG = "❌ <b>Error getting link:</b>\n{error_msg}"
    AA_ERROR_SENDING_FORMATS_MSG = "❌ Error sending formats file: {error}"
    AA_FAILED_GET_FORMATS_MSG = "❌ Failed to get formats:\n<code>{output}</code>"
    AA_PROCESSING_WAIT_MSG = "🔄 प्रसंस्करण हो रहा है... (wait 6 sec)"
    AA_PROCESSING_MSG = "🔄 प्रसंस्करण हो रहा है..."
    AA_TAG_FORBIDDEN_CHARS_MSG = "❌ Tag #{wrong} contains forbidden characters. Only letters, digits and _ are allowed.\nPlease use: {example}"
    
    # Helper limitter messages
    HELPER_ADMIN_RIGHTS_REQUIRED_MSG = "❗️ Для работы в группе боту нужны права администратора. Пожалуйста, сделайте бота админом этой группы."
    
    # URL extractor messages
    URL_EXTRACTOR_AUDIO_HINT_MSG = "Download only audio from video source.\n\nUsage: /audio + URL \n\n(ex. /audio https://youtu.be/abc123)\n(ex. /audio https://youtu.be/playlist?list=abc123*1*10)"
    URL_EXTRACTOR_WELCOME_MSG = "Hello {first_name},\n \n<i>This bot🤖 can download any videos into telegram directly.😊 For more information press <b>/help</b></i> 👈\n \n {credits}"
    URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG = "🗑 नहीं files को हटाएं."
    URL_EXTRACTOR_ALL_FILES_REMOVED_MSG = "🗑 All files removed successfully!\n\nRemoved files:\n{files_list}"
    URL_EXTRACTOR_ALL_MEDIA_FILES_REMOVED_MSG = "🗑 सभी मीडिया files are removed."
    
    # Video extractor messages
    VIDEO_EXTRACTOR_WAIT_DOWNLOAD_MSG = "⏰ WAIT तक YOUR पिछला डाउनलोड IS FINISHED"
    
    # Helper messages
    HELPER_APP_INSTANCE_NONE_MSG = "App instance is कोई नहीं में check_user"
    HELPER_CHECK_FILE_SIZE_LIMIT_INFO_DICT_NONE_MSG = "check_file_size_limit: info_dict is कोई नहीं, allowing डाउनलोड"
    HELPER_CHECK_SUBS_LIMITS_INFO_DICT_NONE_MSG = "check_subs_limits: info_dict is कोई नहीं, allowing subtitle embedding"
    HELPER_CHECK_SUBS_LIMITS_CHECKING_LIMITS_MSG = "check_subs_limits: checking limits - max_quality={max_quality}p, max_duration={max_duration}s, max_size={max_size}MB"
    HELPER_CHECK_SUBS_LIMITS_INFO_DICT_KEYS_MSG = "check_subs_limits: info_dict keys: {keys}"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_DURATION_MSG = "Subtitle embedding skipped: duration {duration}s exceeds limit {max_duration}s"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_SIZE_MSG = "Subtitle embedding skipped: size {size_mb:.2f}MB exceeds limit {max_size}MB"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_QUALITY_MSG = "Subtitle embedding skipped: quality {width}x{height} (min side {min_side}p) exceeds limit {max_quality}p"
    HELPER_COMMAND_TYPE_TIKTOK_MSG = "टिकटॉक"
    HELPER_COMMAND_TYPE_INSTAGRAM_MSG = "इंस्टाग्राम"
    HELPER_COMMAND_TYPE_PLAYLIST_MSG = "प्लेलिस्ट"
    HELPER_RANGE_LIMIT_EXCEEDED_MSG = "❗️ Range limit exceeded for {service}: {count} (maximum {max_count}).\n\nUse one of these commands to download maximum available files:\n\n<code>{suggested_command_url_format}</code>\n\n"
    HELPER_RANGE_LIMIT_EXCEEDED_LOG_MSG = "❗️ Range limit exceeded for {service}: {count} (maximum {max_count})\nUser ID: {user_id}"
    
    # Handler registry messages
    
    # Download status messages
    
    # POT helper messages
    HELPER_POT_PROVIDER_DISABLED_MSG = "PO token provider अक्षम में config"
    HELPER_POT_URL_NOT_YOUTUBE_MSG = "URL {url} is not a YouTube domain, skipping PO token"
    HELPER_POT_PROVIDER_NOT_AVAILABLE_MSG = "PO token provider is not available at {base_url}, falling back to standard YouTube extraction"
    HELPER_POT_PROVIDER_CACHE_CLEARED_MSG = "PO token provider cache cleared, will जांच availability पर अगला request"
    HELPER_POT_GENERIC_ARGS_MSG = "generic:impersonate=chrome,youtubetab:skip=authcheck"
    
    # Safe messenger messages
    HELPER_APP_INSTANCE_NOT_AVAILABLE_MSG = "App instance not उपलब्ध अभी तक"
    HELPER_USER_NAME_MSG = "उपयोगकर्ता"
    HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG = "Flood wait detected, sleeping for {wait_seconds} seconds"
    HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG = "Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds"
    HELPER_MSG_SEQNO_ERROR_DETECTED_MSG = "msg_seqno error detected, sleeping for {retry_delay} seconds"
    HELPER_MESSAGE_ID_INVALID_MSG = "MESSAGE_ID_INVALID"
    HELPER_MESSAGE_DELETE_FORBIDDEN_MSG = "MESSAGE_DELETE_FORBIDDEN"
    
    # Proxy helper messages
    HELPER_PROXY_CONFIG_INCOMPLETE_MSG = "Proxy कॉन्फ़िगरेशन अपूर्ण, using direct कनेक्शन"
    HELPER_PROXY_COOKIE_PATH_MSG = "users/{user_id}/cookie.txt"
    
    # URL extractor messages
    URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG = "🔚पास"
    URL_EXTRACTOR_ADD_GROUP_CLOSE_BUTTON_MSG = "🔚पास"
    URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG = "youtube"
    URL_EXTRACTOR_COOKIE_ARGS_TIKTOK_MSG = "tiktok"
    URL_EXTRACTOR_COOKIE_ARGS_INSTAGRAM_MSG = "instagram"
    URL_EXTRACTOR_COOKIE_ARGS_TWITTER_MSG = "twitter"
    URL_EXTRACTOR_COOKIE_ARGS_CUSTOM_MSG = "कस्टम"
    URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG = "🔚पास"
    URL_EXTRACTOR_CLEAN_LOGS_FILE_REMOVED_MSG = "🗑 लॉग्स फ़ाइल removed."
    URL_EXTRACTOR_CLEAN_TAGS_FILE_REMOVED_MSG = "🗑 Tags फ़ाइल removed."
    URL_EXTRACTOR_CLEAN_FORMAT_FILE_REMOVED_MSG = "🗑 प्रारूप फ़ाइल removed."
    URL_EXTRACTOR_CLEAN_SPLIT_FILE_REMOVED_MSG = "🗑 Split फ़ाइल removed."
    URL_EXTRACTOR_CLEAN_MEDIAINFO_FILE_REMOVED_MSG = "🗑 Mediainfo फ़ाइल removed."
    URL_EXTRACTOR_CLEAN_SUBS_SETTINGS_REMOVED_MSG = "🗑 Subtitle सेटिंग्स removed."
    URL_EXTRACTOR_CLEAN_KEYBOARD_SETTINGS_REMOVED_MSG = "🗑 Keyboard सेटिंग्स removed."
    URL_EXTRACTOR_CLEAN_ARGS_SETTINGS_REMOVED_MSG = "🗑 Args सेटिंग्स removed."
    URL_EXTRACTOR_CLEAN_NSFW_SETTINGS_REMOVED_MSG = "🗑 NSFW सेटिंग्स removed."
    URL_EXTRACTOR_CLEAN_PROXY_SETTINGS_REMOVED_MSG = "🗑 Proxy सेटिंग्स removed."
    URL_EXTRACTOR_CLEAN_FLOOD_WAIT_SETTINGS_REMOVED_MSG = "🗑 Flood wait सेटिंग्स removed."
    URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG = "🔚पास"
    URL_EXTRACTOR_VID_HELP_TITLE_MSG = "🎬 वीडियो डाउनलोड Command"
    URL_EXTRACTOR_VID_HELP_USAGE_MSG = "Usage: <code>/vid URL</code>"
    URL_EXTRACTOR_VID_HELP_EXAMPLES_MSG = "Examples:"
    URL_EXTRACTOR_VID_HELP_EXAMPLE_1_MSG = "• <code>/vid 3-7 https://youtube.com/playlist?list=123abc</code>"
    URL_EXTRACTOR_VID_HELP_ALSO_SEE_MSG = "Also see: /ऑडियो, /img, /सहायता, /playlist, /सेटिंग्स"
    URL_EXTRACTOR_ADD_GROUP_USER_CLOSED_MSG = "User {user_id} closed add_bot_to_group command"

    # YouTube messages
    YOUTUBE_FAILED_EXTRACT_ID_MSG = "असफल को extract YouTube ID"
    YOUTUBE_FAILED_DOWNLOAD_THUMBNAIL_MSG = "असफल को डाउनलोड thumbnail or it is too big"
        
    # Thumbnail downloader messages
    
    # Commands messages   
    
    # Always Ask menu callback messages
    AA_CHOOSE_AUDIO_LANGUAGE_MSG = "चुनें ऑडियो language"
    AA_NO_SUBTITLES_DETECTED_MSG = "नहीं subtitles detected"
    AA_CHOOSE_SUBTITLE_LANGUAGE_MSG = "चुनें subtitle language"
    
    # Gallery-dl error type messages
    GALLERY_DL_AUTH_ERROR_MSG = "Authentication त्रुटि"
    GALLERY_DL_ACCOUNT_NOT_FOUND_MSG = "Account Not Found"
    GALLERY_DL_ACCOUNT_UNAVAILABLE_MSG = "Account अनुपलब्ध"
    GALLERY_DL_RATE_LIMIT_EXCEEDED_MSG = "दर सीमा Exceeded"
    GALLERY_DL_NETWORK_ERROR_MSG = "नेटवर्क त्रुटि"
    GALLERY_DL_CONTENT_UNAVAILABLE_MSG = "सामग्री अनुपलब्ध"
    GALLERY_DL_GEOGRAPHIC_RESTRICTIONS_MSG = "भौगोलिक प्रतिबंध"
    GALLERY_DL_VERIFICATION_REQUIRED_MSG = "सत्यापन आवश्यक"
    GALLERY_DL_POLICY_VIOLATION_MSG = "नीति उल्लंघन"
    GALLERY_DL_UNKNOWN_ERROR_MSG = "Unknown त्रुटि"
    
    # Download started message (used in both audio and video downloads)
    DOWNLOAD_STARTED_MSG = "<b>▶️ Download started</b>"
    
    # Split command constants
    SPLIT_CLOSE_BUTTON_MSG = "🔚पास"
    
    # Always ask menu constants
    
    # Search command constants
    
    # List command constants
    
    # Magic.py messages
    MAGIC_VID_HELP_TITLE_MSG = "<b>🎬 Video Download Command</b>\n\n"
    MAGIC_VID_HELP_USAGE_MSG = "Usage: <code>/vid URL</code>\n\n"
    MAGIC_VID_HELP_EXAMPLES_MSG = "<b>Examples:</b>\n"
    MAGIC_VID_HELP_EXAMPLE_1_MSG = "• <code>/vid https://youtube.com/watch?v=123abc</code>\n"
    MAGIC_VID_HELP_EXAMPLE_2_MSG = "• <code>/vid https://youtube.com/playlist?list=123abc*1*5</code>\n"
    MAGIC_VID_HELP_EXAMPLE_3_MSG = "• <code>/vid 3-7 https://youtube.com/playlist?list=123abc</code>\n\n"
    MAGIC_VID_HELP_ALSO_SEE_MSG = "Also see: /audio, /img, /help, /playlist, /settings"
    
    # Flood limit messages
    FLOOD_LIMIT_TRY_LATER_FALLBACK_MSG = "⏳ Flood सीमा. Try बाद में."
    
    # Cookie command usage messages
    COOKIE_COMMAND_USAGE_MSG = """<b>🍪 Cookie Command Usage</b>

<code>/cookie</code> - Show cookie menu
<code>/cookie youtube</code> - Download YouTube cookies
<code>/cookie instagram</code> - Download Instagram cookies
<code>/cookie tiktok</code> - Download TikTok cookies
<code>/cookie x</code> or <code>/cookie twitter</code> - Download Twitter/X cookies
<code>/cookie facebook</code> - Download Facebook cookies
<code>/cookie custom</code> - Show custom cookie instructions

<i>Available services depend on bot configuration.</i>"""
    
    # Cookie cache messages
    COOKIE_FILE_REMOVED_CACHE_CLEARED_MSG = "🗑 Cookie फ़ाइल removed and cache cleared."
    
    # Subtitles Command Messages
    SUBS_PREV_BUTTON_MSG = "⬅️ Prev"
    SUBS_BACK_BUTTON_MSG = "🔙वापस"
    SUBS_OFF_BUTTON_MSG = "🚫 बंद"
    SUBS_SET_LANGUAGE_MSG = "• <code>/subs ru</code> - set language"
    SUBS_SET_LANGUAGE_AUTO_MSG = "• <code>/subs ru auto</code> - set language with AUTO/TRANS"
    SUBS_VALID_OPTIONS_MSG = "मान्य विकल्प:"
    
    # Settings Command Messages
    SETTINGS_DEV_GITHUB_BUTTON_MSG = "🛠 Dev GitHub"
    SETTINGS_CONTR_GITHUB_BUTTON_MSG = "🛠 Contr GitHub"
    SETTINGS_CLEAN_BUTTON_MSG = "🧹 CLEAN"
    SETTINGS_COOKIES_BUTTON_MSG = "🍪 COOKIES"
    SETTINGS_MEDIA_BUTTON_MSG = "🎞 मीडिया"
    SETTINGS_INFO_BUTTON_MSG = "📖 INFO"
    SETTINGS_MORE_BUTTON_MSG = "⚙️ अधिक"
    SETTINGS_COOKIES_ONLY_BUTTON_MSG = "🍪 Cookies केवल"
    SETTINGS_LOGS_BUTTON_MSG = "📃 लॉग्स "
    SETTINGS_TAGS_BUTTON_MSG = "#️⃣ Tags"
    SETTINGS_FORMAT_BUTTON_MSG = "📼 प्रारूप"
    SETTINGS_SPLIT_BUTTON_MSG = "✂️ Split"
    SETTINGS_MEDIAINFO_BUTTON_MSG = "📊 Mediainfo"
    SETTINGS_SUBTITLES_BUTTON_MSG = "💬 Subtitles"
    SETTINGS_KEYBOARD_BUTTON_MSG = "🎹 Keyboard"
    SETTINGS_ARGS_BUTTON_MSG = "⚙️ Args"
    SETTINGS_NSFW_BUTTON_MSG = "🔞 NSFW"
    SETTINGS_PROXY_BUTTON_MSG = "🌎 Proxy"
    SETTINGS_FLOOD_WAIT_BUTTON_MSG = "🔄 Flood wait"
    SETTINGS_ALL_FILES_BUTTON_MSG = "🗑  सभी files"
    SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG = "📥 /cookie - डाउनलोड my 5 cookies"
    SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG = "🌐 /cookies_from_browser - Get ब्राउज़र's YT-cookie"
    SETTINGS_CHECK_COOKIE_BUTTON_MSG = "🔎 /check_cookie - मान्य करें your cookie फ़ाइल"
    SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG = "🔖 /save_as_cookie - अपलोड कस्टम cookie"
    SETTINGS_FORMAT_CMD_BUTTON_MSG = "📼 /प्रारूप - Change गुणवत्ता & प्रारूप"
    SETTINGS_MEDIAINFO_CMD_BUTTON_MSG = "📊 /mediainfo - Turn पर / बंद MediaInfo"
    SETTINGS_SPLIT_CMD_BUTTON_MSG = "✂️ /split - Change split वीडियो भाग आकार"
    SETTINGS_AUDIO_CMD_BUTTON_MSG = "🎧 /ऑडियो - डाउनलोड वीडियो as ऑडियो"
    SETTINGS_SUBS_CMD_BUTTON_MSG = "💬 /subs - Subtitles language सेटिंग्स"
    SETTINGS_PLAYLIST_CMD_BUTTON_MSG = "⏯️ /playlist - How को डाउनलोड playlists"
    SETTINGS_IMG_CMD_BUTTON_MSG = "🖼 /img - डाउनलोड images via gallery-dl"
    SETTINGS_TAGS_CMD_BUTTON_MSG = "#️⃣ /tags - भेजें your #tags"
    SETTINGS_HELP_CMD_BUTTON_MSG = "🆘 /सहायता - Get निर्देश"
    SETTINGS_USAGE_CMD_BUTTON_MSG = "📃 /usage -भेजें your लॉग्स"
    SETTINGS_PLAYLIST_HELP_CMD_BUTTON_MSG = "⏯️ /playlist - Playlist's सहायता"
    SETTINGS_ADD_BOT_CMD_BUTTON_MSG = "🤖 /add_bot_to_group - howto"
    SETTINGS_LINK_CMD_BUTTON_MSG = "🔗 /लिंक - Get direct वीडियो links"
    SETTINGS_PROXY_CMD_BUTTON_MSG = "🌍 /proxy - सक्षम करें/अक्षम करें proxy"
    SETTINGS_KEYBOARD_CMD_BUTTON_MSG = "🎹 /keyboard - Keyboard layout"
    SETTINGS_SEARCH_CMD_BUTTON_MSG = "🔍 /खोजें - Inline खोजें helper"
    SETTINGS_ARGS_CMD_BUTTON_MSG = "⚙️ /args - yt-dlp arguments"
    SETTINGS_NSFW_CMD_BUTTON_MSG = "🔞 /nsfw - NSFW blur सेटिंग्स"
    SETTINGS_CLEAN_OPTIONS_MSG = "<b>🧹 Clean Options</b>\n\nChoose what to clean:"
    SETTINGS_MOBILE_ACTIVATE_SEARCH_MSG = "📱 Mobile: Activate @vid search"
    
    # Search Command Messages
    SEARCH_MOBILE_ACTIVATE_SEARCH_MSG = "📱 Mobile: Activate @vid search"
    
    # Keyboard Command Messages
    KEYBOARD_OFF_BUTTON_MSG = "🔴 बंद"
    KEYBOARD_FULL_BUTTON_MSG = "🔣 भरा हुआ"
    KEYBOARD_1X3_BUTTON_MSG = "📱 1x3"
    KEYBOARD_2X3_BUTTON_MSG = "📱 2x3"
    
    # Image Command Messages
    IMAGE_URL_CAPTION_MSG = "🔗[Images URL]({url}) @{Config.BOT_NAME}"
    IMAGE_ERROR_MSG = "❌ Error: {str(e)}"
    
    # Format Command Messages
    FORMAT_BACK_BUTTON_MSG = "🔙वापस"
    FORMAT_CUSTOM_FORMAT_MSG = "• <code>/format &lt;format_string&gt;</code> - custom format"
    FORMAT_720P_MSG = "• <code>/format 720</code> - 720p quality"
    FORMAT_4K_MSG = "• <code>/format 4k</code> - 4K quality"
    FORMAT_8K_MSG = "• <code>/format 8k</code> - 8K quality"
    FORMAT_ID_MSG = "• <code>/format id 401</code> - specific format ID"
    FORMAT_ASK_MSG = "• <code>/format ask</code> - always show menu"
    FORMAT_BEST_MSG = "• <code>/format best</code> - bv+ba/best quality"
    FORMAT_ALWAYS_ASK_BUTTON_MSG = "❓ Always Ask (मेनू + buttons)"
    FORMAT_OTHERS_BUTTON_MSG = "🎛 Others (144p - 4320p)"
    FORMAT_4K_PC_BUTTON_MSG = "💻4k (सबसे अच्छा for PC/Mac Telegram)"
    FORMAT_FULLHD_MOBILE_BUTTON_MSG = "📱FullHD (सबसे अच्छा for मोबाइल Telegram)"
    FORMAT_BESTVIDEO_BUTTON_MSG = "📈Bestvideo+Bestaudio (MAX गुणवत्ता)"
    FORMAT_CUSTOM_BUTTON_MSG = "🎚 कस्टम (enter your own)"
    
    # Cookies Command Messages
    COOKIES_YOUTUBE_BUTTON_MSG = "📺 YouTube (1-{max(1, len(get_youtube_cookie_urls()))})"
    COOKIES_FROM_BROWSER_BUTTON_MSG = "🌐 से ब्राउज़र"
    COOKIES_TWITTER_BUTTON_MSG = "🐦 Twitter/X"
    COOKIES_TIKTOK_BUTTON_MSG = "🎵 TikTok"
    COOKIES_VK_BUTTON_MSG = "📘 Vkontakte"
    COOKIES_INSTAGRAM_BUTTON_MSG = "📷 Instagram"
    COOKIES_YOUR_OWN_BUTTON_MSG = "📝 Your Own"
    
    # Args Command Messages
    ARGS_INPUT_TIMEOUT_MSG = "⏰ Input बहुलक automatically बंद देय को inactivity (5 minutes)."
    ARGS_RESET_ALL_BUTTON_MSG = "🔄 रीसेट सभी"
    ARGS_VIEW_CURRENT_BUTTON_MSG = "📋 दृश्य वर्तमान"
    ARGS_BACK_BUTTON_MSG = "🔙 वापस"
    ARGS_FORWARD_TEMPLATE_MSG = "\n---\n\n<i>Forward this message to your favorites to save these settings as a template.</i> \n\n<i>Forward this message back here to apply these settings.</i>"
    ARGS_NO_SETTINGS_MSG = "📋 Current yt-dlp Arguments:\n\nNo custom settings configured.\n\n---\n\n<i>Forward this message to your favorites to save these settings as a template.</i> \n\n<i>Forward this message back here to apply these settings.</i>"
    ARGS_CURRENT_ARGUMENTS_MSG = "📋 वर्तमान yt-dlp Arguments:\n\n"
    ARGS_EXPORT_SETTINGS_BUTTON_MSG = "📤 Export सेटिंग्स"
    ARGS_SETTINGS_READY_MSG = "सेटिंग्स तैयार for export! Forward this संदेश को favorites को सहेजें."
    ARGS_CURRENT_VALUE_MSG = "Current value: <code>{value}</code>"
    ARGS_CURRENT_ARGUMENTS_HEADER_MSG = "📋 वर्तमान yt-dlp Arguments:"
    ARGS_FAILED_RECOGNIZE_MSG = "❌ असफल को recognize सेटिंग्स में संदेश. Make sure you sent a सही सेटिंग्स template."
    ARGS_SUCCESSFULLY_IMPORTED_MSG = "✅ Settings successfully imported!\n\nApplied parameters: {applied_count}\n\n"
    ARGS_KEY_SETTINGS_MSG = "Key सेटिंग्स:\n"
    ARGS_ERROR_SAVING_MSG = "❌ त्रुटि saving imported सेटिंग्स."
    ARGS_ERROR_IMPORTING_MSG = "❌ An त्रुटि occurred जबकि importing सेटिंग्स."

    #######################################################
