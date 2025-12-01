# Navigation — Catalogue produits

Nouvelles routes activées dans `apps/produits/urls.py` pour le catalogue produits générique.

- /produits/catalogue/ → Liste produits (q, type)
  - Breadcrumb: Produits › Catalogue
- /produits/catalogue/nouveau/ → Création produit
  - Breadcrumb: Produits › Catalogue › Nouveau
- /produits/catalogue/<slug>/ → Fiche produit
  - Breadcrumb: Produits › Catalogue › <Produit>
- /produits/catalogue/<slug>/edit/ → Édition produit
  - Breadcrumb: Produits › Catalogue › <Produit> › Modifier
- /produits/skus/<uuid>/edit/ → Édition d’une variante (SKU)
  - Breadcrumb: Produits › Catalogue › <Produit> › Modifier SKU

Liens utiles depuis la fiche produit (si type=wine et cuvée liée):
- /produits/lots-commerciaux/?cuvee=<id>
- /production/mises/nouveau/ (Wizard Mise)

Notes:
- Pages privées avec `login_required`; Middleware `X-Robots-Tag: noindex` déjà actif.
- Breadcrumb partagé rendu via `templates/_layout/breadcrumbs.html` avec `breadcrumb_items`.
