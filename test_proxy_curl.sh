#!/bin/bash

PROXY="http://hZEYrh:8zfv7m@192.241.122.132:8000"

echo "=========================================="
echo "Проверка прокси через curl"
echo "=========================================="
echo ""

echo "📸 Instagram:"
curl -x "$PROXY" \
  --connect-timeout 10 \
  --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -s -o /dev/null \
  -w "  HTTP код: %{http_code}\n  Время: %{time_total}s\n  Размер: %{size_download} bytes\n" \
  https://www.instagram.com
echo ""

echo "📘 Facebook:"
curl -x "$PROXY" \
  --connect-timeout 10 \
  --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -s -o /dev/null \
  -w "  HTTP код: %{http_code}\n  Время: %{time_total}s\n  Размер: %{size_download} bytes\n" \
  https://www.facebook.com
echo ""

echo "💼 LinkedIn:"
curl -x "$PROXY" \
  --connect-timeout 10 \
  --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -s -o /dev/null \
  -w "  HTTP код: %{http_code}\n  Время: %{time_total}s\n  Размер: %{size_download} bytes\n" \
  https://www.linkedin.com
echo ""

echo "🌐 IP через прокси (httpbin.org):"
curl -x "$PROXY" \
  --connect-timeout 5 \
  --max-time 10 \
  -s \
  https://httpbin.org/ip | grep -o '"origin":"[^"]*"' | cut -d'"' -f4
echo ""

echo "=========================================="


