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