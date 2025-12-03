from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://instagram_cf:instagram_cf_password@localhost:5436/instagram_cf"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6383/0"
    
    # Instagram
    INSTAGRAM_SESSION_LIFETIME_DAYS: int = 90
    
    # Translation
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ENCRYPTION_KEY: str = "change-me-in-production-32-bytes-base64"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6383/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6383/0"
    
    # Limits
    MAX_POSTS_PER_DAY_PER_ACCOUNT: int = 10
    MAX_CONCURRENT_TASKS: int = 50
    MIN_DELAY_BETWEEN_POSTS_SEC: int = 120
    MAX_DELAY_BETWEEN_POSTS_SEC: int = 300
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    # App
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

