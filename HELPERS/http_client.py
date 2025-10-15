"""
HTTP client utilities with proper session management to prevent socket leaks
"""
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

# Global session manager
_session_manager = None

class HTTPSessionManager:
    """Manages HTTP sessions to prevent socket leaks"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        async with self._lock:
            if self._session is None or self._session.closed:
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector,
                    headers={'User-Agent': 'tg-ytdlp-bot/1.0'}
                )
            return self._session
    
    async def close(self):
        """Close HTTP session"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
    
    async def __aenter__(self):
        return await self.get_session()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

def get_session_manager() -> HTTPSessionManager:
    """Get global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = HTTPSessionManager()
    return _session_manager

@asynccontextmanager
async def http_session():
    """Context manager for HTTP session"""
    manager = get_session_manager()
    session = await manager.get_session()
    try:
        yield session
    finally:
        # Don't close here - let manager handle it
        pass

async def fetch_json(url: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """
    Fetch JSON from URL with proper session management
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for aiohttp
    
    Returns:
        JSON response as dict
    """
    async with http_session() as session:
        try:
            async with session.get(url, timeout=timeout, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Failed to fetch JSON from {url}: {e}")
            raise

async def fetch_text(url: str, timeout: int = 30, **kwargs) -> str:
    """
    Fetch text from URL with proper session management
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for aiohttp
    
    Returns:
        Response text
    """
    async with http_session() as session:
        try:
            async with session.get(url, timeout=timeout, **kwargs) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logging.error(f"Failed to fetch text from {url}: {e}")
            raise

async def fetch_bytes(url: str, timeout: int = 30, **kwargs) -> bytes:
    """
    Fetch bytes from URL with proper session management
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for aiohttp
    
    Returns:
        Response bytes
    """
    async with http_session() as session:
        try:
            async with session.get(url, timeout=timeout, **kwargs) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as e:
            logging.error(f"Failed to fetch bytes from {url}: {e}")
            raise

async def close_all_sessions():
    """Close all HTTP sessions"""
    global _session_manager
    if _session_manager:
        await _session_manager.close()
        _session_manager = None
