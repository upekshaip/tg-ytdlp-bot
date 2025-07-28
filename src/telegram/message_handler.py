from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from telegram.commands import TelegramCommands

class MessageHandler:
    def __init__(self, app: Client):
        self.app = app
        self.commands = TelegramCommands(app)
    
    
    async def register_handlers(self):
        # Commands
        @self.app.on_message(filters.command(prefixes=["/"]) & filters.private)
        async def handle_commands(app: Client, message: Message):
            self.commands.check_commands(message)

        
        # Callback Query
        @self.app.on_callback_query()
        async def handle_callback(client: Client, query: CallbackQuery):
            pass  # Add logic


        # Text Parser
        @self.app.on_message(filters.text & filters.private)
        async def handle_text(app: Client, message: Message):
            self.app.send_message(message.chat.id, "Sorry, I don't understand that.")
    