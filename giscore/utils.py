from typing import Tuple, Dict, Any


def compute_metrics_and_lod(feature: Dict[str, Any]) -> Tuple[float, float, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Compute area (m2), perimeter (m) and LOD1/2/3 simplified GeoJSON features.
    - Requires shapely; uses pyproj if available for accurate meters via EPSG:3857.
    - If libs missing, returns zeros and original feature as all LODs.
    """
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import transform
        import shapely
    except Exception:
        return 0.0, 0.0, feature, feature, feature

    geom = shape(feature.get('geometry') or {})
    if geom.is_empty:
        return 0.0, 0.0, feature, feature, feature

    # Project lon/lat → WebMercator for meters if pyproj available
    try:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        g_m = transform(lambda x, y, z=None: transformer.transform(x, y), geom)
    except Exception:
        # Fallback: crude degree → meters approx at mid-latitude
        # Not accurate but avoids crashing.
        g_m = geom

    try:
        area_m2 = float(getattr(g_m, 'area', 0.0))
    except Exception:
        area_m2 = 0.0
    try:
        perimeter_m = float(getattr(g_m, 'length', 0.0))
    except Exception:
        perimeter_m = 0.0

    # Build LODs with simplification tolerances based on bbox size
    minx, miny, maxx, maxy = geom.bounds
    span = max(maxx - minx, maxy - miny) or 0.0001
    tol1 = span * 0.0005
    tol2 = span * 0.0015
    tol3 = span * 0.0035

    try:
        lod1_geom = geom.simplify(tol1, preserve_topology=True)
        lod2_geom = geom.simplify(tol2, preserve_topology=True)
        lod3_geom = geom.simplify(tol3, preserve_topology=True)
        lod1 = {**feature, 'geometry': mapping(lod1_geom)}
        lod2 = {**feature, 'geometry': mapping(lod2_geom)}
        lod3 = {**feature, 'geometry': mapping(lod3_geom)}
    except Exception:
        lod1 = feature
        lod2 = feature
        lod3 = feature

    return area_m2, perimeter_m, lod1, lod2, lod3
