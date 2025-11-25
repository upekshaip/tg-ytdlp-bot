from __future__ import annotations

import pathlib
from typing import Any, List
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from CONFIG.config import Config
from services import stats_service
from services import system_service, lists_service


BASE_DIR = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="TG YTDLP Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Статистика бота",
            "config": {
                "STATS_ACTIVE_TIMEOUT": getattr(Config, "STATS_ACTIVE_TIMEOUT", 900),
            },
        },
    )


@app.get("/api/active-users")
async def api_active_users(limit: int = 10):
    return stats_service.fetch_active_users(limit=limit)


@app.get("/api/top-downloaders")
async def api_top_downloaders(
    period: str = Query(default="today", regex="^(today|week|month|all)$"),
    limit: int = 10,
):
    return stats_service.fetch_top_downloaders(period=period, limit=limit)


@app.get("/api/top-domains")
async def api_top_domains(period: str = "today", limit: int = 10):
    return stats_service.fetch_top_domains(period=period, limit=limit)


@app.get("/api/top-countries")
async def api_top_countries(period: str = "today", limit: int = 10):
    return stats_service.fetch_top_countries(period=period, limit=limit)


@app.get("/api/gender-stats")
async def api_gender_stats(period: str = "today"):
    return stats_service.fetch_gender_stats(period)


@app.get("/api/age-stats")
async def api_age_stats(period: str = "today"):
    return stats_service.fetch_age_stats(period)


@app.get("/api/top-nsfw-users")
async def api_nsfw_users(limit: int = 10):
    return stats_service.fetch_top_nsfw_users(limit)


@app.get("/api/top-nsfw-domains")
async def api_nsfw_domains(limit: int = 10):
    return stats_service.fetch_top_nsfw_domains(limit)


@app.get("/api/top-playlist-users")
async def api_playlist_users(limit: int = 10):
    return stats_service.fetch_top_playlist_users(limit)


@app.get("/api/power-users")
async def api_power_users(limit: int = 10):
    return stats_service.fetch_power_users(limit)


@app.get("/api/blocked-users")
async def api_blocked_users(limit: int = 50):
    return stats_service.fetch_blocked_users(limit)


@app.get("/api/channel-events")
async def api_channel_events(hours: int = 48, limit: int = 100):
    return stats_service.fetch_recent_channel_events(hours=hours, limit=limit)


class BlockRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=120)


@app.post("/api/block-user")
async def api_block_user(payload: BlockRequest):
    try:
        stats_service.block_user(payload.user_id, reason=payload.reason or "manual")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@app.post("/api/unblock-user")
async def api_unblock_user(payload: BlockRequest):
    try:
        stats_service.unblock_user(payload.user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@app.get("/api/system-metrics")
async def api_system_metrics():
    return system_service.get_system_metrics()


@app.get("/api/package-versions")
async def api_package_versions():
    return system_service.get_package_versions()


@app.get("/api/config-settings")
async def api_config_settings():
    return system_service.get_config_settings()


class ConfigUpdateRequest(BaseModel):
    key: str = Field(...)
    value: Any


@app.post("/api/update-config")
async def api_update_config(payload: ConfigUpdateRequest):
    try:
        success = system_service.update_config_setting(payload.key, payload.value)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update config")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@app.get("/api/lists-stats")
async def api_lists_stats():
    return lists_service.get_lists_stats()


@app.get("/api/domain-lists")
async def api_domain_lists():
    return lists_service.get_domain_lists()


class DomainListUpdateRequest(BaseModel):
    list_name: str = Field(...)
    items: List[str] = Field(...)


@app.post("/api/update-domain-list")
async def api_update_domain_list(payload: DomainListUpdateRequest):
    try:
        success = lists_service.update_domain_list(payload.list_name, payload.items)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update domain list")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}

