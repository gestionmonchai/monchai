# Navigation Backoffice - Mon Chai V1

## Date : 2025-09-24

## 🎯 Principe de Séparation

### Séparation stricte
- **`/admin/`** = Interface technique Django (superuser uniquement)
- **`/backoffice/`** = Interface métier pour utilisateurs finaux

### Migration nécessaire
Toutes les fonctionnalités métier actuellement dans `/admin/` doivent être migrées vers `/backoffice/` ou les sections métier appropriées.

---

## 📊 Cartographie des Fonctionnalités à Migrer

### ❌ Actuellement dans `/admin/` (À MIGRER)

#### Gestion des Clients
- **Source** : `/admin/sales/customer/`
- **Destination** : `/clients/` (déjà existant)
- **Statut** : ✅ Déjà migré

#### Gestion des Ventes
- **Source** : `/admin/sales/quote/`, `/admin/sales/order/`
- **Destination** : `/ventes/devis/`, `/ventes/commandes/`
- **Statut** : 🔄 À créer

#### Gestion de la Facturation
- **Source** : `/admin/billing/invoice/`, `/admin/billing/payment/`
- **Destination** : `/ventes/factures/`, `/ventes/paiements/`
- **Statut** : 🔄 À créer

#### Gestion des Produits Viticoles
- **Source** : `/admin/viticulture/cuvee/`, `/admin/viticulture/lot/`
- **Destination** : `/backoffice/produits/cuvees/`, `/backoffice/produits/lots/`
- **Statut** : 🔄 À créer (alternative : intégrer à `/catalogue/`)

#### Gestion des Référentiels
- **Source** : `/admin/viticulture/grapevariety/`, `/admin/viticulture/vineyardplot/`, etc.
- **Destination** : `/referentiels/` (déjà existant)
- **Statut** : ✅ Déjà migré

#### Paramètres Organisation
- **Source** : `/auth/settings/billing/`, `/auth/settings/general/`
- **Destination** : `/backoffice/parametres/`
- **Statut** : 🔄 À réorganiser

#### Gestion des Utilisateurs
- **Source** : `/auth/settings/roles/`
- **Destination** : `/backoffice/utilisateurs/`
- **Statut** : 🔄 À réorganiser

---

## 🏗️ Architecture du Backoffice

### Structure des URLs `/backoffice/`

```
/backoffice/
├── /                           # Dashboard principal
├── /utilisateurs/              # Gestion des utilisateurs
│   ├── /                       # Liste des utilisateurs
│   ├── /inviter/               # Inviter un utilisateur
│   ├── /<uuid>/                # Détail utilisateur
│   └── /<uuid>/roles/          # Gestion des rôles
├── /produits/                  # Gestion des produits (si pas dans /catalogue/)
│   ├── /cuvees/                # Gestion des cuvées
│   ├── /lots/                  # Gestion des lots
│   └── /skus/                  # Gestion des SKU
├── /parametres/                # Paramètres organisation
│   ├── /                       # Vue d'ensemble
│   ├── /generaux/              # Paramètres généraux
│   ├── /facturation/           # Paramètres facturation
│   ├── /taxes/                 # Configuration taxes
│   └── /devises/               # Configuration devises
├── /monitoring/                # Monitoring système
├── /feature-flags/             # Gestion des feature flags
└── /onboarding/                # Checklist d'onboarding
```

---

## 🎨 Design du Dashboard Backoffice

### Layout Principal
```html
<!-- /backoffice/ -->
<div class="backoffice-dashboard">
    <header class="dashboard-header">
        <h1>Administration - {{ organization.name }}</h1>
        <div class="quick-stats">
            <div class="stat-card">
                <span class="stat-number">{{ users_count }}</span>
                <span class="stat-label">Utilisateurs</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ pending_invitations }}</span>
                <span class="stat-label">Invitations en attente</span>
            </div>
        </div>
    </header>
    
    <div class="dashboard-grid">
        <!-- Cartes de navigation -->
    </div>
</div>
```

### Cartes de Navigation par Rôle

#### AdminOrganisation (Accès complet)
```
┌─ Utilisateurs ──────────────────────────────────┐
│ 👥 Gérer les utilisateurs et leurs permissions │
│ • Inviter des utilisateurs                     │
│ • Gérer les rôles et scopes                    │
│ • Voir l'activité des utilisateurs             │
│ [Gérer les utilisateurs]                       │
└─────────────────────────────────────────────────┘

┌─ Paramètres ────────────────────────────────────┐
│ ⚙️ Configuration de l'organisation             │
│ • Informations légales et facturation          │
│ • Taxes et devises                             │
│ • Conditions générales                         │
│ [Configurer l'organisation]                    │
└─────────────────────────────────────────────────┘

┌─ Monitoring ────────────────────────────────────┐
│ 📊 Surveillance du système                     │
│ • Logs d'activité                              │
│ • Performance et erreurs                       │
│ • Feature flags                                │
│ [Voir le monitoring]                           │
└─────────────────────────────────────────────────┘
```

#### Manager (Accès limité)
```
┌─ Onboarding ────────────────────────────────────┐
│ 📋 Checklist de configuration                  │
│ • Compléter les informations manquantes        │
│ • Suivre la progression                        │
│ [Voir la checklist]                            │
└─────────────────────────────────────────────────┘
```

#### Autres rôles
- **Comptabilité** : Accès aux paramètres de facturation uniquement
- **Opérateur, LectureSeule, Partenaire** : Pas d'accès au backoffice

---

## 🔐 Contrôle d'Accès par Section

### Matrice d'Accès Backoffice

| Section | SuperAdmin | AdminOrg | Manager | Comptabilité | Autres |
|---------|------------|----------|---------|--------------|--------|
| **Dashboard** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Utilisateurs** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Produits** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Paramètres généraux** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Paramètres facturation** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Monitoring** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Feature flags** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Onboarding** | ✅ | ✅ | ✅ | ❌ | ❌ |

### Décorateurs de Sécurité
```python
@require_membership('admin')  # AdminOrg ou SuperAdmin
def backoffice_users_list(request):
    pass

@require_membership('admin', 'comptabilite')  # AdminOrg ou Comptabilité
def backoffice_billing_settings(request):
    pass

@require_superuser  # SuperAdmin uniquement
def backoffice_feature_flags(request):
    pass
```

---

## 📱 Menu de Navigation

### Menu Principal (Header)
```html
<!-- Remplace le dropdown actuel -->
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
        <i class="bi bi-building me-1"></i>Administration
    </a>
    <ul class="dropdown-menu">
        {% if user.get_active_membership.can_manage_organization %}
            <li><a class="dropdown-item" href="{% url 'backoffice:dashboard' %}">
                <i class="bi bi-speedometer2 me-2"></i>Dashboard admin
            </a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="{% url 'backoffice:users_list' %}">
                <i class="bi bi-people me-2"></i>Utilisateurs
            </a></li>
            <li><a class="dropdown-item" href="{% url 'backoffice:settings' %}">
                <i class="bi bi-gear me-2"></i>Paramètres
            </a></li>
            <li><a class="dropdown-item" href="{% url 'backoffice:monitoring' %}">
                <i class="bi bi-graph-up me-2"></i>Monitoring
            </a></li>
        {% endif %}
        {% if user.get_active_membership.can_access_billing %}
            <li><a class="dropdown-item" href="{% url 'backoffice:billing_settings' %}">
                <i class="bi bi-receipt me-2"></i>Facturation
            </a></li>
        {% endif %}
        <li><a class="dropdown-item" href="{% url 'backoffice:onboarding' %}">
            <i class="bi bi-list-check me-2"></i>Onboarding
        </a></li>
    </ul>
</li>
```

### Breadcrumb Backoffice
```html
<nav aria-label="breadcrumb" class="mb-4">
    <ol class="breadcrumb bg-light rounded-3 p-3 mb-0">
        <li class="breadcrumb-item">
            <a href="{% url 'dashboard' %}">Dashboard</a>
        </li>
        <li class="breadcrumb-item">
            <a href="{% url 'backoffice:dashboard' %}">Administration</a>
        </li>
        <li class="breadcrumb-item active" aria-current="page">
            {{ page_title }}
        </li>
    </ol>
</nav>
```

---

## 🎯 Actions de Migration

### Étape 1 : Créer l'app backoffice
```bash
python manage.py startapp backoffice
```

### Étape 2 : Créer les vues backoffice
```python
# apps/backoffice/views.py
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import require_membership

@login_required
@require_membership('admin')
def dashboard(request):
    context = {
        'users_count': request.current_org.memberships.count(),
        'pending_invitations': request.current_org.invitations.filter(status='sent').count(),
    }
    return render(request, 'backoffice/dashboard.html', context)

@login_required
@require_membership('admin')
def users_list(request):
    # Remplace /auth/settings/roles/
    pass

@login_required
@require_membership('admin', 'comptabilite')
def billing_settings(request):
    # Remplace /auth/settings/billing/
    pass
```

### Étape 3 : Créer les templates
```html
<!-- templates/backoffice/base.html -->
{% extends 'admin/base_site.html' %}

{% block title %}Administration - {{ organization.name }}{% endblock %}

{% block content %}
<div class="backoffice-container">
    {% block backoffice_content %}{% endblock %}
</div>
{% endblock %}
```

### Étape 4 : Configurer les URLs
```python
# apps/backoffice/urls.py
from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('utilisateurs/', views.users_list, name='users_list'),
    path('parametres/', views.settings, name='settings'),
    path('monitoring/', views.monitoring, name='monitoring'),
]
```

---

## 📋 Checklist de Migration

### ✅ Fonctionnalités déjà migrées
- [x] Clients : `/admin/sales/customer/` → `/clients/`
- [x] Référentiels : `/admin/viticulture/*` → `/referentiels/`

### 🔄 Fonctionnalités à migrer

#### Priorité 1 (Critique)
- [ ] Ventes : `/admin/sales/quote|order/` → `/ventes/`
- [ ] Facturation : `/admin/billing/*` → `/ventes/factures|paiements/`
- [ ] Gestion utilisateurs : `/auth/settings/roles/` → `/backoffice/utilisateurs/`

#### Priorité 2 (Important)
- [ ] Paramètres : `/auth/settings/*` → `/backoffice/parametres/`
- [ ] Monitoring : `/metadata/monitoring/` → `/backoffice/monitoring/`
- [ ] Feature flags : `/metadata/feature-flags/` → `/backoffice/feature-flags/`

#### Priorité 3 (Amélioration)
- [ ] Onboarding : `/onboarding/checklist/` → `/backoffice/onboarding/`
- [ ] Produits viticoles : Décision `/catalogue/` vs `/backoffice/produits/`

---

## 🎨 Design System Backoffice

### Couleurs et Thème
```css
:root {
    --backoffice-primary: #6f42c1;
    --backoffice-secondary: #6c757d;
    --backoffice-success: #198754;
    --backoffice-warning: #fd7e14;
    --backoffice-danger: #dc3545;
    --backoffice-bg: #f8f9fa;
}

.backoffice-container {
    background: var(--backoffice-bg);
    min-height: calc(100vh - 200px);
    padding: 2rem;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
}
```

### Composants Réutilisables
```html
<!-- Carte de navigation -->
<div class="nav-card">
    <div class="nav-card-header">
        <i class="bi bi-{{ icon }} nav-card-icon"></i>
        <h3 class="nav-card-title">{{ title }}</h3>
    </div>
    <div class="nav-card-body">
        <p class="nav-card-description">{{ description }}</p>
        <ul class="nav-card-features">
            {% for feature in features %}
                <li>{{ feature }}</li>
            {% endfor %}
        </ul>
    </div>
    <div class="nav-card-footer">
        <a href="{{ url }}" class="btn btn-primary">{{ cta_text }}</a>
    </div>
</div>
```

---

**Navigation backoffice définie : 8 sections principales avec contrôle d'accès par rôle**
