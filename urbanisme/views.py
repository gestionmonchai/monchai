from __future__ import annotations

import re
from typing import Tuple

from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.http import require_GET
from django.utils.cache import patch_cache_control
from django.shortcuts import render

from . import cache as mini_cache
from . import services
from . import validators as V

# Simple rate limit: sliding window 60 req / 60s per IP+path
RATE_LIMIT = 60
RATE_TTL = 60


def _client_key(request: HttpRequest) -> str:
    ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR") or "?"
    # Normalize to first IP if behind proxy
    ip = ip.split(",")[0].strip()
    return f"throttle:{request.path}:{ip}"


def _throttle_allow(request: HttpRequest) -> bool:
    key = _client_key(request)
    val = mini_cache.get(key)
    if val is None:
        mini_cache.set(key, 1, RATE_TTL)
        return True
    try:
        count = int(val)
    except Exception:
        count = 0
    if count >= RATE_LIMIT:
        return False
    mini_cache.set(key, count + 1, RATE_TTL)
    return True


INSEE_RE = re.compile(r"^\d{5}$")
SECTION_RE = re.compile(r"^[A-Z0-9]{1,3}$")
NUM_RE = re.compile(r"^[0-9]{1,5}$")


def _bad_request(msg: str) -> JsonResponse:
    return JsonResponse({"error": msg}, status=400)


def _json_ok(payload, max_age: int = 3600) -> JsonResponse:
    resp = JsonResponse(payload, safe=False)
    patch_cache_control(resp, public=True, max_age=max_age)
    return resp


@require_GET
def parcel(request: HttpRequest) -> JsonResponse:
    if not _throttle_allow(request):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    insee_raw = (request.GET.get("insee") or "").strip()
    section_raw = (request.GET.get("section") or "").strip()
    numero_raw = (request.GET.get("numero") or "").strip()
    force_fallback = (request.GET.get("fallback") or "0") in ("1", "true", "True")

    if not (insee_raw and section_raw and numero_raw):
        return _bad_request("Paramètres requis: insee, section, numero")
    try:
        insee = V.normalize_insee(insee_raw)
        section = V.normalize_section(section_raw)
        numero = V.normalize_numero(numero_raw)
    except ValueError as e:
        return _bad_request(str(e))

    key = f"parcel:{insee}:{section}:{numero}"
    cached = mini_cache.get(key)
    if cached is not None:
        return _json_ok(cached)

    try:
        if force_fallback:
            fc = services.fallback_parcel_truegeometry(insee, section, numero)
        else:
            try:
                fc = services.fetch_parcel_geojson(insee, section, numero)
            except services.ParcelNotFound:
                fc = services.fallback_parcel_truegeometry(insee, section, numero)
    except services.requests.Timeout:
        return JsonResponse({"error": "Timeout amont"}, status=504)
    except services.requests.HTTPError as e:
        return JsonResponse({"error": f"Erreur amont: {e}"}, status=502)
    except services.ParcelNotFound as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {e}"}, status=502)

    mini_cache.set(key, fc, int((__import__("os").getenv("CACHE_TTL_SECONDS") or 3600)))
    return _json_ok(fc)


@require_GET
def plu_zones(request: HttpRequest) -> JsonResponse:
    if not _throttle_allow(request):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    bbox_s = (request.GET.get("bbox") or "").strip()
    if not bbox_s:
        return _bad_request("Paramètre requis: bbox")
    try:
        parts = [float(x) for x in bbox_s.split(",")]
        if len(parts) != 4:
            raise ValueError
        bbox: Tuple[float, float, float, float] = (parts[0], parts[1], parts[2], parts[3])
    except Exception:
        return _bad_request("bbox invalide (minx,miny,maxx,maxy)")
    # Guard: avoid too-large bbox to protect upstream
    if (bbox[2] - bbox[0] > 0.5) or (bbox[3] - bbox[1] > 0.5):
        return _bad_request("Emprise trop grande, zoomez davantage (≤ 0.5°)")

    # Canonical cache key with rounding 5 decimals
    key_bbox = ",".join(f"{v:.5f}" for v in bbox)
    key = f"plu:{key_bbox}"
    cached = mini_cache.get(key)
    if cached is not None:
        return _json_ok(cached)

    try:
        fc = services.fetch_plu_wfs_geojson(bbox)
    except services.requests.Timeout:
        return JsonResponse({"error": "Timeout amont"}, status=504)
    except services.requests.HTTPError as e:
        return JsonResponse({"error": f"Erreur amont: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {e}"}, status=502)

    mini_cache.set(key, fc, int((__import__("os").getenv("CACHE_TTL_SECONDS") or 3600)))
    return _json_ok(fc)


@require_GET
def cadastre_wfs(request: HttpRequest) -> JsonResponse:
    if not _throttle_allow(request):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    bbox_s = (request.GET.get("bbox") or "").strip()
    if not bbox_s:
        return _bad_request("Paramètre requis: bbox")
    try:
        parts = [float(x) for x in bbox_s.split(",")]
        if len(parts) != 4:
            raise ValueError
        bbox: Tuple[float, float, float, float] = (parts[0], parts[1], parts[2], parts[3])
    except Exception:
        return _bad_request("bbox invalide (minx,miny,maxx,maxy)")

    key = f"cadastre_wfs:{bbox_s}"
    cached = mini_cache.get(key)
    if cached is not None:
        return _json_ok(cached)

    try:
        fc = services.fetch_cadastre_wfs_geojson(bbox)
    except services.requests.Timeout:
        return JsonResponse({"error": "Timeout amont"}, status=504)
    except services.requests.HTTPError as e:
        return JsonResponse({"error": f"Erreur amont: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {e}"}, status=502)

    mini_cache.set(key, fc, int((__import__("os").getenv("CACHE_TTL_SECONDS") or 3600)))
    return _json_ok(fc)


@require_GET
def embed_cadastre_wms(request: HttpRequest) -> HttpResponse:
    bbox_s = (request.GET.get("bbox") or "").strip()
    # WMS URL from env
    from decouple import config

    wms_url = config("CADASTRE_WMS_URL", default="https://wxs.ign.fr/cadastre/geoportail/r/wms")
    context = {
        "bbox": bbox_s,
        "WMS_URL": wms_url,
    }
    return render(request, "embed/cadastre_wms.html", context)


@require_GET
def geocode(request: HttpRequest) -> JsonResponse:
    if not _throttle_allow(request):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    q = (request.GET.get("q") or "").strip()
    if not q or len(q) < 3:
        return _bad_request("Paramètre requis q (≥3 caractères)")
    key = f"geocode:{q.lower()}"
    cached = mini_cache.get(key)
    if cached is not None:
        return _json_ok(cached, max_age=int((__import__("os").getenv("CACHE_TTL_SECONDS") or 3600)))
    try:
        data = services.geocode_address(q, limit=int((request.GET.get("limit") or 5)))
    except services.requests.Timeout:
        return JsonResponse({"error": "Timeout amont"}, status=504)
    except services.requests.HTTPError as e:
        return JsonResponse({"error": f"Erreur amont: {e}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": f"Erreur interne: {e}"}, status=502)
    mini_cache.set(key, data, int((__import__("os").getenv("CACHE_TTL_SECONDS") or 3600)))
    return _json_ok(data)


def viewer(request: HttpRequest) -> HttpResponse:
    # Optional injection of IGN WMS settings for Leaflet front
    try:
        from decouple import config  # lazy import to avoid hard dep at import time
        ctx = {
            "IGN_WMS_PARCELLAIRE": config("IGN_WMS_PARCELLAIRE", default=""),
            "IGN_WMS_LAYERS": config("IGN_WMS_LAYERS", default="CADASTRE.PARCELLE,CADASTRE.NUMERO"),
        }
    except Exception:
        ctx = {}
    return render(request, "urbanisme/viewer.html", ctx)
