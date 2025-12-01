# Sprint 14 - Système Import/Export Générique

## 📋 Résumé Exécutif

**Statut**: 🚧 **EN COURS**  
**Objectif**: Implémenter système complet import/export selon roadmaps CSV 1-5  
**Foundation**: Service export fonctionnel, service import partiel  
**Cible**: Service générique réutilisable toutes entités

## 🎯 Objectifs Sprint 14

### Phase 1 - Service Import Générique ✅ PLANIFIÉ
- **App dédiée** : `apps/imports` avec modèles complets
- **Pipeline 5 étapes** : upload → preview → mapping → dry-run → execute
- **Sécurité** : streaming, hash SHA-256, anti-injection CSV
- **Modèles** : `ImportJob`, `ImportJobRow`, `ImportMapping`

### Phase 2 - UI/UX Complète 🎯 CIBLE
- **Modal générique** réutilisable toutes entités
- **Écrans mapping** avec drag & drop
- **Prévisualisation** temps réel avec transformations
- **Rapports** téléchargeables (erreurs.csv, warnings.csv)

### Phase 3 - Intégration Pages 🎯 CIBLE
- **Boutons Import/Export** sur toutes pages listes
- **Adapters entités** configurables
- **Tests E2E** complets (Playwright)

## 🏗️ Architecture Cible

### App Imports Structure
```
apps/imports/
├── models.py              # ImportJob, ImportJobRow, ImportMapping
├── services/
│   ├── upload_service.py   # CSV_1: Upload & Preview
│   ├── mapping_service.py  # CSV_2: Mapping & Transformations
│   ├── dryrun_service.py   # CSV_3: Validation & FK Lookup
│   ├── execute_service.py  # CSV_4: Upsert Idempotent
│   └── report_service.py   # CSV_5: Rapports & Observabilité
├── adapters/
│   ├── base.py            # Adapter générique
│   ├── grape_variety.py   # Adapter cépages
│   ├── parcelle.py        # Adapter parcelles
│   └── unite.py           # Adapter unités
├── views.py               # Endpoints REST API
├── urls.py                # Routes /import/*
└── templates/imports/     # UI générique
```

### Modèles Cibles
```python
class ImportJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization)
    entity = models.CharField(max_length=50)  # 'grape_variety', 'parcelle'
    filename = models.CharField(max_length=255)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    status = models.CharField(choices=STATUS_CHOICES, default='uploaded')
    total_rows = models.PositiveIntegerField(null=True)
    created_by = models.ForeignKey(User)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    
    # Métriques
    inserted_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)

class ImportJobRow(models.Model):
    job = models.ForeignKey(ImportJob, related_name='rows')
    row_index = models.PositiveIntegerField()
    status = models.CharField(choices=['ok', 'warning', 'error'])
    field = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    suggestion = models.TextField(blank=True)
    raw_data = models.JSONField()  # Données ligne originale
    processed_data = models.JSONField(null=True)  # Après transformations

class ImportMapping(models.Model):
    job = models.ForeignKey(ImportJob, related_name='mappings')
    csv_column = models.CharField(max_length=100)
    entity_field = models.CharField(max_length=100)
    transforms = models.JSONField(default=list)  # ['trim', 'unaccent']
    options = models.JSONField(default=dict)
```

## 🔧 Services Détaillés

### UploadService (CSV_1)
```python
class UploadService:
    """Ingestion sécurisée & Prévisualisation"""
    
    def upload_file(self, file, entity, organization, user):
        # Validation sécurité
        self._validate_file_security(file)
        
        # Stockage temporaire
        job = self._create_import_job(file, entity, organization, user)
        file_path = self._store_temporary_file(file, job)
        
        # Hash SHA-256
        job.sha256 = self._calculate_sha256(file_path)
        job.save()
        
        return job
    
    def preview_file(self, job_id, rows=10, sheet=0):
        # Détection encodage/séparateur
        detected = self._detect_file_format(job.file_path)
        
        # Lecture streaming sécurisée
        sample_data = self._read_sample_data(job.file_path, rows, detected)
        
        # Anti-injection CSV
        sample_data = self._neutralize_csv_injection(sample_data)
        
        return {
            'header': sample_data[0] if detected['has_header'] else [],
            'sample': sample_data[1:] if detected['has_header'] else sample_data,
            'detected': detected,
            'warnings': self._generate_warnings(detected)
        }
```

### MappingService (CSV_2)
```python
class MappingService:
    """Mapping des champs & Transformations"""
    
    def get_entity_schema(self, entity):
        adapter = self._get_adapter(entity)
        return adapter.get_schema()
    
    def auto_map_columns(self, job_id, csv_columns):
        schema = self.get_entity_schema(job.entity)
        mapping = {}
        
        for csv_col in csv_columns:
            # Recherche par synonymes
            field = self._find_field_by_synonyms(csv_col, schema['synonyms'])
            if field:
                mapping[csv_col] = {
                    'field': field,
                    'transforms': schema['transforms_defaults'].get(field, []),
                    'confidence': self._calculate_confidence(csv_col, field)
                }
        
        return mapping
    
    def save_mapping(self, job_id, mapping):
        # Validation mapping
        self._validate_mapping(job.entity, mapping)
        
        # Sauvegarde
        ImportMapping.objects.filter(job_id=job_id).delete()
        for csv_col, config in mapping.items():
            ImportMapping.objects.create(
                job_id=job_id,
                csv_column=csv_col,
                entity_field=config['field'],
                transforms=config['transforms'],
                options=config.get('options', {})
            )
```

## 🎨 UI/UX Générique

### Modal Import Réutilisable
```html
<!-- templates/imports/modal_import.html -->
<div class="modal fade" id="importModal" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-upload me-2"></i>
                    Importer {{ entity_display_name }}
                </h5>
            </div>
            <div class="modal-body">
                <!-- Étapes navigation -->
                <div class="import-steps mb-4">
                    <div class="step active" data-step="upload">1. Upload</div>
                    <div class="step" data-step="preview">2. Aperçu</div>
                    <div class="step" data-step="mapping">3. Mapping</div>
                    <div class="step" data-step="dryrun">4. Validation</div>
                    <div class="step" data-step="execute">5. Import</div>
                </div>
                
                <!-- Contenu dynamique par étape -->
                <div id="step-content">
                    <!-- Chargé via AJAX selon étape -->
                </div>
            </div>
        </div>
    </div>
</div>
```

### JavaScript Générique
```javascript
// static/js/import-modal.js
class ImportModal {
    constructor(entity, entityDisplayName) {
        this.entity = entity;
        this.entityDisplayName = entityDisplayName;
        this.currentStep = 'upload';
        this.jobId = null;
    }
    
    open() {
        $('#importModal').modal('show');
        this.loadStep('upload');
    }
    
    async loadStep(step) {
        const response = await fetch(`/import/ui/${step}/`, {
            method: 'GET',
            headers: {
                'X-Entity': this.entity,
                'X-Job-Id': this.jobId || ''
            }
        });
        
        const html = await response.text();
        document.getElementById('step-content').innerHTML = html;
        this.updateStepNavigation(step);
    }
    
    async uploadFile(formData) {
        const response = await fetch(`/import/${this.entity}/upload/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        this.jobId = result.job_id;
        this.loadStep('preview');
    }
}
```

## 📊 Intégration Pages Listes

### Boutons Import/Export
```html
<!-- templates/referentiels/cepage_list.html -->
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>
        <i class="bi bi-flower1 me-2 text-success"></i>Cépages
    </h1>
    <div>
        <!-- Boutons Import/Export -->
        <div class="btn-group me-2">
            <button type="button" class="btn btn-outline-primary" 
                    onclick="openImportModal('grape_variety', 'Cépages')">
                <i class="bi bi-upload"></i> Importer
            </button>
            <button type="button" class="btn btn-outline-secondary"
                    onclick="openExportDialog('cepages')">
                <i class="bi bi-download"></i> Exporter
            </button>
        </div>
        
        <!-- Boutons existants -->
        <a href="{% url 'referentiels:home' %}" class="btn btn-outline-secondary me-2">
            <i class="bi bi-arrow-left"></i> Référentiels
        </a>
        {% if user.get_active_membership.can_edit_data %}
            <a href="{% url 'referentiels:cepage_create' %}" class="btn btn-primary">
                <i class="bi bi-plus"></i> Nouveau cépage
            </a>
        {% endif %}
    </div>
</div>
```

## 🔒 Sécurité & Performance

### Anti-Injection CSV
```python
def neutralize_csv_injection(value):
    """Neutralise les formules CSV dangereuses"""
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t')):
        return f"'{value}"
    return value
```

### Streaming Upload
```python
def handle_large_file_upload(file, max_size=10*1024*1024):
    """Upload streaming pour fichiers volumineux"""
    if file.size > max_size:
        raise ValidationError(f"Fichier trop volumineux: {file.size} > {max_size}")
    
    hasher = hashlib.sha256()
    total_size = 0
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in file.chunks(chunk_size=64*1024):
            temp_file.write(chunk)
            hasher.update(chunk)
            total_size += len(chunk)
            
            if total_size > max_size:
                os.unlink(temp_file.name)
                raise ValidationError("Fichier trop volumineux")
    
    return temp_file.name, hasher.hexdigest()
```

## 📈 Métriques & Observabilité

### Métriques Prometheus
```python
from prometheus_client import Counter, Histogram, Gauge

# Métriques import
import_duration = Histogram('import_duration_seconds', 'Durée import', ['entity', 'stage'])
import_rows_total = Counter('import_rows_total', 'Lignes importées', ['entity', 'status'])
import_errors_total = Counter('import_errors_total', 'Erreurs import', ['entity', 'error_type'])
lookup_ambiguous_total = Counter('lookup_ambiguous_total', 'Lookups ambigus', ['entity', 'field'])

# Métriques export
export_duration = Histogram('export_duration_seconds', 'Durée export', ['entity'])
export_rows_total = Counter('export_rows_total', 'Lignes exportées', ['entity'])
```

## ✅ Plan d'Implémentation

### Étape 1 - Foundation (Aujourd'hui)
- [x] **Audit complet** CSV 1-5 vs existant
- [x] **Documentation** architecture cible
- [ ] **App imports** : création structure
- [ ] **Modèles** : ImportJob, ImportJobRow, ImportMapping

### Étape 2 - Services Core
- [ ] **UploadService** : upload sécurisé + preview
- [ ] **MappingService** : auto-mapping + transformations
- [ ] **DryRunService** : validation + FK lookup
- [ ] **ExecuteService** : upsert idempotent

### Étape 3 - UI/UX
- [ ] **Modal générique** réutilisable
- [ ] **Écrans mapping** interactifs
- [ ] **Rapports** téléchargeables
- [ ] **JavaScript** générique

### Étape 4 - Intégration
- [ ] **Boutons** sur toutes pages listes
- [ ] **Adapters** pour chaque entité
- [ ] **Tests E2E** complets

### Étape 5 - Production
- [ ] **Métriques** Prometheus
- [ ] **Quotas/rate-limit**
- [ ] **Runbook** opérationnel

## 🎉 Impact Attendu

### Utilisateurs Finaux
- **Import convivial** : 5 étapes guidées avec prévisualisation
- **Sécurité** : validation complète avant import effectif
- **Flexibilité** : mapping personnalisable, transformations
- **Feedback** : rapports détaillés, suggestions d'amélioration

### Développeurs
- **Réutilisabilité** : service générique pour toutes entités
- **Extensibilité** : adapters configurables
- **Maintenabilité** : architecture modulaire
- **Observabilité** : métriques et logs structurés

### Opérations
- **Monitoring** : dashboards temps réel
- **Sécurité** : quotas, rate-limit, audit trail
- **Performance** : streaming, cache, index optimisés
- **Fiabilité** : transactions, idempotence, reprise

---
*Sprint 14 - Système Import/Export Générique - 2025-09-22*
