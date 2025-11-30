
import os
import math
import hashlib
import subprocess
import shutil
import logging
import time
import re
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import resize
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_all, send_to_logger
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.safe_messeger import safe_forward_messages
from COMMANDS.format_cmd import get_user_mkv_preference
from pyrogram import enums

# Get app instance for decorators
app = get_app()

def get_ffmpeg_path():
    messages = safe_get_messages(None)
    """Get FFmpeg path - first try system PATH, then fallback to local binary"""
    import shutil
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # First try to find ffmpeg in system PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        # Fallback to local binary
        if os.name == 'nt':  # Windows
            ffmpeg_path = os.path.join(project_root, "ffmpeg.exe")
        else:  # Linux/Unix
            ffmpeg_path = os.path.join(project_root, "ffmpeg")
        
        if not os.path.exists(ffmpeg_path):
            logger.error(safe_get_messages(None).FFMPEG_NOT_FOUND_MSG)
            return None
    
    return ffmpeg_path

def normalize_path_for_ffmpeg(path, for_ffmpeg=True):
    """Normalize path for FFmpeg compatibility across platforms"""
    if os.name == 'nt':  # Windows
        # For Windows, normalize the path first
        normalized = os.path.normpath(path)
        
        # Convert to forward slashes for FFmpeg compatibility
        normalized = normalized.replace('\\', '/')
        
        # Only add quotes if this is for FFmpeg command line
        if for_ffmpeg and (' ' in normalized or any(char in normalized for char in ['(', ')', '[', ']', '{', '}', '&', '|', ';', '"', "'"])):
            # For Windows, use double quotes and escape internal quotes
            escaped_path = normalized.replace('"', '\\"')
            normalized = f'"{escaped_path}"'
        return normalized
    else:  # Linux/Unix
        # For Linux, normalize the path and use absolute path
        normalized = os.path.normpath(path)
        return os.path.abspath(normalized)

def create_safe_filename(original_path, prefix="safe", extension=None):
    """Create a safe filename for cross-platform compatibility"""
    import hashlib
    import time
    import re
    
    # Get original filename and extension
    base_name = os.path.basename(original_path)
    if extension is None:
        name, ext = os.path.splitext(base_name)
    else:
        name = os.path.splitext(base_name)[0]
        ext = extension
    
    # Create safe name using hash and timestamp
    file_hash = hashlib.md5(original_path.encode('utf-8')).hexdigest()[:8]
    timestamp = int(time.time())
    
    # Clean the original name - remove or replace problematic characters
    # Keep only alphanumeric characters, spaces, dots, and common punctuation
    safe_chars = re.sub(r'[^\w\s\-\.\(\)]', '_', name)
    # Limit length to avoid path issues
    safe_chars = safe_chars[:50] if len(safe_chars) > 50 else safe_chars
    
    # Use cleaned name + hash + timestamp for maximum compatibility
    safe_name = f"{prefix}_{safe_chars}_{file_hash}_{timestamp}{ext}"
    
    # Ensure no double underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    
    return safe_name

def test_path_handling():
    """Test function to verify path handling with special characters"""
    # Use universal path format
    test_path = os.path.join("users", "7360853", "Ценам приказано не расти _ Послушаются ли они (Eng.en.srt")
    
    logger.info(f"Testing path: {test_path}")
    logger.info(f"Path exists: {os.path.exists(test_path)}")
    logger.info(f"Platform: {os.name}")
    
    # Test universal path handling
    normalized_path = os.path.normpath(test_path)
    logger.info(f"Normalized path: {normalized_path}")
    
    return True

def get_ytdlp_path():
    messages = safe_get_messages(None)
    """Get yt-dlp binary path - first try system PATH, then fallback to local binary.
    This is used only for functions that need the binary directly (like /cookies_from_browser)"""
    import shutil
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # First try to find yt-dlp in system PATH
    ytdlp_path = shutil.which('yt-dlp')
    if not ytdlp_path:
        # Fallback to local binary
        if os.name == 'nt':  # Windows
            ytdlp_path = os.path.join(project_root, "yt-dlp.exe")
        else:  # Linux/Unix
            ytdlp_path = os.path.join(project_root, "yt-dlp")
        
        if not os.path.exists(ytdlp_path):
            logger.error(safe_get_messages(None).YTDLP_NOT_FOUND_MSG)
            return None
    
    return ytdlp_path

def split_video_2(dir, video_name, video_path, video_size, max_size, duration, user_id):
    messages = safe_get_messages(None)
    """
    Split a video into multiple parts

    Args:
        dir: Directory path
        video_name: Name for the video
        video_path: Path to the video file
        video_size: Size of the video in bytes
        max_size: Maximum size for each part
        duration: Duration of the video

    Returns:
        dict: Dictionary with video parts information
    """
    rounds = (math.floor(video_size / max_size)) + 1
    n = duration / rounds
    caption_lst = []
    path_lst = []

    try:
        if rounds and rounds > 20:
            logger.warning(safe_get_messages(user_id).FFMPEG_VIDEO_SPLIT_EXCESSIVE_MSG.format(rounds=rounds))

        for x in range(rounds):
            start_time = x * n
            end_time = (x * n) + n

            # Ensure end_time doesn't exceed duration
            end_time = min(end_time, duration)

            cap_name = video_name + " - Part " + str(x + 1)
            target_name = os.path.join(dir, cap_name + ".mp4")

            caption_lst.append(cap_name)
            path_lst.append(target_name)

            try:
                # Use progress logging
                logger.info(safe_get_messages(user_id).FFMPEG_SPLITTING_VIDEO_PART_MSG.format(current=x+1, total=rounds, start_time=start_time, end_time=end_time))
                ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=target_name)

                # Verify the split was successful
                if not os.path.exists(target_name) or os.path.getsize(target_name) == 0:
                    logger.error(safe_get_messages(user_id).FFMPEG_FAILED_CREATE_SPLIT_PART_MSG.format(part=x+1, target_name=target_name))
                else:
                    logger.info(safe_get_messages(user_id).FFMPEG_SUCCESSFULLY_CREATED_SPLIT_PART_MSG.format(part=x+1, target_name=target_name, size=os.path.getsize(target_name)))

            except Exception as e:
                logger.error(safe_get_messages(user_id).FFMPEG_ERROR_SPLITTING_VIDEO_PART_MSG.format(part=x+1, error=e))
                # If a part fails, we continue with the others

        split_vid_dict = {
            "video": caption_lst,
            "path": path_lst
        }

        logger.info(safe_get_messages(user_id).FFMPEG_VIDEO_SPLIT_SUCCESS_MSG.format(count=len(path_lst)))
        return split_vid_dict

    except Exception as e:
        logger.error(safe_get_messages(user_id).FFMPEG_ERROR_VIDEO_SPLITTING_PROCESS_MSG.format(error=e))
        # Return what we have so far
        split_vid_dict = {
            "video": caption_lst,
            "path": path_lst,
            "duration": duration
        }
        return split_vid_dict


def get_duration_thumb_(dir, video_path, thumb_name):
    messages = safe_get_messages(None)
    # Generate a short unique name for the thumbnail
    thumb_hash = hashlib.md5(thumb_name.encode()).hexdigest()[:10]
    thumb_dir = os.path.abspath(os.path.join(dir, thumb_hash + ".jpg"))
    try:
        width, height, duration = get_video_info_ffprobe(video_path)
        duration = int(duration)
        orig_w = width if width and width > 0 else 1920
        orig_h = height if height and height > 0 else 1080
    except Exception as e:
        logger.error(safe_get_messages(None).FFMPEG_FFPROBE_BYPASS_ERROR_MSG.format(video_path=video_path, error=e))
        import traceback
        logger.error(traceback.format_exc())
        duration = 0
        orig_w, orig_h = 1920, 1080  # Default dimensions
    
    # Determine optimal thumbnail size based on video aspect ratio
    aspect_ratio = orig_w / orig_h
    max_dimension = 640  # Maximum width or height
    
    if aspect_ratio and aspect_ratio > 1.5:  # Wide/horizontal video (16:9, etc.)
        thumb_w = max_dimension
        thumb_h = int(max_dimension / aspect_ratio)
    elif aspect_ratio and aspect_ratio < 0.75:  # Tall/vertical video (9:16, etc.)
        thumb_h = max_dimension
        thumb_w = int(max_dimension * aspect_ratio)
    else:  # Square-ish video (1:1, 4:3, etc.)
        if orig_w >= orig_h:
            thumb_w = max_dimension
            thumb_h = int(max_dimension / aspect_ratio)
        else:
            thumb_h = max_dimension
            thumb_w = int(max_dimension * aspect_ratio)
    
    # Ensure minimum size
    thumb_w = max(thumb_w, 240)
    thumb_h = max(thumb_h, 240)
    
    # Create thumbnail using FFmpeg instead of moviepy
    try:
        # Get FFmpeg path using the common function
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            logger.error(safe_get_messages(None).FFMPEG_NOT_FOUND_MSG)
            create_default_thumbnail(thumb_dir, thumb_w, thumb_h)
            return duration, thumb_dir
        
        ffmpeg_command = [
            ffmpeg_path,
            "-y",
            "-i", video_path,
            "-ss", "2",         # Seek to 2 Seconds
            "-vframes", "1",    # Capture 1 Frame
            "-vf", f"scale={thumb_w}:{thumb_h}",  # Scale to exact thumbnail size
            thumb_dir
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True, encoding='utf-8', errors='replace')
    except Exception as e:
        logger.error(safe_get_messages(None).FFMPEG_ERROR_CREATING_THUMBNAIL_WITH_FFMPEG_MSG.format(error=e))
        # Create default thumbnail as fallback
        create_default_thumbnail(thumb_dir, thumb_w, thumb_h)
    
    return duration, thumb_dir

def get_duration_thumb(message, dir_path, video_path, thumb_name):
    user_id = message.chat.id
    messages = safe_get_messages(user_id)
    """
    Captures a thumbnail at 2 seconds into the video and retrieves video duration.
    Creates thumbnail with same aspect ratio as video (no black bars).

    Args:
        message: The message object
        dir_path: Directory path for the thumbnail
        video_path: Path to the video file
        thumb_name: Name for the thumbnail

    Returns:
        tuple: (duration, thumbnail_path) or None if error
    """
    # Generate a short unique name for the thumbnail
    thumb_hash = hashlib.md5(thumb_name.encode()).hexdigest()[:10]
    thumb_dir = os.path.abspath(os.path.join(dir_path, thumb_hash + ".jpg"))

    # FFPROBE COMMAND to GET Video Dimensions and Duration
    ffprobe_size_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]
    
    ffprobe_duration_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        # First check if video file exists
        if not os.path.exists(video_path):
            logger.error(safe_get_messages(user_id).FFMPEG_VIDEO_FILE_NOT_EXISTS_MSG.format(video_path=video_path))
            send_to_all(message, safe_get_messages(user_id).VIDEO_FILE_NOT_FOUND_MSG.format(filename=os.path.basename(video_path)))
            return None

        # Get video dimensions
        try:
            size_result = subprocess.check_output(ffprobe_size_command, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='replace').strip()
        except UnicodeDecodeError:
            # Fallback with error handling
            size_result = subprocess.check_output(ffprobe_size_command, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace').decode('utf-8', errors='replace').strip()
        # Robust parse of dimensions like "1920x1080"; tolerate any trailing garbage
        dims_match = re.search(r"(\d+)\s*x\s*(\d+)", size_result)
        if dims_match:
            try:
                orig_w = int(dims_match.group(1))
                orig_h = int(dims_match.group(2))
            except Exception as e:
                logger.error(safe_get_messages(user_id).FFMPEG_ERROR_PARSING_DIMENSIONS_MSG.format(size_result=size_result, error=e))
                orig_w, orig_h = 1920, 1080
        else:
            # Fallback to default horizontal orientation
            orig_w, orig_h = 1920, 1080
            logger.warning(safe_get_messages(user_id).FFMPEG_COULD_NOT_DETERMINE_DIMENSIONS_MSG.format(size_result=size_result, width=orig_w, height=orig_h))
        
        # Determine optimal thumbnail size based on video aspect ratio
        aspect_ratio = orig_w / orig_h
        max_dimension = 640  # Maximum width or height
        
        if aspect_ratio and aspect_ratio > 1.5:  # Wide/horizontal video (16:9, etc.)
            thumb_w = max_dimension
            thumb_h = int(max_dimension / aspect_ratio)
        elif aspect_ratio and aspect_ratio < 0.75:  # Tall/vertical video (9:16, etc.)
            thumb_h = max_dimension
            thumb_w = int(max_dimension * aspect_ratio)
        else:  # Square-ish video (1:1, 4:3, etc.)
            if orig_w >= orig_h:
                thumb_w = max_dimension
                thumb_h = int(max_dimension / aspect_ratio)
            else:
                thumb_h = max_dimension
                thumb_w = int(max_dimension * aspect_ratio)
        
        # Ensure minimum size
        thumb_w = max(thumb_w, 240)
        thumb_h = max(thumb_h, 240)
        
        # FFMPEG Command to create thumbnail with calculated dimensions
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", "2",         # Seek to 2 Seconds
            "-vframes", "1",    # Capture 1 Frame
            "-vf", f"scale={thumb_w}:{thumb_h}",  # Scale to exact thumbnail size
            thumb_dir
        ]

        # Run ffmpeg command to create thumbnail
        ffmpeg_result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if ffmpeg_result.returncode != 0:
            logger.error(safe_get_messages(user_id).FFMPEG_ERROR_CREATING_THUMBNAIL_MSG.format(stderr=ffmpeg_result.stderr))

        # Run ffprobe command to get duration
        try:
            result = subprocess.check_output(ffprobe_duration_command, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='replace')
        except UnicodeDecodeError:
            # Fallback with error handling
            result = subprocess.check_output(ffprobe_duration_command, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace').decode('utf-8', errors='replace')

        try:
            # Extract duration robustly from any stdout (handle proxychains noise)
            text = str(result)
            # Prefer last numeric in the output as ffprobe prints duration alone
            matches = re.findall(r"(\d+(?:\.\d+)?)", text)
            if matches:
                duration = int(float(matches[-1]))
            else:
                raise ValueError("No numeric duration found in ffprobe output")
        except (ValueError, TypeError) as e:
            logger.error(safe_get_messages(user_id).FFMPEG_ERROR_PARSING_DURATION_MSG.format(error=e, result=result))
            duration = 0

        # Verify thumbnail was created
        if not os.path.exists(thumb_dir):
            logger.warning(safe_get_messages(user_id).FFMPEG_THUMBNAIL_NOT_CREATED_MSG.format(thumb_dir=thumb_dir))
            # Create a blank thumbnail as fallback
            create_default_thumbnail(thumb_dir, thumb_w, thumb_h)

        return duration, thumb_dir
    except subprocess.CalledProcessError as e:
        logger.error(safe_get_messages(user_id).FFMPEG_COMMAND_EXECUTION_ERROR_MSG.format(error=e.stderr if hasattr(e, 'stderr') else e))
        send_to_all(message, safe_get_messages(user_id).VIDEO_PROCESSING_ERROR_MSG.format(error=str(e)))
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing video: {e}")
        send_to_all(message, safe_get_messages(user_id).VIDEO_PROCESSING_ERROR_MSG.format(error=str(e)))
        return None

def create_default_thumbnail(thumb_path, width=480, height=480):
    """Create a default thumbnail when normal thumbnail creation fails"""
    try:
        # Get FFmpeg path using the common function
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            logger.error("ffmpeg not found in PATH or project directory.")
            return
        
        # Create a black image with specified dimensions (square by default)
        ffmpeg_cmd = [
            ffmpeg_path, "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}",
            "-frames:v", "1",
            thumb_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        logger.info(f"Created default {width}x{height} thumbnail at {thumb_path}")
    except Exception as e:
        logger.error(f"Failed to create default thumbnail: {e}")


def ensure_utf8_srt(srt_path):
    """Ensure SRT file is in UTF-8 encoding"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return srt_path
    except UnicodeDecodeError:
        try:
            # Try to detect encoding and convert to UTF-8
            import chardet
            with open(srt_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'cp1252'
            
            with open(srt_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Write back as UTF-8
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return srt_path
        except Exception as e:
            logger.error(f"Error converting SRT to UTF-8: {e}")
            return None


def force_fix_arabic_encoding(srt_path, lang):
    """Fix Arabic subtitle encoding issues"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply Arabic-specific fixes if needed
        if lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
            # Add any Arabic-specific text processing here
            pass
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return srt_path
    except Exception as e:
        logger.error(f"Error fixing Arabic encoding: {e}")
        return None


def ffmpeg_extract_subclip(video_path, start_time, end_time, targetname):
    """Extract a subclip from video using FFmpeg"""
    try:
        # Get FFmpeg path using the common function
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            logger.error("ffmpeg not found in PATH or project directory.")
            return False
        
        # Check if video file exists first (without quotes)
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        # Normalize paths for universal compatibility (with quotes for FFmpeg)
        normalized_video_path = normalize_path_for_ffmpeg(video_path, for_ffmpeg=True)
        normalized_targetname = normalize_path_for_ffmpeg(targetname, for_ffmpeg=True)
        
        cmd = [
            ffmpeg_path, '-y',
            '-i', normalized_video_path,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c', 'copy',
            normalized_targetname
        ]
        
        logger.info(f"Running ffmpeg extract command: {' '.join(cmd)}")
        logger.info(f"Original video path: {video_path}")
        logger.info(f"Normalized video path: {normalized_video_path}")
        logger.info(f"Original target path: {targetname}")
        logger.info(f"Normalized target path: {normalized_targetname}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        logger.info(f"FFmpeg extract completed successfully for {targetname}")
        logger.info(f"Output file size: {os.path.getsize(targetname) if os.path.exists(targetname) else 'File not found'}")
        return True
    except subprocess.CalledProcessError as e:
        error_details = ""
        if e.stderr:
            error_details = f"stderr: {e.stderr[:500]}"
        if e.stdout:
            error_details += f"\nstdout: {e.stdout[:500]}" if error_details else f"stdout: {e.stdout[:500]}"
        
        logger.error(f"FFmpeg extract error (code {e.returncode}): {error_details if error_details else str(e)}")
        
        # Try to identify common error types
        error_text = (error_details + str(e)).lower()
        if "invalid argument" in error_text or "invalid data" in error_text:
            logger.error("FFmpeg error: Invalid argument - video format may be incompatible")
        elif "no such file" in error_text or "cannot find" in error_text:
            logger.error("FFmpeg error: File not found")
        elif "permission denied" in error_text:
            logger.error("FFmpeg error: Permission denied")
        elif "codec" in error_text and ("not found" in error_text or "unsupported" in error_text):
            logger.error("FFmpeg error: Codec not found or unsupported")
        
        return False
    except Exception as e:
        logger.error(f"Error extracting subclip: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


# ####################################################################################
# ####################################################################################

def get_video_info_ffprobe(video_path):
    import json
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-show_entries', 'format=duration',
            '-of', 'json', video_path
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            data = json.loads(result.stdout)
            width = data['streams'][0]['width'] if data['streams'] else 0
            height = data['streams'][0]['height'] if data['streams'] else 0
            duration = float(data['format']['duration']) if 'format' in data and 'duration' in data['format'] else 0
            return width, height, duration
    except Exception as e:
        logger.error(f'ffprobe error: {e}')
        return 0, 0, 0



def embed_subs_to_video(video_path, user_id, tg_update_callback=None, app=None, message=None):
    messages = safe_get_messages(user_id)
    """
    Burning (hardcode) subtitles in a video file, if there is any .SRT file and subs.txt
    tg_update_callback (Progress: Float, ETA: StR) - Function for updating the status in Telegram
    """
    try:
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        user_dir = os.path.join("users", str(user_id))
        subs_file = os.path.join(user_dir, "subs.txt")
        if not os.path.exists(subs_file):
            logger.info(f"No subs.txt for user {user_id}, skipping embed_subs_to_video")
            return False
        
        with open(subs_file, "r", encoding="utf-8") as f:
            subs_lang = f.read().strip()
        if not subs_lang or subs_lang == "OFF":
            logger.info(f"Subtitles disabled for user {user_id}")
            return False
        
        video_dir = os.path.dirname(video_path)
        
        # Если контейнер MKV — выполняем «софт»-встраивание дорожки субтитров без прожига
        try:
            mkv_selected = bool(get_user_mkv_preference(user_id))
        except Exception:
            mkv_selected = False
        is_mkv_file = video_path.lower().endswith('.mkv')

        if is_mkv_file or mkv_selected:
            # Убедимся, что есть SRT (в UTF-8)
            srt_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.srt')]
            if not srt_files:
                logger.info(f"No .srt files found in {video_dir} for soft-mux MKV")
                return False
            subs_path = os.path.join(video_dir, srt_files[0])
            subs_path = ensure_utf8_srt(subs_path)
            if not subs_path or not os.path.exists(subs_path) or os.path.getsize(subs_path) == 0:
                logger.error(f"Subtitle file invalid for MKV soft-mux: {subs_path}")
                return False

            # Подготавливаем путь вывода
            video_base = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_base}_with_subs_temp.mkv")

            # Собираем MKV: видео/аудио копируем, субтитры как srt
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                logger.error("ffmpeg not found for MKV soft-mux")
                return False
            cmd = [
                ffmpeg_path, '-y',
                '-i', video_path,
                '-i', subs_path,
                '-c', 'copy',
                '-c:s', 'srt',
                '-map', '0',
                '-map', '1:0'
            ]
            # Язык субтитров, если указан
            if subs_lang and subs_lang != 'OFF':
                cmd += ['-metadata:s:s:0', f'language={subs_lang}']
            cmd += [output_path]

            try:
                logger.info(f"Running ffmpeg soft-mux (MKV): {' '.join(cmd)}")
                subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            except Exception as e:
                logger.error(f"FFmpeg soft-mux failed: {e}")
                return False

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error("Soft-mux output missing or empty")
                return False

            # Безопасно заменяем исходный файл на результат (оставляем .mkv путь)
            backup_path = video_path + ".backup"
            try:
                os.rename(video_path, backup_path)
                os.rename(output_path, video_path)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            except Exception as e:
                logger.error(f"Error replacing MKV after soft-mux: {e}")
                # Откат
                try:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(backup_path):
                        os.rename(backup_path, video_path)
                except Exception:
                    pass
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False

            logger.info("Soft subtitle mux into MKV completed successfully")
            return True

        # We get video parameters via FFPRobe (жёсткое прожигание для MP4 и прочих контейнеров)
        width, height, total_time = get_video_info_ffprobe(video_path)
        if width == 0 or height == 0:
            logger.error(f"Unable to determine video resolution via ffprobe: width={width}, height={height}")
            return False
        original_size = os.path.getsize(video_path)

        # Checking the duration of the video
        if total_time and total_time > Config.MAX_SUB_DURATION:
            logger.info(f"Video duration too long for subtitles: {total_time} sec")
            return False

        # Checking the file size
        original_size_mb = original_size / (1024 * 1024)
        if original_size_mb and original_size_mb > Config.MAX_SUB_SIZE:
            logger.info(f"Video file too large for subtitles: {original_size_mb:.2f} MB")
            return False

        # Video quality testing on the smallest side
        # Logue video parameters before checking quality
        logger.info(f"Quality check: width={width}, height={height}, min_side={min(width, height)}, limit={Config.MAX_SUB_QUALITY}")
        if min(width, height) > Config.MAX_SUB_QUALITY:
            logger.info(f"Video quality too high for subtitles: {width}x{height}, min side: {min(width, height)}p > {Config.MAX_SUB_QUALITY}p")
            return False

        # --- Simplified search: take any .SRT file in the folder ---
        srt_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.srt')]
        if not srt_files:
            logger.info(f"No .srt files found in {video_dir}")
            return False
        
        subs_path = os.path.join(video_dir, srt_files[0])
        if not os.path.exists(subs_path):
            logger.error(f"Subtitle file not found: {subs_path}")
            return False

        # Always bring .SRT to UTF-8
        subs_path = ensure_utf8_srt(subs_path)
        if not subs_path or not os.path.exists(subs_path) or os.path.getsize(subs_path) == 0:
            logger.error(f"Subtitle file after ensure_utf8_srt is missing or empty: {subs_path}")
            return False

        # Forcibly correcting Arab cracies
        if subs_lang in {'ar', 'fa', 'ur', 'ps', 'iw', 'he'}:
            subs_path = force_fix_arabic_encoding(subs_path, subs_lang)
        if not subs_path or not os.path.exists(subs_path) or os.path.getsize(subs_path) == 0:
            logger.error(f"Subtitle file after force_fix_arabic_encoding is missing or empty: {subs_path}")
            return False
        
        video_base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_base}_with_subs_temp.mp4")
        
        # We get the duration of the video via FFPRobe
        def get_duration(path):
            messages = safe_get_messages(user_id)
            try:
                import json
                result = subprocess.run([
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'json', path
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return float(data['format']['duration'])
            except Exception as e:
                logger.error(f"ffprobe error: {e}")
            return None
        
        # Field of subtitles with improved styling - using Arial Black font and black 75% background
        subs_path_escaped = subs_path.replace("'", "'\\''")
        # Use Arial Black font with black 75% background and white text
        filter_arg = f"subtitles='{subs_path_escaped}':force_style='FontName=Arial Black,FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,BackColour=&H80000000,Outline=2,Shadow=1,MarginV=25'"
        cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-vf', filter_arg,
            '-c:a', 'copy',
            output_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        progress = 0.0
        last_update = time.time()
        eta = "?"
        time_pattern = re.compile(r'time=([0-9:.]+)')
        
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            logger.info(line.strip())
            match = time_pattern.search(line)
            if match and total_time:
                t = match.group(1)
                # Transform T (hh: mm: ss.xx) in seconds
                h, m, s = 0, 0, 0.0
                parts = t.split(':')
                if len(parts) == 3:
                    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
                elif len(parts) == 2:
                    m, s = int(parts[0]), float(parts[1])
                elif len(parts) == 1:
                    s = float(parts[0])
                cur_sec = h * 3600 + m * 60 + s
                progress = min(cur_sec / total_time, 1.0)
                # ETA
                if progress and progress > 0:
                    elapsed = time.time() - last_update
                    eta_sec = int((1.0 - progress) * (elapsed / progress)) if progress and progress > 0 else 0
                    eta = f"{eta_sec//60}:{eta_sec%60:02d}"
                # Update every 10 seconds or with a change in progress> 1%
                if tg_update_callback and (time.time() - last_update > 10 or progress >= 1.0):
                    tg_update_callback(progress, eta)
                    last_update = time.time()
        
        proc.wait()
        
        if proc.returncode != 0:
            # Try to read any remaining output for error details
            remaining_output = proc.stdout.read() if proc.stdout else ""
            error_details = remaining_output[:500] if remaining_output else "No error details available"
            
            logger.error(f"FFmpeg error: process exited with code {proc.returncode}")
            logger.error(f"FFmpeg error details: {error_details}")
            
            # Try to identify common error types
            error_lower = error_details.lower()
            if "invalid argument" in error_lower or "invalid data" in error_lower:
                logger.error("FFmpeg error: Invalid argument or data - video/subtitle format may be incompatible")
            elif "no such file" in error_lower or "cannot find" in error_lower:
                logger.error("FFmpeg error: File not found - check if video or subtitle file exists")
            elif "permission denied" in error_lower:
                logger.error("FFmpeg error: Permission denied - check file permissions")
            elif "codec" in error_lower and ("not found" in error_lower or "unsupported" in error_lower):
                logger.error("FFmpeg error: Codec not found or unsupported")
            elif "out of memory" in error_lower or "cannot allocate" in error_lower:
                logger.error("FFmpeg error: Out of memory - video may be too large")
            
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Check that the file exists and is not empty
        if not os.path.exists(output_path):
            logger.error("Output file does not exist after ffmpeg")
            return False
        
        # We are waiting a little so that the file will definitely complete the recording
        time.sleep(1)
        
        output_size = os.path.getsize(output_path)
        original_size = os.path.getsize(video_path)
        
        if output_size == 0:
            logger.error("Output file is empty")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # We check that the final file is not too small (there should be at least 50% of the original)
        if output_size and output_size < original_size * 0.5:
            logger.error(f"Output file too small: {output_size} bytes (original: {original_size} bytes)")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Safely replace the file
        backup_path = video_path + ".backup"
        try:
            os.rename(video_path, backup_path)   # Create a backup
            os.rename(output_path, video_path)   # Rename the result
            os.remove(backup_path)               # Delete backup
        except Exception as e:
            logger.error(f"Error replacing video file: {e}")
            # Restore the source file
            if os.path.exists(backup_path):
                os.rename(backup_path, video_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
        # Send .SRT to the user before removing
        if os.path.exists(subs_path):
            try:
                if app is not None and message is not None:
                    sent_msg = app.send_document(
                        chat_id=user_id,
                        document=subs_path,
                        caption="<blockquote>💬 Subtitles SRT-file</blockquote>",
                        reply_parameters=enums.ReplyParameters(message_id=message.id) if hasattr(enums, 'ReplyParameters') else None,
                        parse_mode=enums.ParseMode.HTML
                    )
                    from HELPERS.logger import get_log_channel
                    safe_forward_messages(get_log_channel("video"), user_id, [sent_msg.id])
                    send_to_logger(message, safe_get_messages(user_id).SUBS_SENT_MSG) 
            except Exception as e:
                logger.error(f"Error sending srt file: {e}")
            try:
                os.remove(subs_path)
            except Exception as e:
                logger.error(f"Error deleting srt file: {e}")
        
        logger.info("Successfully burned-in subtitles")
        return True
        
    except Exception as e:
        logger.error(f"Error in embed_subs_to_video: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
