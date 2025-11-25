from __future__ import annotations

import psutil
import time
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from CONFIG.config import Config
from DATABASE.cache_db import get_next_reload_time


def get_system_metrics() -> Dict[str, Any]:
    """Возвращает метрики системы."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net_io = psutil.net_io_counters()
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        # Время до следующего reload_cache
        interval_hours = getattr(Config, "RELOAD_CACHE_EVERY", 4)
        next_reload = get_next_reload_time(interval_hours)
        now = datetime.now()
        delta = next_reload - now
        reload_seconds = int(delta.total_seconds())
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round(disk.used / disk.total * 100, 1),
            },
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            },
            "uptime": {
                "days": uptime_days,
                "hours": uptime_hours,
                "minutes": uptime_minutes,
            },
            "next_reload": {
                "datetime": next_reload.isoformat(),
                "seconds": reload_seconds,
            },
            "status": "online",
        }
    except Exception as e:
        return {"error": str(e)}


def get_package_versions() -> Dict[str, str]:
    """Возвращает версии установленных пакетов."""
    versions = {}
    packages = ["yt-dlp", "gallery-dl", "pyrotgfork"]
    for pkg in packages:
        try:
            result = subprocess.run(
                [pkg, "--version"] if pkg != "pyrotgfork" else ["python", "-c", f"import {pkg}; print({pkg}.__version__)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                versions[pkg] = result.stdout.strip().split()[0] if pkg != "pyrotgfork" else result.stdout.strip()
            else:
                versions[pkg] = "unknown"
        except Exception:
            try:
                if pkg == "pyrotgfork":
                    import pyrotgfork
                    versions[pkg] = getattr(pyrotgfork, "__version__", "unknown")
                else:
                    result = subprocess.run(["pip", "show", pkg], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        match = re.search(r"Version:\s*(\S+)", result.stdout)
                        versions[pkg] = match.group(1) if match else "unknown"
                    else:
                        versions[pkg] = "unknown"
            except Exception:
                versions[pkg] = "unknown"
    return versions


def get_config_settings() -> Dict[str, Any]:
    """Возвращает редактируемые настройки из конфига."""
    return {
        "proxy": {
            "type": getattr(Config, "PROXY_TYPE", ""),
            "ip": getattr(Config, "PROXY_IP", ""),
            "port": getattr(Config, "PROXY_PORT", ""),
            "user": getattr(Config, "PROXY_USER", ""),
            "password": getattr(Config, "PROXY_PASSWORD", ""),
        },
        "proxy_2": {
            "type": getattr(Config, "PROXY_2_TYPE", ""),
            "ip": getattr(Config, "PROXY_2_IP", ""),
            "port": getattr(Config, "PROXY_2_PORT", ""),
            "user": getattr(Config, "PROXY_2_USER", ""),
            "password": getattr(Config, "PROXY_2_PASSWORD", ""),
        },
        "cookies": {
            "youtube": getattr(Config, "YOUTUBE_COOKIE_URL", ""),
            "instagram": getattr(Config, "INSTAGRAM_COOKIE_URL", ""),
            "tiktok": getattr(Config, "TIKTOK_COOKIE_URL", ""),
            "twitter": getattr(Config, "TWITTER_COOKIE_URL", ""),
            "vk": getattr(Config, "VK_COOKIE_URL", ""),
        },
        "allowed_groups": getattr(Config, "ALLOWED_GROUP", []),
        "admins": getattr(Config, "ADMIN", []),
        "miniapp_url": getattr(Config, "MINIAPP_URL", ""),
        "subscribe_channel_url": getattr(Config, "SUBSCRIBE_CHANNEL_URL", ""),
    }


def update_config_setting(key: str, value: Any) -> bool:
    """Обновляет настройку в CONFIG/config.py."""
    config_path = Path(__file__).parent.parent / "CONFIG" / "config.py"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Простое обновление через поиск строки
        patterns = {
            "PROXY_TYPE": r'^\s*PROXY_TYPE\s*=',
            "PROXY_IP": r'^\s*PROXY_IP\s*=',
            "PROXY_PORT": r'^\s*PROXY_PORT\s*=',
            "PROXY_USER": r'^\s*PROXY_USER\s*=',
            "PROXY_PASSWORD": r'^\s*PROXY_PASSWORD\s*=',
            "PROXY_2_TYPE": r'^\s*PROXY_2_TYPE\s*=',
            "PROXY_2_IP": r'^\s*PROXY_2_IP\s*=',
            "PROXY_2_PORT": r'^\s*PROXY_2_PORT\s*=',
            "PROXY_2_USER": r'^\s*PROXY_2_USER\s*=',
            "PROXY_2_PASSWORD": r'^\s*PROXY_2_PASSWORD\s*=',
            "MINIAPP_URL": r'^\s*MINIAPP_URL\s*=',
            "SUBSCRIBE_CHANNEL_URL": r'^\s*SUBSCRIBE_CHANNEL_URL\s*=',
            "YOUTUBE_COOKIE_URL": r'^\s*YOUTUBE_COOKIE_URL\s*=',
            "INSTAGRAM_COOKIE_URL": r'^\s*INSTAGRAM_COOKIE_URL\s*=',
            "TIKTOK_COOKIE_URL": r'^\s*TIKTOK_COOKIE_URL\s*=',
            "TWITTER_COOKIE_URL": r'^\s*TWITTER_COOKIE_URL\s*=',
            "VK_COOKIE_URL": r'^\s*VK_COOKIE_URL\s*=',
        }
        
        updated = False
        for i, line in enumerate(lines):
            if key in patterns and re.match(patterns[key], line):
                if isinstance(value, str):
                    lines[i] = f"    {key} = \"{value}\"\n"
                elif isinstance(value, int):
                    lines[i] = f"    {key} = {value}\n"
                updated = True
                break
            elif key == "ADMIN" and re.match(r'^\s*ADMIN\s*=', line):
                if isinstance(value, list):
                    list_str = ", ".join(str(v) for v in value)
                    lines[i] = f"    ADMIN = [{list_str}]\n"
                    updated = True
                    break
            elif key == "ALLOWED_GROUP" and re.match(r'^\s*ALLOWED_GROUP\s*=', line):
                if isinstance(value, list):
                    list_str = ", ".join(str(v) for v in value)
                    lines[i] = f"    ALLOWED_GROUP = [{list_str}]\n"
                    updated = True
                    break
        
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        print(f"Error updating config: {e}")
        return False

