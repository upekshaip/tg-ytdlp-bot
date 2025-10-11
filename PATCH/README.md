# PATCH Module

Эта папка содержит глобальные патчи для проекта.

## Файлы:

- `GLOBAL_MESSAGES_PATCH.py` - Глобальный патч для предотвращения ошибки 'name messages is not defined'
- `__init__.py` - Автоматически применяет патчи при импорте модуля
- `run_patch.py` - Скрипт для запуска патча отдельно

## Использование:

### Автоматическое применение:
```python
import PATCH  # Патч применится автоматически
```

### Ручное применение:
```python
from PATCH.GLOBAL_MESSAGES_PATCH import apply_global_messages_patch
apply_global_messages_patch()
```

### Запуск отдельно:
```bash
python3 PATCH/run_patch.py
```

## Что делает патч:

1. **Предотвращает ошибку** `name 'messages' is not defined`
2. **Добавляет безопасные функции** в глобальное пространство имен
3. **Гарантирует** что объект `Messages` всегда доступен
4. **Работает** во всех файлах проекта автоматически
