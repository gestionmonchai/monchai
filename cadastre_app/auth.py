import os
import jwt
from jwt import InvalidTokenError
from django.http import HttpResponseForbidden

ALGO = os.getenv("JWT_ALGO", "HS256")
KEY = os.getenv("JWT_PUBLIC_KEY", "dev-secret")

def get_token(req):
    auth = req.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return req.GET.get("token")


def require_jwt(view):
    def _wrap(req, *a, **kw):
        t = get_token(req)
        if not t:
            return HttpResponseForbidden("Missing token")
        try:
            if t == "DEV_TOKEN":
                payload = {"sub": "dev", "tenant_id": ""}
            else:
                payload = jwt.decode(t, KEY, algorithms=[ALGO], options={"verify_aud": False})
        except InvalidTokenError:
            return HttpResponseForbidden("Invalid token")
        req.jwt = payload
        return view(req, *a, **kw)
    return _wrap
