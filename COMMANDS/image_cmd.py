# ===================== /img command =====================
import os
import re
import subprocess
import tempfile
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyParameters
from pyrogram import enums
from HELPERS.logger import send_to_logger, logger
from HELPERS.app_instance import get_app
from HELPERS.safe_messeger import safe_send_message, safe_edit_message_text
from DOWN_AND_UP.gallery_dl_hook import get_image_info, download_image
from HELPERS.filesystem_hlp import create_directory
from COMMANDS.proxy_cmd import is_proxy_enabled

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
        
        # Convert WebM videos to MP4
        elif file_ext == '.webm':
            output_path = os.path.join(file_dir, f"{file_name}.mp4")
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
            "• <code>/img https://imgur.com/abc123</code>\n"
            "• <code>/img https://flickr.com/photos/user/123456</code>\n\n"
            "<b>Supported platforms:</b>\n"
            "• Direct image URLs (jpg, png, gif, webp, etc.)\n"
            "• Imgur, Flickr, DeviantArt, Pinterest\n"
            "• Instagram, Twitter/X, Reddit\n"
            "• Google Drive, Dropbox, Mega\n"
            "• And many more via gallery-dl",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=ReplyParameters(message_id=message.id)
        )
        send_to_logger(message, "Showed /img help")
        return
    
    # Extract URL from command
    url = text.split(' ', 1)[1].strip()
    
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
        
        # Download the images
        downloaded_files = download_image(url, user_id, use_proxy, user_dir)
        
        if not downloaded_files:
            safe_edit_message_text(
                user_id, status_msg.id,
                f"❌ <b>Failed to download images</b>\n\n<code>{url}</code>\n\n"
                "The images might be protected or the URL might be invalid.",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, f"Failed to download images: {url}")
            return
        
        # Verify all downloaded files exist
        valid_files = []
        for file_path in downloaded_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                logger.warning(f"Downloaded file not found: {file_path}")
        
        if not valid_files:
            safe_edit_message_text(
                user_id, status_msg.id,
                f"❌ <b>No valid files found after download</b>\n\n<code>{url}</code>\n\n"
                f"Expected files: <code>{downloaded_files}</code>",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, f"No valid files found: {downloaded_files}")
            return
        
        # Initialize files to cleanup list
        files_to_cleanup = []
        
        # Send the downloaded images
        try:
            # Delete status message
            try:
                status_msg.delete()
            except:
                pass
            
            logger.info(f"Attempting to send {len(valid_files)} files: {valid_files}")
            
            # Send images in batches of 10 (Telegram album limit)
            batch_size = 10
            total_batches = (len(valid_files) + batch_size - 1) // batch_size
            
            # Send files and forward to log channel
            sent_message_ids = []
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(valid_files))
                batch_files = valid_files[start_idx:end_idx]
                
                logger.info(f"Sending batch {batch_num + 1}/{total_batches} with {len(batch_files)} files")
                
                # Send files individually and collect message IDs
                for file_path in batch_files:
                    try:
                        # Convert file to Telegram-supported format if needed
                        converted_file_path = convert_file_to_telegram_format(file_path)
                        file_ext = os.path.splitext(converted_file_path)[1].lower()
                        
                        # Track files for cleanup
                        files_to_cleanup.append(converted_file_path)
                        if converted_file_path != file_path:
                            files_to_cleanup.append(file_path)  # Also clean up original if converted
                        
                        with open(converted_file_path, 'rb') as f:
                            # Определяем тип файла и отправляем соответствующим методом
                            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']:
                                # Изображения
                                sent_msg = app.send_photo(user_id, photo=f)
                                sent_message_ids.append(sent_msg.id)
                                logger.info(f"Successfully sent photo: {converted_file_path}")
                            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']:
                                # Видео
                                sent_msg = app.send_video(user_id, video=f)
                                sent_message_ids.append(sent_msg.id)
                                logger.info(f"Successfully sent video: {converted_file_path}")
                            elif file_ext in ['.mp3', '.wav', '.ogg', '.m4a']:
                                # Аудио
                                sent_msg = app.send_audio(user_id, audio=f)
                                sent_message_ids.append(sent_msg.id)
                                logger.info(f"Successfully sent audio: {converted_file_path}")
                            else:
                                # Все остальные файлы как документы
                                sent_msg = app.send_document(user_id, document=f)
                                sent_message_ids.append(sent_msg.id)
                                logger.info(f"Successfully sent document: {converted_file_path}")
                    except Exception as e:
                        logger.error(f"Failed to send file {converted_file_path}: {e}")
                        continue
            
            # Forward sent messages to log channel
            try:
                from CONFIG.config import Config
                from HELPERS.safe_messeger import safe_forward_messages
                
                # Forward all sent messages to log channel
                if sent_message_ids:
                    safe_forward_messages(Config.LOGS_ID, user_id, sent_message_ids)
                    
            except Exception as e:
                logger.error(f"Failed to forward messages to log channel: {e}")

            # Clean up all files (original + converted)
            try:
                for file_path in files_to_cleanup:
                    try:
                        # Check if file still exists before trying to remove it
                        if os.path.exists(file_path):
                            # Get the directory of the file
                            file_dir = os.path.dirname(file_path)
                            
                            # Remove only the specific file
                            os.remove(file_path)
                            logger.info(f"Cleaned up file: {file_path}")
                            
                            # If directory is empty after removing file, remove it too
                            try:
                                if os.path.exists(file_dir) and not os.listdir(file_dir):
                                    os.rmdir(file_dir)
                                    logger.info(f"Removed empty directory: {file_dir}")
                            except:
                                pass  # Directory not empty or other error
                        else:
                            logger.info(f"File already removed: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {e}")
            except Exception as e:
                logger.warning(f"Failed to clean up downloaded files: {e}")

            send_to_logger(message, f"Successfully downloaded and sent {len(valid_files)} images: {url}")
            
        except Exception as e:
            logger.error(f"Failed to send images: {e}")
            
            # Clean up all files (original + converted) on error
            try:
                for file_path in files_to_cleanup:
                    try:
                        # Check if file still exists before trying to remove it
                        if os.path.exists(file_path):
                            # Get the directory of the file
                            file_dir = os.path.dirname(file_path)
                            
                            # Remove only the specific file
                            os.remove(file_path)
                            logger.info(f"Cleaned up file after error: {file_path}")
                            
                            # If directory is empty after removing file, remove it too
                            try:
                                if os.path.exists(file_dir) and not os.listdir(file_dir):
                                    os.rmdir(file_dir)
                                    logger.info(f"Removed empty directory after error: {file_dir}")
                            except:
                                pass  # Directory not empty or other error
                        else:
                            logger.info(f"File already removed after error: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file after error {file_path}: {e}")
            except Exception as cleanup_e:
                logger.warning(f"Failed to clean up downloaded files after error: {cleanup_e}")
            
            safe_edit_message_text(
                user_id, status_msg.id,
                f"❌ <b>Failed to send images</b>\n\n<code>{url}</code>\n\nError: {str(e)}",
                parse_mode=enums.ParseMode.HTML
            )
            send_to_logger(message, f"Failed to send images: {url}, error: {e}")
            
    except Exception as e:
        logger.error(f"Error in image command: {e}")
        
        # Clean up only the specific media files that were downloaded on general error
        try:
            # Try to find and clean up any recently downloaded files
            import time
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
