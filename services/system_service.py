from __future__ import annotations

import psutil
import time
import subprocess
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from importlib import import_module, metadata

from CONFIG.config import Config
from DATABASE.cache_db import get_next_reload_time

# Кеш для скорости сети
_network_speed_cache = {"last_check": 0, "last_sent": 0, "last_recv": 0, "speed_sent": 0, "speed_recv": 0}


def get_network_speed() -> Dict[str, Any]:
    """Вычисляет текущую скорость сети на основе активных потоков."""
    global _network_speed_cache
    try:
        now = time.time()
        net_io = psutil.net_io_counters()
        
        # Если прошло меньше секунды с последней проверки, возвращаем кеш
        if now - _network_speed_cache["last_check"] < 1:
            return {
                "speed_sent_mbps": round(_network_speed_cache["speed_sent"] / (1024**2) * 8, 2),
                "speed_recv_mbps": round(_network_speed_cache["speed_recv"] / (1024**2) * 8, 2),
            }
        
        # Вычисляем скорость
        if _network_speed_cache["last_check"] > 0:
            time_diff = now - _network_speed_cache["last_check"]
            sent_diff = net_io.bytes_sent - _network_speed_cache["last_sent"]
            recv_diff = net_io.bytes_recv - _network_speed_cache["last_recv"]
            
            _network_speed_cache["speed_sent"] = sent_diff / time_diff if time_diff > 0 else 0
            _network_speed_cache["speed_recv"] = recv_diff / time_diff if time_diff > 0 else 0
        else:
            _network_speed_cache["speed_sent"] = 0
            _network_speed_cache["speed_recv"] = 0
        
        _network_speed_cache["last_check"] = now
        _network_speed_cache["last_sent"] = net_io.bytes_sent
        _network_speed_cache["last_recv"] = net_io.bytes_recv
        
        return {
            "speed_sent_mbps": round(_network_speed_cache["speed_sent"] / (1024**2) * 8, 2),
            "speed_recv_mbps": round(_network_speed_cache["speed_recv"] / (1024**2) * 8, 2),
        }
    except Exception as e:
        return {"error": str(e)}


def get_external_ip() -> str:
    """Получает внешний IP адрес."""
    try:
        # Пробуем несколько сервисов
        services = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
        ]
        for service in services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    return response.text.strip()
            except Exception:
                continue
        return "unknown"
    except Exception:
        return "unknown"


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
        
        # Скорость сети
        network_speed = get_network_speed()
        
        # Внешний IP
        external_ip = get_external_ip()
        
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
                "speed_sent_mbps": network_speed.get("speed_sent_mbps", 0),
                "speed_recv_mbps": network_speed.get("speed_recv_mbps", 0),
            },
            "external_ip": external_ip,
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


def _read_package_version(
    package_name: str,
    module_name: str | None = None,
    cli_command: list[str] | None = None,
) -> str:
    """Пытается определить версию пакета несколькими способами."""
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        pass
    except Exception:
        pass
    
    if module_name:
        try:
            module = import_module(module_name)
            version = getattr(module, "__version__", None)
            if version:
                return str(version)
        except Exception:
            pass
    
    if cli_command:
        try:
            result = subprocess.run(
                cli_command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[0]
        except Exception:
            pass
    
    return "unknown"


def get_package_versions() -> Dict[str, str]:
    """Возвращает версии установленных пакетов."""
    return {
        "yt-dlp": _read_package_version("yt-dlp", module_name="yt_dlp", cli_command=["yt-dlp", "--version"]),
        "gallery-dl": _read_package_version("gallery-dl", module_name="gallery_dl", cli_command=["gallery-dl", "--version"]),
        "pyrotgfork": _read_package_version("pyrotgfork", module_name="pyrotgfork"),
    }


def rotate_ip() -> Dict[str, Any]:
    """Ротирует IP адрес через перезапуск WireGuard."""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "wg-quick@wgcf"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "IP rotated successfully"}
        else:
            return {"status": "error", "message": result.stderr or "Failed to rotate IP"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def restart_service() -> Dict[str, Any]:
    """Перезапускает сервис tg-ytdlp-bot."""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "tg-ytdlp-bot"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "Service restarted successfully"}
        else:
            return {"status": "error", "message": result.stderr or "Failed to restart service"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_engines() -> Dict[str, Any]:
    """Обновляет движки через engines_updater.sh."""
    try:
        script_path = "/root/Telegram/tg-ytdlp-bot/engines_updater.sh"
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "Engines updated successfully", "output": result.stdout}
        else:
            return {"status": "error", "message": result.stderr or "Failed to update engines"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def cleanup_user_files() -> Dict[str, Any]:
    """Удаляет файлы из папок пользователей (кроме системных)."""
    try:
        users_dir = "/root/Telegram/tg-ytdlp-bot/users"
        result = subprocess.run(
            [
                "/usr/bin/find",
                users_dir,
                "-type", "f",
                "!", "-name", "lang.txt",
                "!", "-name", "args.txt",
                "!", "-name", "keyboard.txt",
                "!", "-name", "subs.txt",
                "!", "-name", "subs_auto.txt",
                "!", "-name", "mediainfo.txt",
                "!", "-name", "split.txt",
                "!", "-name", "tags.txt",
                "!", "-name", "cookie.txt",
                "!", "-name", "logs.txt",
                "!", "-name", "format.txt",
                "-delete",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "User files cleaned up successfully"}
        else:
            return {"status": "error", "message": result.stderr or "Failed to cleanup files"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_lists() -> Dict[str, Any]:
    """Обновляет списки через script.sh."""
    try:
        script_path = "/root/Telegram/tg-ytdlp-bot/script.sh"
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут
            check=False,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "Lists updated successfully", "output": result.stdout}
        else:
            return {"status": "error", "message": result.stderr or "Failed to update lists"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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

