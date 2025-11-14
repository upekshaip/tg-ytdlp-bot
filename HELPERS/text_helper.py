"""
Text helper functions for formatting and limiting text length
"""

def truncate_text_with_html(text, max_length=4000, ellipsis="..."):
    """
    Truncate text to fit within Telegram's message limit while preserving HTML structure.
    
    Args:
        text (str): The text to truncate
        max_length (int): Maximum allowed length (default: 4000)
        ellipsis (str): Text to append when truncating (default: "...")
    
    Returns:
        str: Truncated text that fits within the limit
    """
    if len(text) <= max_length:
        return text
    
    # Reserve space for ellipsis
    available_length = max_length - len(ellipsis)
    
    # Find the last complete line before the limit
    truncated = text[:available_length]
    last_newline = truncated.rfind('\n')
    
    if last_newline and last_newline > 0:
        truncated = truncated[:last_newline]
    
    return truncated + ellipsis


def format_clean_output_as_html(items_list, user_id=None, max_length=4000):
    """
    Format the clean command output as a collapsible HTML quote.
    
    Args:
        items_list (str): The list of removed items
        user_id (int): User ID for language selection
        max_length (int): Maximum allowed length (default: 4000)
    
    Returns:
        str: HTML-formatted collapsible quote
    """
    # Base message structure
    from CONFIG.messages import safe_get_messages
    messages = safe_get_messages(user_id)
    base_message = messages.URL_EXTRACTOR_ALL_FILES_REMOVED_MSG.split('\n')[0]
    
    # Extract the "Removed files:" part from the translated message
    full_message = messages.URL_EXTRACTOR_ALL_FILES_REMOVED_MSG
    removed_files_text = full_message.split('\n')[2] if len(full_message.split('\n')) > 2 else "Removed files:"
    
    # Calculate available space for items list
    html_overhead = len(f'<b>{removed_files_text}</b>\n<pre>\n</pre>')
    available_space = max_length - len(base_message) - html_overhead
    
    # Truncate items list if needed
    if len(items_list) > available_space:
        items_list = truncate_text_with_html(items_list, available_space, "\n...")
    
    # Format as simple HTML with basic tags
    html_output = f"""<b>{removed_files_text}</b>
<pre>{items_list}</pre>"""
    
    return f"{base_message}\n\n{html_output}"
