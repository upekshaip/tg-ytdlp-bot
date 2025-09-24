# #############################################################################################################################
import re
import time
import logging
import threading
import asyncio
from types import SimpleNamespace
from HELPERS.app_instance import get_app
from pyrogram.errors import FloodWait
import os
from pyrogram.types import ReplyParameters

# Configure local logger
logger = logging.getLogger(__name__)

# Global message sending throttle to prevent msg_seqno issues
_last_message_sent = {}
_message_send_lock = threading.Lock()

# Get app instance dynamically to avoid None issues
def get_app_safe():
    app = get_app()
    if app is None:
        raise RuntimeError("App instance not available yet")
    return app

def fake_message(text, user_id, command=None, original_chat_id=None):
    m = SimpleNamespace()
    m.chat = SimpleNamespace()
    m.chat.id = user_id
    m.chat.first_name = "User"
    m.text = text
    m.first_name = m.chat.first_name
    m.reply_to_message = None
    m.id = 0
    m.from_user = SimpleNamespace()
    m.from_user.id = user_id
    m.from_user.first_name = m.chat.first_name
    # ЖЕСТКО: Помечаем как fake message для правильной обработки платных медиа
    m._is_fake_message = True
    # ЖЕСТКО: Сохраняем оригинальный chat_id для правильного определения is_private_chat
    m._original_chat_id = original_chat_id if original_chat_id is not None else user_id
    if command is not None:
        m.command = command
    else:
        # Emulate pyrogram's Message.command behavior when text starts with '/'
        try:
            if isinstance(text, str) and text.startswith('/'):
                parts = text.strip().split()
                if parts:
                    cmd = parts[0][1:] if len(parts[0]) > 1 else ''
                    args = parts[1:]
                    m.command = [cmd] + args
        except Exception:
            pass
    return m

# Helper function for safe message sending with flood wait handling
def safe_send_message(chat_id, text, **kwargs):
    # Normalize reply parameters and preserve topic/thread info
    original_message = kwargs.get('message')
    if 'reply_parameters' not in kwargs:
        if 'reply_to_message_id' in kwargs and kwargs['reply_to_message_id'] is not None:
            kwargs['reply_parameters'] = ReplyParameters(message_id=kwargs['reply_to_message_id'])
            del kwargs['reply_to_message_id']
        elif original_message is not None and getattr(original_message, 'id', None) is not None:
            kwargs['reply_parameters'] = ReplyParameters(message_id=original_message.id)
    # Ensure topic/thread routing for supergroups with topics
    try:
        if original_message is not None and getattr(original_message, 'message_thread_id', None):
            kwargs.setdefault('message_thread_id', original_message.message_thread_id)
    except Exception:
        pass
    # Remove helper-only key
    if 'message' in kwargs:
        del kwargs['message']
    max_retries = 3
    retry_delay = 5
    # Extract internal helper kwargs (not supported by pyrogram)
    cb = kwargs.pop('_callback_query', None)
    notice = kwargs.pop('_fallback_notice', None)
    # Drop any other underscored keys just in case
    for k in list(kwargs.keys()):
        if isinstance(k, str) and k.startswith('_'):
            kwargs.pop(k, None)

    # Throttle message sending to prevent msg_seqno issues
    with _message_send_lock:
        last_sent = _last_message_sent.get(chat_id, 0)
        now = time.time()
        if now - last_sent < 0.1:  # 100ms minimum delay between messages
            time.sleep(0.1 - (now - last_sent))
        _last_message_sent[chat_id] = time.time()

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.send_message(chat_id, text, **kwargs)
        except FloodWait as e:
            # Write FloodWait seconds to per-user file and do not spin retries for huge waits
            try:
                user_dir = os.path.join("users", str(chat_id))
                os.makedirs(user_dir, exist_ok=True)
                with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                    f.write(str(e.value))
            except Exception:
                pass
            logger.warning(f"Flood wait detected ({e.value}s) while sending message to {chat_id}")
            # Try to fall back to answering the callback (if provided) to give user feedback
            try:
                if cb is not None:
                    try:
                        cb.answer(notice or "⏳ Flood limit. Try later.", show_alert=False)
                    except Exception:
                        pass
            except Exception:
                pass
            return None
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 5))  # short backoff
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)
                if attempt < max_retries - 1:
                    continue
            
            # Handle msg_seqno errors
            elif "msg_seqno is too high" in str(e):
                logger.warning(f"msg_seqno error detected, sleeping for {retry_delay} seconds")
                time.sleep(retry_delay)
                if attempt < max_retries - 1:
                    continue
            logger.error(f"Failed to send message after {max_retries} attempts: {e}")
            return None

# Helper function for safe message forwarding with flood wait handling
def safe_forward_messages(chat_id, from_chat_id, message_ids, **kwargs):
    """
    Safely forward messages with flood wait handling

    Args:
        chat_id: The chat ID to forward to
        from_chat_id: The chat ID to forward from
        message_ids: The message IDs to forward
        **kwargs: Additional arguments for forward_messages

    Returns:
        The message objects or None if forwarding failed
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.forward_messages(chat_id, from_chat_id, message_ids, **kwargs)
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue

            logger.error(f"Failed to forward messages after {max_retries} attempts: {e}")
            return None

# Helper function for safely editing message text with flood wait handling
def safe_edit_message_text(chat_id, message_id, text, **kwargs):
    """
    Safely edit message text with flood wait handling

    Args:
        chat_id: The chat ID
        message_id: The message ID to edit
        text: The new text
        **kwargs: Additional arguments for edit_message_text

    Returns:
        The message object or None if editing failed
    """
    max_retries = 3
    retry_delay = 5

    # Throttle edits in groups to no more than once per 5 seconds per chat
    try:
        is_group = isinstance(chat_id, int) and chat_id < 0
    except Exception:
        is_group = False

    # Module-level storage for last edit timestamps
    global _last_edit_ts_per_chat
    try:
        _last_edit_ts_per_chat
    except NameError:
        _last_edit_ts_per_chat = {}

    if is_group:
        last_ts = _last_edit_ts_per_chat.get(chat_id, 0.0)
        now = time.time()
        elapsed = now - last_ts
        if elapsed < 5.0:
            try:
                time.sleep(5.0 - elapsed)
            except Exception:
                pass
        _last_edit_ts_per_chat[chat_id] = time.time()

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.edit_message_text(chat_id, message_id, text, **kwargs)
        except FloodWait as e:
            # Persist FloodWait info and stop
            try:
                user_dir = os.path.join("users", str(chat_id))
                os.makedirs(user_dir, exist_ok=True)
                with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                    f.write(str(e.value))
            except Exception:
                pass
            logger.warning(f"Flood wait detected ({e.value}s) while editing message for {chat_id}")
            return None
        except Exception as e:
            # If message ID is invalid, it means the message was deleted
            # No need to retry, just return immediately
            if "MESSAGE_ID_INVALID" in str(e):
                # We only log this once, not for every retry
                if attempt == 0:
                    logger.debug(f"Tried to edit message that was already deleted: {message_id}")
                return None

            # If message was not modified, also return immediately (not an error)
            elif "message is not modified" in str(e).lower() or "MESSAGE_NOT_MODIFIED" in str(e):
                return None

            # Handle flood wait errors
            elif "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 5))
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue
            
            # Handle msg_seqno errors
            elif "msg_seqno is too high" in str(e):
                logger.warning(f"msg_seqno error detected, sleeping for {retry_delay} seconds")
                time.sleep(retry_delay)
                if attempt < max_retries - 1:
                    continue

            # Only log other errors as real errors
            if attempt == max_retries - 1:  # Log only on last attempt
                logger.error(f"Failed to edit message after {max_retries} attempts: {e}")
            return None

# Helper function for safely deleting messages with flood wait handling
def safe_delete_messages(chat_id, message_ids, **kwargs):
    """
    Safely delete messages with flood wait handling

    Args:
        chat_id: The chat ID
        message_ids: List of message IDs to delete
        **kwargs: Additional arguments for delete_messages

    Returns:
        True on success or None if deletion failed
    """
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.delete_messages(chat_id=chat_id, message_ids=message_ids, **kwargs)
        except Exception as e:
            # Если сообщение уже удалено/невалидно — не считаем это ошибкой
            try:
                msg = str(e)
            except Exception:
                msg = f"{type(e).__name__}"
            if "MESSAGE_ID_INVALID" in msg or "MESSAGE_DELETE_FORBIDDEN" in msg:
                if attempt == 0:
                    logger.debug(f"Tried to delete non-existent message(s): {message_ids}")
                return None
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(f"Flood wait detected, sleeping for {wait_seconds} seconds")
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)

                if attempt < max_retries - 1:
                    continue

            # Избегаем внутренних атрибутов исключения (например, pts_count)
            logger.error(f"Failed to delete messages after {max_retries} attempts: {type(e).__name__}")
            return None

# Helper function for sending messages with auto-delete functionality
def safe_send_message_with_auto_delete(chat_id, text, delete_after_seconds=60, **kwargs):
    """
    Send a message and automatically delete it after specified seconds
    
    Args:
        chat_id: The chat ID to send to
        text: The message text
        delete_after_seconds: Seconds after which to delete the message (default: 60)
        **kwargs: Additional arguments for send_message
    
    Returns:
        The message object or None if sending failed
    """
    # Send the message first
    message = safe_send_message(chat_id, text, **kwargs)
    
    if message and hasattr(message, 'id'):
        # Schedule deletion in a separate thread with better error handling
        def delete_message_after_delay():
            try:
                logger.info(f"[AUTO-DELETE] Scheduling message {message.id} for deletion in {delete_after_seconds} seconds")
                time.sleep(delete_after_seconds)
                logger.info(f"[AUTO-DELETE] Attempting to delete message {message.id}")
                result = safe_delete_messages(chat_id, [message.id])
                if result:
                    logger.info(f"[AUTO-DELETE] Successfully deleted message {message.id}")
                else:
                    logger.warning(f"[AUTO-DELETE] Failed to delete message {message.id}")
            except Exception as e:
                logger.error(f"[AUTO-DELETE] Error in auto-delete thread for message {message.id}: {e}")
        
        # Start the deletion thread
        delete_thread = threading.Thread(target=delete_message_after_delay, daemon=True)
        delete_thread.start()
        logger.info(f"[AUTO-DELETE] Started auto-delete thread for message {message.id} (thread: {delete_thread.name})")
    else:
        logger.warning(f"[AUTO-DELETE] Failed to send message or message has no ID: {message}")
    
    return message

def schedule_delete_message(chat_id, message_id, delete_after_seconds=60):
    """
    Schedule deletion of an already-sent message after a delay.

    Args:
        chat_id: The chat ID
        message_id: The message ID to delete
        delete_after_seconds: Seconds to wait before deleting
    Returns:
        True if scheduled, False otherwise
    """
    try:
        if not chat_id or not message_id:
            return False

        def _del():
            try:
                logger.info(f"[AUTO-DELETE] Scheduling message {message_id} for deletion in {delete_after_seconds} seconds")
                time.sleep(delete_after_seconds)
                safe_delete_messages(chat_id, [message_id])
            except Exception as e:
                logger.error(f"[AUTO-DELETE] Error while deleting message {message_id}: {e}")

        t = threading.Thread(target=_del, daemon=True)
        t.start()
        return True
    except Exception:
        return False
