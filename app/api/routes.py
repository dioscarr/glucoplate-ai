from fastapi import APIRouter, Query

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.price_availability_service import PriceAvailabilityService
from app.services.recipe_generator import generate_recipe
from app.services.store_locator_service import StoreLocatorService
from app.services.recipe_gallery_service import RecipeGalleryService
from app.services.recipe_store_service import RecipeStoreService
from app.services.cart_store_service import CartStoreService
from app.services.store_locator_service import StoreLocatorService
from app.services.route_service import RouteService
from app.services.web_scraper_service import fetch_metadata
from app.services.ingredient_normalizer import normalize_ingredients
from app.schemas.recipe_image import RecipeImageRequest, RecipeGalleryResponse
from app.schemas.store import StoreSearchRequest, Store

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


from app.services.gallery_job_service import GalleryJobService


@router.post("/recipes/gallery")
def enqueue_recipe_gallery(request: RecipeImageRequest):
    """Enqueue an image generation job and return a job_id. Use GET /api/recipes/gallery/{job_id} to poll."""
    job_svc = GalleryJobService()
    job_id = job_svc.enqueue(request.dict() if hasattr(request, 'dict') else dict(request))
    return {"ok": True, "job_id": job_id}


@router.get('/recipes/gallery/{job_id}')
def get_gallery_job(job_id: str):
    job_svc = GalleryJobService()
    job = job_svc.get(job_id)
    if not job:
        return {"ok": False, "error": "not found"}
    return job


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


# Recents: simple file-backed list of generated recipe summaries
from app.services.recents_service import RecentsService


@router.post('/recipes/recents')
def add_recent(recipe: dict):
    svc = RecentsService()
    entry = svc.add(recipe)
    return {'ok': True, 'recent': entry}


@router.get('/recipes/recents')
def list_recents(limit: int = 20):
    svc = RecentsService()
    return svc.list(limit=limit)


@router.post('/carts', response_model=dict)
def create_cart(cart: dict):
    svc = CartStoreService()
    created = svc.create(cart)
    return {'ok': True, 'cart': created}


@router.get('/carts', response_model=list)
def list_carts():
    svc = CartStoreService()
    return svc.list()


@router.get('/carts/{cart_id}', response_model=dict)
def get_cart(cart_id: str):
    svc = CartStoreService()
    c = svc.get(cart_id)
    return c or {}


@router.put('/carts/{cart_id}', response_model=dict)
def update_cart(cart_id: str, cart: dict):
    svc = CartStoreService()
    updated = svc.update(cart_id, cart)
    return {'ok': bool(updated), 'cart': updated}


@router.post('/route/plan')
def plan_route(request: dict):
    """Plan an ordered route for the provided cart with stops as store IDs or coordinates.
    Request should include: start_lat, start_lng, stops: [{id, latitude, longitude, ...}]
    """
    start_lat = request.get('start_lat')
    start_lng = request.get('start_lng')
    stops = [Store(**s) for s in request.get('stops', [])]
    rs = RouteService()
    return rs.plan_route(start_lat, start_lng, stops)


@router.post('/stores/enrich')
def enrich_stores(request: dict):
    """Given a list of stores (from OSM), enrich with website meta tags where available."""
    stores = [Store(**s) for s in request.get('stores', [])]
    enriched = []
    for s in stores:
        meta = {}
        if s.website:
            try:
                meta = fetch_metadata(s.website)
            except Exception:
                meta = {}
        store = s.dict()
        store['meta'] = meta
        enriched.append(store)
    return enriched


@router.post('/ingredients/normalize')
def normalize_ingredients_endpoint(request: dict):
    """Normalize a list of ingredient strings into structured search terms."""
    ingredients = request.get('ingredients') or []
    result = normalize_ingredients(ingredients)
    return {'normalized': result}


@router.get("/ai/health")
async def ai_health() -> dict:
    """Quick check whether the GitHub Copilot SDK Python package is importable."""
    try:
        import copilot  # type: ignore

        return {"copilot_installed": True, "version": getattr(copilot, "__version__", None)}
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        return {"copilot_installed": False, "error": str(exc)}
