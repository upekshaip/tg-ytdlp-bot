from __future__ import annotations

import time
from typing import Dict, List, Any

from CONFIG.config import Config
from DATABASE.firebase_init import db
from HELPERS.channel_guard import get_channel_guard
from HELPERS.logger import logger
from services.stats_collector import get_stats_collector


def _db_node(suffix: str):
    base = getattr(Config, "BOT_DB_PATH", f"bot/{getattr(Config, 'BOT_NAME_FOR_USERS', 'tgytdlp_bot')}")
    base = base.rstrip("/")
    suffix = suffix.lstrip("/")
    path = f"{base}/{suffix}" if suffix else base
    return db.child(path)


def fetch_active_users(limit: int = 10, minutes: int | None = None) -> Dict[str, Any]:
    return get_stats_collector().get_active_users(limit=limit, minutes=minutes)


def fetch_top_downloaders(period: str, limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_downloaders(period, limit)


def fetch_top_domains(period: str, limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_domains(period, limit)


def fetch_top_countries(period: str, limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_countries(period, limit)


def fetch_gender_stats(period: str) -> List[Dict[str, Any]]:
    return get_stats_collector().get_gender_stats(period)


def fetch_age_stats(period: str) -> List[Dict[str, Any]]:
    return get_stats_collector().get_age_stats(period)


def fetch_top_nsfw_users(limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_nsfw_users(limit)


def fetch_top_nsfw_domains(limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_nsfw_domains(limit)


def fetch_top_playlist_users(limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_top_playlist_users(limit)


def fetch_power_users(min_urls: int = 10, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    return get_stats_collector().get_power_users(min_urls=min_urls, days=days, limit=limit)


def fetch_blocked_users(limit: int = 50) -> List[Dict[str, Any]]:
    return get_stats_collector().get_blocked_users(limit)


def fetch_user_history(user_id: int, period: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
    return get_stats_collector().get_user_history(user_id, period, limit)


def fetch_suspicious_users(period: str, limit: int = 20) -> List[Dict[str, Any]]:
    return get_stats_collector().get_suspicious_users(period, limit)


def _is_guard_ready(guard) -> bool:
    return bool(
        guard
        and getattr(guard, "_running", False)
        and getattr(guard, "_loop", None)
    )


def fetch_recent_channel_events(hours: int = 48, limit: int = 100) -> List[Dict[str, Any]]:
    guard = get_channel_guard()
    if _is_guard_ready(guard) and guard.can_read_admin_log():
        try:
            return guard.export_recent_activity(hours=hours, limit=limit)
        except Exception as exc:
            logger.debug(f"[stats-service] channel guard export failed: {exc}")
    return get_stats_collector().get_recent_channel_events(hours=hours, limit=limit)


def _blocked_users_node():
    return _db_node("blocked_users")


def _unblocked_users_node():
    return _db_node("unblocked_users")


def block_user(user_id: int, reason: str = "manual") -> None:
    ts = str(int(time.time()))
    payload = {"ID": str(user_id), "timestamp": ts, "blocked_reason": reason}
    _blocked_users_node().child(str(user_id)).set(payload)
    collector = get_stats_collector()
    collector.block_user_local(user_id, reason=reason)
    guard = get_channel_guard()
    if guard:
        guard.mark_user_blocked(user_id, reason)


def unblock_user(user_id: int) -> None:
    ts = str(int(time.time()))
    payload = {"ID": str(user_id), "timestamp": ts}
    _unblocked_users_node().child(str(user_id)).set(payload)
    _blocked_users_node().child(str(user_id)).remove()
    collector = get_stats_collector()
    collector.unblock_user_local(user_id)
    guard = get_channel_guard()
    if guard:
        guard.record_manual_unblock(user_id)

