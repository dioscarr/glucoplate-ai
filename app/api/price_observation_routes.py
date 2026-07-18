from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_price_observation_service import FirebasePriceObservationService

router = APIRouter(prefix="/api/price-observations", tags=["price-observations"])


class PriceObservationPayload(BaseModel):
    ingredient: str = Field(min_length=1, max_length=240)
    price: float = Field(gt=0, le=100000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    store_name: str = Field(min_length=1, max_length=240)
    store_id: str | None = Field(default=None, max_length=160)
    barcode: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=240)
    observed_at: str | None = None
    source: Literal["user-submitted", "receipt-extracted", "retailer-supplied"] = "user-submitted"
    receipt_id: str | None = Field(default=None, max_length=160)
    profile_id: str | None = Field(default=None, max_length=120)


def service() -> FirebasePriceObservationService:
    try:
        return FirebasePriceObservationService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


@router.post("", status_code=201)
def create_price_observation(
    payload: PriceObservationPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    observation = service().create_observation(
        user.enterprise_id,
        user.uid,
        payload.model_dump(exclude_none=True),
    )
    return {"ok": True, "observation": observation}


@router.get("/summary")
def price_observation_summary(
    user: Annotated[AuthContext, Depends(scoped_user)],
    ingredient: str | None = Query(default=None, max_length=240),
    barcode: str | None = Query(default=None, max_length=80),
    store_name: str | None = Query(default=None, max_length=240),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
) -> dict[str, Any]:
    if not ingredient and not barcode:
        raise HTTPException(status_code=400, detail="Ingredient or barcode is required")
    return service().aggregate(
        user.enterprise_id,
        ingredient=ingredient,
        barcode=barcode,
        store_name=store_name,
        currency=currency,
    )


@router.post("/{observation_id}/report")
def report_price_observation(
    observation_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, bool]:
    if not service().report_observation(user.enterprise_id, observation_id):
        raise HTTPException(status_code=404, detail="Price observation not found")
    return {"ok": True}
