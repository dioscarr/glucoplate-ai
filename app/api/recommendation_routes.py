from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user, service
from app.services.firebase_pantry_service import FirebasePantryService
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


class RecommendationSessionRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=1000)
    culture: str | None = Field(default=None, max_length=120)
    profile_id: str | None = Field(default=None, max_length=120)
    ranking_version: str = Field(default="flavor-memory-v1", max_length=80)
    concepts: list[RecipeConceptCandidate] = Field(min_length=1, max_length=5)


class RecommendationEventRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)
    event_type: Literal["impression", "selected", "skipped", "generated"]
    concept_id: str | None = Field(default=None, max_length=120)
    profile_id: str | None = Field(default=None, max_length=120)
    occurred_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def _create_session(
    user_data,
    user: AuthContext,
    *,
    goal: str,
    culture: str | None,
    profile_id: str | None,
    ranking_version: str,
    concepts: list[dict[str, Any]],
) -> dict[str, Any]:
    session = user_data.create_recommendation_session(
        user.enterprise_id,
        user.uid,
        {
            "goal": goal,
            "culture": culture,
            "ranking_version": ranking_version,
            "concepts": concepts,
        },
        profile_id,
    )
    for concept in session.get("concepts", []):
        user_data.record_recommendation_event(
            user.enterprise_id,
            user.uid,
            {
                "session_id": session["id"],
                "concept_id": concept.get("id"),
                "event_type": "impression",
                "metadata": {"rank": concept.get("rank"), "score": concept.get("score")},
            },
            session.get("profile_id"),
        )
    return session


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
    try:
        pantry_items = FirebasePantryService().list_items(
            user.enterprise_id,
            user.uid,
            payload.profile_id,
        )
    except Exception:
        pantry_items = []

    concepts = RecipeRecommendationService().rank(
        goal=payload.goal,
        culture=payload.culture,
        interactions=interactions,
        preferences=preferences,
        pantry_items=pantry_items,
        candidates=[candidate.model_dump(exclude_none=True) for candidate in payload.candidates] or None,
        limit=payload.limit,
    )
    ranking_version = "flavor-memory-pantry-v1"
    session = _create_session(
        user_data,
        user,
        goal=payload.goal,
        culture=payload.culture,
        profile_id=payload.profile_id,
        ranking_version=ranking_version,
        concepts=concepts,
    )
    return {
        "profile_id": session["profile_id"],
        "session_id": session["id"],
        "concepts": concepts,
        "interaction_count": len(interactions),
        "pantry_count": len(pantry_items),
        "use_soon_count": sum(item.get("expiration_status") == "use_soon" for item in pantry_items),
        "ranking_version": ranking_version,
    }


@router.post("/sessions")
def create_recommendation_session(
    payload: RecommendationSessionRequest,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    user_data = service()
    session = _create_session(
        user_data,
        user,
        goal=payload.goal,
        culture=payload.culture,
        profile_id=payload.profile_id,
        ranking_version=payload.ranking_version,
        concepts=[concept.model_dump(exclude_none=True) for concept in payload.concepts],
    )
    return {"ok": True, "session": session}


@router.post("/events")
def record_recommendation_event(
    payload: RecommendationEventRequest,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        event = service().record_recommendation_event(
            user.enterprise_id,
            user.uid,
            payload.model_dump(exclude_none=True),
            payload.profile_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "event": event}


@router.get("/history")
def recommendation_history(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=50, ge=1, le=200),
    profile_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return service().recommendation_history(user.enterprise_id, user.uid, limit, profile_id)
