#!/bin/bash

# Файл с результатами
RESULTS_FILE="proxy_check_results.txt"

# Очищаем файл результатов
echo "Результаты проверки прокси - $(date)" > $RESULTS_FILE
echo "========================================" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Список прокси
proxies=(
    "http://topfriendcorp_yandex_ru:66a204aa3a@85.31.51.47:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@45.134.31.201:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@176.53.166.31:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@84.54.8.184:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@185.64.251.84:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@45.90.199.104:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@45.91.10.208:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@5.182.119.188:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@2.56.114.31:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@37.16.79.237:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@5.172.181.235:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@37.77.146.158:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@193.142.242.145:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@193.192.1.184:30010"
    "http://topfriendcorp_yandex_ru:66a204aa3a@193.142.249.205:30010"
)

# Функция проверки прокси
check_proxy() {
    local proxy=$1
    local num=$2
    
    echo "[$num/15] Проверка: ${proxy:0:60}..."
    
    # Получаем IP через прокси
    ip_result=$(curl -x "$proxy" --connect-timeout 10 --max-time 15 -s https://httpbin.org/ip 2>&1)
    ip_status=$?
    
    if [ $ip_status -eq 0 ]; then
        ip=$(echo "$ip_result" | grep -oP '"origin":\s*"\K[^"]+' || echo "N/A")
        echo "  ✅ Прокси работает, IP: $ip"
    else
        ip="НЕ РАБОТАЕТ"
        echo "  ❌ Прокси не работает"
    fi
    
    # Проверка Google
    google_result=$(curl -x "$proxy" --connect-timeout 10 --max-time 15 -s -o /dev/null -w "%{http_code}" https://www.google.com 2>&1)
    google_status=$?
    if [ $google_status -eq 0 ] && [ "$google_result" != "000" ] && [ "$google_result" != "" ]; then
        google="✅ ($google_result)"
    else
        google="❌"
    fi
    
    # Проверка Telegram
    telegram_result=$(curl -x "$proxy" --connect-timeout 10 --max-time 15 -s -o /dev/null -w "%{http_code}" https://telegram.org 2>&1)
    telegram_status=$?
    if [ $telegram_status -eq 0 ] && [ "$telegram_result" != "000" ] && [ "$telegram_result" != "" ]; then
        telegram="✅ ($telegram_result)"
    else
        telegram="❌"
    fi
    
    # Проверка Instagram
    instagram_result=$(curl -x "$proxy" --connect-timeout 10 --max-time 15 -s -o /dev/null -w "%{http_code}" -H "User-Agent: Mozilla/5.0" https://www.instagram.com 2>&1)
    instagram_status=$?
    if [ $instagram_status -eq 0 ] && [ "$instagram_result" != "000" ] && [ "$instagram_result" != "" ]; then
        instagram="✅ ($instagram_result)"
    else
        instagram="❌"
    fi
    
    # Записываем в файл
    echo "Прокси #$num: ${proxy:0:60}..." >> $RESULTS_FILE
    echo "  IP: $ip" >> $RESULTS_FILE
    echo "  Google: $google" >> $RESULTS_FILE
    echo "  Telegram: $telegram" >> $RESULTS_FILE
    echo "  Instagram: $instagram" >> $RESULTS_FILE
    echo "" >> $RESULTS_FILE
    
    # Выводим результат
    echo "  Google: $google | Telegram: $telegram | Instagram: $instagram"
    echo ""
}

# Проверяем все прокси
counter=1
for proxy in "${proxies[@]}"; do
    check_proxy "$proxy" $counter
    counter=$((counter + 1))
    sleep 1  # Небольшая задержка между проверками
done

# Итоговая статистика
echo "" >> $RESULTS_FILE
echo "========================================" >> $RESULTS_FILE
echo "Проверка завершена: $(date)" >> $RESULTS_FILE

echo ""
echo "Результаты сохранены в файл: $RESULTS_FILE"
echo "Просмотр результатов: cat $RESULTS_FILE"



