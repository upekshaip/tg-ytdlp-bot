# Playlist utilities
# This module contains functions for playlist detection and processing

import re
from HELPERS.logger import logger

def is_playlist_with_range(text: str) -> bool:
    """
    Checks if the text contains a playlist range pattern like *1*3, 1*1000, *5*10, or just * for full playlist.
    Returns True if a range is detected, False otherwise.
    """
    if not isinstance(text, str):
        return False

    # Look for patterns like *1*3, 1*1000, *5*10, or just * for full playlist
    range_pattern = r'\*[0-9]+\*[0-9]+|[0-9]+\*[0-9]+|\*'
    return bool(re.search(range_pattern, text)) 