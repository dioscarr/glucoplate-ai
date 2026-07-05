from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="GlucoPlate AI",
    description="AI-powered diabetes-friendly recipe and meal-planning system.",
    version="0.1.0",
)

app.include_router(router)
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/web/index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
