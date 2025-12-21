from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api import groups, accounts, posts, proxies, translations, auth
import os

# Создание таблиц (в продакшене используем миграции)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Instagram Content Factory",
    description="Автоматизированный постинг контента на множество Instagram-аккаунтов",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,  # Отключаем docs в продакшене
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Настройка CORS
# В продакшене используем CORS_ORIGINS из переменных окружения
# В разработке разрешаем все источники
if settings.DEBUG:
    cors_origins = ["http://localhost:3002", "http://127.0.0.1:3002", "http://localhost:3001", "http://127.0.0.1:3001"]
else:
    cors_origins_str = os.getenv("CORS_ORIGINS", "http://144.76.59.27:3001")
    # Разбиваем по запятой и очищаем от пробелов
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

# Логируем настройки CORS для отладки
import logging
logger = logging.getLogger(__name__)
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)  # Auth роутер должен быть первым (без защиты)
app.include_router(groups.router)
app.include_router(accounts.router)
app.include_router(posts.router)
app.include_router(proxies.router)
app.include_router(translations.router)


@app.get("/")
async def root():
    return {"message": "Instagram Content Factory API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

