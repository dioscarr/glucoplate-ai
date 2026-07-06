from app.services.ingredient_normalizer import _rule_normalize, normalize_ingredients


def test_rule_normalize_simple():
    res = _rule_normalize('1/4 tsp crushed red pepper flakes')
    assert res['name'].lower().startswith('crushed red pepper') or 'pepper' in res['name'].lower()
    assert 'quantity' in res


def test_normalize_list():
    lst = ['1 cup sugar', '2 tomatoes']
    out = normalize_ingredients(lst)
    assert isinstance(out, list) and len(out) == 2
    assert out[0]['name']
