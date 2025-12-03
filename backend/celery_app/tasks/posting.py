import logging
import random
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID
from celery import Task
from sqlalchemy.orm import Session
from backend.celery_app.config import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.post import Post, PostExecution, PostStatus, PostExecutionStatus
from app.models.account import Account, AccountStatus
from app.services.instagram import InstagramService
from app.services.translator import translator_service
from app.utils.logging import log_activity, update_account_status
from app.models.activity_log import LogStatus

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Базовый класс для задач с доступом к БД"""
    
    _db: Session = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Закрываем сессию БД после выполнения задачи"""
        if self._db:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="instagram_cf.post_to_instagram",
    max_retries=3,
    default_retry_delay=300  # 5 минут между попытками
)
def task_post_to_instagram(
    self,
    post_id: str,
    account_id: str,
    execution_id: str
) -> Dict[str, Any]:
    """
    Задача для публикации поста на один аккаунт Instagram
    
    Args:
        post_id: UUID поста
        account_id: UUID аккаунта
        execution_id: UUID записи PostExecution
        
    Returns:
        dict: Результат публикации
    """
    db = self.db
    
    try:
        # Получаем данные из БД
        post = db.query(Post).filter(Post.id == UUID(post_id)).first()
        account = db.query(Account).filter(Account.id == UUID(account_id)).first()
        execution = db.query(PostExecution).filter(PostExecution.id == UUID(execution_id)).first()
        
        if not all([post, account, execution]):
            logger.error(f"Не найдены необходимые данные: post={post_id}, account={account_id}, execution={execution_id}")
            return {"success": False, "error": "Данные не найдены"}
        
        # Проверяем статус аккаунта
        if account.status != AccountStatus.ACTIVE:
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = f"Аккаунт не активен (статус: {account.status})"
            db.commit()
            return {"success": False, "error": execution.error_message}
        
        # Проверяем лимиты
        if account.posts_count_today >= account.posts_limit_per_day:
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = "Достигнут дневной лимит постов"
            db.commit()
            return {"success": False, "error": execution.error_message}
        
        # Проверяем минимальную задержку между постами (30 минут)
        if account.last_post_at:
            time_since_last_post = datetime.utcnow() - account.last_post_at
            if time_since_last_post < timedelta(minutes=30):
                wait_seconds = (timedelta(minutes=30) - time_since_last_post).total_seconds()
                logger.info(f"Ожидание {wait_seconds:.0f} секунд перед публикацией для {account.username}")
                raise self.retry(countdown=int(wait_seconds))
        
        # Обновляем статус выполнения
        execution.status = PostExecutionStatus.POSTING
        db.commit()
        
        # Создаём сервис Instagram
        instagram_service = InstagramService(account)
        
        # Получаем путь к медиа
        if not post.media_paths:
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = "У поста нет медиа файлов"
            db.commit()
            return {"success": False, "error": execution.error_message}
        
        media_path = post.media_paths[0]
        
        # Проверяем существование файла
        if not os.path.exists(media_path):
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = f"Файл не найден: {media_path}"
            db.commit()
            return {"success": False, "error": execution.error_message}
        
        # Публикуем
        if post.media_type.value == "photo":
            result = instagram_service.post_photo(media_path, execution.caption_translated)
        elif post.media_type.value == "video":
            result = instagram_service.post_video(media_path, execution.caption_translated)
        else:
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = f"Неподдерживаемый тип медиа: {post.media_type}"
            db.commit()
            return {"success": False, "error": execution.error_message}
        
        if result["success"]:
            # Успешная публикация
            execution.status = PostExecutionStatus.SUCCESS
            execution.instagram_media_id = result.get("media_id")
            execution.posted_at = datetime.utcnow()
            
            # Обновляем счётчики аккаунта
            account.posts_count_today += 1
            account.last_post_at = datetime.utcnow()
            
            # Логируем успех
            log_activity(
                db=db,
                action="post",
                status=LogStatus.SUCCESS,
                account_id=account.id,
                details={"post_id": str(post_id), "media_id": result.get("media_id")},
                duration_ms=result.get("duration_ms")
            )
            
            db.commit()
            
            logger.info(f"Пост успешно опубликован для {account.username}")
            return {
                "success": True,
                "media_id": result.get("media_id"),
                "account": account.username
            }
        else:
            # Ошибка публикации
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = result.get("message", "Неизвестная ошибка")
            execution.retry_count += 1
            
            # Обновляем статус аккаунта при ошибках
            if result.get("requires_login"):
                update_account_status(db, account, AccountStatus.LOGIN_REQUIRED.value, "Требуется повторная авторизация")
            elif result.get("rate_limited"):
                update_account_status(db, account, AccountStatus.COOLDOWN.value, "Rate limit")
            elif result.get("proxy_error"):
                from app.services.proxy_manager import ProxyManager
                ProxyManager.rotate_proxy_for_account(db, account, reason="proxy_error_in_celery_task")
            
            # Логируем ошибку
            log_activity(
                db=db,
                action="post",
                status=LogStatus.FAILED,
                account_id=account.id,
                error_message=execution.error_message
            )
            
            db.commit()
            
            # Если не превышен лимит попыток, повторяем
            if execution.retry_count < 3:
                retry_delay = min(300 * (2 ** execution.retry_count), 3600)  # Экспоненциальная задержка
                logger.warning(f"Повторная попытка публикации для {account.username} через {retry_delay} сек")
                raise self.retry(countdown=retry_delay)
            
            return {"success": False, "error": execution.error_message}
            
    except Exception as e:
        logger.error(f"Ошибка в задаче task_post_to_instagram: {e}", exc_info=True)
        
        # Обновляем статус выполнения
        if execution:
            execution.status = PostExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.retry_count += 1
            db.commit()
        
        # Повторяем при необходимости
        if execution and execution.retry_count < 3:
            raise self.retry(exc=e)
        
        return {"success": False, "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="instagram_cf.batch_post",
    max_retries=1
)
def task_batch_post(self, post_id: str) -> Dict[str, Any]:
    """
    Задача для массовой публикации поста на все аккаунты в выбранных группах
    
    Создаёт задачи task_post_to_instagram для каждого аккаунта с задержками.
    
    Args:
        post_id: UUID поста
        
    Returns:
        dict: Результат создания задач
    """
    db = self.db
    
    try:
        post = db.query(Post).filter(Post.id == UUID(post_id)).first()
        if not post:
            return {"success": False, "error": "Пост не найден"}
        
        # Обновляем статус поста
        post.status = PostStatus.POSTING
        db.commit()
        
        # Получаем аккаунты из выбранных групп
        from app.models.group import Group
        
        accounts_to_post = []
        for group_id_str in post.target_groups:
            try:
                group_id = UUID(group_id_str)
                group = db.query(Group).filter(Group.id == group_id).first()
                if group:
                    for account in group.accounts:
                        if account.status == AccountStatus.ACTIVE:
                            accounts_to_post.append(account)
            except Exception as e:
                logger.warning(f"Ошибка при получении группы {group_id_str}: {e}")
                continue
        
        if not accounts_to_post:
            post.status = PostStatus.FAILED
            db.commit()
            return {"success": False, "error": "Не найдено активных аккаунтов"}
        
        # Переводим текст для каждого языка
        languages_needed = set(acc.language for acc in accounts_to_post)
        translations = {}
        
        for lang in languages_needed:
            result = translator_service.translate(
                text=post.caption_original,
                language_from=post.original_language,
                language_to=lang,
                db=db,
                use_cache=True
            )
            translations[lang] = result["translated_text"] if result["success"] else post.caption_original
        
        # Создаём задачи для каждого аккаунта
        created_tasks = 0
        for account in accounts_to_post:
            # Получаем переведённый текст
            translated_caption = translations.get(account.language, post.caption_original)
            
            # Создаём запись PostExecution
            execution = PostExecution(
                post_id=post.id,
                account_id=account.id,
                caption_translated=translated_caption,
                status=PostExecutionStatus.QUEUED
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Вычисляем задержку (random между MIN и MAX)
            delay = random.randint(
                settings.MIN_DELAY_BETWEEN_POSTS_SEC,
                settings.MAX_DELAY_BETWEEN_POSTS_SEC
            )
            
            # Создаём задачу Celery с задержкой
            task_post_to_instagram.apply_async(
                args=[str(post.id), str(account.id), str(execution.id)],
                countdown=delay,
                priority=5  # Нормальный приоритет
            )
            
            created_tasks += 1
            logger.info(f"Создана задача публикации для {account.username} с задержкой {delay} сек")
        
        logger.info(f"Создано {created_tasks} задач для публикации поста {post_id}")
        
        return {
            "success": True,
            "post_id": str(post_id),
            "tasks_created": created_tasks,
            "accounts_count": len(accounts_to_post)
        }
        
    except Exception as e:
        logger.error(f"Ошибка в задаче task_batch_post: {e}", exc_info=True)
        if post:
            post.status = PostStatus.FAILED
            db.commit()
        return {"success": False, "error": str(e)}

