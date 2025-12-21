#!/bin/bash
# Команды для проверки состояния на проде

echo "=== 1. Статус контейнеров ==="
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|instagram_cf"

echo ""
echo "=== 2. Логи app (последние 30 строк) ==="
sudo docker logs instagram_cf_app --tail=30

echo ""
echo "=== 3. Логи frontend (последние 20 строк) ==="
sudo docker logs instagram_cf_frontend --tail=20

echo ""
echo "=== 4. Проверка .env (DATABASE_URL и REDIS_URL) ==="
grep -E "DATABASE_URL|REDIS_URL|CELERY_BROKER|CELERY_RESULT|VITE_API_URL|CORS_ORIGINS" .env | head -10

echo ""
echo "=== 5. Проверка подключения app к db ==="
sudo docker exec instagram_cf_app ping -c 1 db 2>&1 | head -3

echo ""
echo "=== 6. Проверка CORS в app ==="
sudo docker exec instagram_cf_app python -c "import os; print('CORS_ORIGINS:', os.getenv('CORS_ORIGINS', 'NOT SET'))" 2>&1

echo ""
echo "=== 7. Проверка health endpoint ==="
curl -s http://localhost:8009/health || echo "Health check failed"

echo ""
echo "=== 8. Проверка nginx в frontend ==="
sudo docker exec instagram_cf_frontend cat /etc/nginx/conf.d/default.conf | grep -A 5 "location /api" | head -10






