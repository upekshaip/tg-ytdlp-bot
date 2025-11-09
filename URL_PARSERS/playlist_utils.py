# Playlist utilities
# This module contains functions for playlist detection and processing

import re
from HELPERS.logger import logger

def is_playlist_with_range(text: str) -> bool:
    """
    Checks if the text contains a playlist range pattern like *1*3, 1*1000, *5*10, *-1*-100, or just * for full playlist.
    Returns True if a range is detected, False otherwise.
    """
    if not isinstance(text, str):
        return False

    # Look for patterns like *1*3, 1*1000, *5*10, *-1*-100, or just * for full playlist (поддерживаем отрицательные числа)
    range_pattern = r'\*-?\d+\*-?\d+|-?\d+\*-?\d+|\*'
    return bool(re.search(range_pattern, text)) 