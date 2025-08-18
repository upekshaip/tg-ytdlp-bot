#!/bin/bash

cd /mnt/c/Users/chelaxian/Desktop/tg-ytdlp-NEW/TXT || exit 1

HOST_URL="https://free-vpn.ratu.sh/files/porn/porn_domains.txt"
HOST_URL_2="https://free-vpn.ratu.sh/files/porn/porn_keywords.txt"
#HOSTS_URL="https://raw.githubusercontent.com/4skinSkywalker/Anti-Porn-HOSTS-File/refs/heads/master/>
SUPPORTED_URL="https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md"

# Получаем порнодомены
#curl -s "$HOSTS_URL" | grep '^0\.0\.0\.0' | awk '{print $2}' > porn_domains.txt
rm -rf porn_domains.txt
rm -rf porn_keywords.txt
wget $HOST_URL
wget $HOST_URL_2

# Добавляем кастомные списки
#for CUSTOM_FILE in custom_porn_domains.txt custom_porn.txt; do
#  [ -f "$CUSTOM_FILE" ] && cat "$CUSTOM_FILE" >> porn_domains.txt
#done

# Удаляем дубликаты
sort -u porn_domains.txt -o porn_domains.txt

# Удаляем домены и поддомены из белого списка и clean_not_porn
if [ -f whitelist_porn.txt ] || [ -f clean_not_porn.txt ]; then
  cp porn_domains.txt porn_domains_filtered.txt
  for WHITELIST_FILE in whitelist_porn.txt clean_not_porn.txt; do
    if [ -f "$WHITELIST_FILE" ]; then
      while IFS= read -r domain; do
        # Пропускаем пустые строки
        [ -z "$domain" ] && continue
        # Удаляем домен и все поддомены
        sed -i "/^$domain$/d" porn_domains_filtered.txt
        sed -i "/\.$domain$/d" porn_domains_filtered.txt
      done < "$WHITELIST_FILE"
    fi
  done
  mv porn_domains_filtered.txt porn_domains.txt
fi

# Скачиваем список поддерживаемых сайтов yt-dlp
rm -rf supported_sites.txt
curl -s "$SUPPORTED_URL" \
  | grep '^ - \*\*' \
  | sed 's/^ - \*\*//;s/\*\*:.*//;s/\*\*$//' \
  | sed 's/:.*$//' \
  | sed 's/ .*//' \
  | sed '/^$/d' \
  > supported_sites.txt

sort -u supported_sites.txt -o supported_sites.txt
