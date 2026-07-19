from pathlib import Path

from app.services.receipt_parser_service import ReceiptParserService


def test_parser_extracts_reviewable_line_items():
    receipt = ReceiptParserService().extract("Wegmans\n07/18/2026\nMilk 3.49\n2 x Apples 4.00\nSubtotal 7.49\nTax 0.00\nTotal 7.49")
    assert receipt.merchant == "Wegmans"
    assert receipt.total == 7.49
    assert len(receipt.line_items) == 2
    assert receipt.line_items[0].description == "Milk"
    assert receipt.line_items[1].quantity == 2
    assert receipt.confidence["line_items"] >= 0.7


def test_receipt_import_contracts_are_registered():
    route_source = Path("app/api/receipt_import_routes.py").read_text()
    main_source = Path("app/main.py").read_text()
    service_source = Path("app/services/receipt_import_service.py").read_text()
    ui_source = Path("app/static/receipt-import-ui.js").read_text()

    assert '@router.post("/extract")' in route_source
    assert '@router.post("/import")' in route_source
    assert "app.include_router(receipt_import_router)" in main_source
    assert '"source": "receipt-extracted"' in service_source
    assert '"receipt_id": receipt_id' in service_source
    assert '"fingerprint": fingerprint' in service_source
    assert "add_to_pantry" in service_source
    assert "complete_shopping_items" in service_source
    assert "/api/receipt-imports/extract" in ui_source
    assert "/api/receipt-imports/import" in ui_source


def test_pwa_caches_receipt_import_client():
    sw = Path("app/static/sw.js").read_text()
    assert "const CACHE='glucoplate-shell-v" in sw
    assert "/static/receipt-import-ui.js" in sw
