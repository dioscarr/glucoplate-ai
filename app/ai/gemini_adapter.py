import importlib

from app.core.secrets import get_secret


_CURRENT_STABLE_MODEL = "gemini-3.5-flash"
_MODEL_REPLACEMENTS = {
    "gemini-1.5-flash": _CURRENT_STABLE_MODEL,
    "gemini-2.0-flash": _CURRENT_STABLE_MODEL,
    "gemini-2.5-flash": _CURRENT_STABLE_MODEL,
    "gemini-2.5-flash-latest": _CURRENT_STABLE_MODEL,
    "gemini-flash-latest": _CURRENT_STABLE_MODEL,
}


def generate_text(prompt: str) -> str:
    api_key = get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini API key is not configured")

    configured_model = get_secret("GEMINI_MODEL") or _CURRENT_STABLE_MODEL
    model = _MODEL_REPLACEMENTS.get(configured_model, configured_model)

    module = importlib.import_module("google.genai")
    types_module = importlib.import_module("google.genai.types")
    client = module.Client(
        api_key=api_key,
        http_options=types_module.HttpOptions(api_version="v1"),
    )
    result = client.models.generate_content(model=model, contents=prompt)
    return result.text or ""
