# 🎨 Dashboard Viticole - Documentation

## 📊 Vue d'Ensemble

Le **Dashboard Viticole** est la page d'accueil principale de Mon Chai, offrant une vue d'ensemble complète et visuelle de votre exploitation viticole.

---

## ✨ Fonctionnalités

### 1. Métriques Principales (Cartes Visuelles)

#### 🍇 Volume Récolté
- **Affichage** : Poids total en kilogrammes
- **Source** : Vendanges de la campagne en cours (ex: 2025-2026)
- **Détails** : 
  - Volume de moût estimé en litres (si disponible)
  - Nombre de vendanges enregistrées
- **Couleur** : Dégradé violet (harvest)

#### 🍷 Volume en Cuve
- **Affichage** : Volume total en litres
- **Source** : Stocks actuels (StockVracBalance)
- **Détails** : Nombre de lots en stock
- **Couleur** : Dégradé rose/rouge (stock)

#### 💰 Chiffre d'Affaires
- **Affichage** : CA TTC de l'année en cours
- **Source** : Factures émises et payées
- **Détails** : 
  - CA HT
  - Nombre de factures
- **Couleur** : Dégradé bleu (revenue)

---

### 2. Statistiques Secondaires

| Métrique | Description | Couleur |
|----------|-------------|---------|
| **Clients actifs** | Nombre de clients actifs | Vert |
| **Cuvées actives** | Nombre de cuvées actives | Bleu |
| **Commandes en cours** | Commandes draft + confirmées | Jaune |
| **Factures impayées** | Montant total dû | Rouge |

---

### 3. Actions Rapides

Accès direct aux modules principaux :
- 👥 **Gérer les clients** → `/ventes/clients/`
- 🍷 **Gérer les cuvées** → `/catalogue/cuvees/`
- 📦 **Stocks & Transferts** → `/stocks/`
- 🍇 **Vendanges** → `/admin/production/vendangereception/`
- 🧾 **Factures** → `/admin/billing/invoice/`
- ⚙️ **Configuration** → `/onboarding/checklist/`

---

## 🎨 Design

### Palette de Couleurs

```css
/* Carte Récolte */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Carte Stock */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

/* Carte CA */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
```

### Effets Visuels
- **Hover** : Élévation de la carte (-4px) + ombre accentuée
- **Transitions** : 0.2s smooth sur transform et box-shadow
- **Icônes** : Bootstrap Icons 1.10+
- **Responsive** : Grid adaptatif (col-lg-4, col-md-6)

---

## 🔧 Architecture Technique

### Vue Django

**Fichier** : `apps/accounts/views.py`

```python
@login_required
def dashboard_placeholder(request):
    """
    Dashboard viticole avec métriques clés
    """
    organization = request.current_org
    
    # 1. Volume récolté (campagne en cours)
    vendanges_stats = VendangeReception.objects.filter(
        organization=organization,
        campagne=current_campaign
    ).aggregate(
        total_kg=Sum('poids_kg'),
        total_volume_l=Sum('volume_mesure_l'),
        count=Count('id')
    )
    
    # 2. Volumes en cuve (stocks actuels)
    stock_stats = StockVracBalance.objects.filter(
        organization=organization,
        qty_l__gt=0
    ).aggregate(
        total_volume=Sum('qty_l'),
        nb_lots=Count('lot', distinct=True)
    )
    
    # 3. Chiffre d'affaires (année en cours)
    factures_stats = Invoice.objects.filter(
        organization=organization,
        date_issue__year=current_year,
        status__in=['issued', 'paid']
    ).aggregate(
        ca_ht=Sum('total_ht'),
        ca_ttc=Sum('total_ttc'),
        count=Count('id')
    )
    
    # ... statistiques complémentaires
```

### Template

**Fichier** : `templates/accounts/dashboard_viticole.html`

**Structure** :
1. Header avec titre et organisation
2. 3 cartes métriques principales (grid responsive)
3. 4 statistiques secondaires
4. Actions rapides (grid adaptatif)
5. Informations compte (footer)

---

## 📊 Requêtes SQL

### Performance Optimisée

Toutes les requêtes utilisent des **agrégations SQL** pour minimiser les appels DB :

```python
# 1 requête pour vendanges
.aggregate(total_kg=Sum('poids_kg'), total_volume_l=Sum('volume_mesure_l'), count=Count('id'))

# 1 requête pour stocks
.aggregate(total_volume=Sum('qty_l'), nb_lots=Count('lot', distinct=True))

# 1 requête pour CA
.aggregate(ca_ht=Sum('total_ht'), ca_ttc=Sum('total_ttc'), count=Count('id'))

# 1 requête pour clients actifs
.count()

# 1 requête pour cuvées actives
.count()

# 1 requête pour commandes en cours
.count()

# 1 requête pour factures impayées
.aggregate(montant_du=Sum('amount_due'))
```

**Total** : **7 requêtes SQL** pour charger le dashboard complet

---

## 🎯 Cas d'Usage

### Scénario 1 : Début de Campagne
```
Volume Récolté: 0 kg
Volume en Cuve: 5 000 L (stock précédent)
CA: 0 € (début d'année)
```

### Scénario 2 : Après Vendanges
```
Volume Récolté: 12 500 kg
Volume en Cuve: 14 375 L (stock + moût)
CA: 15 000 € (premières ventes)
```

### Scénario 3 : Fin de Campagne
```
Volume Récolté: 25 000 kg
Volume en Cuve: 3 200 L (stock résiduel)
CA: 125 000 € (année complète)
```

---

## 🔄 Évolutions Futures

### Phase 1 : Graphiques
- [ ] Graphique évolution CA mensuel
- [ ] Graphique évolution stocks
- [ ] Graphique répartition par cuvée

### Phase 2 : Alertes
- [ ] Alerte stock faible
- [ ] Alerte factures en retard
- [ ] Alerte vendanges à traiter

### Phase 3 : Comparaisons
- [ ] Comparaison année N vs N-1
- [ ] Objectifs CA vs réalisé
- [ ] Rendement moyen par parcelle

### Phase 4 : Exports
- [ ] Export PDF rapport mensuel
- [ ] Export Excel données brutes
- [ ] Envoi email rapport automatique

---

## 🧪 Tests

### Test 1 : Données Vides
```python
# Organisation sans données
assert volume_recolte_kg == 0
assert volume_en_cuve_l == 0
assert ca_ttc == 0
```

### Test 2 : Données Complètes
```python
# Organisation avec vendanges, stocks, factures
assert volume_recolte_kg > 0
assert volume_en_cuve_l > 0
assert ca_ttc > 0
assert nb_factures > 0
```

### Test 3 : Isolation Multi-Tenant
```python
# Vérifier que seules les données de l'organisation sont affichées
org1_data = get_dashboard_data(org1)
org2_data = get_dashboard_data(org2)
assert org1_data != org2_data
```

---

## 📱 Responsive Design

### Breakpoints

| Taille | Colonnes Métriques | Colonnes Stats |
|--------|-------------------|----------------|
| **< 768px** (Mobile) | 1 colonne | 1 colonne |
| **768-992px** (Tablet) | 1 colonne | 2 colonnes |
| **> 992px** (Desktop) | 3 colonnes | 4 colonnes |

### Optimisations Mobile
- Icônes 48px au lieu de 64px
- Valeurs métriques 2rem au lieu de 2.5rem
- Padding réduit (16px au lieu de 32px)

---

## 🎨 Personnalisation

### Modifier les Couleurs

Éditer `dashboard_viticole.html` :

```css
/* Carte Récolte - Remplacer par vos couleurs */
.metric-card.harvest {
    background: linear-gradient(135deg, #VOTRE_COULEUR_1 0%, #VOTRE_COULEUR_2 100%);
}
```

### Ajouter une Métrique

1. **Vue** (`views.py`) :
```python
nouvelle_metrique = Model.objects.filter(
    organization=organization
).aggregate(total=Sum('champ'))

context['nouvelle_metrique'] = nouvelle_metrique['total'] or 0
```

2. **Template** (`dashboard_viticole.html`) :
```html
<div class="col-lg-3">
    <div class="stat-card nouvelle">
        <div class="stat-value">{{ nouvelle_metrique }}</div>
        <div class="stat-label">Nouvelle Métrique</div>
    </div>
</div>
```

---

## 🔗 Liens Utiles

- **URL** : `/dashboard/` (après connexion)
- **Vue** : `apps/accounts/views.py::dashboard_placeholder`
- **Template** : `templates/accounts/dashboard_viticole.html`
- **Permissions** : `@login_required` (tous les utilisateurs connectés)

---

## 📝 Notes Techniques

### Campagne Viticole
- Format : `YYYY-YYYY+1` (ex: 2025-2026)
- Calcul automatique basé sur l'année en cours
- Utilisé pour filtrer les vendanges

### Gestion des Valeurs Nulles
Toutes les agrégations utilisent `or Decimal('0')` pour éviter les `None` :
```python
volume_recolte_kg = vendanges_stats['total_kg'] or Decimal('0')
```

### Filtres Statuts
- **Factures** : `status__in=['issued', 'paid']` (exclut draft et cancelled)
- **Commandes** : `status__in=['draft', 'confirmed']` (en cours de traitement)
- **Clients/Cuvées** : `is_active=True` (actifs uniquement)

---

*Documentation créée le : 30/10/2024*
*Version : 1.0*
*Auteur : Mon Chai Team*
