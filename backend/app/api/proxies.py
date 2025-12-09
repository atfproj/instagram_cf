from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.models.proxy import Proxy, ProxyStatus
from app.schemas.proxy import ProxyCreate, ProxyUpdate, ProxyResponse, ProxyCheckResponse
from app.services.proxy_manager import ProxyManager

router = APIRouter(prefix="/api/proxies", tags=["proxies"])


@router.post("/", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
def create_proxy(proxy: ProxyCreate, db: Session = Depends(get_db)):
    """Добавить новый прокси"""
    # Проверка на уникальность URL
    existing = db.query(Proxy).filter(Proxy.url == proxy.url).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Прокси с URL '{proxy.url}' уже существует"
        )
    
    db_proxy = Proxy(
        url=proxy.url,
        type=proxy.type,
        country=proxy.country,
        status=ProxyStatus.CHECKING,
        assigned_accounts=[]
    )
    db.add(db_proxy)
    db.commit()
    db.refresh(db_proxy)
    
    return db_proxy


@router.get("/", response_model=List[ProxyResponse])
def list_proxies(
    skip: int = 0,
    limit: int = 100,
    status_filter: ProxyStatus = None,
    db: Session = Depends(get_db)
):
    """Получить список всех прокси"""
    query = db.query(Proxy)
    
    if status_filter:
        query = query.filter(Proxy.status == status_filter)
    
    proxies = query.offset(skip).limit(limit).all()
    return proxies


@router.get("/available", response_model=List[ProxyResponse])
def get_available_proxies(db: Session = Depends(get_db)):
    """Получить список неиспользуемых прокси (не назначенных ни одному аккаунту)"""
    from app.models.account import Account
    
    # Получаем все активные прокси
    all_proxies = db.query(Proxy).filter(Proxy.status == ProxyStatus.ACTIVE).all()
    
    # Получаем все аккаунты с назначенными прокси
    accounts_with_proxy = db.query(Account).filter(Account.proxy_id.isnot(None)).all()
    used_proxy_ids = {acc.proxy_id for acc in accounts_with_proxy if acc.proxy_id}
    
    # Фильтруем неиспользуемые прокси
    available_proxies = [p for p in all_proxies if p.id not in used_proxy_ids]
    
    return available_proxies


@router.get("/{proxy_id}", response_model=ProxyResponse)
def get_proxy(proxy_id: UUID, db: Session = Depends(get_db)):
    """Получить информацию о прокси"""
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прокси не найден"
        )
    return proxy


@router.put("/{proxy_id}", response_model=ProxyResponse)
def update_proxy(proxy_id: UUID, proxy_update: ProxyUpdate, db: Session = Depends(get_db)):
    """Обновить прокси"""
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прокси не найден"
        )
    
    update_data = proxy_update.dict(exclude_unset=True)
    
    # Проверка на уникальность URL, если меняется
    if "url" in update_data:
        existing = db.query(Proxy).filter(
            Proxy.url == update_data["url"],
            Proxy.id != proxy_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Прокси с URL '{update_data['url']}' уже существует"
            )
    
    for field, value in update_data.items():
        setattr(db_proxy, field, value)
    
    db.commit()
    db.refresh(db_proxy)
    return db_proxy


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proxy(proxy_id: UUID, db: Session = Depends(get_db)):
    """Удалить прокси"""
    from app.models.account import Account, AccountStatus
    
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прокси не найден"
        )
    
    # Проверяем, не используется ли прокси
    accounts_using_proxy = db.query(Account).filter(
        Account.proxy_id == proxy_id
    ).count()
    
    if accounts_using_proxy > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Прокси используется {accounts_using_proxy} аккаунтом(ами). Сначала отвяжите аккаунты."
        )
    
    db.delete(db_proxy)
    db.commit()
    return None


@router.post("/{proxy_id}/check", response_model=ProxyCheckResponse)
def check_proxy(proxy_id: UUID, db: Session = Depends(get_db)):
    """Проверить работоспособность прокси"""
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прокси не найден"
        )
    
    # Проверяем прокси
    proxy.status = ProxyStatus.CHECKING
    db.commit()
    
    check_result = ProxyManager.check_proxy(proxy)
    
    # Обновляем статус прокси
    ProxyManager.update_proxy_status(db, proxy, check_result)
    
    return ProxyCheckResponse(
        success=check_result["success"],
        message=check_result["message"],
        response_time_ms=check_result.get("response_time_ms"),
        error=check_result.get("error")
    )


@router.get("/available", response_model=List[ProxyResponse])
def get_available_proxies(db: Session = Depends(get_db)):
    """Получить список неиспользуемых прокси (не назначенных ни одному аккаунту)"""
    from app.models.account import Account
    
    # Получаем все прокси
    all_proxies = db.query(Proxy).filter(Proxy.status == ProxyStatus.ACTIVE).all()
    
    # Получаем все аккаунты с назначенными прокси
    accounts_with_proxy = db.query(Account).filter(Account.proxy_id.isnot(None)).all()
    used_proxy_ids = {acc.proxy_id for acc in accounts_with_proxy if acc.proxy_id}
    
    # Фильтруем неиспользуемые прокси
    available_proxies = [p for p in all_proxies if p.id not in used_proxy_ids]
    
    return available_proxies


@router.get("/{proxy_id}/accounts")
def get_proxy_accounts(proxy_id: UUID, db: Session = Depends(get_db)):
    """Получить список аккаунтов, использующих этот прокси"""
    from app.schemas.account import AccountResponse
    
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прокси не найден"
        )
    
    from app.models.account import Account
    accounts = db.query(Account).filter(Account.proxy_id == proxy_id).all()
    
    return [AccountResponse.from_orm(acc) for acc in accounts]

