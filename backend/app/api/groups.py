from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.models.group import Group
from app.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Создать новую группу"""
    # Проверка на уникальность имени
    existing = db.query(Group).filter(Group.name == group.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Группа с именем '{group.name}' уже существует"
        )
    
    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.get("/", response_model=List[GroupResponse])
def list_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить список всех групп"""
    groups = db.query(Group).offset(skip).limit(limit).all()
    return groups


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить информацию о группе"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    return group


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(group_id: UUID, group_update: GroupUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Обновить группу"""
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    update_data = group_update.dict(exclude_unset=True)
    if "name" in update_data:
        # Проверка на уникальность нового имени
        existing = db.query(Group).filter(
            Group.name == update_data["name"],
            Group.id != group_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Группа с именем '{update_data['name']}' уже существует"
            )
    
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Удалить группу"""
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    db.delete(db_group)
    db.commit()
    return None


@router.get("/{group_id}/accounts")
def get_group_accounts(group_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить список аккаунтов в группе"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    
    from app.schemas.account import AccountResponse
    accounts = [AccountResponse.from_orm(acc) for acc in group.accounts]
    return accounts

