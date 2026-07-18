from app.services.recipe_recommendation_service import RecipeRecommendationService


def test_repeated_and_cooked_signals_raise_matching_concepts():
    service = RecipeRecommendationService()
    candidates = [
        {"id": "pasta", "title": "Creamy Italian Pasta", "direction": "Comforting pasta", "cuisine": "Italian", "tags": ["pasta", "creamy"]},
        {"id": "salad", "title": "Fresh Garden Salad", "direction": "Crisp vegetables", "tags": ["salad", "fresh"]},
        {"id": "soup", "title": "Quick Tomato Soup", "direction": "Easy soup", "tags": ["soup", "quick"]},
    ]
    interactions = [
        {"interaction_type": "repeated", "recipe_name": "Creamy pasta", "cuisine": "Italian", "tags": ["pasta"]},
        {"interaction_type": "cooked", "recipe_name": "Italian noodles", "tags": ["creamy"]},
    ]

    ranked = service.rank("dinner", interactions, candidates=candidates)

    assert ranked[0]["id"] == "pasta"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "Similar to meals you choose again" in ranked[0]["why_this_fits"]


def test_dismissed_signals_reduce_similar_concepts():
    service = RecipeRecommendationService()
    candidates = [
        {"id": "spicy", "title": "Spicy Curry", "direction": "Hot curry", "tags": ["spicy", "curry"]},
        {"id": "mild", "title": "Mild Herb Chicken", "direction": "Gentle herb flavor", "tags": ["mild", "chicken"]},
    ]
    interactions = [{"interaction_type": "dismissed", "recipe_name": "Spicy curry", "tags": ["spicy"]}]

    ranked = service.rank("dinner", interactions, candidates=candidates, limit=2)

    assert ranked[0]["id"] == "mild"
    assert ranked[1]["score"] < 0
    assert "Reduced because similar ideas were skipped" in ranked[1]["why_this_fits"]


def test_default_candidates_are_distinct_and_limited():
    concepts = RecipeRecommendationService().rank(
        "chicken and rice",
        interactions=[],
        preferences={"preferred_cuisines": ["Dominican"]},
        culture="Dominican",
        limit=3,
    )

    assert len(concepts) == 3
    assert len({concept["id"] for concept in concepts}) == 3
    assert all(concept["why_this_fits"] for concept in concepts)
    assert all("score" in concept for concept in concepts)
