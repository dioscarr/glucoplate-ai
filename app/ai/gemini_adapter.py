import importlib
import os


def generate_text(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini API key is not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    module = importlib.import_module("google.genai")
    client = module.Client(api_key=api_key)
    result = client.models.generate_content(model=model, contents=prompt)
    return result.text or ""
