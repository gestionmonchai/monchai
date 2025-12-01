# Catalogue Produits

Ce module fournit un catalogue générique couvrant les vins et les produits dérivés (alimentaires, merchandising, autres). Il réutilise les entités existantes (Unités, Cuvées, Lots commerciaux) sans duplication.

## Modèles

- Product (apps/produits/models_catalog.py)
  - type_code: wine | food | merch | other
  - name, brand, slug (unique par org), tax_class, attrs (JSON), is_active
  - cuvee? (FK → viticulture.Cuvee) pour les vins
- SKU (variant vendable)
  - product (FK), name, unite (FK → referentiels.Unite), pack_of?, barcode?, internal_ref?, default_price_ht?
  - normalized_ml (property): int(round(unite.facteur_conversion * 1000)) si unite.type_unite == "volume"
- InventoryItem (stock simple non-vin)
  - sku, qty, warehouse?

## Règles vin vs non-vin

- Vin: pas de stock manuel. Le stock par variante s’agrège depuis `LotCommercial` en filtrant par `cuvee_id` et en groupant par `format_ml`. La variante (SKU) est projetée via `normalized_ml`.
- Non-vin: stock simple depuis `InventoryItem.qty` agrégé par SKU.

## Mapping Unité(ref) → format_ml

- `SKU.unite.type_unite == 'volume'` et `SKU.unite.facteur_conversion` (ex: 0.75 L) → `SKU.normalized_ml = 750`
- La table des lots commerciaux (`LotCommercial.format_ml`) est comparée à `normalized_ml` pour agréger le stock de la variante.

## Vues et URLs

- Liste: `/produits/catalogue/` (q, type)
- Nouveau: `/produits/catalogue/nouveau/`
- Détail: `/produits/catalogue/<slug>/`
- Modifier: `/produits/catalogue/<slug>/edit/`
- Modifier SKU: `/produits/skus/<id>/edit/`

Fichier vues: `apps/produits/views_catalog.py`.

## Intégrations

- Fiche vin: lien vers `/produits/lots-commerciaux/?cuvee=<id>` et vers le wizard Mise `/production/mises/nouveau/`.
- Ventes (placeholder): lors d’un ajout de ligne avec SKU vin, le picking de lot commercial (FIFO) sera proposé ultérieurement.

## Garde-fous

- Pas de stock négatif côté lecture (agrégation). Pour non-vin, l’écriture des flux de stock se fera via un service séparé (placeholder).
- Pages privées: SEO `noindex` via middleware existant.

## Tests

Fichier: `tests/produits/test_product_catalog.py`
- Création Product vin + SKU (0.75 L) → liste 200, fiche 200, SKU affiché
- Stock vin: `LotCommercial(cuvee, format_ml=750, stock_disponible=X)` → fiche affiche X pour le SKU 75cl
- Non-vin: `InventoryItem.qty` agrégé affiché en fiche

## UI/UX

- Sélecteur d’unités réutilise `referentiels.Unite`.
- Conseils concis dans le panneau Aide (pas de texte d’instruction inline).

