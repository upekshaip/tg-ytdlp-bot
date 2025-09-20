# @reply_with_keyboard
from pyrogram import enums
from pyrogram.types import ReplyParameters, InputPaidMediaVideo
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.logger import get_log_channel
from HELPERS.download_status import progress_bar
from HELPERS.limitter import TimeFormatter
from HELPERS.caption import truncate_caption
from DOWN_AND_UP.ffmpeg import get_video_info_ffprobe
import os
import subprocess
import json
from HELPERS.safe_messeger import safe_forward_messages
from URL_PARSERS.thumbnail_downloader import download_thumbnail
from CONFIG.config import Config
from CONFIG.limits import LimitsConfig
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
            is_spoiler = bool(re.search(r"(?i)(?:^|\s)#nsfw(?:\s|$)", tags_text or ""))
        except Exception:
            is_spoiler = False
        # Флаг: было ли отправлено как платное медиа
        was_paid = False
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

        def _should_generate_cover(video_path: str, duration_seconds: int) -> bool:
            try:
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
            except Exception:
                size_mb = 0.0
            try:
                dur = float(duration_seconds or 0)
            except Exception:
                dur = 0.0
            # Generate unless both duration<60 and size<10
            return (dur >= 60.0) or (size_mb >= 10.0)

        def _gen_thumb(video_path: str) -> str | None:
            try:
                if not _should_generate_cover(video_path, duration):
                    return None
                base_dir = os.path.dirname(video_path)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                thumb_path = os.path.join(base_dir, base_name + '.__tgthumb.jpg')
                if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                    return thumb_path
                middle_sec = max(1, int(duration) // 2 if isinstance(duration, int) else 1)
                subprocess.run([
                    'ffmpeg','-y','-ss', str(middle_sec), '-i', video_abs_path,
                    '-vframes','1','-vf','scale=320:-1', thumb_path
                ], capture_output=True, text=True, timeout=30)
                return thumb_path if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0 else None
            except Exception:
                return None

        def _resize_to_cover(src_path: str, dest_path: str) -> bool:
            try:
                subprocess.run([
                    'ffmpeg','-y','-i', src_path,
                    '-vf','scale=if(gte(a,1),320,-2):if(gte(a,1),-2,320),pad=320:320:(320-iw)/2:(320-ih)/2:color=black',
                    '-vframes','1','-q:v','4', dest_path
                ], capture_output=True, text=True, timeout=30)
                return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0
            except Exception:
                return False

        def _gen_paid_cover(video_path: str) -> str | None:
            try:
                if not _should_generate_cover(video_path, duration):
                    return None
                base_dir = os.path.dirname(video_path)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                cover_path = os.path.join(base_dir, base_name + '.__tgcover_paid.jpg')
                if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
                    return cover_path
                # 1) Попробовать скачать внешнюю миниатюру (приоритетно)
                try:
                    tmp_dl = os.path.join(base_dir, base_name + '.__ext_thumb.jpg')
                    if video_url:
                        if download_thumbnail(video_url, tmp_dl):
                            if _resize_to_cover(tmp_dl, cover_path):
                                try:
                                    if os.path.exists(tmp_dl):
                                        os.remove(tmp_dl)
                                except Exception:
                                    pass
                                return cover_path
                    # удалить временный, если остался
                    try:
                        if os.path.exists(tmp_dl):
                            os.remove(tmp_dl)
                    except Exception:
                        pass
                except Exception:
                    pass
                # 2) Фолбэк: кадр из видео, затем привести к нужному размеру без паддинга (с сохранением пропорций)
                try:
                    tmp_frame = os.path.join(base_dir, base_name + '.__frame.jpg')
                    middle_sec = max(1, int(duration) // 2 if isinstance(duration, int) else 1)
                    subprocess.run([
                        'ffmpeg','-y','-ss', str(middle_sec), '-i', video_path,
                        '-vframes','1','-q:v','4', tmp_frame
                    ], capture_output=True, text=True, timeout=30)
                    if os.path.exists(tmp_frame) and os.path.getsize(tmp_frame) > 0:
                        if _resize_to_cover(tmp_frame, cover_path):
                            try:
                                if os.path.exists(tmp_frame):
                                    os.remove(tmp_frame)
                            except Exception:
                                pass
                            return cover_path
                    try:
                        if os.path.exists(tmp_frame):
                            os.remove(tmp_frame)
                    except Exception:
                        pass
                except Exception:
                    pass
                return cover_path if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0 else None
            except Exception:
                return None

        def _resize_to_thumb_free(src_path: str, dest_path: str) -> bool:
            try:
                subprocess.run([
                    'ffmpeg','-y','-i', src_path,
                    '-vf','scale=320:-1',
                    '-vframes','1','-q:v','4', dest_path
                ], capture_output=True, text=True, timeout=30)
                return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0
            except Exception:
                return False

        def _gen_free_cover(video_path: str) -> str | None:
            try:
                # Встраиваем миниатюру только если файл >10MB или длительность >=60 сек
                if not _should_generate_cover(video_path, duration):
                    return None
                base_dir = os.path.dirname(video_path)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                cover_path = os.path.join(base_dir, base_name + '.__tgthumb_ext.jpg')
                if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
                    return cover_path
                # 1) Попробовать скачать внешнюю миниатюру (без паддинга, только масштаб до 640 по ширине)
                try:
                    tmp_dl = os.path.join(base_dir, base_name + '.__ext_thumb.jpg')
                    if video_url and download_thumbnail(video_url, tmp_dl):
                        if _resize_to_thumb_free(tmp_dl, cover_path):
                            try:
                                if os.path.exists(tmp_dl):
                                    os.remove(tmp_dl)
                            except Exception:
                                pass
                            return cover_path
                    try:
                        if os.path.exists(tmp_dl):
                            os.remove(tmp_dl)
                    except Exception:
                        pass
                except Exception:
                    pass
                # 2) Фолбэк: кадр из видео (как и раньше)
                return _gen_thumb(video_path)
            except Exception:
                return _gen_thumb(video_path)

        def _try_send_video(caption_text: str):
            nonlocal was_paid
            # Для бесплатных сообщений — внешний превью без паддинга; для платных — обложка 320x320
            local_thumb_free = _gen_free_cover(video_abs_path)
            # Paid media only in private chats; in groups/channels send regular video
            try:
                chat_type = getattr(message.chat, "type", None)
                is_private_chat = chat_type == enums.ChatType.PRIVATE
            except Exception:
                is_private_chat = True
            if is_spoiler and is_private_chat:
                try:
                    # Пробиваем метаданные и добавляем корректный cover и параметры
                    try:
                        v_w, v_h, v_dur = get_video_info_ffprobe(video_abs_path)
                    except Exception:
                        v_w, v_h, v_dur = width, height, duration
                    # duration для paid должен быть float и >0
                    try:
                        safe_paid_dur = float(v_dur) if v_dur and float(v_dur) > 0 else float(duration) if duration and float(duration) > 0 else 1.0
                    except Exception:
                        safe_paid_dur = 1.0
                    # ширина/высота обязаны быть заданы (>0)
                    try:
                        safe_w = int(v_w) if v_w and int(v_w) > 0 else 640
                    except Exception:
                        safe_w = 640
                    try:
                        safe_h = int(v_h) if v_h and int(v_h) > 0 else 360
                    except Exception:
                        safe_h = 360
                    paid_media = InputPaidMediaVideo(
                        media=video_abs_path,
                        cover=_gen_paid_cover(video_abs_path),
                        width=safe_w,
                        height=safe_h,
                        duration=safe_paid_dur,
                        supports_streaming=True
                    )
                except TypeError:
                    paid_media = InputPaidMediaVideo(
                        media=video_abs_path,
                    )
                was_paid = True
                allow_broadcast = getattr(message.chat, "type", None) != enums.ChatType.PRIVATE
                result = app.send_paid_media(
                    chat_id=user_id,
                    media=[paid_media],
                    star_count=LimitsConfig.NSFW_STAR_COST,
                    **({"allow_paid_broadcast": True} if allow_broadcast else {}),
                    payload=str(Config.STAR_RECEIVER),
                    reply_parameters=ReplyParameters(message_id=message.id),
                )
                try:
                    # Some forks return list for albums; wrap to single message for uniformity
                    video_msg = result[0] if isinstance(result, list) and result else result
                    # Paid media will be forwarded to LOGS_PAID_ID in image_cmd.py for caching
                    return video_msg
                except Exception:
                    return result
            # Для бесплатных тоже удерживаем правильные метаданные и мини-обложку по правилу
            try:
                v_w2, v_h2, v_dur2 = get_video_info_ffprobe(video_abs_path)
            except Exception:
                v_w2, v_h2, v_dur2 = width, height, duration
            result = app.send_video(
                chat_id=user_id,
                video=video_abs_path,
                caption=caption_text,
                duration=int(v_dur2) if v_dur2 else duration,
                width=int(v_w2) if v_w2 else width,
                height=int(v_h2) if v_h2 else height,
                supports_streaming=True,
                thumb=local_thumb_free,
                has_spoiler=False,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n\n<i>📤 Uploading Video...</i>"
                ),
                reply_parameters=ReplyParameters(message_id=message.id),
                parse_mode=enums.ParseMode.HTML
            )
            # Cleanup special thumb (free-only temp files)
            try:
                if local_thumb_free and (
                    local_thumb_free.endswith('.__tgthumb.jpg') or local_thumb_free.endswith('.__tgthumb_ext.jpg')
                ) and os.path.exists(local_thumb_free):
                    os.remove(local_thumb_free)
            except Exception:
                pass
            return result

        def _fallback_send_document(caption_text: str):
            nonlocal was_paid
            # Для бесплатных документов — внешний превью без паддинга
            local_thumb = _gen_free_cover(video_abs_path) or thumb_file_path
            try:
                if not local_thumb or not os.path.exists(local_thumb):
                    local_thumb = os.path.join(os.path.dirname(video_abs_path), os.path.splitext(os.path.basename(video_abs_path))[0] + ".jpg")
                    import subprocess
                    try:
                        middle_sec = max(1, int(duration) // 2 if isinstance(duration, int) else 1)
                        subprocess.run([
                            'ffmpeg','-y','-ss', str(middle_sec), '-i', video_abs_path,
                            '-vframes','1','-vf','scale=320:-1', local_thumb
                        ], capture_output=True, text=True, timeout=30)
                        if not os.path.exists(local_thumb):
                            local_thumb = None
                    except Exception:
                        local_thumb = None
            except Exception:
                local_thumb = thumb_file_path
            try:
                chat_type = getattr(message.chat, "type", None)
                is_private_chat = chat_type == enums.ChatType.PRIVATE
            except Exception:
                is_private_chat = True
            if is_spoiler and is_private_chat:
                try:
                    try:
                        v_w, v_h, v_dur = get_video_info_ffprobe(video_abs_path)
                    except Exception:
                        v_w, v_h, v_dur = width, height, duration
                    # duration для paid должен быть float и >0
                    try:
                        safe_paid_dur = float(v_dur) if v_dur and float(v_dur) > 0 else float(duration) if duration and float(duration) > 0 else 1.0
                    except Exception:
                        safe_paid_dur = 1.0
                    # ширина/высота обязаны быть заданы (>0)
                    try:
                        safe_w = int(v_w) if v_w and int(v_w) > 0 else 640
                    except Exception:
                        safe_w = 640
                    try:
                        safe_h = int(v_h) if v_h and int(v_h) > 0 else 360
                    except Exception:
                        safe_h = 360
                    paid_media = InputPaidMediaVideo(
                        media=video_abs_path,
                        cover=_gen_paid_cover(video_abs_path),
                        width=safe_w,
                        height=safe_h,
                        duration=safe_paid_dur,
                        supports_streaming=True
                    )
                except TypeError:
                    paid_media = InputPaidMediaVideo(
                        media=video_abs_path,
                    )
                was_paid = True
                allow_broadcast = getattr(message.chat, "type", None) != enums.ChatType.PRIVATE
                result = app.send_paid_media(
                    chat_id=user_id,
                    media=[paid_media],
                    star_count=LimitsConfig.NSFW_STAR_COST,
                    **({"allow_paid_broadcast": True} if allow_broadcast else {}),
                    payload=str(Config.STAR_RECEIVER),
                    reply_parameters=ReplyParameters(message_id=message.id),
                )
                try:
                    video_msg = result[0] if isinstance(result, list) and result else result
                    # Paid media will be forwarded to LOGS_PAID_ID in image_cmd.py for caching
                    return video_msg
                except Exception:
                    return result
            result = app.send_document(
                chat_id=user_id,
                document=video_abs_path,
                caption=caption_text,
                thumb=local_thumb,
                progress=progress_bar,
                progress_args=(
                    user_id,
                    msg_id,
                    f"{info_text}\n<b>Video duration:</b> <i>{TimeFormatter(duration*1000)}</i>\n\n<i>📤 Uploading file...</i>"
                ),
                reply_parameters=ReplyParameters(message_id=message.id),
                parse_mode=enums.ParseMode.HTML
            )
            # Cleanup special thumb
            try:
                if local_thumb and (local_thumb.endswith('.__tgthumb.jpg') or local_thumb.endswith('.__tgcover_paid.jpg')) and os.path.exists(local_thumb):
                    os.remove(local_thumb)
            except Exception:
                pass
            return result

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
                # If the error is not related to the length of the caption, log it and pass it further
                from HELPERS.logger import send_error_to_user
                send_error_to_user(message, f"❌ Error sending video: {str(e)}")
                raise e
        # Note: Forwarding to log channels is now handled in down_and_up.py
        # to avoid double forwarding and ensure proper channel routing

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
                # Note: Description file forwarding is handled in down_and_up.py
            except Exception as e:
                logger.error(f"Error sending full description file: {e}")
                from HELPERS.logger import send_error_to_user
                send_error_to_user(message, f"❌ Error sending description file: {str(e)}")
        return video_msg
    finally:
        if os.path.exists(temp_desc_path):
            try:
                os.remove(temp_desc_path)
            except Exception as e:
                logger.error(f"Error removing temporary description file: {e}")
                # This is not critical enough to log to LOG_EXCEPTION channel

#####################################################################################
