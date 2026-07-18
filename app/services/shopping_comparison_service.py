from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.schemas.store import ProductSearchRequest
from app.services.price_availability_service import PriceAvailabilityService


class ShoppingComparisonService:
    """Match shopping-list items to product metadata without overstating live pricing."""

    def __init__(self, price_service: PriceAvailabilityService | None = None) -> None:
        self.price_service = price_service or PriceAvailabilityService()

    def compare(
        self,
        items: list[dict[str, Any]],
        *,
        store_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict[str, Any]:
        checked_at = datetime.now(UTC).isoformat()
        matches: list[dict[str, Any]] = []
        known_total = 0.0
        known_price_count = 0

        for item in items:
            if item.get("checked"):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            products = self.price_service.search(ProductSearchRequest(
                ingredient=name,
                store_id=store_id,
                latitude=latitude,
                longitude=longitude,
            ))
            best = products[0].model_dump() if products else {
                "ingredient": name,
                "availability": "unknown",
                "source": "no-match",
                "notes": ["No product match found."],
            }
            price = best.get("price")
            if isinstance(price, (int, float)):
                known_total += float(price)
                known_price_count += 1
            matches.append({
                "shopping_item_id": item.get("id"),
                "shopping_item_name": name,
                "source_recipe": item.get("source_recipe"),
                "match": best,
                "price_status": "known" if isinstance(price, (int, float)) else "unavailable",
                "checked_at": checked_at,
            })

        return {
            "checked_at": checked_at,
            "store_id": store_id,
            "items": matches,
            "item_count": len(matches),
            "known_price_count": known_price_count,
            "known_total": round(known_total, 2),
            "currency": next((row["match"].get("currency") for row in matches if row["match"].get("currency")), None),
            "estimate_complete": bool(matches) and known_price_count == len(matches),
            "disclaimer": "Prices and availability are estimates from the named source and may be stale or unavailable. Confirm with the retailer before purchasing.",
        }
