import igraph
from pyvis.network import Network

from src.core.logging import get_logger

logger = get_logger(__name__)


class GraphVisualizer:
    def visualize(self, cib: igraph.Graph, groups: list[igraph.Graph]) -> Network:
        logger.info(f"Visualizing {len(groups)} groups")
        net = Network(
            notebook=True, directed=cib.is_directed(), cdn_resources="in_line"
        )

        for v in cib.vs:
            net.add_node(
                v.index, label=str(v["name"]), title=f"Nodo {v.index}", color=v["color"]
            )

        for e in cib.es:
            net.add_edge(
                e.source,
                e.target,
                value=e["weight"],
                title=f"Acciones coordinadas: {e['weight']}",
            )

        return net
