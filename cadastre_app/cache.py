import time

_store = {}

def get(key):
    v = _store.get(key)
    if not v:
        return None
    exp, val = v
    if exp < time.time():
        _store.pop(key, None)
        return None
    return val


def set(key, val, ttl=3600):
    _store[key] = (time.time() + int(ttl or 0), val)
