from collections import Counter
from datetime import datetime
from typing import Any, NamedTuple, Optional

import igraph
from igraph.drawing.colors import ClusterColoringPalette, color_to_html_format

from src.core.logging import get_logger
from src.domain.dataclasses import (
    CoordinatedAuthor,
    CoordinationAnalysis,
    CoordinationGroup,
    InteractionNormalized,
    Message,
    PublicMetrics,
    TopMessage,
    UserProfile,
)

logger = get_logger(__name__)


def _to_jsonable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def interaction_to_dict(it: InteractionNormalized) -> dict:
    d = it.model_dump()
    for k, v in list(d.items()):
        d[k] = _to_jsonable(v)
    return d


class GraphOutcome(NamedTuple):
    analysis: CoordinationAnalysis
    laid_out_subgraph: igraph.Graph
    groups: list[igraph.Graph]
    metadata: dict


class GraphAnalysisTools:
    """Encapsulates tools for analyzing igraph Graphs."""

    def analyze(
        self,
        graph: igraph.Graph,
        posts: dict,
        *,
        n_clusters: int = 1000,
        n_messages: int = 10,
        minimum_weight: float = 8.0,
        layout_iterations: int = 1000,
    ) -> GraphOutcome:
        """
        Orchestrates the analysis and returns a domain GraphAnalysis.
        """
        logger.info("Analyzing graph")
        groups = self._get_groups(
            graph,
            n_clusters=n_clusters,
            minimum_weight=minimum_weight,
        )
        # Compute group info
        groups_computed: list[CoordinationGroup] = []
        groups_pairs_json = []
        for idx_g, group in enumerate(groups):
            comp_group = self._get_group_info(
                group, posts, n_messages=n_messages, group_id=idx_g
            )
            groups_computed.append(comp_group)

            group_json = self.group_pairs_evidence_json(group)
            group_json["group_id"] = idx_g
            groups_pairs_json.append(group_json)

        # Mark + color
        palette = ClusterColoringPalette(len(groups_computed))
        self._mark_groups_on_graph(graph, groups, palette, color_to_html_format)

        # Subgraph + layout
        new_g = self._induced_subgraph_of_marked(graph)
        if new_g.vcount() > 0:
            self._apply_fr_layout(new_g, iterations=layout_iterations)

        analysis = CoordinationAnalysis(
            most_coordinated_authors=self._most_coordinated_nodes(new_g),
            coordination_groups=groups_computed,
        )

        return GraphOutcome(analysis, new_g, groups, {"metadata": groups_pairs_json})

    @staticmethod
    def _mark_groups_on_graph(
        g: igraph.Graph,
        groups: list[igraph.Graph],
        palette,
        color_formatter,
    ) -> None:
        """Assign group ids and colors to vertices in-place (fast & safe)."""
        n = g.vcount()
        g.vs["group"] = [-1] * n
        g.vs["color"] = [None] * n

        name_to_idx = {nm: i for i, nm in enumerate(g.vs["name"])}

        for group_id, sub in enumerate(groups):
            color_html = color_formatter(palette.get(group_id))
            ids = [name_to_idx[nm] for nm in sub.vs["name"]]
            g.vs[ids]["group"] = [group_id] * len(ids)
            g.vs[ids]["color"] = [color_html] * len(ids)

    @staticmethod
    def _induced_subgraph_of_marked(g: igraph.Graph) -> igraph.Graph:
        kept = [i for i, grp in enumerate(g.vs["group"]) if grp != -1]
        return g.subgraph(kept)

    @staticmethod
    def _apply_fr_layout(new_g: igraph.Graph, iterations: int = 1000) -> None:
        weights: Optional[list[float]] = None
        if "weight" in new_g.es.attributes():
            weights = new_g.es["weight"]
        layout = new_g.layout_fruchterman_reingold(weights=weights, niter=iterations)
        new_g.vs["x"] = [float(p[0]) for p in layout]
        new_g.vs["y"] = [float(p[1]) for p in layout]

    @staticmethod
    def _canonical_pair(a: str, b: str) -> tuple[str, str]:
        """Return a canonical ordered pair (min, max) to index shared_tweets."""
        return (a, b) if a <= b else (b, a)

    def _get_group_info(
        self,
        group: igraph.Graph,
        posts: dict[str, dict],
        *,
        n_messages: int = 10,
        group_id: int,
    ) -> CoordinationGroup:
        names: list[str] = list(group.vs["name"])
        component_messages: Counter[str] = Counter()

        # Iterate edges within the component subgraph
        for edge in group.es:
            evidence = edge["evidence"] if "evidence" in group.es.attributes() else None
            if not evidence:
                continue

            for it_a, it_b in evidence:
                component_messages[str(it_a.target_model_id)] += 1

        top_n = component_messages.most_common(n_messages)
        top_messages: list[TopMessage] = []
        for msg_id, cnt in top_n:
            raw = posts.get(msg_id)
            if not raw:
                continue
            msg = self._message_from_raw_tweet(raw)
            top_messages.append(TopMessage(count=int(cnt), message=msg))

        users = [UserProfile(username=str(u)) for u in names]

        return CoordinationGroup(
            group_id=group_id,
            size=len(names),
            users=users,
            pushed_users=[],
            top_messages=top_messages,
        )

    @staticmethod
    def _message_from_raw_tweet(obj: dict[str, Any]) -> Message:
        """
        Map your tweet dict (per sample) into the Message dataclass.
        """
        author_username = obj.get("author_username") or obj.get("username") or "unknown"
        author = UserProfile(
            username=author_username,
            display_name=None,
            description=None,
            metrics=PublicMetrics(),
        )
        text = obj.get("full_text") or obj.get("cleaned_text") or obj.get("text") or ""
        url = obj.get("external_url")
        created_at = obj.get("created_at")
        return Message(
            author=author, text=text, external_url=url, created_at=created_at
        )

    @staticmethod
    def _most_coordinated_nodes(
        graph: igraph.Graph, min_degree=8
    ) -> list[CoordinatedAuthor]:
        degrees = graph.degree()

        strengths = graph.strength(weights="weight")

        # Build records per vertex
        records: list[CoordinatedAuthor] = []
        for idx, (deg, strg) in enumerate(zip(degrees, strengths)):
            if deg <= min_degree:
                continue
            v = graph.vs[idx]
            vid = v["name"] if "name" in v.attributes() else None
            user = UserProfile(username=vid)

            records.append(CoordinatedAuthor(user=user, coordination_degree=deg))

        # Sort by weighted degree desc, then by unweighted degree desc,
        # then by index for tie-break
        records.sort(key=lambda r: r.coordination_degree, reverse=True)
        return records

    def _get_groups(
        self,
        graph: igraph.Graph,
        *,
        n_clusters: int = 1000,
        minimum_weight: float = 8.0,
    ) -> list[igraph.Graph]:
        """
        Analyze connected components, keep the most relevant ones
        and return a reduced graph + per-group results.
        """
        components = graph.connected_components()
        logger.info(f"Connected components: {len(components)}")

        # Score and select
        groups = [graph.subgraph(component) for component in components]
        groups_filtered = [
            g
            for g in groups
            if sum(g.es["weight"] if "weight" in g.es.attributes() else [])
            >= minimum_weight
        ]
        groups_filtered = groups_filtered[:n_clusters]

        if not groups_filtered:
            min_w = round(minimum_weight, 2)
            logger.info(f"No components met the minimum weight threshold ({min_w}).")
            return []

        logger.info(f"Top groups total filtered: {len(groups_filtered)}")
        return groups_filtered

    def group_pairs_evidence_json(self, group: igraph.Graph) -> dict[str, Any]:
        """
        Returns JSON-like dict with, for each author pair in the group,
        all coincidence evidence pairs stored in edge attribute 'evidence'.
        """
        if "name" not in group.vs.attributes():
            raise ValueError("Group graph must have vertex attribute 'name'")

        if "evidence" not in group.es.attributes():
            return {"pairs": []}

        pairs_out: list[dict[str, Any]] = []

        for e in group.es:
            src = group.vs[e.source]["name"]
            tgt = group.vs[e.target]["name"]
            a, b = self._canonical_pair(str(src), str(tgt))

            evidence = e["evidence"] or []
            serialized = [
                {"a": interaction_to_dict(ia), "b": interaction_to_dict(ib)}
                for (ia, ib) in evidence
            ]

            pairs_out.append(
                {
                    "a": a,
                    "b": b,
                    "count": len(serialized),
                    "evidence": serialized,
                }
            )

        return {"pairs": pairs_out}
