import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable, Union

from pyrogram.errors import RPCError
from pyrogram.raw.functions.channels import GetAdminLog
from pyrogram.raw.types import (
    ChannelAdminLogEventActionParticipantLeave,
    ChannelAdminLogEventsFilter,
)

from CONFIG.config import Config
from CONFIG.messages import safe_get_messages
from DATABASE.firebase_init import db
from HELPERS.logger import logger
from HELPERS.safe_messeger import safe_send_message

# --------------------------------------------------------------------------------------
# Duration helpers
# --------------------------------------------------------------------------------------

_DURATION_UNITS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
    "M": 60 * 60 * 24 * 30,
    "y": 60 * 60 * 24 * 365,
}


def parse_period_to_seconds(value: str) -> int:
    """Parse strings like '10s', '5m', '2h' into seconds."""
    if not value:
        raise ValueError("empty duration")
    text = value.strip()
    unit = text[-1]
    if unit not in _DURATION_UNITS:
        raise ValueError(f"unsupported unit '{unit}'")
    amount = text[:-1]
    if not amount.isdigit():
        raise ValueError("duration amount must be integer")
    seconds = int(amount) * _DURATION_UNITS[unit]
    if seconds <= 0:
        raise ValueError("duration must be positive")
    return seconds


def format_seconds_human(seconds: int) -> str:
    """Return a compact human-readable representation with canonical unit."""
    if seconds <= 0:
        return "0s"
    for unit, divisor in (
        ("y", _DURATION_UNITS["y"]),
        ("M", _DURATION_UNITS["M"]),
        ("w", _DURATION_UNITS["w"]),
        ("d", _DURATION_UNITS["d"]),
        ("h", _DURATION_UNITS["h"]),
        ("m", _DURATION_UNITS["m"]),
    ):
        if seconds % divisor == 0 and seconds >= divisor:
            return f"{seconds // divisor}{unit}"
    if seconds % _DURATION_UNITS["s"] == 0:
        return f"{seconds}s"
    return f"{seconds}s"


# --------------------------------------------------------------------------------------
# Channel guard core
# --------------------------------------------------------------------------------------


class ChannelGuard:
    def __init__(self) -> None:
        self._channel_id = getattr(Config, "SUBSCRIBE_CHANNEL", None)
        self._guard_root = (
            db.child("bot")
            .child(Config.BOT_NAME_FOR_USERS)
            .child("channel_guard")
        )
        self._settings = {
            "scan_interval": 300,
            "auto_enabled": False,
            "auto_interval": 0,
            "auto_window": 0,
        }
        self._last_event_id: int = 0
        self._leavers: Dict[str, Dict[str, Any]] = {}
        self._app = None
        self._loop = None
        self._scan_task: Optional[asyncio.Task] = None
        self._auto_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._running = False
        self._block_executor: Optional[Callable[[int, Optional[str]], None]] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize_from_db(self) -> None:
        """Load cached settings and leavers from the database."""
        try:
            settings_snapshot = self._guard_root.child("settings").get()
            if settings_snapshot and isinstance(settings_snapshot.val(), dict):
                self._settings.update(
                    {k: settings_snapshot.val().get(k, v) for k, v in self._settings.items()}
                )
            state_snapshot = self._guard_root.child("state").get()
            if state_snapshot and isinstance(state_snapshot.val(), dict):
                self._last_event_id = int(state_snapshot.val().get("last_event_id", 0))
            leavers_snapshot = self._guard_root.child("leavers").get()
            if leavers_snapshot and isinstance(leavers_snapshot.val(), dict):
                for uid, data in leavers_snapshot.val().items():
                    if isinstance(data, dict):
                        self._leavers[str(uid)] = data
        except Exception as exc:
            logger.error(f"[ChannelGuard] Failed to initialize DB state: {exc}")

    async def start(self, app) -> None:
        if self._running:
            return
        if not self._channel_id:
            logger.warning("[ChannelGuard] SUBSCRIBE_CHANNEL is not configured, guard disabled")
            return
        self._app = app
        self._loop = app.loop
        self.initialize_from_db()
        self._running = True
        self._scan_task = self._loop.create_task(self._scan_loop())
        self._auto_task = self._loop.create_task(self._auto_loop())
        logger.info("[ChannelGuard] Guard started")

    async def stop(self) -> None:
        self._running = False
        if self._scan_task:
            self._scan_task.cancel()
        if self._auto_task:
            self._auto_task.cancel()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_block_executor(self, callback: Callable[[int, Optional[str]], None]) -> None:
        self._block_executor = callback

    def set_scan_interval(self, seconds: int) -> None:
        self._settings["scan_interval"] = max(10, seconds)
        self._guard_root.child("settings").update({"scan_interval": self._settings["scan_interval"]})

    def set_auto_interval(self, seconds: int) -> None:
        self._settings["auto_interval"] = max(10, seconds)
        self._settings["auto_window"] = self._settings["auto_interval"]
        self._guard_root.child("settings").update(
            {
                "auto_interval": self._settings["auto_interval"],
                "auto_window": self._settings["auto_window"],
            }
        )

    def toggle_auto_mode(self) -> bool:
        self._settings["auto_enabled"] = not bool(self._settings.get("auto_enabled"))
        self._guard_root.child("settings").update({"auto_enabled": self._settings["auto_enabled"]})
        return self._settings["auto_enabled"]

    def set_auto_mode(self, enabled: bool) -> None:
        self._settings["auto_enabled"] = bool(enabled)
        self._guard_root.child("settings").update({"auto_enabled": self._settings["auto_enabled"]})

    def get_pending_leavers(self) -> List[Dict[str, Any]]:
        pending = [
            data
            for data in self._leavers.values()
            if not data.get("blocked")
        ]
        pending.sort(key=lambda item: int(item.get("last_left_ts", 0)))
        return pending

    def get_pending_ids(self) -> List[int]:
        return [int(item.get("ID")) for item in self.get_pending_leavers() if item.get("ID")]

    def mark_user_blocked(self, user_id: Union[str, int], reason: str) -> None:
        uid = str(user_id)
        leaver = self._leavers.get(uid)
        now = int(datetime.now(tz=timezone.utc).timestamp())
        if not leaver:
            leaver = {"ID": uid}
        leaver.update(
            {
                "blocked": True,
                "blocked_ts": now,
                "blocked_reason": reason,
            }
        )
        self._leavers[uid] = leaver
        self._guard_root.child("leavers").child(uid).update(leaver)

    def record_manual_unblock(self, user_id: Union[str, int]) -> None:
        uid = str(user_id)
        leaver = self._leavers.get(uid)
        if not leaver:
            return
        leaver["unblocked_ts"] = int(datetime.now(tz=timezone.utc).timestamp())
        self._leavers[uid] = leaver
        self._guard_root.child("leavers").child(uid).update(leaver)

    # ------------------------------------------------------------------
    # Internal loops
    # ------------------------------------------------------------------

    async def _scan_loop(self) -> None:
        while self._running:
            try:
                new_leavers, auto_banned = await self._scan_once()
                await self._send_scan_report(new_leavers, auto_banned)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[ChannelGuard] Scan loop error: {exc}")
            await asyncio.sleep(self._settings["scan_interval"])

    async def _auto_loop(self) -> None:
        while self._running:
            if not self._settings.get("auto_enabled") or self._settings.get("auto_interval", 0) <= 0:
                await asyncio.sleep(5)
                continue
            try:
                await self._process_auto_window()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[ChannelGuard] Auto loop error: {exc}")
            await asyncio.sleep(self._settings["auto_interval"])

    async def _scan_once(self) -> Tuple[int, int]:
        async with self._lock:
            events = await self._fetch_leave_events()
            if not events:
                return 0, 0
            events.sort(key=lambda e: e.id)
            new_count = 0
            auto_banned = 0
            for event, user_info in events:
                if event.id <= self._last_event_id:
                    continue
                self._last_event_id = max(self._last_event_id, event.id)
                uid = str(user_info.get("id"))
                now = int(datetime.now(tz=timezone.utc).timestamp())
                leaver = self._leavers.get(uid, {})
                if not leaver:
                    leaver = {
                        "ID": uid,
                        "first_left_ts": event.date.timestamp(),
                        "username": user_info.get("username"),
                        "name": user_info.get("full_name"),
                    }
                leaver["last_left_ts"] = event.date.timestamp()
                leaver["blocked"] = leaver.get("blocked", False)
                self._leavers[uid] = leaver
                self._guard_root.child("leavers").child(uid).update(leaver)
                new_count += 1
                if self._settings.get("auto_enabled"):
                    if await self._auto_block_user(int(uid), reason="auto_immediate"):
                        auto_banned += 1
            self._guard_root.child("state").update({"last_event_id": self._last_event_id})
            return new_count, auto_banned

    async def _process_auto_window(self) -> None:
        window = self._settings.get("auto_window", 0)
        if window <= 0:
            return
        threshold = int(datetime.now(tz=timezone.utc).timestamp()) - window
        pending = [
            int(entry["ID"])
            for entry in self.get_pending_leavers()
            if int(entry.get("last_left_ts", 0)) >= threshold
        ]
        if not pending:
            return
        for user_id in pending:
            await self._auto_block_user(user_id, reason="auto_window")

    async def _auto_block_user(self, user_id: int, reason: str) -> bool:
        if self._block_executor:
            try:
                self._block_executor(user_id, reason)
                return True
            except Exception as exc:
                logger.error(f"[ChannelGuard] Block executor failed for {user_id}: {exc}")
                return False
        # Fallback: mark as blocked directly to avoid silent failure
        self.mark_user_blocked(user_id, reason)
        return True

    async def _fetch_leave_events(self) -> List[Tuple[Any, Dict[str, Any]]]:
        peer = await self._app.resolve_peer(self._channel_id)
        events_filter = ChannelAdminLogEventsFilter(participants_left=True)
        try:
            result = await self._app.invoke(
                GetAdminLog(
                    channel=peer,
                    q="",
                    events_filter=events_filter,
                    admins=None,
                    max_id=0,
                    min_id=0,
                    limit=100,
                )
            )
        except RPCError as exc:
            logger.error(f"[ChannelGuard] GetAdminLog RPC error: {exc}")
            return []
        except Exception as exc:
            logger.error(f"[ChannelGuard] Unexpected log fetch error: {exc}")
            return []

        users_map = {}
        for user in getattr(result, "users", []):
            try:
                full_name = " ".join(
                    filter(
                        None,
                        [
                            getattr(user, "first_name", None),
                            getattr(user, "last_name", None),
                        ],
                    )
                ).strip()
            except Exception:
                full_name = ""
            users_map[user.id] = {
                "id": user.id,
                "username": getattr(user, "username", None),
                "full_name": full_name or getattr(user, "first_name", "") or "",
            }

        leave_events: List[Tuple[Any, Dict[str, Any]]] = []
        for event in getattr(result, "events", []):
            if isinstance(event.action, ChannelAdminLogEventActionParticipantLeave):
                user_meta = users_map.get(event.user_id, {"id": event.user_id})
                leave_events.append((event, user_meta))
        return leave_events

    async def _send_scan_report(self, new_count: int, auto_banned: int) -> None:
        admins = getattr(Config, "ADMIN", [])
        if not admins:
            return
        interval_text = format_seconds_human(self._settings.get("scan_interval", 0))
        pending_count = len(self.get_pending_leavers())
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for admin_id in admins:
            try:
                safe_send_message(
                    admin_id,
                    safe_get_messages(admin_id).BAN_TIME_REPORT_MSG.format(
                        run_ts=ts,
                        interval=interval_text,
                        new_leavers=new_count,
                        auto_banned=auto_banned,
                        pending=pending_count,
                        last_event_id=self._last_event_id,
                    ),
                )
            except Exception as exc:
                logger.error(f"[ChannelGuard] Failed to send report to {admin_id}: {exc}")


# --------------------------------------------------------------------------------------
# Singleton helpers
# --------------------------------------------------------------------------------------

_channel_guard = ChannelGuard()


def get_channel_guard() -> ChannelGuard:
    return _channel_guard


def start_channel_guard(app) -> None:
    loop = getattr(app, "loop", None)
    if not loop:
        logger.error("[ChannelGuard] App loop is not available, cannot start guard")
        return
    loop.create_task(_channel_guard.start(app))


async def stop_channel_guard() -> None:
    await _channel_guard.stop()


def register_block_user_executor(callback: Callable[[int, Optional[str]], None]) -> None:
    _channel_guard.register_block_executor(callback)

