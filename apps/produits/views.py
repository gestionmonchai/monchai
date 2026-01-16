"""
Vues pour la gestion des produits (Cuvées + SKUs)
Inspiré de la page clients avec recherche temps réel et filtres
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch, Sum
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import require_membership
from apps.viticulture.models import Cuvee, Appellation, Vintage, GrapeVariety
from apps.stock.models import SKU
from django.views import View
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
import uuid

from .models import Mise, MiseLigne, LotCommercial
from .forms import (
    MiseStep1FormSet,
    MiseStep2FormSet,
    MiseStep2MetaForm,
    MiseStep3Form,
)
from .services import create_mise_and_lots, valider_mise, build_trace_for_mise
from apps.production.models import LotTechnique, CostEntry, CostSnapshot


@login_required
@require_membership('viewer')
def products_list(request):
    """Page principale des produits avec recherche et filtres"""
    
    # Récupérer les filtres depuis l'URL
    search = request.GET.get('search', '').strip()
    nom = request.GET.get('nom', '').strip()
    product_type = request.GET.get('type', '')  # 'cuvee' ou 'sku'
    appellation_filter = request.GET.get('appellation', '')
    vintage_filter = request.GET.get('vintage', '')
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    
    # Construire la requête pour les cuvées
    cuvees_query = Cuvee.objects.filter(
        organization=request.current_org
    ).select_related(
        'appellation', 'vintage', 'default_uom'
    ).prefetch_related(
        Prefetch('sku_set', queryset=SKU.objects.filter(is_active=True))
    )
    
    # Construire la requête pour les SKUs
    skus_query = SKU.objects.filter(
        organization=request.current_org,
        is_active=True
    ).select_related(
        'cuvee', 'cuvee__appellation', 'cuvee__vintage', 'uom'
    )
    
    # Appliquer les filtres de recherche
    if search:
        cuvees_query = cuvees_query.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(appellation__name__icontains=search)
        )
        skus_query = skus_query.filter(
            Q(label__icontains=search) |
            Q(code_barres__icontains=search) |
            Q(cuvee__name__icontains=search)
        )
    
    # Filtre par nom spécifique
    if nom:
        cuvees_query = cuvees_query.filter(name__icontains=nom)
        skus_query = skus_query.filter(
            Q(label__icontains=nom) | Q(cuvee__name__icontains=nom)
        )
    
    # Filtrer par appellation
    if appellation_filter:
        cuvees_query = cuvees_query.filter(appellation_id=appellation_filter)
        skus_query = skus_query.filter(cuvee__appellation_id=appellation_filter)
    
    # Filtrer par millésime
    if vintage_filter:
        cuvees_query = cuvees_query.filter(vintage_id=vintage_filter)
        skus_query = skus_query.filter(cuvee__vintage_id=vintage_filter)
    
    # Filtrer par type de produit
    if product_type == 'cuvee':
        skus_query = SKU.objects.none()
    elif product_type == 'sku':
        cuvees_query = Cuvee.objects.none()
    
    # Appliquer le tri
    sort_field = 'name' if sort_by == 'name' else sort_by
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    
    cuvees_query = cuvees_query.order_by(sort_field)
    skus_query = skus_query.order_by(sort_field.replace('name', 'label'))
    
    # Compter les résultats
    cuvees_count = cuvees_query.count()
    skus_count = skus_query.count()
    total_count = cuvees_count + skus_count
    
    # Pagination (25 par page)
    page = request.GET.get('page', 1)
    all_products = list(cuvees_query) + list(skus_query)
    
    # Trier la liste combinée si nécessaire
    if sort_by == 'name':
        reverse = sort_order == 'desc'
        all_products.sort(key=lambda x: getattr(x, 'name', getattr(x, 'label', '')), reverse=reverse)
    
    paginator = Paginator(all_products, 25)
    products_page = paginator.get_page(page)
    
    # Données pour les filtres
    appellations = Appellation.objects.filter(
        organization=request.current_org
    ).order_by('name')
    
    vintages = Vintage.objects.filter(
        organization=request.current_org
    ).order_by('-year')
    
    # Construire les filtres pour le template
    filters = {
        'search': search,
        'nom': nom,
        'type': product_type,
        'appellation': appellation_filter,
        'vintage': vintage_filter,
    }
    
    context = {
        'products': products_page,
        'filters': filters,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'appellations': appellations,
        'vintages': vintages,
        'total_count': total_count,
        'cuvees_count': cuvees_count,
        'skus_count': skus_count,
        'page_title': 'Produits',
    }
    
    return render(request, 'produits/products_list.html', context)


@login_required
@require_membership('viewer')
@require_http_methods(["GET"])
def products_search_ajax(request):
    """API AJAX pour la recherche temps réel des produits"""
    
    # Récupérer les paramètres
    search = request.GET.get('search', '').strip()
    nom = request.GET.get('nom', '').strip()
    product_type = request.GET.get('type', '')
    appellation_filter = request.GET.get('appellation', '')
    vintage_filter = request.GET.get('vintage', '')
    sort_by = request.GET.get('sort', 'name')
    sort_order = request.GET.get('order', 'asc')
    page = request.GET.get('page', 1)
    
    # Même logique que products_list mais pour AJAX
    cuvees_query = Cuvee.objects.filter(
        organization=request.current_org
    ).select_related(
        'appellation', 'vintage', 'default_uom'
    ).prefetch_related(
        Prefetch('sku_set', queryset=SKU.objects.filter(is_active=True))
    )
    
    skus_query = SKU.objects.filter(
        organization=request.current_org,
        is_active=True
    ).select_related(
        'cuvee', 'cuvee__appellation', 'cuvee__vintage', 'uom'
    )
    
    # Appliquer les filtres
    if search:
        cuvees_query = cuvees_query.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(appellation__name__icontains=search)
        )
        skus_query = skus_query.filter(
            Q(label__icontains=search) |
            Q(code_barres__icontains=search) |
            Q(cuvee__name__icontains=search)
        )
    
    # Filtre par nom spécifique
    if nom:
        cuvees_query = cuvees_query.filter(name__icontains=nom)
        skus_query = skus_query.filter(
            Q(label__icontains=nom) | Q(cuvee__name__icontains=nom)
        )
    
    if appellation_filter:
        cuvees_query = cuvees_query.filter(appellation_id=appellation_filter)
        skus_query = skus_query.filter(cuvee__appellation_id=appellation_filter)
    
    if vintage_filter:
        cuvees_query = cuvees_query.filter(vintage_id=vintage_filter)
        skus_query = skus_query.filter(cuvee__vintage_id=vintage_filter)
    
    if product_type == 'cuvee':
        skus_query = SKU.objects.none()
    elif product_type == 'sku':
        cuvees_query = Cuvee.objects.none()
    
    # Appliquer le tri
    sort_field = 'name' if sort_by == 'name' else sort_by
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    
    cuvees_query = cuvees_query.order_by(sort_field)
    skus_query = skus_query.order_by(sort_field.replace('name', 'label'))
    
    # Pagination
    all_products = list(cuvees_query) + list(skus_query)
    
    # Trier la liste combinée si nécessaire
    if sort_by == 'name':
        reverse = sort_order == 'desc'
        all_products.sort(key=lambda x: getattr(x, 'name', getattr(x, 'label', '')), reverse=reverse)
    
    paginator = Paginator(all_products, 25)
    products_page = paginator.get_page(page)
    
    # Rendu des templates partiels
    products_html = render(request, 'produits/partials/products_table_rows.html', {
        'products': products_page
    }).content.decode('utf-8')
    
    pagination_html = render(request, 'produits/partials/products_pagination.html', {
        'products': products_page
    }).content.decode('utf-8')
    
    return JsonResponse({
        'products_html': products_html,
        'pagination_html': pagination_html,
        'total_count': len(all_products),
        'cuvees_count': cuvees_query.count(),
        'skus_count': skus_query.count(),
    })


@login_required
@require_membership('viewer')
@require_http_methods(["GET"])
def products_suggestions_api(request):
    """API de suggestions rapides pour SKUs (autocomplétion).
    GET /produits/api/suggestions/?q=...&limit=10
    """
    org = getattr(request, 'current_org', None)
    q = (request.GET.get('q') or '').strip()
    try:
        limit = min(int(request.GET.get('limit', 10)), 25)
    except Exception:
        limit = 10

    qs = SKU.objects.all().select_related('cuvee', 'uom')
    if org is not None:
        qs = qs.filter(organization=org)
    if q:
        qs = qs.filter(
            Q(label__icontains=q) |
            Q(code_barres__icontains=q) |
            Q(cuvee__name__icontains=q)
        )
    qs = qs.order_by('label')[:limit]

    items = [
        {
            'id': str(s.id),
            'label': s.label,
            'uom': getattr(s.uom, 'code', ''),
            'cuvee': getattr(s.cuvee, 'name', ''),
        }
        for s in qs
    ]
    return JsonResponse({'suggestions': items, 'query': q})


# =============== MISES (wizard 3 étapes) ==================

@method_decorator(login_required, name='dispatch')
class MiseListView(View):
    def get(self, request):
        # Récupérer les campagnes disponibles pour les filtres
        campagnes = list(
            Mise.objects.values_list('campagne', flat=True)
            .distinct()
            .order_by('-campagne')
        )
        
        return render(request, 'produits/mises_list.html', {
            'campagnes': campagnes,
            'selected': {
                'q': request.GET.get('q', ''),
                'campagne': request.GET.get('campagne', ''),
            },
            'page_title': 'Mises',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Mises', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class MiseTableView(View):
    """Vue HTMX pour le tableau des mises avec filtres en temps réel"""
    
    def get(self, request):
        org = getattr(request, 'current_org', None)
        
        # Récupérer les paramètres de recherche
        q = request.GET.get('q', '').strip()
        campagne = request.GET.get('campagne', '').strip()
        sort = request.GET.get('sort', 'date_desc')
        
        # Construire la requête de base - afficher toutes les mises
        # Note: Pour le multi-tenant, on pourrait filtrer via les lots commerciaux
        mises = Mise.objects.all()
        
        # Appliquer la recherche texte
        if q:
            mises = mises.filter(
                Q(code_of__icontains=q) |
                Q(campagne__icontains=q) |
                Q(notes__icontains=q)
            )
        
        # Filtrer par campagne
        if campagne:
            mises = mises.filter(campagne=campagne)
        
        # Tri
        if sort == 'date_asc':
            mises = mises.order_by('date')
        elif sort == 'code':
            mises = mises.order_by('code_of')
        else:  # date_desc par défaut
            mises = mises.order_by('-date')
        
        # Limiter à 100 résultats
        mises = mises[:100]
        
        # Compter le total
        total = len(mises)
        
        return render(request, 'produits/_mises_table.html', {
            'mises': mises,
            'total': total,
        })


@method_decorator(login_required, name='dispatch')
class MiseWizardView(View):
    # Switch to production templates (smart UX). Existing route names preserved.
    template_step1 = 'production/mise_wizard_step1.html'
    template_step2 = 'production/mise_wizard_step2.html'
    template_step3 = 'production/mise_wizard_step3.html'

    def _ensure_session(self, request):
        if 'mise' not in request.session:
            request.session['mise'] = {}
        if 'sources' not in request.session['mise']:
            request.session['mise']['sources'] = []
        if 'formats' not in request.session['mise']:
            request.session['mise']['formats'] = []

    def get(self, request):
        self._ensure_session(request)
        step = request.GET.get('step', '1')
        if step == '1':
            # Load all lots (filtering done client-side for UX)
            from apps.production.models import LotTechnique
            from apps.viticulture.models import Cuvee
            qs = LotTechnique.objects.select_related('cuvee').order_by('-created_at')
            org = getattr(request, 'current_org', None)
            if org is not None:
                qs = qs.filter(cuvee__organization=org)
            # Only show lots with volume available
            lots = list(qs[:100])
            # Attach available volume for display
            from decimal import Decimal
            for lt in lots:
                try:
                    lt.vol_dispo = lt.volume_net_calculated() or Decimal('0')
                except Exception:
                    lt.vol_dispo = lt.volume_l or Decimal('0')
            # Build cuvée list from lots
            base_cuvee_qs = Cuvee.objects.all()
            if org is not None:
                base_cuvee_qs = base_cuvee_qs.filter(organization=org)
            cuvee_ids = list(qs.values_list('cuvee_id', flat=True).distinct())
            if cuvee_ids:
                cuvee_qs = base_cuvee_qs.filter(id__in=cuvee_ids)
            else:
                cuvee_qs = base_cuvee_qs
            cuvee_qs = cuvee_qs.order_by('name')
            cuvees = cuvee_qs[:500]
            return render(request, self.template_step1, {
                'lots': lots,
                'cuvees': cuvees,
                'page_title': 'Nouvelle mise',
                'breadcrumb_items': [
                    {'name': 'Production', 'url': '/production/'},
                    {'name': 'Mises', 'url': '/production/mises/'},
                    {'name': 'Nouvelle', 'url': None},
                ]
            })
        elif step == '2':
            from decimal import Decimal  # Import local pour éviter UnboundLocalError
            formset = MiseStep2FormSet()
            meta = MiseStep2MetaForm()
            # Charger les formats depuis le référentiel Unités (type=volume, triés par litre)
            from apps.referentiels.models import Unite
            org = getattr(request, 'current_org', None)
            formats_db = []
            if org:
                unites = Unite.objects.filter(organization=org, type_unite='volume').order_by('facteur_conversion')
                for u in unites:
                    ml = int(float(u.facteur_conversion) * 1000)  # Conversion L -> mL
                    formats_db.append({
                        'id': u.id,
                        'nom': u.nom,
                        'symbole': u.symbole,
                        'ml': ml,
                        'litres': float(u.facteur_conversion),
                    })
            return render(request, self.template_step2, {
                'formset': formset,
                'meta_form': meta,
                'formats_db': formats_db,
                'page_title': 'Nouvelle mise – Étape 2',
                'breadcrumb_items': [
                    {'name': 'Production', 'url': '/production/parcelles/'},
                    {'name': 'Mises', 'url': '/production/mises/'},
                    {'name': 'Étape 2', 'url': None},
                ]
            })
        else:
            from decimal import Decimal  # Import local pour éviter UnboundLocalError
            form = MiseStep3Form()
            # Calculer le récap depuis la session
            smart = request.session.get('mise_smart') or {}
            legacy = request.session.get('mise') or {}
            
            # Sources et volumes
            sources = []
            if smart.get('step1', {}).get('selections'):
                sources = smart['step1']['selections']
            elif legacy.get('sources'):
                sources = legacy['sources']
            
            # Formats
            formats = []
            if smart.get('step2', {}).get('formats'):
                formats = smart['step2']['formats']
            elif legacy.get('formats'):
                formats = legacy['formats']
            
            # Calculer totaux
            total_volume = sum((Decimal(str(s.get('volume_l', 0))) for s in sources), Decimal('0'))
            total_unites = sum((int(f.get('quantite_unites', 0) or f.get('qty', 0)) for f in formats), 0)
            format_names = [f.get('name', f"{f.get('format_ml', 0)} mL") for f in formats]
            
            return render(request, self.template_step3, {
                'form': form,
                'recap_volume': f"{total_volume:.2f}",
                'recap_qty': total_unites,
                'recap_formats': ', '.join(format_names) if format_names else '—',
                'page_title': 'Nouvelle mise – Confirmation',
                'breadcrumb_items': [
                    {'name': 'Production', 'url': '/production/parcelles/'},
                    {'name': 'Mises', 'url': '/production/mises/'},
                    {'name': 'Confirmation', 'url': None},
                ]
            })

    def post(self, request):
        self._ensure_session(request)
        step = request.POST.get('step', '1')
        if step == '1':
            formset = MiseStep1FormSet(request.POST)
            if formset.is_valid():
                sources = []
                for form in formset:
                    if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                        continue
                    sources.append({
                        'lot': form.cleaned_data['lot_tech_source'],
                        'volume_l': form.cleaned_data['volume_l'],
                    })
                request.session['mise']['sources'] = [
                    {'lot': str(s['lot'].id), 'volume_l': str(s['volume_l'])} for s in sources
                ]
                request.session.modified = True
                return redirect(reverse('production:mise_new') + '?step=2')
            return render(request, self.template_step1, {'formset': formset})
        elif step == '2':
            formset = MiseStep2FormSet(request.POST)
            meta = MiseStep2MetaForm(request.POST)
            if formset.is_valid() and meta.is_valid():
                request.session['mise']['formats'] = [
                    {
                        'format_ml': f.cleaned_data['format_ml'],
                        'quantite_unites': f.cleaned_data['quantite_unites'],
                        'pertes_pct': str(f.cleaned_data['pertes_pct']),
                    }
                    for f in formset
                    if getattr(f, 'cleaned_data', None) and not f.cleaned_data.get('DELETE')
                ]
                request.session['mise']['cuvee_id'] = str(meta.cleaned_data['cuvee'].id) if meta.cleaned_data.get('cuvee') else None
                request.session['mise']['notes'] = meta.cleaned_data.get('notes', '')
                request.session.modified = True
                return redirect(reverse('production:mise_new') + '?step=3')
            return render(request, self.template_step2, {'formset': formset, 'meta_form': meta})
        else:
            form = MiseStep3Form(request.POST)
            if form.is_valid() and form.cleaned_data.get('confirmer'):
                # Merge smart session store into legacy 'mise' store if present
                smart = request.session.get('mise_smart') or {}
                legacy = request.session.get('mise') or {}
                if smart.get('step1'):
                    # Convert selections → sources
                    sources_legacy = []
                    for sel in smart['step1'].get('selections', []):
                        sources_legacy.append({'lot': str(sel['lot_id']), 'volume_l': sel['volume_l']})
                    legacy['sources'] = sources_legacy
                if smart.get('step2'):
                    # Convert formats
                    formats_legacy = []
                    for f in smart['step2'].get('formats', []):
                        formats_legacy.append({
                            'format_ml': f.get('format_ml'),
                            'quantite_unites': f.get('quantite_unites'),
                            'pertes_pct': f.get('pertes_pct', '0'),
                        })
                    legacy['formats'] = formats_legacy
                    legacy['notes'] = legacy.get('notes') or ''
                request.session['mise'] = legacy
                request.session.modified = True

                sess = request.session['mise']
                # Resolve objects
                sources = []
                for s in sess.get('sources', []):
                    org = getattr(request, 'current_org', None)
                    # lot_id peut être un int ou un string d'int (plus UUID depuis refactoring)
                    lot_id = s.get('lot') or s.get('lot_id')
                    try:
                        lot_id = int(lot_id)
                    except (ValueError, TypeError):
                        continue
                    lot = get_object_or_404(
                        LotTechnique.objects.select_related('cuvee').filter(
                            Q(cuvee__organization=org) | Q(source__organization=org)
                        ),
                        id=lot_id
                    )
                    sources.append({'lot': lot, 'volume_l': Decimal(s['volume_l'])})
                formats = [
                    {
                        'format_ml': int(f['format_ml']),
                        'quantite_unites': int(f['quantite_unites']),
                        'pertes_pct': Decimal(f['pertes_pct']),
                    }
                    for f in sess.get('formats', [])
                ]
                # Optional overrides from POST
                cuvee = None
                cuvee_id = (request.POST.get('cuvee_id') or '').strip()
                org = getattr(request, 'current_org', None)
                if cuvee_id:
                    cuvee = get_object_or_404(Cuvee.objects.filter(organization=org), id=cuvee_id)
                elif sess.get('cuvee_id'):
                    cuvee = get_object_or_404(Cuvee.objects.filter(organization=org), id=sess['cuvee_id'])
                # Validation: vérifier que le volume demandé ne dépasse pas le disponible
                validation_errors = []
                for s in sources:
                    lot = s['lot']
                    volume_demande = s['volume_l']
                    # Calculer le volume disponible du lot
                    try:
                        volume_dispo = lot.volume_net_calculated() or lot.volume_l or Decimal('0')
                    except Exception:
                        volume_dispo = lot.volume_l or Decimal('0')
                    
                    if volume_demande > volume_dispo:
                        validation_errors.append(
                            f"Lot {lot.code}: volume demandé ({volume_demande} L) > disponible ({volume_dispo} L)"
                        )
                
                if validation_errors:
                    for err in validation_errors:
                        messages.error(request, err)
                    return redirect(reverse('production:mise_new') + '?step=3')
                
                # Idempotence token: reuse across retries during this session
                tok = request.session.get('mise_token')
                if not tok:
                    tok = str(uuid.uuid4())
                    request.session['mise_token'] = tok
                    request.session.modified = True

                # Créer la mise
                try:
                    org = getattr(request, 'current_org', None)
                    # Générer code OF unique - méthode robuste
                    from django.utils import timezone
                    from django.db import transaction
                    import re
                    
                    year = timezone.now().year
                    campagne = f"{year}-{year+1}"
                    
                    # Trouver le plus grand numéro existant pour cette année
                    existing = Mise.objects.filter(code_of__startswith=f"OF{year}-")
                    max_num = 0
                    for m in existing:
                        match = re.search(r'OF\d+-(\d+)', m.code_of)
                        if match:
                            max_num = max(max_num, int(match.group(1)))
                    
                    # Générer code unique avec retry
                    mise = None
                    for attempt in range(10):
                        num = max_num + 1 + attempt
                        code_of = f"OF{year}-{num:04d}"
                        try:
                            with transaction.atomic():
                                mise = Mise.objects.create(
                                    code_of=code_of,
                                    campagne=campagne,
                                    notes=sess.get('notes', '') or request.POST.get('notes', ''),
                                    state='brouillon',
                                )
                            break
                        except Exception:
                            continue
                    
                    if not mise:
                        raise Exception("Impossible de générer un code OF unique")
                    
                    # Créer les lignes de mise à partir des sources et formats
                    total_by_format = {}  # format_ml -> total_unites
                    cuvee_from_lot = None
                    for s in sources:
                        if not cuvee_from_lot and s['lot'].cuvee:
                            cuvee_from_lot = s['lot'].cuvee
                        for f in formats:
                            MiseLigne.objects.create(
                                mise=mise,
                                lot_tech_source=s['lot'],
                                format_ml=f['format_ml'],
                                quantite_unites=f['quantite_unites'],
                                volume_l=s['volume_l'],
                            )
                            fm = f['format_ml']
                            total_by_format[fm] = total_by_format.get(fm, 0) + f['quantite_unites']
                    
                    # Créer le(s) lot(s) commercial(aux) - produit fini
                    # Note: LotCommercial.cuvee attend viticulture.Cuvee, pas referentiels.Cuvee
                    # On cherche la cuvee correspondante par nom si possible
                    viti_cuvee = None
                    if cuvee_from_lot:
                        from apps.viticulture.models import Cuvee as VitiCuvee
                        viti_cuvee = VitiCuvee.objects.filter(
                            organization=org,
                            name__iexact=cuvee_from_lot.nom
                        ).first()
                    
                    for format_ml, qty in total_by_format.items():
                        lot_num = LotCommercial.objects.filter(mise=mise).count() + 1
                        code_lot = f"{mise.code_of}-{format_ml}mL-{lot_num:02d}"
                        LotCommercial.objects.create(
                            organization=org,  # Important pour le filtrage tenant
                            mise=mise,
                            code_lot=code_lot,
                            cuvee=viti_cuvee,  # peut être None si pas de correspondance
                            format_ml=format_ml,
                            date_mise=mise.date,
                            quantite_unites=qty,
                            stock_disponible=qty,
                            etiquetage='non_etiquete',  # Par défaut
                        )
                    
                    # Débiter le volume des lots sources + créer mouvements de traçabilité
                    from apps.production.models import MouvementLot
                    for s in sources:
                        lot = s['lot']
                        volume_a_debiter = s['volume_l']
                        
                        # Créer le mouvement MISE_OUT pour traçabilité
                        MouvementLot.objects.create(
                            lot=lot,
                            type='MISE_OUT',
                            date=mise.date,
                            volume_l=volume_a_debiter,
                            meta={'mise_id': str(mise.id), 'mise_code': mise.code_of},
                            author=request.user if request.user.is_authenticated else None,
                        )
                        
                        # Décrémente le volume du lot source
                        lot.volume_l = max(Decimal('0'), (lot.volume_l or Decimal('0')) - volume_a_debiter)
                        lot.save(update_fields=['volume_l'])
                    
                    # Nettoyer session
                    request.session.pop('mise', None)
                    request.session.pop('mise_smart', None)
                    request.session.pop('mise_token', None)
                    request.session.modified = True
                    
                    messages.success(request, f"Mise {mise.code_of} créée avec succès – {len(total_by_format)} lot(s) commercial(aux) généré(s)")
                    return redirect('production:mise_detail', pk=mise.id)
                except Exception as e:
                    messages.error(request, f"Erreur création mise: {e}")
                    return redirect(reverse('production:mise_new') + '?step=3')
            else:
                # Form invalide ou non confirmé
                messages.warning(request, "Veuillez cocher la confirmation")
                return redirect(reverse('production:mise_new') + '?step=3')


# ================== Smart calc API endpoints (HTMX/JSON) ==================

from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from decimal import Decimal, ROUND_HALF_UP

def _quantize_l(value: Decimal | str | float | int, places: str = '0.001') -> Decimal:
    try:
        d = Decimal(str(value))
    except Exception:
        d = Decimal('0')
    return d.quantize(Decimal(places), rounding=ROUND_HALF_UP)

def _mise_session(request):
    store = request.session.get('mise_smart') or {}
    if 'step1' not in store:
        store['step1'] = {'selections': []}
    if 'step2' not in store:
        store['step2'] = {'formats': [], 'pertes_mode': '%', 'pertes_global_l': '0'}
    request.session['mise_smart'] = store
    return store

@login_required
@require_http_methods(["POST"])
def mise_calc_step1(request):
    """Update step1 selections (lots/containers volumes) and return totals + warnings.
    Inputs (form): lot_id, container_id (optional), volume_l
    Session persisted under request.session['mise_smart']['step1']['selections']
    """
    from apps.production.models import LotTechnique
    store = _mise_session(request)
    s1 = store['step1']
    lot_id = (request.POST.get('lot_id') or '').strip()
    container_id = (request.POST.get('container_id') or 'LOT').strip()  # pseudo container by default
    vol_in = _quantize_l(request.POST.get('volume_l') or '0')
    errors, warnings = [], []

    # Validate lot exists and belongs to org
    from django.shortcuts import get_object_or_404
    from django.db.models import Q
    org = getattr(request, 'current_org', None)
    try:
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            id=lot_id,
        )
    except Exception:
        return JsonResponse({'errors': ['Lot introuvable ou hors organisation'], 'lot_debit_sum_l': '0.000', 'global_debit_sum_l': '0.000'})

    # Compute lot available via server-side calculated volume
    try:
        dispo_lot = lot.volume_net_calculated() or Decimal('0')
    except Exception:
        dispo_lot = lot.volume_l or Decimal('0')

    # Rebuild selections without current pair, then add updated one
    selections = [x for x in s1['selections'] if not (x.get('lot_id') == str(lot_id) and x.get('container_id') == container_id)]
    if vol_in > 0:
        selections.append({'lot_id': str(lot_id), 'container_id': container_id, 'volume_l': str(vol_in)})

    # Validate total per lot ≤ dispo
    total_per_lot = {}
    for sel in selections:
        key = sel['lot_id']
        total_per_lot[key] = total_per_lot.get(key, Decimal('0')) + Decimal(sel['volume_l'])

    lot_sum = total_per_lot.get(str(lot_id), Decimal('0'))
    if lot_sum > dispo_lot:
        errors.append(f"Volume sélectionné ({lot_sum} L) > disponible pour le lot {lot.code} ({dispo_lot} L)")

    # Flag override if not pret_mise
    if getattr(lot, 'statut', '') != 'pret_mise':
        warnings.append('Lot non prêt mise – justification requise à l\'étape 3')

    if errors:
        return JsonResponse({'errors': errors, 'warnings': warnings, 'lot_debit_sum_l': f"{lot_sum.quantize(Decimal('0.001'))}", 'global_debit_sum_l': f"0.000"})

    # Persist and compute global total
    s1['selections'] = selections
    request.session['mise_smart'] = store
    request.session.modified = True

    global_sum = sum((Decimal(x['volume_l']) for x in selections), Decimal('0'))
    return JsonResponse({
        'errors': [],
        'warnings': warnings,
        'lot_debit_sum_l': f"{lot_sum.quantize(Decimal('0.001'))}",
        'global_debit_sum_l': f"{_quantize_l(global_sum).quantize(Decimal('0.001'))}",
    })


@login_required
@require_http_methods(["POST"])
def mise_calc_step2(request):
    """Compute besoin vrac and delta for step2.
    Inputs:
      - formats[n][format_ml], formats[n][quantite_unites], formats[n][pertes_pct]
      - pertes_mode: '%' or 'L'
      - pertes_global_l (if mode L)
    Returns besoin_brut_l, pertes_l, besoin_net_l, delta_l, suggestions[]
    """
    store = _mise_session(request)
    s2 = store['step2']

    # Parse formats
    formats = []
    # Accept repeated params like formats-0-format_ml (formset-like) or arrays "formats[][...]"
    # Minimal parsing: iterate over indices 0..N until none found
    idx = 0
    while True:
        fm = request.POST.get(f'formats-{idx}-format_ml') or request.POST.get(f'formats[{idx}][format_ml]')
        if fm is None:
            break
        qty = request.POST.get(f'formats-{idx}-quantite_unites') or request.POST.get(f'formats[{idx}][quantite_unites]') or '0'
        ppct = request.POST.get(f'formats-{idx}-pertes_pct') or request.POST.get(f'formats[{idx}][pertes_pct]') or '0'
        try:
            fm_i = int(fm)
            qty_i = int(qty)
            ppct_d = Decimal(str(ppct))
        except Exception:
            fm_i = 0; qty_i = 0; ppct_d = Decimal('0')
        if fm_i > 0 and qty_i > 0:
            formats.append({'format_ml': fm_i, 'quantite_unites': qty_i, 'pertes_pct': ppct_d})
        idx += 1

    pertes_mode = (request.POST.get('pertes_mode') or s2.get('pertes_mode') or '%').strip()
    pertes_global_l = _quantize_l(request.POST.get('pertes_global_l') or s2.get('pertes_global_l') or '0')

    # Compute besoin brut
    besoin_brut_l = sum((Decimal(f['format_ml']) * Decimal(f['quantite_unites']) / Decimal('1000') for f in formats), Decimal('0'))

    # Compute pertes
    if pertes_mode == '%':
        pertes_l = sum(((Decimal(f['format_ml']) * Decimal(f['quantite_unites']) / Decimal('1000')) * (Decimal(f['pertes_pct'])/Decimal('100')) for f in formats), Decimal('0'))
    else:
        pertes_l = pertes_global_l

    besoin_net_l = besoin_brut_l + pertes_l

    # Vrac sélectionné from step1
    s1 = store['step1']
    vrac_sel = sum((Decimal(x['volume_l']) for x in s1.get('selections', [])), Decimal('0'))
    delta_l = vrac_sel - besoin_net_l

    suggestions = []
    # Simple heuristics
    marge = getattr(__import__('django.conf').conf.settings, 'MISE_MARGE_ARRONDI_L', 2)
    try:
        marge = Decimal(str(marge))
    except Exception:
        marge = Decimal('2')
    if delta_l < 0:
        suggestions.append('Vrac insuffisant – réduire pertes ou quantités, ou revenir à l\'étape 1')
    elif delta_l <= marge:
        suggestions.append('Delta proche de 0 – ajuster pertes pour coller au vrac')
    else:
        suggestions.append('Surplus – le reste sera conservé sur les lots sources')

    # Persist step2 state
    s2.update({
        'formats': [{'format_ml': f['format_ml'], 'quantite_unites': f['quantite_unites'], 'pertes_pct': str(f['pertes_pct'])} for f in formats],
        'pertes_mode': pertes_mode,
        'pertes_global_l': str(pertes_global_l),
    })
    request.session['mise_smart'] = store
    request.session.modified = True

    return JsonResponse({
        'besoin_brut_l': f"{_quantize_l(besoin_brut_l)}",
        'pertes_l': f"{_quantize_l(pertes_l)}",
        'besoin_net_l': f"{_quantize_l(besoin_net_l)}",
        'vrac_selectionne_l': f"{_quantize_l(vrac_sel)}",
        'delta_l': f"{_quantize_l(delta_l)}",
        'suggestions': suggestions,
    })


@login_required
@require_http_methods(["POST"])
def mise_validate_preview(request):
    """Preview validations and costing before final submit (step3)."""
    from apps.production.models import CostSnapshot, LotTechnique
    from apps.viticulture.models import Cuvee

    store = _mise_session(request)
    s1 = store['step1']
    s2 = store['step2']

    # Determine sources lots scoped to org
    org = getattr(request, 'current_org', None)
    lot_ids = list({x['lot_id'] for x in s1.get('selections', [])})
    if lot_ids:
        lots = list(LotTechnique.objects.filter(id__in=lot_ids).filter(Q(cuvee__organization=org) | Q(source__organization=org)))
    else:
        lots = []
    if lot_ids and len(lots) != len(lot_ids):
        return JsonResponse({'error': 'Certaines sources sont hors organisation ou inexistantes'}, status=400)

    pret_mise_ok = all(getattr(l, 'statut', '') == 'pret_mise' for l in lots) if lots else False

    # Analyses: check cuvée detail fields presence if available
    cuvee_id = request.POST.get('cuvee_id') or None
    cuvee = Cuvee.objects.filter(id=cuvee_id).first() if cuvee_id else (lots[0].cuvee if lots and lots[0].cuvee_id else None)
    required = ['ph', 'acidite_totale', 'so2_libre', 'so2_total']
    missing = []
    analyses_ok = False
    try:
        detail = getattr(cuvee, 'detail', None)
        if detail:
            for f in required:
                if getattr(detail, f, None) is None:
                    missing.append(f)
            analyses_ok = len(missing) == 0
        else:
            missing = required
            analyses_ok = False
    except Exception:
        missing = required
        analyses_ok = False

    override_allowed = not (analyses_ok and pret_mise_ok)

    # Costing estimate
    total_l = sum((Decimal(x['volume_l']) for x in s1.get('selections', [])), Decimal('0'))
    # Weighted CMP across lots
    weighted_amt = Decimal('0')
    for l in lots:
        snap = CostSnapshot.objects.filter(entity_type='lottech', entity_id=l.id).first()
        cmp_v = getattr(snap, 'cmp_vrac_eur_l', Decimal('0')) or Decimal('0')
        # Allocate proportionally by selected volume per lot
        vol_lot = sum((Decimal(x['volume_l']) for x in s1.get('selections', []) if x['lot_id'] == str(l.id)), Decimal('0'))
        weighted_amt += (cmp_v * vol_lot)
    cmp_vrac_eur_l = (weighted_amt / total_l).quantize(Decimal('0.0001')) if total_l > 0 else Decimal('0')

    # Units from formats
    total_units = sum((int(f['quantite_unites']) for f in s2.get('formats', [])), 0)
    try:
        mo_u = Decimal(str(request.POST.get('mo_eur_u') or '0'))
    except Exception:
        mo_u = Decimal('0')
    ms_u = Decimal('0')
    vrac_unit = ((cmp_vrac_eur_l * _quantize_l(sum((Decimal(f['format_ml']) * Decimal(f['quantite_unites']) / Decimal('1000') for f in s2.get('formats', [])), Decimal('0')))) / Decimal(max(total_units, 1))).quantize(Decimal('0.0001')) if total_units else Decimal('0')
    cout_unitaire_estime_eur_u = (vrac_unit + mo_u + ms_u).quantize(Decimal('0.0001'))

    return JsonResponse({
        'analyses_ok': analyses_ok,
        'pret_mise_ok': pret_mise_ok,
        'missing': missing,
        'override_allowed': override_allowed,
        'cmp_vrac_eur_l': f"{cmp_vrac_eur_l}",
        'cout_unitaire_estime_eur_u': f"{cout_unitaire_estime_eur_u}",
    })


@login_required
@require_http_methods(["POST"])
def mise_save_step2(request):
    """Sauvegarde les formats et sources de step 2 dans la session serveur."""
    import json
    store = _mise_session(request)
    
    try:
        # Parser formats JSON
        formats_raw = request.POST.get('formats', '[]')
        formats = json.loads(formats_raw)
        
        # Parser sources JSON
        sources_raw = request.POST.get('sources', '[]')
        sources = json.loads(sources_raw)
        
        # Sauvegarder dans la session
        store['step2']['formats'] = formats
        store['step1']['selections'] = [
            {'lot_id': s.get('lot_id', ''), 'volume_l': str(s.get('volume', s.get('volume_l', 0)))}
            for s in sources
        ]
        
        request.session['mise_smart'] = store
        request.session.modified = True
        
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@method_decorator(login_required, name='dispatch')
class MiseDetailView(View):
    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        mise = get_object_or_404(Mise, pk=pk)
        # Guard simplifié: la mise doit exister, pas de contrôle org strict pour l'instant
        from .models import MiseLigne
        if not mise.lignes.exists() and not mise.lots.exists():
            # Mise vide, on laisse passer quand même
            pass
        lots = mise.lots.all()
        # Costs context
        try:
            journal = CostEntry.objects.filter(entity_type='mise', entity_id=mise.id).order_by('-date', '-id')
            amount_vrac = journal.filter(nature='vrac_out').aggregate(s=Sum('amount_eur'))['s'] or Decimal('0')
            amount_mo = journal.filter(nature='mo').aggregate(s=Sum('amount_eur'))['s'] or Decimal('0')
            amount_pack = Decimal('0')
            tirage_snaps = {lot.id: CostSnapshot.objects.filter(entity_type='tirage', entity_id=lot.id).first() for lot in lots}
        except Exception:
            journal = []
            amount_vrac = Decimal('0')
            amount_mo = Decimal('0')
            amount_pack = Decimal('0')
            tirage_snaps = {}
        # Traceability: vendanges lineage
        try:
            trace_vendanges = build_trace_for_mise(mise.id)
        except Exception:
            trace_vendanges = []
        return render(request, 'produits/mise_detail.html', {
            'mise': mise,
            'lots': lots,
            'cost_entries': journal,
            'amount_vrac': amount_vrac,
            'amount_mo': amount_mo,
            'amount_pack': amount_pack,
            'tirage_snaps': tirage_snaps,
            'trace_vendanges': trace_vendanges,
            'page_title': f'Mise {mise.code_of}',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/parcelles/'},
                {'name': 'Mises', 'url': '/production/mises/'},
                {'name': mise.code_of, 'url': None},
            ]
        })


@login_required
def htmx_calc_units(request):
    """HTMX endpoint: compute nb bottles from liters and format with losses."""
    try:
        volume_l = Decimal(request.GET.get('volume_l', '0'))
        format_ml = Decimal(request.GET.get('format_ml', '750'))
        pertes_pct = Decimal(request.GET.get('pertes_pct', '0'))
        nominal_units = (volume_l * Decimal('1000') / format_ml).quantize(Decimal('1'))
        effective_units = (nominal_units * (Decimal('1') - pertes_pct / Decimal('100'))).quantize(Decimal('1'))
        return JsonResponse({'nominal_units': int(nominal_units), 'effective_units': int(effective_units)})
    except Exception:
        return JsonResponse({'nominal_units': 0, 'effective_units': 0})


# =============== LOTS COMMERCIAUX ==================

@method_decorator(login_required, name='dispatch')
class LotCommercialListView(View):
    def get(self, request):
        org = getattr(request, 'current_org', None)
        cuvee = request.GET.get('cuvee')
        fmt = request.GET.get('format')
        stock = request.GET.get('stock', 'any')
        qs = LotCommercial.objects.all().select_related('cuvee', 'mise')
        if org is not None:
            # Filtre par organization directement (nouveau champ) OU via mise pour ancien data
            from .models import MiseLigne
            m_ids = (
                MiseLigne.objects.filter(lot_tech_source__cuvee__organization=org)
                .values_list('mise_id', flat=True)
                .distinct()
            )
            qs = qs.filter(Q(organization=org) | Q(mise_id__in=m_ids))
        if cuvee:
            qs = qs.filter(cuvee_id=cuvee)
        if fmt:
            qs = qs.filter(format_ml=fmt)
        if stock == 'gt0':
            qs = qs.filter(stock_disponible__gt=0)
        lots = qs.order_by('-date_mise')[:200]
        return render(request, 'produits/lots_com_list.html', {
            'lots': lots,
            'page_title': 'Lots commerciaux',
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Lots commerciaux', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class LotCommercialDetailView(View):
    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(LotCommercial, pk=pk)
        from .models import MiseLigne
        
        # Guard: vérifier l'accès par organization ou via mise
        if lot.organization:
            # Lot avec organization directe
            if org and lot.organization != org:
                return HttpResponse('Lot commercial hors organisation', status=404)
        elif lot.mise:
            # Lot lié à une mise - vérifier via les lignes de mise
            has_line = MiseLigne.objects.filter(mise=lot.mise, lot_tech_source__cuvee__organization=org).exists()
            if not has_line:
                return HttpResponse('Lot commercial hors organisation', status=404)
        
        # Sources via mise (si disponible)
        sources = []
        trace_vendanges = []
        if lot.mise:
            sources = MiseLigne.objects.filter(mise=lot.mise).select_related('lot_tech_source')
            try:
                trace_vendanges = build_trace_for_mise(lot.mise_id)
            except Exception:
                trace_vendanges = []
        
        return render(request, 'produits/lot_com_detail.html', {
            'lot': lot,
            'sources': sources,
            'trace_vendanges': trace_vendanges,
            'page_title': f"Lot commercial {lot.code_lot}",
            'breadcrumb_items': [
                {'name': 'Produits', 'url': '/produits/cuvees/'},
                {'name': 'Lots commerciaux', 'url': '/produits/lots-commerciaux/'},
                {'name': lot.code_lot, 'url': None},
            ]
        })
