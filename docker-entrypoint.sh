#!/bin/bash
set -e

# Функция для обработки сигналов завершения
cleanup() {
    echo "Получен сигнал завершения, останавливаем процессы..."
    kill $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    wait $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

# Устанавливаем обработчики сигналов
trap cleanup SIGTERM SIGINT

# Получаем порт из конфига (по умолчанию 5555)
DASHBOARD_PORT=$(python -c "from CONFIG.config import Config; print(getattr(Config, 'DASHBOARD_PORT', 5555))" 2>/dev/null || echo "5555")

# Запускаем бота в фоне
echo "Запуск Telegram бота..."
python magic.py &
BOT_PID=$!

# Запускаем панель управления в фоне
echo "Запуск панели управления на порту ${DASHBOARD_PORT}..."
python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port ${DASHBOARD_PORT} &
DASHBOARD_PID=$!

echo "Бот и панель управления запущены"
echo "Панель доступна на http://localhost:${DASHBOARD_PORT}"

# Ждем завершения процессов
wait $BOT_PID $DASHBOARD_PID

