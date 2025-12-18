"""
Vues pour l'édition et la gestion des templates de documents
"""
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import require_membership
from apps.sales.models_documents import DocumentTemplate, DocumentPreset
from apps.sales.document_renderer import DocumentRenderer, DocumentHelper
from apps.sales.models import Quote
from apps.billing.models import Invoice


@login_required
@require_membership('read_only')
def template_list(request):
    """
    Liste des templates de documents
    """
    org = request.current_org
    
    # Filtres
    doc_type = request.GET.get('type', '')
    search = request.GET.get('search', '').strip()
    
    qs = DocumentTemplate.objects.filter(organization=org)
    
    if doc_type:
        qs = qs.filter(document_type=doc_type)
    
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Types de documents pour le filtre
    doc_types = DocumentTemplate.DOCUMENT_TYPES
    
    return render(request, 'sales/templates/template_list.html', {
        'page_obj': page_obj,
        'doc_types': doc_types,
        'selected_type': doc_type,
        'search': search,
    })


@login_required
@require_membership('admin')
def template_create(request):
    """
    Création d'un nouveau template
    """
    org = request.current_org
    
    if request.method == 'POST':
        try:
            template = DocumentTemplate.objects.create(
                organization=org,
                name=request.POST.get('name'),
                document_type=request.POST.get('document_type'),
                description=request.POST.get('description', ''),
                is_default=request.POST.get('is_default') == 'on',
                is_active=True,
                paper_size=request.POST.get('paper_size', 'A4'),
                orientation=request.POST.get('orientation', 'portrait'),
                html_header=request.POST.get('html_header', ''),
                html_body=request.POST.get('html_body', ''),
                html_footer=request.POST.get('html_footer', ''),
                custom_css=request.POST.get('custom_css', ''),
                created_by=request.user,
            )
            
            messages.success(request, f'Template "{template.name}" créé avec succès.')
            return redirect('ventes:template_detail', pk=template.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {e}')
    
    # Templates par défaut pour pré-remplissage
    from apps.sales.default_templates import DEFAULT_TEMPLATES
    
    return render(request, 'sales/templates/template_form.html', {
        'mode': 'create',
        'doc_types': DocumentTemplate.DOCUMENT_TYPES,
        'paper_sizes': DocumentTemplate.PAPER_SIZES,
        'orientations': DocumentTemplate.ORIENTATIONS,
        'default_templates': DEFAULT_TEMPLATES,
        'default_templates_json': json.dumps(DEFAULT_TEMPLATES),
    })


@login_required
@require_membership('read_only')
def template_detail(request, pk):
    """
    Détail d'un template
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    # Variables disponibles
    var_help = template.get_variable_help_text()
    
    return render(request, 'sales/templates/template_detail.html', {
        'template': template,
        'var_help': var_help,
        'doc_types': DocumentTemplate.DOCUMENT_TYPES,
    })


@login_required
@require_membership('admin')
def template_edit(request, pk):
    """
    Édition d'un template
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    if request.method == 'POST':
        try:
            template.name = request.POST.get('name')
            template.document_type = request.POST.get('document_type')
            template.description = request.POST.get('description', '')
            template.is_default = request.POST.get('is_default') == 'on'
            template.paper_size = request.POST.get('paper_size', 'A4')
            template.orientation = request.POST.get('orientation', 'portrait')
            template.html_header = request.POST.get('html_header', '')
            template.html_body = request.POST.get('html_body', '')
            template.html_footer = request.POST.get('html_footer', '')
            template.custom_css = request.POST.get('custom_css', '')
            
            template.save()
            
            messages.success(request, 'Template mis à jour avec succès.')
            return redirect('ventes:template_detail', pk=template.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour : {e}')
    
    # Variables disponibles
    var_help = template.get_variable_help_text()
    
    return render(request, 'sales/templates/template_form.html', {
        'mode': 'edit',
        'template': template,
        'doc_types': DocumentTemplate.DOCUMENT_TYPES,
        'paper_sizes': DocumentTemplate.PAPER_SIZES,
        'orientations': DocumentTemplate.ORIENTATIONS,
        'var_help': var_help,
    })


@login_required
@require_membership('admin')
def template_delete(request, pk):
    """
    Suppression d'un template
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" supprimé.')
        return redirect('ventes:template_list')
    
    return render(request, 'sales/templates/template_confirm_delete.html', {
        'template': template,
    })


@login_required
@require_membership('read_only')
def template_preview(request, pk):
    """
    Prévisualisation d'un template avec des données fictives
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    # Récupérer un document existant pour les données réelles
    # Ou créer des données fictives
    if template.document_type == 'quote':
        doc = Quote.objects.filter(organization=org).first()
    elif template.document_type == 'invoice':
        doc = Invoice.objects.filter(organization=org).first()
    else:
        doc = None
    
    if doc:
        renderer = DocumentRenderer(template)
        html = renderer.render_html(doc, org)
    else:
        # Données fictives si aucun document n'existe
        html = create_preview_with_dummy_data(template, org)
    
    return HttpResponse(html)


def create_preview_with_dummy_data(template, organization):
    """
    Crée une prévisualisation avec des données fictives
    """
    from decimal import Decimal
    from datetime import date, timedelta
    
    # Classe fictive pour simuler un document
    class DummyDocument:
        def __init__(self):
            self.id = type('obj', (object,), {'hex': lambda: 'PREVIEW123'})()
            self.number = 'PREV-2025-001'
            self.currency = 'EUR'
            self.status = 'draft'
            self.date_issue = date.today()
            self.valid_until = date.today() + timedelta(days=30)
            self.due_date = date.today() + timedelta(days=30)
            self.total_ht = Decimal('250.00')
            self.total_tax = Decimal('50.00')
            self.total_ttc = Decimal('300.00')
        
        def get_status_display(self):
            return 'Brouillon'
        
        class lines:
            @staticmethod
            def all():
                return [
                    type('obj', (object,), {
                        'description': 'Bouteille Château Example 2020',
                        'qty': 6,
                        'unit_price': Decimal('25.00'),
                        'total_ht': Decimal('150.00'),
                    })(),
                    type('obj', (object,), {
                        'description': 'Bouteille Domaine Test 2021',
                        'qty': 4,
                        'unit_price': Decimal('25.00'),
                        'total_ht': Decimal('100.00'),
                    })(),
                ]
    
    class DummyCustomer:
        legal_name = 'Client Exemple SARL'
        billing_address = '123 Rue de la Vigne'
        billing_postal_code = '33000'
        billing_city = 'Bordeaux'
        billing_country = 'France'
        vat_number = 'FR12345678901'
    
    doc = DummyDocument()
    customer = DummyCustomer()
    
    renderer = DocumentRenderer(template)
    return renderer.render_html(doc, organization, customer)


@login_required
@require_membership('read_only')
@require_http_methods(['POST'])
def template_generate_pdf(request, pk, doc_type, doc_id):
    """
    Génère un PDF pour un document spécifique
    
    :param pk: ID du template
    :param doc_type: Type de document ('quote', 'invoice', etc.)
    :param doc_id: ID du document
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    # Récupérer le document
    if doc_type == 'quote':
        doc = get_object_or_404(Quote, id=doc_id, organization=org)
    elif doc_type == 'invoice':
        doc = get_object_or_404(Invoice, id=doc_id, organization=org)
    else:
        return JsonResponse({'error': 'Type de document non supporté'}, status=400)
    
    try:
        renderer = DocumentRenderer(template)
        pdf_bytes = renderer.generate_pdf(doc, org)
        
        # Nom du fichier
        filename = f"{doc_type}_{doc.number or doc.id.hex[:8]}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership('admin')
def template_duplicate(request, pk):
    """
    Duplique un template existant
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    if request.method == 'POST':
        new_template = DocumentTemplate.objects.create(
            organization=org,
            name=f"{template.name} (copie)",
            document_type=template.document_type,
            description=template.description,
            is_default=False,  # La copie n'est jamais par défaut
            is_active=template.is_active,
            paper_size=template.paper_size,
            orientation=template.orientation,
            margin_top=template.margin_top,
            margin_bottom=template.margin_bottom,
            margin_left=template.margin_left,
            margin_right=template.margin_right,
            html_header=template.html_header,
            html_body=template.html_body,
            html_footer=template.html_footer,
            custom_css=template.custom_css,
            created_by=request.user,
        )
        
        messages.success(request, f'Template dupliqué : "{new_template.name}"')
        return redirect('ventes:template_edit', pk=new_template.id)
    
    return render(request, 'sales/templates/template_confirm_duplicate.html', {
        'template': template,
    })


@login_required
@require_membership('read_only')
def template_variables_help(request, pk):
    """
    Aide sur les variables disponibles (AJAX)
    """
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
    
    variables = template.available_variables
    
    return JsonResponse({
        'variables': variables,
        'help_text': template.get_variable_help_text(),
    })


@login_required
@require_membership('admin')
@require_http_methods(['POST'])
def template_generalize(request, pk):
    org = request.current_org
    template = get_object_or_404(DocumentTemplate, id=pk, organization=org)

    target_types = request.POST.getlist('target_types')
    create_without_prices = request.POST.get('without_prices') == 'on'

    if not target_types:
        messages.error(request, "Sélectionnez au moins un type de document.")
        return redirect('ventes:template_edit', pk=template.id)

    from apps.sales.default_templates import DEFAULT_TEMPLATES

    def type_label(dt):
        return dict(DocumentTemplate.DOCUMENT_TYPES).get(dt, dt)

    def unique_name(base, dt):
        name = base
        i = 2
        while DocumentTemplate.objects.filter(organization=org, document_type=dt, name=name).exists():
            name = f"{base} ({i})"
            i += 1
        return name

    def body_without_prices():
        return (
            """
<h3 style="margin-top: 30px;">Détail</h3>
<table>
  <thead>
    <tr>
      <th>Désignation</th>
      <th style="text-align: center; width: 120px;">Quantité</th>
    </tr>
  </thead>
  <tbody>
    {% for line in lines %}
    <tr>
      <td>{{ line.description }}</td>
      <td style="text-align: center;">{{ line.qty }}</td>
    </tr>
    {% endfor %}
  </tbody>
 </table>
            """
        ).strip()

    created = []
    supports_price = {'quote', 'order', 'invoice'}

    with transaction.atomic():
        for dt in target_types:
            default_cfg = DEFAULT_TEMPLATES.get(dt)
            if not default_cfg:
                continue

            base_name = f"{template.name} – {type_label(dt)}"

            body_with = template.html_body if dt == template.document_type else default_cfg['body']
            name_with = base_name
            if dt in supports_price:
                name_with = f"{base_name} (avec prix)"
            name_with = unique_name(name_with, dt)

            new_t_with = DocumentTemplate.objects.create(
                organization=org,
                name=name_with,
                document_type=dt,
                description=template.description,
                is_default=False,
                is_active=True,
                paper_size=template.paper_size,
                orientation=template.orientation,
                margin_top=template.margin_top,
                margin_bottom=template.margin_bottom,
                margin_left=template.margin_left,
                margin_right=template.margin_right,
                html_header=template.html_header,
                html_body=body_with,
                html_footer=template.html_footer,
                custom_css=template.custom_css,
                created_by=request.user,
            )
            created.append(new_t_with)

            if create_without_prices and dt in supports_price:
                name_wo = unique_name(f"{base_name} (sans prix)", dt)
                body_wo = body_without_prices()
                new_t_wo = DocumentTemplate.objects.create(
                    organization=org,
                    name=name_wo,
                    document_type=dt,
                    description=template.description,
                    is_default=False,
                    is_active=True,
                    paper_size=template.paper_size,
                    orientation=template.orientation,
                    margin_top=template.margin_top,
                    margin_bottom=template.margin_bottom,
                    margin_left=template.margin_left,
                    margin_right=template.margin_right,
                    html_header=template.html_header,
                    html_body=body_wo,
                    html_footer=template.html_footer,
                    custom_css=template.custom_css,
                    created_by=request.user,
                )
                created.append(new_t_wo)

    messages.success(request, f"{len(created)} modèles créés.")
    return redirect('ventes:template_list')


# ========== BUILDER VISUEL ==========

@login_required
@require_membership('admin')
def template_builder(request, pk=None):
    """
    Éditeur visuel de template par blocs
    """
    org = request.current_org
    template = None
    initial_blocks = []
    
    if pk:
        template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
        if template.blocks_config:
            initial_blocks = template.blocks_config
    
    # Import des presets et types de blocs
    from apps.sales.block_presets import BLOCK_TYPES, BLOCK_PRESETS
    
    return render(request, 'sales/templates/template_builder.html', {
        'mode': 'edit' if pk else 'create',
        'template': template,
        'doc_types': DocumentTemplate.DOCUMENT_TYPES,
        'block_types_json': json.dumps(BLOCK_TYPES),
        'presets_json': json.dumps(BLOCK_PRESETS),
        'presets': BLOCK_PRESETS,
        'initial_blocks_json': json.dumps(initial_blocks),
    })


@login_required
@require_membership('admin')
@require_http_methods(['POST'])
def template_save_blocks(request, pk=None):
    """
    API pour sauvegarder un template en mode blocs
    """
    org = request.current_org
    
    try:
        data = json.loads(request.body)
        name = data.get('name', 'Nouveau template').strip()
        doc_type = data.get('document_type', 'quote')
        
        if pk:
            # Modification
            template = get_object_or_404(DocumentTemplate, id=pk, organization=org)
            
            # Vérifier si le nom est pris par un autre template
            existing = DocumentTemplate.objects.filter(
                organization=org, name=name, document_type=doc_type
            ).exclude(id=pk).first()
            
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': f'Un template "{name}" existe déjà pour ce type de document. Choisissez un autre nom.'
                }, status=400)
            
            template.name = name
            template.document_type = doc_type
            template.orientation = data.get('orientation', template.orientation)
            template.blocks_config = data.get('blocks_config', [])
            template.editor_mode = 'blocks'
            template.save()
        else:
            # Création - générer un nom unique si nécessaire
            base_name = name
            counter = 1
            while DocumentTemplate.objects.filter(
                organization=org, name=name, document_type=doc_type
            ).exists():
                name = f"{base_name} ({counter})"
                counter += 1
            
            template = DocumentTemplate.objects.create(
                organization=org,
                name=name,
                document_type=doc_type,
                orientation=data.get('orientation', 'portrait'),
                blocks_config=data.get('blocks_config', []),
                editor_mode='blocks',
                is_active=True,
                created_by=request.user,
            )
        
        # Générer le HTML à partir des blocs pour la compatibilité
        html_header, html_body, html_footer = render_blocks_to_html(template.blocks_config)
        template.html_header = html_header
        template.html_body = html_body
        template.html_footer = html_footer
        template.save()
        
        return JsonResponse({
            'success': True,
            'template_id': str(template.id),
            'redirect_url': f'/ventes/templates/{template.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def render_blocks_to_html(blocks):
    """
    Convertit la configuration de blocs en HTML pour le rendu PDF
    """
    if not blocks:
        return '', '', ''
    
    header_parts = []
    body_parts = []
    footer_parts = []
    
    for block in blocks:
        block_type = block.get('type')
        props = block.get('props', {})
        html = render_single_block(block_type, props)
        
        # Dispatcher vers header/body/footer selon le type
        if block_type in ['logo', 'title', 'document_info', 'org_info', 'customer_info']:
            header_parts.append(html)
        elif block_type == 'footer':
            footer_parts.append(html)
        else:
            body_parts.append(html)
    
    return '\n'.join(header_parts), '\n'.join(body_parts), '\n'.join(footer_parts)


def render_single_block(block_type, props):
    """
    Rend un bloc unique en HTML avec les variables Django/Jinja
    """
    p = props
    
    if block_type == 'logo':
        align = p.get('alignment', 'left')
        size_map = {'S': '80px', 'M': '120px', 'L': '180px'}
        size = size_map.get(p.get('size', 'M'), '120px')
        return f'''<div style="text-align: {align}; margin-bottom: {p.get('margin_bottom', 20)}px;">
            {{% if organization.logo %}}<img src="{{{{ organization.logo.url }}}}" style="max-width: {size}; height: auto;">{{% endif %}}
        </div>'''
    
    elif block_type == 'title':
        return f'''<h1 style="font-size: {p.get('font_size', 28)}px; color: {p.get('color', '#8B1538')}; text-align: {p.get('alignment', 'left')}; font-weight: {'bold' if p.get('bold', True) else 'normal'}; font-style: {'italic' if p.get('italic') else 'normal'}; margin-bottom: {p.get('margin_bottom', 10)}px;">
            {p.get('text', 'DOCUMENT')}
        </h1>'''
    
    elif block_type == 'document_info':
        parts = []
        if p.get('show_number', True):
            parts.append(f'<p><strong>{p.get("number_label", "N°")}</strong> {{{{ document.number }}}}</p>')
        if p.get('show_date', True):
            parts.append(f'<p>{p.get("date_label", "Date")} : {{{{ document.date|date:"d/m/Y" }}}}</p>')
        if p.get('show_validity'):
            parts.append(f'<p>{p.get("validity_label", "Valable jusqu\'au")} : {{{{ document.valid_until|date:"d/m/Y" }}}}</p>')
        if p.get('show_due_date'):
            parts.append(f'<p>{p.get("due_date_label", "Échéance")} : {{{{ document.due_date|date:"d/m/Y" }}}}</p>')
        return f'<div style="text-align: {p.get("alignment", "left")}; font-size: {p.get("font_size", 12)}px;">{"".join(parts)}</div>'
    
    elif block_type == 'org_info':
        parts = []
        if p.get('show_name', True):
            parts.append(f'<div style="font-size: {p.get("name_size", 16)}px; font-weight: {"bold" if p.get("name_bold", True) else "normal"};">{{{{ organization.name }}}}</div>')
        if p.get('show_address', True):
            parts.append('{{ organization.address }}<br>{{ organization.postal_code }} {{ organization.city }}')
        if p.get('show_phone', True):
            parts.append('{% if organization.phone %}<div>Tél : {{ organization.phone }}</div>{% endif %}')
        if p.get('show_email', True):
            parts.append('{% if organization.email %}<div>{{ organization.email }}</div>{% endif %}')
        if p.get('show_siret'):
            parts.append('{% if organization.siret %}<div>SIRET : {{ organization.siret }}</div>{% endif %}')
        if p.get('show_vat'):
            parts.append('{% if organization.tva_number %}<div>TVA : {{ organization.tva_number }}</div>{% endif %}')
        if p.get('show_website'):
            parts.append('{% if organization.website %}<div>{{ organization.website }}</div>{% endif %}')
        return f'<div style="text-align: {p.get("alignment", "right")}; font-size: {p.get("font_size", 11)}px; line-height: 1.5;">{"<br>".join(parts)}</div>'
    
    elif block_type == 'customer_info':
        return f'''<div style="padding: {p.get('padding', 15)}px; background: {p.get('background_color', '#f9f9f9')}; border-left: 4px solid {p.get('border_left_color', '#d4af37')}; text-align: {p.get('alignment', 'left')}; font-size: {p.get('font_size', 11)}px; margin-top: 20px;">
            <strong>{p.get('title', 'Client :')}</strong><br>
            <strong>{{{{ customer.legal_name }}}}</strong><br>
            {{{{ customer.billing_address }}}}<br>
            {{{{ customer.billing_postal_code }}}} {{{{ customer.billing_city }}}}
            {{% if customer.vat_number %}}<br>TVA : {{{{ customer.vat_number }}}}{{% endif %}}
        </div>'''
    
    elif block_type == 'spacer':
        return f'<div style="height: {p.get("height", 30)}px;"></div>'
    
    elif block_type == 'divider':
        return f'<hr style="border: none; border-top: {p.get("thickness", 1)}px solid {p.get("color", "#ddd")}; width: {p.get("width", 100)}%; margin: {p.get("margin_top", 15)}px 0 {p.get("margin_bottom", 15)}px 0;">'
    
    elif block_type == 'section_title':
        return f'<h3 style="font-size: {p.get("font_size", 14)}px; font-weight: {"bold" if p.get("bold", True) else "normal"}; margin-top: {p.get("margin_top", 20)}px; margin-bottom: {p.get("margin_bottom", 10)}px;">{p.get("text", "Détail")}</h3>'
    
    elif block_type == 'lines_table':
        cols = p.get('columns', {})
        headers = []
        cells = []
        
        if cols.get('description', {}).get('show', True):
            headers.append(f'<th>{cols.get("description", {}).get("label", "Désignation")}</th>')
            cells.append('<td>{{ line.description }}</td>')
        if cols.get('quantity', {}).get('show', True):
            headers.append(f'<th style="text-align: center; width: 80px;">{cols.get("quantity", {}).get("label", "Qté")}</th>')
            cells.append('<td style="text-align: center;">{{ line.qty }}</td>')
        if cols.get('unit_price', {}).get('show', True):
            headers.append(f'<th style="text-align: right; width: 120px;">{cols.get("unit_price", {}).get("label", "Prix unit. HT")}</th>')
            cells.append('<td style="text-align: right;">{{ line.unit_price|currency }}</td>')
        if cols.get('total', {}).get('show', True):
            headers.append(f'<th style="text-align: right; width: 120px;">{cols.get("total", {}).get("label", "Total HT")}</th>')
            cells.append('<td style="text-align: right;">{{ line.total_ht|currency }}</td>')
        
        return f'''<table style="width: 100%; border-collapse: collapse; font-size: {p.get('font_size', 11)}px;">
            <thead><tr style="background: {p.get('header_bg_color', '#f5f5f5')};">{''.join(headers)}</tr></thead>
            <tbody>
                {{% for line in lines %}}
                <tr>{''.join(cells)}</tr>
                {{% endfor %}}
            </tbody>
        </table>'''
    
    elif block_type == 'totals':
        parts = []
        if p.get('show_subtotal', True):
            parts.append(f'<tr><td>{p.get("subtotal_label", "Total HT")}</td><td style="text-align: right;">{{{{ totals.total_ht|currency }}}}</td></tr>')
        if p.get('show_vat', True):
            parts.append(f'<tr><td>{p.get("vat_label", "TVA")}</td><td style="text-align: right;">{{{{ totals.total_tax|currency }}}}</td></tr>')
        if p.get('show_total', True):
            bold = 'font-weight: bold;' if p.get('total_bold', True) else ''
            size = f'font-size: {p.get("total_size", 14)}px;' if p.get('total_size') else ''
            parts.append(f'<tr style="{bold}{size}"><td>{p.get("total_label", "Total TTC")}</td><td style="text-align: right;">{{{{ totals.total_ttc|currency }}}}</td></tr>')
        
        return f'''<div style="text-align: {p.get('alignment', 'right')}; margin-top: 20px;">
            <table style="margin-left: auto; font-size: {p.get('font_size', 12)}px;">
                {''.join(parts)}
            </table>
        </div>'''
    
    elif block_type == 'conditions':
        content = p.get('content', '').replace('\n', '<br>')
        title_html = f'<strong>{p.get("title", "Conditions")}</strong><br>' if p.get('show_title', True) else ''
        return f'''<div style="padding: {p.get('padding', 15)}px; background: {p.get('background_color', '#f7e7ce')}; border: 1px solid {p.get('border_color', '#d4af37')}; border-radius: 4px; font-size: {p.get('font_size', 10)}px; margin-top: {p.get('margin_top', 30)}px;">
            {title_html}{content}
        </div>'''
    
    elif block_type == 'signature':
        border = 'border: 1px solid #333;' if p.get('show_border', True) else ''
        return f'''<div style="{border} padding: 15px; margin-top: {p.get('margin_top', 40)}px;">
            <strong>{p.get('title', 'Signature du client')}</strong>
            <p style="margin-top: 10px; color: #666;">{p.get('subtitle', 'Date et signature')}</p>
            <div style="height: {p.get('height', 80)}px;"></div>
        </div>'''
    
    elif block_type == 'footer':
        if p.get('content'):
            content = p.get('content')
        else:
            parts = []
            if p.get('show_name', True):
                parts.append('{{ organization.name }}')
            if p.get('show_siret', True):
                parts.append('SIRET : {{ organization.siret }}')
            if p.get('show_vat', True):
                parts.append('TVA : {{ organization.tva_number }}')
            if p.get('show_website'):
                parts.append('{{ organization.website }}')
            content = ' - '.join(parts)
        
        return f'<p style="text-align: {p.get("alignment", "center")}; font-size: {p.get("font_size", 8)}pt; color: {p.get("color", "#666")};">{content}</p>'
    
    elif block_type == 'text':
        return f'''<p style="font-size: {p.get('font_size', 11)}px; text-align: {p.get('alignment', 'left')}; font-weight: {'bold' if p.get('bold') else 'normal'}; font-style: {'italic' if p.get('italic') else 'normal'};">
            {p.get('content', '')}
        </p>'''
    
    return ''
