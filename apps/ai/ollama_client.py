from typing import Optional, Dict, Any
import json
import time
from django.conf import settings


class OllamaError(Exception):
    """Raised when Ollama returns an error or is unreachable."""


def ollama_generate(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    timeout: int = 60,
    template: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Call local Ollama /api/generate and return the generated text (response field).

    - prompt: user prompt
    - model: model name (defaults to settings.OLLAMA_MODEL)
    - system: optional system prompt; if provided, will be prefixed in the prompt
    - timeout: request timeout in seconds
    """
    model = model or settings.OLLAMA_MODEL
    # Do not embed any control tokens in the prompt; rely on Ollama 'system' field
    final_prompt = prompt

    # Accept either a full endpoint or a base host. If base, append /api/generate
    url_base = getattr(settings, 'OLLAMA_URL', '').rstrip()
    if not url_base:
        raise OllamaError("OLLAMA_URL non configurée")
    if url_base.endswith('/api/generate') or url_base.endswith('/api/chat'):
        url = url_base
    else:
        if url_base.endswith('/api'):
            url = url_base + '/generate'
        elif url_base.endswith('/'):
            url = url_base + 'api/generate'
        else:
            url = url_base + '/api/generate'
    payload: Dict[str, Any] = {"model": model, "prompt": final_prompt, "stream": False}
    # Keep model in memory to avoid cold start slowness
    keep_alive = getattr(settings, 'OLLAMA_KEEP_ALIVE', None)
    if keep_alive:
        payload["keep_alive"] = keep_alive
    if template:
        payload["template"] = template
    if system:
        payload["system"] = system
    if options:
        payload["options"] = options

    # Lazy session with connection pooling to reduce latency (keep-alive)
    session = _get_http_session()

    # Timeouts optimisés
    connect_timeout = getattr(settings, 'OLLAMA_CONNECT_TIMEOUT', 2)  # Réduit de 3s à 2s
    read_timeout = timeout or getattr(settings, 'HELP_TIMEOUT', 12)
    req_timeout = (connect_timeout, read_timeout)

    # Retries réduits pour plus de réactivité
    max_attempts = max(1, int(getattr(settings, 'HELP_OLLAMA_RETRIES', 2)))  # Réduit de 3 à 2
    backoff_base = 0.2  # Réduit de 0.3s à 0.2s
    last_err: Optional[Exception] = None
    tried_fallback = False

    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.post(url, json=payload, timeout=req_timeout)
        except Exception as e:
            last_err = e
            if attempt < max_attempts:
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            raise OllamaError(f"Ollama unreachable after {attempt} attempts: {e}")

        # Non-200 handling
        if resp.status_code != 200:
            # Inspect error content
            detail = None
            try:
                data = resp.json()
                detail = data.get("error") or data
            except Exception:
                detail = resp.text

            # Fallback to default model if current model missing
            if resp.status_code == 404 or (isinstance(detail, str) and 'model' in detail.lower() and 'not found' in detail.lower()):
                fallback_model = getattr(settings, 'OLLAMA_MODEL', None)
                if fallback_model and payload.get('model') != fallback_model and not tried_fallback:
                    payload['model'] = fallback_model
                    tried_fallback = True
                    # Retry immediately with fallback
                    continue

            if attempt < max_attempts:
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            raise OllamaError(f"Ollama error {resp.status_code}: {detail}")

        # Parse JSON
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            last_err = e
            if attempt < max_attempts:
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            raise OllamaError("Invalid JSON response from Ollama")

        # Error key in JSON
        if isinstance(data, dict) and data.get('error'):
            detail = data.get('error')
            if attempt < max_attempts:
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            raise OllamaError(f"Ollama error: {detail}")

        answer = data.get("response")
        if not isinstance(answer, str):
            if attempt < max_attempts:
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            raise OllamaError("Missing 'response' in Ollama reply")

        return answer.strip()


# --- Internal: pooled HTTP session ------------------------------------------------
_SESSION = None  # type: ignore[var-annotated]


def _get_http_session():
    """Create or reuse a global requests.Session with HTTP connection pooling."""
    global _SESSION
    try:
        import requests  # type: ignore
        from requests.adapters import HTTPAdapter  # type: ignore
    except Exception:
        # Keep the same error surface exposed previously
        raise OllamaError("Le client HTTP 'requests' n'est pas installé")

    if _SESSION is None:
        _SESSION = requests.Session()
        pool_size = int(getattr(settings, 'HELP_HTTP_POOL_SIZE', 20))  # Augmenté de 10 à 20
        adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size, max_retries=0)
        _SESSION.mount('http://', adapter)
        _SESSION.mount('https://', adapter)
        # Explicit keep-alive header for some proxies
        _SESSION.headers.update({'Connection': 'keep-alive'})
    return _SESSION
