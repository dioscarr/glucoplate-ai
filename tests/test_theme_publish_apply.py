from pathlib import Path


def test_publish_theme_is_activated_and_selected() -> None:
    source = Path("app/static/theme-publish-apply.js").read_text(encoding="utf-8")

    assert "publish')==='true'" in source
    assert "/activate" in source
    assert "localStorage.setItem(storageKey(),themeId)" in source
    assert "Publish & apply" in source


def test_publish_apply_script_is_registered() -> None:
    source = Path("app/main.py").read_text(encoding="utf-8")

    assert '"/static/theme-publish-apply.js"' in source
