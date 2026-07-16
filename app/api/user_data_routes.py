from __future__ import annotations

from typing import Annotated, Any

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


class PreferencesPayload(BaseModel):
    preferences: dict[str, Any]


def scoped_user(user: Annotated[AuthContext, Depends(current_user)]) -> AuthContext:
    if not user.enterprise_id:
        raise HTTPException(status_code=403, detail="Enterprise membership is required")
    return user


def service() -> FirebaseUserDataService:
    try:
        return FirebaseUserDataService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


@router.post("/recipes")
def save_recipe(payload: RecipePayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    recipe = service().save_recipe(user.enterprise_id, user.uid, payload.recipe)
    return {"ok": True, "recipe": recipe}


@router.get("/recipes")
def list_recipes(user: Annotated[AuthContext, Depends(scoped_user)]) -> list[dict[str, Any]]:
    return service().list_recipes(user.enterprise_id, user.uid)


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    deleted = service().delete_recipe(user.enterprise_id, user.uid, recipe_id)
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
    )
    return {"ok": True, "history": history}


@router.get("/cooking-history")
def list_cooked(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    return service().list_cooked(user.enterprise_id, user.uid, limit)


@router.put("/preferences")
def save_preferences(payload: PreferencesPayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict:
    preferences = service().save_preferences(user.enterprise_id, user.uid, payload.preferences)
    return {"ok": True, "preferences": preferences}


@router.get("/preferences")
def get_preferences(user: Annotated[AuthContext, Depends(scoped_user)]) -> dict[str, Any]:
    return service().get_preferences(user.enterprise_id, user.uid)
