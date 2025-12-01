import os
import requests
from typing import Any, Dict

TIMEOUT = int(os.getenv("HTTP_TIMEOUT_SECONDS", "6") or "6")
HEADERS = {"Accept": "application/json"}


def _get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def geocode_search(q: str, limit: int = 5) -> Dict[str, Any]:
    return _get_json(
        "https://data.geopf.fr/geocodage/search",
        {"q": q, "limit": max(1, min(int(limit), 15))},
    )


def parcel_by_ref(insee: str, section: str, numero: str) -> Dict[str, Any]:
    return _get_json(
        "https://apicarto.ign.fr/api/cadastre/parcelle",
        {"code_insee": insee, "section": section, "numero": numero},
    )


def parcel_truegeometry(insee: str, section: str, numero: str) -> Dict[str, Any]:
    dep, mun = insee[:2], insee[2:]
    gj = _get_json(
        "https://data.geopf.fr/geocodage/search",
        {
            "index": "parcel",
            "returntruegeometry": "true",
            "limit": 1,
            "departmentcode": dep,
            "municipalitycode": mun,
            "section": section,
            "number": numero,
        },
    )
    feats = gj.get("features") or []
    if not feats:
        return {"type": "FeatureCollection", "features": []}
    f = feats[0]
    props = f.get("properties") or {}
    tg = props.pop("truegeometry", None)
    if tg:
        f["geometry"] = tg
    return {"type": "FeatureCollection", "features": [f]}
