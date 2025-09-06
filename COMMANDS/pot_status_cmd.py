# PO Token Provider Status Command
# Allows admins to check and manage PO token provider status

from pyrogram import filters
from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.logger import logger, send_to_user
from HELPERS.pot_helper import is_pot_provider_available, clear_pot_provider_cache, is_pot_enabled, get_pot_base_url

# Get app instance for decorators
app = get_app()

@app.on_message(filters.command("pot_status") & filters.private)
def pot_status_command(app, message):
    """
    Показывает статус PO token провайдера
    Доступно только администраторам
    """
    user_id = message.chat.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in Config.ADMIN:
        send_to_user(message, "❌ Эта команда доступна только администраторам")
        return
    
    try:
        # Получаем статус
        pot_enabled = is_pot_enabled()
        base_url = get_pot_base_url()
        is_available = is_pot_provider_available()
        
        # Формируем ответ
        status_text = "🔧 **PO Token Provider Status**\n\n"
        
        # Статус в конфигурации
        if pot_enabled:
            status_text += "✅ **Enabled in config**\n"
        else:
            status_text += "❌ **Disabled in config**\n"
        
        # URL провайдера
        status_text += f"🌐 **Provider URL:** `{base_url}`\n"
        
        # Статус доступности
        if is_available:
            status_text += "🟢 **Provider Status:** Available\n"
        else:
            status_text += "🔴 **Provider Status:** Unavailable\n"
        
        # Дополнительная информация
        if pot_enabled and not is_available:
            status_text += "\n⚠️ **Fallback Mode:** Bot will use standard YouTube extraction\n"
            status_text += "💡 **Tip:** Use `/pot_retry` to force recheck\n"
        elif pot_enabled and is_available:
            status_text += "\n✅ **Active:** PO tokens will be used for YouTube downloads\n"
        else:
            status_text += "\nℹ️ **Info:** PO token provider is disabled\n"
        
        send_to_user(message, status_text)
        
    except Exception as e:
        logger.error(f"Error in pot_status command: {e}")
        send_to_user(message, f"❌ Ошибка при проверке статуса: {e}")

@app.on_message(filters.command("pot_retry") & filters.private)
def pot_retry_command(app, message):
    """
    Принудительно перепроверяет доступность PO token провайдера
    Доступно только администраторам
    """
    user_id = message.chat.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in Config.ADMIN:
        send_to_user(message, "❌ Эта команда доступна только администраторам")
        return
    
    try:
        # Сбрасываем кэш
        clear_pot_provider_cache()
        
        # Проверяем доступность
        is_available = is_pot_provider_available()
        base_url = get_pot_base_url()
        
        if is_available:
            send_to_user(message, f"✅ **PO Token Provider is now available!**\n\n🌐 URL: `{base_url}`\n\n🔄 Cache cleared and rechecked successfully")
        else:
            send_to_user(message, f"❌ **PO Token Provider is still unavailable**\n\n🌐 URL: `{base_url}`\n\n⚠️ Bot will continue using fallback mode")
        
    except Exception as e:
        logger.error(f"Error in pot_retry command: {e}")
        send_to_user(message, f"❌ Ошибка при перепроверке: {e}")

@app.on_message(filters.command("pot_disable") & filters.private)
def pot_disable_command(app, message):
    """
    Временно отключает PO token провайдер (только для текущей сессии)
    Доступно только администраторам
    """
    user_id = message.chat.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in Config.ADMIN:
        send_to_user(message, "❌ Эта команда доступна только администраторам")
        return
    
    try:
        # Сбрасываем кэш и помечаем как недоступный
        clear_pot_provider_cache()
        global _pot_provider_cache
        _pot_provider_cache['available'] = False
        
        send_to_user(message, "🔴 **PO Token Provider temporarily disabled**\n\n⚠️ Bot will use standard YouTube extraction until restart or `/pot_retry`")
        
    except Exception as e:
        logger.error(f"Error in pot_disable command: {e}")
        send_to_user(message, f"❌ Ошибка при отключении: {e}")
