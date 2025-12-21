# ИСПРАВЛЕНИЕ .env файла - СДЕЛАЙТЕ ЭТО СЕЙЧАС

## В .env файле удалите/закомментируйте:

1. **Дубликаты CELERY (удалите строки с localhost):**
```env
# УДАЛИТЕ ЭТИ СТРОКИ:
CELERY_BROKER_URL=redis://localhost:6383/0
CELERY_RESULT_BACKEND=redis://localhost:6383/0

# ОСТАВЬТЕ ТОЛЬКО ЭТИ:
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

2. **VITE_API_URL (закомментируйте или удалите):**
```env
# VITE_API_URL=http://202.148.54.41:8009
```

## Итоговый .env должен содержать:

```env
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CORS_ORIGINS=*
# VITE_API_URL=http://202.148.54.41:8009  <-- закомментировано
```

## После исправления выполните:

```bash
# 1. Пересобрать фронтенд
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend

# 2. Перезапустить все
sudo docker-compose -f docker-compose.prod.yml up -d

# 3. Проверить статус
sudo docker ps | grep instagram_cf
```






