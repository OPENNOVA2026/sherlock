from src.domain.analysis_helper import GraphInsightsAnalyzer

mock_data = {
    "metadata": [
        {
            "pairs": [
                {
                    "a": "AMar",
                    "b": "AE",
                    "count": 2,
                    "evidence": [
                        {
                            "a": {
                                "created_at": "2026-01-25T14:36:45+00:00",
                                "interaction_type": "repost",
                                "model_type": "post",
                                "research_id": None,
                                "source_author_id": "293091747",
                                "source_author_username": "AMar",
                                "source_model_id": "2015433666541813873",
                                "target_author_id": "80251375",
                                "target_author_username": "ARnar",
                                "target_model_id": "2015383957043306896",
                                "topic_id": "50b38466-e2e1-4d79-a95f-5f5f4c403745",
                            },
                            "b": {
                                "created_at": "2026-01-25T14:36:19+00:00",
                                "interaction_type": "repost",
                                "model_type": "post",
                                "research_id": None,
                                "source_author_id": "747088176",
                                "source_author_username": "AE",
                                "source_model_id": "2015433555027821045",
                                "target_author_id": "80251375",
                                "target_author_username": "ARnar",
                                "target_model_id": "2015383957043306896",
                                "topic_id": "50b38466-e2e1-4d79-a95f-5f5f4c403745",
                            },
                        },
                        {
                            "a": {
                                "created_at": "2026-01-25T14:35:02+00:00",
                                "interaction_type": "repost",
                                "model_type": "post",
                                "research_id": None,
                                "source_author_id": "293091747",
                                "source_author_username": "AMar",
                                "source_model_id": "2015433233035342030",
                                "target_author_id": "14436030",
                                "target_author_username": "paper",
                                "target_model_id": "2015391865479086159",
                                "topic_id": "50b38466-e2e1-4d79-a95f-5f5f4c403745",
                            },
                            "b": {
                                "created_at": "2026-01-25T14:35:55+00:00",
                                "interaction_type": "repost",
                                "model_type": "post",
                                "research_id": None,
                                "source_author_id": "747088176",
                                "source_author_username": "AE",
                                "source_model_id": "2015433455945884074",
                                "target_author_id": "14436030",
                                "target_author_username": "paper",
                                "target_model_id": "2015391865479086159",
                                "topic_id": "50b38466-e2e1-4d79-a95f-5f5f4c403745",
                            },
                        },
                    ],
                }
            ],
            "group": 0,
        }
    ]
}


def test_analysis_helper():
    analysis = GraphInsightsAnalyzer(data=mock_data)
    analysis.parse_interactions()
    analysis.build_coordination_aggregate()
    analysis.build_posts_coordination_rows()
    analysis.build_posts_rows()
    analysis.build_sharers_coordination_rows()
