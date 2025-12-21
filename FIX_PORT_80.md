# Исправление ошибки "port 80 is already allocated"

## Проблема
Порт 80 уже занят другим процессом или контейнером.

## Решение

### Вариант 1: Остановить контейнер, занимающий порт 80

```bash
# Найти контейнер, использующий порт 80
sudo docker ps | grep :80

# Остановить его
sudo docker stop <container_id>

# Или если это другой docker-compose проект
sudo docker-compose -f <other-compose-file> down
```

### Вариант 2: Использовать другой порт для фронтенда

В `docker-compose.prod.yml` уже установлен порт `3001:80`, но если нужно использовать другой:

```yaml
ports:
  - "8080:80"  # или любой другой свободный порт
```

### Вариант 3: Освободить порт 80 системно

```bash
# Найти процесс, использующий порт 80
sudo lsof -i :80
# или
sudo netstat -tulpn | grep :80

# Остановить процесс (если это не критично)
sudo kill -9 <PID>
```

## Текущая конфигурация

В `docker-compose.prod.yml` фронтенд настроен на порт `3001:80`, что означает:
- Внешний порт: 3001
- Внутренний порт (nginx): 80

Фронтенд будет доступен на `http://your-server:3001`

## После исправления

```bash
# Перезапустить фронтенд
sudo docker-compose -f docker-compose.prod.yml up -d frontend

# Проверить статус
sudo docker-compose -f docker-compose.prod.yml ps
```






