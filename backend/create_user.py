#!/usr/bin/env python3
"""
Скрипт для создания пользователя на продакшене
Использование:
    python create_user.py --username admin --email admin@example.com --password secure_password --role admin
"""
import sys
import os
import argparse
from uuid import uuid4

# Добавляем путь к проекту
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from sqlalchemy.exc import IntegrityError

def create_user(username: str, email: str, password: str, role: str = "editor"):
    """Создать пользователя"""
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"❌ Ошибка: Пользователь с username '{username}' или email '{email}' уже существует")
            return False
        
        # Создаём пользователя
        user_role = UserRole.ADMIN if role.lower() == "admin" else UserRole.EDITOR
        
        new_user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=user_role,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ Пользователь успешно создан!")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Role: {new_user.role.value}")
        print(f"   Active: {new_user.is_active}")
        
        return True
        
    except IntegrityError as e:
        db.rollback()
        print(f"❌ Ошибка целостности данных: {e}")
        return False
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании пользователя: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Создать пользователя для Instagram Content Factory')
    parser.add_argument('--username', required=True, help='Имя пользователя')
    parser.add_argument('--email', required=True, help='Email пользователя')
    parser.add_argument('--password', required=True, help='Пароль пользователя')
    parser.add_argument('--role', choices=['admin', 'editor'], default='editor', help='Роль пользователя (admin или editor)')
    
    args = parser.parse_args()
    
    # Проверка длины пароля
    if len(args.password) < 8:
        print("❌ Ошибка: Пароль должен быть не менее 8 символов")
        return 1
    
    success = create_user(
        username=args.username,
        email=args.email,
        password=args.password,
        role=args.role
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

