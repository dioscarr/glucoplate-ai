from pathlib import Path


INDEX_HTML = Path("app/static/index.html")


def test_product_shell_uses_the_refreshed_design_tokens() -> None:
    markup = INDEX_HTML.read_text(encoding="utf-8")

    assert "/* Product refresh: Premium utilitarian kitchen */" in markup
    assert "--brand:#245f36" in markup
    assert 'font-family:"Avenir Next","Segoe UI",Helvetica,Arial,sans-serif' in markup
    assert '<div class="logo" aria-label="GlucoPlate"></div>' in markup


def test_product_shell_navigation_uses_textual_accessible_marks() -> None:
    markup = INDEX_HTML.read_text(encoding="utf-8")

    assert markup.count('<span aria-hidden="true"></span><span>') == 5
    assert '<span>🏠</span><span>Home</span>' not in markup
    assert '<span>🌍</span><span>Cuisines</span>' not in markup
    assert ".tab>span:first-child{display:none}" in markup
    assert 'content:"Home"' not in markup
