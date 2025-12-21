# Запуск фронтенда на продакшене

## Текущая конфигурация

- **Внешний порт:** 3001 (свободен ✅)
- **Внутренний порт:** 80 (nginx)
- **URL:** `http://your-server:3001`

## Запуск

```bash
# Запустить только фронтенд
sudo docker-compose -f docker-compose.prod.yml up -d frontend

# Или перезапустить все
sudo docker-compose -f docker-compose.prod.yml up -d
```

## Проверка

```bash
# Проверить статус
sudo docker-compose -f docker-compose.prod.yml ps frontend

# Проверить логи
sudo docker-compose -f docker-compose.prod.yml logs frontend --tail=50

# Проверить доступность
curl http://localhost:3001
```

## Если порт 80 занят другим контейнером

Порт 80 занят `telegram_companion_nginx`, но это не проблема, так как:
- Фронтенд использует внешний порт **3001**
- Внутри контейнера nginx слушает на порту **80**
- Маппинг: `3001:80` означает "внешний 3001 → внутренний 80"

## Настройка API URL

Если фронтенд и бэкенд на одном сервере, используйте nginx proxy:
- В `.env` НЕ указывайте `VITE_API_URL` (или оставьте пустым)
- Nginx автоматически проксирует `/api` → `http://app:8000`

Если на разных серверах:
- В `.env` укажите: `VITE_API_URL=http://your-backend-server:8009`
- Пересоберите фронтенд: `docker-compose -f docker-compose.prod.yml build frontend`






