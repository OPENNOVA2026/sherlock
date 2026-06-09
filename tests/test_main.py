from unittest.mock import MagicMock

from src.domain.report_builder import CoordinationReportRenderer
from src.graph.graph_analysis import GraphAnalysisTools, GraphOutcome
from src.graph.graph_builder import CBGraphBuilder
from src.graph.graph_visualizer import GraphVisualizer
from src.main import start_coordinated_analysis


def test_entrypoint(monkeypatch, mock_s3_client):
    report = MagicMock(spec=GraphOutcome)
    report.metadata = {"test": "test_string"}

    builder_instance = MagicMock(spec=CBGraphBuilder)
    analysis_instance = MagicMock(spec=GraphAnalysisTools)
    analysis_instance.analyze.return_value = report
    vis_instance = MagicMock(spec=GraphVisualizer)
    report_instance = MagicMock(spec=CoordinationReportRenderer)

    builder_mock = MagicMock(return_value=builder_instance)
    analysis_mock = MagicMock(return_value=analysis_instance)
    vis_mock = MagicMock(return_value=vis_instance)
    report_mock = MagicMock(return_value=report_instance)

    monkeypatch.setattr("src.main.CBGraphBuilder", builder_mock)
    monkeypatch.setattr("src.main.GraphAnalysisTools", analysis_mock)
    monkeypatch.setattr("src.main.GraphVisualizer", vis_mock)
    monkeypatch.setattr("src.main.CoordinationReportRenderer", report_mock)
    monkeypatch.setattr("src.main.S3Client", mock_s3_client)

    start_coordinated_analysis("topic_id", "research_id")

    builder_mock.assert_called_once()
    analysis_mock.assert_called_once()
    vis_mock.assert_called_once()
    report_mock.assert_called_once()
