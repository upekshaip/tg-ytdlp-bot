from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_user, send_to_logger, send_to_all, send_error_to_user
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from HELPERS.safe_messeger import safe_send_message, safe_send_message_with_auto_delete, safe_edit_message_text, safe_delete_messages
from CONFIG.config import Config
from datetime import datetime
import subprocess
import sys
import math
import time
import os
import re
import threading
# from DATABASE.cache_db import reload_firebase_cache, get_from_local_cache  # moved to lazy imports
from DATABASE.firebase_init import db
from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
from URL_PARSERS.normalizer import normalize_url_for_cache, get_clean_playlist_url
from HELPERS.limitter import TimeFormatter, is_user_in_channel
# from DATABASE.cache_db import get_url_hash, db_child_by_path  # moved to lazy imports
from HELPERS.logger import logger

# Global variable for bot start time
starting_point = [time.time()]

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("reload_cache") & filters.private)
def reload_firebase_cache_command(app, message):
    """The processor of command for rebooting the local cache Firebase"""
    if int(message.chat.id) not in Config.ADMIN:
        from CONFIG.messages import MessagesConfig as Messages
        safe_send_message_with_auto_delete(message.chat.id, Messages.ACCESS_DENIED_ADMIN_MSG, delete_after_seconds=60)
        return
    
    # Check if this is a fake message (called programmatically)
    is_fake_message = getattr(message, '_is_fake_message', False) or message.id == 0
    
    try:
        # 1) Download fresh dump via external script path
        script_path = getattr(Config, "DOWNLOAD_FIREBASE_SCRIPT_PATH", "DATABASE/download_firebase.py")
        # Ensure we have the full path to the script
        if not os.path.isabs(script_path):
            script_path = os.path.join(os.getcwd(), script_path)
        
        # Verify script exists
        if not os.path.exists(script_path):
            from CONFIG.messages import MessagesConfig as Messages
            error_msg = Messages.SCRIPT_NOT_FOUND_MSG.format(path=script_path)
            safe_send_message_with_auto_delete(message.chat.id, error_msg, delete_after_seconds=60)
            send_to_logger(message, f"Script not found: {script_path}")
            return
            
        # Send initial status message (skip for fake_message)
        status_msg = None
        if not is_fake_message:
            from CONFIG.messages import MessagesConfig as Messages
            status_msg = safe_send_message(message.chat.id, Messages.ADMIN_FIREBASE_DUMP_MSG.format(path=script_path))
            if not status_msg:
                send_to_logger(message, "Failed to send initial status message")
                return
        
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=os.path.dirname(os.path.dirname(script_path)))
        if result.returncode != 0:
            error_msg = f"❌ Error running {script_path}:\n{result.stdout}\n{result.stderr}"
            if is_fake_message:
                # Do not send anything to chat on fake_message
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                send_to_logger(message, f"Error running {script_path}: {result.stdout}\n{result.stderr}")
            else:
                safe_edit_message_text(message.chat.id, status_msg.id, error_msg)
                # Schedule deletion after 60 seconds for real messages
                def delete_msg():
                    time.sleep(60)
                    safe_delete_messages(message.chat.id, [status_msg.id])
                threading.Thread(target=delete_msg, daemon=True).start()
                from HELPERS.logger import log_error_to_channel
                log_error_to_channel(message, error_msg)
                send_to_logger(message, f"Error running {script_path}: {result.stdout}\n{result.stderr}")
            return
        
        # Update status to reloading
        if is_fake_message:
            # Do not send anything to chat on fake_message
            pass
        else:
            from CONFIG.messages import MessagesConfig as Messages
            safe_edit_message_text(message.chat.id, status_msg.id, Messages.RELOADING_FIREBASE_MSG)
        
        # 2) Reload local cache into memory
        from DATABASE.cache_db import reload_firebase_cache as _reload_local
        success = _reload_local()
        if success:
            from CONFIG.messages import MessagesConfig as Messages
            final_msg = getattr(Messages, 'ADMIN_FIREBASE_RELOADED_SUCCESS_MSG', "✅ Firebase cache reloaded successfully!")
            if is_fake_message:
                # Only log to channel/logger
                send_to_logger(message, "Firebase cache reloaded by auto task.")
            else:
                safe_edit_message_text(message.chat.id, status_msg.id, final_msg)
                # Schedule deletion after 60 seconds for real messages
                def delete_msg():
                    time.sleep(60)
                    safe_delete_messages(message.chat.id, [status_msg.id])
                threading.Thread(target=delete_msg, daemon=True).start()
                send_to_logger(message, "Firebase cache reloaded by admin.")
        else:
            cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
            from CONFIG.messages import MessagesConfig as Messages
            final_msg = getattr(Messages, 'ADMIN_FIREBASE_RELOAD_FAILED_MSG', "❌ Failed to reload Firebase cache. Check if {cache_file} exists.").replace('{cache_file}', cache_file)
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
        from CONFIG.messages import MessagesConfig as Messages
        error_msg = getattr(Messages, 'GENERIC_ERROR_WITH_DETAIL_MSG', '❌ Error: {detail}').format(detail=f"reloading cache: {str(e)}")
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
        send_to_logger(message, f"Error reloading Firebase cache: {str(e)}")

# SEND BRODCAST Message to All Users

def send_promo_message(app, message):
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

    send_to_logger(message, f"Broadcast initiated. Text:\n{broadcast_text}")

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
                            logger.error(f"Error processing reply message for user {user}: {e}")
                            continue
                    # If there is an additional text, we send it
                    if broadcast_text:
                        safe_send_message(user, broadcast_text)
            except Exception as e:
                logger.error(f"Error sending broadcast to user {user}: {e}")
        from CONFIG.messages import MessagesConfig as Messages
        send_to_all(message, getattr(Messages, 'ADMIN_PROMO_SENT_MSG', "<b>✅ Promo message sent to all other users</b>"))
        send_to_logger(message, "Broadcast message sent to all users.")
    except Exception as e:
        from CONFIG.messages import MessagesConfig as Messages
        send_error_to_user(message, getattr(Messages, 'ADMIN_PROMO_FAILED_MSG', "<b>❌ Cannot send the promo message. Try replying to a message\nOr some error occurred</b>"))
        send_to_logger(message, f"Failed to broadcast message: {e}")


# Getting the User Logs

def get_user_log(app, message):
    # Lazy import to avoid cycles
    from DATABASE.cache_db import get_from_local_cache
    from CONFIG.messages import MessagesConfig as Messages
    user_id = str(message.chat.id)
    if int(message.chat.id) in Config.ADMIN and Config.GET_USER_LOGS_COMMAND in message.text:
        user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    logs_dict = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, "logs", user_id])
    if not logs_dict:
        send_to_all(message, getattr(Messages, 'ADMIN_USER_NO_LOGS_MSG', "<b>❌ User did not download any content yet...</b> Not exist in logs"))
        return

    logs = list(logs_dict.values())
    data, data_tg = [], []

    for l in logs:
        ts = datetime.fromtimestamp(int(l["timestamp"]))
        name = l.get('name', 'Unknown')
        row = f"{ts} | {l['ID']} | {name} | {l['title']} | {l['urls']}"
        row_2 = f"<b>{ts}</b> | <code>{l['ID']}</code> | <b>{name}</b> | {l['title']} | {l['urls']}"
        data.append(row)
        data_tg.append(row_2)

    total = len(data_tg)
    least_10 = sorted(data_tg[-10:], key=str.lower) if total > 10 else sorted(data_tg, key=str.lower)
    format_str = "\n\n".join(least_10)
    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = f"Logs of {Config.BOT_NAME_FOR_USERS}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n\n" + '\n'.join(sorted(data, key=str.lower))

    user_dir = os.path.join("users", str(message.chat.id))
    os.makedirs(user_dir, exist_ok=True)
    log_path = os.path.join(user_dir, "logs.txt")
    with open(log_path, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(getattr(Messages, 'BTN_CLOSE', "🔚Close"), callback_data="userlogs_close|close")]])
    from HELPERS.safe_messeger import safe_send_message
    safe_send_message(message.chat.id, Messages.ADMIN_LOGS_TOTAL_MSG.format(total=total, user=user_id, lines=format_str), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    app.send_document(message.chat.id, log_path, caption=Messages.ADMIN_ALL_LOGS_CAPTION_MSG.format(user=user_id))
    from HELPERS.logger import get_log_channel
    app.send_document(get_log_channel("general"), log_path, caption=Messages.ADMIN_ALL_LOGS_CAPTION_MSG.format(user=user_id))


# Get All Kinds of Users (Users/ Blocked/ Unblocked)

def get_user_details(app, message):
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
        from CONFIG.messages import MessagesConfig as Messages
        send_to_all(message, getattr(Messages, 'ADMIN_INVALID_COMMAND_MSG', "❌ Invalid command"))
        return

    data_dict = get_from_local_cache(["bot", Config.BOT_NAME_FOR_USERS, path])
    if not data_dict:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_all(message, getattr(Messages, 'ADMIN_NO_DATA_IN_CACHE_MSG', "❌ No data found in cache for <code>{path}</code>").format(path=path))
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
    txt_format = f"{Config.BOT_NAME_FOR_USERS} {path}\nTotal {path}: {len(modified_lst)}\nCurrent time: {now}\n\n" + '\n'.join(txt_lst)
    mod = f"<i>Total Users: {len(modified_lst)}</i>\nLast 20 {path}:\n\n" + '\n'.join(display_list)

    file = f"{path}.txt"
    with open(file, 'w', encoding="utf-8") as f:
        f.write(txt_format)

    send_to_all(message, mod)
    from CONFIG.messages import MessagesConfig as Messages
    app.send_document(message.chat.id, f"./{file}", caption=Messages.ADMIN_DUMP_CAPTION_MSG.format(bot=Config.BOT_NAME_FOR_USERS, path=path))
    from HELPERS.logger import get_log_channel
    app.send_document(get_log_channel("general"), f"./{file}", caption=f"{Config.BOT_NAME_FOR_USERS} - all {path}")
    logger.info(mod)

# Block User

def block_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        dt = math.floor(time.time())
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.USAGE_BLOCK_USER_MSG)
            return
        b_user_id = parts[1].strip()

        try:
            if int(b_user_id) in Config.ADMIN:
                from CONFIG.messages import MessagesConfig as Messages
                send_to_all(message, getattr(Messages, 'ADMIN_CANNOT_DELETE_ADMIN_MSG', "🚫 Admin cannot delete an admin"))
                return
        except Exception:
            pass

        snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
        all_blocked_users = snapshot.each() if snapshot else []
        b_users = [str(b_user.key()) for b_user in (all_blocked_users or []) if b_user is not None]

        if b_user_id not in b_users:
            data = {"ID": b_user_id, "timestamp": str(dt)}
            db.child(f"{Config.BOT_DB_PATH}/blocked_users/{b_user_id}").set(data)
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.USER_BLOCKED_MSG.format(user_id=b_user_id, blocked_date=datetime.fromtimestamp(dt)))
        else:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.USER_ALREADY_BLOCKED_MSG.format(user_id=b_user_id))
    else:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_all(message, getattr(Messages, 'ADMIN_NOT_ADMIN_MSG', "🚫 Sorry! You are not an admin"))


# Unblock User

def unblock_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.USAGE_UNBLOCK_USER_MSG)
            return
        ub_user_id = parts[1].strip()

        snapshot = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get()
        all_blocked_users = snapshot.each() if snapshot else []
        b_users = [str(b_user.key()) for b_user in (all_blocked_users or []) if b_user is not None]

        if ub_user_id in b_users:
            dt = math.floor(time.time())

            data = {"ID": ub_user_id, "timestamp": str(dt)}
            db.child(f"{Config.BOT_DB_PATH}/unblocked_users/{ub_user_id}").set(data)
            db.child(f"{Config.BOT_DB_PATH}/blocked_users/{ub_user_id}").remove()
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(
                message, getattr(Messages, 'ADMIN_USER_UNBLOCKED_MSG', "User unblocked 🔓✅\n \nID: <code>{user}</code>\nUnblocked Date: {date}").format(user=ub_user_id, date=datetime.fromtimestamp(dt)))

        else:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.USER_ALREADY_UNBLOCKED_MSG.format(user_id=ub_user_id))
    else:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_all(message, getattr(Messages, 'ADMIN_NOT_ADMIN_MSG', "🚫 Sorry! You are not an admin"))


# Check Runtime

def check_runtime(message):
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        from CONFIG.messages import MessagesConfig as Messages
        now = TimeFormatter(now)
        send_to_user(message, Messages.BOT_RUNNING_TIME_MSG.format(uptime=now))
    pass



def uncache_command(app, message):
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
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.UNCACHE_USAGE_MSG)
        return
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.UNCACHE_URL_INVALID_MSG)
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
        if removed_any:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.UNCACHE_CLEARED_MSG.format(url=url))
            send_to_logger(message, f"Admin {user_id} cleared cache for URL: {url}")
        else:
            from CONFIG.messages import MessagesConfig as Messages
            send_to_user(message, Messages.UNCACHE_NOT_FOUND_MSG)
    except Exception as e:
        send_to_all(message, f"❌ Error clearing cache: {e}")


@app.on_message(filters.command("update_porn") & filters.private)
def update_porn_command(app, message):
    """Admin command to run the porn list update script"""
    if int(message.chat.id) not in Config.ADMIN:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.ACCESS_DENIED_ADMIN_MSG)
        return
    
    script_path = getattr(Config, "UPDATE_PORN_SCRIPT_PATH", "./script.sh")
    
    try:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.RUNNING_PORN_UPDATE_SCRIPT_MSG.format(path=script_path))
        send_to_logger(message, f"Admin {message.chat.id} started porn list update script: {script_path}")
        
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
            from CONFIG.messages import MessagesConfig as Messages
            if output:
                send_to_user(message, Messages.SCRIPT_COMPLETED_WITH_OUTPUT_MSG.format(output=output))
            else:
                send_to_user(message, Messages.SCRIPT_COMPLETED_SUCCESS_MSG)
            send_to_logger(message, f"Porn list update script completed successfully by admin {message.chat.id}")
        else:
            from CONFIG.messages import MessagesConfig as Messages
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            send_to_user(message, Messages.SCRIPT_FAILED_WITH_CODE_MSG.format(code=result.returncode, error=error_msg))
            send_to_logger(message, f"Porn list update script failed by admin {message.chat.id}: {error_msg}")
            
    except FileNotFoundError:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.SCRIPT_NOT_FOUND_MSG.format(path=script_path))
        send_to_logger(message, f"Admin {message.chat.id} tried to run non-existent script: {script_path}")
    except Exception as e:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.ERROR_RUNNING_SCRIPT_MSG.format(error=str(e)))
        send_to_logger(message, f"Error running porn update script by admin {message.chat.id}: {str(e)}")


@app.on_message(filters.command("reload_porn") & filters.private)
def reload_porn_command(app, message):
    """Admin command to reload porn domains and keywords cache without restarting the bot"""
    if int(message.chat.id) not in Config.ADMIN:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.ACCESS_DENIED_ADMIN_MSG)
        return
    
    try:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.RELOADING_PORN_CACHE_MSG)
        send_to_logger(message, f"Admin {message.chat.id} started porn cache reload")
        
        # Import and reload all caches (files + CONFIG/domains.py arrays)
        from HELPERS.porn import reload_all_porn_caches
        counts = reload_all_porn_caches()

        send_to_user(
            message,
            (
                "✅ Porn caches reloaded successfully!\n\n"
                "📊 Current cache status:\n"
                f"• Porn domains: {counts.get('porn_domains', 0)}\n"
                f"• Porn keywords: {counts.get('porn_keywords', 0)}\n"
                f"• Supported sites: {counts.get('supported_sites', 0)}\n"
                f"• WHITELIST: {counts.get('whitelist', 0)}\n"
                f"• GREYLIST: {counts.get('greylist', 0)}\n"
                f"• BLACK_LIST: {counts.get('black_list', 0)}\n"
                f"• WHITE_KEYWORDS: {counts.get('white_keywords', 0)}\n"
                f"• PROXY_DOMAINS: {counts.get('proxy_domains', 0)}\n"
                f"• PROXY_2_DOMAINS: {counts.get('proxy_2_domains', 0)}\n"
                f"• CLEAN_QUERY: {counts.get('clean_query', 0)}\n"
                f"• NO_COOKIE_DOMAINS: {counts.get('no_cookie_domains', 0)}"
            )
        )

        send_to_logger(
            message,
            (
                f"Porn caches reloaded by admin {message.chat.id}. "
                f"Domains: {counts.get('porn_domains', 0)}, Keywords: {counts.get('porn_keywords', 0)}, Sites: {counts.get('supported_sites', 0)}, "
                f"WHITELIST: {counts.get('whitelist', 0)}, GREYLIST: {counts.get('greylist', 0)}, BLACK_LIST: {counts.get('black_list', 0)}, "
                f"WHITE_KEYWORDS: {counts.get('white_keywords', 0)}, PROXY_DOMAINS: {counts.get('proxy_domains', 0)}, PROXY_2_DOMAINS: {counts.get('proxy_2_domains', 0)}, "
                f"CLEAN_QUERY: {counts.get('clean_query', 0)}, NO_COOKIE_DOMAINS: {counts.get('no_cookie_domains', 0)}"
            )
        )
        
    except Exception as e:
        from CONFIG.messages import MessagesConfig as Messages
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.ADMIN_ERROR_RELOADING_PORN_CACHE_MSG.format(error=str(e)))
        send_to_logger(message, f"Error reloading porn cache by admin {message.chat.id}: {str(e)}")


@app.on_message(filters.command("check_porn") & filters.private)
def check_porn_command(app, message):
    """Admin command to check if a URL is NSFW and get detailed explanation"""
    user_id = message.chat.id
    
    # First check if user is subscribed to channel
    if not is_user_in_channel(app, message):
        return
    
    # Then check if user is admin
    if int(user_id) not in Config.ADMIN:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, Messages.ACCESS_DENIED_ADMIN_MSG)
        return
    
    text = message.text.strip()
    if len(text.split()) < 2:
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, getattr(Messages, 'CHECK_PORN_USAGE_MSG', "❌ Please provide a URL to check.\nUsage: <code>/check_porn &lt;URL&gt;</code>"))
        return
    
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        from CONFIG.messages import MessagesConfig as Messages
        send_to_user(message, getattr(Messages, 'CHECK_PORN_URL_INVALID_MSG', "❌ Please provide a valid URL.\nUsage: <code>/check_porn &lt;URL&gt;</code>"))
        return
    
    try:
        # Send initial status message
        from CONFIG.messages import MessagesConfig as Messages
        status_msg = safe_send_message(user_id, Messages.ADMIN_CHECKING_URL_NSFW_MSG.format(url=url), parse_mode=enums.ParseMode.HTML)
        
        # Import the detailed check function
        from HELPERS.porn import check_porn_detailed
        
        # For now, we'll check without title/description since we don't have video info
        # In a real scenario, you might want to fetch video info first
        is_nsfw, explanation = check_porn_detailed(url, "", "", None)
        
        # Format the result
        status_icon = "🔞" if is_nsfw else "✅"
        status_text = "NSFW" if is_nsfw else "Clean"
        
        result_message = f"{status_icon} <b>Porn Check Result</b>\n\n"
        result_message += f"<b>URL:</b> <code>{url}</code>\n"
        result_message += f"<b>Status:</b> <b>{status_text}</b>\n\n"
        result_message += f"<b>Explanation:</b>\n{explanation}"
        
        # Update the status message with results
        if status_msg:
            safe_edit_message_text(message.chat.id, status_msg.id, result_message, parse_mode=enums.ParseMode.HTML)
        else:
            safe_send_message(user_id, result_message, parse_mode=enums.ParseMode.HTML)
        
        # Log the check
        send_to_logger(message, f"Admin {message.chat.id} checked URL for NSFW: {url} - Result: {status_text}")
        
    except Exception as e:
        error_msg = f"❌ Error checking URL: {str(e)}"
        if 'status_msg' in locals() and status_msg:
            safe_edit_message_text(message.chat.id, status_msg.id, error_msg)
        else:
            safe_send_message(user_id, error_msg, parse_mode=enums.ParseMode.HTML)
        send_to_logger(message, f"Error in check_porn command by admin {message.chat.id}: {str(e)}")

