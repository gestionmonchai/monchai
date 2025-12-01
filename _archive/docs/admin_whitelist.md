# Liste Blanche Admin Django - Mon Chai V1

## 🎯 Objectif

**L'admin Django est exclusivement réservé aux tâches techniques pour les superusers.**

Aucun modèle métier ne doit être accessible via `/admin/` pour les utilisateurs normaux.

---

## ✅ Modules Autorisés (Liste Blanche)

### 🔐 **Authentication & Authorization**
- `auth.User` - Gestion utilisateurs système
- `auth.Group` - Groupes de permissions Django
- `auth.Permission` - Permissions système Django

### 🏢 **Accounts (Technique)**
- `accounts.Organization` - Organisations (technique uniquement)
- `accounts.Membership` - Adhésions (debug technique)
- `accounts.UserProfile` - Profils utilisateurs (support technique)

### 🌐 **Sites Framework**
- `sites.Site` - Configuration multi-sites Django

### 🔄 **Redirections**
- `redirects.Redirect` - Redirections 301/302 système

### ⏰ **Celery Beat (si installé)**
- `django_celery_beat.PeriodicTask` - Tâches programmées
- `django_celery_beat.IntervalSchedule` - Intervalles
- `django_celery_beat.CrontabSchedule` - Crontabs

### 🔧 **Django Admin Logs**
- `admin.LogEntry` - Logs d'actions admin (audit technique)

---

## ❌ Modules INTERDITS (Métier)

### 🧾 **Billing - INTERDIT**
- `billing.Invoice` → Utiliser `/billing/factures/`
- `billing.InvoiceLine` → Géré via interface factures
- `billing.Payment` → Utiliser `/billing/paiements/`
- `billing.CreditNote` → Utiliser `/billing/avoirs/`
- `billing.Reconciliation` → Géré via interface paiements
- `billing.AccountMap` → Configuration comptable back-office
- `billing.GLEntry` → Écritures via interface comptable

### 💰 **Sales - INTERDIT**
- `sales.Customer` → Utiliser `/clients/`
- `sales.TaxCode` → Configuration back-office
- `sales.PriceList` → Utiliser `/sales/tarifs/`
- `sales.Quote` → Utiliser `/sales/devis/`
- `sales.Order` → Utiliser `/sales/commandes/`
- `sales.QuoteLine` → Géré via interface devis
- `sales.OrderLine` → Géré via interface commandes
- `sales.StockReservation` → Géré automatiquement

### 📦 **Stock - INTERDIT**
- `stock.SKU` → Utiliser `/catalogue/produits/`
- `stock.StockVracBalance` → Utiliser `/stock/vrac/`
- `stock.StockSKUBalance` → Utiliser `/stock/produits/`
- `stock.StockVracMove` → Utiliser `/stock/mouvements/`
- `stock.StockSKUMove` → Utiliser `/stock/mouvements/`
- `stock.StockTransfer` → Utiliser `/stock/transferts/`

### 🍇 **Viticulture - INTERDIT**
- `viticulture.Cuvee` → Utiliser `/catalogue/cuvees/`
- `viticulture.Lot` → Utiliser `/catalogue/lots/`
- `viticulture.GrapeVariety` → Utiliser `/referentiels/cepages/`
- `viticulture.Appellation` → Utiliser `/referentiels/appellations/`
- `viticulture.Vintage` → Utiliser `/referentiels/millesimes/`
- `viticulture.Warehouse` → Utiliser `/referentiels/entrepots/`
- `viticulture.VineyardPlot` → Utiliser `/referentiels/parcelles/`
- `viticulture.UnitOfMeasure` → Utiliser `/referentiels/unites/`

### 👥 **Clients - INTERDIT**
- `clients.Customer` → Utiliser `/clients/`
- `clients.CustomerTag` → Géré via interface clients
- `clients.CustomerTagLink` → Géré via interface clients
- `clients.CustomerActivity` → Géré via CRM

---

## 🔒 Règles d'Accès

### 👤 **Utilisateurs Normaux** (staff=True, superuser=False)
- ❌ **Accès refusé** à `/admin/` → Redirection 302
- ❌ **Aucun module visible** dans l'interface admin
- ✅ **Interfaces métier** : `/clients/`, `/billing/`, `/sales/`, `/stock/`, `/catalogue/`

### 🔧 **Superusers** (superuser=True)
- ✅ **Accès complet** à `/admin/` pour maintenance technique
- ✅ **Modules liste blanche** visibles uniquement
- ✅ **Outils Django** : shell, migrations, logs, debug
- ⚠️ **Usage exceptionnel** : Debug, support, maintenance système

---

## 🛡️ Implémentation Technique

### Méthode 1 : Permissions Bloquantes
```python
class MetierModelAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser
```

### Méthode 2 : Désenregistrement (Recommandée)
```python
# Ne pas enregistrer du tout
# admin.site.register(MetierModel, MetierModelAdmin)  # SUPPRIMÉ
```

### Méthode 3 : Désenregistrement Conditionnel
```python
# Enregistrer seulement si nécessaire pour debug
if settings.DEBUG and settings.ADMIN_ENABLE_METIER_MODELS:
    admin.site.register(MetierModel, MetierModelAdmin)
```

---

## 🔍 Vérifications

### Test Utilisateur Normal
```bash
# Doit retourner 302 (redirection)
curl -I http://localhost:8000/admin/

# Doit retourner 302 pour tous les modèles métier
curl -I http://localhost:8000/admin/billing/invoice/
curl -I http://localhost:8000/admin/sales/quote/
curl -I http://localhost:8000/admin/stock/sku/
```

### Test Superuser
```bash
# Doit retourner 200 avec liste blanche uniquement
curl -I http://localhost:8000/admin/
```

### Audit Registry
```python
from django.contrib import admin
print("Modèles enregistrés:", list(admin.site._registry.keys()))
```

---

## 📋 Redirections Actives

### Redirections Ciblées (Conservées)
- `/admin/sales/customer/` → `/clients/` (301)
- `/admin/sales/customer/add/` → `/clients/nouveau/` (301)
- `/admin/sales/customer/{id}/change/` → `/clients/{id}/modifier/` (301)

### Pas de Redirection Générique
- ❌ Pas de `/admin/{app}/{model}/` → `/back-office/` générique
- ✅ Blocage net avec 302/403 pour forcer l'usage des bonnes interfaces

---

## 🚨 Sentinelles Anti-Régression

### 1. Audit Hebdomadaire
```python
# management/commands/audit_admin_registry.py
def handle(self):
    metier_apps = ['billing', 'sales', stock', 'viticulture', 'clients']
    for model in admin.site._registry:
        if model._meta.app_label in metier_apps:
            raise CommandError(f"Modèle métier détecté: {model}")
```

### 2. Check CI
```bash
# .github/workflows/admin_check.yml
grep -r "/admin/billing\|/admin/sales\|/admin/stock" templates/ && exit 1
```

---

## 📚 Documentation Associée

- `docs/backoffice_billing_sales.md` - Écrans métier de remplacement
- `docs/routing_change_log.md` - Historique des changements de routes
- `docs/rapport_admin_access_refactoring.md` - Rapport complet du refactoring

---

## ✅ Validation Finale

### Checklist Superuser
- [ ] `/admin/` → 200 avec modules liste blanche uniquement
- [ ] `/admin/auth/user/` → 200 (technique OK)
- [ ] `/admin/billing/invoice/` → 200 (technique OK si enregistré)
- [ ] Aucun module métier visible dans navigation

### Checklist Utilisateur Normal
- [ ] `/admin/` → 302 (accès refusé)
- [ ] `/admin/billing/invoice/` → 302 (bloqué)
- [ ] `/clients/` → 200 (interface métier OK)
- [ ] `/billing/factures/` → 200 (interface métier OK)

### Checklist Navigation
- [ ] Aucun lien `/admin/` dans templates métier
- [ ] Aucun lien `/admin/` dans JavaScript
- [ ] Aucun lien `/admin/` dans emails/notifications
- [ ] Menu back-office complet et fonctionnel

---

**Dernière mise à jour :** 2025-09-25  
**Statut :** ✅ Liste blanche définie  
**Prochaine étape :** Désenregistrement des ModelAdmin métier
