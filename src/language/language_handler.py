from pyrogram.types import Message, CallbackQuery
from language.languages import Languages as Lang
from db.firebase import Firebase as FDB

class LanguageHandler:
    """
    Handles the main process of the bot, including startup tasks.
    """
    
    def __init__(self):
        self.db = FDB()
        pass

    def check_language(self, obj: Message | CallbackQuery):
        """
        Check the language of the user and return the appropriate language code.
        """
        lang = "en"  # Default language
        lang = obj.from_user.language_code
        selected_language = self.db.get_selected_language(obj.from_user.id)

        if selected_language:
            lang = selected_language
        if lang not in Lang.LANGUAGES:
            lang = "en"
        return lang
    
    
    async def update_language(self, user_id, selected_language, query: CallbackQuery):
        if selected_language == "auto":
            self.db.delete_selected_language(user_id)
            lang = self.check_language(query)
            await query.edit_message_text(f"{Lang.LANGUAGE_SELECTED_MESSAGE[lang]} **{lang}**")
        else:
            self.db.update_selected_language(user_id, selected_language)
            await query.edit_message_text(f"{Lang.LANGUAGE_SELECTED_MESSAGE[selected_language]} **{selected_language}**")
        