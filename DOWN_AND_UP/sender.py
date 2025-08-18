# @reply_with_keyboard
from pyrogram import enums
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.download_status import progress_bar
from HELPERS.limitter import TimeFormatter
from HELPERS.caption import truncate_caption
from DOWN_AND_UP.ffmpeg import get_video_info_ffprobe
from HELPERS.safe_messeger import safe_forward_messages
from CONFIG.config import Config

# Get app instance for decorators
app = get_app()

def send_videos(
    message,
    video_abs_path: str,
    caption: str,
    duration: int,
    thumb_file_path: str,
    info_text: str,
    msg_id: int,
    full_video_title: str,
    tags_text: str = '',
):
    import re
    import os
    user_id = message.chat.id
    text = message.text or ""
    m = re.search(r'https?://[^\s\*]+', text)
    video_url = m.group(0) if m else ""
    temp_desc_path = os.path.join(os.path.dirname(video_abs_path), "full_description.txt")
    was_truncated = False

    # --- Define the size of the preview/video ---
    width = None
    height = None
    if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
        if "youtube.com/shorts/" in video_url or "/shorts/" in video_url:
            width, height = 360, 640
        else:
            width, height = 640, 360
    else:
        # For the rest - define the size of the video dynamically
        try:
            width, height, _ = get_video_info_ffprobe(video_abs_path)
        except Exception as e:
            logger.error(f"[FFPROBE BYPASS] Error while processing video{video_abs_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            width, height = 0, 0

    try:
        # Logic simplified: use tags that were already generated in down_and_up.
        # Use original title for caption, but truncated description
        title_html, pre_block, blockquote_content, tags_block, link_block, was_truncated = truncate_caption(
            title=caption,  # Original title for caption
            description=full_video_title,  # Full description to be truncated
            url=video_url,
            tags_text=tags_text, # Use final tags for calculation
            max_length=1000  # Reduced for safety
        )
        # Form HTML caption: title outside the quote, timecodes outside the quote, description in the quote, tags and link outside the quote
        cap = ''
        if title_html:
            cap += title_html + '\n\n'
        if pre_block:
            cap += pre_block + '\n'
        cap += f'<blockquote expandable>{blockquote_content}</blockquote>\n'
        if tags_block:
            cap += tags_block
        cap += link_block

        try:
            # First try sending with full caption
            video_msg = app.send_video(
                chat_id=user_id,
                video=video_abs_path,
                caption=cap,
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,
                thumb=thumb_file_path,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n\n<i>📤 Uploading Video...</i>"
                ),
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            if "MEDIA_CAPTION_TOO_LONG" in str(e):
                logger.info("Caption too long, trying with minimal caption")
                # If the caption is too long, try sending only with the main information
                minimal_cap = ''
                if title_html:
                    minimal_cap += title_html + '\n\n'
                minimal_cap += link_block
                
                try:
                    # Try sending with minimal caption
                    video_msg = app.send_video(
                        chat_id=user_id,
                        video=video_abs_path,
                        caption=minimal_cap,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        thumb=thumb_file_path,
                        progress=progress_bar,
                        progress_args=(
                            user_id,
                            msg_id,
                            f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n<i>📤 Uploading Video...</i>"
                        ),
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Error sending video with minimal caption: {e}")
                    # If even the minimal caption does not work, send without caption
                    video_msg = app.send_video(
                        chat_id=user_id,
                        video=video_abs_path,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        thumb=thumb_file_path,
                        progress=progress_bar,
                        progress_args=(
                            user_id,
                            msg_id,
                            f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n<i>📤 Uploading Video...</i>"
                        ),
                        reply_to_message_id=message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
            else:
                # If the error is not related to the length of the caption, pass it further
                raise e
        if was_truncated and full_video_title:
            with open(temp_desc_path, "w", encoding="utf-8") as f:
                f.write(full_video_title)
        if was_truncated and os.path.exists(temp_desc_path):
            try:
                user_doc_msg = app.send_document(
                    chat_id=user_id,
                    document=temp_desc_path,
                    caption="<blockquote>📝 if you want to change video caption - reply to video with new text</blockquote>",
                    reply_to_message_id=message.id,
                    parse_mode=enums.ParseMode.HTML
                )
                safe_forward_messages(Config.LOGS_ID, user_id, [user_doc_msg.id])
            except Exception as e:
                logger.error(f"Error sending full description file: {e}")
        return video_msg
    finally:
        if os.path.exists(temp_desc_path):
            try:
                os.remove(temp_desc_path)
            except Exception as e:
                logger.error(f"Error removing temporary description file: {e}")

#####################################################################################
