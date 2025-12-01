# 🎨 Aperçu du Nouveau Dashboard Viticole

## 📸 Aperçu Visuel

```
┌─────────────────────────────────────────────────────────────────────┐
│  🏠 Dashboard Viticole                    🏢 Mon Domaine Viticole   │
│  Vue d'ensemble de votre exploitation - Campagne 2025-2026          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  🍇                  │  │  🍷                  │  │  💰                  │
│                      │  │                      │  │                      │
│  12 500 kg           │  │  14 375 L            │  │  125 000 €           │
│  VOLUME RÉCOLTÉ      │  │  VOLUME EN CUVE      │  │  CHIFFRE D'AFFAIRES  │
│  ≈ 9 375 L de moût   │  │  15 lots en stock    │  │  104 167 € HT - 42 f │
│                      │  │                      │  │                      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
   Dégradé Violet            Dégradé Rose/Rouge        Dégradé Bleu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Statistiques

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 🟢 45       │  │ 🔵 12       │  │ 🟡 8        │  │ 🔴 15 000 € │
│ Clients     │  │ Cuvées      │  │ Commandes   │  │ Impayées    │
│ actifs      │  │ actives     │  │ en cours    │  │             │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Actions Rapides

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 👥 Gérer les │ │ 🍷 Gérer les │ │ 📦 Stocks &  │ │ 🍇 Vendanges │
│    clients   │ │    cuvées    │ │  Transferts  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐
│ 🧾 Factures  │ │ ⚙️ Config    │
│              │ │              │
└──────────────┘ └──────────────┘
```

---

## ✨ Caractéristiques Visuelles

### 🎨 Cartes Métriques Principales

#### Carte 1 : Volume Récolté (Violet)
- **Icône** : 🍇 Panier (basket3)
- **Couleur** : Dégradé violet (#667eea → #764ba2)
- **Valeur** : 12 500 kg (grande, 2.5rem)
- **Label** : "VOLUME RÉCOLTÉ" (uppercase)
- **Détail** : "≈ 9 375 L de moût" (petit, gris)
- **Effet hover** : Élévation -4px + ombre

#### Carte 2 : Volume en Cuve (Rose/Rouge)
- **Icône** : 🍷 Goutte (droplet-fill)
- **Couleur** : Dégradé rose/rouge (#f093fb → #f5576c)
- **Valeur** : 14 375 L
- **Label** : "VOLUME EN CUVE"
- **Détail** : "15 lots en stock"
- **Effet hover** : Élévation -4px + ombre

#### Carte 3 : Chiffre d'Affaires (Bleu)
- **Icône** : 💰 Euro (currency-euro)
- **Couleur** : Dégradé bleu (#4facfe → #00f2fe)
- **Valeur** : 125 000 €
- **Label** : "CHIFFRE D'AFFAIRES 2025"
- **Détail** : "104 167 € HT - 42 factures"
- **Effet hover** : Élévation -4px + ombre

---

## 🎯 Données Affichées

### Volume Récolté
```python
Source: VendangeReception
Filtre: campagne='2025-2026', organization=current_org
Calcul: Sum(poids_kg), Sum(volume_mesure_l), Count(id)
Affichage: "12 500 kg" + "≈ 9 375 L de moût"
```

### Volume en Cuve
```python
Source: StockVracBalance
Filtre: qty_l > 0, organization=current_org
Calcul: Sum(qty_l), Count(lot, distinct=True)
Affichage: "14 375 L" + "15 lots en stock"
```

### Chiffre d'Affaires
```python
Source: Invoice
Filtre: date_issue__year=2025, status=['issued','paid'], organization=current_org
Calcul: Sum(total_ht), Sum(total_ttc), Count(id)
Affichage: "125 000 €" + "104 167 € HT - 42 factures"
```

---

## 📱 Responsive

### Desktop (> 992px)
```
┌────────────┐ ┌────────────┐ ┌────────────┐
│  Récolte   │ │   Cuve     │ │     CA     │
└────────────┘ └────────────┘ └────────────┘

┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Client│ │Cuvées│ │Comman│ │Impayé│
└──────┘ └──────┘ └──────┘ └──────┘
```

### Tablet (768-992px)
```
┌────────────┐
│  Récolte   │
└────────────┘
┌────────────┐
│   Cuve     │
└────────────┘
┌────────────┐
│     CA     │
└────────────┘

┌──────┐ ┌──────┐
│Client│ │Cuvées│
└──────┘ └──────┘
┌──────┐ ┌──────┐
│Comman│ │Impayé│
└──────┘ └──────┘
```

### Mobile (< 768px)
```
┌────────────┐
│  Récolte   │
└────────────┘
┌────────────┐
│   Cuve     │
└────────────┘
┌────────────┐
│     CA     │
└────────────┘
┌────────────┐
│  Clients   │
└────────────┘
┌────────────┐
│  Cuvées    │
└────────────┘
┌────────────┐
│ Commandes  │
└────────────┘
┌────────────┐
│  Impayés   │
└────────────┘
```

---

## 🚀 Pour Tester

### 1. Démarrer le serveur
```bash
cd "c:\Users\33685\Desktop\Mon Chai V1"
python manage.py runserver
```

### 2. Accéder au dashboard
```
http://localhost:8000/dashboard/
```

### 3. Vérifier les métriques
- Volume récolté affiche les vendanges de la campagne en cours
- Volume en cuve affiche les stocks actuels
- CA affiche les factures de l'année en cours

---

## 🎨 Personnalisation Rapide

### Changer les couleurs des cartes

Éditer `templates/accounts/dashboard_viticole.html` :

```css
/* Carte Récolte - Remplacer par vos couleurs */
.metric-card.harvest {
    background: linear-gradient(135deg, #VOTRE_COULEUR_1 0%, #VOTRE_COULEUR_2 100%);
}

/* Carte Stock */
.metric-card.stock {
    background: linear-gradient(135deg, #VOTRE_COULEUR_1 0%, #VOTRE_COULEUR_2 100%);
}

/* Carte CA */
.metric-card.revenue {
    background: linear-gradient(135deg, #VOTRE_COULEUR_1 0%, #VOTRE_COULEUR_2 100%);
}
```

### Suggestions de Palettes

#### Palette 1 : Naturelle
```css
Récolte: #2ecc71 → #27ae60 (Vert)
Stock:   #e74c3c → #c0392b (Rouge)
CA:      #3498db → #2980b9 (Bleu)
```

#### Palette 2 : Élégante
```css
Récolte: #8e44ad → #9b59b6 (Violet)
Stock:   #e67e22 → #d35400 (Orange)
CA:      #16a085 → #1abc9c (Turquoise)
```

#### Palette 3 : Moderne
```css
Récolte: #34495e → #2c3e50 (Gris foncé)
Stock:   #e74c3c → #c0392b (Rouge)
CA:      #f39c12 → #f1c40f (Jaune)
```

---

## 📊 Exemple de Données

### Scénario Réaliste

```
Organisation: Domaine des Vignes
Campagne: 2025-2026

Vendanges:
- 15 réceptions
- 12 500 kg total
- 9 375 L de moût (rendement 75%)

Stocks:
- 15 lots actifs
- 14 375 L total en cuve
- Répartition: 5 cuves principales

Factures:
- 42 factures émises en 2025
- 125 000 € TTC
- 104 167 € HT
- 15 000 € impayés (12%)

Clients:
- 45 clients actifs
- 12 cuvées actives
- 8 commandes en cours
```

---

## ✅ Avantages du Nouveau Dashboard

### 1. Visibilité Immédiate
- ✅ 3 métriques clés en un coup d'œil
- ✅ Couleurs distinctives par métrique
- ✅ Valeurs grandes et lisibles

### 2. Design Moderne
- ✅ Dégradés élégants
- ✅ Effets hover fluides
- ✅ Icônes expressives

### 3. Données Temps Réel
- ✅ Calculs automatiques depuis la DB
- ✅ Mise à jour à chaque chargement
- ✅ Filtrage par organisation

### 4. Responsive
- ✅ Adapté mobile/tablet/desktop
- ✅ Grid flexible
- ✅ Tailles optimisées

### 5. Actions Rapides
- ✅ Accès direct aux modules
- ✅ Navigation fluide
- ✅ Gain de temps

---

*Aperçu créé le : 30/10/2024*
*Pour tester : http://localhost:8000/dashboard/*
