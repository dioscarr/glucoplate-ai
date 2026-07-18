import time

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.enterprise_admin_routes import router as enterprise_admin_router
from app.api.firebase_auth_routes import router as firebase_auth_router
from app.api.live_cook_room_routes import router as live_cook_room_router
from app.api.pantry_routes import router as pantry_router
from app.api.price_observation_routes import router as price_observation_router
from app.api.push_routes import router as push_router
from app.api.receipt_import_routes import router as receipt_import_router
from app.api.recommendation_routes import router as recommendation_router
from app.api.routes import router
from app.api.shopping_list_routes import router as shopping_list_router
from app.api.user_data_routes import router as user_data_router
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="GlucoPlate AI",
    description="AI-powered recipe generation, personalization, saving, grocery planning, and collaborative cooking API.",
    version="0.16.0",
)

app.include_router(router)
app.include_router(push_router)
app.include_router(firebase_auth_router)
app.include_router(enterprise_admin_router)
app.include_router(user_data_router)
app.include_router(recommendation_router)
app.include_router(pantry_router)
app.include_router(shopping_list_router)
app.include_router(price_observation_router)
app.include_router(receipt_import_router)
app.include_router(live_cook_room_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

HTML_SCRIPT_PATHS = (
    "/static/device-manager.js",
    "/static/native-cook.js",
    "/static/live-cook-rooms.js",
    "/static/native-timers.js",
    "/static/native-ingredients.js",
    "/static/offline-actions.js",
    "/static/firebase-auth.js",
    "/static/firebase-user-data.js",
    "/static/profile-personalization.js",
    "/static/pantry-ui.js",
    "/static/shopping-list-ui.js",
    "/static/receipt-import-ui.js",
    "/static/pantry-generation.js",
    "/static/recommendation-ui.js",
    "/static/theme-runtime.js",
    "/static/theme-publish-apply.js",
    "/static/pwa.js",
)


@app.middleware("http")
async def pwa_headers_and_script(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path

    if path.endswith("/sw.js"):
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"

    if path.endswith(".webmanifest"):
        response.headers["Content-Type"] = "application/manifest+json"

    if path.endswith(".html"):
        chunks = [chunk async for chunk in response.body_iterator]
        body = b"".join(chunks)
        head_marker = b"</head>"
        body_marker = b"</body>"
        native_style = b'<link rel="stylesheet" href="/static/native-pwa.css" /></head>'

        if b"/static/native-pwa.css" not in body and head_marker in body:
            body = body.replace(head_marker, native_style)

        for script_path in HTML_SCRIPT_PATHS:
            encoded_path = script_path.encode()
            if encoded_path not in body and body_marker in body:
                tag = b'<script src="' + encoded_path + b'" defer></script></body>'
                body = body.replace(body_marker, tag)

        headers = dict(response.headers)
        headers.pop("content-length", None)
        headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        headers["Pragma"] = "no-cache"
        headers["Expires"] = "0"
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "{method} {path} -> {status} ({duration:.1f}ms)",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration_ms,
    )

    try:
        from app.ai.agent_memory import AgentMemory

        memory = AgentMemory()
        path = request.url.path or ""
        method = request.method or ""
        tracked_routes = [
            "/api/recipes",
            "/api/ingredients",
            "/api/carts",
            "/api/products",
            "/api/stores",
            "/api/auth",
            "/api/firebase-auth",
            "/api/enterprise",
            "/api/user-data",
            "/api/recommendations",
            "/api/pantry",
            "/api/shopping-list",
            "/api/price-observations",
            "/api/receipt-imports",
            "/api/live-cook-rooms",
            "/api/push",
        ]
        if method in ("POST", "PUT", "PATCH", "DELETE") and any(route in path for route in tracked_routes):
            try:
                body = await request.body()
                memory.add_memory(
                    f"{method} {path} payload_len={len(body)} status={response.status_code}",
                    tags=["api_event"],
                )
            except Exception:
                memory.add_memory(f"{method} {path} (payload unreadable)", tags=["api_event"])
    except Exception:
        pass

    return response


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "product": "GlucoPlate AI"}
