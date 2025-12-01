# 🧪 TESTS DES 3 MODULES IMPLÉMENTÉS

## ✅ Ce Qui A Été Codé

### 1. Dashboard Personnalisable
- **Modèles** : `DashboardWidget` et `UserDashboardConfig`
- **Migration** : `0011_dashboardwidget_userdashboardconfig.py` ✅ APPLIQUÉE
- **Statut** : Base de données prête, interface à venir

### 2. Module Commandes
- **Vues** : `apps/ventes/views_orders.py`
  - `orders_list()` - Liste des commandes
  - `order_create()` - Création commande
  - `order_detail()` - Détail commande
- **Templates** :
  - `templates/ventes/orders_list.html`
  - `templates/ventes/order_form.html`
  - `templates/ventes/order_detail.html`
- **URLs** : `/ventes/commandes/` ✅ FONCTIONNELLES

### 3. Module Factures
- **Vues** : `apps/ventes/views_invoices.py`
  - `invoices_list()` - Liste des factures
  - `invoice_create()` - Création facture avec numérotation auto
  - `invoice_detail()` - Détail facture
- **Templates** :
  - `templates/ventes/invoices_list.html`
  - `templates/ventes/invoice_form.html`
  - `templates/ventes/invoice_detail.html`
- **URLs** : `/ventes/factures/` ✅ FONCTIONNELLES

---

## 🧪 TESTS À EFFECTUER

### Test 1 : Créer une Commande
```
1. Démarrer le serveur : python manage.py runserver
2. Aller sur : http://127.0.0.1:8000/ventes/commandes/
3. Cliquer sur "Nouvelle commande"
4. Sélectionner un client
5. Cliquer sur "Créer la commande"
6. Vérifier en DB : python manage.py shell
   >>> from apps.sales.models import Order
   >>> Order.objects.count()
   Attendu : Au moins 1
```

### Test 2 : Créer une Facture
```
1. Aller sur : http://127.0.0.1:8000/ventes/factures/
2. Cliquer sur "Nouvelle facture"
3. Sélectionner un client
4. Cliquer sur "Créer la facture"
5. Vérifier le numéro généré (format YYYY-NNNN)
6. Vérifier en DB : python manage.py shell
   >>> from apps.billing.models import Invoice
   >>> Invoice.objects.count()
   Attendu : Au moins 1
   >>> Invoice.objects.last().number
   Attendu : '2025-0001' (ou similaire)
```

### Test 3 : Lister les Commandes
```
1. Aller sur : http://127.0.0.1:8000/ventes/commandes/
2. Vérifier que la liste s'affiche
3. Tester les filtres (recherche, statut)
4. Cliquer sur "Voir" pour une commande
5. Vérifier que le détail s'affiche
```

### Test 4 : Lister les Factures
```
1. Aller sur : http://127.0.0.1:8000/ventes/factures/
2. Vérifier que la liste s'affiche
3. Tester les filtres (recherche, statut)
4. Cliquer sur "Voir" pour une facture
5. Vérifier que le détail s'affiche avec le numéro
```

---

## 🔍 VÉRIFICATIONS EN BASE DE DONNÉES

### Vérifier les Commandes Créées
```python
python manage.py shell

from apps.sales.models import Order
from apps.accounts.models import Organization

# Compter les commandes
print(f"Nombre de commandes : {Order.objects.count()}")

# Voir la dernière commande
last_order = Order.objects.last()
if last_order:
    print(f"Dernière commande :")
    print(f"  - Client : {last_order.customer.legal_name}")
    print(f"  - Statut : {last_order.status}")
    print(f"  - Date : {last_order.created_at}")
    print(f"  - Total TTC : {last_order.total_ttc} €")
```

### Vérifier les Factures Créées
```python
python manage.py shell

from apps.billing.models import Invoice

# Compter les factures
print(f"Nombre de factures : {Invoice.objects.count()}")

# Voir la dernière facture
last_invoice = Invoice.objects.last()
if last_invoice:
    print(f"Dernière facture :")
    print(f"  - Numéro : {last_invoice.number}")
    print(f"  - Client : {last_invoice.customer.legal_name}")
    print(f"  - Statut : {last_invoice.status}")
    print(f"  - Date émission : {last_invoice.date_issue}")
    print(f"  - Total TTC : {last_invoice.total_ttc} €")
```

---

## ⚠️ PRÉREQUIS

### Données de Test Nécessaires
Pour que les tests fonctionnent, vous devez avoir au moins :
- **1 organisation** active
- **1 utilisateur** avec membership
- **1 client** (SalesCustomer) dans l'organisation

### Créer un Client de Test (si nécessaire)
```python
python manage.py shell

from apps.sales.models import Customer as SalesCustomer
from apps.accounts.models import Organization

org = Organization.objects.first()

client = SalesCustomer.objects.create(
    organization=org,
    type='part',
    legal_name='Client Test',
    billing_address='1 rue Test',
    billing_postal_code='75001',
    billing_city='Paris',
    billing_country='FR',
    payment_terms='30j',
    currency='EUR',
    is_active=True
)

print(f"Client créé : {client.legal_name}")
```

---

## 📊 RÉSULTATS ATTENDUS

### Après Test Commande
- ✅ Une nouvelle ligne dans `sales_order`
- ✅ Statut = 'draft'
- ✅ Total TTC = 0.00 (commande vide)
- ✅ Client associé correctement

### Après Test Facture
- ✅ Une nouvelle ligne dans `billing_invoice`
- ✅ Numéro généré automatiquement (format YYYY-NNNN)
- ✅ Statut = 'draft'
- ✅ Date émission = aujourd'hui
- ✅ Date échéance = aujourd'hui + 30 jours
- ✅ Total TTC = 0.00 (facture vide)
- ✅ Client associé correctement

---

## 🚨 EN CAS D'ERREUR

### Erreur "No such table"
```bash
python manage.py migrate
```

### Erreur "Customer matching query does not exist"
Créer un client de test (voir section Prérequis)

### Erreur "Organization matching query does not exist"
Vérifier que vous êtes connecté et avez une organisation active

### Erreur 404
Vérifier que le serveur est démarré et les URLs sont correctes

---

## ✅ VALIDATION FINALE

Pour valider que tout fonctionne :

1. **Créer 1 commande** via l'interface
2. **Créer 1 facture** via l'interface
3. **Vérifier en DB** que les 2 lignes existent
4. **Afficher les listes** et vérifier que les données apparaissent
5. **Afficher les détails** et vérifier que tout est cohérent

**Si ces 5 étapes passent → Les modules sont FONCTIONNELS** ✅
