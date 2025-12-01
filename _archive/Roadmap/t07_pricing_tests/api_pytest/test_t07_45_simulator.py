import pytest
from .helpers import api_post

@pytest.mark.t07
class TestSimulator45:
    def test_happy_path(self, base_url, auth_headers):
        payload = {
            "client_id": "client_fr_pro",
            "cuvee_id": "X",
            "uom_id": "bottle_75",
            "quantity": 12,
            "date": "2025-10-10",
            "currency": "EUR",
            "explain": True
        }
        r = api_post(base_url, "/tarifs/simulateur", auth_headers, payload)
        assert r.status_code == 200
        data = r.json()
        for k in ("base_price","list_source","discounts","subtotal_ht","tax_rate","total_ttc","audit"):
            assert k in data

    def test_errors(self, base_url, auth_headers):
        payload = {
            "client_id": "client_fr_pro",
            "cuvee_id": "X",
            "uom_id": "unknown_uom",
            "quantity": 6,
            "date": "2025-10-10",
            "currency": "EUR"
        }
        r = api_post(base_url, "/tarifs/simulateur", auth_headers, payload)
        assert r.status_code in (400, 422)
