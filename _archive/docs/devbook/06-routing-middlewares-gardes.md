# Routing, Middleware & Gardes d'accès - Sprint Infrastructure

## But & portée de l'incrément

**Objectif** : Éviter 404/loops et sécuriser les écrans métier selon la roadmap 06_routing_middlewares_gardes.txt. Les développeurs doivent comprendre le cheminement utilisateur, les redirections, et la présence des "guards".

**Portée** :
- Conventions d'URL stables et cohérentes
- Redirections de référence configurées
- Middlewares personnalisés (CurrentOrganization, Security, OrganizationFilter)
- Prévention d'erreurs classiques (boucles, 404 API, CSRF)
- Mesures de sécurité intégrées
- Tests complets de routing et guards

## Conventions d'URL (stables)

### Web Auth
- `/auth/login/` - Connexion
- `/auth/logout/` - Déconnexion
- `/auth/signup/` - Inscription
- `/auth/password/reset/` - Demande de reset
- `/auth/reset/<uidb64>/<token>/` - Confirmation reset

### First-run Guard
- `/auth/first-run/` - Guard principal
- `/auth/first-run/org/` - Création d'organisation

### API (optionnel)
- `/api/auth/session/` - Login API
- `/api/auth/whoami/` - Informations utilisateur
- `/api/auth/logout/` - Logout API
- `/api/auth/csrf/` - Token CSRF

### Dashboard
- `/` ou `/dashboard/` - Placeholder suffisant

**⚠️ Rappel** : Ne pas mélanger `/accounts/` et `/auth/` si les includes pointent sur `/auth/`.

## Redirections de référence

### Settings configurés
```python
# monchai/settings.py
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/auth/first-run/'  # Guard
LOGOUT_REDIRECT_URL = '/auth/login/'
```

### Flux de redirection
1. **login** → **guard** → (has membership?) → **dashboard**
2. **signup** → **guard** → (idem)
3. **logout** → **login**

### Logique racine
```python
# monchai/urls.py
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return redirect('/auth/login/')
```

## Middlewares personnalisés

### 1. CurrentOrganizationMiddleware
**Fichier** : `/apps/accounts/middleware.py`

**Fonctionnalités** :
- Lit `current_org_id` de la session
- Fallback sur 1er membership actif
- Injecte `request.current_org` et `request.membership`
- Nettoyage automatique des org_id invalides

**Logique** :
```python
# 1. Vérifier current_org_id en session
# 2. Valider le membership pour cette org
# 3. Fallback sur get_active_membership()
# 4. Stocker en session pour optimisation
```

### 2. SecurityMiddleware
**Fonctionnalités** :
- Headers de sécurité automatiques
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- Reminder CSRF sur POST

### 3. OrganizationFilterMiddleware
**Statut** : Temporairement désactivé
**Objectif** : S'assurer que les données sont filtrées par organisation courante

## Décorateurs & Guards

### require_membership (amélioré)
```python
@require_membership  # Membership requis
@require_membership(Membership.Role.ADMIN)  # Rôle minimum
```

**Fonctionnalités** :
- Si user non authentifié → `LOGIN_URL`
- Si user sans Membership actif → `/auth/first-run/`
- Option `role_min` pour exiger admin/owner
- Injection `request.membership` et `request.current_org`

### login_required (Django standard)
Utilisé sur toutes les vues métier.

## API améliorée

### WhoAmI avec current_org
```python
# /api/auth/whoami/
{
    "email": "user@example.com",
    "full_name": "User Name",
    "current_org_id": 123,
    "organization": {
        "id": 123,
        "name": "Mon Exploitation",
        "siret": "12345678901234",
        "is_initialized": true
    },
    "role": {
        "code": "owner",
        "display": "Propriétaire",
        "level": 4
    }
}
```

Utilise le `current_org` du middleware pour cohérence.

## Prévention d'erreurs classiques

### 1. Boucles de redirection
**Problème** : `LOGIN_REDIRECT_URL` qui pointe vers une vue elle-même protégée.
**Solution** : Tests en navigation privée et avec user sans org.

### 2. 404 API
**Problème** : Appeler `/accounts/api/logout/` alors que routé `/api/auth/logout/`.
**Solution** : URLs cohérentes et tests de consistance.

### 3. CSRF 403
**Problème** : Endpoints POST sans `{% csrf_token %}` ou requêtes JS sans header.
**Solution** : Vérification systématique et headers automatiques.

### 4. URLconf order
**Solution** : Includes dans ordre logique, pas de catch-all avant routes auth.

## Mesures de sécurité

### Session requise
- Toujours exiger la session pour opérations sensibles (invites, settings)
- Validation membership pour accès données organisation

### CSRF activé partout
- Middleware CSRF activé
- Token form sur tous les formulaires
- Headers CSRF pour API

### Filtrage par organisation
- Pas de données d'organisation sans filtre `organization=current`
- Middleware pour vérification automatique (à réactiver)

### Logs d'accès
- Logs standard Django
- Messages sobres (pas de détails système aux utilisateurs)

## Tests complets

### RoutingConventionsTestCase (3 tests)
**Fichier** : `/apps/accounts/test_routing_guards.py`

**Tests principaux** :
- `test_auth_urls_respond` : Toutes routes répondent sans 404/500
- `test_api_urls_respond` : API endpoints cohérents
- `test_root_redirect_logic` : Logique redirection racine

### RedirectionTestCase (3 tests)
- `test_login_redirect_url` : LOGIN_REDIRECT_URL vers first-run
- `test_logout_redirect_url` : LOGOUT_REDIRECT_URL vers login
- `test_login_required_redirect` : @login_required vers LOGIN_URL

### GuardsTestCase (4 tests)
- `test_first_run_guard_for_user_without_org` : Guard fonctionne
- `test_require_membership_redirect` : Redirect vers first-run
- `test_membership_allows_access` : Membership permet accès
- `test_role_hierarchy_enforcement` : Hiérarchie des rôles

### SecurityTestCase (3 tests)
- `test_csrf_protection_on_forms` : CSRF sur formulaires
- `test_security_headers` : Headers sécurité présents
- `test_api_csrf_requirement` : API nécessite CSRF

### CurrentOrganizationMiddlewareTestCase (3 tests)
- `test_current_org_fallback_to_first_membership` : Fallback membership
- `test_current_org_from_session` : Respect session
- `test_invalid_org_id_in_session_cleanup` : Nettoyage invalides

### ErrorPreventionTestCase (2 tests)
- `test_no_redirect_loops` : Éviter boucles redirection
- `test_api_url_consistency` : URLs API cohérentes

### Commandes de test
```bash
python manage.py test apps.accounts.test_routing_guards -v 2
python manage.py test apps.accounts.test_routing_guards.GuardsTestCase -v 2
```

## Checklist technique (roadmap)

### ✅ Conformité roadmap
- [x] Toutes les routes listées répondent (GET) sans 500/404
- [x] Guard first-run fonctionne pour user sans org
- [x] Accès vue métier sans membership → redirect vers first-run
- [x] CSRF OK sur tous les formulaires POST
- [x] API whoami renvoie infos cohérentes avec session

### Erreurs prévenues
- [x] Boucles de redirection évitées
- [x] 404 API avec URLs cohérentes
- [x] CSRF 403 avec tokens et headers
- [x] URLconf order logique

### Sécurité implémentée
- [x] Session requise pour opérations sensibles
- [x] CSRF activé partout
- [x] Headers de sécurité automatiques
- [x] Filtres par organisation (décorateur)

## Architecture middleware

### Ordre des middlewares
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middlewares (roadmap 06)
    'apps.accounts.middleware.CurrentOrganizationMiddleware',
    'apps.accounts.middleware.SecurityMiddleware',
    # 'apps.accounts.middleware.OrganizationFilterMiddleware',  # Désactivé
]
```

### Injection de contexte
- `request.current_org` : Organisation courante
- `request.membership` : Membership actif
- Headers de sécurité automatiques
- Nettoyage session automatique

## Fichiers créés/modifiés

### Middlewares créés
- `/apps/accounts/middleware.py` (3 middlewares)

### API améliorée
- `/apps/accounts/api_views.py` (WhoAmI avec current_org)

### Tests ajoutés
- `/apps/accounts/test_routing_guards.py` (18 tests)

### Configuration
- `/monchai/settings.py` (middlewares ajoutés)

### URLs vérifiées
- `/monchai/urls.py` (logique racine)
- `/apps/accounts/urls.py` (conventions stables)
- `/apps/accounts/api_urls.py` (API cohérente)

---

**Date** : 2025-09-20  
**Sprint** : Routing, Middleware & Gardes d'accès  
**Statut** : Infrastructure routing complète ✅  
**Tests** : 18 tests routing et guards ✅  
**Conformité roadmap** : 100% ✅
