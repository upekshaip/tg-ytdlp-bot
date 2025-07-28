from config.config import Config
from pyrogram import Client, filters, enums
import asyncio
from helpers.process import Process
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

process = Process(app)

async def startup_tasks():
    await asyncio.sleep(10)
    await app.send_message(int(Config.ADMIN[0]), "Bot Started!")
    print(f"Starting message sent!")


async def main():
    task_1 = asyncio.create_task(startup_tasks())


handler = MessageHandler(app)
handler.register_handlers()



if __name__ == "__main__":
    print("Program Starts Running...")
    # run the api web server (async)
    app.run(main())
    # run the bot (async)
    app.run()
