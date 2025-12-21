# Исправление проблемы сборки фронтенда

## Проблема
Docker использует кэш старого слоя с `npm ci --only=production`, поэтому `vite` не устанавливается.

## Решение

### Вариант 1: Пересобрать БЕЗ кэша (рекомендуется)

```bash
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Вариант 2: Удалить старый образ и пересобрать

```bash
# Удалить старый образ
docker rmi instagram_cf-frontend 2>/dev/null || true

# Пересобрать
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Вариант 3: Изменить Dockerfile (уже сделано)

Dockerfile.prod теперь использует `npm install` вместо `npm ci --only=production`.

Но Docker может использовать кэш. Чтобы принудительно пересобрать:

```bash
# Очистить build cache для frontend
docker builder prune -f

# Пересобрать
docker compose -f docker-compose.prod.yml build --no-cache frontend
```

## Проверка

После пересборки проверьте логи:

```bash
docker compose -f docker-compose.prod.yml logs frontend --tail=50
```

Должно быть успешное завершение сборки без ошибок `vite: not found`.






