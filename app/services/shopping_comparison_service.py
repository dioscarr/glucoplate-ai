from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.schemas.store import ProductSearchRequest
from app.services.firebase_price_observation_service import FirebasePriceObservationService
from app.services.price_availability_service import PriceAvailabilityService


class ShoppingComparisonService:
    """Match shopping-list items to product metadata and recent community prices."""

    def __init__(
        self,
        price_service: PriceAvailabilityService | None = None,
        observation_service: FirebasePriceObservationService | None = None,
    ) -> None:
        self.price_service = price_service or PriceAvailabilityService()
        self.observation_service = observation_service or FirebasePriceObservationService()

    def compare(
        self,
        items: list[dict[str, Any]],
        *,
        enterprise_id: str,
        store_id: str | None = None,
        store_name: str | None = None,
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
            community = self.observation_service.aggregate(
                enterprise_id,
                ingredient=name,
                barcode=best.get("barcode"),
                store_name=store_name,
            )
            product_price = best.get("price")
            community_price = community.get("latest_price")
            price = product_price if isinstance(product_price, (int, float)) else community_price
            if isinstance(price, (int, float)):
                known_total += float(price)
                known_price_count += 1
            matches.append({
                "shopping_item_id": item.get("id"),
                "shopping_item_name": name,
                "source_recipe": item.get("source_recipe"),
                "match": best,
                "community_price": community,
                "effective_price": price,
                "price_source": best.get("source") if isinstance(product_price, (int, float)) else community.get("latest_source"),
                "price_status": "known" if isinstance(price, (int, float)) else "unavailable",
                "checked_at": checked_at,
            })

        return {
            "checked_at": checked_at,
            "store_id": store_id,
            "store_name": store_name,
            "items": matches,
            "item_count": len(matches),
            "known_price_count": known_price_count,
            "known_total": round(known_total, 2),
            "currency": next((row["community_price"].get("currency") for row in matches if row["community_price"].get("currency")), None),
            "estimate_complete": bool(matches) and known_price_count == len(matches),
            "disclaimer": "Community prices are last-known observations, not live retailer quotes. Confirm price and availability before purchasing.",
        }
