from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from telegram.user_commands import TelegramUserCommands
from telegram.admin_commands import TelegramAdminCommands
from telegram.callbacks import TelegramCallbacks
from config.config import Config

class MessageHandler:
    def __init__(self, app: Client):
        self.app = app
        self.user_commands = TelegramUserCommands(app)
        self.admin_commands = TelegramAdminCommands(app)
        self.callbacks = TelegramCallbacks(app)
    
    
    def register_handlers(self):
        # Admin Commands
        @self.app.on_message(filters.text & filters.private & filters.user(Config.ADMIN))
        async def handle_admin_commands(app: Client, message: Message):
            print(f"Admin command received: {message.text}")
            # admin commands
            if (message.text.startswith(tuple(Config.ADMIN_COMMANDS))):
                await self.admin_commands.check_commands(message)
            # user commands - admins can also use user commands
            else:
                await self.user_commands.check_commands(message)
            
        
        # User Commands
        @self.app.on_message(filters.text & filters.private)
        async def handle_user_commands(app: Client, message: Message):        
            print(f"User command received: {message.text}")
            await self.user_commands.check_commands(message)

        
        # Callback Query (admins and users)
        @self.app.on_callback_query()
        async def handle_callback(client: Client, query: CallbackQuery):
            await self.callbacks.check_callbacks(query)