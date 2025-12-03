import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog, LogStatus
from app.models.account import Account
from typing import Optional, Dict, Any
from uuid import UUID


def log_activity(
    db: Session,
    action: str,
    status: LogStatus,
    account_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> ActivityLog:
    """
    Логирование действия в БД
    
    Args:
        db: Сессия БД
        action: Название действия (login, post, check_status, etc.)
        status: Статус (success, failed)
        account_id: ID аккаунта (опционально)
        details: Дополнительные детали (JSON)
        error_message: Сообщение об ошибке (если есть)
        duration_ms: Длительность действия в миллисекундах
        
    Returns:
        ActivityLog: Созданная запись лога
    """
    log_entry = ActivityLog(
        account_id=account_id,
        action=action,
        status=status,
        details=details,
        error_message=error_message,
        duration_ms=duration_ms
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return log_entry


def update_account_status(
    db: Session,
    account: Account,
    new_status: str,
    error_message: Optional[str] = None
):
    """
    Обновление статуса аккаунта с логированием
    
    Args:
        db: Сессия БД
        account: Аккаунт
        new_status: Новый статус (из AccountStatus enum)
        error_message: Сообщение об ошибке (если есть)
    """
    from app.models.account import AccountStatus
    
    old_status = account.status
    account.status = AccountStatus(new_status)
    account.failed_attempts = account.failed_attempts + 1 if new_status != "active" else 0
    
    db.commit()
    
    # Логируем изменение статуса
    log_activity(
        db=db,
        action="status_change",
        status=LogStatus.SUCCESS if new_status == "active" else LogStatus.FAILED,
        account_id=account.id,
        details={
            "old_status": old_status.value,
            "new_status": new_status,
            "error_message": error_message
        }
    )

