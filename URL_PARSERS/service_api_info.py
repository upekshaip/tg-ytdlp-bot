import re
import json
import os
import shutil
from functools import lru_cache
from typing import Dict, Optional, Tuple
from datetime import datetime

import requests


DEFAULT_TIMEOUT_SECONDS = 6
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _load_cookies_for_user(user_id: int) -> Optional[str]:
    """
    Загружает куки для пользователя.
    Возвращает путь к файлу куки или None.
    """
    if not user_id:
        return None
    
    user_dir = os.path.join("users", str(user_id))
    user_cookie_path = os.path.join(user_dir, "cookie.txt")
    
    # Проверяем пользовательские куки
    if os.path.exists(user_cookie_path):
        return user_cookie_path
    
    # Пробуем глобальные куки
    try:
        from CONFIG._config import Config
        global_cookie_path = Config.COOKIE_FILE_PATH
        if os.path.exists(global_cookie_path):
            # Создаем директорию пользователя и копируем глобальные куки
            os.makedirs(user_dir, exist_ok=True)
            shutil.copy2(global_cookie_path, user_cookie_path)
            return user_cookie_path
    except Exception as e:
        print(f"[COOKIES] Error loading global cookies: {e}")
    
    return None


def _create_session_with_cookies(user_id: int = None) -> requests.Session:
    """
    Создает сессию requests с куки пользователя.
    Uses managed session for automatic cleanup.
    """
    from HELPERS.http_manager import get_managed_session
    
    session_name = f"api-info-{user_id}" if user_id else "api-info-global"
    manager = get_managed_session(session_name)
    session = manager.get_session()
    
    # Устанавливаем заголовки
    session.headers.update(DEFAULT_HEADERS)
    
    # Загружаем куки если указан user_id
    if user_id:
        cookie_path = _load_cookies_for_user(user_id)
        if cookie_path:
            try:
                # Загружаем куки из файла
                session.cookies = _load_cookies_from_file(cookie_path)
                print(f"[COOKIES] Loaded cookies for user {user_id} from {cookie_path}")
            except Exception as e:
                print(f"[COOKIES] Error loading cookies for user {user_id}: {e}")
    
    return session


def _load_cookies_from_file(cookie_path: str) -> requests.cookies.RequestsCookieJar:
    """
    Загружает куки из файла в формате Netscape.
    """
    jar = requests.cookies.RequestsCookieJar()
    
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    domain_flag = parts[1] == 'TRUE'
                    path = parts[2]
                    secure = parts[3] == 'TRUE'
                    expiration = parts[4]
                    name = parts[5]
                    value = parts[6]
                    
                    # Пропускаем куки с истекшим сроком (если expiration > 0)
                    if expiration != '0':
                        try:
                            exp_time = int(expiration)
                            if exp_time and exp_time > 0 and exp_time < int(datetime.now().timestamp()):
                                continue
                        except ValueError:
                            pass
                    
                    jar.set(name, value, domain=domain, path=path)
    except Exception as e:
        print(f"[COOKIES] Error parsing cookie file {cookie_path}: {e}")
    
    return jar


def _http_get(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS, user_id: int = None) -> Optional[str]:
    try:
        session = _create_session_with_cookies(user_id)
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.ok:
            return resp.text
    except Exception as e:
        print(f"[HTTP_GET] Request error for {url}: {e}")
        return None
    return None


def _http_get_json(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS, user_id: int = None) -> Optional[Dict]:
    try:
        session = _create_session_with_cookies(user_id)
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.ok:
            return resp.json()
        else:
            # Логируем HTTP ошибки для отладки, но не прерываем процесс
            if resp.status_code == 401:
                print(f"[HTTP_GET_JSON] Authentication required for {url} (401 Unauthorized)")
            elif resp.status_code == 403:
                print(f"[HTTP_GET_JSON] Access forbidden for {url} (403 Forbidden)")
            else:
                print(f"[HTTP_GET_JSON] HTTP error {resp.status_code} for {url}")
    except Exception as e:
        print(f"[HTTP_GET_JSON] Request error for {url}: {e}")
        return None
    return None


META_TAG_RE = re.compile(
    r"<meta[^>]+(?:property|name)=\"([^\"]+)\"[^>]+content=\"([^\"]*)\"[^>]*>",
    re.IGNORECASE,
)


def _extract_meta(html: str) -> Dict[str, str]:
    metas: Dict[str, str] = {}
    if not html:
        return metas
    for match in META_TAG_RE.finditer(html):
        key = match.group(1).strip().lower()
        val = match.group(2).strip()
        metas[key] = val
    return metas


def _extract_via_oembed(url: str, endpoints: Tuple[str, ...], user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Пробует стандартные oEmbed endpoints, возвращает (author_name/provider_name, site_label)
    """
    for ep in endpoints:
        try:
            full = ep.format(url=url)
            data = _http_get_json(full, user_id=user_id)
            if not data:
                continue
            author = data.get("author_name") or data.get("author_url") or data.get("title")
            provider = data.get("provider_name") or data.get("provider_url")
            # Очистим author если это URL
            if isinstance(author, str) and author.startswith("http"):
                # вытащим хвост пути
                try:
                    from urllib.parse import urlparse
                    p = urlparse(author)
                    segment = p.path.strip("/").split("/")
                    if segment and segment[0]:
                        author = segment[-1]
                except Exception:
                    pass
            return (author if isinstance(author, str) else None, provider if isinstance(provider, str) else None)
        except Exception as e:
            print(f"[OEMBED] Endpoint {ep} error: {e}")
            continue
    return (None, None)


def _normalize_slug(text: str) -> str:
    if not text:
        return ""
    # Remove emojis and non-word except spaces/underscore/dash
    text = re.sub(r"[\u2600-\u27BF\U0001F300-\U0001FAD6]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lower()
    text = re.sub(r"[^a-z0-9а-яё\s_-]", "", text)
    text = text.replace(" ", "_")
    return text


def _is_valid_username(token: str) -> bool:
    """Проверяет, что токен похож на ник: >=3 символов, содержит буквы, не только цифры."""
    if not token:
        return False
    token = token.strip()
    if len(token) < 3:
        return False
    if token.isdigit():
        return False
    if not re.search(r"[A-Za-zА-Яа-яЁё]", token):
        return False
    return True


def _parse_date_string(date_str: str) -> Optional[str]:
    """
    Универсальная функция парсинга даты из строки.
    Возвращает дату в формате DD.MM.YYYY или None.
    """
    if not date_str:
        return None
    
    # Список форматов дат для парсинга
    date_formats = [
        "%Y-%m-%d",                    # 2024-10-04
        "%Y-%m-%dT%H:%M:%S",          # 2024-10-04T15:30:00
        "%Y-%m-%dT%H:%M:%SZ",         # 2024-10-04T15:30:00Z
        "%Y-%m-%dT%H:%M:%S.%f",       # 2024-10-04T15:30:00.123456
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2024-10-04T15:30:00.123456Z
        "%Y-%m-%d %H:%M:%S",          # 2024-10-04 15:30:00
        "%Y-%m-%d %H:%M:%S.%f",       # 2024-10-04 15:30:00.123456
        "%d.%m.%Y",                   # 04.10.2024
        "%d/%m/%Y",                   # 04/10/2024
        "%m/%d/%Y",                   # 10/04/2024
        "%B %d, %Y",                  # October 4, 2024
        "%d %B %Y",                   # 4 October 2024
    ]
    
    # Сначала пробуем стандартные форматы
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            continue
    
    # Если не удалось распарсить, попробуем извлечь год-месяц-день регулярным выражением
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if date_match:
        year, month, day = date_match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            pass
    
    # Попробуем ISO формат с временной зоной
    try:
        # Убираем временную зону если есть
        date_clean = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
        dt = datetime.fromisoformat(date_clean)
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        pass
    
    return None


def _guess_username_from_url(url: str, service: Optional[str]) -> Optional[str]:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = [p for p in (parsed.path or '').split('/') if p]
        if not path_parts:
            return None
        u = (url or '').lower()
        # Service-specific heuristics
        if service == 'tiktok':
            # https://www.tiktok.com/@username/... -> take after '@'
            for part in path_parts:
                if part.startswith('@') and _is_valid_username(part[1:]):
                    return part[1:]
        if service == 'instagram':
            blocked = {'p', 'reel', 'reels', 'stories', 'explore', 'tv', 's'}
            cand = path_parts[0]
            if cand not in blocked and _is_valid_username(cand):
                return cand
        if service in {'x', 'twitter'}:
            blocked = {'i', 'status', 'home', 'explore', 'notifications', 'share'}
            cand = path_parts[0]
            if cand not in blocked and _is_valid_username(cand):
                return cand
        if service == 'vk':
            # Prefer readable slugs like /somegroup; skip wall-, video, photo
            blocked_prefixes = ('wall', 'video', 'photo')
            cand = path_parts[0]
            if not any(cand.startswith(p) for p in blocked_prefixes) and _is_valid_username(cand):
                return cand
        if service in {'youtube'}:
            # /@channel, /channel/UC..., /c/name, /user/name
            if path_parts[0].startswith('@') and _is_valid_username(path_parts[0][1:]):
                return path_parts[0][1:]
            if len(path_parts) >= 2 and path_parts[0] in {'c', 'user'} and _is_valid_username(path_parts[1]):
                return path_parts[1]
        # Generic fallback: first segment that looks like username and not a known content marker
        generic_blocked = {'status', 'watch', 'post', 'p', 'reel', 'photo', 'video', 'wall'}
        for part in path_parts:
            if part in generic_blocked:
                continue
            # strip common file extensions
            part_clean = re.sub(r"\.(jpg|jpeg|png|gif|webp|mp4|mov|avi|mkv)$", "", part, flags=re.IGNORECASE)
            if _is_valid_username(part_clean):
                return part_clean
    except Exception:
        return None
    return None


def _detect_service(url: str) -> Optional[str]:
    if not url:
        return None
    u = url.lower()
    if "instagram.com" in u:
        return "instagram"
    if "tiktok.com" in u:
        return "tiktok"
    if "twitter.com" in u or "x.com" in u:
        return "x"
    if "vk.com" in u or "vkontakte.ru" in u:
        return "vk"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "reddit.com" in u:
        return "reddit"
    if "pinterest.com" in u:
        return "pinterest"
    if "flickr.com" in u:
        return "flickr"
    if "deviantart.com" in u:
        return "deviantart"
    if "imgur.com" in u:
        return "imgur"
    if "tumblr.com" in u:
        return "tumblr"
    if "pixiv.net" in u:
        return "pixiv"
    if "artstation.com" in u:
        return "artstation"
    if "danbooru.donmai.us" in u or "danbooru" in u:
        return "danbooru"
    if "gelbooru.com" in u:
        return "gelbooru"
    if "yande.re" in u or "yande" in u:
        return "yandere"
    if "sankakucomplex.com" in u or "c.sankakucomplex.com" in u or "chan.sankaku" in u:
        return "sankaku"
    if "e621.net" in u:
        return "e621"
    if "rule34.xxx" in u or "rule34.paheal.net" in u:
        return "rule34"
    if "behance.net" in u or "behance.com" in u:
        return "behance"
    return None


# -------- Instagram --------


def _extract_instagram_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed first with cookies
    try:
        data = _http_get_json(f"https://www.instagram.com/oembed/?url={url}", user_id=user_id)
        if data and isinstance(data, dict):
            author = data.get("author_name")
            provider = data.get("provider_name") or "Instagram"
            if author:
                return (author, provider)
    except Exception as e:
        print(f"[INSTAGRAM_INFO] oEmbed error: {e}")
        pass
    # Fallback to OpenGraph
    html = _http_get(url, user_id=user_id)
    metas = _extract_meta(html or "")
    title = metas.get("og:title") or metas.get("twitter:title")
    site = metas.get("og:site_name") or "Instagram"
    name: Optional[str] = None
    if title:
        # Patterns commonly seen
        patterns = [
            r"^(.*?) on Instagram",
            r"^(.*?) • Instagram",
            r"^Instagram post by (.*?)(?:\s+•|$)",
            r"^(.+?) \(@[^)]+\) • Instagram",
        ]
        for p in patterns:
            m = re.search(p, title, re.IGNORECASE)
            if m and m.group(1):
                name = m.group(1).strip()
                break
    return (name, site)


def _extract_instagram_date(url: str, user_id: int = None) -> Optional[str]:
    """
    Извлекает дату загрузки из Instagram API (oEmbed).
    Возвращает дату в формате DD.MM.YYYY или None.
    """
    try:
        data = _http_get_json(f"https://www.instagram.com/oembed/?url={url}", user_id=user_id)
        if data and isinstance(data, dict):
            # oEmbed может содержать дату в разных полях
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс
        print(f"[INSTAGRAM_DATE] API error: {e}")
        pass
    
    # Fallback: попробуем извлечь из OpenGraph мета-тегов
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        
        # Ищем дату в различных мета-тегах
        date_fields = [
            "article:published_time",
            "article:modified_time", 
            "og:updated_time",
            "twitter:data1",
            "date",
            "pubdate"
        ]
        
        for field in date_fields:
            date_str = metas.get(field)
            if date_str:
                result = _parse_date_string(date_str)
                if result:
                    return result
    except Exception as e:
        print(f"[INSTAGRAM_DATE] OpenGraph error: {e}")
        pass
    
    return None


# -------- TikTok --------


def _extract_tiktok_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        oembed_url = f"https://www.tiktok.com/oembed?url={url}"
        data = _http_get_json(oembed_url, user_id=user_id)
        if data and isinstance(data, dict):
            author = data.get("author_name")
            if author:
                return (author, "TikTok")
    except Exception as e:
        print(f"[TIKTOK_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        oembed_url = f"https://www.tiktok.com/oembed?url={url}"
        data = _http_get_json(oembed_url)
        if data and isinstance(data, dict):
            author = data.get("author_name")
            if author:
                return (author, "TikTok")
    except Exception as e:
        print(f"[TIKTOK_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        if title:
            m = re.search(r"^(.*?) on TikTok|^(.*?) \| TikTok", title, re.IGNORECASE)
            if m:
                candidate = m.group(1) or m.group(2)
                if candidate:
                    return (candidate.strip(), "TikTok")
    except Exception as e:
        print(f"[TIKTOK_INFO] OpenGraph error: {e}")
        pass
    
    return (None, "TikTok")


def _extract_tiktok_date(url: str, user_id: int = None) -> Optional[str]:
    """Извлекает дату загрузки из TikTok API."""
    # Try with cookies first
    try:
        data = _http_get_json(f"https://www.tiktok.com/oembed?url={url}", user_id=user_id)
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[TIKTOK_DATE] API with cookies error: {e}")
        pass
    
    # Fallback without cookies
    try:
        data = _http_get_json(f"https://www.tiktok.com/oembed?url={url}")
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[TIKTOK_DATE] API without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        date_str = metas.get("article:published_time") or metas.get("og:updated_time")
        if date_str:
            return _parse_date_string(date_str)
    except Exception as e:
        print(f"[TIKTOK_DATE] OpenGraph error: {e}")
        pass
    
    return None


# -------- X (Twitter) --------


def _extract_x_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={url}"
        data = _http_get_json(oembed_url, user_id=user_id)
        if data and isinstance(data, dict):
            author = data.get("author_name")
            if author:
                return (author, "X")
    except Exception as e:
        print(f"[X_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={url}"
        data = _http_get_json(oembed_url)
        if data and isinstance(data, dict):
            author = data.get("author_name")
            if author:
                return (author, "X")
    except Exception as e:
        print(f"[X_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback: meta twitter:site or title
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        handle = metas.get("twitter:site")
        if handle:
            handle = handle.strip()
            if handle.startswith("@"):
                return (handle, "X")
        title = metas.get("og:title") or metas.get("twitter:title")
        if title:
            m = re.search(r"^(.*?) on X|^(.*?) / X", title, re.IGNORECASE)
            if m:
                candidate = m.group(1) or m.group(2)
                if candidate:
                    return (candidate.strip(), "X")
    except Exception as e:
        print(f"[X_INFO] OpenGraph error: {e}")
        pass
    
    return (None, "X")


def _extract_x_date(url: str, user_id: int = None) -> Optional[str]:
    """Извлекает дату публикации из X (Twitter) API."""
    # Try with cookies first
    try:
        data = _http_get_json(f"https://publish.twitter.com/oembed?url={url}", user_id=user_id)
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[X_DATE] API with cookies error: {e}")
        pass
    
    # Fallback without cookies
    try:
        data = _http_get_json(f"https://publish.twitter.com/oembed?url={url}")
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[X_DATE] API without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        date_str = metas.get("article:published_time") or metas.get("og:updated_time")
        if date_str:
            return _parse_date_string(date_str)
    except Exception as e:
        print(f"[X_DATE] OpenGraph error: {e}")
        pass
    
    return None


# -------- VK --------


def _extract_vk_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try to resolve owner from wall-<owner>_<post>
    site = "VK"
    try:
        m = re.search(r"vk\.com/(?:wall)(-?\d+)_\d+", url, re.IGNORECASE)
        if m:
            owner_id = int(m.group(1))
            probe_urls = []
            if owner_id and owner_id < 0:
                gid = abs(owner_id)
                probe_urls = [
                    f"https://vk.com/public{gid}",
                    f"https://vk.com/club{gid}",
                ]
            else:
                probe_urls = [
                    f"https://vk.com/id{owner_id}",
                ]
            for pu in probe_urls:
                try:
                    html_p = _http_get(pu, user_id=user_id)
                    metas_p = _extract_meta(html_p or "")
                    t = metas_p.get("og:title") or metas_p.get("twitter:title")
                    s = metas_p.get("og:site_name") or site
                    if t:
                        mm = re.search(r"^(.+?)\s*\|\s*VK$", t, re.IGNORECASE)
                        name = (mm.group(1).strip() if mm and mm.group(1) else t.strip())
                        name = re.sub(r"^Сообщество\s+«?", "", name).strip()
                        name = re.sub(r"»$", "", name).strip()
                        name = re.sub(r"^Запись сообщества\s+", "", name).strip()
                        if name:
                            return (name, s)
                except Exception as e:
                    print(f"[VK_INFO] Probe URL {pu} error: {e}")
                    continue
    except Exception as e:
        print(f"[VK_INFO] Wall parsing error: {e}")
        pass
    
    # Fallback: use current page OG/title heuristics with cookies
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or site
        if title:
            mm = re.search(r"^(.+?)\s*\|\s*VK$", title, re.IGNORECASE)
            if mm and mm.group(1):
                cleaned = re.sub(r"^Сообщество\s+«?", "", mm.group(1)).strip()
                cleaned = re.sub(r"»$", "", cleaned).strip()
                cleaned = re.sub(r"^Запись сообщества\s+", "", cleaned).strip()
                if cleaned:
                    return (cleaned, site)
    except Exception as e:
        print(f"[VK_INFO] OpenGraph error: {e}")
        pass
    
    return (None, site)


# -------- YouTube --------


def _extract_youtube_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.youtube.com/oembed?url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "YouTube")
    except Exception as e:
        print(f"[YOUTUBE_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.youtube.com/oembed?url={url}",
        ))
        if name:
            return (name, provider or "YouTube")
    except Exception as e:
        print(f"[YOUTUBE_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        channel = metas.get("og:site_name") or metas.get("twitter:title")
        return (channel, "YouTube")
    except Exception as e:
        print(f"[YOUTUBE_INFO] OpenGraph error: {e}")
        return (None, "YouTube")


def _extract_youtube_date(url: str, user_id: int = None) -> Optional[str]:
    """Извлекает дату загрузки из YouTube API."""
    # Try with cookies first
    try:
        data = _http_get_json(f"https://www.youtube.com/oembed?url={url}", user_id=user_id)
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[YOUTUBE_DATE] API with cookies error: {e}")
        pass
    
    # Fallback without cookies
    try:
        data = _http_get_json(f"https://www.youtube.com/oembed?url={url}")
        if data and isinstance(data, dict):
            date_str = data.get("upload_date") or data.get("created_at") or data.get("date")
            if date_str:
                return _parse_date_string(date_str)
    except Exception as e:
        print(f"[YOUTUBE_DATE] API without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        date_str = metas.get("article:published_time") or metas.get("og:updated_time")
        if date_str:
            return _parse_date_string(date_str)
    except Exception as e:
        print(f"[YOUTUBE_DATE] OpenGraph error: {e}")
        pass
    
    return None


# -------- Reddit --------


def _extract_reddit_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.reddit.com/oembed?url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "Reddit")
    except Exception as e:
        print(f"[REDDIT_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.reddit.com/oembed?url={url}",
        ))
        if name:
            return (name, provider or "Reddit")
    except Exception as e:
        print(f"[REDDIT_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Reddit")
    except Exception as e:
        print(f"[REDDIT_INFO] OpenGraph error: {e}")
        return (None, "Reddit")


# -------- Pinterest --------


def _extract_pinterest_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Нет официального публичного oEmbed, используем только OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Pinterest"
        return (title, site)
    except Exception as e:
        print(f"[PINTEREST_INFO] OpenGraph error: {e}")
        return (None, "Pinterest")


# -------- Flickr --------


def _extract_flickr_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.flickr.com/services/oembed?format=json&url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "Flickr")
    except Exception as e:
        print(f"[FLICKR_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.flickr.com/services/oembed?format=json&url={url}",
        ))
        if name:
            return (name, provider or "Flickr")
    except Exception as e:
        print(f"[FLICKR_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title")
        return (title, "Flickr")
    except Exception as e:
        print(f"[FLICKR_INFO] OpenGraph error: {e}")
        return (None, "Flickr")


# -------- DeviantArt --------


def _extract_deviantart_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://backend.deviantart.com/oembed?url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "DeviantArt")
    except Exception as e:
        print(f"[DEVIANTART_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://backend.deviantart.com/oembed?url={url}",
        ))
        if name:
            return (name, provider or "DeviantArt")
    except Exception as e:
        print(f"[DEVIANTART_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        author = metas.get("twitter:creator") or metas.get("og:site_name")
        return (author, "DeviantArt")
    except Exception as e:
        print(f"[DEVIANTART_INFO] OpenGraph error: {e}")
        return (None, "DeviantArt")


# -------- Imgur --------


def _extract_imgur_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://api.imgur.com/oembed?url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "Imgur")
    except Exception as e:
        print(f"[IMGUR_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://api.imgur.com/oembed?url={url}",
        ))
        if name:
            return (name, provider or "Imgur")
    except Exception as e:
        print(f"[IMGUR_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Imgur")
    except Exception as e:
        print(f"[IMGUR_INFO] OpenGraph error: {e}")
        return (None, "Imgur")


# -------- Tumblr --------


def _extract_tumblr_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try oEmbed with cookies first
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.tumblr.com/oembed/1.0?url={url}",
        ), user_id=user_id)
        if name:
            return (name, provider or "Tumblr")
    except Exception as e:
        print(f"[TUMBLR_INFO] oEmbed with cookies error: {e}")
        pass
    
    # Fallback to oEmbed without cookies
    try:
        name, provider = _extract_via_oembed(url, (
            "https://www.tumblr.com/oembed/1.0?url={url}",
        ))
        if name:
            return (name, provider or "Tumblr")
    except Exception as e:
        print(f"[TUMBLR_INFO] oEmbed without cookies error: {e}")
        pass
    
    # Final fallback to OpenGraph
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Tumblr"
        return (title, site)
    except Exception as e:
        print(f"[TUMBLR_INFO] OpenGraph error: {e}")
        return (None, "Tumblr")


# -------- Pixiv --------


def _extract_pixiv_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Try OpenGraph with cookies first
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Pixiv"
        if title:
            return (title, site)
    except Exception as e:
        print(f"[PIXIV_INFO] OpenGraph with cookies error: {e}")
        pass
    
    # Fallback to OpenGraph without cookies
    try:
        html = _http_get(url)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Pixiv"
        if title:
            return (title, site)
    except Exception as e:
        print(f"[PIXIV_INFO] OpenGraph without cookies error: {e}")
        pass
    
    # Final fallback: try to parse user from URL
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        parts = [s for s in p.path.split('/') if s]
        if len(parts) >= 2 and parts[0] in {"users", "member"}:
            return (parts[1], "Pixiv")
    except Exception as e:
        print(f"[PIXIV_INFO] URL parsing error: {e}")
        pass
    
    return (None, "Pixiv")


# -------- ArtStation --------


def _extract_artstation_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # ArtStation has OG meta with title/site
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "ArtStation"
        return (title, site)
    except Exception as e:
        print(f"[ARTSTATION_INFO] OpenGraph error: {e}")
        return (None, "ArtStation")


# -------- Danbooru --------


def _extract_danbooru_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Danbooru")
    except Exception as e:
        print(f"[DANBOORU_INFO] OpenGraph error: {e}")
        return (None, "Danbooru")


# -------- Gelbooru --------


def _extract_gelbooru_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Gelbooru")
    except Exception as e:
        print(f"[GELBOORU_INFO] OpenGraph error: {e}")
        return (None, "Gelbooru")


# -------- Yande.re --------


def _extract_yandere_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Yande.re")
    except Exception as e:
        print(f"[YANDERE_INFO] OpenGraph error: {e}")
        return (None, "Yande.re")


# -------- Sankaku --------


def _extract_sankaku_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Sankaku"
        return (title, site)
    except Exception as e:
        print(f"[SANKAKU_INFO] OpenGraph error: {e}")
        return (None, "Sankaku")


# -------- e621 --------


def _extract_e621_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "e621")
    except Exception as e:
        print(f"[E621_INFO] OpenGraph error: {e}")
        return (None, "e621")


# -------- Rule34 --------


def _extract_rule34_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        return (title, "Rule34")
    except Exception as e:
        print(f"[RULE34_INFO] OpenGraph error: {e}")
        return (None, "Rule34")


# -------- Behance --------


def _extract_behance_info(url: str, user_id: int = None) -> Tuple[Optional[str], Optional[str]]:
    # Behance has OG meta; sometimes author is in og:title or profile path
    try:
        html = _http_get(url, user_id=user_id)
        metas = _extract_meta(html or "")
        title = metas.get("og:title") or metas.get("twitter:title")
        site = metas.get("og:site_name") or "Behance"
        if title:
            return (title, site)
    except Exception as e:
        print(f"[BEHANCE_INFO] OpenGraph error: {e}")
        pass
    
    # Fallback: try to parse author from URL path
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        seg = [s for s in p.path.split('/') if s]
        if seg:
            return (seg[0], "Behance")
    except Exception as e:
        print(f"[BEHANCE_INFO] URL parsing error: {e}")
        pass
    
    return (None, "Behance")


SERVICE_HANDLERS = {
    "instagram": _extract_instagram_info,
    "tiktok": _extract_tiktok_info,
    "x": _extract_x_info,
    "vk": _extract_vk_info,
    # extended set
    "youtube": _extract_youtube_info,
    "reddit": _extract_reddit_info,
    "pinterest": _extract_pinterest_info,
    "flickr": _extract_flickr_info,
    "deviantart": _extract_deviantart_info,
    "imgur": _extract_imgur_info,
    "tumblr": _extract_tumblr_info,
    # gallery-dl popular
    "pixiv": _extract_pixiv_info,
    "artstation": _extract_artstation_info,
    "danbooru": _extract_danbooru_info,
    "gelbooru": _extract_gelbooru_info,
    "yandere": _extract_yandere_info,
    "sankaku": _extract_sankaku_info,
    "e621": _extract_e621_info,
    "rule34": _extract_rule34_info,
    "behance": _extract_behance_info,
}

SERVICE_DATE_HANDLERS = {
    "instagram": _extract_instagram_date,
    "tiktok": _extract_tiktok_date,
    "x": _extract_x_date,
    "youtube": _extract_youtube_date,
    # Добавьте другие сервисы по мере необходимости
}


@lru_cache(maxsize=512)
def get_service_account_info(url: str, user_id: int = None) -> Dict[str, Optional[str]]:
    """
    Возвращает словарь с ключами:
      - service: детектированное имя сервиса
      - account_display: читаемое имя/ник или @handle если получилось
      - site_label: человекочитаемое название площадки (OG)
    Никогда не бросает исключений.
    """
    try:
        service = _detect_service(url)
        if not service:
            return {"service": None, "account_display": None, "site_label": None}
        handler = SERVICE_HANDLERS.get(service)
        if not handler:
            return {"service": service, "account_display": None, "site_label": None}
        
        # Передаем user_id во все handlers для поддержки куки
        if user_id:
            name, site_label = handler(url, user_id)
        else:
            name, site_label = handler(url)
            
        display = name if name else None
        if not display:
            # Fallback to URL-based guess if API/OG didn't provide
            guessed = _guess_username_from_url(url, service)
            if guessed:
                display = guessed
        return {"service": service, "account_display": display, "site_label": site_label}
    except Exception as e:
        print(f"[SERVICE_ACCOUNT_INFO] Error: {e}")
        return {"service": None, "account_display": None, "site_label": None}


def build_tags(info: Dict[str, Optional[str]]) -> Tuple[str, Optional[str]]:
    """
    Формирует пару (service_tag, account_tag) вида ("#instagram", "#some_account").
    Второй элемент может быть None, если аккаунт не распознан.
    """
    service = info.get("service") or ""
    account = info.get("account_display") or ""
    if not service:
        return ("", None)
    service_tag = f"#{service}"
    account_tag: Optional[str] = None
    if account:
        slug = _normalize_slug(account)
        if slug:
            account_tag = f"#{slug}"
    return (service_tag, account_tag)


def get_account_tag(url: str, user_id: int = None) -> str:
    """
    Удобный интерфейс: возвращает строку хэштегов для сообщения.
    Пример: "#instagram #some_account" или просто "#instagram".
    """
    info = get_service_account_info(url, user_id)
    service_tag, account_tag = build_tags(info)
    if service_tag and account_tag:
        return f"{service_tag} {account_tag}"
    return service_tag or ""


@lru_cache(maxsize=512)
def get_service_date(url: str, user_id: int = None) -> Optional[str]:
    """
    Извлекает дату загрузки/публикации из API различных сервисов.
    Возвращает дату в формате DD.MM.YYYY или None.
    
    Поддерживаемые сервисы:
    - Instagram (oEmbed API) - с поддержкой куки
    - TikTok (oEmbed API)
    - X/Twitter (oEmbed API)
    - YouTube (oEmbed API)
    - И другие через OpenGraph мета-теги
    
    ВАЖНО: Эта функция НЕ критична для работы бота. 
    Если API недоступен (например, Instagram требует аутентификации),
    функция просто вернет None и процесс продолжится.
    """
    try:
        service = _detect_service(url)
        if not service:
            return None
            
        # Пробуем специализированный обработчик для сервиса
        date_handler = SERVICE_DATE_HANDLERS.get(service)
        if date_handler:
            try:
                # Передаем user_id во все date handlers для поддержки куки
                if user_id:
                    result = date_handler(url, user_id)
                else:
                    result = date_handler(url)
                    
                if result:
                    return result
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                print(f"[SERVICE_DATE] {service} API error: {e}")
                pass
        
        # Fallback: попробуем извлечь из OpenGraph мета-тегов
        try:
            html = _http_get(url, user_id=user_id)
            metas = _extract_meta(html or "")
            
            # Ищем дату в различных мета-тегах
            date_fields = [
                "article:published_time",
                "article:modified_time", 
                "og:updated_time",
                "twitter:data1",
                "date",
                "pubdate"
            ]
            
            for field in date_fields:
                date_str = metas.get(field)
                if date_str:
                    result = _parse_date_string(date_str)
                    if result:
                        return result
        except Exception as e:
            print(f"[SERVICE_DATE] OpenGraph error: {e}")
            pass
            
    except Exception as e:
        print(f"[SERVICE_DATE] General error: {e}")
        pass
    
    return None


__all__ = [
    "get_service_account_info",
    "build_tags",
    "get_account_tag",
    "get_service_date",
    "_parse_date_string",
]


