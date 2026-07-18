from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_pantry_service import FirebasePantryService

router = APIRouter(prefix="/api/pantry", tags=["pantry"])


class PantryItemPayload(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    quantity: float | None = Field(default=None, ge=0, le=100000)
    unit: str | None = Field(default=None, max_length=40)
    category: str | None = Field(default=None, max_length=80)
    expiration_date: str | None = Field(default=None, max_length=10)
    purchase_date: str | None = Field(default=None, max_length=10)
    location: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    estimated_price: float | None = Field(default=None, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=1000)
    profile_id: str | None = Field(default=None, max_length=120)


class PantryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    quantity: float | None = Field(default=None, ge=0, le=100000)
    unit: str | None = Field(default=None, max_length=40)
    category: str | None = Field(default=None, max_length=80)
    expiration_date: str | None = Field(default=None, max_length=10)
    purchase_date: str | None = Field(default=None, max_length=10)
    location: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    estimated_price: float | None = Field(default=None, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=1000)
    profile_id: str | None = Field(default=None, max_length=120)


def service() -> FirebasePantryService:
    try:
        return FirebasePantryService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


@router.post("/items", status_code=201)
def create_pantry_item(
    payload: PantryItemPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    item = service().create_item(
        user.enterprise_id,
        user.uid,
        payload.model_dump(exclude_none=True),
        payload.profile_id,
    )
    return {"ok": True, "item": item}


@router.get("/items")
def list_pantry_items(
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    items = service().list_items(user.enterprise_id, user.uid, profile_id)
    return {
        "profile_id": profile_id or FirebasePantryService.DEFAULT_PROFILE_ID,
        "items": items,
        "count": len(items),
        "use_soon_count": sum(item.get("expiration_status") == "use_soon" for item in items),
        "expired_count": sum(item.get("expiration_status") == "expired" for item in items),
    }


@router.get("/items/{item_id}")
def get_pantry_item(
    item_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    item = service().get_item(user.enterprise_id, user.uid, item_id, profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return {"item": item}


@router.put("/items/{item_id}")
def update_pantry_item(
    item_id: str,
    payload: PantryItemUpdate,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    item = service().update_item(
        user.enterprise_id,
        user.uid,
        item_id,
        updates,
        payload.profile_id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return {"ok": True, "item": item}


@router.delete("/items/{item_id}")
def delete_pantry_item(
    item_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
    profile_id: str | None = Query(default=None, max_length=120),
) -> dict[str, bool]:
    deleted = service().delete_item(user.enterprise_id, user.uid, item_id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return {"ok": True}
