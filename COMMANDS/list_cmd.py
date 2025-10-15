# ####################################################################################
# List Command - Get available formats for video URL
# ####################################################################################

import os
# import subprocess  # Not used anymore, replaced with async_subprocess
import asyncio
from HELPERS.guard import async_subprocess
import sys
import tempfile
from typing import Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_error_to_user
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config
from CONFIG.messages import safe_get_messages
from CONFIG.logger_msg import LoggerMsg
from HELPERS.pot_helper import build_cli_extractor_args

# Get app instance
app = get_app()

async def get_user_cookie_path(user_id: int) -> Optional[str]:
    """Get user's cookie file path if it exists"""
    user_dir = os.path.join("users", str(user_id))
    cookie_file = os.path.join(user_dir, "cookie.txt")
    
    if os.path.exists(cookie_file):
        return cookie_file
    return None

async def run_ytdlp_list(url: str, user_id: int) -> tuple[bool, str]:
    """
    Run yt-dlp -F command to get available formats
    Returns (success, output)
    """
    try:
        # Get user's cookie file if available
        cookie_file = await get_user_cookie_path(user_id)
        
        # Build command: options BEFORE URL to ensure they apply
        # Use the same yt-dlp as Python API: python -m yt_dlp
        cmd = [sys.executable, "-m", "yt_dlp"]
        # Add PO token extractor-args for CLI if applicable
        cmd.extend(build_cli_extractor_args(url))
        # Use -F for format list without verbose output
        cmd.extend(["-F"])
        if cookie_file:
            cmd.extend(["--cookies", cookie_file])
        # Append URL last
        cmd.append(url)
        
        logger.info(f"Running yt-dlp list command: {' '.join(cmd)}")
        
        # Run command
        stdout, stderr = await async_subprocess(*cmd, timeout=60)
        
        stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
        stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
        
        # Check if we got valid format output (contains format lines)
        if stdout_text and ("format code" in stdout_text.lower() or "id" in stdout_text.lower()):
            return True, stdout_text
        else:
            error_msg = stderr_text or stdout_text or "No output received"
            logger.error(f"yt-dlp list failed: {error_msg}")
            return False, error_msg
            
    except asyncio.TimeoutError:
        logger.error("yt-dlp list command timed out")
        return False, "Command timed out after 60 seconds"
    except Exception as e:
        logger.error(f"Error running yt-dlp list: {e}")
        return False, str(e)

@app.on_message(filters.command("list") & filters.private)
async def list_command(app, message):
    """Handle /list command"""
    user_id = message.chat.id
    
    # Subscription check for non-admins
    if int(user_id) not in Config.ADMIN and not is_user_in_channel(app, message):
        return  # is_user_in_channel already sends subscription message
    
    # Parse command arguments
    try:
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            # Show help message
            help_text = (
safe_get_messages(user_id).LIST_HELP_MSG
            )
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(safe_get_messages(user_id).LIST_CLOSE_BUTTON_MSG, callback_data="list_help|close")
            ]])
            await safe_send_message(
                user_id,
                help_text,
                reply_markup=keyboard,
                message=message
            )
            return
        
        url = parts[1].strip()
        
        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            await send_error_to_user(message, safe_get_messages(user_id).LIST_INVALID_URL_MSG)
            return
        
        # Send processing message
        processing_msg = await safe_send_message(
            user_id,
safe_get_messages(user_id).LIST_PROCESSING_MSG,
            message=message
        )
        
        # Run yt-dlp list command
        success, output = await run_ytdlp_list(url, user_id)
        
        if success:
            # Check if any format contains "audio only" and "video only" and extract format IDs
            audio_only_formats = []
            video_only_formats = []
            lines = output.split('\n')
            for line in lines:
                if 'audio only' in line.lower() or 'audio_only' in line.lower():
                    # Extract format ID from the line (usually at the beginning)
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        format_id = parts[0]
                        audio_only_formats.append(format_id)
                elif 'video only' in line.lower() or 'video_only' in line.lower():
                    # Extract format ID from the line (usually at the beginning)
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        format_id = parts[0]
                        video_only_formats.append(format_id)
            
            # Create temporary file with output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(safe_get_messages(user_id).LIST_AVAILABLE_FORMATS_HEADER_MSG.format(url=url) + "\n")
                temp_file.write("=" * 50 + "\n\n")
                temp_file.write(output)
                temp_file.write("\n\n" + "=" * 50 + "\n")
                temp_file.write(safe_get_messages(user_id).LIST_HOW_TO_USE_FORMAT_IDS_TITLE)
                temp_file.write(safe_get_messages(user_id).LIST_FORMAT_USAGE_INSTRUCTIONS)
                temp_file.write(safe_get_messages(user_id).LIST_FORMAT_EXAMPLE_401)
                temp_file.write(safe_get_messages(user_id).LIST_FORMAT_EXAMPLE_401_SHORT)
                temp_file.write(safe_get_messages(user_id).LIST_FORMAT_EXAMPLE_140_AUDIO)
                temp_file.write(safe_get_messages(user_id).LIST_FORMAT_EXAMPLE_140_AUDIO_SHORT)
                
                # Add special note for audio-only formats
                if audio_only_formats:
                    temp_file.write(f"\n{safe_get_messages(user_id).LIST_AUDIO_FORMATS_DETECTED.format(formats=', '.join(audio_only_formats))}")
                    temp_file.write(safe_get_messages(user_id).LIST_AUDIO_FORMATS_NOTE)
                
                temp_file_path = temp_file.name
            
            try:
                # Send the file
                caption = safe_get_messages(user_id).LIST_CAPTION_MSG.format(url=url, audio_note="")
                
                # Add video-only formats info first
                if video_only_formats:
                    video_formats_text = ', '.join([f'<code>{fmt}</code>' for fmt in video_only_formats])
                    caption += f"\n{safe_get_messages(user_id).LIST_VIDEO_ONLY_FORMATS_MSG.format(formats=video_formats_text)}"
                
                # Add special note for audio-only formats with monospace formatting
                if audio_only_formats:
                    audio_formats_text = ', '.join([f'<code>{fmt}</code>' for fmt in audio_only_formats])
                    caption += safe_get_messages(user_id).LIST_AUDIO_FORMATS_MSG.format(formats=audio_formats_text)
                
                caption += f"\n{safe_get_messages(user_id).LIST_USE_FORMAT_ID_MSG}"
                
                await app.send_document(
                    user_id,
                    document=temp_file_path,
                    file_name=safe_get_messages(user_id).LIST_FORMATS_FILE_NAME_MSG.format(user_id=user_id),
                    caption=caption,
                    reply_to_message_id=message.id
                )
                
                # Delete processing message
                try:
                    await processing_msg.delete()
                except Exception:
                    pass
                    
            except Exception as e:
                logger.error(f"Error sending formats file: {e}")
                await send_error_to_user(message, safe_get_messages(user_id).LIST_ERROR_SENDING_MSG.format(error=str(e)))
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        else:
            # Delete processing message
            try:
                await processing_msg.delete()
            except Exception:
                pass
                
            await send_error_to_user(message, safe_get_messages(user_id).LIST_ERROR_GETTING_MSG.format(error=output))
            
    except Exception as e:
        logger.error(f"Error in list command: {e}")
        await send_error_to_user(message, safe_get_messages(user_id).LIST_ERROR_OCCURRED_MSG)

@app.on_callback_query(filters.regex("^list_help\\|"))
async def list_help_callback(app, callback_query):
    """Handle list help callback"""
    try:
        data = callback_query.data.split("|")[1]
        if data == "close":
            await callback_query.message.delete()
            await callback_query.answer(safe_get_messages(callback_query.from_user.id).HELP_CLOSED_MSG)
    except Exception as e:
        logger.error(LoggerMsg.LIST_ERROR_IN_HELP_CALLBACK_LOG_MSG.format(e=e))
        await callback_query.answer(safe_get_messages(callback_query.from_user.id).LIST_ERROR_CALLBACK_MSG, show_alert=True)
