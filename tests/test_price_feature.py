from __future__ import annotations

import io
import json
import urllib.request

from app.schemas.store import ProductSearchRequest
from app.services.product_lookup_service import ProductLookupService


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_product_lookup_enriches_open_food_facts_match_with_lowest_open_price(monkeypatch):
    responses = [
        {"products": [{"code": "0123456789012", "product_name": "Grade A Parmesan", "brands": "Test"}]},
        {"items": [{"price": "8.99", "currency": "USD"}, {"price": "6.49", "currency": "USD"}]},
    ]

    def fake_urlopen(_request, timeout):
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = ProductLookupService().search_products(ProductSearchRequest(ingredient="parmesan"))

    assert result[0].price == 6.49
    assert result[0].currency == "USD"
    assert result[0].source == "openfoodfacts-open-prices"
    assert result[0].availability == "available"


def test_product_lookup_keeps_safe_unknown_when_open_prices_is_unavailable(monkeypatch):
    responses = [{"products": [{"code": "0123456789012", "product_name": "Garlic Powder"}]}]

    def fake_urlopen(_request, timeout):
        response = FakeResponse(responses.pop(0))
        if len(responses) == 0:
            raise urllib.error.URLError("offline")
        return response

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = ProductLookupService().search_products(ProductSearchRequest(ingredient="garlic powder"))

    assert result[0].price is None
    assert result[0].source == "openfoodfacts"
    assert result[0].availability == "unknown"


def test_price_endpoint_contract_remains_exposed():
    from app.main import app

    paths = {route.path for route in app.routes}
    assert "/api/products/search" in paths
