import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.receipt import Receipt, ReceiptSummary

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "receipts.json")
os.makedirs(DATA_DIR, exist_ok=True)


def _read_store() -> list[dict]:
    if not os.path.exists(STORE_PATH):
        return []
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_store(items: list[dict]) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2, default=str)


class ReceiptStoreService:
    def list(
        self,
        merchant: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[dict]:
        items = _read_store()
        if merchant:
            items = [item for item in items if merchant.lower() in item.get("merchant", "").lower()]
        if category:
            items = [item for item in items if item.get("category") == category]
        if search:
            needle = search.lower()
            items = [
                item
                for item in items
                if needle in json.dumps(item, ensure_ascii=False, default=str).lower()
            ]
        return items

    def get(self, receipt_id: str) -> dict | None:
        return next((item for item in _read_store() if item.get("id") == receipt_id), None)

    def save(self, receipt: Receipt | dict) -> dict:
        model = receipt if isinstance(receipt, Receipt) else Receipt.model_validate(receipt)
        now = datetime.now(timezone.utc)
        payload = model.model_dump(mode="json")
        payload["id"] = payload.get("id") or f"receipt-{uuid4().hex[:12]}"
        payload["created_at"] = payload.get("created_at") or now.isoformat()
        payload["updated_at"] = now.isoformat()
        items = [payload] + [item for item in _read_store() if item.get("id") != payload["id"]]
        _write_store(items)
        return payload

    def update(self, receipt_id: str, receipt: Receipt | dict) -> dict | None:
        current = self.get(receipt_id)
        if current is None:
            return None
        incoming = receipt if isinstance(receipt, Receipt) else Receipt.model_validate(receipt)
        payload = incoming.model_dump(mode="json")
        payload["id"] = receipt_id
        payload["created_at"] = current.get("created_at")
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        items = [payload if item.get("id") == receipt_id else item for item in _read_store()]
        _write_store(items)
        return payload

    def delete(self, receipt_id: str) -> bool:
        items = _read_store()
        remaining = [item for item in items if item.get("id") != receipt_id]
        if len(remaining) == len(items):
            return False
        _write_store(remaining)
        return True

    def summary(self) -> ReceiptSummary:
        by_category: dict[str, float] = defaultdict(float)
        by_merchant: dict[str, float] = defaultdict(float)
        items = _read_store()
        for item in items:
            total = float(item.get("total") or 0)
            by_category[item.get("category") or "other"] += total
            by_merchant[item.get("merchant") or "Unknown merchant"] += total
        return ReceiptSummary(
            receipt_count=len(items),
            total_spend=round(sum(by_category.values()), 2),
            by_category={key: round(value, 2) for key, value in by_category.items()},
            by_merchant={key: round(value, 2) for key, value in by_merchant.items()},
        )
