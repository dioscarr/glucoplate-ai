from pathlib import Path


def test_all_html_pages_load_the_product_redesign_layer() -> None:
    main = Path("app/main.py").read_text(encoding="utf-8")

    assert "/static/native-pwa.css" in main
    assert "/static/product-redesign.css" in main


def test_product_redesign_covers_dynamic_ui_surfaces() -> None:
    stylesheet = Path("app/static/product-redesign.css").read_text(encoding="utf-8")

    for selector in (
        ".recipe-card",
        ".cook-step.cook-active-state",
        ".pantry-launcher",
        ".shopping-launcher",
        ".live-room-panel",
        "[data-live-video-studio]",
    ):
        assert selector in stylesheet

    assert "prefers-reduced-motion:reduce" in stylesheet
    assert "outline:3px solid" in stylesheet
