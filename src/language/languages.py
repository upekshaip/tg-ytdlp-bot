class Languages(object):
    """
    A class to handle languages.
    This class only contains dictionaries for the languages
    that are currently being used in the bot, including messages and commands.
    """
    LANGUAGES = ["en", "es", "pt-br", "de", "ru", "uk"]

    LANGUAGE_MESSAGE = {
        "en": "🌐 Please select your language:",
        "es": "🌐 Por favor, selecciona tu idioma:",
        "pt-br": "🌐 Por favor, selecione seu idioma:",
        "de": "🌐 Bitte wähle deine Sprache:",
        "ru": "🌐 Пожалуйста, выберите ваш язык:",
        "uk": "🌐 Будь ласка, виберіть вашу мову:"
    }
    
    LANGUAGE_SELECTED_MESSAGE = {
        "en": "Language selected:",
        "es": "Idioma seleccionado:",
        "pt-br": "Idioma selecionado:",
        "de": "Sprache ausgewählt:",
        "ru": "Язык выбран:",
        "uk": "Мову вибрано:"
    }

    PROCESSING_MESSAGE = {
        "en": "⏳ Please wait. Processing your video...",
        "es": "⏳ Por favor, espera. Procesando tu video...",
        "pt-br": "⏳ Por favor, aguarde. Processando seu vídeo...",
        "de": "⏳ Bitte warten. Verarbeite dein Video...",
        "ru": "⏳ Пожалуйста, подождите. Обработка вашего видео...",
        "uk": "⏳ Будь ласка, зачекайте. Обробка вашого відео..."
    }

    VIDEO_FORMATS_MESSAGE = {
        "en": "📹 Available video formats:",
        "es": "📹 Formatos de video disponibles:",
        "pt-br": "📹 Formatos de vídeo disponíveis:",
        "de": "📹 Verfügbare Videoformate:",
        "ru": "📹 Доступные форматы видео:",
        "uk": "📹 Доступні формати відео:"
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
    
    
    WELCOME_MESSAGE = {
        "en": """
Hello {user},
 
This bot🤖 can download any videos into telegram directly.😊 For more information press /help 👈
 
Created by @upekshaip
Managed by @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
""",
        "es": """
Hola {user},

Este bot🤖 puede descargar cualquier video directamente a telegram.😊 Para más información presiona /help 👈

Creado por @upekshaip
Administrado por @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
""",
        "pt-br": """
Olá {user},

Este bot🤖 pode baixar qualquer vídeo diretamente para o telegram.😊 Para mais informações, pressione /help 👈

Criado por @upekshaip
Administrado por @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
"""
,
        "de": """
Hallo {user},

        
Dieser Bot🤖 kann jedes Video direkt in Telegram herunterladen.😊 Für weitere Informationen drücke /help 👈
Erstellt von @upekshaip
Verwaltet von @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl

""",
        "ru": """
Привет {user},

Этот бот🤖 может скачивать любые видео прямо в телеграм.😊 Для получения дополнительной информации нажмите /help 👈

Создан @upekshaip
Управляется @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
""",


}
    HELP_MESSAGE = {
    "en": """
🎬 <b>Video Download Bot - Help</b>

📥 <b>Basic Usage:</b>
• Send any video link and the bot will download it
• For audio extraction, use <code>/audio URL</code>
• Reply to any video with text to change its caption

📋 <b>Playlists:</b>
• <code>URL*1*5</code> - Download videos 1-5 from playlist
• <code>URL*1*5*My Playlist</code> - With custom name

🍪 <b>Cookies & Private Content:</b>
• Upload *.txt cookie file for private videos downloading
• <code>/download_cookie</code> - Get my YouTube cookie
• <code>/cookies_from_browser</code> - Extract from browser
• <code>/check_cookie</code> - Verify your cookie
• <code>/save_as_cookie</code> - Save text as cookie

🧹 <b>Cleaning:</b>
• <code>/clean</code> - Remove media files only
• <code>/clean all</code> - Remove everything
• <code>/clean cookies</code> - Remove cookie file
• <code>/clean logs</code> - Remove logs file
• <code>/clean tags</code> - Remove tags file
• <code>/clean format</code> - Remove format settings
• <code>/clean split</code> - Remove split settings
• <code>/clean mediainfo</code> - Remove mediainfo settings
• <code>/clean sub</code> - Remove subtitle settings

⚙️ <b>Settings:</b>
• <code>/settings</code> - Open settings menu
• <code>/format</code> - Change video quality & format
• <code>/split</code> - Set max part size (250MB-2GB)
• <code>/mediainfo</code> - Enable/disable file info
• <code>/tags</code> - View your saved tags
• <code>/sub</code> - Turn on/off subtitles

🏷️ <b>Tags System:</b>
• Add <code>#tag1#tag2</code> after any URL
• Tags appear in captions and are saved
• Use <code>/tags</code> to view all your tags

📊 <b>Information:</b>
• <code>/usage</code> - View your download history
• <code>/help</code> - Show this help message

👨‍💻 <i>Developer:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Contributor:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",

    "es": """
🎬 <b>Bot de Descarga de Videos - Ayuda</b>

📥 <b>Uso Básico:</b>
• Envía cualquier enlace de video y el bot lo descargará
• Para extraer audio, usa <code>/audio URL</code>
• Responde a cualquier video con texto para cambiar el título

📋 <b>Listas de Reproducción:</b>
• <code>URL*1*5</code> - Descarga videos 1-5 de la lista
• <code>URL*1*5*Mi Lista</code> - Con nombre personalizado

🍪 <b>Cookies y Contenido Privado:</b>
• Sube un archivo *.txt con cookies para descargar videos privados
• <code>/download_cookie</code> - Obtener mi cookie de YouTube
• <code>/cookies_from_browser</code> - Extraer desde navegador
• <code>/check_cookie</code> - Verificar tu cookie
• <code>/save_as_cookie</code> - Guardar texto como cookie

🧹 <b>Limpieza:</b>
• <code>/clean</code> - Eliminar solo archivos multimedia
• <code>/clean all</code> - Eliminar todo
• <code>/clean cookies</code> - Eliminar archivo de cookies
• <code>/clean logs</code> - Eliminar archivos de registro
• <code>/clean tags</code> - Eliminar etiquetas guardadas
• <code>/clean format</code> - Eliminar configuración de formato
• <code>/clean split</code> - Eliminar configuración de división
• <code>/clean mediainfo</code> - Eliminar info de medios
• <code>/clean sub</code> - Eliminar subtítulos

⚙️ <b>Configuración:</b>
• <code>/settings</code> - Abrir menú de configuración
• <code>/format</code> - Cambiar calidad y formato del video
• <code>/split</code> - Establecer tamaño máximo por parte
• <code>/mediainfo</code> - Activar/desactivar info del archivo
• <code>/tags</code> - Ver tus etiquetas guardadas
• <code>/sub</code> - Activar/desactivar subtítulos

🏷️ <b>Sistema de Etiquetas:</b>
• Agrega <code>#etiqueta1#etiqueta2</code> después de cualquier URL
• Las etiquetas aparecerán en los títulos
• Usa <code>/tags</code> para ver tus etiquetas

📊 <b>Información:</b>
• <code>/usage</code> - Ver tu historial de descargas
• <code>/help</code> - Mostrar este mensaje de ayuda

👨‍💻 <i>Desarrollador:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Colaborador:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",

    "pt-br": """
🎬 <b>Bot de Download de Vídeos - Ajuda</b>

📥 <b>Uso Básico:</b>
• Envie qualquer link de vídeo e o bot fará o download
• Para extrair áudio, use <code>/audio URL</code>
• Responda a qualquer vídeo com texto para alterar a legenda

📋 <b>Playlists:</b>
• <code>URL*1*5</code> - Baixar vídeos 1 a 5 da playlist
• <code>URL*1*5*Minha Playlist</code> - Com nome personalizado

🍪 <b>Cookies e Conteúdo Privado:</b>
• Envie um arquivo *.txt com cookies para baixar vídeos privados
• <code>/download_cookie</code> - Obter meu cookie do YouTube
• <code>/cookies_from_browser</code> - Extrair do navegador
• <code>/check_cookie</code> - Verificar seu cookie
• <code>/save_as_cookie</code> - Salvar texto como cookie

🧹 <b>Limpeza:</b>
• <code>/clean</code> - Remover apenas arquivos de mídia
• <code>/clean all</code> - Remover tudo
• <code>/clean cookies</code> - Remover arquivo de cookies
• <code>/clean logs</code> - Remover logs
• <code>/clean tags</code> - Remover etiquetas
• <code>/clean format</code> - Remover configurações de formato
• <code>/clean split</code> - Remover configurações de divisão
• <code>/clean mediainfo</code> - Remover configurações de info
• <code>/clean sub</code> - Remover legendas

⚙️ <b>Configurações:</b>
• <code>/settings</code> - Abrir menu de configurações
• <code>/format</code> - Alterar qualidade e formato do vídeo
• <code>/split</code> - Definir tamanho máximo da parte
• <code>/mediainfo</code> - Ativar/desativar informações
• <code>/tags</code> - Ver suas tags salvas
• <code>/sub</code> - Ativar/desativar legendas

🏷️ <b>Sistema de Tags:</b>
• Adicione <code>#tag1#tag2</code> após qualquer URL
• As tags aparecem nas legendas e são salvas
• Use <code>/tags</code> para ver suas tags

📊 <b>Informações:</b>
• <code>/usage</code> - Ver seu histórico de downloads
• <code>/help</code> - Mostrar esta mensagem de ajuda

👨‍💻 <i>Desenvolvedor:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Contribuidor:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",

    "de": """
🎬 <b>Video-Download-Bot – Hilfe</b>

📥 <b>Grundlegende Verwendung:</b>
• Sende einen Videolink und der Bot lädt es herunter
• Für Audio, nutze <code>/audio URL</code>
• Antworte mit Text, um die Beschreibung zu ändern

📋 <b>Playlists:</b>
• <code>URL*1*5</code> – Videos 1–5 herunterladen
• <code>URL*1*5*Meine Playlist</code> – Mit eigenem Namen

🍪 <b>Cookies & Private Inhalte:</b>
• Lade *.txt Cookie-Datei für private Videos hoch
• <code>/download_cookie</code> – Mein YouTube-Cookie abrufen
• <code>/cookies_from_browser</code> – Aus Browser extrahieren
• <code>/check_cookie</code> – Cookie prüfen
• <code>/save_as_cookie</code> – Text als Cookie speichern

🧹 <b>Bereinigung:</b>
• <code>/clean</code> – Nur Mediendateien entfernen
• <code>/clean all</code> – Alles entfernen
• <code>/clean cookies</code> – Cookie-Datei entfernen
• <code>/clean logs</code> – Logs löschen
• <code>/clean tags</code> – Tags entfernen
• <code>/clean format</code> – Format-Einstellungen löschen
• <code>/clean split</code> – Teilungseinstellungen löschen
• <code>/clean mediainfo</code> – Mediainfo löschen
• <code>/clean sub</code> – Untertitel entfernen

⚙️ <b>Einstellungen:</b>
• <code>/settings</code> – Einstellungsmenü öffnen
• <code>/format</code> – Qualität & Format ändern
• <code>/split</code> – Maximale Teilgröße setzen
• <code>/mediainfo</code> – Dateiinfo aktivieren/deaktivieren
• <code>/tags</code> – Gespeicherte Tags ansehen
• <code>/sub</code> – Untertitel ein/aus

🏷️ <b>Tagsystem:</b>
• Füge <code>#tag1#tag2</code> nach der URL hinzu
• Tags erscheinen in der Beschreibung
• Mit <code>/tags</code> anzeigen

📊 <b>Information:</b>
• <code>/usage</code> – Downloadverlauf anzeigen
• <code>/help</code> – Diese Hilfe anzeigen

👨‍💻 <i>Entwickler:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Beitrag:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",
"ru": """
🎬 <b>Бот для скачивания видео — Помощь</b>

📥 <b>Основное использование:</b>
• Отправьте любую ссылку на видео, и бот скачает его
• Для извлечения аудио используйте <code>/audio URL</code>
• Ответьте на любое видео с текстом, чтобы изменить подпись

📋 <b>Плейлисты:</b>
• <code>URL*1*5</code> — Скачать видео с 1 по 5 из плейлиста
• <code>URL*1*5*Мой плейлист</code> — С пользовательским названием

🍪 <b>Cookies и приватный контент:</b>
• Загрузите файл *.txt с cookie для скачивания приватных видео
• <code>/download_cookie</code> — Получить мой YouTube cookie
• <code>/cookies_from_browser</code> — Извлечь из браузера
• <code>/check_cookie</code> — Проверить cookie
• <code>/save_as_cookie</code> — Сохранить текст как cookie

🧹 <b>Очистка:</b>
• <code>/clean</code> — Удалить только медиафайлы
• <code>/clean all</code> — Удалить всё
• <code>/clean cookies</code> — Удалить файл cookie
• <code>/clean logs</code> — Удалить файлы логов
• <code>/clean tags</code> — Удалить теги
• <code>/clean format</code> — Удалить настройки формата
• <code>/clean split</code> — Удалить параметры разделения
• <code>/clean mediainfo</code> — Удалить инфо о файле
• <code>/clean sub</code> — Удалить субтитры

⚙️ <b>Настройки:</b>
• <code>/settings</code> — Открыть меню настроек
• <code>/format</code> — Изменить качество и формат
• <code>/split</code> — Установить максимальный размер части
• <code>/mediainfo</code> — Вкл/выкл информацию о файле
• <code>/tags</code> — Просмотр сохраненных тегов
• <code>/sub</code> — Вкл/выкл субтитры

🏷️ <b>Система тегов:</b>
• Добавьте <code>#тег1#тег2</code> после любой ссылки
• Теги отображаются в подписях и сохраняются
• Используйте <code>/tags</code> для просмотра тегов

📊 <b>Информация:</b>
• <code>/usage</code> — История загрузок
• <code>/help</code> — Показать это сообщение помощи

👨‍💻 <i>Разработчик:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Участник:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",
"uk": """
🎬 <b>Бот для завантаження відео — Допомога</b>

📥 <b>Основне використання:</b>
• Надішліть будь-яке посилання на відео, і бот його завантажить
• Для отримання аудіо використовуйте <code>/audio URL</code>
• Відповідайте на будь-яке відео текстом, щоб змінити підпис

📋 <b>Плейлисти:</b>
• <code>URL*1*5</code> — Завантажити відео з 1 по 5 з плейлиста
• <code>URL*1*5*Мій плейлист</code> — З власною назвою

🍪 <b>Cookies та приватний контент:</b>
• Завантажте файл *.txt з cookie для приватного контенту
• <code>/download_cookie</code> — Отримати мій YouTube cookie
• <code>/cookies_from_browser</code> — Витягти з браузера
• <code>/check_cookie</code> — Перевірити cookie
• <code>/save_as_cookie</code> — Зберегти текст як cookie

🧹 <b>Очищення:</b>
• <code>/clean</code> — Видалити тільки медіафайли
• <code>/clean all</code> — Видалити все
• <code>/clean cookies</code> — Видалити cookie
• <code>/clean logs</code> — Видалити логи
• <code>/clean tags</code> — Видалити теги
• <code>/clean format</code> — Видалити налаштування формату
• <code>/clean split</code> — Видалити налаштування розбиття
• <code>/clean mediainfo</code> — Видалити інформацію про файл
• <code>/clean sub</code> — Видалити субтитри

⚙️ <b>Налаштування:</b>
• <code>/settings</code> — Відкрити меню налаштувань
• <code>/format</code> — Змінити якість і формат відео
• <code>/split</code> — Встановити макс. розмір частини
• <code>/mediainfo</code> — Увімк/вимк інформацію про файл
• <code>/tags</code> — Перегляд збережених тегів
• <code>/sub</code> — Увімк/вимк субтитри

🏷️ <b>Система тегів:</b>
• Додайте <code>#тег1#тег2</code> після будь-якої URL
• Теги з’являються в підписах і зберігаються
• Використовуйте <code>/tags</code> для перегляду тегів

📊 <b>Інформація:</b>
• <code>/usage</code> — Історія ваших завантажень
• <code>/help</code> — Показати це повідомлення допомоги

👨‍💻 <i>Розробник:</i> @upekshaip <a href="https://github.com/upekshaip/tg-ytdlp-bot">[🛠 github]</a>
🤝 <i>Співавтор:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl <a href="https://github.com/chelaxian/tg-ytdlp-bot">[🛠 github]</a>
""",

}


    
