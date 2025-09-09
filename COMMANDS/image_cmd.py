# ===================== /img command =====================
import os
import re
import subprocess
import tempfile
import threading
import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters, InputMediaPhoto, InputMediaVideo, InputPaidMediaPhoto, InputPaidMediaVideo
from pyrogram import enums
from HELPERS.logger import send_to_logger, logger, get_log_channel
from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
import HELPERS.safe_messeger as sm
from DOWN_AND_UP.gallery_dl_hook import (
    get_image_info,
    download_image,
    get_total_media_count,
    download_image_range,
    download_image_range_cli,
)
from HELPERS.filesystem_hlp import create_directory
from COMMANDS.proxy_cmd import is_proxy_enabled
from CONFIG.limits import LimitsConfig
from CONFIG.config import Config
from HELPERS.limitter import is_user_in_channel
from HELPERS.porn import is_porn
from COMMANDS.nsfw_cmd import should_apply_spoiler
from DATABASE.cache_db import save_to_image_cache, get_cached_image_posts, get_cached_image_post_indices

# Get app instance for decorators
app = get_app()

def _save_album_now(url: str, album_index: int, message_ids: list):
    try:
        logger.info(f"[IMG CACHE] About to save album: index={album_index}, ids={message_ids}")
        save_to_image_cache(url, album_index, message_ids)
        logger.info(f"[IMG CACHE] Save requested for index={album_index}")
    except Exception as e:
        logger.error(f"[IMG CACHE] Save failed for index={album_index}: {e}")
def is_image_url(url):
    """Check if URL is likely an image URL"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg']
    url_lower = url.lower()
    
    # Check for image extensions
    for ext in image_extensions:
        if ext in url_lower:
            return True
    
    # Check for common image hosting domains
    image_domains = [
        'imgur.com', 'i.imgur.com', 'flickr.com', 'deviantart.com',
        'pinterest.com', 'instagram.com', 'twitter.com', 'x.com',
        'reddit.com', 'imgbb.com', 'postimg.cc', 'ibb.co',
        'drive.google.com', 'dropbox.com', 'mega.nz'
    ]
    
    for domain in image_domains:
        if domain in url_lower:
            return True
    
    return False

def convert_file_to_telegram_format(file_path):
    """
    Convert unsupported file formats to Telegram-supported formats
    Returns the converted file path or original path if no conversion needed
    """
    if not os.path.exists(file_path):
        return file_path
    
    file_ext = os.path.splitext(file_path)[1].lower()
    file_dir = os.path.dirname(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    try:
        # Convert WebP images to JPEG
        if file_ext == '.webp':
            output_path = os.path.join(file_dir, f"{file_name}.jpg")
            cmd = [
                'ffmpeg', '-i', file_path, 
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure dimensions are divisible by 2
                '-c:v', 'mjpeg', '-q:v', '2',  # Use MJPEG codec for JPEG output
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Converted WebP to JPEG: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert WebP: {result.stderr}")
                return file_path
        
        # Convert WebM videos to MP4 (add thumbnail to avoid black preview)
        elif file_ext == '.webm':
            output_path = os.path.join(file_dir, f"{file_name}.mp4")
            # We will generate/send thumbnail later during sending
            cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Converted WebM to MP4: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert WebM: {result.stderr}")
                return file_path
        
        # Convert other unsupported video formats to MP4
        elif file_ext in ['.avi', '.mov', '.mkv', '.flv']:
            output_path = os.path.join(file_dir, f"{file_name}.mp4")
            # We will generate/send thumbnail later during sending
            cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Converted {file_ext} to MP4: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert {file_ext}: {result.stderr}")
                return file_path
        
        # Convert other unsupported image formats to JPEG
        elif file_ext in ['.bmp', '.tiff']:
            output_path = os.path.join(file_dir, f"{file_name}.jpg")
            cmd = [
                'ffmpeg', '-i', file_path,
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',  # Ensure dimensions are divisible by 2
                '-c:v', 'mjpeg', '-q:v', '2',  # Use MJPEG codec for JPEG output
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Converted {file_ext} to JPEG: {file_path} -> {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to convert {file_ext}: {result.stderr}")
                return file_path
        
        # No conversion needed
        else:
            return file_path
            
    except subprocess.TimeoutExpired:
        logger.error(f"Conversion timeout for {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Conversion error for {file_path}: {e}")
        return file_path

@app.on_message(filters.command("img") & filters.private)
def image_command(app, message):
    """Handle /img command for downloading images"""
    user_id = message.chat.id
    text = message.text.strip()
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        try:
            text_join = f"{Config.TO_USE_MSG}\n \n{Config.CREDITS_MSG}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=Config.SUBSCRIBE_CHANNEL_URL)]])
            safe_send_message(user_id, text_join, reply_markup=keyboard)
        except Exception:
            pass
        return
    
    # Extract URL from command
    if len(text.split()) < 2:
        # Show help if no URL provided
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔚Close", callback_data="img_help|close")]
        ])
        safe_send_message(
            user_id,
            "<b>🖼 Image Download Command</b>\n\n"
            "Usage: <code>/img URL</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/img https://example.com/image.jpg</code>\n"
            "• <code>/img 11-20 https://example.com/album</code>\n"
            "• <code>/img 11- https://example.com/album</code>\n"
            "• <code>/img https://vk.com/wall-160916577_408508</code>\n"
            "• <code>/img https://2ch.hk/fd/res/1747651.html</code>\n"
            "• <code>/img https://imgur.com/abc123</code>\n\n"
            "<b>Supported platforms (examples):</b>\n"
            "<blockquote>vk, 2ch, 35photo, 4chan, 500px, ArtStation, Boosty, Civitai, Cyberdrop, DeviantArt, Discord, Facebook, Fansly, Instagram, Patreon, Pinterest, Reddit, TikTok, Tumblr, Twitter/X, JoyReactor, etc. — <a href=\"https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md\">full list</a></blockquote>"
            "Also see: /audio, /vid, /help, /playlist, /settings",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id)
        )
        send_to_logger(message, "Showed /img help")
        return
    
    # Extract optional range and URL from command
    # Allow: /img URL  OR  /img 11-20 URL  OR  /img 11- URL
    manual_range = None  # tuple (start:int, end:int|None)
    rest = text.split(' ', 1)[1].strip()
    parts = rest.split()
    if len(parts) >= 2:
        rng_candidate = parts[0]
        if re.fullmatch(r"\d+-\d*", rng_candidate):
            start_str, end_str = rng_candidate.split('-', 1)
            try:
                start_val = int(start_str)
                end_val = int(end_str) if end_str != '' else None
                if start_val >= 1:
                    manual_range = (start_val, end_val)
                    url = ' '.join(parts[1:]).strip()
                else:
                    url = rest
            except Exception:
                url = rest
        else:
            url = rest
    else:
        url = rest
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        safe_send_message(
            user_id,
            Config.INVALID_URL_MSG,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id)
        )
        send_to_logger(message, f"Invalid URL provided: {url}")
        return
    
    # Check if user has proxy enabled
    use_proxy = is_proxy_enabled(user_id)
    
    # Send initial message
    status_msg = safe_send_message(
        user_id,
        Config.CHECKING_CACHE_MSG.format(url=url),
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
    # Pin the status message for visibility
    try:
        app.pin_chat_message(user_id, status_msg.id, disable_notification=True)
    except Exception:
        pass

    # Default NSFW flag before any analysis
    nsfw_flag = False
    # Early cache serve before any analysis/downloading
    try:
        requested_indices = None
        if manual_range is not None:
            start_i, end_i = manual_range
            if end_i is not None:
                requested_indices = list(range(int(start_i), int(end_i) + 1))
            else:
                cached_all = sorted(list(get_cached_image_post_indices(url)))
                requested_indices = [i for i in cached_all if i >= int(start_i)]
        cached_map = get_cached_image_posts(url, requested_indices)
        if cached_map:
            for album_idx in sorted(cached_map.keys()):
                ids = cached_map[album_idx]
                try:
                    kwargs = {}
                    thread_id = getattr(message, 'message_thread_id', None)
                    if thread_id:
                        kwargs['message_thread_id'] = thread_id
                    try:
                        sm.safe_forward_messages(user_id, get_log_channel("image", nsfw=nsfw_flag, paid=True), ids, **kwargs)
                    except Exception:
                        app.forward_messages(user_id, get_log_channel("image", nsfw=nsfw_flag, paid=True), ids, **kwargs)
                except Exception as _e:
                    logger.warning(f"Failed to forward cached album {album_idx}: {_e}")
            try:
                safe_edit_message_text(
                    user_id, status_msg.id,
                    Config.SENT_FROM_CACHE_MSG.format(count=len(cached_map)),
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
            send_to_logger(message, f"Reposted {len(cached_map)} cached albums for {url}")
            return
    except Exception as _e:
        logger.warning(f"Image cache forward (early) failed: {_e}")
    
    try:
        # Get image information first
        image_info = get_image_info(url, user_id, use_proxy)
        # NSFW detection using domain and metadata
        try:
            info_title = (image_info or {}).get('title') if isinstance(image_info, dict) else None
            info_desc = (image_info or {}).get('description') if isinstance(image_info, dict) else None
            info_caption = (image_info or {}).get('caption') if isinstance(image_info, dict) else None
        except Exception:
            info_title = info_desc = info_caption = None
        try:
            nsfw_flag = bool(is_porn(url, info_title, info_desc, info_caption))
        except Exception:
            nsfw_flag = False
        
        if not image_info:
            safe_edit_message_text(
                user_id, status_msg.id,
                Config.FAILED_ANALYZE_MSG.format(url=url) +
                "The URL might not be accessible or not contain a valid image.",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, f"Failed to analyze image URL: {url}")
            return
        
        # Update status message
        title = image_info.get('title', 'Unknown')
        safe_edit_message_text(
            user_id, status_msg.id,
            Config.DOWNLOADING_IMAGE_MSG +
            f"<b>Title:</b> {title}\n"
            f"<b>URL:</b> <code>{url}</code>",
            parse_mode=enums.ParseMode.HTML
        )
        # Try to serve from cache again (after analysis) — safe redundancy
        try:
            requested_indices = None
            if manual_range is not None:
                start_i, end_i = manual_range
                if end_i is not None:
                    requested_indices = list(range(int(start_i), int(end_i) + 1))
                else:
                    cached_all = sorted(list(get_cached_image_post_indices(url)))
                    requested_indices = [i for i in cached_all if i >= int(start_i)]
            cached_map = get_cached_image_posts(url, requested_indices)
            if cached_map:
                for album_idx in sorted(cached_map.keys()):
                    ids = cached_map[album_idx]
                    try:
                        kwargs = {}
                        thread_id = getattr(message, 'message_thread_id', None)
                        if thread_id:
                            kwargs['message_thread_id'] = thread_id
                        try:
                            sm.safe_forward_messages(user_id, get_log_channel("image", nsfw=nsfw_flag, paid=True), ids, **kwargs)
                        except Exception:
                            app.forward_messages(user_id, get_log_channel("image", nsfw=nsfw_flag, paid=True), ids, **kwargs)
                    except Exception as _e:
                        logger.warning(f"Failed to forward cached album {album_idx}: {_e}")
                # If we found anything in cache, finish early (do not re-download)
                try:
                    safe_edit_message_text(
                        user_id,
                        status_msg.id,
                        Config.SENT_FROM_CACHE_MSG.format(count=len(cached_map)),
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass
                send_to_logger(message, f"Reposted {len(cached_map)} cached albums for {url}")
                return
        except Exception as _e:
            logger.warning(f"Image cache forward failed: {_e}")
        
        # Create user directory
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        # Admin users have no limit, regular users have MAX_IMG_FILES limit
        is_admin = int(user_id) in Config.ADMIN
        total_limit = float('inf') if is_admin else LimitsConfig.MAX_IMG_FILES
        logger.info(f"[IMG] User {user_id} is admin: {is_admin}, limit: {'unlimited' if is_admin else total_limit}")
        
        # Determine expected total via --get-urls analog
        detected_total = None
        if manual_range is None or manual_range[1] is None:
            detected_total = get_total_media_count(url, user_id, use_proxy)
        if detected_total and detected_total > 0:
            total_expected = detected_total if is_admin else min(detected_total, LimitsConfig.MAX_IMG_FILES)
        # Streaming download: run range-based batches (1-10, 11-20, ...) scoped to a unique per-run directory
        run_dir = os.path.join("users", str(user_id), f"run_{int(time.time())}")
        create_directory(run_dir)
        files_to_cleanup = []

        def _run_download():
            try:
                # We ignore the return; files will appear while it runs
                download_image(url, user_id, use_proxy, user_dir)
            except Exception as _:
                pass

        # We'll not start full download thread; we'll pull ranges to enforce batching

        batch_size = 10
        sent_message_ids = []
        seen_files = set()
        photos_videos_buffer = []  # store (converted_path, type, original_path)
        others_buffer = []  # store (converted_path, original_path)
        total_downloaded = 0
        total_sent = 0
        album_index = 0  # index of posts we send (albums only)
        # is_admin and total_limit already defined above
        # Using detected_total if present; else metadata-based fallback
        total_expected = locals().get('total_expected') or None
        try:
            for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                if isinstance(image_info.get(key), int) and image_info.get(key) > 0:
                    total_expected = image_info.get(key) if is_admin else min(image_info.get(key), total_limit)
                    break
        except Exception:
            pass

        def update_status():
            try:
                safe_edit_message_text(
                    user_id,
                    status_msg.id,
                    Config.DOWNLOADING_MSG +
                    f"Downloaded: <b>{total_downloaded}</b> / <b>{total_expected or total_limit}</b>\n"
                    f"Sent: <b>{total_sent}</b>\n"
                    f"Pending to send: <b>{len(photos_videos_buffer) + len(others_buffer)}</b>",
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass

        gallery_dl_dir = run_dir
        last_status_update = 0.0
        # Seed current_start and upper bound from manual range if provided
        current_start = 1
        manual_end_cap = None
        if manual_range is not None:
            current_start = manual_range[0]
            # Upper cap: if user provided end, respect it (but not above limit for non-admins)
            if manual_range[1] is not None:
                manual_end_cap = manual_range[1] if is_admin else min(manual_range[1], total_limit)
                total_expected = manual_end_cap  # show as expected
        # helper to run one range and wait for files to appear
        def run_and_collect(next_end: int):
            range_expr = f"{current_start}-{next_end}"
            # Prefer CLI to enforce strict range behavior across gallery-dl versions
            logger.info(f"Prepared range: {range_expr}")
            ok = download_image_range_cli(url, range_expr, user_id, use_proxy, output_dir=run_dir)
            if not ok:
                logger.warning(f"CLI range download failed or rejected for {range_expr}, trying Python API.")
                return download_image_range(url, range_expr, user_id, use_proxy, run_dir)
            return True

        while True:
            # If buffer has room for a new batch, trigger next range
            if len(photos_videos_buffer) < batch_size:
                upper_cap = manual_end_cap or total_expected
                if upper_cap and current_start > upper_cap:
                    pass
                else:
                    next_end = current_start + batch_size - 1
                    if upper_cap:
                        next_end = min(next_end, upper_cap)
                    run_and_collect(next_end)
                    current_start = next_end + 1
            # Find new files
            if os.path.exists(gallery_dl_dir):
                for root, _, files in os.walk(gallery_dl_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file_path in seen_files:
                            continue
                        # Only consider media-like files
                        if not file.lower().endswith((
                            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
                            '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv',
                            '.mp3', '.wav', '.ogg', '.m4a',
                            '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z'
                        )):
                            continue
                        # Skip incomplete/zero-byte files
                        try:
                            if os.path.getsize(file_path) == 0:
                                continue
                        except Exception:
                            continue
                        seen_files.add(file_path)
                        total_downloaded += 1

                        # Enforce cap (but not for admins)
                        if not is_admin and total_downloaded > total_limit:
                            continue

                        # Convert if needed, then classify
                        original_path = file_path
                        converted = convert_file_to_telegram_format(file_path)
                        files_to_cleanup.append(converted)
                        if converted != original_path:
                            files_to_cleanup.append(original_path)
                        ext = os.path.splitext(converted)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                            photos_videos_buffer.append((converted, 'photo', original_path))
                        elif ext in ['.mp4']:
                            photos_videos_buffer.append((converted, 'video', original_path))
                        elif ext in ['.avi', '.mov', '.mkv', '.webm', '.flv']:
                            # Try to convert to mp4 if not already
                            converted = convert_file_to_telegram_format(converted)
                            ext2 = os.path.splitext(converted)[1].lower()
                            if ext2 != '.mp4':
                                # keep as document if still not mp4
                                others_buffer.append((converted, original_path))
                            else:
                                photos_videos_buffer.append((converted, 'video', original_path))
                        else:
                            others_buffer.append((converted, original_path))

                        # Send status occasionally
                        now = time.time()
                        if now - last_status_update > 1.5:
                            update_status()
                            last_status_update = now

                        # If we have 10 media for album, send
                        if len(photos_videos_buffer) >= batch_size:
                            media_group = []
                            group_items = photos_videos_buffer[:batch_size]
                            for p, t, _orig in group_items:
                                if t == 'photo':
                                    # No spoiler in groups, only in private chats for paid media
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    media_group.append(InputMediaPhoto(p, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                                else:
                                    # generate thumbnail for better preview
                                    thumb = None
                                    try:
                                        thumb = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '.jpg')
                                        subprocess.run([
                                            'ffmpeg', '-y', '-i', p, '-vf', 'thumbnail,scale=640:-1', '-frames:v', '1', thumb
                                        ], capture_output=True, text=True, timeout=30)
                                    except Exception:
                                        thumb = None
                                    # No spoiler in groups, only in private chats for paid media
                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                    if thumb and os.path.exists(thumb):
                                        media_group.append(InputMediaVideo(p, thumb=thumb, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                                    else:
                                        media_group.append(InputMediaVideo(p, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                            try:
                                # For paid media, only send in private chats (not groups/channels)
                                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                if nsfw_flag and is_private_chat:
                                    # Send each file individually as paid media (Telegram doesn't support paid media groups)
                                    sent = []
                                    for m in media_group:
                                        try:
                                            if isinstance(m, InputMediaPhoto):
                                                paid_msg = app.send_paid_media(
                                    user_id,
                                                    media=[InputPaidMediaPhoto(media=m.media)],
                                                    star_count=LimitsConfig.NSFW_STAR_COST,
                                                    payload=str(Config.STAR_RECEIVER),
                                                    reply_parameters=ReplyParameters(message_id=message.id)
                                                )
                                            else:
                                                # Try to use existing thumb; if none, generate one for cover
                                                _cover = getattr(m, 'thumb', None)
                                                if not _cover:
                                                    try:
                                                        import subprocess
                                                        _cover = os.path.join(os.path.dirname(m.media), os.path.splitext(os.path.basename(m.media))[0] + '.jpg')
                                                        subprocess.run([
                                                            'ffmpeg','-y','-i', m.media,
                                                            '-vf','thumbnail,scale=640:-1','-frames:v','1', _cover
                                                        ], capture_output=True, text=True, timeout=30)
                                                        if not os.path.exists(_cover):
                                                            _cover = None
                                                    except Exception:
                                                        _cover = None
                                                try:
                                                    paid_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[InputPaidMediaVideo(media=m.media, cover=_cover)],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                except TypeError:
                                                    paid_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[InputPaidMediaVideo(media=m.media)],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                            if isinstance(paid_msg, list):
                                                sent.extend(paid_msg)
                                            elif paid_msg is not None:
                                                sent.append(paid_msg)
                                        except Exception as e:
                                            logger.error(f"Failed to send individual paid media: {e}")
                                            # Fallback to regular media
                                            if isinstance(m, InputMediaPhoto):
                                                fallback_msg = app.send_photo(
                                                    user_id,
                                                    photo=m.media,
                                                    caption=m.caption,
                                                    has_spoiler=False,
                                                    reply_parameters=ReplyParameters(message_id=message.id)
                                                )
                                            else:
                                                fallback_msg = app.send_video(
                                                    user_id,
                                                    video=m.media,
                                                    caption=m.caption,
                                                    duration=m.duration,
                                                    width=m.width,
                                                    height=m.height,
                                                    thumb=m.thumb,
                                                    has_spoiler=False,
                                    reply_parameters=ReplyParameters(message_id=message.id),
                                    message_thread_id=getattr(message, 'message_thread_id', None)
                                                )
                                            sent.extend(fallback_msg)
                                else:
                                    # In groups/channels or non-NSFW content, send as regular media group
                                    sent = app.send_media_group(
                                        user_id,
                                        media=media_group,
                                        reply_parameters=ReplyParameters(message_id=message.id)
                                )
                                sent_message_ids.extend([m.id for m in sent])
                                total_sent += len(media_group)
                                # Forward album to logs and save forwarded IDs to cache
                                try:
                                    orig_ids = [m.id for m in sent]
                                    logger.info(f"[IMG CACHE] Copying album to logs, orig_ids={orig_ids}")
                                    f_ids = []
                                    
                                    # Determine correct log channel based on media type and chat type
                                    is_private_chat = message.chat.type == enums.ChatType.PRIVATE
                                    is_paid_media = nsfw_flag and is_private_chat
                                    
                                    for _mid in orig_ids:
                                        try:
                                            if is_paid_media:
                                                # For paid media, forward to LOGS_PAID_ID and save forwarded IDs
                                                log_channel = get_log_channel("image", nsfw=False, paid=True)
                                                try:
                                                    forwarded_msgs = app.forward_messages(chat_id=log_channel, from_chat_id=user_id, message_ids=[_mid])
                                                    if forwarded_msgs:
                                                        # forward_messages returns a list of forwarded messages
                                                        forwarded_msg = forwarded_msgs[0] if isinstance(forwarded_msgs, list) else forwarded_msgs
                                                        f_ids.append(forwarded_msg.id)
                                                        time.sleep(0.05)
                                                except Exception as fe:
                                                    logger.error(f"[IMG CACHE] forward_messages failed for paid media id={_mid}: {fe}")
                                                    # Fallback to original ID if forwarding fails
                                                    f_ids.append(_mid)
                                                    time.sleep(0.05)
                                            elif nsfw_flag and not is_private_chat:
                                                # NSFW content in groups -> LOGS_NSWF_ID
                                                log_channel = get_log_channel("image", nsfw=True, paid=False)
                                                msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                                if msg:
                                                    f_ids.append(msg.id)
                                                    time.sleep(0.05)
                                            else:
                                                # Regular content -> LOGS_IMG_ID
                                                log_channel = get_log_channel("image", nsfw=False, paid=False)
                                                msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                                if msg:
                                                    f_ids.append(msg.id)
                                                    time.sleep(0.05)
                                        except Exception as ce:
                                            logger.error(f"[IMG CACHE] copy_message failed for id={_mid}: {ce}")
                                    album_index += 1
                                    if f_ids:
                                        logger.info(f"[IMG CACHE] Album index={album_index} collected log_ids={f_ids}")
                                        _save_album_now(url, album_index, f_ids)
                                    else:
                                        logger.error("[IMG CACHE] No log IDs collected; skipping cache save for this album")
                                except Exception as e_copy:
                                    logger.error(f"[IMG CACHE] Unexpected error while copying album to logs: {e_copy}")
                                # Zero out files to keep placeholders for re-run skipping
                                def zero_file(path):
                                    try:
                                        if os.path.exists(path):
                                            with open(path, 'wb') as zf:
                                                pass
                                    except Exception:
                                        pass
                                for p, _t, orig in group_items:
                                    zero_file(p)
                                    zero_file(orig)
                                photos_videos_buffer = photos_videos_buffer[batch_size:]
                                update_status()
                            except Exception as e:
                                logger.error(f"Failed to send media group: {e}")
                                # fallback: send individually
                                fallback = photos_videos_buffer[:batch_size]
                                photos_videos_buffer = photos_videos_buffer[batch_size:]
                                tmp_ids = []
                                for p, t, orig in fallback:
                                    try:
                                        with open(p, 'rb') as f:
                                            if t == 'photo':
                                                is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                if nsfw_flag and is_private_chat:
                                                    sent_msg = app.send_paid_media(
                                                        user_id,
                                                        media=[InputPaidMediaPhoto(media=f)],
                                                        star_count=LimitsConfig.NSFW_STAR_COST,
                                                        payload=str(Config.STAR_RECEIVER),
                                                        reply_parameters=ReplyParameters(message_id=message.id)
                                                    )
                                                else:
                                                    # No spoiler in groups, only in private chats for paid media
                                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                sent_msg = app.send_photo(
                                                    user_id,
                                                    photo=f,
                                                        has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                    reply_parameters=ReplyParameters(message_id=message.id),
                                                    message_thread_id=getattr(message, 'message_thread_id', None)
                                                )
                                            else:
                                                # try generate thumbnail
                                                thumb = None
                                                try:
                                                    thumb = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '.jpg')
                                                    subprocess.run([
                                                        'ffmpeg', '-y', '-i', p, '-vf', 'thumbnail,scale=640:-1', '-frames:v', '1', thumb
                                                    ], capture_output=True, text=True, timeout=30)
                                                except Exception:
                                                    thumb = None
                                                if thumb and os.path.exists(thumb):
                                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                    if nsfw_flag and is_private_chat:
                                                        # Ensure we have a cover
                                                        _cover = thumb
                                                        if not _cover:
                                                            try:
                                                                import subprocess
                                                                _cover = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '.jpg')
                                                                subprocess.run([
                                                                    'ffmpeg','-y','-i', p,
                                                                    '-vf','thumbnail,scale=640:-1','-frames:v','1', _cover
                                                                ], capture_output=True, text=True, timeout=30)
                                                                if not os.path.exists(_cover):
                                                                    _cover = None
                                                            except Exception:
                                                                _cover = None
                                                        try:
                                                            media_item = InputPaidMediaVideo(media=f, cover=_cover)
                                                        except TypeError:
                                                            media_item = InputPaidMediaVideo(media=f)
                                                        sent_msg = app.send_paid_media(
                                                            user_id,
                                                            media=[media_item],
                                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                                            payload=str(Config.STAR_RECEIVER),
                                                            reply_parameters=ReplyParameters(message_id=message.id),
                                                            message_thread_id=getattr(message, 'message_thread_id', None)
                                                        )
                                                    else:
                                                        # No spoiler in groups, only in private chats for paid media
                                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                    sent_msg = app.send_video(
                                                        user_id,
                                                        video=f,
                                                        thumb=thumb,
                                                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=message.id),
                                                        message_thread_id=getattr(message, 'message_thread_id', None)
                                                    )
                                                else:
                                                    is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                    if nsfw_flag and is_private_chat:
                                                        sent_msg = app.send_paid_media(
                                                            user_id,
                                                            media=[InputPaidMediaVideo(media=f)],
                                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                                            payload=str(Config.STAR_RECEIVER),
                                                            reply_parameters=ReplyParameters(message_id=message.id),
                                                            message_thread_id=getattr(message, 'message_thread_id', None)
                                                        )
                                                    else:
                                                        # No spoiler in groups, only in private chats for paid media
                                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                                    sent_msg = app.send_video(
                                                        user_id,
                                                        video=f,
                                                            has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                        reply_parameters=ReplyParameters(message_id=message.id),
                                                        message_thread_id=getattr(message, 'message_thread_id', None)
                                                    )
                                            sent_message_ids.append(sent_msg.id)
                                            tmp_ids.append(sent_msg.id)
                                            total_sent += 1
                                        # zero out both converted and original
                                        try:
                                            with open(p, 'wb') as zf:
                                                pass
                                        except Exception:
                                            pass
                                        try:
                                            if os.path.exists(orig):
                                                with open(orig, 'wb') as zf2:
                                                    pass
                                        except Exception:
                                            pass
                                    except Exception as ee:
                                        logger.error(f"Failed to send file in fallback: {ee}")
                                # Forward fallback album and save forwarded IDs
                                try:
                                    if tmp_ids:
                                        logger.info(f"[IMG CACHE] Copying fallback album to logs, orig_ids={tmp_ids}")
                                        f_ids = []
                                        
                                        # Determine correct log channel based on media type and chat type
                                        is_private_chat = message.chat.type == enums.ChatType.PRIVATE
                                        is_paid_media = nsfw_flag and is_private_chat
                                        
                                        for _mid in tmp_ids:
                                            try:
                                                if is_paid_media:
                                                    # For paid media, forward to LOGS_PAID_ID and save forwarded IDs
                                                    log_channel = get_log_channel("image", nsfw=False, paid=True)
                                                    try:
                                                        forwarded_msgs = app.forward_messages(chat_id=log_channel, from_chat_id=user_id, message_ids=[_mid])
                                                        if forwarded_msgs:
                                                            # forward_messages returns a list of forwarded messages
                                                            forwarded_msg = forwarded_msgs[0] if isinstance(forwarded_msgs, list) else forwarded_msgs
                                                            f_ids.append(forwarded_msg.id)
                                                            time.sleep(0.05)
                                                    except Exception as fe:
                                                        logger.error(f"[IMG CACHE] forward_messages (fallback) failed for paid media id={_mid}: {fe}")
                                                        # Fallback to original ID if forwarding fails
                                                        f_ids.append(_mid)
                                                        time.sleep(0.05)
                                                elif nsfw_flag and not is_private_chat:
                                                    # NSFW content in groups -> LOGS_NSWF_ID
                                                    log_channel = get_log_channel("image", nsfw=True, paid=False)
                                                    msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                                    if msg:
                                                        f_ids.append(msg.id)
                                                        time.sleep(0.05)
                                                else:
                                                    # Regular content -> LOGS_IMG_ID
                                                    log_channel = get_log_channel("image", nsfw=False, paid=False)
                                                    msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                                    if msg:
                                                        f_ids.append(msg.id)
                                                        time.sleep(0.05)
                                            except Exception as ce:
                                                logger.error(f"[IMG CACHE] copy_message (fallback) failed for id={_mid}: {ce}")
                                        album_index += 1
                                        if f_ids:
                                            logger.info(f"[IMG CACHE] Fallback album index={album_index} collected log_ids={f_ids}")
                                            _save_album_now(url, album_index, f_ids)
                                        else:
                                            logger.error("[IMG CACHE] No log IDs collected in fallback; skipping cache save for this album")
                                except Exception as e_copy2:
                                    logger.error(f"[IMG CACHE] Unexpected error while copying fallback album to logs: {e_copy2}")

                        # Send non-groupable immediately
                        while others_buffer:
                            p, orig = others_buffer.pop(0)
                            try:
                                with open(p, 'rb') as f:
                                    sent_msg = app.send_document(
                                        user_id,
                                        document=f,
                                        reply_parameters=ReplyParameters(message_id=message.id),
                                        message_thread_id=getattr(message, 'message_thread_id', None)
                                    )
                                sent_message_ids.append(sent_msg.id)
                                total_sent += 1
                                update_status()
                                # zero out placeholders
                                try:
                                    with open(p, 'wb') as zf:
                                        pass
                                except Exception:
                                    pass
                                try:
                                    if os.path.exists(orig):
                                        with open(orig, 'wb') as zf2:
                                            pass
                                except Exception:
                                    pass
                            except Exception as e:
                                logger.error(f"Failed to send document: {e}")

                        # Stop if limit reached (but not for admins)
                        if not is_admin and total_sent >= total_limit:
                            break

            # Flush remainder if no more ranges pending
            upper_cap = manual_end_cap or total_expected
            if (upper_cap and (total_sent >= upper_cap or current_start > upper_cap)) or (not is_admin and total_sent >= total_limit):
                # Send remaining media groups
                if photos_videos_buffer:
                    group = photos_videos_buffer[:batch_size]
                    media_group = []
                    for p, t, _orig in group:
                        if t == 'photo':
                            # No spoiler in groups, only in private chats for paid media
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            media_group.append(InputMediaPhoto(p, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                        else:
                            # generate thumbnail
                            thumb = None
                            try:
                                thumb = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '.jpg')
                                subprocess.run([
                                    'ffmpeg', '-y', '-i', p, '-vf', 'thumbnail,scale=640:-1', '-frames:v', '1', thumb
                                ], capture_output=True, text=True, timeout=30)
                            except Exception:
                                thumb = None
                            # No spoiler in groups, only in private chats for paid media
                            is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                            if thumb and os.path.exists(thumb):
                                media_group.append(InputMediaVideo(p, thumb=thumb, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                            else:
                                media_group.append(InputMediaVideo(p, has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat)))
                    try:
                        # For paid media, only send in private chats (not groups/channels)
                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                        if nsfw_flag and is_private_chat:
                            # Send each file individually as paid media (Telegram doesn't support paid media groups)
                            sent = []
                            for m in media_group:
                                try:
                                    if isinstance(m, InputMediaPhoto):
                                        paid_msg = app.send_paid_media(
                                            user_id,
                                            media=[InputPaidMediaPhoto(media=m.media)],
                                            star_count=LimitsConfig.NSFW_STAR_COST,
                                            payload=str(Config.STAR_RECEIVER),
                                            reply_parameters=ReplyParameters(message_id=message.id),
                                            message_thread_id=getattr(message, 'message_thread_id', None)
                                        )
                                        if isinstance(paid_msg, list):
                                            sent.extend(paid_msg)
                                        elif paid_msg is not None:
                                            sent.append(paid_msg)
                                    else:
                                        # Generate cover for video if needed
                                        _cover = None
                                        try:
                                            if hasattr(m, 'thumb') and m.thumb and os.path.exists(m.thumb):
                                                _cover = m.thumb
                                            else:
                                                # Try to generate cover via FFmpeg
                                                video_path = m.media
                                                if hasattr(video_path, 'name'):
                                                    video_path = video_path.name
                                                _cover = os.path.join(os.path.dirname(video_path), os.path.splitext(os.path.basename(video_path))[0] + '_cover.jpg')
                                                if not os.path.exists(_cover):
                                                    subprocess.run([
                                                        'ffmpeg', '-i', video_path, '-ss', '00:00:01', '-vframes', '1', '-q:v', '2', '-y', _cover
                                                    ], capture_output=True, timeout=10)
                                                if not os.path.exists(_cover):
                                                    _cover = None
                                        except Exception:
                                            _cover = None
                                        try:
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=[InputPaidMediaVideo(media=m.media, cover=_cover)],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
                                            )
                                        except TypeError:
                                            paid_msg = app.send_paid_media(
                                                user_id,
                                                media=[InputPaidMediaVideo(media=m.media)],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
                                            )
                                        if isinstance(paid_msg, list):
                                            sent.extend(paid_msg)
                                        elif paid_msg is not None:
                                            sent.append(paid_msg)
                                except Exception as e:
                                    logger.error(f"Failed to send individual paid media: {e}")
                                    # Fallback to regular media
                                    if isinstance(m, InputMediaPhoto):
                                        fallback_msg = app.send_photo(
                                            user_id,
                                            photo=m.media,
                                            caption=m.caption,
                                            has_spoiler=False,
                                            reply_parameters=ReplyParameters(message_id=message.id),
                                            message_thread_id=getattr(message, 'message_thread_id', None)
                                        )
                                    else:
                                        fallback_msg = app.send_video(
                                            user_id,
                                            video=m.media,
                                            caption=m.caption,
                                            duration=m.duration,
                                            width=m.width,
                                            height=m.height,
                                            thumb=m.thumb,
                                            has_spoiler=False,
                                            reply_parameters=ReplyParameters(message_id=message.id),
                                            message_thread_id=getattr(message, 'message_thread_id', None)
                                        )
                                    sent.extend(fallback_msg)
                        else:
                            # In groups/channels or non-NSFW content, send as regular media group
                            sent = app.send_media_group(
                                user_id,
                                media=media_group,
                                reply_parameters=ReplyParameters(message_id=message.id),
                                message_thread_id=getattr(message, 'message_thread_id', None)
                            )
                        sent_message_ids.extend([m.id for m in sent])
                        total_sent += len(media_group)
                        # Forward tail album and save forwarded IDs
                        try:
                            orig_ids2 = [m.id for m in sent]
                            logger.info(f"[IMG CACHE] Copying tail album to logs, orig_ids={orig_ids2}")
                            f_ids = []
                            
                            # Determine correct log channel based on media type and chat type
                            is_private_chat = message.chat.type == enums.ChatType.PRIVATE
                            is_paid_media = nsfw_flag and is_private_chat
                            
                            for _mid in orig_ids2:
                                try:
                                    if is_paid_media:
                                        # For paid media, forward to LOGS_PAID_ID and save forwarded IDs
                                        log_channel = get_log_channel("image", nsfw=False, paid=True)
                                        try:
                                            forwarded_msgs = app.forward_messages(chat_id=log_channel, from_chat_id=user_id, message_ids=[_mid])
                                            if forwarded_msgs:
                                                # forward_messages returns a list of forwarded messages
                                                forwarded_msg = forwarded_msgs[0] if isinstance(forwarded_msgs, list) else forwarded_msgs
                                                f_ids.append(forwarded_msg.id)
                                                time.sleep(0.05)
                                        except Exception as fe:
                                            logger.error(f"[IMG CACHE] forward_messages (tail) failed for paid media id={_mid}: {fe}")
                                            # Fallback to original ID if forwarding fails
                                            f_ids.append(_mid)
                                            time.sleep(0.05)
                                    elif nsfw_flag and not is_private_chat:
                                        # NSFW content in groups -> LOGS_NSWF_ID
                                        log_channel = get_log_channel("image", nsfw=True, paid=False)
                                        msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                        if msg:
                                            f_ids.append(msg.id)
                                            time.sleep(0.05)
                                    else:
                                        # Regular content -> LOGS_IMG_ID
                                        log_channel = get_log_channel("image", nsfw=False, paid=False)
                                        msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                        if msg:
                                            f_ids.append(msg.id)
                                            time.sleep(0.05)
                                except Exception as ce:
                                    logger.error(f"[IMG CACHE] copy_message (tail) failed for id={_mid}: {ce}")
                            album_index += 1
                            if f_ids:
                                logger.info(f"[IMG CACHE] Tail album index={album_index} collected log_ids={f_ids}")
                                _save_album_now(url, album_index, f_ids)
                            else:
                                logger.error("[IMG CACHE] No log IDs collected in tail; skipping cache save for this album")
                        except Exception as e_tail:
                            logger.error(f"[IMG CACHE] Unexpected error while copying tail album to logs: {e_tail}")
                        # zero out
                        for p, _t, orig in group:
                            try:
                                with open(p, 'wb') as zf:
                                    pass
                            except Exception:
                                pass
                            try:
                                if os.path.exists(orig):
                                    with open(orig, 'wb') as zf2:
                                        pass
                            except Exception:
                                pass
                    except Exception:
                        tmp_ids2 = []
                        for p, t, orig in group:
                            try:
                                with open(p, 'rb') as f:
                                    if t == 'photo':
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        if nsfw_flag and is_private_chat:
                                            sent_msg = app.send_paid_media(
                                                user_id,
                                                media=[InputPaidMediaPhoto(media=f)],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id),
                                                message_thread_id=getattr(message, 'message_thread_id', None)
                                            )
                                        else:
                                            # No spoiler in groups, only in private chats for paid media
                                            sent_msg = app.send_photo(
                                                user_id,
                                                photo=f,
                                                has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                reply_parameters=ReplyParameters(message_id=message.id),
                                                message_thread_id=getattr(message, 'message_thread_id', None)
                                            )
                                    else:
                                        # try generate thumbnail
                                        thumb = None
                                        try:
                                            thumb = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '.jpg')
                                            subprocess.run([
                                                'ffmpeg', '-y', '-i', p, '-vf', 'thumbnail,scale=640:-1', '-frames:v', '1', thumb
                                            ], capture_output=True, text=True, timeout=30)
                                        except Exception:
                                            thumb = None
                                        is_private_chat = getattr(message.chat, "type", None) == enums.ChatType.PRIVATE
                                        if nsfw_flag and is_private_chat:
                                            # Generate cover for video if needed
                                            _cover = None
                                            if thumb and os.path.exists(thumb):
                                                _cover = thumb
                                            else:
                                                try:
                                                    _cover = os.path.join(os.path.dirname(p), os.path.splitext(os.path.basename(p))[0] + '_cover.jpg')
                                                    if not os.path.exists(_cover):
                                                        subprocess.run([
                                                            'ffmpeg', '-i', p, '-ss', '00:00:01', '-vframes', '1', '-q:v', '2', '-y', _cover
                                                        ], capture_output=True, timeout=10)
                                                    if not os.path.exists(_cover):
                                                        _cover = None
                                                except Exception:
                                                    _cover = None
                                            try:
                                                media_item = InputPaidMediaVideo(media=f, cover=_cover)
                                            except TypeError:
                                                media_item = InputPaidMediaVideo(media=f)
                                            sent_msg = app.send_paid_media(
                                                user_id,
                                                media=[media_item],
                                                star_count=LimitsConfig.NSFW_STAR_COST,
                                                payload=str(Config.STAR_RECEIVER),
                                                reply_parameters=ReplyParameters(message_id=message.id)
                                            )
                                        else:
                                            # No spoiler in groups, only in private chats for paid media
                                            if thumb and os.path.exists(thumb):
                                                sent_msg = app.send_video(
                                                    user_id,
                                                    video=f,
                                                    thumb=thumb,
                                                    has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                    reply_parameters=ReplyParameters(message_id=message.id),
                                                    message_thread_id=getattr(message, 'message_thread_id', None)
                                                )
                                            else:
                                                sent_msg = app.send_video(
                                                    user_id,
                                                    video=f,
                                                    has_spoiler=should_apply_spoiler(user_id, nsfw_flag, is_private_chat),
                                                    reply_parameters=ReplyParameters(message_id=message.id),
                                                    message_thread_id=getattr(message, 'message_thread_id', None)
                                                )
                                    sent_message_ids.append(sent_msg.id)
                                    tmp_ids2.append(sent_msg.id)
                                    total_sent += 1
                                # zero out
                                try:
                                    with open(p, 'wb') as zf:
                                        pass
                                except Exception:
                                    pass
                                try:
                                    if os.path.exists(orig):
                                        with open(orig, 'wb') as zf2:
                                            pass
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        # Forward tail fallback album and save forwarded IDs
                        try:
                            if tmp_ids2:
                                logger.info(f"[IMG CACHE] Copying tail-fallback album to logs, orig_ids={tmp_ids2}")
                                f_ids = []
                                
                                # Determine correct log channel based on media type and chat type
                                is_private_chat = message.chat.type == enums.ChatType.PRIVATE
                                is_paid_media = nsfw_flag and is_private_chat
                                
                                for _mid in tmp_ids2:
                                    try:
                                        if is_paid_media:
                                            # For paid media, forward to LOGS_PAID_ID and save forwarded IDs
                                            log_channel = get_log_channel("image", nsfw=False, paid=True)
                                            try:
                                                forwarded_msgs = app.forward_messages(chat_id=log_channel, from_chat_id=user_id, message_ids=[_mid])
                                                if forwarded_msgs:
                                                    # forward_messages returns a list of forwarded messages
                                                    forwarded_msg = forwarded_msgs[0] if isinstance(forwarded_msgs, list) else forwarded_msgs
                                                    f_ids.append(forwarded_msg.id)
                                                    time.sleep(0.05)
                                            except Exception as fe:
                                                logger.error(f"[IMG CACHE] forward_messages (tail-fallback) failed for paid media id={_mid}: {fe}")
                                                # Fallback to original ID if forwarding fails
                                                f_ids.append(_mid)
                                                time.sleep(0.05)
                                        elif nsfw_flag and not is_private_chat:
                                            # NSFW content in groups -> LOGS_NSWF_ID
                                            log_channel = get_log_channel("image", nsfw=True, paid=False)
                                            msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                            if msg:
                                                f_ids.append(msg.id)
                                                time.sleep(0.05)
                                        else:
                                            # Regular content -> LOGS_IMG_ID
                                            log_channel = get_log_channel("image", nsfw=False, paid=False)
                                            msg = app.copy_message(chat_id=log_channel, from_chat_id=user_id, message_id=_mid)
                                            if msg:
                                                f_ids.append(msg.id)
                                                time.sleep(0.05)
                                    except Exception as ce:
                                        logger.error(f"[IMG CACHE] copy_message (tail-fallback) failed for id={_mid}: {ce}")
                                album_index += 1
                                if f_ids:
                                    logger.info(f"[IMG CACHE] Tail-fallback album index={album_index} collected log_ids={f_ids}")
                                    _save_album_now(url, album_index, f_ids)
                                else:
                                    logger.error("[IMG CACHE] No log IDs collected in tail-fallback; skipping cache save for this album")
                        except Exception as e_tail2:
                            logger.error(f"[IMG CACHE] Unexpected error while copying tail-fallback album to logs: {e_tail2}")
                    photos_videos_buffer = photos_videos_buffer[len(group):]

                # Send remaining others
                while others_buffer:
                    p, orig = others_buffer.pop(0)
                    try:
                        with open(p, 'rb') as f:
                            sent_msg = app.send_document(
                                user_id,
                                document=f,
                                reply_parameters=ReplyParameters(message_id=message.id),
                                message_thread_id=getattr(message, 'message_thread_id', None)
                            )
                        sent_message_ids.append(sent_msg.id)
                        total_sent += 1
                        # zero out
                        try:
                            with open(p, 'wb') as zf:
                                pass
                        except Exception:
                            pass
                        try:
                            if os.path.exists(orig):
                                with open(orig, 'wb') as zf2:
                                    pass
                        except Exception:
                            pass
                    except Exception:
                        pass
                # Final update and replace header to 'Download complete'
                final_expected = total_expected or min(total_downloaded, total_limit)
                try:
                    safe_edit_message_text(
                        user_id,
                        status_msg.id,
                        Config.DOWNLOAD_COMPLETE_MSG +
                        f"Downloaded: <b>{total_downloaded}</b> / <b>{final_expected}</b>\n"
                        f"Sent: <b>{total_sent}</b>",
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass
                break

            if not is_admin and total_sent >= total_limit:
                break

            time.sleep(0.5)

        # Messages are already forwarded to log channels during caching process above

        # Cleanup files
        try:
            for file_path in files_to_cleanup:
                try:
                    if os.path.exists(file_path):
                        file_dir = os.path.dirname(file_path)
                        os.remove(file_path)
                        if os.path.exists(file_dir) and not os.listdir(file_dir):
                            os.rmdir(file_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up file {file_path}: {e}")
        except Exception:
            pass

        send_to_logger(message, f"Streamed and sent {total_sent} media: {url}")
            
    except Exception as e:
        logger.error(f"Error in image command: {e}")
        
        # Clean up only the specific media files that were downloaded on general error
        try:
            # Try to find and clean up any recently downloaded files
            current_time = time.time()
            gallery_dl_dir = "gallery-dl"
            if os.path.exists(gallery_dl_dir):
                for root, _, files in os.walk(gallery_dl_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_time = os.path.getctime(file_path)
                        time_diff = current_time - file_time
                        # Clean up files created in the last 5 minutes
                        if time_diff < 300:
                            try:
                                # Check if file still exists before trying to remove it
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    logger.info(f"Cleaned up file after general error: {file_path}")
                                    
                                    # If directory is empty after removing file, remove it too
                                    try:
                                        if os.path.exists(root) and not os.listdir(root):
                                            os.rmdir(root)
                                            logger.info(f"Removed empty directory after general error: {root}")
                                    except:
                                        pass  # Directory not empty or other error
                                else:
                                    logger.info(f"File already removed after general error: {file_path}")
                            except Exception as e:
                                logger.warning(f"Failed to clean up file after general error {file_path}: {e}")
        except Exception as cleanup_e:
            logger.warning(f"Failed to clean up downloaded files after general error: {cleanup_e}")
        
        safe_edit_message_text(
            user_id, status_msg.id,
            Config.ERROR_OCCURRED_MSG.format(url=url, error=str(e)),
            parse_mode=enums.ParseMode.HTML
        )
        send_to_logger(message, f"Error in image command: {url}, error: {e}")

@app.on_callback_query(filters.regex(r"^img_help\|"))
def img_help_callback(app, callback_query: CallbackQuery):
    """Handle img help callback"""
    data = callback_query.data.split("|")[-1]
    
    if data == "close":
        try:
            callback_query.message.delete()
        except Exception:
            callback_query.edit_message_reply_markup(reply_markup=None)
        try:
            callback_query.answer("Help closed.")
        except Exception:
            pass
        return
    
    try:
        callback_query.answer()
    except Exception:
        pass
