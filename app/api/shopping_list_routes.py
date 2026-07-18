from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_shopping_list_service import FirebaseShoppingListService

router = APIRouter(prefix="/api/shopping-list", tags=["shopping-list"])


class ShoppingListItemPayload(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    quantity: float | None = Field(default=None, ge=0, le=100000)
    unit: str | None = Field(default=None, max_length=40)
    source_recipe: str | None = Field(default=None, max_length=240)


class ShoppingListBatchPayload(BaseModel):
    items: list[ShoppingListItemPayload] = Field(min_length=1, max_length=100)
    profile_id: str | None = Field(default=None, max_length=120)


class ShoppingListUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    quantity: float | None = Field(default=None, ge=0, le=100000)
    unit: str | None = Field(default=None, max_length=40)
    checked: bool | None = None
    profile_id: str | None = Field(default=None, max_length=120)


def service() -> FirebaseShoppingListService:
    try:
        return FirebaseShoppingListService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


@router.post("/items", status_code=201)
def add_shopping_list_items(
    payload: ShoppingListBatchPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    items = service().add_items(
        user.enterprise_id,
        user.uid,
        [item.model_dump(exclude_none=True) for item in payload.items],
        payload.profile_id,
    )
    return {"ok": True, "items": items, "added_count": len(items)}


@router.get("/items")
def list_shopping_list_items(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    items = service().list_items(user.enterprise_id, user.uid, profile_id)
    return {
        "profile_id": profile_id or FirebaseShoppingListService.DEFAULT_PROFILE_ID,
        "items": items,
        "count": len(items),
        "remaining_count": sum(not item.get("checked") for item in items),
    }


@router.put("/items/{item_id}")
def update_shopping_list_item(
    item_id: str,
    payload: ShoppingListUpdatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    item = service().update_item(
        user.enterprise_id,
        user.uid,
        item_id,
        payload.model_dump(exclude_unset=True),
        payload.profile_id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return {"ok": True, "item": item}


@router.delete("/items/{item_id}")
def delete_shopping_list_item(
    item_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, bool]:
    if not service().delete_item(user.enterprise_id, user.uid, item_id, profile_id):
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return {"ok": True}


@router.delete("/checked")
def clear_checked_shopping_list_items(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    removed = service().clear_checked(user.enterprise_id, user.uid, profile_id)
    return {"ok": True, "removed_count": removed}
