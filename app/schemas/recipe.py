from pydantic import BaseModel, Field


class RecipeRequest(BaseModel):
    goal: str = Field(..., examples=["quick Dominican-style dinner"])
    servings: int = Field(default=2, ge=1, le=12)
    max_carbs_per_serving: int | None = Field(default=45, ge=0, le=150)
    preferences: list[str] = Field(default_factory=list)
    avoid_ingredients: list[str] = Field(default_factory=list)
    culture: str | None = Field(default=None, examples=["Dominican", "Latin", "Mediterranean"])


class NutritionEstimate(BaseModel):
    calories: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fiber_g: float | None = None
    sugar_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None


class SafetyReview(BaseModel):
    approved: bool
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str


class RecipeResponse(BaseModel):
    title: str
    summary: str
    ingredients: list[str]
    steps: list[str]
    nutrition_estimate: NutritionEstimate
    substitutions: list[str]
    safety_review: SafetyReview
    ai_provider: str = "fallback"
