# Plan de consolidation de la base de données MonChai

## État actuel après nettoyage

- **Modèles totaux**: 147
- **Migrations**: Toutes appliquées
- **Check Django**: 0 issues

## Doublons identifiés (consolidation future)

### 1. Customer (PRIORITÉ HAUTE)

| Modèle | Enregistrements | Usage |
|--------|-----------------|-------|
| `partners.Partner` | 14 | App unifiée Tiers (clients/fournisseurs) |
| `sales.Customer` | 1 | Utilisé par Quote (3), Order (0) |

**Action recommandée**: Migrer les FK de `sales.Customer` vers `partners.Partner` puis supprimer `sales.Customer`.

**Risque**: Les modèles Quote et Order référencent sales.Customer. Nécessite migration de données.

### 2. Cuvee (PRIORITÉ MOYENNE)

| Modèle | Enregistrements | Usage |
|--------|-----------------|-------|
| `referentiels.Cuvee` | 3 | Référentiel simple |
| `viticulture.Cuvee` | 10 | Modèle complet avec détails |

**Action recommandée**: Consolider vers `viticulture.Cuvee` qui est plus complet. Migrer les FK depuis `referentiels.Cuvee`.

**Risque**: VendangeReception et LotTechnique référencent referentiels.Cuvee.

### 3. SKU (À ÉVALUER)

| Modèle | Usage |
|--------|-------|
| `produits.SKU` | Variantes vendables (catalogue) |
| `stock.SKU` | Gestion des stocks |

**Note**: Ces deux modèles semblent avoir des usages distincts. Évaluer si une consolidation est pertinente.

### 4. Parcelle (RÉSOLU ✅)

| Modèle | Statut |
|--------|--------|
| `production.Parcelle` | **SUPPRIMÉ** (migration 0022) |
| `referentiels.Parcelle` | Principal |
| `giscore.Parcelle` | Données GIS |

## Modèles supprimés

- `production.Parcelle` - Migration 0022 (0 enregistrements, non utilisé)

## Prochaines étapes

1. [ ] Planifier migration sales.Customer → partners.Partner
2. [ ] Planifier consolidation Cuvee
3. [ ] Évaluer nécessité de consolider SKU
4. [ ] Nettoyer migrations obsolètes après consolidation
