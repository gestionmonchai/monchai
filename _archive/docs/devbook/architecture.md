# Architecture - Mon Chai V1

## Vue d'ensemble

Mon Chai est une application Django monolithique avec séparation web/API pour la gestion d'exploitations agricoles.

### Stack technique
- **Backend** : Django 4.2.7
- **Base de données** : SQLite (dev), PostgreSQL (prod)
- **Authentification** : Django Sessions (session-based)
- **API** : Django REST Framework (SessionAuthentication)

## Conventions

### Structure des dossiers
```
monchai/
├── monchai/          # Configuration Django
├── apps/             # Applications métier
│   └── accounts/     # Authentification et organisations
├── docs/devbook/     # Documentation technique
├── templates/        # Templates Django
├── static/           # Fichiers statiques
└── media/            # Fichiers uploadés
```

### Conventions de nommage
- **Modèles** : PascalCase (User, Organization, Membership)
- **URLs** : snake_case avec namespaces (auth:login, api_auth:user_profile)
- **Vues** : PascalCase + suffixe (LoginView, UserAPIView)
- **Tables DB** : prefix app + snake_case (accounts_user, accounts_organization)

### Patterns utilisés
- **Custom User Model** : email comme USERNAME_FIELD
- **Membership Pattern** : relation User-Organization avec rôles
- **Guard Pattern** : vérification Membership actif obligatoire
- **Namespace URLs** : séparation web (/auth/*) et API (/api/auth/*)

## Technologies

### Core
- Django 4.2.7 avec Custom User Model
- python-decouple pour configuration
- django-extensions pour outils dev

### Authentification
- Django Sessions (invariant technique)
- CSRF protection activée
- Password validators standards

---

*Dernière mise à jour : 2025-09-19*
