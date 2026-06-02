"""Celery app para tareas periódicas (ingesta noticias, refresco de fixtures,
recálculo de predicciones). Beat schedule se define cuando las tareas existan."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery("mundial2026", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = settings.display_timezone


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"
