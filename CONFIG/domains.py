from CONFIG.messages import Messages
# Domains Configuration

class DomainsConfig(object):
    #######################################################
    # Restricted content site lists
    #######################################################
    BLACK_LIST = []
    #BLACK_LIST = ["pornhub", "phncdn.com", "xvideos", "xhcdn.com", "xhamster"]
    # Paths to domain and keyword lists
    PORN_DOMAINS_FILE = "TXT/porn_domains.txt"
    PORN_KEYWORDS_FILE = "TXT/porn_keywords.txt"
    SUPPORTED_SITES_FILE = "TXT/supported_sites.txt"
    #CLEAN_QUERY = "normalized_sites.txt"
    
    # Script for updating porn lists
    UPDATE_PORN_SCRIPT_PATH = "./script.sh"
    
    # --- Whitelist of keywords that are not considered porn ---
    WHITE_KEYWORDS = [
        'a55',
        'Hassas',
        'assasinate', 'assasinated', 'assassinate', 'assassinated', 'assassination'
    ]
    YTDLP_ONLY_DOMAINS = [
        # Video platforms that should only use yt-dlp (no gallery-dl fallback)
        'youtube.com', 'youtu.be', 'm.youtube.com', 'www.youtube.com',
        'music.youtube.com', 'gaming.youtube.com'
    ]
    GALLERYDL_ONLY_DOMAINS = [
        # Imageboards / archives / art communities largely covered by gallery-dl
        '2ch.su', '35photo.pro', 'behoimi.org', '4archive.org', '8chan.moe',
        'comics.8muses.com', 'agn.ph', 'arca.live', 'architizer.com', 'aryion.com',
        'catbox.moe', 'civitai.com', 'danke-fuers-lesen.de', 'desktopography.net',
        'e-hentai.org', 'exhentai.org', 'everia.club', 'fapello.com', 'furry34.com',
        'gelbooru.com', 'girlswithmuscle.com', 'itaku.ee', 'kemono.cr', 'kemono.party',
        'coomer.party', 'leakgallery.com', 'myportfolio.com', 'nekohouse.su',
        'nhentai.net', 'photovogue.com', 'pixeltabel.com', 'weasyl.com', 'wikifeet.com',
        'xasiat.com', 'wallhaven.cc'
    ]

    GALLERYDL_ONLY_PATH = [
        # Imageboards / archives / art communities largely covered by gallery-dl
        'vk.com/wall-',
        'vk.com/album-',
    ]

    GALLERYDL_FALLBACK_DOMAINS = [
        # Social media platforms largely covered by gallery-dl
        'instagram.com',
    ]

    # --- Whitelist of domains that are not considered porn ---
    WHITELIST = [
        'www.linkedin.com',
        'linkedin.com',
        'boozallen.com',
        'www.boozallen.com',
        'm.ok.ru',
        'ok.ru',
        'shazam.com',
        'rutube.ru',
        'soundcloud.com',
        'a-tushar-82q-fef07c6bf20a.herokuapp.com', 'file-to-link-632f24ac9728.herokuapp.com',
        'bilibili.com', 'dailymotion.com', 'sky.com', 'xbox.com', 'youtube.com', 'youtu.be', '1tv.ru', 'x.ai',
        'twitch.tv', 'vimeo.com', 'facebook.com', 'tiktok.com', 'instagram.com', 'fb.com', 'ig.me',
        'ahm7tech.vercel.app', 'vz-db5b8c20-711.b-cdn.net', 'b-cdn.net'
        # Other secure domains can be added
    ]


    # --- Greylist of domains excluded only from domain list check but still checked for keywords ---
    GREYLIST = [
        'snapchat.com',
        'reddit.com',
        'vkvideo.ru', 'vkontakte.ru', 'vk.com',
        'twitter.com', 'x.com', 't.co'
        #'twimg.com', 'video.twimg.com'
        # Add domains here that should be excluded from porn_domains.txt check
        # but still checked against porn_keywords.txt
    ]

    NO_COOKIE_DOMAINS = [
        'dailymotion.com'
        # Other secure domains can be added
    ]
    PROXY_DOMAINS = [
        #'pornhub.com', 'pornhub.org'
        # Other secure domains can be added
    ]
    PROXY_2_DOMAINS = [
        #'instagram.com', 'ig.me'
        # Other secure domains can be added
    ]

    # Domains that don't work well with match_filter (messages.STREAM_messages.STREAM_DURATION_MSG.format(duration=duration)_MSG.format(messages.STREAM_DURATION_MSG.format(duration=duration)=messages.STREAM_DURATION_MSG.format(duration=duration))/live detection issues)
    NO_FILTER_DOMAINS = [
        'bashlinker.alenwalak.workers.dev',
        'cdn.indexer.eu.org',
        'a-tushar-82q-fef07c6bf20a.herokuapp.com',
        'file-to-link-632f24ac9728.herokuapp.com'
        # Add other domains that have issues with messages.STREAM_messages.STREAM_DURATION_MSG.format(duration=duration)_MSG.format(messages.STREAM_DURATION_MSG.format(duration=duration)=messages.STREAM_DURATION_MSG.format(duration=duration))/live detection
    ]

    # TikTok Domain List
    TIKTOK_DOMAINS = [
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com',
        'www.tiktok.com', 'm.tiktok.com', 'tiktokv.com',
        'www.tiktokv.com', 'tiktok.ru', 'www.tiktok.ru'
    ]
    # Added CLEAN_QUERY array for domains where query and fragment can be safely cleared
    CLEAN_QUERY = [
        #'vk.com', 'vkvideo.ru', 'vkontakte.ru',
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

    # Piped frontend domain for opening YouTube links as a WebApp
    PIPED_DOMAIN = "poketube.fun"
    #######################################################
