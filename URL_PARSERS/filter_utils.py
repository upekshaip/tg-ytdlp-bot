# Filter utilities for yt-dlp
import yt_dlp
from CONFIG.config import Config
from CONFIG.limits import LimitsConfig
from HELPERS.logger import logger

def create_smart_match_filter():
    """
    Create a smart yt-dlp match_filter that allows downloading when:
    1. The video is not live (!is_live) — only if ENABLE_LIVE_STREAM_BLOCKING = True
    2. Duration is known and <= MAX_VIDEO_DURATION
    3. Duration is unknown (duration is None) — allow download
    
    Returns:
        function: Filter function for yt-dlp
    """
    def match_filter(info_dict):
        """
        Smart filter for yt-dlp.
        
        Args:
            info_dict (dict): Video info dict
            
        Returns:
            str or None: None if allowed, otherwise an error message
        """
        try:
            # Some extractors may return a list in early stages; allow silently.
            if not isinstance(info_dict, dict):
                return None
            # Check live streams (only if detection is enabled)
            is_live = info_dict.get('is_live', False)
            if is_live and LimitsConfig.ENABLE_LIVE_STREAM_BLOCKING:
                return "LIVE_STREAM_DETECTED"
            
            # Read duration
            duration = info_dict.get('duration')
            
            # If duration is unknown, allow download
            if duration is None:
                logger.info("Duration not available, allowing download")
                return None
            
            # Allow completed live streams
            was_live = info_dict.get('was_live', False)
            if was_live and not is_live:
                logger.info(f"Completed live stream detected (duration: {duration}s), allowing download")
                return None
            
            # If duration is known, enforce limit
            if duration and duration > Config.MAX_VIDEO_DURATION:
                return f"Video too long: {duration}s > {Config.MAX_VIDEO_DURATION}s"
            
            # All checks passed
            return None
            
        except Exception as e:
            logger.error(f"Error in match_filter: {e}")
            # On errors, allow download
            return None
    
    return match_filter

def create_legacy_match_filter():
    """
    Create the legacy match_filter for backward compatibility.
    Respects ENABLE_LIVE_STREAM_BLOCKING.
    
    Returns:
        function: Filter function for yt-dlp
    """
    if LimitsConfig.ENABLE_LIVE_STREAM_BLOCKING:
        return yt_dlp.utils.match_filter_func(f'!is_live & duration <= {Config.MAX_VIDEO_DURATION}')
    else:
        # If live stream detection is disabled, only check duration
        return yt_dlp.utils.match_filter_func(f'duration <= {Config.MAX_VIDEO_DURATION}')
