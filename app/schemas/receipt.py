from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


ReceiptCategory = Literal[
    "groceries",
    "dining",
    "transportation",
    "shopping",
    "home",
    "health",
    "utilities",
    "travel",
    "business",
    "other",
]


class ReceiptLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float | None = None
    total: float | None = None


class Receipt(BaseModel):
    id: str | None = None
    merchant: str = Field(min_length=1)
    purchase_date: date | None = None
    subtotal: float | None = None
    tax: float | None = None
    tip: float | None = None
    total: float = Field(ge=0)
    currency: str = "USD"
    category: ReceiptCategory = "other"
    payment_method: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    line_items: list[ReceiptLineItem] = Field(default_factory=list)
    source_text: str | None = None
    confidence: dict[str, float] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReceiptExtractRequest(BaseModel):
    text: str = Field(min_length=3)


class ReceiptSummary(BaseModel):
    receipt_count: int
    total_spend: float
    by_category: dict[str, float]
    by_merchant: dict[str, float]
