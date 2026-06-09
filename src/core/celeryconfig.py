from src.core.settings import settings

result_backend = None
broker_url = settings.celery_broker_url
broker_connection_retry_on_startup = True
include = [
    "src.tasks",
]
task_default_queue = "sherlock"
timezone = "Europe/Madrid"
enable_utc = False
worker_concurrency = 1
worker_max_tasks_per_child = 1
worker_prefetch_multiplier = 1
