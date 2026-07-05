# Recipe Image Gallery

## Purpose

Recipe images are generated as a gallery after a recipe is created. This is a separate workflow from recipe text generation, nutrition review, store lookup, and safety review.

## Provider Boundary

Gemini/Nano Banana is used only for image generation.

Environment variable:

```bash
GOOGLE_GEMINI_API_KEY=your-key-here
```

Optional model override:

```bash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image-preview
```

## Workflow

```text
RecipeResponse
  -> ImagePromptService
  -> GeminiImageProvider
  -> Generated image files
  -> RecipeGalleryResponse
```

## Endpoint

```http
POST /api/recipes/gallery
```

Request:

```json
{
  "recipe_id": "dominican-chicken-bowl",
  "title": "Dominican-Inspired Chicken Bowl",
  "summary": "Balanced chicken bowl with vegetables and controlled carbs.",
  "ingredients": ["chicken", "black beans", "cauliflower rice", "avocado"],
  "style": "realistic plated food photography",
  "image_count": 4
}
```

Response:

```json
{
  "recipe_id": "dominican-chicken-bowl",
  "title": "Dominican-Inspired Chicken Bowl",
  "provider": "google-gemini-image",
  "images": [
    {
      "image_id": "dominican-chicken-bowl-1",
      "recipe_id": "dominican-chicken-bowl",
      "title": "Dominican-Inspired Chicken Bowl image 1",
      "prompt": "...",
      "image_url": "/static/generated/dominican-chicken-bowl/example.png",
      "provider": "google-gemini-image",
      "status": "generated",
      "notes": []
    }
  ]
}
```

## Fallback Behavior

If `GOOGLE_GEMINI_API_KEY` is missing, the API returns prompt-only gallery items. This keeps the UI and workflow testable without spending image generation credits.

## Safety Rules

Image prompts should avoid:

- medical claims
- brand logos
- packaging brands
- fake certification labels
- text overlays that could imply clinical approval

## Future Enhancements

- Persist gallery metadata in `data/galleries.json`
- Add regenerate image button
- Add image rating/review workflow
- Add style presets
- Add gallery caching by recipe hash
