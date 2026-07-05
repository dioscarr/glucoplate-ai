from fastapi import APIRouter, Query

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.recipe_image import RecipeGalleryResponse, RecipeImageRequest
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.price_availability_service import PriceAvailabilityService
from app.services.recipe_gallery_service import RecipeGalleryService
from app.services.recipe_generator import generate_recipe
from app.services.store_locator_service import StoreLocatorService

router = APIRouter(prefix="/api")


@router.post("/recipes/generate", response_model=RecipeResponse)
async def generate_recipe_endpoint(
    request: RecipeRequest,
    use_ai: bool = Query(default=True, description="Use Copilot SDK provider when available."),
) -> RecipeResponse:
    return await generate_recipe(request, use_ai=use_ai)


@router.post("/recipes/gallery", response_model=RecipeGalleryResponse)
def generate_recipe_gallery_endpoint(request: RecipeImageRequest) -> RecipeGalleryResponse:
    service = RecipeGalleryService()
    return service.generate_gallery(request)


@router.post("/stores/search", response_model=list[Store])
def search_stores_endpoint(request: StoreSearchRequest) -> list[Store]:
    service = StoreLocatorService()
    return service.find_nearby_stores(request)


@router.post("/products/search", response_model=list[ProductAvailability])
def search_products_endpoint(request: ProductSearchRequest) -> list[ProductAvailability]:
    service = PriceAvailabilityService()
    return service.search(request)
