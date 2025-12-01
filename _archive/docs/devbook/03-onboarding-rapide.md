# Onboarding Rapide - Sprint Auth & Identité

## But & portée de l'incrément

**Objectif** : Implémenter l'onboarding rapide pour créer une exploitation à la première connexion selon la roadmap 03_onboarding_rapide.txt.

**Portée** :
- First-run guard complet avec redirection conditionnelle
- Formulaire de création d'exploitation (nom, SIRET, TVA, devise)
- Création automatique du Membership owner
- Décorateur de protection pour les vues métier
- Tests complets du flux d'onboarding

## Endpoints/URL

### Onboarding
- `GET /auth/first-run/` - First-run guard (redirection conditionnelle)
- `GET/POST /auth/first-run/org/` - Formulaire création exploitation

### Logique de redirection
- **Si Membership actif** : `/auth/first-run/` → `/dashboard/`
- **Si aucun Membership** : `/auth/first-run/` → `/auth/first-run/org/`
- **Après création exploitation** : `/auth/first-run/org/` → `/dashboard/`

## Modèles/relations

### Organization (modifié)
**Nouveau champ** :
- `is_initialized` (BooleanField) - Marque l'exploitation comme initialisée via onboarding

### Membership (inchangé)
- Création automatique avec `role=OWNER` et `is_active=True` lors de l'onboarding

### Migration
- `0002_organization_is_initialized.py` - Ajout du champ is_initialized

## Permissions/rôles

### First-run guard
- **Utilisateur non connecté** : Redirection vers login
- **Utilisateur connecté sans Membership** : Redirection vers création exploitation
- **Utilisateur connecté avec Membership** : Redirection vers dashboard

### Décorateur require_membership
- **@require_membership** : Protège les vues métier
- **Redirection automatique** vers `/auth/first-run/` si pas de Membership
- **Usage** : `@require_membership` sur les vues business

## États UX/erreurs

### Formulaire de création d'exploitation
- **Champs obligatoires** : Nom de l'exploitation
- **Champs optionnels** : SIRET (14 chiffres), Numéro TVA, Devise (défaut EUR)
- **Validation SIRET** : Exactement 14 chiffres si fourni
- **Message rassurant** : "Vous pourrez compléter ces paramètres plus tard"

### Messages utilisateur
- **Création réussie** : "Exploitation '{nom}' créée avec succès ! Vous êtes maintenant propriétaire"
- **Badge de session** : Mise à jour automatique avec "rôle: owner @ {org}"

## Tests

### Tests implémentés (6 tests onboarding)

**OnboardingTestCase** :
- `test_first_run_no_membership_redirects_to_org_creation` : First-run sans membership
- `test_create_organization_success` : Création exploitation complète
- `test_create_organization_minimal_data` : Création avec nom seulement
- `test_create_organization_invalid_siret` : Validation SIRET
- `test_first_run_with_existing_membership_redirects_dashboard` : First-run avec membership
- `test_require_membership_decorator` : Protection vues métier

### Tests mis à jour
- **AuthFlowTestCase** : Adaptation aux nouvelles redirections first-run
- **Total** : 17 tests passent (11 auth + 6 onboarding)

### Commandes de test
```bash
python manage.py test apps.accounts.tests.OnboardingTestCase -v 2
python manage.py test apps.accounts -v 1
```

## Formulaires

### OrganizationCreationForm
- **Héritage** : ModelForm basé sur Organization
- **Validation** : SIRET 14 chiffres si fourni
- **Méthode save()** : Crée Organization + Membership owner automatiquement
- **Champs optionnels** : SIRET et TVA non requis

### Widgets Bootstrap
- **Styling** : form-control, form-select pour cohérence UI
- **Placeholders** : Exemples pour guider l'utilisateur
- **Help text** : Messages d'aide pour chaque champ

## Décorateurs

### require_membership
- **Protection** : Vues métier nécessitant un Membership actif
- **Redirection** : Vers `/auth/first-run/` si pas de Membership
- **Compatibilité** : Fonctionne avec @login_required

### require_active_organization
- **Protection renforcée** : Vérifie aussi organization.is_initialized
- **Usage futur** : Pour vues nécessitant exploitation complètement configurée

## Configuration

### Paramètres par défaut
- **Devise** : EUR par défaut
- **is_initialized** : True lors de la création via onboarding
- **Membership** : role=OWNER, is_active=True automatiquement

### Référentiels futurs (roadmap)
- **Unités** : bouteille, L, hL (à implémenter plus tard)
- **Entrepôt** : 'Chai principal' (à implémenter plus tard)
- **TVA** : Taux par défaut 20% (à implémenter plus tard)

---

**Date** : 2025-09-19  
**Sprint** : Auth & Identité  
**Statut** : Onboarding rapide complet ✅  
**Tests** : 17/17 passent ✅
