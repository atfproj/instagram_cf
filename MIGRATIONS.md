# Команды для миграций на продакшене

## Применить миграции

```bash
# В контейнере app
docker exec -it instagram_cf_app alembic upgrade head

# Или из директории backend внутри контейнера
docker exec -it instagram_cf_app bash -c "cd backend && alembic upgrade head"
```

## Создать нового пользователя

```bash
# В контейнере app
docker exec -it instagram_cf_app python create_user.py --username admin --email admin@example.com --password your_secure_password --role admin

# Или из корневой директории проекта
docker exec -it instagram_cf_app python backend/create_user.py --username admin --email admin@example.com --password your_secure_password --role admin
```

## Проверка статуса миграций

```bash
docker exec -it instagram_cf_app alembic current
```

## Откат последней миграции

```bash
docker exec -it instagram_cf_app alembic downgrade -1
```






