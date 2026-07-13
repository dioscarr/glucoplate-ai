from app.ai import provider_selector


def _secret_lookup(values: dict[str, str]):
    def get_secret(*names: str) -> str | None:
        for name in names:
            value = values.get(name)
            if value:
                return value
        return None

    return get_secret


def test_groq_is_preferred_when_configured(monkeypatch):
    monkeypatch.setattr(
        provider_selector,
        "get_secret",
        _secret_lookup({"GROQ_API_KEY": "test-groq", "GEMINI_API_KEY": "test-gemini"}),
    )

    assert provider_selector.available_providers() == ["groq", "gemini", "local"]
    assert provider_selector.select_provider("auto") == "groq"


def test_gemini_is_secondary_when_groq_is_missing(monkeypatch):
    monkeypatch.setattr(
        provider_selector,
        "get_secret",
        _secret_lookup({"GEMINI_API_KEY": "test-gemini"}),
    )

    assert provider_selector.available_providers() == ["gemini", "local"]
    assert provider_selector.select_provider("auto") == "gemini"


def test_local_is_final_fallback(monkeypatch):
    monkeypatch.setattr(provider_selector, "get_secret", _secret_lookup({}))

    assert provider_selector.available_providers() == ["local"]
    assert provider_selector.select_provider("auto") == "local"
