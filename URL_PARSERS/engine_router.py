from URL_PARSERS.tags import extract_url_range_tags
from HELPERS.safe_messeger import fake_message
from HELPERS.logger import logger
from COMMANDS.image_cmd import image_command
from CONFIG.domains import DomainsConfig
from urllib.parse import urlparse


def route_if_gallerydl_only(app, message) -> bool:
    """
    Решает, нужно ли сразу маршрутизировать ссылку в gallery-dl (команда /img),
    минуя yt-dlp. Возвращает True, если обработка полностью выполнена здесь.
    """
    try:
        text = (getattr(message, 'text', None) or getattr(message, 'caption', '') or '').strip()
        if not text:
            return False

        url, _s, _e, _plist, _tags, tags_text, _err = extract_url_range_tags(text)
        if not url:
            return False

        url_l = url.lower()
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        # Правила маршрутизации напрямую в gallery-dl
        # 1) VK wall- посты: картинки обрабатываются стабильнее через gallery-dl
        if "vk.com/wall-" in url_l:
            try:
                fallback_text = f"/img {url}"
                if tags_text:
                    fallback_text += f" {tags_text}"
                fake_msg = fake_message(fallback_text, message.chat.id, original_chat_id=message.chat.id)
                image_command(app, fake_msg)
                logger.info(f"[ENGINE_ROUTER] Routed to gallery-dl: {fallback_text}")
                return True
            except Exception as e:
                logger.error(f"[ENGINE_ROUTER] Failed routing to gallery-dl for {url}: {e}")
                return False

        # 2) Домены из списка GALLERYDL_ONLY_DOMAINS
        try:
            domains_list = getattr(DomainsConfig, 'GALLERYDL_ONLY_DOMAINS', []) or []
        except Exception:
            domains_list = []
        for d in domains_list:
            try:
                d_l = (d or '').strip().lower()
                if not d_l:
                    continue
                if domain == d_l or domain.endswith('.' + d_l):
                    fallback_text = f"/img {url}"
                    if tags_text:
                        fallback_text += f" {tags_text}"
                    fake_msg = fake_message(fallback_text, message.chat.id, original_chat_id=message.chat.id)
                    image_command(app, fake_msg)
                    logger.info(f"[ENGINE_ROUTER] Routed by domain list to gallery-dl: {domain} -> {fallback_text}")
                    return True
            except Exception as e:
                logger.error(f"[ENGINE_ROUTER] Error checking domain {d}: {e}")

        # По умолчанию — не перехватываем, пусть идёт через yt-dlp
        return False
    except Exception as e:
        logger.error(f"[ENGINE_ROUTER] route_if_gallerydl_only error: {e}")
        return False


