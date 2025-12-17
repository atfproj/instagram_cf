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


class InstagramService:
    """Сервис для работы с Instagram через instagrapi"""
    
    def __init__(self, account: Account):
        self.account = account
        self.client = Client()
        self._setup_client()
    
    def _setup_client(self):
        """Настройка клиента Instagram с прокси и сессией"""
        # Настройка прокси, если указан
        proxy_url = None
        
        # Сначала пытаемся получить прокси через proxy_id (новый способ)
        if self.account.proxy_id and self.account.proxy:
            proxy_url = self.account.proxy.url
        # Если нет proxy_id, используем старый способ через proxy_url
        elif self.account.proxy_url:
            proxy_url = self.account.proxy_url
        
        if proxy_url:
            try:
                # instagrapi принимает прокси как строку в формате http://user:pass@host:port
                # Убеждаемся, что формат правильный
                if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                    # Если нет протокола, добавляем http://
                    proxy_url = f"http://{proxy_url}"
                
                self.client.set_proxy(proxy_url)
                logger.info(f"Прокси установлен для {self.account.username}: {proxy_url[:50]}...")
            except Exception as e:
                logger.error(f"Не удалось установить прокси для {self.account.username}: {e}", exc_info=True)
                # Не прерываем выполнение, но логируем ошибку
        
        # Загрузка сессии, если есть
        if self.account.session_data:
            try:
                self.client.set_settings(self.account.session_data)
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
            
            # Проверяем, что прокси действительно установлен
            try:
                current_proxy = getattr(self.client, '_proxy', None) or getattr(self.client, 'proxy', None)
                if current_proxy:
                    logger.info(f"Прокси в клиенте: {current_proxy}")
                else:
                    logger.warning(f"Прокси не найден в клиенте, хотя должен быть установлен")
            except Exception as e:
                logger.warning(f"Не удалось проверить прокси в клиенте: {e}")
            
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
            return {
                "success": False,
                "message": f"Требуется подтверждение: {str(e)}",
                "requires_challenge": True
            }
            
        except BadPassword:
            return {
                "success": False,
                "message": "Неверный пароль"
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
            if "proxy" in error_str or "tunnel" in error_str or "403" in error_str or "connection" in error_str:
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
            # Изменяем приватность профиля
            account_info = self.client.account_edit(is_private=is_private)
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            privacy_status = "приватным" if is_private else "публичным"
            
            return {
                "success": True,
                "message": f"Профиль успешно сделан {privacy_status}",
                "is_private": account_info.is_private if hasattr(account_info, 'is_private') else is_private,
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

