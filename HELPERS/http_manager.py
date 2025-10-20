"""
HTTP Session Manager with forced connection cleanup
Prevents hanging connections and CLOSE-WAIT states
"""

import threading
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from CONFIG.limits import LimitsConfig
from HELPERS.logger import logger


class ManagedHTTPSession:
    """
    HTTP Session with automatic cleanup and connection lifetime limits
    """
    
    def __init__(self, session_name="default", max_lifetime=None):
        self.session_name = session_name
        self.max_lifetime = max_lifetime or LimitsConfig.MAX_HTTP_CONNECTION_LIFETIME
        self.created_at = time.time()
        self._session = None
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
    def _create_session(self):
        """Create a new requests session with proper configuration"""
        session = requests.Session()
        
        # Set headers to minimize connection reuse
        session.headers.update({
            'User-Agent': 'tg-ytdlp-bot/1.0',
            'Connection': 'close'  # Force close connections
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure HTTP adapter with connection limits
        adapter = HTTPAdapter(
            pool_connections=2,      # Minimal connection pools
            pool_maxsize=5,          # Small pool size
            max_retries=retry_strategy,
            pool_block=False,         # Don't block when pool is full
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def get_session(self):
        """Get the current session, creating a new one if needed or expired"""
        with self._lock:
            current_time = time.time()
            
            # Check if session is expired or doesn't exist
            if (self._session is None or 
                current_time - self.created_at > self.max_lifetime):
                
                # Close old session if exists
                if self._session is not None:
                    try:
                        self._session.close()
                        logger.debug(f"Closed expired HTTP session: {self.session_name}")
                    except Exception as e:
                        logger.warning(f"Error closing HTTP session: {e}")
                
                # Create new session
                self._session = self._create_session()
                self.created_at = current_time
                logger.debug(f"Created new HTTP session: {self.session_name}")
                
                # Start cleanup thread if not already running
                if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
                    self._stop_cleanup.clear()
                    self._cleanup_thread = threading.Thread(
                        target=self._cleanup_worker, 
                        daemon=True,
                        name=f"HTTP-Cleanup-{self.session_name}"
                    )
                    self._cleanup_thread.start()
            
            return self._session
    
    def _cleanup_worker(self):
        """Background worker to force cleanup expired sessions"""
        while not self._stop_cleanup.is_set():
            try:
                # Wait for session lifetime or stop event
                self._stop_cleanup.wait(self.max_lifetime)
                
                if not self._stop_cleanup.is_set():
                    # Force cleanup
                    with self._lock:
                        if self._session is not None:
                            try:
                                self._session.close()
                                logger.debug(f"Forced cleanup of HTTP session: {self.session_name}")
                            except Exception as e:
                                logger.warning(f"Error in forced cleanup: {e}")
                            finally:
                                self._session = None
                                self.created_at = time.time()
                                
            except Exception as e:
                logger.error(f"Error in HTTP cleanup worker: {e}")
                break
    
    def close(self):
        """Manually close the session and stop cleanup thread"""
        self._stop_cleanup.set()
        
        with self._lock:
            if self._session is not None:
                try:
                    self._session.close()
                    logger.debug(f"Manually closed HTTP session: {self.session_name}")
                except Exception as e:
                    logger.warning(f"Error manually closing HTTP session: {e}")
                finally:
                    self._session = None
        
        # Wait for cleanup thread to finish
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)
    
    def __enter__(self):
        return self.get_session()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't close here, let the cleanup worker handle it
        pass


# Global session managers for different purposes
_http_managers = {}
_managers_lock = threading.Lock()


def get_managed_session(session_name="default"):
    """
    Get a managed HTTP session by name
    Creates a new manager if it doesn't exist
    """
    with _managers_lock:
        if session_name not in _http_managers:
            _http_managers[session_name] = ManagedHTTPSession(session_name)
        return _http_managers[session_name]


def close_all_sessions():
    """Close all managed HTTP sessions"""
    with _managers_lock:
        for manager in _http_managers.values():
            try:
                manager.close()
            except Exception as e:
                logger.warning(f"Error closing HTTP manager: {e}")
        _http_managers.clear()


def safe_http_get(url, session_name="default", timeout=None, **kwargs):
    """
    Safe HTTP GET with managed session
    """
    timeout = timeout or LimitsConfig.HTTP_REQUEST_TIMEOUT
    manager = get_managed_session(session_name)
    
    try:
        with manager as session:
            response = session.get(url, timeout=timeout, **kwargs)
            return response
    except Exception as e:
        logger.error(f"HTTP GET error for {url}: {e}")
        return None


def safe_http_post(url, session_name="default", timeout=None, **kwargs):
    """
    Safe HTTP POST with managed session
    """
    timeout = timeout or LimitsConfig.HTTP_REQUEST_TIMEOUT
    manager = get_managed_session(session_name)
    
    try:
        with manager as session:
            response = session.post(url, timeout=timeout, **kwargs)
            return response
    except Exception as e:
        logger.error(f"HTTP POST error for {url}: {e}")
        return None
