# Architecture Clients - Séparation Ventes / Référentiels

## 📋 Diagnostic Actuel

### Problème Identifié
Le système actuel présente une **confusion d'URLs et de responsabilités** entre deux contextes métier distincts :
- **Ventes** : opérationnel (devis → commandes → factures)
- **Référentiels/CRM** : master data + relationnel (fiche riche, relances, tags, timeline)

### État des Lieux URLs

#### URLs Actuelles
```
/ventes/clients/                    → ventes:clients_dashboard (liste ventes)
/referentiels/clients/              → clients:customers_list (liste CRM)
/referentiels/clients/<uuid>/       → clients:customer_detail (fiche CRM)
/referentiels/clients/<uuid>/modifier/ → clients:customer_edit
```

#### Problèmes Constatés
1. **Namespace ambigu** : `clients:` utilisé partout (ventes + référentiels)
2. **Pas de fiche ventes dédiée** : `/ventes/clients/<id>/` n'existe pas
3. **Templates partagent `clients:customer_detail`** : confusion entre contextes
4. **Redirections middleware** : admin → `/referentiels/clients/` (hardcodé)

---

## 🎯 Architecture Cible

### Principe : 1 Modèle, 2 Workbenches

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer (modèle unique)                  │
│         apps/clients/models.py - Données centralisées        │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐      ┌──────▼───────┐
        │  VENTES        │      │ RÉFÉRENTIELS │
        │  (Opérationnel)│      │    (CRM)     │
        └────────────────┘      └──────────────┘
```

### Séparation Fonctionnelle

#### A) Workbench VENTES (Opérationnel)
**Objectif** : Exécution commerciale rapide

**URLs** :
```
/ventes/clients/                      → ventes:clients_list
/ventes/clients/<code>/               → ventes:client_detail
/ventes/clients/<code>/devis/         → ventes:client_quotes
/ventes/clients/<code>/commandes/     → ventes:client_orders
/ventes/clients/<code>/factures/      → ventes:client_invoices
```

**Vue** : Focus documents commerciaux
- Liste : CA, encours, dernière commande, statut facturation
- Fiche : Onglets Devis / Commandes / Factures / Paiements
- Actions : Créer devis, Voir encours, Relancer paiement

**Template** : `ventes/client_detail.html`

---

#### B) Workbench RÉFÉRENTIELS (CRM/Master Data)
**Objectif** : Gestion relationnelle et qualité données

**URLs** :
```
/referentiels/clients/                → referentiels:clients_list
/referentiels/clients/<code>/         → referentiels:client_detail
/referentiels/clients/<code>/contacts/→ referentiels:client_contacts
/referentiels/clients/<code>/relances/→ referentiels:client_followups
/referentiels/clients/<code>/notes/   → referentiels:client_notes
```

**Vue** : Focus master data + CRM
- Liste : Segments, tags, qualité data, dernière interaction
- Fiche : Onglets Identité / Commercial / Logistique / Performance / Conformité
- Actions : Gérer tags, Ajouter note, Planifier relance, Exporter fiche

**Template** : `clients/customer_detail_modern.html` (existant)

---

## 🔧 Plan d'Implémentation

### Phase 1 : Créer Workbench Ventes (PRIORITÉ)

#### 1.1 Créer `apps/ventes/views_clients_detail.py`
```python
@login_required
@require_membership('read_only')
def client_detail_ventes(request, code):
    """Fiche client orientée ventes (devis/commandes/factures)"""
    organization = request.current_org
    customer = get_object_or_404(Customer, code=code, organization=organization)
    
    # Récupérer documents commerciaux
    quotes = Quote.objects.filter(customer=customer).order_by('-created_at')[:10]
    orders = Order.objects.filter(customer=customer).order_by('-created_at')[:10]
    invoices = Invoice.objects.filter(customer=customer).order_by('-created_at')[:10]
    
    # KPIs ventes
    ca_12m = calculate_ca_12m(customer)
    encours = calculate_encours(customer)
    
    context = {
        'customer': customer,
        'quotes': quotes,
        'orders': orders,
        'invoices': invoices,
        'ca_12m': ca_12m,
        'encours': encours,
    }
    return render(request, 'ventes/client_detail.html', context)
```

#### 1.2 Ajouter Routes dans `apps/commerce/urls_ventes.py`
```python
# Clients (workbench ventes)
path('clients/', ventes_clients_views.clients_dashboard, name='clients_list'),
path('clients/<str:code>/', ventes_clients_views.client_detail_ventes, name='client_detail'),
path('clients/<str:code>/devis/', ventes_clients_views.client_quotes, name='client_quotes'),
path('clients/<str:code>/commandes/', ventes_clients_views.client_orders, name='client_orders'),
path('clients/<str:code>/factures/', ventes_clients_views.client_invoices, name='client_invoices'),
```

#### 1.3 Créer Template `templates/ventes/client_detail.html`
- Layout simple avec onglets Documents
- Focus CA, encours, paiements
- Boutons actions : Créer devis, Voir factures

---

### Phase 2 : Renforcer Workbench Référentiels

#### 2.1 Renommer Namespace dans `apps/clients/urls.py`
```python
# AVANT
app_name = 'clients'

# APRÈS
app_name = 'referentiels'  # ou créer alias
```

#### 2.2 Ajouter Routes CRM Manquantes
```python
path('<str:code>/contacts/', views.client_contacts, name='client_contacts'),
path('<str:code>/relances/', views.client_followups, name='client_followups'),
path('<str:code>/notes/', views.client_notes, name='client_notes'),
path('<str:code>/timeline/', views.client_timeline, name='client_timeline'),
```

#### 2.3 Enrichir Template Existant
- Ajouter onglet "Relances"
- Ajouter onglet "Notes CRM"
- Ajouter onglet "Timeline"

---

### Phase 3 : Nettoyer Redirections et Ambiguïtés

#### 3.1 Supprimer Redirections Middleware
```python
# apps/core/middleware.py - SUPPRIMER BLOC
# Redirection ciblée: admin sales customer vers clients
if path == '/admin/sales/customer/':
    return HttpResponsePermanentRedirect('/referentiels/clients/')
```

#### 3.2 Fixer Templates avec Namespace Explicite
```django
{# AVANT - AMBIGU #}
{% url 'customer_detail' customer.id %}

{# APRÈS - EXPLICITE #}
{% url 'ventes:client_detail' customer.code %}  {# Contexte ventes #}
{% url 'referentiels:client_detail' customer.code %}  {# Contexte CRM #}
```

#### 3.3 Ajouter Cross-Links Entre Workbenches
Dans chaque fiche, bouton clair :
```html
<!-- Dans ventes/client_detail.html -->
<a href="{% url 'referentiels:client_detail' customer.code %}" class="btn btn-outline-secondary">
    <i class="bi bi-database"></i> Voir fiche CRM complète
</a>

<!-- Dans clients/customer_detail_modern.html -->
<a href="{% url 'ventes:client_detail' customer.code %}" class="btn btn-outline-primary">
    <i class="bi bi-cart"></i> Voir documents commerciaux
</a>
```

---

## 📊 Matrice de Décision

| Action Utilisateur | Contexte | URL Cible |
|-------------------|----------|-----------|
| Créer devis | Ventes | `/ventes/clients/<code>/` |
| Voir CA client | Ventes | `/ventes/clients/<code>/` |
| Gérer tags | Référentiels | `/referentiels/clients/<code>/` |
| Ajouter note CRM | Référentiels | `/referentiels/clients/<code>/notes/` |
| Planifier relance | Référentiels | `/referentiels/clients/<code>/relances/` |
| Export RGPD | Référentiels | `/referentiels/clients/<code>/?tab=conformite` |

---

## ✅ Checklist Migration

- [ ] Créer `apps/ventes/views_clients_detail.py`
- [ ] Ajouter routes dans `apps/commerce/urls_ventes.py`
- [ ] Créer template `templates/ventes/client_detail.html`
- [ ] Renommer namespace `clients` → `referentiels` (ou alias)
- [ ] Ajouter routes CRM manquantes
- [ ] Supprimer redirections middleware
- [ ] Fixer tous les `{% url 'customer_detail' %}` sans namespace
- [ ] Ajouter cross-links entre workbenches
- [ ] Tester navigation Ventes → Clients
- [ ] Tester navigation Référentiels → Clients
- [ ] Documenter dans README

---

## 🚫 Anti-Patterns à Éviter

1. **NE JAMAIS** rediriger automatiquement de ventes → référentiels
2. **NE JAMAIS** utiliser `{% url 'customer_detail' %}` sans namespace
3. **NE JAMAIS** partager le même template entre les deux contextes
4. **NE JAMAIS** avoir deux routes identiques dans namespaces différents

---

## 📝 Notes Techniques

### Utilisation du Code Court
- URLs utilisent `<str:code>` au lieu de `<uuid:pk>`
- Format : `CUS-00123` (lisible, unique)
- Lookup : `Customer.objects.get(code=code, organization=org)`

### Permissions
- Ventes : `require_membership('read_only')`
- Référentiels : `require_membership('editor')` pour modifications

### Templates
- Base ventes : `extends 'base.html'`
- Base référentiels : `extends 'referentiels/base_referentiels.html'`

---

**Dernière mise à jour** : 2026-01-08
**Auteur** : Cascade AI
**Status** : 🟡 En cours d'implémentation
