from app.schemas.store import ProductAvailability, ProductSearchRequest
from app.services.product_lookup_service import ProductLookupService


class PriceAvailabilityService:
    """Product price and availability facade using Open Food Facts.

    Future adapters: Kroger API, Walmart search, Instacart, Open Food Facts Open Prices.
    """

    def __init__(self, product_lookup_service: ProductLookupService | None = None) -> None:
        self.product_lookup_service = product_lookup_service or ProductLookupService()

    def search(self, request: ProductSearchRequest) -> list[ProductAvailability]:
        return self.product_lookup_service.search_products(request)
