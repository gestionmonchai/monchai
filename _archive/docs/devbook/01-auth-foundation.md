# Fondations Authentification - Sprint Auth & Identité

## But & portée de l'incrément

**Objectif** : Créer les fondations techniques pour le système d'authentification de Mon Chai selon la roadmap 01_auth_identite_overview.

**Portée** :
- Structure Django de base avec Custom User Model
- Modèles User, Organization, Membership respectant les invariants techniques
- Configuration auth session-based
- Chemins stables /auth/* et /api/auth/*

## Endpoints/URL

### Web (/auth/*)
- Structure préparée dans `apps/accounts/urls.py`
- À implémenter dans 02_auth_flow.txt :
  - `/auth/login/` - Connexion utilisateur
  - `/auth/signup/` - Inscription utilisateur  
  - `/auth/logout/` - Déconnexion
  - `/auth/password/reset/` - Reset mot de passe

### API (/api/auth/*)
- Structure préparée dans `apps/accounts/api_urls.py`
- À implémenter dans 02_auth_flow.txt :
  - `/api/auth/login/` - Connexion API
  - `/api/auth/logout/` - Déconnexion API
  - `/api/auth/user/` - Profil utilisateur

## Modèles/relations

### User (Custom User Model)
- **Champs** : email (USERNAME_FIELD), first_name, last_name, username
- **Méthodes** : full_name, get_active_membership(), has_active_membership()
- **Invariant** : email comme identifiant de connexion

### Organization
- **Champs** : name, siret (unique), tva_number, currency, timestamps
- **Validation** : SIRET 14 chiffres via RegexValidator
- **Relation** : 1-N avec Membership

### Membership
- **Champs** : user, organization, role, is_active, timestamps
- **Rôles** : owner, admin, editor, read_only
- **Contrainte** : unique_together sur (user, organization)
- **Index** : sur (user, is_active) et (organization, is_active)
- **Méthodes** : is_owner_or_admin(), can_edit(), can_invite()

## Permissions/rôles

### Hiérarchie des rôles
1. **owner** : Propriétaire (tous droits)
2. **admin** : Administrateur (gestion + invitation)
3. **editor** : Éditeur (modification données)
4. **read_only** : Lecture seule

### Permissions par rôle
- **Invitation** : owner, admin
- **Édition** : owner, admin, editor
- **Lecture** : tous les rôles

## États UX/erreurs

### Invariants techniques respectés
- ✅ Auth en session Django
- ✅ Chemins /auth/* et /api/auth/*
- ✅ User référencé par email
- ✅ Organization via Membership
- ✅ Vérification Membership actif

### Configuration
- LOGIN_URL = `/auth/login/`
- LOGIN_REDIRECT_URL = `/dashboard/`
- LOGOUT_REDIRECT_URL = `/auth/login/`
- Email backend console pour dev

## Tests

### Tests à implémenter
- `test_user_creation_with_email` : Création User avec email
- `test_organization_siret_validation` : Validation SIRET 14 chiffres
- `test_membership_active_check` : Vérification Membership actif
- `test_role_permissions` : Permissions par rôle
- `test_unique_user_organization` : Contrainte unique Membership

### Commandes de test
```bash
python manage.py test apps.accounts
python manage.py test apps.accounts.tests.test_models
```

## Migrations

### Commandes
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### Fichiers générés
- `0001_initial.py` : Création tables User, Organization, Membership
- Index sur Membership pour performance

---

**Date** : 2025-09-19  
**Sprint** : Auth & Identité  
**Statut** : Fondations créées ✅
