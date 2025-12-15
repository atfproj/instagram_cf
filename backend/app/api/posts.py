from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import os
import logging
import uuid
from app.core.database import get_db
from app.core.config import settings
from app.models.post import Post, PostExecution, MediaType, PostStatus, PostExecutionStatus
from app.models.account import Account, AccountStatus
from app.models.user import User
from app.api.auth import get_current_user
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostExecutionResponse
from app.services.instagram import InstagramService
from app.utils.logging import log_activity
from app.models.activity_log import LogStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posts", tags=["posts"])

# Директория для загрузки медиа
UPLOAD_DIR = "backend/static/uploads"


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    files: List[UploadFile] = File(...),
    caption: str = Form(None),
    original_language: str = Form("ru"),
    target_groups: str = Form(None),  # JSON строка с массивом UUID
    media_type: MediaType = Form(MediaType.PHOTO),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать пост (загрузить медиа + текст)
    
    Args:
        files: Файлы медиа (фото/видео)
        caption: Текст под постом
        original_language: Язык исходного текста
        target_groups: JSON строка с массивом UUID групп
        media_type: Тип медиа (photo, video, carousel)
    """
    import json
    
    logger.info(f"Создание поста: files={len(files) if files else 0}, caption={bool(caption)}, media_type={media_type}")
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить хотя бы один файл"
        )
    
    if not caption:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать текст под постом"
        )
    
    # Парсим группы
    try:
        if target_groups:
            group_ids = json.loads(target_groups)
            if not isinstance(group_ids, list):
                raise ValueError("target_groups должен быть массивом")
        else:
            group_ids = []
    except Exception as e:
        logger.error(f"Ошибка парсинга target_groups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный формат target_groups: {str(e)}"
        )
    
    # Сохраняем файлы
    media_paths = []
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    for file in files:
        # Генерируем уникальное имя файла
        file_ext = os.path.splitext(file.filename)[1]
        file_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Сохраняем файл
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        media_paths.append(file_path)
    
    # Создаём пост
    db_post = Post(
        media_paths=media_paths,
        media_type=media_type,
        caption_original=caption,
        original_language=original_language,
        target_groups=[str(gid) for gid in group_ids],
        status=PostStatus.DRAFT
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post


@router.get("/", response_model=List[PostResponse])
def list_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить список всех постов"""
    posts = db.query(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить информацию о посте"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    return post


@router.post("/{post_id}/publish")
def publish_post(post_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Запустить публикацию поста на все аккаунты в выбранных группах
    
    Создаёт Celery задачу task_batch_post, которая создаст задачи для каждого аккаунта
    с задержками между публикациями.
    """
    from backend.celery_app.tasks.posting import task_batch_post
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    if post.status not in [PostStatus.DRAFT, PostStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пост уже опубликован или находится в процессе публикации (статус: {post.status})"
        )
    
    # Проверяем наличие медиа
    if not post.media_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У поста нет медиа файлов"
        )
    
    # Проверяем наличие групп
    if not post.target_groups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не выбраны группы для публикации"
        )
    
    # Получаем аккаунты из выбранных групп для проверки
    from app.models.group import Group
    
    accounts_count = 0
    for group_id_str in post.target_groups:
        try:
            group_id = UUID(group_id_str)
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                accounts_count += len([acc for acc in group.accounts if acc.status == AccountStatus.ACTIVE])
        except Exception:
            continue
    
    if accounts_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не найдено активных аккаунтов в выбранных группах"
        )
    
    # Запускаем Celery задачу
    task = task_batch_post.delay(str(post_id))
    
    # Обновляем статус поста
    post.status = PostStatus.PENDING
    db.commit()
    
    return {
        "message": "Публикация запущена",
        "post_id": str(post_id),
        "task_id": task.id,
        "accounts_count": accounts_count,
        "status": "pending"
    }


@router.get("/{post_id}/executions", response_model=List[PostExecutionResponse])
def get_post_executions(post_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить статус публикации по аккаунтам"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    executions = db.query(PostExecution).filter(PostExecution.post_id == post_id).all()
    
    # Возвращаем список executions (как указано в response_model)
    return [PostExecutionResponse.from_orm(e) for e in executions]


@router.post("/{post_id}/translate")
def get_post_translations(post_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получить переводы текста поста для всех языков аккаунтов в выбранных группах
    
    Используется для предпросмотра переводов перед публикацией.
    """
    from app.services.translator import translator_service
    from app.models.group import Group
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    # Собираем уникальные языки из аккаунтов в выбранных группах
    languages = set()
    for group_id_str in post.target_groups:
        try:
            group_id = UUID(group_id_str)
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                for account in group.accounts:
                    if account.status == AccountStatus.ACTIVE:
                        languages.add(account.language)
        except Exception:
            continue
    
    # Добавляем исходный язык, если его нет
    languages.add(post.original_language)
    
    # Переводим текст для каждого языка
    translations = {}
    for lang in languages:
        result = translator_service.translate(
            text=post.caption_original,
            language_from=post.original_language,
            language_to=lang,
            db=db,
            use_cache=True
        )
        
        translations[lang] = {
            "text": result["translated_text"],
            "from_cache": result.get("from_cache", False),
            "success": result["success"]
        }
    
    return {
        "post_id": str(post_id),
        "original_text": post.caption_original,
        "original_language": post.original_language,
        "translations": translations
    }


@router.post("/{post_id}/test-post/{account_id}")
def test_post_to_account(
    post_id: UUID,
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Тестовая публикация поста на один аккаунт
    
    Используется для проверки работы Instagram API перед массовой публикацией
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аккаунт не активен (статус: {account.status})"
        )
    
    if not post.media_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У поста нет медиа файлов"
        )
    
    # Создаём сервис Instagram
    instagram_service = InstagramService(account)
    
    # Публикуем (пока только фото)
    if post.media_type == MediaType.PHOTO:
        media_path = post.media_paths[0]
        if not os.path.exists(media_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл не найден: {media_path}"
            )
        
        result = instagram_service.post_photo(media_path, post.caption_original)
    elif post.media_type == MediaType.VIDEO:
        media_path = post.media_paths[0]
        if not os.path.exists(media_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл не найден: {media_path}"
            )
        
        result = instagram_service.post_video(media_path, post.caption_original)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип медиа {post.media_type} пока не поддерживается для тестовой публикации"
        )
    
    # Логируем результат
    log_activity(
        db=db,
        action="test_post",
        status=LogStatus.SUCCESS if result["success"] else LogStatus.FAILED,
        account_id=account_id,
        details=result,
        error_message=None if result["success"] else result.get("message"),
        duration_ms=result.get("duration_ms")
    )
    
    if result["success"]:
        # Обновляем счётчик постов
        account.posts_count_today += 1
        account.last_post_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": result["message"],
            "media_id": result.get("media_id"),
            "account": account.username
        }
    else:
        # Обновляем статус аккаунта при ошибках
        if result.get("requires_login"):
            account.status = AccountStatus.LOGIN_REQUIRED
        elif result.get("rate_limited"):
            account.status = AccountStatus.COOLDOWN
        elif result.get("proxy_error"):
            # Пробуем ротировать прокси
            from app.services.proxy_manager import ProxyManager
            ProxyManager.rotate_proxy_for_account(db, account, reason="proxy_error_in_post")
        
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

