from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.process import Process
from language.languages import Languages as Lang
from language.language_handler import LanguageHandler
from config.config import Config


class TelegramCallbacks:
    def __init__(self, app: Client):
        self.app = app
        self.process = Process(app)

    async def check_callbacks(self, query: CallbackQuery):
        lang = LanguageHandler().check_language(query=query)
        user_id = query.from_user.id

        if query.data.startswith(Config.START_COMMAND):
            await self.app.send_message(user_id, Lang.WELCOME_MESSAGE[lang])

        elif query.data.startswith(Config.HELP_COMMAND):
            await self.app.send_message(user_id, Lang.WELCOME_MESSAGE[lang])