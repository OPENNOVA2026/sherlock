from celery import Celery, signals

from src.core.settings import init_sentry

celery_app = Celery()

celery_app.config_from_object("src.core.celeryconfig")


@signals.celeryd_init.connect
def initialize_sentry(**kwargs: dict) -> None:
    init_sentry()
