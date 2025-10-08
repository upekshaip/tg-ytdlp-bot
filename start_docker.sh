#!/bin/bash

# Скрипт для запуска Docker в WSL
# Использование: ./start_docker.sh

echo "Проверяем статус Docker..."

# Проверяем, запущен ли уже Docker
if docker ps >/dev/null 2>&1; then
    echo "✅ Docker уже запущен и работает"
    docker ps
    exit 0
fi

echo "Docker не запущен. Запускаем..."

# Проверяем, есть ли уже запущенный dockerd процесс
if pgrep dockerd >/dev/null; then
    echo "⚠️  Процесс dockerd уже запущен, но Docker не отвечает"
    echo "Попытка перезапуска..."
    sudo pkill dockerd
    sleep 2
fi

# Запускаем Docker daemon в фоновом режиме
echo "Запускаем Docker daemon..."
sudo dockerd > /dev/null 2>&1 &

# Ждем запуска
echo "Ожидаем запуска Docker..."
for i in {1..10}; do
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker успешно запущен!"
        docker ps
        exit 0
    fi
    echo "Попытка $i/10..."
    sleep 2
done

echo "❌ Не удалось запустить Docker"
exit 1
