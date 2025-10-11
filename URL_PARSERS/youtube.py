
from urllib.parse import urlparse, parse_qs, urlencode
import re
import requests
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.logger import logger

def youtube_to_short_url(url: str) -> str:
    """Converts youtube.com/watch?v=... to youtu.be/... while preserving query parameters."""
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc and parsed.path == '/watch':
        qs = parse_qs(parsed.query)
        v = qs.get('v', [None])[0]
        if v:
            # Collect query without v
            query = {k: v for k, v in qs.items() if k != 'v'}
            query_str = urlencode(query, doseq=True)
            base = f'https://youtu.be/{v}'
            if query_str:
                return f'{base}?{query_str}'
            return base
    elif 'youtube.com' in parsed.netloc and parsed.path.startswith('/shorts/'):
        # For YouTube Shorts, convert to youtu.be format
        video_id = parsed.path.split('/')[2]  # /shorts/VIDEO_ID
        if video_id:
            return f'https://youtu.be/{video_id}'
    return url


def youtube_to_long_url(url: str) -> str:
    """Converts youtu.be/... to youtube.com/watch?v=... while preserving query parameters."""
    parsed = urlparse(url)
    if 'youtu.be' in parsed.netloc:
        video_id = parsed.path.lstrip('/')
        if video_id:
            qs = parsed.query
            base = f'https://www.youtube.com/watch?v={video_id}'
            if qs:
                return f'{base}&{qs}'
            return base
    elif 'youtube.com' in parsed.netloc and parsed.path.startswith('/shorts/'):
        # For YouTube Shorts, convert to watch format
        video_id = parsed.path.split('/')[2]  # /shorts/VIDEO_ID
        if video_id:
            return f'https://www.youtube.com/watch?v={video_id}'
    return url


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc


def extract_youtube_id(url: str, user_id=None) -> str:
    """
    It extracts YouTube Video ID from different link formats.
    """
    patterns = [
        r"youtu\.be/([^?&/]+)",
        r"v=([^?&/]+)",
        r"embed/([^?&/]+)",
        r"youtube\.com/watch\?[^ ]*v=([^?&/]+)"
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    raise ValueError(safe_get_messages(user_id).YOUTUBE_FAILED_EXTRACT_ID_MSG)


def download_thumbnail(video_id: str, dest: str, url: str = None) -> None:
    """
    Downloads YouTube (Maxresdefault/Hqdefault) to the disk in the original size.
    URL - it is needed to determine Shorts by link (but now it is not used).
    """
    base = f"https://img.youtube.com/vi/{video_id}"
    img_bytes = None
    for name in ("maxresdefault.jpg", "hqdefault.jpg"):
        r = requests.get(f"{base}/{name}", timeout=10)
        if r.status_code == 200 and len(r.content) <= 1024 * 1024:
            with open(dest, "wb") as f:
                f.write(r.content)
            img_bytes = r.content
            break
    if not img_bytes:
        raise RuntimeError(safe_get_messages(user_id).YOUTUBE_FAILED_DOWNLOAD_THUMBNAIL_MSG)
    # We do nothing else - we keep the original size!


def youtube_to_piped_url(url: str) -> str:
    """Преобразует YouTube-ссылку к формату
    https://<Config.PIPED_DOMAIN>/api/video/download?v=<ID>&q=18
    1) youtu.be -> извлечь ID и собрать целевой URL
    2) youtube.com/watch?v= -> извлечь ID и собрать целевой URL
    3) youtube.com/shorts/ID -> привести к watch и собрать целевой URL
    Иные параметры из исходной ссылки игнорируются (по ТЗ).
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        query = parsed.query
        # 1) короткая форма youtu.be/ID
        if 'youtu.be' in domain:
            video_id = path.lstrip('/')
            return f"https://{Config.PIPED_DOMAIN}/api/video/download?v={video_id}&q=18"
        # 2) полная форма
        if 'youtube.com' in domain:
            # shorts -> watch
            if path.startswith('/shorts/'):
                parts = path.split('/')
                if len(parts) >= 3:
                    vid = parts[2]
                    return f"https://{Config.PIPED_DOMAIN}/api/video/download?v={vid}&q=18"
            # watch?v=ID
            qs = parse_qs(query)
            vid = (qs.get('v') or [None])[0]
            if vid:
                return f"https://{Config.PIPED_DOMAIN}/api/video/download?v={vid}&q=18"
        return url
    except Exception:
        return url
