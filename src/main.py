import json

import click

from src.clients.s3_client import S3Client
from src.core.logging import get_logger
from src.core.settings import settings
from src.domain.analysis_helper import GraphInsightsAnalyzer
from src.domain.coincidence_counter import CoincidenceCounter
from src.domain.dataclasses import InteractionNormalized
from src.domain.report_builder import CoordinationReportRenderer
from src.graph.graph_analysis import GraphAnalysisTools
from src.graph.graph_builder import CBGraphBuilder
from src.graph.graph_visualizer import GraphVisualizer

logger = get_logger(__name__)


def start_coordinated_analysis(topic_id: str, research_id: str) -> None:
    # S3 client setup
    s3_client = S3Client()

    # Read data from s3
    twitter_interactions = s3_client.read_twitter_interactions(topic_id, research_id)
    twitter_posts = s3_client.read_twitter_posts(topic_id, research_id)
    interactions = (
        InteractionNormalized(**interaction)
        for interaction in twitter_interactions
        if interaction["interaction_type"] == "repost"
    )
    posts = {
        item["primitive_id"]: item
        for item in twitter_posts
        if item.get("is_original") is not False
    }

    # Build graph
    counter = CoincidenceCounter(window_seconds=settings.max_time_offset)
    cib = CBGraphBuilder(counter).build_graph(
        interactions, min_participation=settings.min_participation
    )

    # Analyze graph results using posts
    analyzer = GraphAnalysisTools()
    outcome = analyzer.analyze(cib, posts)
    metadata = json.dumps(outcome.metadata, ensure_ascii=True, indent=2)
    s3_client.post_cb_metadata(metadata, topic_id, research_id)

    # Build report and push it to s3
    report = CoordinationReportRenderer()
    doc = report.render(analysis=outcome.analysis)
    s3_client.post_cib_report(doc=doc, topic_id=topic_id, research_id=research_id)

    # Build graph visualization and post it to s3
    visualizer = GraphVisualizer()
    cib_graph = visualizer.visualize(outcome.laid_out_subgraph, outcome.groups)
    s3_client.post_cib_graph(
        graph_html=cib_graph.generate_html(), topic_id=topic_id, research_id=research_id
    )

    # Build extra analysis

    extra_analysis = GraphInsightsAnalyzer(outcome.metadata)
    extra_analysis.parse_interactions()
    posts_fields, posts_rows = extra_analysis.build_posts_rows()
    sharers_fields, sharers_rows = extra_analysis.build_sharers_coordination_rows()
    posts_coord_fields, posts_coord_rows = (
        extra_analysis.build_posts_coordination_rows()
    )
    aggregated = extra_analysis.build_coordination_aggregate()
    aggregated = json.dumps(aggregated, ensure_ascii=True, indent=2)

    s3_client.post_csv(
        "posts_summary.csv", posts_rows, posts_fields, topic_id, research_id
    )
    s3_client.post_csv(
        "sharers_coordination.csv", sharers_rows, sharers_fields, topic_id, research_id
    )
    s3_client.post_csv(
        "posts_coordination.csv",
        posts_coord_rows,
        posts_coord_fields,
        topic_id,
        research_id,
    )
    s3_client.post_cb_aggregate(aggregated, topic_id, research_id)


@click.command
@click.argument("topic_id")
@click.argument("research_id")
def run(topic_id: str, research_id: str):
    logger.info("Get coordinated networks localy executed")
    start_coordinated_analysis(topic_id, research_id)


if __name__ == "__main__":
    run()
