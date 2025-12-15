from celery import Celery
import os
from app.core.config import settings

# Используем переменные окружения напрямую, если они есть, иначе из settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.CELERY_BROKER_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", settings.CELERY_RESULT_BACKEND)

celery_app = Celery(
    "instagram_cf",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.celery_app.tasks.posting"]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 минут на задачу
    task_soft_time_limit=240,  # мягкий лимит 4 минуты
    worker_prefetch_multiplier=1,  # Брать по одной задаче за раз
    worker_max_tasks_per_child=50,  # Перезапускать воркер после 50 задач
)

