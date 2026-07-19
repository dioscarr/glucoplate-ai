from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "app" / "static" / "premium-recipe-detail.js"


def test_premium_recipe_detail_is_injected_and_cached() -> None:
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert '"/static/premium-recipe-detail.js"' in main
    assert "'/static/premium-recipe-detail.js'" in worker
    assert "glucoplate-shell-v25" in worker


def test_recipe_normalization_preserves_legacy_strings_and_adds_stable_ids() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    assert "recipe.ingredients=details.map(detail=>detail.text)" in source
    assert "recipe.ingredient_details=details" in source
    assert "'ing_'+stableHash(recipeKey+'|'+key+'|'+occurrence)" in source
    assert "supplied.id||previous[index]&&previous[index].id" in source
    assert "item.dataset.ingredientId=detail.id" in source


def test_serving_controls_scale_from_immutable_base_quantities() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    assert "recipe.selected_servings/recipe.base_servings" in source
    assert "detail.quantity*factor" in source
    assert "Math.min(MAX_SERVINGS" in source
    assert "Math.max(MIN_SERVINGS" in source
    assert "glucoplate:servings-changed" in source
    assert "48px" in source
    assert "aria-live=\"polite\"" in source


def test_quantity_parser_supports_common_recipe_formats() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    assert "\\d+\\s+\\d+\\/\\d+" in source
    assert "\\d+\\/\\d+" in source
    assert "¼½¾⅓⅔⅛⅜⅝⅞" in source
    assert "Math.round(value*8)/8" in source
