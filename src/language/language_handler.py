from pyrogram.types import Message, CallbackQuery
from language.languages import Languages as Lang

class LanguageHandler:
    """
    Handles the main process of the bot, including startup tasks.
    """
    
    def __init__(self):
        pass

    def check_language(self, obj: Message | CallbackQuery):
        """
        Check the language of the user and return the appropriate language code.
        """
        lang = "en"  # Default language
        lang = obj.from_user.language_code
        if lang not in Lang.LANGUAGES:
            lang = "en"
        return lang