# Как сделать запросы похожие на браузер

## Проблема
Instagram блокирует автоматизированные запросы, потому что они отличаются от браузера:
- ❌ Python requests: HTTP/1.1, другой TLS fingerprint, нет Sec-Fetch-* заголовков
- ✅ Браузер: HTTP/2 или HTTP/3, правильный TLS fingerprint, все заголовки

## Решения

### 1. httpx с HTTP/2 (рекомендуется)

```python
import httpx

proxy = 'http://user:pass@host:port'

with httpx.Client(
    http2=True,  # Включаем HTTP/2 (как браузер)
    proxies=proxy,
    verify=False,
    timeout=10.0
) as client:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    
    response = client.get('https://www.instagram.com', headers=headers)
    print(f"HTTP {response.status_code}, версия: {response.http_version}")
```

**Установка:**
```bash
pip install httpx[http2]
```

### 2. curl_cffi с правильным TLS fingerprint

```python
from curl_cffi import requests

proxy = 'http://user:pass@host:port'

response = requests.get(
    'https://www.instagram.com',
    proxies={'http': proxy, 'https': proxy},
    impersonate='chrome110',  # Эмулируем Chrome 110 (правильный TLS fingerprint)
    timeout=10,
    verify=False
)
```

**Установка:**
```bash
pip install curl-cffi
```

**Доступные браузеры:**
- `chrome110`, `chrome120`
- `firefox109`
- `safari15_5`

### 3. requests с максимально браузерными заголовками

```python
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

response = requests.get(
    'https://www.instagram.com',
    headers=headers,
    proxies={'http': proxy, 'https': proxy},
    timeout=10,
    verify=False
)
```

**НО:** Все равно HTTP/1.1 и другой TLS fingerprint!

## Интеграция в instagrapi

### Проблема
instagrapi использует `requests` под капотом, который не поддерживает HTTP/2 и имеет другой TLS fingerprint.

### Решение 1: Модификация instagrapi (сложно)
Нужно заменить `requests` на `httpx` или `curl_cffi` в исходном коде instagrapi.

### Решение 2: Использовать сохраненные сессии (рекомендуется)
1. Авторизуйтесь в браузере через прокси
2. Экспортируйте сессию
3. Используйте сессию в instagrapi - для уже авторизованных аккаунтов прокси работает!

### Решение 3: Wrapper для instagrapi
Создать wrapper, который перехватывает запросы instagrapi и отправляет их через httpx/curl_cffi.

## Что нужно для полной эмуляции браузера

1. ✅ **HTTP/2 или HTTP/3** - используйте `httpx[http2]`
2. ✅ **Правильный TLS fingerprint** - используйте `curl_cffi` с `impersonate`
3. ✅ **Все заголовки браузера** - добавьте Sec-Fetch-*, Accept, Accept-Language и т.д.
4. ✅ **Cookies и сессии** - используйте сохраненные сессии
5. ⚠️ **JavaScript** - невозможно эмулировать в Python (но для API не нужно)

## Вывод

**Для новых авторизаций:**
- Instagram блокирует автоматизированные запросы, даже с HTTP/2 и правильным TLS fingerprint
- Решение: авторизуйтесь в браузере, затем используйте сохраненную сессию

**Для уже авторизованных аккаунтов:**
- Прокси работает отлично (как на проде - обновление профиля работает)
- instagrapi с прокси работает для всех операций, кроме новой авторизации



