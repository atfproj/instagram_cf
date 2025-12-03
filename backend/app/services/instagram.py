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
        if self.account.proxy_url:
            try:
                # instagrapi принимает прокси как строку
                self.client.set_proxy(self.account.proxy_url)
            except Exception as e:
                logger.warning(f"Не удалось установить прокси для {self.account.username}: {e}")
        
        # Загрузка сессии, если есть
        if self.account.session_data:
            try:
                self.client.set_settings(self.account.session_data)
                # Восстанавливаем device_id из сессии, если есть
                if self.account.device_id:
                    self.client.set_device(self.account.device_id)
            except Exception as e:
                logger.warning(f"Не удалось загрузить сессию для {self.account.username}: {e}")
    
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
            
            # Попытка авторизации
            self.client.login(self.account.username, password)
            
            # Сохраняем сессию
            session_data = self.client.get_settings()
            
            # Сохраняем device_id и user_agent
            device_id = self.client.device_id
            user_agent = self.client.user_agent
            
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
            logger.error(f"Ошибка при авторизации {self.account.username}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Неизвестная ошибка: {str(e)}"
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

