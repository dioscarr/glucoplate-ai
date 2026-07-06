from fastapi import APIRouter, Query

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.price_availability_service import PriceAvailabilityService
from app.services.recipe_generator import generate_recipe
from app.services.store_locator_service import StoreLocatorService

router = APIRouter(prefix="/api")


@router.post("/recipes/generate", response_model=RecipeResponse)
async def generate_recipe_endpoint(
    request: RecipeRequest,
    use_ai: bool = Query(default=True, description="Use Copilot SDK provider when available."),
) -> RecipeResponse:
    return await generate_recipe(request, use_ai=use_ai)


@router.post("/stores/search", response_model=list[Store])
def search_stores_endpoint(request: StoreSearchRequest) -> list[Store]:
    return StoreLocatorService().find_nearby_stores(request)


@router.post("/products/search", response_model=list[ProductAvailability])
def search_products_endpoint(request: ProductSearchRequest) -> list[ProductAvailability]:
    return PriceAvailabilityService().search(request)


@router.get("/ai/health")
async def ai_health() -> dict:
    """Quick check whether the GitHub Copilot SDK Python package is importable."""
    try:
        import copilot  # type: ignore

        return {"copilot_installed": True, "version": getattr(copilot, "__version__", None)}
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        return {"copilot_installed": False, "error": str(exc)}
