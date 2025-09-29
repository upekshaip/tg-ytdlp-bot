#!/bin/bash

# Папка назначения
DEST_DIR="/mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW"
BIN_NAME="yt-dlp"
ARCHIVE_NAME="yt-dlp_linux"

# Получаем ссылку на последний релиз yt-dlp для amd64
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest | \
  grep browser_download_url | grep $ARCHIVE_NAME | cut -d '"' -f 4)

# Проверка: ссылка найдена
if [[ -z "$DOWNLOAD_URL" ]]; then
  echo "Ошибка: не удалось получить ссылку на $ARCHIVE_NAME"
  exit 1
fi

# Скачиваем бинарник
curl -L "$DOWNLOAD_URL" -o "$DEST_DIR/$ARCHIVE_NAME"

# Переименовываем и даём права
mv "$DEST_DIR/$ARCHIVE_NAME" "$DEST_DIR/$BIN_NAME"
chmod 777 "$DEST_DIR/$BIN_NAME"

echo "yt-dlp обновлён успешно."
