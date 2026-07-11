import time

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.routes import router
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="GlucoPlate AI",
    description="AI-powered recipe generation, personalization, saving, and grocery planning API.",
    version="0.3.0",
)

app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def no_cache_html(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
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
        ]
        if method in ("POST", "PUT", "DELETE") and any(route in path for route in tracked_routes):
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
