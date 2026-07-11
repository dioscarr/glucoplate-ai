import importlib

from app.core.secrets import get_secret


_RETIRED_MODEL_REPLACEMENTS = {
    "gemini-1.5-flash": "gemini-2.5-flash",
    "gemini-2.0-flash": "gemini-2.5-flash",
}


def generate_text(prompt: str) -> str:
    api_key = get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini API key is not configured")

    configured_model = get_secret("GEMINI_MODEL") or "gemini-2.5-flash"
    model = _RETIRED_MODEL_REPLACEMENTS.get(configured_model, configured_model)

    module = importlib.import_module("google.genai")
    client = module.Client(api_key=api_key)
    result = client.models.generate_content(model=model, contents=prompt)
    return result.text or ""
