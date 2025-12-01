# Plan d'URL Canonique - Mon Chai V1

## Date : 2025-09-24

## 🎯 Conventions appliquées

### Web App (Français)
- **CRUD** : `/ressource/`, `/ressource/nouveau/`, `/ressource/<id>/`, `/ressource/<id>/modifier/`, `/ressource/<id>/supprimer/`
- **Recherche** : `/ressource/search/` (AJAX)
- **Export** : `/ressource/export/`

### API REST v1 (Anglais)
- **Collection** : `GET/POST /api/v1/ressource/`
- **Item** : `GET/PATCH/DELETE /api/v1/ressource/<id>/`
- **Actions** : `POST /api/v1/ressource/<id>/action/`

### Namespaces
- `auth:`, `catalogue:`, `clients:`, `ventes:`, `stocks:`, `referentiels:`, `backoffice:`, `apiv1:`

---

## 📱 ROUTES WEB CIBLES

### 🔐 Authentification (auth:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/auth/login/` | auth:login | False | - | - | ✅ OK |
| `/auth/signup/` | auth:signup | False | - | - | ✅ OK |
| `/auth/logout/` | auth:logout | True | - | - | ✅ OK |
| `/auth/password/reset/` | auth:password_reset | False | - | - | ✅ OK |
| `/auth/first-run/` | auth:first_run | True | - | - | ✅ OK |
| `/auth/me/profile/` | auth:profile | True | - | - | ✅ OK |

### 🏠 Dashboard (core)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/` | root | False | - | - | Redirection vers /dashboard/ |
| `/dashboard/` | dashboard | True | Tous | - | ✅ OK |

### 📦 Catalogue (catalogue:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/catalogue/` | catalogue:home | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/search/` | catalogue:search | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/cuvees/<uuid>/` | catalogue:cuvee_detail | True | Tous | catalogue:read | `/catalogue/<uuid>/` |
| `/catalogue/lots/` | catalogue:lots_list | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/lots/nouveau/` | catalogue:lot_create | True | Manager+ | catalogue:write | ✅ OK |
| `/catalogue/lots/<int>/` | catalogue:lot_detail | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/lots/<int>/modifier/` | catalogue:lot_edit | True | Manager+ | catalogue:write | ✅ OK |
| `/catalogue/lots/<int>/supprimer/` | catalogue:lot_delete | True | Manager+ | catalogue:write | ✅ OK |
| `/catalogue/produits/` | catalogue:products_dashboard | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/produits/cuvees/` | catalogue:products_cuvees | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/produits/lots/` | catalogue:products_lots | True | Tous | catalogue:read | ✅ OK |
| `/catalogue/produits/skus/` | catalogue:products_skus | True | Tous | catalogue:read | ✅ OK |

### 👥 Clients (clients:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/clients/` | clients:list | True | Tous | clients:read | ✅ OK |
| `/clients/nouveau/` | clients:create | True | Manager+ | clients:write | ✅ OK |
| `/clients/<uuid>/` | clients:detail | True | Tous | clients:read | ✅ OK |
| `/clients/<uuid>/modifier/` | clients:edit | True | Manager+ | clients:write | ✅ OK |
| `/clients/<uuid>/supprimer/` | clients:delete | True | AdminOrg+ | clients:write | NOUVEAU |
| `/clients/export/` | clients:export | True | Manager+ | clients:read | ✅ OK |
| `/clients/search/` | clients:search | True | Tous | clients:read | NOUVEAU |

### 💰 Ventes (ventes:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/ventes/` | ventes:dashboard | True | Tous | ventes:read | NOUVEAU |
| `/ventes/devis/` | ventes:quotes_list | True | Tous | ventes:read | `/admin/sales/quote/` |
| `/ventes/devis/nouveau/` | ventes:quote_create | True | Manager+ | ventes:write | NOUVEAU |
| `/ventes/devis/<uuid>/` | ventes:quote_detail | True | Tous | ventes:read | NOUVEAU |
| `/ventes/devis/<uuid>/modifier/` | ventes:quote_edit | True | Manager+ | ventes:write | NOUVEAU |
| `/ventes/commandes/` | ventes:orders_list | True | Tous | ventes:read | `/admin/sales/order/` |
| `/ventes/commandes/nouvelle/` | ventes:order_create | True | Manager+ | ventes:write | NOUVEAU |
| `/ventes/commandes/<uuid>/` | ventes:order_detail | True | Tous | ventes:read | NOUVEAU |
| `/ventes/factures/` | ventes:invoices_list | True | Comptabilité+ | ventes:read | `/admin/billing/invoice/` |
| `/ventes/factures/nouvelle/` | ventes:invoice_create | True | Comptabilité+ | ventes:write | NOUVEAU |
| `/ventes/factures/<uuid>/` | ventes:invoice_detail | True | Comptabilité+ | ventes:read | NOUVEAU |
| `/ventes/paiements/` | ventes:payments_list | True | Comptabilité+ | ventes:read | `/admin/billing/payment/` |

### 📦 Stocks (stocks:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/stocks/` | stocks:dashboard | True | Tous | stocks:read | ✅ OK |
| `/stocks/transferts/` | stocks:transferts_list | True | Tous | stocks:read | ✅ OK |
| `/stocks/transferts/nouveau/` | stocks:transfert_create | True | Opérateur+ | stocks:write | ✅ OK |
| `/stocks/inventaire/` | stocks:inventaire | True | Tous | stocks:read | ✅ OK |
| `/stocks/inventaire/comptage/<uuid>/` | stocks:inventaire_counting | True | Opérateur+ | stocks:write | `/stocks/inventaire/counting/<uuid>/` |
| `/stocks/alertes/` | stocks:alertes | True | Tous | stocks:read | ✅ OK |
| `/stocks/seuils/` | stocks:seuils | True | Manager+ | stocks:write | ✅ OK |

### 📚 Référentiels (referentiels:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/referentiels/` | referentiels:home | True | Tous | referentiels:read | `/ref/` |
| `/referentiels/cepages/` | referentiels:cepages_list | True | Tous | referentiels:read | `/ref/cepages/` |
| `/referentiels/cepages/nouveau/` | referentiels:cepage_create | True | Manager+ | referentiels:write | `/ref/cepages/nouveau/` |
| `/referentiels/cepages/<int>/` | referentiels:cepage_detail | True | Tous | referentiels:read | NOUVEAU |
| `/referentiels/cepages/<int>/modifier/` | referentiels:cepage_edit | True | Manager+ | referentiels:write | NOUVEAU |
| `/referentiels/cepages/search/` | referentiels:cepages_search | True | Tous | referentiels:read | `/ref/cepages/search-ajax/` |
| `/referentiels/parcelles/` | referentiels:parcelles_list | True | Tous | referentiels:read | `/ref/parcelles/` |
| `/referentiels/unites/` | referentiels:unites_list | True | Tous | referentiels:read | `/ref/unites/` |
| `/referentiels/cuvees/` | referentiels:cuvees_list | True | Tous | referentiels:read | `/ref/cuvees/` |
| `/referentiels/entrepots/` | referentiels:entrepots_list | True | Tous | referentiels:read | `/ref/entrepots/` |
| `/referentiels/import/` | referentiels:import | True | Manager+ | referentiels:write | `/ref/import/` |

### 🏢 Backoffice (backoffice:)
| URL | Name | Auth | Role | Scope | Remplace |
|-----|------|------|------|-------|----------|
| `/backoffice/` | backoffice:dashboard | True | AdminOrg+ | - | NOUVEAU |
| `/backoffice/utilisateurs/` | backoffice:users_list | True | AdminOrg+ | - | `/auth/settings/roles/` |
| `/backoffice/utilisateurs/inviter/` | backoffice:user_invite | True | AdminOrg+ | - | `/auth/settings/roles/invite/` |
| `/backoffice/parametres/` | backoffice:settings | True | AdminOrg+ | - | NOUVEAU |
| `/backoffice/parametres/facturation/` | backoffice:billing_settings | True | AdminOrg+ | - | `/auth/settings/billing/` |
| `/backoffice/parametres/generaux/` | backoffice:general_settings | True | AdminOrg+ | - | `/auth/settings/general/` |
| `/backoffice/monitoring/` | backoffice:monitoring | True | AdminOrg+ | - | `/metadata/monitoring/` |
| `/backoffice/feature-flags/` | backoffice:feature_flags | True | SuperAdmin | - | `/metadata/feature-flags/` |
| `/backoffice/onboarding/` | backoffice:onboarding | True | AdminOrg+ | - | `/onboarding/checklist/` |

---

## 🔌 ROUTES API CIBLES

### API v1 Auth (apiv1:auth:)
| URL | Method | Name | Auth | Remplace |
|-----|--------|------|------|----------|
| `/api/v1/auth/session/` | POST | apiv1:auth:login | False | `/api/auth/session/` |
| `/api/v1/auth/whoami/` | GET | apiv1:auth:whoami | True | `/api/auth/whoami/` |
| `/api/v1/auth/logout/` | POST | apiv1:auth:logout | True | `/api/auth/logout/` |
| `/api/v1/auth/csrf/` | GET | apiv1:auth:csrf | False | `/api/auth/csrf/` |

### API v1 Catalogue (apiv1:catalogue:)
| URL | Method | Name | Auth | Remplace |
|-----|--------|------|------|----------|
| `/api/v1/catalogue/` | GET | apiv1:catalogue:list | True | `/catalogue/api/catalogue/` |
| `/api/v1/catalogue/facets/` | GET | apiv1:catalogue:facets | True | `/catalogue/api/catalogue/facets/` |
| `/api/v1/catalogue/cuvees/<uuid>/` | GET | apiv1:catalogue:cuvee_detail | True | `/catalogue/api/catalogue/<uuid>/` |

### API v1 Clients (apiv1:clients:)
| URL | Method | Name | Auth | Remplace |
|-----|--------|------|------|----------|
| `/api/v1/clients/` | GET/POST | apiv1:clients:list_create | True | `/clients/api/` |
| `/api/v1/clients/<uuid>/` | GET/PATCH/DELETE | apiv1:clients:detail | True | NOUVEAU |
| `/api/v1/clients/suggestions/` | GET | apiv1:clients:suggestions | True | `/clients/api/suggestions/` |
| `/api/v1/clients/duplicates/` | GET | apiv1:clients:duplicates | True | `/clients/api/duplicates/` |

### API v1 Stocks (apiv1:stocks:)
| URL | Method | Name | Auth | Remplace |
|-----|--------|------|------|----------|
| `/api/v1/stocks/transferts/` | GET/POST | apiv1:stocks:transferts | True | `/stocks/api/transferts/` |
| `/api/v1/stocks/inventaire/` | GET | apiv1:stocks:inventaire | True | `/stocks/api/inventaire/` |
| `/api/v1/stocks/alertes/` | GET | apiv1:stocks:alertes | True | `/stocks/api/alertes/` |
| `/api/v1/stocks/alertes/compteur/` | GET | apiv1:stocks:alerts_count | True | `/stocks/api/alertes/badge-count/` |
| `/api/v1/stocks/seuils/` | GET/POST | apiv1:stocks:seuils | True | `/stocks/api/seuils/create/` |
| `/api/v1/stocks/seuils/<uuid>/` | DELETE | apiv1:stocks:seuil_delete | True | `/stocks/api/seuils/<uuid>/` |

### API v1 Référentiels (apiv1:referentiels:)
| URL | Method | Name | Auth | Remplace |
|-----|--------|------|------|----------|
| `/api/v1/referentiels/search/` | GET | apiv1:referentiels:search | True | `/ref/api/v2/search/` |
| `/api/v1/referentiels/suggestions/` | GET | apiv1:referentiels:suggestions | True | `/ref/api/v2/suggestions/` |
| `/api/v1/referentiels/facets/` | GET | apiv1:referentiels:facets | True | `/ref/api/v2/facets/` |

---

## 📋 RÉSUMÉ DES CHANGEMENTS

### ✅ Routes conservées (28)
- Authentification de base
- Dashboard principal  
- Structure catalogue existante
- Clients (interface web)
- Stocks (interface web)

### 🔄 Routes déplacées (15)
- `/admin/sales/*` → `/ventes/*`
- `/admin/billing/*` → `/ventes/*`
- `/auth/settings/*` → `/backoffice/*`
- `/metadata/*` → `/backoffice/*`
- `/onboarding/*` → `/backoffice/*`

### 🆕 Routes créées (22)
- Interface `/ventes/` complète
- Interface `/backoffice/` complète
- Actions CRUD manquantes
- API v1 unifiée

### 🗑️ Routes supprimées (12)
- Doublons admin/métier
- API non versionnées
- Routes incohérentes

**Total : 65 routes cibles vs 87 actuelles = -22 routes (simplification)**
