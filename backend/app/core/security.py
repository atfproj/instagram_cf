from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.core.config import settings
import base64

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def get_encryption_key() -> bytes:
    """Получение ключа шифрования для Fernet (base64-encoded строка)"""
    key = settings.ENCRYPTION_KEY
    
    # Если ключ уже в base64 формате (44 символа для 32 байт)
    if len(key) == 44:
        try:
            # Проверяем, что это валидный base64
            decoded = base64.urlsafe_b64decode(key)
            if len(decoded) == 32:
                # Возвращаем base64-encoded строку как bytes
                return key.encode()
        except Exception:
            pass
    
    # Если ключ не в правильном формате, создаём правильный ключ из строки
    # Используем хеш SHA256 для получения 32 байт
    import hashlib
    key_hash = hashlib.sha256(key.encode()).digest()
    # Fernet требует base64-encoded ключ (44 символа)
    encoded_key = base64.urlsafe_b64encode(key_hash).decode()
    return encoded_key.encode()


def encrypt_data(data: str) -> str:
    """Шифрование данных (для паролей Instagram, прокси)"""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Расшифровка данных"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode()).decode()

