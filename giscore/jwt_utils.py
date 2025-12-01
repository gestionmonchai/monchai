import os
import jwt
from jwt import InvalidTokenError
from django.http import HttpResponseForbidden


def get_token_from_request(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return request.GET.get("token")


def require_jwt(view):
    def _wrap(request, *args, **kwargs):
        token = get_token_from_request(request)
        if not token:
            return HttpResponseForbidden("Missing token")
        try:
            algo = os.getenv("JWT_ALGO", "RS256")
            pub = os.getenv("JWT_PUBLIC_KEY", "").encode()
            payload = jwt.decode(
                token,
                pub,
                algorithms=[algo],
                options={"verify_aud": False},
            )
        except InvalidTokenError:
            return HttpResponseForbidden("Invalid token")
        request.jwt = payload
        return view(request, *args, **kwargs)

    return _wrap


def has_scope(request, needed: str) -> bool:
    payload = getattr(request, 'jwt', {}) or {}
    scopes = payload.get('scopes')
    if scopes is None:
        return False
    if isinstance(scopes, str):
        # Allow space or comma separated
        scopes = [s.strip() for s in scopes.replace(',', ' ').split() if s.strip()]
    if not isinstance(scopes, (list, tuple)):
        return False
    return needed in scopes


def require_scope(needed: str):
    def _decorator(view):
        def _wrap(request, *args, **kwargs):
            if not has_scope(request, needed):
                return HttpResponseForbidden('Missing scope: ' + needed)
            return view(request, *args, **kwargs)
        return _wrap
    return _decorator
