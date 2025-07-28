from pyrogram.types import Message, CallbackQuery
from language.languages import Languages as Lang

class Process:
    """
    Handles the main process of the bot, including startup tasks.
    """
    
    def __init__(self, app):
        self.app = app