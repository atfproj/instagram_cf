#!/usr/bin/env python3
"""
Тестовый скрипт для проверки авторизации в Instagram
"""
import json
import sys
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword,
    UserError,
    PleaseWaitFewMinutes,
    RateLimitError,
    UserNotFound,
    UnknownError
)

def test_login(username, password, proxy_url=None):
    """Тест авторизации с указанным прокси"""
    print(f"\n{'='*60}")
    print(f"Тест авторизации для: {username}")
    if proxy_url:
        print(f"Прокси: {proxy_url[:50]}...")
    else:
        print("Без прокси")
    print(f"{'='*60}\n")
    
    client = Client()
    
    # Установка прокси, если указан
    if proxy_url:
        try:
            # Убеждаемся, что формат правильный
            if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                proxy_url = f"http://{proxy_url}"
            
            print(f"[1] Устанавливаю прокси: {proxy_url[:50]}...")
            client.set_proxy(proxy_url)
            print(f"[✓] Прокси установлен")
            
            # Проверяем, что прокси действительно установлен
            try:
                proxy_attr = getattr(client, '_proxy', None) or getattr(client, 'proxy', None)
                if proxy_attr:
                    print(f"[✓] Прокси подтвержден в клиенте: {proxy_attr}")
                else:
                    print(f"[!] Прокси не найден в атрибутах клиента")
            except Exception as e:
                print(f"[!] Не удалось проверить прокси в клиенте: {e}")
                
        except Exception as e:
            print(f"[✗] Ошибка установки прокси: {e}")
            return False
    
    # Попытка авторизации
    try:
        print(f"[2] Пытаюсь авторизоваться...")
        import time
        time.sleep(2)  # Небольшая задержка перед авторизацией
        client.login(username, password)
        print(f"[✓] Успешная авторизация!")
        
        # Получаем сессию
        session_data = client.get_settings()
        print(f"[✓] Сессия получена")
        
        # Получаем device_id и user_agent из сессии
        device_id = session_data.get("device_id") or session_data.get("device_settings", {}).get("device_id")
        user_agent = session_data.get("user_agent")
        
        print(f"\n[Результат]")
        print(f"  - device_id: {device_id}")
        print(f"  - user_agent: {user_agent[:50] if user_agent else 'None'}...")
        print(f"  - Сессия сохранена: {len(str(session_data))} символов")
        
        return True
        
    except TwoFactorRequired:
        print(f"[!] Требуется двухфакторная аутентификация")
        return False
        
    except ChallengeRequired as e:
        print(f"[!] Требуется подтверждение: {e}")
        return False
        
    except BadPassword:
        print(f"[✗] Неверный пароль")
        return False
        
    except (UserError, UserNotFound) as e:
        print(f"[✗] Аккаунт не найден или неверный username: {e}")
        return False
        
    except PleaseWaitFewMinutes as e:
        print(f"[!] Слишком много попыток. Подождите: {e}")
        return False
        
    except RateLimitError as e:
        print(f"[!] Превышен лимит запросов: {e}")
        return False
        
    except UnknownError as e:
        print(f"[✗] Неизвестная ошибка Instagram: {e.message if hasattr(e, 'message') else str(e)}")
        # Пытаемся получить больше информации
        if hasattr(e, 'response'):
            print(f"    Response: {e.response}")
        if hasattr(e, 'last_json'):
            print(f"    Last JSON: {e.last_json}")
        # Пытаемся получить детали из исключения
        import traceback
        print(f"    Детали ошибки:")
        traceback.print_exc()
        return False
        
    except Exception as e:
        error_str = str(e).lower()
        error_type = type(e).__name__
        print(f"[✗] Ошибка ({error_type}): {str(e)}")
        
        # Проверяем, связана ли ошибка с прокси
        if "proxy" in error_str or "connection" in error_str or "403 forbidden" in error_str:
            print(f"    [Возможная проблема с прокси]")
        
        import traceback
        print(f"\n[Traceback]:")
        traceback.print_exc()
        return False


def load_proxies():
    """Загрузка прокси из proxy.json"""
    try:
        with open('proxy.json', 'r') as f:
            proxies = json.load(f)
        return proxies
    except Exception as e:
        print(f"Ошибка загрузки proxy.json: {e}")
        return []


def format_proxy_url(proxy_data):
    """Форматирование URL прокси из данных"""
    username = proxy_data.get('username', '')
    password = proxy_data.get('password', '')
    ip = proxy_data.get('ip', '')
    port = proxy_data.get('port', '')
    
    if username and password:
        return f"http://{username}:{password}@{ip}:{port}"
    else:
        return f"http://{ip}:{port}"


if __name__ == "__main__":
    # Параметры для теста
    if len(sys.argv) < 3:
        print("Использование: python test_instagram_login.py <username> <password> [proxy_index]")
        print("\nПримеры:")
        print("  python test_instagram_login.py username password")
        print("  python test_instagram_login.py username password 0  # с первым прокси из proxy.json")
        print("  python test_instagram_login.py username password http://user:pass@ip:port  # с конкретным прокси")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    proxy_url = None
    
    # Если указан третий аргумент
    if len(sys.argv) >= 4:
        arg3 = sys.argv[3]
        
        # Если это число - индекс прокси из proxy.json
        if arg3.isdigit():
            proxies = load_proxies()
            index = int(arg3)
            if 0 <= index < len(proxies):
                proxy_url = format_proxy_url(proxies[index])
                print(f"Использую прокси #{index} из proxy.json")
            else:
                print(f"Ошибка: индекс {index} вне диапазона (0-{len(proxies)-1})")
                sys.exit(1)
        # Иначе - это URL прокси
        else:
            proxy_url = arg3
    
    # Запуск теста
    success = test_login(username, password, proxy_url)
    
    if success:
        print(f"\n{'='*60}")
        print("✓ ТЕСТ ПРОЙДЕН УСПЕШНО")
        print(f"{'='*60}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print("✗ ТЕСТ НЕ ПРОЙДЕН")
        print(f"{'='*60}\n")
        sys.exit(1)

