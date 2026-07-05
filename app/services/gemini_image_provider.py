import base64
import os
from pathlib import Path
from uuid import uuid4


class GeminiImageProvider:
    """Image-only provider for recipe gallery generation.

    Uses GOOGLE_GEMINI_API_KEY. This provider must not be used for recipe text,
    nutrition, stores, or safety workflows.
    """

    provider_name = "google-gemini-image"

    def __init__(self, model: str | None = None, output_dir: str = "app/web/static/generated") -> None:
        self.model = model or os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
        self.output_dir = Path(output_dir)

    def is_configured(self) -> bool:
        return bool(os.environ.get("GOOGLE_GEMINI_API_KEY"))

    def generate_image(self, prompt: str, recipe_id: str) -> str | None:
        if not self.is_configured():
            return None

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai package is not installed.") from exc

        client = genai.Client(api_key=os.environ["GOOGLE_GEMINI_API_KEY"])
        response = client.models.generate_content(model=self.model, contents=prompt)
        image_bytes = self._extract_image_bytes(response)
        if not image_bytes:
            return None

        recipe_dir = self.output_dir / recipe_id
        recipe_dir.mkdir(parents=True, exist_ok=True)
        image_id = f"{uuid4().hex}.png"
        image_path = recipe_dir / image_id
        image_path.write_bytes(image_bytes)

        return f"/static/generated/{recipe_id}/{image_id}"

    def _extract_image_bytes(self, response) -> bytes | None:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if not inline_data:
                    continue
                data = getattr(inline_data, "data", None)
                if not data:
                    continue
                if isinstance(data, bytes):
                    return data
                if isinstance(data, str):
                    return base64.b64decode(data)
        return None
