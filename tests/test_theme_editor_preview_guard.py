from pathlib import Path


def test_theme_editor_skips_missing_preview_selector() -> None:
    source = Path("app/static/theme-editor.js").read_text(encoding="utf-8")

    assert "const selector=selectors[key];if(!selector)return;" in source
    assert "querySelectorAll(selectors[key]||'')" not in source
