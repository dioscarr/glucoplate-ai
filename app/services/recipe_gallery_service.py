from uuid import uuid4

from app.schemas.recipe_image import RecipeGalleryResponse, RecipeImageItem, RecipeImageRequest
from app.services.gemini_image_provider import GeminiImageProvider
from app.services.image_prompt_service import ImagePromptService


class RecipeGalleryService:
    def __init__(
        self,
        prompt_service: ImagePromptService | None = None,
        image_provider: GeminiImageProvider | None = None,
    ) -> None:
        self.prompt_service = prompt_service or ImagePromptService()
        self.image_provider = image_provider or GeminiImageProvider()

    def generate_gallery(self, request: RecipeImageRequest) -> RecipeGalleryResponse:
        recipe_id = request.recipe_id or self._slugify(request.title)
        prompts = self.prompt_service.build_prompts(request)
        images: list[RecipeImageItem] = []

        for index, prompt in enumerate(prompts, start=1):
            image_url = self.image_provider.generate_image(prompt, recipe_id)
            status = "generated" if image_url else "prompt-only"
            notes = [] if image_url else [
                "Image was not generated. Configure GOOGLE_GEMINI_API_KEY and google-genai to enable Gemini image generation."
            ]
            images.append(
                RecipeImageItem(
                    image_id=f"{recipe_id}-{index}",
                    recipe_id=recipe_id,
                    title=f"{request.title} image {index}",
                    prompt=prompt,
                    image_url=image_url,
                    provider=self.image_provider.provider_name,
                    status=status,
                    notes=notes,
                )
            )

        return RecipeGalleryResponse(
            recipe_id=recipe_id,
            title=request.title,
            provider=self.image_provider.provider_name,
            images=images,
        )

    def _slugify(self, value: str) -> str:
        cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
        cleaned = "-".join(part for part in cleaned.split("-") if part)
        return cleaned[:80] or uuid4().hex
