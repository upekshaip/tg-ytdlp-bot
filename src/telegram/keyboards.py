from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class TelegramKeyboards:
    """
    Only defines Telegram keyboards for the bot.
    """
    
    def __init__(self):
        pass


    def main_menu_keyboard(self):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
            [InlineKeyboardButton("🌐 Language", callback_data="language")]
        ])
        return keyboard
    
    def language_selection_keyboard(self):
        keybord = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇺🇸 English", callback_data=f"lang_en")], 
            [InlineKeyboardButton("🇪🇸 Spanish", callback_data=f"lang_es")], 
            [InlineKeyboardButton("🇧🇷 Portuguese", callback_data=f"lang_pt-br")], 
            [InlineKeyboardButton("🇩🇪 German", callback_data=f"lang_de")], 
            [InlineKeyboardButton("🇷🇺 Russian", callback_data=f"lang_ru")], 
            [InlineKeyboardButton("🇺🇦 Ukrainian", callback_data=f"lang_uk")], 
            [InlineKeyboardButton("🌐 Auto Detect", callback_data=f"lang_auto")]
        ])
        return keybord
    
    def video_format_keyboard(self, formats, url_id):
        buttons = []
        for fmt in formats:
            format_id = fmt.get("format_id", "unknown")
            ext = fmt.get("ext", "unknown")
            height = fmt.get("height", "unknown")
            width = fmt.get("width", "unknown")
            fps = fmt.get("fps", "unknown")
            filesize = fmt.get("filesize", "unknown")
            format_note = fmt.get("format_note", "")

            button_text = f"{height}p {fps}fps"
            buttons.append(InlineKeyboardButton(button_text, callback_data=f"vid_{url_id}_{format_id}"))

        # Group buttons into rows of 3
        keyboard_rows = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
        keyboard = InlineKeyboardMarkup(keyboard_rows)
        return keyboard