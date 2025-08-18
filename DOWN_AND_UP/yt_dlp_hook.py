# --- receiving formats and metadata via yt-dlp ---
import os
import yt_dlp
from CONFIG.config import Config
from HELPERS.logger import logger
from HELPERS.filesystem_hlp import create_directory
from URL_PARSERS.nocookie import is_no_cookie_domain

def get_video_formats(url, user_id=None, playlist_start_index=1):
    ytdl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'no_warnings': True,
        'extract_flat': False,
        'simulate': True,
        'playlist_items': str(playlist_start_index),    
        'extractor_args': {
            'generic': ['impersonate=chrome'],
            'youtubetab': ['skip=authcheck']
        },
        'referer': url,
        'geo_bypass': True,
        'check_certificate': False,
        'live_from_start': True
    }
    if user_id is not None:
        user_dir = os.path.join("users", str(user_id))
        # Check the availability of cookie.txt in the user folder
        user_cookie_path = os.path.join(user_dir, "cookie.txt")
        if os.path.exists(user_cookie_path):
            cookie_file = user_cookie_path
        else:
            # If not in the user folder, we copy from the global folder
            global_cookie_path = Config.COOKIE_FILE_PATH
            if os.path.exists(global_cookie_path):
                try:
                    create_directory(user_dir)
                    import shutil
                    shutil.copy2(global_cookie_path, user_cookie_path)
                    logger.info(f"Copied global cookie file to user {user_id} folder for format detection")
                    cookie_file = user_cookie_path
                except Exception as e:
                    logger.error(f"Failed to copy global cookie file for user {user_id}: {e}")
                    cookie_file = None
            else:
                cookie_file = None
        
        # We check whether to use —no-Cookies for this domain
        if is_no_cookie_domain(url):
            ytdl_opts['cookiefile'] = None  # Equivalent-No-Cookies
            logger.info(f"Using --no-cookies for domain in get_video_formats: {url}")
        elif cookie_file:
            ytdl_opts['cookiefile'] = cookie_file
    try:
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info and info.get('entries'):
            return info['entries'][0]
        return info
    except yt_dlp.utils.DownloadError as e:
        error_text = str(e)
        return {'error': error_text}
    except Exception as e:
        return {'error': str(e)}


# YT-DLP HOOK

def ytdlp_hook(d):
    logger.info(d['status'])
