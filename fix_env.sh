#!/bin/bash
# Скрипт для исправления .env файла для Docker

echo "Исправляю .env файл для Docker..."

# Создаём backup
cp .env .env.backup

# Заменяем localhost на имена сервисов
sed -i 's/@localhost:5436/@db:5432/g' .env
sed -i 's|redis://localhost:6383|redis://redis:6379|g' .env

echo "Готово! Изменения:"
echo "- localhost:5436 → db:5432 (для БД)"
echo "- localhost:6383 → redis:6379 (для Redis)"
echo ""
echo "Backup сохранён в .env.backup"
echo ""
echo "Теперь перезапустите:"
echo "sudo docker-compose -f docker-compose.prod.yml restart app celery_worker"






