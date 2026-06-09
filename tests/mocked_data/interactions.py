from datetime import UTC, datetime, timedelta

from src.domain.dataclasses import InteractionNormalized, InteractionTypes, ModelTypes

base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

interactions_mocked = [
    # ────────────────────────────────────────────────────────────
    # SCENARIO 1: Dense cluster of REPOSTs on the same target_model_id (TMID1)
    #  - Authors A1, A2, A3 with timestamps within a small window
    #  - This should create a full triangle of coincidences between (A1, A2, A3)
    # ────────────────────────────────────────────────────────────
    InteractionNormalized(
        created_at=base_time + timedelta(seconds=0),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID1",
        source_author_username="author_1",
        source_model_id="SMID1",
        target_model_id="TMID1",
        topic_id="TOPIC1",
        target_author_id="TAID1",
        target_author_username="t_author_1",
    ),
    InteractionNormalized(
        created_at=base_time + timedelta(seconds=10),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID2",
        source_author_username="author_2",
        source_model_id="SMID2",
        target_model_id="TMID1",
        topic_id="TOPIC1",
        target_author_id="TAID1",
        target_author_username="t_author_1",
    ),
    InteractionNormalized(
        created_at=base_time + timedelta(seconds=20),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID3",
        source_author_username="author_3",
        source_model_id="SMID3",
        target_model_id="TMID1",
        topic_id="TOPIC1",
        target_author_id="TAID1",
        target_author_username="t_author_1",
    ),
    # ────────────────────────────────────────────────────────────
    # SCENARIO 2: Same authors, same interaction_type and model_type,
    #             but a different target_model_id (TMID2), also within window
    #  - More coincidences on a different target for the same trio (A1, A2, A3)
    # ────────────────────────────────────────────────────────────
    InteractionNormalized(
        created_at=base_time + timedelta(minutes=5, seconds=0),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID1",
        source_author_username="author_1",
        source_model_id="SMID4",
        target_model_id="TMID2",
        topic_id="TOPIC1",
        target_author_id="TAID2",
        target_author_username="t_author_2",
    ),
    InteractionNormalized(
        created_at=base_time + timedelta(minutes=5, seconds=5),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID2",
        source_author_username="author_2",
        source_model_id="SMID5",
        target_model_id="TMID2",
        topic_id="TOPIC1",
        target_author_id="TAID2",
        target_author_username="t_author_2",
    ),
    InteractionNormalized(
        created_at=base_time + timedelta(minutes=5, seconds=8),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID3",
        source_author_username="author_3",
        source_model_id="SMID6",
        target_model_id="TMID2",
        topic_id="TOPIC1",
        target_author_id="TAID2",
        target_author_username="t_author_2",
    ),
    # ────────────────────────────────────────────────────────────
    # SCENARIO 3: Same authors, but far apart in time (beyond window)
    #             to ensure NO coincidences for these interactions.
    #  - Assuming window is something like <= 1 hour.
    # ────────────────────────────────────────────────────────────
    InteractionNormalized(
        created_at=base_time + timedelta(hours=3),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID1",
        source_author_username="author_1",
        source_model_id="SMID7",
        target_model_id="TMID3",
        topic_id="TOPIC2",
        target_author_id="TAID3",
        target_author_username="t_author_3",
    ),
    InteractionNormalized(
        created_at=base_time + timedelta(hours=5),
        interaction_type=InteractionTypes.REPOST,
        model_type=ModelTypes.POST,
        source_author_id="AID2",
        source_author_username="author_2",
        source_model_id="SMID8",
        target_model_id="TMID3",
        topic_id="TOPIC2",
        target_author_id="TAID3",
        target_author_username="t_author_3",
    ),
]
