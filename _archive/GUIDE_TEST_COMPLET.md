# 🧪 GUIDE DE TEST COMPLET - MODULES VENTES

## 🚀 ÉTAPE 1 : CRÉER LES DONNÉES DE TEST

### Commande Automatique
```bash
cd "c:\Users\33685\Desktop\Mon Chai V1"
python manage.py test_ventes_ui
```

**Cette commande va créer automatiquement :**
- ✅ 4 clients de test (Domaine Dupont, Cave Martin, Restaurant Le Gourmet, Particulier Durand)
- ✅ 2 devis de test
- ✅ 2 commandes de test
- ✅ 2 factures de test avec numérotation automatique

**Résultat attendu :**
```
✅ Organisation : [Votre organisation]
✅ Utilisateur : [Votre email]

📋 Création de clients de test...
  ✨ Créé : Domaine Dupont
  ✨ Créé : Cave Martin
  ✨ Créé : Restaurant Le Gourmet
  ✨ Créé : Particulier Durand

📄 Création de devis de test...
  ✨ Créé : Devis pour Domaine Dupont
  ✨ Créé : Devis pour Cave Martin

🛒 Création de commandes de test...
  ✨ Créé : Commande pour Domaine Dupont
  ✨ Créé : Commande pour Cave Martin

🧾 Création de factures de test...
  ✨ Créé : Facture 2025-0001 pour Domaine Dupont
  ✨ Créé : Facture 2025-0002 pour Cave Martin

📊 STATISTIQUES
  Clients : 4
  Devis : 2
  Commandes : 2
  Factures : 2

✅ Données de test créées avec succès !
```

---

## 🧪 ÉTAPE 2 : DÉMARRER LE SERVEUR

```bash
python manage.py runserver
```

**Ouvrir le navigateur :** `http://127.0.0.1:8000`

---

## 📋 ÉTAPE 3 : TESTS DES 5 MODULES

### ✅ TEST 1 : DEVIS

**URL :** http://127.0.0.1:8000/ventes/devis/

**Tests à effectuer :**
1. ✅ La liste affiche les 2 devis créés
2. ✅ Cliquer sur "Nouveau devis"
3. ✅ **VÉRIFIER** : Le select "Client" contient 4 clients
4. ✅ Sélectionner "Restaurant Le Gourmet"
5. ✅ Cliquer sur "Créer le devis"
6. ✅ **VÉRIFIER** : Redirection vers le détail du devis
7. ✅ **VÉRIFIER** : Le client est bien "Restaurant Le Gourmet"

**Vérification DB :**
```python
python manage.py shell
>>> from apps.sales.models import Quote
>>> Quote.objects.count()  # Doit être 3
>>> Quote.objects.last().customer.legal_name  # Doit être "Restaurant Le Gourmet"
```

---

### ✅ TEST 2 : COMMANDES

**URL :** http://127.0.0.1:8000/ventes/commandes/

**Tests à effectuer :**
1. ✅ La liste affiche les 2 commandes créées
2. ✅ Cliquer sur "Nouvelle commande"
3. ✅ **VÉRIFIER** : Le select "Client" contient 4 clients
4. ✅ Sélectionner "Particulier Durand"
5. ✅ Cliquer sur "Créer la commande"
6. ✅ **VÉRIFIER** : Redirection vers le détail de la commande
7. ✅ **VÉRIFIER** : Le client est bien "Particulier Durand"

**Vérification DB :**
```python
python manage.py shell
>>> from apps.sales.models import Order
>>> Order.objects.count()  # Doit être 3
>>> Order.objects.last().customer.legal_name  # Doit être "Particulier Durand"
```

---

### ✅ TEST 3 : FACTURES

**URL :** http://127.0.0.1:8000/ventes/factures/

**Tests à effectuer :**
1. ✅ La liste affiche les 2 factures créées (2025-0001, 2025-0002)
2. ✅ Cliquer sur "Nouvelle facture"
3. ✅ **VÉRIFIER** : Le select "Client" contient 4 clients
4. ✅ Sélectionner "Restaurant Le Gourmet"
5. ✅ Cliquer sur "Créer la facture"
6. ✅ **VÉRIFIER** : Redirection vers le détail de la facture
7. ✅ **VÉRIFIER** : Le numéro est "2025-0003" (auto-incrémenté)
8. ✅ **VÉRIFIER** : Le client est bien "Restaurant Le Gourmet"

**Vérification DB :**
```python
python manage.py shell
>>> from apps.billing.models import Invoice
>>> Invoice.objects.count()  # Doit être 3
>>> Invoice.objects.last().number  # Doit être "2025-0003"
>>> Invoice.objects.last().customer.legal_name  # Doit être "Restaurant Le Gourmet"
```

---

### ✅ TEST 4 : VENTE PRIMEUR (NOUVEAU)

**URL :** http://127.0.0.1:8000/ventes/primeur/

**Tests à effectuer :**
1. ✅ La page affiche "Aucune vente en primeur" (normal, aucune créée)
2. ✅ Cliquer sur "Nouvelle vente primeur"
3. ✅ **VÉRIFIER** : Le select "Client" contient 4 clients
4. ✅ **VÉRIFIER** : Le select "Millésime" contient 2025, 2026, 2027
5. ✅ Sélectionner "Domaine Dupont"
6. ✅ Sélectionner millésime "2026"
7. ✅ Saisir campagne "Primeurs 2026"
8. ✅ Sélectionner date livraison (ex: 01/06/2027)
9. ✅ Cliquer sur "Créer la vente primeur"
10. ✅ **VÉRIFIER** : Redirection vers le détail
11. ✅ **VÉRIFIER** : Millésime = 2026, Remise = 20%

**Vérification DB :**
```python
python manage.py shell
>>> from apps.sales.models import Quote
>>> primeur = Quote.objects.filter(is_primeur=True).last()
>>> primeur.vintage_year  # Doit être 2026
>>> primeur.primeur_discount_pct  # Doit être 20.00
>>> primeur.customer.legal_name  # Doit être "Domaine Dupont"
```

---

### ✅ TEST 5 : VENTE VRAC (NOUVEAU)

**URL :** http://127.0.0.1:8000/ventes/vrac/

**Tests à effectuer :**
1. ✅ La page affiche "Aucune vente en vrac" (normal, aucune créée)
2. ✅ Cliquer sur "Nouvelle vente vrac"
3. ✅ **VÉRIFIER** : Le select "Client" contient 4 clients
4. ✅ **VÉRIFIER** : Le select "Lot" contient des lots (si disponibles)
5. ✅ Sélectionner "Cave Martin"
6. ✅ Saisir volume "1000" litres
7. ✅ Cliquer sur "Créer la vente vrac"
8. ✅ **VÉRIFIER** : Redirection vers le détail
9. ✅ **VÉRIFIER** : Notes contient "Vente en vrac - 1000L"

**Vérification DB :**
```python
python manage.py shell
>>> from apps.sales.models import Quote
>>> vrac = Quote.objects.filter(notes__icontains='vrac').last()
>>> vrac.notes  # Doit contenir "Vente en vrac - 1000L"
>>> vrac.customer.legal_name  # Doit être "Cave Martin"
```

---

## 🎯 ÉTAPE 4 : VÉRIFICATION MENU NAVIGATION

### Menu Desktop
1. ✅ Cliquer sur "Ventes" dans le menu principal
2. ✅ **VÉRIFIER** : Le dropdown contient :
   - Devis
   - Commandes
   - Factures
   - ─────────── (séparateur)
   - 🕐 Vente Primeur
   - 💧 Vente Vrac

### Menu Mobile
1. ✅ Réduire la fenêtre ou ouvrir sur mobile
2. ✅ Cliquer sur le bouton hamburger
3. ✅ Cliquer sur "Ventes"
4. ✅ **VÉRIFIER** : Même contenu que desktop

---

## 📊 ÉTAPE 5 : VALIDATION FINALE

### Comptage Total en DB
```python
python manage.py shell

from apps.sales.models import Customer as SalesCustomer, Quote, Order
from apps.billing.models import Invoice

print(f"Clients : {SalesCustomer.objects.count()}")  # Doit être >= 4
print(f"Devis : {Quote.objects.count()}")  # Doit être >= 3
print(f"Commandes : {Order.objects.count()}")  # Doit être >= 3
print(f"Factures : {Invoice.objects.count()}")  # Doit être >= 3
print(f"Ventes Primeur : {Quote.objects.filter(is_primeur=True).count()}")  # Doit être >= 1
print(f"Ventes Vrac : {Quote.objects.filter(notes__icontains='vrac').count()}")  # Doit être >= 1
```

**Résultat attendu :**
```
Clients : 4
Devis : 3
Commandes : 3
Factures : 3
Ventes Primeur : 1
Ventes Vrac : 1
```

---

## ✅ CHECKLIST FINALE

### Fonctionnalités Testées
- [x] Devis : Liste, Création, Détail
- [x] Commandes : Liste, Création, Détail
- [x] Factures : Liste, Création, Détail, Numérotation auto
- [x] Vente Primeur : Liste, Création, Détail, Millésime, Remise
- [x] Vente Vrac : Liste, Création, Détail, Volume
- [x] Menu Navigation : Desktop et Mobile
- [x] Clients chargés dans tous les formulaires
- [x] Données créées en base de données

### Problèmes Résolus
- ✅ Clients ne chargeaient pas → Commande test_ventes_ui créée
- ✅ Formulaires vides → Alerte si aucun client + lien création
- ✅ Menu navigation → Primeur et Vrac ajoutés avec icônes
- ✅ Tests UI → Commande automatique pour valider

---

## 🚨 EN CAS DE PROBLÈME

### Erreur "No such table"
```bash
python manage.py migrate
```

### Aucun client dans les formulaires
```bash
python manage.py test_ventes_ui
```

### Erreur 404 sur les URLs
Vérifier que le serveur est démarré :
```bash
python manage.py runserver
```

### Erreur "Customer matching query does not exist"
Créer un client manuellement :
```python
python manage.py shell

from apps.sales.models import Customer as SalesCustomer
from apps.accounts.models import Organization

org = Organization.objects.first()

SalesCustomer.objects.create(
    organization=org,
    type='part',
    legal_name='Client Test Manuel',
    billing_address='1 rue Test',
    billing_postal_code='75001',
    billing_city='Paris',
    billing_country='FR',
    payment_terms='30j',
    currency='EUR',
    is_active=True
)
```

---

## 🎉 SUCCÈS

**Si tous les tests passent :**
- ✅ 5 modules fonctionnels (Devis, Commandes, Factures, Primeur, Vrac)
- ✅ Formulaires chargent les clients correctement
- ✅ Données créées en base de données
- ✅ Menu navigation accessible
- ✅ UI testée et validée

**Les modules sont PRÊTS POUR LA PRODUCTION !** 🚀
