# Command for managing bot scaling
import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from CONFIG.config import Config
from HELPERS.config_manager import config_manager
from HELPERS.logger import logger

async def scale_command(client: Client, message: Message):
    """Command for managing scaling"""
    user_id = message.chat.id
    
    # Check admin rights
    if int(user_id) not in Config.ADMIN:
        await message.reply("❌ This command is only available to administrators")
        return
    
    # Get command arguments
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        # Show current configuration
        await show_current_config(client, message)
        return
    
    command = args[0].lower()
    
    if command == "info":
        await show_current_config(client, message)
    elif command == "options":
        await show_scale_options(client, message)
    elif command == "apply":
        if len(args) < 2:
            await message.reply("❌ Specify scaling type: /scale apply <small|medium|large|enterprise|extreme>")
            return
        await apply_scale_config(client, message, args[1])
    elif command == "optimal":
        if len(args) < 2:
            await message.reply("❌ Specify expected number of users: /scale optimal <number>")
            return
        try:
            expected_users = int(args[1])
            await apply_optimal_config(client, message, expected_users)
        except ValueError:
            await message.reply("❌ Specify a valid number of users")
    else:
        await show_help(client, message)

async def show_current_config(client: Client, message: Message):
    """Show current configuration"""
    config = config_manager.get_current_config()
    
    text = "🔧 **Current scaling configuration:**\n\n"
    text += f"👥 **Users:** {config['max_users']}\n"
    text += f"🔄 **Processes:** {config['max_processes']}\n"
    text += f"🧵 **Threads per process:** {config['max_threads_per_process']}\n"
    text += f"📊 **Total threads:** {config['max_global_workers']}\n"
    text += f"⬇️ **Concurrent downloads:** {config['max_concurrent_global']}\n"
    text += f"🔥 **Firebase pool:** {config['firebase_pool_size']}\n"
    text += f"📱 **Telegram pool:** {config['telegram_pool_size']}\n"
    text += f"🛡️ **Semaphore:** {config['guard_semaphore_limit']}\n\n"
    
    text += "📈 **Priority pools:**\n"
    text += f"👑 VIP: {config['vip_processes']} processes\n"
    text += f"⭐ HIGH: {config['high_processes']} processes\n"
    text += f"📋 NORMAL: {config['normal_processes']} processes\n"
    text += f"📄 LOW: {config['low_processes']} processes"
    
    await message.reply(text)

async def show_scale_options(client: Client, message: Message):
    """Show available scaling options"""
    text = "🎯 **Available scaling options:**\n\n"
    
    scales = [
        ('small', 'Small loads (< 100 users)'),
        ('medium', 'Medium loads (< 1000 users)'),
        ('large', 'Large loads (< 5000 users)'),
        ('enterprise', 'Enterprise loads (10000+ users)'),
        ('extreme', 'Extreme loads (50000+ users)')
    ]
    
    for scale_type, description in scales:
        config = config_manager.get_scale_config(scale_type)
        requirements = config_manager.get_system_requirements(scale_type)
        
        text += f"**{scale_type.upper()}:** {description}\n"
        text += f"   🔄 Processes: {config['max_processes']}\n"
        text += f"   🧵 Threads: {config['max_threads_per_process']}\n"
        text += f"   📊 Total threads: {config['max_global_workers']}\n"
        text += f"   💻 CPU: {requirements['cpu_cores']} cores\n"
        text += f"   🧠 RAM: {requirements['ram_gb']} GB\n"
        text += f"   💾 Disk: {requirements['disk_gb']} GB\n"
        text += f"   🌐 Network: {requirements['network_mbps']} Mbps\n\n"
    
    # Add buttons for quick application
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Small", callback_data="scale_apply_small"),
            InlineKeyboardButton("Medium", callback_data="scale_apply_medium")
        ],
        [
            InlineKeyboardButton("Large", callback_data="scale_apply_large"),
            InlineKeyboardButton("Enterprise", callback_data="scale_apply_enterprise")
        ],
        [
            InlineKeyboardButton("Extreme", callback_data="scale_apply_extreme")
        ]
    ])
    
    await message.reply(text, reply_markup=keyboard)

async def apply_scale_config(client: Client, message: Message, scale_type: str):
    """Apply scaling configuration"""
    if scale_type not in ['small', 'medium', 'large', 'enterprise', 'extreme']:
        await message.reply("❌ Invalid scaling type. Available: small, medium, large, enterprise, extreme")
        return
    
    success = config_manager.apply_scale_config(scale_type)
    
    if success:
        config = config_manager.get_scale_config(scale_type)
        text = f"✅ **Configuration {scale_type.upper()} applied!**\n\n"
        text += f"🔄 Processes: {config['max_processes']}\n"
        text += f"🧵 Threads: {config['max_threads_per_process']}\n"
        text += f"📊 Total threads: {config['max_global_workers']}\n"
        text += f"⬇️ Downloads: {config['max_concurrent_global']}\n"
        text += f"🔥 Firebase: {config['firebase_pool_size']}\n"
        text += f"📱 Telegram: {config['telegram_pool_size']}\n\n"
        text += "⚠️ **Bot restart required to apply changes!**"
        
        await message.reply(text)
    else:
        await message.reply("❌ Error applying configuration")

async def apply_optimal_config(client: Client, message: Message, expected_users: int):
    """Apply optimal configuration for number of users"""
    config = config_manager.get_optimal_config(expected_users)
    
    # Determine scaling type
    if expected_users <= 100:
        scale_type = 'small'
    elif expected_users <= 1000:
        scale_type = 'medium'
    elif expected_users <= 5000:
        scale_type = 'large'
    elif expected_users <= 10000:
        scale_type = 'enterprise'
    else:
        scale_type = 'extreme'
    
    success = config_manager.apply_scale_config(scale_type)
    
    if success:
        requirements = config_manager.get_system_requirements(scale_type)
        text = f"✅ **Optimal configuration for {expected_users} users:**\n\n"
        text += f"🎯 Type: {scale_type.upper()}\n"
        text += f"🔄 Processes: {config['max_processes']}\n"
        text += f"🧵 Threads: {config['max_threads_per_process']}\n"
        text += f"📊 Total threads: {config['max_global_workers']}\n\n"
        text += "💻 **System requirements:**\n"
        text += f"   CPU: {requirements['cpu_cores']} cores\n"
        text += f"   RAM: {requirements['ram_gb']} GB\n"
        text += f"   Disk: {requirements['disk_gb']} GB\n"
        text += f"   Network: {requirements['network_mbps']} Mbps\n\n"
        text += "⚠️ **Bot restart required to apply changes!**"
        
        await message.reply(text)
    else:
        await message.reply("❌ Error applying configuration")

async def show_help(client: Client, message: Message):
    """Show command help"""
    text = "🔧 **Bot scaling management:**\n\n"
    text += "**Commands:**\n"
    text += "`/scale info` - show current configuration\n"
    text += "`/scale options` - show available options\n"
    text += "`/scale apply <type>` - apply configuration\n"
    text += "`/scale optimal <number>` - optimal configuration\n\n"
    text += "**Scaling types:**\n"
    text += "• `small` - small loads (< 100 users)\n"
    text += "• `medium` - medium loads (< 1000 users)\n"
    text += "• `large` - large loads (< 5000 users)\n"
    text += "• `enterprise` - enterprise loads (10000+ users)\n"
    text += "• `extreme` - extreme loads (50000+ users)\n\n"
    text += "**Examples:**\n"
    text += "`/scale apply enterprise`\n"
    text += "`/scale optimal 5000`"
    
    await message.reply(text)

# Callback handler for buttons
async def handle_scale_callback(client: Client, callback_query):
    """Callback handler for scaling buttons"""
    data = callback_query.data
    
    if data.startswith("scale_apply_"):
        scale_type = data.replace("scale_apply_", "")
        await apply_scale_config(client, callback_query.message, scale_type)
        await callback_query.answer(f"Configuration {scale_type.upper()} applied!")
