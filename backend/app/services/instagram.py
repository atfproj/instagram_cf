import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
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
)
from app.core.security import decrypt_data
from app.models.account import Account, AccountStatus
from app.models.activity_log import ActivityLog, LogStatus

logger = logging.getLogger(__name__)


def normalize_session_data(session_data: Any) -> Dict[str, Any]:
    """
    Нормализует session_data из БД для использования с instagrapi.
    Исправляет проблемы с JSON сериализацией (строки вместо словарей).
    
    Args:
        session_data: Данные сессии (может быть dict, str, или None)
        
    Returns:
        Нормализованный словарь для client.set_settings()
    """
    if not session_data:
        return {}
    
    # Если это строка, пытаемся распарсить
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except json.JSONDecodeError:
            logger.error(f"Не удалось распарсить session_data из строки")
            return {}
    
    # Если это не словарь, возвращаем пустой
    if not isinstance(session_data, dict):
        logger.error(f"session_data не является словарем: {type(session_data)}")
        return {}
    
    # Создаём копию чтобы не изменять оригинал
    normalized = {}
    
    # Копируем все поля
    for key, value in session_data.items():
        if key == 'device_settings':
            # device_settings должен быть словарём
            if isinstance(value, str):
                try:
                    normalized[key] = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"Не удалось распарсить device_settings из строки, создаю пустой dict")
                    normalized[key] = {}
            elif isinstance(value, dict):
                normalized[key] = value.copy()
                # Убеждаемся что android_version это int, не str
                if 'android_version' in normalized[key]:
                    try:
                        normalized[key]['android_version'] = int(normalized[key]['android_version'])
                    except (ValueError, TypeError):
                        logger.warning(f"android_version не может быть преобразован в int: {normalized[key]['android_version']}")
            else:
                logger.warning(f"device_settings имеет неожиданный тип: {type(value)}, создаю пустой dict")
                normalized[key] = {}
        elif key == 'uuids':
            # uuids должен быть словарём
            if isinstance(value, str):
                try:
                    normalized[key] = json.loads(value)
                except json.JSONDecodeError:
                    normalized[key] = {}
            elif isinstance(value, dict):
                normalized[key] = value.copy()
            else:
                normalized[key] = {}
        elif key == 'authorization_data':
            # authorization_data должен быть словарём
            if isinstance(value, str):
                try:
                    normalized[key] = json.loads(value)
                except json.JSONDecodeError:
                    normalized[key] = {}
            elif isinstance(value, dict):
                normalized[key] = value.copy()
            else:
                normalized[key] = {}
        elif key == 'cookies':
            # cookies должен быть словарём
            if isinstance(value, str):
                try:
                    normalized[key] = json.loads(value)
                except json.JSONDecodeError:
                    normalized[key] = {}
            elif isinstance(value, dict):
                normalized[key] = value.copy()
            else:
                normalized[key] = {}
        else:
            # Остальные поля копируем как есть
            normalized[key] = value
    
    return normalized


class InstagramService:
    """Сервис для работы с Instagram через instagrapi"""
    
    def __init__(self, account: Account):
        self.account = account
        # ВАЖНО: Создаем клиент БЕЗ запросов к Instagram
        # Client() не делает запросов при инициализации, только создает объект
        self.client = Client()
        logger.debug(f"Создан Client() для {account.username}, прокси еще не установлен")
        self._setup_client()
    
    def _setup_client(self):
        """Настройка клиента Instagram с прокси и сессией"""
        # Настройка прокси, если указан
        proxy_url = None
        
        # Сначала пытаемся получить прокси через proxy_id (новый способ)
        proxy_url = None
        logger.warning(f"[PROXY DEBUG] Проверка прокси для {self.account.username}: proxy_id={self.account.proxy_id}, proxy_url={self.account.proxy_url}")
        if self.account.proxy_id:
            if self.account.proxy:
                proxy_url = self.account.proxy.url
                logger.warning(f"[PROXY DEBUG] Прокси найден через relationship: {proxy_url[:50]}...")
            else:
                logger.warning(f"[PROXY DEBUG] proxy_id={self.account.proxy_id} указан, но self.account.proxy=None! Relationship не загружен!")
        # Если нет proxy_id, используем старый способ через proxy_url
        if not proxy_url and self.account.proxy_url:
            proxy_url = self.account.proxy_url
            logger.warning(f"[PROXY DEBUG] Прокси найден через proxy_url: {proxy_url[:50]}...")
        
        if proxy_url:
            try:
                # instagrapi принимает прокси как строку в формате http://user:pass@host:port
                # Убеждаемся, что формат правильный
                original_proxy_url = proxy_url
                if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                    # Если нет протокола, добавляем http://
                    proxy_url = f"http://{proxy_url}"
                
                logger.warning(f"[PROXY DEBUG] Устанавливаем прокси для {self.account.username}: {proxy_url[:60]}...")
                
                # ВАЖНО: Устанавливаем прокси ДО любых других операций
                # instagrapi использует requests под капотом, нужно установить прокси правильно
                # Упрощаем: используем только стандартный метод set_proxy (как работало раньше)
                self.client.set_proxy(proxy_url)
                logger.warning(f"[PROXY DEBUG] Прокси установлен через set_proxy() для {self.account.username}")
                
                # Проверяем, что прокси действительно установлен
                current_proxy = None
                # Проверяем разные возможные атрибуты
                for attr in ['_proxy', 'proxy', 'proxies', '_proxies']:
                    if hasattr(self.client, attr):
                        value = getattr(self.client, attr)
                        if value:
                            current_proxy = value
                            logger.warning(f"[PROXY DEBUG] Прокси найден в client.{attr}: {str(value)[:60]}")
                            break
                
                if not current_proxy:
                    logger.error(f"КРИТИЧНО: Прокси не установлен в клиенте для {self.account.username}!")
                    logger.error(f"Проверенные атрибуты: {[attr for attr in ['_proxy', 'proxy', 'proxies', '_proxies'] if hasattr(self.client, attr)]}")
                    # Не прерываем выполнение, но логируем критическую ошибку
                else:
                    logger.info(f"Прокси подтвержден в клиенте для {self.account.username}")
            except Exception as e:
                logger.error(f"КРИТИЧНО: Не удалось установить прокси для {self.account.username}: {e}", exc_info=True)
                # Если прокси обязателен, не продолжаем работу
                raise Exception(f"Не удалось установить прокси: {str(e)}")
        else:
            logger.warning(f"Прокси не указан для {self.account.username} - запросы будут идти с реального IP!")
        
        # Загрузка сессии, если есть
        if self.account.session_data:
            try:
                # Исправляем device_settings если это строка (проблема с JSON сериализацией)
                session_data = self.account.session_data.copy() if isinstance(self.account.session_data, dict) else self.account.session_data
                if isinstance(session_data, dict):
                    if 'device_settings' in session_data and isinstance(session_data['device_settings'], str):
                        import json
                        try:
                            session_data['device_settings'] = json.loads(session_data['device_settings'])
                        except:
                            logger.warning(f"Не удалось распарсить device_settings для {self.account.username}")
                            session_data['device_settings'] = {}
                
                # DEBUG: Проверяем что передаём в set_settings
                logger.warning(f"[DEBUG] ДО set_settings - device_settings тип: {type(session_data.get('device_settings'))}")
                logger.warning(f"[DEBUG] ДО set_settings - device_settings: {session_data.get('device_settings')}")
                
                self.client.set_settings(session_data)
                
                # DEBUG: Проверяем что получилось после set_settings
                logger.warning(f"[DEBUG] ПОСЛЕ set_settings - client.device_settings тип: {type(self.client.device_settings)}")
                logger.warning(f"[DEBUG] ПОСЛЕ set_settings - client.device_settings: {self.client.device_settings}")
                
                logger.info(f"Сессия загружена для {self.account.username} (не требуется повторный логин)")
                # Восстанавливаем device_id из сессии, если есть
                if self.account.device_id:
                    self.client.set_device(self.account.device_id)
                    logger.debug(f"Device ID восстановлен для {self.account.username}")
            except Exception as e:
                logger.warning(f"Не удалось загрузить сессию для {self.account.username}: {e}. Потребуется повторный логин.")
        else:
            logger.info(f"Сессия отсутствует для {self.account.username}. Потребуется авторизация.")
    
    def login(self, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Авторизация в Instagram
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "session_data": dict (если успешно),
                "requires_2fa": bool
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Расшифровываем пароль, если не передан
            if not password:
                password = decrypt_data(self.account.password)
            
            # Логируем информацию о прокси
            proxy_info = "без прокси"
            if self.account.proxy_id and self.account.proxy:
                proxy_info = f"прокси: {self.account.proxy.url[:50]}..."
            elif self.account.proxy_url:
                proxy_info = f"прокси: {self.account.proxy_url[:50]}..."
            
            logger.info(f"Попытка авторизации {self.account.username} ({proxy_info})")
            
            # КРИТИЧНО: Проверяем, что прокси действительно установлен ПЕРЕД авторизацией
            current_proxy = None
            proxy_attr = None
            # Проверяем все возможные атрибуты прокси
            for attr in ['_proxy', 'proxy', 'proxies', '_proxies']:
                if hasattr(self.client, attr):
                    value = getattr(self.client, attr)
                    if value:
                        current_proxy = value
                        proxy_attr = attr
                        break
            
            if not current_proxy:
                error_msg = f"КРИТИЧНО: Прокси не установлен в клиенте для {self.account.username} перед авторизацией! Запрос пойдет с реального IP!"
                logger.error(error_msg)
                # Проверяем, может быть прокси установлен в requests session
                if hasattr(self.client, 'private') and hasattr(self.client.private, 'session'):
                    session = self.client.private.session
                    if hasattr(session, 'proxies') and session.proxies:
                        logger.info(f"Прокси найден в session.proxies: {session.proxies}")
                        current_proxy = session.proxies
                    elif hasattr(session, '_proxies') and session._proxies:
                        logger.info(f"Прокси найден в session._proxies: {session._proxies}")
                        current_proxy = session._proxies
                
                if not current_proxy:
                    return {
                        "success": False,
                        "message": f"Ошибка: прокси не установлен. {error_msg}",
                        "proxy_error": True
                    }
            else:
                logger.info(f"Прокси подтвержден перед авторизацией для {self.account.username} в {proxy_attr}: {str(current_proxy)[:100]}")
            
            # Дополнительная проверка: смотрим, что использует requests под капотом
            if hasattr(self.client, 'private') and hasattr(self.client.private, 'session'):
                session = self.client.private.session
                if hasattr(session, 'proxies'):
                    logger.info(f"Прокси в requests session: {session.proxies}")
                if hasattr(session, 'trust_env'):
                    logger.info(f"trust_env в session: {session.trust_env}")
            
            # КРИТИЧНО: Проверяем прокси ПЕРЕД каждым запросом
            # instagrapi может создавать новую сессию при login(), нужно убедиться, что прокси установлен
            if hasattr(self.client, 'private') and hasattr(self.client.private, 'session'):
                session = self.client.private.session
                if hasattr(session, 'proxies') and not session.proxies:
                    # Если прокси не установлен в session, устанавливаем его
                    logger.warning(f"[PROXY DEBUG] Прокси не найден в session.proxies перед login, устанавливаем...")
                    if current_proxy:
                        if isinstance(current_proxy, str):
                            session.proxies = {'http': current_proxy, 'https': current_proxy}
                        else:
                            session.proxies = current_proxy
                        logger.warning(f"[PROXY DEBUG] Прокси установлен в session.proxies: {session.proxies}")
            
            # Небольшая задержка перед авторизацией (помогает избежать проблем с Instagram)
            import time
            time.sleep(2)
            
            # Попытка авторизации
            self.client.login(self.account.username, password)
            
            # Сохраняем сессию
            session_data = self.client.get_settings()
            
            # Сохраняем device_id и user_agent из settings
            device_id = session_data.get("device_id") or session_data.get("device_settings", {}).get("device_id")
            user_agent = session_data.get("user_agent")
            
            # Если device_id не найден, это нормально - он может быть None
            if not device_id:
                logger.info(f"device_id не найден в session_data для {self.account.username}, это нормально")
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "message": "Успешная авторизация",
                "session_data": session_data,
                "device_id": device_id,
                "user_agent": user_agent,
                "duration_ms": duration_ms
            }
            
        except TwoFactorRequired:
            return {
                "success": False,
                "message": "Требуется двухфакторная аутентификация",
                "requires_2fa": True
            }
            
        except ChallengeRequired as e:
            logger.warning(f"ChallengeRequired для {self.account.username}: {str(e)}")
            return {
                "success": False,
                "message": f"Требуется подтверждение: {str(e)}",
                "requires_challenge": True,
                "error_type": "ChallengeRequired"
            }
            
        except BadPassword as e:
            # Логируем полное сообщение от Instagram
            error_message = str(e)
            logger.error(f"BadPassword для {self.account.username}: {error_message}")
            
            # Пытаемся получить дополнительную информацию об ошибке
            error_details = {
                "error_type": "BadPassword",
                "message": error_message,
                "full_repr": repr(error_message)
            }
            
            # Проверяем, есть ли у исключения дополнительные атрибуты
            if hasattr(e, 'response'):
                try:
                    response = e.response
                    if hasattr(response, 'status_code'):
                        error_details["http_status"] = response.status_code
                        logger.error(f"[ERROR DETAILS] HTTP Status: {response.status_code}")
                    if hasattr(response, 'headers'):
                        error_details["response_headers"] = dict(response.headers)
                        logger.error(f"[ERROR DETAILS] Response Headers: {dict(response.headers)}")
                    if hasattr(response, 'text'):
                        error_details["response_body"] = response.text[:500]  # Первые 500 символов
                        logger.error(f"[ERROR DETAILS] Response Body: {response.text[:500]}")
                except:
                    pass
            
            # Проверяем, есть ли информация о черном списке IP
            if "blacklist" in error_message.lower() or "change your ip" in error_message.lower():
                logger.error(f"[PROXY DEBUG] Instagram сообщает, что IP в черном списке!")
                logger.error(f"[PROXY DEBUG] Полное сообщение от Instagram: {error_message}")
                logger.error(f"[PROXY DEBUG] Детали ошибки: {json.dumps(error_details, indent=2, default=str)}")
                return {
                    "success": False,
                    "message": f"Instagram сообщает, что IP адрес прокси в черном списке: {error_message}",
                    "error_type": "BadPassword",
                    "ip_blacklisted": True,
                    "error_details": error_details
                }
            
            logger.error(f"[ERROR DETAILS] Полная информация об ошибке: {json.dumps(error_details, indent=2, default=str)}")
            return {
                "success": False,
                "message": f"Неверный пароль. Сообщение от Instagram: {error_message}",
                "error_type": "BadPassword",
                "error_details": error_details
            }
            
        except (UserError, UserNotFound):
            return {
                "success": False,
                "message": "Неверный username или пользователь не найден"
            }
            
        except PleaseWaitFewMinutes as e:
            return {
                "success": False,
                "message": f"Слишком много попыток. Подождите несколько минут: {str(e)}"
            }
            
        except RateLimitError as e:
            return {
                "success": False,
                "message": f"Превышен лимит запросов: {str(e)}"
            }
            
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Логируем детали ошибки с полным traceback
            import traceback
            logger.error(f"Ошибка при авторизации {self.account.username}: {error_type}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Пытаемся получить дополнительную информацию об ошибке
            error_details = {
                "error_type": error_type,
                "message": str(e),
                "full_repr": repr(str(e))
            }
            
            # Проверяем, есть ли у исключения дополнительные атрибуты
            if hasattr(e, 'response'):
                try:
                    response = e.response
                    if hasattr(response, 'status_code'):
                        error_details["http_status"] = response.status_code
                        logger.error(f"[ERROR DETAILS] HTTP Status: {response.status_code}")
                    if hasattr(response, 'headers'):
                        error_details["response_headers"] = dict(response.headers)
                        logger.error(f"[ERROR DETAILS] Response Headers: {dict(response.headers)}")
                    if hasattr(response, 'text'):
                        error_details["response_body"] = response.text[:500]  # Первые 500 символов
                        logger.error(f"[ERROR DETAILS] Response Body: {response.text[:500]}")
                except:
                    pass
            
            logger.error(f"[ERROR DETAILS] Полная информация об ошибке: {json.dumps(error_details, indent=2, default=str)}")
            
            # Проверяем, используется ли прокси
            try:
                proxy_used = getattr(self.client, '_proxy', None) or getattr(self.client, 'proxy', None)
                if proxy_used:
                    logger.info(f"Прокси был установлен: {proxy_used}")
                else:
                    logger.warning(f"Прокси не найден в клиенте для {self.account.username}")
            except:
                pass
            
            # Проверяем, не связана ли ошибка с прокси
            if "proxy" in error_str or "tunnel" in error_str or "403" in error_str or "connection" in error_str or "502" in error_str or "bad gateway" in error_str:
                # Детальная диагностика для 502 Bad Gateway
                if "502" in error_str or "bad gateway" in error_str:
                    logger.error(f"[PROXY DEBUG] 502 Bad Gateway для {self.account.username}")
                    proxy_url = self.account.proxy.url if self.account.proxy else self.account.proxy_url
                    logger.error(f"[PROXY DEBUG] Прокси: {proxy_url[:60] if proxy_url else 'None'}...")
                    logger.error(f"[PROXY DEBUG] Это означает, что прокси не может подключиться к Instagram")
                    logger.error(f"[PROXY DEBUG] Возможные причины: Instagram блокирует этот прокси, прокси перегружен, или прокси неправильно настроен")
                
                return {
                    "success": False,
                    "message": f"Ошибка прокси: {str(e)}. Проверьте настройки прокси или попробуйте другой прокси.",
                    "proxy_error": True
                }
            
            # Проверяем специфичные ошибки Instagram
            if "sorry, there was a problem" in error_str:
                return {
                    "success": False,
                    "message": f"Instagram сообщает о проблеме с запросом. Возможные причины: аккаунт требует подтверждения, заблокирован, или проблема с прокси. Ошибка: {str(e)}",
                    "instagram_error": True
                }
            
            if "can't find an account" in error_str:
                return {
                    "success": False,
                    "message": f"Аккаунт не найден: {str(e)}. Проверьте правильность username/email.",
                    "account_not_found": True
                }
            
            return {
                "success": False,
                "message": f"Ошибка авторизации ({error_type}): {str(e)}"
            }
    
    def check_status(self) -> Dict[str, Any]:
        """Проверка статуса аккаунта (можно ли постить)"""
        start_time = datetime.utcnow()
        
        try:
            # Пытаемся получить информацию о профиле
            user_info = self.client.user_info_by_username(self.account.username)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "status": "active",
                "username": user_info.username,
                "follower_count": user_info.follower_count,
                "following_count": user_info.following_count,
                "media_count": user_info.media_count,
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "status": "login_required",
                "message": "Требуется повторная авторизация"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
    
    def post_photo(self, photo_path: str, caption: str) -> Dict[str, Any]:
        """
        Публикация фото
        
        Args:
            photo_path: Путь к файлу фото
            caption: Текст под фото
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "media_id": str (если успешно)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Конвертируем и изменяем размер изображения, если нужно
            from PIL import Image
            import os
            
            # Открываем изображение
            img = Image.open(photo_path)
            
            # Конвертируем в RGB (на случай если PNG с прозрачностью)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Проверяем и исправляем соотношение сторон
            width, height = img.size
            aspect_ratio = width / height
            
            # Instagram принимает:
            # - Квадрат: 1:1 (0.8 - 1.91)
            # - Вертикальное: 4:5 (0.8 - 1.0)
            # - Горизонтальное: 1.91:1 (1.91 - 1.0)
            # Минимальное соотношение: 0.8, максимальное: 1.91
            
            if aspect_ratio < 0.8:
                # Слишком узкое (высокое) - обрезаем до 4:5
                new_width = int(height * 0.8)
                left = (width - new_width) // 2
                img = img.crop((left, 0, left + new_width, height))
                logger.info(f"Изображение обрезано до соотношения 4:5 (было {aspect_ratio:.2f})")
            elif aspect_ratio > 1.91:
                # Слишком широкое - обрезаем до 1.91:1
                new_height = int(width / 1.91)
                top = (height - new_height) // 2
                img = img.crop((0, top, width, top + new_height))
                logger.info(f"Изображение обрезано до соотношения 1.91:1 (было {aspect_ratio:.2f})")
            
            # Проверяем формат файла и конвертируем в JPG, если нужно
            file_ext = os.path.splitext(photo_path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg']:
                logger.info(f"Конвертация изображения {photo_path} в JPG")
                # Создаём временный файл JPG
                jpg_path = os.path.splitext(photo_path)[0] + '.jpg'
                img.save(jpg_path, 'JPEG', quality=95)
                photo_path = jpg_path
                logger.info(f"Изображение сохранено как {photo_path}")
            else:
                # Сохраняем обратно, если изменили размер
                if aspect_ratio < 0.8 or aspect_ratio > 1.91:
                    img.save(photo_path, 'JPEG', quality=95)
                    logger.info(f"Изображение сохранено с исправленным соотношением сторон")
            
            # Публикуем фото
            media = self.client.photo_upload(photo_path, caption)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "message": "Фото успешно опубликовано",
                "media_id": str(media.id),
                "code": media.code,
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "message": "Требуется повторная авторизация",
                "requires_login": True
            }
            
        except PleaseWaitFewMinutes as e:
            return {
                "success": False,
                "message": f"Слишком много действий. Подождите: {str(e)}",
                "rate_limited": True
            }
            
        except RateLimitError as e:
            return {
                "success": False,
                "message": f"Превышен лимит запросов: {str(e)}",
                "rate_limited": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при публикации фото для {self.account.username}: {e}", exc_info=True)
            
            # Проверяем, не связана ли ошибка с прокси
            error_str = str(e).lower()
            if "proxy" in error_str or "connection" in error_str:
                return {
                    "success": False,
                    "message": f"Ошибка публикации (возможно проблема с прокси): {str(e)}",
                    "proxy_error": True
                }
            
            return {
                "success": False,
                "message": f"Ошибка публикации: {str(e)}"
            }
    
    def post_video(self, video_path: str, caption: str, thumbnail_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Публикация видео
        
        Args:
            video_path: Путь к файлу видео
            caption: Текст под видео
            thumbnail_path: Путь к превью (опционально)
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "media_id": str (если успешно)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Публикуем видео
            if thumbnail_path:
                media = self.client.video_upload(video_path, caption, thumbnail=thumbnail_path)
            else:
                media = self.client.video_upload(video_path, caption)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "message": "Видео успешно опубликовано",
                "media_id": str(media.id),
                "code": media.code,
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "message": "Требуется повторная авторизация",
                "requires_login": True
            }
            
        except PleaseWaitFewMinutes as e:
            return {
                "success": False,
                "message": f"Слишком много действий. Подождите: {str(e)}",
                "rate_limited": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при публикации видео для {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка публикации: {str(e)}"
            }
    
    def get_session_data(self) -> Dict[str, Any]:
        """Получить текущие данные сессии"""
        try:
            return self.client.get_settings()
        except Exception as e:
            logger.error(f"Ошибка при получении сессии: {e}")
            return {}
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Получить информацию о профиле аккаунта
        
        Returns:
            dict: {
                "success": bool,
                "profile": dict с информацией о профиле (bio, full_name, external_url и т.д.)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Получаем информацию о текущем аккаунте
            account_info = self.client.account_info()
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Логируем тип объекта для отладки
            logger.debug(f"account_info type: {type(account_info)}, dir: {dir(account_info)[:10] if hasattr(account_info, '__dict__') else 'N/A'}")
            
            # Безопасное извлечение полей (обрабатываем и объекты, и словари)
            def safe_get(obj, attr, default=None):
                """Безопасное получение атрибута или ключа"""
                try:
                    if isinstance(obj, dict):
                        return obj.get(attr, default)
                    return getattr(obj, attr, default)
                except Exception as e:
                    logger.warning(f"Ошибка при получении атрибута {attr}: {e}")
                    return default
            
            # Извлекаем данные с fallback значениями
            profile_data = {
                "username": safe_get(account_info, 'username', ''),
                "full_name": safe_get(account_info, 'full_name', ''),
                "biography": safe_get(account_info, 'biography', ''),
                "external_url": safe_get(account_info, 'external_url', ''),
                "profile_pic_url": safe_get(account_info, 'profile_pic_url') or safe_get(account_info, 'profile_pic_url_hd', ''),
                "follower_count": safe_get(account_info, 'follower_count', 0),
                "following_count": safe_get(account_info, 'following_count', 0),
                "media_count": safe_get(account_info, 'media_count', 0),
                "is_private": safe_get(account_info, 'is_private', False),
                "is_verified": safe_get(account_info, 'is_verified', False),
            }
            
            return {
                "success": True,
                "profile": profile_data,
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "message": "Требуется повторная авторизация",
                "requires_login": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении профиля {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка получения профиля: {str(e)}"
            }
    
    def update_profile(
        self,
        biography: Optional[str] = None,
        full_name: Optional[str] = None,
        external_url: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обновить информацию профиля
        
        Args:
            biography: Описание профиля (bio)
            full_name: Полное имя
            external_url: Внешняя ссылка
            phone_number: Номер телефона
            email: Email
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "profile": dict (если успешно)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Формируем словарь с параметрами для обновления
            # НЕ передаём email и phone_number, если они не указаны (Instagram требует подтверждённый email/телефон)
            update_params = {}
            if biography is not None and biography.strip():
                update_params['biography'] = biography
            if full_name is not None and full_name.strip():
                update_params['full_name'] = full_name
            if external_url is not None:
                # Пустая строка для external_url допустима (удаление ссылки)
                update_params['external_url'] = external_url
            # НЕ передаём phone_number и email, если они не указаны
            # Instagram требует подтверждённый email или телефон для обновления профиля
            
            if not update_params:
                return {
                    "success": False,
                    "message": "Не указаны параметры для обновления"
                }
            
            # Обновляем профиль
            account_info = self.client.account_edit(**update_params)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "message": "Профиль успешно обновлён",
                "profile": {
                    "username": account_info.username,
                    "full_name": account_info.full_name,
                    "biography": account_info.biography,
                    "external_url": account_info.external_url,
                },
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "message": "Требуется повторная авторизация",
                "requires_login": True
            }
            
        except PleaseWaitFewMinutes as e:
            return {
                "success": False,
                "message": f"Слишком много действий. Подождите: {str(e)}",
                "rate_limited": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка обновления профиля: {str(e)}"
            }
    
    def set_profile_privacy(self, is_private: bool) -> Dict[str, Any]:
        """
        Изменить приватность профиля (открыть/закрыть)
        
        Args:
            is_private: True - сделать приватным, False - сделать публичным
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "is_private": bool (если успешно)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Получаем текущее состояние профиля перед изменением
            current_info = self.client.account_info()
            current_is_private = getattr(current_info, 'is_private', None)
            logger.info(f"Текущая приватность профиля {self.account.username}: {current_is_private}, запрашиваем: {is_private}")
            
            # Если приватность уже такая, какая нужна, возвращаем успех
            if current_is_private == is_private:
                privacy_status = "приватным" if is_private else "публичным"
                return {
                    "success": True,
                    "message": f"Профиль уже {privacy_status}",
                    "is_private": current_is_private,
                    "duration_ms": 0
                }
            
            # Используем официальные методы instagrapi для изменения приватности
            # account_set_private() и account_set_public() - это безопасные методы библиотеки
            if is_private:
                # Делаем профиль приватным
                self.client.account_set_private()
                logger.info(f"Вызван account_set_private() для {self.account.username}")
            else:
                # Делаем профиль публичным
                self.client.account_set_public()
                logger.info(f"Вызван account_set_public() для {self.account.username}")
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Проверяем результат - получаем обновленную информацию
            updated_info = self.client.account_info()
            new_is_private = getattr(updated_info, 'is_private', None)
            
            logger.info(f"Приватность после изменения: {new_is_private}, ожидалось: {is_private}")
            
            # Проверяем, что изменение действительно произошло
            if new_is_private != is_private:
                logger.warning(f"Приватность не изменилась! Ожидалось {is_private}, получили {new_is_private}")
                return {
                    "success": False,
                    "message": f"Не удалось изменить приватность. Текущий статус: {'приватный' if new_is_private else 'публичный'}. Возможно, Instagram требует подтверждённый email или телефон для изменения приватности.",
                    "is_private": new_is_private
                }
            
            privacy_status = "приватным" if is_private else "публичным"
            
            return {
                "success": True,
                "message": f"Профиль успешно сделан {privacy_status}",
                "is_private": new_is_private,
                "duration_ms": duration_ms
            }
            
        except LoginRequired:
            return {
                "success": False,
                "message": "Требуется повторная авторизация",
                "requires_login": True
            }
            
        except PleaseWaitFewMinutes as e:
            return {
                "success": False,
                "message": f"Слишком много действий. Подождите: {str(e)}",
                "rate_limited": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при изменении приватности профиля {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка изменения приватности: {str(e)}"
            }

