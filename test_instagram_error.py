#!/usr/bin/env python3
"""
Скрипт для тестирования точной ошибки от Instagram при запросах с прокси
"""
import sys
sys.path.insert(0, 'backend')

from instagrapi import Client
from instagrapi.exceptions import *
import traceback
import json

def test_instagram_error(proxy_url: str, username: str, password: str):
    """Тестирует авторизацию и выводит точную ошибку"""
    print("="*60)
    print("ТЕСТ: Авторизация в Instagram через прокси")
    print("="*60)
    print(f"Прокси: {proxy_url[:60]}...")
    print(f"Username: {username}")
    print("="*60)
    
    try:
        client = Client()
        client.set_proxy(proxy_url)
        print("✅ Прокси установлен")
        
        print("\nПробуем авторизацию...")
        client.login(username, password)
        print("✅✅✅ УСПЕХ! Авторизация прошла!")
        return
        
    except BadPassword as e:
        error_msg = str(e)
        print(f"\n❌ BadPassword (Неверный пароль или IP в черном списке):")
        print(f"   Тип исключения: {type(e).__name__}")
        print(f"   Сообщение: {error_msg}")
        print(f"   Длина сообщения: {len(error_msg)} символов")
        print(f"\n   Полный текст (repr):")
        print(f"   {repr(error_msg)}")
        
        # Проверяем наличие ключевых слов
        if "blacklist" in error_msg.lower():
            print("\n   ⚠️  Содержит 'blacklist' - IP в черном списке!")
        if "change your ip" in error_msg.lower():
            print("\n   ⚠️  Содержит 'change your ip' - нужно сменить IP!")
        if "password" in error_msg.lower():
            print("\n   ⚠️  Содержит 'password' - возможно, неверный пароль")
            
    except ProxyError as e:
        error_msg = str(e)
        print(f"\n❌ ProxyError (Ошибка прокси):")
        print(f"   Тип исключения: {type(e).__name__}")
        print(f"   Сообщение: {error_msg}")
        print(f"   Полный текст (repr):")
        print(f"   {repr(error_msg)}")
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"\n❌ Ошибка ({error_type}):")
        print(f"   Сообщение: {error_msg}")
        print(f"   Длина сообщения: {len(error_msg)} символов")
        print(f"\n   Полный текст (repr):")
        print(f"   {repr(error_msg)}")
        
        # Проверяем наличие ключевых слов
        keywords = ["502", "bad gateway", "timeout", "connection", "tunnel", "403", "forbidden"]
        found_keywords = [kw for kw in keywords if kw in error_msg.lower()]
        if found_keywords:
            print(f"\n   Найдены ключевые слова: {', '.join(found_keywords)}")
        
        print(f"\n   Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    # Тестовые данные
    proxy = "http://topfriendcorp_yandex_ru:66a204aa3a@37.77.146.158:30010"
    username = "mila_lazarevaw"
    password = "z5EtifcdPeIz"
    
    test_instagram_error(proxy, username, password)



