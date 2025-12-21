#!/bin/bash

# Точное повторение PHP скрипта через curl

PROXY="192.241.122.132:8000"
PROXY_USER="hZEYrh"
PROXY_PASS="8zfv7m"
URL="https://www.instagram.com/s_bezrukov"

# Создаем временный файл для cookies (как в PHP)
COOKIE_FILE=$(mktemp insta_cookies_XXXXXX)

echo "Запрос к: $URL"
echo "Прокси: $PROXY"
echo "Cookies файл: $COOKIE_FILE"
echo "="*60

curl -x "http://$PROXY_USER:$PROXY_PASS@$PROXY" \
  --insecure \
  --connect-timeout 10 \
  --max-time 15 \
  -L \
  -b "$COOKIE_FILE" \
  -c "$COOKIE_FILE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" \
  -H "Accept: */*" \
  -H "Accept-Language: en-US,en;q=0.5" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -s \
  -w "\n\nHTTP код: %{http_code}\nВремя: %{time_total}s\nРазмер: %{size_download} bytes\nURL финальный: %{url_effective}\n" \
  "$URL" > /tmp/instagram_response.html

HTTP_CODE=$(curl -x "http://$PROXY_USER:$PROXY_PASS@$PROXY" \
  --insecure \
  --connect-timeout 10 \
  --max-time 15 \
  -L \
  -b "$COOKIE_FILE" \
  -c "$COOKIE_FILE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" \
  -H "Accept: */*" \
  -H "Accept-Language: en-US,en;q=0.5" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -H "Connection: keep-alive" \
  -H "Upgrade-Insecure-Requests: 1" \
  -s -o /dev/null \
  -w "%{http_code}" \
  "$URL")

echo "HTTP код: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Успешно!"
  # Пробуем найти JSON как в PHP
  if grep -q '<script type="application/ld+json">' /tmp/instagram_response.html; then
    echo "✅ Найден JSON блок"
  fi
else
  echo "❌ Ошибка: $HTTP_CODE"
fi

# Удаляем временный файл
rm -f "$COOKIE_FILE"
rm -f /tmp/instagram_response.html


