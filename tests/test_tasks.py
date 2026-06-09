from unittest.mock import MagicMock

from src.main import start_coordinated_analysis
from src.tasks import detect_coordinated_networks


def test_entrypoint_celery_task(monkeypatch):
    launcher_mock = MagicMock(spec=start_coordinated_analysis)

    monkeypatch.setattr("src.tasks.start_coordinated_analysis", launcher_mock)
    detect_coordinated_networks("topic_id", "research_id")
