from pathlib import Path


def test_all_html_pages_load_the_component_design_system() -> None:
    main = Path("app/main.py").read_text(encoding="utf-8")

    assert "/static/design-tokens.css" in main
    assert "/static/app-shell.css" in main
    assert "/static/native-pwa.css" in main
    assert "/static/product-redesign.css" not in main


def test_component_system_covers_core_product_surfaces() -> None:
    tokens = Path("app/static/design-tokens.css").read_text(encoding="utf-8")
    shell = Path("app/static/app-shell.css").read_text(encoding="utf-8")
    cook = Path("app/static/native-pwa.css").read_text(encoding="utf-8")
    studio = Path("app/static/live-video-studio.css").read_text(encoding="utf-8")

    assert "--radius-control:2px" in tokens
    assert "--forest:#1d5a3a" in tokens
    assert ".recipe-card" in shell
    assert ".cook-active-stage" in cook
    assert "[data-live-video-studio]" in studio
    assert "prefers-reduced-motion:reduce" in tokens


def test_home_surface_uses_the_today_entry_point() -> None:
    index = Path("app/static/index.html").read_text(encoding="utf-8")
    shell = Path("app/static/app-shell.css").read_text(encoding="utf-8")

    assert "Today in your kitchen" in index
    assert "Your kitchen, in focus." in index
    assert "Plan a meal" in index
    assert "today-prompt" in index
    assert ".today-prompt" in shell
