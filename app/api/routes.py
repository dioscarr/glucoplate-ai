from fastapi import APIRouter, Query

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.price_availability_service import PriceAvailabilityService
from app.services.recipe_generator import generate_recipe
from app.services.store_locator_service import StoreLocatorService
from app.services.recipe_gallery_service import RecipeGalleryService
from app.services.recipe_store_service import RecipeStoreService
from app.schemas.recipe_image import RecipeImageRequest, RecipeGalleryResponse

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


@router.post("/recipes/gallery", response_model=RecipeGalleryResponse)
def generate_recipe_gallery_endpoint(request: RecipeImageRequest) -> RecipeGalleryResponse:
    service = RecipeGalleryService()
    return service.generate_gallery(request)


@router.post("/recipes/save")
def save_recipe_endpoint(recipe: dict):
    """Save a generated recipe to the local JSON store."""
    svc = RecipeStoreService()
    saved = svc.save(recipe)
    return {"ok": True, "recipe": saved}


@router.get("/recipes/list")
def list_recipes_endpoint():
    svc = RecipeStoreService()
    return svc.list()


@router.get("/ai/health")
async def ai_health() -> dict:
    """Quick check whether the GitHub Copilot SDK Python package is importable."""
    try:
        import copilot  # type: ignore

        return {"copilot_installed": True, "version": getattr(copilot, "__version__", None)}
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        return {"copilot_installed": False, "error": str(exc)}
