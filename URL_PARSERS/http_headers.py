# ####################################################################################
# HTTP Headers Parser for yt-dlp
# ####################################################################################

import re
import json
from typing import Dict, Optional, Tuple
from HELPERS.logger import logger

def parse_http_headers_from_url(text: str) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Parse HTTP headers from URL text with -opt http_headers: format.
    
    Args:
        text (str): The input text containing URL and optional headers
        
    Returns:
        Tuple[str, Optional[Dict[str, str]]]: (clean_url, headers_dict)
        
    Examples:
        Input: "https://example.com -opt http_headers:{\"Referer\":\"https://web.alphaplatform.net/Home/Alpha\"}"
        Output: ("https://example.com", {"Referer": "https://web.alphaplatform.net/Home/Alpha"})
        
        Input: "https://example.com"
        Output: ("https://example.com", None)
    """
    if not isinstance(text, str):
        return text, None
    
    # Pattern to match URL followed by -opt http_headers: and JSON
    pattern = r'^(.*?)\s+-opt\s+http_headers:\s*(\{.*\})\s*$'
    match = re.match(pattern, text.strip(), re.DOTALL)
    
    if not match:
        # No headers found, return original text
        return text.strip(), None
    
    url_part = match.group(1).strip()
    headers_json = match.group(2).strip()
    
    try:
        # Parse JSON headers
        headers_dict = json.loads(headers_json)
        
        # Validate that it's a dictionary with string values
        if not isinstance(headers_dict, dict):
            logger.warning(f"HTTP headers must be a dictionary, got: {type(headers_dict)}")
            return text.strip(), None
            
        # Convert all values to strings
        clean_headers = {}
        for key, value in headers_dict.items():
            if not isinstance(key, str):
                logger.warning(f"HTTP header key must be string, got: {type(key)} for key '{key}'")
                continue
            clean_headers[key] = str(value)
        
        logger.info(f"Parsed HTTP headers from URL: {url_part} -> {clean_headers}")
        return url_part, clean_headers
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse HTTP headers JSON: {e}, text: {headers_json}")
        return text.strip(), None
    except Exception as e:
        logger.error(f"Unexpected error parsing HTTP headers: {e}")
        return text.strip(), None

def add_http_headers_to_ytdl_opts(ytdl_opts: dict, headers: Optional[Dict[str, str]]) -> dict:
    """
    Add HTTP headers to yt-dlp options, replacing referer if specified.
    
    Args:
        ytdl_opts (dict): yt-dlp options dictionary
        headers (Optional[Dict[str, str]]): HTTP headers to add
        
    Returns:
        dict: Updated yt-dlp options
    """
    if not headers:
        return ytdl_opts
    
    # Add http_headers to ytdl_opts
    ytdl_opts['http_headers'] = headers
    
    # If Referer is specified in headers, replace the default referer
    if 'Referer' in headers:
        ytdl_opts['referer'] = headers['Referer']
        logger.info(f"Replaced referer with custom header: {headers['Referer']}")
    
    logger.info(f"Added HTTP headers to yt-dlp options: {headers}")
    return ytdl_opts

def extract_url_and_headers(text: str) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Convenience function that combines URL extraction and header parsing.
    This is the main function to use for processing user input.
    
    Args:
        text (str): Input text that may contain URL and headers
        
    Returns:
        Tuple[str, Optional[Dict[str, str]]]: (clean_url, headers_dict)
    """
    return parse_http_headers_from_url(text)
