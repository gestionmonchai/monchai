import json
import os
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .auth import require_jwt
from .cache import get as cache_get, set as cache_set
from .validators import (
    norm_insee,
    norm_section,
    norm_numero,
    build_parcelle_id,
    split_parcelle_id,
)
from .services import geocode_search, parcel_by_ref, parcel_truegeometry
from .models import UserParcel
from .serializers import UserParcelSerializer

TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600") or "3600")


def _ok(data, max_age=TTL):
    r = JsonResponse(data, safe=False)
    r["Cache-Control"] = f"public, max-age={max_age}"
    return r


# Optional geocode endpoint (namespaced to avoid conflicts)
@require_http_methods(["GET"])
def api_geocode(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return HttpResponseBadRequest("q required")
    key = f"cad_geocode:{q}"
    c = cache_get(key)
    if c:
        return _ok(c, 600)
    try:
        res = geocode_search(q, limit=int(request.GET.get("limit", "5")))
    except Exception:
        res = {"features": []}
    cache_set(key, res, 600)
    return _ok(res, 600)


@require_http_methods(["GET"])
def api_parcel_by_id(request):
    pid = request.GET.get("parcelleId")
    if not pid:
        return HttpResponseBadRequest("parcelleId required")
    insee, section, numero = split_parcelle_id(pid)
    # Try reference endpoint directly (no fallback here)
    try:
        fc = parcel_by_ref(insee, section, numero)
    except Exception:
        fc = {"type": "FeatureCollection", "features": []}
    return _ok(fc)


@require_http_methods(["GET"])
def api_parcel_by_ref(request):
    try:
        insee = norm_insee(request.GET.get("insee"))
        section = norm_section(request.GET.get("section"))
        numero = norm_numero(request.GET.get("numero"))
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    fb = request.GET.get("fallback") == "1"
    key = f"cad_parcel:{insee}:{section}:{numero}:fb={fb}"
    c = cache_get(key)
    if c:
        return _ok(c)
    try:
        fc = parcel_truegeometry(insee, section, numero) if fb else parcel_by_ref(insee, section, numero)
    except Exception:
        fc = {"type": "FeatureCollection", "features": []}
    cache_set(key, fc, TTL)
    return _ok(fc)


# CRUD “Mes parcelles” (JWT: tenant_id/user_id in payload)
@require_jwt
@csrf_exempt
@require_http_methods(["GET", "POST"])
def my_parcels(request):
    payload = getattr(request, "jwt", {}) or {}
    tenant = payload.get("tenant_id", "")
    user = payload.get("sub") or payload.get("user_id") or "anon"

    if request.method == "GET":
        qs = UserParcel.objects.filter(tenant_id=tenant, user_id=user).order_by("-updated_at")
        data = UserParcelSerializer(qs, many=True).data
        return _ok(data, 60)

    # POST
    body = json.loads(request.body or "{}")
    pid = body.get("parcelle_id") or body.get("parcelleId")
    label = body.get("label", "")
    pct = float(body.get("harvested_pct", 0) or 0)
    pct = max(0.0, min(100.0, pct))

    if not pid:
        insee = norm_insee(body.get("insee"))
        section = norm_section(body.get("section"))
        numero = norm_numero(body.get("numero"))
        pid = build_parcelle_id(insee, section, numero)
    else:
        insee, section, numero = split_parcelle_id(pid)

    geo = body.get("geojson")
    if not geo:
        try:
            gj = parcel_by_ref(insee, section, numero)
            geo = (gj.get("features") or [None])[0]
        except Exception:
            geo = None

    obj, _ = UserParcel.objects.get_or_create(
        tenant_id=tenant,
        user_id=user,
        parcelle_id=pid,
        defaults=dict(insee=insee, section=section, numero=numero),
    )
    obj.label = str(label)
    obj.harvested_pct = pct
    obj.geojson = geo
    obj.save()
    return _ok(UserParcelSerializer(obj).data, 0)


@require_jwt
@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def my_parcel_item(request, pk: int):
    payload = getattr(request, "jwt", {}) or {}
    tenant = payload.get("tenant_id", "")
    user = payload.get("sub") or payload.get("user_id") or "anon"

    try:
        obj = UserParcel.objects.get(pk=pk, tenant_id=tenant, user_id=user)
    except UserParcel.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({}, status=204, safe=False)

    body = json.loads(request.body or "{}")
    if "label" in body:
        obj.label = str(body["label"])
    if "harvested_pct" in body:
        try:
            pct = max(0.0, min(100.0, float(body["harvested_pct"])) )
            obj.harvested_pct = pct
        except Exception:
            pass
    if "geojson" in body:
        obj.geojson = body["geojson"]
    obj.save()
    return _ok(UserParcelSerializer(obj).data, 0)
