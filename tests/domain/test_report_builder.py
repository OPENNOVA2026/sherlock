import pytest

from src.domain.dataclasses import (
    CoordinatedAuthor,
    CoordinationAnalysis,
    CoordinationGroup,
    UserProfile,
)
from src.domain.report_builder import CoordinationReportRenderer

u_profiles = [
    UserProfile("user_1"),
    UserProfile("user_2"),
    UserProfile("user_3"),
    UserProfile("user_4"),
]

coord_authors = [
    CoordinatedAuthor(u_profiles[0], 16),
    CoordinatedAuthor(u_profiles[1], 10),
    CoordinatedAuthor(u_profiles[2], 12),
    CoordinatedAuthor(u_profiles[3], 4),
]

coord_groups = [
    CoordinationGroup(1, 4, u_profiles, [UserProfile("usuario_impulsado")], [])
]

c_analysis = CoordinationAnalysis(
    "title",
    "description",
    "query",
    "some_date_from",
    "some_date_to",
    3.14,
    coord_authors,
    coord_groups,
)


@pytest.mark.no_patch_open_and_makedirs
def test_coordination_report():
    cr = CoordinationReportRenderer()
    cr.render(c_analysis)
    pass
