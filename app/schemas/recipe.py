from pydantic import BaseModel, Field


class RecipeRequest(BaseModel):
    goal: str = Field(..., examples=["quick Dominican-style dinner with chicken and rice"])
    servings: int = Field(default=2, ge=1, le=12)
    max_carbs_per_serving: int | None = Field(
        default=None,
        ge=0,
        le=150,
        description="Optional nutrition preference, not a required health target.",
    )
    preferences: list[str] = Field(default_factory=list)
    avoid_ingredients: list[str] = Field(default_factory=list)
    culture: str | None = Field(default=None, examples=["Dominican", "Latin", "Mediterranean"])
    pantry_items: list[str] = Field(default_factory=list, max_length=200)
    use_soon_ingredients: list[str] = Field(default_factory=list, max_length=50)


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


class PantryCoverage(BaseModel):
    available_count: int = 0
    required_count: int = 0
    coverage_ratio: float = 0
    coverage_percent: int = 0


class RecipeResponse(BaseModel):
    title: str
    summary: str
    ingredients: list[str]
    steps: list[str]
    nutrition_estimate: NutritionEstimate
    substitutions: list[str]
    safety_review: SafetyReview
    ai_provider: str = "fallback"
    already_have: list[str] = Field(default_factory=list)
    need_to_buy: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    use_soon_matches: list[str] = Field(default_factory=list)
    pantry_coverage: PantryCoverage = Field(default_factory=PantryCoverage)
