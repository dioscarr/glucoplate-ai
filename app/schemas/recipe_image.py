from pydantic import BaseModel, Field


class RecipeImageRequest(BaseModel):
    recipe_id: str | None = None
    title: str
    summary: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    style: str = Field(default="realistic plated food photography")
    image_count: int = Field(default=4, ge=1, le=4)


class RecipeImageItem(BaseModel):
    image_id: str
    recipe_id: str
    title: str
    prompt: str
    image_url: str | None = None
    provider: str
    status: str = "generated"
    notes: list[str] = Field(default_factory=list)


class RecipeGalleryResponse(BaseModel):
    recipe_id: str
    title: str
    provider: str
    images: list[RecipeImageItem]
