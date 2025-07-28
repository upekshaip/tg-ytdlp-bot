from config.config import Config
from pyrogram import Client, filters, enums
import asyncio
from language.languages import Languages as Lang
# from pyrogram.types import Message, CallbackQuery
# from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.message_handler import MessageHandler

app = Client(
    Config.BOT_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


handler = MessageHandler(app)
handler.register_handlers()



if __name__ == "__main__":
    print("Program Starts Running...")
    app.run()
