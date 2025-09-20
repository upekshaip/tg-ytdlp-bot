# Filter check for domains
from urllib.parse import urlparse
from CONFIG.domains import DomainsConfig
from HELPERS.logger import logger

def is_no_filter_domain(url: str) -> bool:
    """
    Проверяет, нужно ли отключить match_filter для данного URL.
    
    Args:
        url (str): URL для проверки
        
    Returns:
        bool: True если домен находится в списке NO_FILTER_DOMAINS
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Убираем www. если есть
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Проверяем NO_FILTER_DOMAINS
        if hasattr(DomainsConfig, 'NO_FILTER_DOMAINS') and DomainsConfig.NO_FILTER_DOMAINS:
            # Проверяем точное совпадение домена
            if domain in DomainsConfig.NO_FILTER_DOMAINS:
                logger.info(f"Domain {domain} found in NO_FILTER_DOMAINS list - skipping match_filter")
                return True
                
            # Проверяем поддомены
            for no_filter_domain in DomainsConfig.NO_FILTER_DOMAINS:
                if domain.endswith('.' + no_filter_domain) or domain == no_filter_domain:
                    logger.info(f"Domain {domain} matches no-filter domain {no_filter_domain} - skipping match_filter")
                    return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error checking no-filter domain for {url}: {e}")
        return False
