# -*- coding: utf-8 -*-
"""
gallery-dl integration (robust, version-agnostic)
- Safe config.set wrapper for different gallery-dl versions
- get_image_info(): returns first info dict for a given URL
- download_image(): downloads to output_dir
"""

import os
import time
import shutil
import gallery_dl
import json

from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.logger import logger, log_error_to_channel
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
import subprocess
import sys
import tempfile


# ---------- Low-level helpers ----------

def get_user_gallery_dl_args(user_id: int) -> dict:
    """
    Get user's yt-dlp arguments that are compatible with gallery-dl
    Returns dict with gallery-dl compatible configuration
    """
    try:
        # Import here to avoid circular imports
        from COMMANDS.args_cmd import get_user_args
        
        user_args = get_user_args(user_id)
        if not user_args:
            return {}
        
        gallery_dl_config = {}
        
        # Gallery-dl uses 'extractor' section for most configuration
        # Compatible arguments mapping from yt-dlp to gallery-dl
        compatible_args = {
            'user_agent': 'extractor.headers.User-Agent',
            'referer': 'extractor.headers.Referer', 
            'username': 'extractor.username',
            'password': 'extractor.password',
            'timeout': 'extractor.timeout',
            'retries': 'extractor.retries'
        }
        
        # Apply compatible arguments
        for ytdlp_param, gallery_dl_path in compatible_args.items():
            if ytdlp_param in user_args:
                value = user_args[ytdlp_param]
                if value:  # Only apply non-empty values
                    # Parse nested path like 'extractor.headers.User-Agent'
                    parts = gallery_dl_path.split('.')
                    current = gallery_dl_config
                    
                    # Navigate/create nested structure
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    
                    # Set the final value
                    current[parts[-1]] = value
        
        # Handle http_headers (JSON format) - merge with existing headers
        if 'http_headers' in user_args and user_args['http_headers']:
            try:
                custom_headers = json.loads(user_args['http_headers'])
                if isinstance(custom_headers, dict):
                    # Ensure extractor.headers exists
                    if 'extractor' not in gallery_dl_config:
                        gallery_dl_config['extractor'] = {}
                    if 'headers' not in gallery_dl_config['extractor']:
                        gallery_dl_config['extractor']['headers'] = {}
                    
                    # Merge custom headers
                    gallery_dl_config['extractor']['headers'].update(custom_headers)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in http_headers for user {user_id}")
        
        # Log applied arguments
        if gallery_dl_config:
            logger.info(f"Applied gallery-dl compatible args for user {user_id}: {gallery_dl_config}")
        
        return gallery_dl_config
        
    except Exception as e:
        logger.error(f"Error getting user gallery-dl args for user {user_id}: {e}")
        return {}

def _add_cookies_to_cmd(cmd: list, url: str, user_id: int) -> list:
    """
    Add cookies to gallery-dl CLI command for all sites
    """
    user_dir = os.path.join("users", str(user_id))
    user_cookie_path = os.path.join(user_dir, "cookie.txt")
    if os.path.exists(user_cookie_path):
        # Insert --cookies and path before the URL (last argument)
        cmd.insert(-1, "--cookies")
        cmd.insert(-1, user_cookie_path)
        logger.info(f"[gallery-dl] Added --cookies {user_cookie_path} for {url}")
    return cmd

def _gdl_set(section: str, key: str, value):
    """
    Version-agnostic wrapper for gallery_dl.config.set
    Tries 3-arg signature first, falls back to tuple signature.
    """
    try:
        # 3-arg signature (current version)
        gallery_dl.config.set(section, key, value)
    except TypeError:
        # Tuple signature (older versions)
        gallery_dl.config.set((section, key), value)


def _apply_config(config: dict, user_id=None):
    messages = safe_get_messages(user_id)
    """
    Apply dict config to gallery-dl config safely.
    Expects shape like:
      {
        "extractor": {"timeout": 30, "retries": 3, "cookies": "...", "proxy": "..."},
        "output": {"mode": "info"|"download", "directory": "..."}
      }
    """
    for section, opts in config.items():
        if not isinstance(opts, dict):
            # Rare case: set a whole section value (not typical in gallery-dl)
            logger.debug(safe_get_messages(user_id).GALLERY_DL_SKIPPING_NON_DICT_CONFIG_MSG.format(section=section, opts=opts))
            continue
        for key, value in opts.items():
            logger.info(safe_get_messages(user_id).GALLERY_DL_SETTING_CONFIG_MSG.format(section=section, key=key, value=value))
            _gdl_set(section, key, value)


def _prepare_user_cookies_and_proxy(url: str, user_id, use_proxy: bool, config: dict):
    messages = safe_get_messages(user_id)
    """
    Fill cookies/proxy into config['extractor'] according to your logic.
    Also applies user's compatible yt-dlp arguments to gallery-dl.
    """
    if user_id is None:
        return config

    # Apply user's compatible yt-dlp arguments to gallery-dl
    user_gallery_dl_args = get_user_gallery_dl_args(user_id)
    if user_gallery_dl_args:
        # Deep merge user args into config
        def deep_merge(target, source, user_id=None):
            messages = safe_get_messages(user_id)
            """Recursively merge source dict into target dict"""
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value, user_id)
                else:
                    target[key] = value
        
        deep_merge(config, user_gallery_dl_args, user_id)

    user_dir = os.path.join("users", str(user_id))
    user_cookie_path = os.path.join(user_dir, "cookie.txt")

    # Add Instagram-specific headers to prevent "useragent mismatch" error
    # Only if user hasn't set custom User-Agent
    if "instagram.com" in url.lower():
        # Check if user has set custom User-Agent
        user_has_custom_ua = (
            'extractor' in config and 
            'headers' in config['extractor'] and 
            'User-Agent' in config['extractor']['headers']
        )
        
        if not user_has_custom_ua:
            # Ensure extractor.headers exists
            if 'extractor' not in config:
                config['extractor'] = {}
            if 'headers' not in config['extractor']:
                config['extractor']['headers'] = {}
            
            # Add Instagram-specific headers
            config['extractor']['headers'].update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            })
            logger.info("[GALLERY_DL] Added Instagram-specific headers to prevent useragent mismatch")
        else:
            logger.info("[GALLERY_DL] Using user's custom User-Agent for Instagram")

    # cookies - use new caching system for non-YouTube sites
    if not is_youtube_url(url):
        # For non-YouTube URLs, use new cookie fallback system
        from COMMANDS.cookies_cmd import get_cookie_cache_result, try_non_youtube_cookie_fallback
        cache_result = get_cookie_cache_result(user_id, url)
        
        if cache_result and cache_result['result']:
            # Use cached successful cookies
            config['extractor']['cookies'] = cache_result['cookie_path']
            logger.info(f"Using cached cookies for gallery-dl non-YouTube URL: {url}")
        elif os.path.exists(user_cookie_path):
            config['extractor']['cookies'] = user_cookie_path
            logger.info(safe_get_messages(user_id).GALLERY_DL_USING_USER_COOKIES_MSG.format(cookie_path=user_cookie_path))
        else:
            global_cookie_path = Config.COOKIE_FILE_PATH
            if os.path.exists(global_cookie_path):
                try:
                    create_directory(user_dir)
                    shutil.copy2(global_cookie_path, user_cookie_path)
                    config['extractor']['cookies'] = user_cookie_path
                    logger.info(safe_get_messages(user_id).GALLERY_DL_COPIED_GLOBAL_COOKIE_MSG.format(user_id=user_id))
                    logger.info(safe_get_messages(user_id).GALLERY_DL_USING_COPIED_GLOBAL_COOKIES_MSG.format(cookie_path=user_cookie_path))
                except Exception as e:
                    logger.error(safe_get_messages(user_id).GALLERY_DL_FAILED_COPY_GLOBAL_COOKIE_MSG.format(user_id=user_id, error=e))
    else:
        # For YouTube URLs, use existing logic
        if os.path.exists(user_cookie_path):
            config['extractor']['cookies'] = user_cookie_path
            logger.info(safe_get_messages(user_id).GALLERY_DL_USING_USER_COOKIES_MSG.format(cookie_path=user_cookie_path))
            logger.info(safe_get_messages(user_id).GALLERY_DL_USING_YOUTUBE_COOKIES_MSG.format(user_id=user_id))
        else:
            global_cookie_path = Config.COOKIE_FILE_PATH
            if os.path.exists(global_cookie_path):
                try:
                    create_directory(user_dir)
                    shutil.copy2(global_cookie_path, user_cookie_path)
                    config['extractor']['cookies'] = user_cookie_path
                    logger.info(safe_get_messages(user_id).GALLERY_DL_COPIED_GLOBAL_COOKIE_MSG.format(user_id=user_id))
                    logger.info(safe_get_messages(user_id).GALLERY_DL_USING_COPIED_GLOBAL_COOKIES_MSG.format(cookie_path=user_cookie_path))
                except Exception as e:
                    logger.error(safe_get_messages(user_id).GALLERY_DL_FAILED_COPY_GLOBAL_COOKIE_MSG.format(user_id=user_id, error=e))

    # no-cookies domains
    if is_no_cookie_domain(url):
        config['extractor']['cookies'] = None
        logger.info(safe_get_messages(user_id).GALLERY_DL_USING_NO_COOKIES_MSG.format(url=url))

    # proxy
    if use_proxy:
        try:
            from COMMANDS.proxy_cmd import get_proxy_config
            proxy_config = get_proxy_config()
        except Exception as e:
            proxy_config = None
            logger.warning(safe_get_messages(user_id).GALLERY_DL_PROXY_REQUESTED_FAILED_MSG.format(error=e))

        if proxy_config and 'type' in proxy_config and 'ip' in proxy_config and 'port' in proxy_config:
            ptype = proxy_config['type']
            auth = ""
            if proxy_config.get('user') and proxy_config.get('password'):
                auth = f"{proxy_config['user']}:{proxy_config['password']}@"

            if ptype in ('http', 'https', 'socks4', 'socks5', 'socks5h'):
                proxy_url = f"{ptype}://{auth}{proxy_config['ip']}:{proxy_config['port']}"
            else:
                # default to http
                proxy_url = f"http://{auth}{proxy_config['ip']}:{proxy_config['port']}"

            config['extractor']['proxy'] = proxy_url
            logger.info(safe_get_messages(user_id).GALLERY_DL_FORCE_USING_PROXY_MSG.format(proxy_url=proxy_url))
        else:
            logger.warning(safe_get_messages(user_id).GALLERY_DL_PROXY_CONFIG_INCOMPLETE_MSG)
    else:
        # Domain-based proxy logic from your helper
        try:
            from HELPERS.proxy_helper import add_proxy_to_gallery_dl_config
            new_config = add_proxy_to_gallery_dl_config(config, url, user_id)
            if new_config is not None:
                config = new_config
        except Exception as e:
            logger.warning(safe_get_messages(user_id).GALLERY_DL_PROXY_HELPER_FAILED_MSG.format(error=e))

    return config


def _first_info_from_items(items_iter, user_id=None):
    messages = safe_get_messages(user_id)
    """
    Parse gallery-dl extractor items() stream and return first meaningful info dict.
    The stream yields tuples like:
      (1, ...) - version
      (2, {...}) - metadata (post info)
      (3, "url", {...}) - URL with metadata
      (4, "filename", ...) - filename
      (5, "directory", ...) - directory
    We'll prioritize metadata (tag 2) and URL (tag 3). If not found, fallback to assembling minimal dict.
    """
    info = None
    fallback = {}

    logger.info(safe_get_messages(user_id).GALLERY_DL_PARSING_EXTRACTOR_ITEMS_MSG)
    item_count = 0
    
    for it in items_iter:
        item_count += 1
        logger.info(safe_get_messages(user_id).GALLERY_DL_ITEM_COUNT_MSG.format(count=item_count, item=it))
        
        if not isinstance(it, tuple) or not it:
            continue
        tag = it[0]
        
        # Tag 2 = metadata (post info)
        if tag == 2 and len(it) > 1 and isinstance(it[1], dict):
            info = it[1]
            logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_METADATA_TAG2_MSG.format(info=info))
            break
        # Tag 3 = URL with metadata
        elif tag == 3 and len(it) > 2:
            url = it[1]
            metadata = it[2] if isinstance(it[2], dict) else {}
            if "url" not in fallback:
                fallback["url"] = url
                fallback.update(metadata)
                logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_URL_TAG3_MSG.format(url=url, metadata=metadata))
        # Legacy string tags for compatibility
        elif tag in ("metadata", "gallery", "result"):
            if len(it) > 1 and isinstance(it[1], dict):
                info = it[1]
                logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_METADATA_LEGACY_MSG.format(info=info))
                break
        elif tag == "url" and len(it) > 1:
            if "url" not in fallback:
                fallback["url"] = it[1]
                logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_URL_LEGACY_MSG.format(url=it[1]))
        elif tag == "filename" and len(it) > 1:
            fallback["filename"] = it[1]
            logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_FILENAME_MSG.format(filename=it[1]))
        elif tag == "directory" and len(it) > 1:
            fallback["directory"] = it[1]
            logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_DIRECTORY_MSG.format(directory=it[1]))
        elif tag == "extension" and len(it) > 1:
            fallback["extension"] = it[1]
            logger.info(safe_get_messages(user_id).GALLERY_DL_FOUND_EXTENSION_MSG.format(extension=it[1]))

    logger.info(safe_get_messages(user_id).GALLERY_DL_PARSED_ITEMS_MSG.format(count=item_count, info=info, fallback=fallback))
    return info or (fallback if fallback else None)


# ---------- Public API ----------

def get_image_info(url: str, user_id=None, use_proxy: bool = False):
    messages = safe_get_messages(user_id)
    """
    Return first metadata dict for URL (or None).
    Works across gallery-dl versions (Extractor API -> MetadataJob).
    """
    config = {
        "extractor": {
            "timeout": 30,
            "retries": 3,
        },
        "output": {
            "mode": "info",
        },
    }

    # cookies / proxy
    config = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, config)

    try:
        logger.info(safe_get_messages(user_id).GALLERY_DL_SETTING_CONFIG_MSG2.format(config=config))
        _apply_config(config, user_id)

        # ---- Strategy A: extractor.find + items() (no downloads) ----
        try:
            logger.info(safe_get_messages(user_id).GALLERY_DL_TRYING_STRATEGY_A_MSG)
            ex_find = getattr(gallery_dl, "extractor", None)
            if ex_find is None:
                raise AttributeError(safe_get_messages(user_id).GALLERY_DL_EXTRACTOR_MODULE_NOT_FOUND_MSG)

            find_fn = getattr(ex_find, "find", None)
            if find_fn is None:
                raise AttributeError(safe_get_messages(user_id).GALLERY_DL_EXTRACTOR_FIND_NOT_AVAILABLE_MSG)

            logger.info(safe_get_messages(user_id).GALLERY_DL_CALLING_EXTRACTOR_FIND_MSG.format(url=url))
            extractor = find_fn(url)
            if extractor is None:
                raise RuntimeError(safe_get_messages(user_id).GALLERY_DL_NO_EXTRACTOR_MATCHED_MSG)

            # Try to set cookies on the extractor if it has the attribute
            if hasattr(extractor, 'cookies') and config.get('extractor', {}).get('cookies'):
                try:
                    cookie_path = config['extractor']['cookies']
                    if os.path.exists(cookie_path):
                        logger.info(safe_get_messages(user_id).GALLERY_DL_SETTING_COOKIES_ON_EXTRACTOR_MSG.format(cookie_path=cookie_path))
                        # Try different ways to set cookies
                        if hasattr(extractor, 'set_cookies'):
                            extractor.set_cookies(cookie_path)
                        elif hasattr(extractor, 'cookies'):
                            extractor.cookies = cookie_path
                except Exception as cookie_e:
                    logger.warning(safe_get_messages(user_id).GALLERY_DL_FAILED_SET_COOKIES_ON_EXTRACTOR_MSG.format(error=cookie_e))

            logger.info(safe_get_messages(user_id).GALLERY_DL_EXTRACTOR_FOUND_CALLING_ITEMS_MSG)
            items_iter = extractor.items()
            info = _first_info_from_items(items_iter, user_id)
            if info:
                logger.info(safe_get_messages(user_id).GALLERY_DL_STRATEGY_A_SUCCEEDED_MSG.format(info=info))
                return info
            else:
                logger.warning(safe_get_messages(user_id).GALLERY_DL_STRATEGY_A_NO_VALID_INFO_MSG)

        except Exception as inner_e:
            logger.warning(safe_get_messages(user_id).GALLERY_DL_STRATEGY_A_FAILED_MSG.format(error=inner_e))

        # Fallback: use --get-urls count only (no downloads)
        try:
            total = get_total_media_count(url, user_id, use_proxy)
            if isinstance(total, int) and total > 0:
                logger.info(safe_get_messages(user_id).GALLERY_DL_FALLBACK_METADATA_MSG.format(total=total))
                return {"total": total, "title": "Unknown"}
        except Exception as _:
            pass

        try:
            logger.error(safe_get_messages(user_id).GALLERY_DL_ALL_STRATEGIES_FAILED_MSG)
        except Exception as log_e:
            logger.error(f"All strategies failed to obtain metadata (log error: {log_e})")
        return None

    except Exception as e:
        try:
            logger.error(safe_get_messages(user_id).GALLERY_DL_FAILED_EXTRACT_IMAGE_INFO_MSG.format(error=e))
        except Exception as log_e:
            logger.error(f"Failed to extract image info: {e} (log error: {log_e})")
        return None


def download_image(url: str, user_id=None, use_proxy: bool = False, output_dir: str = None):
    messages = safe_get_messages(user_id)
    """
    Download using gallery-dl DownloadJob, return list of paths to downloaded files or None.
    """
    # Простая конфигурация - пусть gallery-dl работает по умолчанию
    config = {
        "extractor": {
            "timeout": 30,
            "retries": 3,
        },
    }
    
    # Set output directory if provided
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
        # Gallery-dl uses 'output' and 'base-directory' keys (not in extractor)
        config["output"] = {"directory": [output_dir]}
        config["base-directory"] = output_dir

    # cookies/proxy
    config = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, config)

    try:
        logger.info(safe_get_messages(user_id).GALLERY_DL_SETTING_CONFIG_MSG2.format(config=config))
        _apply_config(config, user_id)

        # Use DownloadJob (CLI-equivalent)
        job_mod = getattr(gallery_dl, "job", None)
        if job_mod is None:
            raise RuntimeError(safe_get_messages(user_id).GALLERY_DL_JOB_MODULE_NOT_FOUND_MSG)

        DownloadJob = getattr(job_mod, "DownloadJob", None)
        if DownloadJob is None:
            raise RuntimeError(safe_get_messages(user_id).GALLERY_DL_DOWNLOAD_JOB_NOT_AVAILABLE_MSG)

        job = DownloadJob(url)
        status = job.run()
        
        # Convention: 0 = success
        if status == 0:
            # Ищем файлы в указанной папке или в стандартной папке gallery-dl
            downloaded_files = []
            current_time = time.time()
            logger.info(safe_get_messages(user_id).GALLERY_DL_SEARCHING_DOWNLOADED_FILES_MSG)

            # Сначала пытаемся найти файлы по именам из extractor
            try:
                extractor = getattr(job, "extractor", None)
                if extractor is not None:
                    logger.info(safe_get_messages(user_id).GALLERY_DL_TRYING_FIND_FILES_BY_NAMES_MSG)
                    for item in extractor.items():
                        if isinstance(item, tuple) and len(item) >= 2:
                            tag = item[0]
                            if tag == 3:  # URL item
                                url_part = item[1]
                                metadata = item[2] if len(item) > 2 and isinstance(item[2], dict) else {}
                                
                                # Пытаемся построить имя файла из метаданных
                                filename = metadata.get('filename', '')
                                extension = metadata.get('extension', '')
                                if filename and extension:
                                    full_filename = f"{filename}.{extension}"
                                    
                                    # Ищем файл в возможных местах
                                    possible_paths = []
                                    if output_dir:
                                        # Сначала ищем в указанной папке пользователя
                                        possible_paths.append(os.path.join(output_dir, full_filename))
                                    # Затем в стандартной папке gallery-dl (fallback)
                                    possible_paths.extend([
                                        os.path.join("gallery-dl", full_filename),
                                        os.path.join(".", full_filename)
                                    ])
                                    
                                    # Также пробуем с gallery-dl структурой каталогов
                                    if 'twitter' in url.lower() or 'x.com' in url.lower():
                                        possible_paths.extend([
                                            f"gallery-dl/twitter/{full_filename}",
                                            f"gallery-dl/twitter/{metadata.get('author', {}).get('nick', 'unknown')}/{full_filename}"
                                        ])
                                    elif 'vk.com' in url.lower():
                                        possible_paths.extend([
                                            f"gallery-dl/vk/{full_filename}",
                                            f"gallery-dl/vk/{metadata.get('user', {}).get('id', 'unknown')}/wall/{full_filename}"
                                        ])
                                    elif '2ch.hk' in url.lower() or '2ch' in url.lower():
                                        possible_paths.extend([
                                            f"gallery-dl/2ch/{full_filename}",
                                            f"gallery-dl/2ch/b/{metadata.get('thread', {}).get('id', 'unknown')}/{full_filename}"
                                        ])
                                    
                                    for file_path in possible_paths:
                                        if os.path.exists(file_path):
                                            downloaded_files.append(file_path)
                                            logger.info(f"Found file by name: {file_path}")
                                            break
            except Exception as e:
                logger.warning(f"Failed to find files by names: {e}")

            # Если не нашли по именам, ищем по времени (fallback)
            if not downloaded_files:
                logger.info("Fallback: searching by creation time")
                search_dirs = []
                if output_dir and os.path.exists(output_dir):
                    search_dirs.append(output_dir)
                if os.path.exists("gallery-dl"):
                    search_dirs.append("gallery-dl")
                
                for search_dir in search_dirs:
                    for root, _, files in os.walk(search_dir):
                        for file in files:
                            # Поддерживаем все типы файлов, которые может скачать gallery-dl
                            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.mp3', '.wav', '.ogg', '.m4a', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z')):
                                file_path = os.path.join(root, file)
                                file_time = os.path.getctime(file_path)
                                time_diff = current_time - file_time
                                logger.info(f"Gallery-dl file: {file_path}, created: {file_time}, diff: {time_diff}s")
                                # Check if file was created in the last 0.5 minutes
                                if time_diff and time_diff < 30:
                                    downloaded_files.append(file_path)
                                    logger.info(f"Found recently created file in {search_dir}: {file_path}")

            if downloaded_files:
                logger.info(f"Downloaded {len(downloaded_files)} files: {downloaded_files}")
                return downloaded_files
            else:
                logger.warning("No files found in gallery-dl directory")
                return None

        logger.error(f"DownloadJob finished with non-zero status: {status}")
        return None

    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        return None


# ---------- Optional progress hook (log only) ----------

def gallery_dl_hook(extractor, url, info):
    """Hook for progress tracking (log only)."""
    try:
        title = (info or {}).get("title") if isinstance(info, dict) else "Unknown"
    except Exception:
        title = "Unknown"
    logger.info(f"Gallery-dl extracting from {url}: {title}")


# ---------- New utilities for batching ----------

def get_total_media_count(url: str, user_id=None, use_proxy: bool = False) -> int | None:
    """
    Estimate total media count using gallery-dl extractor to get all media (images + videos).
    Returns integer or None if failed.
    """
    cfg = {
        "extractor": {
            "timeout": 30,
            "retries": 3,
        }
    }
    cfg = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, cfg)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cfg, f)
            cfg_path = f.name
        try:
            # For VK specifically, --simulate is notoriously slow; jump straight to --get-urls
            if 'vk.com' in url.lower():
                logger.info("VK domain detected, skipping --simulate and using --get-urls directly")
                return _get_total_media_count_fallback(url, user_id, use_proxy, cfg_path)
            
            # For Instagram, use special method with Instagram-specific config
            if 'instagram.com' in url.lower():
                # Check if Instagram should skip simulation (from GALLERYDL_FALLBACK_DOMAINS)
                from CONFIG.domains import DomainsConfig
                if 'instagram.com' in DomainsConfig.GALLERYDL_FALLBACK_DOMAINS:
                    logger.info("Instagram domain in GALLERYDL_FALLBACK_DOMAINS, skipping simulation")
                    return None  # Skip simulation for fallback domains
                else:
                    logger.info("Instagram domain detected, using Instagram-specific method")
                    return _get_instagram_media_count(url, user_id, use_proxy, cfg_path)

            # Use gallery-dl extractor to get all media info (not just URLs)
            logger.info(f"[gallery-dl] cookies for media count: {cfg.get('extractor',{}).get('cookies')}")
            cmd = [sys.executable, "-m", "gallery_dl", "--config", cfg_path, "--simulate", url]
            cmd = _add_cookies_to_cmd(cmd, url, user_id)
            logger.info(f"Counting total media via: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            except subprocess.TimeoutExpired:
                logger.warning("--simulate timed out after 15s, falling back to --get-urls")
                return _get_total_media_count_fallback(url, user_id, use_proxy, cfg_path)

            if result.returncode == 0:
                # Count lines that contain media info (not just URLs)
                lines = [ln for ln in result.stdout.splitlines() if ln.strip() and ('"url"' in ln or '"filename"' in ln or '"extension"' in ln)]
                media_count = len(lines)
                if media_count and media_count > 0:
                    logger.info(f"Detected {media_count} total media items (images + videos)")
                    return media_count
                else:
                    logger.warning("--simulate returned 0 media items, trying --get-urls fallback")
                    return _get_total_media_count_fallback(url, user_id, use_proxy, cfg_path)
            else:
                logger.warning(f"get_total_media_count failed: {result.stderr[:400]}")
                # Fallback to --get-urls for sites that don't work with --simulate
                return _get_total_media_count_fallback(url, user_id, use_proxy, cfg_path)
        finally:
            try:
                os.unlink(cfg_path)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"get_total_media_count error: {e}")
        return None

def _get_total_media_count_fallback(url: str, user_id, use_proxy: bool, cfg_path: str) -> int | None:
    """Fallback method using --get-urls for sites that don't work with --simulate"""
    try:
        # Special handling for Instagram - use different approach
        if 'instagram.com' in url.lower():
            # Check if Instagram should skip simulation (from GALLERYDL_FALLBACK_DOMAINS)
            from CONFIG.domains import DomainsConfig
            if 'instagram.com' in DomainsConfig.GALLERYDL_FALLBACK_DOMAINS:
                logger.info("Instagram domain in GALLERYDL_FALLBACK_DOMAINS, skipping simulation in fallback")
                return None  # Skip simulation for fallback domains
            else:
                return _get_instagram_media_count(url, user_id, use_proxy, cfg_path)
        
        cmd = [sys.executable, "-m", "gallery_dl", "--config", cfg_path, "--get-urls", url]
        cmd = _add_cookies_to_cmd(cmd, url, user_id)
        logger.info(f"Fallback counting via --get-urls: {' '.join(cmd)}")
        # VK альбомы могут быть большими – увеличим таймаут для VK
        timeout_sec = 30 if 'vk.com' in url.lower() else 15
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            logger.warning(f"--get-urls timed out after {timeout_sec}s")
            return None
        if result.returncode == 0:
            lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
            logger.info(f"Fallback detected {len(lines)} media items")
            # Add warning for VK about video limitation
            if 'vk.com' in url.lower():
                logger.warning("Note: Gallery-dl only supports images from VK, not videos")
            return len(lines)
        else:
            logger.warning(f"Fallback get_total_media_count failed: {result.stderr[:400]}")
            # Try without cookies for problematic sites
            if any(domain in url.lower() for domain in ['vk.com', 'instagram.com', 'tiktok.com']):
                logger.info(f"Trying {url.split('/')[2]} without cookies...")
                return _try_without_cookies(url, cfg_path, user_id)
            return None
    except Exception as e:
        logger.error(f"Fallback get_total_media_count error: {e}")
        return None

def _get_instagram_media_count(url: str, user_id, use_proxy: bool, cfg_path: str) -> int | None:
    """Special method for Instagram media count using --simulate with Instagram-specific config"""
    try:
        # Create Instagram-specific config with higher limits
        instagram_config = {
            "extractor": {
                "timeout": 60,
                "retries": 3,
                "instagram": {
                    "posts": True,
                    "stories": False,
                    "highlights": False,
                    "igtv": False,
                    "reels": True,
                    "count": 1000  # Increase limit for Instagram
                }
            }
        }
        
        # Add user cookies if available
        user_cookie_path = os.path.join("users", str(user_id), "cookie.txt")
        if os.path.exists(user_cookie_path):
            instagram_config["extractor"]["cookies"] = user_cookie_path
        
        # Add proxy if enabled
        if use_proxy:
            from HELPERS.proxy_helper import get_proxy_for_url
            proxy = get_proxy_for_url(url)
            if proxy:
                instagram_config["extractor"]["proxy"] = proxy
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(instagram_config, f)
            instagram_cfg_path = f.name
        
        try:
            # Use --simulate with Instagram-specific config
            cmd = [sys.executable, "-m", "gallery_dl", "--config", instagram_cfg_path, "--simulate", url]
            logger.info(f"Instagram media count via --simulate: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                # Count lines that contain media info
                lines = [ln for ln in result.stdout.splitlines() if ln.strip() and ('"url"' in ln or '"filename"' in ln or '"extension"' in ln)]
                media_count = len(lines)
                logger.info(f"Instagram detected {media_count} media items via --simulate")
                return media_count
            else:
                logger.warning(f"Instagram --simulate failed: {result.stderr[:400]}")
                # Fallback to --get-urls with Instagram config
                cmd = [sys.executable, "-m", "gallery_dl", "--config", instagram_cfg_path, "--get-urls", url]
                cmd = _add_cookies_to_cmd(cmd, url, user_id)
                logger.info(f"Instagram fallback via --get-urls: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
                    media_count = len(lines)
                    logger.info(f"Instagram detected {media_count} media items via --get-urls")
                    # If still very few items, likely Instagram is blocking - return None to trigger manual input
                    if media_count and media_count < 5:
                        logger.warning(f"Instagram returned only {media_count} items, likely blocked - suggesting manual input")
                        return None
                    return media_count
                else:
                    logger.warning(f"Instagram --get-urls also failed: {result.stderr[:400]}")
                    return None
        finally:
            try:
                os.unlink(instagram_cfg_path)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Instagram media count error: {e}")
        return None

def _try_without_cookies(url: str, cfg_path: str, user_id: int = None) -> int | None:
    """Try without cookies as fallback for problematic sites"""
    try:
        # Create config without cookies
        no_cookies_cfg = {
            "extractor": {
                "timeout": 30,
                "retries": 3,
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(no_cookies_cfg, f)
            no_cookies_cfg_path = f.name
        
        try:
            cmd = [sys.executable, "-m", "gallery_dl", "--config", no_cookies_cfg_path, "--get-urls", url]
            cmd = _add_cookies_to_cmd(cmd, url, user_id)
            logger.info(f"Without cookies: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
                logger.info(f"Without cookies detected {len(lines)} media items")
                return len(lines)
            else:
                logger.warning(f"Without cookies failed: {result.stderr[:400]}")
                return None
        finally:
            try:
                os.unlink(no_cookies_cfg_path)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Without cookies error: {e}")
        return None


def download_image_range(url: str, range_expr: str, user_id=None, use_proxy: bool = False, output_dir: str = None) -> bool | str:
    """
    Download only a range of items using extractor.range option.
    Returns True on success (status 0), False otherwise, or error message string for 401 Unauthorized.
    """
    config = {
        "extractor": {
            "timeout": 30,
            "retries": 3,
            "range": range_expr,
        },
    }
    # Set output directory if provided
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
        # Gallery-dl uses 'output' and 'base-directory' keys (not in extractor)
        config["output"] = {"directory": [output_dir]}
        config["base-directory"] = output_dir
    config = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, config)
    try:
        _apply_config(config, user_id)
        job_mod = getattr(gallery_dl, "job", None)
        if job_mod is None:
            raise RuntimeError("gallery_dl.job module not found (broken install?)")
        DownloadJob = getattr(job_mod, "DownloadJob", None)
        if DownloadJob is None:
            raise RuntimeError("gallery_dl.job.DownloadJob not available in this build")
        job = DownloadJob(url)
        status = job.run()
        return status == 0
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to download range {range_expr}: {error_msg}")
        
        # Check for fatal errors in exception message
        if _is_fatal_error(error_msg):
            error_type = _get_error_type(error_msg, user_id)
            error_response = f"{error_type}: {error_msg}"
            logger.error(f"Fatal error in gallery-dl Python API: {error_response}")
            
            # Log error to exception channel
            log_error_to_channel(None, f"Gallery-dl Python API fatal error: {error_response}", url)
            
            return error_response
        
        return False


def _is_fatal_error(stderr_text: str) -> bool:
    """
    Check if the error is fatal and should stop the download process.
    Returns True if the error indicates that continuing would be pointless.
    """
    stderr_lower = stderr_text.lower()
    
    # Instagram-specific errors that should be treated as fatal (handle early)
    #  - extractor breakage: KeyError - 'data'
    #  - authentication: 401 Unauthorized
    if "instagram" in stderr_lower:
        if "keyerror - 'data'" in stderr_lower or "keyerror: 'data'" in stderr_lower:
            return True
        if "401 unauthorized" in stderr_lower or "http 401" in stderr_lower or " 401 " in stderr_lower:
            return True

    # Authentication errors
    if any(error in stderr_lower for error in [
        "401 unauthorized",
        "403 forbidden", 
        "authentication failed",
        "login required",
        "access denied",
        "unauthorized access",
        "http redirect to login page",
        "redirect to login",
        "login page"
    ]):
        return True
    
    # Unknown errors that should stop the process - but NOT for social media platforms
    if "unknown error" in stderr_lower or "unexpected error" in stderr_lower:
        # For social media platforms, unknown errors are often related to private accounts and should not be fatal
        social_media_platforms = [
            "tiktok", "instagram", "twitter", "x.com", "facebook", "pinterest", 
            "tumblr", "flickr", "deviantart", "artstation", "behance", "pixiv",
            "reddit", "vk", "youtube", "twitch", "patreon", "fanbox", "fantia",
            "onlyfans", "snapchat", "linkedin", "discord", "telegram", "whatsapp"
        ]
        
        for platform in social_media_platforms:
            if platform in stderr_lower:
                print(f"[GALLERY_DL] {platform.title()} unknown error detected, but continuing (non-fatal)")
                return False
        return True
    
    # Other critical errors that should always stop the process
    if any(error in stderr_lower for error in [
        "fatal error",
        "critical error"
    ]):
        return True
    
    # Account/Profile errors
    if any(error in stderr_lower for error in [
        "account not found",
        "profile not found",
        "user not found",
        "page not found",
        "account suspended",
        "account banned",
        "account private",
        "profile private"
    ]):
        return True
    
    # Rate limiting errors
    if any(error in stderr_lower for error in [
        "rate limit exceeded",
        "too many requests",
        "429 too many requests",
        "quota exceeded"
    ]):
        return True
    
    # Network/Connection errors that indicate permanent failure
    if any(error in stderr_lower for error in [
        "connection refused",
        "connection timeout",
        "network unreachable",
        "dns resolution failed"
    ]):
        return True
    
    # Content not available errors
    if any(error in stderr_lower for error in [
        "no media found",
        "no content available",
        "empty profile",
        "no posts found",
        "no videos found",
        "no images found"
    ]):
        return True
    
    # Platform-specific fatal errors
    if any(error in stderr_lower for error in [
        "instagram", "401 unauthorized",  # Instagram auth
        "twitter", "401 unauthorized",    # Twitter auth
        "tiktok", "403 forbidden",        # TikTok access
        "youtube", "403 forbidden",       # YouTube access
        "reddit", "403 forbidden",        # Reddit access
        "pinterest", "401 unauthorized",  # Pinterest auth
        "tumblr", "401 unauthorized",     # Tumblr auth
        "flickr", "401 unauthorized",     # Flickr auth
        "deviantart", "401 unauthorized", # DeviantArt auth
        "artstation", "401 unauthorized", # ArtStation auth
        "onlyfans", "401 unauthorized",   # OnlyFans auth
        "patreon", "401 unauthorized",    # Patreon auth
        "fanbox", "401 unauthorized",     # Fanbox auth
        "fantia", "401 unauthorized",     # Fantia auth
    ]):
        return True
    
    # Additional common errors
    if any(error in stderr_lower for error in [
        "blocked by robots.txt",
        "geoblocked",
        "region blocked",
        "country blocked",
        "ip blocked",
        "user agent blocked",
        "captcha required",
        "verification required",
        "age verification required",
        "nsfw verification required",
        "terms of service violation",
        "copyright violation",
        "dmca takedown",
        "content removed",
        "post deleted",
        "account deleted",
        "account terminated"
    ]):
        return True
    
    return False


def _get_error_type(stderr_text: str, user_id=None) -> str:
    """
    Determine the type of error for better user messaging.
    Returns a human-readable error type.
    """
    stderr_lower = stderr_text.lower()
    
    # Authentication errors
    if any(error in stderr_lower for error in [
        "401 unauthorized", "authentication failed", "login required", "access denied",
        "http redirect to login page", "redirect to login", "login page"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_AUTH_ERROR_MSG
    
    # Unknown errors - but NOT for social media platforms
    if "unknown error" in stderr_lower:
        # For social media platforms, unknown errors are often related to private accounts and should not be fatal
        social_media_platforms = [
            "tiktok", "instagram", "twitter", "x.com", "facebook", "pinterest", 
            "tumblr", "flickr", "deviantart", "artstation", "behance", "pixiv",
            "reddit", "vk", "youtube", "twitch", "patreon", "fanbox", "fantia",
            "onlyfans", "snapchat", "linkedin", "discord", "telegram", "whatsapp"
        ]
        
        for platform in social_media_platforms:
            if platform in stderr_lower:
                return f"{platform.title()} account access error (non-fatal - continuing)"
        return safe_get_messages(user_id).GALLERY_DL_UNKNOWN_ERROR_MSG

    # Instagram-specific errors that should be treated as fatal
    if "instagram" in stderr_lower:
        # KeyError - 'data' (upstream extractor change)
        if "keyerror - 'data'" in stderr_lower or "keyerror: 'data'" in stderr_lower:
            return safe_get_messages(user_id).GALLERY_DL_UNKNOWN_ERROR_MSG
        # 401 Unauthorized - Instagram requires authentication
        if "401 unauthorized" in stderr_lower or "401" in stderr_lower:
            return safe_get_messages(user_id).GALLERY_DL_INSTAGRAM_AUTH_ERROR_MSG
    
    # Other critical errors that should always stop the process
    if any(error in stderr_lower for error in [
        "fatal error", "critical error", "unexpected error"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_UNKNOWN_ERROR_MSG
    
    # Account/Profile errors
    if any(error in stderr_lower for error in [
        "account not found", "profile not found", "user not found", "page not found"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_ACCOUNT_NOT_FOUND_MSG
    
    if any(error in stderr_lower for error in [
        "account suspended", "account banned", "account private", "profile private"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_ACCOUNT_UNAVAILABLE_MSG
    
    # Rate limiting errors
    if any(error in stderr_lower for error in [
        "rate limit exceeded", "too many requests", "429 too many requests", "quota exceeded"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_RATE_LIMIT_EXCEEDED_MSG
    
    # Network errors
    if any(error in stderr_lower for error in [
        "connection refused", "connection timeout", "network unreachable", "dns resolution failed"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_NETWORK_ERROR_MSG
    
    # Content not available
    if any(error in stderr_lower for error in [
        "no media found", "no content available", "empty profile", "no posts found"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_CONTENT_UNAVAILABLE_MSG
    
    # Blocking/Geographic restrictions
    if any(error in stderr_lower for error in [
        "geoblocked", "region blocked", "country blocked", "ip blocked", "user agent blocked"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_GEOGRAPHIC_RESTRICTIONS_MSG
    
    # Verification required
    if any(error in stderr_lower for error in [
        "captcha required", "verification required", "age verification required", "nsfw verification required"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_VERIFICATION_REQUIRED_MSG
    
    # Legal/Policy violations
    if any(error in stderr_lower for error in [
        "terms of service violation", "copyright violation", "dmca takedown", "content removed"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_POLICY_VIOLATION_MSG
    
    # Account issues
    if any(error in stderr_lower for error in [
        "post deleted", "account deleted", "account terminated"
    ]):
        return safe_get_messages(user_id).GALLERY_DL_ACCOUNT_UNAVAILABLE_MSG
    
    return safe_get_messages(user_id).GALLERY_DL_UNKNOWN_ERROR_MSG


def download_image_range_cli(url: str, range_expr: str, user_id=None, use_proxy: bool = False, output_dir: str | None = None) -> bool | str:
    """
    Strict range download using gallery-dl CLI with --range to avoid Python API variances.
    Returns True if exit code 0, False for other errors, or error message string for 401 Unauthorized.
    """
    # Validate range expression to avoid accidental full downloads
    import re as _re
    if not isinstance(range_expr, str) or not _re.fullmatch(r"\d+-\d*", range_expr):
        logger.error(f"Invalid range expression: '{range_expr}'. Expected 'start-end' or 'start-' format.")
        return False

    cfg = {"extractor": {"timeout": 30, "retries": 3}}
    # Scope outputs to a specific run directory if provided
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass
        # Use correct gallery-dl configuration keys
        # Gallery-dl uses 'output' and 'base-directory' keys (not in extractor)
        cfg["output"] = {"directory": [output_dir]}
        cfg["base-directory"] = output_dir
    cfg = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, cfg)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cfg, f)
            cfg_path = f.name
        try:
            # Use module invocation to avoid PATH issues
            logger.info(f"[gallery-dl] cookies for --range {range_expr}: {cfg.get('extractor',{}).get('cookies')}")
            cmd = [sys.executable, "-m", "gallery_dl", "--config", cfg_path, "--range", range_expr, url]
            
            # Add cookies via CLI for social media sites
            cmd = _add_cookies_to_cmd(cmd, url, user_id)
            cmd_pretty = ' '.join(cmd)
            # Final safety check that command includes proper --range
            if "--range" not in cmd or range_expr not in cmd:
                logger.error(f"Safety check failed for command (missing --range): {cmd_pretty}")
                return False
            logger.info(f"Downloading range via CLI: {cmd_pretty}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                stderr_text = result.stderr[:400]
                logger.warning(f"CLI range download failed [{result.returncode}]: {stderr_text}")
                
                # Check for common authentication and access errors
                if _is_fatal_error(stderr_text):
                    error_type = _get_error_type(stderr_text)
                    error_msg = f"{error_type}: {stderr_text}"
                    logger.error(f"Fatal error in gallery-dl: {error_msg}")
                    
                    # Log error to exception channel (skip if no message object available)
                    try:
                        from HELPERS.logger import log_error_to_channel
                        # Create a minimal message object for logging
                        class MinimalMessage:
                            def __init__(self, chat_id, first_name="Unknown"):
                                self.chat = type('Chat', (), {'id': chat_id, 'first_name': first_name})()
                        
                        minimal_msg = MinimalMessage(-1, "Gallery-dl")
                        log_error_to_channel(minimal_msg, f"Gallery-dl fatal error: {error_msg}", url)
                    except Exception as log_e:
                        logger.error(f"Failed to log gallery-dl error: {log_e}")
                    
                    return error_msg
                
                return False
            # Log short stdout to confirm ranged downloads occurred
            if result.stdout:
                preview = '\n'.join(result.stdout.splitlines()[:5])
                logger.info(f"CLI stdout (first lines):\n{preview}")
            return True
        finally:
            try:
                os.unlink(cfg_path)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"download_image_range_cli error: {e}")
        return False