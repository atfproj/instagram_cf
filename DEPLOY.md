# Инструкция по деплою на продакшен

## Подготовка

### 1. Генерация ключей безопасности

```bash
python generate_keys.py
```

Скопируйте сгенерированные ключи в `.env` файл.

### 2. Настройка переменных окружения

Скопируйте `env.example` в `.env`:

```bash
cp env.example .env
```

Заполните все переменные:
- `POSTGRES_PASSWORD` - надежный пароль для БД
- `SECRET_KEY` - из `generate_keys.py`
- `ENCRYPTION_KEY` - из `generate_keys.py`
- `DEEPSEEK_API_KEY` - ваш API ключ DeepSeek
- `CORS_ORIGINS` - список разрешенных доменов через запятую (например: `https://yourdomain.com,https://www.yourdomain.com`)
- `DEBUG=False`
- `VITE_API_URL` - URL вашего API (например: `https://api.yourdomain.com`)

### 3. Настройка CORS

В `.env` добавьте:
```
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Деплой

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Используем production конфигурацию
docker compose -f docker-compose.prod.yml up -d --build

# Применить миграции
docker compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Вариант 2: Ручной деплой

1. Установите зависимости
2. Настройте PostgreSQL и Redis
3. Примените миграции: `alembic upgrade head`
4. Запустите приложение: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4`
5. Запустите Celery worker: `celery -A backend.celery_app.config.celery_app worker --loglevel=info`

## Проверка

1. Проверьте health endpoint: `curl http://localhost:8000/health`
2. Проверьте логи: `docker compose -f docker-compose.prod.yml logs -f`
3. Проверьте доступность фронтенда

## Обновление

```bash
# Остановить сервисы
docker compose -f docker-compose.prod.yml down

# Обновить код
git pull

# Пересобрать и запустить
docker compose -f docker-compose.prod.yml up -d --build

# Применить новые миграции (если есть)
docker compose -f docker-compose.prod.yml exec app alembic upgrade head
```

## Бэкапы

### PostgreSQL

```bash
# Создать бэкап
docker compose -f docker-compose.prod.yml exec db pg_dump -U instagram_cf instagram_cf > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из бэкапа
docker compose -f docker-compose.prod.yml exec -T db psql -U instagram_cf instagram_cf < backup.sql
```

## Мониторинг

- Логи: `docker compose -f docker-compose.prod.yml logs -f [service_name]`
- Health checks: `curl http://localhost:8000/health`
- Статус контейнеров: `docker compose -f docker-compose.prod.yml ps`

## Безопасность

- ✅ Используйте HTTPS (настройте nginx reverse proxy)
- ✅ Ограничьте доступ к портам БД и Redis (не публикуйте наружу)
- ✅ Регулярно обновляйте зависимости
- ✅ Настройте firewall
- ✅ Используйте managed БД если возможно
- ✅ Настройте автоматические бэкапы







