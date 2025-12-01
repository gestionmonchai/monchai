# Decision Log - Mon Chai V1

## Format des entrées

Chaque décision suit le format :
- **Date** : YYYY-MM-DD
- **Décision** : Titre concis
- **Contexte** : Situation qui nécessite la décision
- **Alternatives** : Options considérées
- **Décision** : Choix retenu
- **Raison** : Justification du choix

---

## Historique des décisions

### 2025-09-19 - Initialisation du Dev Book

**Contexte** : Mise en place de la structure de documentation selon le prompt d'entrée

**Alternatives** :
- Documentation inline dans le code
- Wiki externe
- Structure Dev Book dédiée

**Décision** : Structure Dev Book sous `/docs/devbook/`

**Raison** : Conformité stricte au prompt d'entrée, centralisation de la documentation technique, traçabilité des décisions

### 2025-09-19 - Custom User Model avec email

**Contexte** : Invariant technique "User référencé par email" dans roadmap 01

**Alternatives** :
- User Django standard avec username
- Custom User avec username=email
- Custom User avec USERNAME_FIELD=email

**Décision** : Custom User avec USERNAME_FIELD=email

**Raison** : Respect strict invariant roadmap, meilleure UX (connexion par email), évite duplication username/email

### 2025-09-19 - Structure apps/ pour organisation

**Contexte** : Organisation du code Django pour scalabilité

**Alternatives** :
- Apps dans racine projet
- Apps sous dossier apps/
- Apps sous dossier src/

**Décision** : Apps sous dossier apps/

**Raison** : Séparation claire config/apps, facilite navigation, pattern Django courant pour projets moyens/grands

### 2025-09-19 - Bootstrap pour UI et UX

**Contexte** : Choix du framework CSS pour les templates d'authentification

**Alternatives** :
- CSS custom from scratch
- Tailwind CSS
- Bootstrap 5
- Bulma CSS

**Décision** : Bootstrap 5 via CDN

**Raison** : Rapidité de développement, composants prêts, responsive par défaut, documentation excellente, compatible Django messages

### 2025-09-19 - LOGIN_REDIRECT_URL vers first-run

**Contexte** : Redirection après connexion selon roadmap (first-run guard)

**Alternatives** :
- Redirection directe vers dashboard
- Redirection vers first-run guard
- Redirection conditionnelle dans la vue

**Décision** : LOGIN_REDIRECT_URL = '/auth/first-run/'

**Raison** : Respect roadmap, centralise la logique onboarding, permet gérer cas sans organisation

### 2025-09-19 - Champ is_initialized pour Organization

**Contexte** : Marquer les exploitations créées via onboarding selon roadmap 03

**Alternatives** :
- Flag dans Membership
- Champ status avec enum
- Champ boolean is_initialized
- Pas de marquage

**Décision** : Champ boolean is_initialized sur Organization

**Raison** : Simple, clair, permet distinguer exploitations complètes vs partielles, extensible pour futures validations

### 2025-09-19 - Décorateur require_membership

**Contexte** : Protection des vues métier selon roadmap (anti-état invalide)

**Alternatives** :
- Vérification manuelle dans chaque vue
- Middleware global
- Décorateur réutilisable
- Mixin pour class-based views

**Décision** : Décorateur require_membership

**Raison** : Réutilisable, explicite, compatible function/class views, redirection automatique vers first-run

### 2025-09-20 - Hiérarchie des rôles avec niveaux numériques

**Contexte** : Implémentation de la hiérarchie owner > admin > editor > read_only

**Alternatives** :
- Comparaison par strings
- Enum avec ordre
- Niveaux numériques (1-4)
- Permissions Django natives

**Décision** : Niveaux numériques avec mapping

**Raison** : Simple à comparer, extensible, performant, compatible avec décorateur role_min

### 2025-09-20 - Tokens signés pour invitations

**Contexte** : Sécurisation du système d'invitations selon roadmap

**Alternatives** :
- UUID en base de données
- JWT avec clé secrète
- Django Signer avec salt
- Hash simple

**Décision** : Django Signer avec salt 'invitation_token'

**Raison** : Intégré Django, sécurisé, pas de stockage requis, expiration intégrée

### 2025-09-20 - Composants réutilisables vs templates monolithiques

**Contexte** : Structuration du design system pour les templates d'authentification

**Alternatives** :
- Templates monolithiques avec duplication
- Composants réutilisables avec includes
- Template tags personnalisés
- Mixins de vues avec logique partagée

**Décision** : Composants réutilisables avec includes Django

**Raison** : Maintenabilité, réutilisabilité, séparation des responsabilités, testabilité

### 2025-09-20 - Template de base auth_base.html vs extension de base.html

**Contexte** : Templates d'authentification avec design spécifique centré

**Alternatives** :
- Extension de base.html avec blocks
- Template dédié auth_base.html
- CSS conditionnel dans base.html
- Pages SPA avec API

**Décision** : Template dédié auth_base.html

**Raison** : Séparation claire, design centré spécifique, pas de pollution de base.html

### 2025-09-20 - Middlewares personnalisés vs décorateurs uniquement

**Contexte** : Gestion de l'organisation courante et sécurité globale

**Alternatives** :
- Décorateurs uniquement sur chaque vue
- Middlewares globaux pour injection de contexte
- Mixins de vues avec logique partagée
- Context processors Django

**Décision** : Middlewares personnalisés (CurrentOrganization, Security)

**Raison** : Injection automatique, pas de duplication, sécurité globale, optimisation session

### 2025-09-20 - OrganizationFilterMiddleware actif vs désactivé

**Contexte** : Prévention d'accès aux données sans filtre organisation

**Alternatives** :
- Middleware actif avec vérifications strictes
- Décorateurs require_membership suffisants
- Validation dans les vues métier
- ORM avec filtres automatiques

**Décision** : Middleware temporairement désactivé, décorateurs suffisants

**Raison** : Éviter interférences routing, décorateurs plus précis, tests plus simples

### 2025-09-20 - Modèle Invitation vs Extension User

**Contexte** : Système d'invitations selon roadmap 07, choix architecture

**Alternatives** :
- Extension User avec champs invitation
- Système de flags sur User
- Modèle Invitation séparé
- Table de liaison temporaire

**Décision** : Modèle Invitation séparé avec cycle de vie complet

**Raison** : Séparation claire responsabilités, historique invitations, gestion expirations simplifiée, pas de pollution modèle User

### 2025-09-20 - Tokens signés vs UUID simples

**Contexte** : Sécurisation liens d'invitation selon roadmap 07

**Alternatives** :
- UUID simples en base
- JWT tokens
- Tokens custom
- Django Signer avec payload

**Décision** : Django Signer avec payload chiffré et salt spécifique

**Raison** : Sécurité renforcée anti-tampering, payload intégré (pas requête DB), expiration native, salt spécifique

### 2025-09-20 - Stratégie double acceptation

**Contexte** : Gestion utilisateurs connectés vs non connectés selon roadmap 07

**Alternatives** :
- Forcer déconnexion pour tous
- Un seul flux via signup
- Deux flux distincts selon état
- Modal de choix utilisateur

**Décision** : Deux flux distincts selon état utilisateur (connecté/non connecté)

**Raison** : UX optimale (pas déconnexion forcée), conformité roadmap 07, simplicité implémentation

### 2025-09-20 - Templates d'email HTML + texte

**Contexte** : Format emails d'invitation selon roadmap 07

**Alternatives** :
- HTML seulement
- Texte seulement
- Service email tiers
- Templates Django mixtes

**Décision** : EmailMultiAlternatives avec versions HTML et texte

**Raison** : Compatibilité maximale clients email, fallback texte, branding cohérent, contrôle total rendu

### 2025-09-21 - PostgreSQL avec extensions pour recherche avancée

**Contexte** : Implémentation roadmap meta base de données - Phase P0/P2

**Alternatives** :
- Elasticsearch externe pour recherche
- SQLite avec FTS5
- PostgreSQL standard
- PostgreSQL avec extensions (unaccent, pg_trgm, pgvector)

**Décision** : PostgreSQL 15+ avec extensions unaccent, pg_trgm, et pgvector (optionnel)

**Raison** : Intégration native Django, recherche tolérante aux fautes, support multi-langue, performance, pas de service externe

### 2025-09-21 - Métamodèle pour gouvernance des données

**Contexte** : Roadmap P1 - Schéma "meta" & gouvernance des données

**Alternatives** :
- Hardcoder configuration recherche dans le code
- Fichiers YAML de configuration
- Métamodèle en base de données
- Django ContentTypes uniquement

**Décision** : Métamodèle complet avec tables meta_entity, meta_attribute, meta_relation

**Raison** : Flexibilité runtime, gouvernance centralisée, configuration par interface, évolutivité

### 2025-09-21 - UUIDs vs BigSerial pour clés primaires

**Contexte** : Charte de nommage roadmap P0 - choix des identifiants

**Alternatives** :
- BigSerial (entiers auto-incrémentés)
- UUID v4 (aléatoires)
- UUID v7 (time-ordered)
- Clés composites

**Décision** : UUIDs v7 pour nouvelles entités, BigSerial pour compatibilité existante

**Raison** : Pas de collision multi-instance, tri chronologique, sécurité (pas d'énumération), distribution

### 2025-09-21 - API unifiée /api/search/ vs endpoints spécialisés

**Contexte** : Roadmap P3 - API & Query Builder pour tri/filtre/recherche

**Alternatives** :
- Endpoints REST par entité (/api/cuvees/, /api/lots/)
- GraphQL avec résolveurs
- API unifiée /api/search/ multi-entités
- Vues Django avec AJAX

**Décision** : API unifiée /api/search/ avec Query Builder sécurisé

**Raison** : Interface cohérente, réutilisabilité, sécurité centralisée, facettes cross-entités

---

*Dernière mise à jour : 2025-09-21*
