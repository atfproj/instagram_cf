# Почему нельзя использовать localhost в Docker

## Проблема

В вашем `.env` файле:
```env
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@localhost:5436/instagram_cf
REDIS_URL=redis://localhost:6383/0
```

## Почему это не работает?

### В Docker контейнерах:
- `localhost` = **сам контейнер**, а не хост-машина
- Когда контейнер `app` обращается к `localhost:5436`, он ищет PostgreSQL **внутри себя**
- PostgreSQL находится в **другом контейнере** `db`
- Поэтому получается ошибка "Connection refused"

### Правильно для Docker:

```env
# Используйте ИМЕНА СЕРВИСОВ из docker-compose.yml
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
```

### Объяснение портов:

**Внешние порты** (для доступа с хост-машины):
- PostgreSQL: `5436:5432` (внешний:внутренний)
- Redis: `6383:6379` (внешний:внутренний)

**Внутренние порты** (между контейнерами Docker):
- PostgreSQL: `5432` (стандартный порт PostgreSQL)
- Redis: `6379` (стандартный порт Redis)

### Схема:

```
Хост-машина → localhost:5436 → Контейнер db:5432
                    ↑
                    └─── НЕ работает из контейнера app!

Контейнер app → db:5432 → Контейнер db:5432
                    ↑
                    └─── Работает! (через Docker network)
```

## Исправление

Замените в `.env`:

```env
# ❌ НЕПРАВИЛЬНО (для Docker)
DATABASE_URL=postgresql://instagram_cf:password@localhost:5436/instagram_cf
REDIS_URL=redis://localhost:6383/0

# ✅ ПРАВИЛЬНО (для Docker)
DATABASE_URL=postgresql://instagram_cf:password@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
```

## Когда использовать localhost?

- **Без Docker** (локальная разработка): `localhost:5436`
- **В Docker контейнерах**: `db:5432` (имя сервиса:внутренний порт)

## После исправления:

```bash
# Перезапустить сервисы
sudo docker-compose -f docker-compose.prod.yml restart app celery_worker

# Проверить подключение
sudo docker-compose -f docker-compose.prod.yml logs app --tail=20
```






