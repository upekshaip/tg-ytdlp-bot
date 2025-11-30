import json
from pathlib import Path

import pytest

from CONFIG.config import Config
from services.stats_collector import StatsCollector


def _write_dump(tmp_path: Path, bot_name: str) -> Path:
    dump_data = {
        "bot": {
            bot_name: {
                "logs": {
                    "100": {
                        "1700000000": {
                            "ID": "100",
                            "timestamp": "1700000000",
                            "name": "Alice",
                            "urls": "https://example.com/video1",
                            "title": "Video 1",
                        },
                        "1700003600": {
                            "ID": "100",
                            "timestamp": "1700003600",
                            "name": "Alice",
                            "urls": "https://example.com/video2",
                            "title": "Video 2",
                        },
                    },
                    "200": {
                        "1700007200": {
                            "ID": "200",
                            "timestamp": "1700007200",
                            "name": "Bob",
                            "urls": "https://youtube.com/watch?v=xyz",
                            "title": "Playlist #1",
                        }
                    },
                },
                "blocked_users": {
                    "300": {"ID": "300", "timestamp": "1700010000"},
                },
                "channel_guard": {
                    "leavers": {
                        "400": {
                            "ID": "400",
                            "name": "Charlie",
                            "username": "charlie",
                            "last_left_ts": 1700010800,
                        }
                    }
                },
            }
        }
    }
    dump_path = tmp_path / "dump.json"
    dump_path.write_text(json.dumps(dump_data), encoding="utf-8")
    return dump_path


@pytest.fixture
def collector(tmp_path, monkeypatch):
    bot_name = "test_bot"
    monkeypatch.setattr(Config, "BOT_NAME_FOR_USERS", bot_name, raising=False)
    dump_path = _write_dump(tmp_path, bot_name)
    return StatsCollector(
        dump_path=str(dump_path),
        reload_interval=3600,
        active_timeout=300,
        start_background=False,
    )


def test_top_downloaders_from_dump(collector):
    top_all = collector.get_top_downloaders("all", limit=5)
    assert top_all, "должен вернуть хотя бы одного пользователя"
    assert top_all[0]["count"] == 2
    assert top_all[0]["user_id"] == 100


def test_handle_db_event_updates_live_data(collector):
    payload = {
        "ID": "500",
        "timestamp": "1800000000",
        "name": "Zoe",
        "urls": "https://onlyfans.com/creator",
        "title": "NSFW drop",
    }
    collector.handle_db_event("/bot/test_bot/logs/500/1800000000", "set", payload)

    nsfw_users = collector.get_top_nsfw_users(limit=5)
    ids = [item["user_id"] for item in nsfw_users]
    assert 500 in ids

    active = collector.get_active_users(limit=5)
    active_ids = [item["user_id"] for item in active["items"]]
    assert 500 in active_ids

