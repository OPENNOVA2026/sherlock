from igraph import Graph

from src.graph.graph_builder import CBGraphBuilder
from tests.mocked_data.interactions import interactions_mocked


def test_graph_builder_standard():
    gb = CBGraphBuilder()
    graph = gb.build_graph(interactions_mocked)
    assert isinstance(graph, Graph)


def test_graph_builder_annotate():
    gb = CBGraphBuilder()
    graph = gb.build_graph(interactions_mocked, mode="annotate")
    assert isinstance(graph, Graph)
