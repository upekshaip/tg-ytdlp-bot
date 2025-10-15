# Команда для просмотра статуса загрузок
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from CONFIG.messages import safe_get_messages
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

app = get_app()

@app.on_message(filters.command("status") & filters.private)
async def status_command(app, message):
    """Показывает статус текущих загрузок (только для админов)"""
    user_id = message.chat.id
    
    # Проверяем права администратора
    if user_id not in Config.ADMIN:
        await safe_send_message(user_id, "❌ Эта команда доступна только администраторам")
        return
    
    try:
        from HELPERS.concurrent_limiter import concurrent_limiter
        status = await concurrent_limiter.get_status()
        
        # Формируем сообщение о статусе
        status_text = f"📊 <b>Статус загрузок</b>\n\n"
        status_text += f"🔄 Активных загрузок: <b>{status['active_downloads']}</b>\n"
        status_text += f"📈 Максимум: <b>{status['max_concurrent']}</b>\n"
        status_text += f"✅ Доступно слотов: <b>{status['available_slots']}</b>\n"
        
        if status['users']:
            status_text += f"\n👥 Пользователи с активными загрузками:\n"
            for user in status['users']:
                status_text += f"• <code>{user}</code>\n"
        else:
            status_text += f"\n💤 Нет активных загрузок"
        
        # Добавляем кнопку обновления
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить", callback_data="status_refresh")]
        ])
        
        await safe_send_message(
            user_id, 
            status_text, 
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in status_command: {e}")
        await safe_send_message(user_id, f"❌ Ошибка получения статуса: {e}")

@app.on_callback_query(filters.regex(r"^status_refresh$"))
async def status_refresh_callback(app, callback_query):
    """Обновляет статус загрузок"""
    user_id = callback_query.from_user.id
    
    # Проверяем права администратора
    if user_id not in Config.ADMIN:
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        from HELPERS.concurrent_limiter import concurrent_limiter
        status = await concurrent_limiter.get_status()
        
        # Формируем сообщение о статусе
        status_text = f"📊 <b>Статус загрузок</b>\n\n"
        status_text += f"🔄 Активных загрузок: <b>{status['active_downloads']}</b>\n"
        status_text += f"📈 Максимум: <b>{status['max_concurrent']}</b>\n"
        status_text += f"✅ Доступно слотов: <b>{status['available_slots']}</b>\n"
        
        if status['users']:
            status_text += f"\n👥 Пользователи с активными загрузками:\n"
            for user in status['users']:
                status_text += f"• <code>{user}</code>\n"
        else:
            status_text += f"\n💤 Нет активных загрузок"
        
        # Добавляем кнопку обновления
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить", callback_data="status_refresh")]
        ])
        
        await callback_query.edit_message_text(
            status_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await callback_query.answer("✅ Статус обновлен")
        
    except Exception as e:
        logger.error(f"Error in status_refresh_callback: {e}")
        await callback_query.answer(f"❌ Ошибка: {e}", show_alert=True)
