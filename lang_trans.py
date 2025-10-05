#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-translate user-facing messages in a Python source file (e.g., Telegram bot messages).
- Translates only string literals (single, double, triple quotes).
- Preserves technical elements: HTML/Markdown, placeholders {var}, commands, URLs, emojis, versions, codecs, sizes, etc.
- Language packs for RU (Russian), AR (Arabic), HI (Hindi/India).
- Allows custom dictionary merge via JSON.
- Deterministic, offline, regex-based.

Usage:
  python3 translate_bot_messages.py /path/to/messages_EN.py --lang ru [--out messages_RU.py] [--dict custom.json]

Examples:
  python3 translate_bot_messages.py messages_EN.py --lang ru
  python3 translate_bot_messages.py messages_EN.py --lang ar --out messages_AR.py
  python3 translate_bot_messages.py messages_EN.py --lang hi --dict my_terms.json
"""

import re
import os
import sys
import json
import argparse
from typing import List, Tuple, Dict

# ------------------------------------------------------------------------------
# Built-in base dictionaries per language (extend as needed)
# Keys are English canonical forms; casing is preserved at runtime.
# ------------------------------------------------------------------------------

TRANSLATIONS_RU: Dict[str, str] = {
    # Basic words
    "Error": "Ошибка",
    "Errors": "Ошибки",
    "Unknown": "Неизвестно",
    "Success": "Успешно",
    "Warning": "Предупреждение",
    "Info": "Информация",
    "Help": "Помощь",
    "Settings": "Настройки",
    "Menu": "Меню",
    "Close": "Закрыть",
    "Opened": "Открыто",
    "Closed": "Закрыто",
    "Enabled": "Включено",
    "Disabled": "Выключено",
    "ON": "ВКЛ",
    "OFF": "ВЫКЛ",
    "Proxy": "Прокси",
    "Keyboard": "Клавиатура",
    "Cookies": "Куки",
    "MediaInfo": "Информация о файле",
    "Subtitles": "Субтитры",
    "Subtitle": "Субтитр",
    "Language": "Язык",
    "Video": "Видео",
    "Audio": "Аудио",
    "Images": "Изображения",
    "Image": "Изображение",
    "Playlist": "Плейлист",
    "Playlists": "Плейлисты",
    "Group": "Группа",
    "Limits": "Лимиты",
    "Format": "Формат",
    "Formats": "Форматы",
    "Quality": "Качество",
    "Duration": "Длительность",
    "Title": "Название",
    "Direct": "Прямые",
    "Link": "Ссылка",
    "Links": "Ссылки",
    "Download": "Загрузка",
    "Downloading": "Загрузка",
    "Processing": "Обработка",
    "Completed": "Завершено",
    "Complete": "Завершено",
    "Please": "Пожалуйста",
    "Wait": "Подождите",
    "Try": "Попробуйте",
    "again": "ещё раз",
    "File": "Файл",
    "Files": "Файлы",
    "Size": "Размер",
    "Cache": "Кэш",
    "Sent": "Отправлено",
    "from": "из",
    "Checking": "Проверка",
    "Invalid": "Некорректно",
    "Valid": "Корректно",
    "Provide": "Укажите",
    "URL": "URL",
    "Warning:": "Внимание:",
    "Example": "Пример",
    "Examples": "Примеры",
    "Range": "Диапазон",
    "Usage": "Использование",
    "Notes": "Заметки",
    "Note": "Примечание",
    "Tests": "Тесты",
    "Test": "Тест",
    "Selected": "Выбрано",
    "Set": "Установлено",
    "Saved": "Сохранено",
    "Parameters": "Параметры",
    "Parameter": "Параметр",
    "Option": "Опция",
    "Options": "Опции",
    "Current value": "Текущее значение",
    "Quick commands": "Быстрые команды",
    "Search": "Поиск",
    "History": "История",
    "Account": "Аккаунт",
    "username": "имя пользователя",
    
    # Bot-specific terms
    "Live": "Прямой",
    "Stream": "Стрим",
    "Detected": "Обнаружен",
    "Downloading of ongoing": "Загрузка текущих",
    "infinite live streams": "бесконечных прямых трансляций",
    "is not allowed": "не разрешена",
    "Please wait for the stream": "Пожалуйста, дождитесь окончания стрима",
    "to end and try downloading": "и попробуйте загрузить",
    "again when": "снова, когда",
    "The stream duration": "Длительность стрима",
    "is known": "известна",
    "The stream has finished": "Стрим завершился",
    "Mobile": "Мобильный",
    "Activate": "Активировать",
    "Inline search helper": "Встроенный помощник поиска",
    "set language with": "установить язык с",
    "AUTO/TRANS": "АВТО/ПЕРЕВОД",
    "Current value": "Текущее значение",
    "Geo Bypass": "Гео Обход",
    "Embed Meta": "Встроить Мета",
    "Embed Thumb": "Встроить Миниатюру",
    "Write Thumb": "Записать Миниатюру",
    "Concurrent": "Параллельно",
    "Sleep Subs": "Ожидание Субтитров",
    "Legacy Connect": "Устаревшее Подключение",
    "Ignore Errors": "Игнорировать Ошибки",
    "Playlist Items": "Элементы Плейлиста",
    "Max Sleep": "Макс Ожидание",
    "Join Channel": "Присоединиться к Каналу",
    "Verification Required": "Требуется Проверка",
    "Policy Violation": "Нарушение Политики",
    "Impersonate": "Имперсонация",
    "Referer": "Реферер",
    "Username": "Имя Пользователя",
    "Password": "Пароль",
    "Clean": "Чистый",
    "TikTok": "ТикТок",
    "Instagram": "Инстаграм",
    "playlist": "плейлист",
    "Smart grouping": "Умная группировка",
    "Filters updated": "Фильтры обновлены",
    "db created": "база данных создана",
    "Bot started": "Бот запущен",
    
    # Common phrases
    "Error occurred": "Произошла ошибка",
    "Unknown error": "Неизвестная ошибка",
    "An error occurred": "Произошла ошибка",
    "Please wait": "Пожалуйста, подождите",
    "Processing...": "Обработка...",
    "Downloading media...": "Загрузка медиа...",
    "Download complete": "Загрузка завершена",
    "Invalid URL": "Некорректный URL",
    "Not enough disk space": "Недостаточно места на диске",
    "File size exceeds the limit": "Размер файла превышает лимит",
    "Direct link obtained": "Получена прямая ссылка",
    "Getting direct link...": "Получение прямой ссылки...",
    "Getting available formats...": "Получение доступных форматов...",
    "Invalid parameter": "Некорректный параметр",
    "Command executed": "Команда выполнена",
    "Menu closed": "Меню закрыто",
    "Access denied": "Доступ запрещён",
    "Please send a number": "Пожалуйста, отправьте число",
    "Please provide a valid URL": "Пожалуйста, укажите корректный URL",
    "Please send valid JSON": "Пожалуйста, отправьте корректный JSON",
    "Language set to": "Язык установлен:",
    "Subtitles are disabled": "Субтитры отключены",
    "Provide a valid URL": "Укажите корректный URL",
}

TRANSLATIONS_AR: Dict[str, str] = {
    # Basic words
    "Error": "خطأ",
    "Errors": "أخطاء",
    "Unknown": "غير معروف",
    "Success": "نجاح",
    "Warning": "تحذير",
    "Info": "معلومات",
    "Help": "مساعدة",
    "Settings": "الإعدادات",
    "Menu": "القائمة",
    "Close": "إغلاق",
    "Opened": "مفتوح",
    "Closed": "مغلق",
    "Enabled": "مُمكّن",
    "Disabled": "معطّل",
    "ON": "تشغيل",
    "OFF": "إيقاف",
    "Proxy": "وكيل",
    "Keyboard": "لوحة المفاتيح",
    "Cookies": "ملفات تعريف الارتباط",
    "MediaInfo": "معلومات الملف",
    "Subtitles": "الترجمات",
    "Subtitle": "ترجمة",
    "Language": "اللغة",
    "Video": "فيديو",
    "Audio": "صوت",
    "Images": "صور",
    "Image": "صورة",
    "Playlist": "قائمة تشغيل",
    "Playlists": "قوائم تشغيل",
    "Group": "مجموعة",
    "Limits": "الحدود",
    "Format": "الصيغة",
    "Formats": "الصيغ",
    "Quality": "الجودة",
    "Duration": "المدة",
    "Title": "العنوان",
    "Direct": "مباشر",
    "Link": "رابط",
    "Links": "روابط",
    "Download": "تنزيل",
    "Downloading": "جارٍ التنزيل",
    "Processing": "جارٍ المعالجة",
    "Completed": "اكتمل",
    "Complete": "مكتمل",
    "Please": "الرجاء",
    "Wait": "الانتظار",
    "Try": "حاول",
    "again": "مرة أخرى",
    "File": "ملف",
    "Files": "ملفات",
    "Size": "الحجم",
    "Cache": "ذاكرة مؤقتة",
    "Sent": "تم الإرسال",
    "from": "من",
    "Checking": "جارٍ الفحص",
    "Invalid": "غير صالح",
    "Valid": "صالح",
    "Provide": "قدّم",
    "URL": "URL",
    "Warning:": "تحذير:",
    "Example": "مثال",
    "Examples": "أمثلة",
    "Range": "نطاق",
    "Usage": "الاستخدام",
    "Notes": "ملاحظات",
    "Note": "ملاحظة",
    "Tests": "اختبارات",
    "Test": "اختبار",
    "Selected": "محدّد",
    "Set": "تعيين",
    "Saved": "تم الحفظ",
    "Parameters": "المعلمات",
    "Parameter": "معلمة",
    "Option": "خيار",
    "Options": "خيارات",
    "Current value": "القيمة الحالية",
    "Quick commands": "أوامر سريعة",
    "Search": "بحث",
    "History": "السجل",
    "Account": "الحساب",
    "username": "اسم المستخدم",
    
    # Bot-specific terms
    "Live": "مباشر",
    "Stream": "بث",
    "Detected": "تم اكتشاف",
    "Downloading of ongoing": "تحميل الجاري",
    "infinite live streams": "البث المباشر اللامحدود",
    "is not allowed": "غير مسموح",
    "Please wait for the stream": "يرجى انتظار انتهاء البث",
    "to end and try downloading": "وانتهاءه ثم حاول التحميل",
    "again when": "مرة أخرى عندما",
    "The stream duration": "مدة البث",
    "is known": "معروفة",
    "The stream has finished": "انتهى البث",
    "Mobile": "محمول",
    "Activate": "تفعيل",
    "Inline search helper": "مساعد البحث المدمج",
    "set language with": "تعيين اللغة مع",
    "AUTO/TRANS": "تلقائي/ترجمة",
    "Current value": "القيمة الحالية",
    "Geo Bypass": "تجاوز جغرافي",
    "Embed Meta": "تضمين البيانات الوصفية",
    "Embed Thumb": "تضمين الصورة المصغرة",
    "Write Thumb": "كتابة الصورة المصغرة",
    "Concurrent": "متزامن",
    "Sleep Subs": "انتظار الترجمات",
    "Legacy Connect": "اتصال قديم",
    "Ignore Errors": "تجاهل الأخطاء",
    "Playlist Items": "عناصر القائمة",
    "Max Sleep": "أقصى انتظار",
    "Join Channel": "انضم للقناة",
    "Verification Required": "التحقق مطلوب",
    "Policy Violation": "انتهاك السياسة",
    "Impersonate": "انتحال شخصية",
    "Referer": "المرجع",
    "Username": "اسم المستخدم",
    "Password": "كلمة المرور",
    "Clean": "نظيف",
    "TikTok": "تيك توك",
    "Instagram": "إنستغرام",
    "playlist": "قائمة تشغيل",
    "Smart grouping": "تجميع ذكي",
    "Filters updated": "تم تحديث المرشحات",
    "db created": "تم إنشاء قاعدة البيانات",
    "Bot started": "تم بدء البوت",
    
    # Common phrases
    "Error occurred": "حدث خطأ",
    "Unknown error": "خطأ غير معروف",
    "An error occurred": "حدث خطأ",
    "Please wait": "يرجى الانتظار",
    "Processing...": "جارٍ المعالجة...",
    "Downloading media...": "جارٍ تنزيل الوسائط...",
    "Download complete": "اكتمل التنزيل",
    "Invalid URL": "رابط غير صالح",
    "Not enough disk space": "لا توجد مساحة كافية على القرص",
    "File size exceeds the limit": "يتجاوز حجم الملف الحد",
    "Direct link obtained": "تم الحصول على رابط مباشر",
    "Getting direct link...": "جارٍ الحصول على رابط مباشر...",
    "Getting available formats...": "جارٍ الحصول على الصيغ المتاحة...",
    "Invalid parameter": "معلمة غير صالحة",
    "Command executed": "تم تنفيذ الأمر",
    "Menu closed": "تم إغلاق القائمة",
    "Access denied": "تم رفض الوصول",
    "Please send a number": "يرجى إرسال رقم",
    "Please provide a valid URL": "يرجى تقديم رابط صالح",
    "Please send valid JSON": "يرجى إرسال JSON صالح",
    "Language set to": "تم تعيين اللغة إلى",
    "Subtitles are disabled": "تم تعطيل الترجمات",
    "Provide a valid URL": "يرجى تقديم رابط صالح",
}

TRANSLATIONS_HI: Dict[str, str] = {
    # Basic words
    "Error": "त्रुटि",
    "Errors": "त्रुटियाँ",
    "Unknown": "अज्ञात",
    "Success": "सफल",
    "Warning": "चेतावनी",
    "Info": "जानकारी",
    "Help": "सहायता",
    "Settings": "सेटिंग्स",
    "Menu": "मेनू",
    "Close": "बंद करें",
    "Opened": "खोला गया",
    "Closed": "बंद",
    "Enabled": "सक्रिय",
    "Disabled": "निष्क्रिय",
    "ON": "चालू",
    "OFF": "बंद",
    "Proxy": "प्रॉक्सी",
    "Keyboard": "कीबोर्ड",
    "Cookies": "कुकीज़",
    "MediaInfo": "फ़ाइल जानकारी",
    "Subtitles": "उपशीर्षक",
    "Subtitle": "उपशीर्षक",
    "Language": "भाषा",
    "Video": "वीडियो",
    "Audio": "ऑडियो",
    "Images": "छवियाँ",
    "Image": "छवि",
    "Playlist": "प्लेलिस्ट",
    "Playlists": "प्लेलिस्ट्स",
    "Group": "समूह",
    "Limits": "सीमाएँ",
    "Format": "फ़ॉर्मेट",
    "Formats": "फ़ॉर्मेट्स",
    "Quality": "गुणवत्ता",
    "Duration": "अवधि",
    "Title": "शीर्षक",
    "Direct": "प्रत्यक्ष",
    "Link": "लिंक",
    "Links": "लिंक",
    "Download": "डाउनलोड",
    "Downloading": "डाउनलोड हो रहा है",
    "Processing": "प्रोसेस हो रहा है",
    "Completed": "पूर्ण",
    "Complete": "पूर्ण",
    "Please": "कृपया",
    "Wait": "प्रतीक्षा करें",
    "Try": "कोशिश करें",
    "again": "फिर से",
    "File": "फ़ाइल",
    "Files": "फ़ाइलें",
    "Size": "आकार",
    "Cache": "कैश",
    "Sent": "भेजा गया",
    "from": "से",
    "Checking": "जाँच",
    "Invalid": "अमान्य",
    "Valid": "मान्य",
    "Provide": "प्रदान करें",
    "URL": "URL",
    "Warning:": "चेतावनी:",
    "Example": "उदाहरण",
    "Examples": "उदाहरण",
    "Range": "सीमा",
    "Usage": "उपयोग",
    "Notes": "नोट्स",
    "Note": "नोट",
    "Tests": "परीक्षण",
    "Test": "परीक्षण",
    "Selected": "चयनित",
    "Set": "सेट",
    "Saved": "सहेजा गया",
    "Parameters": "पैरामीटर",
    "Parameter": "पैरामीटर",
    "Option": "विकल्प",
    "Options": "विकल्प",
    "Current value": "वर्तमान मान",
    "Quick commands": "त्वरित कमांड",
    "Search": "खोज",
    "History": "इतिहास",
    "Account": "खाता",
    "username": "उपयोगकर्ता नाम",
    
    # Bot-specific terms
    "Live": "लाइव",
    "Stream": "स्ट्रीम",
    "Detected": "पता चला",
    "Downloading of ongoing": "चल रहे का डाउनलोड",
    "infinite live streams": "अनंत लाइव स्ट्रीम",
    "is not allowed": "अनुमति नहीं है",
    "Please wait for the stream": "कृपया स्ट्रीम के समाप्त होने की प्रतीक्षा करें",
    "to end and try downloading": "समाप्त होने और डाउनलोड करने की कोशिश करें",
    "again when": "फिर से जब",
    "The stream duration": "स्ट्रीम की अवधि",
    "is known": "ज्ञात है",
    "The stream has finished": "स्ट्रीम समाप्त हो गई है",
    "Mobile": "मोबाइल",
    "Activate": "सक्रिय करें",
    "Inline search helper": "इनलाइन खोज सहायक",
    "set language with": "भाषा सेट करें",
    "AUTO/TRANS": "ऑटो/ट्रांस",
    "Current value": "वर्तमान मान",
    "Geo Bypass": "भौगोलिक बायपास",
    "Embed Meta": "एम्बेड मेटा",
    "Embed Thumb": "एम्बेड थंबनेल",
    "Write Thumb": "लिखें थंबनेल",
    "Concurrent": "समवर्ती",
    "Sleep Subs": "सबटाइटल प्रतीक्षा",
    "Legacy Connect": "पुराना कनेक्ट",
    "Ignore Errors": "त्रुटियों को नजरअंदाज करें",
    "Playlist Items": "प्लेलिस्ट आइटम",
    "Max Sleep": "अधिकतम प्रतीक्षा",
    "Join Channel": "चैनल में शामिल हों",
    "Verification Required": "सत्यापन आवश्यक",
    "Policy Violation": "नीति उल्लंघन",
    "Impersonate": "अनुकरण",
    "Referer": "रेफरर",
    "Username": "उपयोगकर्ता नाम",
    "Password": "पासवर्ड",
    "Clean": "साफ",
    "TikTok": "टिकटॉक",
    "Instagram": "इंस्टाग्राम",
    "playlist": "प्लेलिस्ट",
    "Smart grouping": "स्मार्ट समूहीकरण",
    "Filters updated": "फिल्टर अपडेट किए गए",
    "db created": "डेटाबेस बनाया गया",
    "Bot started": "बॉट शुरू किया गया",
    
    # Common phrases
    "Error occurred": "त्रुटि हुई",
    "Unknown error": "अज्ञात त्रुटि",
    "An error occurred": "एक त्रुटि हुई",
    "Please wait": "कृपया प्रतीक्षा करें",
    "Processing...": "प्रोसेस हो रहा है...",
    "Downloading media...": "मीडिया डाउनलोड हो रहा है...",
    "Download complete": "डाउनलोड पूर्ण",
    "Invalid URL": "अमान्य URL",
    "Not enough disk space": "डिस्क में पर्याप्त स्थान नहीं",
    "File size exceeds the limit": "फ़ाइल आकार सीमा से अधिक है",
    "Direct link obtained": "प्रत्यक्ष लिंक प्राप्त",
    "Getting direct link...": "प्रत्यक्ष लिंक प्राप्त किया जा रहा है...",
    "Getting available formats...": "उपलब्ध फ़ॉर्मेट्स प्राप्त किए जा रहे हैं...",
    "Invalid parameter": "अमान्य पैरामीटर",
    "Command executed": "कमांड निष्पादित",
    "Menu closed": "मेनू बंद",
    "Access denied": "पहुँच अस्वीकृत",
    "Please send a number": "कृपया एक संख्या भेजें",
    "Please provide a valid URL": "कृपया मान्य URL दें",
    "Please send valid JSON": "कृपया मान्य JSON भेजें",
    "Language set to": "भाषा सेट:",
    "Subtitles are disabled": "उपशीर्षक अक्षम हैं",
    "Provide a valid URL": "कृपया मान्य URL दें",
}

LANG_MAP = {
    "ru": TRANSLATIONS_RU,
    "ar": TRANSLATIONS_AR,
    "hi": TRANSLATIONS_HI,  # Hindi (India)
}

# ------------------------------------------------------------------------------
# Regex patterns for string literals and protections
# ------------------------------------------------------------------------------

STRING_RE = re.compile(r'(?P<quote>"""|\'\'\'|"|\')(?P<body>.*?)(?P=quote)', re.DOTALL)

PROTECT_PATTERNS = {
    "placeholders": re.compile(r"\{[^}]+\}"),
    "html_tags": re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(\s+[^>]*?)?>"),
    "md_strong": re.compile(r"\*\*[^*]+\*\*"),
    "md_em": re.compile(r"(?<!\*)\*[^*\n]+\*(?!\*)"),
    "md_u": re.compile(r"__[^_\n]+__"),
    "md_i": re.compile(r"_[^_\n]+_"),
    "backticks": re.compile(r"`[^`]*`"),
    "slash_commands": re.compile(r"(?<!\S)/(?:[A-Za-z0-9_]+)(?:[ \t]+[^\n]*)?"),
    "at_handles": re.compile(r"@[A-Za-z0-9_]+"),
    "urls": re.compile(r"(https?://[^\s<>\"]+|www\.[^\s<>\"]+|(?:youtube|tiktok|instagram|twitter|facebook)\.com[^\s<>\"]*)", re.IGNORECASE),
    "underscored": re.compile(r"\b[A-Za-z0-9]+_[A-Za-z0-9_]+\b"),
    "versions": re.compile(r"\bv?\d+\.\d+\.\d+\b", re.IGNORECASE),
    "sizes_units": re.compile(r"\b(?:\d+(?:\.\d+)?(?:MB|GB|KB)|\d+p|[48]K)\b", re.IGNORECASE),
    "dates_times": re.compile(r"\b(?:\d{8}|\d{2}:\d{2}:\d{2})\b"),
    "ips": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b"),
    "emails": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "hashes": re.compile(r"\b[a-zA-Z0-9]{3,}[-_a-zA-Z0-9]*\b"),
    "paths": re.compile(r"(?:[A-Za-z]:\\[^\s\"']+|/[^ \t\n\"']+|[A-Za-z0-9_\-]+/[A-Za-z0-9_\-./{}]+)"),
    "extensions": re.compile(r"\.(?:txt|py|js|mp4|avi|mkv|mp3|wav|webm|ogg|flac)\b", re.IGNORECASE),
    "protocols": re.compile(r"\b(?:HTTP|HTTPS|FTP|SSH)\b"),
    "currency_percent": re.compile(r"[$€₽]\s?\d+(?:\.\d+)?|\b\d+(?:\.\d+)?%"),
    "country_codes": re.compile(r"\b(?:US|GB|DE|FR|JP)\b"),
    "codecs": re.compile(r"\b(?:MP4|MKV|AVI|MOV|WEBM|H\.264|AV1|VP9|avc1|av01|vp09|MP3|WAV|AAC|FLAC|OGG)\b", re.IGNORECASE),
    # Bot-specific patterns
    "bot_commands": re.compile(r"/(?:vid|audio|img|search|subs|format|split|proxy|keyboard|args|nsfw|clean|help|settings|usage|playlist|link|list|mediainfo|tags|add_bot_to_group|auto_cache|check_porn|uncache|block_user|unblock_user|promo|user_logs|bot_data|update_porn|reload_cache|check_cookie|cookies_from_browser|save_as_cookie|cookie)(?:\s+[^\n]*)?", re.IGNORECASE),
    "bot_handles": re.compile(r"@(?:vid|tgytdlp_it_bot|tgytdlp_uae_bot|tgytdlp_uk_bot|tgytdlp_fr_bot|tg_ytdlp|iilililiiillliiliililliilliliiil|upekshaip|IIlIlIlIIIlllIIlIIlIllIIllIlIIIl)", re.IGNORECASE),
    "technical_vars": re.compile(r"\b(?:FIREBASE_|Config\.|ADMIN_|DB_|MAGIC_|YTDLP_|GALLERY_DL_|FFMPEG_|HELPER_|SENDER_|URL_PARSER_|VIDEO_EXTRACTOR_|THUMBNAIL_|POT_|SAFE_MESSENGER_|HANDLER_REGISTRY_|APP_INSTANCE_|CAPTION_|UPDATE_|RESTORE_|MULTILANG_|LANGUAGE_ROUTER_)[A-Za-z0-9_]*\b"),
    "emojis": re.compile(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F0F5\U0001F200-\U0001F2FF]+"),
    "unicode_emojis": re.compile(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F0F5\U0001F200-\U0001F2FF]+"),
    "special_chars": re.compile(r"[•▶️⏳⌛📥📤🔗🎬📹🎵🎧🖼📱🔍⚙️🧹🍪🌐📊💬🎹🔞📃⏯️🔚🔙⬅️➡️⬆️⬇️✅❌⚠️ℹ️🚫📋🎛️🔤🗣️💻📱💎⭐️🆓🔞🆕🔄🛑🛠️🤖👥📢🗒️💡💰💲🌍🇮🇹🇦🇪🇬🇧🇫🇷🇷🇺]"),
    "time_formats": re.compile(r"\b(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?|\d+(?:\.\d+)?\s*(?:hours?|minutes?|seconds?|hrs?|mins?|secs?))\b", re.IGNORECASE),
    "file_sizes": re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:KB|MB|GB|TB|PB|EB|ZB|YB))\b", re.IGNORECASE),
    "quality_formats": re.compile(r"\b(?:\d+p|4K|8K|HD|FHD|UHD|SD|LD)\b", re.IGNORECASE),
    "browser_names": re.compile(r"\b(?:Chrome|Firefox|Safari|Edge|Opera|Brave|Vivaldi|Chromium)\b", re.IGNORECASE),
    "os_names": re.compile(r"\b(?:Windows|macOS|Linux|iOS|Android|Ubuntu|Debian|CentOS|Fedora|Arch|Mint|Elementary|Pop|Manjaro)\b", re.IGNORECASE),
    "social_platforms": re.compile(r"\b(?:YouTube|TikTok|Instagram|Twitter|Facebook|VK|Vimeo|Twitch|Rutube|Pornhub|OnlyFans|Patreon|Discord|Telegram|WhatsApp|Signal|Skype|Zoom|Teams|Slack|Discord|Reddit|LinkedIn|Pinterest|Snapchat|Tumblr|Flickr|Imgur|DeviantArt|ArtStation|Behance|Dribbble|GitHub|GitLab|Bitbucket|StackOverflow|Medium|Dev\.to|Hashnode|Substack|Ghost|WordPress|Joomla|Drupal|Magento|Shopify|WooCommerce|PrestaShop|OpenCart|BigCommerce|Squarespace|Wix|Webflow|Framer|Figma|Sketch|Adobe|Canva|Unsplash|Pexels|Pixabay|Freepik|Shutterstock|Getty|iStock|Depositphotos|123RF|Dreamstime|Alamy|Westend61|Corbis|Masterfile|Photodisc|ImageSource|Blend|Stocksy|Offset|Moment|Twenty20|Death|To|Stock|Photo|Unsplash|Pexels|Pixabay|Freepik|Shutterstock|Getty|iStock|Depositphotos|123RF|Dreamstime|Alamy|Westend61|Corbis|Masterfile|Photodisc|ImageSource|Blend|Stocksy|Offset|Moment|Twenty20|Death|To|Stock|Photo)\b", re.IGNORECASE),
}

SKIP_ENTIRE_LITERAL = [
    re.compile(r"^\s*$"),
    re.compile(r"^[\n\r\t\\]+$"),
    re.compile(r"^\s*(https?://|www\.)", re.I),
    re.compile(r"^[A-Za-z0-9_/.\-]+$"),
]

TECH_PREFIXES = ("FIREBASE_", "Config.", "ADMIN_", "DB_", "MAGIC_")

# ------------------------------------------------------------------------------
# Casing utilities
# ------------------------------------------------------------------------------

def preserve_casing(src: str, dst: str) -> str:
    """Try to preserve capitalization style from src to dst."""
    if src.isupper():
        return dst.upper()
    if src.istitle():
        parts = dst.split(" ")
        if len(parts) == 1:
            return dst.capitalize()
        else:
            return parts[0].capitalize() + " " + " ".join(parts[1:])
    if src.islower():
        return dst.lower()
    return dst

# ------------------------------------------------------------------------------
# Protection / restoration
# ------------------------------------------------------------------------------

def protect_fragments(s: str) -> (str, List[str]):
    """Replace protected fragments with numbered tokens __P_i__ to avoid translating them."""
    protected = []
    text = s

    def _replacer(match):
        idx = len(protected)
        token = f"__P_{idx}__"
        protected.append(match.group(0))
        return token

    for name, rx in PROTECT_PATTERNS.items():
        text = rx.sub(_replacer, text)

    return text, protected

def restore_fragments(s: str, protected: List[str]) -> str:
    out = s
    for i, frag in enumerate(protected):
        out = out.replace(f"__P_{i}__", frag)
    return out

# ------------------------------------------------------------------------------
# Exception checker
# ------------------------------------------------------------------------------

def should_translate(text: str) -> bool:
    """Return True if the string literal likely contains user-facing text to translate."""
    for rx in SKIP_ENTIRE_LITERAL:
        if rx.search(text):
            return False
    has_alpha = bool(re.search(r"[A-Za-z]", text))
    if not has_alpha:
        return False
    prot_hits = 0
    for _, rx in PROTECT_PATTERNS.items():
        prot_hits += len(rx.findall(text))
    if prot_hits > 0 and (prot_hits * 6) > len(text):
        return False
    return True

# ------------------------------------------------------------------------------
# Core translation logic (dictionary-based)
# ------------------------------------------------------------------------------

WORD_RE = re.compile(r"([A-Za-z][A-Za-z'\-]+)")

def translate_text(text: str, translations: Dict[str, str]) -> str:
    """Translate only English words using a dictionary. Preserve protected fragments."""
    protected_text, protected = protect_fragments(text)

    def _word_sub(m: re.Match) -> str:
        word = m.group(1)
        if word.isupper() and word not in ("ON", "OFF"):
            return word
        if word in translations:
            return preserve_casing(word, translations[word])
        lower = word.lower()
        for k, v in translations.items():
            if k.lower() == lower:
                return preserve_casing(word, v)
        return word

    translated = WORD_RE.sub(_word_sub, protected_text)
    translated = restore_fragments(translated, protected)
    return translated

# ------------------------------------------------------------------------------
# File processing
# ------------------------------------------------------------------------------

def is_probably_message_var(lhs: str) -> bool:
    """Heuristic for message-like constant names."""
    if lhs.startswith(TECH_PREFIXES):
        return False
    if lhs.endswith(("_MSG", "_TITLE", "_TEXT", "_HINT")):
        return True
    if re.match(r"^[A-Z0-9_]+$", lhs):
        return True
    return False

ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*=\s*(?P<val>.+)$", re.DOTALL)

def translate_messages_file(file_path: str, translations: Dict[str, str], out_path: str = None) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    out_parts = []
    last_idx = 0
    changes = 0
    skipped = 0

    for m in STRING_RE.finditer(code):
        start, end = m.span()
        quote = m.group("quote")
        body = m.group("body")

        line_start = code.rfind("\n", 0, start) + 1
        line_prefix = code[line_start:start]
        lhs_name = None
        block_start = code.rfind("\n", 0, line_start) + 1
        block = code[block_start:end]
        m_assign = ASSIGNMENT_RE.search(block)
        if m_assign:
            lhs_name = m_assign.group(1)

        should = should_translate(body)
        if lhs_name and not is_probably_message_var(lhs_name):
            should = False

        if should:
            new_body = translate_text(body, translations)
            if new_body != body:
                changes += 1
                out_parts.append(code[last_idx:m.start()])
                out_parts.append(quote + new_body + quote)
                last_idx = m.end()
                orig_preview = body.replace("\n", "\\n")
                new_preview = new_body.replace("\n", "\\n")
                if len(orig_preview) > 120:
                    orig_preview = orig_preview[:117] + "..."
                if len(new_preview) > 120:
                    new_preview = new_preview[:117] + "..."
                print(f"[OK] Translated: {orig_preview} -> {new_preview}")
                continue

        skipped += 1
        out_parts.append(code[last_idx:m.start()])
        out_parts.append(code[m.start():m.end()])
        last_idx = m.end()

    out_parts.append(code[last_idx:])
    result = "".join(out_parts)

    if not out_path:
        base, ext = os.path.splitext(file_path)
        out_path = base + "_OUT" + ext

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\nDone. Translated: {changes}, Skipped: {skipped}")
    print(f"Written: {out_path}")

# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------

def load_lang_dict(lang: str) -> Dict[str, str]:
    lang = (lang or "").lower()
    if lang in LANG_MAP:
        # Return a copy to avoid accidental in-place mutation
        return dict(LANG_MAP[lang])
    # Unknown language -> empty dict (no-op unless user passes --dict)
    print(f"[WARN] No built-in dictionary for language '{lang}'. Using empty base.")
    return {}

def merge_custom_dict(base: Dict[str, str], json_path: str) -> Dict[str, str]:
    if not json_path:
        return base
    if not os.path.isfile(json_path):
        print(f"[WARN] Custom dictionary file not found: {json_path}")
        return base
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print(f"[WARN] Custom dictionary must be a JSON object of key:value.")
            return base
        # override / extend
        out = dict(base)
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, str):
                continue
            out[k] = v
        print(f"[OK] Custom dictionary merged: {json_path} ({len(data)} entries)")
        return out
    except Exception as e:
        print(f"[WARN] Failed to load custom dictionary: {e}")
        return base

def main():
    parser = argparse.ArgumentParser(description="Translate Telegram bot message strings in a Python file (safe, multi-language).")
    parser.add_argument("src", help="Input Python file path (e.g., messages_EN.py)")
    parser.add_argument("--out", help="Output file path (default: *_OUT.py)")
    parser.add_argument("--lang", required=True, help="Target language code (e.g., ru, ar, hi). Unknown -> empty base dict.")
    parser.add_argument("--dict", dest="custom_dict", help="Custom JSON dictionary to merge/override (key: EN word/phrase, value: target translation).")
    args = parser.parse_args()

    if not os.path.isfile(args.src):
        print(f"ERROR: file not found: {args.src}")
        sys.exit(1)

    base_dict = load_lang_dict(args.lang)
    trans_dict = merge_custom_dict(base_dict, args.custom_dict)

    translate_messages_file(args.src, trans_dict, out_path=args.out)

if __name__ == "__main__":
    main()
