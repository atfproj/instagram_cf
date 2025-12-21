# Как экспортировать cookies из браузера для instagrapi

## Проблема
Instagram блокирует автоматизированные запросы через прокси (Python/instagrapi), даже если прокси работает в браузере. Это происходит из-за различий в TLS fingerprint и HTTP-версии.

## Решение
Использовать готовые сессии (cookies) из браузера, где авторизация прошла успешно.

## Инструкция по экспорту cookies

### Вариант 1: Через DevTools (Chrome/Firefox)

1. Откройте Instagram в браузере через прокси
2. Авторизуйтесь в аккаунте
3. Нажмите F12 (открыть DevTools)
4. Перейдите на вкладку "Application" (Chrome) или "Storage" (Firefox)
5. В левом меню выберите "Cookies" → `https://www.instagram.com`
6. Найдите следующие cookies:
   - `IG-INTENDED-USER-ID` или `IG-U-DS-USER-ID`
   - `X-MID`
   - `X-IG-WWW-Claim`
   - `Authorization` (если есть)
   - `csrftoken`
   - `sessionid` (если есть)
   - `mid`
   - `ig_did`
   - `datr`

7. Скопируйте значения cookies в формате:
```
IG-INTENDED-USER-ID=значение;X-MID=значение;X-IG-WWW-Claim=значение;Authorization=значение;...
```

### Вариант 2: Через расширение браузера

1. Установите расширение "Cookie-Editor" или "EditThisCookie"
2. Откройте Instagram и авторизуйтесь
3. Откройте расширение
4. Экспортируйте cookies в JSON или Netscape формат
5. Преобразуйте в нужный формат для импорта

### Вариант 3: Через JavaScript в консоли браузера

1. Откройте Instagram и авторизуйтесь
2. Нажмите F12 → Console
3. Выполните:
```javascript
// Получить все cookies для instagram.com
const cookies = document.cookie.split(';').map(c => c.trim()).filter(c => c);
const importantCookies = [
  'IG-INTENDED-USER-ID',
  'IG-U-DS-USER-ID',
  'X-MID',
  'X-IG-WWW-Claim',
  'Authorization',
  'csrftoken',
  'sessionid',
  'mid',
  'ig_did',
  'datr'
];

const result = {};
cookies.forEach(cookie => {
  const [name, value] = cookie.split('=');
  if (importantCookies.includes(name) || name.startsWith('IG-') || name.startsWith('X-')) {
    result[name] = value;
  }
});

console.log(JSON.stringify(result, null, 2));
```

4. Скопируйте результат

## Формат для импорта в систему

После экспорта cookies используйте API endpoint:
```
POST /api/accounts/{account_id}/import-session
```

С телом:
```json
{
  "session_data": {
    "cookies": {
      "IG-INTENDED-USER-ID": "значение",
      "X-MID": "значение",
      "X-IG-WWW-Claim": "значение",
      "Authorization": "значение"
    },
    "device_id": "android-xxxxx",
    "user_agent": "Instagram ..."
  }
}
```

## Важно

1. **Cookies должны быть свежими** - экспортируйте сразу после авторизации
2. **Используйте тот же прокси**, через который авторизовались в браузере
3. **Device ID и User-Agent** должны совпадать с браузером (или использовать Android device ID из файла)
4. **Сессия может устареть** - если не работает, экспортируйте заново

## Альтернатива: Массовый импорт

Если у вас есть файл с аккаунтами в формате:
```
username:password|user_agent|device_ids|cookies||
```

Используйте:
```
POST /api/accounts/bulk-import
```

С телом:
```json
{
  "accounts_data": [
    "username:password|user_agent|device_ids|cookies||",
    ...
  ],
  "group_id": "uuid",
  "proxy_id": "uuid",
  "validate_sessions": true
}
```



