from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from src.clients.s3_client import S3Client

pytestmark = pytest.mark.s3_client_tests


@pytest.fixture(autouse=True)
def mock_boto3_s3_client(monkeypatch):
    mock_s3 = MagicMock()

    def fake_boto_client(service_name, *args, **kwargs):
        assert service_name == "s3"
        return mock_s3

    monkeypatch.setattr(
        "src.clients.s3_client.boto3.client",
        fake_boto_client,
    )

    yield mock_s3


@pytest.fixture
def faily_client(mock_boto3_s3_client):
    error_response = {
        "Error": {
            "Code": "BadErrorNotHandled",
            "Message": "This is an unexpected error",
        }
    }
    operation_name = "FailedOperation"

    mock_boto3_s3_client.put_object.side_effect = ClientError(
        error_response, operation_name
    )


@pytest.fixture
def moc_doc():
    moc_doc = MagicMock()
    moc_doc.save = MagicMock()
    return moc_doc


def test_s3_read_twitter_interactions(mock_boto3_s3_client):
    s3 = S3Client()
    list(s3.read_twitter_interactions("topic_id", "research_id"))
    mock_boto3_s3_client.download_fileobj.assert_called_once()


def test_s3_read_twitter_posts(mock_boto3_s3_client):
    s3 = S3Client()
    list(s3.read_twitter_posts("topic_id", "research_id"))
    mock_boto3_s3_client.download_fileobj.assert_called_once()


def test_post_cib_report_prod_mode(mock_boto3_s3_client, moc_doc):
    s3 = S3Client()
    s3.post_cib_report(moc_doc, "topic_id", "research_id")
    mock_boto3_s3_client.put_object.assert_called_once()


def test_post_cib_report_local_mode(monkeypatch, patch_open_and_makedirs, moc_doc):
    mocked_open, makedirs_mock = patch_open_and_makedirs
    monkeypatch.setattr("src.core.settings.settings.local_exec", True)

    s3 = S3Client()
    s3.post_cib_report(moc_doc, "topic_id", "research_id")

    expected_path = "./locals/topic_topic_id/research_research_id/cib_report.docx"

    makedirs_mock.assert_called_once_with(
        "./locals/topic_topic_id/research_research_id", exist_ok=True
    )
    mocked_open.assert_called_once_with(expected_path, "wb")

    handle = mocked_open()
    handle.write.assert_called_once()


def test_post_cib_report_failed(moc_doc, faily_client):
    s3 = S3Client()

    with pytest.raises(ClientError):
        s3.post_cib_report(moc_doc, "topic_id", "research_id")


def test_post_graph_prod_mode(mock_boto3_s3_client, monkeypatch):
    monkeypatch.setattr("src.core.settings.settings.local_exec", False)

    s3 = S3Client()
    s3.post_cib_graph("<div>mock_graph</div>", "topic_id", "research_id")
    mock_boto3_s3_client.put_object.assert_called_once()


def test_post_graph_local_mode(monkeypatch, patch_open_and_makedirs):
    mocked_open, makedirs_mock = patch_open_and_makedirs
    monkeypatch.setattr("src.core.settings.settings.local_exec", True)

    s3 = S3Client()
    s3.post_cib_graph("<div>mock_graph</div>", "topic_id", "research_id")

    expected_path = "./locals/topic_topic_id/research_research_id/cib_graph.html"

    makedirs_mock.assert_called_once_with(
        "./locals/topic_topic_id/research_research_id", exist_ok=True
    )
    mocked_open.assert_called_once_with(expected_path, "w", encoding="utf-8")

    handle = mocked_open()
    handle.write.assert_called_once()


def test_post_graph_failed(faily_client):
    s3 = S3Client()

    with pytest.raises(ClientError):
        s3.post_cib_graph("<div>mock_graph</div>", "topic_id", "research_id")


def test_post_meta_prod_mode(mock_boto3_s3_client, monkeypatch):
    monkeypatch.setattr("src.core.settings.settings.local_exec", False)

    s3 = S3Client()
    s3.post_cb_metadata("{'data': 'meta'}", "topic_id", "research_id")
    mock_boto3_s3_client.put_object.assert_called_once()


def test_post_meta_local_mode(monkeypatch, patch_open_and_makedirs):
    mocked_open, makedirs_mock = patch_open_and_makedirs
    monkeypatch.setattr("src.core.settings.settings.local_exec", True)

    s3 = S3Client()
    s3.post_cb_metadata("{'data': 'meta'}", "topic_id", "research_id")

    expected_path = "./locals/topic_topic_id/research_research_id/graph_insights.json"

    makedirs_mock.assert_called_once_with(
        "./locals/topic_topic_id/research_research_id", exist_ok=True
    )
    mocked_open.assert_called_once_with(expected_path, "w", encoding="utf-8")

    handle = mocked_open()
    handle.write.assert_called_once()


def test_post_graph_failed_metadata(faily_client):
    s3 = S3Client()

    with pytest.raises(ClientError):
        s3.post_cb_metadata("{'data': 'meta'}", "topic_id", "research_id")


def test_post_agg_prod_mode(mock_boto3_s3_client, monkeypatch):
    monkeypatch.setattr("src.core.settings.settings.local_exec", False)

    s3 = S3Client()
    s3.post_cb_aggregate("{'data': 'agg'}", "topic_id", "research_id")
    mock_boto3_s3_client.put_object.assert_called_once()


def test_post_agg_local_mode(monkeypatch, patch_open_and_makedirs):
    mocked_open, makedirs_mock = patch_open_and_makedirs
    monkeypatch.setattr("src.core.settings.settings.local_exec", True)

    s3 = S3Client()
    s3.post_cb_aggregate("{'data': 'agg'}", "topic_id", "research_id")

    expected_path = (
        "./locals/topic_topic_id/research_research_id/coordination_aggregate.json"
    )

    makedirs_mock.assert_called_once_with(
        "./locals/topic_topic_id/research_research_id", exist_ok=True
    )
    mocked_open.assert_called_once_with(expected_path, "w", encoding="utf-8")

    handle = mocked_open()
    handle.write.assert_called_once()


def test_post_graph_failed_agg(faily_client):
    s3 = S3Client()

    with pytest.raises(ClientError):
        s3.post_cb_aggregate("{'data': 'agg'}", "topic_id", "research_id")


def test_post_csv_prod_mode(mock_boto3_s3_client, monkeypatch):
    monkeypatch.setattr("src.core.settings.settings.local_exec", False)

    s3 = S3Client()
    s3.post_csv(
        "some_filename.csv", [{"data": "agg"}], ["data"], "topic_id", "research_id"
    )
    mock_boto3_s3_client.put_object.assert_called_once()


def test_post_csv_local_mode(monkeypatch, patch_open_and_makedirs):
    mocked_open, makedirs_mock = patch_open_and_makedirs
    monkeypatch.setattr("src.core.settings.settings.local_exec", True)

    s3 = S3Client()
    s3.post_csv(
        "some_filename.csv", [{"data": "agg"}], ["data"], "topic_id", "research_id"
    )

    expected_path = "./locals/topic_topic_id/research_research_id/some_filename.csv"

    makedirs_mock.assert_called_once_with(
        "./locals/topic_topic_id/research_research_id", exist_ok=True
    )
    mocked_open.assert_called_once_with(expected_path, "wb")

    handle = mocked_open()
    handle.write.assert_called_once()


def test_post_graph_failed_csv(faily_client):
    s3 = S3Client()

    with pytest.raises(ClientError):
        s3.post_csv(
            "some_filename.csv", [{"data": "agg"}], ["data"], "topic_id", "research_id"
        )
