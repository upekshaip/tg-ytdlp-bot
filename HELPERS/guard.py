"""
Guard decorators for async handlers to prevent event loop blocking
"""
import asyncio
import logging
from functools import wraps
import sys
import os

# Add the parent directory to the path to import CONFIG
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CONFIG.LANGUAGES.language_router import get_message

# NO GLOBAL SEMAPHORE - removed to allow true parallelism
# Limiting is now handled by concurrent_limiter per-user
# from CONFIG.limits import LimitsConfig
# SEM = asyncio.Semaphore(LimitsConfig.GUARD_SEMAPHORE_LIMIT)  # REMOVED - was blocking all users!

def safe_handler(timeout=300):
    """
    Simple decorator for basic error handling without blocking execution
    
    This decorator provides:
    - Basic error handling: catches and logs errors gracefully
    - No timeout protection (to avoid blocking commands)
    - No global semaphore (concurrent_limiter handles limiting)
    
    Args:
        timeout: Not used (kept for compatibility)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.exception("Handler %s failed: %s", func.__name__, e)
                # Try to send error message to user if possible
                try:
                    if args and hasattr(args[0], 'reply_text'):
                        # Get user ID from the message object
                        user_id = getattr(args[0], 'from_user', {}).get('id') if hasattr(args[0], 'from_user') else None
                        error_msg = get_message('GUARD_ERROR_MSG', user_id)
                        await args[0].reply_text(error_msg)
                except (AttributeError, TypeError, ValueError):
                    pass
        return wrapper
    return decorator

async def async_subprocess(*args, timeout=1800):
    """
    Run subprocess asynchronously without blocking event loop
    
    Args:
        *args: Command and arguments to run
        timeout: Maximum time in seconds for subprocess execution
    
    Returns:
        Tuple of (stdout, stderr) as bytes
    """
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
        if process.returncode != 0:
            raise RuntimeError(f"Subprocess failed with return code {process.returncode}: {stderr.decode('utf-8', errors='ignore')}")
        return stdout, stderr
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.wait()
        raise RuntimeError(f"Subprocess timed out after {timeout}s") from exc

def cpu_bound(func, *args, **kwargs):
    """
    Run CPU-bound function in thread pool to avoid blocking event loop
    
    Args:
        func: Function to run
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Coroutine that will return function result
    """
    return asyncio.to_thread(func, *args, **kwargs)
