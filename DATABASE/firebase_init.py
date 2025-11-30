import math
import time
import threading
import os
import json
from typing import Any, Dict, List, Optional

import requests
from requests import Session
from requests.adapters import HTTPAdapter
import firebase_admin
from firebase_admin import credentials, db as admin_db

from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.logger import logger
from HELPERS.filesystem_hlp import create_directory
from HELPERS.logger import send_to_all
from services.stats_events import emit_download_event, wrap_db_adapter

# Global variable for timing
starting_point = []


def _get_database_url() -> str:
    # ГЛОБАЛЬНАЯ ЗАЩИТА: Инициализируем messages
    messages = safe_get_messages(None)
    
    try:
        database_url_local = Config.FIREBASE_CONF.get("databaseURL")
    except Exception:
        database_url_local = None
    if not database_url_local:
        raise RuntimeError(safe_get_messages().DB_DATABASE_URL_MISSING_MSG)
    return database_url_local


def _init_firebase_admin_if_needed() -> bool:
    """Initialize firebase_admin with databaseURL from Config.

    Prefers credentials from GOOGLE_APPLICATION_CREDENTIALS or
    Config.FIREBASE_SERVICE_ACCOUNT (path to service account JSON).
    """
    if firebase_admin._apps:
        return True

    database_url = _get_database_url()

    # 1) Explicit path in config
    service_account_path = getattr(Config, "FIREBASE_SERVICE_ACCOUNT", None)
    if service_account_path and os.path.exists(service_account_path):
        cred_obj = credentials.Certificate(service_account_path)
    else:
        # 2) GOOGLE_APPLICATION_CREDENTIALS path present?
        adc_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if adc_path and os.path.exists(adc_path):
            try:
                cred_obj = credentials.Certificate(adc_path)
            except Exception:
                cred_obj = None
        else:
            cred_obj = None

    if cred_obj is None:
        logger.info("ℹ️ firebase_admin credentials not found, will use REST fallback")
        return False

    firebase_admin.initialize_app(cred_obj, {"databaseURL": database_url})
    logger.info(safe_get_messages().DB_FIREBASE_ADMIN_INITIALIZED_MSG)
    return True


class _SnapshotChild:
    def __init__(self, key: str, value: Any):
        messages = safe_get_messages(None)
        self._key = key
        self._value = value

    def key(self) -> str:
        return self._key

    def val(self) -> Any:
        return self._value


class _SnapshotCompat:
    """Pyrebase-like snapshot wrapper providing .val() and .each()."""

    def __init__(self, value: Any):
        self._value = value

    def val(self) -> Any:
        return self._value

    def each(self) -> List[_SnapshotChild] | None:
        if isinstance(self._value, dict):
            return [_SnapshotChild(k, v) for k, v in self._value.items()]
        return None


class FirebaseDBAdapter:
    """Adapter to mimic Pyrebase's chained .child().get().set() API on top of firebase_admin."""

    def __init__(self, path: str = "/"):
        self._path = path if path.startswith("/") else f"/{path}"

    def child(self, *path_parts: str) -> "FirebaseDBAdapter":
        path = self._path.rstrip("/")
        for part in path_parts:
            part = str(part).strip("/")
            if not part:
                continue
            path = f"{path}/{part}"
        return FirebaseDBAdapter(path)

    def _ref(self):
        messages = safe_get_messages(None)
        return admin_db.reference(self._path)

    def set(self, data: Any) -> None:
        return self._ref().set(data)

    def get(self) -> _SnapshotCompat:
        value = self._ref().get()
        return _SnapshotCompat(value)

    def push(self, data: Any):
        messages = safe_get_messages(None)
        # firebase_admin Reference has push in RTDB; return child key-compatible object
        ref = self._ref().push(data)
        return ref

    def update(self, data: Dict[str, Any]) -> None:
        return self._ref().update(data)

    def remove(self) -> None:
        return self._ref().delete()


class RestDBAdapter:
    """Pyrebase-like adapter using Firebase Realtime Database REST API with idToken.

    Важно: все дочерние адаптеры (child) разделяют одно общее состояние токенов,
    один requests.Session и один фоновой поток обновления токена.
    """

    def __init__(
        self,
        database_url: str,
        id_token: str,
        refresh_token: Optional[str],
        api_key: str,
        path: str = "/",
        *,
        _shared: Optional[dict] = None,
        _session: Optional[Session] = None,
        _start_refresher: bool = True,
        _is_child: bool = False,
    ):
        self._database_url = database_url.rstrip("/")
        self._api_key = api_key
        self._path = path if path.startswith("/") else f"/{path}"
        self._is_child = _is_child

        # Общее (shared) состояние между всеми child-экземплярами
        if _shared is None:
            self._shared = {
                "lock": threading.RLock(),
                "id_token": id_token,
                "refresh_token": refresh_token,
                "refresher_started": False,
            }
        else:
            self._shared = _shared

        # Общая сессия между всеми child-экземплярами
        if _session is None:
            from HELPERS.http_manager import get_managed_session
            # Use managed session for automatic cleanup
            self._session_manager = get_managed_session("firebase")
            self._session = self._session_manager.get_session()
        else:
            self._session = _session
            self._session_manager = None

        # Запускаем рефрешер токена только один раз (и только у корневого адаптера)
        if _start_refresher and self._shared.get("refresh_token"):
            with self._shared["lock"]:
                if not self._shared["refresher_started"]:
                    thread = threading.Thread(target=self._token_refresher, daemon=True)
                    thread.start()
                    self._shared["refresher_started"] = True

    def _token_refresher(self):
        messages = safe_get_messages(None)
        # Обновляем каждые ~50 минут
        while True:
            time.sleep(3000)
            try:
                url = f"https://securetoken.googleapis.com/v1/token?key={self._api_key}"
                with self._shared["lock"]:
                    refresh_token = self._shared.get("refresh_token")
                resp = self._session.post(url, data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                with self._shared["lock"]:
                    self._shared["id_token"] = data.get("id_token", self._shared.get("id_token"))
                    self._shared["refresh_token"] = data.get("refresh_token", self._shared.get("refresh_token"))
                logger.info(safe_get_messages().DB_REST_ID_TOKEN_REFRESHED_MSG)
            except Exception as e:
                logger.error(safe_get_messages().DB_REST_TOKEN_REFRESH_ERROR_MSG.format(error=e))

    def _auth_params(self) -> Dict[str, str]:
        with self._shared["lock"]:
            token = self._shared.get("id_token")
        return {"auth": token}

    def child(self, *path_parts: str) -> "RestDBAdapter":
        path = self._path.rstrip("/")
        for part in path_parts:
            part = str(part).strip("/")
            if not part:
                continue
            path = f"{path}/{part}"
        # ВАЖНО: не запускаем новый рефрешер и переиспользуем shared и session
        return RestDBAdapter(
            self._database_url,
            self._shared.get("id_token"),
            self._shared.get("refresh_token"),
            self._api_key,
            path,
            _shared=self._shared,
            _session=self._session,
            _start_refresher=False,
            _is_child=True,
        )

    def _url(self) -> str:
        return f"{self._database_url}{self._path}.json"

    def set(self, data: Any) -> None:
        r = self._session.put(self._url(), params=self._auth_params(), json=data, timeout=60)
        r.raise_for_status()

    def update(self, data: Dict[str, Any]) -> None:
        r = self._session.patch(self._url(), params=self._auth_params(), json=data, timeout=60)
        r.raise_for_status()

    def remove(self) -> None:
        r = self._session.delete(self._url(), params=self._auth_params(), timeout=60)
        r.raise_for_status()

    def push(self, data: Any):
        parent_url = f"{self._database_url}{self._path}.json"
        r = self._session.post(parent_url, params=self._auth_params(), json=data, timeout=60)
        r.raise_for_status()
        return r.json()

    def get(self) -> _SnapshotCompat:
        r = self._session.get(self._url(), params=self._auth_params(), timeout=60)
        r.raise_for_status()
        return _SnapshotCompat(r.json())

    def close(self):
        messages = safe_get_messages(None)
        """Закрывает сетевые ресурсы только у корневого адаптера.
        Дети разделяют сессию и не должны её закрывать.
        """
        if self._is_child:
            return
        try:
            if hasattr(self, '_session') and self._session:
                for adapter in self._session.adapters.values():
                    if hasattr(adapter, 'poolmanager'):
                        pool = adapter.poolmanager
                        if hasattr(pool, 'clear'):
                            pool.clear()
                self._session.close()
                logger.info("✅ Firebase session closed successfully (root)")
        except Exception as e:
            logger.error(safe_get_messages().DB_ERROR_CLOSING_SESSION_MSG.format(error=e))

    def __del__(self):
        # Ничего не делаем у детей, чтобы не ломать общую сессию
        if not self._is_child and hasattr(self, '_session_manager') and self._session_manager:
            try:
                self._session_manager.close()
            except Exception:
                pass


class LocalDBAdapter:
    """Локальный адаптер для работы с JSON файлом вместо Firebase.
    
    Имитирует API Pyrebase для совместимости с существующим кодом.
    Все операции чтения/записи выполняются с локальным JSON файлом.
    """
    
    def __init__(self, cache_file: str, path: str = "/"):
        self._cache_file = cache_file
        self._path = path if path.startswith("/") else f"/{path}"
        self._lock = threading.RLock()
        self._ensure_cache_file()
    
    def _ensure_cache_file(self):
        """Создает файл кэша если его нет."""
        if not os.path.exists(self._cache_file):
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки локального кэша: {e}")
            return {}
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Сохраняет данные в JSON файл."""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения локального кэша: {e}")
            raise
    
    def _get_path_value(self, data: Dict[str, Any], path: str) -> Any:
        """Получает значение по пути в словаре."""
        if path == "/" or not path:
            return data
        parts = [p for p in path.strip("/").split("/") if p]
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    
    def _set_path_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Устанавливает значение по пути в словаре."""
        if path == "/" or not path:
            if isinstance(value, dict):
                data.update(value)
            else:
                raise ValueError("Корневой путь должен быть словарем")
            return
        
        parts = [p for p in path.strip("/").split("/") if p]
        current = data
        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    
    def _remove_path_value(self, data: Dict[str, Any], path: str) -> None:
        """Удаляет значение по пути в словаре."""
        if path == "/" or not path:
            data.clear()
            return
        
        parts = [p for p in path.strip("/").split("/") if p]
        current = data
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return  # Путь не существует
        if isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]
    
    def child(self, *path_parts: str) -> "LocalDBAdapter":
        """Создает дочерний адаптер с расширенным путем."""
        path = self._path.rstrip("/")
        for part in path_parts:
            part = str(part).strip("/")
            if not part:
                continue
            path = f"{path}/{part}"
        return LocalDBAdapter(self._cache_file, path)
    
    def set(self, data: Any) -> None:
        """Устанавливает значение по текущему пути."""
        with self._lock:
            cache = self._load_cache()
            self._set_path_value(cache, self._path, data)
            self._save_cache(cache)
    
    def update(self, data: Dict[str, Any]) -> None:
        """Обновляет значения по текущему пути."""
        with self._lock:
            cache = self._load_cache()
            current = self._get_path_value(cache, self._path)
            if isinstance(current, dict):
                current.update(data)
                self._set_path_value(cache, self._path, current)
            else:
                self._set_path_value(cache, self._path, data)
            self._save_cache(cache)
    
    def remove(self) -> None:
        """Удаляет значение по текущему пути."""
        with self._lock:
            cache = self._load_cache()
            self._remove_path_value(cache, self._path)
            self._save_cache(cache)
    
    def push(self, data: Any):
        """Добавляет данные в список (генерирует ключ как timestamp)."""
        with self._lock:
            cache = self._load_cache()
            current = self._get_path_value(cache, self._path)
            if not isinstance(current, dict):
                current = {}
            key = str(int(time.time() * 1000))  # timestamp в миллисекундах
            current[key] = data
            self._set_path_value(cache, self._path, current)
            self._save_cache(cache)
            return key
    
    def get(self) -> _SnapshotCompat:
        """Получает значение по текущему пути."""
        with self._lock:
            cache = self._load_cache()
            value = self._get_path_value(cache, self._path)
            return _SnapshotCompat(value)
    
    def close(self):
        """Закрывает адаптер (для локального режима ничего не делает)."""
        pass


# Initialize db adapter (admin, REST fallback, or local)
use_firebase = getattr(Config, 'USE_FIREBASE', True)
if not use_firebase:
    # Локальный режим - используем JSON файл
    cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'dump.json')
    db = LocalDBAdapter(cache_file, "/")
    logger.info(f"✅ Локальный режим активирован (кэш: {cache_file})")
else:
    # Firebase режим - используем облачную базу
    use_admin = _init_firebase_admin_if_needed()
    if use_admin:
        db = FirebaseDBAdapter("/")
    else:
        database_url = _get_database_url()
        api_key = getattr(Config, "FIREBASE_CONF", {}).get("apiKey")
        if not api_key:
            raise RuntimeError("FIREBASE_CONF.apiKey отсутствует — нужен для REST аутентификации")
        # Sign in via REST using managed session
        from HELPERS.http_manager import get_managed_session
        auth_manager = get_managed_session("firebase-auth")
        auth_session = auth_manager.get_session()
        try:
            auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            resp = auth_session.post(auth_url, json={
                "email": getattr(Config, "FIREBASE_USER", None),
                "password": getattr(Config, "FIREBASE_PASSWORD", None),
                "returnSecureToken": True,
            }, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            id_token = payload.get("idToken")
            refresh_token = payload.get("refreshToken")
            if not id_token:
                raise RuntimeError("Не удалось получить idToken через REST аутентификацию")
            logger.info("✅ REST Firebase auth successful")
            db = RestDBAdapter(database_url, id_token, refresh_token, api_key, "/")
        finally:
            auth_manager.close()

db = wrap_db_adapter(db)


def db_child_by_path(db_adapter, path: str):
    """Создает дочерний адаптер по пути (работает с любым типом адаптера)."""
    for part in path.strip("/").split("/"):
        db_adapter = db_adapter.child(part)
    return db_adapter


# Cheking Users are in Main User Directory in DB
def check_user(message):
    user_id_str = str(message.chat.id)

    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
    create_directory(user_dir)

    # Updated path for cookie.txt
    cookie_src = os.path.join(os.getcwd(), "cookies", "cookie.txt")
    cookie_dest = os.path.join(user_dir, os.path.basename(Config.COOKIE_FILE_PATH))

    # Copy Cookie.txt to the User's Folder if Not Already Present
    if os.path.exists(cookie_src) and not os.path.exists(cookie_dest):
        import shutil
        shutil.copy(cookie_src, cookie_dest)

    # Register the User in the Database if Not Already Registered
    use_firebase = getattr(Config, 'USE_FIREBASE', True)
    if use_firebase:
        user_db = db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("users").get().each()
        users = [user.key() for user in user_db] if user_db else []
        if user_id_str not in users:
            data = {"ID": message.chat.id, "timestamp": math.floor(time.time())}
            db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("users").child(user_id_str).set(data)
    else:
        # В локальном режиме проверяем через локальный кэш
        from DATABASE.cache_db import get_from_local_cache
        users_data = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, "users"])
        users = list(users_data.keys()) if isinstance(users_data, dict) else []
        if user_id_str not in users:
            data = {"ID": message.chat.id, "timestamp": math.floor(time.time())}
            db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("users").child(user_id_str).set(data)


# Checking user is Blocked or not
def is_user_blocked(message):
    messages = safe_get_messages(message.chat.id)
    use_firebase = getattr(Config, 'USE_FIREBASE', True)
    if use_firebase:
        blocked = db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("blocked_users").get().each()
        blocked_users = [int(b_user.key()) for b_user in blocked] if blocked else []
    else:
        # В локальном режиме проверяем через локальный кэш
        from DATABASE.cache_db import get_from_local_cache
        blocked_data = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, "blocked_users"])
        blocked_users = [int(k) for k in blocked_data.keys()] if isinstance(blocked_data, dict) else []
    
    if int(message.chat.id) in blocked_users:
        send_to_all(message, safe_get_messages().DB_USER_BANNED_MSG)
        return True
    else:
        return False


def _build_stats_metadata(message) -> dict:
    metadata = {}
    user = getattr(message, "from_user", None) or getattr(message, "chat", None)
    if user:
        metadata["first_name"] = getattr(user, "first_name", None)
        metadata["last_name"] = getattr(user, "last_name", None)
        metadata["username"] = getattr(user, "username", None)
        metadata["language_code"] = getattr(user, "language_code", None)
    return {k: v for k, v in metadata.items() if v}


def write_logs(message, video_url, video_title):
    messages = safe_get_messages(message.chat.id)
    ts = str(math.floor(time.time()))
    data = {"ID": str(message.chat.id), "timestamp": ts,
            "name": message.chat.first_name, "urls": str(video_url), "title": video_title}
    db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("logs").child(str(message.chat.id)).child(str(ts)).set(data)
    logger.info(safe_get_messages().DB_LOG_FOR_USER_ADDED_MSG)
    try:
        emit_download_event(
            user_id=int(message.chat.id),
            url=str(video_url),
            title=str(video_title),
            timestamp=int(ts),
            metadata=_build_stats_metadata(message),
        )
    except Exception as exc:
        logger.debug(f"[stats] failed to emit download event: {exc}")


# ####################################################################################
# Initialize minimal structure
use_firebase = getattr(Config, 'USE_FIREBASE', True)
_format = {"ID": '0', "timestamp": math.floor(time.time())}
try:
    db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("users").child("0").set(_format)
    db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("blocked_users").child("0").set(_format)
    db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("unblocked_users").child("0").set(_format)
    messages = safe_get_messages(None)
    if use_firebase:
        logger.info(safe_get_messages().DB_DATABASE_CREATED_MSG)
    else:
        logger.info("✅ Локальная база данных инициализирована")
except Exception as e:
    messages = safe_get_messages(None)
    if use_firebase:
        logger.error(safe_get_messages().DB_ERROR_INITIALIZING_BASE_MSG.format(error=e))
    else:
        logger.error(f"Ошибка инициализации локальной базы данных: {e}")

starting_point.append(time.time())
messages = safe_get_messages(None)
logger.info(safe_get_messages().DB_BOT_STARTED_MSG)
