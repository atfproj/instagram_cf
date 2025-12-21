# Context Memory - Instagram CF

## 21.12.2025 - ✅ ИСПРАВЛЕНО! Проблема с Docker портами

### Проблема
- Бэкенд не отвечал через порт 8009 (Empty reply from server) 3+ часа
- Внутри контейнера работало (200 OK), снаружи — нет
- docker-proxy слушал порт, соединение устанавливалось, но ответа не было

### Причина
1. **Монтирование `.:/app`** — вызывало постоянные перезапуски uvicorn
2. **Проброс портов Docker** — не работал корректно
3. **37.75GB мусора** в Docker cache

### Решение
1. Убрали `volumes: - .:/app` (оставили только `uploads_data`)
2. Почистили Docker: `docker system prune -f` (37.75GB)
3. Использовали `network_mode: host` для app
4. Изменили порт uvicorn на 8009
5. Обновили DATABASE_URL на `localhost:5436` вместо `db:5432`

### Результат
- ✅ **Бэкенд работает:** `http://localhost:8009/health`
- ✅ **Фронтенд работает:** `http://localhost:3001`
- ✅ Всё запускается локально без проблем

### Ключевые изменения
- `docker-compose.yml`: убрали `- .:/app`, добавили `network_mode: host`
- Бэкенд теперь слушает порт 8009 напрямую (без проброса)
- DB/Redis доступны через localhost:5436/6383

## 25.12.2025 - Исправление портов для локальной разработки

### Проблема
- Фронтенд не запускался локально (ERR_CONNECTION_REFUSED на localhost:3002)
- Несоответствие портов: vite запускался на 3002 внутри контейнера, но docker-compose пробрасывал 3001
- Пользователь пытался открыть localhost:3002, но порт не был проброшен

### Решение
1. **Исправлены порты:**
   - `docker-compose.yml`: изменён порт с `3001:3001` на `3002:3002`
   - `frontend/vite.config.js`: порт изменён с 3001 на 3002
   - `frontend/Dockerfile`: EXPOSE изменён с 3001 на 3002
   - Пересоздан контейнер фронтенда через `docker compose up -d --force-recreate frontend`

2. **Результат:**
   - ✅ Фронтенд доступен на `http://localhost:3002`
   - ✅ Бэкенд доступен на `http://localhost:8009`
   - ✅ Все сервисы работают локально

### Команды для запуска
```bash
docker compose up -d
# Фронтенд: http://localhost:3002
# Бэкенд: http://localhost:8009
```

## 19.12.2025 - Решение проблемы авторизации

### Проблема
- Авторизация через `login/password` попадала под проверки Instagram (email, SMS)
- Instagram блокировал автоматические запросы с серверного IP
- VPN IP тоже блокировался Instagram при логине
- Купленные аккаунты с готовыми сессиями не использовались

### Решение
1. **Добавлен импорт готовых сессий:**
   - Новый сервис `session_importer.py` - парсит строки формата купленных аккаунтов
   - API endpoint `/api/accounts/import-session-from-text`
   - UI модалка `ImportSessionModal` для импорта через интерфейс

2. **Формат данных:**
   ```
   username:password|User-Agent|device_ids|cookies||email
   ```
   - Парсятся: Authorization Bearer token, sessionid, device IDs, cookies
   - Создается полная `session_data` для instagrapi
   - Обходятся все проверки Instagram

3. **Файлы проекта:**
   - `backend/app/services/session_importer.py`
   - `backend/app/api/accounts.py` - endpoint
   - `frontend/src/components/ImportSessionModal.jsx`
   - `frontend/src/pages/Accounts.jsx` - кнопка "Загрузка сессии"

### Проблемы с доступом к Instagram

1. **Без VPN:**
   - Instagram недоступен с серверного IP (100% packet loss)
   - Дата-центры заблокированы Instagram

2. **С VPN:**
   - ✅ Instagram доступен
   - ✅ Прокси работают через VPN
   - ❌ Логин блокируется (но сессии работают!)

3. **Решение на проде:**
   - Настроить VPN на сервере (см. `PRODUCTION_VPN_SETUP.md`)
   - Использовать импорт готовых сессий
   - Прокси для изоляции аккаунтов

### Ключевые файлы
- Купленные аккаунты: `17-12-25_17-*.txt` (3 файла, ~15 аккаунтов)
- Документация: `IMPORT_SESSION_GUIDE.md`, `PRODUCTION_SOLUTIONS.md`
- Changelog: `changelog.md`

### Что работает
- ✅ Импорт сессий через UI
- ✅ Обход проверок Instagram
- ✅ Прокси с VPN
- ✅ Обновление профиля

### Следующие шаги
- [ ] Перенести на прод с VPN
- [ ] Импортировать купленные аккаунты
- [ ] Протестировать постинг
