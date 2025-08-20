import re
import os
import tldextract
from urllib.parse import urlparse
from CONFIG.config import Config
from URL_PARSERS.tiktok import is_tiktok_url, extract_tiktok_profile, get_clean_url_for_tagging
from HELPERS.filesystem_hlp import create_directory
from HELPERS.porn import is_porn_domain, extract_domain_parts, SUPPORTED_SITES
from HELPERS.logger import logger

def sanitize_autotag(tag: str) -> str:
    # Leave only letters (any language), numbers and _
    return '#' + re.sub(r'[^\w\d_]', '_', tag.lstrip('#'), flags=re.UNICODE)

def generate_final_tags(url, user_tags, info_dict):
    """Tags now include #porn if found by title, description or caption."""
    final_tags = []
    seen = set()
    # 1. Custom tags
    for tag in user_tags:
        tag_l = tag.lower()
        if tag_l not in seen:
            final_tags.append(tag)
            seen.add(tag_l)
    # 2. Auto-tags (no duplicates)
    auto_tags = get_auto_tags(url, final_tags)
    for tag in auto_tags:
        tag_l = tag.lower()
        if tag_l not in seen:
            final_tags.append(tag)
            seen.add(tag_l)
    # 3. Profile/channel tags (tiktok/youtube)
    if is_tiktok_url(url):
        tiktok_profile = extract_tiktok_profile(url)
        if tiktok_profile:
            tiktok_tag = sanitize_autotag(tiktok_profile)
            if tiktok_tag.lower() not in seen:
                final_tags.append(tiktok_tag)
                seen.add(tiktok_tag.lower())
        if '#tiktok' not in seen:
            final_tags.append('#tiktok')
            seen.add('#tiktok')
    clean_url_for_check = get_clean_url_for_tagging(url)
    if ("youtube.com" in clean_url_for_check or "youtu.be" in clean_url_for_check) and info_dict:
        channel_name = info_dict.get("channel") or info_dict.get("uploader")
        if channel_name:
            channel_tag = sanitize_autotag(channel_name)
            if channel_tag.lower() not in seen:
                final_tags.append(channel_tag)
                seen.add(channel_tag.lower())
    # 4. #porn if defined by title, description or caption
    video_title = info_dict.get("title") if info_dict else None
    video_description = info_dict.get("description") if info_dict else None
    video_caption = info_dict.get("caption") if info_dict else None
    # Temporarily disable porn detection to avoid circular import
    # if is_porn(url, video_title, video_description, video_caption):
    #     if '#porn' not in seen:
    #         final_tags.append('#porn')
    #         seen.add('#porn')
    result = ' '.join(final_tags)
    # Check if info_dict is None before accessing it
    title = info_dict.get('title', 'N/A') if info_dict else 'N/A'
    logger.info(f"Generated final tags for '{title}': \"{result}\"")
    return result


# --- Function for cleaning tags for Telegram ---
def clean_telegram_tag(tag: str) -> str:
    return '#' + re.sub(r'[^\w]', '', tag.lstrip('#'))

# --- a function for extracting the URL, the range and tags from the text ---
def extract_url_range_tags(text: str):
    # This function now always returns the full original download link
    if not isinstance(text, str):
        return None, 1, 1, None, [], '', None
    url_match = re.search(r'https?://[^\s\*#]+', text)
    if not url_match:
        return None, 1, 1, None, [], '', None
    url = url_match.group(0)

    after_url = text[url_match.end():]
    # Range
    range_match = re.match(r'\*([0-9]+)\*([0-9]+)', after_url)
    if range_match:
        video_start_with = int(range_match.group(1))
        video_end_with = int(range_match.group(2))
        after_range = after_url[range_match.end():]
    else:
        video_start_with = 1
        video_end_with = 1
        after_range = after_url
    playlist_name = None
    playlist_match = re.match(r'\*([^\s\*#]+)', after_range)
    if playlist_match:
        playlist_name = playlist_match.group(1)
        after_playlist = after_range[playlist_match.end():]
    else:
        after_playlist = after_range
    # New way: Looking for everything #tags throughout the text (multi -line)
    tags = []
    tags_text = ''
    error_tag = None
    error_tag_example = None
    # We collect everything #tags from the whole text (multi -line)
    for raw in re.finditer(r'#([^#\s]+)', text, re.UNICODE):
        tag = raw.group(1)
        if not re.fullmatch(r'[\w\d_]+', tag, re.UNICODE):
            error_tag = tag
            example = re.sub(r'[^\w\d_]', '_', tag, flags=re.UNICODE)
            error_tag_example = f'#{example}'
            break
        tags.append(f'#{tag}')
    tags_text = ' '.join(tags)
    # Return the error if there is
    return url, video_start_with, video_end_with, playlist_name, tags, tags_text, (error_tag, error_tag_example) if error_tag else None

def save_user_tags(user_id, tags):
    if not tags:
        return
    user_dir = os.path.join("users", str(user_id))
    create_directory(user_dir)
    tags_file = os.path.join(user_dir, "tags.txt")
    # We read already saved tags
    existing = set()
    if os.path.exists(tags_file):
        with open(tags_file, "r", encoding="utf-8") as f:
            for line in f:
                tag = line.strip()
                if tag:
                    existing.add(tag.lower())
    # Add new tags (without registering and without repetitions)
    new_tags = [t for t in tags if t and t.lower() not in existing]
    if new_tags:
        with open(tags_file, "a", encoding="utf-8") as f:
            for tag in new_tags:
                f.write(tag + "\n")


# --- an auxiliary function for searching for car tues ---
def get_auto_tags(url, user_tags):
    auto_tags = set()
    clean_url = get_clean_url_for_tagging(url)
    url_l = clean_url.lower()
    domain_parts, main_domain = extract_domain_parts(url_l)
    parsed = urlparse(clean_url)
    ext = tldextract.extract(clean_url)
    second_level = ext.domain.lower() if ext.domain else ''
    full_domain = f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else ''
    # 1. Porn Check (for all the suffixes of the domain, but taking into account the whitelist)
    if is_porn_domain(domain_parts):
        auto_tags.add(sanitize_autotag('porn'))
    # 2. YouTube Check (including YouTu.be)
    if ("youtube.com" in url_l or "youtu.be" in url_l):
        auto_tags.add("#youtube")
    # 3. Twitter/X check (exact domain match)
    twitter_domains = {"twitter.com", "x.com", "t.co"}
    domain = parsed.netloc.lower()
    if domain in twitter_domains:
        auto_tags.add("#twitter")
    # 4. Boosty check (boosty.to, boosty.com)
    if ("boosty.to" in url_l or "boosty.com" in url_l):
        auto_tags.add("#boosty")
        auto_tags.add("#porn")
    # 5. Service tag for supported sites (by full domain or 2nd level)
    for site in SUPPORTED_SITES:
        site_l = site.lower()
        if second_level == site_l or full_domain == site_l:
            service_tag = '#' + re.sub(r'[^\w\d_]', '', site_l)
            auto_tags.add(service_tag)
            break
    # Do not duplicate user tags
    user_tags_lower = set(t.lower() for t in user_tags)
    auto_tags = [t for t in auto_tags if t.lower() not in user_tags_lower]
    return auto_tags
