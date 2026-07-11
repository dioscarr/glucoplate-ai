from fastapi.testclient import TestClient

from app.main import app
from app.services.receipt_parser_service import ReceiptParserService

client = TestClient(app)


def test_parser_extracts_common_receipt_fields():
    receipt = ReceiptParserService().extract(
        """Target
07/11/2026
Subtotal 18.50
Tax 1.48
Total $19.98
"""
    )

    assert receipt.merchant == "Target"
    assert receipt.purchase_date.isoformat() == "2026-07-11"
    assert receipt.subtotal == 18.50
    assert receipt.tax == 1.48
    assert receipt.total == 19.98
    assert receipt.confidence["total"] >= 0.9


def test_extract_endpoint_returns_reviewable_receipt():
    response = client.post(
        "/api/receipts/extract",
        json={"text": "Home Depot\n2026-07-10\nAmount Due $84.32"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["merchant"] == "Home Depot"
    assert data["total"] == 84.32
    assert data["purchase_date"] == "2026-07-10"


def test_receipt_validation_rejects_negative_total():
    response = client.post(
        "/api/receipts/save",
        json={"merchant": "Test Store", "total": -1, "category": "other"},
    )

    assert response.status_code == 422
