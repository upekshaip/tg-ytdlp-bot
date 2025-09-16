import tldextract
import re
from urllib.parse import urlparse, parse_qs, unquote
# --- an auxiliary function for extracting a domain ---
def unwrap_redirect_url(url: str) -> str:
    """
    Unwrap common redirect links (Google, Facebook, etc.) by extracting the first
    http(s) URL from known query parameters like url, u, q, redirect, redir, target, to, dest, destination, r, s.

    Performs up to 2 unwrapping passes.
    """
    try:
        current = url
        for _ in range(2):
            parsed = urlparse(current)
            qs = parse_qs(parsed.query or "")
            candidate = None
            for key in [
                "url", "u", "q", "redirect", "redir", "target", "to", "dest", "destination", "r", "s"
            ]:
                values = qs.get(key)
                if not values:
                    continue
                for v in values:
                    v = unquote(v)
                    m = re.search(r"https?://[^\s]+", v)
                    if m:
                        candidate = m.group(0)
                        break
                if candidate:
                    break
            if candidate:
                current = candidate
                continue
            break
        return current
    except Exception:
        return url
from CONFIG.config import Config
from CONFIG.domains import DomainsConfig
import importlib
import types
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
        # Try to unwrap redirectors before extracting the domain
        unwrapped = unwrap_redirect_url(url)
        ext = tldextract.extract(unwrapped)
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
    # If any suffix domain is on a whitelist, it is not porn
    for dom in domain_parts:
        if dom in Config.WHITELIST:
            return False
    # GREYLIST: exclude from domain list check entirely (keywords still apply via is_porn)
    for dom in domain_parts:
        if dom in Config.GREYLIST:
            return False
    # If any suffix domain is in the porn domains list, treat as porn
    for dom in domain_parts:
        if dom in PORN_DOMAINS:
            return True
    return False

# --- a new function for checking for porn ---
def is_porn(url, title, description, caption=None):
    """
    Checks content for pornography by domain and keywords (word-boundary regex search)
    in title, description and caption. Domain whitelist has highest priority.
    White keywords list can override porn detection for false positive correction.
    """
    # 1. Checking the domain (with redirect unwrapping)
    clean_url = unwrap_redirect_url(url).lower()
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

    # 4. Check for white keywords first (override porn detection)
    white_keywords = getattr(DomainsConfig, 'WHITE_KEYWORDS', [])
    if white_keywords:
        white_kws = [re.escape(kw.lower()) for kw in white_keywords if kw.strip()]
        if white_kws:
            white_pattern = re.compile(r"\b(" + "|".join(white_kws) + r")\b", flags=re.IGNORECASE)
            if white_pattern.search(combined):
                logger.info(f"is_porn: white keyword match found, content considered clean: {white_pattern.pattern}")
                return False

    # 5. Preparing a regex pattern with a list of keywords
    kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not kws:
        # There is not a single valid key
        return False

    # The boundaries of words (\ b) + flag ignorecase
    pattern = re.compile(r"\b(" + "|".join(kws) + r")\b", flags=re.IGNORECASE)

    # 6. We are looking for a coincidence
    if pattern.search(combined):
        logger.info(f"is_porn: keyword match (regex): {pattern.pattern}")
        return True

    logger.info("is_porn: no keyword matches found")
    return False


def check_porn_detailed(url, title, description, caption=None):
    """
    Detailed porn check that returns both result and explanation.
    Returns: (is_porn: bool, explanation: str)
    """
    explanation_parts = []
    
    # 1. Checking the domain (with redirect unwrapping)
    clean_url = unwrap_redirect_url(url).lower()
    domain_parts, _ = extract_domain_parts(clean_url)
    
    # Check whitelist first
    for dom in Config.WHITELIST:
        if dom in domain_parts:
            explanation_parts.append(f"✅ Domain in whitelist: {dom}")
            return False, " | ".join(explanation_parts)
    
    # Check if domain is in porn domains
    if is_porn_domain(domain_parts):
        explanation_parts.append(f"❌ Domain in porn blacklist: {domain_parts}")
        return True, " | ".join(explanation_parts)

    # 2. Preparation of the text
    title_lower       = title.lower()       if title       else ""
    description_lower = description.lower() if description else ""
    caption_lower     = caption.lower()     if caption     else ""
    
    if not (title_lower or description_lower or caption_lower):
        explanation_parts.append("ℹ️ All text fields are empty")
        return False, " | ".join(explanation_parts)

    # 3. We collect a single text for search
    combined = " ".join([title_lower, description_lower, caption_lower])
    
    # 4. Check for white keywords first (override porn detection)
    white_keywords = getattr(DomainsConfig, 'WHITE_KEYWORDS', [])
    if white_keywords:
        white_kws = [re.escape(kw.lower()) for kw in white_keywords if kw.strip()]
        if white_kws:
            white_pattern = re.compile(r"\b(" + "|".join(white_kws) + r")\b", flags=re.IGNORECASE)
            white_matches = white_pattern.findall(combined)
            if white_matches:
                explanation_parts.append(f"✅ Found whitelist keywords: {', '.join(set(white_matches))}")
                return False, " | ".join(explanation_parts)

    # 5. Check for porn keywords
    kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not kws:
        explanation_parts.append("ℹ️ No porn keywords loaded")
        return False, " | ".join(explanation_parts)

    # The boundaries of words (\ b) + flag ignorecase
    pattern = re.compile(r"\b(" + "|".join(kws) + r")\b", flags=re.IGNORECASE)
    porn_matches = pattern.findall(combined)
    
    if porn_matches:
        explanation_parts.append(f"❌ Found porn keywords: {', '.join(set(porn_matches))}")
        return True, " | ".join(explanation_parts)

    explanation_parts.append("✅ No porn keywords found")
    return False, " | ".join(explanation_parts)


# --- runtime reload of config-driven lists and file caches ---
def reload_all_porn_caches():
    """
    Reloads:
    - Text-based caches: PORN_DOMAINS, PORN_KEYWORDS, SUPPORTED_SITES
    - Config-based arrays from CONFIG/domains.py: WHITE_KEYWORDS, WHITELIST,
      GREYLIST, PROXY_DOMAINS, PROXY_2_DOMAINS, CLEAN_QUERY, NO_COOKIE_DOMAINS,
      BLACK_LIST, TIKTOK_DOMAINS, PIPED_DOMAIN.

    Returns a dict with basic counts for confirmation output.
    """
    # 1) Reload CONFIG.domains module to pick up changes without bot restart
    try:
        import CONFIG.domains as domains_module  # type: ignore
        domains_module = importlib.reload(domains_module)  # type: ignore
    except Exception as e:
        logger.error(f"Failed to reload CONFIG.domains: {e}")
        # Proceed anyway to reload file-based lists
        domains_module = None  # type: ignore

    # 2) Apply new DomainsConfig values onto runtime Config so other helpers see updates
    try:
        DomainsCfg = domains_module.DomainsConfig if isinstance(domains_module, types.ModuleType) else DomainsConfig  # type: ignore
        attrs_to_copy = [
            'WHITE_KEYWORDS', 'WHITELIST', 'GREYLIST', 'PROXY_DOMAINS', 'PROXY_2_DOMAINS',
            'CLEAN_QUERY', 'NO_COOKIE_DOMAINS', 'BLACK_LIST', 'TIKTOK_DOMAINS', 'PIPED_DOMAIN'
        ]
        for name in attrs_to_copy:
            if hasattr(DomainsCfg, name):
                try:
                    setattr(Config, name, getattr(DomainsCfg, name))
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Failed to apply DomainsConfig to Config: {e}")

    # 3) Reload file-based caches
    load_domain_lists()

    # 4) Build counts snapshot
    counts = {
        'porn_domains': len(PORN_DOMAINS),
        'porn_keywords': len(PORN_KEYWORDS),
        'supported_sites': len(SUPPORTED_SITES),
        'whitelist': len(getattr(Config, 'WHITELIST', []) or []),
        'greylist': len(getattr(Config, 'GREYLIST', []) or []),
        'black_list': len(getattr(Config, 'BLACK_LIST', []) or []),
        'white_keywords': len(getattr(Config, 'WHITE_KEYWORDS', []) or []),
        'proxy_domains': len(getattr(Config, 'PROXY_DOMAINS', []) or []),
        'proxy_2_domains': len(getattr(Config, 'PROXY_2_DOMAINS', []) or []),
        'clean_query': len(getattr(Config, 'CLEAN_QUERY', []) or []),
        'no_cookie_domains': len(getattr(Config, 'NO_COOKIE_DOMAINS', []) or []),
    }
    return counts
