from config._config import Config
from pyrogram import Client, filters, enums
import asyncio
from helpers.process import Process
from languages.languages import Languages as Lang
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

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


# BOT inside callbacks
@app.on_callback_query()
async def handle_callback(app:Client, query: CallbackQuery):
    # handle callback queries here with the process object
    pass
    
    
# register command (start)
@app.on_message(filters.command(["start"]) & filters.private)
async def start_command(app, message: Message):
    # send welcome message
    pass


# Language functionslity
@app.on_message(filters.command(["language"]) & filters.private)
async def language_command(app: Client, message: Message):
    # send_language_selector
    pass


# help command
@app.on_message(filters.command(["help"]) & filters.private)
async def help_command(app:Client, message:Message):
    # we can get language from the message or db (default to English)
    lang = process.process_language(message.chat.id, message.from_user.language_code)
    await app.send_message(message.chat.id, Lang.HELP_MESSAGE[lang], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(Lang.SUPPORT_BUTTON[lang], url="https://t.me/glambusupport")]]))


# Menu command
@app.on_message(filters.command(["menu"]) & filters.private)
async def menu_command(app:Client, message:Message):
    await process.send_menu(message)



# Handle urls
@app.on_message(filters.text & filters.private)
async def cmd_parser(app: Client, message: Message):
    # normal message parser
    pass




if __name__ == "__main__":
    print("Program Starts Running...")
    # run the api web server (async)
    app.run(main())
    # run the bot (async)
    app.run()
