# Instagram Content Factory

Автоматизированный сервис для постинга контента на множество Instagram-аккаунтов с автоматическим переводом текста.

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL (порт 5436)
- Redis (порт 6383)
- FastAPI приложение (порт 8009)
- Celery worker

### 4. Создание миграций БД

```bash
# Перейти в директорию backend
cd backend

# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции
alembic upgrade head
```

### 5. Запуск без Docker

```bash
# Запустить PostgreSQL и Redis отдельно, затем:
# Из корневой директории проекта
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn backend.app.main:app --reload
```

### 6. Запуск Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:3001`

Для настройки API URL создайте файл `frontend/.env`:
```env
VITE_API_URL=http://localhost:8009
```

## API Endpoints

### Группы
- `POST /api/groups/` - Создать группу
- `GET /api/groups/` - Список групп
- `GET /api/groups/{id}` - Информация о группе
- `PUT /api/groups/{id}` - Обновить группу
- `DELETE /api/groups/{id}` - Удалить группу
- `GET /api/groups/{id}/accounts` - Аккаунты в группе

### Аккаунты
- `POST /api/accounts/` - Добавить аккаунт
- `GET /api/accounts/` - Список аккаунтов
- `GET /api/accounts/{id}` - Информация об аккаунте
- `PUT /api/accounts/{id}` - Обновить аккаунт
- `DELETE /api/accounts/{id}` - Удалить аккаунт
- `POST /api/accounts/{id}/login` - Авторизоваться в Instagram
- `GET /api/accounts/{id}/status` - Проверить статус аккаунта

## Документация API

После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8009/docs
- ReDoc: http://localhost:8009/redoc

## Структура проекта

См. `TZ.md` для полного технического задания.

## Разработка

Проект находится в активной разработке. См. `TZ.md` раздел "План разработки" для текущего статуса.

