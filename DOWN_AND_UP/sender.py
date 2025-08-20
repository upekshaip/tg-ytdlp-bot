# @reply_with_keyboard
from pyrogram import enums
from pyrogram.types import ReplyParameters
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.download_status import progress_bar
from HELPERS.limitter import TimeFormatter
from HELPERS.caption import truncate_caption
from DOWN_AND_UP.ffmpeg import get_video_info_ffprobe
from HELPERS.safe_messeger import safe_forward_messages
from CONFIG.config import Config
import time

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
        # Define spoiler flag for porn-tagged content
        try:
            is_spoiler = bool(re.search(r"(?i)(?:^|\s)#porn(?:\s|$)", tags_text or ""))
        except Exception:
            is_spoiler = False
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

        def _try_send_video(caption_text: str):
            return app.send_video(
                chat_id=user_id,
                video=video_abs_path,
                caption=caption_text,
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,
                thumb=thumb_file_path,
                has_spoiler=is_spoiler,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n\n<i>📤 Uploading Video...</i>"
                ),
                reply_parameters=ReplyParameters(message_id=message.id),
                parse_mode=enums.ParseMode.HTML
            )

        def _fallback_send_document(caption_text: str):
            return app.send_document(
                chat_id=user_id,
                document=video_abs_path,
                caption=caption_text,
                thumb=thumb_file_path,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n\n<i>📤 Uploading file...</i>"
                ),
                reply_parameters=ReplyParameters(message_id=message.id),
                parse_mode=enums.ParseMode.HTML
            )

        try:
            # Первая попытка с полным описанием, с ограничением на количество ретраев по таймауту
            attempts_left = 3
            while True:
                try:
                    video_msg = _try_send_video(cap)
                    break
                except Exception as e:
                    if "Request timed out" in str(e) or isinstance(e, TimeoutError):
                        attempts_left -= 1
                        if attempts_left <= 0:
                            logger.warning("send_video timed out repeatedly; falling back to send_document")
                            video_msg = _fallback_send_document(cap)
                            break
                        time.sleep(2)
                        continue
                    raise
        except Exception as e:
            if "MEDIA_CAPTION_TOO_LONG" in str(e):
                logger.info("Caption too long, trying with minimal caption")
                # If the caption is too long, try sending only with the main information
                minimal_cap = ''
                if title_html:
                    minimal_cap += title_html + '\n\n'
                minimal_cap += link_block
                
                try:
                    # Попытка с коротким описанием и ограниченными ретраями по таймауту
                    attempts_left = 2
                    while True:
                        try:
                            video_msg = _try_send_video(minimal_cap)
                            break
                        except Exception as e2:
                            if "Request timed out" in str(e2) or isinstance(e2, TimeoutError):
                                attempts_left -= 1
                                if attempts_left <= 0:
                                    logger.warning("send_video (minimal caption) timed out; fallback to send_document")
                                    video_msg = _fallback_send_document(minimal_cap)
                                    break
                                time.sleep(2)
                                continue
                            raise
                except Exception as e:
                    logger.error(f"Error sending video with minimal caption: {e}")
                    # Последний фолбэк — без описания, с документом при таймауте
                    try:
                        video_msg = _try_send_video("")
                    except Exception as e3:
                        if "Request timed out" in str(e3) or isinstance(e3, TimeoutError):
                            video_msg = _fallback_send_document("")
                        else:
                            raise
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
                    reply_parameters=ReplyParameters(message_id=message.id),
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
