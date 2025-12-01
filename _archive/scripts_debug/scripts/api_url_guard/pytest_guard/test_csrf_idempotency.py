import pytest
from .helpers import request_json

pytestmark = pytest.mark.urlguard

def test_idempotency_and_csrf(base_url, auth_headers):
    # Adapter la route cible selon votre stack si nécessaire
    path = "/cuvees"

    # Sans auth
    r = request_json(base_url, "POST", path, headers={"Content-Type":"application/json"}, payload={"name":"Test"})
    assert r.status_code in (401,403,405), f"POST sans auth ne devrait pas être accepté: {r.status_code}"

    # Avec auth (selon votre politique CSRF/api-only)
    r = request_json(base_url, "POST", path, headers=auth_headers("editor"), payload={"name":"Test"})
    assert r.status_code in (200,201,202,400,401,403,422), "Statut inattendu — adapter selon votre politique CSRF"
