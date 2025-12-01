# Audit CSV Import/Export - État Actuel vs Roadmaps

## 📋 Résumé Exécutif

**Date**: 2025-09-22  
**Statut Global**: 🟡 **PARTIEL** - Foundation posée, implémentation complète requise  
**Conformité Roadmaps CSV 1-5**: 30% (foundation seulement)  
**Prochaines étapes**: Implémentation service générique selon spécifications

## 🔍 Audit Détaillé par Roadmap

### CSV_1 - Ingestion sécurisée & Prévisualisation
**Statut**: 🔴 **NON IMPLÉMENTÉ**

#### ❌ Manquant
- Endpoints `/import/:entity/upload` et `/import/:job_id/preview`
- Stockage temporaire sécurisé avec hash SHA-256
- Détection encodage/séparateur robuste
- Modèle `import_job` et `import_job_row`
- Sécurité anti-injection CSV
- Streaming upload (chunks 64-256 KB)

#### ✅ Existant (partiel)
- Service `CSVImportService` basique dans `apps/referentiels/csv_import.py`
- Configuration entités supportées (grape, parcelle, unite)
- Validation de base

### CSV_2 - Mapping des champs & Transformations
**Statut**: 🔴 **NON IMPLÉMENTÉ**

#### ❌ Manquant
- Dictionnaires de synonymes par entité
- Écran Mapping UI (drag/select)
- Transformations (trim, lower/upper, unaccent, regex, date parser)
- Endpoint `POST /import/:job_id/mapping`
- Persistance mapping par utilisateur
- Auto-mapping basé sur synonymes

#### ✅ Existant (partiel)
- Configuration champs requis/optionnels dans `SUPPORTED_TYPES`
- Validation unique_key basique

### CSV_3 - Dry-run : parsing, validations, lookups FK
**Statut**: 🔴 **NON IMPLÉMENTÉ**

#### ❌ Manquant
- Endpoint `POST /import/:job_id/dry-run`
- Moteur parsing streaming (chunks 5-10k lignes)
- Résolution FK avec trigram et seuils
- Exports `erreurs.csv`, `warnings.csv`
- Index optimisés pour lookups
- Cache LRU pour performances

#### ✅ Existant (partiel)
- Validation métier basique dans service existant
- Gestion des erreurs avec `CSVImportError`

### CSV_4 - Exécution réelle : upsert idempotent & transactions
**Statut**: 🔴 **NON IMPLÉMENTÉ**

#### ❌ Manquant
- Endpoint `POST /import/:job_id/execute` (async)
- Upsert idempotent par clé unique
- Transactions par chunk avec rollback
- Verrouillage logique anti-concurrence
- Polling `GET /import/:job_id/report`
- Métriques progression (inserted, updated, skipped, errors)

#### ✅ Existant (partiel)
- Transaction basique dans service existant
- Logique upsert simple

### CSV_5 - Rapports, Observabilité, Sécurité avancée
**Statut**: 🔴 **NON IMPLÉMENTÉ**

#### ❌ Manquant
- Rapports téléchargeables (erreurs.csv, warnings.csv)
- Dashboards et métriques (Prometheus/OpenTelemetry)
- Quotas/rate-limit par organisation
- CSRF protection pour POST
- Nettoyage automatique fichiers temporaires
- Runbook opérationnel

## 🚀 Export Service - État Actuel

### ✅ Implémenté (CSVExportService)
- **Service générique** dans `apps/referentiels/export_service.py`
- **5 entités supportées** : cepages, parcelles, unites, cuvees, entrepots
- **Sécurité anti-injection** : neutralisation cellules `= + - @ \t`
- **Configuration flexible** : encodage, séparateur, colonnes
- **Intégration views** : endpoints export par entité

#### Fonctionnalités Disponibles
```python
# Configuration entités
EXPORTABLE_ENTITIES = {
    'cepages': {
        'model': Cepage,
        'columns': ['nom', 'code', 'couleur', 'notes', 'created_at'],
        'headers': ['Nom', 'Code', 'Couleur', 'Notes', 'Date création'],
    },
    # ... autres entités
}

# Méthodes disponibles
def export_entity(entity_type, queryset, encoding='utf-8', delimiter=';')
def _neutralize_csv_injection(value)
def _format_value(value, field_name)
```

#### Endpoints Fonctionnels
- `GET /ref/cepages/export/` - Export cépages CSV
- Paramètres : `encoding`, `delimiter`
- Headers appropriés : `Content-Disposition: attachment`

### 🔴 Manquant Export
- **UI générique** : dialog sélection colonnes/encodage
- **Formats multiples** : XLSX, JSON
- **Quotas/rate-limit** : protection abus
- **Audit trail** : logs exports
- **Templates export** : sauvegarde configurations

## 📊 Analyse Conformité

### Roadmaps CSV 1-5 : 30% Conformité

| Roadmap | Statut | Conformité | Priorité |
|---------|--------|------------|----------|
| CSV_1 - Upload/Preview | 🔴 Non implémenté | 10% | **CRITIQUE** |
| CSV_2 - Mapping | 🔴 Non implémenté | 5% | **CRITIQUE** |
| CSV_3 - Dry-run | 🔴 Non implémenté | 15% | **CRITIQUE** |
| CSV_4 - Exécution | 🔴 Non implémenté | 20% | **CRITIQUE** |
| CSV_5 - Observabilité | 🔴 Non implémenté | 0% | **HAUTE** |

### Export Service : 70% Conformité

| Fonctionnalité | Statut | Conformité |
|----------------|--------|------------|
| Service générique | ✅ Implémenté | 100% |
| Anti-injection CSV | ✅ Implémenté | 100% |
| Multi-entités | ✅ Implémenté | 100% |
| Endpoints REST | ✅ Implémenté | 100% |
| UI générique | 🔴 Manquant | 0% |
| Formats multiples | 🔴 Manquant | 0% |
| Quotas/sécurité | 🔴 Manquant | 0% |

## 🎯 Foundation Existante - Points Forts

### Architecture Modulaire
- **App dédiée** : `apps/referentiels` avec services séparés
- **Configuration entités** : dictionnaires extensibles
- **Sécurité de base** : filtrage par organisation
- **Validation métier** : champs requis, types, contraintes

### Code Réutilisable
```python
# Service import existant (partiel)
class CSVImportService:
    SUPPORTED_TYPES = {
        'grape': {
            'model': Cepage,
            'fields': ['nom', 'couleur', 'code', 'notes'],
            'required': ['nom'],
            'unique_key': 'nom',
        }
    }

# Service export fonctionnel
class CSVExportService:
    def export_entity(self, entity_type, queryset, **options):
        # Implémentation complète avec sécurité
```

### Tests Partiels
- **Tests import** : `apps/referentiels/tests_csv_import.py`
- **Couverture basique** : validation, erreurs
- **Foundation** : structure pour tests complets

## 🚨 Gaps Critiques Identifiés

### 1. Architecture Service Import
- **Manque** : Service générique réutilisable toutes entités
- **Actuel** : Service spécifique référentiels seulement
- **Impact** : Pas de scalabilité pour clients, produits, ventes

### 2. Pipeline Complet Import
- **Manque** : 4 étapes (upload → mapping → dry-run → execute)
- **Actuel** : Import direct sans prévisualisation
- **Impact** : Pas de validation utilisateur, risque erreurs

### 3. UI/UX Import
- **Manque** : Interface utilisateur complète
- **Actuel** : Endpoints backend seulement
- **Impact** : Pas utilisable par utilisateurs finaux

### 4. Sécurité Avancée
- **Manque** : Quotas, rate-limit, streaming sécurisé
- **Actuel** : Sécurité de base (RLS, validation)
- **Impact** : Vulnérable à abus, fichiers volumineux

### 5. Observabilité
- **Manque** : Métriques, dashboards, audit trail
- **Actuel** : Logs basiques Django
- **Impact** : Pas de monitoring production

## 📋 Plan d'Action Recommandé

### Phase 1 - Service Générique (Roadmap Import 1)
1. **Créer app `imports`** dédiée
2. **Implémenter pipeline complet** : upload → preview → mapping → dry-run → execute
3. **Modèles** : `ImportJob`, `ImportJobRow`, `ImportMapping`
4. **Sécurité** : streaming, hash SHA-256, anti-injection

### Phase 2 - UI/UX Complète (Roadmap Import 2)
1. **Modal générique** réutilisable
2. **Écrans mapping** avec drag & drop
3. **Prévisualisation** avec transformations
4. **Rapports** téléchargeables

### Phase 3 - Intégration Pages (Integration Checklist)
1. **Boutons Import/Export** sur toutes pages listes
2. **Adapters entités** pour chaque référentiel
3. **Tests E2E** complets

### Phase 4 - Observabilité (Roadmap Import 5)
1. **Métriques** Prometheus
2. **Dashboards** Grafana
3. **Quotas/rate-limit**
4. **Runbook** opérationnel

## 🎉 Conclusion

La **foundation est solide** avec un service export fonctionnel et une architecture modulaire. Cependant, l'**implémentation complète des roadmaps CSV 1-5 est requise** pour avoir un système d'import/export production-ready.

**Priorité immédiate** : Implémenter le service générique d'import selon `import_service_spec.txt` et `integration_import_export_checklist.txt`.

**Impact utilisateur** : Passage d'un système basique à une solution complète permettant import/export sécurisé et convivial pour toutes les entités.

---
*Audit généré le 2025-09-22 - Analyse CSV Import/Export*
