class Languages(object):
    """
    A class to handle languages.
    This class only contains dictionaries for the languages
    that are currently being used in the bot, including messages and commands.
    """
    LANGUAGES = ["en", "es", "pt-br", "de", "ru", "uk"]

    WELCOME_MESSAGE = {
        "en": "Welcome to the bot! Use /help for assistance.",
        "es": "¡Bienvenido al bot! Usa /help para asistencia.",
        "pt-br": "Bem-vindo ao bot! Use /help para assistência.",
        "de": "Willkommen beim Bot! Verwenden Sie /help für Hilfe.",
        "ru": "Добро пожаловать в бота! Используйте /help для помощи.",
        "uk": "Ласкаво просимо до бота! Використовуйте /help для допомоги."
    }
    # Yes and No
    YES = {
        "en": "✅ Yes",
        "es": "✅ Sí",
        "pt-br": "✅ Sim",
        "de": "✅ Ja",
        "ru": "✅ Да",
        "uk": "✅ Так"
    }
    NO = {
        "en": "❌ No",
        "es": "❌ No",
        "pt-br": "❌ Não",
        "de": "❌ Nein",
        "ru": "❌ Нет",
        "uk": "❌ Ні"
    }