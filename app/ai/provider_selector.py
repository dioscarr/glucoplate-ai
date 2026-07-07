import os
from typing import Literal


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
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY"))


def select_provider(prefer: str | None = "auto") -> Literal["copilot", "gemini", "local"]:
    """Select the best available AI provider.

    prefer: 'auto'|'copilot'|'gemini'|'local' - if 'auto', prefer Copilot then Gemini then local.

    Returns one of: 'copilot', 'gemini', or 'local'.
    """
    p = (prefer or "auto").lower()
    if p == "local":
        return "local"
    if p == "copilot":
        return "copilot" if _has_copilot() else ("gemini" if _has_gemini() else "local")
    if p == "gemini":
        return "gemini" if _has_gemini() else ("copilot" if _has_copilot() else "local")

    # auto
    if _has_copilot():
        return "copilot"
    if _has_gemini():
        return "gemini"
    return "local"
