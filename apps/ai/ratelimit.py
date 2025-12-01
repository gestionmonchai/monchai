from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


class RateLimitExceeded(Exception):
    pass


def _client_ip(request: HttpRequest) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[0]
    return request.META.get("REMOTE_ADDR", "unknown")


def check_rate_limit(request: HttpRequest) -> None:
    """Simple fixed-window rate limit based on user ID or IP address."""
    # Disable rate limiting in development or when explicitly requested
    if getattr(settings, "HELP_DISABLE_RATELIMIT", False) or getattr(settings, "DEBUG", False):
        return
    window = int(getattr(settings, "HELP_RATE_LIMIT_WINDOW", 300))
    limit = int(getattr(settings, "HELP_RATE_LIMIT_CALLS", 10))

    if getattr(request, "user", None) and request.user.is_authenticated:
        ident = f"user:{request.user.id}"
    else:
        ident = f"ip:{_client_ip(request)}"

    key = f"help:{ident}"
    # Initialize if missing, then increment
    added = cache.add(key, 0, timeout=window)
    try:
        current = cache.incr(key)
    except ValueError:
        # If backend doesn't support incr or key missing
        current = cache.get(key, 0) + 1
        cache.set(key, current, timeout=window)

    if current > limit:
        raise RateLimitExceeded(f"Rate limit exceeded for {ident}")
