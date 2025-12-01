# Incohérences détectées dans le routage actuel

## Date d'analyse : 2025-09-24

## 🚨 Problèmes majeurs identifiés

### 1. Fonctionnalités métier dans `/admin/`

**PROBLÈME CRITIQUE** : De nombreuses fonctionnalités métier sont accessibles uniquement via l'admin Django, ce qui viole la séparation technique/métier.

#### URLs problématiques :
- `/admin/sales/customer/` → Gestion des clients dans l'admin
- `/admin/sales/quote/` → Devis dans l'admin  
- `/admin/sales/order/` → Commandes dans l'admin
- `/admin/billing/invoice/` → Factures dans l'admin
- `/admin/billing/payment/` → Paiements dans l'admin
- `/admin/viticulture/cuvee/` → Cuvées dans l'admin
- `/admin/viticulture/lot/` → Lots dans l'admin
- `/admin/viticulture/grapevariety/` → Cépages dans l'admin

**Impact** : Les utilisateurs métier doivent accéder à l'interface technique Django au lieu d'avoir une interface dédiée.

### 2. Doublons de modèles

#### Clients dupliqués :
- `sales.Customer` accessible via `/admin/sales/customer/`
- `clients.Customer` accessible via `/clients/`

**Impact** : Confusion sur quel modèle utiliser, risque d'incohérence des données.

### 3. Versions d'API incohérentes

#### Mélange v1/v2 :
- `/api/auth/` (pas de version)
- `/ref/api/v2/` (version 2)
- `/catalogue/api/` (pas de version)
- `/stocks/api/` (pas de version)

**Impact** : Pas de stratégie de versioning cohérente, difficile à maintenir.

### 4. Nommage incohérent

#### Patterns différents :
- `/ref/cepages/search-ajax/` (avec tirets)
- `/catalogue/search/` (sans suffixe)
- `/stocks/api/alertes/acknowledge/` (anglais/français mélangé)

**Impact** : Imprévisibilité pour les développeurs, maintenance difficile.

## 📊 Statistiques

### Répartition par type :
- **URLs métier dans admin** : 15 routes
- **URLs API sans version** : 12 routes  
- **URLs avec nommage incohérent** : 8 routes
- **Doublons identifiés** : 2 modèles

### Répartition par app :
- **accounts** : 12 routes (dont 6 à déplacer vers backoffice)
- **referentiels** : 18 routes (dont 6 API à versionner)
- **catalogue** : 15 routes (dont 3 API à versionner)
- **stock** : 15 routes (dont 11 API à versionner)
- **clients** : 8 routes (dont 3 API à versionner)
- **admin Django** : 15+ routes métier à migrer

## 🎯 Actions prioritaires

### Priorité 1 - Critique
1. **Migrer toutes les fonctionnalités métier hors de `/admin/`**
2. **Résoudre les doublons de modèles clients**
3. **Créer l'interface `/backoffice/`**

### Priorité 2 - Important  
1. **Uniformiser les versions d'API vers v1**
2. **Standardiser le nommage des routes**
3. **Créer les redirections 301**

### Priorité 3 - Amélioration
1. **Optimiser les patterns d'URLs**
2. **Ajouter les routes manquantes (détail, édition)**
3. **Documenter les conventions**

## 🔍 URLs manquantes identifiées

### Référentiels - Actions CRUD manquantes :
- Détail : `/referentiels/cepages/<id>/`
- Édition : `/referentiels/cepages/<id>/modifier/`
- Suppression : `/referentiels/cepages/<id>/supprimer/`
- (Idem pour parcelles, unités, entrepôts)

### Ventes - Interface complète manquante :
- `/ventes/` (dashboard)
- `/ventes/devis/`
- `/ventes/commandes/`  
- `/ventes/factures/`
- `/ventes/paiements/`

### Backoffice - Interface d'administration :
- `/backoffice/` (dashboard admin)
- `/backoffice/utilisateurs/`
- `/backoffice/parametres/`
- `/backoffice/monitoring/`

## 📋 Prochaines étapes

1. ✅ **Phase 1 terminée** : Inventaire complet réalisé
2. 🔄 **Phase 2** : Créer le plan d'URL canonique
3. 🔄 **Phase 3** : Définir le modèle RBAC
4. 🔄 **Phase 4** : Implémenter les scopes
5. 🔄 **Phase 5** : Migrer vers `/backoffice/`

---

**Total : 87 routes inventoriées, 35 problèmes identifiés, 0 zone grise**
