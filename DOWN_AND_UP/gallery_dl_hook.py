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

from CONFIG.config import Config
from HELPERS.logger import logger
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain
from URL_PARSERS.youtube import is_youtube_url
import subprocess
import sys
import json
import tempfile


# ---------- Low-level helpers ----------

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


def _apply_config(config: dict):
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
            logger.debug(f"Skipping non-dict config section: {section}={opts}")
            continue
        for key, value in opts.items():
            logger.info(f"Setting {section}.{key} = {value}")
            _gdl_set(section, key, value)


def _prepare_user_cookies_and_proxy(url: str, user_id, use_proxy: bool, config: dict):
    """
    Fill cookies/proxy into config['extractor'] according to your logic.
    """
    if user_id is None:
        return config

    user_dir = os.path.join("users", str(user_id))
    user_cookie_path = os.path.join(user_dir, "cookie.txt")

    # cookies
    if os.path.exists(user_cookie_path):
        config['extractor']['cookies'] = user_cookie_path
        if is_youtube_url(url):
            logger.info(f"Using YouTube cookies for user {user_id}")
    else:
        global_cookie_path = Config.COOKIE_FILE_PATH
        if os.path.exists(global_cookie_path):
            try:
                create_directory(user_dir)
                shutil.copy2(global_cookie_path, user_cookie_path)
                logger.info(f"Copied global cookie file to user {user_id} folder")
                config['extractor']['cookies'] = user_cookie_path
            except Exception as e:
                logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")

    # no-cookies domains
    if is_no_cookie_domain(url):
        config['extractor']['cookies'] = None
        logger.info(f"Using --no-cookies for domain: {url}")

    # proxy
    if use_proxy:
        try:
            from COMMANDS.proxy_cmd import get_proxy_config
            proxy_config = get_proxy_config()
        except Exception as e:
            proxy_config = None
            logger.warning(f"Proxy requested but failed to import/get config: {e}")

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
            logger.info(f"Force using proxy for gallery-dl: {proxy_url}")
        else:
            logger.warning("Proxy requested but proxy configuration is incomplete")
    else:
        # Domain-based proxy logic from your helper
        try:
            from HELPERS.proxy_helper import add_proxy_to_gallery_dl_config
            new_config = add_proxy_to_gallery_dl_config(config, url, user_id)
            if new_config is not None:
                config = new_config
        except Exception as e:
            logger.warning(f"Proxy helper failed: {e}")

    return config


def _first_info_from_items(items_iter):
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

    logger.info("Parsing extractor items...")
    item_count = 0
    
    for it in items_iter:
        item_count += 1
        logger.info(f"Item {item_count}: {it}")
        
        if not isinstance(it, tuple) or not it:
            continue
        tag = it[0]
        
        # Tag 2 = metadata (post info)
        if tag == 2 and len(it) > 1 and isinstance(it[1], dict):
            info = it[1]
            logger.info(f"Found metadata (tag 2): {info}")
            break
        # Tag 3 = URL with metadata
        elif tag == 3 and len(it) > 2:
            url = it[1]
            metadata = it[2] if isinstance(it[2], dict) else {}
            if "url" not in fallback:
                fallback["url"] = url
                fallback.update(metadata)
                logger.info(f"Found URL (tag 3): {url}, metadata: {metadata}")
        # Legacy string tags for compatibility
        elif tag in ("metadata", "gallery", "result"):
            if len(it) > 1 and isinstance(it[1], dict):
                info = it[1]
                logger.info(f"Found metadata (legacy): {info}")
                break
        elif tag == "url" and len(it) > 1:
            if "url" not in fallback:
                fallback["url"] = it[1]
                logger.info(f"Found URL (legacy): {it[1]}")
        elif tag == "filename" and len(it) > 1:
            fallback["filename"] = it[1]
            logger.info(f"Found filename: {it[1]}")
        elif tag == "directory" and len(it) > 1:
            fallback["directory"] = it[1]
            logger.info(f"Found directory: {it[1]}")
        elif tag == "extension" and len(it) > 1:
            fallback["extension"] = it[1]
            logger.info(f"Found extension: {it[1]}")

    logger.info(f"Parsed {item_count} items, info: {info}, fallback: {fallback}")
    return info or (fallback if fallback else None)


# ---------- Public API ----------

def get_image_info(url: str, user_id=None, use_proxy: bool = False):
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
        logger.info(f"Setting gallery-dl config: {config}")
        _apply_config(config)

        # ---- Strategy A: extractor.find + items() (no downloads) ----
        try:
            logger.info("Trying Strategy A: extractor.find + items()")
            ex_find = getattr(gallery_dl, "extractor", None)
            if ex_find is None:
                raise AttributeError("gallery_dl.extractor module not found")

            find_fn = getattr(ex_find, "find", None)
            if find_fn is None:
                raise AttributeError("gallery_dl.extractor.find() not available in this build")

            logger.info(f"Calling extractor.find({url})")
            extractor = find_fn(url)
            if extractor is None:
                raise RuntimeError("No extractor matched the URL")

            # Try to set cookies on the extractor if it has the attribute
            if hasattr(extractor, 'cookies') and config.get('extractor', {}).get('cookies'):
                try:
                    cookie_path = config['extractor']['cookies']
                    if os.path.exists(cookie_path):
                        logger.info(f"Setting cookies on extractor: {cookie_path}")
                        # Try different ways to set cookies
                        if hasattr(extractor, 'set_cookies'):
                            extractor.set_cookies(cookie_path)
                        elif hasattr(extractor, 'cookies'):
                            extractor.cookies = cookie_path
                except Exception as cookie_e:
                    logger.warning(f"Failed to set cookies on extractor: {cookie_e}")

            logger.info("Extractor found, calling items()")
            items_iter = extractor.items()
            info = _first_info_from_items(items_iter)
            if info:
                logger.info(f"Strategy A succeeded, got info: {info}")
                return info
            else:
                logger.warning("Strategy A: extractor.items() returned no valid info")

        except Exception as inner_e:
            logger.warning(f"Strategy A (extractor.find) failed: {inner_e}")

        # Fallback: use --get-urls count only (no downloads)
        try:
            total = get_total_media_count(url, user_id, use_proxy)
            if isinstance(total, int) and total > 0:
                logger.info(f"Fallback metadata from --get-urls: total={total}")
                return {"total": total, "title": "Unknown"}
        except Exception as _:
            pass

        logger.error("All strategies failed to obtain metadata")
        return None

    except Exception as e:
        logger.error(f"Failed to extract image info: {e}")
        return None


def download_image(url: str, user_id=None, use_proxy: bool = False, output_dir: str = None):
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

    # cookies/proxy
    config = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, config)

    try:
        logger.info(f"Setting gallery-dl config: {config}")
        _apply_config(config)

        # Use DownloadJob (CLI-equivalent)
        job_mod = getattr(gallery_dl, "job", None)
        if job_mod is None:
            raise RuntimeError("gallery_dl.job module not found (broken install?)")

        DownloadJob = getattr(job_mod, "DownloadJob", None)
        if DownloadJob is None:
            raise RuntimeError("gallery_dl.job.DownloadJob not available in this build")

        job = DownloadJob(url)
        status = job.run()
        
        # Convention: 0 = success
        if status == 0:
            # Ищем файлы в стандартной папке gallery-dl
            downloaded_files = []
            current_time = time.time()
            logger.info("Searching for downloaded files in gallery-dl directory")

            # Сначала пытаемся найти файлы по именам из extractor
            try:
                extractor = getattr(job, "extractor", None)
                if extractor is not None:
                    logger.info("Trying to find files by names from extractor")
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
                                    possible_paths = [
                                        os.path.join("gallery-dl", full_filename),
                                        os.path.join(".", full_filename)
                                    ]
                                    
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
                gallery_dl_dir = "gallery-dl"
                if os.path.exists(gallery_dl_dir):
                    for root, _, files in os.walk(gallery_dl_dir):
                        for file in files:
                            # Поддерживаем все типы файлов, которые может скачать gallery-dl
                            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.mp3', '.wav', '.ogg', '.m4a', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z')):
                                file_path = os.path.join(root, file)
                                file_time = os.path.getctime(file_path)
                                time_diff = current_time - file_time
                                logger.info(f"Gallery-dl file: {file_path}, created: {file_time}, diff: {time_diff}s")
                                # Check if file was created in the last 0.5 minutes
                                if time_diff < 30:
                                    downloaded_files.append(file_path)
                                    logger.info(f"Found recently created file in gallery-dl dir: {file_path}")

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
    Estimate total media count using CLI equivalent of --get-urls and counting lines.
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
            # Use the same Python interpreter to invoke gallery-dl module (no PATH dependency)
            cmd = [sys.executable, "-m", "gallery_dl", "--config", cfg_path, "--get-urls", url]
            logger.info(f"Counting total media via: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                # each URL per line
                lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
                return len(lines)
            else:
                logger.warning(f"get_total_media_count failed: {result.stderr[:400]}")
                return None
        finally:
            try:
                os.unlink(cfg_path)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"get_total_media_count error: {e}")
        return None


def download_image_range(url: str, range_expr: str, user_id=None, use_proxy: bool = False, output_dir: str = None) -> bool:
    """
    Download only a range of items using extractor.range option.
    Returns True on success (status 0), False otherwise.
    """
    config = {
        "extractor": {
            "timeout": 30,
            "retries": 3,
            "range": range_expr,
        },
    }
    config = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, config)
    try:
        _apply_config(config)
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
        logger.error(f"Failed to download range {range_expr}: {e}")
        return False


def download_image_range_cli(url: str, range_expr: str, user_id=None, use_proxy: bool = False, output_dir: str | None = None) -> bool:
    """
    Strict range download using gallery-dl CLI with --range to avoid Python API variances.
    Returns True if exit code 0.
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
        cfg["extractor"]["base-directory"] = output_dir
        cfg["extractor"]["directory"] = []  # flatten into base-directory
    cfg = _prepare_user_cookies_and_proxy(url, user_id, use_proxy, cfg)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cfg, f)
            cfg_path = f.name
        try:
            # Use module invocation to avoid PATH issues
            cmd = [sys.executable, "-m", "gallery_dl", "--config", cfg_path, "--range", range_expr, url]
            cmd_pretty = ' '.join(cmd)
            # Final safety check that command includes proper --range
            if "--range" not in cmd or range_expr not in cmd:
                logger.error(f"Safety check failed for command (missing --range): {cmd_pretty}")
                return False
            logger.info(f"Downloading range via CLI: {cmd_pretty}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.warning(f"CLI range download failed [{result.returncode}]: {result.stderr[:400]}")
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