from __future__ import annotations

# Version 1.0.1

import hashlib
import secrets
import time
import logging
import json
from pathlib import Path
from typing import Dict, Optional
from threading import Lock

from CONFIG.config import Config

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис авторизации с защитой от перебора."""
    
    def __init__(self):
        self._sessions: Dict[str, float] = {}  # token -> expiry_time
        self._failed_attempts: Dict[str, int] = {}  # ip -> count
        self._lockdown_until: Dict[str, float] = {}  # ip -> unlock_time
        self._lock = Lock()
        self._session_ttl = 15 * 60  # 15 минут неактивности
        self._sessions_file = Path(__file__).resolve().parent.parent / "CONFIG" / ".dashboard_sessions.json"
        
        # Получаем логин/пароль из конфига (убираем пробелы)
        username = getattr(Config, "DASHBOARD_USERNAME", "admin")
        password = getattr(Config, "DASHBOARD_PASSWORD", "admin123")
        self._username = str(username).strip() if username else "admin"
        self._password_hash = self._hash_password(str(password).strip() if password else "admin123")
        logger.info(f"[auth] Initialized with username='{self._username}' (length={len(self._username)})")
        
        self._load_sessions()
    
    def _hash_password(self, password: str) -> str:
        """Хеширует пароль."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _check_password(self, password: str) -> bool:
        """Проверяет пароль."""
        return self._hash_password(password) == self._password_hash
    
    def _get_lockdown_time(self, failed_count: int) -> float:
        """Вычисляет время блокировки на основе количества неудачных попыток."""
        if failed_count <= 5:
            return 5 * 60  # 5 минут
        # Каждая следующая попытка удваивает время
        base_time = 5 * 60
        multiplier = 2 ** (failed_count - 5)
        return base_time * multiplier
    
    def login(self, username: str, password: str, ip: str) -> Optional[str]:
        """Пытается авторизовать пользователя. Возвращает токен или None."""
        with self._lock:
            # Проверяем блокировку
            unlock_time = self._lockdown_until.get(ip, 0)
            if unlock_time > time.time():
                remaining = int(unlock_time - time.time())
                raise ValueError(f"Too many failed attempts. Try again in {remaining // 60} minutes.")
            
            # Убираем пробелы из входящих данных
            username = str(username).strip() if username else ""
            password = str(password).strip() if password else ""
            
            # Проверяем логин/пароль
            username_match = username == self._username
            password_match = self._check_password(password)
            
            # Отладочная информация для первой неудачной попытки
            failed_count = self._failed_attempts.get(ip, 0)
            if not username_match or not password_match:
                failed_count = failed_count + 1
                if failed_count == 1:
                    # Детальная отладочная информация только для первой попытки
                    logger.warning(
                        f"[auth] Login failed for IP {ip}: "
                        f"username_match={username_match} "
                        f"(got='{username}' len={len(username)}, expected='{self._username}' len={len(self._username)}), "
                        f"password_match={password_match} "
                        f"(password_len={len(password)})"
                    )
                
                # Увеличиваем счетчик неудачных попыток
                self._failed_attempts[ip] = failed_count
                
                # Устанавливаем блокировку
                lockdown_time = self._get_lockdown_time(failed_count)
                self._lockdown_until[ip] = time.time() + lockdown_time
                
                raise ValueError("Invalid username or password")
            
            # Успешная авторизация - сбрасываем счетчики
            self._failed_attempts.pop(ip, None)
            self._lockdown_until.pop(ip, None)
            
            # Создаем сессию
            token = secrets.token_urlsafe(32)
            self._sessions[token] = time.time() + self._session_ttl
            self._save_sessions()
            return token
    
    def verify_token(self, token: str) -> bool:
        """Проверяет валидность токена."""
        with self._lock:
            expiry = self._sessions.get(token, 0)
            now = time.time()
            if expiry < now:
                self._sessions.pop(token, None)
                self._save_sessions()
                return False
            # Продлеваем сессию при активности
            self._sessions[token] = now + self._session_ttl
            self._save_sessions()
            return True
    
    def logout(self, token: str) -> None:
        """Удаляет сессию."""
        with self._lock:
            removed = self._sessions.pop(token, None)
            if removed is not None:
                self._save_sessions()
    
    def cleanup_expired_sessions(self) -> None:
        """Удаляет истекшие сессии."""
        now = time.time()
        with self._lock:
            expired = [token for token, expiry in self._sessions.items() if expiry < now]
            for token in expired:
                self._sessions.pop(token, None)
            if expired:
                self._save_sessions()
    
    def reload_config(self) -> None:
        """Перезагружает настройки из конфига."""
        username = getattr(Config, "DASHBOARD_USERNAME", "admin")
        password = getattr(Config, "DASHBOARD_PASSWORD", "admin123")
        username_clean = str(username).strip() if username else "admin"
        password_clean = str(password).strip() if password else "admin123"
        with self._lock:
            old_username = self._username
            self._username = username_clean
            self._password_hash = self._hash_password(password_clean)
            if old_username != username_clean:
                logger.info(f"[auth] Config reloaded: username changed from '{old_username}' to '{username_clean}'")
    
    def reset_lockdown(self, ip: str) -> None:
        """Сбрасывает блокировку для указанного IP (для отладки)."""
        with self._lock:
            self._failed_attempts.pop(ip, None)
            self._lockdown_until.pop(ip, None)
    
    def _load_sessions(self) -> None:
        try:
            if not self._sessions_file.exists():
                return
            with open(self._sessions_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            now = time.time()
            valid = {token: expiry for token, expiry in data.items() if expiry > now}
            self._sessions.update(valid)
            if len(valid) != len(data):
                self._save_sessions()
        except Exception as exc:
            logger.warning(f"[auth] Failed to load dashboard sessions: {exc}")
    
    def _save_sessions(self) -> None:
        try:
            self._sessions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._sessions_file, "w", encoding="utf-8") as fh:
                json.dump(self._sessions, fh)
        except Exception as exc:
            logger.warning(f"[auth] Failed to persist dashboard sessions: {exc}")

    @property
    def session_ttl(self) -> int:
        return self._session_ttl


# Глобальный экземпляр
_auth_service = None


def get_auth_service() -> AuthService:
    """Возвращает глобальный экземпляр AuthService."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

