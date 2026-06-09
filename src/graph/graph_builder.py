from collections.abc import Iterable
from typing import Literal

import igraph
import numpy as np

from src.core.logging import get_logger
from src.domain.coincidence_counter import CoincidenceCounter
from src.domain.dataclasses import InteractionNormalized

logger = get_logger(__name__)

AuthorPair = tuple[str, str]
PairEvidence = dict[
    AuthorPair, list[tuple[InteractionNormalized, InteractionNormalized]]
]


class CBGraphBuilder:
    def __init__(self, counter: CoincidenceCounter | None = None):
        self.counter = counter or CoincidenceCounter()

    def build_graph(
        self,
        interactions: Iterable[InteractionNormalized],
        *,
        min_participation: int = 1,
        percentile: float = 0.5,
        mode: Literal["filter", "annotate"] = "filter",
        directed: bool = False,
    ) -> igraph.Graph:
        logger.info("Building CB graph with interactions")

        interaction_counter = self.counter.fit(
            interactions, min_participation=min_participation
        )
        author_interaction_counts = interaction_counter.author_interaction_counts()
        author_pair_counts = interaction_counter.pair_counts()
        pair_evidence = interaction_counter.pair_evidence()

        users = sorted(author_interaction_counts.keys())

        graph, name_to_idx = self._build_structure(users, directed)
        self._compute_edges(
            graph,
            name_to_idx,
            author_pair_counts,
            author_interaction_counts,
            pair_evidence,
        )
        self._normalize_weights(graph, percentile=percentile, mode=mode)
        return graph

    @staticmethod
    def _build_structure(
        users: list[str], directed: bool
    ) -> tuple[igraph.Graph, dict[str, int]]:
        logger.info("Building CIB graph structure")
        graph = igraph.Graph(directed=directed)
        graph.add_vertices(len(users))
        graph.vs["name"] = users
        name_to_idx = {name: idx for idx, name in enumerate(users)}
        return graph, name_to_idx

    def _compute_edges(
        self,
        graph: igraph.Graph,
        name_to_idx: dict[str, int],
        author_pairs: dict[AuthorPair, int],
        author_interactions: dict[str, int],
        pair_evidence: PairEvidence,
    ) -> None:
        logger.info("Computing graph weights")

        weights = []
        evidences = []
        symmetries = []
        edges = []

        for (user1, user2), weight in author_pairs.items():
            if user1 not in name_to_idx or user2 not in name_to_idx:
                continue

            user1_idx = name_to_idx[user1]
            user2_idx = name_to_idx[user2]
            edges.append((user1_idx, user2_idx))
            weights.append(weight)
            evidences.append(pair_evidence.get((user1, user2), []))

            user1_posts = author_interactions[user1]
            user2_posts = author_interactions[user2]
            symmetry = self._count_symmetry(user1_posts, user2_posts)
            symmetries.append(symmetry)

        if edges:
            graph.add_edges(edges)
            graph.es["weight"] = weights
            graph.es["evidence"] = evidences
            graph.es["symmetry"] = symmetries
        else:
            logger.warning("No edges found")

        logger.info(f"Added {len(edges)} edges")

    @staticmethod
    def _normalize_weights(
        graph: igraph.Graph, percentile: float, mode: Literal["filter", "annotate"]
    ):
        """
        Normalize edge weights using a percentile criterion as in the paper.

        Parameters
        ----------
        percentile : float
            Percentile in [0, 1]. Example:
            - 0.50 keeps edges > median
            - 0.99 keeps top 1% heaviest edges
        mode : {"filter", "annotate"}
            - "filter": delete edges with weight <= cutoff
            - "annotate": keep all edges and store their empirical percentile
              in edge attribute 'weight_percentile' (ECDF).

        Returns
        -------
        cutoff : float
            The weight cutoff used for this normalization.

        Notes
        -----
        - Edges with weight > cutoff are considered "strong" according to the
          chosen percentile.
        - If there are no edges, the method is a no-op and returns np.nan.
        - The chosen cutoff is stored in graph attribute: graph["cutoff_weight"].
        """
        logger.info(f"Normalizing edge weights with percentile {percentile}")
        if graph.ecount() == 0 or "weight" not in graph.es.attributes():
            graph["cutoff_weight"] = float("nan")
            return float("nan")

        weights = np.asarray(graph.es["weight"], dtype=float)
        if weights.size == 0:
            graph["cutoff_weight"] = float("nan")
            return float("nan")

        perc = min(max(percentile, 0.0), 1.0)
        cutoff = float(np.percentile(weights, perc * 100.0))
        graph["cutoff_weight"] = cutoff
        logger.info(f"Cutoff established at {cutoff}")

        if mode == "filter":
            logger.info("Normalizing edges with filtering mode")
            to_delete = graph.es.select(weight_le=cutoff)
            if len(to_delete) > 0:
                logger.info(f"Filtering {len(to_delete)} edges")
                graph.delete_edges(to_delete)
            graph["normalized_mode"] = "filter"
            graph["normalized_percentile"] = perc

        elif mode == "annotate":
            # Compute empirical CDF percentile rank for each weight
            # Handle ties by averaging ranks (typical ECDF behavior).
            logger.info("Normalizing edges with annotation mode")
            sorted_w = np.sort(weights)
            ranks = np.searchsorted(sorted_w, weights, side="right")
            ecdf = ranks / float(
                len(sorted_w)
            )  # in (0,1]; convert to [0,1] by -1 if you prefer
            graph.es["weight_percentile"] = ecdf.tolist()
            graph["normalized_mode"] = "annotate"
            graph["normalized_percentile"] = perc

        else:
            raise ValueError("mode must be either 'filter' or 'annotate'")

    @staticmethod
    def _count_symmetry(a_length: int, b_length: int) -> float:
        """
        We get the minimum value among both contributors to calculate the proportion
        of the contributions and get a number between 0 and 0.5, meaning completely
        unequal contribution to the edge to completely equal contribution.
        Then we multiply it by 2 to get a number between 0 and 1, easier to understand
        """
        total = a_length + b_length
        if total == 0:
            return 0.0
        return 2.0 * (min(a_length, b_length) / total)
