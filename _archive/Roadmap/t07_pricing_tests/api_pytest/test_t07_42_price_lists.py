import pytest, time
from .helpers import api_get, api_post

@pytest.mark.t07
class TestPriceLists42:
    def test_crud_and_activation(self, base_url, auth_headers, unique_code):
        payload = {"code": unique_code, "name": "PL Pro FR", "segment": "business", "country_code": "FR", "currency": "EUR"}
        r = api_post(base_url, "/tarifs/listes", auth_headers, payload)
        assert r.status_code in (200, 201)
        pl = r.json()
        pl_id = pl.get("id")

        r = api_post(base_url, f"/tarifs/listes/{pl_id}/versions", auth_headers, {"effective_from": "2025-10-01", "status": "draft"})
        assert r.status_code in (200, 201)
        v1 = r.json()
        v1_no = v1.get("version_no")

        r = api_post(base_url, f"/tarifs/listes/{pl_id}/versions/{v1_no}/activate", auth_headers, {"effective_from": "2025-10-01"})
        assert r.status_code == 200

    def test_items_bulk_and_resolution(self, base_url, auth_headers, unique_code):
        r = api_post(base_url, "/tarifs/listes", auth_headers, {"code": unique_code, "name": "PL Pro FR", "segment": "business", "country_code": "FR", "currency": "EUR"})
        pl_id = r.json()["id"]
        r = api_post(base_url, f"/tarifs/listes/{pl_id}/versions", auth_headers, {"effective_from": "2025-10-01"})
        v_no = r.json()["version_no"]

        items = [
            {"cuvee_id":"X","uom_id":"bottle_75","min_qty":1,"base_price":10.00,"volume_eq_l":0.75},
            {"cuvee_id":"X","uom_id":"bottle_75","min_qty":6,"base_price":9.50,"volume_eq_l":0.75},
            {"cuvee_id":"X","uom_id":"bottle_75","min_qty":12,"base_price":9.00,"volume_eq_l":0.75},
        ]
        r = api_post(base_url, f"/tarifs/listes/{pl_id}/versions/{v_no}/items/bulk", auth_headers, {"items": items})
        assert r.status_code in (200,201)

        r = api_post(base_url, f"/tarifs/listes/{pl_id}/versions/{v_no}/activate", auth_headers, {"effective_from": "2025-10-01"})
        assert r.status_code == 200

        r = api_get(base_url, "/tarifs/listes/resolve", auth_headers, params={"segment":"business","country":"FR","date":"2025-10-10"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("version_no") == v_no
