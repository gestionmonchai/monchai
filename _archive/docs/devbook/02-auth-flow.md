# Auth Flow - Sprint Auth & Identité

## But & portée de l'incrément

**Objectif** : Implémenter le flux d'authentification complet (signup, login, logout, reset password) selon la roadmap 02_auth_flow.txt.

**Portée** :
- Vues d'authentification web avec formulaires Django
- Templates Bootstrap avec UX claire et erreurs inline
- Endpoints API avec SessionAuthentication
- First-run guard pour redirection vers onboarding
- Tests complets du flux d'authentification

## Endpoints/URL

### Web (/auth/*)
- `GET/POST /auth/login/` - Connexion avec email+password
- `GET/POST /auth/signup/` - Inscription avec champs optionnels
- `POST /auth/logout/` - Déconnexion avec redirection
- `GET/POST /auth/password/reset/` - Demande reset password
- `GET /auth/password/reset/done/` - Confirmation envoi email
- `GET/POST /auth/reset/<uidb64>/<token>/` - Saisie nouveau mot de passe
- `GET /auth/reset/complete/` - Confirmation reset terminé
- `GET /auth/first-run/` - First-run guard (onboarding)

### API (/api/auth/*)
- `POST /api/auth/session/` - Connexion API {email, password} → 200/401
- `GET /api/auth/whoami/` - Profil utilisateur avec org/rôle
- `POST /api/auth/logout/` - Déconnexion API → 204
- `GET /api/auth/csrf/` - Token CSRF pour clients JS

### Autres
- `GET /` - Redirection root vers login/dashboard
- `GET /dashboard/` - Dashboard placeholder

## Modèles/relations

**Aucune modification des modèles** - Utilisation des modèles créés dans le sprint 01.

**Formulaires ajoutés** :
- `LoginForm` - Connexion avec email (AuthenticationForm personnalisé)
- `SignupForm` - Inscription avec email, nom/prénom optionnels (UserCreationForm personnalisé)
- `PasswordResetRequestForm` - Demande reset sans révéler existence email

## Permissions/rôles

### Authentification
- **Pages publiques** : login, signup, password reset
- **Pages protégées** : first-run, dashboard (login_required)
- **API publique** : /session/, /csrf/
- **API protégée** : /whoami/, /logout/ (IsAuthenticated)

### First-run guard
- **Avec Membership actif** : redirection vers /dashboard/
- **Sans Membership** : affichage page onboarding (placeholder)

## États UX/erreurs

### Templates Bootstrap
- **Base template** : Navigation avec badge de session, messages Django
- **Formulaires** : Erreurs inline, validation côté client
- **Badge de session** : "Connecté : {nom} — rôle: {rôle} @ {org}" + bouton logout
- **Messages** : Success/error/info avec auto-dismiss

### Gestion des erreurs
- **Login échec** : "Email ou mot de passe incorrect" (sécurisé)
- **Reset password** : "Si un compte existe..." (ne révèle pas l'existence)
- **Validation formulaires** : Erreurs Django + Bootstrap styling
- **CSRF** : Protection activée sur tous les formulaires POST

## Tests

### Tests implémentés (11 tests)

**AuthFlowTestCase** :
- `test_signup_success_redirect_first_run` : Signup → redirection first-run
- `test_login_failure_shows_error_message` : Login échec → message erreur
- `test_login_success_redirect_first_run` : Login → redirection first-run
- `test_password_reset_sends_email_console` : Reset → email console
- `test_logout_destroys_session_shows_message` : Logout → session détruite
- `test_first_run_guard_no_membership` : First-run sans membership
- `test_first_run_guard_with_membership_redirects_dashboard` : First-run avec membership

**APIAuthTestCase** :
- `test_api_login_success` : API login réussi
- `test_api_login_failure` : API login échec
- `test_api_whoami_authenticated` : API whoami avec user connecté
- `test_api_logout` : API logout détruit session

### Commandes de test
```bash
python manage.py test apps.accounts
python manage.py test apps.accounts.tests.AuthFlowTestCase -v 2
python manage.py test apps.accounts.tests.APIAuthTestCase -v 2
```

## Configuration

### Settings ajoutés
- `LOGIN_REDIRECT_URL = '/auth/first-run/'` (first-run guard)
- `rest_framework` dans INSTALLED_APPS
- `REST_FRAMEWORK` config avec SessionAuthentication
- `djangorestframework==3.14.0` dans requirements.txt

### Email console
- Reset password utilise `send_mail()` avec console backend
- Email visible dans la console du serveur de développement

## Sécurité

### CSRF Protection
- `{% csrf_token %}` dans tous les formulaires POST
- API utilise SessionAuthentication (CSRF requis)
- Token CSRF disponible via `/api/auth/csrf/`

### Gestion des erreurs sécurisée
- Pas de révélation d'existence d'email dans reset password
- Messages d'erreur génériques pour login
- Validation côté serveur + côté client

---

**Date** : 2025-09-19  
**Sprint** : Auth & Identité  
**Statut** : Auth Flow complet ✅  
**Tests** : 11/11 passent ✅
