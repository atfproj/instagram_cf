"""
Сервис для импорта готовых сессий Instagram из текста
Поддерживает форматы:
1. InstAccountsManager (2022-2023): username:password|UA|device_ids|IG-cookies||email
2. IAM New (2024): username:password|UA|device_ids|full_cookies||email
"""
import re
import json
import logging
from typing import Dict, Any, Optional
from instagrapi import Client

logger = logging.getLogger(__name__)


def parse_session_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Парсит строку с данными аккаунта
    Формат: username:password|User-Agent|device_ids|cookies||email_data
    
    Returns:
        dict с ключами: username, password, user_agent, device_id, phone_id, 
                       uuid, adid, cookies, authorization, sessionid, user_id
    """
    try:
        # Убираем лишние пробелы и переносы
        line = line.strip()
        
        # Разбиваем по основным разделителям
        parts = line.split('|')
        if len(parts) < 4:
            logger.error(f"Недостаточно частей в строке: {len(parts)}")
            return None
        
        # 1. Username и пароль
        credentials = parts[0].split(':')
        if len(credentials) < 2:
            logger.error("Не найден username или password")
            return None
        username = credentials[0]
        password = ':'.join(credentials[1:])  # Пароль может содержать ':'
        
        # 2. User-Agent
        user_agent = parts[1]
        
        # 3. Device IDs (4 UUID через ';')
        device_ids = parts[2].split(';')
        if len(device_ids) < 4:
            logger.error(f"Недостаточно device IDs: {len(device_ids)}")
            return None
        
        android_device_id = device_ids[0]  # android-xxx
        phone_id = device_ids[1]  # UUID
        uuid = device_ids[2]  # UUID
        adid = device_ids[3]  # UUID (advertising ID)
        
        # 4. Cookies (разделены ';')
        cookies_raw = parts[3]
        cookies_dict = {}
        
        # Парсим cookies
        cookie_pairs = cookies_raw.split(';')
        for pair in cookie_pairs:
            if ':' in pair and '=' not in pair:
                # Формат "key:value" (старый формат, только важные куки)
                key, value = pair.split(':', 1)
                cookies_dict[key.strip()] = value.strip()
            elif '=' in pair:
                # Формат "key=value" (новый формат, полные куки)
                key, value = pair.split('=', 1)
                cookies_dict[key.strip()] = value.strip()
        
        # Извлекаем важные данные
        authorization = cookies_dict.get('Authorization', '')
        sessionid = cookies_dict.get('sessionid', '')
        user_id = cookies_dict.get('IG-INTENDED-USER-ID') or cookies_dict.get('IG-U-DS-USER-ID') or cookies_dict.get('ds_user_id', '')
        mid = cookies_dict.get('X-MID') or cookies_dict.get('mid', '')
        www_claim = cookies_dict.get('X-IG-WWW-Claim', '')
        csrf_token = cookies_dict.get('csrftoken', '')
        ig_did = cookies_dict.get('ig_did', '')
        rur = cookies_dict.get('rur') or cookies_dict.get('IG-U-RUR') or cookies_dict.get('ig-u-rur', '')
        
        # 5. Email (опционально, через ||)
        email = None
        email_password = None
        if len(parts) > 4:
            email_data = parts[4].split('||')
            if email_data and email_data[0]:
                email_parts = email_data[0].split(':')
                if len(email_parts) >= 2:
                    email = email_parts[0]
                    email_password = ':'.join(email_parts[1:])
        
        result = {
            'username': username,
            'password': password,
            'user_agent': user_agent,
            'device_id': android_device_id,
            'phone_id': phone_id,
            'uuid': uuid,
            'adid': adid,
            'cookies': cookies_dict,
            'authorization': authorization,
            'sessionid': sessionid,
            'user_id': user_id,
            'mid': mid,
            'www_claim': www_claim,
            'csrf_token': csrf_token,
            'ig_did': ig_did,
            'rur': rur,
            'email': email,
            'email_password': email_password
        }
        
        logger.info(f"✅ Успешно распарсен аккаунт: {username}")
        logger.debug(f"   User ID: {user_id}")
        logger.debug(f"   Device ID: {android_device_id}")
        logger.debug(f"   Cookies: {len(cookies_dict)} шт")
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка парсинга строки: {e}")
        logger.exception(e)
        return None


def create_instagrapi_session(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Создает session_data для instagrapi из распарсенных данных
    
    Args:
        account_data: Результат parse_session_line()
        
    Returns:
        session_data dict для client.set_settings()
    """
    cookies = account_data.get('cookies', {})
    
    # Преобразуем cookies в правильный формат для instagrapi
    # instagrapi ожидает cookies как dict
    instagrapi_cookies = {}
    for key, value in cookies.items():
        if value:  # Только непустые значения
            instagrapi_cookies[key] = value
    
    # Извлекаем app_version из User-Agent
    user_agent = account_data['user_agent']
    app_version_match = re.search(r'Instagram\s+([\d.]+)', user_agent)
    app_version = app_version_match.group(1) if app_version_match else '385.0.0.47.74'
    
    # Извлекаем android_version
    android_version_match = re.search(r'Android\s+\((\d+)/', user_agent)
    android_version = int(android_version_match.group(1)) if android_version_match else 30
    
    # Извлекаем android_release
    android_release_match = re.search(r'Android\s+\(\d+/([\d.]+)', user_agent)
    android_release = android_release_match.group(1) if android_release_match else '11'
    
    # Извлекаем dpi
    dpi_match = re.search(r';\s*(\d+)dpi;', user_agent)
    dpi = f"{dpi_match.group(1)}dpi" if dpi_match else '480dpi'
    
    # Извлекаем resolution
    resolution_match = re.search(r';\s*(\d+x\d+);', user_agent)
    resolution = resolution_match.group(1) if resolution_match else '1080x1920'
    
    # Извлекаем manufacturer и device
    device_match = re.search(r';\s*([^;/]+?)[;/]\s*([^;]+);', user_agent)
    manufacturer = device_match.group(1).strip() if device_match else 'Samsung'
    device = device_match.group(2).strip() if device_match else 'SM-G960F'
    
    # Извлекаем model
    model_match = re.search(r';\s*([^;]+);\s*([^;]+);\s*([^;]+);\s*[a-z]{2}_[A-Z]{2};', user_agent)
    model = model_match.group(2).strip() if model_match else device
    
    # Извлекаем cpu
    cpu_match = re.search(r';\s*([^;]+);\s*[a-z]{2}_[A-Z]{2};', user_agent)
    cpu = cpu_match.group(1).strip() if cpu_match else 'exynos9820'
    
    # Извлекаем version_code
    version_code_match = re.search(r';\s*(\d+)\)$', user_agent)
    version_code = version_code_match.group(1) if version_code_match else '750732754'
    
    # Создаем session_data в формате instagrapi
    session_data = {
        'uuids': {
            'phone_id': account_data['phone_id'],
            'uuid': account_data['uuid'],
            'client_session_id': account_data['uuid'],  # Используем uuid
            'advertising_id': account_data['adid'],
            'android_device_id': account_data['device_id'],
        },
        'mid': account_data.get('mid'),
        'ig_www_claim': account_data.get('www_claim'),
        'authorization_data': {
            'sessionid': account_data.get('sessionid'),
            'ds_user_id': account_data.get('user_id'),
        },
        'cookies': instagrapi_cookies,
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
    
    # Добавляем user_id в корень (важно для instagrapi)
    if account_data.get('user_id'):
        session_data['user_id'] = account_data['user_id']
    
    logger.info(f"✅ Session data создан для {account_data['username']}")
    logger.debug(f"   User ID: {session_data.get('user_id')}")
    logger.debug(f"   Device settings: {session_data['device_settings']['manufacturer']} {session_data['device_settings']['device']}")
    
    return session_data


def validate_session(session_data: Dict[str, Any], proxy_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Валидирует сессию (опционально)
    
    Args:
        session_data: session_data для instagrapi
        proxy_url: URL прокси (опционально)
        
    Returns:
        dict: {'success': bool, 'message': str, 'user_info': dict или None}
    """
    try:
        client = Client()
        
        # Устанавливаем прокси, если указан
        if proxy_url:
            client.set_proxy(proxy_url)
            logger.info(f"Прокси установлен для валидации: {proxy_url[:50]}...")
        
        # Устанавливаем session_data
        client.set_settings(session_data)
        logger.info("Session data установлен")
        
        # Проверяем сессию
        user_info = client.account_info()
        
        logger.info(f"✅ Сессия валидна! Username: {user_info.username}, User ID: {user_info.pk}")
        
        # Безопасное извлечение полей
        def safe_get(obj, attr, default=None):
            """Безопасное получение атрибута или ключа"""
            try:
                if isinstance(obj, dict):
                    return obj.get(attr, default)
                else:
                    return getattr(obj, attr, default)
            except (AttributeError, KeyError, TypeError):
                return default

        return {
            'success': True,
            'message': 'Сессия валидна',
            'user_info': {
                'username': safe_get(user_info, 'username', ''),
                'full_name': safe_get(user_info, 'full_name', ''),
                'user_id': safe_get(user_info, 'pk', 0),
                'is_private': safe_get(user_info, 'is_private', False),
                'is_verified': user_info.is_verified,
                'biography': user_info.biography,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка валидации сессии: {type(e).__name__}: {str(e)}")
        return {
            'success': False,
            'message': f'Ошибка валидации: {type(e).__name__}: {str(e)[:200]}',
            'user_info': None
        }


