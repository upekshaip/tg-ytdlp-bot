# ===================== /img command =====================
import os
import re
import subprocess
import tempfile
import threading
import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters, InputMediaPhoto, InputMediaVideo
from pyrogram import enums
from HELPERS.logger import send_to_logger, logger
from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
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

# Get app instance for decorators
app = get_app()

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
            "<blockquote>vk, 2ch, 35photo, 4chan, 500px, ArtStation, Boosty, Civitai, Cyberdrop, DeviantArt, Discord, Facebook, Fansly, Instagram, Patreon, Pinterest, Reddit, TikTok, Tumblr, Twitter/X, JoyReactor, etc. — <a href=\"https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md\">full list</a></blockquote>",
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
            "❌ <b>Invalid URL</b>\n\nPlease provide a valid URL starting with http:// or https://",
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
        f"🔄 <b>Analyzing image URL...</b>\n\n<code>{url}</code>",
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
    
    try:
        # Get image information first
        image_info = get_image_info(url, user_id, use_proxy)
        
        if not image_info:
            safe_edit_message_text(
                user_id, status_msg.id,
                f"❌ <b>Failed to analyze image</b>\n\n<code>{url}</code>\n\n"
                "The URL might not be accessible or not contain a valid image.",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, f"Failed to analyze image URL: {url}")
            return
        
        # Update status message
        title = image_info.get('title', 'Unknown')
        safe_edit_message_text(
            user_id, status_msg.id,
            f"📥 <b>Downloading image...</b>\n\n"
            f"<b>Title:</b> {title}\n"
            f"<b>URL:</b> <code>{url}</code>",
            parse_mode=enums.ParseMode.HTML
        )
        
        # Create user directory
        user_dir = os.path.join("users", str(user_id))
        create_directory(user_dir)
        
        # Determine expected total via --get-urls analog
        detected_total = None
        if manual_range is None or manual_range[1] is None:
            detected_total = get_total_media_count(url, user_id, use_proxy)
        if detected_total and detected_total > 0:
            total_expected = min(detected_total, LimitsConfig.MAX_IMG_FILES)
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
        total_limit = LimitsConfig.MAX_IMG_FILES
        # Using detected_total if present; else metadata-based fallback
        total_expected = locals().get('total_expected') or None
        try:
            for key in ("count", "total", "num", "items", "files", "num_images", "images_count"):
                if isinstance(image_info.get(key), int) and image_info.get(key) > 0:
                    total_expected = min(image_info.get(key), total_limit)
                    break
        except Exception:
            pass

        def update_status():
            try:
                safe_edit_message_text(
                    user_id,
                    status_msg.id,
                    f"📥 <b>Downloading media...</b>\n\n"
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
            # Upper cap: if user provided end, respect it (but not above limit)
            if manual_range[1] is not None:
                manual_end_cap = min(manual_range[1], total_limit)
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

                        # Enforce cap
                        if total_downloaded > total_limit:
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
                                    media_group.append(InputMediaPhoto(p))
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
                                    if thumb and os.path.exists(thumb):
                                        media_group.append(InputMediaVideo(p, thumb=thumb))
                                    else:
                                        media_group.append(InputMediaVideo(p))
                            try:
                                sent = app.send_media_group(user_id, media=media_group)
                                sent_message_ids.extend([m.id for m in sent])
                                total_sent += len(media_group)
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
                                for p, t, orig in fallback:
                                    try:
                                        with open(p, 'rb') as f:
                                            if t == 'photo':
                                                sent_msg = app.send_photo(user_id, photo=f)
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
                                                    sent_msg = app.send_video(user_id, video=f, thumb=thumb)
                                                else:
                                                    sent_msg = app.send_video(user_id, video=f)
                                            sent_message_ids.append(sent_msg.id)
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

                        # Send non-groupable immediately
                        while others_buffer:
                            p, orig = others_buffer.pop(0)
                            try:
                                with open(p, 'rb') as f:
                                    sent_msg = app.send_document(user_id, document=f)
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

                        # Stop if limit reached
                        if total_sent >= total_limit:
                            break

            # Flush remainder if no more ranges pending
            upper_cap = manual_end_cap or total_expected
            if (upper_cap and (total_sent >= upper_cap or current_start > upper_cap)) or (total_sent >= total_limit):
                # Send remaining media groups
                if photos_videos_buffer:
                    group = photos_videos_buffer[:batch_size]
                    media_group = []
                    for p, t, _orig in group:
                        if t == 'photo':
                            media_group.append(InputMediaPhoto(p))
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
                            if thumb and os.path.exists(thumb):
                                media_group.append(InputMediaVideo(p, thumb=thumb))
                            else:
                                media_group.append(InputMediaVideo(p))
                    try:
                        sent = app.send_media_group(user_id, media=media_group)
                        sent_message_ids.extend([m.id for m in sent])
                        total_sent += len(media_group)
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
                        for p, t, orig in group:
                            try:
                                with open(p, 'rb') as f:
                                    if t == 'photo':
                                        sent_msg = app.send_photo(user_id, photo=f)
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
                                            sent_msg = app.send_video(user_id, video=f, thumb=thumb)
                                        else:
                                            sent_msg = app.send_video(user_id, video=f)
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
                    photos_videos_buffer = photos_videos_buffer[len(group):]

                # Send remaining others
                while others_buffer:
                    p, orig = others_buffer.pop(0)
                    try:
                        with open(p, 'rb') as f:
                            sent_msg = app.send_document(user_id, document=f)
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
                        f"✅ <b>Download complete</b>\n\n"
                        f"Downloaded: <b>{total_downloaded}</b> / <b>{final_expected}</b>\n"
                        f"Sent: <b>{total_sent}</b>",
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass
                break

            if total_sent >= total_limit:
                break

            time.sleep(0.5)

        # Forward sent messages to log channel
        try:
            from CONFIG.config import Config
            from HELPERS.safe_messeger import safe_forward_messages
            if sent_message_ids:
                safe_forward_messages(Config.LOGS_ID, user_id, sent_message_ids)
        except Exception as e:
            logger.error(f"Failed to forward messages to log channel: {e}")

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
            f"❌ <b>Error occurred</b>\n\n<code>{url}</code>\n\nError: {str(e)}",
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
