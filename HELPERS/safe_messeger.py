# #############################################################################################################################
import re
import time
import logging
import threading
import asyncio
from types import SimpleNamespace
from HELPERS.app_instance import get_app
from CONFIG.messages import Messages, safe_get_messages
from pyrogram.errors import FloodWait
import os
from pyrogram.types import ReplyParameters
from pyrogram import enums

# Configure local logger
logger = logging.getLogger(__name__)

# Global message sending throttle to prevent msg_seqno issues
_last_message_sent = {}
_message_send_lock = threading.Lock()

# Get app instance dynamically to avoid None issues
def get_app_safe():
    messages = safe_get_messages(None)
    app = get_app()
    if app is None:
        raise RuntimeError(safe_get_messages(user_id).HELPER_APP_INSTANCE_NOT_AVAILABLE_MSG)
    return app

def fake_message(text, user_id, command=None, original_chat_id=None, message_thread_id=None, original_message=None):
    messages = safe_get_messages(user_id)
    m = SimpleNamespace()
    m.chat = SimpleNamespace()
    # Use original_chat_id if provided, otherwise use user_id
    # Ensure we have a valid chat_id (fallback to -1 if both are None)
    chat_id = original_chat_id if original_chat_id is not None else user_id
    if chat_id is None:
        chat_id = -1  # Fallback for gallery-dl operations
    m.chat.id = chat_id
    m.chat.first_name = safe_get_messages(user_id).HELPER_USER_NAME_MSG
    # Set chat type based on chat_id (negative = group, positive = private)
    m.chat.type = enums.ChatType.PRIVATE if (original_chat_id if original_chat_id is not None else user_id) > 0 else enums.ChatType.SUPERGROUP
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
    # ЖЕСТКО: Сохраняем message_thread_id для правильной работы с топиками в группах
    m.message_thread_id = message_thread_id
    # ЖЕСТКО: Сохраняем оригинальное сообщение для реплаев
    m._original_message = original_message
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

def fake_message_with_context(text, user_id, context_message=None, command=None):
    """
    Создает fake_message с автоматическим извлечением message_thread_id из контекста.
    
    Args:
        text: Текст сообщения
        user_id: ID пользователя
        context_message: Сообщение для извлечения контекста (message_thread_id, chat_id)
        command: Команда (опционально)
    
    Returns:
        fake_message с правильным message_thread_id
    """
    if context_message:
        original_chat_id = getattr(context_message, 'chat', {}).id if hasattr(context_message, 'chat') else user_id
        message_thread_id = getattr(context_message, 'message_thread_id', None)
        return fake_message(text, user_id, command=command, original_chat_id=original_chat_id, 
                          message_thread_id=message_thread_id, original_message=context_message)
    else:
        return fake_message(text, user_id, command=command)

# Helper function for safe message sending with flood wait handling
def safe_send_message(chat_id, text, **kwargs):
    messages = safe_get_messages(None)
    # Normalize reply parameters and preserve topic/thread info
    original_message = kwargs.get('message')
    # Peek callback_query (will be popped later) to inherit thread context in topics
    cb_peek = kwargs.get('_callback_query', None)
    
    # DEBUG: Log all parameters
    logger.info(f"[SAFE_SEND_DEBUG] chat_id={chat_id}, text_length={len(text) if text else 0}")
    logger.info(f"[SAFE_SEND_DEBUG] original_message={original_message}")
    logger.info(f"[SAFE_SEND_DEBUG] original_message.message_thread_id={getattr(original_message, 'message_thread_id', None) if original_message else None}")
    logger.info(f"[SAFE_SEND_DEBUG] cb_peek={cb_peek}")
    logger.info(f"[SAFE_SEND_DEBUG] kwargs keys: {list(kwargs.keys())}")
    if 'reply_parameters' not in kwargs:
        if 'reply_to_message_id' in kwargs and kwargs['reply_to_message_id'] is not None:
            kwargs['reply_parameters'] = ReplyParameters(message_id=kwargs['reply_to_message_id'])
            del kwargs['reply_to_message_id']
        elif original_message is not None and getattr(original_message, 'id', None) is not None:
            # Check if this is a fake message with original message reference
            if hasattr(original_message, '_is_fake_message') and hasattr(original_message, '_original_message'):
                if original_message._original_message is not None and getattr(original_message._original_message, 'id', None) is not None:
                    logger.info(f"[SAFE_SEND] Using original message for reply: {original_message._original_message.id}")
                    kwargs['reply_parameters'] = ReplyParameters(message_id=original_message._original_message.id)
                else:
                    logger.info(f"[SAFE_SEND] Fake message but no original message available, using fake message id: {original_message.id}")
                    kwargs['reply_parameters'] = ReplyParameters(message_id=original_message.id)
            else:
                kwargs['reply_parameters'] = ReplyParameters(message_id=original_message.id)
        elif cb_peek is not None and getattr(getattr(cb_peek, 'message', None), 'id', None) is not None:
            kwargs['reply_parameters'] = ReplyParameters(message_id=cb_peek.message.id)
    # Ensure topic/thread routing for supergroups with topics (only for groups, not private chats)
    try:
        # Only apply topic routing for groups (negative chat_id)
        if chat_id and chat_id < 0:
            # Check if message is provided in kwargs (for fake messages)
            if original_message is not None:
                # For fake messages, use the original message's thread_id
                if hasattr(original_message, '_is_fake_message') and hasattr(original_message, '_original_message') and original_message._original_message is not None:
                    message_thread_id = getattr(original_message._original_message, 'message_thread_id', None)
                    logger.info(f"[SAFE_SEND] fake_message._original_message.message_thread_id={message_thread_id}, chat_id={chat_id}")
                else:
                    message_thread_id = getattr(original_message, 'message_thread_id', None)
                    logger.info(f"[SAFE_SEND] original_message.message_thread_id={message_thread_id}, chat_id={chat_id}")
                
                if message_thread_id:
                    kwargs.setdefault('message_thread_id', message_thread_id)
                    logger.info(f"[SAFE_SEND] Set message_thread_id={message_thread_id} for chat_id={chat_id}")
            # Inherit thread_id from callback context when message is not provided
            elif cb_peek is not None and getattr(getattr(cb_peek, 'message', None), 'message_thread_id', None):
                kwargs.setdefault('message_thread_id', cb_peek.message.message_thread_id)
        else:
            logger.info(f"[SAFE_SEND] Skipping topic routing for private chat_id={chat_id}")
    except Exception as e:
        logger.warning(f"[SAFE_SEND] Error in topic routing: {e}")
        pass
    # Remove helper-only key
    if 'message' in kwargs:
        del kwargs['message']
    
    # DEBUG: Log final parameters before sending
    logger.info(f"[SAFE_SEND_FINAL] chat_id={chat_id}, message_thread_id={kwargs.get('message_thread_id', 'NOT_SET')}")
    logger.info(f"[SAFE_SEND_FINAL] Final kwargs: {kwargs}")
    
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
        # Increase minimum spacing to reduce RANDOM_ID_DUPLICATE in high-throughput chats
        min_spacing = 0.25  # seconds
        if now - last_sent < min_spacing:
            time.sleep(min_spacing - (now - last_sent))
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
                        cb.answer(notice or safe_get_messages(user_id).HELPER_FLOOD_LIMIT_TRY_LATER_MSG, show_alert=False)
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
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG.format(wait_seconds=wait_seconds))
                    time.sleep(min(wait_seconds + 1, 5))  # short backoff
                else:
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG.format(retry_delay=retry_delay))
                    time.sleep(retry_delay)
                if attempt and attempt < max_retries - 1:
                    continue
            
            # Handle msg_seqno errors
            elif "msg_seqno is too high" in str(e):
                logger.warning(safe_get_messages(user_id).HELPER_MSG_SEQNO_ERROR_DETECTED_MSG.format(retry_delay=retry_delay))
                time.sleep(retry_delay)
                if attempt and attempt < max_retries - 1:
                    continue
            # Handle RANDOM_ID_DUPLICATE errors by brief backoff and retry
            elif "RANDOM_ID_DUPLICATE" in str(e):
                try:
                    logger.warning("RANDOM_ID_DUPLICATE detected, backing off briefly and retrying")
                except Exception:
                    pass
                time.sleep(0.5)
                if attempt and attempt < max_retries - 1:
                    continue
            logger.error(f"Failed to send message after {max_retries} attempts: {e}")
            return None

# Helper function for safe message forwarding with flood wait handling
def safe_forward_messages(chat_id, from_chat_id, message_ids, **kwargs):
    messages = safe_get_messages(None)
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
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG.format(wait_seconds=wait_seconds))
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG.format(retry_delay=retry_delay))
                    time.sleep(retry_delay)

                if attempt and attempt < max_retries - 1:
                    continue

            logger.error(f"Failed to forward messages after {max_retries} attempts: {e}")
            return None

# Helper function for safely editing message text with flood wait handling
def safe_edit_message_text(chat_id, message_id, text, **kwargs):
    messages = safe_get_messages(None)
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
        if elapsed and elapsed < 5.0:
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
            if safe_get_messages().HELPER_MESSAGE_ID_INVALID_MSG in str(e):
                # We only log this once, not for every retry
                if attempt == 0:
                    logger.debug(f"Tried to edit message that was already deleted: {message_id}")
                return None

# Helper function for safely clearing reply markup (inline keyboard)
def safe_edit_reply_markup(chat_id, message_id, reply_markup=None, **kwargs):
    messages = safe_get_messages(None)
    """
    Safely edit message reply markup (e.g., clear inline keyboard) with flood wait handling

    Inherits message_thread_id from provided message or _callback_query for topics.
    """
    max_retries = 3
    retry_delay = 5

    # Inherit thread context from helpers
    original_message = kwargs.get('message')
    cb_peek = kwargs.get('_callback_query', None)
    try:
        if 'message_thread_id' not in kwargs:
            if original_message is not None and getattr(original_message, 'message_thread_id', None):
                kwargs['message_thread_id'] = original_message.message_thread_id
            elif cb_peek is not None and getattr(getattr(cb_peek, 'message', None), 'message_thread_id', None):
                kwargs['message_thread_id'] = cb_peek.message.message_thread_id
    except Exception:
        pass
    if 'message' in kwargs:
        del kwargs['message']
    if '_callback_query' in kwargs:
        kwargs.pop('_callback_query', None)

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.edit_message_reply_markup(chat_id, message_id, reply_markup=reply_markup, **kwargs)
        except FloodWait as e:
            try:
                user_dir = os.path.join("users", str(chat_id))
                os.makedirs(user_dir, exist_ok=True)
                with open(os.path.join(user_dir, "flood_wait.txt"), 'w') as f:
                    f.write(str(e.value))
            except Exception:
                pass
            logger.warning(f"Flood wait detected ({e.value}s) while editing reply markup for {chat_id}")
            return None
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG.format(wait_seconds=wait_seconds))
                    time.sleep(min(wait_seconds + 1, 5))
                else:
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG.format(retry_delay=retry_delay))
                    time.sleep(retry_delay)
                if attempt and attempt < max_retries - 1:
                    continue
            elif "msg_seqno is too high" in str(e):
                logger.warning(safe_get_messages(user_id).HELPER_MSG_SEQNO_ERROR_DETECTED_MSG.format(retry_delay=retry_delay))
                time.sleep(retry_delay)
                if attempt and attempt < max_retries - 1:
                    continue
            if attempt == max_retries - 1:
                logger.error(f"Failed to edit reply markup after {max_retries} attempts: {e}")
            return None

# Helper function for safely deleting messages with flood wait handling
def safe_delete_messages(chat_id, message_ids, **kwargs):
    messages = safe_get_messages(None)
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
            if safe_get_messages(user_id).HELPER_MESSAGE_ID_INVALID_MSG in msg or safe_get_messages(user_id).HELPER_MESSAGE_DELETE_FORBIDDEN_MSG in msg:
                if attempt == 0:
                    logger.debug(f"Tried to delete non-existent message(s): {message_ids}")
                return None
            if "FLOOD_WAIT" in str(e):
                # Extract wait time
                wait_match = re.search(r'A wait of (\d+) seconds is required', str(e))
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG.format(wait_seconds=wait_seconds))
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(safe_get_messages(user_id).HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG.format(retry_delay=retry_delay))
                    time.sleep(retry_delay)

                if attempt and attempt < max_retries - 1:
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

def schedule_delete_processing_messages(chat_id, delete_after_seconds=5):
    messages = safe_get_messages(None)
    """
    Schedule deletion of all "Processing..." messages for a user after a delay.
    This helps clean up duplicate processing messages.

    Args:
        chat_id: The chat ID
        delete_after_seconds: Seconds to wait before deleting
    Returns:
        True if scheduled, False otherwise
    """
    try:
        if not chat_id:
            return False

        def _del_processing_messages():
            try:
                logger.info(f"[AUTO-DELETE] Scheduling deletion of all processing messages for user {chat_id} in {delete_after_seconds} seconds")
                time.sleep(delete_after_seconds)
                
                # Get app instance
                app = get_app_safe()
                if not app:
                    logger.error("[AUTO-DELETE] Cannot get app instance for deleting processing messages")
                    return
                
                # Bots cannot use get_chat_history, so we'll skip this functionality
                # Instead, we'll rely on the individual message deletion that's already scheduled
                logger.info(f"[AUTO-DELETE] Skipping chat history scan for user {chat_id} (bots cannot use get_chat_history)")
                logger.info(f"[AUTO-DELETE] Individual processing messages will be deleted by their own timers")
                    
            except Exception as e:
                logger.error(f"[AUTO-DELETE] Error while deleting processing messages for user {chat_id}: {e}")

        t = threading.Thread(target=_del_processing_messages, daemon=True)
        t.start()
        return True
    except Exception:
        return False
