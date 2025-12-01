# 📄 SYSTÈME D'ÉDITION DE DOCUMENTS RÉUTILISABLE

## 🎯 Vue d'Ensemble

Système complet d'édition et de génération de documents (devis, factures, commandes, bons de livraison, etc.) entièrement réutilisable et extensible.

### ✨ Fonctionnalités

✅ **Éditeur WYSIWYG avec CodeMirror**
- Coloration syntaxique HTML/CSS
- Auto-complétion
- Thème Monokai élégant
- Édition en temps réel

✅ **Variables dynamiques**
- Organisation, Client, Document, Totaux
- Système de templates Jinja2
- Insertion par clic depuis une palette
- Filtres personnalisés (currency, date_format, etc.)

✅ **Templates prédéfinis**
- Devis standard
- Facture avec mentions légales
- Bon de commande
- Bon de livraison
- Créez vos propres templates

✅ **Génération PDF**
- Export PDF via WeasyPrint
- Mise en page professionnelle
- CSS personnalisable
- Format A4/Letter/A5

✅ **Prévisualisation en temps réel**
- Aperçu avant publication
- Données fictives pour test
- Iframe responsive

✅ **Gestion multi-templates**
- Template par défaut par type
- Duplication de templates
- Historique des versions
- Organisation multi-tenant

---

## 🏗️ Architecture Technique

### Modèles

#### 1. DocumentTemplate
```python
- name: Nom du template
- document_type: quote, invoice, order, delivery, etc.
- html_header: En-tête HTML
- html_body: Corps HTML
- html_footer: Pied de page HTML
- custom_css: Styles personnalisés
- is_default: Template par défaut
- paper_size: A4, Letter, A5
- orientation: portrait, landscape
- margins: top, bottom, left, right
```

#### 2. DocumentPreset
```python
- name: Nom du preset
- primary_color: Couleur primaire (#8B1538)
- secondary_color: Couleur secondaire (#d4af37)
- font_family: Police principale
- font_size_base: Taille de base
- generated_css: CSS auto-généré
```

### Moteur de Rendu

**DocumentRenderer** (`document_renderer.py`)
```python
- prepare_context(): Prépare les variables
- render_html(): Génère le HTML final
- generate_pdf(): Crée le PDF
```

**Filtres Jinja2 disponibles** :
- `currency`: Formate les montants (250.00 EUR)
- `date_format`: Formate les dates (03/11/2025)
- `percentage`: Formate les pourcentages (20%)

### Variables Disponibles

#### Organisation
```jinja2
{{ organization.name }}
{{ organization.address }}
{{ organization.postal_code }}
{{ organization.city }}
{{ organization.country }}
{{ organization.phone }}
{{ organization.email }}
{{ organization.website }}
{{ organization.vat_number }}
{{ organization.siret }}
```

#### Client
```jinja2
{{ customer.legal_name }}
{{ customer.billing_address }}
{{ customer.billing_postal_code }}
{{ customer.billing_city }}
{{ customer.billing_country }}
{{ customer.vat_number }}
```

#### Document
```jinja2
{{ document.number }}
{{ document.date|date_format }}
{{ document.date_issue|date_format }}
{{ document.valid_until|date_format }}
{{ document.due_date|date_format }}
{{ document.currency }}
{{ document.status }}
```

#### Totaux
```jinja2
{{ totals.total_ht|currency }}
{{ totals.total_tax|currency }}
{{ totals.total_ttc|currency }}
```

#### Lignes (boucle)
```jinja2
{% for line in lines %}
  <tr>
    <td>{{ line.description }}</td>
    <td>{{ line.qty }}</td>
    <td>{{ line.unit_price|currency }}</td>
    <td>{{ line.total_ht|currency }}</td>
  </tr>
{% endfor %}
```

---

## 📁 Fichiers Créés

### Backend
```
apps/sales/
├── models_documents.py          # Modèles DocumentTemplate, DocumentPreset
├── document_renderer.py         # Moteur de rendu et génération PDF
├── default_templates.py         # Templates prédéfinis (devis, facture, etc.)
├── views_documents.py           # Vues CRUD pour templates
├── admin_documents.py           # Admin Django
└── migrations/
    └── 0004_documentpreset_documenttemplate.py
```

### Frontend
```
templates/sales/templates/
├── template_list.html           # Liste des templates
├── template_form.html           # Éditeur avec CodeMirror
├── template_detail.html         # Détail d'un template
└── template_confirm_delete.html # Confirmation suppression
```

### URLs
```
/clients/templates/                              # Liste
/clients/templates/creer/                        # Créer
/clients/templates/<uuid>/                       # Détail
/clients/templates/<uuid>/modifier/              # Éditer
/clients/templates/<uuid>/supprimer/             # Supprimer
/clients/templates/<uuid>/dupliquer/             # Dupliquer
/clients/templates/<uuid>/apercu/                # Prévisualiser
/clients/templates/<uuid>/pdf/<type>/<doc_id>/   # Générer PDF
/clients/templates/<uuid>/variables/             # Aide variables (AJAX)
```

---

## 🚀 Utilisation

### 1. Créer un Template

```bash
# Via l'interface
http://127.0.0.1:8000/clients/templates/creer/

# Ou par code
from apps.sales.models_documents import DocumentTemplate

template = DocumentTemplate.objects.create(
    organization=org,
    name="Mon Devis Personnalisé",
    document_type="quote",
    is_default=True,
    html_header="<h1>{{ organization.name }}</h1>",
    html_body="<table>...</table>",
    html_footer="<p>Merci de votre confiance</p>",
)
```

### 2. Utiliser un Template

```python
from apps.sales.document_renderer import DocumentRenderer, DocumentHelper
from apps.sales.models import Quote

# Récupérer le template par défaut
template = DocumentHelper.get_default_template(organization, 'quote')

# Générer le HTML
quote = Quote.objects.get(id=quote_id)
renderer = DocumentRenderer(template)
html = renderer.render_html(quote, organization)

# Générer le PDF
pdf_bytes = renderer.generate_pdf(quote, organization)

# Enregistrer le PDF
with open('devis.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

### 3. Ajouter un Bouton "Générer PDF" dans une Vue

```html
<!-- Dans template_detail.html d'un devis -->
<a href="{% url 'sales:template_generate_pdf' pk=template.id doc_type='quote' doc_id=quote.id %}" 
   class="btn btn-danger">
    <i class="bi bi-file-pdf"></i> Télécharger PDF
</a>
```

### 4. Intégrer dans les Vues Existantes

```python
# Dans views_invoices.py ou views_orders.py
from apps.sales.document_renderer import DocumentRenderer, DocumentHelper

@login_required
def invoice_pdf(request, pk):
    org = request.current_org
    invoice = get_object_or_404(Invoice, id=pk, organization=org)
    
    # Récupérer le template
    template = DocumentHelper.get_default_template(org, 'invoice')
    
    # Générer le PDF
    renderer = DocumentRenderer(template)
    pdf_bytes = renderer.generate_pdf(invoice, org)
    
    # Retourner le PDF
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{invoice.number}.pdf"'
    return response
```

---

## 🎨 Personnalisation Avancée

### Créer un Template Viticole

```html
<!-- Header -->
<div style="background: linear-gradient(135deg, #8B1538 0%, #722f37 100%); padding: 30px; color: white;">
    <h1>🍷 {{ organization.name }}</h1>
    <p>{{ organization.address }}, {{ organization.postal_code }} {{ organization.city }}</p>
</div>

<!-- Body avec tableau élégant -->
<table style="width: 100%; margin-top: 30px;">
    <thead style="background: #d4af37; color: #722f37;">
        <tr>
            <th>Cuvée</th>
            <th>Millésime</th>
            <th>Qté</th>
            <th>Prix</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td>{{ line.vintage_year|default:'-' }}</td>
            <td>{{ line.qty }}</td>
            <td>{{ line.unit_price|currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Totaux avec design viticole -->
<div style="margin-top: 40px; padding: 20px; background: #f7e7ce; border-left: 5px solid #d4af37;">
    <h3 style="color: #8B1538;">Total : {{ totals.total_ttc|currency }}</h3>
</div>
```

### CSS Personnalisé

```css
/* Dans custom_css */
:root {
    --wine-bordeaux: #8B1538;
    --wine-gold: #d4af37;
}

body {
    font-family: 'Georgia', serif;
}

h1, h2 {
    color: var(--wine-bordeaux);
    border-bottom: 2px solid var(--wine-gold);
}

.highlight {
    background: var(--wine-gold);
    padding: 2px 8px;
    border-radius: 4px;
}

table {
    border-collapse: collapse;
}

table thead th {
    background: var(--wine-bordeaux);
    color: white;
}

.footer {
    font-size: 8pt;
    color: #666;
    text-align: center;
    margin-top: 50px;
}
```

---

## 📦 Dépendances

### Installer WeasyPrint pour la génération PDF

```bash
# Windows
pip install weasyprint

# Dépendances système Windows (GTK3)
# Télécharger GTK3 : https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

# Linux (Ubuntu/Debian)
sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
pip install weasyprint

# macOS
brew install python3 cairo pango gdk-pixbuf libffi
pip install weasyprint
```

---

## 🔧 Configuration

### Settings Django

```python
# settings.py

# Jinja2 pour les templates de documents
TEMPLATES = [
    # ... existing templates ...
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'apps.sales.jinja2.environment',
        },
    },
]
```

### Fonction Environment Jinja2

```python
# apps/sales/jinja2.py
from jinja2 import Environment

def environment(**options):
    env = Environment(**options)
    
    # Ajouter des filtres globaux
    env.filters['currency'] = lambda value: f"{value:,.2f} €"
    env.filters['date_format'] = lambda value: value.strftime('%d/%m/%Y')
    
    return env
```

---

## 🧪 Tests

### Tester le Rendu

```python
from apps.sales.document_renderer import DocumentRenderer
from apps.sales.models_documents import DocumentTemplate
from apps.sales.models import Quote

# Créer un template de test
template = DocumentTemplate.objects.create(
    organization=org,
    name="Test",
    document_type="quote",
    html_body="Total: {{ totals.total_ttc|currency }}",
)

# Tester le rendu
quote = Quote.objects.first()
renderer = DocumentRenderer(template)
html = renderer.render_html(quote, org)

assert 'Total:' in html
assert '€' in html
```

### Tester la Génération PDF

```python
# Tester que le PDF est généré sans erreur
renderer = DocumentRenderer(template)
pdf_bytes = renderer.generate_pdf(quote, org)

assert len(pdf_bytes) > 0
assert pdf_bytes[:4] == b'%PDF'  # Signature PDF
```

---

## 🔐 Sécurité & Permissions

### Permissions par Rôle

| Action | read_only | editor | admin | owner |
|--------|-----------|--------|-------|-------|
| Lister templates | ✅ | ✅ | ✅ | ✅ |
| Voir détail | ✅ | ✅ | ✅ | ✅ |
| Prévisualiser | ✅ | ✅ | ✅ | ✅ |
| Générer PDF | ✅ | ✅ | ✅ | ✅ |
| Créer template | ❌ | ❌ | ✅ | ✅ |
| Modifier template | ❌ | ❌ | ✅ | ✅ |
| Supprimer template | ❌ | ❌ | ✅ | ✅ |
| Dupliquer template | ❌ | ❌ | ✅ | ✅ |

### Isolation Multi-Tenant

Tous les templates sont isolés par `organization` :
```python
# Filtrage automatique dans les vues
template = get_object_or_404(
    DocumentTemplate,
    id=pk,
    organization=request.current_org  # RLS
)
```

---

## 📊 Exemples de Templates

### Devis avec Conditions

```html
<h1>DEVIS N° {{ document.number }}</h1>

<div class="client-box">
    <strong>Client :</strong><br>
    {{ customer.legal_name }}<br>
    {{ customer.billing_address }}
</div>

<table>
    <thead>
        <tr>
            <th>Produit</th>
            <th>Qté</th>
            <th>P.U. HT</th>
            <th>Total HT</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td>{{ line.qty }}</td>
            <td>{{ line.unit_price|currency }}</td>
            <td>{{ line.total_ht|currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="totals">
    <p>Total HT : {{ totals.total_ht|currency }}</p>
    <p>TVA : {{ totals.total_tax|currency }}</p>
    <p><strong>Total TTC : {{ totals.total_ttc|currency }}</strong></p>
</div>

<div class="conditions">
    <h3>Conditions</h3>
    <p>Devis valable jusqu'au {{ document.valid_until|date_format }}</p>
    <p>Acompte de 30% à la commande</p>
    <p>Solde à la livraison</p>
</div>
```

### Facture avec Mentions Légales

```html
<h1>FACTURE N° {{ document.number }}</h1>

<div class="info">
    <p>Date : {{ document.date_issue|date_format }}</p>
    <p>Échéance : {{ document.due_date|date_format }}</p>
</div>

<!-- ... contenu similaire au devis ... -->

<div class="legal">
    <small>
    En cas de retard de paiement, pénalité de 3 fois le taux d'intérêt légal.<br>
    Indemnité forfaitaire pour frais de recouvrement : 40 €.<br>
    {{ organization.name }} - SIRET : {{ organization.siret }}<br>
    TVA : {{ organization.vat_number }}
    </small>
</div>
```

---

## 🚀 Roadmap Future

### Version 2.0
- [ ] Éditeur drag-and-drop WYSIWYG complet
- [ ] Bibliothèque de blocs réutilisables
- [ ] Import/Export de templates
- [ ] Versioning automatique
- [ ] Prévisualisation multi-device

### Version 2.1
- [ ] Génération de documents en masse (batch)
- [ ] Envoi automatique par email
- [ ] Signature électronique intégrée
- [ ] Traductions multi-langues
- [ ] Templates conditionnels (if client VIP)

---

## 📞 Support

**Documentation** : `/clients/templates/` → Bouton "Variables disponibles"

**Admin Django** : `/admin/sales/documenttemplate/`

**Logs** : Voir `document_renderer.py` ligne 30-40 pour les erreurs de rendu

---

## ✅ Checklist de Déploiement

- [x] Migrations appliquées (`python manage.py migrate`)
- [x] WeasyPrint installé
- [ ] Templates par défaut créés (auto-créés au premier accès)
- [ ] Permissions configurées (décorateurs `@require_membership`)
- [ ] Tests de génération PDF effectués
- [ ] CSS viticole appliqué
- [ ] Variables documentées

---

**Le système est maintenant prêt à être utilisé pour tous vos documents ! 🎉**

**Accès** : http://127.0.0.1:8000/clients/templates/
