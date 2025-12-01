# 🍷 Spécificités Viticoles - Système de Ventes

## 📋 Spécificités Métier Identifiées

### 1. **VENTE EN PRIMEUR** ⭐ (Spécificité Majeure)

#### Définition
Vente de vin **avant sa mise en bouteille**, typiquement 18-24 mois avant livraison.

#### Caractéristiques
- **Paiement anticipé** : Client paie à la commande
- **Livraison différée** : 18-24 mois plus tard
- **Prix avantageux** : Réduction 20-30% vs prix final
- **Engagement ferme** : Commande non annulable
- **Millésime spécifique** : Ex: Primeur 2024 livré en 2026

#### Workflow Spécifique
```
1. Campagne Primeur (Avril-Juin N)
   ↓
2. Devis Primeur (prix réduit, millésime N)
   ↓
3. Commande Primeur (paiement immédiat)
   ↓ [Statut: en_elevage]
4. Attente 18-24 mois
   ↓
5. Mise en bouteille (N+2)
   ↓
6. Livraison (N+2)
   ↓ [Statut: delivered]
7. Facture définitive (déjà payé)
```

#### Données Requises
- `is_primeur`: Boolean
- `vintage_year`: Année du millésime
- `expected_delivery_date`: Date livraison prévue
- `primeur_campaign`: Campagne primeur (ex: "Primeur 2024")
- `primeur_discount_pct`: Remise primeur (ex: 25%)

---

### 2. **MILLÉSIMES**

#### Importance
Chaque millésime = produit différent avec prix différent.

#### Caractéristiques
- **Traçabilité obligatoire** : Millésime sur facture
- **Prix variables** : 2020 ≠ 2021 ≠ 2022
- **Stock par millésime** : Séparation stricte
- **Appellation + Millésime** : "Bordeaux Rouge 2020"

#### Données Requises
- `vintage_year` sur SKU et lignes de vente
- Affichage systématique du millésime
- Filtres par millésime dans recherche

---

### 3. **CONDITIONNEMENTS MULTIPLES**

#### Types de Conditionnements
- **Bouteille** : 75cl (standard)
- **Magnum** : 1,5L (2 bouteilles)
- **Jéroboam** : 3L (4 bouteilles)
- **Mathusalem** : 6L (8 bouteilles)
- **Salmanazar** : 9L (12 bouteilles)
- **Balthazar** : 12L (16 bouteilles)
- **Nabuchodonosor** : 15L (20 bouteilles)

#### Caractéristiques
- **Prix différents** : Magnum ≠ 2 × Bouteille
- **Stock séparé** : 10 bouteilles ≠ 5 magnums
- **Conversion** : 1 Magnum = 1,5L = 2 bouteilles
- **Étiquetage** : Affichage format sur documents

#### Données Requises
- `format` sur SKU (75cl, 150cl, 300cl...)
- `format_label` (Bouteille, Magnum, Jéroboam...)
- Conversion automatique en litres

---

### 4. **CARTONS ET CAISSES**

#### Types de Vente
- **À l'unité** : 1 bouteille
- **Carton de 6** : Prix dégressif
- **Carton de 12** : Prix dégressif
- **Palette** : 600 bouteilles (50 cartons)

#### Caractéristiques
- **Prix dégressifs** : 1 BT = 15€, 6 BT = 85€ (14,17€/BT), 12 BT = 160€ (13,33€/BT)
- **Conditionnement mixte** : Possibilité carton mixte (6 vins différents)
- **Frais de port** : Gratuit à partir de 12 bouteilles
- **Emballage** : Carton bois pour magnums

#### Données Requises
- Seuils de quantité avec remises (déjà existant via `PriceItem.min_qty`)
- `packaging_type`: unité, carton_6, carton_12, palette
- `packaging_notes`: Instructions emballage spécial

---

### 5. **APPELLATIONS ET CERTIFICATIONS**

#### Mentions Obligatoires
- **Appellation** : AOC Bordeaux, IGP Pays d'Oc...
- **Degré alcoolique** : 13,5% vol.
- **Contenance** : 75cl
- **Allergènes** : "Contient des sulfites"
- **Origine** : "Produit de France"
- **Lot** : Numéro de lot (traçabilité)

#### Caractéristiques
- **Affichage facture** : Mentions légales obligatoires
- **Export** : Mentions en anglais si export
- **Bio/Biodynamie** : Logos et certifications
- **Vegan** : Certification sans produits animaux

#### Données Requises
- `appellation` sur Cuvée
- `alcohol_degree` sur SKU
- `allergens` (défaut: sulfites)
- `certifications`: Bio, Biodynamie, Vegan, HVE...
- `lot_number` sur ligne de commande (traçabilité)

---

### 6. **LIVRAISONS SPÉCIFIQUES**

#### Types de Livraison
- **Retrait cave** : Gratuit, RDV
- **Livraison locale** : < 50km, 10€
- **Transporteur** : France, 15-25€
- **Export** : International, 50-200€
- **Coursier** : Paris, 20€, J+1

#### Caractéristiques
- **Température** : Transport réfrigéré en été
- **Assurance** : Obligatoire > 500€
- **Emballage** : Carton renforcé, calage
- **Signature** : Requise pour > 200€
- **Suivi** : Numéro de tracking

#### Données Requises
- `delivery_method`: retrait, local, transporteur, export, coursier
- `delivery_cost`: Frais de port
- `delivery_notes`: Instructions spéciales
- `tracking_number`: Suivi colis
- `requires_signature`: Boolean
- `temperature_controlled`: Boolean (été)

---

### 7. **ÉCHANTILLONS ET DÉGUSTATIONS**

#### Types
- **Échantillon gratuit** : 1 bouteille offerte
- **Dégustation** : Visite + dégustation
- **Coffret découverte** : 3 vins × 37,5cl
- **Abonnement** : 6 bouteilles/mois

#### Caractéristiques
- **Prix 0€** : Échantillon gratuit
- **Remise 100%** : Sur ligne spécifique
- **Suivi marketing** : Conversion échantillon → vente
- **Limite** : 1 échantillon/client/an

#### Données Requises
- `is_sample`: Boolean
- `sample_reason`: découverte, fidélité, pro...
- `sample_limit_reached`: Vérification

---

### 8. **CLIENTS PROFESSIONNELS**

#### Types de Clients Pro
- **Cavistes** : Revendeurs, remise 30-40%
- **Restaurants** : CHR, remise 25-35%
- **Grossistes** : Volume, remise 40-50%
- **Export** : Importateurs, remise 35-45%
- **Œnotourisme** : Hôtels, remise 20-30%

#### Caractéristiques
- **Grilles tarifaires** : Par segment client
- **Conditions paiement** : 30j, 60j, 90j
- **Remises quantité** : Paliers volume
- **TVA** : Autoliquidation UE
- **Documents** : Facture + DAE (export)

#### Données Requises
- `customer_segment`: particulier, caviste, restaurant, grossiste, export
- `payment_terms`: comptant, 30j, 60j, 90j
- `tax_regime`: normal, autoliquidation, export
- `requires_dae`: Boolean (Document Accompagnement Export)

---

### 9. **RÉGLEMENTATION ALCOOL**

#### Contraintes Légales
- **Âge minimum** : 18 ans (vérification)
- **Vente à distance** : Déclaration DGDDI
- **Droits d'accises** : Export hors UE
- **Capsules CRD** : Traçabilité fiscale
- **DRM** : Déclaration mensuelle

#### Caractéristiques
- **Vérification âge** : Checkbox obligatoire
- **Mentions légales** : "L'abus d'alcool est dangereux"
- **Interdiction** : Vente mineurs, publicité
- **Traçabilité** : Numéro CRD sur facture

#### Données Requises
- `age_verification`: Boolean (checkbox)
- `crd_number`: Numéro capsule CRD
- `legal_warnings`: Mentions obligatoires
- `drm_declaration`: Lien vers DRM

---

### 10. **ÉVÉNEMENTS ET CAMPAGNES**

#### Types d'Événements
- **Portes ouvertes** : Mai-Juin
- **Fête des vendanges** : Septembre
- **Salon des vins** : Novembre
- **Saint-Vincent** : Janvier
- **Primeur** : Avril-Juin

#### Caractéristiques
- **Promotions** : Remises événementielles
- **Packs** : Coffrets spéciaux
- **Réservations** : Visites + achats
- **Fidélité** : Points, cadeaux

#### Données Requises
- `campaign`: Nom de la campagne
- `event_date`: Date événement
- `promo_code`: Code promo
- `loyalty_points`: Points fidélité

---

### 11. **FISCALITÉ VITICOLE**

#### Taxes Spécifiques
- **TVA réduite** : 5,5% (vente à emporter)
- **TVA normale** : 20% (consommation sur place)
- **Droits d'accises** : Export hors UE
- **Taxe CVO** : Contribution volontaire obligatoire

#### Caractéristiques
- **Taux TVA variable** : Selon mode de vente
- **Exonération** : Export hors UE
- **Autoliquidation** : Pro UE avec TVA
- **Déclarations** : DRM, DGDDI

#### Données Requises
- `vat_rate`: 5.5%, 20%, 0% (export)
- `vat_regime`: normal, export, autoliquidation
- `excise_duty`: Droits d'accises (export)
- `cvo_amount`: Contribution CVO

---

### 12. **STOCK ET DISPONIBILITÉ**

#### Particularités
- **Stock limité** : Millésimes épuisables
- **Allocation** : Répartition clients VIP
- **Réservation** : Primeur, événements
- **Rupture** : Millésime épuisé définitivement

#### Caractéristiques
- **Alerte stock** : < 50 bouteilles
- **Dernières bouteilles** : Affichage urgence
- **Indisponible** : Millésime épuisé
- **Précommande** : Primeur, nouveautés

#### Données Requises
- `stock_status`: disponible, limité, épuisé, précommande
- `stock_alert_threshold`: Seuil alerte
- `allocation_priority`: VIP, pro, particulier
- `is_allocated`: Boolean (réservé)

---

## 🎯 Résumé des Spécificités Prioritaires

### Critiques (Must-Have)
1. ✅ **Vente en primeur** (livraison différée 18-24 mois)
2. ✅ **Millésimes** (traçabilité, prix variables)
3. ✅ **Conditionnements** (bouteille, magnum, jéroboam...)
4. ✅ **Prix dégressifs** (cartons 6/12)
5. ✅ **Appellations** (mentions légales)

### Importantes (Should-Have)
6. ✅ **Livraisons spécifiques** (retrait, transport, export)
7. ✅ **Clients pro** (cavistes, restaurants, grossistes)
8. ✅ **TVA viticole** (5,5% / 20% / export)
9. ✅ **Réglementation** (âge, CRD, DRM)
10. ✅ **Stock limité** (millésimes épuisables)

### Optionnelles (Nice-to-Have)
11. ⚪ **Échantillons** (gratuits, dégustations)
12. ⚪ **Événements** (campagnes, promotions)

---

## 📊 Impact sur les Modèles

### Extensions Requises

#### Quote / Order
```python
# Primeur
is_primeur = Boolean
vintage_year = Integer
expected_delivery_date = Date
primeur_campaign = CharField
primeur_discount_pct = Decimal

# Livraison
delivery_method = CharField (choices)
delivery_cost = Decimal
delivery_notes = TextField
tracking_number = CharField
requires_signature = Boolean
temperature_controlled = Boolean

# Réglementation
age_verification = Boolean
legal_warnings = TextField
campaign = CharField
```

#### QuoteLine / OrderLine
```python
# Millésime & Format
vintage_year = Integer
format = CharField (75cl, 150cl...)
format_label = CharField (Bouteille, Magnum...)

# Traçabilité
lot_number = CharField
crd_number = CharField
appellation = CharField
alcohol_degree = Decimal
certifications = JSONField

# Conditionnement
packaging_type = CharField
packaging_notes = TextField
is_sample = Boolean
```

#### Customer
```python
# Segment pro
customer_segment = CharField (choices)
payment_terms = CharField
tax_regime = CharField
requires_dae = Boolean
allocation_priority = Integer
```

#### SKU
```python
# Caractéristiques viticoles
vintage_year = Integer
format = CharField
format_label = CharField
appellation = ForeignKey
alcohol_degree = Decimal
allergens = CharField
certifications = JSONField
stock_status = CharField (choices)
```

---

## 🚀 Prochaines Étapes

1. **Étendre les modèles** avec champs viticoles
2. **Migration Django** pour ajout colonnes
3. **Formulaires adaptés** avec validations viticoles
4. **Templates spécialisés** (devis primeur, facture avec mentions)
5. **Workflows** (primeur, livraison différée)
6. **Tests** spécifiques viticoles
7. **Documentation** utilisateur

---

*Document créé le : 29/10/2024*
*Version : 1.0*
*Spécificités : 12 identifiées, 10 critiques/importantes*
