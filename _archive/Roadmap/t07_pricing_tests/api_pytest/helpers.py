import json
from typing import Any, Dict
import httpx

def api_post(base_url: str, path: str, headers: Dict[str, str], payload: Dict[str, Any]):
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{base_url}{path}", headers=headers, json=payload)
    return r

def api_get(base_url: str, path: str, headers: Dict[str, str], params: Dict[str, Any] = None):
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{base_url}{path}", headers=headers, params=params or {})
    return r
