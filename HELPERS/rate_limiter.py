"""
Rate limiter for URL requests per user.
Tracks URLs per minute, hour, and day with cooldown periods.
"""
import time
import os
import json
import threading
from typing import Optional, Tuple
from CONFIG.config import Config
from CONFIG.limits import LimitsConfig
from HELPERS.logger import logger

# In-memory storage: {user_id: {'minute': [...], 'hour': [...], 'day': [...]}}
_rate_limits: dict = {}
_rate_limits_lock = threading.Lock()

# Cooldown storage: {user_id: {'period': 'minute'|'hour'|'day', 'until': timestamp}}
_cooldowns: dict = {}
_cooldowns_lock = threading.Lock()

# File for persistence
_RATE_LIMITS_FILE = "CONFIG/.rate_limits.json"
_COOLDOWNS_FILE = "CONFIG/.cooldowns.json"


def _load_from_disk():
    """Load rate limits and cooldowns from disk"""
    global _rate_limits, _cooldowns
    
    # Load rate limits
    if os.path.exists(_RATE_LIMITS_FILE):
        try:
            with open(_RATE_LIMITS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                with _rate_limits_lock:
                    _rate_limits = {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load rate limits: {e}")
            _rate_limits = {}
    else:
        _rate_limits = {}
    
    # Load cooldowns
    if os.path.exists(_COOLDOWNS_FILE):
        try:
            with open(_COOLDOWNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                with _cooldowns_lock:
                    _cooldowns = {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load cooldowns: {e}")
            _cooldowns = {}


def _save_to_disk():
    """Save rate limits and cooldowns to disk"""
    try:
        os.makedirs(os.path.dirname(_RATE_LIMITS_FILE), exist_ok=True)
        
        # Save rate limits
        with _rate_limits_lock:
            data = {str(k): v for k, v in _rate_limits.items()}
        with open(_RATE_LIMITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Save cooldowns
        with _cooldowns_lock:
            data = {str(k): v for k, v in _cooldowns.items()}
        with open(_COOLDOWNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save rate limits/cooldowns: {e}")


def _cleanup_old_entries(user_id: int, current_time: float):
    """Remove old entries outside the time windows"""
    with _rate_limits_lock:
        if user_id not in _rate_limits:
            _rate_limits[user_id] = {'minute': [], 'hour': [], 'day': []}
        
        user_data = _rate_limits[user_id]
        
        # Clean minute entries (older than 60 seconds)
        user_data['minute'] = [ts for ts in user_data['minute'] if current_time - ts < 60]
        
        # Clean hour entries (older than 3600 seconds)
        user_data['hour'] = [ts for ts in user_data['hour'] if current_time - ts < 3600]
        
        # Clean day entries (older than 86400 seconds)
        user_data['day'] = [ts for ts in user_data['day'] if current_time - ts < 86400]


def _check_cooldown(user_id: int, current_time: float) -> Optional[Tuple[str, float]]:
    """Check if user is in cooldown. Returns (period, seconds_remaining) or None"""
    with _cooldowns_lock:
        if user_id not in _cooldowns:
            return None
        
        cooldown = _cooldowns[user_id]
        until = cooldown.get('until', 0)
        
        if current_time < until:
            period = cooldown.get('period', 'unknown')
            remaining = until - current_time
            return (period, remaining)
        
        # Cooldown expired, remove it
        del _cooldowns[user_id]
        _save_to_disk()
        return None


def _set_cooldown(user_id: int, period: str, current_time: float):
    """Set cooldown for user until end of the period"""
    period_durations = {
        'minute': LimitsConfig.RATE_LIMIT_COOLDOWN_MINUTE,
        'hour': LimitsConfig.RATE_LIMIT_COOLDOWN_HOUR,
        'day': LimitsConfig.RATE_LIMIT_COOLDOWN_DAY
    }
    
    duration = period_durations.get(period, LimitsConfig.RATE_LIMIT_COOLDOWN_MINUTE)
    until = current_time + duration
    
    with _cooldowns_lock:
        _cooldowns[user_id] = {'period': period, 'until': until}
    
    _save_to_disk()


def check_rate_limit(user_id: int, is_admin: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check if user can send another URL.
    Returns (allowed: bool, message: Optional[str])
    If not allowed, message contains cooldown info.
    """
    # Admins bypass rate limits
    if is_admin:
        return (True, None)
    
    current_time = time.time()
    
    # Check cooldown first
    cooldown_info = _check_cooldown(user_id, current_time)
    if cooldown_info:
        period, remaining = cooldown_info
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        if period == 'day':
            msg = f"Rate limit exceeded. Cooldown: {hours}h {minutes}m {seconds}s remaining"
        elif period == 'hour':
            msg = f"Rate limit exceeded. Cooldown: {minutes}m {seconds}s remaining"
        else:
            msg = f"Rate limit exceeded. Cooldown: {seconds}s remaining"
        
        return (False, msg)
    
    # Cleanup old entries
    _cleanup_old_entries(user_id, current_time)
    
    # Check limits
    with _rate_limits_lock:
        user_data = _rate_limits[user_id]
        
        # Check minute limit
        if len(user_data['minute']) >= LimitsConfig.RATE_LIMIT_PER_MINUTE:
            _set_cooldown(user_id, 'minute', current_time)
            remaining = LimitsConfig.RATE_LIMIT_COOLDOWN_MINUTE
            minutes = int(remaining // 60)
            return (False, f"Rate limit exceeded (max {LimitsConfig.RATE_LIMIT_PER_MINUTE} URLs/minute). Cooldown: {minutes}m remaining")
        
        # Check hour limit
        if len(user_data['hour']) >= LimitsConfig.RATE_LIMIT_PER_HOUR:
            _set_cooldown(user_id, 'hour', current_time)
            remaining = LimitsConfig.RATE_LIMIT_COOLDOWN_HOUR
            hours = int(remaining // 3600)
            return (False, f"Rate limit exceeded (max {LimitsConfig.RATE_LIMIT_PER_HOUR} URLs/hour). Cooldown: {hours}h remaining")
        
        # Check day limit
        if len(user_data['day']) >= LimitsConfig.RATE_LIMIT_PER_DAY:
            _set_cooldown(user_id, 'day', current_time)
            remaining = LimitsConfig.RATE_LIMIT_COOLDOWN_DAY
            hours = int(remaining // 3600)
            return (False, f"Rate limit exceeded (max {LimitsConfig.RATE_LIMIT_PER_DAY} URLs/day). Cooldown: {hours}h remaining")
        
        # All checks passed, record the request
        user_data['minute'].append(current_time)
        user_data['hour'].append(current_time)
        user_data['day'].append(current_time)
    
    _save_to_disk()
    return (True, None)


# Load on module import
_load_from_disk()

