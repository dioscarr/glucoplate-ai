from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.schemas.receipt import Receipt
from app.services.receipt_import_service import ReceiptImportService
from app.services.receipt_parser_service import ReceiptParserService

router = APIRouter(prefix="/api/receipt-imports", tags=["receipt-imports"])

class ReceiptReviewPayload(BaseModel):
    text: str = Field(min_length=3, max_length=50000)

class ReceiptImportPayload(BaseModel):
    receipt: Receipt
    profile_id: str | None = Field(default=None, max_length=120)
    add_to_pantry: bool = True
    complete_shopping_items: bool = True
    create_price_observations: bool = True

@router.post("/extract")
def extract_for_review(payload: ReceiptReviewPayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict[str, Any]:
    receipt = ReceiptParserService().extract(payload.text)
    low_confidence = [key for key, value in receipt.confidence.items() if value < 0.7]
    return {"receipt": receipt.model_dump(mode="json"), "requires_review": bool(low_confidence), "low_confidence_fields": low_confidence}

@router.post("/import")
def import_reviewed_receipt(payload: ReceiptImportPayload, user: Annotated[AuthContext, Depends(scoped_user)]) -> dict[str, Any]:
    return ReceiptImportService().import_receipt(
        user.enterprise_id, user.uid, payload.receipt.model_dump(mode="json"),
        profile_id=payload.profile_id, add_to_pantry=payload.add_to_pantry,
        complete_shopping_items=payload.complete_shopping_items,
        create_price_observations=payload.create_price_observations,
    )
