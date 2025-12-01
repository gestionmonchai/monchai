"""
Vues pour l'édition et la gestion des templates de documents
"""

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
            return redirect('sales:template_detail', pk=template.id)
            
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
            return redirect('sales:template_detail', pk=template.id)
            
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
        return redirect('sales:template_list')
    
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
        return redirect('sales:template_edit', pk=new_template.id)
    
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
        return redirect('sales:template_edit', pk=template.id)

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
    return redirect('sales:template_list')
