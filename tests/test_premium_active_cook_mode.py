from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_active_cook_mode_has_premium_stage_and_tool_slots():
    source = (ROOT / "app" / "static" / "native-cook.js").read_text(encoding="utf-8")
    assert "enhanceActiveCookMode" in source
    assert "cook-active-shell" in source
    assert "cook-active-stage" in source
    assert "cook-step-progress" in source
    assert "data.cookTimerSlot" in source
    assert "data-cook-live-slot" in source
    assert "View recipe" in source


def test_active_stage_exposes_accessible_recipe_progress():
    source = (ROOT / "app" / "static" / "native-cook.js").read_text(encoding="utf-8")
    assert "'progressbar'" in source
    assert "'aria-valuemin','1'" in source
    assert "'aria-valuemax',String(total)" in source
    assert "'aria-valuenow',String(Math.min(index+1,total))" in source


def test_active_cook_mode_is_responsive_and_touch_friendly():
    css = (ROOT / "app" / "static" / "native-pwa.css").read_text(encoding="utf-8")
    assert ".cook-step.cook-active-state" in css
    assert ".cook-active-tools" in css
    assert "grid-template-columns:1fr 1fr" in css
    assert "min-height:56px" in css
    assert "bottom:calc(72px + var(--safe-bottom))" in css
    assert "@media(prefers-reduced-motion:reduce)" in css


def test_timer_cancel_only_appears_while_running():
    source = (ROOT / "app" / "static" / "native-timers.js").read_text(encoding="utf-8")
    assert "cancelButton.hidden=!endsAt" in source
    assert 'data-cancel="true" hidden' in source
    assert "Choose a preset to start" in source
