# Настройка для домена cf.atfmedia.ru

## 1. Обновите .env файл:

```env
# CORS - укажите ваш домен
CORS_ORIGINS=https://cf.atfmedia.ru,http://cf.atfmedia.ru

# VITE_API_URL - закомментируйте (будет использоваться nginx proxy)
# VITE_API_URL=https://cf.atfmedia.ru/api
```

## 2. Вариант A: Использовать nginx proxy (рекомендуется)

Если фронтенд и бэкенд на одном домене через nginx:

1. **В .env закомментируйте VITE_API_URL:**
```env
# VITE_API_URL=https://cf.atfmedia.ru/api
```

2. **Пересоберите фронтенд:**
```bash
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend
sudo docker-compose -f docker-compose.prod.yml up -d frontend
```

3. **Настройте внешний nginx (на хосте) для проксирования:**
```nginx
server {
    listen 80;
    server_name cf.atfmedia.ru;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cf.atfmedia.ru;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Фронтенд
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API (если нужно напрямую)
    location /api {
        proxy_pass http://localhost:8009;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 3. Вариант B: Прямые запросы (если нет внешнего nginx)

1. **В .env укажите:**
```env
VITE_API_URL=https://cf.atfmedia.ru/api
CORS_ORIGINS=https://cf.atfmedia.ru,http://cf.atfmedia.ru
```

2. **Пересоберите фронтенд:**
```bash
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend
sudo docker-compose -f docker-compose.prod.yml up -d
```

3. **Настройте внешний nginx для обоих портов:**
```nginx
# Фронтенд на порту 3001
# API на порту 8009
```

## 4. После настройки:

```bash
# Перезапустить все
sudo docker-compose -f docker-compose.prod.yml restart app frontend

# Проверить CORS
curl -H "Origin: https://cf.atfmedia.ru" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://cf.atfmedia.ru/api/auth/login \
     -v
```






