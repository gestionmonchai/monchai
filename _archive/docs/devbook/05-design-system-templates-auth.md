# Design System & Templates Auth - Sprint UX/UI

## But & portée de l'incrément

**Objectif** : Cadrer la qualité UI/UX des écrans d'authentification avec un design system cohérent et accessible selon la roadmap 05_design_system_et_templates_auth.txt.

**Portée** :
- Composants de base réutilisables (FormGroup, SubmitButton, Banner, SessionBadge)
- Templates d'authentification refactorisés avec principes UX
- Validation HTML5 côté client
- Accessibilité WCAG 2.1 (contraste AA, ARIA, focus, tabulation)
- Tests de design system et d'accessibilité

## Principes UX incontournables

### Clarté > originalité
- Écrans d'auth prévisibles et familiers
- Un seul objectif par écran (login, signup, reset)
- Pas de distractions visuelles

### Feedback immédiat
- Erreurs inline sous chaque champ
- Messages globaux avec composant Banner
- Pas d'alertes modales pour erreurs de saisie
- États loading sur boutons d'action

### Langage utilisateur
- "Adresse e-mail" au lieu d'email
- "Mot de passe oublié" au lieu de reset
- Messages neutres et précis

## Composants du Design System

### 1. FormGroup
**Fichier** : `/templates/components/form_group.html`

**Fonctionnalités** :
- Label obligatoire avec indicateur requis (*)
- Input avec classes Bootstrap automatiques
- Help-text optionnel avec couleur atténuée
- Error-text inline avec role="alert"
- aria-describedby automatique si help-text ou erreur

**Usage** :
```django
{% include 'components/form_group.html' with field=form.email %}
{% include 'components/form_group.html' with field=form.password help_text="8 caractères minimum" %}
```

### 2. SubmitButton
**Fichier** : `/templates/components/submit_button.html`

**Fonctionnalités** :
- État loading avec spinner après POST
- Disabled si form invalide côté client (HTML5)
- Validation en temps réel
- Classes Bootstrap personnalisables

**Usage** :
```django
{% include 'components/submit_button.html' with text="Se connecter" %}
{% include 'components/submit_button.html' with text="Créer mon compte" class="btn-success" %}
```

### 3. Banner
**Fichier** : `/templates/components/banner.html`

**Fonctionnalités** :
- Types : success, error, info, warning
- Icônes Bootstrap Icons automatiques
- Rôles ARIA (role="status" pour success, role="alert" pour erreurs)
- Dismissible optionnel

**Usage** :
```django
{% include 'components/banner.html' with type="success" message="Compte créé avec succès !" %}
{% include 'components/banner.html' with type="error" message="Identifiants invalides" %}
```

### 4. SessionBadge
**Intégré dans** : `/templates/base.html`

**Fonctionnalités** :
- Display name + rôle + organisation
- Dropdown avec actions contextuelles
- Responsive (mobile/desktop)
- Icônes Bootstrap Icons

## Templates d'authentification

### Template de base : auth_base.html
**Conteneur auth** : 420-480px max, centré vertical/horizontal
**Hiérarchie** : H1 > labels > placeholder > help-text
**Responsive** : < 360px mobile-friendly

### Templates refactorisés
- `login.html` - Connexion avec invitation en session
- `signup.html` - Inscription avec contexte invitation
- `password_reset.html` - Demande de reset
- `password_reset_done.html` - Confirmation générique

### Grille & typographie
- **Titre H1** : 1.75rem, font-weight 600
- **Labels** : 0.9rem, font-weight 500, contraste AA
- **Inputs** : 1rem, padding 0.75rem, border-radius 8px
- **Help-text** : 0.85rem, couleur atténuée #718096

## Validation côté client

### HTML5 intégré
- `required` sur champs obligatoires
- `type="email"` pour validation email
- `minlength="8"` pour mots de passe
- `autocomplete` pour UX navigateur

### Attributs ajoutés aux formulaires
```python
# LoginForm
'required': True,
'autocomplete': 'email'
'autocomplete': 'current-password'

# SignupForm  
'required': True,
'minlength': '8',
'autocomplete': 'new-password'
```

### Validation en temps réel
- JavaScript intégré dans SubmitButton
- Bouton disabled si form invalide
- États visuels (outline vs solid)

## Accessibilité WCAG 2.1

### Focus visible
- Outline 2px solid #667eea sur tous contrôles
- Offset 2px pour lisibilité
- Styles CSS personnalisés

### Ordre de tabulation
- Logique : email → password → submit → liens secondaires
- Liens annexes après bouton principal (ordre DOM)

### ARIA et sémantique
- `aria-describedby` sur inputs avec help-text/erreurs
- `role="alert"` pour erreurs
- `role="status"` pour succès
- `aria-label="requis"` sur indicateurs *

### Contraste et typographie
- Contraste AA minimum respecté
- Tailles >= 14px (0.9rem = 14.4px)
- Couleurs testées avec checker

## États & transitions

### Login
- **Erreur** : conserver email, vider password
- **Succès** : redirect vers /auth/first-run/ (guard)
- **Invitation** : message discret "Votre compte rejoindra {org}"

### Signup
- **Succès** : connecté automatiquement puis guard
- **Invitation** : contexte visible avec rôle

### Reset
- **Demande** : message générique (sécurité)
- **Confirmation** : "Mot de passe mis à jour"

## Tests du Design System

### DesignSystemTestCase (18 tests)
**Fichier** : `/apps/accounts/test_design_system.py`

**Tests principaux** :
- `test_login_template_uses_auth_base` : Vérification template de base
- `test_form_fields_have_required_attributes` : HTML5 validation
- `test_form_labels_are_present` : Labels associés (for/id)
- `test_error_messages_are_inline` : Pas de modales
- `test_session_badge_in_header` : SessionBadge complet
- `test_banner_component_with_aria_roles` : Rôles ARIA
- `test_submit_button_loading_state` : États loading
- `test_password_reset_generic_message` : Sécurité messages

### AccessibilityTestCase
- `test_tabulation_order` : Ordre logique DOM
- `test_aria_describedby_attributes` : ARIA sur erreurs
- `test_required_field_indicators` : Indicateurs requis

### Commandes de test
```bash
python manage.py test apps.accounts.test_design_system -v 2
python manage.py test apps.accounts.test_design_system.DesignSystemTestCase -v 2
```

## Checklist revue UI (roadmap)

### ✅ Conformité roadmap
- [x] Labels présents, associés aux inputs (for/id)
- [x] Messages d'erreur utiles et concis, pas de stacktrace
- [x] Responsif OK < 360px (mobile)
- [x] États loading sur boutons d'action
- [x] Contraste AA, tailles de police >= 14px
- [x] Focus visible (outline) sur contrôles
- [x] Ordre tabulation logique
- [x] Rôles ARIA pour bannières
- [x] Validation HTML5 (required, type=email, minlength)

### Gestion erreurs fréquentes
- [x] {% csrf_token %} présent (évite page blanche POST)
- [x] Pas de preventDefault inutile sur forms
- [x] Messages Django intégrés avec Banner component

## Fichiers créés/modifiés

### Composants créés
- `/templates/components/form_group.html`
- `/templates/components/submit_button.html`
- `/templates/components/banner.html`
- `/templates/components/django_messages.html`
- `/templates/auth_base.html`

### Templates refactorisés
- `/templates/accounts/login.html`
- `/templates/accounts/signup.html`
- `/templates/accounts/password_reset.html`
- `/templates/accounts/password_reset_done.html`
- `/templates/base.html` (SessionBadge amélioré)

### Formulaires améliorés
- `/apps/accounts/forms.py` (validation HTML5)

### Tests ajoutés
- `/apps/accounts/test_design_system.py`

### Dépendances
- `django-widget-tweaks==1.5.0` ajouté
- `widget_tweaks` dans INSTALLED_APPS

---

**Date** : 2025-09-20  
**Sprint** : Design System & Templates Auth  
**Statut** : Design System complet ✅  
**Tests** : 18 tests design system ✅  
**Conformité roadmap** : 100% ✅
