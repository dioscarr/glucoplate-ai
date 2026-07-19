from pathlib import Path

from app.services.live_cook_insight_service import LiveCookInsightService


ROOT = Path(__file__).resolve().parents[1]


def test_live_kitchen_workspace_is_loaded():
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert '"/static/live-kitchen-workspace.js"' in main


def test_live_kitchen_supports_full_page_and_compact_modes():
    source = (ROOT / "app" / "static" / "live-kitchen-workspace.js").read_text(encoding="utf-8")
    css = (ROOT / "app" / "static" / "live-cook-room-premium.css").read_text(encoding="utf-8")
    assert "data-live-expand" in source
    assert "setMode('workspace')" in source
    assert "setMode('compact')" in source
    assert "event.key==='Escape'" in source
    assert "history.pushState" in source
    assert "title.focus()" in source
    assert ".live-room-panel.is-full-page" in css
    assert "height:100dvh" in css
    assert "prefers-reduced-motion:reduce" in css


def test_live_kitchen_insights_require_review_before_shopping_write():
    source = (ROOT / "app" / "static" / "live-kitchen-workspace.js").read_text(encoding="utf-8")
    assert "Review before adding" in source
    assert "Nothing is added automatically" in source
    assert "data-add-suggestions" in source
    assert "GlucoPlateShoppingList?.addItems" in source
    assert "/insights" in source


def test_local_insight_extracts_explicit_purchase_intent_and_respects_negation():
    service = LiveCookInsightService()
    room = {
        "id": "room-1",
        "title": "Taco night",
        "chat": [
            {"id": "1", "display_name": "Maya", "message": "We need limes for tomorrow."},
            {"id": "2", "display_name": "Lee", "message": "Don't buy milk, we already have it."},
        ],
    }

    result = service.generate(room, provider="local")

    assert result["provider"] == "local"
    assert [item["name"] for item in result["suggested_items"]] == ["limes"]
    assert result["suggested_items"][0]["source_message_ids"] == ["1"]
    assert result["transcript_revision"]


def test_local_insight_deduplicates_repeated_mentions():
    service = LiveCookInsightService()
    room = {
        "id": "room-2",
        "chat": [
            {"id": "1", "display_name": "Maya", "message": "Buy cilantro."},
            {"id": "2", "display_name": "Lee", "message": "We need cilantro."},
        ],
    }

    result = service.generate(room, provider="local")

    assert len(result["suggested_items"]) == 1
