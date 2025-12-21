# Исправление DATABASE_URL для продакшена

## Проблема
Бэкенд не может подключиться к БД, потому что в `.env` файле указан `localhost` вместо имени сервиса Docker.

## Решение

### 1. Проверьте `.env` файл на проде

Убедитесь, что в `.env` файле указаны правильные URL для Docker:

```env
# ДЛЯ DOCKER (продакшен) - используйте имена сервисов
DATABASE_URL=postgresql://instagram_cf:YOUR_PASSWORD@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# НЕ используйте localhost в Docker!
# ❌ DATABASE_URL=postgresql://instagram_cf:password@localhost:5436/instagram_cf
# ✅ DATABASE_URL=postgresql://instagram_cf:password@db:5432/instagram_cf
```

### 2. Важно:
- **В Docker:** используйте `db:5432` (имя сервиса и внутренний порт)
- **Без Docker:** используйте `localhost:5436` (внешний порт)

### 3. После исправления:

```bash
# Перезапустить бэкенд
sudo docker-compose -f docker-compose.prod.yml restart app celery_worker

# Проверить логи
sudo docker-compose -f docker-compose.prod.yml logs app --tail=20
```

### 4. Также проверьте CORS:

В `.env` должно быть:
```env
CORS_ORIGINS=http://202.148.54.41:3001,http://202.148.54.41:8009
```

Или для тестирования:
```env
CORS_ORIGINS=*
```

### 5. Проверка подключения:

```bash
# Проверить, что контейнер app видит контейнер db
sudo docker exec instagram_cf_app ping -c 1 db

# Проверить подключение к БД из контейнера app
sudo docker exec instagram_cf_app python -c "from app.core.database import engine; engine.connect()"
```






