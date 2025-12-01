# Changelog - Mon Chai V1

## Format des entrées

- **Date** : YYYY-MM-DD
- **Incrément** : Nom/description de l'incrément
- **PR/Commit** : Référence technique
- **Portée** : Impact et périmètre

---

## Historique chronologique

### 2025-09-19 - Initialisation du projet

**Incrément** : Setup initial Dev Book
**PR/Commit** : Initial commit
**Portée** : 
- Création structure `/docs/devbook/`
- Mise en place README, architecture, decision-log, changelog
- Préparation pour développement selon roadmap

### 2025-09-19 - Fondations authentification

**Incrément** : Auth Foundation (roadmap 01_auth_identite_overview)
**PR/Commit** : auth-foundation-setup
**Portée** :
- Structure Django complète avec Custom User Model
- Modèles User, Organization, Membership avec invariants techniques
- Configuration session-based auth + chemins /auth/* et /api/auth/*
- Interface admin Django pour gestion des données
- Documentation architecture et décisions techniques
- Préparation pour implémentation auth flow (02_auth_flow.txt)

### 2025-09-19 - Auth Flow complet

**Incrément** : Auth Flow (roadmap 02_auth_flow.txt)
**PR/Commit** : auth-flow-implementation
**Portée** :
- Flux d'authentification complet : login, signup, logout, reset password
- Templates Bootstrap avec UX claire et erreurs inline
- Formulaires Django personnalisés (LoginForm, SignupForm, PasswordResetRequestForm)
- Vues d'authentification avec gestion des redirections
- Endpoints API avec SessionAuthentication (/api/auth/session/, /whoami/, /logout/)
- First-run guard pour redirection vers onboarding
- Badge de session dans header avec nom/rôle/organisation
- 11 tests couvrant tous les flux d'authentification
- Email console pour reset password en développement
- Sécurité CSRF et gestion d'erreurs sécurisée
- Dashboard placeholder en attendant modules métier

### 2025-09-19 - Onboarding rapide

**Incrément** : Onboarding Rapide (roadmap 03_onboarding_rapide.txt)
**PR/Commit** : onboarding-rapide-implementation
**Portée** :
- First-run guard complet avec redirection conditionnelle
- Formulaire de création d'exploitation (nom, SIRET, TVA, devise)
- Champ is_initialized ajouté au modèle Organization avec migration
- Création automatique du Membership owner lors de l'onboarding
- Décorateur require_membership pour protection des vues métier
- Template Bootstrap pour création d'exploitation avec UX claire
- 6 tests d'onboarding couvrant tous les cas de la roadmap
- Validation SIRET (14 chiffres) et gestion des champs optionnels
- Mise à jour des tests auth existants pour nouveau comportement
- Badge de session mis à jour automatiquement avec rôle owner

### 2025-09-20 - Rôles & Accès

**Incrément** : Rôles & Accès (roadmap 04_roles_acces.txt)
**PR/Commit** : roles-access-implementation
**Portée** :
- Hiérarchie des rôles avec décorateur require_membership(role_min)
- Interface de gestion des membres /settings/roles avec statistiques
- Système d'invitations avec tokens signés et expiration (7 jours)
- Flux A/B pour invitations (connecté/non connecté)
- Protection anti-état invalide (impossible supprimer dernier owner)
- Matrice d'autorisations par fonctionnalité
- Formulaires InviteUserForm et ChangeRoleForm avec restrictions
- Templates Bootstrap pour gestion des rôles avec actions contextuelles
- InvitationManager avec tokens signés Django Signer
- 12 tests de rôles et permissions couvrant tous les cas
- Méthodes utilitaires sur modeles Membership et Organization
- Intégration signup avec invitations en session

### 2025-09-20 - Design System & Templates Auth

**Incrément** : Design System & Templates Auth (roadmap 05_design_system_et_templates_auth.txt)
**PR/Commit** : design-system-auth-implementation
**Portée** :
- Composants réutilisables (FormGroup, SubmitButton, Banner, SessionBadge)
- Template de base auth_base.html avec design centré et responsive
- Templates d'authentification refactorisés selon principes UX
- Validation HTML5 côté client (required, type=email, minlength)
- Accessibilité WCAG 2.1 (ARIA, focus visible, tabulation logique)
- Messages d'erreur inline avec rôles ARIA appropriés
- États loading sur boutons avec spinner et validation temps réel
- SessionBadge amélioré avec dropdown contextuel et responsive
- Grille et typographie avec contraste AA minimum
- 18 tests de design system et d'accessibilité
- django-widget-tweaks intégré pour manipulation des widgets
- Checklist UI complète selon roadmap (labels, erreurs, responsive, loading)

### 2025-09-20 - Invitations, Tokens & Emails

**Incrément** : Invitations, Tokens & Emails (roadmap 07_invitations_tokens_emails.txt)
**PR/Commit** : invitations-tokens-emails-implementation
**Portée** :
- Modèle Invitation avec gestion complète du cycle de vie
- Système de tokens signés sécurisés (expiration 72h)
- InvitationManager pour centraliser la logique d'invitations
- Deux stratégies d'acceptation (utilisateur connecté/non connecté)
- Templates d'email HTML et texte pour invitations
- Formulaire d'invitation avec validation et sécurité
- Page d'acceptation d'invitation avec design cohérent
- Gestion des invitations dans la page des rôles
- Actions d'administration (renvoyer, annuler invitations)
- Tests complets (modèle, gestionnaire, vues, sécurité)

### 2025-09-20 - Routing, Middleware & Gardes d'accès

**Incrément** : Routing, Middleware & Gardes (roadmap 06_routing_middlewares_gardes.txt)
**PR/Commit** : routing-middleware-guards-implementation
**Portée** :
- Conventions d'URL stables (/auth/*, /api/auth/*, /dashboard/)
- Redirections de référence configurées (LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL)
- 3 middlewares personnalisés (CurrentOrganization, Security, OrganizationFilter)
- Current organization resolver avec fallback sur premier membership
- Injection automatique request.current_org et request.membership
- Headers de sécurité automatiques (X-Frame-Options, X-XSS-Protection, etc.)
- API whoami améliorée avec current_org_id et infos cohérentes
- Prévention erreurs classiques (boucles redirection, 404 API, CSRF 403)
- Nettoyage automatique session pour org_id invalides
- Décorateur require_membership amélioré avec injection contexte
- 18 tests de routing, guards, middlewares et sécurité
- Checklist technique complète selon roadmap (guards, CSRF, API cohérence)

### 2025-09-21 - Settings Billing (Coordonnées facturation, SIRET, TVA)

**Incrément** : Settings Billing (roadmap item 11)
**PR/Commit** : settings-billing-implementation
**Portée** :
- Modèle OrgBilling avec gestion informations légales, fiscales et facturation
- Signal automatique création billing pour nouvelles organisations
- Migration de données pour organisations existantes avec valeurs par défaut
- Formulaire OrgBillingForm avec validation robuste SIRET (14 chiffres), TVA française
- Vue /settings/billing/ avec require_membership admin et validation croisée
- Template responsive avec 4 sections et JavaScript affichage conditionnel TVA
- Intégration ChecklistService pour company_info et taxes
- 23 tests complets couvrant modèle, formulaire, vues, permissions, validation
- Validation SIRET française et TVA intracommunautaire avec nettoyage automatique
- UX cohérente avec composants design system et accessibilité WCAG 2.1

### 2025-09-21 - Settings General (Devise & Formats, CGV)

**Incrément** : Settings General (roadmap 12_settings_general.txt)
**PR/Commit** : settings-general-implementation
**Portée** :
- Modèle OrgSettings avec gestion devise, formats date/nombre, CGV
- Signal automatique création paramètres pour nouvelles organisations
- Migration de données pour organisations existantes avec valeurs par défaut
- Formulaire OrgSettingsForm avec validation robuste (PDF 5 Mo max, priorité fichier)
- Vue /settings/general/ avec require_membership admin et gestion fichiers
- Template responsive avec aperçu temps réel des formats via JavaScript
- Intégration ChecklistService pour currency_format et terms
- Extension ChecklistService avec nouvelles validations OrgSettings
- 17 tests complets couvrant modèle, formulaire, vue, intégration checklist
- Gestion upload PDF sécurisé avec nettoyage fichiers orphelins
- UX cohérente avec composants design system et accessibilité WCAG 2.1

### 2025-09-21 - Interface Navigation Settings

**Incrément** : Amélioration UX - Accès aux paramètres
**PR/Commit** : interface-navigation-settings
**Portée** :
- Menu "Paramètres" dans dropdown utilisateur (header navigation)
- Section avec icônes Bootstrap pour checklist, billing, general
- Permissions admin+ via can_manage_roles() pour visibilité menu
- Carte "Paramètres" sur dashboard avec boutons d'accès rapide
- Design cohérent réutilisant classes Bootstrap existantes
- Navigation intuitive remplaçant accès URL manuelle
- Responsive design mobile et desktop
- Documentation complète interface navigation

### 2025-09-21 - Référentiels (Cépages, Parcelles & Unités)

**Incrément** : Référentiels Cut #3 (roadmap items 14, 15, 16)
**PR/Commit** : referentiels-cepages-parcelles-unites
**Portée** :
- App referentiels avec 5 modèles complets (Cepage, Parcelle, Unite, Cuvee, Entrepot)
- CRUD complet /ref/cepages avec nom, code, couleur, notes
- CRUD complet /ref/parcelles avec nom, surface, lieu-dit, commune, appellation
- CRUD complet /ref/unites avec nom, symbole, type, facteur conversion
- Page d'accueil /ref/ avec statistiques et navigation
- Permissions graduées (read_only, editor, admin) avec décorateurs require_membership
- Templates responsive avec recherche, pagination, actions contextuelles
- Navigation intuitive : menu dropdown + carte dashboard pour tous utilisateurs
- 20 tests complets couvrant modèles, formulaires, vues, permissions
- Commande Django create_default_units pour données de test
- Contraintes unique_together par organisation pour isolation données
- Intégration design system Sprint 05 et middlewares Sprint 06

### 2025-09-22 - DB Roadmap 03 - Ventes, Clients & Pricing

**Incrément** : Système de ventes complet (roadmap db_roadmap_03_ventes_pricing.txt)
**PR/Commit** : db-roadmap-03-sales-pricing-implementation
**Portée** :
- App apps.sales avec 10 modèles complets (TaxCode, Customer, PriceList, PriceItem, Quote, Order, etc.)
- Gestionnaires métier PricingManager et SalesManager pour logique complexe
- Résolution prix intelligente avec grilles clients, seuils quantité et remises
- Gestion TVA française/européenne selon type client (pro/particulier, FR/UE)
- Workflow complet devis→commande avec réservations stock automatiques
- Intégration stock via StockReservation et mouvements lors expédition
- Interface admin complète avec inlines et recherche avancée
- 9 tests robustes couvrant tous cas métier et validation cross-organisation
- Commande create_sales_demo générant 5 clients, 3 grilles, 24 prix, devis et commandes
- Contraintes d'intégrité fortes et index de performance optimisés
- Documentation complète architecture et règles métier

### 2025-09-22 - DB Roadmap 04 - Facturation & Comptabilité

**Incrément** : Système de facturation et comptabilité complet (roadmap db_roadmap_04_facturation_compta.txt)
**PR/Commit** : db-roadmap-04-billing-accounting-implementation
**Portée** :
- App apps.billing avec 7 modèles complets (Invoice, Payment, GLEntry, AccountMap, etc.)
- Gestionnaires métier BillingManager et AccountingManager pour workflow facturation
- Numérotation séquentielle française (YYYY-NNNN, AV-YYYY-NNNN)
- Écritures comptables automatiques (411/707/4457) avec plan comptable paramétrable
- Lettrage intelligent multi-paiements/multi-factures avec gestion trop-perçu
- Avoirs avec écritures inverses et calculs proportionnels
- Arrondi bancaire ROUND_HALF_UP pour cohérence totaux
- Export comptable CSV/JSON paramétrables (journaux VEN/BAN/OD)
- Interface admin complète avec readonly écritures et indicateurs retards
- 15 tests robustes couvrant facturation, lettrage, comptabilité et arrondis
- Commande create_billing_demo générant plan comptable, factures, paiements et écritures
- Intégration complète avec modules Sales (commandes→factures) et Stock (traçabilité)
- Contraintes d'intégrité fortes et audit trail append-only

### 2025-09-23 - Roadmap 24 - Catalogue Grid & Navigation

**Incrément** : Catalogue des cuvées avec grille responsive et navigation intégrée (roadmap 24_catalogue_grid.txt)
**PR/Commit** : catalogue-grid-navigation-integration
**Portée** :
- App apps.catalogue intégrée dans INSTALLED_APPS et URLs principales
- Vue catalogue_home avec grille responsive, recherche avancée et filtres multiples
- Templates catalogue avec vue grille/tableau commutable et pagination
- Navigation intégrée : menu dropdown + cartes dashboard pour accès rapide
- Filtres avancés : couleur, classification, appellation, cépage, degré d'alcool, présence lots
- Tri intelligent multi-colonnes avec ordre par défaut selon type de champ
- Interface cohérente réutilisant design system Sprint 05
- Modèles Lot et MouvementLot pour gestion production viticole
- Permissions graduées read_only/editor/admin selon fonctionnalités
- Statistiques temps réel et facettes pour améliorer UX recherche
- Templates responsive avec cartes visuelles et tableaux détaillés
- Intégration complète avec référentiels existants (Cuvee, Entrepot, Unite)

---

*Dernière mise à jour : 2025-09-23*
