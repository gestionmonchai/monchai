# API URL Guard — Anti-403 / Anti-regression Pack (Mon Chai)

But
---
Éviter les **403/URL cassées** après des changements (RBAC, middlewares, routes refactor). Ce pack:
- lit **/openapi.json**,
- parcourt **toutes les routes** et méthodes (GET/POST/PATCH/DELETE…),
- teste **RBAC** (admin/editor/viewer) selon une **matrice** configurable,
- valide les **statuts attendus** (et alerte sur 403 non prévus),
- compare le schéma à un **snapshot OpenAPI** (diff),
- inclut des **tests ciblés** pour la création de **cuvée**,
- fournit un mode **baseline** pour enregistrer l’état actuel et détecter les deltas.

Usage rapide
------------
```bash
pip install pytest httpx pyyaml deepdiff
export BASE_URL=http://localhost:8000
export AUTH_ADMIN=token_admin
export AUTH_EDITOR=token_editor
export AUTH_VIEWER=token_viewer

# Lancer la suite
pytest -q pytest_guard -m urlguard --base-url $BASE_URL   --auth-admin $AUTH_ADMIN --auth-editor $AUTH_EDITOR --auth-viewer $AUTH_VIEWER

# Enregistrer un snapshot OpenAPI (base actuelle)
pytest -q pytest_guard/test_openapi_snapshot.py --base-url $BASE_URL --write-snapshot

# Mettre à jour la baseline de statuts observés (facultatif)
pytest -q pytest_guard/test_route_matrix.py --base-url $BASE_URL --auth-admin $AUTH_ADMIN   --auth-editor $AUTH_EDITOR --auth-viewer $AUTH_VIEWER --write-baseline
```

Personnalisation
----------------
- **config/sample_ids.json** : IDs d’échantillon pour remplir les paramètres d’URL (`{cuvee_id: "X123", lot_id: "L001", ...}`).
- **config/route_overrides.yaml** : exceptions par route/méthode/rôle (ex.: `expected_status: [403]` si interdit volontairement).
- **config/payloads.json** : corps minimaux pour POST/PATCH quand le schéma n’est pas accessible/strict.

Principes
---------
- Par défaut, **403** est considéré **anormal** (échec) sauf si sur liste d’exceptions.
- GET tolère 200/204/404/422; POST 201/200/400/422; PATCH/PUT 200/204/400/404/422; DELETE 204/200/404.
- Toute autre réponse (ou 5xx) échoue, pour attraper vite les régressions.
