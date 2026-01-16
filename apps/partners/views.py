"""
Vues pour la gestion des partenaires (tiers unifiés)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.template.loader import render_to_string
from django.urls import reverse
from apps.accounts.decorators import require_membership
from .models import (
    Partner, PartnerRole, Address, ContactPerson,
    ClientProfile, SupplierProfile, PartnerTag, PartnerTagLink, PartnerEvent
)
from .forms import (
    PartnerForm, PartnerQuickCreateForm, AddressForm, ContactPersonForm,
    ClientProfileForm, SupplierProfileForm, PartnerFilterForm
)
import json


# =============================================================================
# LISTES
# =============================================================================

@login_required
@require_membership(role_min='read_only')
def partners_list(request, role_filter=None):
    """
    Liste globale des partenaires (tous rôles) ou filtrée par rôle.
    - /contacts/ : tous les partenaires
    - /ventes/clients/ : role_filter='client'
    - /achats/fournisseurs/ : role_filter='supplier'
    """
    organization = request.current_org
    
    # Queryset de base
    partners = Partner.objects.filter(
        organization=organization,
        is_archived=False
    ).prefetch_related('roles', 'addresses').order_by('name')
    
    # Filtrage par rôle si spécifié (menus Ventes/Achats)
    if role_filter:
        partners = partners.filter(roles__code=role_filter)
    
    # Filtres additionnels depuis GET
    search = request.GET.get('search', '').strip()
    segment = request.GET.get('segment', '').strip()
    is_active = request.GET.get('is_active', '').strip()
    country = request.GET.get('country', '').strip()
    roles_filter = request.GET.getlist('roles')
    
    if search:
        partners = partners.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(vat_number__icontains=search) |
            Q(siret__icontains=search) |
            Q(code__icontains=search)
        )
    
    if segment:
        partners = partners.filter(segment=segment)
    
    if is_active == 'true':
        partners = partners.filter(is_active=True)
    elif is_active == 'false':
        partners = partners.filter(is_active=False)
    
    if country:
        partners = partners.filter(country_code__iexact=country)
    
    if roles_filter and not role_filter:
        partners = partners.filter(roles__code__in=roles_filter).distinct()
    
    # Tri
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    valid_sorts = ['name', 'email', 'created_at', 'updated_at']
    if sort_by not in valid_sorts:
        sort_by = 'name'
    if sort_order == 'desc':
        sort_by = f'-{sort_by}'
    partners = partners.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(partners.distinct(), 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Stats
    total_count = Partner.objects.filter(organization=organization, is_archived=False)
    if role_filter:
        total_count = total_count.filter(roles__code=role_filter)
    total_count = total_count.count()
    
    # Configuration selon le contexte
    if role_filter == 'client':
        page_title = 'Clients'
        create_url = 'partners:partner_create_as_client'
        icon = 'bi-person-check'
        color = 'primary'
    elif role_filter == 'supplier':
        page_title = 'Fournisseurs'
        create_url = 'partners:partner_create_as_supplier'
        icon = 'bi-truck'
        color = 'success'
    else:
        page_title = 'Contacts'
        create_url = 'partners:partner_create'
        icon = 'bi-people'
        color = 'secondary'
    
    context = {
        'page_title': page_title,
        'page_obj': page_obj,
        'partners': page_obj,
        'role_filter': role_filter,
        'create_url': create_url,
        'icon': icon,
        'color': color,
        'filters': {
            'search': search,
            'segment': segment,
            'is_active': is_active,
            'country': country,
            'roles': roles_filter,
        },
        'sort_by': request.GET.get('sort', 'name'),
        'sort_order': sort_order.replace('-', ''),
        'segment_choices': Partner.SEGMENT_CHOICES,
        'role_choices': PartnerRole.objects.all(),
        'stats': {
            'total': total_count,
            'filtered': paginator.count,
        }
    }
    
    # Réponse AJAX (partials pour HTMX)
    if request.headers.get('HX-Request'):
        html = render_to_string('partners/partials/partner_table_rows.html', context, request=request)
        pagination_html = render_to_string('partners/partials/pagination.html', context, request=request)
        return JsonResponse({
            'success': True,
            'table_html': html,
            'pagination_html': pagination_html,
            'stats': context['stats']
        })
    
    return render(request, 'partners/partners_list.html', context)


# Vues filtrées pour menus Ventes et Achats
@login_required
@require_membership(role_min='read_only')
def clients_list(request):
    """Liste des clients (vue filtrée pour menu Ventes)"""
    return partners_list(request, role_filter='client')


@login_required
@require_membership(role_min='read_only')
def suppliers_list(request):
    """Liste des fournisseurs (vue filtrée pour menu Achats)"""
    return partners_list(request, role_filter='supplier')


# =============================================================================
# DÉTAIL PARTENAIRE (FICHE UNIQUE)
# =============================================================================

@login_required
@require_membership(role_min='read_only')
def partner_detail(request, display_id):
    """
    Fiche partenaire unique avec onglets contextuels.
    Onglets: Aperçu, Interlocuteurs, Adresses, Documents, Ventes*, Achats*, Timeline
    * Affichés uniquement si le partenaire a le rôle correspondant
    """
    organization = request.current_org
    
    partner = get_object_or_404(
        Partner.objects.select_related('organization')
                      .prefetch_related('roles', 'addresses', 'contacts', 'tag_links__tag', 'events'),
        display_id=display_id,
        organization=organization
    )
    
    # Onglet actif (depuis URL ou défaut)
    current_tab = request.GET.get('tab', 'overview')
    valid_tabs = ['overview', 'contacts', 'addresses', 'documents', 'sales', 'purchases', 'timeline']
    if current_tab not in valid_tabs:
        current_tab = 'overview'
    
    # Profils spécifiques
    client_profile = None
    supplier_profile = None
    
    if partner.is_client:
        client_profile, _ = ClientProfile.objects.get_or_create(
            partner=partner,
            defaults={'organization': organization}
        )
    
    if partner.is_supplier:
        supplier_profile, _ = SupplierProfile.objects.get_or_create(
            partner=partner,
            defaults={'organization': organization}
        )
    
    # Timeline (10 derniers événements)
    recent_events = partner.events.all()[:10]
    
    # Tags
    tags = [link.tag for link in partner.tag_links.select_related('tag').all()]
    
    # Documents liés (depuis commerce)
    sales_documents = []
    purchase_documents = []
    try:
        from apps.commerce.models import CommercialDocument
        if partner.is_client:
            # Chercher par mapping ou directement (migration nécessaire)
            pass
        if partner.is_supplier:
            pass
    except ImportError:
        pass
    
    context = {
        'page_title': f'{partner.name}',
        'partner': partner,
        'current_tab': current_tab,
        'client_profile': client_profile,
        'supplier_profile': supplier_profile,
        'recent_events': recent_events,
        'tags': tags,
        'addresses': partner.addresses.all(),
        'contacts': partner.contacts.all(),
        'sales_documents': sales_documents,
        'purchase_documents': purchase_documents,
    }
    
    return render(request, 'partners/partner_detail.html', context)


# =============================================================================
# CRÉATION / ÉDITION
# =============================================================================

@login_required
@require_membership(role_min='editor')
def partner_create(request, default_role=None):
    """
    Création d'un partenaire.
    default_role: 'client', 'supplier' si appelé depuis Ventes/Achats
    """
    organization = request.current_org
    
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    partner = form.save(commit=False)
                    partner.organization = organization
                    partner.save()
                    
                    # Rôles
                    roles = form.cleaned_data.get('roles', [])
                    if roles:
                        partner.roles.set(roles)
                    elif default_role:
                        # Ajouter le rôle par défaut si aucun sélectionné
                        partner.add_role(default_role)
                    
                    # Créer les profils si rôles correspondants
                    if partner.is_client:
                        ClientProfile.objects.get_or_create(
                            partner=partner,
                            defaults={'organization': organization}
                        )
                    if partner.is_supplier:
                        SupplierProfile.objects.get_or_create(
                            partner=partner,
                            defaults={'organization': organization}
                        )
                    
                    messages.success(request, f'Partenaire "{partner.name}" créé avec succès.')
                    
                    # Redirection selon contexte
                    if default_role == 'client':
                        return redirect('partners:partner_detail', display_id=partner.display_id)
                    elif default_role == 'supplier':
                        return redirect('partners:partner_detail', display_id=partner.display_id)
                    return redirect('partners:partner_detail', display_id=partner.display_id)
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        initial = {}
        if default_role:
            try:
                role = PartnerRole.objects.get(code=default_role)
                initial['roles'] = [role]
            except PartnerRole.DoesNotExist:
                pass
        form = PartnerForm(initial=initial)
    
    # Configuration selon contexte
    if default_role == 'client':
        page_title = 'Nouveau client'
        back_url = 'partners:clients_list'
    elif default_role == 'supplier':
        page_title = 'Nouveau fournisseur'
        back_url = 'partners:suppliers_list'
    else:
        page_title = 'Nouveau contact'
        back_url = 'partners:partners_list'
    
    context = {
        'page_title': page_title,
        'form': form,
        'default_role': default_role,
        'back_url': back_url,
        'available_tags': PartnerTag.objects.filter(organization=organization),
    }
    
    return render(request, 'partners/partner_form.html', context)


@login_required
@require_membership(role_min='editor')
def partner_create_as_client(request):
    """Création rapide en tant que client"""
    return partner_create(request, default_role='client')


@login_required
@require_membership(role_min='editor')
def partner_create_as_supplier(request):
    """Création rapide en tant que fournisseur"""
    return partner_create(request, default_role='supplier')


@login_required
@require_membership(role_min='editor')
def partner_edit(request, display_id):
    """Édition d'un partenaire"""
    organization = request.current_org
    
    partner = get_object_or_404(
        Partner.objects.prefetch_related('roles'),
        display_id=display_id,
        organization=organization
    )
    
    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            try:
                with transaction.atomic():
                    partner = form.save()
                    
                    # Mettre à jour les rôles
                    roles = form.cleaned_data.get('roles', [])
                    partner.roles.set(roles)
                    
                    # Créer/supprimer les profils selon les rôles
                    if partner.is_client:
                        ClientProfile.objects.get_or_create(
                            partner=partner,
                            defaults={'organization': organization}
                        )
                    if partner.is_supplier:
                        SupplierProfile.objects.get_or_create(
                            partner=partner,
                            defaults={'organization': organization}
                        )
                    
                    messages.success(request, f'Partenaire "{partner.name}" modifié avec succès.')
                    return redirect('partners:partner_detail', display_id=partner.display_id)
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de la modification: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PartnerForm(instance=partner)
    
    context = {
        'page_title': f'Modifier - {partner.name}',
        'form': form,
        'partner': partner,
        'is_edit': True,
        'back_url': 'partners:partner_detail',
        'available_tags': PartnerTag.objects.filter(organization=organization),
    }
    
    return render(request, 'partners/partner_form.html', context)


# =============================================================================
# GESTION ADRESSES
# =============================================================================

@login_required
@require_membership(role_min='editor')
def address_create(request, partner_display_id):
    """Ajout d'une adresse"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=partner_display_id, organization=organization)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.partner = partner
            address.organization = organization
            address.save()
            messages.success(request, 'Adresse ajoutée.')
            
            if request.headers.get('HX-Request'):
                html = render_to_string('partners/partials/addresses_list.html', {
                    'partner': partner,
                    'addresses': partner.addresses.all()
                }, request=request)
                return HttpResponse(html)
            
            return redirect('partners:partner_detail', display_id=partner.display_id)
    else:
        form = AddressForm()
    
    context = {
        'form': form,
        'partner': partner,
        'page_title': 'Nouvelle adresse'
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partners/partials/address_form.html', context)
    
    return render(request, 'partners/address_form.html', context)


@login_required
@require_membership(role_min='editor')
@require_POST
def address_delete(request, address_id):
    """Suppression d'une adresse"""
    organization = request.current_org
    address = get_object_or_404(Address, id=address_id, organization=organization)
    partner = address.partner
    address.delete()
    messages.success(request, 'Adresse supprimée.')
    
    if request.headers.get('HX-Request'):
        html = render_to_string('partners/partials/addresses_list.html', {
            'partner': partner,
            'addresses': partner.addresses.all()
        }, request=request)
        return HttpResponse(html)
    
    return redirect('partners:partner_detail', display_id=partner.display_id)


# =============================================================================
# GESTION CONTACTS
# =============================================================================

@login_required
@require_membership(role_min='editor')
def contact_create(request, partner_display_id):
    """Ajout d'un interlocuteur"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=partner_display_id, organization=organization)
    
    if request.method == 'POST':
        form = ContactPersonForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.partner = partner
            contact.organization = organization
            contact.save()
            messages.success(request, 'Interlocuteur ajouté.')
            
            if request.headers.get('HX-Request'):
                html = render_to_string('partners/partials/contacts_list.html', {
                    'partner': partner,
                    'contacts': partner.contacts.all()
                }, request=request)
                return HttpResponse(html)
            
            return redirect('partners:partner_detail', display_id=partner.display_id)
    else:
        form = ContactPersonForm()
    
    context = {
        'form': form,
        'partner': partner,
        'page_title': 'Nouvel interlocuteur'
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partners/partials/contact_form.html', context)
    
    return render(request, 'partners/contact_form.html', context)


@login_required
@require_membership(role_min='editor')
@require_POST
def contact_delete(request, contact_id):
    """Suppression d'un interlocuteur"""
    organization = request.current_org
    contact = get_object_or_404(ContactPerson, id=contact_id, organization=organization)
    partner = contact.partner
    contact.delete()
    messages.success(request, 'Interlocuteur supprimé.')
    
    if request.headers.get('HX-Request'):
        html = render_to_string('partners/partials/contacts_list.html', {
            'partner': partner,
            'contacts': partner.contacts.all()
        }, request=request)
        return HttpResponse(html)
    
    return redirect('partners:partner_detail', display_id=partner.display_id)


# =============================================================================
# PROFILS SPÉCIFIQUES
# =============================================================================

@login_required
@require_membership(role_min='editor')
def client_profile_edit(request, partner_display_id):
    """Édition du profil client"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=partner_display_id, organization=organization)
    
    profile, _ = ClientProfile.objects.get_or_create(
        partner=partner,
        defaults={'organization': organization}
    )
    
    if request.method == 'POST':
        form = ClientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil client mis à jour.')
            return redirect('partners:partner_detail', display_id=partner.display_id)
    else:
        form = ClientProfileForm(instance=profile)
    
    context = {
        'form': form,
        'partner': partner,
        'profile': profile,
        'page_title': f'Profil client - {partner.name}'
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partners/partials/client_profile_form.html', context)
    
    return render(request, 'partners/client_profile_form.html', context)


@login_required
@require_membership(role_min='editor')
def supplier_profile_edit(request, partner_display_id):
    """Édition du profil fournisseur"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=partner_display_id, organization=organization)
    
    profile, _ = SupplierProfile.objects.get_or_create(
        partner=partner,
        defaults={'organization': organization}
    )
    
    if request.method == 'POST':
        form = SupplierProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil fournisseur mis à jour.')
            return redirect('partners:partner_detail', display_id=partner.display_id)
    else:
        form = SupplierProfileForm(instance=profile)
    
    context = {
        'form': form,
        'partner': partner,
        'profile': profile,
        'page_title': f'Profil fournisseur - {partner.name}'
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partners/partials/supplier_profile_form.html', context)
    
    return render(request, 'partners/supplier_profile_form.html', context)


# =============================================================================
# API / AJAX
# =============================================================================

@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def partners_search_ajax(request):
    """API AJAX pour recherche en temps réel"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête AJAX requise'}, status=400)
    
    organization = request.current_org
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    page = int(request.GET.get('page', 1))
    
    partners = Partner.objects.filter(
        organization=organization,
        is_archived=False
    ).prefetch_related('roles')
    
    if search:
        partners = partners.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(code__icontains=search)
        )
    
    if role_filter:
        partners = partners.filter(roles__code=role_filter)
    
    partners = partners.distinct().order_by('name')
    
    paginator = Paginator(partners, 25)
    page_obj = paginator.get_page(page)
    
    # Contexte pour les templates
    context = {
        'partners': page_obj,
        'page_obj': page_obj,
        'role_filter': role_filter,
    }
    
    table_html = render_to_string('partners/partials/partner_table_rows.html', context, request=request)
    pagination_html = render_to_string('partners/partials/pagination.html', context, request=request)
    
    return JsonResponse({
        'success': True,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'stats': {
            'total': Partner.objects.filter(organization=organization, is_archived=False).count(),
            'filtered': paginator.count,
            'current_page': page,
            'total_pages': paginator.num_pages,
        }
    })


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def partners_suggestions_api(request):
    """API suggestions pour autocomplétion"""
    organization = request.current_org
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    limit = min(int(request.GET.get('limit', 10)), 20)
    
    partners = Partner.objects.filter(
        organization=organization,
        is_active=True,
        is_archived=False
    )
    
    if query:
        partners = partners.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        )
    
    if role:
        partners = partners.filter(roles__code=role)
    
    partners = partners.distinct()[:limit]
    
    suggestions = [{
        'id': str(p.id),
        'display_id': p.display_id,
        'code': p.code,
        'name': p.name,
        'email': p.email or '',
        'phone': p.phone or '',
        'roles': list(p.roles.values_list('label', flat=True)),
    } for p in partners]
    
    return JsonResponse({'suggestions': suggestions, 'query': query})


@login_required
@require_membership(role_min='editor')
@require_http_methods(["POST"])
def partner_quick_create_api(request):
    """API création rapide depuis modale"""
    organization = request.current_org
    
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': {'__all__': 'JSON invalide'}}, status=400)
    
    name = (data.get('name') or '').strip()
    role = data.get('role', 'client')
    email = (data.get('email') or '').strip() or None
    phone = (data.get('phone') or '').strip() or None
    segment = data.get('segment', '')
    
    if not name:
        return JsonResponse({'success': False, 'errors': {'name': 'Nom requis'}}, status=400)
    
    try:
        with transaction.atomic():
            partner = Partner(
                organization=organization,
                name=name,
                email=email,
                phone=phone,
                segment=segment,
                is_active=True
            )
            partner.full_clean()
            partner.save()
            
            # Ajouter le rôle
            partner.add_role(role)
            
            # Créer le profil correspondant
            if role == 'client':
                ClientProfile.objects.create(partner=partner, organization=organization)
            elif role == 'supplier':
                SupplierProfile.objects.create(partner=partner, organization=organization)
            
            return JsonResponse({
                'success': True,
                'partner': {
                    'id': str(partner.id),
                    'display_id': partner.display_id,
                    'code': partner.code,
                    'name': partner.name
                }
            })
    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'__all__': str(e)}}, status=400)


@login_required
@require_membership(role_min='editor')
@require_POST
def partner_archive(request, display_id):
    """Archivage d'un partenaire"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=display_id, organization=organization)
    
    partner.is_archived = True
    partner.save()
    
    messages.success(request, f'"{partner.name}" archivé.')
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    
    # Redirection selon contexte
    referer = request.META.get('HTTP_REFERER', '')
    if 'clients' in referer:
        return redirect('partners:clients_list')
    elif 'fournisseurs' in referer:
        return redirect('partners:suppliers_list')
    return redirect('partners:partners_list')


@login_required
@require_membership(role_min='editor')
@require_POST
def partner_restore(request, display_id):
    """Restauration d'un partenaire archivé"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=display_id, organization=organization)
    
    partner.is_archived = False
    partner.save()
    
    messages.success(request, f'"{partner.name}" restauré.')
    return redirect('partners:partner_detail', display_id=partner.display_id)


@login_required
@require_membership(role_min='editor')
@require_POST
def partner_add_role(request, display_id):
    """Ajouter un rôle à un partenaire"""
    organization = request.current_org
    partner = get_object_or_404(Partner, display_id=display_id, organization=organization)
    
    role_code = request.POST.get('role')
    if role_code:
        partner.add_role(role_code)
        
        # Créer le profil si nécessaire
        if role_code == 'client':
            ClientProfile.objects.get_or_create(partner=partner, defaults={'organization': organization})
        elif role_code == 'supplier':
            SupplierProfile.objects.get_or_create(partner=partner, defaults={'organization': organization})
        
        messages.success(request, f'Rôle ajouté.')
    
    return redirect('partners:partner_detail', display_id=partner.display_id)


# =============================================================================
# VUES SIMPLES STYLE PARCELLES (AJAX + HTMX)
# =============================================================================

@login_required
@require_membership(role_min='read_only')
def clients_list_simple(request):
    """
    Liste simple des clients style parcelles.
    Vue principale avec filtres HTMX.
    """
    organization = request.current_org
    
    # Stats de base
    total_count = Partner.objects.filter(
        organization=organization,
        is_archived=False,
        roles__code='client'
    ).distinct().count()
    
    context = {
        'page_title': 'Clients',
        'total_count': total_count,
        'role_filter': 'client',
    }
    
    return render(request, 'partners/clients_list_simple.html', context)


@login_required
@require_membership(role_min='read_only')
def suppliers_list_simple(request):
    """
    Liste simple des fournisseurs style parcelles.
    Vue principale avec filtres HTMX.
    """
    organization = request.current_org
    
    total_count = Partner.objects.filter(
        organization=organization,
        is_archived=False,
        roles__code='supplier'
    ).distinct().count()
    
    context = {
        'page_title': 'Fournisseurs',
        'total_count': total_count,
        'role_filter': 'supplier',
    }
    
    return render(request, 'partners/suppliers_list_simple.html', context)


@login_required
@require_membership(role_min='read_only')
def partners_table_ajax(request, role=None):
    """
    Vue AJAX pour le tableau des partenaires (HTMX).
    Retourne le HTML du tableau filtré.
    """
    organization = request.current_org
    
    # Queryset de base
    partners = Partner.objects.filter(
        organization=organization,
        is_archived=False
    ).prefetch_related('roles', 'addresses').order_by('name')
    
    # Filtrage par rôle
    if role:
        partners = partners.filter(roles__code=role)
    
    # Filtres depuis GET
    q = request.GET.get('q', '').strip()
    segment = request.GET.get('segment', '').strip()
    is_active = request.GET.get('is_active', '').strip()
    country = request.GET.get('country', '').strip()
    
    if q:
        partners = partners.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(vat_number__icontains=q) |
            Q(siret__icontains=q) |
            Q(code__icontains=q)
        )
    
    if segment:
        partners = partners.filter(segment=segment)
    
    if is_active == 'true':
        partners = partners.filter(is_active=True)
    elif is_active == 'false':
        partners = partners.filter(is_active=False)
    
    if country:
        partners = partners.filter(country_code__iexact=country)
    
    # Tri
    sort = request.GET.get('sort', 'name')
    sort_mapping = {
        'name': 'name',
        'name_desc': '-name',
        'email': 'email',
        'created_desc': '-created_at',
        'created_asc': 'created_at',
    }
    order = sort_mapping.get(sort, 'name')
    partners = partners.order_by(order).distinct()
    
    # Pagination
    paginator = Paginator(partners, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'partners': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_count': paginator.count,
        'role_filter': role,
        'selected': {
            'q': q,
            'segment': segment,
            'is_active': is_active,
            'country': country,
            'sort': sort,
        }
    }
    
    return render(request, 'partners/_partners_table.html', context)
