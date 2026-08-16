"""Celery application instance and worker configuration."""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "codegraph",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    worker_prefetch_multiplier=1,
    # A request that creates a repository must not block while Celery retries
    # an unavailable Redis broker. The endpoint records the repository first
    # and surfaces the scheduling failure through its existing error handling.
    task_publish_retry=False,
    broker_connection_retry=False,
    broker_connection_timeout=1,
    task_routes={
        "app.tasks.analysis.*": {"queue": "analysis"},
    },
)
