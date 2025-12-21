# Установка и настройка nginx на сервере

## 1. Установите nginx:

```bash
sudo apt update
sudo apt install nginx -y
```

## 2. Создайте конфигурацию для cf.atfmedia.ru:

```bash
sudo nano /etc/nginx/sites-available/cf.atfmedia.ru
```

## 3. Вставьте эту конфигурацию:

```nginx
# Редирект HTTP на HTTPS
server {
    listen 80;
    server_name cf.atfmedia.ru;
    return 301 https://$server_name$request_uri;
}

# HTTPS конфигурация
server {
    listen 443 ssl http2;
    server_name cf.atfmedia.ru;

    # SSL сертификаты (используйте Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/cf.atfmedia.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cf.atfmedia.ru/privkey.pem;

    # Проксирование фронтенда
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API уже проксируется через nginx в Docker контейнере фронтенда
    # Но можно и напрямую:
    # location /api {
    #     proxy_pass http://localhost:8009;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #     proxy_set_header X-Forwarded-Proto $scheme;
    # }
}
```

## 4. Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/cf.atfmedia.ru /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка конфигурации
sudo systemctl reload nginx
```

## 5. Если нужен SSL (Let's Encrypt):

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d cf.atfmedia.ru
```

## 6. Проверьте статус:

```bash
sudo systemctl status nginx
```

## Готово!

После этого:
- `https://cf.atfmedia.ru` → фронтенд (порт 3001)
- `/api` → автоматически проксируется на бэкенд через nginx в Docker






