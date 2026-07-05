from app.schemas.recipe_image import RecipeImageRequest


class ImagePromptService:
    def build_prompts(self, request: RecipeImageRequest) -> list[str]:
        ingredients = ", ".join(request.ingredients[:12]) or "balanced ingredients"
        base = (
            f"{request.title}. {request.summary or ''} "
            f"Ingredients: {ingredients}. "
            "Diabetes-conscious balanced meal, appetizing but realistic portions. "
            "No medical claims, no text overlays, no logos, no packaging brands."
        ).strip()

        prompt_styles = [
            "hero plated food photography, natural light, clean kitchen table, 3/4 angle",
            "overhead flat lay of the complete meal, fresh ingredients visible, editorial food photography",
            "ingredient prep layout, colorful vegetables and protein separated, clean cutting board",
            "meal prep containers version, practical weekly healthy eating presentation",
        ]

        return [f"{base} Style: {request.style}, {style}." for style in prompt_styles[: request.image_count]]
