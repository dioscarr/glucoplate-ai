from app.schemas.store import ProductAvailability, ProductSearchRequest
from app.services.product_lookup_service import ProductLookupService


class PriceAvailabilityService:
    """Product price and availability facade.

    MVP behavior:
    - Uses Open Food Facts for product metadata.
    - Returns unknown price and inventory unless a retailer adapter is added.

    Future adapters:
    - Kroger API
    - Walmart affiliate/search APIs where permitted
    - Instacart/retailer partner APIs
    - Open Food Facts Open Prices, where available
    - User-submitted local price observations
    """

    def __init__(self, product_lookup_service: ProductLookupService | None = None) -> None:
        self.product_lookup_service = product_lookup_service or ProductLookupService()

    def search(self, request: ProductSearchRequest) -> list[ProductAvailability]:
        return self.product_lookup_service.search_products(request)
