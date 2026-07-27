import json

from app.services.theme_service import DEFAULT_THEME_NAME, ThemeService


def test_new_enterprises_start_with_midnight_fire(tmp_path) -> None:
    service = ThemeService(path=str(tmp_path / "themes.json"))

    bundle = service.list("glucoplate")

    assert bundle["activeThemeId"] == "default"
    theme = bundle["themes"][0]
    assert theme["name"] == DEFAULT_THEME_NAME
    assert theme["tokens"]["colors"]["background"] == "#101411"
    assert theme["tokens"]["colors"]["primary"] == "#ff5a36"
    assert theme["tokens"]["shape"]["controlRadius"] == 3


def test_reset_restores_midnight_fire_as_company_default(tmp_path) -> None:
    service = ThemeService(path=str(tmp_path / "themes.json"))

    restored = service.reset("glucoplate")

    assert restored["name"] == DEFAULT_THEME_NAME
    assert restored["tokens"]["colors"]["accent"] == "#c7ef57"


def test_legacy_default_name_is_normalized_to_midnight_fire(tmp_path) -> None:
    path = tmp_path / "themes.json"
    path.write_text(
        json.dumps({"glucoplate": {"themes": {"default": {"name": "Default"}}}}),
        encoding="utf-8",
    )
    service = ThemeService(path=str(path))

    assert service.get("glucoplate")["name"] == DEFAULT_THEME_NAME
