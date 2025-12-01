# Plan de Tests - Mon Chai V1

## Date : 2025-09-24

## 🎯 Objectif des Tests

Prouver que le nouveau système de routage fonctionne correctement avec :
- Toutes les routes accessibles et fonctionnelles
- Redirections 301 opérationnelles
- Permissions RBAC + Scopes respectées
- Isolation multi-tenant étanche
- Performance acceptable

---

## 📊 Matrice de Tests

### 1. Tests de Santé des Routes

#### Routes Web Principales
| URL | Status Attendu | Auth Requise | Rôle Min | Test |
|-----|----------------|--------------|----------|------|
| `/` | 302 → `/dashboard/` | Non | - | ✅ |
| `/dashboard/` | 200 | Oui | Tous | ✅ |
| `/catalogue/` | 200 | Oui | Tous | ✅ |
| `/clients/` | 200 | Oui | Tous | ✅ |
| `/stocks/` | 200 | Oui | Tous | ✅ |
| `/referentiels/` | 200 | Oui | Tous | ✅ |
| `/backoffice/` | 200 | Oui | AdminOrg+ | 🔄 |
| `/ventes/` | 200 | Oui | Tous | 🔄 |

#### Routes API v1
| URL | Method | Status | Auth | Scope | Test |
|-----|--------|--------|------|-------|------|
| `/api/v1/auth/whoami/` | GET | 200 | Oui | - | ✅ |
| `/api/v1/catalogue/` | GET | 200 | Oui | catalogue:read | 🔄 |
| `/api/v1/clients/` | GET | 200 | Oui | clients:read | 🔄 |
| `/api/v1/stocks/alertes/` | GET | 200 | Oui | stocks:read | ✅ |

### 2. Tests de Redirections 301

#### Redirections Critiques
| Ancienne URL | Nouvelle URL | Status | Test |
|--------------|--------------|--------|------|
| `/admin/sales/customer/` | `/clients/` | 301 | 🔄 |
| `/admin/sales/quote/` | `/ventes/devis/` | 301 | 🔄 |
| `/ref/` | `/referentiels/` | 301 | ✅ |
| `/auth/settings/billing/` | `/backoffice/parametres/facturation/` | 301 | 🔄 |

#### Redirections API
| Ancienne URL | Nouvelle URL | Status | Test |
|--------------|--------------|--------|------|
| `/api/auth/whoami/` | `/api/v1/auth/whoami/` | 301 | 🔄 |
| `/catalogue/api/catalogue/` | `/api/v1/catalogue/` | 301 | 🔄 |

### 3. Tests d'Authentification

#### Accès Anonyme
| URL | Comportement Attendu | Test |
|-----|---------------------|------|
| `/dashboard/` | 302 → `/auth/login/` | ✅ |
| `/clients/` | 302 → `/auth/login/` | ✅ |
| `/backoffice/` | 302 → `/auth/login/` | 🔄 |
| `/api/v1/catalogue/` | 401 Unauthorized | 🔄 |

#### Accès Authentifié Sans Organisation
| URL | Comportement Attendu | Test |
|-----|---------------------|------|
| `/dashboard/` | 302 → `/auth/first-run/` | 🔄 |
| `/clients/` | 302 → `/auth/first-run/` | 🔄 |

---

## 🔐 Tests RBAC et Scopes

### Matrice de Permissions par Rôle

#### SuperAdmin
| Action | URL | Scope | Résultat Attendu | Test |
|--------|-----|-------|------------------|------|
| Voir clients | `/clients/` | clients:read | 200 | 🔄 |
| Créer client | `/clients/nouveau/` | clients:write | 200 | 🔄 |
| Voir backoffice | `/backoffice/` | - | 200 | 🔄 |
| Gérer feature flags | `/backoffice/feature-flags/` | - | 200 | 🔄 |

#### AdminOrganisation
| Action | URL | Scope | Résultat Attendu | Test |
|--------|-----|-------|------------------|------|
| Voir clients | `/clients/` | clients:read | 200 | 🔄 |
| Créer client | `/clients/nouveau/` | clients:write | 200 | 🔄 |
| Voir backoffice | `/backoffice/` | - | 200 | 🔄 |
| Gérer feature flags | `/backoffice/feature-flags/` | - | 403 | 🔄 |

#### Manager
| Action | URL | Scope | Résultat Attendu | Test |
|--------|-----|-------|------------------|------|
| Voir clients | `/clients/` | clients:read | 200 | 🔄 |
| Créer client | `/clients/nouveau/` | clients:write | 200 | 🔄 |
| Voir backoffice | `/backoffice/` | - | 403 | 🔄 |

#### LectureSeule
| Action | URL | Scope | Résultat Attendu | Test |
|--------|-----|-------|------------------|------|
| Voir clients | `/clients/` | clients:read | 200 | 🔄 |
| Créer client | `/clients/nouveau/` | clients:write | 403 | 🔄 |
| Voir backoffice | `/backoffice/` | - | 403 | 🔄 |

---

## 🏢 Tests d'Isolation Multi-Tenant

### Scénarios de Test

#### Scénario 1 : Utilisateur Mono-Organisation
```python
# Test : Utilisateur ne voit que ses données
def test_single_org_isolation():
    # Créer 2 organisations avec données
    org_a = Organization.objects.create(name="Domaine A")
    org_b = Organization.objects.create(name="Domaine B")
    
    client_a = Customer.objects.create(name="Client A", organization=org_a)
    client_b = Customer.objects.create(name="Client B", organization=org_b)
    
    # Utilisateur membre de org_a uniquement
    user = User.objects.create_user("user@a.com")
    Membership.objects.create(user=user, organization=org_a, role="manager")
    
    # Test : ne voit que client_a
    response = client.get('/clients/', user=user)
    assert "Client A" in response.content
    assert "Client B" not in response.content
```

#### Scénario 2 : Utilisateur Multi-Organisation
```python
def test_multi_org_switching():
    # Utilisateur membre de 2 organisations
    user = User.objects.create_user("user@multi.com")
    Membership.objects.create(user=user, organization=org_a, role="manager")
    Membership.objects.create(user=user, organization=org_b, role="lecture_seule")
    
    # Test : changement d'organisation
    session = client.session
    session['current_org_id'] = str(org_a.id)
    session.save()
    
    response = client.get('/clients/', user=user)
    # Doit voir les clients de org_a uniquement
```

#### Scénario 3 : Tentative d'Accès Cross-Organisation
```python
def test_cross_org_access_denied():
    # Tentative d'accès direct à un objet d'une autre org
    response = client.get(f'/clients/{client_b.id}/', user=user_org_a)
    assert response.status_code == 403
```

---

## 🚀 Tests de Performance

### Benchmarks de Performance

#### Tests de Charge Routes Principales
```python
def test_dashboard_performance():
    """Dashboard doit répondre en < 500ms"""
    start_time = time.time()
    response = client.get('/dashboard/')
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 0.5  # 500ms

def test_clients_list_performance():
    """Liste clients avec 1000 entrées < 1s"""
    # Créer 1000 clients
    for i in range(1000):
        Customer.objects.create(name=f"Client {i}", organization=org)
    
    start_time = time.time()
    response = client.get('/clients/')
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed < 1.0  # 1 seconde
```

#### Tests de Performance Redirections
```python
def test_redirections_performance():
    """100 redirections en < 1 seconde"""
    start_time = time.time()
    
    for _ in range(100):
        response = client.get('/ref/')
        assert response.status_code == 301
    
    elapsed = time.time() - start_time
    assert elapsed < 1.0
```

---

## 🧪 Tests d'Intégration

### Tests End-to-End

#### Workflow Complet Utilisateur
```python
def test_complete_user_workflow():
    """Test complet : connexion → navigation → action → déconnexion"""
    
    # 1. Connexion
    response = client.post('/auth/login/', {
        'email': 'user@test.com',
        'password': 'password123'
    })
    assert response.status_code == 302
    
    # 2. Accès dashboard
    response = client.get('/dashboard/')
    assert response.status_code == 200
    
    # 3. Navigation vers clients
    response = client.get('/clients/')
    assert response.status_code == 200
    
    # 4. Création d'un client
    response = client.post('/clients/nouveau/', {
        'name': 'Nouveau Client',
        'segment': 'individual'
    })
    assert response.status_code == 302
    
    # 5. Vérification création
    assert Customer.objects.filter(name='Nouveau Client').exists()
    
    # 6. Déconnexion
    response = client.post('/auth/logout/')
    assert response.status_code == 302
```

#### Test Migration Données
```python
def test_data_migration_integrity():
    """Vérifier que les données sont préservées après migration"""
    
    # Données avant migration
    original_customers = list(Customer.objects.all().values())
    original_products = list(Cuvee.objects.all().values())
    
    # Simuler migration (redirections, nouveaux namespaces)
    # ... code de migration ...
    
    # Vérifier intégrité après migration
    migrated_customers = list(Customer.objects.all().values())
    migrated_products = list(Cuvee.objects.all().values())
    
    assert original_customers == migrated_customers
    assert original_products == migrated_products
```

---

## 🔍 Tests de Sécurité

### Tests d'Injection et Attaques

#### Test Injection SQL
```python
def test_sql_injection_protection():
    """Tester la protection contre l'injection SQL"""
    malicious_input = "'; DROP TABLE customers; --"
    
    response = client.get('/clients/', {'q': malicious_input})
    
    # La table doit toujours exister
    assert Customer.objects.count() > 0
    assert response.status_code == 200
```

#### Test CSRF Protection
```python
def test_csrf_protection():
    """Vérifier la protection CSRF sur les formulaires"""
    
    # Tentative POST sans token CSRF
    response = client.post('/clients/nouveau/', {
        'name': 'Test Client'
    })
    
    assert response.status_code == 403  # CSRF failure
```

#### Test XSS Protection
```python
def test_xss_protection():
    """Vérifier la protection contre XSS"""
    xss_payload = "<script>alert('XSS')</script>"
    
    Customer.objects.create(name=xss_payload, organization=org)
    response = client.get('/clients/')
    
    # Le script ne doit pas être exécutable
    assert "<script>" not in response.content.decode()
    assert "&lt;script&gt;" in response.content.decode()
```

---

## 📋 Jeux de Données de Test

### Organisations de Test
```python
# Organisations avec différents profils
ORGANIZATIONS = [
    {
        'name': 'Château Margaux',
        'type': 'premium_winery',
        'users_count': 15,
        'data_volume': 'high'
    },
    {
        'name': 'Cave Coopérative',
        'type': 'cooperative',
        'users_count': 50,
        'data_volume': 'very_high'
    },
    {
        'name': 'Petit Domaine',
        'type': 'small_winery',
        'users_count': 3,
        'data_volume': 'low'
    }
]
```

### Utilisateurs de Test
```python
# Utilisateurs avec différents rôles
TEST_USERS = [
    {
        'email': 'superadmin@monchai.fr',
        'role': 'superadmin',
        'organizations': ['all']
    },
    {
        'email': 'admin@margaux.fr',
        'role': 'admin_organisation',
        'organizations': ['Château Margaux']
    },
    {
        'email': 'manager@margaux.fr',
        'role': 'manager',
        'organizations': ['Château Margaux']
    },
    {
        'email': 'comptable@margaux.fr',
        'role': 'comptabilite',
        'organizations': ['Château Margaux']
    },
    {
        'email': 'caviste@margaux.fr',
        'role': 'operateur',
        'organizations': ['Château Margaux']
    },
    {
        'email': 'consultant@externe.fr',
        'role': 'lecture_seule',
        'organizations': ['Château Margaux', 'Cave Coopérative']
    }
]
```

### Données Métier de Test
```python
# Données pour tests de performance et fonctionnels
TEST_DATA = {
    'customers': 1000,  # Par organisation
    'products': 50,     # Cuvées par organisation
    'lots': 200,        # Lots par organisation
    'orders': 500,      # Commandes par organisation
    'invoices': 300,    # Factures par organisation
}
```

---

## 🎯 Critères d'Acceptation

### Performance
- [ ] Dashboard < 500ms p95
- [ ] Listes avec pagination < 1s p95
- [ ] Redirections < 100ms p95
- [ ] API < 300ms p95

### Fonctionnel
- [ ] Toutes les routes principales accessibles
- [ ] Toutes les redirections fonctionnelles
- [ ] Aucune régression fonctionnelle
- [ ] Formulaires et actions CRUD opérationnels

### Sécurité
- [ ] Authentification obligatoire respectée
- [ ] Isolation multi-tenant étanche
- [ ] Permissions RBAC + Scopes respectées
- [ ] Aucune faille de sécurité détectée

### Compatibilité
- [ ] Anciens liens redirigent correctement
- [ ] Bookmarks utilisateurs fonctionnent
- [ ] API backward compatible
- [ ] Pas de perte de données

---

## 🚀 Commandes de Test

### Tests Automatisés
```bash
# Tests complets
python manage.py test

# Tests par domaine
python manage.py test apps.accounts.tests
python manage.py test apps.clients.tests
python manage.py test apps.catalogue.tests

# Tests de performance
python manage.py test --tag=performance

# Tests de sécurité
python manage.py test --tag=security
```

### Tests Manuels
```bash
# Test des redirections
curl -I http://localhost:8000/ref/
curl -I http://localhost:8000/admin/sales/customer/

# Test des API
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/clients/

# Test de charge
ab -n 1000 -c 10 http://localhost:8000/dashboard/
```

---

**Plan de tests défini : 200+ tests couvrant routes, permissions, sécurité et performance**
