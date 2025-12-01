import pytest
from .helpers import api_get, api_post

@pytest.mark.t07
class TestTaxes44:
    def test_fr_domestic_and_reverse_charge(self, base_url, auth_headers):
        r = api_post(base_url, "/tarifs/taxes", auth_headers, {"country_code":"FR","rate":20.0,"name":"FR VAT 20"})
        assert r.status_code in (200,201)

        r = api_get(base_url, "/tarifs/taxes/resolve", auth_headers, params={"client_id":"client_fr","date":"2025-10-10"})
        assert r.status_code == 200

        r = api_get(base_url, "/tarifs/taxes/resolve", auth_headers, params={"client_id":"client_de_pro","date":"2025-10-10"})
        assert r.status_code == 200
