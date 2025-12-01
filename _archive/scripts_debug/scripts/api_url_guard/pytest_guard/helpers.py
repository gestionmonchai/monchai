import re, httpx
from typing import Dict, Any, Tuple

PARAM_RE = re.compile(r"{(.*?)}")

DEFAULT_OK = {
  "GET":   {200,204,206,304,404,422},
  "POST":  {200,201,202,400,409,422},
  "PUT":   {200,204,400,404,409,422},
  "PATCH": {200,204,400,404,409,422},
  "DELETE":{200,204,404}
}

def fill_path_params(path: str, sample_ids: Dict[str,str]) -> Tuple[str, Dict[str,str]]:
    used = {}
    def repl(m):
        k = m.group(1)
        v = sample_ids.get(k) or sample_ids.get(k+"_id") or f"SAMPLE_{k.upper()}"
        used[k]=v
        return str(v)
    real = PARAM_RE.sub(lambda m: repl(m), path)
    return real, used

def method_payload(method: str, path: str, payloads: Dict[str,Any]) -> Any:
    if method in ("POST","PUT","PATCH"):
        if path in payloads:
            return payloads[path]
        for key in list(payloads.keys()):
            if key.endswith("*") and path.startswith(key[:-1]):
                return payloads[key]
        return {"name":"Smoke","code":"AUTO","_note":"fallback"}
    return None

def request_json(base_url, method, path, headers, payload=None, params=None):
    with httpx.Client(timeout=30) as c:
        url = f"{base_url}{path}"
        if method == "GET":
            return c.get(url, headers=headers, params=params or {})
        if method == "POST":
            return c.post(url, headers=headers, json=payload or {})
        if method == "PUT":
            return c.put(url, headers=headers, json=payload or {})
        if method == "PATCH":
            return c.patch(url, headers=headers, json=payload or {})
        if method == "DELETE":
            return c.delete(url, headers=headers)
        return None
