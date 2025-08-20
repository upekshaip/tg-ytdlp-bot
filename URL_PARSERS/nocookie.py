from urllib.parse import urlparse
from CONFIG.config import Config
from HELPERS.logger import logger

def is_no_cookie_domain(url: str) -> bool:
    """
    Checks whether the domain is from the list no_cookie_domains.
    For such domains, you need to use —no-Cookies instead of-Cookies.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # We remove www. If there is
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Check the domain and its subdomain
        for no_cookie_domain in Config.NO_COOKIE_DOMAINS:
            if domain == no_cookie_domain or domain.endswith('.' + no_cookie_domain):
                logger.info(f"URL {url} matches NO_COOKIE_DOMAINS pattern: {no_cookie_domain}")
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking NO_COOKIE_DOMAINS for URL {url}: {e}")
        return False
