# ####################################################################################
# List Command - Get available formats for video URL
# ####################################################################################

import os
import subprocess
import tempfile
from typing import Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user, send_error_to_user
from HELPERS.limitter import is_user_in_channel
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config

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
        
        # Build command
        cmd = ["yt-dlp", "-F", url]
        if cookie_file:
            cmd.extend(["--cookies", cookie_file])
        
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
            help_text = (
                "<b>📃 List Available Formats</b>\n\n"
                "Get available video/audio formats for a URL.\n\n"
                "<b>Usage:</b>\n"
                "<code>/list URL</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/list https://youtube.com/watch?v=123abc</code>\n"
                "• <code>/list https://youtube.com/playlist?list=123abc</code>\n\n"
                "<b>💡 How to use format IDs:</b>\n"
                "After getting the list, use specific format ID:\n"
                "• <code>/format id 401</code> - download format 401\n"
                "• <code>/format id401</code> - same as above\n\n"
                "This command will show all available formats that can be downloaded."
            )
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
            # Create temporary file with output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(f"Available formats for: {url}\n")
                temp_file.write("=" * 50 + "\n\n")
                temp_file.write(output)
                temp_file.write("\n\n" + "=" * 50 + "\n")
                temp_file.write("💡 How to use format IDs:\n")
                temp_file.write("After getting the list, use specific format ID:\n")
                temp_file.write("• /format id 401 - download format 401\n")
                temp_file.write("• /format id401 - same as above\n")
                temp_file_path = temp_file.name
            
            try:
                # Send the file
                app.send_document(
                    user_id,
                    document=temp_file_path,
                    file_name=f"formats_{user_id}.txt",
                    caption=f"📃 Available formats for:\n<code>{url}</code>\n\n"
                           f"💡 <b>How to set format:</b>\n"
                           f"• <code>/format id 134</code> - Download specific format ID\n"
                           f"• <code>/format 720p</code> - Download by quality\n"
                           f"• <code>/format best</code> - Download best quality\n"
                           f"• <code>/format ask</code> - Always ask for quality\n\n"
                           f"📋 Use format ID from the list above",
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
            callback_query.message.delete()
            callback_query.answer("Help closed")
    except Exception as e:
        logger.error(f"Error in list help callback: {e}")
        callback_query.answer("Error occurred", show_alert=True)
