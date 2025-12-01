import os
import requests
from typing import Dict, Any, List, Tuple

TIMEOUT = int(os.getenv("HTTP_TIMEOUT_SECONDS", "6"))
GPU_WFS_BASE = os.getenv("GPU_WFS_BASE", "")
GPU_TYPENAME_ZONES = os.getenv("GPU_TYPENAME_ZONES", "urba:zone_urba")
CADASTRE_WFS_BASE = os.getenv("CADASTRE_WFS_BASE", "")
CADASTRE_WFS_TYPENAMES = os.getenv("CADASTRE_WFS_TYPENAMES", "cadastre:parcelle")

HEADERS = {"Accept": "application/json"}


def _req_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _to_fc(obj: Any) -> Dict[str, Any]:
    if not obj:
        return {"type": "FeatureCollection", "features": []}
    # If API returned a raw list of features
    if isinstance(obj, list):
        feats = [f for f in obj if isinstance(f, dict) and f.get("type") == "Feature"]
        return {"type": "FeatureCollection", "features": feats}
    if isinstance(obj, dict):
        if obj.get("type") == "Feature":
            return {"type": "FeatureCollection", "features": [obj]}
        if obj.get("type") == "FeatureCollection":
            return obj
        # Some APIs wrap as {features:[...]}
        if "features" in obj and isinstance(obj["features"], list):
            return {"type": "FeatureCollection", "features": obj["features"]}
    # Fallback
    return {"type": "FeatureCollection", "features": []}


def _only_polygons(fc: Dict[str, Any]) -> Dict[str, Any]:
    feats = fc.get("features", [])
    keep: List[Dict[str, Any]] = []
    for f in feats:
        geom = f.get("geometry") or {}
        if not geom:
            continue
        gtype = geom.get("type")
        if gtype in ("Polygon", "MultiPolygon"):
            keep.append(f)
    return {"type": "FeatureCollection", "features": keep}


class ParcelNotFound(Exception):
    pass


def fetch_parcel_geojson(insee: str, section: str, numero: str) -> Dict[str, Any]:
    base = "https://apicarto.ign.fr/api/cadastre/parcelle"
    params = {"code_insee": insee, "section": section, "numero": numero}
    data = _req_json(base, params)
    fc = _only_polygons(_to_fc(data))
    if not fc.get("features"):
        raise ParcelNotFound("Aucune géométrie trouvée sur l'API cadastre")
    return fc


def fallback_parcel_truegeometry(insee: str, section: str, numero: str) -> Dict[str, Any]:
    """Use GEOPF geocoding search index=parcel with returntruegeometry=true.
    INSEE = DDMMM (département 2 chiffres naïf, commune 3 chiffres)
    """
    dd = insee[:2]
    mmm = insee[2:5]
    url = "https://data.geopf.fr/geocodage/search"
    params = {
        "index": "parcel",
        "q": "",
        "departmentcode": dd,
        "municipalitycode": mmm,
        "section": section,
        "number": numero,
        "returntruegeometry": "true",
        "limit": 5,
    }
    data = _req_json(url, params)
    # Expect FeatureCollection of points with properties.truegeometry
    feats = []
    if isinstance(data, dict) and isinstance(data.get("features"), list):
        for f in data["features"]:
            props = f.get("properties") or {}
            tg = props.get("truegeometry")
            if isinstance(tg, dict) and tg.get("type") in ("Polygon", "MultiPolygon"):
                feats.append({"type": "Feature", "properties": props, "geometry": tg})
    fc = {"type": "FeatureCollection", "features": feats}
    if not fc["features"]:
        raise ParcelNotFound("Aucune truegeometry disponible")
    return fc


def fetch_plu_wfs_geojson(bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
    if not GPU_WFS_BASE:
        raise ValueError("GPU_WFS_BASE not configured")
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": GPU_TYPENAME_ZONES,
        "srsName": "EPSG:4326",
        "outputFormat": "application/json",
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
    }
    data = _req_json(GPU_WFS_BASE, params)
    return _to_fc(data)


def fetch_cadastre_wfs_geojson(bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
    if not CADASTRE_WFS_BASE:
        raise ValueError("CADASTRE_WFS_BASE not configured")
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": CADASTRE_WFS_TYPENAMES,
        "srsName": "EPSG:4326",
        "outputFormat": "application/json",
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326",
    }
    data = _req_json(CADASTRE_WFS_BASE, params)
    return _to_fc(data)


def geocode_address(q: str, limit: int = 5) -> Dict[str, Any]:
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": q, "limit": max(1, min(int(limit), 15))}
    return _req_json(url, params)
