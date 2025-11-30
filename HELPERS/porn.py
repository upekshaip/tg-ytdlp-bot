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
from CONFIG.messages import Messages, safe_get_messages
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
def is_porn(url, title, description, caption=None, tags=None):
    """
    Checks content for pornography by domain and keywords (word-boundary regex search)
    in title, description, caption, tags and URL. Domain whitelist has highest priority.
    White keywords list can override porn detection for false positive correction.
    URL keywords are checked with spaces replaced by underscores and dashes.
    Tags are checked with underscores treated as word separators.
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
    # Process tags: replace underscores with spaces for keyword matching
    tags_lower = ""
    if tags:
        # Tags are space-separated, but keywords inside tags use underscores
        # Replace underscores with spaces for matching
        tags_lower = tags.lower().replace("_", " ")
    
    # 3. Prepare URL for keyword checking (replace spaces with underscores and dashes)
    url_lower = clean_url
    logger.debug(f"is_porn URL for keyword check: '{url_lower}'")
    
    if not (title_lower or description_lower or caption_lower or tags_lower or url_lower):
        logger.info("is_porn: all text fields and URL empty")
        return False

    # 4. We collect a single text for search (including URL and tags)
    combined = " ".join([title_lower, description_lower, caption_lower, tags_lower, url_lower])
    logger.debug(f"is_porn combined text: '{combined}'")
    logger.debug(f"is_porn keywords: {PORN_KEYWORDS}")

    # 5. Check for white keywords first (override porn detection)
    white_keywords = getattr(DomainsConfig, 'WHITE_KEYWORDS', [])
    if white_keywords:
        white_kws = [re.escape(kw.lower()) for kw in white_keywords if kw.strip()]
        if white_kws:
            white_pattern = re.compile(r"\b(" + "|".join(white_kws) + r")\b", flags=re.IGNORECASE)
            if white_pattern.search(combined):
                logger.info(f"is_porn: white keyword match found, content considered clean: {white_pattern.pattern}")
                return False

    # 6. Preparing regex patterns
    # For text fields we use word boundaries with escaped keywords
    text_kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    # For URL checks we need raw lowercase keywords to build custom delimiter-aware patterns
    url_kws = [kw.lower() for kw in PORN_KEYWORDS if kw.strip()]
    if not text_kws:
        # There is not a single valid key
        return False

    # 7. Check for keyword matches in text fields (with word boundaries)
    # Include tags in text fields check (tags already have underscores replaced with spaces)
    text_pattern = re.compile(r"\b(" + "|".join(text_kws) + r")\b", flags=re.IGNORECASE)
    text_to_check = " ".join([title_lower, description_lower, caption_lower, tags_lower])
    if text_pattern.search(text_to_check):
        logger.info(f"is_porn: keyword match in text fields (regex): {text_pattern.pattern}")
        return True

    # 8. Check for keyword matches in URL with delimiter-aware patterns
    # We only trigger when keyword is delimited on both sides by non-alphanumeric chars (e.g. _, -, symbols) or string edges.
    def _compile_url_keyword_regex(raw_keyword: str) -> re.Pattern:
        words = [re.escape(w) for w in raw_keyword.split() if w]
        if not words:
            # Fallback: compile something that never matches
            return re.compile(r"a^")
        # allow ANY non-alphanumeric delimiters between words inside URL
        joiner = r"[^A-Za-z0-9]+"
        core = joiner.join(words)
        # Require non-alphanumeric (or start/end) around the whole keyword
        return re.compile(rf"(?<![A-Za-z0-9])(?:{core})(?![A-Za-z0-9])", flags=re.IGNORECASE)

    for raw_kw in url_kws:
        url_pattern = _compile_url_keyword_regex(raw_kw)
        if url_pattern.search(url_lower):
            logger.info(f"is_porn: keyword match in URL with delimiters: {raw_kw}")
            return True

    logger.info("is_porn: no keyword matches found")
    return False


def check_porn_detailed(url, title, description, caption=None):
    messages = safe_get_messages(None)
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
            explanation_parts.append(messages.PORN_DOMAIN_WHITELIST_MSG.format(domain=dom))
            return False, " | ".join(explanation_parts)
    
    # Check if domain is in porn domains
    if is_porn_domain(domain_parts):
        explanation_parts.append(messages.PORN_DOMAIN_BLACKLIST_MSG.format(domain_parts=domain_parts))
        return True, " | ".join(explanation_parts)

    # 2. Preparation of the text
    title_lower       = title.lower()       if title       else ""
    description_lower = description.lower() if description else ""
    caption_lower     = caption.lower()     if caption     else ""
    url_lower         = clean_url
    
    if not (title_lower or description_lower or caption_lower or url_lower):
        explanation_parts.append(messages.PORN_ALL_TEXT_FIELDS_EMPTY_MSG)
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
                explanation_parts.append(messages.PORN_WHITELIST_KEYWORDS_MSG.format(keywords=', '.join(set(white_matches))))
                return False, " | ".join(explanation_parts)

    # 5. Check for porn keywords in text fields
    text_kws = [re.escape(kw.lower()) for kw in PORN_KEYWORDS if kw.strip()]
    if not text_kws:
        explanation_parts.append("ℹ️ No porn keywords loaded")
        return False, " | ".join(explanation_parts)

    # Check text fields with word boundaries
    text_pattern = re.compile(r"\b(" + "|".join(text_kws) + r")\b", flags=re.IGNORECASE)
    text_matches = text_pattern.findall(combined)
    
    if text_matches:
        explanation_parts.append(messages.PORN_KEYWORDS_FOUND_MSG.format(keywords=', '.join(set(text_matches))))
        return True, " | ".join(explanation_parts)

    # 6. Check for porn keywords in URL with delimiter-aware patterns
    url_matches = []
    def _compile_url_keyword_regex(raw_keyword: str) -> re.Pattern:
        words = [re.escape(w) for w in raw_keyword.split() if w]
        if not words:
            return re.compile(r"a^")
        # allow ANY non-alphanumeric delimiters between words inside URL
        joiner = r"[^A-Za-z0-9]+"
        core = joiner.join(words)
        return re.compile(rf"(?<![A-Za-z0-9])(?:{core})(?![A-Za-z0-9])", flags=re.IGNORECASE)

    for raw_kw in [kw.lower() for kw in PORN_KEYWORDS if kw.strip()]:
        url_pattern = _compile_url_keyword_regex(raw_kw)
        matches = url_pattern.findall(url_lower)
        if matches:
            url_matches.extend(matches)
    
    if url_matches:
        explanation_parts.append(f"🔗 NSFW keywords found in URL: {', '.join(set(url_matches))}")
        return True, " | ".join(explanation_parts)

    explanation_parts.append(messages.PORN_NO_KEYWORDS_FOUND_MSG)
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
