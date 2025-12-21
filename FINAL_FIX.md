# ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ - 3 команды

## 1. В .env файле - удалите или закомментируйте VITE_API_URL:

```env
# VITE_API_URL=http://202.148.54.41:8009  <-- закомментируйте или удалите эту строку
```

## 2. Пересоберите фронтенд:

```bash
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend
sudo docker-compose -f docker-compose.prod.yml up -d frontend
```

## 3. Перезапустите app (чтобы CORS точно работал):

```bash
sudo docker-compose -f docker-compose.prod.yml restart app
```

## Готово!

Фронтенд будет использовать `/api` (относительный путь), nginx проксирует на `app:8000`.
CORS не нужен, так как запросы идут через nginx на тот же домен.






