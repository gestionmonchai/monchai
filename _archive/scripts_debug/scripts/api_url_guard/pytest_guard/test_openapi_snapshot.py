import json, pytest
from deepdiff import DeepDiff

pytestmark = pytest.mark.urlguard

def test_openapi_snapshot(base_url, auth_headers, request):
    import httpx, os
    snapshot_file = "openapi_snapshot.json"
    write = request.config.getoption("--write-snapshot")

    with httpx.Client(timeout=30) as c:
        r = c.get(f"{base_url}/openapi.json", headers=auth_headers("admin"))
        assert r.status_code == 200, "/openapi.json non accessible"
        spec = r.json()

    if write:
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        pytest.skip(f"Snapshot écrit: {snapshot_file}")

    if not os.path.exists(snapshot_file):
        pytest.skip("Pas de snapshot encore enregistré — exécutez avec --write-snapshot")

    old = json.load(open(snapshot_file, "r", encoding="utf-8"))
    diff = DeepDiff(old, spec, ignore_order=True, exclude_paths={"root['servers']"})
    assert diff == {}, f"Changements OpenAPI détectés : {diff}"
