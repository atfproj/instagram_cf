from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import encrypt_data, decrypt_data
from app.models.account import Account, AccountStatus
from app.models.group import Group
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Добавить новый аккаунт"""
    from app.services.proxy_manager import ProxyManager
    from app.models.proxy import Proxy
    
    # Проверка на уникальность username
    existing = db.query(Account).filter(Account.username == account.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аккаунт с username '{account.username}' уже существует"
        )
    
    # Проверка существования группы, если указана
    if account.group_id:
        group = db.query(Group).filter(Group.id == account.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Группа не найдена"
            )
    
    # Проверка существования прокси, если указан
    proxy = None
    if account.proxy_id:
        proxy = db.query(Proxy).filter(Proxy.id == account.proxy_id).first()
        if not proxy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Прокси не найден"
            )
        # Проверяем, не используется ли прокси другим аккаунтом
        existing_account = db.query(Account).filter(Account.proxy_id == account.proxy_id).first()
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот прокси уже используется другим аккаунтом"
            )
    
    # Шифруем пароль
    encrypted_password = encrypt_data(account.password)
    
    db_account = Account(
        username=account.username,
        password=encrypted_password,
        language=account.language,
        group_id=account.group_id,
        proxy_id=account.proxy_id,
        proxy_url=proxy.url if proxy else None,  # Сохраняем для обратной совместимости
        proxy_type=proxy.type.value if proxy else None,  # Сохраняем для обратной совместимости
        status=AccountStatus.LOGIN_REQUIRED
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Автоматически назначаем прокси, если не указан
    if not account.proxy_id:
        ProxyManager.assign_proxy_to_account(db, db_account)
    
    # Обновляем счётчик аккаунтов в группе
    if account.group_id:
        group = db.query(Group).filter(Group.id == account.group_id).first()
        group.accounts_count = len(group.accounts)
        db.commit()
    
    db.refresh(db_account)
    return db_account


@router.get("/", response_model=List[AccountResponse])
def list_accounts(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    group_id: UUID = None,
    status_filter: AccountStatus = None,
    db: Session = Depends(get_db)
):
    """Получить список всех аккаунтов"""
    query = db.query(Account)
    
    if group_id:
        query = query.filter(Account.group_id == group_id)
    if status_filter:
        query = query.filter(Account.status == status_filter)
    
    accounts = query.offset(skip).limit(limit).all()
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить информацию об аккаунте"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, account_update: AccountUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Обновить аккаунт"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    update_data = account_update.dict(exclude_unset=True)
    
    # Проверка на уникальность username, если меняется
    if "username" in update_data:
        existing = db.query(Account).filter(
            Account.username == update_data["username"],
            Account.id != account_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Аккаунт с username '{update_data['username']}' уже существует"
            )
    
    # Шифруем пароль, если он обновляется
    if "password" in update_data:
        update_data["password"] = encrypt_data(update_data["password"])
    
    # Проверка существования группы, если меняется
    if "group_id" in update_data and update_data["group_id"]:
        group = db.query(Group).filter(Group.id == update_data["group_id"]).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Группа не найдена"
            )
    
    # Обработка отвязки прокси (если proxy_id = None)
    old_proxy_id = db_account.proxy_id
    if "proxy_id" in update_data:
        if update_data["proxy_id"] is None:
            # Отвязываем прокси
            db_account.proxy_id = None
            db_account.proxy_url = None
            db_account.proxy_type = None
            # Удаляем proxy_id из update_data, чтобы не перезаписать None
            del update_data["proxy_id"]
        elif update_data["proxy_id"]:
            # Проверяем существование нового прокси
            from app.models.proxy import Proxy
            proxy = db.query(Proxy).filter(Proxy.id == update_data["proxy_id"]).first()
            if not proxy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Прокси не найден"
                )
            # Проверяем, не используется ли прокси другим аккаунтом
            existing_account = db.query(Account).filter(
                Account.proxy_id == update_data["proxy_id"],
                Account.id != account_id
            ).first()
            if existing_account:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Этот прокси уже используется другим аккаунтом"
                )
            # Обновляем proxy_url и proxy_type из прокси
            update_data["proxy_url"] = proxy.url
            update_data["proxy_type"] = proxy.type.value
    
    old_group_id = db_account.group_id
    
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    
    # Обновляем счётчики в группах
    if old_group_id != db_account.group_id:
        if old_group_id:
            old_group = db.query(Group).filter(Group.id == old_group_id).first()
            if old_group:
                old_group.accounts_count = len(old_group.accounts)
        if db_account.group_id:
            new_group = db.query(Group).filter(Group.id == db_account.group_id).first()
            if new_group:
                new_group.accounts_count = len(new_group.accounts)
        db.commit()
    
    return db_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Удалить аккаунт"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    group_id = db_account.group_id
    db.delete(db_account)
    db.commit()
    
    # Обновляем счётчик в группе
    if group_id:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            group.accounts_count = len(group.accounts)
            db.commit()
    
    return None


@router.post("/{account_id}/login")
def login_account(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Авторизоваться в Instagram"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity, update_account_status
    from app.models.activity_log import LogStatus
    from app.models.proxy import Proxy
    from datetime import datetime
    from sqlalchemy.orm import joinedload
    
    # Загружаем аккаунт с прокси
    db_account = db.query(Account).options(joinedload(Account.proxy)).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Если есть proxy_id, но proxy_url не установлен, обновляем из прокси
    if db_account.proxy_id and not db_account.proxy_url and db_account.proxy:
        db_account.proxy_url = db_account.proxy.url
        db_account.proxy_type = db_account.proxy.type.value
        db.commit()
        db.refresh(db_account)
    
    # Создаём сервис Instagram
    instagram_service = InstagramService(db_account)
    
    # Пытаемся авторизоваться
    result = instagram_service.login()
    
    if result["success"]:
        # Сохраняем сессию
        db_account.session_data = result["session_data"]
        db_account.device_id = result.get("device_id")
        db_account.user_agent = result.get("user_agent")
        db_account.status = AccountStatus.ACTIVE
        db_account.last_login_at = datetime.utcnow()
        db_account.failed_attempts = 0
        db.commit()
        db.refresh(db_account)
        
        # Логируем успешную авторизацию
        log_activity(
            db=db,
            action="login",
            status=LogStatus.SUCCESS,
            account_id=account_id,
            details={"message": result["message"]},
            duration_ms=result.get("duration_ms")
        )
        
        return {
            "success": True,
            "message": result["message"],
            "account": AccountResponse.from_orm(db_account)
        }
    else:
        # Обновляем статус аккаунта
        if result.get("requires_2fa"):
            # Для 2FA не меняем статус, это нормальная ситуация
            pass
        else:
            update_account_status(
                db=db,
                account=db_account,
                new_status=AccountStatus.LOGIN_REQUIRED.value,
                error_message=result["message"]
            )
        
        # Логируем неудачную попытку
        log_activity(
            db=db,
            action="login",
            status=LogStatus.FAILED,
            account_id=account_id,
            error_message=result["message"]
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )


@router.delete("/{account_id}/proxy", response_model=AccountResponse)
def remove_proxy_from_account(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Отвязать прокси от аккаунта"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Отвязываем прокси
    db_account.proxy_id = None
    db_account.proxy_url = None
    db_account.proxy_type = None
    
    db.commit()
    db.refresh(db_account)
    
    return db_account


@router.get("/{account_id}/status")
def get_account_status(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Проверить статус аккаунта в Instagram"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity, update_account_status
    from app.models.activity_log import LogStatus
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Проверяем статус через Instagram API
    instagram_service = InstagramService(account)
    result = instagram_service.check_status()
    
    # Обновляем статус аккаунта, если нужно
    if result["success"]:
        if account.status != AccountStatus.ACTIVE:
            account.status = AccountStatus.ACTIVE
            account.failed_attempts = 0
            db.commit()
        
        log_activity(
            db=db,
            action="check_status",
            status=LogStatus.SUCCESS,
            account_id=account_id,
            details=result,
            duration_ms=result.get("duration_ms")
        )
    else:
        if result.get("status") == "login_required":
            update_account_status(
                db=db,
                account=account,
                new_status=AccountStatus.LOGIN_REQUIRED.value,
                error_message=result.get("message")
            )
        
        log_activity(
            db=db,
            action="check_status",
            status=LogStatus.FAILED,
            account_id=account_id,
            error_message=result.get("message")
        )
    
    return {
        "account": AccountResponse.from_orm(account),
        "instagram_status": result
    }


class ProfileUpdate(BaseModel):
    biography: Optional[str] = None
    full_name: Optional[str] = None
    external_url: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None


@router.get("/{account_id}/profile")
def get_account_profile(account_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить информацию о профиле Instagram аккаунта"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity
    from app.models.activity_log import LogStatus
    from datetime import datetime
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Создаём сервис Instagram
    instagram_service = InstagramService(account)
    
    # Получаем информацию о профиле
    result = instagram_service.get_profile()
    
    if result["success"]:
        # Логируем успех
        log_activity(
            db=db,
            action="get_profile",
            status=LogStatus.SUCCESS,
            account_id=account_id,
            duration_ms=result.get("duration_ms")
        )
        return result
    else:
        # Логируем ошибку
        log_activity(
            db=db,
            action="get_profile",
            status=LogStatus.FAILED,
            account_id=account_id,
            error_message=result.get("message")
        )
        
        # Обновляем статус аккаунта при необходимости
        if result.get("requires_login"):
            from app.utils.logging import update_account_status
            update_account_status(
                db=db,
                account=account,
                new_status=AccountStatus.LOGIN_REQUIRED.value,
                error_message="Требуется повторная авторизация"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Ошибка получения профиля")
        )


@router.put("/{account_id}/profile")
def update_account_profile(
    account_id: UUID,
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить информацию профиля Instagram аккаунта"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity, update_account_status
    from app.models.activity_log import LogStatus
    from datetime import datetime
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Создаём сервис Instagram
    instagram_service = InstagramService(account)
    
    # Обновляем профиль
    result = instagram_service.update_profile(
        biography=profile_update.biography,
        full_name=profile_update.full_name,
        external_url=profile_update.external_url,
        phone_number=profile_update.phone_number,
        email=profile_update.email
    )
    
    if result["success"]:
        # Логируем успех
        log_activity(
            db=db,
            action="update_profile",
            status=LogStatus.SUCCESS,
            account_id=account_id,
            details={"updated_fields": {k: v for k, v in profile_update.dict().items() if v is not None}},
            duration_ms=result.get("duration_ms")
        )
        return result
    else:
        # Логируем ошибку
        log_activity(
            db=db,
            action="update_profile",
            status=LogStatus.FAILED,
            account_id=account_id,
            error_message=result.get("message")
        )
        
        # Обновляем статус аккаунта при необходимости
        if result.get("requires_login"):
            update_account_status(
                db=db,
                account=account,
                new_status=AccountStatus.LOGIN_REQUIRED.value,
                error_message="Требуется повторная авторизация"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Ошибка обновления профиля")
        )


class ProfilePrivacyUpdate(BaseModel):
    is_private: bool


@router.post("/{account_id}/profile/privacy")
def toggle_profile_privacy(
    account_id: UUID,
    privacy_update: ProfilePrivacyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Изменить приватность профиля (открыть/закрыть)"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity, update_account_status
    from app.models.activity_log import LogStatus
    from datetime import datetime
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
    # Создаём сервис Instagram
    instagram_service = InstagramService(account)
    
    # Изменяем приватность профиля
    result = instagram_service.set_profile_privacy(privacy_update.is_private)
    
    if result["success"]:
        # Логируем успех
        log_activity(
            db=db,
            action="set_profile_privacy",
            status=LogStatus.SUCCESS,
            account_id=account_id,
            details={"is_private": privacy_update.is_private},
            duration_ms=result.get("duration_ms")
        )
        return result
    else:
        # Логируем ошибку
        log_activity(
            db=db,
            action="set_profile_privacy",
            status=LogStatus.FAILED,
            account_id=account_id,
            error_message=result.get("message")
        )
        
        # Обновляем статус аккаунта при необходимости
        if result.get("requires_login"):
            update_account_status(
                db=db,
                account=account,
                new_status=AccountStatus.LOGIN_REQUIRED.value,
                error_message="Требуется повторная авторизация"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Ошибка изменения приватности")
        )

