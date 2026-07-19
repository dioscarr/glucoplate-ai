from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext, current_user
from app.services.firebase_user_data_service import FirebaseUserDataService

router = APIRouter(prefix="/api/user-data", tags=["user-data"])


class RecipePayload(BaseModel):
    recipe: dict[str, Any]


class CookedPayload(BaseModel):
    recipe_id: str | None = None
    recipe_name: str | None = None
    recipe: dict[str, Any] | None = None
    servings: int | None = Field(default=None, ge=1, le=100)
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=2000)
    cooked_at: str | None = None
    profile_id: str | None = None


class CookingSessionCreatePayload(BaseModel):
    recipe_id: str | None = Field(default=None, max_length=200)
    recipe_name: str | None = Field(default=None, max_length=240)
    recipe: dict[str, Any]
    current_step: int = Field(default=0, ge=0, le=1000)
    completed_steps: list[int] = Field(default_factory=list, max_length=1000)
    started_at: str | None = None
    profile_id: str | None = Field(default=None, max_length=120)


class CookingSessionUpdatePayload(BaseModel):
    recipe: dict[str, Any] | None = None
    current_step: int | None = Field(default=None, ge=0, le=1000)
    completed_steps: list[int] | None = Field(default=None, max_length=1000)
    status: Literal["active", "completed", "abandoned"] | None = None
    timer: dict[str, Any] | None = None
    profile_id: str | None = Field(default=None, max_length=120)


class RecipeInteractionPayload(BaseModel):
    interaction_type: Literal["saved", "cooked", "dismissed", "repeated"]
    recipe_id: str | None = Field(default=None, max_length=200)
    recipe_name: str | None = Field(default=None, max_length=240)
    cuisine: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=30)
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=1000)
    source: str | None = Field(default=None, max_length=80)
    occurred_at: str | None = None
    profile_id: str | None = None


class PreferencesPayload(BaseModel):
    preferences: dict[str, Any]
    profile_id: str | None = None


class ProfilePayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    avatar: str | None = Field(default=None, max_length=16)
    relationship: str | None = Field(default=None, max_length=40)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


def scoped_user(user: Annotated[AuthContext, Depends(current_user)]) -> AuthContext:
    if not user.enterprise_id:
        raise HTTPException(status_code=403, detail="Enterprise membership is required")
    return user


def service() -> FirebaseUserDataService:
    try:
        return FirebaseUserDataService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


@router.post("/profiles")
def create_profile(payload: ProfilePayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    profile = service().create_profile(user.enterprise_id, user.uid, payload.model_dump())
    return {"ok": True, "profile": profile}


@router.get("/profiles")
def list_profiles(user: Annotated[AuthContext, Depends(scoped_user)]) -> list[dict[str, Any]]:
    return service().list_profiles(user.enterprise_id, user.uid)


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    deleted = service().delete_profile(user.enterprise_id, user.uid, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found or cannot be deleted")
    return {"ok": True}


@router.post("/recipes")
def save_recipe(
    payload: RecipePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
    store: Annotated[FirebaseUserDataService, Depends(FirebaseUserDataService)],
) -> dict:
    recipe = store.save_recipe(user.enterprise_id, user.uid, payload.recipe)
    return {"ok": True, "recipe": recipe}


@router.get("/recipes")
def list_recipes(
    user: Annotated[AuthContext, Depends(scoped_user)],
    store: Annotated[FirebaseUserDataService, Depends(FirebaseUserDataService)],
) -> list[dict[str, Any]]:
    return store.list_recipes(user.enterprise_id, user.uid)


@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
    store: Annotated[FirebaseUserDataService, Depends(FirebaseUserDataService)],
) -> dict:
    deleted = store.delete_recipe(user.enterprise_id, user.uid, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"ok": True}


@router.post("/recents")
def add_recent(payload: RecipePayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    recent = service().add_recent(user.enterprise_id, user.uid, payload.recipe)
    return {"ok": True, "recent": recent}


@router.get("/recents")
def list_recents(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, Any]]:
    return service().list_recents(user.enterprise_id, user.uid, limit)


@router.post("/cooking-history")
def record_cooked(payload: CookedPayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    history = service().record_cooked(
        user.enterprise_id,
        user.uid,
        payload.model_dump(exclude_none=True),
        payload.profile_id,
    )
    return {"ok": True, "history": history}


@router.get("/cooking-history")
def list_cooked(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=50, ge=1, le=200),
    profile_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return service().list_cooked(user.enterprise_id, user.uid, limit, profile_id)


@router.post("/cooking-sessions", status_code=201)
def create_cooking_session(
    payload: CookingSessionCreatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    session = service().create_cooking_session(
        user.enterprise_id,
        user.uid,
        payload.model_dump(exclude_none=True),
        payload.profile_id,
    )
    return {"ok": True, "session": session}


@router.get("/cooking-sessions/active")
def active_cooking_session(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None),
) -> dict[str, Any]:
    session = service().active_cooking_session(user.enterprise_id, user.uid, profile_id)
    return {"session": session}


@router.patch("/cooking-sessions/{session_id}")
def update_cooking_session(
    session_id: str,
    payload: CookingSessionUpdatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    session = service().update_cooking_session(
        user.enterprise_id,
        user.uid,
        session_id,
        updates,
        payload.profile_id,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Cooking session not found")
    return {"ok": True, "session": session}


@router.post("/recipe-interactions")
def record_recipe_interaction(
    payload: RecipeInteractionPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict:
    interaction = service().record_recipe_interaction(
        user.enterprise_id,
        user.uid,
        payload.model_dump(exclude_none=True),
        payload.profile_id,
    )
    return {"ok": True, "interaction": interaction}


@router.get("/recipe-interactions")
def list_recipe_interactions(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=100, ge=1, le=500),
    profile_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return service().list_recipe_interactions(user.enterprise_id, user.uid, limit, profile_id)


@router.get("/flavor-memory")
def get_flavor_memory(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return service().flavor_memory_summary(user.enterprise_id, user.uid, profile_id)


@router.put("/preferences")
def save_preferences(payload: PreferencesPayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    preferences = service().save_preferences(user.enterprise_id, user.uid, payload.preferences, payload.profile_id)
    return {"ok": True, "preferences": preferences}


@router.get("/preferences")
def get_preferences(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return service().get_preferences(user.enterprise_id, user.uid, profile_id)
