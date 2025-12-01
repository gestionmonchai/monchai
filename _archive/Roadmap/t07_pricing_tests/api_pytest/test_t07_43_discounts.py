import pytest
from .helpers import api_get, api_post

@pytest.mark.t07
class TestDiscounts43:
    def test_stack_exclusive_stop(self, base_url, auth_headers):
        rules = [
            {"scope":"global","percent":2.0,"min_qty":1,"priority":200,"stack_mode":"stack","is_active":True},
            {"scope":"segment","target_id":"business","percent":3.0,"min_qty":1,"priority":150,"stack_mode":"stack","is_active":True},
            {"scope":"client","target_id":"dupont_client_id","percent":12.0,"min_qty":1,"priority":10,"stack_mode":"exclusive","is_active":True}
        ]
        for rule in rules:
            r = api_post(base_url, "/tarifs/remises", auth_headers, rule)
            assert r.status_code in (200,201)

        r = api_get(base_url, "/tarifs/remises", auth_headers, params={"active":"1"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
