# 🔄 WORKFLOW : Création Grille → Consultation BDD

## Étape 1 : Créer une Grille via l'Interface

### Via le Navigateur

1. **Connexion** :
   - URL : http://127.0.0.1:8000/auth/login/
   - Email : demo@monchai.fr
   - Mot de passe : demo123

2. **Accéder au module** :
   - Menu : Clients → Grilles tarifaires
   - OU URL directe : http://127.0.0.1:8000/ventes/tarifs/

3. **Créer la grille** :
   - Cliquer "Créer une grille"
   - Remplir :
     - Nom : "Test Grille 2025"
     - Devise : EUR
     - Date début : 01/01/2025
     - Date fin : (vide)
     - Active : ✅
   - Cliquer "Créer la grille"

4. **Remplir des prix** :
   - Cliquer "Éditer en grille"
   - Remplir au moins 3 produits :
     ```
     Produit 1 : 15.50€ | 14.00€ | 13.00€
     Produit 2 : 22.00€ | 20.50€ | 19.00€
     Produit 3 : 18.00€ | 16.50€ | 15.00€
     ```
   - Les prix se sauvegardent automatiquement (onBlur)

**✅ Résultat** : Grille créée avec 9 prix (3 produits × 3 niveaux)

---

## Étape 2 : Consulter en Base de Données

### Méthode A : Via l'Admin Django

1. **Ouvrir l'admin** :
   ```
   URL : http://127.0.0.1:8000/admin/
   Connexion : demo@monchai.fr / demo123
   ```

2. **Naviguer** :
   - Section **"SALES"**
   - Cliquer **"Price lists"**

3. **Trouver votre grille** :
   - Chercher "Test Grille 2025" dans la liste
   - Cliquer dessus

4. **Vérifier** :
   - ✅ Nom : Test Grille 2025
   - ✅ Devise : EUR
   - ✅ Date début : 2025-01-01
   - ✅ Active : Oui
   - ✅ Organization : Domaine de Démonstration

5. **Voir les prix** :
   - Scroller en bas de la page
   - Section **"PRICE ITEMS"**
   - Tableau avec tous les prix créés

6. **Cliquer sur un prix** :
   - Voir les détails complets :
     - SKU (produit)
     - unit_price (prix unitaire)
     - min_qty (quantité minimum)
     - discount_pct (remise)
     - created_at (date création)
     - updated_at (dernière modification)

**✅ Résultat** : Toutes les données visibles et persistées !

---

### Méthode B : Via SQL Direct (Avancé)

Si vous avez accès à la base de données PostgreSQL/SQLite :

#### 1. Lister toutes les grilles

```sql
SELECT 
    id,
    name,
    currency,
    valid_from,
    valid_to,
    is_active,
    created_at
FROM sales_pricelist
ORDER BY created_at DESC
LIMIT 10;
```

**Résultat attendu** :
```
┌──────────────────────────────────────┬────────────────────┬──────────┬────────────┬────────────┬───────────┬─────────────────────┐
│ id                                   │ name               │ currency │ valid_from │ valid_to   │ is_active │ created_at          │
├──────────────────────────────────────┼────────────────────┼──────────┼────────────┼────────────┼───────────┼─────────────────────┤
│ abc123...                            │ Test Grille 2025   │ EUR      │ 2025-01-01 │ NULL       │ true      │ 2025-11-03 16:30:00 │
│ def456...                            │ Tarif VIP          │ EUR      │ 2024-01-01 │ 2024-12-31 │ true      │ 2025-11-03 10:00:00 │
│ ghi789...                            │ Tarif Professionnel│ EUR      │ 2024-01-01 │ 2024-12-31 │ true      │ 2025-11-03 10:00:00 │
└──────────────────────────────────────┴────────────────────┴──────────┴────────────┴────────────┴───────────┴─────────────────────┘
```

**Copier l'UUID** de "Test Grille 2025" (colonne `id`)

---

#### 2. Lister les prix d'une grille

```sql
SELECT 
    pi.id,
    s.label as produit,
    pi.unit_price,
    pi.min_qty,
    pi.discount_pct,
    pi.created_at
FROM sales_priceitem pi
JOIN stock_sku s ON pi.sku_id = s.id
WHERE pi.price_list_id = 'VOTRE_UUID_ICI'
ORDER BY s.label, pi.min_qty;
```

**Résultat attendu** :
```
┌──────────────────────────────────────┬──────────────────────────────┬────────────┬─────────┬──────────────┬─────────────────────┐
│ id                                   │ produit                      │ unit_price │ min_qty │ discount_pct │ created_at          │
├──────────────────────────────────────┼──────────────────────────────┼────────────┼─────────┼──────────────┼─────────────────────┤
│ item1...                             │ Rouge Tradition 2023 - 75cl  │ 15.50      │ 0       │ 0.00         │ 2025-11-03 16:35:00 │
│ item2...                             │ Rouge Tradition 2023 - 75cl  │ 14.00      │ 6       │ 9.68         │ 2025-11-03 16:35:05 │
│ item3...                             │ Rouge Tradition 2023 - 75cl  │ 13.00      │ 12      │ 16.13        │ 2025-11-03 16:35:10 │
│ item4...                             │ Blanc de Blanc 2024 - 75cl   │ 22.00      │ 0       │ 0.00         │ 2025-11-03 16:35:15 │
│ item5...                             │ Blanc de Blanc 2024 - 75cl   │ 20.50      │ 6       │ 6.82         │ 2025-11-03 16:35:20 │
│ item6...                             │ Blanc de Blanc 2024 - 75cl   │ 19.00      │ 12      │ 13.64        │ 2025-11-03 16:35:25 │
└──────────────────────────────────────┴──────────────────────────────┴────────────┴─────────┴──────────────┴─────────────────────┘
```

**✅ Vérifications** :
- Chaque produit a bien 3 prix (min_qty 0, 6, 12)
- Les prix sont dans l'ordre croissant de min_qty
- Les remises (discount_pct) sont calculées automatiquement
- Les timestamps montrent la progression de la saisie

---

#### 3. Compter les prix par grille

```sql
SELECT 
    pl.name as grille,
    pl.currency,
    COUNT(pi.id) as nb_prix,
    MIN(pi.unit_price) as prix_min,
    MAX(pi.unit_price) as prix_max
FROM sales_pricelist pl
LEFT JOIN sales_priceitem pi ON pl.id = pi.price_list_id
GROUP BY pl.id, pl.name, pl.currency
ORDER BY pl.name;
```

**Résultat attendu** :
```
┌────────────────────┬──────────┬─────────┬──────────┬──────────┐
│ grille             │ currency │ nb_prix │ prix_min │ prix_max │
├────────────────────┼──────────┼─────────┼──────────┼──────────┤
│ Tarif Professionnel│ EUR      │ 24      │ 10.00    │ 35.00    │
│ Tarif Public       │ EUR      │ 24      │ 12.00    │ 40.00    │
│ Tarif VIP          │ EUR      │ 24      │ 8.00     │ 30.00    │
│ Test Grille 2025   │ EUR      │ 9       │ 13.00    │ 22.00    │
└────────────────────┴──────────┴─────────┴──────────┴──────────┘
```

**✅ Vérifications** :
- "Test Grille 2025" apparaît avec 9 prix
- Les prix min/max correspondent à ce que vous avez saisi

---

#### 4. Historique des modifications

```sql
SELECT 
    pi.id,
    s.label as produit,
    pi.unit_price,
    pi.min_qty,
    pi.created_at,
    pi.updated_at,
    CASE 
        WHEN pi.created_at = pi.updated_at THEN 'Créé'
        ELSE 'Modifié'
    END as statut
FROM sales_priceitem pi
JOIN stock_sku s ON pi.sku_id = s.id
WHERE pi.price_list_id = 'VOTRE_UUID_ICI'
ORDER BY pi.updated_at DESC;
```

**✅ Vérifications** :
- Si vous avez modifié un prix, `updated_at` > `created_at`
- Colonne "statut" montre si c'est une création ou modification

---

### Méthode C : Via Script Python

Créer un fichier `check_pricelist.py` :

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.sales.models import PriceList, PriceItem

# Récupérer votre grille
pricelist = PriceList.objects.filter(name__icontains="Test Grille").first()

if pricelist:
    print(f"\n✅ GRILLE TROUVÉE : {pricelist.name}")
    print(f"   UUID        : {pricelist.id}")
    print(f"   Devise      : {pricelist.currency}")
    print(f"   Validité    : {pricelist.valid_from} → {pricelist.valid_to or 'illimité'}")
    print(f"   Active      : {'Oui' if pricelist.is_active else 'Non'}")
    print(f"   Organisation: {pricelist.organization.name}")
    print(f"   Créée le    : {pricelist.created_at}")
    
    # Compter les prix
    items = pricelist.items.all()
    print(f"\n📊 PRIX ({items.count()}) :")
    
    for item in items:
        print(f"   - {item.sku.label}")
        print(f"     Prix: {item.unit_price} {pricelist.currency}")
        print(f"     Qté min: {item.min_qty or 0}")
        print(f"     Remise: {item.discount_pct}%")
        print(f"     Créé: {item.created_at}")
        print()
else:
    print("❌ Grille non trouvée")
```

**Exécuter** :
```bash
python check_pricelist.py
```

**Résultat** :
```
✅ GRILLE TROUVÉE : Test Grille 2025
   UUID        : abc123-def456-ghi789...
   Devise      : EUR
   Validité    : 2025-01-01 → illimité
   Active      : Oui
   Organisation: Domaine de Démonstration
   Créée le    : 2025-11-03 16:30:00

📊 PRIX (9) :
   - Rouge Tradition 2023 - Bouteille 75cl
     Prix: 15.50 EUR
     Qté min: 0
     Remise: 0.00%
     Créé: 2025-11-03 16:35:00

   - Rouge Tradition 2023 - Bouteille 75cl
     Prix: 14.00 EUR
     Qté min: 6
     Remise: 9.68%
     Créé: 2025-11-03 16:35:05
   ...
```

---

## ✅ CHECKLIST DE VALIDATION

### Création Interface Web
- [ ] Grille créée via formulaire
- [ ] Nom affiché correctement
- [ ] Dates de validité OK
- [ ] Prix remplis via grille interactive
- [ ] Sauvegarde automatique (onBlur) fonctionne
- [ ] Feedback visuel (orange → vert) OK

### Consultation Admin Django
- [ ] Grille visible dans /admin/sales/pricelist/
- [ ] UUID généré automatiquement
- [ ] Organization correcte
- [ ] Timestamps (created_at, updated_at) OK
- [ ] Section "Price items" visible
- [ ] Tous les prix affichés
- [ ] Relations SKU correctes

### Consultation BDD
- [ ] Requête SQL 1 : Grille trouvée dans sales_pricelist
- [ ] Requête SQL 2 : Prix trouvés dans sales_priceitem
- [ ] Requête SQL 3 : Compteur correct
- [ ] Requête SQL 4 : Historique modifications OK
- [ ] Script Python affiche toutes les données

### Intégrité Données
- [ ] UUID unique et valide
- [ ] Organization_id correct
- [ ] Relations FK correctes (sku_id, price_list_id)
- [ ] Contraintes UNIQUE respectées (price_list, sku, min_qty)
- [ ] Dates cohérentes (valid_to > valid_from si rempli)
- [ ] Prix > 0
- [ ] Remise 0-100%

---

## 🎓 Comprendre le Workflow Complet

### 1. Saisie Utilisateur (Frontend)

```
Interface Web (Django Template)
         ↓
   Formulaire HTML
         ↓
   JavaScript (AJAX)
         ↓
   POST /ventes/api/tarifs/<uuid>/items/
```

### 2. Traitement Backend (Django)

```
views_pricelists.py
         ↓
   pricelist_items_api(request, pk)
         ↓
   Validation données (forms_pricelists.py)
         ↓
   PriceItem.objects.create(...)
         ↓
   Sauvegarde PostgreSQL/SQLite
```

### 3. Persistance Base de Données

```
Table: sales_pricelist
  - id (UUID)
  - organization_id (FK)
  - name
  - currency
  - valid_from, valid_to
  - is_active
  - created_at, updated_at

Table: sales_priceitem
  - id (UUID)
  - organization_id (FK)
  - price_list_id (FK → sales_pricelist)
  - sku_id (FK → stock_sku)
  - unit_price
  - min_qty
  - discount_pct
  - created_at, updated_at
  
Contrainte UNIQUE: (price_list_id, sku_id, min_qty)
```

### 4. Consultation

```
Admin Django : /admin/sales/pricelist/
  ↓ ORM Django
  ↓ SELECT * FROM sales_pricelist...

SQL Direct : psql / sqlite3
  ↓ Requête brute
  ↓ Résultats tables

Script Python : check_pricelist.py
  ↓ Django ORM
  ↓ print() résultats formatés
```

---

## 🚀 TEST RAPIDE (5 minutes)

### Workflow Complet

1. **Créer** :
   - http://127.0.0.1:8000/ventes/tarifs/
   - Cliquer "Créer une grille"
   - Nom: "Test Quick"
   - Dates: 01/01/2025 → vide
   - Créer

2. **Remplir** :
   - Cliquer "Éditer en grille"
   - Remplir 2 produits × 3 prix = 6 valeurs
   - Temps: < 1 minute

3. **Vérifier Interface** :
   - Retour à la liste
   - "Test Quick" visible avec "6" prix

4. **Vérifier Admin** :
   - http://127.0.0.1:8000/admin/sales/pricelist/
   - Chercher "Test Quick"
   - Ouvrir → 6 items visibles

5. **Vérifier SQL** :
   ```sql
   SELECT name, COUNT(*) as nb 
   FROM sales_pricelist pl
   LEFT JOIN sales_priceitem pi ON pl.id = pi.price_list_id
   WHERE pl.name = 'Test Quick'
   GROUP BY pl.name;
   ```
   Résultat : `Test Quick | 6`

**✅ SI TOUT PASSE : MODULE 100% FONCTIONNEL !**

---

## 📚 Ressources

- **Documentation module** : `docs/MODULE_GRILLES_TARIFAIRES.md`
- **Tests complets** : `TEST_GRILLES_TARIFAIRES.md`
- **Modèles DB** : `apps/sales/models.py` lignes 156-255
- **Vues** : `apps/sales/views_pricelists.py`
- **Templates** : `templates/sales/pricelist_*.html`

---

**Félicitations ! Vous savez maintenant créer et consulter vos grilles tarifaires ! 🎉**
