# Décisions de Design - Refactoring Routage Mon Chai V1

## Date de validation : 2025-09-24

## 1. Tenancy - Organisation comme entité maîtresse

### Décision
Une **Organisation/Domaine (vignoble)** est l'entité maîtresse pour la séparation des données.

### Raisons
- Chaque vignoble est une entité métier indépendante
- Isolation naturelle des données par exploitation
- Modèle de SaaS multi-tenant cohérent avec le domaine viticole
- Facilite la facturation et la gestion des accès

### Impacts
- Toutes les données métier sont liées à une organisation
- Middleware d'organisation obligatoire pour les vues métier
- Session utilisateur contient `current_org_id`
- Filtrage automatique des données par organisation

## 2. Séparation Back-office vs Admin Django

### Décision
- `/admin/` = **strictement l'admin Django technique** (superuser uniquement)
- `/backoffice/` = **panneau métier** pour les utilisateurs finaux

### Raisons
- Séparation claire entre technique (Django) et métier (vignoble)
- Interface métier adaptée aux besoins spécifiques
- Sécurité renforcée (pas d'accès technique aux utilisateurs métier)
- UX optimisée pour chaque contexte d'usage

### Impacts
- Migration de toutes les fonctionnalités métier hors de `/admin/`
- Création d'interfaces dédiées dans `/backoffice/`
- Permissions Django natives uniquement pour `/admin/`
- RBAC personnalisé pour `/backoffice/`

## 3. Structure des URLs

### Décision
**Web app (français accepté) :**
- `/catalogue/` - Gestion des produits, cuvées, lots
- `/clients/` - Gestion de la clientèle et CRM  
- `/ventes/` - Devis, commandes, facturation
- `/stocks/` - Gestion des stocks et logistique
- `/referentiels/` - Données de référence (cépages, parcelles, etc.)
- `/backoffice/` - Panneau d'administration métier

**API (anglais, versionnée) :**
- `/api/v1/` - API REST avec ressources au pluriel
- `/api/v1/products/`, `/api/v1/customers/`, `/api/v1/orders/`

**Option sécurité forte (à évaluer) :**
- Préfixe d'organisation : `/o/<org_slug>/catalogue/...`

### Raisons
- URLs françaises plus naturelles pour les utilisateurs finaux français
- API en anglais pour cohérence technique internationale
- Versioning API pour évolutions futures
- Préfixe org optionnel pour sécurité renforcée si nécessaire

### Impacts
- Refactoring complet des URLs actuelles
- Mise à jour de tous les templates et JS
- Redirections 301 pour rétro-compatibilité
- Namespaces Django par domaine métier

## 4. Rôles & Scopes (RBAC + Scopes)

### Décision
**Modèle hybride :**
- **Rôles** : définissent les responsabilités métier
- **Scopes** : définissent les périmètres de données (lecture/écriture par domaine)
- **Règle d'or** : deny by default + le plus restrictif gagne

### Raisons
- Flexibilité maximale pour les configurations complexes
- Séparation claire responsabilités vs périmètres
- Évolutivité pour nouveaux besoins
- Principe de sécurité par défaut

### Impacts
- Nouveau système de permissions personnalisé
- Middleware de vérification des scopes
- Interface d'administration des permissions
- Migration des permissions existantes

## 5. Conventions de nommage

### Décision
**CRUD web :**
- `/ressource/` (liste)
- `/ressource/nouveau/` (création)
- `/ressource/<id>/` (détail)
- `/ressource/<id>/modifier/` (édition)
- `/ressource/<id>/supprimer/` (suppression)

**API REST v1 :**
- `GET/POST /api/v1/ressource/`
- `GET/PATCH/DELETE /api/v1/ressource/<id>/`

**Namespaces :**
- `catalogue:`, `clients:`, `ventes:`, `stocks:`, `referentiels:`
- `backoffice:`, `apiv1:`

### Raisons
- Cohérence et prévisibilité
- Standards REST respectés
- Namespaces évitent les collisions
- Facilite la maintenance

### Impacts
- Standardisation de toutes les URLs
- Refactoring des noms d'URLs existants
- Mise à jour des références dans le code

## 6. Sécurité et authentification

### Décision
- **Authentification obligatoire** pour toutes les vues métier
- **Vérification des rôles et scopes** systématique
- **Logs d'accès** pour traçabilité
- **Middleware de sécurité** global

### Raisons
- Protection des données sensibles
- Conformité réglementaire
- Traçabilité des actions
- Détection d'anomalies

### Impacts
- Décorateurs de sécurité sur toutes les vues
- Système de logs centralisé
- Middleware de vérification automatique
- Tests de sécurité systématiques

## 7. Migration et rétro-compatibilité

### Décision
- **Redirections 301** pour toutes les anciennes URLs
- **Feature flags** pour activation progressive
- **Plan de rollback** systématique
- **Tests de non-régression** complets

### Raisons
- Éviter la casse des liens existants
- Migration progressive et sécurisée
- Possibilité de retour arrière
- Validation avant déploiement

### Impacts
- Table de mapping ancien/nouveau
- Système de feature flags
- Procédures de rollback
- Suite de tests étendue

## Validation requise

- [ ] **Tenancy par Organisation** - Validé
- [ ] **Séparation Admin/Backoffice** - Validé  
- [ ] **Structure URLs** - Validé
- [ ] **Rôles & Scopes** - Validé
- [ ] **Conventions nommage** - Validé
- [ ] **Sécurité** - Validé
- [ ] **Migration** - Validé

## Prochaines étapes

Une fois ce document validé :
1. Phase 1 : Inventaire des routes existantes
2. Phase 2 : Plan d'URL canonique
3. Phase 3 : Modèle de rôles (RBAC)
4. Phase 4 : Scopes par utilisateur
5. ... (selon planning défini)

---

**Document à valider avant tout développement. Aucun code ne sera écrit tant que ces décisions ne sont pas approuvées.**
