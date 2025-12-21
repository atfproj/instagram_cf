# Быстрое исправление CORS на продакшене

## Шаги для исправления:

### 1. Добавьте CORS_ORIGINS в .env файл на проде:

```bash
# Если фронтенд и бэкенд на одном домене
CORS_ORIGINS=*

# Или если на разных доменах
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### 2. Пересоберите и перезапустите сервисы:

```bash
# Пересобрать фронтенд с nginx конфигурацией
docker compose -f docker-compose.prod.yml build frontend

# Перезапустить все сервисы
docker compose -f docker-compose.prod.yml up -d

# Проверить логи
docker compose -f docker-compose.prod.yml logs app | grep CORS
docker compose -f docker-compose.prod.yml logs frontend
```

### 3. Если используете nginx proxy (рекомендуется):

Фронтенд уже настроен для проксирования запросов через nginx.
Убедитесь, что:
- `VITE_API_URL` в docker-compose.prod.yml пустой или не указан (для относительных путей)
- Или установите `VITE_API_URL=/api` для использования nginx proxy

### 4. Проверка работы:

```bash
# Проверить CORS заголовки
curl -H "Origin: http://your-frontend-domain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -X OPTIONS \
     http://your-backend-domain.com/api/auth/login \
     -v
```

Должны вернуться заголовки:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH`
- `Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With`

### 5. Если проблема сохраняется:

1. Проверьте логи бэкенда:
   ```bash
   docker compose -f docker-compose.prod.yml logs app --tail=50
   ```

2. Проверьте логи фронтенда:
   ```bash
   docker compose -f docker-compose.prod.yml logs frontend --tail=50
   ```

3. Проверьте в браузере DevTools → Network → посмотрите на запросы к API

4. Убедитесь, что порты правильно проброшены и доступны






