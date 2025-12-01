# Rôles & Accès - Sprint Auth & Identité

## But & portée de l'incrément

**Objectif** : Implémenter la gestion des rôles et permissions avec hiérarchie selon la roadmap 04_roles_acces.txt.

**Portée** :
- Hiérarchie des rôles avec décorateur require_membership(role_min)
- Interface de gestion des membres et rôles
- Système d'invitations avec tokens signés et flux A/B
- Protection anti-état invalide (toujours au moins un owner)
- Matrice d'autorisations par fonctionnalité

## Endpoints/URL

### Gestion des rôles
- `GET /settings/roles/` - Interface de gestion des membres (admin+)
- `GET/POST /settings/roles/invite/` - Formulaire d'invitation (admin+)
- `GET/POST /settings/roles/change/<id>/` - Changement de rôle (admin+)
- `GET/POST /settings/roles/deactivate/<id>/` - Désactivation membre (admin+)

### Invitations
- `GET /invite/accept/<token>/` - Acceptation d'invitation (public)

### Décorateur de protection
- `@require_membership()` - Membership actif requis
- `@require_membership('editor')` - Rôle editor minimum
- `@require_membership('admin')` - Rôle admin minimum
- `@require_membership('owner')` - Rôle owner uniquement

## Modèles/relations

### Membership (enrichi)
**Nouvelles méthodes** :
- `can_manage_roles()` - Vérifie si peut gérer les rôles (owner/admin)
- `can_invite_users()` - Vérifie si peut inviter des utilisateurs
- `can_edit_data()` - Vérifie si peut modifier les données métier
- `can_view_sensitive_data()` - Vérifie si peut voir les données sensibles
- `get_role_level()` - Retourne le niveau numérique du rôle

### Organization (enrichi)
**Nouvelles méthodes** :
- `get_active_members()` - Retourne tous les membres actifs
- `get_owners()` - Retourne tous les propriétaires actifs
- `has_multiple_owners()` - Vérifie s'il y a plusieurs propriétaires
- `can_remove_owner(membership)` - Vérifie si on peut retirer un owner

## Permissions/rôles

### Hiérarchie des rôles
- **Owner (4)** : Tous les droits, peut gérer tous les rôles
- **Admin (3)** : Peut gérer les membres, ne peut pas créer d'owner
- **Editor (2)** : Peut modifier les données métier
- **Read Only (1)** : Consultation uniquement

### Matrice d'autorisations
- **Gestion des membres** : owner, admin
- **Invitations** : owner, admin
- **CRUD données métier** : editor+ (owner/admin/editor)
- **Paramètres sensibles** : owner, admin
- **Lecture données** : read_only+ (tous)

### Protection anti-état invalide
- **Impossible** de supprimer le dernier owner
- **Impossible** de se désactiver soi-même
- **Vérification** avant chaque changement de rôle

## États UX/erreurs

### Interface de gestion
- **Statistiques** : Nombre de membres par rôle
- **Table interactive** : Actions selon les permissions
- **Badges colorés** : Rôles visuellement distincts
- **Protection visuelle** : Boutons désactivés si action interdite

### Messages utilisateur
- **Invitation envoyée** : "Invitation envoyée à {email} avec le rôle {rôle}"
- **Changement réussi** : "Rôle de {nom} changé de {ancien} vers {nouveau}"
- **Erreur protection** : "Impossible de retirer le dernier propriétaire"
- **Accès refusé** : "Cette action nécessite le rôle {rôle} minimum"

## Tests

### Tests implémentés (12 tests rôles)

**RolesAndPermissionsTestCase** :
- `test_read_only_cannot_access_roles_management` : READ_ONLY → 403
- `test_editor_cannot_access_roles_management` : EDITOR → 403
- `test_admin_can_access_roles_management` : ADMIN → 200
- `test_admin_can_invite_user` : Admin peut inviter
- `test_admin_cannot_create_owner` : Admin ne peut pas créer owner
- `test_owner_can_create_any_role` : Owner peut créer tous rôles
- `test_cannot_remove_last_owner` : Protection dernier owner
- `test_can_remove_owner_when_multiple_owners` : Suppression owner OK si multiple
- `test_deactivate_member_success` : Désactivation membre
- `test_cannot_deactivate_self` : Protection auto-désactivation
- `test_require_membership_decorator_hierarchy` : Test hiérarchie décorateur

### Total tests
- **29 tests passent** (17 auth/onboarding + 12 rôles/permissions)

### Commandes de test
```bash
python manage.py test apps.accounts.tests.RolesAndPermissionsTestCase -v 2
python manage.py test apps.accounts -v 1
```

## Formulaires

### InviteUserForm
- **Champs** : email (requis), role (choix limité selon rôle inviteur)
- **Validation** : Email valide, rôle autorisé
- **Restrictions** : Admin ne peut pas créer owner

### ChangeRoleForm
- **Champs** : role (choix limité selon rôle actuel)
- **Validation** : Protection anti-suppression dernier owner
- **Restrictions** : Selon hiérarchie des rôles

## Système d'invitations

### InvitationManager
- **Création token** : `create_invitation_token(email, org_id, role)`
- **Vérification** : `verify_invitation_token(token)` avec expiration
- **Email** : `send_invitation_email()` avec lien d'acceptation
- **Expiration** : 7 jours par défaut

### Flux A/B
- **Cas A (non connecté)** : Stockage en session → signup → création membership
- **Cas B (connecté)** : Vérification email → création membership immédiate

### Sécurité
- **Tokens signés** : Django Signer avec salt 'invitation_token'
- **Expiration** : Vérification timestamp dans payload
- **Email matching** : Vérification correspondance email

## Décorateurs

### require_membership(role_min)
- **Fonctionnalités** : Authentification + membership + hiérarchie rôles
- **Injection** : request.membership et request.current_org
- **Gestion erreurs** : Messages + HttpResponseForbidden
- **Compatibilité** : Avec et sans parenthèses

### Hiérarchie
- **Fonction** : `_has_required_role(user_role, required_role)`
- **Mapping** : String vers enum automatique
- **Comparaison** : Niveaux numériques (1-4)

---

**Date** : 2025-09-20  
**Sprint** : Auth & Identité  
**Statut** : Rôles & Accès complet ✅  
**Tests** : 29/29 passent ✅
