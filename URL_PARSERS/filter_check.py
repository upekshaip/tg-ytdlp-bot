# Filter check for domains
from urllib.parse import urlparse
from CONFIG.domains import DomainsConfig
from HELPERS.logger import logger

def is_no_filter_domain(url: str) -> bool:
    """
    Check whether match_filter should be disabled for the given URL.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if the domain is in NO_FILTER_DOMAINS
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Strip leading www.
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Check NO_FILTER_DOMAINS
        if hasattr(DomainsConfig, 'NO_FILTER_DOMAINS') and DomainsConfig.NO_FILTER_DOMAINS:
            # Exact match
            if domain in DomainsConfig.NO_FILTER_DOMAINS:
                logger.info(f"Domain {domain} found in NO_FILTER_DOMAINS list - skipping match_filter")
                return True
                
            # Subdomain match
            for no_filter_domain in DomainsConfig.NO_FILTER_DOMAINS:
                if domain.endswith('.' + no_filter_domain) or domain == no_filter_domain:
                    logger.info(f"Domain {domain} matches no-filter domain {no_filter_domain} - skipping match_filter")
                    return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error checking no-filter domain for {url}: {e}")
        return False
