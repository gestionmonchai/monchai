# DB Roadmap 01 - Cœur Viticole

## Vue d'ensemble

Implémentation du **modèle de données robuste** pour la production viticole selon la DB Roadmap 01.
Couvre les référentiels (cépages, appellations), ressources terrain (parcelles), produits (cuvées), et traçabilité des lots avec assemblages.

## Architecture

### Modèle de base : BaseViticultureModel

Tous les modèles héritent de `BaseViticultureModel` qui fournit :
- **UUID** comme clé primaire
- **organization** : Isolation par organisation (RLS logique)
- **row_version** : Locking optimiste pour éditions concurrentes
- **created_at/updated_at** : Timestamps automatiques
- **is_active** : Soft delete

```python
class BaseViticultureModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    row_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

## Schéma des données

### 1. Référentiels

#### GrapeVariety (Cépage)
- **Contraintes** : `UNIQUE(organization, name_norm)`
- **Validation** : Normalisation automatique du nom
- **Index** : organization+name_norm, organization+color

```python
# Exemple
cabernet = GrapeVariety.objects.create(
    organization=org,
    name="Cabernet Sauvignon",
    color="rouge"
)
```

#### Appellation
- **Contraintes** : `UNIQUE(organization, name_norm)`
- **Types** : AOC, IGP, VSIG, Autre
- **Index** : organization+name_norm, organization+type

#### Vintage (Millésime)
- **Contraintes** : `UNIQUE(organization, year)`, `CHECK(1900 <= year <= current_year+1)`
- **Validation** : Plage d'années cohérente

#### UnitOfMeasure (Unité de mesure)
- **Contraintes** : `UNIQUE(organization, code)`
- **Conversion** : `base_ratio_to_l` pour conversion en litres
- **Seeds** : L (1.0), hL (100.0), BT (0.75), MAG (1.5)

### 2. Ressources terrain

#### VineyardPlot (Parcelle de vignes)
- **Contraintes** : `UNIQUE(organization, name)`, `CHECK(area_ha > 0)`
- **FK same org** : grape_variety, appellation
- **Validation** : Année plantation cohérente (1900-current_year)

### 3. Produits

#### Cuvee
- **Contraintes** : `UNIQUE(organization, name)`
- **FK same org** : default_uom, appellation, vintage
- **Relations** : Liée aux lots via `lots` (related_name)

### 4. Traçabilité

#### Warehouse (Entrepôt)
- **Contraintes** : `UNIQUE(organization, name)`
- **Usage** : Localisation des lots

#### Lot (Lot de production)
- **Contraintes** : `UNIQUE(organization, code)`, `CHECK(volume_l >= 0)`
- **Statuts** : en_cours, élevage, stabilisé, embouteillé, archivé
- **FK same org** : cuvee, warehouse
- **Validation** : Degré alcool 0-20%

#### LotGrapeRatio (Composition cépages)
- **Contraintes** : `PK(lot, grape_variety)`, `CHECK(ratio_pct BETWEEN 0 AND 100)`
- **Règle métier** : SUM(ratio_pct) = 100 par lot (validée côté application)

#### LotAssemblage (Assemblage de lots)
- **Contraintes** : `PK(parent_lot, child_lot, created_at)`, `CHECK(volume_l > 0)`
- **Anti-cycle** : Validation DFS côté service (TODO)
- **Traçabilité** : Historique complet des assemblages

## Contraintes et validations

### Contraintes de base de données
- **UNIQUE** : Unicité par organisation sur noms/codes
- **CHECK** : Plages de valeurs (années, volumes, pourcentages)
- **FK PROTECT** : Protection contre suppression accidentelle

### Validations métier (clean())
- **Same organization** : Toutes les FK doivent appartenir à la même organisation
- **Normalisation** : name_norm automatique pour unicité insensible à la casse
- **Plages cohérentes** : Années, volumes, degrés d'alcool

### Locking optimiste
- **row_version** incrémenté à chaque sauvegarde
- **Conflit détecté** → 409 Conflict → UI propose refresh
- **Usage** : `obj.row_version` dans formulaires cachés

## Index et performances

### Index BTree (jointures fréquentes)
- `lot(cuvee_id)` : Lots par cuvée
- `vineyard_plot(grape_variety_id)` : Parcelles par cépage
- `cuvee(vintage_id, appellation_id)` : Cuvées par millésime/appellation

### Index composites (recherche)
- `(organization_id, name_norm)` : Recherche par nom
- `(organization_id, code)` : Recherche par code
- `(organization_id, status)` : Filtrage par statut

### Index FTS (optionnel)
- `cuvee(name, code)` → tsvector + GIN
- `grape_variety(name)` → trigram GIN pour fuzzy

## Seeds minimaux

Commande : `python manage.py create_viticulture_seeds`

### Unités de mesure
- **L** (Litre) : 1.0 - *défaut*
- **hL** (Hectolitre) : 100.0
- **BT** (Bouteille 75cl) : 0.75
- **MAG** (Magnum 1.5L) : 1.5

### Cépages démo
- **Rouges** : Cabernet Sauvignon, Merlot, Pinot Noir, Syrah
- **Blancs** : Chardonnay, Sauvignon Blanc

### Appellations
- **AOC** : Bordeaux, Côtes du Rhône, Languedoc
- **IGP** : Pays d'Oc
- **VSIG** : Vin de France

### Millésimes
- **Plage** : 2021-2026 (5 ans passés + courant + suivant)

### Infrastructure
- **Entrepôt** : "Chai principal"

## Règles métier

### Composition des lots
1. **Ratios cépages** : SUM(ratio_pct) = 100% par lot
2. **Validation** : Côté application (pas contrainte DB)
3. **Flexibilité** : Permet assemblages complexes

### Assemblages
1. **Anti-cycle** : Un lot ne peut pas s'assembler avec lui-même
2. **Traçabilité** : Historique complet parent ← enfant
3. **Volumes** : Volume assemblé > 0

### Life-cycle d'un lot
```
Moût → En cours → Élevage → Stabilisé → Embouteillé → Archivé
```

## Tests de robustesse

### Contraintes d'unicité
```python
# Doit lever IntegrityError → ValidationError
GrapeVariety.objects.create(
    organization=org,
    name="Cabernet Sauvignon",  # Doublon
    color="rouge"
)
```

### Validation plages
```python
# Doit lever ValidationError
Vintage.objects.create(
    organization=org,
    year=3000  # Hors plage
)
```

### FK cross-org
```python
# Doit lever ValidationError
VineyardPlot.objects.create(
    organization=org1,
    grape_variety=grape_from_org2  # Différente org
)
```

### Locking optimiste
```python
# Simulation conflit concurrent
lot1 = Lot.objects.get(id=lot_id)
lot2 = Lot.objects.get(id=lot_id)

lot1.volume_l = 1000
lot1.save()  # row_version = 2

lot2.volume_l = 1500
lot2.save()  # Doit détecter conflit row_version
```

## Migration et déploiement

### Ordre des migrations
1. **Référentiels** : grape_variety, appellation, vintage, unit_of_measure
2. **Ressources terrain** : vineyard_plot
3. **Produits** : cuvee
4. **Lots & assemblages** : lot, lot_grape_ratio, lot_assemblage
5. **Index FTS/trigram** (si activés)
6. **Seeds**

### Commandes de déploiement
```bash
# Migrations
python manage.py migrate viticulture

# Seeds minimaux
python manage.py create_viticulture_seeds

# Vérification
python manage.py shell -c "
from apps.viticulture.models import *
print(f'Cépages: {GrapeVariety.objects.count()}')
print(f'UoM: {UnitOfMeasure.objects.count()}')
"
```

## Conformité roadmap

✅ **Tables normalisées** avec contraintes fortes (FK, unique, check)  
✅ **row_version** pour locking optimiste  
✅ **Index** alignés sur recherche & jointures  
✅ **Seeds minimaux** (UoM L/hL/BT ; cépages démo)  
✅ **RLS logique** par organisation  
✅ **Règles de qualité** (plage millésime, validation cépages)  
✅ **Dev Book** : schéma, dictionnaire, règles  

**Status** : DB Roadmap 01 - ✅ TERMINÉE

---

*Dernière mise à jour : 2025-09-21*
