# ####################################################################################
# List Command - Get available formats for video URL
# ####################################################################################

import os
import subprocess
import sys
import tempfile
from typing import Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user, send_error_to_user
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config
from HELPERS.pot_helper import build_cli_extractor_args

# Get app instance
app = get_app()

def get_user_cookie_path(user_id: int) -> Optional[str]:
    """Get user's cookie file path if it exists"""
    user_dir = os.path.join("users", str(user_id))
    cookie_file = os.path.join(user_dir, "cookie.txt")
    
    if os.path.exists(cookie_file):
        return cookie_file
    return None

def run_ytdlp_list(url: str, user_id: int) -> tuple[bool, str]:
    """
    Run yt-dlp -F command to get available formats
    Returns (success, output)
    """
    try:
        # Get user's cookie file if available
        cookie_file = get_user_cookie_path(user_id)
        
        # Build command: options BEFORE URL to ensure they apply
        # Use the same yt-dlp as Python API: python -m yt_dlp
        cmd = [sys.executable, "-m", "yt_dlp"]
        # Add PO token extractor-args for CLI if applicable
        cmd.extend(build_cli_extractor_args(url))
        # Verbose for clearer diagnostics
        cmd.extend(["-v", "-F"])
        if cookie_file:
            cmd.extend(["--cookies", cookie_file])
        # Append URL last
        cmd.append(url)
        
        logger.info(f"Running yt-dlp list command: {' '.join(cmd)}")
        
        # Run command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"yt-dlp list failed: {error_msg}")
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp list command timed out")
        return False, "Command timed out after 60 seconds"
    except Exception as e:
        logger.error(f"Error running yt-dlp list: {e}")
        return False, str(e)

@app.on_message(filters.command("list") & filters.private)
def list_command(app, message):
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
            from CONFIG.messages import MessagesConfig as Messages
            help_text = Messages.LIST_HELP_MSG
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔚 Close", callback_data="list_help|close")
            ]])
            safe_send_message(
                user_id,
                help_text,
                reply_markup=keyboard,
                message=message
            )
            return
        
        url = parts[1].strip()
        
        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            send_error_to_user(message, "❌ Please provide a valid URL starting with http:// or https://")
            return
        
        # Send processing message
        processing_msg = safe_send_message(
            user_id,
            "🔄 Getting available formats...",
            message=message
        )
        
        # Run yt-dlp list command
        success, output = run_ytdlp_list(url, user_id)
        
        if success:
            # Check if any format contains "audio only" and extract format IDs
            audio_only_formats = []
            lines = output.split('\n')
            for line in lines:
                if 'audio only' in line.lower() or 'audio_only' in line.lower():
                    # Extract format ID from the line (usually at the beginning)
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        format_id = parts[0]
                        audio_only_formats.append(format_id)
            
            # Create temporary file with output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(f"Available formats for: {url}\n")
                temp_file.write("=" * 50 + "\n\n")
                temp_file.write(output)
                temp_file.write("\n\n" + "=" * 50 + "\n")
                temp_file.write("💡 How to use format IDs:\n")
                temp_file.write("After getting the list, use specific format ID:\n")
                temp_file.write("• /format id 401 - download format 401\n")
                temp_file.write("• /format id 140 audio - download format 140 as MP3 audio\n")
                
                # Add special note for audio-only formats
                if audio_only_formats:
                    temp_file.write(f"\n🎵 Audio-only formats detected: {', '.join(audio_only_formats)}\n")
                    temp_file.write("These formats will be downloaded as MP3 audio files.\n")
                
                temp_file_path = temp_file.name
            
            try:
                # Send the file
                from CONFIG.messages import MessagesConfig as Messages
                caption = Messages.LIST_FORMATS_CAPTION_MSG.format(url=url)
                caption += Messages.LIST_FORMAT_INSTRUCTIONS_MSG
                
                # Add special note for audio-only formats
                if audio_only_formats:
                    caption += Messages.LIST_AUDIO_FORMATS_MSG.format(audio_formats=', '.join(audio_only_formats))
                
                caption += Messages.LIST_USE_FORMAT_ID_MSG
                
                app.send_document(
                    user_id,
                    document=temp_file_path,
                    file_name=f"formats_{user_id}.txt",
                    caption=caption,
                    reply_to_message_id=message.id
                )
                
                # Delete processing message
                try:
                    processing_msg.delete()
                except Exception:
                    pass
                    
            except Exception as e:
                logger.error(f"Error sending formats file: {e}")
                send_error_to_user(message, f"❌ Error sending formats file: {str(e)}")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
        else:
            # Delete processing message
            try:
                processing_msg.delete()
            except Exception:
                pass
                
            send_error_to_user(message, f"❌ Failed to get formats:\n<code>{output}</code>")
            
    except Exception as e:
        logger.error(f"Error in list command: {e}")
        send_error_to_user(message, "❌ An error occurred while processing the command")

@app.on_callback_query(filters.regex("^list_help\\|"))
def list_help_callback(app, callback_query):
    """Handle list help callback"""
    try:
        data = callback_query.data.split("|")[1]
        if data == "close":
            from CONFIG.messages import MessagesConfig as Messages
            callback_query.message.delete()
            callback_query.answer(Messages.AA_HELP_CLOSED_MSG)
    except Exception as e:
        from CONFIG.messages import MessagesConfig as Messages
        logger.error(f"Error in list help callback: {e}")
        callback_query.answer(Messages.AA_ERROR_OCCURRED_MSG, show_alert=True)
