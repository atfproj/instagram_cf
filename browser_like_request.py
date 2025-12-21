#!/usr/bin/env python3
"""
Примеры запросов, похожих на браузер
"""

# ВАРИАНТ 1: httpx с HTTP/2 (как браузер)
def request_with_httpx_http2(url, proxy=None):
    """
    Запрос с HTTP/2 (как браузер)
    Требует: pip install httpx[http2]
    """
    import httpx
    
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
    
    with httpx.Client(
        http2=True,  # Включаем HTTP/2 (как браузер)
        proxies=proxy,
        verify=False,
        timeout=10.0
    ) as client:
        response = client.get(url, headers=headers)
        return response


# ВАРИАНТ 2: curl_cffi с эмуляцией браузера (правильный TLS fingerprint)
def request_with_curl_cffi(url, proxy=None, browser='chrome110'):
    """
    Запрос с правильным TLS fingerprint (как браузер)
    Требует: pip install curl-cffi
    
    Доступные браузеры:
    - chrome110, chrome120
    - firefox109
    - safari15_5
    """
    from curl_cffi import requests
    
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
    
    proxies = None
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
    
    response = requests.get(
        url,
        proxies=proxies,
        impersonate=browser,  # Эмулируем браузер (правильный TLS fingerprint)
        timeout=10,
        verify=False
    )
    return response


# ВАРИАНТ 3: requests с максимально браузерными заголовками
def request_with_requests_browser_headers(url, proxy=None):
    """
    Запрос с максимально браузерными заголовками
    НО: все равно HTTP/1.1 и другой TLS fingerprint
    """
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
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }
    
    proxies = None
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
    
    response = requests.get(
        url,
        headers=headers,
        proxies=proxies,
        timeout=10,
        verify=False
    )
    return response


# ИНТЕГРАЦИЯ В INSTAGRAPI
def patch_instagrapi_with_browser_like_requests():
    """
    Как заменить requests в instagrapi на httpx с HTTP/2 или curl_cffi
    
    ВАЖНО: Это требует модификации instagrapi или создания wrapper
    """
    from instagrapi import Client
    import httpx
    
    # Создаем клиент
    client = Client()
    
    # Пробуем заменить session на httpx с HTTP/2
    if hasattr(client, 'private') and hasattr(client.private, 'session'):
        # Создаем httpx клиент с HTTP/2
        http2_client = httpx.Client(http2=True, verify=False)
        
        # Пробуем заменить session (может не сработать, т.к. instagrapi использует requests)
        # client.private.session = http2_client  # Это может не сработать
        
        print("⚠️  instagrapi использует requests, замена на httpx может не сработать")
        print("   Нужно модифицировать instagrapi или использовать wrapper")


if __name__ == "__main__":
    proxy = 'http://topfriendcorp_yandex_ru:66a204aa3a@37.77.146.158:30010'
    url = 'https://www.instagram.com'
    
    print("="*60)
    print("ТЕСТЫ ЗАПРОСОВ, ПОХОЖИХ НА БРАУЗЕР")
    print("="*60)
    
    print("\n1. httpx с HTTP/2:")
    try:
        response = request_with_httpx_http2(url, proxy)
        print(f"   ✅ HTTP {response.status_code}, версия: {response.http_version}")
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {str(e)[:100]}")
    
    print("\n2. curl_cffi с Chrome:")
    try:
        response = request_with_curl_cffi(url, proxy, 'chrome110')
        print(f"   ✅ HTTP {response.status_code}, размер: {len(response.content)} байт")
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {str(e)[:100]}")
    
    print("\n3. requests с браузерными заголовками:")
    try:
        response = request_with_requests_browser_headers(url, proxy)
        print(f"   ✅ HTTP {response.status_code}, размер: {len(response.content)} байт")
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {str(e)[:100]}")



