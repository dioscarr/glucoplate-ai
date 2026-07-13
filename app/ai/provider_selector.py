from typing import Literal

from app.core.secrets import get_secret

ProviderName = Literal["groq", "gemini", "local"]


def _has_groq() -> bool:
    return bool(get_secret("GROQ_API_KEY"))


def _has_gemini() -> bool:
    return bool(get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"))


def available_providers() -> list[ProviderName]:
    """Return configured providers in production preference order."""
    providers: list[ProviderName] = []
    if _has_groq():
        providers.append("groq")
    if _has_gemini():
        providers.append("gemini")
    providers.append("local")
    return providers


def select_provider(prefer: str | None = "auto") -> ProviderName:
    """Select the requested configured provider, preferring Groq for auto mode."""
    requested = (prefer or "auto").lower()
    providers = available_providers()

    if requested in providers:
        return requested  # type: ignore[return-value]
    if requested == "local":
        return "local"

    return providers[0]
