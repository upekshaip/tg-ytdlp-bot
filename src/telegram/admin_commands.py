from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.process import Process
from language.languages import Languages as Lang
from language.language_handler import LanguageHandler
from config.config import Config

class TelegramAdminCommands:
    """
    A class to handle only admin commands in the Telegram bot."""

    def __init__(self, app: Client):
        self.app = app
        self.process = Process(app)

    async def check_commands(self, message: Message):
        lang = LanguageHandler().check_language(message)
        user_id = message.from_user.id


        # Start command
        if message.text.startswith(Config.START_COMMAND):
            await self.app.send_message(user_id, "Welcome Master 🥷")

        elif message.text.startswith(Config.HELP_COMMAND):
            await self.app.send_message(user_id, f"ADMIN HELP\n \n{Lang.HELP_MESSAGE[lang]}")

        
        