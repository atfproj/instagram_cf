#!/usr/bin/env python3
import requests
import tempfile
import os

# Настройки из PHP скрипта
proxy = "192.241.122.132:8000"
proxy_username = "hZEYrh"
proxy_password = "8zfv7m"
proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy}"

# Создаем временный файл для cookies (как в PHP)
cookie_file = tempfile.NamedTemporaryFile(delete=False, prefix='insta_cookies_', suffix='.txt')
cookie_file.close()
cookie_path = cookie_file.name

try:
    # Заголовки точно как в PHP скрипте
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Настройки прокси (в requests авторизация в URL)
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    # Настройки сессии (как в PHP: SSL verification отключена, cookies используются)
    session = requests.Session()
    session.verify = False  # CURLOPT_SSL_VERIFYPEER => false
    session.proxies = proxies
    session.headers.update(headers)
    
    # Отключаем предупреждения о SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Делаем запрос (FOLLOWLOCATION = true в PHP)
    url = 'https://www.instagram.com/s_bezrukov'
    
    print(f"Запрос к: {url}")
    print(f"Прокси: {proxy}")
    print("="*60)
    
    response = session.get(url, allow_redirects=True, timeout=15)
    
    print(f"HTTP код: {response.status_code}")
    print(f"Размер ответа: {len(response.content)} bytes")
    print(f"URL после редиректов: {response.url}")
    
    if response.status_code == 200:
        print("✅ Успешно!")
        # Пробуем найти JSON данные как в PHP скрипте
        import re
        matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', response.text, re.DOTALL)
        if matches:
            print(f"✅ Найдено {len(matches)} JSON блоков")
            try:
                import json
                profile_data = json.loads(matches[0])
                print("✅ JSON распарсен успешно")
                print(f"   Тип: {profile_data.get('@type', 'N/A')}")
            except Exception as e:
                print(f"⚠️  Ошибка парсинга JSON: {e}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"Ответ: {response.text[:500]}")
        
finally:
    # Удаляем временный файл cookies
    if os.path.exists(cookie_path):
        os.unlink(cookie_path)

