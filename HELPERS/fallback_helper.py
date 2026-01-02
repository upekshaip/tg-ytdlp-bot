#!/usr/bin/env python3
"""
Helper functions for fallback mechanisms
"""

def should_fallback_to_gallery_dl(error_message: str, url: str) -> bool:
    """
    Decide whether to fall back to gallery-dl after a yt-dlp error.
    Returns True if the error indicates yt-dlp cannot handle the URL/content.
    """
    # Check whether the URL belongs to a yt-dlp-only domain
    from CONFIG.domains import DomainsConfig
    from urllib.parse import urlparse
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Strip "www." prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Check if the domain is in YTDLP_ONLY_DOMAINS
        for ytdlp_domain in DomainsConfig.YTDLP_ONLY_DOMAINS:
            if domain == ytdlp_domain or domain.endswith('.' + ytdlp_domain):
                return False  # Do not fall back for yt-dlp-only domains
    except Exception:
        # If URL parsing fails, continue with the normal checks
        pass
    
    error_lower = error_message.lower()
    
    # Errors indicating yt-dlp cannot handle the content
    fallback_indicators = [
        # Access/auth errors
        "http error 429: too many requests",
        "http error 403: forbidden", 
        "http error 401: unauthorized",
        "unable to download webpage",
        "too many requests",
        "rate limit exceeded",
        "quota exceeded",
        
        # Content/format errors
        "no videos found in playlist",
        "unsupported url",
        "no video could be found", 
        "no video found",
        "no media found",
        "this tweet does not contain",
        "no video formats found",
        "no video available",
        
        # Extraction errors
        "unable to extract",
        "extraction failed",
        "no suitable formats",
        "requested format is not available",
        
        # Platform errors
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
        
        # Network errors
        "connection refused",
        "connection timeout", 
        "network unreachable",
        "dns resolution failed",
        
        # Blocking/restriction errors
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
        
        # Content availability errors
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
    
    # Check for fallback indicators
    for indicator in fallback_indicators:
        if indicator in error_lower:
            return True
    
    # Additional checks for Instagram errors
    if "instagram" in error_lower and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
    
    # Additional checks for Twitter/X errors
    if any(domain in url.lower() for domain in ["twitter.com", "x.com"]) and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
        
    # Additional checks for TikTok errors
    if "tiktok.com" in url.lower() and any(err in error_lower for err in ["429", "403", "401", "unable to download"]):
        return True
    
    return False
