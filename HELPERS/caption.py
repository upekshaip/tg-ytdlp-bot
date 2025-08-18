# Caption Editor for Videos
import re
from typing import Tuple
from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.logger import send_to_logger
from pyrogram import filters

# Get app instance for decorators
app = get_app()

# Called from url_distractor - no decorator needed
def caption_editor(app, message):
    # Проверяем, что сообщение является ответом на видео
    if not message.reply_to_message or not message.reply_to_message.video:
        return
    
    try:
        users_name = message.chat.first_name
        user_id = message.chat.id
        caption = message.text
        video_file_id = message.reply_to_message.video.file_id
        info_of_video = f"\n<b>Caption:</b> <code>{caption}</code>\n<b>User id:</b> <code>{user_id}</code>\n<b>User first name:</b> <code>{users_name}</code>\n<b>Video file id:</b> <code>{video_file_id}</code>"
        # Sending to logs
        send_to_logger(message, info_of_video)
        app.send_video(user_id, video_file_id, caption=caption)
        app.send_video(Config.LOGS_ID, video_file_id, caption=caption)
    except AttributeError as e:
        # Логируем ошибку, но не прерываем работу бота
        from HELPERS.logger import logger
        logger.error(f"Error in caption_editor: {e}")
        return
    except Exception as e:
        # Логируем любые другие ошибки
        from HELPERS.logger import logger
        logger.error(f"Unexpected error in caption_editor: {e}")
        return


def truncate_caption(
    title: str,
    description: str,
    url: str,
    tags_text: str = '',
    max_length: int = 1000  # Reduced from 1024 to be safe with encoding issues
) -> Tuple[str, str, str, str, str, bool]:
    """
    Returns: (title_html, pre_block, blockquote_content, tags_block, link_block, was_truncated)
    """
    title_html = f'<b>{title}</b>' if title else ''
    # Pattern for finding timestamps at the beginning of a line (00:00, 0:00:00, 0.00, etc.)
    timestamp_pattern = r'^\s*(\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}\.\d{2}(?:\.\d{2})?)\s+.*'

    lines = description.split('\n') if description else []
    pre_block_lines = []
    post_block_lines = []

    # Split lines into timestamps and main text
    for line in lines:
        if re.match(timestamp_pattern, line):
            pre_block_lines.append(line)
        else:
            post_block_lines.append(line)
    
    pre_block_str = '\n'.join(pre_block_lines)
    post_block_str = '\n'.join(post_block_lines).strip()

    tags_block = (tags_text.strip() + '\n') if tags_text and tags_text.strip() else ''
    # --- Add bot name next to the link ---
    bot_name = getattr(Config, 'BOT_NAME', None) or 'bot'
    bot_mention = f' @{bot_name}' if not bot_name.startswith('@') else f' {bot_name}'
    link_block = f'<a href="{url}">🔗 Video URL</a>{bot_mention}'
    
    was_truncated = False
    
    # Calculate constant overhead more accurately
    overhead = len(tags_block) + len(link_block)
    if title_html:
        overhead += len(title_html) + 2 # for '\n\n'
    if pre_block_str:
        overhead += len(pre_block_str) + 1 # for '\n'
    
    # Calculate limit for blockquote (taking into account <blockquote> tags)
    blockquote_overhead = len('<blockquote expandable></blockquote>') + 1 # for '\n'
    blockquote_limit = max_length - overhead - blockquote_overhead
    
    # Ensure we have some space for content
    if blockquote_limit <= 0:
        # If no space for blockquote, truncate everything except essential parts
        if title_html:
            title_html = title_html[:max_length-10] + '...'
        pre_block_str = ''
        blockquote_content = ''
        was_truncated = True
    else:
        blockquote_content = post_block_str
        if len(blockquote_content) > blockquote_limit:
            blockquote_content = blockquote_content[:blockquote_limit - 4] + '...'
            was_truncated = True

    # Final check and possible truncation of pre_block
    current_length = overhead + len(blockquote_content) + blockquote_overhead
    if current_length > max_length:
        # Calculate how much space we can give to pre_block
        pre_block_limit = max_length - (overhead - len(pre_block_str) - 1) - len(blockquote_content) - blockquote_overhead
        if pre_block_limit > 0 and pre_block_limit < len(pre_block_str):
            pre_block_str = pre_block_str[:pre_block_limit-4] + '...'
            was_truncated = True
        else: # if even with truncated pre_block it does not fit, truncate everything
             pre_block_str = ''

    if pre_block_str:
        pre_block_str += '\n'

    # Assembly caption
    cap = ''
    if title_html:
        cap += title_html + '\n\n'
    if pre_block_str:
        cap += pre_block_str + '\n'
    cap += f'<blockquote expandable>{blockquote_content}</blockquote>\n'
    if tags_block:
        cap += tags_block
    cap += link_block
    
    # Final safety check - ensure we never exceed max_length
    if len(cap) > max_length:
        # Emergency truncation - keep only essential parts
        essential_parts = []
        if title_html:
            essential_parts.append(title_html)
        if tags_block:
            essential_parts.append(tags_block.strip())
        if link_block:
            essential_parts.append(link_block)
        
        cap = '\n\n'.join(essential_parts)
        if len(cap) > max_length:
            # More aggressive truncation - remove HTML tags for calculation
            plain_text = re.sub(r'<[^>]+>', '', cap)
            if len(plain_text) > max_length:
                # Truncate plain text and rebuild HTML
                truncated_text = plain_text[:max_length-10] + '...'
                cap = truncated_text
            else:
                cap = cap[:max_length-3] + '...'
        was_truncated = True
    
    return title_html, pre_block_str, blockquote_content, tags_block, link_block, was_truncated
