#!/usr/bin/env python3
"""
Universal thumbnail downloader for various video services
"""

import os
import re
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple
from CONFIG.config import Config
from HELPERS.logger import logger


def extract_service_info(url: str) -> Tuple[str, str]:
    """
    Extract service type and video ID from URL
    Returns: (service_type, video_id)
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path
    
    # VK
    if 'vk.com' in netloc:
        if '/video' in path:
            match = re.search(r'/video(-?\d+_\d+)', path)
            if match:
                return 'vk', match.group(1)
    
    # TikTok
    elif 'tiktok.com' in netloc:
        if '/video/' in path:
            match = re.search(r'/video/(\d+)', path)
            if match:
                return 'tiktok', match.group(1)
    
    # Twitter/X
    elif any(x in netloc for x in ['twitter.com', 'x.com']):
        if '/status/' in path:
            match = re.search(r'/status/(\d+)', path)
            if match:
                return 'twitter', match.group(1)
    
    # Facebook
    elif 'facebook.com' in netloc:
        if '/reel/' in path:
            match = re.search(r'/reel/(\d+)', path)
            if match:
                return 'facebook', match.group(1)
        elif '/watch/' in path:
            match = re.search(r'v=(\d+)', parsed.query)
            if match:
                return 'facebook', match.group(1)
    
    # Pornhub
    elif any(x in netloc for x in ['pornhub.com', 'pornhub.org']):
        if '/view_video.php' in path:
            match = re.search(r'viewkey=([^&]+)', parsed.query)
            if match:
                return 'pornhub', match.group(1)
        elif '/video' in path:
            # Alternative Pornhub URL format
            match = re.search(r'/video/([^/?]+)', path)
            if match:
                return 'pornhub', match.group(1)
    
    return 'unknown', ''


def download_vk_thumbnail(video_id: str, dest: str) -> bool:
    """Download VK video thumbnail"""
    try:
        # VK doesn't have direct thumbnail URLs, but we can try to get from video info
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to download VK thumbnail: {e}")
        return False


def download_tiktok_thumbnail(video_id: str, dest: str) -> bool:
    """Download TikTok video thumbnail"""
    try:
        # TikTok thumbnails are usually in video metadata, not direct URLs
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to download TikTok thumbnail: {e}")
        return False


def download_twitter_thumbnail(video_id: str, dest: str) -> bool:
    """Download Twitter/X video thumbnail"""
    try:
        # Twitter thumbnails are usually in video metadata, not direct URLs
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to download Twitter thumbnail: {e}")
        return False


def download_facebook_thumbnail(video_id: str, dest: str) -> bool:
    """Download Facebook video thumbnail"""
    try:
        # Facebook thumbnails are usually in video metadata, not direct URLs
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to download Facebook thumbnail: {e}")
        return False


def download_pornhub_thumbnail(video_id: str, dest: str) -> bool:
    """Download Pornhub video thumbnail"""
    try:
        # Pornhub thumbnails are usually in video metadata, not direct URLs
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to download Pornhub thumbnail: {e}")
        return False


def download_thumbnail(url: str, dest: str) -> bool:
    """
    Universal thumbnail downloader for various video services
    Returns True if thumbnail was downloaded successfully, False otherwise
    """
    try:
        service, video_id = extract_service_info(url)
        
        if not video_id:
            logger.warning(f"Could not extract video ID from URL: {url}")
            return False
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        
        # Try service-specific thumbnail download
        success = False
        if service == 'vk':
            success = download_vk_thumbnail(video_id, dest)
        elif service == 'tiktok':
            success = download_tiktok_thumbnail(video_id, dest)
        elif service == 'twitter':
            success = download_twitter_thumbnail(video_id, dest)
        elif service == 'facebook':
            success = download_facebook_thumbnail(video_id, dest)
        elif service == 'pornhub':
            success = download_pornhub_thumbnail(video_id, dest)
        
        if success:
            logger.info(f"Successfully downloaded {service} thumbnail to {dest}")
            return True
        
        # If service-specific download failed, return False to use fallback
        logger.info(f"Service-specific thumbnail download failed for {service}, will use fallback")
        return False
        
    except Exception as e:
        logger.error(f"Error in universal thumbnail downloader: {e}")
        return False


def get_thumbnail_from_telegram_embed(url: str, dest: str) -> bool:
    """
    Attempt to extract thumbnail from Telegram's video embed
    This is a placeholder for future implementation
    """
    try:
        # TODO: Implement Telegram embed thumbnail extraction
        # This would require:
        # 1. Getting the embed data from Telegram
        # 2. Extracting thumbnail URL from embed
        # 3. Downloading the thumbnail
        
        # For now, return False to use fallback
        return False
    except Exception as e:
        logger.warning(f"Failed to get Telegram embed thumbnail: {e}")
        return False
