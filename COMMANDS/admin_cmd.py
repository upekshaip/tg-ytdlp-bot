from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_user, send_to_logger, send_to_all
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from CONFIG.config import Config
from datetime import datetime
import subprocess
import sys
import math
import time
import os
import re
# from DATABASE.cache_db import reload_firebase_cache, get_from_local_cache  # moved to lazy imports
from DATABASE.firebase_init import db
from URL_PARSERS.youtube import is_youtube_url, youtube_to_short_url, youtube_to_long_url
from URL_PARSERS.normalizer import normalize_url_for_cache, get_clean_playlist_url
from HELPERS.limitter import TimeFormatter
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
        send_to_user(message, "❌ Access denied. Admin only.")
        return
    try:
        # 1) Download fresh dump via external script path
        script_path = getattr(Config, "DOWNLOAD_FIREBASE_SCRIPT_PATH", "download_firebase.py")
        send_to_user(message, f"⏳ Downloading fresh Firebase dump using {script_path} ...")
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            send_to_user(message, f"❌ Error running {script_path}:\n{result.stdout}\n{result.stderr}")
            send_to_logger(message, f"Error running {script_path}: {result.stdout}\n{result.stderr}")
            return
        # 2) Reload local cache into memory
        from DATABASE.cache_db import reload_firebase_cache as _reload_local
        success = _reload_local()
        if success:
            send_to_user(message, "✅ Firebase cache reloaded successfully!")
            send_to_logger(message, "Firebase cache reloaded by admin.")
        else:
            cache_file = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
            send_to_user(message, f"❌ Failed to reload Firebase cache. Check if {cache_file} exists.")
    except Exception as e:
        send_to_user(message, f"❌ Error reloading cache: {str(e)}")
        send_to_logger(message, f"Error reloading Firebase cache: {str(e)}")

# SEND BRODCAST Message to All Users

def send_promo_message(app, message):
    # We get a list of users from the base
    user_lst = db.child("bot").child("tgytdlp_bot").child("users").get().each()
    user_lst = [int(user.key()) for user in user_lst]
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
                                app.send_message(user, reply.text)
                            elif reply.video:
                                app.send_video(user, reply.video.file_id, caption=reply.caption)
                            elif reply.photo:
                                app.send_photo(user, reply.photo.file_id, caption=reply.caption)
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
                        app.send_message(user, broadcast_text)
            except Exception as e:
                logger.error(f"Error sending broadcast to user {user}: {e}")
        send_to_all(message, "<b>✅ Promo message sent to all other users</b>")
        send_to_logger(message, "Broadcast message sent to all users.")
    except Exception as e:
        send_to_all(message, "<b>❌ Cannot send the promo message. Try replying to a message\nOr some error occurred</b>")
        send_to_logger(message, f"Failed to broadcast message: {e}")


# Getting the User Logs

def get_user_log(app, message):
    # Lazy import to avoid cycles
    from DATABASE.cache_db import get_from_local_cache
    user_id = str(message.chat.id)
    if int(message.chat.id) in Config.ADMIN and Config.GET_USER_LOGS_COMMAND in message.text:
        user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    logs_dict = get_from_local_cache(["bot", "tgytdlp_bot", "logs", user_id])
    if not logs_dict:
        send_to_all(message, "<b>❌ User did not download any content yet...</b> Not exist in logs")
        return

    logs = list(logs_dict.values())
    data, data_tg = [], []

    for l in logs:
        ts = datetime.fromtimestamp(int(l["timestamp"]))
        row = f"{ts} | {l['ID']} | {l['name']} | {l['title']} | {l['urls']}"
        row_2 = f"<b>{ts}</b> | <code>{l['ID']}</code> | <b>{l['name']}</b> | {l['title']} | {l['urls']}"
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

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔚 Close", callback_data="userlogs_close|close")]])
    app.send_message(message.chat.id, f"Total: <b>{total}</b>\n<b>{user_id}</b> - logs (Last 10):\n\n{format_str}", parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    app.send_document(message.chat.id, log_path, caption=f"{user_id} - all logs")
    app.send_document(Config.LOGS_ID, log_path, caption=f"{user_id} - all logs")


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
        send_to_all(message, "❌ Invalid command")
        return

    data_dict = get_from_local_cache(["bot", "tgytdlp_bot", path])
    if not data_dict:
        send_to_all(message, f"❌ No data found in cache for <code>{path}</code>")
        return

    modified_lst, txt_lst = [], []
    for user in data_dict.values():
        if user["ID"] != "0":
            ts = datetime.fromtimestamp(int(user["timestamp"]))
            txt_lst.append(f"TS: {ts} | ID: {user['ID']}")
            modified_lst.append(f"TS: <b>{ts}</b> | ID: <code>{user['ID']}</code>")

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
    app.send_document(message.chat.id, f"./{file}", caption=f"{Config.BOT_NAME_FOR_USERS} - all {path}")
    app.send_document(Config.LOGS_ID, f"./{file}", caption=f"{Config.BOT_NAME_FOR_USERS} - all {path}")
    logger.info(mod)

# Block User

def block_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        dt = math.floor(time.time())
        b_user_id = str((message.text).split(
            Config.BLOCK_USER_COMMAND + " ")[1])

        if int(b_user_id) in Config.ADMIN:
            send_to_all(message, "🚫 Admin cannot delete an admin")
        else:
            all_blocked_users = db.child(
                f"{Config.BOT_DB_PATH}/blocked_users").get().each()
            b_users = [b_user.key() for b_user in all_blocked_users]

            if b_user_id not in b_users:
                data = {"ID": b_user_id, "timestamp": str(dt)}
                db.child(
                    f"{Config.BOT_DB_PATH}/blocked_users/{b_user_id}").set(data)
                send_to_user(
                    message, f"User blocked 🔒❌\n \nID: <code>{b_user_id}</code>\nBlocked Date: {datetime.fromtimestamp(dt)}")

            else:
                send_to_user(message, f"<code>{b_user_id}</code> is already blocked ❌😐")
    else:
        send_to_all(message, "🚫 Sorry! You are not an admin")


# Unblock User

def unblock_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        ub_user_id = str((message.text).split(
            Config.UNBLOCK_USER_COMMAND + " ")[1])
        all_blocked_users = db.child(
            f"{Config.BOT_DB_PATH}/blocked_users").get().each()
        b_users = [b_user.key() for b_user in all_blocked_users]

        if ub_user_id in b_users:
            dt = math.floor(time.time())

            data = {"ID": ub_user_id, "timestamp": str(dt)}
            db.child(
                f"{Config.BOT_DB_PATH}/unblocked_users/{ub_user_id}").set(data)
            db.child(
                f"{Config.BOT_DB_PATH}/blocked_users/{ub_user_id}").remove()
            send_to_user(
                message, f"User unblocked 🔓✅\n \nID: <code>{ub_user_id}</code>\nUnblocked Date: {datetime.fromtimestamp(dt)}")

        else:
            send_to_user(message, f"<code>{ub_user_id}</code> is already unblocked ✅😐")
    else:
        send_to_all(message, "🚫 Sorry! You are not an admin")


# Check Runtime

def check_runtime(message):
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        now = TimeFormatter(now)
        send_to_user(message, f"⏳ <i>Bot running time -</i> <b>{now}</b>")
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
        send_to_user(message, "❌ Please provide a URL to clear cache for.\nUsage: <code>/uncache &lt;URL&gt;</code>")
        return
    url = text.split(maxsplit=1)[1].strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        send_to_user(message, "❌ Please provide a valid URL.\nUsage: <code>/uncache &lt;URL&gt;</code>")
        return
    removed_any = False
    try:
        # Clearing the cache by video
        normalized_url = normalize_url_for_cache(url)
        url_hash = get_url_hash(normalized_url)
        video_cache_path = f"{Config.VIDEO_CACHE_DB_PATH}/{url_hash}"
        db_child_by_path(db, video_cache_path).remove()
        removed_any = True
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
            send_to_user(message, f"✅ Cache cleared successfully for URL:\n<code>{url}</code>")
            send_to_logger(message, f"Admin {user_id} cleared cache for URL: {url}")
        else:
            send_to_user(message, "ℹ️ No cache found for this link.")
    except Exception as e:
        send_to_all(message, f"❌ Error clearing cache: {e}")

