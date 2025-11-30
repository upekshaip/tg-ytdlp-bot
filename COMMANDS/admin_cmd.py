from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_user, send_to_logger, send_to_all, send_error_to_user
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from HELPERS.safe_messeger import safe_send_message, safe_send_message_with_auto_delete, safe_edit_message_text, safe_delete_messages, fake_message
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from datetime import datetime
import subprocess
import sys
import math
import time
import os
import re
from typing import Optional
import threading
# from DATABASE.cache_db import reload_firebase_cache, get_from_local_cache  # moved to lazy imports
from DATABASE.firebase_init import db
from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
from URL_PARSERS.normalizer import normalize_url_for_cache, get_clean_playlist_url
from HELPERS.limitter import TimeFormatter, is_user_in_channel
# Channel guard helpers
from HELPERS.channel_guard import (
    get_channel_guard,
    parse_period_to_seconds,
    format_seconds_human,
    register_block_user_executor,
)
# from DATABASE.cache_db import get_url_hash, db_child_by_path  # moved to lazy imports
from HELPERS.logger import logger
from HELPERS.decorators import background_handler

# Global variable for bot start time
starting_point = [time.time()]

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("reload_cache") & filters.private)
@background_handler(label="reload_cache")
def reload_firebase_cache_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """The processor of command for rebooting the local cache Firebase"""
    if int(message.chat.id) not in Config.ADMIN:
        safe_send_message_with_auto_delete(message.chat.id, safe_get_messages(message.chat.id).ADMIN_ACCESS_DENIED_AUTO_DELETE_MSG, delete_after_seconds=60)
        return
    
    # Check if this is a fake message (called programmatically)
    is_fake_message = getattr(message, '_is_fake_message', False) or message.id == 0
    
    # В локальном режиме просто перезагружаем кэш из файла
    use_firebase = getattr(Config, 'USE_FIREBASE', True)
    if not use_firebase:
        from DATABASE.cache_db import reload_firebase_cache
        success = reload_firebase_cache()
        if success:
            final_msg = "✅ Локальный кэш перезагружен"
            if is_fake_message:
                send_to_logger(message, "✅ Локальный кэш перезагружен автоматически")
            else:
                safe_send_message_with_auto_delete(message.chat.id, final_msg, delete_after_seconds=10)
        else:
            error_msg = "❌ Ошибка перезагрузки локального кэша"
            if is_fake_message:
                send_to_logger(message, error_msg)
            else:
                safe_send_message_with_auto_delete(message.chat.id, error_msg, delete_after_seconds=10)
        return
    
    try:
        # 1) Download fresh dump via external script path
        script_path = getattr(Config, "DOWNLOAD_FIREBASE_SCRIPT_PATH", "DATABASE/download_firebase.py")
        # Ensure we have the full path to the script
        if not os.path.isabs(script_path):
            script_path = os.path.join(os.getcwd(), script_path)
        
        # Verify script exists
        if not os.path.exists(script_path):
            error_msg = safe_get_messages(message.chat.id).ADMIN_SCRIPT_NOT_FOUND_MSG.format(script_path=script_path)
            safe_send_message_with_auto_delete(message.chat.id, error_msg, delete_after_seconds=60)
            send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_NOT_FOUND_LOG_MSG.format(script_path=script_path))
            return
            
        # Send initial status message (skip for fake_message)
        status_msg = None
        if not is_fake_message:
            status_msg = safe_send_message(message.chat.id, safe_get_messages(message.chat.id).ADMIN_DOWNLOADING_MSG.format(script_path=script_path))
            if not status_msg:
                send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_FAILED_SEND_STATUS_LOG_MSG)
                return
        
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=os.path.dirname(os.path.dirname(script_path)))
        if result.returncode != 0:
            error_msg = safe_get_messages(message.chat.id).ADMIN_ERROR_SCRIPT_MSG.format(script_path=script_path, stdout=result.stdout, stderr=result.stderr)
            if is_fake_message:
                # Do not send anything to chat on fake_message
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_ERROR_RUNNING_SCRIPT_LOG_MSG.format(script_path=script_path, stdout=result.stdout, stderr=result.stderr))
            else:
                safe_edit_message_text(message.chat.id, status_msg.id, error_msg)
                # Schedule deletion after 60 seconds for real messages
                def delete_msg():
                    messages = safe_get_messages(message.chat.id)
                    time.sleep(60)
                    safe_delete_messages(message.chat.id, [status_msg.id])
                threading.Thread(target=delete_msg, daemon=True).start()
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_ERROR_RUNNING_SCRIPT_LOG_MSG.format(script_path=script_path, stdout=result.stdout, stderr=result.stderr))
            return
        
        # Update status to reloading
        if is_fake_message:
            # Do not send anything to chat on fake_message
            pass
        else:
            safe_edit_message_text(message.chat.id, status_msg.id, safe_get_messages(message.chat.id).ADMIN_RELOADING_CACHE_MSG)
        
        # 2) Reload local cache into memory
        from DATABASE.cache_db import reload_firebase_cache as _reload_local
        success = _reload_local()
        if success:
            final_msg = safe_get_messages(message.chat.id).ADMIN_CACHE_RELOADED_MSG
            if is_fake_message:
                # Only log to channel/logger
                send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_CACHE_RELOADED_AUTO_LOG_MSG)
            else:
                safe_edit_message_text(message.chat.id, status_msg.id, final_msg)
                # Schedule deletion after 60 seconds for real messages
                def delete_msg():
                    time.sleep(60)
                    safe_delete_messages(message.chat.id, [status_msg.id])
                threading.Thread(target=delete_msg, daemon=True).start()
                send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_CACHE_RELOADED_ADMIN_LOG_MSG)
        else:
            cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
            final_msg = safe_get_messages(message.chat.id).ADMIN_CACHE_FAILED_MSG.format(cache_file=cache_file)
            if is_fake_message:
                # Only log to channel/logger
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, final_msg)
                send_to_logger(message, final_msg)
            else:
                safe_edit_message_text(message.chat.id, status_msg.id, final_msg)
                # Schedule deletion after 60 seconds for real messages
                def delete_msg():
                    time.sleep(60)
                    safe_delete_messages(message.chat.id, [status_msg.id])
                threading.Thread(target=delete_msg, daemon=True).start()
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, final_msg)
    except Exception as e:
        # ГЛОБАЛЬНАЯ ЗАЩИТА: Убедимся, что messages инициализирована
        if 'messages' not in locals() or messages is None:
            try:
                messages = safe_get_messages(message.chat.id)
            except Exception:
                # Если все не удается, создаем минимальную защиту
                class EmergencyMessages:
                    def __getattr__(self, name):
                        return f"[{name}]"
                messages = EmergencyMessages()
        error_msg = safe_get_messages(message.chat.id).ADMIN_ERROR_RELOADING_MSG.format(error=str(e))
        # Try to update the status message if it exists, otherwise send new message
        if 'status_msg' in locals() and status_msg and not is_fake_message:
            safe_edit_message_text(message.chat.id, status_msg.id, error_msg)
            # Schedule deletion after 60 seconds
            def delete_msg():
                time.sleep(60)
                safe_delete_messages(message.chat.id, [status_msg.id])
            threading.Thread(target=delete_msg, daemon=True).start()
        else:
            # For fake messages, do not send to chat; only log
            if not is_fake_message:
                safe_send_message_with_auto_delete(message.chat.id, error_msg, delete_after_seconds=60)
        from HELPERS.logger import log_error_to_channel
        log_error_to_channel(message, error_msg)
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_ERROR_RELOADING_CACHE_LOG_MSG.format(error=str(e)))

# SEND BRODCAST Message to All Users

def send_promo_message(app, message):
    messages = safe_get_messages(message.chat.id)
    # We get a list of users from the base
    user_nodes = db.child("bot").child(Config.BOT_NAME_FOR_USERS).child("users").get().each()
    user_nodes = user_nodes or []
    user_lst = []
    for user in user_nodes:
        try:
            key = user.key()
            if key is not None:
                user_lst.append(int(key))
        except Exception:
            continue
    # Add administrators if they are not on the list
    for admin in Config.ADMIN:
        if admin not in user_lst:
            user_lst.append(admin)

    # We extract the text of Boadcast. If the message contains lines transfers, take all the lines after the first.
    lines = message.text.splitlines()
    if len(lines) > 1:
        broadcast_text = "\n".join(lines[1:]).strip()
    else:
        broadcast_text = message.text[len(Config.BROADCAST_MESSAGE):].strip()

    # If the message is a reference, we get it
    reply = message.reply_to_message if message.reply_to_message else None

    send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_BROADCAST_INITIATED_LOG_MSG.format(broadcast_text=broadcast_text))

    try:
        # We send a message to all users
        for user in user_lst:
            try:
                if user != 0:
                    # If the message is a reference, send it (depending on the type of content)
                    if reply:
                        try:
                            if reply.text:
                                safe_send_message(user, reply.text)
                            elif reply.video:
                                app.send_video(user, reply.video.file_id, caption=reply.caption)
                            elif reply.photo:
                                try:
                                    # Use supported API: take the largest available size's file_id
                                    largest = reply.photo.sizes[-1] if getattr(reply.photo, 'sizes', None) else None
                                    file_id = largest.file_id if largest else None
                                except Exception:
                                    file_id = None
                                if file_id:
                                    app.send_photo(user, file_id, caption=reply.caption)
                                else:
                                    # Fallback: try to forward original message with photo
                                    try:
                                        app.copy_message(chat_id=user, from_chat_id=message.chat.id, message_id=reply.id)
                                    except Exception:
                                        pass
                            elif reply.sticker:
                                app.send_sticker(user, reply.sticker.file_id)
                            elif reply.document:
                                app.send_document(user, reply.document.file_id, caption=reply.caption)
                            elif reply.audio:
                                app.send_audio(user, reply.audio.file_id, caption=reply.caption)
                            elif reply.animation:
                                app.send_animation(user, reply.animation.file_id, caption=reply.caption)
                        except AttributeError as e:
                            logger.error(safe_get_messages(message.chat.id).ADMIN_ERROR_PROCESSING_REPLY_MSG.format(user=user, error=e))
                            continue
                    # If there is an additional text, we send it
                    if broadcast_text:
                        safe_send_message(user, broadcast_text)
            except Exception as e:
                logger.error(safe_get_messages(message.chat.id).ADMIN_ERROR_SENDING_BROADCAST_MSG.format(user=user, error=e))
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_PROMO_SENT_MSG)
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_BROADCAST_SENT_LOG_MSG)
    except Exception as e:
        send_error_to_user(message, safe_get_messages(message.chat.id).ADMIN_CANNOT_SEND_PROMO_MSG)
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_BROADCAST_FAILED_LOG_MSG.format(error=str(e)))


# Getting the User Logs

def get_user_log(app, message):
    messages = safe_get_messages(message.chat.id)
    # Lazy import to avoid cycles
    from DATABASE.cache_db import get_from_local_cache
    user_id = str(message.chat.id)
    if int(message.chat.id) in Config.ADMIN and Config.GET_USER_LOGS_COMMAND in message.text:
        user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    logs_dict = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, "logs", user_id])
    if not logs_dict:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_USER_NO_DOWNLOADS_MSG)
        return

    logs = list(logs_dict.values())
    data, data_tg = [], []

    for l in logs:
        ts_raw = l.get("timestamp")
        try:
            ts = datetime.fromtimestamp(int(ts_raw)) if ts_raw is not None else datetime.fromtimestamp(0)
        except Exception:
            ts = datetime.fromtimestamp(0)
        id_val = l.get('ID', '-')
        name_val = l.get('name', '-')
        title_val = l.get('title', '-')
        urls_val = l.get('urls', '-')
        row = f"{ts} | {id_val} | {name_val} | {title_val} | {urls_val}"
        row_2 = f"<b>{ts}</b> | <code>{id_val}</code> | <b>{name_val}</b> | {title_val} | {urls_val}"
        data.append(row)
        data_tg.append(row_2)

    total = len(data_tg)
    least_10 = sorted(data_tg[-10:], key=str.lower) if total and total > 10 else sorted(data_tg, key=str.lower)
    format_str = "\n\n".join(least_10)
    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = safe_get_messages(message.chat.id).ADMIN_LOGS_FORMAT_MSG.format(bot_name=Config.BOT_NAME_FOR_USERS, user_id=user_id, total=total, now=now, logs='\n'.join(sorted(data, key=str.lower)))

    user_dir = os.path.join("users", str(message.chat.id))
    os.makedirs(user_dir, exist_ok=True)
    log_path = os.path.join(user_dir, "logs.txt")
    with open(log_path, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(safe_get_messages(message.chat.id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="userlogs_close|close")]])
    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(message.chat.id, safe_get_messages(message.chat.id).ADMIN_USER_LOGS_TOTAL_MSG.format(total=total, user_id=user_id, format_str=format_str), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    app.send_document(message.chat.id, log_path, caption=safe_get_messages(message.chat.id).ADMIN_USER_LOGS_CAPTION_MSG.format(user_id=user_id))
    from HELPERS.logger import get_log_channel
    app.send_document(get_log_channel("general"), log_path, caption=safe_get_messages(message.chat.id).ADMIN_USER_LOGS_CAPTION_MSG.format(user_id=user_id))


def get_user_usage_stats(app, message):
    """Get usage statistics for regular users"""
    # Lazy import to avoid cycles
    from DATABASE.cache_db import get_from_local_cache
    user_id = str(message.chat.id)

    logs_dict = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, "logs", user_id])
    if not logs_dict:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_USER_NO_DOWNLOADS_MSG)
        return

    logs = list(logs_dict.values())
    data, data_tg = [], []

    for l in logs:
        ts_raw = l.get("timestamp")
        try:
            ts = datetime.fromtimestamp(int(ts_raw)) if ts_raw is not None else datetime.fromtimestamp(0)
        except Exception:
            ts = datetime.fromtimestamp(0)
        id_val = l.get('ID', '-')
        name_val = l.get('name', '-')
        title_val = l.get('title', '-')
        urls_val = l.get('urls', '-')
        row = f"{ts} | {id_val} | {name_val} | {title_val} | {urls_val}"
        row_2 = f"<b>{ts}</b> | <code>{id_val}</code> | <b>{name_val}</b> | {title_val} | {urls_val}"
        data.append(row)
        data_tg.append(row_2)

    total = len(data_tg)
    least_10 = sorted(data_tg[-10:], key=str.lower) if total and total > 10 else sorted(data_tg, key=str.lower)
    format_str = "\n\n".join(least_10)
    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = safe_get_messages(message.chat.id).ADMIN_LOGS_FORMAT_MSG.format(bot_name=Config.BOT_NAME_FOR_USERS, user_id=user_id, total=total, now=now, logs='\n'.join(sorted(data, key=str.lower)))

    user_dir = os.path.join("users", str(message.chat.id))
    os.makedirs(user_dir, exist_ok=True)
    log_path = os.path.join(user_dir, "logs.txt")
    with open(log_path, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(safe_get_messages(message.chat.id).URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG, callback_data="userlogs_close|close")]])
    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(message.chat.id, safe_get_messages(message.chat.id).ADMIN_USER_LOGS_TOTAL_MSG.format(total=total, user_id=user_id, format_str=format_str), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    app.send_document(message.chat.id, log_path, caption=safe_get_messages(message.chat.id).ADMIN_USER_LOGS_CAPTION_MSG.format(user_id=user_id))


# Get All Kinds of Users (Users/ Blocked/ Unblocked)

def get_user_details(app, message):
    messages = safe_get_messages(message.chat.id)
    # Lazy import
    from DATABASE.cache_db import get_from_local_cache
    command = message.text.split(Config.GET_USER_DETAILS_COMMAND)[1].strip()
    path_map = {
        "_blocked": "blocked_users",
        "_unblocked": "unblocked_users",
        "_users": "users"
    }
    path = path_map.get(command)
    if not path:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_INVALID_COMMAND_MSG)
        return

    data_dict = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, path])
    if not data_dict:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_NO_DATA_FOUND_MSG.format(path=path))
        return

    # Support both dict and list structures from cache
    if isinstance(data_dict, dict):
        iterable = data_dict.values()
    elif isinstance(data_dict, list):
        iterable = data_dict
    else:
        iterable = []

    modified_lst, txt_lst = [], []
    for user in iterable:
        try:
            if isinstance(user, dict):
                user_id = str(user.get("ID")) if user.get("ID") is not None else None
                ts_raw = user.get("timestamp")
            else:
                # If element is not dict, treat it as a user id
                user_id = str(user)
                ts_raw = None

            if not user_id or user_id == "0":
                continue

            try:
                ts_val = int(ts_raw) if ts_raw is not None else 0
            except Exception:
                ts_val = 0
            ts = datetime.fromtimestamp(ts_val)

            txt_lst.append(f"TS: {ts} | ID: {user_id}")
            modified_lst.append(f"TS: <b>{ts}</b> | ID: <code>{user_id}</code>")
        except Exception:
            continue

    modified_lst.sort(key=str.lower)
    txt_lst.sort(key=str.lower)
    display_list = modified_lst[-20:] if len(modified_lst) > 20 else modified_lst

    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = safe_get_messages(message.chat.id).ADMIN_BOT_DATA_FORMAT_MSG.format(bot_name=Config.BOT_NAME_FOR_USERS, path=path, count=len(modified_lst), now=now, data='\n'.join(txt_lst))
    mod = safe_get_messages(message.chat.id).ADMIN_TOTAL_USERS_MSG.format(count=len(modified_lst), path=path, display_list='\n'.join(display_list))

    file = f"{path}.txt"
    with open(file, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    send_to_all(message, mod)
    app.send_document(message.chat.id, f"./{file}", caption=safe_get_messages(message.chat.id).ADMIN_BOT_DATA_CAPTION_MSG.format(bot_name=Config.BOT_NAME_FOR_USERS, path=path))
    from HELPERS.logger import get_log_channel
    app.send_document(get_log_channel("general"), f"./{file}", caption=safe_get_messages(message.chat.id).ADMIN_BOT_DATA_CAPTION_MSG.format(bot_name=Config.BOT_NAME_FOR_USERS, path=path))
    logger.info(mod)

# Block User

def block_user(app, message):
    messages = safe_get_messages(message.chat.id)
    guard = get_channel_guard()
    if int(message.chat.id) in Config.ADMIN:
        dt = math.floor(time.time())
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_BLOCK_USER_USAGE_MSG)
            return
        argument = parts[1].strip()
        argument_lower = argument.lower()

        # Channel guard helpers
        if guard:
            if argument_lower == "show":
                # Используем 48 часов (2 дня) вместо 3 дней
                hours_span = 48
                # Проверяем доступ к admin logs
                if not guard.can_read_admin_log():
                    safe_send_message(
                        message.chat.id,
                        messages.CHANNEL_GUARD_NO_ACCESS_MSG,
                        message=message,
                    )
                    return
                activity_entries = guard.export_recent_activity(hours=hours_span)
                if activity_entries:
                    join_total = sum(1 for item in activity_entries if item.get("type") == "join")
                    leave_total = sum(1 for item in activity_entries if item.get("type") == "leave")
                    lines = []
                    for entry in activity_entries:
                        emoji = "🟢" if entry.get("type") == "join" else "🔴"
                        dt_local = datetime.fromtimestamp(entry.get("timestamp", 0))
                        time_str = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                        user_id = entry.get("user_id")
                        username = entry.get("username")
                        username_part = f"@{username}" if username else ""
                        name_part = entry.get("name") or ""
                        display = (name_part + f" {username_part}").strip()
                        if not display:
                            display = f"ID {user_id}"
                        description = entry.get("description") or ""
                        # Добавляем Telegram ID в строку
                        lines.append(f"{emoji} {time_str} — {display} (ID: {user_id}) {description}".strip())
                    lines.append("")
                    lines.append(
                        messages.CHANNEL_GUARD_ACTIVITY_TOTALS_LINE_MSG.format(
                            joined=join_total,
                            left=leave_total,
                        )
                    )
                    user_dir = os.path.join("users", str(message.chat.id))
                    os.makedirs(user_dir, exist_ok=True)
                    file_path = os.path.join(user_dir, f"channel_activity_{int(time.time())}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                    try:
                        app.send_document(
                            message.chat.id,
                            file_path,
                            caption=messages.CHANNEL_GUARD_ACTIVITY_FILE_CAPTION_MSG.format(hours=hours_span),
                            reply_to_message_id=message.id,
                        )
                    except Exception as e:
                        logger.error(f"[block_user_show] Failed to send activity file: {e}")
                    safe_send_message(
                        message.chat.id,
                        messages.CHANNEL_GUARD_ACTIVITY_SUMMARY_MSG.format(hours=hours_span, joined=join_total, left=leave_total),
                        message=message,
                    )
                else:
                    safe_send_message(
                        message.chat.id,
                        messages.CHANNEL_GUARD_ACTIVITY_EMPTY_MSG.format(hours=hours_span),
                        message=message,
                    )

                # Показываем pending очередь только если она не пуста
                pending = guard.get_pending_leavers()
                if not pending:
                    # Не показываем сообщение "Очередь пуста" если уже показали активность
                    return
                rows = [
                    messages.CHANNEL_GUARD_PENDING_HEADER_MSG.format(total=len(pending))
                ]
                for entry in pending[:50]:
                    left_ts = int(entry.get("last_left_ts", entry.get("first_left_ts", 0)))
                    try:
                        left_dt = datetime.fromtimestamp(left_ts)
                        left_text = left_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        left_text = str(left_ts)
                    rows.append(
                        messages.CHANNEL_GUARD_PENDING_ROW_MSG.format(
                            user_id=entry.get("ID"),
                            name=entry.get("name") or entry.get("username") or "-",
                            username=entry.get("username") or "-",
                            last_left=left_text,
                        )
                    )
                if len(pending) > 50:
                    rows.append(messages.CHANNEL_GUARD_PENDING_MORE_MSG.format(extra=len(pending) - 50))
                rows.append(messages.CHANNEL_GUARD_PENDING_FOOTER_MSG)
                safe_send_message(message.chat.id, "\n".join(rows), message=message)
                return
            if argument_lower == "all":
                # Получаем всех пользователей, которые покинули канал за последние 48 часов
                hours_span = 48
                if not guard.can_read_admin_log():
                    safe_send_message(
                        message.chat.id,
                        messages.CHANNEL_GUARD_NO_ACCESS_MSG,
                        message=message,
                    )
                    return
                
                activity_entries = guard.export_recent_activity(hours=hours_span)
                # Получаем ID всех пользователей, которые покинули канал (тип "leave")
                leave_user_ids = set()
                for entry in activity_entries:
                    if entry.get("type") == "leave":
                        user_id = entry.get("user_id")
                        if user_id:
                            leave_user_ids.add(int(user_id))
                
                # Также добавляем pending leavers (на случай если они еще не попали в activity)
                pending_ids = guard.get_pending_ids()
                for uid in pending_ids:
                    leave_user_ids.add(uid)
                
                if not leave_user_ids:
                    safe_send_message(message.chat.id, messages.CHANNEL_GUARD_PENDING_EMPTY_MSG, message=message)
                    return
                
                # Проверяем, кто уже заблокирован
                snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
                all_blocked_users = snapshot.each() if snapshot else []
                blocked_ids = {int(str(b_user.key())) for b_user in (all_blocked_users or []) if b_user is not None}
                
                # Фильтруем только незаблокированных
                to_block_ids = [uid for uid in leave_user_ids if uid not in blocked_ids]
                
                if not to_block_ids:
                    safe_send_message(
                        message.chat.id,
                        messages.CHANNEL_GUARD_BLOCKED_ALL_MSG.format(count=0),
                        message=message,
                    )
                    return
                
                total_processed = 0
                for uid in to_block_ids:
                    try:
                        fake_msg = fake_message(
                            f"{Config.BLOCK_USER_COMMAND} {uid}",
                            message.chat.id,
                            original_chat_id=message.chat.id,
                            message_thread_id=getattr(message, "message_thread_id", None),
                            original_message=message,
                        )
                        block_user(app, fake_msg)
                        total_processed += 1
                    except Exception as e:
                        logger.error(f"[block_user_all] Failed to block user {uid}: {e}")
                
                safe_send_message(
                    message.chat.id,
                    messages.CHANNEL_GUARD_BLOCKED_ALL_MSG.format(count=total_processed),
                    message=message,
                )
                return
            if argument_lower == "auto":
                enabled = guard.toggle_auto_mode()
                status_msg = (
                    messages.CHANNEL_GUARD_AUTO_ENABLED_MSG
                    if enabled
                    else messages.CHANNEL_GUARD_AUTO_DISABLED_MSG
                )
                safe_send_message(message.chat.id, status_msg, message=message)
                return
            if argument_lower == "auto off":
                guard.set_auto_mode(False)
                safe_send_message(message.chat.id, messages.CHANNEL_GUARD_AUTO_DISABLED_MSG, message=message)
                return
            try:
                seconds = parse_period_to_seconds(argument)
                guard.set_auto_interval(seconds)
                safe_send_message(
                    message.chat.id,
                    messages.CHANNEL_GUARD_AUTO_INTERVAL_SET_MSG.format(interval=format_seconds_human(seconds)),
                    message=message,
                )
                return
            except ValueError:
                pass

        b_user_id = argument
        try:
            if int(b_user_id) in Config.ADMIN:
                send_to_all(message, safe_get_messages(message.chat.id).ADMIN_CANNOT_DELETE_ADMIN_MSG)
                return
        except Exception:
            pass

        snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
        all_blocked_users = snapshot.each() if snapshot else []
        b_users = [str(b_user.key()) for b_user in (all_blocked_users or []) if b_user is not None]

        if b_user_id not in b_users:
            data = {"ID": b_user_id, "timestamp": str(dt)}
            db.child(f"{Config.BOT_DB_PATH}/blocked_users/{b_user_id}").set(data)
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_USER_BLOCKED_MSG.format(user_id=b_user_id, date=datetime.fromtimestamp(dt)))
            if guard:
                guard.mark_user_blocked(b_user_id, reason="manual")
        else:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_USER_ALREADY_BLOCKED_MSG.format(user_id=b_user_id))
    else:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_NOT_ADMIN_MSG)


# Unblock User

def unblock_user(app, message):
    messages = safe_get_messages(message.chat.id)
    guard = get_channel_guard()
    if int(message.chat.id) in Config.ADMIN:
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_UNBLOCK_USER_USAGE_MSG)
            return
        ub_user_id = parts[1].strip()

        if ub_user_id.lower() == "all":
            snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
            all_blocked_users = snapshot.each() if snapshot else []
            user_ids = [
                str(b_user.key())
                for b_user in (all_blocked_users or [])
                if b_user is not None and str(b_user.key()) not in ("0", "")
            ]
            if not user_ids:
                send_to_user(message, messages.CHANNEL_GUARD_PENDING_EMPTY_MSG)
                return
            dt = math.floor(time.time())
            for user_id in user_ids:
                data = {"ID": user_id, "timestamp": str(dt)}
                db.child(f"{Config.BOT_DB_PATH}/unblocked_users/{user_id}").set(data)
                db.child(f"{Config.BOT_DB_PATH}/blocked_users/{user_id}").remove()
                if guard:
                    guard.record_manual_unblock(user_id)
            send_to_user(
                message,
                messages.ADMIN_UNBLOCK_ALL_DONE_MSG.format(count=len(user_ids), date=datetime.fromtimestamp(dt)),
            )
            return

        snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
        all_blocked_users = snapshot.each() if snapshot else []
        b_users = [str(b_user.key()) for b_user in (all_blocked_users or []) if b_user is not None]

        if ub_user_id in b_users:
            dt = math.floor(time.time())

            data = {"ID": ub_user_id, "timestamp": str(dt)}
            db.child(f"{Config.BOT_DB_PATH}/unblocked_users/{ub_user_id}").set(data)
            db.child(f"{Config.BOT_DB_PATH}/blocked_users/{ub_user_id}").remove()
            send_to_user(
                message, safe_get_messages(message.chat.id).ADMIN_USER_UNBLOCKED_MSG.format(user_id=ub_user_id, date=datetime.fromtimestamp(dt)))
            if guard:
                guard.record_manual_unblock(ub_user_id)

        else:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_USER_ALREADY_UNBLOCKED_MSG.format(user_id=ub_user_id))
    else:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_NOT_ADMIN_MSG)


def ban_time_command(app, message):
    messages = safe_get_messages(message.chat.id)
    if int(message.chat.id) not in Config.ADMIN:
        send_to_all(message, messages.ADMIN_NOT_ADMIN_MSG)
        return
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        safe_send_message(message.chat.id, messages.BAN_TIME_USAGE_MSG.format(command=Config.BAN_TIME_COMMAND), message=message)
        return
    duration = parts[1].strip()
    guard = get_channel_guard()
    try:
        seconds = parse_period_to_seconds(duration)
    except ValueError:
        safe_send_message(message.chat.id, messages.BAN_TIME_INTERVAL_INVALID_MSG, message=message)
        return
    guard.set_scan_interval(seconds)
    safe_send_message(
        message.chat.id,
        messages.BAN_TIME_SET_MSG.format(interval=format_seconds_human(seconds)),
        message=message,
    )


# Check Runtime

def check_runtime(message):
    messages = safe_get_messages(message.chat.id)
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        now = TimeFormatter(now)
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_BOT_RUNNING_TIME_MSG.format(time=now))
    pass


def _channel_guard_block_executor(user_id: int, reason: Optional[str] = None):
    admins = getattr(Config, "ADMIN", [])
    if not admins:
        return
    admin_id = admins[0]
    fake_msg = fake_message(f"{Config.BLOCK_USER_COMMAND} {user_id}", admin_id)
    fake_msg._auto_reason = reason
    block_user(app, fake_msg)


register_block_user_executor(_channel_guard_block_executor)



def uncache_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """
    Admin command to clear cache for a specific URL
    Usage: /uncache <URL>
    """
    # Lazy imports to avoid cycles
    from DATABASE.cache_db import get_url_hash
    from DATABASE.firebase_init import db_child_by_path

    user_id = message.chat.id
    text = message.text.strip()
    if len(text.split()) < 2:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_UNCACHE_USAGE_MSG)
        return
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_UNCACHE_INVALID_URL_MSG)
        return
    removed_any = False
    try:
        # Clearing the cache by video
        normalized_url = normalize_url_for_cache(url)
        url_hash = get_url_hash(normalized_url)
        video_cache_path = f"{Config.VIDEO_CACHE_DB_PATH}/{url_hash}"
        db_child_by_path(db, video_cache_path).remove()
        removed_any = True
        # Clear cache by image posts (for /img)
        try:
            img_cache_path = f"{Config.IMAGE_CACHE_DB_PATH}/{url_hash}"
            db_child_by_path(db, img_cache_path).remove()
            removed_any = True
        except Exception:
            pass
        # Clear cache by playlist (if any)
        playlist_url = get_clean_playlist_url(url)
        if playlist_url:
            playlist_normalized = normalize_url_for_cache(playlist_url)
            playlist_hash = get_url_hash(playlist_normalized)
            playlist_cache_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{playlist_hash}"
            db_child_by_path(db, playlist_cache_path).remove()
            removed_any = True
            # If there is a range (eg *1*5), clear the cache for each index
            m = re.search(r"\*(\d+)\*(\d+)", url)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                for idx in range(start, end + 1):
                    idx_path = f"{Config.PLAYLIST_CACHE_DB_PATH}/{playlist_hash}/{idx}"
                    db_child_by_path(db, idx_path).remove()
        # Clear cache for short/long YouTube links
        if is_youtube_url(url):
            short_url = youtube_to_short_url(url)
            long_url = youtube_to_long_url(url)
            for variant in [short_url, long_url]:
                norm = normalize_url_for_cache(variant)
                h = get_url_hash(norm)
                db_child_by_path(db, f"{Config.VIDEO_CACHE_DB_PATH}/{h}").remove()
                db_child_by_path(db, f"{Config.PLAYLIST_CACHE_DB_PATH}/{h}").remove()
        # Обновляем локальный кэш после удаления в локальном режиме
        use_firebase = getattr(Config, 'USE_FIREBASE', True)
        if not use_firebase and removed_any:
            from DATABASE.cache_db import reload_firebase_cache
            reload_firebase_cache()
        
        if removed_any:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_CACHE_CLEARED_MSG.format(url=url))
            send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_CACHE_CLEARED_LOG_MSG.format(user_id=user_id, url=url))
        else:
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_NO_CACHE_FOUND_MSG)
    except Exception as e:
        send_to_all(message, safe_get_messages(message.chat.id).ADMIN_ERROR_CLEARING_CACHE_MSG.format(error=e))


@app.on_message(filters.command("update_porn") & filters.private)
@background_handler(label="update_porn")
def update_porn_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Admin command to run the porn list update script"""
    if int(message.chat.id) not in Config.ADMIN:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ACCESS_DENIED_MSG)
        return
    
    script_path = getattr(Config, "UPDATE_PORN_SCRIPT_PATH", "./script.sh")
    
    try:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_UPDATE_PORN_RUNNING_MSG.format(script_path=script_path))
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_UPDATE_STARTED_LOG_MSG.format(user_id=message.chat.id, script_path=script_path))
        
        # Run the script
        result = subprocess.run(
            [script_path], 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            cwd=os.getcwd()  # Run from bot root directory
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                send_to_user(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_COMPLETED_WITH_OUTPUT_MSG.format(output=output))
            else:
                send_to_user(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_COMPLETED_MSG)
            send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_UPDATE_COMPLETED_LOG_MSG.format(user_id=message.chat.id))
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            send_to_user(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_FAILED_MSG.format(returncode=result.returncode, error=error_msg))
            send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_UPDATE_FAILED_LOG_MSG.format(user_id=message.chat.id, error=error_msg))
            
    except FileNotFoundError:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_NOT_FOUND_MSG.format(script_path=script_path))
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_SCRIPT_NOT_FOUND_LOG_MSG.format(user_id=message.chat.id, script_path=script_path))
    except Exception as e:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ERROR_RUNNING_SCRIPT_MSG.format(error=str(e)))
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_UPDATE_ERROR_LOG_MSG.format(user_id=message.chat.id, error=str(e)))


@app.on_message(filters.command("reload_porn") & filters.private)
@background_handler(label="reload_porn")
def reload_porn_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Admin command to reload porn domains and keywords cache without restarting the bot"""
    if int(message.chat.id) not in Config.ADMIN:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ACCESS_DENIED_MSG)
        return
    
    try:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_RELOADING_PORN_MSG)
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_CACHE_RELOAD_STARTED_LOG_MSG.format(user_id=message.chat.id))
        
        # Import and reload all caches (files + CONFIG/domains.py arrays)
        from HELPERS.porn import reload_all_porn_caches
        counts = reload_all_porn_caches()

        send_to_user(
            message,
            safe_get_messages(message.chat.id).ADMIN_PORN_CACHES_RELOADED_MSG.format(
                porn_domains=counts.get('porn_domains', 0),
                porn_keywords=counts.get('porn_keywords', 0),
                supported_sites=counts.get('supported_sites', 0),
                whitelist=counts.get('whitelist', 0),
                greylist=counts.get('greylist', 0),
                black_list=counts.get('black_list', 0),
                white_keywords=counts.get('white_keywords', 0),
                proxy_domains=counts.get('proxy_domains', 0),
                proxy_2_domains=counts.get('proxy_2_domains', 0),
                clean_query=counts.get('clean_query', 0),
                no_cookie_domains=counts.get('no_cookie_domains', 0)
            )
        )

        send_to_logger(
            message,
            safe_get_messages(message.chat.id).ADMIN_PORN_CACHE_RELOADED_MSG.format(
                admin_id=message.chat.id,
                domains=counts.get('porn_domains', 0),
                keywords=counts.get('porn_keywords', 0),
                sites=counts.get('supported_sites', 0),
                whitelist=counts.get('whitelist', 0),
                greylist=counts.get('greylist', 0),
                black_list=counts.get('black_list', 0),
                white_keywords=counts.get('white_keywords', 0),
                proxy_domains=counts.get('proxy_domains', 0),
                proxy_2_domains=counts.get('proxy_2_domains', 0),
                clean_query=counts.get('clean_query', 0),
                no_cookie_domains=counts.get('no_cookie_domains', 0)
            )
        )
        
    except Exception as e:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ERROR_RELOADING_PORN_MSG.format(error=str(e)))
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_CACHE_RELOAD_ERROR_LOG_MSG.format(user_id=message.chat.id, error=str(e)))


@app.on_message(filters.command("check_porn") & filters.private)
@background_handler(label="check_porn")
def check_porn_command(app, message):
    messages = safe_get_messages(message.chat.id)
    """Admin command to check if a URL is NSFW and get detailed explanation"""
    user_id = message.chat.id
    
    # First check if user is subscribed to channel
    if not is_user_in_channel(app, message):
        return
    
    # Then check if user is admin
    if int(user_id) not in Config.ADMIN:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ACCESS_DENIED_MSG)
        return
    
    text = message.text.strip()
    if len(text.split()) < 2:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_CHECK_PORN_USAGE_MSG)
        return
    
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_CHECK_PORN_INVALID_URL_MSG)
        return
    
    try:
        # Send initial status message
        status_msg = safe_send_message(user_id, safe_get_messages(message.chat.id).ADMIN_CHECKING_URL_MSG.format(url=url), parse_mode=enums.ParseMode.HTML)
        
        # Import the detailed check function
        from HELPERS.porn import check_porn_detailed
        
        # For now, we'll check without title/description since we don't have video info
        # In a real scenario, you might want to fetch video info first
        is_nsfw, explanation = check_porn_detailed(url, "", "", None)
        
        # Format the result
        status_icon = safe_get_messages(message.chat.id).ADMIN_STATUS_NSFW_MSG if is_nsfw else safe_get_messages(message.chat.id).ADMIN_STATUS_CLEAN_MSG
        status_text = safe_get_messages(message.chat.id).ADMIN_STATUS_NSFW_TEXT_MSG if is_nsfw else safe_get_messages(message.chat.id).ADMIN_STATUS_CLEAN_TEXT_MSG
        
        result_message = safe_get_messages(message.chat.id).ADMIN_PORN_CHECK_RESULT_MSG.format(
            status_icon=status_icon,
            url=url,
            status_text=status_text,
            explanation=explanation
        )
        
        # Update the status message with results
        if status_msg:
            safe_edit_message_text(message.chat.id, status_msg.id, result_message, parse_mode=enums.ParseMode.HTML)
        else:
            safe_send_message(user_id, result_message, parse_mode=enums.ParseMode.HTML)
        
        # Log the check
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_PORN_CHECK_LOG_MSG.format(user_id=message.chat.id, url=url, status=status_text))
        
    except Exception as e:
        error_msg = safe_get_messages(message.chat.id).ADMIN_ERROR_CHECKING_URL_MSG.format(error=str(e))
        if 'status_msg' in locals() and status_msg:
            safe_edit_message_text(message.chat.id, status_msg.id, error_msg)
        else:
            safe_send_message(user_id, error_msg, parse_mode=enums.ParseMode.HTML)
        send_to_logger(message, safe_get_messages(message.chat.id).ADMIN_CHECK_PORN_ERROR_LOG_MSG.format(admin_id=message.chat.id, error=str(e)))

