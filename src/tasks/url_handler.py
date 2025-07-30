from pyrogram.types import Message, CallbackQuery
from pyrogram import Client, enums
from language.languages import Languages as Lang
from tasks.youtube import YouTubeTask
from telegram.keyboards import TelegramKeyboards
from telegram.message_formatter import TelegramMessageFormatter

class URLHandler:
    def __init__(self, app: Client):
        self.app = app
        self.yt = YouTubeTask()
        self.keyboards = TelegramKeyboards()

    async def process_url(self, message: Message, lang: str):
        url = message.text
        url_id = message.id
        
        sent = await self.app.send_message(message.from_user.id, Lang.PROCESSING_MESSAGE[lang])
        formats, video_info = self.yt.get_available_video_formats(url)
        
        message_text = TelegramMessageFormatter.create_video_info_format(video_info, formats, lang)
        keyboard = self.keyboards.video_format_keyboard(formats, url_id)

        await self.app.edit_message_text(
            chat_id=message.from_user.id,
            message_id=sent.id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )


    async def process_video_selection(self, query: CallbackQuery):
        data = query.data.split("_")
        url_id = data[1]
        format_id = data[2]

        url = await self.app.get_messages(query.from_user.id, int(url_id))
        url = url.text

        await self.app.answer_callback_query(query.id, text=f"Selected format: {format_id} for URL ID: {url_id}")
        await self.app.edit_message_text(
            chat_id=query.from_user.id,
            message_id=query.message.id,
            text=f"You selected format ID: {format_id}"
        )



    