import os
import uuid
import pytest

def pytest_addoption(parser):
    parser.addoption("--base-url", action="store", default=os.getenv("BASE_URL", "http://localhost:8000"), help="API base URL")
    parser.addoption("--org-id", action="store", default=os.getenv("ORG_ID", "orgA"), help="Organisation ID")
    parser.addoption("--auth-token", action="store", default=os.getenv("AUTH_TOKEN", "devtoken"), help="Bearer token for API")

@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return pytestconfig.getoption("--base-url").rstrip("/")

@pytest.fixture(scope="session")
def org_id(pytestconfig):
    return pytestconfig.getoption("--org-id")

@pytest.fixture(scope="session")
def auth_headers(pytestconfig):
    token = pytestconfig.getoption("--auth-token")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

@pytest.fixture
def unique_code():
    return f"PL_{uuid.uuid4().hex[:8].upper()}"
