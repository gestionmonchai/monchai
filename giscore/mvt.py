from django.http import HttpResponse
from django.db import connection
from .jwt_utils import require_jwt
from .perms import enforce_tenant


@require_jwt
def tiles_mvt(request, z: int, x: int, y: int):
    tenant, err = enforce_tenant(request, "tenant")
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            """
        WITH q AS (
          SELECT id, name, area_m2,
                 ST_AsMVTGeom(geom, ST_TileEnvelope(%s,%s,%s), 4096, 64, true) AS mvtgeom
          FROM giscore_parcelle
          WHERE tenant_id=%s
            AND geom && ST_TileEnvelope(%s,%s,%s)
        )
        SELECT ST_AsMVT(q,'parcelles',4096,'mvtgeom');
        """,
            [z, x, y, tenant, z, x, y],
        )
        row = cur.fetchone()
        tile = row[0] if row and row[0] else bytes()
    return HttpResponse(tile, content_type="application/vnd.mapbox-vector-tile")
