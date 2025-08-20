import tldextract
from urllib.parse import urlparse
from CONFIG.config import Config
from HELPERS.logger import logger

# --- global lists of domains and keywords ---
PORN_DOMAINS = set()
SUPPORTED_SITES = set()
PORN_KEYWORDS = set()

# --- loading lists at start ---
def load_domain_lists():
    global PORN_DOMAINS, SUPPORTED_SITES, PORN_KEYWORDS
    try:
        with open(Config.PORN_DOMAINS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            PORN_DOMAINS = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(PORN_DOMAINS)} domains from {Config.PORN_DOMAINS_FILE}. Example: {list(PORN_DOMAINS)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.PORN_DOMAINS_FILE}: {e}")
        PORN_DOMAINS = set()
    try:
        with open(Config.PORN_KEYWORDS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            PORN_KEYWORDS = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(PORN_KEYWORDS)} keywords from {Config.PORN_KEYWORDS_FILE}. Example: {list(PORN_KEYWORDS)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.PORN_KEYWORDS_FILE}: {e}")
        PORN_KEYWORDS = set()
    try:
        with open(Config.SUPPORTED_SITES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            SUPPORTED_SITES = set(line.strip().lower() for line in f if line.strip())
        logger.info(f"Loaded {len(SUPPORTED_SITES)} supported sites from {Config.SUPPORTED_SITES_FILE}. Example: {list(SUPPORTED_SITES)[:5]}")
    except Exception as e:
        logger.error(f"Failed to load {Config.SUPPORTED_SITES_FILE}: {e}")
        SUPPORTED_SITES = set()

load_domain_lists()

# --- an auxiliary function for extracting a domain ---
def extract_domain_parts(url):
    try:
        ext = tldextract.extract(url)
        # We collect the domain: Domain.suffix (for example, xvideos.com)
        if ext.domain and ext.suffix:
            full_domain = f"{ext.domain}.{ext.suffix}".lower()
            subdomain = ext.subdomain.lower() if ext.subdomain else ''
            # We get all the suffixes: xvideos.com, b.xvideos.com, a.b.xvideos.com
            parts = [full_domain]
            if subdomain:
                sub_parts = subdomain.split('.')
                for i in range(len(sub_parts)):
                    parts.append('.'.join(sub_parts[i:] + [full_domain]))
            return parts, ext.domain.lower()
        elif ext.domain:
            return [ext.domain.lower()], ext.domain.lower()
        else:
            return [url.lower()], url.lower()
    except Exception:
        # Fallback for URLs without a clear domain, e.g., "localhost"
        parsed = urlparse(url)
        if parsed.netloc:
             return [parsed.netloc.lower()], parsed.netloc.lower()
        return [url.lower()], url.lower()


# --- White list of domains that are not considered porn ---
# Now we take from config.py

def is_porn_domain(domain_parts):
    # If any suffix domain on a white list is not porn
    for dom in domain_parts:
        if dom in Config.WHITELIST:
            return False
    # If any suffix domain in the list of porn is porn
    for dom in domain_parts:
        if dom in PORN_DOMAINS:
            return True
    return False

# --- a new function for checking for porn ---
def is_porn(url, title, description, caption=None):
    """
    Checks content for pornography by domain and keywords (word-boundary regex search)
    in title, description and caption. Domain whitelist has highest priority.
    """
    # 1. Checking the domain
    clean_url = url.lower() # Assuming get_clean_url_for_tagging is removed, so we just use the lowercased URL
    domain_parts, _ = extract_domain_parts(clean_url)
    for dom in Config.WHITELIST:
        if dom in domain_parts:
            logger.info(f"is_porn: domain in WHITELIST: {dom}")
            return False
    if is_porn_domain(domain_parts):
        logger.info(f"is_porn: domain match: {domain_parts}")
        return True

    # 2. Preparation of the text
    title_lower       = title.lower()       if title       else ""
    description_lower = description.lower() if description else ""
    caption_lower     = caption.lower()     if caption     else ""
    if not (title_lower or description_lower or caption_lower):
        logger.info("is_porn: all text fields empty")
        return False

    # 3. We collect a single text for search
    combined = " ".join([title_lower, description_lower, caption_lower])
    logger.debug(f"is_porn combined text: '{combined}'")
    logger.debug(f"is_porn keywords: {PORN_KEYWORDS}")

    # 4. Preparing a regex pattern with a list of keywords
    kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not kws:
        # There is not a single valid key
        return False

    # The boundaries of words (\ b) + flag ignorecase
    pattern = re.compile(r"\b(" + "|".join(kws) + r")\b", flags=re.IGNORECASE)

    # 5. We are looking for a coincidence
    if pattern.search(combined):
        logger.info(f"is_porn: keyword match (regex): {pattern.pattern}")
        return True

    logger.info("is_porn: no keyword matches found")
    return False

