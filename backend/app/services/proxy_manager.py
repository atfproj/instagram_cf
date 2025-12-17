import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.proxy import Proxy, ProxyStatus, ProxyType
from app.models.account import Account, AccountStatus

logger = logging.getLogger(__name__)


class ProxyManager:
    """Менеджер для работы с прокси"""
    
    @staticmethod
    def check_proxy(proxy: Proxy, timeout: int = 10) -> Dict[str, Any]:
        """
        Проверка работоспособности прокси
        
        Args:
            proxy: Объект прокси
            timeout: Таймаут проверки в секундах
            
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "response_time_ms": int (если успешно),
                "error": str (если ошибка)
            }
        """
        start_time = datetime.utcnow()
        instagram_accessible = False  # Инициализация переменной
        
        try:
            # Настройка прокси для httpx
            proxies = {
                "http://": proxy.url,
                "https://": proxy.url
            }
            
            # Тест 1: Проверка базовой работоспособности
            with httpx.Client(proxies=proxies, timeout=timeout) as client:
                try:
                    response = client.get("https://httpbin.org/ip", follow_redirects=True)
                    if response.status_code != 200:
                        return {
                            "success": False,
                            "message": f"Прокси вернул статус {response.status_code}",
                            "error": f"HTTP {response.status_code}"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Ошибка подключения к тестовому серверу: {str(e)}",
                        "error": "ConnectionError"
                    }
            
            # Тест 2: Проверка доступа к Instagram (важно для работы)
            try:
                with httpx.Client(proxies=proxies, timeout=timeout) as client:
                    # Пытаемся подключиться к Instagram
                    response = client.get("https://i.instagram.com/api/v1/launcher/sync/", follow_redirects=True, timeout=timeout)
                    # Если получили ответ (даже ошибку), значит прокси пропускает Instagram
                    instagram_accessible = True
            except httpx.ProxyError as e:
                error_str = str(e).lower()
                if "403" in error_str or "forbidden" in error_str:
                    return {
                        "success": False,
                        "message": "Прокси блокирует доступ к Instagram (403 Forbidden). Прокси не подходит для работы с Instagram.",
                        "error": "InstagramBlocked",
                        "instagram_accessible": False
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Ошибка подключения к Instagram через прокси: {str(e)}",
                        "error": "InstagramConnectionError"
                    }
            except Exception as e:
                # Другие ошибки (таймаут и т.д.) - считаем что прокси работает, но может быть медленным
                instagram_accessible = False
                logger.warning(f"Не удалось проверить доступ к Instagram через прокси {proxy.url}: {e}")
            
            # Если дошли сюда, прокси работает
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "message": "Прокси работает" + (" и доступен Instagram" if instagram_accessible else " (Instagram не проверен)"),
                "response_time_ms": duration_ms,
                "instagram_accessible": instagram_accessible
            }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "Таймаут при проверке прокси",
                "error": "Timeout"
            }
            
        except httpx.ProxyError as e:
            return {
                "success": False,
                "message": f"Ошибка подключения к прокси: {str(e)}",
                "error": "ProxyError"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке прокси {proxy.url}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Неизвестная ошибка: {str(e)}",
                "error": str(type(e).__name__)
            }
    
    @staticmethod
    def assign_proxy_to_account(db: Session, account: Account) -> Optional[Proxy]:
        """
        Назначить свободный прокси аккаунту
        
        Args:
            db: Сессия БД
            account: Аккаунт
            
        Returns:
            Proxy: Назначенный прокси или None, если нет доступных
        """
        # Ищем активный прокси, который не назначен или назначен минимальному количеству аккаунтов
        available_proxies = db.query(Proxy).filter(
            Proxy.status == ProxyStatus.ACTIVE
        ).all()
        
        if not available_proxies:
            logger.warning("Нет доступных прокси для назначения")
            return None
        
        # Выбираем прокси с минимальным количеством назначенных аккаунтов
        best_proxy = min(
            available_proxies,
            key=lambda p: len(p.assigned_accounts) if p.assigned_accounts else 0
        )
        
        # Обновляем список назначенных аккаунтов
        assigned = best_proxy.assigned_accounts or []
        if str(account.id) not in assigned:
            assigned.append(str(account.id))
            best_proxy.assigned_accounts = assigned
        
        # Обновляем аккаунт
        account.proxy_url = best_proxy.url
        account.proxy_type = best_proxy.type.value
        
        db.commit()
        db.refresh(best_proxy)
        
        logger.info(f"Прокси {best_proxy.url} назначен аккаунту {account.username}")
        return best_proxy
    
    @staticmethod
    def rotate_proxy_for_account(db: Session, account: Account, reason: str = "error") -> Optional[Proxy]:
        """
        Ротация прокси для аккаунта (переключение на другой прокси)
        
        Args:
            db: Сессия БД
            account: Аккаунт
            reason: Причина ротации
            
        Returns:
            Proxy: Новый прокси или None
        """
        # Удаляем аккаунт из старого прокси
        if account.proxy_url:
            old_proxy = db.query(Proxy).filter(Proxy.url == account.proxy_url).first()
            if old_proxy and old_proxy.assigned_accounts:
                assigned = old_proxy.assigned_accounts.copy()
                if str(account.id) in assigned:
                    assigned.remove(str(account.id))
                    old_proxy.assigned_accounts = assigned
                    db.commit()
        
        # Назначаем новый прокси
        new_proxy = ProxyManager.assign_proxy_to_account(db, account)
        
        if new_proxy:
            logger.info(f"Прокси для {account.username} ротирован: {reason}. Новый прокси: {new_proxy.url}")
        else:
            logger.warning(f"Не удалось найти новый прокси для {account.username}")
            account.status = AccountStatus.PROXY_ERROR
        
        db.commit()
        return new_proxy
    
    @staticmethod
    def update_proxy_status(
        db: Session,
        proxy: Proxy,
        check_result: Dict[str, Any]
    ):
        """
        Обновить статус прокси на основе результата проверки
        
        Args:
            db: Сессия БД
            proxy: Прокси
            check_result: Результат проверки от check_proxy()
        """
        proxy.last_check_at = datetime.utcnow()
        
        if check_result["success"]:
            # Обновляем success_rate (простое скользящее среднее)
            proxy.success_rate = (proxy.success_rate * 0.9) + (1.0 * 0.1)
            
            if proxy.status != ProxyStatus.ACTIVE:
                proxy.status = ProxyStatus.ACTIVE
                logger.info(f"Прокси {proxy.url} восстановлен")
        else:
            # Уменьшаем success_rate
            proxy.success_rate = proxy.success_rate * 0.9
            
            # Если success_rate упал ниже 0.5, помечаем как failed
            if proxy.success_rate < 0.5:
                proxy.status = ProxyStatus.FAILED
                logger.warning(f"Прокси {proxy.url} помечен как failed (success_rate: {proxy.success_rate:.2f})")
        
        db.commit()

