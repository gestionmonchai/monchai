# 📍 Référence Complète des URLs MonChai

> **Version:** 2.0  
> **Dernière mise à jour:** Décembre 2024  
> **Application:** MonChai - Gestion Viticole SaaS

---

## 🏠 Navigation Principale

| URL | Description | Authentification |
|-----|-------------|------------------|
| `/` | Redirection vers dashboard ou landing | Non |
| `/monchai/` | Page d'accueil publique | Non |
| `/dashboard/` | Tableau de bord principal | ✅ Oui |
| `/admin/` | Administration Django | ✅ Admin |

---

## 🔐 Authentification (`/auth/`)

### Connexion & Inscription

| URL | Méthode | Description |
|-----|---------|-------------|
| `/auth/login/` | GET/POST | Page de connexion |
| `/auth/signup/` | GET/POST | Page d'inscription |
| `/auth/logout/` | POST | Déconnexion |

### Réinitialisation Mot de Passe

| URL | Description |
|-----|-------------|
| `/auth/password/reset/` | Demande de réinitialisation |
| `/auth/password/reset/done/` | Confirmation d'envoi email |
| `/auth/reset/<uidb64>/<token>/` | Formulaire nouveau mot de passe |
| `/auth/reset/complete/` | Confirmation changement |

### Premier Lancement (Onboarding)

| URL | Description |
|-----|-------------|
| `/auth/first-run/` | Garde premier lancement |
| `/auth/first-run/org/` | Création première organisation |

### Gestion des Rôles

| URL | Description |
|-----|-------------|
| `/auth/settings/roles/` | Liste des rôles et membres |
| `/auth/settings/roles/invite/` | Inviter un utilisateur |
| `/auth/settings/roles/change/<id>/` | Modifier un rôle |
| `/auth/settings/roles/deactivate/<id>/` | Désactiver un membre |

### Invitations

| URL | Description |
|-----|-------------|
| `/auth/invite/accept/<token>/` | Accepter une invitation |
| `/auth/invite/send/` | Envoyer une invitation |
| `/auth/invite/cancel/<id>/` | Annuler une invitation |
| `/auth/invite/resend/<id>/` | Renvoyer une invitation |

### Paramètres Utilisateur

| URL | Description |
|-----|-------------|
| `/auth/settings/billing/` | Paramètres de facturation |
| `/auth/settings/general/` | Paramètres généraux |
| `/auth/me/profile/` | Mon profil |
| `/auth/me/team/<id>/` | Détail d'un membre |

### Gestion Multi-Chai

| URL | Description |
|-----|-------------|
| `/auth/organizations/` | Mes organisations |
| `/auth/organizations/select/` | Sélectionner une organisation |
| `/auth/organizations/create/` | Créer une organisation |
| `/auth/organizations/switch/<id>/` | Changer d'organisation |
| `/auth/organizations/leave/<id>/` | Quitter une organisation |

### Dashboard Personnalisable

| URL | Description |
|-----|-------------|
| `/auth/dashboard/configure/` | Configurer le dashboard |
| `/auth/api/dashboard/config/` | API sauvegarde config |
| `/auth/api/dashboard/widget/add/` | Ajouter un widget |
| `/auth/api/dashboard/widget/remove/` | Supprimer un widget |
| `/auth/api/dashboard/widget/reorder/` | Réordonner les widgets |
| `/auth/api/dashboard/reset/` | Réinitialiser le dashboard |

---

## 🍇 Production (`/production/`)

### Vue d'Ensemble

| URL | Description |
|-----|-------------|
| `/production/` | Accueil production |
| `/production/vigne/` | Dashboard Vigne |
| `/production/chai/` | Dashboard Chai |
| `/production/elevage/` | Dashboard Élevage |
| `/production/conditionnement/` | Dashboard Conditionnement |

### Parcelles

| URL | Description |
|-----|-------------|
| `/production/parcelles/` | Liste des parcelles |
| `/production/parcelles/v2/` | Liste V2 (nouvelle interface) |
| `/production/parcelles/table/` | Vue tableau HTMX |
| `/production/parcelles/nouveau/` | Créer une parcelle |
| `/production/parcelles/<id>/` | Détail parcelle |
| `/production/parcelles/<id>/modifier/` | Modifier parcelle |
| `/production/parcelles/<id>/weather-preview/` | Aperçu météo |
| `/production/parcelles/<id>/events-preview/` | Aperçu événements |
| `/production/parcelles/<id>/composition-preview/` | Aperçu encépagement |

### Journal Cultural

| URL | Description |
|-----|-------------|
| `/production/journal-cultural/` | Journal cultural unifié |
| `/production/journal-cultural/table/` | Vue tableau |
| `/production/cahier-cultural/` | → Redirect journal |
| `/production/registre-phyto/` | → Redirect journal (onglet phyto) |
| `/production/suivi-maturite/` | → Redirect journal (onglet maturité) |

### Vendanges

| URL | Description |
|-----|-------------|
| `/production/vendanges/` | Liste des vendanges |
| `/production/vendanges/table/` | Vue tableau |
| `/production/vendanges/nouveau/` | Saisie vendange |
| `/production/vendanges/carte/` | Vue carte |
| `/production/vendanges/<id>/` | Détail vendange |
| `/production/vendanges/<id>/modifier/` | Modifier vendange |
| `/production/vendanges/<id>/affecter-cuvee/` | Affecter à une cuvée |
| `/production/vendanges/<id>/encuvage/` | Wizard encuvage |

### Lots Techniques

| URL | Description |
|-----|-------------|
| `/production/lots-techniques/` | Vue Cuvée (principale) |
| `/production/lots-techniques/liste/` | Liste classique |
| `/production/lots-techniques/v2/` | Liste V2 |
| `/production/lots-techniques/table/` | Vue tableau |
| `/production/lots-techniques/nouveau/` | Créer un lot |
| `/production/lots-techniques/<id>/` | Détail lot |
| `/production/lots-techniques/<id>/action/<action>/` | Actions sur lot |
| `/production/lots-techniques/<id>/affecter-cuvee/` | Affecter cuvée |
| `/production/lots-techniques/<id>/soutirage/` | Wizard soutirage |
| `/production/lots-techniques/<id>/pressurage/` | Wizard pressurage |
| `/production/lots-techniques/<id>/mouvements/export/` | Export mouvements |

### Vinification

| URL | Description |
|-----|-------------|
| `/production/vinification/` | Accueil vinification |
| `/production/vinification/table/` | Vue tableau |
| `/production/vinification/operation/create/` | Créer opération |

### Soutirages

| URL | Description |
|-----|-------------|
| `/production/soutirages/` | Liste soutirages |
| `/production/soutirages/table/` | Vue tableau |
| `/production/soutirages/nouveau/` | Créer soutirage |

### Assemblages

| URL | Description |
|-----|-------------|
| `/production/assemblages/` | Liste assemblages |
| `/production/assemblages/table/` | Vue tableau |
| `/production/assemblages/nouveau/` | Wizard assemblage |
| `/production/assemblages/<id>/` | Détail assemblage |

### Opérations de Cave

| URL | Description |
|-----|-------------|
| `/production/operations/nouvelle/` | Créer opération |
| `/production/operations/<id>/` | Détail opération |
| `/production/operations/<id>/modifier/` | Modifier opération |
| `/production/operations/<id>/supprimer/` | Supprimer opération |
| `/production/operations/<id>/creer-alerte/` | Créer alerte depuis opération |

### Encuvages & Pressurages

| URL | Description |
|-----|-------------|
| `/production/encuvages/` | Liste encuvages |
| `/production/encuvages/table/` | Vue tableau |
| `/production/pressurages/` | Liste pressurages |

### Lots Élevage

| URL | Description |
|-----|-------------|
| `/production/lots-elevage/` | → Redirect lots (scope=elevage) |
| `/production/lots-elevage/table/` | Vue tableau |
| `/production/lots-elevage/journal/` | Journal vrac |
| `/production/lots-elevage/journal/table/` | Vue tableau journal |

### Analyses Œnologiques

| URL | Description |
|-----|-------------|
| `/production/lots-elevage/analyses/` | Liste analyses |
| `/production/lots-elevage/analyses/table/` | Vue tableau |
| `/production/lots-elevage/analyses/nouvelle/` | Créer analyse |
| `/production/lots-elevage/analyses/<id>/` | Modifier analyse |
| `/production/lots-elevage/analyses/<id>/supprimer/` | Supprimer |
| `/production/lots-elevage/analyses/<id>/dupliquer/` | Dupliquer |

### Contenants

| URL | Description |
|-----|-------------|
| `/production/contenants/` | Liste contenants |
| `/production/contenants/v2/` | Liste V2 |
| `/production/contenants/nouveau/` | Créer contenant |
| `/production/contenants/<id>/` | Détail contenant |
| `/production/contenants/<id>/edit/` | Modifier |
| `/production/contenants/<id>/occupancy/recalc/` | Recalculer occupation |
| `/production/contenants/<id>/actions/affecter-lot/` | Affecter lot |
| `/production/contenants/<id>/actions/vidange/` | Vidanger |
| `/production/contenants/<id>/actions/nettoyage/` | Nettoyage |

### Mises en Bouteille

| URL | Description |
|-----|-------------|
| `/production/mises/` | Liste mises |
| `/production/mises/nouveau/` | Wizard mise |
| `/production/mises/<uuid>/` | Détail mise |

### Inventaire

| URL | Description |
|-----|-------------|
| `/production/inventaire/` | Accueil inventaire |
| `/production/inventaire/tab/vrac/` | Onglet vrac |
| `/production/inventaire/tab/produits/` | Onglet produits |
| `/production/inventaire/tab/lots-commerciaux/` | Onglet lots commerciaux |
| `/production/inventaire/tab/ms/` | Onglet matières sèches |
| `/production/inventaire/ms/entree/` | Modal entrée MS |
| `/production/inventaire/ms/transfert/` | Modal transfert MS |
| `/production/inventaire/ms/ajustement/` | Modal ajustement MS |

### Alertes & Rappels

| URL | Description |
|-----|-------------|
| `/production/alertes/` | Liste alertes |
| `/production/alertes/nouvelle/` | Créer alerte |
| `/production/alertes/<id>/modifier/` | Modifier alerte |
| `/production/alertes/<id>/supprimer/` | Supprimer |
| `/production/alertes/<id>/terminer/` | Marquer terminée |
| `/production/alertes/<id>/ignorer/` | Ignorer |
| `/production/alertes/<id>/reporter/` | Reporter |

### Registres & Rapports

| URL | Description |
|-----|-------------|
| `/production/registres/` | Registres obligatoires |
| `/production/parametres/` | Paramètres production |
| `/production/rapports/` | Rapports & DRM |

---

## 👥 Clients (`/referentiels/clients/`)

| URL | Description |
|-----|-------------|
| `/referentiels/clients/` | Liste clients |
| `/referentiels/clients/v2/` | Liste V2 |
| `/referentiels/clients/nouveau/` | Créer client |
| `/referentiels/clients/<uuid>/` | Détail client |
| `/referentiels/clients/<uuid>/modifier/` | Modifier client |
| `/referentiels/clients/export/` | Export clients |
| `/referentiels/clients/search-ajax/` | Recherche AJAX |
| `/referentiels/clients/api/` | API clients |
| `/referentiels/clients/api/suggestions/` | Suggestions auto |
| `/referentiels/clients/api/quick-create/` | Création rapide |
| `/referentiels/clients/api/duplicates/` | Détection doublons |

---

## 🛒 Commerce - Achats (`/achats/`)

### Dashboard & Articles

| URL | Description |
|-----|-------------|
| `/achats/dashboard/` | Tableau de bord achats |
| `/achats/articles/` | Catalogue articles achat |
| `/achats/articles/nouveau/` | Créer article |
| `/achats/articles/<id>/` | Détail article |
| `/achats/articles/<id>/modifier/` | Modifier article |

### Fournisseurs

| URL | Description |
|-----|-------------|
| `/achats/fournisseurs/` | Liste fournisseurs |
| `/achats/fournisseurs/nouveau/` | Créer fournisseur |
| `/achats/fournisseurs/<uuid>/` | Détail fournisseur |
| `/achats/fournisseurs/<uuid>/modifier/` | Modifier fournisseur |

### Cycle d'Achat

| URL | Description |
|-----|-------------|
| `/achats/demandes-prix/` | Demandes de prix |
| `/achats/demandes-prix/nouveau/` | Créer demande |
| `/achats/demandes-prix/<uuid>/` | Détail demande |
| `/achats/commandes/` | Commandes fournisseurs |
| `/achats/commandes/nouvelle/` | Créer commande |
| `/achats/commandes/<uuid>/` | Détail commande |
| `/achats/receptions/` | Réceptions |
| `/achats/receptions/nouvelle/` | Créer réception |
| `/achats/receptions/<uuid>/` | Détail réception |

### Facturation Achats

| URL | Description |
|-----|-------------|
| `/achats/factures/` | Factures fournisseurs |
| `/achats/factures/nouvelle/` | Créer facture |
| `/achats/factures/<uuid>/` | Détail facture |
| `/achats/avoirs/` | Avoirs fournisseurs |
| `/achats/avoirs/nouvel/` | Créer avoir |
| `/achats/avoirs/<uuid>/` | Détail avoir |

### Paiements

| URL | Description |
|-----|-------------|
| `/achats/paiements/echeancier/` | Échéancier paiements |
| `/achats/paiements/effectues/` | Paiements effectués |

---

## 💰 Commerce - Ventes (`/ventes/`)

### Dashboard & Articles

| URL | Description |
|-----|-------------|
| `/ventes/dashboard/` | Tableau de bord ventes |
| `/ventes/articles/` | Catalogue articles vente |
| `/ventes/articles/nouveau/` | Créer article |
| `/ventes/articles/<id>/` | Détail article |
| `/ventes/articles/<id>/modifier/` | Modifier article |

### Pipeline Commercial

| URL | Description |
|-----|-------------|
| `/ventes/pipeline/` | Pipeline commercial |
| `/ventes/devis/` | Liste des devis |
| `/ventes/devis/nouveau/` | Créer devis |
| `/ventes/devis/<uuid>/` | Détail devis |

### Commandes & Livraisons

| URL | Description |
|-----|-------------|
| `/ventes/commandes/` | Commandes clients |
| `/ventes/commandes/nouvelle/` | Créer commande |
| `/ventes/commandes/<uuid>/` | Détail commande |
| `/ventes/livraisons/` | Bons de livraison |
| `/ventes/livraisons/nouvelle/` | Créer BL |
| `/ventes/livraisons/<uuid>/` | Détail BL |

### Facturation Ventes

| URL | Description |
|-----|-------------|
| `/ventes/factures/` | Factures clients |
| `/ventes/factures/nouvelle/` | Créer facture |
| `/ventes/factures/<uuid>/` | Détail facture |
| `/ventes/avoirs/` | Avoirs clients |
| `/ventes/avoirs/nouvel/` | Créer avoir |
| `/ventes/avoirs/<uuid>/` | Détail avoir |

### Encaissements

| URL | Description |
|-----|-------------|
| `/ventes/paiements/echeancier/` | Échéancier |
| `/ventes/paiements/encaissements/` | Encaissements |

### Gestion Tarifaire

| URL | Description |
|-----|-------------|
| `/ventes/grilletarifs/` | Grilles tarifaires |
| `/ventes/grilletarifs/creer/` | Créer grille |
| `/ventes/grilletarifs/<id>/` | Détail grille |
| `/ventes/grilletarifs/<id>/modifier/` | Modifier grille |
| `/ventes/grilletarifs/<id>/supprimer/` | Supprimer grille |
| `/ventes/grilletarifs/<id>/grille/` | Édition en grille |
| `/ventes/grilletarifs/<id>/import/` | Import tarifs |

### Templates Documents

| URL | Description |
|-----|-------------|
| `/ventes/templates/` | Liste templates |
| `/ventes/templates/creer/` | Builder visuel |
| `/ventes/templates/creer-html/` | Mode HTML |
| `/ventes/templates/<uuid>/` | Détail template |
| `/ventes/templates/<uuid>/modifier/` | Modifier |
| `/ventes/templates/<uuid>/supprimer/` | Supprimer |
| `/ventes/templates/<uuid>/dupliquer/` | Dupliquer |
| `/ventes/templates/<uuid>/apercu/` | Aperçu |
| `/ventes/templates/<uuid>/variables/` | Aide variables |

---

## 📦 Produits (`/produits/`)

### Catalogue

| URL | Description |
|-----|-------------|
| `/produits/` | Liste produits (legacy) |
| `/produits/produits/catalogue/` | Catalogue produits |
| `/produits/produits/catalogue/nouveau/` | Créer produit |
| `/produits/produits/catalogue/<slug>/` | Détail produit |
| `/produits/produits/catalogue/<slug>/edit/` | Modifier produit |

### Cuvées

| URL | Description |
|-----|-------------|
| `/produits/produits/cuvees/` | Liste cuvées |
| `/produits/produits/cuvees/nouveau/` | Créer cuvée |
| `/produits/produits/cuvees/<id>/` | Détail cuvée |

### SKUs

| URL | Description |
|-----|-------------|
| `/produits/produits/skus/` | Liste SKUs |
| `/produits/produits/skus/nouveau/` | Créer SKU |
| `/produits/produits/skus/<id>/` | Détail SKU |
| `/produits/produits/skus/<id>/edit/` | Modifier SKU |

### Workflow Achat/Vente

| URL | Description |
|-----|-------------|
| `/produits/produits/achats/nouveau/` | Créer article achat |
| `/produits/produits/achats/<slug>/succes/` | Succès création |
| `/produits/produits/achats/<slug>/vendre/` | Bridge vers vente |
| `/produits/produits/ventes/nouveau/` | Créer article vente |
| `/produits/produits/ventes/<slug>/succes/` | Succès création |
| `/produits/produits/ventes/<slug>/acheter/` | Bridge vers achat |

### Lots Commerciaux

| URL | Description |
|-----|-------------|
| `/produits/produits/lots-commerciaux/` | Liste lots commerciaux |
| `/produits/produits/lots-commerciaux/<uuid>/` | Détail lot |

---

## 📚 Référentiels (`/referentiels/`)

### Accueil

| URL | Description |
|-----|-------------|
| `/referentiels/` | Page d'accueil référentiels |

### Cépages

| URL | Description |
|-----|-------------|
| `/referentiels/cepages/` | Liste cépages |
| `/referentiels/cepages/export/` | Export CSV |
| `/referentiels/cepages/search-ajax/` | Recherche AJAX |
| `/referentiels/cepages/import-reference/` | Import référence |
| `/referentiels/cepages/<id>/` | Détail cépage |
| `/referentiels/cepages/nouveau/` | Créer cépage |
| `/referentiels/cepages/<id>/modifier/` | Modifier cépage |
| `/referentiels/cepages/<id>/supprimer/` | Supprimer cépage |

### Parcelles

| URL | Description |
|-----|-------------|
| `/referentiels/parcelles/` | Liste parcelles |
| `/referentiels/parcelles/carte/` | Vue carte |
| `/referentiels/parcelles/export/` | Export CSV |
| `/referentiels/parcelles/search-ajax/` | Recherche AJAX |
| `/referentiels/parcelles/<id>/` | Détail parcelle |
| `/referentiels/parcelles/nouvelle/` | Créer parcelle |
| `/referentiels/parcelles/<id>/modifier/` | Modifier parcelle |
| `/referentiels/parcelles/<id>/supprimer/` | Supprimer parcelle |

### Encépagement

| URL | Description |
|-----|-------------|
| `/referentiels/parcelles/<id>/encepagement/ajouter/` | Ajouter cépage |
| `/referentiels/parcelles/<id>/encepagement/<id>/modifier/` | Modifier |
| `/referentiels/parcelles/<id>/encepagement/<id>/supprimer/` | Supprimer |

### Unités

| URL | Description |
|-----|-------------|
| `/referentiels/unites/` | Liste unités |
| `/referentiels/unites/export/` | Export CSV |
| `/referentiels/unites/search-ajax/` | Recherche AJAX |
| `/referentiels/unites/<id>/` | Détail unité |
| `/referentiels/unites/nouvelle/` | Créer unité |
| `/referentiels/unites/<id>/modifier/` | Modifier unité |
| `/referentiels/unites/<id>/supprimer/` | Supprimer unité |

### Cuvées (Référentiel)

| URL | Description |
|-----|-------------|
| `/referentiels/cuvees/` | Liste cuvées |
| `/referentiels/cuvees/export/` | Export CSV |
| `/referentiels/cuvees/search-ajax/` | Recherche AJAX |
| `/referentiels/cuvees/<id>/` | Détail cuvée |
| `/referentiels/cuvees/nouvelle/` | Créer cuvée |
| `/referentiels/cuvees/<id>/modifier/` | Modifier cuvée |
| `/referentiels/cuvees/<id>/supprimer/` | Supprimer cuvée |

### Entrepôts

| URL | Description |
|-----|-------------|
| `/referentiels/entrepots/` | Liste entrepôts |
| `/referentiels/entrepots/export/` | Export CSV |
| `/referentiels/entrepots/search-ajax/` | Recherche AJAX |
| `/referentiels/entrepots/<id>/` | Détail entrepôt |
| `/referentiels/entrepots/nouveau/` | Créer entrepôt |
| `/referentiels/entrepots/<id>/modifier/` | Modifier entrepôt |
| `/referentiels/entrepots/<id>/supprimer/` | Supprimer entrepôt |

### Import CSV

| URL | Description |
|-----|-------------|
| `/referentiels/import/` | Page import |
| `/referentiels/import/preview/` | Aperçu données |
| `/referentiels/import/execute/` | Exécuter import |
| `/referentiels/import/download-errors/` | Télécharger erreurs |

---

## 📊 DRM (`/drm/`)

| URL | Description |
|-----|-------------|
| `/drm/` | Dashboard DRM |
| `/drm/crd/` | CRD / Code INAO |
| `/drm/inao/` | Liste codes INAO |
| `/drm/editer/` | Éditeur période courante |
| `/drm/editer/<period>/` | Éditeur période spécifique |
| `/drm/export/` | Export période courante |
| `/drm/export/<period>/` | Export période spécifique |
| `/drm/api/inao/` | API recherche codes INAO |

---

## 📦 Stocks (`/stocks/`)

### Dashboard & Mouvements

| URL | Description |
|-----|-------------|
| `/stocks/` | Dashboard stocks |
| `/stocks/mouvements/` | Journal des mouvements |

### Inventaires

| URL | Description |
|-----|-------------|
| `/stocks/inventaires/` | Liste inventaires |
| `/stocks/inventaires/nouveau/` | Créer inventaire |
| `/stocks/inventaires/<id>/` | Détail inventaire |
| `/stocks/inventaire/` | Vue inventaire |
| `/stocks/inventaire/counting/<id>/` | Comptage |

### Entrepôts & Emplacements

| URL | Description |
|-----|-------------|
| `/stocks/entrepots/` | Liste entrepôts |
| `/stocks/emplacements/` | Liste emplacements |

### Transferts

| URL | Description |
|-----|-------------|
| `/stocks/transferts/` | Liste transferts |
| `/stocks/transferts/nouveau/` | Créer transfert |

### Alertes & Seuils

| URL | Description |
|-----|-------------|
| `/stocks/alertes/` | Alertes stock |
| `/stocks/seuils/` | Seuils d'alerte |

---

## 📘 Catalogue (`/catalogue/`)

### Grille Catalogue

| URL | Description |
|-----|-------------|
| `/catalogue/` | Grille catalogue |
| `/catalogue/search/` | Recherche AJAX |
| `/catalogue/<id>/` | Détail cuvée |

### Interface Produits

| URL | Description |
|-----|-------------|
| `/catalogue/produits/` | Dashboard produits |
| `/catalogue/produits/cuvees/` | Cuvées |
| `/catalogue/produits/lots/` | Lots |
| `/catalogue/produits/skus/` | SKUs |
| `/catalogue/produits/referentiels/` | Référentiels |

### Articles

| URL | Description |
|-----|-------------|
| `/catalogue/articles/` | Tous les articles |
| `/catalogue/articles/achats/` | Articles achat |
| `/catalogue/articles/ventes/` | Articles vente |
| `/catalogue/articles/nouveau/` | Créer article |
| `/catalogue/articles/<id>/` | Modifier article |

---

## 🎯 Onboarding (`/onboarding/`)

| URL | Description |
|-----|-------------|
| `/onboarding/` | Flow guidé |
| `/onboarding/checklist/` | Checklist organisation |
| `/onboarding/skip/<step>/` | Passer une étape |
| `/onboarding/dismiss/` | Fermer |
| `/onboarding/reset/` | Réinitialiser |

---

## 🤖 API Aide IA (`/api/`)

### Aide Contextuelle

| URL | Description |
|-----|-------------|
| `/api/help/` | Assistant d'aide |
| `/api/help/query` | Requête aide |

### Smart Suggestions

| URL | Description |
|-----|-------------|
| `/api/smart/weather/parcelle/<id>/` | Alertes météo parcelle |
| `/api/smart/weather/forecast/` | Prévisions météo |
| `/api/smart/cuves/` | Suggestions cuves |
| `/api/smart/analyse/<lot_id>/` | Alertes analyse |
| `/api/smart/drm/` | Statut DRM |
| `/api/smart/intrants/` | Suggestions intrants |
| `/api/smart/context/` | Contexte intelligent |

---

## 🔌 API Authentification (`/api/auth/`)

| URL | Méthode | Description |
|-----|---------|-------------|
| `/api/auth/session/` | POST | Login API |
| `/api/auth/whoami/` | GET | Info utilisateur courant |
| `/api/auth/logout/` | POST | Déconnexion API |
| `/api/auth/csrf/` | GET | Token CSRF |

---

## 🌍 Viticulture (`/viticulture/`)

| URL | Description |
|-----|-------------|
| `/viticulture/cuvee/<id>/change/` | Changer cuvée |
| `/viticulture/parcelles/<id>/journal/` | Journal parcelle |
| `/viticulture/parcelles/<id>/journal/partial/` | Partial HTMX |
| `/viticulture/parcelles/<id>/operation/<code>/` | Opération rapide |
| `/viticulture/journal/<id>/` | Détail entrée journal |
| `/viticulture/journal/<id>/modifier/` | Modifier entrée |
| `/viticulture/journal/<id>/supprimer/` | Supprimer entrée |

---

## 🗺️ GIS & Cadastre

### Parcelles

| URL | Description |
|-----|-------------|
| `/embed/parcelles` | Visualiseur parcelles intégré |
| `/api/parcelles/` | API parcelles GIS |
| `/api/tiles/` | Tuiles cartographiques |

---

## 📋 Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+K` | Recherche globale |
| `Ctrl+N` | Nouvelle entité (contextuel) |
| `Esc` | Fermer modal/panneau |
| `?` | Aide contextuelle |

---

## 🔗 Redirections Importantes

| Ancienne URL | Nouvelle URL |
|--------------|--------------|
| `/catalogue/produits/` | `/produits/cuvees/` |
| `/stock/mouvements/` | `/stocks/mouvements/` |
| `/stock/drm/` | `/drm/` |
| `/ref/cepages/` | `/referentiels/cepages/` |
| `/ref/parcelles/` | `/referentiels/parcelles/` |
| `/clients/` | `/referentiels/clients/` |

---

*Documentation générée automatiquement pour MonChai v2.0*
