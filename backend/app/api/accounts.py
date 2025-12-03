from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.core.security import encrypt_data, decrypt_data
from app.models.account import Account, AccountStatus
from app.models.group import Group
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Добавить новый аккаунт"""
    from app.services.proxy_manager import ProxyManager
    
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
    
    # Шифруем пароль
    encrypted_password = encrypt_data(account.password)
    
    db_account = Account(
        username=account.username,
        password=encrypted_password,
        language=account.language,
        group_id=account.group_id,
        proxy_url=account.proxy_url,
        proxy_type=account.proxy_type,
        status=AccountStatus.LOGIN_REQUIRED
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Автоматически назначаем прокси, если не указан
    if not account.proxy_url:
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
def get_account(account_id: UUID, db: Session = Depends(get_db)):
    """Получить информацию об аккаунте"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, account_update: AccountUpdate, db: Session = Depends(get_db)):
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
def delete_account(account_id: UUID, db: Session = Depends(get_db)):
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
def login_account(account_id: UUID, db: Session = Depends(get_db)):
    """Авторизоваться в Instagram"""
    from app.services.instagram import InstagramService
    from app.utils.logging import log_activity, update_account_status
    from app.models.activity_log import LogStatus
    from datetime import datetime
    
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт не найден"
        )
    
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
            "account": AccountResponse.model_validate(db_account)
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


@router.get("/{account_id}/status")
def get_account_status(account_id: UUID, db: Session = Depends(get_db)):
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
        "account": AccountResponse.model_validate(account),
        "instagram_status": result
    }

