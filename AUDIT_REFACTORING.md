# Audit de Refactoring - Mon Chai V1

**Date:** 17 décembre 2024

## 📊 Résumé Exécutif

Le projet contient plusieurs couches d'apps qui font des choses similaires, résultant de migrations successives. Voici l'état des lieux et les recommandations de nettoyage.

---

## 🔴 Apps à Supprimer (Obsolètes)

### 1. `apps/ref/` → **À SUPPRIMER**
- **Raison:** Remplacée par `apps/referentiels/`
- **Contenu:** Seulement `urls.py` qui redirige vers `referentiels`
- **Action:** Supprimer le dossier entièrement

### 2. `apps/stock_drm/` → **À SUPPRIMER**
- **Raison:** Vide, les routes sont gérées par `apps/stock/` et `apps/drm/`
- **Contenu:** Seulement `urls.py` avec des placeholders
- **Action:** Supprimer le dossier entièrement

### 3. `apps/chai/` → **À SUPPRIMER**
- **Raison:** Contient seulement un dossier `services/` vide ou minimal
- **Action:** Vérifier si utilisé, sinon supprimer

---

## 🟠 Apps avec Duplications (À Fusionner/Nettoyer)

### 1. Système Commercial: `commerce` vs `sales` vs `ventes`

**Situation actuelle:**
```
apps/commerce/     → Nouveau système unifié (actif via /achats/ et /ventes/)
apps/sales/        → Ancien système (Quote, Order, pricelists, templates) - PARTIELLEMENT UTILISÉ
apps/ventes/       → Module legacy (orders, invoices, primeur, vrac) - UTILISÉ MAIS REDONDANT
```

**Ce qui est UTILISÉ dans `apps/sales/`:**
- ✅ `views_pricelists.py` - Grilles tarifaires (monté sous `/ventes/grilletarifs/`)
- ✅ `views_documents.py` - Templates de documents (monté sous `/ventes/templates/`)
- ✅ `views_quotes.py` - Devis legacy (monté sous `/ventes/devis/` via apps.ventes.urls)
- ✅ `models.py` - Quote, QuoteLine, Order, OrderLine, TaxCode, Customer

**Ce qui est UTILISÉ dans `apps/ventes/`:**
- ✅ `views_orders.py` - Commandes (via `/ventes/commandes/`)
- ✅ `views_invoices.py` - Factures (via `/ventes/factures/`)
- ✅ `views_primeur.py` - Ventes primeur
- ✅ `views_vrac.py` - Ventes vrac

**Recommandation:**
- **Court terme:** Garder les 3 apps mais documenter clairement leur usage
- **Moyen terme:** Migrer `sales` et `ventes` vers `commerce` progressivement

---

### 2. Catalogue: `views.py` vs `views_unified.py` vs `views_grid.py`

**Vues OBSOLÈTES dans `apps/catalogue/views.py`:**
```python
# Ces fonctions ont des suffixes _legacy dans les URLs
- catalogue_home()      → Remplacée par views_grid.catalogue_grid
- catalogue_cuvee_detail() → Remplacée par views_unified.cuvee_detail
- lot_list()            → Route catalogue:lot_list_legacy (OBSOLÈTE)
- lot_create()          → Route catalogue:lot_create_legacy (OBSOLÈTE)
- lot_detail()          → Route catalogue:lot_detail_legacy (OBSOLÈTE)
- lot_update()          → Route catalogue:lot_update_legacy (OBSOLÈTE)
- lot_delete()          → Route catalogue:lot_delete_legacy (OBSOLÈTE)
- lot_add_mouvement()   → Route catalogue:lot_add_mouvement_legacy (OBSOLÈTE)
```

**Vues ACTIVES (à conserver):**
```python
# views.py - Classes Article (nouveau catalogue)
- ArticleListView, PurchaseArticleListView, SalesArticleListView
- ArticleCreateView, ArticleUpdateView
- InventoryListView

# views_grid.py
- catalogue_grid()
- catalogue_search_ajax()

# views_unified.py
- products_dashboard(), products_cuvees(), products_lots(), products_skus()
- cuvee_create(), cuvee_detail(), lot_create(), lot_detail()
- *_search_ajax() fonctions
```

---

## 🟡 Fichiers Views avec Code Mort

### `apps/catalogue/views.py`
Lignes 22-467: Vues `catalogue_home`, `catalogue_cuvee_detail`, `lot_list`, `lot_create`, `lot_detail`, `lot_update`, `lot_delete`, `lot_add_mouvement`
**→ À SUPPRIMER** (remplacées par views_unified et views_grid)

### `apps/production/views.py`
Vérifier les vues non référencées dans urls.py

---

## ✅ Apps Propres (Pas de Nettoyage Nécessaire)

- `apps/accounts/` - Authentification, organisations
- `apps/production/` - Production viticole (bien structuré)
- `apps/viticulture/` - Modèles et vues viticulture
- `apps/referentiels/` - Données de référence
- `apps/clients/` - Gestion clients
- `apps/drm/` - Déclaration récapitulative
- `apps/stock/` - Gestion stock
- `apps/produits/` - Produits et SKUs
- `apps/ai/` - Assistant IA
- `apps/onboarding/` - Onboarding

---

## 📋 Plan d'Action Recommandé

### Phase 1: Nettoyage Immédiat (Sans Risque)
1. [ ] Supprimer `apps/ref/` (remplacé par referentiels)
2. [ ] Supprimer `apps/stock_drm/` (vide)
3. [ ] Supprimer `apps/chai/` si vide
4. [ ] Supprimer les vues legacy dans `apps/catalogue/views.py`

### Phase 2: Consolidation URLs
1. [ ] Retirer les routes `_legacy` de `apps/catalogue/urls.py`
2. [ ] Vérifier les redirections dans `apps/core/urls.py`

### Phase 3: Migration Commerce (Futur)
1. [ ] Migrer les modèles Quote/Order de `sales` vers `commerce`
2. [ ] Migrer les vues factures/commandes de `ventes` vers `commerce`
3. [ ] Supprimer `apps/sales/` et `apps/ventes/`

---

## 📂 Structure Cible Recommandée

```
apps/
├── accounts/        # Auth, orgs, users
├── ai/              # Assistant IA
├── billing/         # Facturation (garder pour Invoice model)
├── catalogue/       # Catalogue produits (nettoyer views.py)
├── clients/         # Clients/Fournisseurs
├── commerce/        # Achats + Ventes unifiés
├── core/            # Redirections, placeholders
├── drm/             # DRM
├── imports/         # Import données
├── metadata/        # Métadonnées
├── onboarding/      # Onboarding
├── production/      # Production viticole
├── produits/        # Produits, SKUs, Mises
├── referentiels/    # Données référence
├── stock/           # Stock
├── viticulture/     # Modèles viticulture
└── [SUPPRIMER: ref/, stock_drm/, chai/]
```
