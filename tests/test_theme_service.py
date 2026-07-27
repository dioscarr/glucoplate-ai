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
