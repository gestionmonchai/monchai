import pytest
from .helpers import request_json

pytestmark = pytest.mark.urlguard

def test_cuvees_create_roles(base_url, auth_headers):
    payload = {"name":"Cuvée Automatique","code":"AUTO","color":"rouge"}
    r = request_json(base_url, "POST", "/cuvees", headers=auth_headers("admin"), payload=payload)
    assert r.status_code in (200,201,202,422,400), f"Admin ne devrait pas rencontrer 403 ici, statut={r.status_code}"

    r = request_json(base_url, "POST", "/cuvees", headers=auth_headers("editor"), payload=payload)
    assert r.status_code in (200,201,202,422,400,403), "Editor peut être autorisé selon RBAC — 403 acceptable si défini dans overrides"

    r = request_json(base_url, "POST", "/cuvees", headers=auth_headers("viewer"), payload=payload)
    assert r.status_code in (401,403), "Viewer ne devrait pas pouvoir créer de cuvée"
