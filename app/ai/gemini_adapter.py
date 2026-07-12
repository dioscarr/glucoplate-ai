import importlib
from functools import lru_cache
from typing import Any

from loguru import logger

from app.core.secrets import get_secret

_PREFERRED_MODEL = "gemini-2.5-flash"
_GENERATE_ACTIONS = {"generatecontent", "generate_content"}


def _normalise_model_name(name: str) -> str:
    return name.removeprefix("models/")


def _supported_actions(model: Any) -> set[str]:
    actions = (
        getattr(model, "supported_actions", None)
        or getattr(model, "supported_generation_methods", None)
        or []
    )
    return {str(action).replace("-", "_").lower() for action in actions}


def _supports_generate_content(model: Any) -> bool:
    actions = _supported_actions(model)
    return bool(actions & _GENERATE_ACTIONS)


def _choose_model(available_models: list[str], configured_model: str | None) -> str:
    if not available_models:
        raise RuntimeError("Gemini returned no models that support generateContent")

    configured = _normalise_model_name(configured_model) if configured_model else None
    if configured and configured in available_models:
        return configured

    if configured:
        logger.warning(
            "Configured Gemini model '{}' is unavailable. Selecting from models exposed to this API key.",
            configured,
        )

    if _PREFERRED_MODEL in available_models:
        return _PREFERRED_MODEL

    flash_models = [name for name in available_models if "flash" in name.lower()]
    if flash_models:
        return sorted(flash_models, reverse=True)[0]

    return sorted(available_models)[0]


@lru_cache(maxsize=1)
def _client_and_model() -> tuple[Any, str]:
    api_key = get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini API key is not configured")

    module = importlib.import_module("google.genai")
    client = module.Client(api_key=api_key)

    models = list(client.models.list())
    available_models = sorted(
        {
            _normalise_model_name(str(model.name))
            for model in models
            if getattr(model, "name", None) and _supports_generate_content(model)
        }
    )

    logger.info(
        "Gemini models available to this API key for generateContent: {}",
        available_models,
    )

    configured_model = get_secret("GEMINI_MODEL")
    selected_model = _choose_model(available_models, configured_model)
    logger.info("Selected Gemini model: {}", selected_model)

    return client, selected_model


def generate_text(prompt: str) -> str:
    client, model = _client_and_model()
    result = client.models.generate_content(model=model, contents=prompt)
    return result.text or ""
