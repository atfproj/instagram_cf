#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логина через сессию с instagrapi==2.0.0
"""
import json
import re
from instagrapi import Client

def parse_session_line(line: str):
    """Парсит строку сессии в формате InstAccountsManager"""
    parts = line.strip().split('|')
    if len(parts) < 4:
        raise ValueError(f"Недостаточно частей в строке: {len(parts)}")
    
    # 1. Username и пароль
    credentials = parts[0].split(':')
    username = credentials[0]
    password = ':'.join(credentials[1:])
    
    # 2. User-Agent
    user_agent = parts[1]
    
    # 3. Device IDs
    device_ids = parts[2].split(';')
    android_device_id = device_ids[0]
    phone_id = device_ids[1]
    uuid = device_ids[2]
    adid = device_ids[3]
    
    # 4. Cookies
    cookies_raw = parts[3]
    cookies_dict = {}
    
    cookie_pairs = cookies_raw.split(';')
    for pair in cookie_pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            cookies_dict[key.strip()] = value.strip()
    
    return {
        'username': username,
        'password': password,
        'user_agent': user_agent,
        'android_device_id': android_device_id,
        'phone_id': phone_id,
        'uuid': uuid,
        'adid': adid,
        'cookies': cookies_dict
    }

def create_session_data(account_data):
    """Создает session_data для instagrapi из распарсенных данных"""
    cookies = account_data['cookies']
    user_agent = account_data['user_agent']
    
    # Извлекаем параметры из User-Agent
    app_version_match = re.search(r'Instagram\s+([\d.]+)', user_agent)
    app_version = app_version_match.group(1) if app_version_match else '385.0.0.47.74'
    
    android_version_match = re.search(r'Android\s+\((\d+)/', user_agent)
    android_version = int(android_version_match.group(1)) if android_version_match else 30
    
    android_release_match = re.search(r'Android\s+\(\d+/([\d.]+)', user_agent)
    android_release = android_release_match.group(1) if android_release_match else '11'
    
    dpi_match = re.search(r';\s*(\d+)dpi;', user_agent)
    dpi = f"{dpi_match.group(1)}dpi" if dpi_match else '480dpi'
    
    resolution_match = re.search(r';\s*(\d+x\d+);', user_agent)
    resolution = resolution_match.group(1) if resolution_match else '1080x1920'
    
    # Извлекаем manufacturer и device из User-Agent
    parts = user_agent.split(';')
    manufacturer = 'Samsung'
    device = 'SM-G960F'
    model = 'SM-G960F'
    cpu = 'exynos9820'
    
    if len(parts) >= 5:
        manufacturer = parts[3].strip()
        device = parts[4].strip()
        model = device
        if len(parts) >= 6:
            cpu = parts[5].strip()
    
    version_code_match = re.search(r';\s*(\d+)\)$', user_agent)
    version_code = version_code_match.group(1) if version_code_match else '750732754'
    
    # Создаем session_data
    session_data = {
        'uuids': {
            'phone_id': account_data['phone_id'],
            'uuid': account_data['uuid'],
            'client_session_id': account_data['uuid'],
            'advertising_id': account_data['adid'],
            'android_device_id': account_data['android_device_id'],
        },
        'mid': cookies.get('X-MID') or cookies.get('mid'),
        'ig_www_claim': cookies.get('X-IG-WWW-Claim'),
        'authorization_data': {
            'sessionid': cookies.get('sessionid', ''),
            'ds_user_id': cookies.get('ds_user_id') or cookies.get('IG-U-DS-USER-ID') or cookies.get('IG-INTENDED-USER-ID'),
        },
        'cookies': cookies,
        'last_login': None,
        'device_settings': {
            'app_version': app_version,
            'android_version': android_version,
            'android_release': android_release,
            'dpi': dpi,
            'resolution': resolution,
            'manufacturer': manufacturer,
            'device': device,
            'model': model,
            'cpu': cpu,
            'version_code': version_code,
        },
        'user_agent': user_agent,
        'country': 'US',
        'country_code': 1,
        'locale': 'en_US',
        'timezone_offset': -14400,
    }
    
    # Добавляем user_id
    user_id = cookies.get('ds_user_id') or cookies.get('IG-U-DS-USER-ID') or cookies.get('IG-INTENDED-USER-ID')
    if user_id:
        session_data['user_id'] = user_id
    
    return session_data

def test_session_login():
    """Тестирует логин через сессию"""
    
    # Используем строку из 17-12-25_17-26-43-d50c508d3b6eaa616f10d6ed1eb6216b.txt
    session_line = "aaravinthselvam:1uZVC9wGtG3p|Instagram 385.0.0.47.74 Android (27/8.1.0; 240dpi; 1440x2924; samsung; SM-A405FN; a40; exynos7904; es_ES; 750732754)|android-45af7455cd8e83eb;f042db99-37ed-45bd-a581-b5c95bd7d578;438a3a2b-7a27-4d16-a3a8-0205f6206ed7;74115610-bcd7-4103-bce0-f03130d80761|mid=aA9rzgABAAGcfKX2jia4sC27kb9Z;ig_cb=deleted;csrftoken=HcHdd1Ql7bBoXeknZCthy6idmNw49cSG;rur=\"RVA\\05466346554750\\0541794923369:01feb81c0cfda0ce0baec8732089a0e16f1969df7b1e581fd2c3e96165a246a775c707ad\";ds_user_id=66346554750;ig_did=AF7DF2BA-348F-43B7-90D0-C5C91AAFBBDE;sessionid=66346554750%3ArWDCe2HVFbkpyL%3A24%3AAYhQBgHjiN0d-sw9F2GAtow20koevG8WyTOOO_EwHQ;X-IG-WWW-Claim=hmac.AR13me2ymkGtwug60RhLYSOvBXCLa7UK42u9gDISsz8NsvFJ;Authorization=Bearer IGT:2:eyJkc191c2VyX2lkIjoiNjYzNDY1NTQ3NTAiLCJzZXNzaW9uaWQiOiI2NjM0NjU1NDc1MCUzQXJXRENlMkhWRmJrcHlMJTNBMjQlM0FBWWhRQmdIamlOMGQtc3c5RjJHQXRvdzIwa29ldkc4V3lUT09PX0V3SFEifQ==;IG-U-DS-USER-ID=66346554750;IG-INTENDED-USER-ID=66346554750;X-MID=aA9rzgABAAGcfKX2jia4sC27kb9Z;||"
    
    print(f"🔍 Тестируем сессию: {session_line[:50]}...")
    
    try:
        # 1. Парсим данные
        print("1️⃣ Парсинг данных сессии...")
        account_data = parse_session_line(session_line)
        print(f"   Username: {account_data['username']}")
        print(f"   User-Agent: {account_data['user_agent'][:60]}...")
        print(f"   Cookies: {len(account_data['cookies'])} шт")
        
        # 2. Создаем session_data
        print("2️⃣ Создание session_data...")
        session_data = create_session_data(account_data)
        print(f"   device_settings тип: {type(session_data['device_settings'])}")
        print(f"   android_version: {session_data['device_settings']['android_version']} (тип: {type(session_data['device_settings']['android_version'])})")
        
        # 3. Читаем прокси
        print("3️⃣ Загрузка прокси...")
        with open('proxies.txt', 'r') as f:
            proxy_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        proxy_url = proxy_lines[0] if proxy_lines else None
        if proxy_url:
            print(f"   Прокси: {proxy_url[:50]}...")
        else:
            print("   ⚠️ Прокси не найден, работаем без прокси")
        
        # 4. Создаем клиент
        print("4️⃣ Создание Instagram клиента...")
        client = Client()
        
        # 5. Устанавливаем прокси
        if proxy_url:
            print("5️⃣ Установка прокси...")
            client.set_proxy(proxy_url)
            print("   ✅ Прокси установлен")
        
        # 6. Устанавливаем сессию
        print("6️⃣ Установка session_data...")
        print(f"   device_settings перед set_settings: {type(session_data['device_settings'])}")
        
        result = client.set_settings(session_data)
        print(f"   set_settings вернул: {result}")
        print(f"   client.device_settings после: {type(client.device_settings)}")
        
        # 7. Проверяем сессию
        print("7️⃣ Проверка сессии через account_info()...")
        account_info = client.account_info()
        
        print(f"✅ УСПЕХ! Логин через сессию работает!")
        print(f"   Username: {account_info.username}")
        print(f"   User ID: {account_info.pk}")
        print(f"   Full name: {account_info.full_name}")
        print(f"   Is private: {account_info.is_private}")
        
        # 8. Проверяем get_settings
        print("8️⃣ Проверка get_settings()...")
        saved_settings = client.get_settings()
        print(f"   get_settings() тип: {type(saved_settings)}")
        if isinstance(saved_settings, dict):
            print(f"   device_settings в get_settings: {type(saved_settings.get('device_settings'))}")
        else:
            print(f"   ❌ get_settings() вернул не dict: {saved_settings}")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Тестирование логина через сессию с instagrapi==2.0.0")
    print("=" * 60)
    success = test_session_login()
    print("=" * 60)
    if success:
        print("🎉 Тест прошел успешно! Можно интегрировать в основной код.")
    else:
        print("💥 Тест провалился. Нужно исправить проблемы.")
