# Простое исправление - пошагово

## Текущая ситуация:
✅ Фронтенд работает (порт 3001)
❌ App работает, но unhealthy (порт 8009)
✅ БД работает (порт 5436)
✅ Redis работает (порт 6383)

## Шаг 1: Проверьте логи app

```bash
sudo docker logs instagram_cf_app --tail=30
```

Если видите ошибку про `localhost:5436` - значит проблема в `.env` файле.

## Шаг 2: Исправьте .env файл

Откройте `.env` на проде и найдите строки:

```env
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@localhost:5436/instagram_cf
REDIS_URL=redis://localhost:6383/0
```

**Замените на:**

```env
DATABASE_URL=postgresql://instagram_cf:instagram_cf_password@db:5432/instagram_cf
REDIS_URL=redis://redis:6379/0
```

**Что изменилось:**
- `localhost` → `db` (для БД) или `redis` (для Redis)
- `5436` → `5432` (внутренний порт PostgreSQL)
- `6383` → `6379` (внутренний порт Redis)

## Шаг 3: Перезапустите app

```bash
sudo docker-compose -f docker-compose.prod.yml restart app celery_worker
```

## Шаг 4: Проверьте статус

```bash
sudo docker ps | grep instagram_cf_app
```

Должно быть `(healthy)` вместо `(unhealthy)`.

## Шаг 5: Проверьте логи снова

```bash
sudo docker logs instagram_cf_app --tail=20
```

Не должно быть ошибок про подключение к БД.

## Готово!

После этого:
- Фронтенд: http://202.148.54.41:3001
- API: http://202.148.54.41:8009






