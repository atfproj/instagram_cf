"""
Celery worker для запуска задач
Использование: celery -A backend.celery_app.config.celery_app worker --loglevel=info
"""
from backend.celery_app.config import celery_app

if __name__ == "__main__":
    celery_app.start()

