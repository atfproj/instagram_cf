#!/usr/bin/env python3
"""
Скрипт для генерации безопасных ключей для продакшена
"""
import secrets
from cryptography.fernet import Fernet

def generate_secret_key():
    """Генерирует SECRET_KEY (32 байта в hex)"""
    return secrets.token_hex(32)

def generate_encryption_key():
    """Генерирует ENCRYPTION_KEY для Fernet (base64 encoded)"""
    return Fernet.generate_key().decode()

if __name__ == "__main__":
    print("=" * 60)
    print("Генерация ключей для продакшена")
    print("=" * 60)
    print()
    print("SECRET_KEY:")
    print(generate_secret_key())
    print()
    print("ENCRYPTION_KEY:")
    print(generate_encryption_key())
    print()
    print("=" * 60)
    print("Скопируйте эти значения в ваш .env файл")
    print("=" * 60)







