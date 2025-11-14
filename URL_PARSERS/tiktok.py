import re
from urllib.parse import urlparse
from CONFIG.config import Config
from HELPERS.logger import logger

def get_clean_url_for_tagging(url: str) -> str:
    """
    Extracts the last (deepest nested) link from URL-wrappers.
    Used ONLY for generating tags.
    """
    if not isinstance(url, str):
        return ''
    last_http_pos = url.rfind('http://')
    last_https_pos = url.rfind('https://')

    start_of_real_url_pos = max(last_http_pos, last_https_pos)

    # If another http/https is found (not at the very beginning), this is the real link
    if start_of_real_url_pos and start_of_real_url_pos > 0:
        return url[start_of_real_url_pos:]
    return url

def is_tiktok_url(url: str) -> bool:
    """
    Checks if URL is a TikTok link
    """
    try:
        clean_url = get_clean_url_for_tagging(url)
        parsed_url = urlparse(clean_url)
        return any(domain in parsed_url.netloc for domain in Config.TIKTOK_DOMAINS)
    except:
        return False


# --- Extracting TikTok profile name from URL ---
def extract_tiktok_profile(url: str) -> str:
    # Looking for @username after the domain
    clean_url = get_clean_url_for_tagging(url)
    m = re.search(r'/@([\w\.\-_]+)', clean_url)
    if m:
        return m.group(1)
    return ''
