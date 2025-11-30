"""
Command rate limiter with exponential backoff for spam protection.
Tracks commands per minute and applies increasing cooldowns for repeated violations.
"""
import time
import os
import json
import threading
from typing import Optional, Tuple
from CONFIG.limits import LimitsConfig
from HELPERS.logger import logger

# In-memory storage: {user_id: {'commands': [timestamps], 'violations': count, 'current_cooldown': duration}}
_command_limits: dict = {}
_command_limits_lock = threading.Lock()

# Cooldown storage: {user_id: {'until': timestamp, 'duration': seconds, 'violations': count}}
_command_cooldowns: dict = {}
_command_cooldowns_lock = threading.Lock()

# File for persistence
_COMMAND_LIMITS_FILE = "CONFIG/.command_limits.json"
_COMMAND_COOLDOWNS_FILE = "CONFIG/.command_cooldowns.json"


def _load_from_disk():
    """Load command limits and cooldowns from disk"""
    global _command_limits, _command_cooldowns
    
    # Load command limits
    if os.path.exists(_COMMAND_LIMITS_FILE):
        try:
            with open(_COMMAND_LIMITS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                with _command_limits_lock:
                    _command_limits = {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load command limits: {e}")
            _command_limits = {}
    else:
        _command_limits = {}
    
    # Load cooldowns
    if os.path.exists(_COMMAND_COOLDOWNS_FILE):
        try:
            with open(_COMMAND_COOLDOWNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                with _command_cooldowns_lock:
                    _command_cooldowns = {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load command cooldowns: {e}")
            _command_cooldowns = {}


def _save_to_disk():
    """Save command limits and cooldowns to disk"""
    try:
        os.makedirs(os.path.dirname(_COMMAND_LIMITS_FILE), exist_ok=True)
        
        # Save command limits
        with _command_limits_lock:
            data = {str(k): v for k, v in _command_limits.items()}
        with open(_COMMAND_LIMITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Save cooldowns
        with _command_cooldowns_lock:
            data = {str(k): v for k, v in _command_cooldowns.items()}
        with open(_COMMAND_COOLDOWNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save command limits/cooldowns: {e}")


def _cleanup_old_entries(user_id: int, current_time: float):
    """Remove old command entries outside the time window"""
    with _command_limits_lock:
        if user_id not in _command_limits:
            _command_limits[user_id] = {'commands': [], 'violations': 0}
        
        user_data = _command_limits[user_id]
        
        # Clean commands older than 60 seconds
        user_data['commands'] = [ts for ts in user_data['commands'] if current_time - ts < 60]


def _check_cooldown(user_id: int, current_time: float) -> Optional[Tuple[float, int]]:
    """Check if user is in cooldown. Returns (seconds_remaining, violations_count) or None"""
    with _command_cooldowns_lock:
        if user_id not in _command_cooldowns:
            return None
        
        cooldown = _command_cooldowns[user_id]
        until = cooldown.get('until', 0)
        violations = cooldown.get('violations', 0)
        
        if current_time < until:
            remaining = until - current_time
            return (remaining, violations)
        
        # Cooldown expired, remove it but keep violations count for next violation
        violations = cooldown.get('violations', 0)
        del _command_cooldowns[user_id]
        # Transfer violations to limits storage
        with _command_limits_lock:
            if user_id not in _command_limits:
                _command_limits[user_id] = {'commands': [], 'violations': 0}
            _command_limits[user_id]['violations'] = violations
        _save_to_disk()
        return None


def _set_cooldown(user_id: int, current_time: float, violations: int):
    """Set cooldown for user with exponential backoff"""
    # Calculate cooldown duration: initial * (multiplier ^ violations)
    duration = LimitsConfig.COMMAND_COOLDOWN_INITIAL * (LimitsConfig.COMMAND_COOLDOWN_MULTIPLIER ** violations)
    until = current_time + duration
    
    with _command_cooldowns_lock:
        _command_cooldowns[user_id] = {
            'until': until,
            'duration': duration,
            'violations': violations
        }
    
    # Clear command history for this user
    with _command_limits_lock:
        if user_id in _command_limits:
            _command_limits[user_id]['commands'] = []
    
    _save_to_disk()
    logger.warning(f"Command spam detected for user {user_id}. Cooldown: {duration}s (violations: {violations})")


def check_command_limit(user_id: int, is_admin: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check if user can send another command.
    Returns (allowed: bool, message: Optional[str])
    If not allowed, message contains cooldown info.
    """
    # Admins bypass command limits
    if is_admin:
        return (True, None)
    
    current_time = time.time()
    
    # Check cooldown first
    cooldown_info = _check_cooldown(user_id, current_time)
    if cooldown_info:
        remaining, violations = cooldown_info
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        if minutes > 0:
            msg = f"Too many commands. Cooldown: {minutes}m {seconds}s remaining"
        else:
            msg = f"Too many commands. Cooldown: {seconds}s remaining"
        
        return (False, msg)
    
    # Cleanup old entries
    _cleanup_old_entries(user_id, current_time)
    
    # Check limits
    with _command_limits_lock:
        if user_id not in _command_limits:
            _command_limits[user_id] = {'commands': [], 'violations': 0}
        
        user_data = _command_limits[user_id]
        violations = user_data.get('violations', 0)
        
        # Check command limit
        if len(user_data['commands']) >= LimitsConfig.COMMAND_LIMIT_PER_MINUTE:
            # Increment violations
            violations += 1
            user_data['violations'] = violations
            _set_cooldown(user_id, current_time, violations)
            
            # Calculate cooldown for message
            duration = LimitsConfig.COMMAND_COOLDOWN_INITIAL * (LimitsConfig.COMMAND_COOLDOWN_MULTIPLIER ** violations)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            
            if minutes > 0:
                msg = f"Too many commands (max {LimitsConfig.COMMAND_LIMIT_PER_MINUTE}/minute). Cooldown: {minutes}m {seconds}s"
            else:
                msg = f"Too many commands (max {LimitsConfig.COMMAND_LIMIT_PER_MINUTE}/minute). Cooldown: {seconds}s"
            
            return (False, msg)
        
        # All checks passed, record the command
        user_data['commands'].append(current_time)
        # Reset violations if user behaved well (no violations for a while)
        if violations > 0 and len(user_data['commands']) == 0:
            user_data['violations'] = 0
    
    _save_to_disk()
    return (True, None)


# Load on module import
_load_from_disk()

