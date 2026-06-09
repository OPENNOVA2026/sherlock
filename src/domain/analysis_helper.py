from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations


def as_sorted_semicolon(values):
    return ";".join(str(x) for x in sorted(values, key=lambda v: str(v)))


@dataclass(frozen=True)
class Interaction:
    group_id: object
    post_id: str
    sharer: str | None
    post_author: str | None


class GraphInsightsAnalyzer:
    def __init__(self, data: dict):
        self.data = data
        self.interactions: list[Interaction] = []

    def parse_interactions(self) -> None:
        interactions: list[Interaction] = []
        metadata = self.data.get("metadata", [])

        for meta_item in metadata:
            group_id = meta_item.get("group_id")
            pairs = meta_item.get("pairs", [])

            for pair in pairs:
                evidence_list = pair.get("evidence", [])
                for ev in evidence_list:
                    for side_key in ("a", "b"):
                        interaction = ev.get(side_key, {})
                        if not isinstance(interaction, dict):
                            continue

                        post_id = interaction.get("target_model_id")
                        if not post_id:
                            continue

                        sharer = interaction.get("source_author_username")
                        author = interaction.get("target_author_username")

                        interactions.append(
                            Interaction(
                                group_id=group_id,
                                post_id=str(post_id),
                                sharer=str(sharer) if sharer else None,
                                post_author=str(author) if author else None,
                            )
                        )

        self.interactions = interactions

    def build_posts_rows(self) -> list[dict]:
        post_groups = defaultdict(set)
        post_sharers = defaultdict(set)
        post_authors = defaultdict(set)

        for it in self.interactions:
            if it.group_id is not None:
                post_groups[it.post_id].add(it.group_id)
            if it.sharer:
                post_sharers[it.post_id].add(it.sharer)
            if it.post_author:
                post_authors[it.post_id].add(it.post_author)

        fieldnames = [
            "post_id",
            "post_author",
            "groups",
            "sharers",
            "n_groups",
            "n_sharers",
        ]
        rows = []
        for post_id in sorted(post_groups.keys(), key=str):
            groups = post_groups.get(post_id, set())
            sharers = post_sharers.get(post_id, set())
            authors = post_authors.get(post_id, set())

            rows.append(
                {
                    "post_id": post_id,
                    "post_author": as_sorted_semicolon(authors) if authors else "",
                    "groups": as_sorted_semicolon(groups),
                    "sharers": as_sorted_semicolon(sharers),
                    "n_groups": len(groups),
                    "n_sharers": len(sharers),
                }
            )

        return fieldnames, rows

    def build_sharers_coordination_rows(self) -> list[dict]:
        group_post_sharers = defaultdict(set)

        sharer_groups = defaultdict(set)
        sharer_posts = defaultdict(set)

        for it in self.interactions:
            if not it.sharer:
                continue
            group_post_sharers[(it.group_id, it.post_id)].add(it.sharer)
            sharer_groups[it.sharer].add(it.group_id)
            sharer_posts[it.sharer].add(it.post_id)

        coordination_counts = defaultdict(lambda: defaultdict(int))
        total_coordination_events = defaultdict(int)

        for (_, _), sharers in group_post_sharers.items():
            if len(sharers) < 2:
                continue

            for u1, u2 in combinations(sorted(sharers), 2):
                coordination_counts[u1][u2] += 1
                coordination_counts[u2][u1] += 1
                total_coordination_events[u1] += 1
                total_coordination_events[u2] += 1

        fieldnames = [
            "sharer",
            "total_coordinations",
            "coordinated_with",
            "coordination_counts",
            "groups",
            "posts_amplified",
            "n_groups",
            "n_posts_amplified",
            "n_partners",
        ]
        rows = []
        all_sharers = sorted(sharer_groups.keys(), key=str)

        for sharer in all_sharers:
            partners = coordination_counts.get(sharer, {})

            rows.append(
                {
                    "sharer": sharer,
                    "total_coordinations": total_coordination_events.get(sharer, 0),
                    "coordinated_with": as_sorted_semicolon(partners.keys())
                    if partners
                    else "",
                    "coordination_counts": ";".join(
                        f"{other}:{count}"
                        for other, count in sorted(
                            partners.items(), key=lambda x: str(x[0])
                        )
                    )
                    if partners
                    else "",
                    "groups": as_sorted_semicolon(sharer_groups.get(sharer, set())),
                    "posts_amplified": as_sorted_semicolon(
                        sharer_posts.get(sharer, set())
                    ),
                    "n_groups": len(sharer_groups.get(sharer, set())),
                    "n_posts_amplified": len(sharer_posts.get(sharer, set())),
                    "n_partners": len(partners),
                }
            )

        return fieldnames, rows

    def build_posts_coordination_rows(self) -> list[dict]:
        group_post_sharers = defaultdict(set)
        for it in self.interactions:
            if not it.sharer:
                continue
            group_post_sharers[(it.group_id, it.post_id)].add(it.sharer)

        post_coord_events = defaultdict(int)
        post_coord_groups = defaultdict(set)
        post_coord_sharers = defaultdict(set)

        for (group_id, post_id), sharers in group_post_sharers.items():
            if len(sharers) < 2:
                continue

            n = len(sharers)
            pair_count = (n * (n - 1)) // 2

            post_coord_events[post_id] += pair_count
            post_coord_groups[post_id].add(group_id)
            post_coord_sharers[post_id].update(sharers)

        all_posts = sorted({it.post_id for it in self.interactions}, key=str)

        fieldnames = [
            "post_id",
            "coordinated_events",
            "coordinated_groups",
            "coordinated_sharers",
            "n_coordinated_groups",
            "n_coordinated_sharers",
        ]
        rows = []
        for post_id in all_posts:
            groups = post_coord_groups.get(post_id, set())
            sharers = post_coord_sharers.get(post_id, set())
            rows.append(
                {
                    "post_id": post_id,
                    "coordinated_events": post_coord_events.get(post_id, 0),
                    "coordinated_groups": as_sorted_semicolon(groups) if groups else "",
                    "coordinated_sharers": as_sorted_semicolon(sharers)
                    if sharers
                    else "",
                    "n_coordinated_groups": len(groups),
                    "n_coordinated_sharers": len(sharers),
                }
            )

        return fieldnames, rows

    def build_coordination_aggregate(self) -> dict:
        group_post_sharers = defaultdict(set)
        for it in self.interactions:
            if not it.sharer:
                continue
            group_post_sharers[(it.group_id, it.post_id)].add(it.sharer)

        posts_with_coord = set()
        accounts_in_coord = set()
        total_events = 0

        for (group_id, post_id), sharers in group_post_sharers.items():
            if len(sharers) < 2:
                continue

            posts_with_coord.add(post_id)
            accounts_in_coord.update(sharers)

            n = len(sharers)
            total_events += (n * (n - 1)) // 2

        return {
            "n_posts_with_coordinated_interactions": len(posts_with_coord),
            "n_unique_accounts_coordinating": len(accounts_in_coord),
            "total_coordination_events": total_events,
        }
