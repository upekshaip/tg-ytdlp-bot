# Исправления проблемы "Too many open files"

## Описание проблемы

Бот испытывал ошибку `OSError: [Errno 24] Too many open files`, которая возникала из-за неправильного управления HTTP соединениями с Firebase. Каждый HTTP запрос создавал новое соединение, которое не закрывалось должным образом, что приводило к исчерпанию файловых дескрипторов.

## Внесенные исправления

### 1. Использование сессий requests

**Файлы:** `DATABASE/firebase_init.py`, `DATABASE/download_firebase.py`

- Заменил прямые вызовы `requests.get()`, `requests.post()` на использование `Session()`
- Добавил правильное управление жизненным циклом соединений
- Реализовал автоматическое закрытие сессий при завершении работы

### 2. Настройка пула соединений

**Файлы:** `DATABASE/firebase_init.py`, `DATABASE/download_firebase.py`

```python
adapter = HTTPAdapter(
    pool_connections=10,  # Количество пулов соединений
    pool_maxsize=20,      # Максимальное количество соединений в пуле
    max_retries=3,        # Количество повторных попыток
    pool_block=False      # Не блокировать при заполнении пула
)
```

### 3. Правильное закрытие соединений

**Файлы:** `DATABASE/firebase_init.py`, `HELPERS/filesystem_hlp.py`, `DATABASE/cache_db.py`

- Добавил метод `close()` в `RestDBAdapter`
- Реализовал автоматическое закрытие соединений при завершении работы
- Добавил обработчики сигналов для graceful shutdown

### 4. Обработка сигналов завершения

**Файлы:** `magic.py`, `HELPERS/filesystem_hlp.py`

- Добавил обработчики сигналов `SIGINT` и `SIGTERM`
- Реализовал функцию `cleanup_on_exit()` для правильного закрытия соединений
- Зарегистрировал cleanup функцию в `atexit`

## Структура исправлений

```
DATABASE/
├── firebase_init.py          # Основные исправления Firebase
├── download_firebase.py      # Исправления для скачивания дампа
└── cache_db.py              # Функции закрытия соединений

HELPERS/
└── filesystem_hlp.py        # Обработчики сигналов

magic.py                     # Основной файл с обработчиками завершения
test_connections.py          # Тестовый скрипт
```

## Ключевые изменения

### RestDBAdapter (firebase_init.py)

```python
class RestDBAdapter:
    def __init__(self, ...):
        # Создание сессии с пулом соединений
        self._session = Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
    
    def close(self):
        """Явное закрытие сессии"""
        if hasattr(self, '_session'):
            self._session.close()
    
    def __del__(self):
        """Автоматическое закрытие при уничтожении объекта"""
        self.close()
```

### Обработка сигналов (magic.py)

```python
def cleanup_on_exit():
    """Функция очистки при завершении"""
    from DATABASE.cache_db import close_all_firebase_connections
    close_all_firebase_connections()

atexit.register(cleanup_on_exit)

def signal_handler(sig, frame):
    """Обработчик сигналов завершения"""
    cleanup_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

## Тестирование

Для проверки исправлений используйте тестовый скрипт:

```bash
python test_connections.py
```

Скрипт проверяет:
- Утечки файловых дескрипторов
- Правильное закрытие соединений
- Работу с одновременными запросами

## Мониторинг

Для мониторинга количества открытых файловых дескрипторов:

```bash
# Проверка лимитов
ulimit -n

# Мониторинг в реальном времени
watch -n 1 'ls /proc/$(pgrep -f magic.py)/fd | wc -l'
```

## Рекомендации

1. **Регулярный мониторинг**: Следите за количеством файловых дескрипторов
2. **Логирование**: Включите логирование для отслеживания соединений
3. **Тестирование**: Регулярно запускайте тестовый скрипт
4. **Обновления**: Следите за обновлениями библиотек requests и firebase_admin

## Результат

После внесения исправлений:
- ✅ Устранены утечки файловых дескрипторов
- ✅ Правильное управление HTTP соединениями
- ✅ Graceful shutdown при завершении работы
- ✅ Ограничение количества одновременных соединений
- ✅ Автоматическая очистка ресурсов
