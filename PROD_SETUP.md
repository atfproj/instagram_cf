# Настройка для продакшена

## Проблема с CORS и API URL

Если фронтенд пытается обратиться к `localhost:8009`, это означает, что:
1. `VITE_API_URL` не установлен или установлен неправильно
2. Или фронтенд не использует nginx proxy

## Решение 1: Использование nginx proxy (рекомендуется)

Если фронтенд и бэкенд на одном сервере:

1. **В .env файле НЕ указывайте VITE_API_URL** (или оставьте пустым):
   ```env
   # VITE_API_URL не указываем - используем относительные пути
   ```

2. **Пересоберите фронтенд:**
   ```bash
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d frontend
   ```

3. **Nginx автоматически проксирует `/api` → `http://app:8000`**

## Решение 2: Прямые запросы к API

Если фронтенд и бэкенд на разных серверах:

1. **В .env файле укажите полный URL бэкенда:**
   ```env
   VITE_API_URL=http://202.148.54.41:8009
   # или
   VITE_API_URL=http://your-backend-domain.com:8009
   ```

2. **В .env файле укажите CORS_ORIGINS:**
   ```env
   CORS_ORIGINS=http://202.148.54.41:3001,http://your-frontend-domain.com
   ```

3. **Пересоберите фронтенд и перезапустите бэкенд:**
   ```bash
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d
   ```

## Проверка

1. **Проверьте, какой URL использует фронтенд:**
   - Откройте DevTools → Console
   - Должно быть: `API_BASE_URL: /api` (для nginx proxy) или `API_BASE_URL: http://...` (для прямых запросов)

2. **Проверьте запросы в Network:**
   - Должны идти на `/api/...` (относительный путь) или на полный URL бэкенда

3. **Проверьте CORS заголовки:**
   ```bash
   curl -H "Origin: http://202.148.54.41:3001" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS \
        http://202.148.54.41:8009/api/auth/login \
        -v
   ```

## Текущая проблема из скриншота

Фронтенд на `http://202.148.54.41:3001` пытается обратиться к `http://localhost:8009`.

**Быстрое исправление:**

1. Добавьте в `.env`:
   ```env
   VITE_API_URL=http://202.148.54.41:8009
   CORS_ORIGINS=http://202.148.54.41:3001
   ```

2. Пересоберите:
   ```bash
   docker compose -f docker-compose.prod.yml build frontend app
   docker compose -f docker-compose.prod.yml up -d
   ```

Или используйте nginx proxy (лучше для продакшена).






