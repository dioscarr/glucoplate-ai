import time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
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
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


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
    return response


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/web/index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
