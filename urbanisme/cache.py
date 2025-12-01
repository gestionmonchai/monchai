import time
from typing import Any, Tuple, Optional

# Very small in-process cache for simple GET proxying
# Keys are strings; values are (expires_ts, payload)
_store: dict[str, Tuple[float, Any]] = {}


def get(key: str) -> Optional[Any]:
    now = time.time()
    item = _store.get(key)
    if not item:
        return None
    expires, value = item
    if expires < now:
        # expire lazily
        try:
            del _store[key]
        except Exception:
            pass
        return None
    return value


def set(key: str, value: Any, ttl_s: int) -> None:
    expires = time.time() + max(1, int(ttl_s))
    _store[key] = (expires, value)
