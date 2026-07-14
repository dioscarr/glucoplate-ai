from fastapi import APIRouter, HTTPException, Query

from app.core.secrets import get_secret
from app.schemas.auth import (
    AccessCodeLookupRequest,
    AccessCodeLookupResponse,
    AuthResponse,
    CompanyAccessCode,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.receipt import Receipt, ReceiptExtractRequest, ReceiptSummary
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.recipe_image import RecipeImageRequest
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.cart_store_service import CartStoreService
from app.services.gallery_job_service import GalleryJobService
from app.services.ingredient_normalizer import normalize_ingredients
from app.services.price_availability_service import PriceAvailabilityService
from app.services.receipt_parser_service import ReceiptParserService
from app.services.receipt_store_service import ReceiptStoreService
from app.services.recipe_generator import generate_recipe
from app.services.recipe_store_service import RecipeStoreService
from app.services.recents_service import RecentsService
from app.services.route_service import RouteService
from app.services.simple_auth_service import SimpleAuthService
from app.services.store_locator_service import StoreLocatorService
from app.services.web_scraper_service import fetch_metadata

router = APIRouter(prefix="/api")


@router.post("/auth/access-code", response_model=AccessCodeLookupResponse)
def lookup_access_code(request: AccessCodeLookupRequest) -> AccessCodeLookupResponse:
    return SimpleAuthService().lookup_access_code(request.access_code)


@router.post("/auth/register", response_model=AuthResponse)
def register_with_access_code(request: RegisterRequest) -> AuthResponse:
    response = SimpleAuthService().register(request)
    if not response.ok:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.post("/auth/login", response_model=AuthResponse)
def login_with_demo_provider(request: LoginRequest) -> AuthResponse:
    response = SimpleAuthService().login(str(request.email))
    if not response.ok:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.get("/auth/companies", response_model=list[CompanyAccessCode])
def list_demo_companies() -> list[CompanyAccessCode]:
    return SimpleAuthService().list_companies()


@router.post("/receipts/extract", response_model=Receipt)
def extract_receipt(request: ReceiptExtractRequest) -> Receipt:
    return ReceiptParserService().extract(request.text)


@router.post("/receipts/save", response_model=dict)
def save_receipt(receipt: Receipt) -> dict:
    return {"ok": True, "receipt": ReceiptStoreService().save(receipt)}


@router.get("/receipts", response_model=list[dict])
def list_receipts(
    merchant: str | None = None,
    category: str | None = None,
    search: str | None = None,
) -> list[dict]:
    return ReceiptStoreService().list(merchant=merchant, category=category, search=search)


@router.get("/receipts/summary", response_model=ReceiptSummary)
def receipt_summary() -> ReceiptSummary:
    return ReceiptStoreService().summary()


@router.get("/receipts/{receipt_id}", response_model=dict)
def get_receipt(receipt_id: str) -> dict:
    receipt = ReceiptStoreService().get(receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.put("/receipts/{receipt_id}", response_model=dict)
def update_receipt(receipt_id: str, receipt: Receipt) -> dict:
    updated = ReceiptStoreService().update(receipt_id, receipt)
    if updated is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {"ok": True, "receipt": updated}


@router.delete("/receipts/{receipt_id}", response_model=dict)
def delete_receipt(receipt_id: str) -> dict:
    deleted = ReceiptStoreService().delete(receipt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {"ok": True}


@router.post("/recipes/generate", response_model=RecipeResponse)
async def generate_recipe_endpoint(
    request: RecipeRequest,
    use_ai: bool = Query(default=True, description="Use configured AI provider when available."),
    provider: str = Query(
        default="auto",
        description="Preferred provider: auto, gemini, copilot, or local.",
    ),
) -> RecipeResponse:
    return await generate_recipe(request, use_ai=use_ai, provider=provider)


@router.post("/stores/search", response_model=list[Store])
def search_stores_endpoint(request: StoreSearchRequest) -> list[Store]:
    return StoreLocatorService().find_nearby_stores(request)


@router.post("/products/search", response_model=list[ProductAvailability])
def search_products_endpoint(request: ProductSearchRequest) -> list[ProductAvailability]:
    return PriceAvailabilityService().search(request)


@router.post("/recipes/gallery")
def enqueue_recipe_gallery(request: RecipeImageRequest):
    job_svc = GalleryJobService()
    job_id = job_svc.enqueue(request.dict() if hasattr(request, "dict") else dict(request))
    return {"ok": True, "job_id": job_id}


@router.get("/recipes/gallery/{job_id}")
def get_gallery_job(job_id: str):
    job = GalleryJobService().get(job_id)
    if not job:
        return {"ok": False, "error": "not found"}
    return job


@router.post("/recipes/save")
def save_recipe_endpoint(recipe: dict):
    return {"ok": True, "recipe": RecipeStoreService().save(recipe)}


@router.get("/recipes/list")
def list_recipes_endpoint():
    return RecipeStoreService().list()


@router.post("/recipes/recents")
def add_recent(recipe: dict):
    return {"ok": True, "recent": RecentsService().add(recipe)}


@router.get("/recipes/recents")
def list_recents(limit: int = 20):
    return RecentsService().list(limit=limit)


@router.post("/carts", response_model=dict)
def create_cart(cart: dict):
    return {"ok": True, "cart": CartStoreService().create(cart)}


@router.get("/carts", response_model=list)
def list_carts():
    return CartStoreService().list()


@router.get("/carts/{cart_id}", response_model=dict)
def get_cart(cart_id: str):
    return CartStoreService().get(cart_id) or {}


@router.put("/carts/{cart_id}", response_model=dict)
def update_cart(cart_id: str, cart: dict):
    updated = CartStoreService().update(cart_id, cart)
    return {"ok": bool(updated), "cart": updated}


@router.delete("/carts/{cart_id}", response_model=dict)
def delete_cart(cart_id: str):
    return {"ok": bool(CartStoreService().delete(cart_id))}


@router.post("/route/plan")
def plan_route(request: dict):
    start_lat = request.get("start_lat")
    start_lng = request.get("start_lng")
    stops = [Store(**store) for store in request.get("stops", [])]
    return RouteService().plan_route(start_lat, start_lng, stops)


@router.post("/stores/enrich")
def enrich_stores(request: dict):
    stores = [Store(**store) for store in request.get("stores", [])]
    enriched = []
    for store in stores:
        meta = {}
        if store.website:
            try:
                meta = fetch_metadata(store.website)
            except Exception:
                meta = {}
        payload = store.dict()
        payload["meta"] = meta
        enriched.append(payload)
    return enriched


@router.post("/ingredients/normalize")
def normalize_ingredients_endpoint(request: dict):
    return {"normalized": normalize_ingredients(request.get("ingredients") or [])}


@router.get("/ai/health")
async def ai_health() -> dict:
    from app.ai.provider_selector import available_providers, select_provider

    gemini_configured = bool(get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"))
    try:
        import copilot  # type: ignore

        copilot_installed = True
        copilot_error = None
        copilot_version = getattr(copilot, "__version__", None)
    except Exception as exc:  # pragma: no cover
        copilot_installed = False
        copilot_error = str(exc)
        copilot_version = None

    return {
        "selected_provider": select_provider("auto"),
        "available_providers": available_providers(),
        "gemini_configured": gemini_configured,
        "copilot_installed": copilot_installed,
        "copilot_version": copilot_version,
        "copilot_error": copilot_error,
    }
