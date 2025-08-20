from HELPERS.logger import logger

def is_instagram_url(url: str) -> bool:
    """Check if URL is from Instagram"""
    return any(domain in url.lower() for domain in ['instagram.com', 'www.instagram.com'])


def is_twitter_url(url: str) -> bool:
    """Check if URL is from Twitter/X"""
    return any(domain in url.lower() for domain in ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'])


def is_reddit_url(url: str) -> bool:
    """Check if URL is from Reddit"""
    return any(domain in url.lower() for domain in ['reddit.com', 'www.reddit.com'])


def transform_to_embed_url(url: str) -> str:
    """Transform URL to embeddable format"""
    if is_instagram_url(url):
        # Replace instagram.com with ddinstagram.com
        return url.replace('instagram.com', 'instagramez.com').replace('www.instagramez.com', 'instagramez.com')
    elif is_twitter_url(url):
        # Replace twitter.com/x.com with fxtwitter.com
        return url.replace('twitter.com', 'fxtwitter.com').replace('x.com', 'fxtwitter.com').replace('www.fxtwitter.com', 'fxtwitter.com')
    elif is_reddit_url(url):
        # Replace reddit.com with rxddit.com
        return url.replace('reddit.com', 'rxddit.com').replace('www.rxddit.com', 'rxddit.com')
    return url

