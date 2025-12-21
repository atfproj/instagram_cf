# Импорт аккаунтов с готовыми сессиями

## Проблема
При авторизации через `login/password` Instagram требует проверки (email, SMS), т.к. видит новый IP/устройство.

## Решение
Использовать **готовые сессии** из купленных аккаунтов — обходим все проверки Instagram!

## Формат данных из файлов

```
username:password|User-Agent|device_ids|cookies||email:password
```

**Пример:**
```
lerchek___:lra.dakhno|Instagram 359.2.0.64.89 Android...|android-xxx;uuid1;uuid2;uuid3|Authorization=Bearer IGT:2:xxx;X-MID=xxx;sessionid=xxx;...||
```

## Как использовать

### Через API

```bash
POST /api/accounts/import-session-from-text
Content-Type: application/json

{
  "session_text": "username:password|User-Agent|device_ids|cookies||email",
  "proxy_id": "uuid-прокси",  // опционально
  "group_id": "uuid-группы",  // опционально
  "validate": false           // валидировать сессию (опционально)
}
```

### Через UI (будет добавлено)

1. Перейти в раздел **"Аккаунты"**
2. Нажать **"Импорт сессии"**
3. Вставить строку с данными аккаунта
4. Выбрать прокси и группу
5. Нажать **"Импортировать"**

## Что происходит

1. **Парсинг данных:**
   - Username, password
   - User-Agent
   - Device IDs (4 UUID)
   - Cookies (Authorization, sessionid, X-MID, etc.)

2. **Создание session_data для instagrapi:**
   - Преобразуем cookies в формат instagrapi
   - Извлекаем device settings из User-Agent
   - Создаем полную сессию

3. **Сохранение в БД:**
   - Аккаунт сохраняется с готовой сессией
   - Не требуется логин через Instagram
   - Сразу готов к использованию

## Преимущества

✅ **Обход проверок Instagram** — используем готовую сессию
✅ **Нет email/SMS верификации** — сессия уже авторизована
✅ **Быстрый импорт** — просто вставить строку
✅ **Работает с прокси** — привязываем прокси к аккаунту
✅ **Поддержка всех форматов** — 2022-2023 и 2024 года

## Важно

- Сессии из файлов 2022-2023 могут быть устаревшими
- Используйте свежие сессии (2024-2025)
- Привязывайте прокси к аккаунтам
- Валидация опциональна (может быть медленной)

## Тестирование

```bash
# Пример данных для теста
curl -X POST http://localhost:8009/api/accounts/import-session-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "session_text": "lerchek___:lra.dakhno|Instagram 359.2.0.64.89...",
    "validate": false
  }'
```

## Файлы проекта

- `backend/app/services/session_importer.py` — парсинг и создание сессий
- `backend/app/api/accounts.py` — эндпоинт `/import-session-from-text`
- UI форма — TODO (будет добавлена)


