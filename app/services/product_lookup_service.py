import json
import urllib.parse
import urllib.request
from typing import Any

from app.schemas.store import ProductAvailability, ProductSearchRequest


class ProductLookupService:
    """Search product metadata and the Open Food Facts Open Prices dataset."""

    search_url = "https://world.openfoodfacts.org/cgi/search.pl"
    prices_url = "https://prices.openfoodfacts.org/api/v1/prices"

    def search_products(self, request: ProductSearchRequest) -> list[ProductAvailability]:
        params = {
            "search_terms": request.ingredient,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 10,
        }
        url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
        try:
            payload = self._get_json(url)
        except Exception:
            return [self._unknown_availability(request.ingredient, "openfoodfacts-unavailable")]

        products = payload.get("products", [])
        if not products:
            return [self._unknown_availability(request.ingredient, "openfoodfacts")]

        return [self._map_product(request.ingredient, product) for product in products]

    def _get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GlucoPlateAI/0.1 (learning project)"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _map_product(self, ingredient: str, product: dict[str, Any]) -> ProductAvailability:
        barcode = product.get("code")
        price_data = self._lookup_price(barcode) if barcode else None
        price = price_data.get("price") if price_data else None
        currency = price_data.get("currency") if price_data else None
        return ProductAvailability(
            ingredient=ingredient,
            product_name=product.get("product_name") or product.get("generic_name"),
            brand=product.get("brands"),
            barcode=barcode,
            image_url=product.get("image_front_small_url") or product.get("image_url"),
            price=price,
            currency=currency,
            availability="available" if price is not None else "unknown",
            source="openfoodfacts-open-prices" if price is not None else "openfoodfacts",
            notes=[
                "Open Prices is a community dataset; confirm price and availability before purchasing."
                if price is not None
                else "No Open Prices observation was found for this product.",
            ],
        )

    def _lookup_price(self, barcode: str) -> dict[str, Any] | None:
        try:
            payload = self._get_json(
                f"{self.prices_url}?{urllib.parse.urlencode({'product_code': barcode, 'page_size': 20})}"
            )
        except Exception:
            return None
        rows = payload.get("items") or payload.get("prices") or []
        valid = []
        for row in rows:
            try:
                value = float(row.get("price"))
            except (TypeError, ValueError):
                continue
            if value > 0:
                valid.append({"price": value, "currency": row.get("currency") or "USD"})
        return min(valid, key=lambda row: row["price"]) if valid else None

    def _unknown_availability(self, ingredient: str, source: str) -> ProductAvailability:
        return ProductAvailability(
            ingredient=ingredient,
            source=source,
            notes=["No product match found or product API unavailable."],
        )
