
from urllib.parse import urlparse, parse_qs, urlencode
import re
import requests
from CONFIG.config import Config
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


def extract_youtube_id(url: str) -> str:
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
    raise ValueError("Failed to extract YouTube ID")


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
        raise RuntimeError("Failed to download thumbnail or it is too big")
    # We do nothing else - we keep the original size!
