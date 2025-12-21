# Простая настройка для домена cf.atfmedia.ru

## Без внешнего nginx - используем только Docker

### 1. Обновите .env:

```env
# CORS - разрешаем все (nginx proxy внутри Docker обработает)
CORS_ORIGINS=*

# VITE_API_URL - не указывайте (используем относительные пути через nginx)
# VITE_API_URL=
```

### 2. Пересоберите фронтенд:

```bash
sudo docker-compose -f docker-compose.prod.yml build --no-cache frontend
sudo docker-compose -f docker-compose.prod.yml up -d
```

### 3. Настройте DNS:

В панели управления доменом `cf.atfmedia.ru` укажите:
- **A запись**: `cf.atfmedia.ru` → `202.148.54.41`

### 4. Варианты доступа:

**Вариант A: С портом (работает сразу)**
- Фронтенд: `http://cf.atfmedia.ru:3001`
- API: `http://cf.atfmedia.ru:8009/api`

**Вариант B: Без порта (нужен внешний прокси)**

Если хотите `https://cf.atfmedia.ru` без порта, нужен внешний nginx или cloudflare proxy.

### 5. Если используете Cloudflare:

1. Добавьте домен в Cloudflare
2. Включите "Proxy" (оранжевое облако)
3. Cloudflare автоматически проксирует на ваш IP:3001

### 6. Проверка:

```bash
# Проверить что фронтенд работает
curl http://localhost:3001

# Проверить что API проксируется через nginx
curl http://localhost:3001/api/health
```

## Готово!

После этого:
- Фронтенд: `http://cf.atfmedia.ru:3001` (или через Cloudflare без порта)
- API автоматически проксируется через `/api` → nginx → `app:8000`
- CORS не нужен (запросы через nginx)






