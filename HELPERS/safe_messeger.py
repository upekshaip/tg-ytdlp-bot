# #############################################################################################################################
import re
import time
import logging
from types import SimpleNamespace
from HELPERS.app_instance import get_app

# Configure local logger
logger = logging.getLogger(__name__)

# Get app instance dynamically to avoid None issues
def get_app_safe():
    app = get_app()
    if app is None:
        raise RuntimeError("App instance not available yet")
    return app

def fake_message(text, user_id, command=None):
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
    if command is not None:
        m.command = command
    return m

# Helper function for safe message sending with flood wait handling
def safe_send_message(chat_id, text, **kwargs):
    # Add reply_to_message_id if message is passed
    if 'reply_to_message_id' not in kwargs and 'message' in kwargs:
        kwargs['reply_to_message_id'] = kwargs['message'].id
        del kwargs['message']
    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.send_message(chat_id, text, **kwargs)
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

    for attempt in range(max_retries):
        try:
            app = get_app_safe()
            return app.edit_message_text(chat_id, message_id, text, **kwargs)
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
                    time.sleep(min(wait_seconds + 1, 30))  # Wait the required time (max 30 sec)
                else:
                    logger.warning(f"Flood wait detected but couldn't extract time, sleeping for {retry_delay} seconds")
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

            logger.error(f"Failed to delete messages after {max_retries} attempts: {e}")
            return None