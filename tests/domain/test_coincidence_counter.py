import pytest

from src.domain.coincidence_counter import CoincidenceCounter
from tests.mocked_data.interactions import interactions_mocked


def test_counter_pair_counts():
    counter = CoincidenceCounter()
    counter.fit(interactions_mocked)
    counter.pair_counts()


def test_counter_coincidence_counts():
    counter = CoincidenceCounter()
    counter.fit(interactions_mocked)
    # First to check when value is not computed
    counter.author_coincidence_counts()

    # Run again to see if it skips if block when value is computed
    counter.author_coincidence_counts()


def test_counter_interaction_counts():
    counter = CoincidenceCounter()
    counter.fit(interactions_mocked)
    counter.author_interaction_counts()


def test_ensure_fails():
    counter = CoincidenceCounter()

    with pytest.raises(RuntimeError):
        counter.pair_counts()


def test_min_participation_one():
    counter = CoincidenceCounter()
    counter.fit(interactions_mocked, min_participation=1)
