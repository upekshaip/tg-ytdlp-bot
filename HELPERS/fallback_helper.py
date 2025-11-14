#!/usr/bin/env python3
"""
Helper functions for fallback mechanisms
"""

def should_fallback_to_gallery_dl(error_message: str, url: str) -> bool:
    """
    Определяет, нужно ли переключаться на gallery-dl при ошибке yt-dlp.
    Возвращает True если ошибка указывает на то, что yt-dlp не может обработать URL.
    """
    # Проверяем, не является ли URL доменом только для yt-dlp
    from CONFIG.domains import DomainsConfig
    from urllib.parse import urlparse
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Убираем www. префикс для сравнения
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Проверяем, не входит ли домен в YTDLP_ONLY_DOMAINS
        for ytdlp_domain in DomainsConfig.YTDLP_ONLY_DOMAINS:
            if domain == ytdlp_domain or domain.endswith('.' + ytdlp_domain):
                return False  # Не переключаемся на gallery-dl для yt-dlp только доменов
    except Exception:
        # Если не удалось распарсить URL, продолжаем обычную проверку
        pass
    
    error_lower = error_message.lower()
    
    # Ошибки, которые указывают на то, что yt-dlp не может обработать контент
    fallback_indicators = [
        # Ошибки доступа и авторизации
        "http error 429: too many requests",
        "http error 403: forbidden", 
        "http error 401: unauthorized",
        "unable to download webpage",
        "too many requests",
        "rate limit exceeded",
        "quota exceeded",
        
        # Ошибки формата контента
        "no videos found in playlist",
        "unsupported url",
        "no video could be found", 
        "no video found",
        "no media found",
        "this tweet does not contain",
        "no video formats found",
        "no video available",
        
        # Ошибки извлечения
        "unable to extract",
        "extraction failed",
        "no suitable formats",
        "requested format is not available",
        
        # Ошибки платформ
        "instagram:user",
        "twitter:user", 
        "tiktok:user",
        "facebook:user",
        "pinterest:user",
        "tumblr:user",
        "flickr:user",
        "deviantart:user",
        "artstation:user",
        "onlyfans:user",
        "patreon:user",
        "fanbox:user",
        "fantia:user",
        
        # Ошибки сети
        "connection refused",
        "connection timeout", 
        "network unreachable",
        "dns resolution failed",
        
        # Ошибки блокировки
        "blocked by robots.txt",
        "geoblocked",
        "region blocked",
        "country blocked",
        "ip blocked",
        "user agent blocked",
        "captcha required",
        "verification required",
        "age verification required",
        "nsfw verification required",
        
        # Ошибки контента
        "content not available",
        "post deleted",
        "account deleted", 
        "account terminated",
        "account suspended",
        "account banned",
        "account private",
        "profile private",
        "terms of service violation",
        "copyright violation",
        "dmca takedown",
        "content removed"
    ]
    
    # Проверяем наличие индикаторов fallback
    for indicator in fallback_indicators:
        if indicator in error_lower:
            return True
    
    # Дополнительная проверка для Instagram ошибок
    if "instagram" in error_lower and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
    
    # Дополнительная проверка для Twitter/X ошибок  
    if any(domain in url.lower() for domain in ["twitter.com", "x.com"]) and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
        
    # Дополнительная проверка для TikTok ошибок
    if "tiktok.com" in url.lower() and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
    
    return False
