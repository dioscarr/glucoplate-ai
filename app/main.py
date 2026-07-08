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
    description="AI-powered diabetes-friendly recipe and meal-planning system.",
    version="0.1.0",
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

    # Update agent memory for key actions to keep short/long-term context fresh.
    try:
        from app.ai.agent_memory import AgentMemory
        am = AgentMemory()
        path = request.url.path or ''
        method = request.method or ''
        # Only record POST/PUT actions on important routes to avoid noise
        if method in ('POST', 'PUT') and any(p in path for p in ['/api/recipes', '/api/carts', '/api/products', '/api/stores', '/api/recipes/gallery']):
            try:
                # Read small payload safely
                body = await request.body()
                summary = f"{method} {path} payload_len={len(body)} status={response.status_code}"
                # Add short fact to memory
                am.add_memory(summary, tags=['api_event'])
            except Exception:
                am.add_memory(f"{method} {path} (payload unreadable)", tags=['api_event'])
    except Exception:
        # Don't break requests if memory subsystem fails
        pass

    return response


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/static/modern.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
