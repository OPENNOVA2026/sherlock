from src.core.celery_app import celery_app
from src.core.logging import get_logger
from src.main import start_coordinated_analysis

logger = get_logger(__name__)


@celery_app.task(name="detect_coordinated_networks")
def detect_coordinated_networks(topic_id: str, research_id: str):
    logger.info("Get coordinated networks automatically executed")
    start_coordinated_analysis(topic_id, research_id)
    logger.info("Coordination detector service completed!")
