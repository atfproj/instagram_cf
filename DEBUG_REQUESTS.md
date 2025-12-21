# Диагностика: запросы не доходят до бэка

## Команды для проверки:

### 1. Проверьте логи nginx во фронтенде (видит ли запросы к /api):

```bash
sudo docker logs instagram_cf_frontend --tail=50 | grep -E "/api|error|failed"
```

### 2. Проверьте логи бэкенда (получает ли запросы):

```bash
sudo docker logs instagram_cf_app --tail=50 | grep -E "POST|GET|/api"
```

### 3. Проверьте nginx конфигурацию во фронтенде:

```bash
sudo docker exec instagram_cf_frontend cat /etc/nginx/conf.d/default.conf | grep -A 15 "location /api"
```

### 4. Проверьте что nginx может достучаться до app:

```bash
sudo docker exec instagram_cf_frontend wget -O- http://app:8000/health 2>&1
```

### 5. Проверьте сеть между контейнерами:

```bash
sudo docker network inspect instagram_cf_network | grep -A 10 "Containers"
```

### 6. Тестовый запрос через nginx proxy:

```bash
curl -v http://localhost:3001/api/health
```

### 7. Проверьте что app отвечает напрямую:

```bash
curl -v http://localhost:8009/health
```

### 8. Проверьте логи nginx в реальном времени:

```bash
sudo docker logs -f instagram_cf_frontend
```

Затем попробуйте залогиниться через браузер и смотрите что появляется в логах.






