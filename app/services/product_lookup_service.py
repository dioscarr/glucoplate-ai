import json
import urllib.parse
import urllib.request
from typing import Any

from app.schemas.store import ProductAvailability, ProductSearchRequest


class ProductLookupService:
    """Search packaged food products using Open Food Facts."""

    search_url = "https://world.openfoodfacts.org/cgi/search.pl"

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
            http_request = urllib.request.Request(
                url,
                headers={"User-Agent": "GlucoPlateAI/0.1 (learning project)"},
            )
            with urllib.request.urlopen(http_request, timeout=10) as response:
                payload = response.read().decode("utf-8")
        except Exception:
            return [self._unknown_availability(request.ingredient, "openfoodfacts-unavailable")]

        data = json.loads(payload)
        products = data.get("products", [])
        if not products:
            return [self._unknown_availability(request.ingredient, "openfoodfacts")]

        return [self._map_product(request.ingredient, product) for product in products]

    def _map_product(self, ingredient: str, product: dict[str, Any]) -> ProductAvailability:
        return ProductAvailability(
            ingredient=ingredient,
            product_name=product.get("product_name") or product.get("generic_name"),
            brand=product.get("brands"),
            barcode=product.get("code"),
            image_url=product.get("image_front_small_url") or product.get("image_url"),
            price=None,
            currency=None,
            availability="unknown",
            source="openfoodfacts",
            notes=[
                "Open Food Facts provides product metadata and nutrition data, not live store inventory.",
                "Price and availability require a retailer-specific API or user-submitted price source.",
            ],
        )

    def _unknown_availability(self, ingredient: str, source: str) -> ProductAvailability:
        return ProductAvailability(
            ingredient=ingredient,
            source=source,
            notes=["No product match found or product API unavailable."],
        )
