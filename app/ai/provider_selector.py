from typing import Literal

from app.core.secrets import get_secret

ProviderName = Literal["gemini", "local"]


def _has_gemini() -> bool:
    return bool(get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"))


def available_providers() -> list[ProviderName]:
    """Return configured providers in production preference order."""
    providers: list[ProviderName] = []
    if _has_gemini():
        providers.append("gemini")
    providers.append("local")
    return providers


def select_provider(prefer: str | None = "auto") -> ProviderName:
    """Select Gemini when configured; otherwise use the local generator."""
    requested = (prefer or "auto").lower()
    providers = available_providers()

    if requested == "local":
        return "local"
    if requested == "gemini" and "gemini" in providers:
        return "gemini"

    return providers[0]
