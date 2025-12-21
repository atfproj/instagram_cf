"""
Сервис для импорта аккаунтов из формата InstAccountsManager
Формат: username:password|User-Agent|device_ids|cookies||email:password
"""
import logging
import re
from typing import Dict, Any, Optional, List
from instagrapi import Client

logger = logging.getLogger(__name__)


def parse_account_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Парсит строку аккаунта из формата InstAccountsManager
    
    Формат:
    username:password|User-Agent|device_id;phone_id;uuid;adid|cookies||email:password
    
    Returns:
        dict с данными аккаунта или None если строка невалидна
    """
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('Заказ') or line.startswith('=') or line.startswith('↓'):
        return None
    
    parts = line.split('|')
    if len(parts) < 4:
        logger.warning(f"Неверный формат строки (меньше 4 частей): {line[:50]}...")
        return None
    
    try:
        # 1. username:password
        username_password = parts[0].split(':')
        if len(username_password) != 2:
            logger.warning(f"Неверный формат username:password: {parts[0]}")
            return None
        username = username_password[0]
        password = username_password[1]
        
        # 2. User-Agent
        user_agent = parts[1]
        
        # 3. Device IDs (device_id;phone_id;uuid;adid)
        device_ids = parts[2].split(';')
        if len(device_ids) < 4:
            logger.warning(f"Неверный формат device IDs: {parts[2]}")
            return None
        device_id = device_ids[0]
        phone_id = device_ids[1] if len(device_ids) > 1 else None
        uuid = device_ids[2] if len(device_ids) > 2 else None
        adid = device_ids[3] if len(device_ids) > 3 else None
        
        # 4. Cookies
        cookies_str = parts[3]
        cookies = {}
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        # 5. Email:password (опционально)
        email = None
        email_password = None
        if len(parts) > 4 and parts[4]:
            email_parts = parts[4].split(':')
            if len(email_parts) >= 2:
                email = email_parts[0]
                email_password = email_parts[1]
        
        return {
            'username': username,
            'password': password,
            'user_agent': user_agent,
            'device_id': device_id,
            'phone_id': phone_id,
            'uuid': uuid,
            'adid': adid,
            'cookies': cookies,
            'email': email,
            'email_password': email_password
        }
        
    except Exception as e:
        logger.error(f"Ошибка парсинга строки {line[:50]}...: {e}")
        return None


def create_session_data_from_import(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Создает session_data для instagrapi из импортированных данных
    
    Args:
        account_data: Данные аккаунта из parse_account_line
        
    Returns:
        session_data dict для instagrapi
    """
    # Извлекаем данные из cookies
    cookies = account_data.get('cookies', {})
    
    # Преобразуем device IDs в формат instagrapi
    uuids = {
        'android_device_id': account_data['device_id'],
        'phone_id': account_data.get('phone_id'),
        'uuid': account_data.get('uuid'),
        'advertising_id': account_data.get('adid'),
    }
    
    # Извлекаем authorization_data из Authorization cookie
    authorization_data = {}
    if 'Authorization' in cookies:
        auth_value = cookies['Authorization']
        if auth_value.startswith('Bearer IGT:2:'):
            # Извлекаем токен
            token = auth_value.replace('Bearer IGT:2:', '')
            authorization_data = {
                'ds_user_id': cookies.get('IG-INTENDED-USER-ID') or cookies.get('IG-U-DS-USER-ID'),
                'sessionid': token  # instagrapi может использовать это
            }
    
    # Преобразуем cookies в правильный формат (dict, не строка)
    cookies_dict = {}
    for key, value in cookies.items():
        if value:  # Только непустые значения
            cookies_dict[key] = value
    
    # Создаем device_settings в правильном формате
    # android_version должен быть числом (int), остальные - строками
    android_version_str = _extract_android_version(account_data['user_agent'])
    android_version_int = int(android_version_str.split('.')[0]) if android_version_str else 26
    
    device_settings = {
        'app_version': _extract_app_version(account_data['user_agent']),
        'android_version': android_version_int,  # Должно быть числом
        'android_release': _extract_android_release(account_data['user_agent']),
        'dpi': _extract_dpi(account_data['user_agent']),
        'resolution': _extract_resolution(account_data['user_agent']),
        'manufacturer': _extract_manufacturer(account_data['user_agent']),
        'device': _extract_device(account_data['user_agent']),
        'model': _extract_model(account_data['user_agent']),
        'cpu': _extract_cpu(account_data['user_agent']),
        'version_code': _extract_version_code(account_data['user_agent']),
    }
    
    # Убираем None значения из device_settings
    device_settings = {k: v for k, v in device_settings.items() if v is not None}
    
    session_data = {
        'uuids': uuids,
        'mid': cookies.get('X-MID'),
        'ig_www_claim': cookies.get('X-IG-WWW-Claim'),
        'authorization_data': authorization_data,
        'cookies': cookies_dict,  # Используем dict, а не исходные cookies
        'device_settings': device_settings,
        'user_agent': account_data['user_agent'],
    }
    
    # Извлекаем user_id из cookies
    if 'IG-INTENDED-USER-ID' in cookies:
        session_data['user_id'] = cookies['IG-INTENDED-USER-ID']
    elif 'IG-U-DS-USER-ID' in cookies:
        session_data['user_id'] = cookies['IG-U-DS-USER-ID']
    
    # Устанавливаем device_id в корне session_data (instagrapi ожидает его там)
    if account_data.get('device_id'):
        session_data['device_id'] = account_data['device_id']
    
    return session_data


def _extract_app_version(user_agent: str) -> str:
    """Извлекает версию приложения из User-Agent"""
    match = re.search(r'Instagram\s+([\d.]+)', user_agent)
    return match.group(1) if match else '354.2.0.47.100'


def _extract_android_version(user_agent: str) -> str:
    """Извлекает версию Android из User-Agent"""
    match = re.search(r'Android\s+\((\d+)/([\d.]+)', user_agent)
    return match.group(2) if match else '11'


def _extract_android_release(user_agent: str) -> str:
    """Извлекает release Android из User-Agent"""
    match = re.search(r'Android\s+\((\d+)/([\d.]+)', user_agent)
    return match.group(1) if match else '30'


def _extract_dpi(user_agent: str) -> str:
    """Извлекает DPI из User-Agent"""
    match = re.search(r'(\d+)dpi', user_agent)
    return match.group(1) if match else '420'


def _extract_resolution(user_agent: str) -> str:
    """Извлекает разрешение из User-Agent"""
    match = re.search(r'(\d+x\d+)', user_agent)
    return match.group(1) if match else '1080x1920'


def _extract_manufacturer(user_agent: str) -> str:
    """Извлекает производителя из User-Agent"""
    match = re.search(r';\s*([^/]+)/', user_agent)
    return match.group(1) if match else 'samsung'


def _extract_device(user_agent: str) -> str:
    """Извлекает устройство из User-Agent"""
    match = re.search(r';\s*([^;]+);\s*([^;]+);', user_agent)
    return match.group(2) if match else 'SM-G973F'


def _extract_model(user_agent: str) -> str:
    """Извлекает модель из User-Agent"""
    match = re.search(r';\s*([^;]+);\s*([^;]+);\s*([^;]+);', user_agent)
    return match.group(3) if match else 'SM-G973F'


def _extract_cpu(user_agent: str) -> str:
    """Извлекает CPU из User-Agent"""
    match = re.search(r';\s*([^;]+);\s*([^;]+);\s*([^;]+);\s*([^;]+);', user_agent)
    return match.group(4) if match else 'exynos9820'


def _extract_version_code(user_agent: str) -> str:
    """Извлекает version_code из User-Agent"""
    match = re.search(r';\s*(\d+)\)', user_agent)
    return match.group(1) if match else '314665256'


def validate_imported_session(account_data: Dict[str, Any], proxy_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Валидирует импортированную сессию через instagrapi
    
    Args:
        account_data: Данные аккаунта из parse_account_line
        proxy_url: URL прокси (опционально)
        
    Returns:
        dict с результатом валидации
    """
    try:
        client = Client()
        
        # Устанавливаем прокси, если указан
        if proxy_url:
            client.set_proxy(proxy_url)
        
        # Создаем session_data
        session_data = create_session_data_from_import(account_data)
        
        # Устанавливаем session_data
        client.set_settings(session_data)
        
        # Устанавливаем device_id
        if account_data.get('device_id'):
            client.set_device(account_data['device_id'])
        
        # Проверяем, что сессия работает
        account_info = client.account_info()
        
        return {
            'success': True,
            'message': 'Сессия валидна',
            'username': account_info.username,
            'user_id': account_info.pk,
            'session_data': session_data
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации сессии для {account_data.get('username')}: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Ошибка валидации: {str(e)}',
            'error': str(e)
        }

