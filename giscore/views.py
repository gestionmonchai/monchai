import json
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from .models import Parcelle
from .serializers import ParcelleSerializer
from .jwt_utils import require_jwt, has_scope
from .perms import enforce_tenant
from .utils import compute_metrics_and_lod


def featurecollection(features):
    return {"type": "FeatureCollection", "features": features}


def _bbox_filter(qs, bbox):
    """Post-filter queryset by bbox (Lite mode, no PostGIS). Intersects against feature bbox.
    bbox format: "minx,miny,maxx,maxy" in lon/lat (EPSG:4326).
    """
    try:
        minx, miny, maxx, maxy = map(float, (bbox or '').split(','))
    except Exception:
        return qs

    def _geom_bbox(gj):
        # Use GeoJSON bbox if present; else compute from coordinates (Polygon/MultiPolygon)
        b = (gj or {}).get('bbox')
        if isinstance(b, (list, tuple)) and len(b) >= 4:
            try:
                return float(b[0]), float(b[1]), float(b[2]), float(b[3])
            except Exception:
                pass
        geom = (gj or {}).get('geometry') or {}
        coords = geom.get('coordinates')
        if not coords:
            return None
        def _iter_coords(c):
            if isinstance(c, (list, tuple)):
                for x in c:
                    if isinstance(x, (int, float)):
                        yield from ()  # not a coord pair
                    if isinstance(x, (list, tuple)) and len(x) == 2 and all(isinstance(v, (int, float)) for v in x):
                        yield x
                    else:
                        yield from _iter_coords(x)
        xs, ys = [], []
        for xy in _iter_coords(coords):
            try:
                xs.append(float(xy[0])); ys.append(float(xy[1]))
            except Exception:
                continue
        if not xs or not ys:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def _intersects(b1, b2):
        a_minx, a_miny, a_maxx, a_maxy = b1
        b_minx, b_miny, b_maxx, b_maxy = b2
        if a_maxx < b_minx or a_minx > b_maxx:
            return False
        if a_maxy < b_miny or a_miny > b_maxy:
            return False
        return True

    out = []
    for p in list(qs[:2000]):
        gj = p.geojson
        fb = _geom_bbox(gj)
        if not fb:
            out.append(p)
            continue
        if _intersects((minx, miny, maxx, maxy), fb):
            out.append(p)
    return out


def embed_parcelles(request):
    """Minimal embed page that instantiates MapLibre with PMTiles and parcelles source."""
    ctx = {
        'PMTILES_URL': getattr(settings, 'PMTILES_URL', ''),
        'PARCELLES_MODE': getattr(settings, 'PARCELLES_MODE', 'LITE'),
    }
    return render(request, 'embed_parcelles.html', ctx)


@csrf_exempt
@require_jwt
def parcelles(request):
    if request.method == "GET":
        if not has_scope(request, 'read'):
            return HttpResponse(status=403)
        tenant, err = enforce_tenant(request, "tenant")
        if err:
            return err
        qs = Parcelle.objects.filter(tenant_id=tenant).order_by("-id")
        bbox = request.GET.get("bbox")
        if bbox:
            qs = _bbox_filter(qs, bbox)
        lod = request.GET.get("lod", "2")
        feats = []
        for p in qs[:500]:
            gj = (p.geojson if lod == "3" else p.lod2 if lod == "2" else p.lod1) or p.geojson
            f = {**gj, "properties": {**gj.get("properties", {}), "id": p.id, "name": p.name, "area_m2": p.area_m2}}
            feats.append(f)
        return JsonResponse(featurecollection(feats))
    if request.method == "POST":
        if not has_scope(request, 'edit'):
            return HttpResponse(status=403)
        tenant, err = enforce_tenant(request, "tenant")
        if err:
            return err
        data = json.loads(request.body or b"{}")
        name = (data.get("properties") or {}).get("name") or "Parcelle"
        area_m2, perimeter_m, lod1, lod2, lod3 = compute_metrics_and_lod(data)
        p = Parcelle.objects.create(
            tenant_id=tenant, name=name, geojson=data,
            area_m2=area_m2, perimeter_m=perimeter_m,
            lod1=lod1, lod2=lod2, lod3=lod3,
        )
        s = ParcelleSerializer(p)
        return JsonResponse(s.data, status=201)
    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
@require_jwt
def parcelles_post(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not has_scope(request, 'edit'):
        return HttpResponse(status=403)
    tenant, err = enforce_tenant(request, "tenant")
    if err:
        return err
    data = json.loads(request.body or b"{}")
    name = (data.get("properties") or {}).get("name") or "Parcelle"
    p = Parcelle.objects.create(tenant_id=tenant, name=name, geojson=data)
    s = ParcelleSerializer(p)
    return JsonResponse(s.data, status=201)


@csrf_exempt
@require_jwt
def parcelle_item(request, pk: int):
    try:
        p = Parcelle.objects.get(pk=pk)
    except Parcelle.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)
    tenant, err = enforce_tenant(request, "tenant")
    if err:
        return err
    if p.tenant_id != tenant:
        return JsonResponse({"error": "forbidden"}, status=403)

    if request.method == "PUT":
        if not has_scope(request, 'edit'):
            return HttpResponse(status=403)
        data = json.loads(request.body or b"{}")
        p.name = (data.get("properties") or {}).get("name") or p.name
        p.geojson = data
        area_m2, perimeter_m, lod1, lod2, lod3 = compute_metrics_and_lod(data)
        p.area_m2 = area_m2
        p.perimeter_m = perimeter_m
        p.lod1 = lod1
        p.lod2 = lod2
        p.lod3 = lod3
        p.save()
        return JsonResponse(ParcelleSerializer(p).data)
    if request.method == "DELETE":
        if not has_scope(request, 'edit'):
            return HttpResponse(status=403)
        p.delete()
        return HttpResponse(status=204)
    return HttpResponseNotAllowed(["PUT", "DELETE"])
