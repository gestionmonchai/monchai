import pytest, json
from deepdiff import DeepDiff
from .helpers import fill_path_params, method_payload, request_json, DEFAULT_OK

pytestmark = pytest.mark.urlguard

SKIP_METHODS = {"HEAD","OPTIONS"}
SKIP_PATH_PATTERNS = ["/health", "/metrics"]

def load_openapi(base_url, headers):
    import httpx
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{base_url}/openapi.json", headers=headers)
    assert r.status_code == 200, "openapi.json non accessible"
    return r.json()

def iter_paths(spec):
    for path, desc in spec.get("paths", {}).items():
        yield path, {k.upper(): v for k,v in desc.items()}

def should_skip(path):
    return any(pat in path for pat in SKIP_PATH_PATTERNS)

def expected_status_set(method):
    return DEFAULT_OK.get(method, {200,201,204,400,404,422})

def role_headers(auth_headers, role):
    return auth_headers(role)

def key_for(path, method, role):
    return f"{method} {path} as {role}"

def apply_overrides(overrides, path, method, role):
    if not overrides: return None
    for row in overrides.get("overrides", []):
        if row.get("method","").upper()==method and row.get("path")==path and row.get("role")==role:
            return set(row.get("expected_status", []))
    return None

def save_baseline(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_baseline(filename):
    try:
        return json.load(open(filename, "r", encoding="utf-8"))
    except Exception:
        return None

def test_route_matrix(base_url, auth_headers, sample_ids, payloads, route_overrides, request):
    spec = load_openapi(base_url, auth_headers("admin"))
    roles = ("admin","editor","viewer")
    baseline_file = "route_matrix_baseline.json"
    write_baseline = request.config.getoption("--write-baseline")
    results = {}

    for path, methods in iter_paths(spec):
        if should_skip(path): 
            continue
        for method in methods.keys():
            m = method.upper()
            if m in SKIP_METHODS: 
                continue

            filled_path, used = fill_path_params(path, sample_ids)
            payload = method_payload(m, path, payloads)

            for role in roles:
                hdrs = role_headers(auth_headers, role)
                r = request_json(base_url, m, filled_path, hdrs, payload=payload)
                results[key_for(path, m, role)] = {"status": r.status_code}

                expected = apply_overrides(route_overrides, path, m, role)
                ok_set = expected if expected is not None else expected_status_set(m)

                assert r.status_code in ok_set, f"Unexpected status {r.status_code} for {m} {path} as {role} (expected in {sorted(ok_set)})"

    if write_baseline:
        save_baseline(results, baseline_file)
        pytest.skip(f"Baseline enregistrée dans {baseline_file}")

    baseline = load_baseline(baseline_file)
    if baseline:
        diff = DeepDiff(baseline, results, ignore_order=True)
        assert diff == {}, f"Delta vs baseline détecté : {diff}"
