from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="GlucoPlate AI",
    description="AI-powered diabetes-friendly recipe and meal-planning system.",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
