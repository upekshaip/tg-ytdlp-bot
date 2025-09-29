#!/bin/bash

# Папка, где выполняется скрипт
cd /mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW || exit 1

echo "[$(date)] Stopping and removing old container..."
docker stop bgutil-provider >/dev/null 2>&1
docker rm bgutil-provider >/dev/null 2>&1

echo "[$(date)] Pulling latest image..."
docker pull brainicism/bgutil-ytdlp-pot-provider

echo "[$(date)] Starting new container..."
docker run -d \
  --name bgutil-provider \
  -p 4416:4416 \
  --init \
  --restart unless-stopped \
  brainicism/bgutil-ytdlp-pot-provider

echo "[$(date)] Done."
