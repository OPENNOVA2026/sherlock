from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
from itertools import combinations

from src.core.logging import get_logger
from src.domain.dataclasses import InteractionNormalized

logger = get_logger(__name__)

ActionKey = tuple[str, str, str]  # (interaction_type, model_type, target_model_id)
AuthorId = str
AuthorPair = tuple[AuthorId, AuthorId]
ByActionByAuthor = dict[
    ActionKey, dict[AuthorId, list[tuple[int, InteractionNormalized]]]
]
PairEvidence = dict[
    AuthorPair, list[tuple[InteractionNormalized, InteractionNormalized]]
]


def _to_second(ts: datetime) -> int:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware and normalized to UTC.")
    return int(ts.astimezone(timezone.utc).timestamp())


class CoincidenceCounter:
    """
    Encapsulates counting of unique author coincidences within a time window
    for interactions grouped by (interaction_type, model_type, target_model_id).

    Usage:
        counter = CoincidenceCounter(use_usernames=True)
        counter.fit(interactions)
        pair_counts = counter.pair_counts()
        author_counts = counter.author_interaction_counts()
        author_coincidences = counter.author_coincidence_counts()  # optional
    """

    def __init__(self, window_seconds: int = 60, use_usernames: bool = True) -> None:
        self._window = window_seconds
        self._use_usernames = use_usernames

        self._by_action_by_author: ByActionByAuthor = {}
        self._author_interaction_counts: dict[AuthorId, int] = {}

        self._pair_counts: dict[AuthorPair, int] | None = None
        self._pair_evidence: PairEvidence | None = None

        self._author_coincidence_counts: dict[AuthorId, int] | None = None
        self._is_fitted: bool = False

    def fit(
        self,
        interactions: Iterable[InteractionNormalized],
        min_participation: int = 1,
    ) -> CoincidenceCounter:
        """
        Ingests interactions and prepares internal grouped structures.
        Resets any previously computed counts.
        """
        logger.info("Fitting CoincidenceCounter")
        self._reset()
        self._group_interactions(interactions)
        self._sort_timestamps()
        self._apply_min_participation_filter(min_participation)
        self._compute_pair_counts()
        self._is_fitted = True
        return self

    def pair_counts(self) -> dict[AuthorPair, int]:
        """Returns {(author_a, author_b): unique_coincidence_count}."""
        logger.info("Calculating pair counts")
        self._ensure_fitted()
        return dict(self._pair_counts or {})

    def pair_evidence(self) -> PairEvidence:
        """Returns {(author_a, author_b): [(interaction_a, interaction_b)]}."""
        self._ensure_fitted()
        return dict(self._pair_evidence or {})

    def author_interaction_counts(self) -> dict[AuthorId, int]:
        """Returns {author: total_number_of_interactions_authored}."""
        logger.info("Computing author interaction counts")
        self._ensure_fitted()
        return dict(self._author_interaction_counts)

    def author_coincidence_counts(self) -> dict[AuthorId, int]:
        """
        Returns {author: number_of_unique_coincidences_they_participate_in}.
        Lazy-computed from pair counts.
        """
        logger.info("Computing coincidence counts")
        self._ensure_fitted()
        if self._author_coincidence_counts is None:
            self._author_coincidence_counts = self._compute_author_coincidence_counts()
        return dict(self._author_coincidence_counts)

    def _reset(self) -> None:
        self._by_action_by_author = {}
        self._author_interaction_counts = {}
        self._pair_counts = None
        self._author_coincidence_counts = None
        self._is_fitted = False
        self._pair_evidence = None

    def _ensure_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                "CoincidenceCounter has not been fitted. Call .fit(...) first."
            )

    def _author_key(self, it: InteractionNormalized) -> AuthorId:
        return it.source_author_username if self._use_usernames else it.source_author_id

    def _group_interactions(
        self, interactions: Iterable[InteractionNormalized]
    ) -> None:
        logger.info("Grouping interactions")
        by_action_by_author = defaultdict(lambda: defaultdict(list))
        author_counts = defaultdict(int)

        for it in interactions or []:
            action_key: ActionKey = (
                str(it.interaction_type),
                str(it.model_type),
                str(it.target_model_id),
            )
            author = self._author_key(it)
            ts = _to_second(it.created_at)

            by_action_by_author[action_key][author].append((ts, it))
            author_counts[author] += 1

        self._by_action_by_author = by_action_by_author
        self._author_interaction_counts = author_counts

    def _sort_timestamps(self) -> None:
        for authors_map in self._by_action_by_author.values():
            for author in authors_map:
                authors_map[author].sort(key=lambda x: x[0])

    def _apply_min_participation_filter(self, min_participation: int) -> None:
        """
        Removes authors with total interactions < min_participation from all internal
        structures. This ensures they do not contribute to pair or author
        coincidence counts.
        """
        if min_participation <= 1:
            logger.info(
                f"Min participation being {min_participation}, skipping this step"
            )
            return

        logger.info(
            f"Filtering participants with total interactions < {min_participation}"
        )

        # Determine which authors to keep
        total_authors = len(self._author_interaction_counts.keys())
        allowed_authors = {
            author
            for author, cnt in self._author_interaction_counts.items()
            if cnt >= min_participation
        }

        if not allowed_authors:
            # If nothing meets the threshold, clear everything
            self._by_action_by_author = {}
            self._author_interaction_counts = {}
            return

        # Filter author_interaction_counts
        self._author_interaction_counts = {
            author: cnt
            for author, cnt in self._author_interaction_counts.items()
            if author in allowed_authors
        }

        # Filter per-action author maps
        new_by_action_by_author: dict[ActionKey, dict[AuthorId, list[int]]] = {}
        for action_key, authors_map in self._by_action_by_author.items():
            filtered_map = {
                a: ts for a, ts in authors_map.items() if a in allowed_authors
            }
            if filtered_map:
                new_by_action_by_author[action_key] = filtered_map

        allowed_authors_count = len(allowed_authors)
        logger.info(f"Filtered {total_authors - allowed_authors_count} authors")

        self._by_action_by_author = new_by_action_by_author

    def _compute_pair_counts(self) -> None:
        """
        Two-pointer sweep per (action, author_a, author_b) to count unique coincidences.
        A coincidence is counted when |ta - tb| <= window, and we advance the earlier
        timestamp to avoid double-counting overlapping windows.
        """
        pair_evidence: PairEvidence = defaultdict(list)
        window = self._window

        for action_key, authors_map in self._by_action_by_author.items():
            authors = sorted(authors_map.keys())

            for auth1, auth2 in combinations(authors, 2):
                ta_list = authors_map[auth1]
                tb_list = authors_map[auth2]
                # Both pointers to first occurrence
                i = j = 0
                while i < len(ta_list) and j < len(tb_list):
                    ta, ita = ta_list[i]
                    tb, itb = tb_list[j]
                    if tb < ta - window:
                        j += 1
                    elif ta < tb - window:
                        i += 1
                    else:
                        # Unique coincidence within window
                        pair_evidence[(auth1, auth2)].append((ita, itb))
                        # Advance the earlier timestamp
                        if ta <= tb:
                            i += 1
                        else:
                            j += 1

        self._pair_evidence = pair_evidence
        self._pair_counts = {
            pair: len(evidence) for pair, evidence in pair_evidence.items()
        }

    def _compute_author_coincidence_counts(self) -> dict[AuthorId, int]:
        """
        Sums pair coincidences onto individual authors:
        For each pair (a, b) with count c, add c to both a and b.
        """
        author_counts: dict[AuthorId, int] = defaultdict(int)
        if not self._pair_counts:
            return {}
        for (a, b), c in self._pair_counts.items():
            author_counts[a] += c
            author_counts[b] += c
        return author_counts
