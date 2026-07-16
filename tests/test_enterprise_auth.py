import json

from app.services.enterprise_auth_service import EnterpriseAuthService


def test_valid_company_access_code_returns_safe_company_data(tmp_path):
    companies_path = tmp_path / "companies.json"
    companies_path.write_text(
        json.dumps(
            {
                "companies": [
                    {
                        "id": "acme",
                        "name": "Acme Foods",
                        "access_code": "2468",
                        "role": "member",
                        "active": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    company = EnterpriseAuthService(companies_path).validate_access_code(" 2468 ")

    assert company == {"id": "acme", "name": "Acme Foods", "role": "member"}
    assert "access_code" not in company


def test_inactive_or_unknown_access_code_is_rejected(tmp_path):
    companies_path = tmp_path / "companies.json"
    companies_path.write_text(
        json.dumps(
            {
                "companies": [
                    {
                        "id": "inactive",
                        "name": "Inactive Company",
                        "access_code": "9999",
                        "active": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    service = EnterpriseAuthService(companies_path)

    assert service.validate_access_code("9999") is None
    assert service.validate_access_code("missing") is None


def test_default_admin_access_code_is_configured():
    company = EnterpriseAuthService().validate_access_code("0001")

    assert company == {"id": "glucoplate", "name": "GlucoPlate AI", "role": "admin"}
