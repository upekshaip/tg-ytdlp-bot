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
    
    # --- Whitelist of domains that are not considered porn ---
    WHITELIST = [
        'dailymotion.com', 'sky.com', 'xbox.com', 'youtube.com', 'youtu.be', '1tv.ru', 'x.ai',
        'twitch.tv', 'vimeo.com', 'facebook.com', 'tiktok.com', 'instagram.com', 'fb.com', 'ig.me'
        # Other secure domains can be added
    ]
    NO_COOKIE_DOMAINS = [
        'dailymotion.com'
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
        'vk.com', 'vkvideo.ru', 'vkontakte.ru',
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
    #######################################################