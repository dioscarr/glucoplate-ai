import json
from typing import Any

from app.ai.json_utils import extract_json_text
from app.schemas.recipe import NutritionEstimate, RecipeRequest, RecipeResponse, SafetyReview


class CopilotRecipeProvider:
    """Recipe provider using the GitHub Copilot SDK cookbook pattern.

    This provider is intentionally isolated from the rest of the application so the
    app can still run with local fallback data when the Copilot SDK/CLI is not
    available in the environment.
    """

    provider_name = "github-copilot-sdk"

    async def generate(self, request: RecipeRequest) -> RecipeResponse:
        try:
            from copilot import CopilotClient, PermissionHandler
        except ImportError as exc:
            raise RuntimeError(
                "GitHub Copilot SDK is not installed or available in this environment."
            ) from exc

        client = CopilotClient()
        await client.start()

        try:
            # Prefer runtime default model unless a specific model is required
            session = await client.create_session(on_permission_request=PermissionHandler.approve_all)

            prompt = self._build_prompt(request)
            response = await session.send_and_wait(prompt, timeout=45.0)
            await session.disconnect()

            if not response or not response.data or not response.data.content:
                raise RuntimeError("Copilot SDK returned an empty response.")

            return self._parse_response(response.data.content)
        finally:
            await client.stop()

    def _build_prompt(self, request: RecipeRequest) -> str:
        return f"""
You are generating a diabetes-conscious recipe for a wellness-support app.
This is not medical advice. Do not diagnose, treat, cure, or adjust medication.

Return ONLY valid JSON matching this shape:
{{
  "title": "string",
  "summary": "string",
  "ingredients": ["string"],
  "steps": ["string"],
  "nutrition_estimate": {{
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fiber_g": 0,
    "sugar_g": 0,
    "fat_g": 0,
    "sodium_mg": 0
  }},
  "substitutions": ["string"],
  "safety_review": {{
    "approved": true,
    "warnings": ["string"],
    "disclaimer": "string"
  }}
}}

User request:
- Goal: {request.goal}
- Servings: {request.servings}
- Max carbs per serving: {request.max_carbs_per_serving}
- Preferences: {request.preferences}
- Avoid ingredients: {request.avoid_ingredients}
- Cultural style: {request.culture}
""".strip()

    def _parse_response(self, raw_content: str) -> RecipeResponse:
        try:
            payload: dict[str, Any] = json.loads(extract_json_text(raw_content))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Copilot SDK response was not valid JSON.") from exc

        payload["ai_provider"] = self.provider_name
        return RecipeResponse.model_validate(payload)
