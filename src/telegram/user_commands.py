from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.process import Process
from language.languages import Languages as Lang
from language.language_handler import LanguageHandler
from config.config import Config
from telegram.keyboards import TelegramKeyboards
from tasks.url_handler import URLHandler
class TelegramUserCommands:
    """A class to handle only user commands in the Telegram bot."""
    def __init__(self, app: Client):
        self.app = app
        self.process = Process(app)
        self.keyboards = TelegramKeyboards()
        self.url_handler = URLHandler(app)

    async def check_commands(self, message: Message):
        lang = LanguageHandler().check_language(message)
        user_id = message.from_user.id


        # Start command
        if message.text.startswith(Config.START_COMMAND):
            await self.app.send_message(user_id, Lang.WELCOME_MESSAGE[lang].replace("{user}", message.from_user.first_name))

        # Help command
        elif message.text.startswith(Config.HELP_COMMAND):
            await self.app.send_message(user_id, Lang.HELP_MESSAGE[lang])
        
        # Language command
        elif message.text.startswith(Config.LANGUAGE_COMMAND):
            await self.app.send_message(user_id, Lang.LANGUAGE_MESSAGE[lang], reply_markup=self.keyboards.language_selection_keyboard())

        # Process URLs
        elif message.text.startswith("https://") or message.text.startswith("http://"):
            await self.url_handler.process_url(message, lang)