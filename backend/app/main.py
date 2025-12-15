from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api import groups, accounts, posts, proxies, translations
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
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if not settings.DEBUG else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
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

