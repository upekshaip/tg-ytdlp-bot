from pyrogram.types import Message, CallbackQuery
from language.languages import Languages as Lang

class LanguageHandler:
    """
    Handles the main process of the bot, including startup tasks.
    """
    
    def __init__(self):
        pass

    def check_language(self, message: Message):
        """
        Check the language of the user and return the appropriate language code.
        """
        lang = message.from_user.language_code
        if lang not in Lang.LANGUAGES:
            lang = "en"
        return lang
    
    def check_language(self, query: CallbackQuery):
        """
        Check the language of the user and return the appropriate language code.
        """
        lang = query.from_user.language_code
        if lang not in Lang.LANGUAGES:
            lang = "en"
        return lang