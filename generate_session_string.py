#!/usr/bin/env python3
"""
Скрипт для генерации session string пользователя для Channel Guard.

Этот скрипт создает пользовательскую сессию Telegram, которая необходима
для чтения admin logs канала (боты не могут это делать).

Использование:
1. Запустите: python generate_session_string.py
2. Введите номер телефона (с кодом страны, например: +79991234567)
3. Введите код подтверждения из Telegram
4. Если включена 2FA, введите пароль
5. Скопируйте полученный session string в конфиг как CHANNEL_GUARD_SESSION_STRING
"""

import asyncio
from pyrogram import Client
from CONFIG.config import Config

async def generate_session_string():
    """Генерирует session string для пользователя."""
    
    print("=" * 60)
    print("Генератор Session String для Channel Guard")
    print("=" * 60)
    print()
    print("Этот скрипт создаст пользовательскую сессию для чтения admin logs.")
    print("Вам понадобится:")
    print("  - Номер телефона (с кодом страны, например: +79991234567)")
    print("  - Код подтверждения из Telegram")
    print("  - Пароль 2FA (если включена)")
    print()
    
    # Проверяем наличие API_ID и API_HASH
    if not hasattr(Config, 'API_ID') or not hasattr(Config, 'API_HASH'):
        print("❌ Ошибка: API_ID или API_HASH не найдены в конфиге!")
        print("   Убедитесь, что они указаны в CONFIG/config.py")
        return
    
    api_id = Config.API_ID
    api_hash = Config.API_HASH
    
    print(f"✅ Используются API_ID: {api_id}")
    print(f"✅ Используется API_HASH: {api_hash[:10]}...")
    print()
    
    # Создаем клиент с временным именем сессии
    session_name = "channel_guard_user_session"
    
    print("Создание клиента...")
    client = Client(
        name=session_name,
        api_id=api_id,
        api_hash=api_hash,
        phone_number=None,  # Будет запрошен интерактивно
    )
    
    try:
        print("Запуск клиента...")
        await client.start()
        
        # Получаем session string
        session_string = await client.export_session_string()
        
        print()
        print("=" * 60)
        print("✅ Session String успешно сгенерирован!")
        print("=" * 60)
        print()
        print("Скопируйте следующую строку и добавьте в CONFIG/config.py:")
        print()
        print(f'    CHANNEL_GUARD_SESSION_STRING = "{session_string}"')
        print()
        print("=" * 60)
        print()
        print("⚠️  ВАЖНО:")
        print("   - Храните session string в безопасности!")
        print("   - Не публикуйте его в открытом доступе!")
        print("   - С этим session string можно получить доступ к вашему аккаунту!")
        print()
        
        # Сохраняем в файл для удобства
        try:
            with open("channel_guard_session_string.txt", "w", encoding="utf-8") as f:
                f.write(f"CHANNEL_GUARD_SESSION_STRING = \"{session_string}\"\n")
            print("✅ Session string также сохранен в файл: channel_guard_session_string.txt")
            print("   (удалите этот файл после копирования в конфиг!)")
        except Exception as e:
            print(f"⚠️  Не удалось сохранить в файл: {e}")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Ошибка при генерации session string:")
        print("=" * 60)
        print(f"   {e}")
        print()
        print("Возможные причины:")
        print("  - Неверный номер телефона или код")
        print("  - Проблемы с подключением к Telegram")
        print("  - Неверные API_ID или API_HASH")
        print()
    finally:
        await client.stop()
        print("Клиент остановлен.")

if __name__ == "__main__":
    print()
    try:
        asyncio.run(generate_session_string())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем.")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")

