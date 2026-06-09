import sentry_sdk
from pydantic_settings import BaseSettings
from sentry_sdk.integrations.celery import CeleryIntegration


class Settings(BaseSettings):
    name: str = "Sherlock"
    description: str = "Service for building coordination graphs"
    environment: str = "local"
    local_exec: bool = False

    aws_region: str = ""
    aws_s3_endpoint: str = ""
    aws_access_key: str = ""
    aws_secret_key: str = ""
    aws_s3_input_bucket: str = "nova-satellites-temp-bucket"
    aws_s3_output_bucket: str = "nova-satellites-output-bucket"

    celery_broker_url: str = ""

    max_time_offset: int = 60
    min_participation: int = 2

    sentry_dsn: str = ""
    sentry_tsr: float = 1.0


settings = Settings()


def init_sentry() -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_tsr,
        integrations=[CeleryIntegration()],
    )
