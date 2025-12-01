import os, json, pytest

# Only enable this legacy guard test plugin when explicitly requested
if os.getenv("ENABLE_ARCHIVE_TESTS", "") == "1":
    def pytest_addoption(parser):
        parser.addoption("--base-url", action="store", default=os.getenv("BASE_URL","http://localhost:8000"))
        parser.addoption("--auth-admin", action="store", default=os.getenv("AUTH_ADMIN",""))
        parser.addoption("--auth-editor", action="store", default=os.getenv("AUTH_EDITOR",""))
        parser.addoption("--auth-viewer", action="store", default=os.getenv("AUTH_VIEWER",""))
        parser.addoption("--write-snapshot", action="store_true", default=False)
        parser.addoption("--write-baseline", action="store_true", default=False)

    @pytest.fixture(scope="session")
    def base_url(pytestconfig):
        return pytestconfig.getoption("--base-url").rstrip("/")

    @pytest.fixture(scope="session")
    def tokens(pytestconfig):
        return {
            "admin": pytestconfig.getoption("--auth-admin"),
            "editor": pytestconfig.getoption("--auth-editor"),
            "viewer": pytestconfig.getoption("--auth-viewer"),
        }

    @pytest.fixture(scope="session")
    def auth_headers(tokens):
        def _h(role):
            tok = tokens.get(role) or ""
            h = {"Content-Type":"application/json"}
            if tok:
                h["Authorization"]=f"Bearer {tok}"
            return h
        return _h

    @pytest.fixture(scope="session")
    def sample_ids():
        p = os.path.join(os.path.dirname(__file__), "..", "config", "sample_ids.json")
        if os.path.exists(p):
            return json.load(open(p, "r", encoding="utf-8"))
        return {}

    @pytest.fixture(scope="session")
    def payloads():
        p = os.path.join(os.path.dirname(__file__), "..", "config", "payloads.json")
        if os.path.exists(p):
            return json.load(open(p, "r", encoding="utf-8"))
        return {}

    @pytest.fixture(scope="session")
    def route_overrides():
        import yaml, os
        p = os.path.join(os.path.dirname(__file__), "..", "config", "route_overrides.yaml")
        if os.path.exists(p):
            return yaml.safe_load(open(p, "r", encoding="utf-8")) or {}
        return {}
