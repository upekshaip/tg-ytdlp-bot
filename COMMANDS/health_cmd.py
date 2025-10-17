# Health Check Command
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from HELPERS.logger import logger
from HELPERS.safe_messeger import safe_send_message
from CONFIG.config import Config

async def health_command(app, message):
    """Health check command for admins"""
    user_id = message.chat.id
    
    # Debug logging
    logger.info(f"Health command called by user {user_id}")
    logger.info(f"Admin list: {Config.ADMIN}")
    logger.info(f"User in admin list: {int(user_id) in Config.ADMIN}")
    
    # Check if user is admin
    if int(user_id) not in Config.ADMIN:
        logger.warning(f"Access denied for user {user_id}")
        await safe_send_message(user_id, "❌ Access denied. Admin only.")
        return
    
    try:
        logger.info("Importing health_monitor...")
        from HELPERS.health_monitor import health_monitor
        logger.info("Getting health status...")
        status = health_monitor.get_status()
        logger.info(f"Health status: {status}")
        
        # Format status message
        status_text = f"🏥 **Bot Health Status**\n\n"
        status_text += f"📊 **Monitor Status:** {'✅ Running' if status['is_running'] else '❌ Stopped'}\n"
        status_text += f"⏰ **Last Activity:** {status['seconds_since_activity']:.1f} seconds ago\n"
        status_text += f"🔄 **Active Tasks:** {status['active_tasks']}\n"
        status_text += f"⚠️ **Hanging Tasks:** {status['hanging_tasks']}\n"
        
        if status['active_task_names']:
            status_text += f"\n📋 **Active Tasks:**\n"
            for task in status['active_task_names'][:5]:  # Show first 5
                status_text += f"• {task}\n"
        
        if status['hanging_task_names']:
            status_text += f"\n🚨 **Hanging Tasks:**\n"
            for task in status['hanging_task_names'][:5]:  # Show first 5
                status_text += f"• {task}\n"
        
        # Add health assessment
        if status['seconds_since_activity'] > 300:
            status_text += f"\n⚠️ **Warning:** Bot appears inactive for {status['seconds_since_activity']:.1f} seconds"
        elif status['hanging_tasks'] > 0:
            status_text += f"\n🚨 **Alert:** {status['hanging_tasks']} hanging tasks detected"
        else:
            status_text += f"\n✅ **Status:** Bot is healthy"
        
        # Create refresh button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="health_refresh")],
            [InlineKeyboardButton("🔚 Close", callback_data="health_close")]
        ])
        
        await safe_send_message(
            user_id,
            status_text,
            reply_markup=keyboard,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Health command error: {e}")
        import traceback
        logger.error(f"Health command traceback: {traceback.format_exc()}")
        await safe_send_message(
            user_id,
            f"❌ Health check failed: {str(e)}",
            message=message
        )

async def health_callback(app, callback_query):
    """Handle health check callbacks"""
    user_id = callback_query.from_user.id
    
    # Check if user is admin
    if int(user_id) not in Config.ADMIN:
        await callback_query.answer("❌ Access denied", show_alert=True)
        return
    
    data = callback_query.data.split("_")[1]
    
    if data == "refresh":
        # Refresh health status
        try:
            from HELPERS.health_monitor import health_monitor
            status = health_monitor.get_status()
            
            # Format status message
            status_text = f"🏥 **Bot Health Status** (Refreshed)\n\n"
            status_text += f"📊 **Monitor Status:** {'✅ Running' if status['is_running'] else '❌ Stopped'}\n"
            status_text += f"⏰ **Last Activity:** {status['seconds_since_activity']:.1f} seconds ago\n"
            status_text += f"🔄 **Active Tasks:** {status['active_tasks']}\n"
            status_text += f"⚠️ **Hanging Tasks:** {status['hanging_tasks']}\n"
            
            if status['active_task_names']:
                status_text += f"\n📋 **Active Tasks:**\n"
                for task in status['active_task_names'][:5]:
                    status_text += f"• {task}\n"
            
            if status['hanging_task_names']:
                status_text += f"\n🚨 **Hanging Tasks:**\n"
                for task in status['hanging_task_names'][:5]:
                    status_text += f"• {task}\n"
            
            # Add health assessment
            if status['seconds_since_activity'] > 300:
                status_text += f"\n⚠️ **Warning:** Bot appears inactive for {status['seconds_since_activity']:.1f} seconds"
            elif status['hanging_tasks'] > 0:
                status_text += f"\n🚨 **Alert:** {status['hanging_tasks']} hanging tasks detected"
            else:
                status_text += f"\n✅ **Status:** Bot is healthy"
            
            # Create refresh button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="health_refresh")],
                [InlineKeyboardButton("🔚 Close", callback_data="health_close")]
            ])
            
            await callback_query.edit_message_text(
                status_text,
                reply_markup=keyboard
            )
            await callback_query.answer("✅ Status refreshed")
            
        except Exception as e:
            logger.error(f"Health refresh error: {e}")
            await callback_query.answer(f"❌ Refresh failed: {str(e)}", show_alert=True)
    
    elif data == "close":
        try:
            await callback_query.message.delete()
            await callback_query.answer("✅ Health check closed")
        except Exception as e:
            logger.error(f"Health close error: {e}")
            await callback_query.answer("❌ Close failed", show_alert=True)
