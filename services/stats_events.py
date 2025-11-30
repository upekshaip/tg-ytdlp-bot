from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import logging

from services.stats_collector import get_stats_collector

logger = logging.getLogger(__name__)


@dataclass
class DBWriteEvent:
    path: str
    operation: str
    payload: Any
    timestamp: float = time.time()


def emit_db_event(path: str, operation: str, payload: Any) -> None:
    """Передаёт событие записи в агрегатор статистики."""
    try:
        collector = get_stats_collector()
        collector.handle_db_event(path, operation, payload)
    except Exception as exc:
        logger.debug(f"[stats] failed to handle db event {operation} {path}: {exc}")


def emit_download_event(
    *,
    user_id: int,
    url: str,
    title: str,
    timestamp: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Регистрирует скачивание с дополнительными метаданными."""
    try:
        collector = get_stats_collector()
        collector.record_download(
            user_id=user_id,
            url=url,
            title=title,
            timestamp=timestamp,
            metadata=metadata,
        )
    except Exception as exc:
        logger.debug(f"[stats] failed to record download event for {user_id}: {exc}")


def capture_message_context(message) -> None:
    """Сохраняет базовые сведения о пользователе из объекта сообщения Pyrogram."""
    try:
        user = getattr(message, "from_user", None) or getattr(message, "chat", None)
        if not user:
            return
        user_id = getattr(user, "id", None)
        if not user_id:
            return
        metadata = {
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "username": getattr(user, "username", None),
            "language_code": getattr(user, "language_code", None),
        }
        metadata = {k: v for k, v in metadata.items() if v}
        if not metadata:
            return
        get_stats_collector().update_user_metadata(int(user_id), metadata)
    except Exception as exc:
        logger.debug(f"[stats] failed to capture metadata: {exc}")


def update_download_progress(
    user_id: int,
    progress: float,
    url: Optional[str] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Обновляет прогресс загрузки для активной сессии пользователя."""
    try:
        collector = get_stats_collector()
        collector.update_download_progress(
            user_id=user_id,
            progress=progress,
            url=url,
            title=title,
            metadata=metadata,
        )
    except Exception as exc:
        logger.debug(f"[stats] failed to update download progress for {user_id}: {exc}")


class StatsAwareDBAdapter:
    """Обёртка над Firebase/локальным адаптером, которая перехватывает записи."""

    __slots__ = ("_adapter", "_path", "_lock")

    def __init__(self, adapter: Any, path: str = "/"):
        self._adapter = adapter
        self._path = path if path.startswith("/") else f"/{path}"
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    @staticmethod
    def _extend_path(base: str, parts: Sequence[Any]) -> str:
        path = base.rstrip("/") if base and base != "/" else ""
        for part in parts:
            segment = str(part).strip("/")
            if not segment:
                continue
            if not path:
                path = f"/{segment}"
            else:
                path = f"{path}/{segment}"
        return path or "/"

    def _emit(self, operation: str, payload: Any, path: Optional[str] = None) -> None:
        emit_db_event(path or self._path, operation, payload)

    # ------------------------------------------------------------------
    # Совместимость с Firebase API
    # ------------------------------------------------------------------

    def child(self, *path_parts: Any) -> "StatsAwareDBAdapter":
        child_adapter = self._adapter.child(*path_parts)
        new_path = self._extend_path(self._path, path_parts)
        return StatsAwareDBAdapter(child_adapter, new_path)

    def set(self, data: Any) -> Any:
        result = self._adapter.set(data)
        self._emit("set", data)
        return result

    def update(self, data: Dict[str, Any]) -> Any:
        result = self._adapter.update(data)
        self._emit("update", data)
        return result

    def remove(self) -> Any:
        result = self._adapter.remove()
        self._emit("remove", None)
        return result

    def push(self, data: Any) -> Any:
        result = self._adapter.push(data)
        key = None
        if hasattr(result, "key"):
            try:
                key = result.key()
            except TypeError:
                key = getattr(result, "key", None)
        if isinstance(result, dict):
            key = result.get("name") or result.get("key")
        if key:
            path = self._extend_path(self._path, [key])
        else:
            path = self._path
        self._emit("push", data, path)
        return result

    def get(self) -> Any:
        return self._adapter.get()

    def close(self) -> None:
        close_fn = getattr(self._adapter, "close", None)
        if callable(close_fn):
            close_fn()

    # ------------------------------------------------------------------
    # Проброс прочих атрибутов
    # ------------------------------------------------------------------

    def __getattr__(self, item: str) -> Any:
        return getattr(self._adapter, item)


def wrap_db_adapter(db_adapter: Any) -> StatsAwareDBAdapter:
    """Упаковывает текущий адаптер базы, чтобы перехватывать записи."""
    if isinstance(db_adapter, StatsAwareDBAdapter):
        return db_adapter
    return StatsAwareDBAdapter(db_adapter, "/")

