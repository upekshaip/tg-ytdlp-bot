import os
import json
import time
import threading

def encode_playlist_cache_index(index: int) -> str:
    """Encode playlist index for cache storage (uses real positive indices)."""
    # Убрана логика с префиксом 1000 для отрицательных индексов
    # Теперь отрицательные индексы преобразуются в положительные перед сохранением в кэш
    try:
        idx = int(index)
        # Используем реальный индекс (уже преобразованный в положительный)
        return str(idx)
    except (TypeError, ValueError):
        return str(index)
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user, send_to_logger

from DATABASE.firebase_init import db
# NOTE: To avoid circular imports during module load, import URL_PARSERS modules lazily inside functions.
from HELPERS.qualifier import ceil_to_popular
from DATABASE.firebase_init import db_child_by_path
from DATABASE.download_firebase import download_firebase_dump

# Get app instance
app = get_app()

# Global variable for local cache Firebase
firebase_cache = {}

# Auto-reload flags and state
auto_cache_enabled = getattr(Config, 'AUTO_CACHE_RELOAD_ENABLED', True)
auto_cache_thread = None
reload_interval_hours = getattr(Config, 'RELOAD_CACHE_EVERY', 4)
_thread_lock = threading.RLock()

###################################################

def _sync_local_cache_to_file():
    """Синхронизирует локальный кэш с файлом (используется при USE_FIREBASE=False)."""
    global firebase_cache
    use_firebase = getattr(Config, 'USE_FIREBASE', True)
    if not use_firebase:
        try:
            cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'dump.json')
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(firebase_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка синхронизации локального кэша: {e}")

def get_from_local_cache(path_parts):
    """
    Receives data from a local cache along the way, divided into parts
    For example: get_from_local_cache (['Bot', 'Video_cache', 'Hash123', '720p'])
    """
    global firebase_cache
    current = firebase_cache
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            log_firebase_access_attempt(path_parts, success=False)
            return None
    
    log_firebase_access_attempt(path_parts, success=True)
    return current

def log_firebase_access_attempt(path_parts, success=True):
    """
    Logs attempts to turn to a local cache (to track the remaining .get () calls)
    """
    # Show the path in JSON format for local cache
    path_str = ' -> '.join(path_parts)  # For example: "bot -> video_cache -> playlists -> url_hash -> quality"
    status = "SUCCESS" if success else "MISS"
    try:
        logger.info(LoggerMsg.DB_FIREBASE_CACHE_ACCESS_LOG_MSG.format(path=path_str, status=status))
    except Exception:
        # Fallback to stdout if logger is not usable for any reason during early init
        print(f"Firebase local-cache access: {path_str} -> {status}")

def load_firebase_cache():
    messages = safe_get_messages(None)
    """Load local Firebase cache from JSON file."""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'dump.json')
        use_firebase = getattr(Config, 'USE_FIREBASE', True)
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            if use_firebase:
                print(safe_get_messages().DB_FIREBASE_CACHE_LOADED_MSG.format(count=len(firebase_cache)))
            else:
                print(f"✅ Локальный кэш загружен из {cache_file} ({len(firebase_cache)} записей)")
        else:
            if use_firebase:
                print(safe_get_messages().DB_FIREBASE_CACHE_NOT_FOUND_MSG.format(cache_file=cache_file))
            else:
                print(f"ℹ️ Локальный кэш не найден, создан новый файл: {cache_file}")
            firebase_cache = {}
    except Exception as e:
        use_firebase = getattr(Config, 'USE_FIREBASE', True)
        if use_firebase:
            print(safe_get_messages().DB_FAILED_LOAD_FIREBASE_CACHE_MSG.format(error=e))
        else:
            print(f"⚠️ Ошибка загрузки локального кэша: {e}")
        firebase_cache = {}

def reload_firebase_cache():
    messages = safe_get_messages(None)
    """Reloading the local Firebase cache from JSON file"""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            print(safe_get_messages().DB_FIREBASE_CACHE_RELOADED_MSG.format(count=len(firebase_cache)))
            return True
        else:
            print(safe_get_messages().DB_FIREBASE_CACHE_FILE_NOT_FOUND_MSG.format(cache_file=cache_file))
            return False
    except Exception as e:
        print(safe_get_messages().DB_FAILED_RELOAD_FIREBASE_CACHE_MSG.format(error=e))
        return False


def get_next_reload_time(interval_hours: int) -> datetime:
    """
    Returns Datetime the following reloading point,
    aligned according to the N-hour step from 00:00.
    """
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    interval_seconds = max(1, interval_hours) * 3600
    intervals_passed = int(seconds_since_midnight // interval_seconds)
    return midnight + timedelta(seconds=(intervals_passed + 1) * interval_seconds)

def _download_and_reload_cache() -> bool:
    """Download dump via REST and reload local JSON into memory."""
    messages = safe_get_messages(None)
    try:
        ok = download_firebase_dump()
        if not ok:
            print(safe_get_messages().DB_FAILED_DOWNLOAD_DUMP_REST_MSG)
            return False
        return reload_firebase_cache()
    except Exception as e:
        print(safe_get_messages().DB_ERROR_DOWNLOAD_RELOAD_CACHE_MSG.format(error=e))
        return False

def auto_reload_firebase_cache():
    messages = safe_get_messages(None)
    """Background thread that reloads local cache every N hours by downloading dump first."""
    global auto_cache_enabled
    
    # В локальном режиме не нужно перезагружать кэш
    use_firebase = getattr(Config, 'USE_FIREBASE', True)
    if not use_firebase:
        print("ℹ️ Автоматическая перезагрузка кэша отключена в локальном режиме")
        return

    while auto_cache_enabled:
        interval_hours_local = max(1, int(reload_interval_hours))
        next_exec = get_next_reload_time(interval_hours_local)
        now = datetime.now()
        wait_seconds = (next_exec - now).total_seconds()
        if wait_seconds and wait_seconds < 0:
            wait_seconds = 0
        print(
            f"⏳ Waiting until {next_exec.strftime('%Y-%m-%d %H:%M:%S')} "
            f"to refresh Firebase cache (every {interval_hours_local}h; wait {wait_seconds/3600:.2f}h)"
        )
        # Smart sleep with 1-second granularity, allowing dynamic interval changes or stop
        end_time = time.time() + wait_seconds
        while auto_cache_enabled and time.time() < end_time:
            time.sleep(min(1, end_time - time.time()))
            # If interval changed dynamically, break early to recalc next_exec
            if interval_hours_local != max(1, int(reload_interval_hours)):
                break
        if not auto_cache_enabled:
            print("🛑 Auto Firebase cache reloader stopped by admin")
            return
        if interval_hours_local != max(1, int(reload_interval_hours)):
            # Interval changed; recompute loop without running job
            continue
        # Run the refresh by triggering /reload_cache command as admin
        max_retries = 3
        retry_delay = 60  # 1 minute between retries
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Triggering /reload_cache as admin (attempt {attempt + 1}/{max_retries})...")
                # Get first admin ID
                admin_id = Config.ADMIN[0] if isinstance(Config.ADMIN, (list, tuple)) else Config.ADMIN
                print(f"🔄 Triggering /reload_cache as admin (user_id={admin_id})")
                
                # Create fake message and run command
                from types import SimpleNamespace
                msg = SimpleNamespace()
                msg.chat = SimpleNamespace()
                msg.chat.id = admin_id
                msg.chat.first_name = "Admin"
                msg.text = "/reload_cache"
                msg.first_name = msg.chat.first_name
                msg.reply_to_message = None
                msg.id = 0
                msg.from_user = SimpleNamespace()
                msg.from_user.id = admin_id
                msg.from_user.first_name = msg.chat.first_name
                # Mark as fake message for proper handling
                msg._is_fake_message = True
                
                # Import and run the command handler
                from COMMANDS.admin_cmd import reload_firebase_cache_command
                reload_firebase_cache_command(get_app(), msg)
                
                print("✅ Auto /reload_cache command executed successfully!")
                break  # Success, exit retry loop
                
            except Exception as e:
                print(safe_get_messages().DB_ERROR_RUNNING_AUTO_RELOAD_MSG.format(attempt=attempt + 1, max_retries=max_retries, error=e))
                if attempt and attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(safe_get_messages().DB_ALL_RETRY_ATTEMPTS_FAILED_MSG)
                    import traceback; traceback.print_exc()

def start_auto_cache_reloader():
    """Start the auto-reload background thread (idempotent)."""
    global auto_cache_thread, auto_cache_enabled
    with _thread_lock:
        # Check if thread is already running
        if auto_cache_thread is not None and auto_cache_thread.is_alive():
            print("🔄 Auto Firebase cache reloader is already running")
            return auto_cache_thread
            
        if auto_cache_enabled:
            auto_cache_thread = threading.Thread(
                target=auto_reload_firebase_cache,
                daemon=True
            )
            auto_cache_thread.start()
            print(
                f"🚀 Auto Firebase cache reloader started "
                f"(every {max(1, int(reload_interval_hours))}h from 00:00)"
            )
    return auto_cache_thread

def stop_auto_cache_reloader():
    """Stop the auto-reload background thread."""
    global auto_cache_enabled, auto_cache_thread
    with _thread_lock:
        auto_cache_enabled = False
        if auto_cache_thread and auto_cache_thread.is_alive():
            print("🛑 Auto Firebase cache reloader stopping...")
        auto_cache_thread = None

def set_auto_cache_enabled(enabled: bool):
    """Enable/disable auto cache reloader safely."""
    global auto_cache_enabled
    with _thread_lock:
        auto_cache_enabled = bool(enabled)
        if auto_cache_enabled:
            start_auto_cache_reloader()
        else:
            stop_auto_cache_reloader()

def _persist_reload_interval_in_config(new_hours: int) -> bool:
    """Write RELOAD_CACHE_EVERY = <new_hours> back to CONFIG/config.py.
    Keeps formatting/comments around the assignment line intact where possible.
    Also repairs previously corrupted lines if found.
    """
    messages = safe_get_messages(None)
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CONFIG', 'config.py')
        if not os.path.exists(cfg_path):
            logger.warning(LoggerMsg.DB_CONFIG_NOT_FOUND_LOG_MSG.format(path=cfg_path))
            return False
        with open(cfg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 1) Repair accidentally corrupted backreference artifacts
        #    e.g. a line like: \g<1>4\g<3>
        content = re.sub(r"^\\g<1>\d+\\g<3>\s*$", "", content, flags=re.MULTILINE)

        # 2) Replace existing assignment, preserving prefix/suffix
        pattern = re.compile(r"^(\s*RELOAD_CACHE_EVERY\s*=\s*)(\d+)(\s*(#.*)?)$", re.MULTILINE)
        def _repl(m: re.Match) -> str:
            return f"{m.group(1)}{int(new_hours)}{m.group(3)}"
        new_content, n_sub = pattern.subn(_repl, content)

        if n_sub == 0:
            # Append new assignment if not present
            new_content = content.rstrip() + f"\nRELOAD_CACHE_EVERY = {int(new_hours)}  # in hours\n"

        with open(cfg_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(safe_get_messages().DB_RELOAD_CACHE_EVERY_PERSISTED_MSG.format(hours=int(new_hours)))
        return True
    except Exception as e:
        logger.error(LoggerMsg.DB_FAILED_PERSIST_RELOAD_CACHE_EVERY_LOG_MSG.format(error=e))
        return False

def set_reload_interval_hours(new_hours: int) -> bool:
    """Set a new reload interval in hours (1..168). Restarts the reloader if needed and persists to config.py."""
    global reload_interval_hours
    try:
        new_val = int(new_hours)
    except Exception:
        return False
    if new_val and new_val < 1 or new_val > 168:
        return False
    with _thread_lock:
        reload_interval_hours = new_val
        # Update in-memory Config for consistency
        try:
            setattr(Config, 'RELOAD_CACHE_EVERY', new_val)
        except Exception:
            pass
        # Persist to CONFIG/config.py
        _persist_reload_interval_in_config(new_val)
        # Restart thread if running so new interval applies immediately
        running = auto_cache_enabled
        if running:
            stop_auto_cache_reloader()
            # preserve enabled state and start again
            auto_cache_enabled = True
            start_auto_cache_reloader()
    return True

def close_all_firebase_connections():
    """Close all Firebase connections to prevent file descriptor leaks"""
    try:
        from DATABASE.firebase_init import db
        if hasattr(db, 'close'):
            db.close()
            print("✅ Firebase connections closed successfully")
    except Exception as e:
        print(f"❌ Error closing Firebase connections: {e}")

def toggle_auto_cache_reloader():
    """Toggle auto-reload mode, returns new state (True/False)."""
    global auto_cache_enabled
    with _thread_lock:
        auto_cache_enabled = not auto_cache_enabled
        if auto_cache_enabled:
            start_auto_cache_reloader()
        else:
            stop_auto_cache_reloader()
        return auto_cache_enabled

# Load cache on module import
load_firebase_cache()

# ================= /auto_cache command =================

def auto_cache_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Command handler to control automatic Firebase cache loading.

    Supports:
      /auto_cache on
      /auto_cache off
      /auto_cache N   (N in 1..168 hours)
    """
    try:
        if int(message.chat.id) not in Config.ADMIN:
            send_to_user(message, safe_get_messages().DB_AUTO_CACHE_ACCESS_DENIED_MSG)
            return

        text = (message.text or "").strip()
        parts = text.split()
        arg = parts[1].lower() if len(parts) > 1 else None

        if arg in ("on", "off"):
            enable = arg == "on"
            set_auto_cache_enabled(enable)
            status = "✅ ENABLED" if enable else "❌ DISABLED"
            if enable:
                interval = max(1, int(reload_interval_hours))
                next_exec = get_next_reload_time(interval)
                delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
                send_to_user(
                    message,
                    safe_get_messages().DB_AUTO_CACHE_RELOADING_UPDATED_MSG.format(
                        status=status,
                        interval=interval,
                        next_exec=next_exec.strftime('%H:%M'),
                        delta_min=delta_min
                    )
                )
                send_to_logger(message, safe_get_messages().DB_AUTO_CACHE_RELOAD_ENABLED_LOG_MSG.format(next_exec=next_exec))
            else:
                send_to_user(message, safe_get_messages().DB_AUTO_CACHE_RELOADING_STOPPED_MSG)
                send_to_logger(message, safe_get_messages().DB_AUTO_CACHE_RELOAD_DISABLED_LOG_MSG)
            return

        # Try numeric interval
        if arg is not None:
            try:
                n = int(arg)
            except Exception:
                send_to_user(message, safe_get_messages().DB_AUTO_CACHE_INVALID_ARGUMENT_MSG)
                return
            if n and n < 1 or n > 168:
                send_to_user(message, safe_get_messages().DB_AUTO_CACHE_INTERVAL_RANGE_MSG)
                return
            ok = set_reload_interval_hours(n)
            if not ok:
                send_to_user(message, safe_get_messages().DB_AUTO_CACHE_FAILED_SET_INTERVAL_MSG)
                return
            interval = max(1, int(reload_interval_hours))
            next_exec = get_next_reload_time(interval)
            delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
            send_to_user(
                message,
                safe_get_messages().DB_AUTO_CACHE_INTERVAL_UPDATED_MSG.format(
                    status='✅ ENABLED' if auto_cache_enabled else '❌ DISABLED',
                    interval=interval,
                    next_exec=next_exec.strftime('%H:%M'),
                    delta_min=delta_min
                )
            )
            send_to_logger(message, safe_get_messages().DB_AUTO_CACHE_INTERVAL_SET_LOG_MSG.format(interval=interval, next_exec=next_exec))
            return

        # No args: toggle legacy behavior
        new_state = toggle_auto_cache_reloader()
        interval = max(1, int(reload_interval_hours))
        if new_state:
            next_exec = get_next_reload_time(interval)
            delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
            send_to_user(
                message,
                safe_get_messages().DB_AUTO_CACHE_RELOADING_STARTED_MSG.format(
                    interval=interval,
                    next_exec=next_exec.strftime('%H:%M'),
                    delta_min=delta_min
                )
            )
            send_to_logger(message, safe_get_messages().DB_AUTO_CACHE_RELOAD_STARTED_LOG_MSG.format(next_exec=next_exec))
        else:
            send_to_user(message, safe_get_messages().DB_AUTO_CACHE_RELOADING_STOPPED_BY_ADMIN_MSG)
            send_to_logger(message, safe_get_messages().DB_AUTO_CACHE_RELOAD_STOPPED_LOG_MSG)
    except Exception as e:
        logger.error(LoggerMsg.DB_AUTO_CACHE_HANDLER_ERROR_LOG_MSG.format(error=e))


# Added playlist caching - separate functions for saving and retrieving playlist cache
def save_to_playlist_cache(playlist_url: str, quality_key: str, video_indices: list, message_ids: list,
                           messages = safe_get_messages(None),
                           clear: bool = False, original_text: str = None, video_urls_dict: dict = None):
    global firebase_cache
    # Lazy imports to avoid circular imports
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    logger.info(
        f"save_to_playlist_cache called: playlist_url={playlist_url}, quality_key={quality_key}, video_indices={video_indices}, message_ids={message_ids}, clear={clear}")
    
    if not quality_key:
        logger.warning(LoggerMsg.DB_QUALITY_KEY_EMPTY_LOG_MSG.format(playlist_url=playlist_url))
        return

    if not hasattr(Config, 'PLAYLIST_CACHE_DB_PATH') or not Config.PLAYLIST_CACHE_DB_PATH or Config.PLAYLIST_CACHE_DB_PATH.strip() in ('', '/', '.'):
        logger.error(LoggerMsg.DB_PLAYLIST_CACHE_PATH_INVALID_LOG_MSG.format(playlist_url=playlist_url))
        return

    try:
        # Normalize the URL (without the range) and form all link options
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.extend([
                normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))),
                normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))),
            ])
        logger.info(LoggerMsg.DB_NORMALIZED_PLAYLIST_URLS_LOG_MSG.format(urls=urls))

        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"Using playlist URL hash: {url_hash}")

            if clear:
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{quality_key}").remove()
                logger.info(f"Cleared playlist cache for hash={url_hash}, quality={quality_key}")
                # Обновляем локальный кэш
                use_firebase = getattr(Config, 'USE_FIREBASE', True)
                if not use_firebase:
                    path_parts_clear = ["bot", "video_cache", "playlists", url_hash, quality_key]
                    current = firebase_cache
                    for i, part in enumerate(path_parts_clear[:-1]):
                        if part in current and isinstance(current[part], dict):
                            current = current[part]
                        else:
                            break
                    else:
                        if path_parts_clear[-1] in current:
                            del current[path_parts_clear[-1]]
                            _sync_local_cache_to_file()
                continue

            if not message_ids or not video_indices:
                logger.warning(f"message_ids or video_indices is empty for playlist: {playlist_url}, quality: {quality_key}")
                continue

            for i, msg_id in zip(video_indices, message_ids):
                encoded_index = encode_playlist_cache_index(i)
                
                path_parts_local = ["bot", "video_cache", "playlists", url_hash, quality_key, encoded_index]
                path_parts = [Config.PLAYLIST_CACHE_DB_PATH, url_hash, quality_key, encoded_index]
                already_cached = get_from_local_cache(path_parts_local)

                if already_cached:
                    logger.info(safe_get_messages().DB_PLAYLIST_PART_ALREADY_CACHED_MSG.format(path_parts=path_parts_local))
                    continue

                db_child_by_path(db, "/".join(path_parts)).set(str(msg_id))
                logger.info(f"Saved to playlist cache: path={path_parts}, msg_id={msg_id}")
                
                # Обновляем локальный кэш для немедленного доступа (и для Firebase, и для локального режима)
                current = firebase_cache
                for part in path_parts_local:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[encoded_index] = str(msg_id)
                logger.info(f"✅ [CACHE] Обновлен локальный кэш: path={path_parts_local}, msg_id={msg_id}")

        logger.info(f"✅ Saved to playlist cache for hash={url_hash}, quality={quality_key}, indices={video_indices}, message_ids={message_ids}")
        
        # Дополнительно кэшируем каждое видео отдельно по его уникальной ссылке
        if video_urls_dict and not clear:
            logger.info(f"🔍 [CACHE] Дополнительно кэшируем {len(video_urls_dict)} видео по их уникальным ссылкам")
            for video_index, video_url in video_urls_dict.items():
                if not video_url:
                    continue
                try:
                    # Извлекаем message_id для этого видео
                    if video_index in video_indices:
                        idx_pos = video_indices.index(video_index)
                        if idx_pos < len(message_ids):
                            video_msg_id = message_ids[idx_pos]
                            # Сохраняем видео отдельно по его уникальной ссылке
                            save_to_video_cache(video_url, quality_key, [video_msg_id], clear=False, original_text=None, user_id=None)
                            logger.info(f"✅ [CACHE] Сохранено отдельное видео: index={video_index}, url={video_url}, msg_id={video_msg_id}")
                except Exception as e:
                    logger.warning(f"⚠️ [CACHE] Не удалось сохранить отдельное видео для index={video_index}, url={video_url}: {e}")
        
        # Синхронизируем локальный кэш с файлом при USE_FIREBASE=False
        use_firebase = getattr(Config, 'USE_FIREBASE', True)
        if not use_firebase:
            _sync_local_cache_to_file()

    except Exception as e:
        logger.error(f"Failed to save to playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        

def get_cached_playlist_videos(playlist_url: str, quality_key: str, requested_indices: list) -> dict:
    messages = safe_get_messages(None)
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    logger.info(
        f"get_cached_playlist_videos called: playlist_url={playlist_url}, quality_key={quality_key}, requested_indices={requested_indices}")
    if not quality_key:
        logger.warning(f"get_cached_playlist_videos: quality_key is empty for playlist: {playlist_url}")
        return {}
    try:
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))))
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))))
        quality_keys = [quality_key]
        try:
            if quality_key.endswith('p'):
                h = int(quality_key[:-1])
                rounded = f"{ceil_to_popular(h)}p"
                if rounded != quality_key:
                    quality_keys.append(rounded)
        except Exception:
            pass
        found = {}
        logger.info(f"get_cached_playlist_videos: checking URLs: {urls}")
        logger.info(f"get_cached_playlist_videos: checking quality keys: {quality_keys}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"get_cached_playlist_videos: checking URL hash: {url_hash}")
            for qk in quality_keys:
                logger.info(f"get_cached_playlist_videos: checking quality: {qk}")

                # A new way for searching in Dump!
                data = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if isinstance(data, dict):
                    for index in requested_indices:
                        try:
                            encoded_index = encode_playlist_cache_index(index)
                            value = data.get(encoded_index)
                            if value:
                                found[index] = int(value)
                                logger.info(
                                    f"get_cached_playlist_videos: found cached video for index {index} (quality={qk}): {value}")
                        except Exception as e:
                            logger.error(
                                f"get_cached_playlist_videos: error reading dict cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                            continue
                elif isinstance(data, list):
                    for index in requested_indices:
                        try:
                            if isinstance(index, int) and index >= 0 and index < len(data) and data[index]:
                                found[index] = int(data[index])
                                logger.info(
                                    f"get_cached_playlist_videos: found cached video for index {index} (quality={qk}): {data[index]}")
                        except Exception as e:
                            logger.error(
                                f"get_cached_playlist_videos: error reading list cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                            continue
                if found:
                    logger.info(
                        f"get_cached_playlist_videos: returning cached videos for indices {list(found.keys())}: {found}")
                    return found

        logger.info(safe_get_messages().DB_GET_CACHED_PLAYLIST_VIDEOS_NO_CACHE_MSG)
        return {}
    except Exception as e:
        logger.error(f"Failed to get from playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


def get_cached_playlist_qualities(playlist_url: str) -> set:
    """Gets all available qualities for a cached playlist."""
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    try:
        # Нормализуем URL так же, как при сохранении (без диапазона) и формируем все варианты ссылок
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.extend([
                normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))),
                normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))),
            ])
        
        # Проверяем все варианты URL и собираем все качества
        all_qualities = set()
        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"get_cached_playlist_qualities: checking hash {url_hash} for URL: {u}")
            
            # Проверяем локальный кэш
            data = get_from_local_cache(["bot", "video_cache", "playlists", url_hash])
            if data and isinstance(data, dict):
                qualities = set(data.keys())
                all_qualities.update(qualities)
                logger.info(f"get_cached_playlist_qualities: found qualities {qualities} for hash {url_hash} (local cache)")
            else:
                # Если в локальном кэше нет, проверяем Firebase напрямую (если используется)
                use_firebase = getattr(Config, 'USE_FIREBASE', True)
                if use_firebase:
                    try:
                        # Пытаемся получить данные из Firebase напрямую
                        firebase_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}"
                        firebase_data = db.child(firebase_path).get()
                        if firebase_data and isinstance(firebase_data.val(), dict):
                            qualities = set(firebase_data.val().keys())
                            all_qualities.update(qualities)
                            logger.info(f"get_cached_playlist_qualities: found qualities {qualities} for hash {url_hash} (Firebase)")
                            # Обновляем локальный кэш для будущих обращений
                            if "bot" not in firebase_cache:
                                firebase_cache["bot"] = {}
                            if "video_cache" not in firebase_cache["bot"]:
                                firebase_cache["bot"]["video_cache"] = {}
                            if "playlists" not in firebase_cache["bot"]["video_cache"]:
                                firebase_cache["bot"]["video_cache"]["playlists"] = {}
                            firebase_cache["bot"]["video_cache"]["playlists"][url_hash] = firebase_data.val()
                    except Exception as e:
                        logger.warning(f"get_cached_playlist_qualities: error checking Firebase for hash {url_hash}: {e}")
        
        if all_qualities:
            logger.info(f"get_cached_playlist_qualities: returning {all_qualities} for playlist: {playlist_url}")
        else:
            logger.info(f"get_cached_playlist_qualities: no cached qualities found for playlist: {playlist_url}")
        return all_qualities
    except Exception as e:
        logger.error(f"Failed to get cached playlist qualities: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return set()


def is_any_playlist_index_cached(playlist_url, quality_key, indices):
    """Checks if at least one index from the range is in the playlist cache."""
    cached = get_cached_playlist_videos(playlist_url, quality_key, indices)
    return bool(cached)

def get_cached_qualities(url: str) -> set:
    """He gets all the castle qualities for the URL."""
    from URL_PARSERS.normalizer import normalize_url_for_cache
    try:
        url_hash = get_url_hash(normalize_url_for_cache(url))
        
        # We use local cache instead of Firebase
        path_parts = ["bot", "video_cache", url_hash]
        data = get_from_local_cache(path_parts)
        
        if data and isinstance(data, dict):
            return set(data.keys())
        return set()
    except Exception as e:
        logger.error(f"Failed to get cached qualities: {e}")
        return set()

# --- Quickly get the number of cached videos for quality ---
def get_cached_playlist_count(playlist_url: str, quality_key: str, indices: list = None) -> int:
    """
    Returns the number of cached videos for the given quality (based on the number of keys in the database),
    considering and rounded quality_key (ceil_to_popular).
    If a list of indices is passed, it only counts their intersection with the cache.
    For large ranges (>100), it uses a fast count.
    """
    messages = safe_get_messages(None)
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    try:
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))))
            urls.append(normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))))
        quality_keys = [quality_key]
        try:
            if quality_key.endswith('p'):
                h = int(quality_key[:-1])
                rounded = f"{ceil_to_popular(h)}p"
                if rounded != quality_key:
                    quality_keys.append(rounded)
        except Exception:
            pass

        cached_count = 0
        for u in set(urls):
            url_hash = get_url_hash(u)
            for qk in quality_keys:
                data = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if data is None:
                    continue
                if indices is not None:
                    target_indices = indices
                    if isinstance(data, dict):
                        if len(target_indices) > 100:
                            try:
                                cached_count = sum(
                                    1 for index in target_indices
                                    if data.get(encode_playlist_cache_index(index)) is not None
                                )
                                logger.info(safe_get_messages().DB_GET_CACHED_PLAYLIST_COUNT_FAST_COUNT_MSG.format(cached_count=cached_count))
                                return cached_count
                            except Exception as e:
                                logger.error(f"get_cached_playlist_count: error in dict fast count: {e}")
                                continue
                        else:
                            for index in target_indices:
                                try:
                                    if data.get(encode_playlist_cache_index(index)) is not None:
                                        cached_count += 1
                                        logger.info(
                                            f"get_cached_playlist_count: found cached video for index {index} (quality={qk})")
                                except Exception as e:
                                    logger.error(
                                        f"get_cached_playlist_count: error reading dict cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                                    continue
                    elif isinstance(data, list):
                        if len(target_indices) > 100:
                            try:
                                cached_count = sum(
                                    1 for index in target_indices
                                    if isinstance(index, int) and index >= 0 and index < len(data) and data[index] is not None
                                )
                                logger.info(safe_get_messages().DB_GET_CACHED_PLAYLIST_COUNT_FAST_COUNT_MSG.format(cached_count=cached_count))
                                return cached_count
                            except Exception as e:
                                logger.error(f"get_cached_playlist_count: error in list fast count: {e}")
                                continue
                        else:
                            for index in target_indices:
                                try:
                                    if isinstance(index, int) and index >= 0 and index < len(data) and data[index] is not None:
                                        cached_count += 1
                                        logger.info(
                                            f"get_cached_playlist_count: found cached video for index {index} (quality={qk}): {data[index]}")
                                except Exception as e:
                                    logger.error(
                                        f"get_cached_playlist_count: error reading list cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                                    continue
                else:
                    # Count all non-empty records
                    try:
                        if isinstance(data, dict):
                            cached_count = sum(1 for item in data.values() if item is not None)
                        elif isinstance(data, list):
                            cached_count = sum(1 for item in data if item is not None)
                        else:
                            cached_count = 0
                    except Exception as e:
                        logger.error(
                            f"get_cached_playlist_count: error reading cache for url_hash={url_hash}, quality={qk}: {e}")
                        continue

                if cached_count and cached_count > 0:
                    logger.info(f"get_cached_playlist_count: returning {cached_count} cached videos for quality {qk}")
                    return cached_count

        logger.info(f"get_cached_playlist_count: no cached videos found, returning 0")
        return 0
    except Exception as e:
        logger.error(f"get_cached_playlist_count error: {e}")
        return 0

# --- new functions for caching ---
def get_url_hash(url: str) -> str:
    """Returns a hash of the URL for use as a cache key."""
    import hashlib
    hash_result = hashlib.md5(url.encode()).hexdigest()
    logger.info(f"get_url_hash: '{url}' -> '{hash_result}'")
    return hashlib.md5(url.encode()).hexdigest()

def _split_path_to_parts(path: str) -> list:
    try:
        return [p for p in str(path).strip('/').split('/') if p]
    except Exception:
        return ["bot", "image_cache"]

def save_to_image_cache(url: str, post_index: int, message_ids: list):
    """Save sent album (post) message IDs for an image URL into cache.
    Stored under local cache path: bot -> image_cache -> url_hash -> str(post_index) -> comma-separated ids
    And mirrored to Firebase using db_child_by_path when available.
    """
    global firebase_cache
    from URL_PARSERS.normalizer import normalize_url_for_cache
    try:
        logger.info(f"[IMG CACHE] save_to_image_cache called: url={url}, post_index={post_index}, message_ids={message_ids}")
        if not url or not message_ids or post_index is None:
            logger.warning("[IMG CACHE] save_to_image_cache skipped: empty args")
            return
        u = normalize_url_for_cache(url)
        url_hash = get_url_hash(u)
        # Avoid duplicate write if already present in local cache (use config path)
        image_root = getattr(Config, 'IMAGE_CACHE_DB_PATH', 'bot/video_cache/images')
        root_parts = _split_path_to_parts(image_root)
        local_path_parts = root_parts + [url_hash, str(int(post_index))]
        existing = get_from_local_cache(local_path_parts)
        if existing:
            logger.info(f"[IMG CACHE] Skip save: already exists in local cache: {'/'.join(local_path_parts)}")
            return
        ids_string = ",".join(map(str, message_ids))
        # Write to Firebase dump path (1:1 style with save_to_video_cache)
        try:
            # parent path without index, then child(index)
            path_parts = [*root_parts, url_hash]
            path_dbg_parent = "/".join(path_parts)
            logger.info(f"[IMG CACHE] Writing parent path: {path_dbg_parent}; index={post_index}; ids={ids_string}")
            cache_ref = db.child(*path_parts)
            try:
                cache_ref.child(str(int(post_index))).set(ids_string)
            except Exception as inner:
                logger.error(f"[IMG CACHE] Primary write failed ({path_dbg_parent}): {inner}")
                # Fallback to db_child_by_path to mimic other modules exactly
                try:
                    db_child_by_path(db, f"{image_root}/{url_hash}/{int(post_index)}").set(ids_string)
                    logger.info(f"[IMG CACHE] Fallback write via db_child_by_path succeeded: {image_root}/{url_hash}/{int(post_index)}")
                except Exception as inner2:
                    logger.error(f"[IMG CACHE] Fallback write failed: {inner2}")
            logger.info(f"[IMG CACHE] Saved album to cache: {path_dbg_parent}/{int(post_index)}")
            
            # Обновляем локальный кэш для немедленного доступа
            use_firebase = getattr(Config, 'USE_FIREBASE', True)
            if not use_firebase:
                current = firebase_cache
                for part in local_path_parts[:-1]:  # Все кроме последнего (post_index)
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[local_path_parts[-1]] = ids_string
                _sync_local_cache_to_file()
            
            # Optional verification
            try:
                val = cache_ref.child(str(int(post_index))).get().val()
                logger.info(f"[IMG CACHE] Verify read: {path_dbg_parent}/{int(post_index)} -> {val}")
            except Exception as ve:
                logger.warning(f"[IMG CACHE] Verify read failed (child-chain): {ve}")
                try:
                    val = db_child_by_path(db, f"{image_root}/{url_hash}/{int(post_index)}").get().val()
                    logger.info(f"[IMG CACHE] Verify read (fallback): {image_root}/{url_hash}/{int(post_index)} -> {val}")
                except Exception as ve2:
                    logger.warning(f"[IMG CACHE] Verify read fallback failed: {ve2}")
        except Exception as we:
            logger.error(f"[IMG CACHE] Write error: {we}")
    except Exception as e:
        logger.error(f"[IMG CACHE] Failed to save image cache: {e}")

def get_cached_image_posts(url: str, requested_indices: list | None = None) -> dict:
    """Return dict {post_index: [msg_ids]} for cached image posts for URL.
    If requested_indices is provided, only return intersection.
    """
    from URL_PARSERS.normalizer import normalize_url_for_cache
    try:
        u = normalize_url_for_cache(url)
        url_hash = get_url_hash(u)
        image_root = getattr(Config, 'IMAGE_CACHE_DB_PATH', 'bot/video_cache/images')
        root_parts = _split_path_to_parts(image_root)
        base = get_from_local_cache(root_parts + [url_hash])
        result = {}
        # Dict layout: {"1": "id,id,..."}
        if isinstance(base, dict):
            for k, v in base.items():
                try:
                    idx = int(k)
                except Exception:
                    continue
                if requested_indices is not None and idx not in requested_indices:
                    continue
                if isinstance(v, list):
                    ids = [int(x) for x in v if x]
                elif isinstance(v, str):
                    ids = [int(x) for x in v.split(',') if x]
                else:
                    continue
                if ids:
                    result[idx] = ids
            return result
        # List layout: [None, "id,id,...", ...] or ["id,id,...", ...]
        if isinstance(base, list):
            start_from_one = False
            try:
                start_from_one = (len(base) > 1 and (base[0] is None or base[0] in ("", [])))
            except Exception:
                start_from_one = False
            for i, v in enumerate(base):
                idx = i if not start_from_one else i
                if start_from_one:
                    # Skip index 0 placeholder
                    if i == 0:
                        continue
                    idx = i  # already 1-based positions
                else:
                    # convert to 1-based index for consistency
                    idx = i + 1
                if requested_indices is not None and idx not in requested_indices:
                    continue
                if not v:
                    continue
                if isinstance(v, list):
                    ids = [int(x) for x in v if x]
                elif isinstance(v, str):
                    ids = [int(x) for x in v.split(',') if x]
                else:
                    continue
                if ids:
                    result[idx] = ids
            return result
        return {}
    except Exception as e:
        logger.error(f"Failed to get cached image posts: {e}")
        return {}

def get_cached_image_post_indices(url: str) -> set:
    """Return set of cached post indices for image URL."""
    from URL_PARSERS.normalizer import normalize_url_for_cache
    try:
        u = normalize_url_for_cache(url)
        url_hash = get_url_hash(u)
        image_root = getattr(Config, 'IMAGE_CACHE_DB_PATH', 'bot/video_cache/images')
        root_parts = _split_path_to_parts(image_root)
        base = get_from_local_cache(root_parts + [url_hash])
        indices = set()
        if isinstance(base, dict):
            for k in base.keys():
                try:
                    indices.add(int(k))
                except Exception:
                    continue
            return indices
        if isinstance(base, list):
            if len(base) == 0:
                return set()
            start_from_one = False
            try:
                start_from_one = (len(base) > 1 and (base[0] is None or base[0] in ("", [])))
            except Exception:
                start_from_one = False
            for i, v in enumerate(base):
                if not v:
                    continue
                if start_from_one:
                    if i == 0:
                        continue
                    indices.add(i)
                else:
                    indices.add(i + 1)
            return indices
        return set()
    except Exception as e:
        logger.error(f"Failed to get cached image indices: {e}")
        return set()

def save_to_video_cache(url: str, quality_key: str, message_ids: list, clear: bool = False, original_text: str = None, user_id: int = None):
    """Saves message IDs to Firebase video cache after checking local cache to avoid duplication."""
    global firebase_cache
    from URL_PARSERS.normalizer import normalize_url_for_cache
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    from URL_PARSERS.playlist_utils import is_playlist_with_range
    found_type = None
    if user_id is not None:
        # Lazy import to avoid circular imports at module level
        try:
            from COMMANDS.subtitles_cmd import (
                check_subs_availability,
                is_subs_enabled,
                get_user_subs_auto_mode,
                is_subs_always_ask,
            )
        except Exception:
            check_subs_availability = None
            is_subs_enabled = lambda _uid: False
            get_user_subs_auto_mode = lambda _uid: False

        # Always save to cache regardless of subtitles or Always Ask mode
        # The cache will be used for display purposes (rocket emoji) but not for reposting
        # Only skip caching if user has send_as_file enabled (handled in _save_video_cache_with_logging)

    logger.info(f"save_to_video_cache called: url={url}, quality_key={quality_key}, message_ids={message_ids}, clear={clear}, original_text={original_text}")

    if not quality_key:
        logger.warning(f"save_to_video_cache: quality_key is empty, skipping cache save for URL: {url}")
        return

    if original_text and is_playlist_with_range(original_text):
        logger.info(f"Playlist with range detected, skipping cache save for URL: {url}")
        return

    try:
        urls = [normalize_url_for_cache(url)]
        if is_youtube_url(url):
            urls += [
                normalize_url_for_cache(youtube_to_short_url(url)),
                normalize_url_for_cache(youtube_to_long_url(url))
            ]
        
        logger.info(f"save_to_video_cache: normalized URLs: {urls}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            path_parts_local = ["bot", "video_cache", "playlists", url_hash]
            path_parts = [Config.VIDEO_CACHE_DB_PATH, url_hash]
            
            # === CLEAR MODE ===
            if clear:
                logger.info(f"Clearing cache for URL hash {url_hash}, quality {quality_key}")
                db.child(*path_parts).child(quality_key).remove()
                # Обновляем локальный кэш
                use_firebase = getattr(Config, 'USE_FIREBASE', True)
                if not use_firebase:
                    current = firebase_cache
                    for part in ["bot", "video_cache", url_hash]:
                        if part in current and isinstance(current[part], dict):
                            current = current[part]
                        else:
                            break
                    else:
                        if quality_key in current:
                            del current[quality_key]
                            _sync_local_cache_to_file()
                continue

            if not message_ids:
                logger.warning(f"save_to_video_cache: message_ids is empty for URL: {url}, quality: {quality_key}")
                continue

            # === LOCAL CACHE CHECK ===
            # Note: We now allow overwriting existing cache to ensure consistency
            existing = get_from_local_cache(path_parts_local + [quality_key])
            if existing is not None:
                logger.info(f"Cache already exists for URL hash {url_hash}, quality {quality_key}, but will update with new message_ids.")

            cache_ref = db.child(*path_parts)

            if len(message_ids) == 1:
                cache_ref.child(quality_key).set(str(message_ids[0]))
                logger.info(f"Saved single video to cache: hash={url_hash}, quality={quality_key}, msg_id={message_ids[0]}")
                # Обновляем локальный кэш
                use_firebase = getattr(Config, 'USE_FIREBASE', True)
                if not use_firebase:
                    current = firebase_cache
                    for part in ["bot", "video_cache", url_hash]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[quality_key] = str(message_ids[0])
            else:
                ids_string = ",".join(map(str, message_ids))
                cache_ref.child(quality_key).set(ids_string)
                logger.info(f"Saved split video to cache: hash={url_hash}, quality={quality_key}, msg_ids={ids_string}")
                # Обновляем локальный кэш
                use_firebase = getattr(Config, 'USE_FIREBASE', True)
                if not use_firebase:
                    current = firebase_cache
                    for part in ["bot", "video_cache", url_hash]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[quality_key] = ids_string
            
            # Синхронизируем локальный кэш с файлом при USE_FIREBASE=False
            use_firebase = getattr(Config, 'USE_FIREBASE', True)
            if not use_firebase:
                _sync_local_cache_to_file()

    except Exception as e:
        logger.error(f"Failed to save to video cache: {e}")
        

def get_cached_message_ids(url: str, quality_key: str) -> list:
    """Searches cache for both versions of YouTube link (long/short)."""
    messages = safe_get_messages(None)
    from URL_PARSERS.normalizer import normalize_url_for_cache
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    logger.info(f"get_cached_message_ids called: url={url}, quality_key={quality_key}")
    if not quality_key:
        logger.warning(f"get_cached_message_ids: quality_key is empty for URL: {url}")
        return None
    try:
        urls = [normalize_url_for_cache(url)]
        if is_youtube_url(url):
            short_url = youtube_to_short_url(url)
            long_url = youtube_to_long_url(url)
            urls.append(normalize_url_for_cache(short_url))
            urls.append(normalize_url_for_cache(long_url))
            logger.info(f"get_cached_message_ids: original={url}, short={short_url}, long={long_url}")
        logger.info(f"get_cached_message_ids: checking URLs: {urls}")
        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"get_cached_message_ids: checking hash {url_hash} for quality {quality_key}")
            
            # We use local cache instead of Firebase
            path_parts = ["bot", "video_cache", url_hash, quality_key]
            ids_string = get_from_local_cache(path_parts)
            
            logger.info(f"get_cached_message_ids: raw value from local cache: {ids_string} (type: {type(ids_string)})")
            if ids_string:
                result = [int(msg_id) for msg_id in ids_string.split(',')]
                logger.info(
                    f"get_cached_message_ids: found cached message_ids {result} for URL: {url}, quality: {quality_key}")
                return result
            else:
                logger.info(safe_get_messages().DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_MSG.format(url_hash=url_hash, quality_key=quality_key))
        logger.info(safe_get_messages().DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_ANY_VARIANT_MSG)
        return None
    except Exception as e:
        logger.error(f"Failed to get from cache: {e}")
        return None
