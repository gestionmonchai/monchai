# Urbanisme: Cadastre & PLU (WFS/WMS) Proxy

Cette fonctionnalité ajoute des endpoints Django pour interroger le cadastre (API Carto IGN) et le PLU (WFS GPU) avec cache et timeouts, ainsi qu'une UI MapLibre sur la page `Référentiels → Parcelles → Nouvelle`.

## Endpoints

- `GET /api/cadastre/parcel?insee=XXXX&section=AA&numero=0123`
  - Proxy API Carto IGN Cadastre → GeoJSON (EPSG:4326)
  - 400 si paramètres invalides, 502/504 si erreur amont/timeout
- `GET /api/plu/zones?insee=XXXX&bbox=minx,miny,maxx,maxy`
  - Proxy WFS GPU `typeNames=urba:zone_urba` → GeoJSON (EPSG:4326)
  - 400 si paramètres invalides, 502/504 si erreur amont/timeout
- `GET /api/cadastre/wfs?bbox=minx,miny,maxx,maxy` (optionnel)
  - Proxy WFS cadastre.data.gouv.fr → GeoJSON
- `GET /embed/cadastre-wms?bbox=minx,miny,maxx,maxy`
  - Iframe Leaflet pour overlay WMS numéros cadastraux

Toutes les réponses succès sont servies avec `Cache-Control: public, max-age=3600` (par défaut, configurable).

## Variables d’environnement (.env)

```
GPU_WFS_BASE=https://wxs-telechargement.geoportail.gouv.fr/<CLE>/wfs
GPU_TYPENAME_ZONES=urba:zone_urba
CADASTRE_WFS_BASE=https://cadastre.data.gouv.fr/wfs
CADASTRE_WFS_TYPENAMES=cadastre:parcelle
CADASTRE_WMS_URL=https://wxs.ign.fr/cadastre/geoportail/r/wms
HTTP_TIMEOUT_SECONDS=5
CACHE_TTL_SECONDS=3600
```

- `GPU_WFS_BASE`: URL WFS du GPU (clé nécessaire). Voir portail Géoportail.
- `GPU_TYPENAME_ZONES`: le type standard CNIG (par défaut `urba:zone_urba`).
- `HTTP_TIMEOUT_SECONDS`: timeout réseau côté serveur (par défaut 5s).
- `CACHE_TTL_SECONDS`: TTL du cache mémoire local (par défaut 1h).

## UI MapLibre (Parcelle → Nouvelle)

- Formulaire “Parcelle cadastrale” (INSEE, Section, Numéro) + bouton Rechercher.
- Toggles:
  - Afficher PLU (zones) → WFS GPU (rafraîchi au `moveend` avec debounce 300ms)
  - Afficher numéros cadastraux (WMS) → iframe Leaflet qui suit le bbox courant
- Quand une parcelle est trouvée: la géométrie est ajoutée et la carte est zoomée sur l’emprise.

## Bonnes pratiques

- Rester sur un bbox raisonnable (≤ 0.2° × 0.2°) pour limiter la charge WFS.
- Debounce 300ms sur `moveend` (déjà implémenté).
- Configurer la clé GPU WFS en production; en dev, tests possibles sur communes disposant d’un PLU publié.

## Tests rapides

- `/api/cadastre/parcel?insee=35238&section=AB&numero=0123` → 200 + GeoJSON
- `/api/plu/zones?insee=35238&bbox=-1.75,48.05,-1.60,48.15` → 200 + FeatureCollection
- Sur la page “Nouvelle parcelle”: recherche cadastrale → zoom + contour; toggle PLU/WMS fonctionnels.
