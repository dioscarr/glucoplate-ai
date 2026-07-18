from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_empty_cook_mode_has_dedicated_premium_hierarchy():
    source = (ROOT / "app" / "static" / "native-cook.js").read_text(encoding="utf-8")
    assert "enhanceEmptyCookMode" in source
    assert "cook-empty-state" in source
    assert "Your kitchen is ready" in source
    assert "Browse recipes" in source
    assert "Open cookbook" in source
    assert "data-cook-live-slot" in source


def test_irrelevant_tools_are_hidden_without_a_recipe():
    timers = (ROOT / "app" / "static" / "native-timers.js").read_text(encoding="utf-8")
    live = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "if(!window.currentRecipe){existing?.remove();return}" in timers
    assert "hasRecipe=Boolean(currentRecipe())" in live
    assert "Browse live rooms" in live
    empty_branch = live.split(":")[1]
    assert "Start live room" not in empty_branch


def test_empty_cook_mode_uses_stable_feature_slots():
    timers = (ROOT / "app" / "static" / "native-timers.js").read_text(encoding="utf-8")
    live = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "data-cook-timer-slot" in timers
    assert "data-cook-live-slot" in live


def test_premium_cook_mode_is_responsive_and_touch_friendly():
    css = (ROOT / "app" / "static" / "native-pwa.css").read_text(encoding="utf-8")
    assert ".cook-step.cook-empty-state" in css
    assert ".cook-empty-shell" in css
    assert "grid-template-columns:minmax(0,1.45fr)" in css
    assert "@media(max-width:760px)" in css
    assert "min-height:52px" in css
