# Исправление проблемы с CORS на продакшене

## Проблема
Запросы с фронтенда не доходят до бэкенда из-за проблем с CORS.

## Решения

### Вариант 1: Использование nginx proxy (рекомендуется)

Если фронтенд и бэкенд на одном домене, используйте nginx для проксирования запросов.

1. **Настройте nginx.conf** (уже добавлен в `frontend/nginx.conf`)
   - Все запросы к `/api` проксируются на `http://app:8000`
   - CORS обрабатывается на уровне nginx

2. **В docker-compose.prod.yml** фронтенд уже настроен с nginx

3. **На фронтенде** используйте относительные пути:
   ```javascript
   // В frontend/src/api/client.js
   const API_BASE_URL = '' // Пустая строка для относительных путей
   ```

### Вариант 2: Настройка CORS_ORIGINS

Если фронтенд и бэкенд на разных доменах:

1. **Добавьте в .env файл:**
   ```env
   CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
   ```

2. **Убедитесь, что VITE_API_URL указывает на правильный URL бэкенда:**
   ```env
   VITE_API_URL=https://api.your-domain.com
   ```

3. **Пересоберите фронтенд:**
   ```bash
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d frontend
   ```

### Вариант 3: Временное решение для тестирования

Для быстрого тестирования можно временно разрешить все источники:

1. **В .env установите:**
   ```env
   CORS_ORIGINS=*
   ```

2. **Перезапустите бэкенд:**
   ```bash
   docker compose -f docker-compose.prod.yml restart app
   ```

## Проверка

1. **Проверьте логи бэкенда:**
   ```bash
   docker compose -f docker-compose.prod.yml logs app | grep CORS
   ```

2. **Проверьте CORS заголовки:**
   ```bash
   curl -H "Origin: http://your-frontend-domain.com" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type,Authorization" \
        -X OPTIONS \
        http://your-backend-domain.com/api/auth/login \
        -v
   ```

3. **Проверьте в браузере:**
   - Откройте DevTools → Network
   - Посмотрите на запросы к API
   - Проверьте заголовки ответа (должны быть Access-Control-Allow-*)

## Рекомендуемая конфигурация для продакшена

1. **Фронтенд и бэкенд на одном домене через nginx:**
   - Фронтенд: `https://yourdomain.com`
   - API: `https://yourdomain.com/api`
   - Используйте nginx proxy (уже настроено)

2. **Или на разных поддоменах:**
   - Фронтенд: `https://app.yourdomain.com`
   - API: `https://api.yourdomain.com`
   - Настройте CORS_ORIGINS в .env






