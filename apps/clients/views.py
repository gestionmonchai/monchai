"""
Vues pour la gestion des clients - Roadmap 36
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.accounts.decorators import require_membership
from .models import Customer, CustomerTag, CustomerTagLink
from .services import CustomerSearchService
from .duplicate_detection import DuplicateDetectionService
import json
import csv
import io

@login_required
@require_membership(role_min='read_only')
def customers_list(request, segment_override=None):
    """
    Liste des clients avec recherche et filtres - Style cépages
    segment_override: Force un segment particulier (ex: 'supplier' pour /achats/fournisseurs/)
    """
    organization = request.current_org
    
    try:
        # Récupération des paramètres de recherche
        filters = {}
        
        # Filtres individuels
        name = request.GET.get('name', '').strip()
        if name:
            filters['name'] = name
        
        email = request.GET.get('email', '').strip()
        if email:
            filters['email'] = email
        
        phone = request.GET.get('phone', '').strip()
        if phone:
            filters['phone'] = phone
        
        vat_number = request.GET.get('vat_number', '').strip()
        if vat_number:
            filters['vat_number'] = vat_number
        
        # Gestion du segment (Override prioritaire)
        if segment_override:
            segment = segment_override
            filters['segment'] = segment
        else:
            segment = request.GET.get('segment', '').strip()
            # STRICT REDIRECT: Si on demande 'supplier' via l'URL générique, on redirige
            if segment == 'supplier':
                return redirect('achats:suppliers_list')
            
            if segment:
                filters['segment'] = segment
        
        is_active = request.GET.get('is_active', '').strip()
        if is_active:
            filters['is_active'] = is_active
        
        country_code = request.GET.get('country_code', '').strip()
        if country_code:
            filters['country_code'] = country_code
        
        search = request.GET.get('search', '').strip()
        if search:
            filters['search'] = search
        
        tags = request.GET.getlist('tags')
        if tags:
            filters['tags'] = tags
        
        # Tri
        sort_by = request.GET.get('sort', 'name')
        sort_order = request.GET.get('order', 'asc')
        
        # Construction de la requête
        customers = Customer.objects.filter(organization=organization)
        
        # Application des filtres
        if name:
            customers = customers.filter(name__icontains=name)
        if email:
            customers = customers.filter(email__icontains=email)
        if phone:
            customers = customers.filter(phone__icontains=phone)
        if vat_number:
            customers = customers.filter(vat_number__icontains=vat_number)
        if segment and segment in dict(Customer.SEGMENT_CHOICES):
            customers = customers.filter(segment=segment)
        if is_active:
            customers = customers.filter(is_active=is_active.lower() in ['true', '1', 'yes'])
        if country_code:
            customers = customers.filter(country_code__icontains=country_code)
        if search:
            from django.db.models import Q
            customers = customers.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(vat_number__icontains=search)
            )
        if tags:
            customers = customers.filter(tag_links__tag__in=tags)
        
        # Tri
        valid_sort_fields = ['name', 'email', 'segment', 'created_at', 'updated_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'name'
        
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        customers = customers.order_by(sort_by)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(customers, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Statistiques
        total_count = Customer.objects.filter(organization=organization).count()
        filtered_count = customers.count()
        
        context = {
            'page_title': 'Clients',
            'page_obj': page_obj,
            'filters': filters,
            'sort_by': request.GET.get('sort', 'name'),
            'sort_order': sort_order,
            'segment_choices': Customer.SEGMENT_CHOICES,
            'stats': {
                'total': total_count,
                'filtered': filtered_count,
            }
        }
        
        return render(request, 'clients/customers_list_cepages_style.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des clients: {str(e)}")
        return render(request, 'clients/customers_list_cepages_style.html', {
            'page_title': 'Clients',
            'page_obj': None,
            'filters': {},
            'segment_choices': Customer.SEGMENT_CHOICES,
            'stats': {'total': 0, 'filtered': 0}
        })


@login_required
@require_membership(role_min='read_only')
def customers_list_v2(request):
    """
    Liste des clients - Nouveau design MonChai (sidebar + grille/liste + preview)
    """
    organization = request.current_org
    
    try:
        clients = Customer.objects.filter(
            organization=organization,
            is_archived=False
        ).order_by('-created_at')[:100]
        
        context = {
            'page_title': 'Clients',
            'clients': clients,
            'organization': organization,
        }
        
        return render(request, 'commerce/customers_list_v2.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des clients: {str(e)}")
        return render(request, 'commerce/customers_list_v2.html', {
            'page_title': 'Clients',
            'clients': [],
            'organization': organization,
        })


@login_required
@require_membership(role_min='read_only')
def customer_detail(request, customer_id):
    """
    Page de détail d'un client avec gestion des onglets
    GET /clients/<uuid>/?tab=<onglet>
    """
    organization = request.current_org
    
    customer = get_object_or_404(
        Customer.objects.select_related('organization')
                       .prefetch_related('tag_links__tag', 'activities'),
        id=customer_id,
        organization=organization
    )
    
    # Gestion des onglets
    current_tab = request.GET.get('tab', 'identite')
    valid_tabs = ['identite', 'commercial', 'logistique', 'performance', 'conformite']
    
    if current_tab not in valid_tabs:
        current_tab = 'identite'
    
    # Récupération des activités récentes
    recent_activities = customer.activities.all()[:10]
    
    # Données spécifiques selon l'onglet
    tab_data = {}
    
    if current_tab == 'commercial':
        # Données commerciales et fiscales
        tab_data = {
            'vat_number': customer.vat_number,
            'segment': customer.segment,
            'segment_display': customer.get_segment_display(),
            'created_at': customer.created_at,
            'updated_at': customer.updated_at,
        }
    elif current_tab == 'logistique':
        # Données d'adresses et logistique
        tab_data = {
            'country_code': customer.country_code,
            'phone': customer.phone,
            'email': customer.email,
            # TODO: Ajouter adresses de livraison/facturation quand le modèle sera étendu
        }
    elif current_tab == 'performance':
        # Données de performance et historique
        tab_data = {
            'total_orders': 0,  # TODO: Calculer depuis les commandes
            'total_revenue': 0,  # TODO: Calculer depuis les factures
            'last_order_date': None,  # TODO: Récupérer depuis les commandes
            'activities_count': len(recent_activities),
        }
    elif current_tab == 'conformite':
        # Documents et conformité
        tab_data = {
            'has_vat': bool(customer.vat_number),
            'is_active': customer.is_active,
            'created_at': customer.created_at,
            'updated_at': customer.updated_at,
        }
    
    context = {
        'page_title': f'Client - {customer.name}',
        'customer': customer,
        'current_tab': current_tab,
        'tab_data': tab_data,
        'recent_activities': recent_activities,
        'tags': [link.tag for link in customer.tag_links.all()],
    }
    
    return render(request, 'clients/customer_detail_modern.html', context)


@login_required
@require_membership(role_min='editor')
def customer_create(request):
    """
    Page de création d'un nouveau client
    GET/POST /clients/nouveau/
    """
    organization = request.current_org
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Récupération des données du formulaire
                data = request.POST
                
                # Création du client
                customer = Customer(
                    organization=organization,
                    name=data.get('name', '').strip(),
                    segment=data.get('segment', ''),
                    email=data.get('email', '').strip() or None,
                    phone=data.get('phone', '').strip() or None,
                    vat_number=data.get('vat_number', '').strip() or None,
                    country_code=data.get('country_code', '').strip() or None,
                    is_active=data.get('is_active') == 'on',
                )
                
                # Validation
                customer.full_clean()
                customer.save()
                
                # Gestion des tags
                tags = data.getlist('tags')
                for tag_id in tags:
                    try:
                        tag = CustomerTag.objects.get(id=tag_id, organization=organization)
                        CustomerTagLink.objects.create(
                            organization=organization,
                            customer=customer,
                            tag=tag
                        )
                    except CustomerTag.DoesNotExist:
                        pass
                
                messages.success(request, f'Client "{customer.name}" créé avec succès.')
                return redirect('clients:customer_detail', customer_id=customer.id)
                
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    # Récupération des tags disponibles
    available_tags = CustomerTag.objects.filter(organization=organization).order_by('name')
    
    context = {
        'page_title': 'Nouveau client',
        'segment_choices': Customer.SEGMENT_CHOICES,
        'available_tags': available_tags,
        'selected_tags': [],
    }
    
    return render(request, 'clients/customer_form_tabs.html', context)


@login_required
@require_membership(role_min='editor')
def customer_edit(request, customer_id):
    """
    Page d'édition d'un client
    GET/POST /clients/<uuid>/modifier/
    """
    organization = request.current_org
    
    customer = get_object_or_404(
        Customer.objects.prefetch_related('tag_links__tag'),
        id=customer_id,
        organization=organization
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mise à jour des données
                data = request.POST
                
                customer.name = data.get('name', '').strip()
                customer.segment = data.get('segment', '')
                customer.email = data.get('email', '').strip() or None
                customer.phone = data.get('phone', '').strip() or None
                customer.vat_number = data.get('vat_number', '').strip() or None
                customer.country_code = data.get('country_code', '').strip() or None
                customer.is_active = data.get('is_active') == 'on'
                
                # Validation
                customer.full_clean()
                customer.save()
                
                # Mise à jour des tags
                current_tags = set(link.tag.id for link in customer.tag_links.all())
                new_tags = set(data.getlist('tags'))
                
                # Supprimer les tags non sélectionnés
                for tag_id in current_tags - new_tags:
                    CustomerTagLink.objects.filter(
                        customer=customer,
                        tag_id=tag_id
                    ).delete()
                
                # Ajouter les nouveaux tags
                for tag_id in new_tags - current_tags:
                    try:
                        tag = CustomerTag.objects.get(id=tag_id, organization=organization)
                        CustomerTagLink.objects.create(
                            organization=organization,
                            customer=customer,
                            tag=tag
                        )
                    except CustomerTag.DoesNotExist:
                        pass
                
                messages.success(request, f'Client "{customer.name}" modifié avec succès.')
                return redirect('clients:customer_detail', customer_id=customer.id)
                
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification: {str(e)}')
    
    # Récupération des tags disponibles et sélectionnés
    available_tags = CustomerTag.objects.filter(organization=organization).order_by('name')
    selected_tags = set(link.tag.id for link in customer.tag_links.all())
    
    context = {
        'page_title': f'Modifier - {customer.name}',
        'customer': customer,
        'segment_choices': Customer.SEGMENT_CHOICES,
        'available_tags': available_tags,
        'selected_tags': selected_tags,
        'is_edit': True,
    }
    
    return render(request, 'clients/customer_form_tabs.html', context)


# API Views

@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def customers_search_ajax(request):
    """API AJAX pour recherche en temps réel des clients avec filtres avancés (comme les cépages)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    
    organization = request.current_org
    page = int(request.GET.get('page', 1))
    
    # Appliquer les mêmes filtres que la vue principale
    customers = Customer.objects.filter(organization=organization)
    
    # Filtres par champs individuels
    filters = {}
    
    # Filtre par nom
    name = request.GET.get('name', '').strip()
    if name:
        customers = customers.filter(name__icontains=name)
        filters['name'] = name
    
    # Filtre par email
    email = request.GET.get('email', '').strip()
    if email:
        customers = customers.filter(email__icontains=email)
        filters['email'] = email
    
    # Filtre par téléphone
    phone = request.GET.get('phone', '').strip()
    if phone:
        customers = customers.filter(phone__icontains=phone)
        filters['phone'] = phone
    
    # Filtre par numéro TVA
    vat_number = request.GET.get('vat_number', '').strip()
    if vat_number:
        customers = customers.filter(vat_number__icontains=vat_number)
        filters['vat_number'] = vat_number
    
    # Filtre par segment
    segment = request.GET.get('segment', '').strip()
    if segment and segment in dict(Customer.SEGMENT_CHOICES):
        customers = customers.filter(segment=segment)
        filters['segment'] = segment
    
    # Filtre par statut
    is_active = request.GET.get('is_active', '').strip()
    if is_active:
        customers = customers.filter(is_active=is_active.lower() in ['true', '1', 'yes'])
        filters['is_active'] = is_active
    
    # Filtre par pays
    country_code = request.GET.get('country_code', '').strip()
    if country_code:
        customers = customers.filter(country_code__icontains=country_code)
        filters['country_code'] = country_code
    
    # Recherche globale (pour compatibilité)
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(vat_number__icontains=search)
        )
        filters['search'] = search
    
    # Tri
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    
    valid_sort_fields = ['name', 'email', 'segment', 'created_at', 'updated_at']
    if sort_by not in valid_sort_fields:
        sort_by = 'name'
    
    if sort_order == 'desc':
        sort_by = f'-{sort_by}'
    
    customers = customers.order_by(sort_by)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(customers, 25)  # 25 clients par page
    page_obj = paginator.get_page(page)
    
    # Statistiques
    total_count = Customer.objects.filter(organization=organization).count()
    filtered_count = customers.count()
    
    # Rendu du template partiel pour les lignes de table
    from django.template.loader import render_to_string
    table_html = render_to_string('clients/partials/customer_table_rows.html', {
        'customers': page_obj,
        'page_obj': page_obj,
    })
    
    # Pagination HTML
    pagination_html = render_to_string('clients/partials/customer_pagination.html', {
        'page_obj': page_obj,
    })
    
    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': total_count,
            'filtered': filtered_count,
            'current_page': page,
            'total_pages': paginator.num_pages,
        },
        'filters': filters,
    })


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def customers_api(request):
    """
    API de recherche des clients - Roadmap 36
    GET /api/clients/
    """
    organization = request.current_org
    
    try:
        # Récupération des paramètres
        query_params = request.GET.copy()
        
        # Recherche via le service
        results = CustomerSearchService.search_customers(organization, query_params)
        
        return JsonResponse(results)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@require_http_methods(["POST"])
def customers_quick_create_api(request):
    """
    API rapide pour créer un client minimal depuis une modale (Devis, etc.).
    Entrée JSON: { name, segment?, email?, phone?, country_code? }
    Par défaut segment='individual' pour éviter TVA requise.
    Retourne { success, customer: {id, name} } ou { success:false, errors:{} }
    """
    organization = request.current_org
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': {'__all__': 'JSON invalide'}}, status=400)

    name = (data.get('name') or '').strip()
    segment = (data.get('segment') or 'individual').strip()
    email = (data.get('email') or '').strip() or None
    phone = (data.get('phone') or '').strip() or None
    country_code = (data.get('country_code') or '').strip() or None

    if not name:
        return JsonResponse({'success': False, 'errors': {'name': 'Nom requis'}}, status=400)

    # Créer puis valider
    customer = Customer(
        organization=organization,
        name=name,
        segment=segment if segment in dict(Customer.SEGMENT_CHOICES) else 'individual',
        email=email,
        phone=phone,
        country_code=country_code,
        is_active=True,
    )
    try:
        customer.full_clean()
        customer.save()
        return JsonResponse({'success': True, 'customer': {'id': str(customer.id), 'name': customer.name}})
    except ValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def customers_suggestions_api(request):
    """
    API de suggestions pour autocomplétion
    GET /api/clients/suggestions/?q=...
    """
    organization = request.current_org
    
    try:
        query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 5)), 20)
        
        suggestions = CustomerSearchService.get_customer_suggestions(
            organization, query, limit
        )
        
        return JsonResponse({
            'suggestions': suggestions,
            'query': query
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='admin')
@require_http_methods(["GET"])
def customers_export(request):
    """
    Export CSV des clients avec neutralisation
    GET /clients/export/?format=csv&...
    """
    organization = request.current_org
    
    try:
        # Récupération des paramètres de filtrage
        query_params = request.GET.copy()
        query_params['page_size'] = '1000'  # Export limité à 1000 clients
        
        # Recherche via le service
        results = CustomerSearchService.search_customers(organization, query_params)
        
        # Format d'export
        export_format = request.GET.get('format', 'csv').lower()
        
        if export_format == 'csv':
            return _export_customers_csv(results['items'], organization.name)
        else:
            return JsonResponse({'error': 'Format non supporté'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _export_customers_csv(customers, org_name):
    """
    Export CSV avec neutralisation des caractères dangereux
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # En-têtes
    headers = [
        'Nom', 'Segment', 'Email', 'Téléphone', 'N° TVA', 
        'Pays', 'Actif', 'Tags', 'Créé le', 'Modifié le'
    ]
    writer.writerow(headers)
    
    # Données
    for customer in customers:
        # Neutralisation CSV injection (caractères dangereux: = + - @ \t)
        def neutralize_csv(value):
            if not value:
                return ''
            value = str(value)
            if value.startswith(('=', '+', '-', '@', '\t')):
                value = "'" + value
            return value
        
        row = [
            neutralize_csv(customer['name']),
            neutralize_csv(customer['segment_display']),
            neutralize_csv(customer['email']),
            neutralize_csv(customer['phone']),
            neutralize_csv(customer['vat_number']),
            neutralize_csv(customer['country_code']),
            'Oui' if customer['is_active'] else 'Non',
            neutralize_csv(', '.join(customer['tags'])),
            neutralize_csv(customer['created_at'][:10]),  # Date seulement
            neutralize_csv(customer['updated_at'][:10]),
        ]
        writer.writerow(row)
    
    # Réponse HTTP
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="clients_{org_name.replace(" ", "_")}.csv"'
    
    return response


@login_required
@require_membership(role_min='editor')
@require_http_methods(["POST"])
def duplicate_detection_api(request):
    """
    API de détection de doublons en temps réel - Roadmap 37
    POST /api/clients/duplicates/
    """
    organization = request.current_org
    
    try:
        data = json.loads(request.body)
        
        # Paramètres de recherche
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        vat_number = data.get('vat_number', '').strip()
        exclude_id = data.get('exclude_id')  # Pour édition
        
        # Validation minimale
        if not any([name, email, phone, vat_number]):
            return JsonResponse({
                'error': 'Au moins un champ doit être fourni pour la détection'
            }, status=400)
        
        # Détection via le service
        results = DuplicateDetectionService.check_duplicates(
            organization=organization,
            name=name or None,
            email=email or None,
            phone=phone or None,
            vat_number=vat_number or None,
            exclude_id=exclude_id
        )
        
        return JsonResponse(results)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
