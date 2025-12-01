# Sprint 07 : Invitations, Tokens & Emails

## Vue d'ensemble

Implémentation complète du système d'invitations selon la roadmap 07. Ce sprint introduit la capacité pour les administrateurs d'inviter de nouveaux utilisateurs via email avec des tokens signés sécurisés.

## Architecture du système d'invitations

### Modèle Invitation

```python
class Invitation(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', 'Envoyée'
        ACCEPTED = 'accepted', 'Acceptée'
        EXPIRED = 'expired', 'Expirée'
        CANCELLED = 'cancelled', 'Annulée'
    
    email = models.EmailField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Membership.Role.choices)
    token = models.TextField()  # Token signé
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    accepted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Gestionnaire d'invitations (InvitationManager)

Le `InvitationManager` centralise toute la logique d'invitations :

- **Génération de tokens signés** : Utilise Django Signer avec salt spécifique
- **Validation de tokens** : Vérification signature + expiration
- **Création d'invitations complètes** : Enregistrement + email
- **Acceptation d'invitations** : Gestion des deux cas d'usage

### Stratégie d'acceptation selon roadmap 07

#### Cas 1 : Utilisateur non connecté
1. Clic sur lien d'invitation
2. Affichage page de confirmation
3. Acceptation → payload stocké en session
4. Redirection vers `/auth/signup/`
5. Création compte → membership automatique

#### Cas 2 : Utilisateur connecté
1. Clic sur lien d'invitation
2. Vérification email correspondant
3. Création immédiate du membership
4. Redirection vers tableau de bord

## Sécurité implémentée

### Tokens signés
- **Salt spécifique** : `'accounts.invite'`
- **Expiration** : 72 heures
- **Payload chiffré** : email, org_id, role, timestamps
- **Protection anti-tampering** : Signature Django

### Contrôles d'accès
- **Invitation** : Réservée aux admins+ (`@require_membership('admin')`)
- **Validation email** : Correspondance stricte pour utilisateurs connectés
- **Prévention doublons** : Une seule invitation active par email/organisation
- **Expiration automatique** : Nettoyage des invitations expirées

### Mesures anti-abus
- **Limitation temporelle** : 72h maximum
- **Validation côté serveur** : Tous les tokens vérifiés
- **Logs d'erreur** : Tentatives d'accès malveillant tracées
- **Session cleanup** : Nettoyage automatique après utilisation

## Templates d'email

### Structure des emails
- **Version texte** : `templates/emails/invitation_email.txt`
- **Version HTML** : `templates/emails/invitation_email.html`
- **Responsive design** : Compatible mobile/desktop
- **Branding cohérent** : Charte graphique Mon Chai

### Contenu des emails
- **Informations claires** : Nom organisation, rôle proposé
- **CTA évident** : Bouton "Accepter l'invitation"
- **Expiration visible** : Délai de 72h mis en avant
- **Instructions** : Création de compte si nécessaire

## Interface utilisateur

### Page de gestion des rôles améliorée
- **Section invitations** : Table des invitations en attente
- **Actions disponibles** : Renvoyer, annuler
- **Statistiques** : Compteur d'invitations actives
- **Filtrage** : Invitations expirées vs actives

### Formulaire d'invitation
- **Validation HTML5** : Email requis, rôle obligatoire
- **Limitation rôles** : Selon permissions utilisateur actuel
- **Feedback immédiat** : Messages de succès/erreur
- **Design system** : Composants réutilisables (FormGroup, SubmitButton)

### Page d'acceptation
- **Design centré** : Template auth_base.html
- **Informations claires** : Organisation, rôle, permissions
- **État utilisateur** : Connecté vs non connecté
- **Actions contextuelles** : Accepter ou annuler

## Tests implémentés

### Tests du modèle (InvitationModelTest)
- Création d'invitations
- Gestion des expirations
- Méthodes du modèle (can_be_accepted, mark_as_accepted)

### Tests du gestionnaire (InvitationManagerTest)
- Génération de tokens
- Validation de tokens
- Création d'invitations complètes
- Prévention des doublons

### Tests des vues (InvitationViewsTest)
- Formulaire d'invitation (GET/POST)
- Acceptation anonyme vs connectée
- Redirections appropriées
- Messages utilisateur

### Tests de sécurité (InvitationSecurityTest)
- Contrôles d'accès (admin requis)
- Protection anti-tampering
- Gestion des tokens expirés
- Validation des permissions

## URLs et routing

```python
# Invitations (Roadmap 07)
path('invite/accept/<str:token>/', views_invitations.accept_invitation, name='accept_invitation'),
path('invite/send/', views_invitations.send_invitation, name='send_invitation'),
path('invite/cancel/<int:invitation_id>/', views_invitations.cancel_invitation, name='cancel_invitation'),
path('invite/resend/<int:invitation_id>/', views_invitations.resend_invitation, name='resend_invitation'),
```

## Configuration email

### Développement
- **Backend** : Console (emails affichés en terminal)
- **Templates** : HTML + texte pour compatibilité
- **Debugging** : Logs détaillés des erreurs

### Production (future)
- **SMTP configuré** : Via settings Django
- **Templates optimisés** : Rendu serveur
- **Monitoring** : Échecs d'envoi tracés

## Intégration avec les sprints précédents

### Sprint 05 (Design System)
- **Composants réutilisés** : FormGroup, SubmitButton, Banner
- **Template auth_base** : Page d'acceptation cohérente
- **Validation HTML5** : Formulaires accessibles

### Sprint 06 (Routing & Middlewares)
- **Décorateurs** : `@require_membership('admin')`
- **Injection contexte** : `request.current_org`, `request.membership`
- **URLs stables** : Namespace `auth:` cohérent

## Métriques et performance

### Base de données
- **Index** : email + organization pour requêtes rapides
- **Cascade** : Suppression automatique si organisation supprimée
- **Optimisation** : Requêtes préparées pour listes

### Emails
- **Asynchrone** : Envoi non-bloquant (future amélioration)
- **Templates cachés** : Rendu optimisé
- **Fallback** : Version texte toujours disponible

## Checklist de conformité roadmap 07

- ✅ Modèle Invitation avec tous les champs requis
- ✅ Tokens signés avec expiration 72h
- ✅ Deux cas d'usage (connecté/non connecté) implémentés
- ✅ Templates d'email HTML + texte
- ✅ Page de gestion des rôles améliorée
- ✅ Sécurité admin+ pour invitations
- ✅ Tests complets (modèle, vues, sécurité)
- ✅ Prévention des doublons d'invitations
- ✅ Gestion des expirations automatique
- ✅ Interface utilisateur cohérente avec design system

## Améliorations futures

### Sprint 08+ (hors scope actuel)
- **Notifications en temps réel** : WebSocket pour invitations
- **Emails asynchrones** : Celery pour performance
- **Analytics** : Taux d'acceptation des invitations
- **Templates personnalisables** : Par organisation
- **Invitations en lot** : Import CSV d'utilisateurs
