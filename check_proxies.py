#!/usr/bin/env python3
"""
Скрипт для проверки работоспособности прокси
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Читаем прокси из файла
proxies = []
with open('proxies.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            proxies.append(line)

print(f"Найдено {len(proxies)} прокси для проверки\n")

def check_proxy(proxy_url, timeout=10):
    """Проверяет один прокси"""
    proxy_dict = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    test_urls = [
        'https://httpbin.org/ip',  # Проверка IP
        'https://api.telegram.org',  # Проверка доступности Telegram API
        'https://www.instagram.com',  # Проверка доступности Instagram
    ]
    
    results = {
        'proxy': proxy_url,
        'working': False,
        'ip': None,
        'telegram': False,
        'instagram': False,
        'error': None
    }
    
    try:
        # Проверка 1: Получение IP через прокси
        try:
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout,
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                results['ip'] = data.get('origin', 'unknown')
                results['working'] = True
        except Exception as e:
            results['error'] = str(e)
            return results
        
        # Проверка 2: Доступность Telegram API
        try:
            response = requests.get(
                'https://api.telegram.org',
                proxies=proxy_dict,
                timeout=timeout,
                verify=False
            )
            results['telegram'] = response.status_code in [200, 301, 302, 404]
        except Exception as e:
            results['telegram'] = False
        
        # Проверка 3: Доступность Instagram
        try:
            response = requests.get(
                'https://www.instagram.com',
                proxies=proxy_dict,
                timeout=timeout,
                verify=False,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            results['instagram'] = response.status_code in [200, 301, 302]
        except Exception as e:
            results['instagram'] = False
            
    except Exception as e:
        results['error'] = str(e)
    
    return results

# Проверяем все прокси
print("Начинаю проверку прокси...\n")
print(f"{'Прокси':<50} {'Статус':<10} {'IP':<20} {'Telegram':<10} {'Instagram':<10}")
print("-" * 100)

working_count = 0
telegram_count = 0
instagram_count = 0

# Используем ThreadPoolExecutor для параллельной проверки
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_proxy = {executor.submit(check_proxy, proxy): proxy for proxy in proxies}
    
    for future in as_completed(future_to_proxy):
        result = future.result()
        proxy_short = result['proxy'][:48] + '...' if len(result['proxy']) > 50 else result['proxy']
        
        status = "✅ РАБОТАЕТ" if result['working'] else "❌ НЕ РАБОТАЕТ"
        ip = result['ip'] or "N/A"
        telegram = "✅" if result['telegram'] else "❌"
        instagram = "✅" if result['instagram'] else "❌"
        
        print(f"{proxy_short:<50} {status:<10} {ip:<20} {telegram:<10} {instagram:<10}")
        
        if result['working']:
            working_count += 1
        if result['telegram']:
            telegram_count += 1
        if result['instagram']:
            instagram_count += 1
        
        if result['error']:
            print(f"  Ошибка: {result['error']}")

print("\n" + "=" * 100)
print(f"Итого:")
print(f"  Работающих прокси: {working_count}/{len(proxies)}")
print(f"  Доступен Telegram: {telegram_count}/{len(proxies)}")
print(f"  Доступен Instagram: {instagram_count}/{len(proxies)}")



