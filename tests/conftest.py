from unittest.mock import MagicMock, mock_open

import pytest

from src.clients.s3_client import S3Client


@pytest.fixture(autouse=True)
def patch_open_and_makedirs(monkeypatch, request):
    if request.node.get_closest_marker("no_patch_open_and_makedirs"):
        return
    mocked_open = mock_open()
    monkeypatch.setattr("builtins.open", mocked_open)

    makedirs_mock = MagicMock()
    monkeypatch.setattr("src.clients.s3_client.os.makedirs", makedirs_mock)

    return mocked_open, makedirs_mock


@pytest.fixture(autouse=True)
def mock_s3_client(monkeypatch, request):
    if "s3_client_tests" in request.keywords:
        yield
        return
    mock_client = MagicMock(spec=S3Client)

    mock_client.read_twitter_interactions.return_value = []
    mock_client.read_twitter_posts.return_value = []

    yield mock_client
