from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user, service
from app.services.recipe_recommendation_service import RecipeRecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RecipeConceptCandidate(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    direction: str = Field(min_length=1, max_length=1000)
    cuisine: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=30)


class RecipeConceptRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=1000)
    culture: str | None = Field(default=None, max_length=120)
    profile_id: str | None = Field(default=None, max_length=120)
    candidates: list[RecipeConceptCandidate] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=3, ge=1, le=5)


@router.post("/recipe-concepts")
def recommend_recipe_concepts(
    payload: RecipeConceptRequest,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    user_data = service()
    interactions = user_data.list_recipe_interactions(
        user.enterprise_id,
        user.uid,
        500,
        payload.profile_id,
    )
    preferences = user_data.get_preferences(
        user.enterprise_id,
        user.uid,
        payload.profile_id,
    )
    concepts = RecipeRecommendationService().rank(
        goal=payload.goal,
        culture=payload.culture,
        interactions=interactions,
        preferences=preferences,
        candidates=[candidate.model_dump(exclude_none=True) for candidate in payload.candidates] or None,
        limit=payload.limit,
    )
    return {
        "profile_id": payload.profile_id or user_data.DEFAULT_PROFILE_ID,
        "concepts": concepts,
        "interaction_count": len(interactions),
        "ranking_version": "flavor-memory-v1",
    }
