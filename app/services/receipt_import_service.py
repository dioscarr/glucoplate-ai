from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService
from app.services.firebase_pantry_service import FirebasePantryService
from app.services.firebase_price_observation_service import FirebasePriceObservationService
from app.services.firebase_shopping_list_service import FirebaseShoppingListService


class ReceiptImportService:
    """Persist reviewed receipts and import their lines into shopping, pantry, and price history."""

    ROOT = "app_data"
    DEFAULT_PROFILE_ID = "default"

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key(value: str | None) -> str:
        return " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(value or "").lower()).split())

    @staticmethod
    def _fingerprint(payload: dict[str, Any]) -> str:
        parts = [
            str(payload.get("merchant") or "").strip().lower(),
            str(payload.get("purchase_date") or ""),
            str(payload.get("total") or ""),
            str(payload.get("currency") or "USD").upper(),
            str(payload.get("source_text") or "").strip(),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def _root(self, enterprise_id: str, uid: str, profile_id: str | None):
        selected = str(profile_id or self.DEFAULT_PROFILE_ID).strip() or self.DEFAULT_PROFILE_ID
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/users/{uid}/profiles/{selected}/receipt_imports"
        )

    def import_receipt(
        self,
        enterprise_id: str,
        uid: str,
        payload: dict[str, Any],
        *,
        profile_id: str | None = None,
        add_to_pantry: bool = True,
        complete_shopping_items: bool = True,
        create_price_observations: bool = True,
    ) -> dict[str, Any]:
        selected = str(profile_id or self.DEFAULT_PROFILE_ID).strip() or self.DEFAULT_PROFILE_ID
        fingerprint = self._fingerprint(payload)
        root = self._root(enterprise_id, uid, selected)
        existing = root.order_by_child("fingerprint").equal_to(fingerprint).get() or {}
        if existing:
            record = next(iter(existing.values()))
            return {"duplicate": True, "receipt": record, "pantry_items": [], "completed_items": [], "price_observations": []}

        receipt_id = uuid.uuid4().hex
        lines = [line for line in payload.get("line_items", []) if str(line.get("description") or "").strip()]
        receipt = {
            **payload,
            "id": receipt_id,
            "profile_id": selected,
            "fingerprint": fingerprint,
            "reviewed": True,
            "imported_at": self._now(),
        }
        root.child(receipt_id).set(receipt)

        pantry_items: list[dict[str, Any]] = []
        completed_items: list[dict[str, Any]] = []
        price_observations: list[dict[str, Any]] = []
        pantry_service = FirebasePantryService()
        shopping_service = FirebaseShoppingListService()
        price_service = FirebasePriceObservationService()
        shopping_items = shopping_service.list_items(enterprise_id, uid, selected) if complete_shopping_items else []

        for line in lines:
            description = str(line.get("description") or "").strip()
            quantity = float(line.get("quantity") or 1)
            unit_price = line.get("unit_price")
            line_total = line.get("total")
            effective_price = unit_price if isinstance(unit_price, (int, float)) else line_total

            if add_to_pantry:
                pantry_items.append(pantry_service.create_item(
                    enterprise_id,
                    uid,
                    {
                        "name": description,
                        "quantity": quantity,
                        "unit": line.get("unit"),
                        "source": "receipt-import",
                        "receipt_id": receipt_id,
                        "purchase_date": payload.get("purchase_date"),
                    },
                    selected,
                ))

            if create_price_observations and isinstance(effective_price, (int, float)):
                price_observations.append(price_service.create_observation(
                    enterprise_id,
                    uid,
                    {
                        "ingredient": description,
                        "price": float(effective_price),
                        "currency": str(payload.get("currency") or "USD").upper(),
                        "store_name": payload.get("merchant"),
                        "observed_at": payload.get("purchase_date") or self._now(),
                        "source": "receipt-extracted",
                        "receipt_id": receipt_id,
                        "profile_id": selected,
                    },
                ))

            if complete_shopping_items:
                line_key = self._key(description)
                for item in shopping_items:
                    item_key = self._key(item.get("name"))
                    if item.get("checked") or not item_key:
                        continue
                    if item_key == line_key or item_key in line_key or line_key in item_key:
                        updated = shopping_service.update_item(
                            enterprise_id,
                            uid,
                            str(item.get("id")),
                            {"checked": True, "receipt_id": receipt_id},
                            selected,
                        )
                        if updated:
                            completed_items.append(updated)
                        break

        root.child(receipt_id).update({
            "pantry_item_count": len(pantry_items),
            "completed_shopping_count": len(completed_items),
            "price_observation_count": len(price_observations),
        })
        receipt.update({
            "pantry_item_count": len(pantry_items),
            "completed_shopping_count": len(completed_items),
            "price_observation_count": len(price_observations),
        })
        return {
            "duplicate": False,
            "receipt": receipt,
            "pantry_items": pantry_items,
            "completed_items": completed_items,
            "price_observations": price_observations,
        }
