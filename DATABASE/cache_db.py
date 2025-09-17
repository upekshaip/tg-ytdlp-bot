import os
import json
import time
import threading
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from CONFIG.config import Config
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
        logger.info(f"Firebase local-cache access: {path_str} -> {status}")
    except Exception:
        # Fallback to stdout if logger is not usable for any reason during early init
        print(f"Firebase local-cache access: {path_str} -> {status}")

def load_firebase_cache():
    """Load local Firebase cache from JSON file."""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            print(f"✅ Firebase cache loaded: {len(firebase_cache)} root nodes")
        else:
            print(f"⚠️ Firebase cache file not found, starting with empty cache: {cache_file}")
            firebase_cache = {}
    except Exception as e:
        print(f"❌ Failed to load firebase cache: {e}")
        firebase_cache = {}

def reload_firebase_cache():
    """Reloading the local Firebase cache from JSON file"""
    global firebase_cache
    try:
        cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                firebase_cache = json.load(f)
            print(f"✅ Firebase cache reloaded: {len(firebase_cache)} root nodes")
            return True
        else:
            print(f"⚠️ Firebase cache file not found: {cache_file}")
            return False
    except Exception as e:
        print(f"❌ Failed to reload firebase cache: {e}")
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
    try:
        ok = download_firebase_dump()
        if not ok:
            print("❌ Failed to download Firebase dump via REST")
            return False
        return reload_firebase_cache()
    except Exception as e:
        print(f"❌ Error in _download_and_reload_cache: {e}")
        return False

def auto_reload_firebase_cache():
    """Background thread that reloads local cache every N hours by downloading dump first."""
    global auto_cache_enabled

    while auto_cache_enabled:
        interval_hours_local = max(1, int(reload_interval_hours))
        next_exec = get_next_reload_time(interval_hours_local)
        now = datetime.now()
        wait_seconds = (next_exec - now).total_seconds()
        if wait_seconds < 0:
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
                print(f"❌ Error running auto reload_cache (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("❌ All retry attempts failed")
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
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CONFIG', 'config.py')
        if not os.path.exists(cfg_path):
            logger.warning(f"config.py not found at {cfg_path}")
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
        logger.info(f"RELOAD_CACHE_EVERY persisted to config.py: {int(new_hours)}h")
        return True
    except Exception as e:
        logger.error(f"Failed to persist RELOAD_CACHE_EVERY to config.py: {e}")
        return False

def set_reload_interval_hours(new_hours: int) -> bool:
    """Set a new reload interval in hours (1..168). Restarts the reloader if needed and persists to config.py."""
    global reload_interval_hours
    try:
        new_val = int(new_hours)
    except Exception:
        return False
    if new_val < 1 or new_val > 168:
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
    """Command handler to control automatic Firebase cache loading.

    Supports:
      /auto_cache on
      /auto_cache off
      /auto_cache N   (N in 1..168 hours)
    """
    try:
        if int(message.chat.id) not in Config.ADMIN:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.ACCESS_DENIED_ADMIN_MSG)
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
                from CONFIG.messages import MessagesConfig as Messages
                send_to_user(
                    message,
                    Messages.CACHE_AUTO_RELOAD_UPDATED_MSG.format(
                        status=status,
                        interval=interval,
                        next_time=next_exec.strftime('%H:%M'),
                        delta_min=delta_min
                    )
                )
                send_to_logger(message, f"Auto reload ENABLED; next at {next_exec}")
            else:
                from CONFIG.messages import MessagesConfig as Messages
                send_to_user(
                    message,
                    Messages.CACHE_AUTO_RELOAD_STOPPED_MSG
                )
                send_to_logger(message, "Auto reload DISABLED by admin.")
            return

        # Try numeric interval
        if arg is not None:
            try:
                n = int(arg)
            except Exception:
                from CONFIG.messages import MessagesConfig as Messages
                send_to_user(message, getattr(Messages, 'AUTO_CACHE_INVALID_ARG_MSG', "❌ Invalid argument. Use /auto_cache on | off | N (1..168)"))
                return
            if n < 1 or n > 168:
                from CONFIG.messages import MessagesConfig as Messages
                send_to_user(message, getattr(Messages, 'AUTO_CACHE_INTERVAL_RANGE_MSG', "❌ Interval must be between 1 and 168 hours"))
                return
            ok = set_reload_interval_hours(n)
            if not ok:
                from CONFIG.messages import MessagesConfig as Messages
                send_to_user(message, getattr(Messages, 'AUTO_CACHE_SET_FAILED_MSG', "❌ Failed to set interval"))
                return
            interval = max(1, int(reload_interval_hours))
            next_exec = get_next_reload_time(interval)
            delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(
                message,
                Messages.AUTO_CACHE_UPDATED_MSG.format(
                    status='✅ ENABLED' if auto_cache_enabled else '❌ DISABLED',
                    interval=interval,
                    next_time=next_exec.strftime('%H:%M'),
                    delta_min=delta_min
                )
            )
            send_to_logger(message, f"Auto reload interval set to {interval}h; next at {next_exec}")
            return

        # No args: toggle legacy behavior
        new_state = toggle_auto_cache_reloader()
        interval = max(1, int(reload_interval_hours))
        if new_state:
            next_exec = get_next_reload_time(interval)
            delta_min = int((next_exec - datetime.now()).total_seconds() // 60)
            send_to_user(
                message,
                "🔄 Auto Firebase cache reloading started!\n\n"
                f"📊 Status: ✅ ENABLED\n"
                f"⏰ Schedule: every {interval} hours from 00:00\n"
                f"🕒 Next reload: {next_exec.strftime('%H:%M')} (in {delta_min} minutes)"
            )
            send_to_logger(message, f"Auto reload started; next at {next_exec}")
        else:
            send_to_user(
                message,
                "🛑 Auto Firebase cache reloading stopped!\n\n"
                "📊 Status: ❌ DISABLED\n"
                "💡 Use /auto_cache on to re-enable"
            )
            send_to_logger(message, "Auto reload stopped by admin.")
    except Exception as e:
        logger.error(f"/auto_cache handler error: {e}")


# Added playlist caching - separate functions for saving and retrieving playlist cache
def save_to_playlist_cache(playlist_url: str, quality_key: str, video_indices: list, message_ids: list,
                           clear: bool = False, original_text: str = None):
    # Lazy imports to avoid circular imports
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
    logger.info(
        f"save_to_playlist_cache called: playlist_url={playlist_url}, quality_key={quality_key}, video_indices={video_indices}, message_ids={message_ids}, clear={clear}")
    
    if not quality_key:
        logger.warning(f"quality_key is empty, skipping cache save for playlist: {playlist_url}")
        return

    if not hasattr(Config, 'PLAYLIST_CACHE_DB_PATH') or not Config.PLAYLIST_CACHE_DB_PATH or Config.PLAYLIST_CACHE_DB_PATH.strip() in ('', '/', '.'):
        logger.error(f"PLAYLIST_CACHE_DB_PATH is invalid, skipping write for: {playlist_url}")
        return

    try:
        # Normalize the URL (without the range) and form all link options
        urls = [normalize_url_for_cache(strip_range_from_url(playlist_url))]
        if is_youtube_url(playlist_url):
            urls.extend([
                normalize_url_for_cache(strip_range_from_url(youtube_to_short_url(playlist_url))),
                normalize_url_for_cache(strip_range_from_url(youtube_to_long_url(playlist_url))),
            ])
        logger.info(f"Normalized playlist URLs: {urls}")

        for u in set(urls):
            url_hash = get_url_hash(u)
            logger.info(f"Using playlist URL hash: {url_hash}")

            if clear:
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{url_hash}/{quality_key}").remove()
                logger.info(f"Cleared playlist cache for hash={url_hash}, quality={quality_key}")
                continue

            if not message_ids or not video_indices:
                logger.warning(f"message_ids or video_indices is empty for playlist: {playlist_url}, quality: {quality_key}")
                continue

            for i, msg_id in zip(video_indices, message_ids):
                
                path_parts_local = ["bot", "video_cache", "playlists", url_hash, quality_key, str(i)]
                path_parts = [Config.PLAYLIST_CACHE_DB_PATH, url_hash, quality_key, str(i)]
                already_cached = get_from_local_cache(path_parts_local)

                if already_cached:
                    logger.info(f"Playlist part already cached: {path_parts_local}, skipping")
                    continue

                db_child_by_path(db, "/".join(path_parts)).set(str(msg_id))
                logger.info(f"Saved to playlist cache: path={path_parts}, msg_id={msg_id}")

        logger.info(f"✅ Saved to playlist cache for hash={url_hash}, quality={quality_key}, indices={video_indices}, message_ids={message_ids}")

    except Exception as e:
        logger.error(f"Failed to save to playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        

def get_cached_playlist_videos(playlist_url: str, quality_key: str, requested_indices: list) -> dict:
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
                arr = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if isinstance(arr, list):
                    for index in requested_indices:
                        try:
                            if index < len(arr) and arr[index]:
                                found[index] = int(arr[index])
                                logger.info(
                                    f"get_cached_playlist_videos: found cached video for index {index} (quality={qk}): {arr[index]}")
                        except Exception as e:
                            logger.error(
                                f"get_cached_playlist_videos: error reading cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                            continue
                    if found:
                        logger.info(
                            f"get_cached_playlist_videos: returning cached videos for indices {list(found.keys())}: {found}")
                        return found

        logger.info(f"get_cached_playlist_videos: no cache found for any URL/quality variant, returning empty dict")
        return {}
    except Exception as e:
        logger.error(f"Failed to get from playlist cache: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


def get_cached_playlist_qualities(playlist_url: str) -> set:
    """Gets all available qualities for a cached playlist."""
    from URL_PARSERS.normalizer import normalize_url_for_cache, strip_range_from_url
    try:
        url_hash = get_url_hash(normalize_url_for_cache(strip_range_from_url(playlist_url)))
        data = get_from_local_cache(["bot", "video_cache", "playlists", url_hash])
        if data and isinstance(data, dict):
            return set(data.keys())
        return set()
    except Exception as e:
        logger.error(f"Failed to get cached playlist qualities: {e}")
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
                arr = get_from_local_cache(["bot", "video_cache", "playlists", url_hash, qk])
                if not isinstance(arr, list):
                    continue
                if indices is not None:
                    # For large ranges, we use a fast count
                    if len(indices) > 100:
                        try:
                            cached_count = sum(1 for index in indices if index < len(arr) and arr[index] is not None)
                            logger.info(
                                f"get_cached_playlist_count: fast count for large range: {cached_count} cached videos")
                            return cached_count
                        except Exception as e:
                            logger.error(f"get_cached_playlist_count: error in fast count: {e}")
                            continue
                    else:
                        # For small ranges, check each index separately
                        for index in indices:
                            try:
                                if index < len(arr) and arr[index] is not None:
                                    cached_count += 1
                                    logger.info(
                                        f"get_cached_playlist_count: found cached video for index {index} (quality={qk}): {arr[index]}")
                            except Exception as e:
                                logger.error(
                                    f"get_cached_playlist_count: error reading cache for url_hash={url_hash}, quality={qk}, index={index}: {e}")
                                continue
                else:
                    # Count all non-empty records
                    try:
                        cached_count = sum(1 for item in arr if item is not None)
                    except Exception as e:
                        logger.error(
                            f"get_cached_playlist_count: error reading cache for url_hash={url_hash}, quality={qk}: {e}")
                        continue

                if cached_count > 0:
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
            logger.info(f"[IMG CACHE] Saved album to Firebase: {path_dbg_parent}/{int(post_index)}")
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

        found_type = check_subs_availability(url, user_id, quality_key, return_type=True) if check_subs_availability else None
        subs_enabled = is_subs_enabled(user_id) if callable(is_subs_enabled) else False
        auto_mode = get_user_subs_auto_mode(user_id) if callable(get_user_subs_auto_mode) else False
        need_subs = (subs_enabled and ((auto_mode and found_type == "auto") or (not auto_mode and found_type == "normal")))
        always_ask_mode = is_subs_always_ask(user_id) if callable(is_subs_always_ask) else False
        if need_subs or always_ask_mode:
            if always_ask_mode:
                logger.info("Video with Always Ask mode enabled is not cached!")
            else:
                logger.info("Video with subtitles is not cached!")
            return

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
                continue

            if not message_ids:
                logger.warning(f"save_to_video_cache: message_ids is empty for URL: {url}, quality: {quality_key}")
                continue

            # === LOCAL CACHE CHECK ===
            existing = get_from_local_cache(path_parts_local + [quality_key])
            if existing is not None:
                logger.info(f"Cache already exists for URL hash {url_hash}, quality {quality_key}, skipping save.")
                continue  # skip writing if already cached locally

            cache_ref = db.child(*path_parts)

            if len(message_ids) == 1:
                cache_ref.child(quality_key).set(str(message_ids[0]))
                logger.info(f"Saved single video to cache: hash={url_hash}, quality={quality_key}, msg_id={message_ids[0]}")
            else:
                ids_string = ",".join(map(str, message_ids))
                cache_ref.child(quality_key).set(ids_string)
                logger.info(f"Saved split video to cache: hash={url_hash}, quality={quality_key}, msg_ids={ids_string}")

    except Exception as e:
        logger.error(f"Failed to save to video cache: {e}")
        

def get_cached_message_ids(url: str, quality_key: str) -> list:
    """Searches cache for both versions of YouTube link (long/short)."""
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
                logger.info(f"get_cached_message_ids: no cache found for hash {url_hash}, quality {quality_key}")
        logger.info(f"get_cached_message_ids: no cache found for any URL variant, returning None")
        return None
    except Exception as e:
        logger.error(f"Failed to get from cache: {e}")
        return None
