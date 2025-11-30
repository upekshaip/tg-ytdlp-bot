from __future__ import annotations

import pathlib
import logging
from typing import Any, List
from fastapi import FastAPI, HTTPException, Query, Request, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from CONFIG.config import Config
from services import stats_service
from services import system_service, lists_service
from services.auth_service import get_auth_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Порт дашборда берется из Config.DASHBOARD_PORT (по умолчанию 5555)
# Для запуска: uvicorn web.dashboard_app:app --host 0.0.0.0 --port {Config.DASHBOARD_PORT}

BASE_DIR = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="TG YTDLP Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# CORS для API запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для проверки авторизации
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Публичные пути
        public_paths = ["/login", "/api/login", "/api/reset-lockdown", "/static", "/health"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Проверяем токен из cookie
        token = request.cookies.get("auth_token")
        auth_service = get_auth_service()
        
        if not token or not auth_service.verify_token(token):
            if request.url.path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Unauthorized")
            return RedirectResponse(url="/login", status_code=302)
        
        response = await call_next(request)
        if request.url.path != "/api/logout":
            response.set_cookie(
                key="auth_token",
                value=token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=auth_service.session_ttl,
            )
        return response


app.add_middleware(AuthMiddleware)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


@app.post("/api/login")
async def api_login(payload: LoginRequest, request: Request):
    auth_service = get_auth_service()
    # Перезагружаем конфиг перед каждой попыткой входа
    auth_service.reload_config()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        token = auth_service.login(payload.username, payload.password, client_ip)
        response = Response(content='{"status": "ok"}', media_type="application/json")
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=False,  # В production установить True для HTTPS
            samesite="lax",
            max_age=auth_service.session_ttl,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/reset-lockdown")
async def api_reset_lockdown(request: Request):
    """Сбрасывает блокировку для текущего IP (для отладки)."""
    auth_service = get_auth_service()
    client_ip = request.client.host if request.client else "unknown"
    auth_service.reset_lockdown(client_ip)
    return {"status": "ok", "message": f"Lockdown reset for IP {client_ip}"}


@app.post("/api/logout")
async def api_logout(request: Request):
    token = request.cookies.get("auth_token")
    if token:
        auth_service = get_auth_service()
        auth_service.logout(token)
    response = Response(content='{"status":"ok"}', media_type="application/json")
    response.delete_cookie("auth_token")
    return response


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
async def api_active_users(
    limit: int = 10,
    minutes: int | None = Query(default=None, ge=1, le=3600),
):
    return stats_service.fetch_active_users(limit=limit, minutes=minutes)


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
async def api_power_users(min_urls: int = 10, days: int = 7, limit: int = 10):
    return stats_service.fetch_power_users(min_urls=min_urls, days=days, limit=limit)


@app.get("/api/blocked-users")
async def api_blocked_users(limit: int = 50):
    return stats_service.fetch_blocked_users(limit)


@app.get("/api/channel-events")
async def api_channel_events(hours: int = 48, limit: int = 100):
    return stats_service.fetch_recent_channel_events(hours=hours, limit=limit)


@app.get("/api/suspicious-users")
async def api_suspicious_users(
    period: str = Query(default="today", regex="^(today|week|month|all)$"),
    limit: int = 20,
):
    return stats_service.fetch_suspicious_users(period=period, limit=limit)


@app.get("/api/user-history")
async def api_user_history(
    user_id: int = Query(..., gt=0),
    period: str = Query(default="all", regex="^(today|week|month|all)$"),
    limit: int = Query(default=100, le=1000),
):
    return stats_service.fetch_user_history(user_id, period, limit)


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


@app.post("/api/rotate-ip")
async def api_rotate_ip():
    return system_service.rotate_ip()


@app.post("/api/restart-service")
async def api_restart_service():
    return system_service.restart_service()


@app.post("/api/update-engines")
async def api_update_engines():
    return system_service.update_engines()


@app.post("/api/cleanup-user-files")
async def api_cleanup_user_files():
    return system_service.cleanup_user_files()


@app.post("/api/update-lists")
async def api_update_lists():
    return lists_service.update_lists()


@app.get("/health")
async def health():
    return {"status": "ok"}

