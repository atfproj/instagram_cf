# ИСПРАВЛЕНИЕ ВСЕГО - ВЫПОЛНИТЕ ПО ПОРЯДКУ

## 1. Исправьте .env файл:

Удалите дубликаты и закомментируйте VITE_API_URL:

```env
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CORS_ORIGINS=*
# VITE_API_URL=http://202.148.54.41:8009  <-- ЗАКОММЕНТИРУЙТЕ ЭТУ СТРОКУ
```

**УДАЛИТЕ эти строки (дубликаты с localhost):**
- `CELERY_BROKER_URL=redis://localhost:6383/0`
- `CELERY_RESULT_BACKEND=redis://localhost:6383/0`

## 2. Пересоберите и перезапустите:

```bash
# Пересобрать фронтенд
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend

# Перезапустить все
sudo docker-compose -f docker-compose.prod.yml up -d

# Проверить статус
sudo docker ps | grep instagram_cf
```

## 3. Проверьте что работает:

```bash
# Проверить health
curl http://localhost:8009/health

# Проверить что фронтенд проксирует /api
curl http://localhost:3001/api/health
```

## Готово!

После этого:
- Фронтенд будет использовать `/api` (nginx proxy)
- CORS не нужен (запросы через nginx)
- App будет healthy






