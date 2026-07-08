from typing import Literal

from app.core.secrets import get_secret

ProviderName = Literal["copilot", "gemini", "local"]


def _has_copilot() -> bool:
    try:
        # Use the app wrapper so tests/mocks remain consistent
        from app.ai.copilot_agent_client import CopilotAgentClient

        # Try to instantiate but don't raise on failures - just indicate availability
        try:
            CopilotAgentClient()
            return True
        except Exception:
            return False
    except Exception:
        return False


def _has_gemini() -> bool:
    return bool(get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"))


def available_providers() -> list[ProviderName]:
    """Return configured AI providers in preferred runtime order."""
    providers: list[ProviderName] = []
    if _has_gemini():
        providers.append("gemini")
    if _has_copilot():
        providers.append("copilot")
    providers.append("local")
    return providers


def select_provider(prefer: str | None = "auto") -> ProviderName:
    """Select the best available AI provider.

    prefer: 'auto'|'gemini'|'copilot'|'local'.

    Auto mode intentionally prefers Gemini before Copilot because Gemini is the deployed
    runtime provider configured through normal API keys. Copilot is useful for local/dev
    experimentation, but it may appear installed while not being usable in production.
    """
    p = (prefer or "auto").lower()
    providers = available_providers()

    if p == "local":
        return "local"
    if p in {"gemini", "copilot"} and p in providers:
        return p  # type: ignore[return-value]
    if p in {"gemini", "copilot"}:
        return providers[0]

    return providers[0]
