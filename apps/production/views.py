from __future__ import annotations
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from django.views.generic import ListView, DetailView, TemplateView, UpdateView
from django.db import transaction
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from decimal import Decimal
import uuid as _uuid
from django import forms
from django.http import HttpResponse
import csv

from apps.accounts.decorators import check_permission


class PermissionMixin:
    """
    Mixin pour verifier les permissions granulaires sur les vues de production.
    Definir permission_module et permission_action sur la classe.
    """
    permission_module = None  # 'vendanges', 'lots', 'stocks', etc.
    permission_action = 'view'  # 'view' ou 'edit'
    
    def dispatch(self, request, *args, **kwargs):
        if self.permission_module:
            membership = getattr(request, 'membership', None)
            if membership and not membership.has_permission(self.permission_module, self.permission_action):
                messages.error(request, f"Acces refuse. Vous n'avez pas la permission sur {self.permission_module}.")
                return redirect('auth:dashboard')
        return super().dispatch(request, *args, **kwargs)


from .models import VendangeReception, LotTechnique, Assemblage, AssemblageLigne, generate_lot_tech_code, generate_assemblage_code, MouvementLot, Operation, LotLineage
from apps.referentiels.models import Parcelle
from .forms import VendangeForm, VendangeLigneFormSet, AssemblageForm, AssemblageLigneFormSet, LotTechniqueForm, LotContainerForm, LotInterventionForm, LotMeasurementForm
from .service_vendange import affecter_cuvee
from .service_vinif import init_from_vendange, _recalc_lottech_snapshot
from apps.chai.services import lots as lot_services
from apps.viticulture.services_journal import log_parcelle_op
from apps.referentiels.models import Cuvee
from apps.viticulture.models import Lot as VitiLot, Warehouse
from apps.viticulture.models_extended import LotIntervention, LotMeasurement, LotContainer, LotDetail, LotDocument
from apps.stock.models import StockManager, StockVracMove
from apps.production.models import CostEntry, CostSnapshot
from apps.drm.models import DRMLine


@method_decorator(login_required, name='dispatch')
class VendangeMapView(View):
    template_name = 'production/vendange_map.html'

    def get(self, request):
        ctx = {
            'page_title': 'Carte parcelles & PLU',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': 'Carte', 'url': None},
            ],
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
class LotContainerCreateModal(View):
    template_name = 'production/modal_container_create.html'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        lots = VitiLot.objects.all()
        if org:
            lots = lots.filter(organization=org)
        lots = lots.order_by('-created_at')[:100]
        ctx = {
            'lots': lots,
            'choices': getattr(LotContainer, 'CONTAINER_CHOICES', []),
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None)
            lot_id = request.POST.get('lot_id')
            type_code = (request.POST.get('type') or '').strip()
            capacite_l = request.POST.get('capacite_l') or '0'
            occ_l = request.POST.get('volume_occupe_l') or '0'
            ident = (request.POST.get('identifiant') or '').strip()
            lot = VitiLot.objects.get(pk=lot_id)
            if org and getattr(lot, 'organization_id', None) and lot.organization_id != org.id:
                return HttpResponse('Lot hors organisation', status=400)
            LotContainer.objects.create(
                organization=org or lot.organization,
                lot=lot,
                type=type_code,
                capacite_l=Decimal(str(capacite_l)),
                volume_occupe_l=Decimal(str(occ_l)),
                identifiant=ident,
            )
            # Redirect appropriately (HTMX or normal)
            if request.headers.get('HX-Request') == 'true':
                resp = HttpResponse('')
                resp['HX-Redirect'] = '/production/contenants/'
                return resp
            else:
                return redirect('/production/contenants/')
        except Exception as e:
            return HttpResponse(str(e), status=400)


@method_decorator(login_required, name='dispatch')
class ContainerDetailView(View):
    template_name = 'production/container_detail.html'

    def get(self, request, pk):
        obj = get_object_or_404(LotContainer, pk=pk)
        # KPI simples pour ce contenant
        cap = getattr(obj, 'capacite_l', Decimal('0')) or Decimal('0')
        occ = getattr(obj, 'volume_occupe_l', Decimal('0')) or Decimal('0')
        try:
            pct = float((occ / cap * 100) if cap and cap > 0 else 0)
        except Exception:
            pct = 0.0
        # Données liées au lot
        lot = getattr(obj, 'lot', None)
        try:
            interventions = LotIntervention.objects.filter(lot=lot).order_by('-date')[:20]
        except Exception:
            interventions = []
        try:
            measures = LotMeasurement.objects.filter(lot=lot).order_by('-date')[:20]
        except Exception:
            measures = []
        try:
            documents = LotDocument.objects.filter(lot=lot).order_by('-uploaded_at')[:20]
        except Exception:
            documents = []
        ctx = {
            'container': obj,
            'lot': lot,
            'cap': cap,
            'occ': occ,
            'pct': pct,
            'interventions': interventions,
            'measures': measures,
            'documents': documents,
            'page_title': 'Fiche contenant',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Contenants', 'url': '/production/contenants/'},
                {'name': f"{obj.get_type_display()} {obj.identifiant or ''}", 'url': None},
            ],
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
class ContainerUpdateView(View):
    template_name = 'production/container_form.html'

    def get(self, request, pk):
        obj = get_object_or_404(LotContainer, pk=pk)
        org = getattr(request, 'current_org', None)
        form = LotContainerForm(instance=obj, organization=org)
        ctx = {
            'form': form,
            'page_title': 'Modifier le contenant',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Contenants', 'url': '/production/contenants/'},
                {'name': 'Modifier', 'url': None},
            ],
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        obj = get_object_or_404(LotContainer, pk=pk)
        org = getattr(request, 'current_org', None)
        form = LotContainerForm(request.POST, instance=obj, organization=org)
        if not form.is_valid():
            ctx = {
                'form': form,
                'page_title': 'Modifier le contenant',
                'breadcrumb_items': [
                    {'name': 'Production', 'url': '/production/'},
                    {'name': 'Contenants', 'url': '/production/contenants/'},
                    {'name': 'Modifier', 'url': None},
                ],
            }
            return render(request, self.template_name, ctx)
        obj = form.save(commit=False)
        try:
            if not obj.organization_id:
                if org:
                    obj.organization = org
                elif obj.lot and getattr(obj.lot, 'organization_id', None):
                    obj.organization_id = obj.lot.organization_id
        except Exception:
            pass
        obj.save()
        messages.success(request, 'Contenant mis à jour')
        try:
            url = reverse('production:container_detail', kwargs={'pk': obj.id})
        except Exception:
            url = f"/production/contenants/{obj.id}/"
        return redirect(url)


@method_decorator(login_required, name='dispatch')
class ServiceEntryModal(View):
    template_name = 'production/modal_service_entry.html'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        # LotTechnique list (filter by cuvee.organization)
        lots = LotTechnique.objects.all()
        if org:
            lots = lots.filter(cuvee__organization=org)
        lots = lots.order_by('-created_at')[:100]
        from apps.produits.models import Mise, MiseLigne
        mises = Mise.objects.all()
        if org:
            m_ids = (
                MiseLigne.objects.filter(lot_tech_source__cuvee__organization=org)
                .values_list('mise_id', flat=True)
                .distinct()
            )
            mises = mises.filter(id__in=m_ids)
        mises = mises.order_by('-date')[:100]
        selected = {
            'entity_type': (request.GET.get('entity_type') or '').strip(),
            'entity_id': (request.GET.get('entity_id') or '').strip(),
        }
        ctx = {
            'lots': lots,
            'mises': mises,
            'selected': selected,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None)
            if not org:
                return HttpResponse('Organisation inconnue', status=400)
            entity_type = (request.POST.get('entity_type') or '').strip()  # 'lottech' | 'mise'
            entity_id = (request.POST.get('entity_id') or '').strip()
            amount = Decimal(str(request.POST.get('amount_eur') or '0'))
            qty = Decimal(str(request.POST.get('qty') or '0'))  # heures ou unités
            service_label = (request.POST.get('service_label') or '').strip()
            notes = (request.POST.get('notes') or '').strip()
            if entity_type not in ['lottech', 'mise']:
                return HttpResponse('Type d\'entité invalide', status=400)
            # Validate entity exists and same org
            target_entity_id = None
            if entity_type == 'lottech':
                lottech = get_object_or_404(
                    LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
                    pk=entity_id,
                )
                # organization via cuvee
                lot_org = getattr(lottech.cuvee, 'organization_id', None)
                if lot_org and lot_org != org.id:
                    return HttpResponse('Lot hors organisation', status=400)
                target_entity_id = lottech.id
            else:
                from apps.produits.models import Mise, MiseLigne
                mise = get_object_or_404(Mise, pk=entity_id)
                has_line = MiseLigne.objects.filter(mise=mise, lot_tech_source__cuvee__organization=org).exists()
                outside = MiseLigne.objects.filter(mise=mise).exclude(lot_tech_source__cuvee__organization=org).exists()
                if not has_line or outside:
                    return HttpResponse('Mise hors organisation', status=400)
                target_entity_id = mise.id
            ce = CostEntry.objects.create(
                organization=org,
                entity_type=entity_type,
                entity_id=target_entity_id,
                nature='mo',
                qty=qty,
                amount_eur=amount,
                meta={'service': service_label, 'notes': notes},
                author=getattr(request, 'user', None),
            )
            # On success, close modal and maybe trigger UI update
            if request.headers.get('HX-Request') == 'true':
                resp = HttpResponse('')
                resp['HX-Trigger'] = 'toast:Service enregistré'
                return resp
            else:
                return redirect('/production/inventaire/')
        except Exception as e:
            return HttpResponse(str(e), status=400)


@method_decorator(login_required, name='dispatch')
class LotsContainersView(View):
    template_name = 'production/lots_contenants.html'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        qs = LotContainer.objects.all()
        if org:
            qs = qs.filter(organization=org)
        # Filtres simples
        t = (request.GET.get('type') or '').strip()
        q = (request.GET.get('q') or '').strip()
        if t:
            try:
                qs = qs.filter(type=t)
            except Exception:
                pass
        if q:
            try:
                qs = qs.filter(
                    Q(lot__code__icontains=q) |
                    Q(lot__cuvee__nom__icontains=q) |
                    Q(identifiant__icontains=q) |
                    Q(lot__warehouse__name__icontains=q)
                )
            except Exception:
                pass
        # KPI
        try:
            total_capacity = qs.aggregate(s=Sum('capacite_l')).get('s') or Decimal('0')
        except Exception:
            total_capacity = Decimal('0')
        try:
            total_occupied = qs.aggregate(s=Sum('volume_occupe_l')).get('s') or Decimal('0')
        except Exception:
            total_occupied = Decimal('0')
        kpi = {
            'count': qs.count(),
            'total_capacity_l': total_capacity,
            'total_occupied_l': total_occupied,
        }
        # Cartes
        containers = qs.select_related('lot', 'lot__cuvee', 'lot__warehouse').order_by('-created_at')[:200]
        cards = []
        for c in containers:
            try:
                cap = getattr(c, 'capacite_l', Decimal('0')) or Decimal('0')
                occ = getattr(c, 'volume_occupe_l', Decimal('0')) or Decimal('0')
                pct = float((occ / cap * 100) if cap and cap > 0 else 0)
            except Exception:
                cap, occ, pct = Decimal('0'), Decimal('0'), 0.0
            try:
                type_label = c.get_type_display() if hasattr(c, 'get_type_display') else getattr(c, 'type', '')
            except Exception:
                type_label = getattr(c, 'type', '')
            cards.append({
                'id': getattr(c, 'id', None),
                'type': type_label,
                'identifiant': getattr(c, 'identifiant', ''),
                'lot_code': getattr(getattr(c, 'lot', None), 'code', ''),
                'cuvee': getattr(getattr(c, 'lot', None), 'cuvee', None) and getattr(c.lot.cuvee, 'name', '') or '',
                'warehouse': getattr(getattr(getattr(c, 'lot', None), 'warehouse', None), 'name', ''),
                'capacity': cap,
                'occupied': occ,
                'pct': pct,
            })
        context = {
            'kpi': kpi,
            'cards': cards,
            'selected': {'type': t, 'q': q},
            'page_title': 'Contenants',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Contenants', 'url': None},
            ],
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class ContainerCreateView(View):
    template_name = 'production/container_form.html'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        form = LotContainerForm(organization=org)
        ctx = {
            'form': form,
            'page_title': 'Nouveau contenant',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Contenants', 'url': '/production/contenants/'},
                {'name': 'Nouveau', 'url': None},
            ],
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        org = getattr(request, 'current_org', None)
        form = LotContainerForm(request.POST, organization=org)
        if not form.is_valid():
            ctx = {
                'form': form,
                'page_title': 'Nouveau contenant',
                'breadcrumb_items': [
                    {'name': 'Production', 'url': '/production/'},
                    {'name': 'Contenants', 'url': '/production/contenants/'},
                    {'name': 'Nouveau', 'url': None},
                ],
            }
            return render(request, self.template_name, ctx)
        obj = form.save(commit=False)
        # Set organization from current_org or from selected lot
        try:
            if not obj.organization_id:
                if org:
                    obj.organization = org
                elif obj.lot and getattr(obj.lot, 'organization_id', None):
                    obj.organization_id = obj.lot.organization_id
        except Exception:
            pass
        obj.save()
        messages.success(request, 'Contenant créé avec succès')
        return redirect('/production/contenants/')

@method_decorator(login_required, name='dispatch')
class ParcellePrefillPartial(View):
    template_name = 'production/_vendange_parcelle_prefill.html'

    def post(self, request):
        pjson = (request.POST.get('props_json') or '').strip()
        geom_wkt = (request.POST.get('geom_wkt') or '').strip()
        geom_geojson = (request.POST.get('geom_geojson') or '').strip()
        surface_ha_client = (request.POST.get('surface_ha') or '').strip()

        data = {
            'section': '',
            'numero': '',
            'commune': '',
            'insee': '',
            'surface_ha': '',
            'geom_wkt': '',
            'source': 'cadastre' if pjson else 'dessin',
        }

        try:
            import json as _json
            props = _json.loads(pjson) if pjson else {}
        except Exception:
            props = {}

        # Normalize props → section/numero/commune/insee
        try:
            sec = (props.get('section') or props.get('SECTION') or props.get('sect') or '')
            data['section'] = str(sec).upper()[:3]
        except Exception:
            data['section'] = ''
        try:
            num = (props.get('numero') or props.get('NUMERO') or props.get('num') or '')
            data['numero'] = str(num).zfill(4)
        except Exception:
            data['numero'] = ''
        try:
            data['commune'] = props.get('commune') or props.get('COMMUNE') or props.get('nom_commune') or props.get('NOM_COMMUNE') or ''
        except Exception:
            data['commune'] = ''
        try:
            data['insee'] = props.get('insee') or props.get('INSEE') or props.get('code_insee') or props.get('CODE_INSEE') or props.get('code_commune') or props.get('CODE_COMMUNE') or ''
        except Exception:
            data['insee'] = ''

        # Geometry parsing and area computation (server-side when possible)
        geom_source = None
        if geom_wkt:
            geom_source = geom_wkt
        elif geom_geojson:
            geom_source = geom_geojson

        area_ha = None
        wkt_out = ''
        if geom_source:
            try:
                import json as _json
                from shapely.geometry import shape
                from shapely import wkt as _wkt
                from shapely.ops import transform as _transform
                try:
                    import pyproj
                    _to3857 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
                except Exception:
                    _to3857 = None

                geom_obj = None
                if geom_source.strip().startswith('{'):
                    gdict = _json.loads(geom_source)
                    geom_obj = shape(gdict)
                else:
                    geom_obj = _wkt.loads(geom_source)

                if geom_obj and not geom_obj.is_empty:
                    if _to3857 is not None:
                        g_m = _transform(_to3857, geom_obj)
                        area_m2 = g_m.area
                    else:
                        area_m2 = 0.0
                    area_ha = round((area_m2 or 0.0) / 10000.0, 4)
                    try:
                        wkt_out = geom_obj.wkt
                    except Exception:
                        wkt_out = ''
            except Exception:
                pass

        if area_ha is None:
            data['surface_ha'] = surface_ha_client or ''
        else:
            data['surface_ha'] = area_ha
        data['geom_wkt'] = wkt_out or (geom_wkt if geom_wkt and not geom_wkt.strip().startswith('{') else '')

        return render(request, self.template_name, {'data': data})


@method_decorator(login_required, name='dispatch')
class VendangeListView(PermissionMixin, ListView):
    model = VendangeReception
    template_name = 'production/vendanges_list.html'
    context_object_name = 'vendanges'
    permission_module = 'vendanges'
    permission_action = 'view'

    def get_queryset(self):
        try:
            org = getattr(self.request, 'current_org', None)
        except Exception:
            org = None
        qs = VendangeReception.objects.select_related('parcelle', 'cuvee').order_by('-date', '-created_at')
        if org:
            return qs.filter(organization=org)
        # Pas d'organisation courante → pas d'accès aux données
        return VendangeReception.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Vendanges'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Vendanges', 'url': None},
        ]
        # Filtres
        try:
            org = getattr(self.request, 'current_org', None)
            campagnes_qs = VendangeReception.objects.order_by('campagne').values_list('campagne', flat=True).distinct()
            campagnes = (campagnes_qs.filter(organization=org) if org else campagnes_qs.none())
        except Exception:
            campagnes = []
        ctx['campagnes'] = [c for c in campagnes if c]
        ctx['statut_choices'] = getattr(VendangeReception, 'STATUT_CHOICES', ())
        # Valeurs sélectionnées pour ré-affichage
        params = self.request.GET
        ctx['selected'] = {
            'q': (params.get('q') or '').strip(),
            'campagne__exact': (params.get('campagne') or '').strip(),
            'statut__exact': (params.get('statut') or '').strip(),
            'date_start': (params.get('date_start') or '').strip(),
            'date_end': (params.get('date_end') or '').strip(),
            'parcelle': (params.get('parcelle') or '').strip(),
            'cuvee': (params.get('cuvee') or '').strip(),
            'code': (params.get('code') or '').strip(),
            'poids_min': (params.get('poids_min') or '').strip(),
            'poids_max': (params.get('poids_max') or '').strip(),
            'sort': (params.get('sort') or 'date_desc').strip(),
        }
        return ctx


@method_decorator(login_required, name='dispatch')
class LotTechniqueCreateView(PermissionMixin, View):
    template_name = 'production/lot_tech_form.html'
    permission_module = 'lots'
    permission_action = 'edit'

    def get(self, request):
        # Wizard: étape unique côté serveur, UI à volets côté client
        # Proposer une sélection de vendanges récentes avec kg restant
        try:
            org = getattr(request, 'current_org', None)
        except Exception:
            org = None
        vqs = VendangeReception.objects.select_related('parcelle').order_by('-date', '-created_at')
        if org:
            vqs = vqs.filter(organization=org)
        vendanges = []
        for v in vqs[:100]:
            try:
                kg_rest = getattr(v, 'kg_restant', 0) or 0
            except Exception:
                kg_rest = 0
            vendanges.append({
                'id': v.id,
                'code': getattr(v, 'code', ''),
                'date': getattr(v, 'date', None),
                'parcelle': getattr(getattr(v, 'parcelle', None), 'nom', ''),
                'kg_restant': kg_rest,
                'cuvee': getattr(getattr(v, 'cuvee', None), 'name', ''),
            })
        return render(request, self.template_name, {
            'page_title': 'Nouveau lot technique',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots techniques', 'url': '/production/lots-techniques/'},
                {'name': 'Nouveau', 'url': None},
            ],
            'vendanges': vendanges,
        })

    @transaction.atomic
    def post(self, request):
        # Wizard submit: créer un lot à partir d'une vendange et le débiter
        vendange_id = (request.POST.get('vendange_id') or '').strip()
        contenant = (request.POST.get('contenant') or '').strip()
        rendement_base = request.POST.get('rendement_base') or '0.75'
        effic_pct = request.POST.get('effic_pct') or '100'
        volume_mesure_l = request.POST.get('volume_mesure_l') or None
        mode_encuvage = (request.POST.get('mode_encuvage') or '').strip() or None
        lot_type = (request.POST.get('lot_type') or '').strip() or None
        temperature_c = request.POST.get('temperature_c') or None
        notes = (request.POST.get('notes') or '').strip() or None
        poids_debite_kg_raw = request.POST.get('poids_debite_kg') or ''
        part_pct_raw = request.POST.get('part_pct') or ''

        errors = []
        if not vendange_id:
            errors.append("Sélectionnez une vendange à débiter")
        if not contenant:
            errors.append("Le contenant est requis")
        # Parse mesure
        from decimal import Decimal as _D
        vol_mes = None
        if volume_mesure_l is not None and str(volume_mesure_l).strip() != "":
            try:
                vol_mes = _D(str(volume_mesure_l))
                if vol_mes <= 0:
                    errors.append("Le volume mesuré doit être > 0")
            except Exception:
                errors.append("Volume mesuré invalide")
        # Parse temperature optionnelle
        if temperature_c is not None and str(temperature_c).strip() != "":
            try:
                _ = _D(str(temperature_c))
            except Exception:
                errors.append("Température invalide")
        # Parse rendement/efficacité si pas de volume mesuré
        if vol_mes is None:
            try:
                base = _D(str(rendement_base)); pct = _D(str(effic_pct))
                if base <= 0 or pct <= 0:
                    errors.append("Rendement de base (L/kg) et efficacité (%) doivent être > 0 si pas de volume mesuré")
            except Exception:
                errors.append("Rendement/efficacité invalides")
        # Fractionnement: kg débités ou part (%)
        kg_debite = None
        try:
            # Sécuriser: récupérer la vendange dans l'organisation courante
            org = getattr(request, 'current_org', None)
            v = get_object_or_404(VendangeReception.objects.filter(organization=org), pk=vendange_id)
            if str(poids_debite_kg_raw).strip() != '':
                kg_debite = _D(str(poids_debite_kg_raw))
            elif str(part_pct_raw).strip() != '':
                tot = _D(str(getattr(v, 'poids_kg', '0') or '0'))
                pctv = _D(str(part_pct_raw))
                kg_debite = (tot * pctv / _D('100'))
            if kg_debite is not None and kg_debite <= 0:
                errors.append("Les kg débités doivent être > 0")
        except Exception:
            errors.append("Valeur de kg débités/part (%) invalide")

        if errors:
            for e in errors:
                messages.error(request, e)
            return self.get(request)

        # Appeler le service d'encuvage qui débite la vendange et crée le lot
        try:
            new_lot_id = init_from_vendange(
                vendange_id=vendange_id,
                rendement_base_l_par_kg=rendement_base,
                effic_pct=effic_pct,
                contenant=contenant,
                volume_mesure_l=volume_mesure_l,
                user=request.user,
                poids_debite_kg=str(kg_debite) if kg_debite is not None else None,
                mode_encuvage=mode_encuvage,
                lot_type=lot_type,
                temperature_c=temperature_c,
                notes=notes,
                expected_org_id=getattr(v, 'organization_id', None),
            )
            messages.success(request, 'Lot technique créé depuis vendange')
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': new_lot_id})
            except Exception:
                url = f"/production/lots-techniques/{new_lot_id}/"
            return redirect(url)
        except Exception as e:
            messages.error(request, f"Erreur création lot: {e}")
            return self.get(request)

@method_decorator(login_required, name='dispatch')
class VendangeCreateView(PermissionMixin, View):
    template_name = 'production/vendange_form.html'
    permission_module = 'vendanges'
    permission_action = 'edit'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        initial = {}
        parcelle_id = (request.GET.get('parcelle') or '').strip()
        if parcelle_id:
            initial['parcelle'] = parcelle_id
        form = VendangeForm(initial=initial, organization=org)
        lignes_formset = VendangeLigneFormSet(prefix='lignes')
        # Passer l'organisation aux formulaires du formset
        for f in lignes_formset.forms:
            f.organization = org
            if org:
                from apps.referentiels.models import Cepage
                f.fields['cepage'].queryset = Cepage.objects.filter(organization=org).order_by('nom')
        
        # Récupérer les cépages de la parcelle si pré-sélectionnée
        encepagements = []
        if parcelle_id:
            try:
                from apps.referentiels.models import Encepagement
                encepagements = list(Encepagement.objects.filter(parcelle_id=parcelle_id).select_related('cepage'))
            except Exception:
                pass
        
        return render(request, self.template_name, {
            'form': form,
            'lignes_formset': lignes_formset,
            'encepagements': encepagements,
            'page_title': 'Nouvelle vendange',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': 'Nouvelle vendange', 'url': None},
            ]
        })

    @transaction.atomic
    def post(self, request):
        org = getattr(request, 'current_org', None)
        form = VendangeForm(request.POST, organization=org)
        lignes_formset = VendangeLigneFormSet(request.POST, prefix='lignes')
        
        if form.is_valid() and lignes_formset.is_valid():
            vendange: VendangeReception = form.save(commit=False)
            # Déterminer l'organisation
            try:
                if not org and vendange.parcelle_id:
                    org = getattr(vendange.parcelle, 'organization', None)
            except Exception:
                pass
            if org and not getattr(vendange, 'organization_id', None):
                vendange.organization = org
            vendange.save()
            
            # Sauvegarder les lignes
            lignes_formset.instance = vendange
            lignes_formset.save()
            
            # Journaliser la vendange
            try:
                p = getattr(vendange, 'parcelle', None)
                if p is not None:
                    try:
                        amount = None
                        poids = vendange.poids_total
                        if getattr(vendange, 'prix_raisin_eur_kg', None) and poids:
                            amount = (Decimal(str(vendange.prix_raisin_eur_kg)) * Decimal(str(poids)))
                    except Exception:
                        amount = None
                    log_parcelle_op(
                        org=org or getattr(p, 'organization', None),
                        parcelle=p,
                        op_code='vendange',
                        date=getattr(vendange, 'date', timezone.now().date()),
                        resume=(getattr(vendange, 'code', '') or 'Vendange')[:80],
                        surface_ha=getattr(p, 'surface', None),
                        cout_matiere_eur=(str(amount) if amount is not None else None),
                        source_obj=vendange,
                    )
            except Exception:
                pass
            
            messages.success(request, 'Vendange enregistrée')
            try:
                url = reverse('production:vendange_detail', kwargs={'pk': vendange.id})
            except Exception:
                url = f"/production/vendanges/{vendange.id}/"
            return redirect(url)
        
        # Formulaire invalide
        return render(request, self.template_name, {
            'form': form,
            'lignes_formset': lignes_formset,
            'page_title': 'Nouvelle vendange',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': 'Nouvelle vendange', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class PressurageWizardView(View):
    template_name = 'production/pressurage_wizard.html'

    class Form(forms.Form):
        volume_goutte_l = forms.DecimalField(min_value=Decimal('0.00'), max_digits=12, decimal_places=2, required=True, label='Vin de goutte (L)')
        volume_presse_l = forms.DecimalField(min_value=Decimal('0.00'), max_digits=12, decimal_places=2, required=True, label='Vin de presse (L)')
        notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=pk,
        )
        form = self.Form()
        return render(request, self.template_name, {
            'form': form,
            'lot': lot,
            'volume_disponible': lot.volume_net_calculated(),
            'page_title': f"Pressurage – {lot.code}",
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots & Élevage', 'url': '/production/lots-elevage/'},
                {'name': lot.code, 'url': f"/production/lots-techniques/{lot.id}/"},
                {'name': 'Pressurage', 'url': None},
            ],
        })

    @transaction.atomic
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').select_for_update().filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=pk,
        )
        form = self.Form(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'lot': lot, 'volume_disponible': lot.volume_net_calculated()})
        vg = form.cleaned_data['volume_goutte_l']
        vp = form.cleaned_data['volume_presse_l']
        notes = form.cleaned_data.get('notes') or ''
        dispo = lot.volume_net_calculated()
        if vg <= 0 and vp <= 0:
            form.add_error(None, 'Saisissez au moins un volume > 0')
            return render(request, self.template_name, {'form': form, 'lot': lot, 'volume_disponible': dispo})
        if (vg + vp) > dispo:
            form.add_error(None, 'Volumes supérieurs au disponible')
            return render(request, self.template_name, {'form': form, 'lot': lot, 'volume_disponible': dispo})
        # Créer les deux lots cibles
        camp = lot.campagne
        goutte = LotTechnique.objects.create(
            code=generate_lot_tech_code(camp),
            campagne=camp,
            contenant='Vin de goutte',
            volume_l=Decimal('0.00'),
            statut='en_cours',
            cuvee=lot.cuvee,
        ) if vg > 0 else None
        presse = LotTechnique.objects.create(
            code=generate_lot_tech_code(camp),
            campagne=camp,
            contenant='Vin de presse',
            volume_l=Decimal('0.00'),
            statut='en_cours',
            cuvee=lot.cuvee,
        ) if vp > 0 else None
        from .services_stock import move_vrac
        # Sorties source + entrées cibles
        total_out = (vg + vp)
        op_obj = None
        try:
            op_obj = Operation.objects.create(
                organization=getattr(getattr(lot, 'cuvee', None), 'organization', None),
                kind='pressurage',
                date=timezone.now(),
                meta={
                    'lot_source_id': str(lot.id),
                    'volume_goutte_l': str(vg),
                    'volume_presse_l': str(vp),
                    'notes': notes,
                }
            )
        except Exception:
            op_obj = None
        if vg > 0:
            MouvementLot.objects.create(lot=lot, type='ASSEMBLAGE_OUT', volume_l=vg, meta={'pressurage': True, 'fraction': 'goutte'})
            MouvementLot.objects.create(lot=goutte, type='ASSEMBLAGE_IN', volume_l=vg, meta={'pressurage': True, 'src': str(lot.id)})
            try:
                move_vrac(lottech=lot, delta_l=-vg, reason='PRESSURAGE_GOUTTE', user=request.user)
                move_vrac(lottech=goutte, delta_l=vg, reason='PRESSURAGE_GOUTTE', user=request.user)
            except Exception:
                pass
            goutte.volume_l = (goutte.volume_l or Decimal('0')) + vg
            goutte.save(update_fields=['volume_l'])
            try:
                if op_obj is not None and total_out > 0:
                    ratio = (vg / total_out) if total_out else None
                    LotLineage.objects.create(operation=op_obj, parent_lot=lot, child_lot=goutte, ratio=ratio)
            except Exception:
                pass
        if vp > 0:
            MouvementLot.objects.create(lot=lot, type='ASSEMBLAGE_OUT', volume_l=vp, meta={'pressurage': True, 'fraction': 'presse'})
            MouvementLot.objects.create(lot=presse, type='ASSEMBLAGE_IN', volume_l=vp, meta={'pressurage': True, 'src': str(lot.id)})
            try:
                move_vrac(lottech=lot, delta_l=-vp, reason='PRESSURAGE_PRESSE', user=request.user)
                move_vrac(lottech=presse, delta_l=vp, reason='PRESSURAGE_PRESSE', user=request.user)
            except Exception:
                pass
            presse.volume_l = (presse.volume_l or Decimal('0')) + vp
            presse.save(update_fields=['volume_l'])
            try:
                if op_obj is not None and total_out > 0:
                    ratio = (vp / total_out) if total_out else None
                    LotLineage.objects.create(operation=op_obj, parent_lot=lot, child_lot=presse, ratio=ratio)
            except Exception:
                pass
        # Décrémenter source
        lot.volume_l = (lot.volume_l or Decimal('0')) - (vg + vp)
        if lot.volume_l <= 0:
            lot.statut = 'epuise'
        lot.save(update_fields=['volume_l', 'statut'])
        # Journal intervention pressurage (viticulture)
        try:
            vlot = _ensure_viti_lot_for_lottech(lot)
            LotIntervention.objects.create(
                organization=vlot.organization,
                lot=vlot,
                type='pressurage',
                date=timezone.now().date(),
                notes=notes,
                volume_out_l=(vg + vp),
            )
        except Exception:
            pass
        messages.success(request, f"Pressurage enregistré: goutte {vg} L, presse {vp} L")
        try:
            url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
        except Exception:
            url = f"/production/lots-techniques/{lot.id}/"
        return redirect(url)


@login_required
def lot_vinif_add_measure(request, pk):
    org = getattr(request, 'current_org', None)
    lot = get_object_or_404(
        LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
        pk=pk,
    )
    try:
        vlot = _ensure_viti_lot_for_lottech(lot)
    except Exception:
        messages.error(request, "Impossible de lier un lot viticulture")
        return redirect('production:lot_tech_detail', pk=pk)

    form = LotMeasurementForm(request.POST)
    if form.is_valid():
        meas = form.save(commit=False)
        meas.organization = vlot.organization
        meas.lot = vlot
        meas.save()
        messages.success(request, "Mesure enregistrée")
    else:
        # Fallback ou message d'erreur
        msg = []
        for field, errs in form.errors.items():
            msg.append(f"{field}: {', '.join(errs)}")
        messages.error(request, "Erreur mesure: " + "; ".join(msg))
    
    return redirect('production:lot_tech_detail', pk=pk)


@login_required
def lot_vinif_add_intervention(request, pk):
    org = getattr(request, 'current_org', None)
    lot = get_object_or_404(
        LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
        pk=pk,
    )
    try:
        vlot = _ensure_viti_lot_for_lottech(lot)
    except Exception:
        messages.error(request, "Impossible de lier un lot viticulture")
        return redirect('production:lot_tech_detail', pk=pk)

    form = LotInterventionForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        # Construction des notes enrichies avec intrants
        notes_str = data.get('notes', '') or ''
        if data.get('produit_intrant'):
            notes_str += f" [Intrant: {data['produit_intrant']}"
            if data.get('quantite'):
                notes_str += f" {data['quantite']}"
                if data.get('unite'):
                    notes_str += f" {data['unite']}"
            notes_str += "]"
        
        LotIntervention.objects.create(
            organization=vlot.organization,
            lot=vlot,
            type=data['type'],
            date=data['date'],
            notes=notes_str.strip(),
        )
        messages.success(request, "Intervention enregistrée")
    else:
        msg = []
        for field, errs in form.errors.items():
            msg.append(f"{field}: {', '.join(errs)}")
        messages.error(request, "Erreur intervention: " + "; ".join(msg))
    
    return redirect('production:lot_tech_detail', pk=pk)


@method_decorator(login_required, name='dispatch')
class VendangeDetailView(DetailView):
    model = VendangeReception
    template_name = 'production/vendange_detail.html'
    context_object_name = 'vendange'

    def get_queryset(self):
        try:
            org = getattr(self.request, 'current_org', None)
        except Exception:
            org = None
        if org:
            return VendangeReception.objects.filter(organization=org)
        return VendangeReception.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lt = LotTechnique.objects.filter(source=self.object).first()
        ctx['lot_technique'] = lt
        # Proposer une liste de cuvées pour affectation rapide
        try:
            org = getattr(self.request, 'current_org', None)
            qs = Cuvee.objects.order_by('nom')
            if org:
                qs = qs.filter(organization=org)
            else:
                qs = qs.none()
            ctx['cuvees'] = qs[:50]
        except Exception:
            try:
                ctx['cuvees'] = Cuvee.objects.order_by('nom')[:50]
            except Exception:
                ctx['cuvees'] = []
        ctx['page_title'] = 'Fiche vendange'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Vendanges', 'url': '/production/vendanges/'},
            {'name': 'Fiche vendange', 'url': None},
        ]
        # Étape suivante
        try:
            kg_rest = getattr(self.object, 'kg_restant', Decimal('0')) or Decimal('0')
        except Exception:
            kg_rest = Decimal('0')
        if not getattr(self.object, 'cuvee_id', None):
            ctx['next_step'] = {'label': 'Affecter une cuvée', 'url': '#affectation-cuvee'}
        elif kg_rest and kg_rest > 0:
            ctx['next_step'] = {'label': 'Encuvage / Pressurage', 'url': f"/production/vendanges/{self.object.id}/encuvage/"}
        elif lt:
            ctx['next_step'] = {'label': 'Voir le lot technique', 'url': f"/production/lots-techniques/{lt.id}/"}
        return ctx


@method_decorator(login_required, name='dispatch')
class VendangeUpdateView(View):
    """Vue de modification d'une vendange existante avec lignes par cépage."""
    template_name = 'production/vendange_form.html'

    def get_object(self, pk):
        org = getattr(self.request, 'current_org', None)
        qs = VendangeReception.objects.all()
        if org:
            qs = qs.filter(organization=org)
        return get_object_or_404(qs, pk=pk)

    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        vendange = self.get_object(pk)
        form = VendangeForm(instance=vendange, organization=org)
        lignes_formset = VendangeLigneFormSet(instance=vendange, prefix='lignes')
        # Passer l'organisation aux formulaires du formset
        for f in lignes_formset.forms:
            if org:
                from apps.referentiels.models import Cepage
                f.fields['cepage'].queryset = Cepage.objects.filter(organization=org).order_by('nom')
        
        return render(request, self.template_name, {
            'form': form,
            'lignes_formset': lignes_formset,
            'vendange': vendange,
            'is_edit': True,
            'page_title': f'Modifier la vendange {vendange.code or ""}',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': f'Fiche {vendange.code or "vendange"}', 'url': f'/production/vendanges/{vendange.id}/'},
                {'name': 'Modifier', 'url': None},
            ]
        })

    @transaction.atomic
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        vendange = self.get_object(pk)
        form = VendangeForm(request.POST, instance=vendange, organization=org)
        lignes_formset = VendangeLigneFormSet(request.POST, instance=vendange, prefix='lignes')
        
        if form.is_valid() and lignes_formset.is_valid():
            vendange = form.save()
            lignes_formset.save()
            messages.success(request, 'Vendange modifiée')
            return redirect('production:vendange_detail', pk=vendange.pk)
        
        return render(request, self.template_name, {
            'form': form,
            'lignes_formset': lignes_formset,
            'vendange': vendange,
            'is_edit': True,
            'page_title': f'Modifier la vendange {vendange.code or ""}',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': f'Fiche {vendange.code or "vendange"}', 'url': f'/production/vendanges/{vendange.id}/'},
                {'name': 'Modifier', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class LotTechniqueListView(PermissionMixin, ListView):
    model = LotTechnique
    template_name = 'production/lots_tech_list.html'
    context_object_name = 'lots'
    paginate_by = 50
    permission_module = 'lots'
    permission_action = 'view'

    def get_queryset(self):
        from django.db.models import Q
        from decimal import Decimal, InvalidOperation

        qs = LotTechnique.objects.all()
        org = getattr(self.request, 'current_org', None)
        if org:
            qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))

        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(code__icontains=q) |
                Q(contenant__icontains=q) |
                Q(campagne__icontains=q)
            )

        campagne = (self.request.GET.get('campagne__exact') or '').strip()
        if campagne:
            qs = qs.filter(campagne=campagne)

        # Accept both 'statut__exact' (preferred) and 'status' (legacy alias)
        statut = (self.request.GET.get('statut__exact') or self.request.GET.get('status') or '').strip()
        scope = (self.request.GET.get('scope') or '').strip()
        if statut:
            qs = qs.filter(statut=statut)
        else:
            if scope == 'elevage':
                qs = qs.filter(statut__in=['en_cours', 'stabilise', 'VIN_ELEVAGE', 'VIN_STABILISE', 'VIN_POST_FA', 'VIN_EN_FML', 'VIN_POST_FML'])
            elif scope == 'pret_mise':
                qs = qs.filter(statut__in=['pret_mise', 'VIN_PRET_MISE'])
            elif scope == 'epuise':
                qs = qs.filter(statut='epuise')

        vmin = (self.request.GET.get('volume_min') or '').strip()
        if vmin:
            try:
                qs = qs.filter(volume_l__gte=Decimal(vmin))
            except InvalidOperation:
                pass

        vmax = (self.request.GET.get('volume_max') or '').strip()
        if vmax:
            try:
                qs = qs.filter(volume_l__lte=Decimal(vmax))
            except InvalidOperation:
                pass

        sort = (self.request.GET.get('sort') or '').strip()
        if sort == 'code':
            qs = qs.order_by('code')
        elif sort == 'volume_desc':
            qs = qs.order_by('-volume_l')
        elif sort == 'volume_asc':
            qs = qs.order_by('volume_l')
        elif sort == 'campagne':
            qs = qs.order_by('-campagne')
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        # Campagnes options (distinct)
        camps_qs = LotTechnique.objects.all()
        if org:
            camps_qs = camps_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        try:
            ctx['campagnes'] = list(camps_qs.values_list('campagne', flat=True).distinct())
        except Exception:
            ctx['campagnes'] = []
        ctx['statut_choices'] = getattr(LotTechnique, 'STATUT_CHOICES', ())
        params = self.request.GET
        ctx['selected'] = {
            'q': (params.get('q') or '').strip(),
            'campagne__exact': (params.get('campagne__exact') or '').strip(),
            'statut__exact': (params.get('statut__exact') or params.get('status') or '').strip(),
            'scope': (params.get('scope') or '').strip(),
            'volume_min': (params.get('volume_min') or '').strip(),
            'volume_max': (params.get('volume_max') or '').strip(),
            'sort': (params.get('sort') or '').strip(),
        }
        try:
            ctx['total_count'] = self.get_queryset().count()
        except Exception:
            ctx['total_count'] = 0
        return ctx


def _journal_filtered_queryset(request):
    params = request.POST if request.method == 'POST' else request.GET
    qs = (StockVracMove.objects
          .select_related('lot', 'lot__cuvee', 'src_warehouse', 'dst_warehouse', 'user'))
    org = getattr(request, 'current_org', None)
    if org:
        qs = qs.filter(organization=org)
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(lot__code__icontains=q) |
            Q(lot__cuvee__nom__icontains=q) |
            Q(src_warehouse__name__icontains=q) |
            Q(dst_warehouse__name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(notes__icontains=q)
        )
    mtype = (params.get('type') or '').strip()
    if mtype:
        qs = qs.filter(move_type=mtype)
    cuvee = (params.get('cuvee') or '').strip()
    if cuvee:
        try:
            _ = _uuid.UUID(cuvee)
            qs = qs.filter(lot__cuvee_id=cuvee)
        except Exception:
            qs = qs.filter(lot__cuvee__nom__icontains=cuvee)
    lot_code = (params.get('lot') or '').strip()
    if lot_code:
        qs = qs.filter(lot__code__icontains=lot_code)
    start = (params.get('start') or '').strip()
    end = (params.get('end') or '').strip()
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    return qs.order_by('-created_at', '-id')


@method_decorator(login_required, name='dispatch')
class JournalVracTableView(ListView):
    template_name = 'production/_journal_vrac_table.html'
    model = StockVracMove
    context_object_name = 'moves'
    paginate_by = 25

    def get_queryset(self):
        return _journal_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs:
                qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except Exception:
            ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx


def _analyses_filtered_queryset(request):
    params = request.POST if request.method == 'POST' else request.GET
    qs = (LotMeasurement.objects
          .select_related('lot', 'lot__cuvee'))
    org = getattr(request, 'current_org', None)
    if org:
        qs = qs.filter(organization=org)
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(lot__code__icontains=q) |
            Q(lot__cuvee__nom__icontains=q) |
            Q(notes__icontains=q)
        )
    typ = (params.get('type') or '').strip()
    if typ:
        qs = qs.filter(type=typ)
    cuvee = (params.get('cuvee') or '').strip()
    if cuvee:
        try:
            _ = _uuid.UUID(cuvee)
            qs = qs.filter(lot__cuvee_id=cuvee)
        except Exception:
            qs = qs.filter(lot__cuvee__nom__icontains=cuvee)
    lot_code = (params.get('lot') or '').strip()
    if lot_code:
        qs = qs.filter(lot__code__icontains=lot_code)
    start = (params.get('start') or '').strip()
    end = (params.get('end') or '').strip()
    if start:
        qs = qs.filter(date__date__gte=start)
    if end:
        qs = qs.filter(date__date__lte=end)
    # Valeurs min/max optionnelles
    vmin = (params.get('vmin') or '').strip()
    vmax = (params.get('vmax') or '').strip()
    try:
        if vmin:
            qs = qs.filter(value__gte=Decimal(vmin))
    except Exception:
        pass
    try:
        if vmax:
            qs = qs.filter(value__lte=Decimal(vmax))
    except Exception:
        pass
    sort = (params.get('sort') or 'date_desc').strip()
    if sort == 'date_asc':
        qs = qs.order_by('date', 'id')
    elif sort == 'type':
        qs = qs.order_by('type', '-date')
    else:
        qs = qs.order_by('-date', '-id')
    return qs


@method_decorator(login_required, name='dispatch')
class AnalysesHomeView(View):
    template_name = 'production/analyses_home.html'

    def get(self, request):
        ctx = {
            'page_title': 'Lots & Élevage - Analyses',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots & Élevage', 'url': '/production/lots-elevage/'},
                {'name': 'Analyses', 'url': None},
            ],
            'meas_choices': getattr(LotMeasurement, 'MEAS_CHOICES', ()),
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
class LotsContainersView(View):
    template_name = 'production/lots_contenants.html'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        qs = LotContainer.objects.select_related('lot', 'lot__cuvee', 'lot__warehouse').all()
        if org:
            qs = qs.filter(lot__organization=org)
        typ = (request.GET.get('type') or '').strip()
        q = (request.GET.get('q') or '').strip()
        if typ:
            qs = qs.filter(type=typ)
        if q:
            qs = qs.filter(Q(lot__code__icontains=q) | Q(lot__cuvee__nom__icontains=q) | Q(identifiant__icontains=q))
        qs = qs.order_by('type', 'identifiant')
        containers = list(qs)
        cards = []
        from decimal import Decimal
        total_cap = Decimal('0'); total_occ = Decimal('0')
        for c in containers:
            cap = Decimal(str(getattr(c, 'capacite_l', 0) or 0))
            occ = Decimal(str(getattr(c, 'volume_occupe_l', 0) or 0))
            pct = Decimal('0')
            if cap and cap > 0:
                try:
                    pct = (occ / cap) * Decimal('100')
                except Exception:
                    pct = Decimal('0')
            total_cap += cap; total_occ += occ
            cards.append({
                'id': c.id,
                'type': c.get_type_display(),
                'type_code': c.type,
                'identifiant': c.identifiant or '',
                'lot_code': getattr(c.lot, 'code', ''),
                'cuvee': getattr(getattr(c.lot, 'cuvee', None), 'name', ''),
                'warehouse': getattr(getattr(c.lot, 'warehouse', None), 'name', ''),
                'capacity': cap,
                'occupied': occ,
                'pct': pct,
            })
        kpi = {
            'count': len(cards),
            'total_capacity_l': total_cap,
            'total_occupied_l': total_occ,
        }
        ctx = {
            'page_title': 'Contenants (cuves, fûts, barriques)',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots & Élevage', 'url': '/production/lots-elevage/'},
                {'name': 'Contenants', 'url': None},
            ],
            'cards': cards,
            'kpi': kpi,
            'selected': {'type': typ, 'q': q},
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
class AnalysesTableView(ListView):
    template_name = 'production/_analyses_table.html'
    model = LotMeasurement
    context_object_name = 'measures'
    paginate_by = 25

    def get_queryset(self):
        return _analyses_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs:
                qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except Exception:
            ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx


@method_decorator(login_required, name='dispatch')
class LotTechniqueDetailView(DetailView):
    model = LotTechnique
    template_name = 'production/lot_tech_detail_v2.html'
    context_object_name = 'lot'

    def get_queryset(self):
        try:
            org = getattr(self.request, 'current_org', None)
        except Exception:
            org = None
        qs = LotTechnique.objects.select_related('cuvee', 'source')
        if org:
            return qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        return LotTechnique.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f'Lot technique {self.object.code}'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Lots techniques', 'url': '/production/lots-techniques/'},
            {'name': self.object.code, 'url': None},
        ]
        # Mouvements & volume net calculé
        try:
            mvs = list(self.object.mouvements.order_by('-date', '-id'))
            ctx['mouvements'] = mvs
            vol = Decimal('0')
            for mv in reversed(mvs):  # oldest first for clarity, but summation commutative
                if mv.type in ('ENTREE_INITIALE', 'ASSEMBLAGE_IN', 'TRANSFERT_IN'):
                    vol += mv.volume_l
                elif mv.type in ('PERTE', 'SOUTIRAGE', 'ASSEMBLAGE_OUT', 'TRANSFERT_OUT', 'MISE_OUT'):
                    vol -= mv.volume_l
            ctx['volume_net_calc'] = vol
            # Volume initial (première entrée initiale) & pertes cumulées
            init_mv = None
            for mv in reversed(mvs):
                if mv.type == 'ENTREE_INITIALE':
                    init_mv = mv
                    break
            ctx['volume_initial_l'] = (init_mv.volume_l if init_mv else getattr(self.object, 'volume_l', Decimal('0')))
            pertes = Decimal('0')
            for mv in mvs:
                if mv.type == 'PERTE':
                    try:
                        pertes += mv.volume_l
                    except Exception:
                        pass
            ctx['pertes_cumulees_l'] = pertes
            # Origine & rendement
            try:
                kg_used = None
                if init_mv and isinstance(getattr(init_mv, 'meta', {}), dict):
                    raw = init_mv.meta.get('poids_debite_kg')
                    if raw:
                        from decimal import Decimal as _D
                        kg_used = _D(str(raw))
                rendement = None
                if kg_used and kg_used > 0 and ctx['volume_initial_l']:
                    rendement = (ctx['volume_initial_l'] / kg_used).quantize(Decimal('0.01'))
                ctx['origin'] = {
                    'vendange': self.object.source,
                    'parcelle': getattr(self.object.source, 'parcelle', None) if self.object.source_id else None,
                    'created_at': getattr(self.object, 'created_at', None),
                    'rendement_l_kg': rendement,
                }
            except Exception:
                ctx['origin'] = {
                    'vendange': self.object.source,
                    'parcelle': getattr(self.object.source, 'parcelle', None) if self.object.source_id else None,
                    'created_at': getattr(self.object, 'created_at', None),
                    'rendement_l_kg': None,
                }
        except Exception:
            ctx['mouvements'] = []
            ctx['volume_net_calc'] = self.object.volume_l
        # Filiation (parents/enfants via LotLineage)
        try:
            parents = list(LotLineage.objects.select_related('operation', 'parent_lot').filter(child_lot=self.object).order_by('-operation__date', '-operation__id'))
        except Exception:
            parents = []
        try:
            enfants = list(LotLineage.objects.select_related('operation', 'child_lot').filter(parent_lot=self.object).order_by('-operation__date', '-operation__id'))
        except Exception:
            enfants = []
        ctx['lineage_parents'] = parents
        ctx['lineage_children'] = enfants
        # Coûts: snapshot, journal, pertes totales
        try:
            snap = None
            try:
                snap = CostSnapshot.objects.filter(entity_type='lottech', entity_id=self.object.id).first()
            except Exception:
                snap = None
            from django.db.models import Sum
            journal = CostEntry.objects.filter(entity_type='lottech', entity_id=self.object.id).order_by('-date', '-id')
            pertes_eur = (journal.filter(nature='vrac_loss').aggregate(s=Sum('amount_eur'))['s'] or 0)
            ctx['cost_snapshot'] = snap
            ctx['cost_entries'] = journal
            ctx['pertes_eur'] = pertes_eur
        except Exception:
            pass
        # Vinification timeline (read-only lists, avoid auto-create vlot)
        try:
            vlot = None
            if getattr(self.object, 'external_lot_id', None):
                vlot = VitiLot.objects.get(id=self.object.external_lot_id)
            if vlot:
                ctx['vinif_interventions'] = list(vlot.interventions.order_by('-date')[:10])
                ctx['vinif_measurements'] = list(vlot.measurements.order_by('-date')[:10])
                ctx['vlot'] = vlot
                # Détails emplacement/ouillage et contenants
                try:
                    ctx['lot_detail'] = LotDetail.objects.filter(lot=vlot).first()
                except Exception:
                    ctx['lot_detail'] = None
                try:
                    ctx['lot_containers'] = list(LotContainer.objects.filter(lot=vlot).order_by('type', 'identifiant'))
                except Exception:
                    ctx['lot_containers'] = []
                # Documents
                try:
                    ctx['lot_documents'] = list(LotDocument.objects.filter(lot=vlot).order_by('-uploaded_at'))
                except Exception:
                    ctx['lot_documents'] = []
            else:
                ctx['vinif_interventions'] = []
                ctx['vinif_measurements'] = []
                ctx['vlot'] = None
                ctx['lot_detail'] = None
                ctx['lot_containers'] = []
                ctx['lot_documents'] = []
        except Exception:
            ctx['vinif_interventions'] = []
            ctx['vinif_measurements'] = []
            ctx['vlot'] = None
            ctx['lot_detail'] = None
            ctx['lot_containers'] = []
            ctx['lot_documents'] = []
        try:
            last_ts = None
            try:
                for mv in ctx.get('mouvements', []):
                    if mv.type in ('SOUTIRAGE', 'TRANSFERT_IN', 'TRANSFERT_OUT'):
                        last_ts = mv.date
                        break
            except Exception:
                last_ts = None
            ctx['last_transfer_soutirage'] = last_ts
            latest_d = None
            dens_init = None
            abv = None
            temp_mean = None
            ph_last = None
            if 'vinif_measurements' in ctx and getattr(self.object, 'external_lot_id', None):
                try:
                    vm = VitiLot.objects.get(id=self.object.external_lot_id).measurements
                    dens_last_row = vm.filter(type='densite').order_by('-date').values('value').first()
                    latest_d = dens_last_row['value'] if dens_last_row else None
                    dens_first_row = vm.filter(type='densite').order_by('date').values('value').first()
                    dens_init = dens_first_row['value'] if dens_first_row else None
                    # Température moyenne (10 dernières)
                    temps = list(vm.filter(type='temperature').order_by('-date').values_list('value', flat=True)[:10])
                    if temps:
                        from decimal import Decimal as _D
                        s = sum([_D(str(t)) for t in temps])
                        temp_mean = (s / _D(str(len(temps)))).quantize(Decimal('0.1'))
                    # pH dernier
                    ph_row = vm.filter(type='ph').order_by('-date').values('value').first()
                    ph_last = ph_row['value'] if ph_row else None
                except Exception:
                    latest_d = None
                    dens_init = None
                    temp_mean = None
                    ph_last = None
                try:
                    abv = VitiLot.objects.only('alcohol_pct').get(id=self.object.external_lot_id).alcohol_pct
                except Exception:
                    abv = None
            ctx['latest_densite'] = latest_d
            ctx['initial_densite'] = dens_init
            ctx['abv_pct'] = abv
            ctx['temp_mean'] = temp_mean
            ctx['ph_last'] = ph_last
            etat = None
            try:
                ivs = ctx.get('vinif_interventions') or []
                if ivs:
                    t = getattr(ivs[0], 'type', '')
                    if t == 'filtration':
                        etat = 'Filtré'
                    elif t in ('soutirage', 'ouillage'):
                        etat = 'En élevage'
                    elif t in ('remontage', 'pigeage'):
                        etat = 'En fermentation'
                    elif t == 'fml':
                        etat = 'En FML'
            except Exception:
                etat = None
            if not etat:
                try:
                    etat = self.object.get_statut_display()
                except Exception:
                    etat = None
            ctx['etat_technique'] = etat
            # Alertes basiques: SO2 libre faible, pH haut, ouillage en retard
            alerts = {}
            try:
                ld = ctx.get('lot_detail')
                if ld and getattr(ld, 'so2_libre_mg_l', None) is not None:
                    try:
                        alerts['so2_libre_low'] = (ld.so2_libre_mg_l < Decimal('15'))
                    except Exception:
                        alerts['so2_libre_low'] = False
                if ld and getattr(ld, 'ph', None) is not None:
                    try:
                        alerts['ph_high'] = (ld.ph > Decimal('3.60'))
                    except Exception:
                        alerts['ph_high'] = False
                # Ouillage
                from django.utils import timezone as _tz
                alerts['ouillage_overdue'] = False
                alerts['ouillage_days'] = None
                if ld and getattr(ld, 'ouillage_dernier_controle', None):
                    days = (_tz.now().date() - ld.ouillage_dernier_controle).days
                    alerts['ouillage_days'] = days
                    limit = ld.ouillage_periodicite_jours or 10
                    if days is not None and limit is not None and days > limit:
                        alerts['ouillage_overdue'] = True
            except Exception:
                pass
            ctx['param_alerts'] = alerts
        except Exception:
            ctx['last_transfer_soutirage'] = None
            ctx['latest_densite'] = None
            ctx['abv_pct'] = None
            ctx['etat_technique'] = None
            ctx['initial_densite'] = None
            ctx['temp_mean'] = None
            ctx['ph_last'] = None
            ctx['param_alerts'] = {}
        # Lots disponibles pour transfert (autres lots)
        try:
            ctx['other_lots'] = (
                LotTechnique.objects.exclude(id=self.object.id)
                .only('id', 'code', 'campagne')
                .order_by('-created_at')[:50]
            )
        except Exception:
            ctx['other_lots'] = []
        # Cuvées disponibles pour affectation
        try:
            org = getattr(self.request, 'current_org', None)
            from apps.referentiels.models import Cuvee as RefCuvee
            ctx['cuvees'] = RefCuvee.objects.filter(organization=org).order_by('nom')
        except Exception:
            ctx['cuvees'] = []
        # Étape suivante
        try:
            vol_net = ctx.get('volume_net_calc') or getattr(self.object, 'volume_l', Decimal('0')) or Decimal('0')
        except Exception:
            vol_net = Decimal('0')
        if getattr(self.object, 'statut', '') == 'pret_mise':
            url = f"/production/mises/nouveau/?step=1&cuvee={self.object.cuvee_id}" if getattr(self.object, 'cuvee_id', None) else "/production/mises/nouveau/?step=1"
            ctx['next_step'] = {'label': 'Planifier une mise', 'url': url}
        elif vol_net and vol_net > 0:
            ctx['next_step'] = {'label': "Marquer 'Prêt mise'", 'url': '#form-pret-mise'}
        return ctx


@method_decorator(login_required, name='dispatch')
class LotTechAffecterCuveeView(View):
    """Affecte une cuvée à un lot technique (POST)."""
    def post(self, request, pk):
        cuvee_id = request.POST.get('cuvee_id')
        if not cuvee_id:
            messages.error(request, "Aucune cuvée sélectionnée")
            return redirect('production:lot_tech_detail', pk=pk)
        try:
            org = getattr(request, 'current_org', None)
            lot = get_object_or_404(LotTechnique, pk=pk)
            # Vérifier que la cuvée appartient à l'organisation
            from apps.referentiels.models import Cuvee as RefCuvee
            cuvee = get_object_or_404(RefCuvee.objects.filter(organization=org), pk=cuvee_id)
            lot.cuvee = cuvee
            lot.save(update_fields=['cuvee'])
            messages.success(request, f"Cuvée '{cuvee.nom}' affectée au lot {lot.code}")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'affectation: {e}")
        return redirect('production:lot_tech_detail', pk=pk)


@method_decorator(login_required, name='dispatch')
class AssemblageCreateView(View):
    template_name = 'production/assemblage_form.html'

    def get(self, request):
        form = AssemblageForm(initial={'campagne': f"{timezone.now().year}-{timezone.now().year+1}"})
        formset = AssemblageLigneFormSet()
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'page_title': 'Nouvel assemblage',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Assemblages', 'url': None},
            ]
        })

    @transaction.atomic
    def post(self, request):
        form = AssemblageForm(request.POST)
        formset = AssemblageLigneFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            assemblage: Assemblage = form.save(commit=False)
            if not assemblage.code:
                assemblage.code = generate_assemblage_code(form.cleaned_data['campagne'])
            assemblage.save()
            total = Decimal('0')
            weights = []  # list of (volume_l, cmp, org)
            for f in formset:
                if not f.cleaned_data or f.cleaned_data.get('DELETE'):
                    continue
                ligne: AssemblageLigne = f.save(commit=False)
                ligne.assemblage = assemblage
                ligne.save()
                # décrémenter les sources
                lt = ligne.lot_source
                lt.volume_l = (lt.volume_l or Decimal('0')) - ligne.volume_l
                if lt.volume_l <= 0:
                    lt.statut = 'epuise'
                lt.save()
                # Mouvement OUT (assemblage)
                try:
                    MouvementLot.objects.create(
                        lot=lt,
                        type='ASSEMBLAGE_OUT',
                        volume_l=ligne.volume_l,
                        meta={'assemblage_id': str(assemblage.id)},
                        author=request.user,
                    )
                except Exception:
                    pass
                # CMP source pour pondération
                try:
                    snap_s = CostSnapshot.objects.filter(entity_type='lottech', entity_id=lt.id).first()
                    cmp_s = getattr(snap_s, 'cmp_vrac_eur_l', Decimal('0')) or Decimal('0')
                    org_s = getattr(snap_s, 'organization', None)
                except Exception:
                    cmp_s = Decimal('0'); org_s = None
                weights.append((Decimal(ligne.volume_l), Decimal(cmp_s), org_s))
                total += Decimal(ligne.volume_l)
            # Créer le lot technique résultant consultable
            result_code = generate_lot_tech_code(form.cleaned_data['campagne'])
            result_lt = LotTechnique.objects.create(
                code=result_code,
                campagne=form.cleaned_data['campagne'],
                contenant='Assemblage',
                volume_l=total,
                statut='en_cours',
            )
            assemblage.result_lot = result_lt
            assemblage.save(update_fields=['result_lot'])
            # Mouvement IN (assemblage) sur le lot cible
            try:
                MouvementLot.objects.create(
                    lot=result_lt,
                    type='ASSEMBLAGE_IN',
                    volume_l=total,
                    meta={'assemblage_id': str(assemblage.id)},
                    author=request.user,
                )
            except Exception:
                pass
            # CMP pondéré pour le lot cible
            try:
                vol_sum = sum((v for v, _c, _o in weights), Decimal('0'))
                if vol_sum and vol_sum > 0:
                    num = sum((v * c for v, c, _o in weights), Decimal('0'))
                    cmp_c = (num / vol_sum).quantize(Decimal('0.0001'))
                    # Choisir organisation: cuvée de result ou première org source connue
                    org_c = getattr(result_lt.cuvee, 'organization', None)
                    if not org_c:
                        for _v, _c, o in weights:
                            if o:
                                org_c = o; break
                    if org_c:
                        snap_c = CostSnapshot.objects.filter(organization=org_c, entity_type='lottech', entity_id=result_lt.id).first()
                        if not snap_c:
                            CostSnapshot.objects.create(organization=org_c, entity_type='lottech', entity_id=result_lt.id, cmp_vrac_eur_l=cmp_c)
                        else:
                            snap_c.cmp_vrac_eur_l = cmp_c
                            snap_c.save(update_fields=['cmp_vrac_eur_l', 'updated_at'])
            except Exception:
                pass
            messages.success(request, f'Assemblage {assemblage.code} créé → {result_lt.code} ({total:.2f} L)')
            try:
                url = reverse('production:assemblage_detail', kwargs={'pk': assemblage.id})
            except Exception:
                try:
                    url = reverse('production:assemblage_detail', kwargs={'pk': assemblage.id})
                except Exception:
                    url = f"/production/assemblages/{assemblage.id}/"
            return redirect(url)
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'page_title': 'Nouvel assemblage',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/parcelles/'},
                {'name': 'Assemblages', 'url': None},
                {'name': 'Nouvel assemblage', 'url': None},
            ]
        })

@method_decorator(login_required, name='dispatch')
class AssemblageDetailView(DetailView):
    model = Assemblage
    template_name = 'production/assemblage_detail.html'
    context_object_name = 'assemblage'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['lignes'] = self.object.lignes.select_related('lot_source').all()
        ctx['result_lot'] = self.object.result_lot
        ctx['page_title'] = f'Assemblage {self.object.code}'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Assemblages', 'url': None},
            {'name': self.object.code, 'url': None},
        ]
        return ctx


@method_decorator(login_required, name='dispatch')
class LotsElevageHomeView(View):
    template_name = 'production/lots_elevage_home.html'

    def get(self, request):
        # Stats par statut
        stats_by_status = []
        statut_labels = dict(LotTechnique.STATUT_CHOICES)
        org = getattr(request, 'current_org', None)
        for code, label in LotTechnique.STATUT_CHOICES:
            qs = LotTechnique.objects.filter(statut=code)
            if org:
                qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
            count = qs.count()
            total = qs.aggregate(total=Sum('volume_l'))['total'] or Decimal('0')
            stats_by_status.append({
                'code': code,
                'label': label,
                'count': count,
                'volume_l': total,
            })

        # Récents lots
        recent_qs = LotTechnique.objects.select_related('cuvee')
        if org:
            recent_qs = recent_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        recent_lots = recent_qs.order_by('-created_at')[:10]

        # Campagnes récentes (top 6)
        camps_qs = LotTechnique.objects.all()
        if org:
            camps_qs = camps_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        campagnes = list(
            camps_qs.values_list('campagne', flat=True).distinct()
        )
        campagnes = sorted([c for c in campagnes if c], reverse=True)[:6]
        campagnes_summary = []
        for camp in campagnes:
            qs = LotTechnique.objects.filter(campagne=camp)
            if org:
                qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
            campagnes_summary.append({
                'campagne': camp,
                'count': qs.count(),
                'volume_l': qs.aggregate(total=Sum('volume_l'))['total'] or Decimal('0'),
            })

        # KPIs
        actifs_qs = LotTechnique.objects.filter(statut__in=['en_cours', 'stabilise'])
        if org:
            actifs_qs = actifs_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        actifs = actifs_qs.count()
        vol_qs = LotTechnique.objects.filter(statut__in=['en_cours', 'stabilise', 'pret_mise'])
        if org:
            vol_qs = vol_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        vol_actif_pret = (
            vol_qs.aggregate(total=Sum('volume_l'))['total'] or Decimal('0')
        )
        pret_qs = LotTechnique.objects.filter(statut='pret_mise')
        if org:
            pret_qs = pret_qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
        kpi = {
            'lots_actifs': actifs,
            'volume_hl': (vol_actif_pret / Decimal('100')).quantize(Decimal('0.01')),
            'pret_mise': pret_qs.count(),
            'alertes': 0,
        }

        ctx = {
            'page_title': 'Lots & Élevage',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots & Élevage', 'url': None},
            ],
            'stats_by_status': stats_by_status,
            'recent_lots': recent_lots,
            'campagnes_summary': campagnes_summary,
            'statut_labels': statut_labels,
            'kpi': kpi,
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
class LotsElevageList(ListView):
    template_name = 'production/_lots_table.html'
    model = LotTechnique
    paginate_by = 25

    def get_queryset(self):
        return _lots_filtered_queryset(self.request)


def _lots_filtered_queryset(request):
    qs = (
        LotTechnique.objects.select_related('cuvee')
        .only('id', 'code', 'statut', 'volume_l', 'campagne', 'contenant', 'cuvee__nom', 'created_at')
    )
    org = getattr(request, 'current_org', None)
    if org:
        qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
    params = request.POST if request.method == 'POST' else request.GET
    status = (params.get('status') or '').strip()
    cuvee = (params.get('cuvee') or '').strip()
    mill = (params.get('millesime') or '').strip()
    q = (params.get('q') or '').strip()

    if status:
        qs = qs.filter(statut=status)
    if cuvee:
        qs = qs.filter(cuvee_id=cuvee)
    if mill:
        # Accept either exact campagne string or year contained
        if '-' in mill:
            qs = qs.filter(campagne=mill)
        else:
            qs = qs.filter(campagne__icontains=mill)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(cuvee__nom__icontains=q))

    return qs.order_by('-created_at', '-id')


# ==========================
# HELPERS DE RECHERCHE
# ==========================

def _parcelle_filtered_queryset(request):
    org = getattr(request, 'current_org', None)
    from apps.referentiels.models import Parcelle
    qs = Parcelle.objects.filter(organization=org) if org else Parcelle.objects.none()
    
    params = request.POST if request.method == 'POST' else request.GET
    
    # Quick search
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | 
            Q(commune__icontains=q) |
            Q(appellation__icontains=q)
        )
        
    # Advanced filters
    nom = (params.get('nom') or '').strip()
    if nom:
        qs = qs.filter(nom__icontains=nom)
        
    commune = (params.get('commune') or '').strip()
    if commune:
        qs = qs.filter(commune__icontains=commune)
        
    appellation = (params.get('appellation') or '').strip()
    if appellation:
        qs = qs.filter(appellation__icontains=appellation)
        
    surface_min = (params.get('surface_min') or '').strip()
    if surface_min:
        try:
            qs = qs.filter(surface__gte=Decimal(surface_min))
        except: pass
        
    surface_max = (params.get('surface_max') or '').strip()
    if surface_max:
        try:
            qs = qs.filter(surface__lte=Decimal(surface_max))
        except: pass

    # Sort
    sort = (params.get('sort') or 'nom').strip()
    if sort == 'nom_desc':
        qs = qs.order_by('-nom')
    elif sort == 'surface_desc':
        qs = qs.order_by('-surface')
    elif sort == 'surface_asc':
        qs = qs.order_by('surface')
    else:
        qs = qs.order_by('nom')
        
    return qs

def _lot_filtered_queryset(request):
    org = getattr(request, 'current_org', None)
    qs = LotTechnique.objects.select_related('cuvee')
    if org:
        qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
    else:
        qs = LotTechnique.objects.none()
        
    params = request.POST if request.method == 'POST' else request.GET
    
    # Quick search
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(code__icontains=q) | 
            Q(cuvee__nom__icontains=q) |
            Q(contenant__icontains=q)
        )
        
    # Advanced filters
    code = (params.get('code') or '').strip()
    if code:
        qs = qs.filter(code__icontains=code)
        
    cuvee = (params.get('cuvee') or '').strip()
    if cuvee:
        qs = qs.filter(cuvee__nom__icontains=cuvee)
        
    statut = (params.get('statut') or '').strip()
    if statut:
        qs = qs.filter(statut=statut)
        
    campagne = (params.get('campagne') or '').strip()
    if campagne:
        qs = qs.filter(campagne=campagne)
        
    contenant = (params.get('contenant') or '').strip()
    if contenant:
        qs = qs.filter(contenant__icontains=contenant)

    vol_min = (params.get('volume_min') or '').strip()
    if vol_min:
        try:
            qs = qs.filter(volume_l__gte=Decimal(vol_min))
        except: pass
        
    vol_max = (params.get('volume_max') or '').strip()
    if vol_max:
        try:
            qs = qs.filter(volume_l__lte=Decimal(vol_max))
        except: pass

    # Sort
    sort = (params.get('sort') or 'created_desc').strip()
    if sort == 'created_asc':
        qs = qs.order_by('created_at')
    elif sort == 'code':
        qs = qs.order_by('code')
    elif sort == 'vol_desc':
        qs = qs.order_by('-volume_l')
    elif sort == 'vol_asc':
        qs = qs.order_by('volume_l')
    else:
        qs = qs.order_by('-created_at')
        
    return qs

def _encuvage_filtered_queryset(request):
    # Filtres pour les lots au stade encuvage/presse
    org = getattr(request, 'current_org', None)
    # On considère comme encuvage les lots avec statut MOUT_* ou VIN_EN_FA
    qs = LotTechnique.objects.select_related('cuvee', 'source').filter(
        statut__in=['MOUT_ENCUVE', 'MOUT_PRESSE', 'MOUT_DEBOURBE', 'VIN_EN_FA']
    )
    if org:
        qs = qs.filter(Q(cuvee__organization=org) | Q(source__organization=org))
    else:
        qs = LotTechnique.objects.none()

    params = request.POST if request.method == 'POST' else request.GET
    
    # Same filters as LotTechnique mostly
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(cuvee__nom__icontains=q))
        
    # ... (reuse logic or simplify)
    code = (params.get('code') or '').strip()
    if code:
        qs = qs.filter(code__icontains=code)
        
    cuvee = (params.get('cuvee') or '').strip()
    if cuvee:
        qs = qs.filter(cuvee__nom__icontains=cuvee)
        
    statut = (params.get('statut') or '').strip()
    if statut:
        qs = qs.filter(statut=statut)
        
    campagne = (params.get('campagne') or '').strip()
    if campagne:
        qs = qs.filter(campagne=campagne)

    sort = (params.get('sort') or 'created_desc').strip()
    if sort == 'created_asc':
        qs = qs.order_by('created_at')
    else:
        qs = qs.order_by('-created_at')
        
    return qs


# ==========================
# VUES DE LISTE AVANCÉES
# ==========================

@method_decorator(login_required, name='dispatch')
class ParcelleListView(TemplateView):
    template_name = 'production/parcelles_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Parcelles'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Parcelles', 'url': None},
        ]
        # Pré-remplissage filtres
        ctx['selected'] = self.request.GET
        # Parcelles pour les deux vues (table + cartes)
        qs = _parcelle_filtered_queryset(self.request)
        ctx['parcelles'] = qs
        ctx['total_count'] = qs.count()
        return ctx

@method_decorator(login_required, name='dispatch')
class ParcelleTableView(ListView):
    template_name = 'production/_parcelles_table.html'
    context_object_name = 'parcelles'
    paginate_by = 25

    def get_queryset(self):
        return _parcelle_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs: qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except: ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx


@method_decorator(login_required, name='dispatch')
class ParcellesInterventionsView(TemplateView):
    """
    Vue "Interventions" des parcelles - affichage en cartes visuelles
    avec panneau d'actions latéral pour les opérations viticoles.
    Complète la vue BDD (tableau) existante.
    """
    template_name = 'production/parcelles_interventions.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Parcelles - Interventions'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Parcelles', 'url': '/production/parcelles/'},
            {'name': 'Interventions', 'url': None},
        ]
        
        org = getattr(self.request, 'current_org', None)
        from apps.referentiels.models import Parcelle
        
        # Récupérer toutes les parcelles de l'organisation
        parcelles = Parcelle.objects.filter(organization=org).order_by('nom') if org else Parcelle.objects.none()
        
        # Enrichir avec les dernières interventions
        parcelles_data = []
        for p in parcelles:
            # Récupérer la dernière opération viticole
            from apps.viticulture.models_ops import ParcelleOperation
            last_op = ParcelleOperation.objects.filter(
                parcelle=p
            ).order_by('-date').first()
            
            parcelles_data.append({
                'parcelle': p,
                'last_operation': last_op,
                'certifications': p.certifications,  # Utilise la propriété qui filtre les tags valides
            })
        
        ctx['parcelles_data'] = parcelles_data
        ctx['total_count'] = len(parcelles_data)
        ctx['selected'] = self.request.GET
        
        # Liste des types d'opérations pour le panneau
        ctx['operation_types'] = [
            {'code': 'traitement', 'label': 'Traitement phyto', 'icon': 'bi-droplet', 'color': 'success'},
            {'code': 'taille', 'label': 'Taille', 'icon': 'bi-scissors', 'color': 'success'},
            {'code': 'travail_sol', 'label': 'Travail du sol', 'icon': 'bi-tools', 'color': 'success'},
            {'code': 'palissage', 'label': 'Palissage / Liage', 'icon': 'bi-diagram-3', 'color': 'success'},
            {'code': 'effeuillage', 'label': 'Effeuillage', 'icon': 'bi-leaf', 'color': 'success'},
            {'code': 'fertilisation', 'label': 'Fertilisation', 'icon': 'bi-droplet', 'color': 'success'},
            {'code': 'irrigation', 'label': 'Irrigation', 'icon': 'bi-water', 'color': 'success'},
            {'code': 'autre', 'label': 'Autre intervention', 'icon': 'bi-tools', 'color': 'secondary'},
        ]
        
        return ctx


@method_decorator(login_required, name='dispatch')
class ParcellesCardsDataView(View):
    """
    API JSON pour récupérer les données des parcelles en mode cartes.
    Utilisé pour le chargement HTMX/AJAX.
    """
    def get(self, request):
        from django.http import JsonResponse
        from apps.referentiels.models import Parcelle
        
        org = getattr(request, 'current_org', None)
        parcelles = Parcelle.objects.filter(organization=org).order_by('nom') if org else []
        
        data = []
        for p in parcelles:
            from apps.viticulture.models_ops import ParcelleOperation
            last_op = ParcelleOperation.objects.filter(parcelle=p).order_by('-date').first()
            
            data.append({
                'id': p.pk,
                'nom': p.nom,
                'surface': float(p.surface),
                'commune': p.commune or '',
                'appellation': p.appellation or '',
                'cepages': [c.nom for c in p.cepages.all()],
                'certifications': p.certifications,  # Utilise la propriété qui filtre les tags valides
                'last_operation': {
                    'type': last_op.operation_type if last_op else None,
                    'date': last_op.date.isoformat() if last_op else None,
                    'label': last_op.get_operation_type_display() if last_op else None,
                } if last_op else None,
                'url': f'/production/parcelles/{p.pk}/',
            })
        
        return JsonResponse({'parcelles': data, 'total': len(data)})


@method_decorator(login_required, name='dispatch')
class LotTechniqueListView(TemplateView):
    template_name = 'production/lots_techniques_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Lots Techniques'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Lots Techniques', 'url': None},
        ]
        ctx['statut_choices'] = LotTechnique.STATUT_CHOICES
        
        # Campagnes
        org = getattr(self.request, 'current_org', None)
        camps = LotTechnique.objects.filter(cuvee__organization=org).values_list('campagne', flat=True).distinct().order_by('-campagne') if org else []
        ctx['campagnes'] = [c for c in camps if c]
        
        ctx['selected'] = self.request.GET
        qs = _lot_filtered_queryset(self.request)
        ctx['total_count'] = qs.count()
        return ctx

@method_decorator(login_required, name='dispatch')
class LotTechniqueTableView(ListView):
    template_name = 'production/_lots_techniques_table.html'
    context_object_name = 'lots'
    paginate_by = 25

    def get_queryset(self):
        return _lot_filtered_queryset(self.request)

    def get(self, request, *args, **kwargs):
        # Support JSON response for by-cuvee view
        if request.GET.get('format') == 'json':
            from django.http import JsonResponse
            qs = self.get_queryset()
            lots_data = []
            for lot in qs:
                lots_data.append({
                    'id': str(lot.id),
                    'code': lot.code,
                    'cuvee_id': str(lot.cuvee.id) if lot.cuvee else None,
                    'cuvee_nom': lot.cuvee.nom if lot.cuvee else None,
                    'volume_l': float(lot.volume_l) if lot.volume_l else 0,
                    'statut': lot.statut,
                    'contenant': lot.contenant,
                    'campagne': lot.campagne,
                })
            return JsonResponse({'lots': lots_data})
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs: qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except: ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx


@method_decorator(login_required, name='dispatch')
class EncuvageListView(TemplateView):
    template_name = 'production/encuvages_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Encuvages & Pressurages'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Encuvages', 'url': None},
        ]
        # Status spécifiques encuvage
        ctx['statut_choices'] = [
            ("MOUT_ENCUVE", "Moût encuvé"),
            ("MOUT_PRESSE", "Moût de presse"),
            ("MOUT_DEBOURBE", "Moût débourbé"),
            ("VIN_EN_FA", "Vin en FA"),
        ]
        ctx['selected'] = self.request.GET
        qs = _encuvage_filtered_queryset(self.request)
        ctx['total_count'] = qs.count()
        return ctx

@method_decorator(login_required, name='dispatch')
class EncuvageTableView(ListView):
    template_name = 'production/_encuvages_table.html'
    context_object_name = 'lots'
    paginate_by = 25

    def get_queryset(self):
        return _encuvage_filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs: qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except: ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx



def _vendanges_filtered_queryset(request):
    params = request.GET
    qs = VendangeReception.objects.select_related('parcelle', 'cuvee')
    
    org = getattr(request, 'current_org', None)
    if org:
        qs = qs.filter(organization=org)
    else:
        return VendangeReception.objects.none()
        
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(parcelle__nom__icontains=q) |
            Q(cuvee__nom__icontains=q) |
            Q(notes__icontains=q)
        )
        
    campagne = (params.get('campagne') or '').strip()
    if campagne:
        qs = qs.filter(campagne=campagne)
        
    statut = (params.get('statut') or '').strip()
    if statut:
        qs = qs.filter(statut=statut)
        
    date_start = (params.get('date_start') or '').strip()
    if date_start:
        qs = qs.filter(date__gte=date_start)
        
    date_end = (params.get('date_end') or '').strip()
    if date_end:
        qs = qs.filter(date__lte=date_end)
        
    sort = (params.get('sort') or 'date_desc').strip()
    if sort == 'date_asc':
        qs = qs.order_by('date', 'created_at')
    elif sort == 'poids_desc':
        qs = qs.order_by('-poids_kg')
    else:
        qs = qs.order_by('-date', '-created_at')
        
    return qs


@method_decorator(login_required, name='dispatch')
class VendangesTableView(ListView):
    template_name = 'production/_vendanges_table.html'
    model = VendangeReception
    context_object_name = 'vendanges'
    paginate_by = 25

    def get_queryset(self):
        return _vendanges_filtered_queryset(self.request)

    def get(self, request, *args, **kwargs):
        # Support JSON format for Kanban view
        if request.GET.get('format') == 'json':
            from django.http import JsonResponse
            qs = self.get_queryset()
            vendanges_data = []
            for v in qs:
                vendanges_data.append({
                    'id': str(v.id),
                    'code': v.code or '',
                    'date': v.date.strftime('%d/%m/%Y') if v.date else '',
                    'campagne': v.campagne or '',
                    'parcelle_nom': v.parcelle.nom if v.parcelle else '',
                    'cuvee_nom': v.cuvee.nom if v.cuvee else '',
                    'poids_kg': float(v.poids_kg) if v.poids_kg else 0,
                    'statut': v.statut or 'brouillon',
                })
            return JsonResponse({'vendanges': vendanges_data})
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Build querystring without 'page' for pagination links
        try:
            qs = self.request.GET.copy()
            if 'page' in qs:
                qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except Exception:
            ctx['querystring'] = ''
        ctx['total_count'] = self.get_queryset().count()
        return ctx


def _ensure_viti_lot_for_lottech(lottech: LotTechnique) -> VitiLot:
    """Garantit un Lot (viticulture) lié à un LotTechnique via external_lot_id.
    Crée le Lot si nécessaire en copiant code/cuvée/volume, et en choisissant un entrepôt.
    """
    if lottech.external_lot_id:
        try:
            return VitiLot.objects.get(id=lottech.external_lot_id)
        except VitiLot.DoesNotExist:
            pass
    org = lottech.cuvee.organization if lottech.cuvee_id else None
    wh = Warehouse.objects.filter(organization=org).order_by('name').first()
    if not wh:
        wh = Warehouse.objects.create(organization=org, name='Principal')
    vlot = VitiLot.objects.create(
        organization=org,
        code=lottech.code,
        cuvee=lottech.cuvee,
        warehouse=wh,
        volume_l=lottech.volume_l,
        status='elevage',
    )
    lottech.external_lot_id = vlot.id
    lottech.save(update_fields=['external_lot_id'])
    return vlot

@method_decorator(login_required, name='dispatch')
class VendangeAffecterCuveeView(View):
    """Affecte une cuvée à une vendange (POST)."""
    def post(self, request, pk):
        cuvee_id = request.POST.get('cuvee_id')
        if not cuvee_id:
            messages.error(request, "Aucune cuvée sélectionnée")
            return redirect('production:vendange_detail', pk=pk)
        try:
            org = getattr(request, 'current_org', None)
            # Guard: ensure both vendange and cuvée are within org
            vendange = get_object_or_404(VendangeReception.objects.filter(organization=org), pk=pk)
            cuvee = get_object_or_404(Cuvee.objects.filter(organization=org), pk=cuvee_id)
            affecter_cuvee(vendange.id, cuvee.id)
            messages.success(request, "Cuvée affectée à la vendange")
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
        try:
            url = reverse('production:vendange_detail', kwargs={'pk': pk})
        except Exception:
            try:
                url = reverse('production:vendange_detail', kwargs={'pk': pk})
            except Exception:
                url = f"/production/vendanges/{pk}/"
        return redirect(url)


@method_decorator(login_required, name='dispatch')
class EncuvageWizardView(View):
    template_name = 'production/encuvage_wizard.html'

    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        vendange = get_object_or_404(VendangeReception.objects.filter(organization=org), pk=pk)
        if not vendange.cuvee_id:
            messages.warning(request, "Affectez d'abord une cuvée à cette vendange")
        # Contenants suggérés (historique lots techniques de l'organisation)
        containers = []
        contenants = []
        try:
            org = getattr(vendange, 'organization', None) or (vendange.cuvee and vendange.cuvee.organization)
            if org:
                containers = list(
                    LotTechnique.objects.filter(cuvee__organization=org)
                    .exclude(contenant="")
                    .values_list('contenant', flat=True)
                    .order_by()
                    .distinct()[:50]
                )
                # Essayer d'exposer aussi les Contenant (modèle dédié) avec capacité libre
                try:
                    from .models_containers import Contenant as _Contenant
                except Exception:
                    _Contenant = None
                if _Contenant is not None:
                    try:
                        qs = _Contenant.objects.filter(organization=org, is_active=True).order_by('code')
                        for c in qs[:200]:
                            try:
                                free = c.free_capacity_l()
                            except Exception:
                                free = Decimal('0')
                            try:
                                cap = c.capacite_utile_effective_l
                            except Exception:
                                cap = getattr(c, 'capacite_utile_l', None) or getattr(c, 'capacite_l', None)
                            try:
                                type_label = c.get_type_display()
                            except Exception:
                                type_label = getattr(c, 'type', '')
                            try:
                                statut_label = c.get_statut_display()
                            except Exception:
                                statut_label = getattr(c, 'statut', '')
                            contenants.append({
                                'code': c.code,
                                'label': getattr(c, 'label', '') or '',
                                'type': type_label,
                                'cap': cap,
                                'free': free,
                                'statut': statut_label,
                            })
                    except Exception:
                        contenants = []
        except Exception:
            containers = []
        ctx = {
            'vendange': vendange,
            'page_title': 'Encuvage / Pressurage',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Vendanges', 'url': '/production/vendanges/'},
                {'name': 'Encuvage', 'url': None},
            ],
            'defaults': {
                'rendement_base': str((vendange.volume_mesure_l and '') or '0.75'),
                'effic_pct': str(vendange.rendement_pct or '100'),
                'poids_total_kg': str(getattr(vendange, 'poids_kg', '') or ''),
                'kg_restant': str(getattr(vendange, 'kg_restant', '') or ''),
                'kg_debites_cumules': str(getattr(vendange, 'kg_debites_cumules', '') or ''),
                'prix_raisin_eur_kg': str(getattr(vendange, 'prix_raisin_eur_kg', '') or ''),
            }
            ,
            'containers': containers,
            'contenants': contenants,
        }
        # Cuvées disponibles pour affectation
        try:
            from apps.referentiels.models import Cuvee as RefCuvee
            ctx['cuvees'] = RefCuvee.objects.filter(organization=org).order_by('nom')
        except Exception:
            ctx['cuvees'] = []
        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        vendange = get_object_or_404(VendangeReception.objects.filter(organization=org), pk=pk)
        contenant = (request.POST.get('contenant') or '').strip()
        rendement_base = request.POST.get('rendement_base') or '0.75'
        effic_pct = request.POST.get('effic_pct') or '100'
        volume_mesure_l = request.POST.get('volume_mesure_l') or None
        # Nouveaux paramètres ergonomie/métier
        mode_encuvage = (request.POST.get('mode_encuvage') or '').strip() or None
        lot_type = (request.POST.get('lot_type') or '').strip() or None
        temperature_c = request.POST.get('temperature_c') or None
        notes = (request.POST.get('notes') or '').strip() or None
        poids_debite_kg_raw = request.POST.get('poids_debite_kg') or ''
        part_pct_raw = request.POST.get('part_pct') or ''
        # Validations basiques (sans formulaire dédié)
        errors = []
        if not vendange.cuvee_id:
            errors.append("La vendange doit être affectée à une cuvée")
        if not contenant:
            errors.append("Le contenant est requis")
        try:
            vol_mes = None
            if volume_mesure_l is not None and str(volume_mesure_l).strip() != "":
                vol_mes = Decimal(str(volume_mesure_l))
                if vol_mes <= 0:
                    errors.append("Le volume mesuré doit être > 0")
        except Exception:
            errors.append("Volume mesuré invalide")
        # Température optionnelle
        try:
            if temperature_c is not None and str(temperature_c).strip() != "":
                _ = Decimal(str(temperature_c))
        except Exception:
            errors.append("Température invalide")
        try:
            base = Decimal(str(rendement_base))
            pct = Decimal(str(effic_pct))
            if (vol_mes is None) and (base <= 0 or pct <= 0):
                errors.append("Rendement de base (L/kg) et efficacité (%) doivent être > 0 si pas de volume mesuré")
        except Exception:
            if vol_mes is None:
                errors.append("Rendement/efficacité invalides")
        # Fractionnement: kg débités ou part (%)
        kg_debite = None
        try:
            if str(poids_debite_kg_raw).strip() != '':
                kg_debite = Decimal(str(poids_debite_kg_raw))
            elif str(part_pct_raw).strip() != '':
                tot = Decimal(str(getattr(vendange, 'poids_kg', '0') or '0'))
                pctv = Decimal(str(part_pct_raw))
                kg_debite = (tot * pctv / Decimal('100'))
            if kg_debite is not None:
                if kg_debite <= 0:
                    errors.append("Les kg débités doivent être > 0")
                else:
                    try:
                        totkg = Decimal(str(getattr(vendange, 'poids_kg', '0') or '0'))
                        if totkg and kg_debite > totkg:
                            errors.append("Les kg débités dépassent le poids de la vendange")
                    except Exception:
                        pass
        except Exception:
            errors.append("Valeur de kg débités/part (%) invalide")

        # Poids vendange > 0 si pas de volume mesuré et pas de kg_debite
        try:
            if vol_mes is None and kg_debite is None:
                if vendange.poids_kg is None or Decimal(vendange.poids_kg) <= 0:
                    errors.append("La vendange doit avoir un poids > 0 kg")
        except Exception:
            errors.append("Poids de vendange invalide")
        if errors:
            for e in errors:
                messages.error(request, e)
            return self.get(request, pk)
        # Alerte de cohérence si efficacité mesurée suspecte (>100% ou <50%)
        try:
            base = Decimal(str(rendement_base))
            default_used = getattr(vendange, 'kg_restant', None)
            kg_used = Decimal(str(kg_debite)) if kg_debite is not None else Decimal(str(default_used if default_used is not None else (getattr(vendange, 'poids_kg', '0') or '0')))
            if vol_mes is not None and kg_used > 0 and base > 0:
                effic_calc = (vol_mes / (kg_used * base)) * Decimal('100')
                if effic_calc > Decimal('100') or effic_calc < Decimal('50'):
                    messages.warning(request, f"Efficacité mesurée suspecte: {effic_calc.quantize(Decimal('0.1'))}%")
        except Exception:
            pass
        try:
            # Convertir volume_mesure_l → hL@20 pour le service (si fourni)
            vol_hl20 = None
            if volume_mesure_l is not None and str(volume_mesure_l).strip() != "":
                try:
                    vol_hl20 = (Decimal(str(volume_mesure_l)) / Decimal('100')).quantize(Decimal('0.001'))
                except Exception:
                    vol_hl20 = None
            lot, _op = lot_services.create_from_encuvage(
                harvest=vendange,
                container=contenant,
                volume_hl20=vol_hl20,
                poids_debite_kg=kg_debite,
                mode_encuvage=mode_encuvage,
                lot_type=lot_type,
                temperature_c=(Decimal(str(temperature_c)) if temperature_c else None),
                notes=notes,
                user=request.user,
            )
            messages.success(request, 'Lot technique initial créé')
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        except Exception as e:
            messages.error(request, f"Erreur encuvage: {e}")
            return self.get(request, pk)


@method_decorator(login_required, name='dispatch')
class SoutirageWizardView(View):
    template_name = 'production/soutirage_wizard.html'

    class Form(forms.Form):
        volume_lies_pertes_l = forms.DecimalField(min_value=Decimal('0.00'), max_digits=12, decimal_places=2, required=True, label='Volume Lies / Pertes (L)')
        destination_contenant = forms.CharField(required=False, label="Nouveau contenant (si transfert)", widget=forms.TextInput(attrs={'placeholder': 'Laisser vide si maintien en cuve'}))
        type_soutirage = forms.ChoiceField(choices=[('aere', 'Aéré'), ('protege', 'Protégé (Inertage)')], required=False, label="Type de soutirage")
        notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=pk,
        )
        form = self.Form()
        return render(request, self.template_name, {
            'form': form,
            'lot': lot,
            'page_title': f"Soutirage – {lot.code}",
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Lots & Élevage', 'url': '/production/lots-elevage/'},
                {'name': lot.code, 'url': f"/production/lots-techniques/{lot.id}/"},
                {'name': 'Soutirage', 'url': None},
            ],
        })

    @transaction.atomic
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').select_for_update().filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=pk,
        )
        form = self.Form(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'lot': lot})

        pertes = form.cleaned_data['volume_lies_pertes_l']
        dest_cont = (form.cleaned_data.get('destination_contenant') or '').strip()
        mode = form.cleaned_data.get('type_soutirage')
        notes = form.cleaned_data.get('notes') or ''

        if pertes > lot.volume_l:
            form.add_error('volume_lies_pertes_l', 'Le volume de lies dépasse le volume total du lot')
            return render(request, self.template_name, {'form': form, 'lot': lot})

        vlot = _ensure_viti_lot_for_lottech(lot)

        # Cas 1 : Transfert vers un nouveau contenant ("Mise au propre")
        if dest_cont:
            vol_clair = lot.volume_l - pertes
            if vol_clair < 0:
                vol_clair = Decimal('0')
            
            # Création du nouveau lot "Clair"
            # Code incrémental ou suffixe ? Standard: Nouveau code séquence
            new_code = generate_lot_tech_code(lot.campagne)
            new_lot = LotTechnique.objects.create(
                code=new_code,
                campagne=lot.campagne,
                contenant=dest_cont,
                volume_l=vol_clair,
                statut=lot.statut, # Garde le même statut (ex: Elevage)
                cuvee=lot.cuvee,
                source=lot.source
            )
            
            # Traçabilité (Filiation)
            op = Operation.objects.create(
                organization=org,
                kind='soutirage',
                date=timezone.now(),
                meta={'type': mode, 'notes': notes}
            )
            LotLineage.objects.create(operation=op, parent_lot=lot, child_lot=new_lot, ratio=1)

            # Mouvements LotTechnique
            # Sortie totale du lot père (Clair + Lies)
            MouvementLot.objects.create(lot=lot, type='TRANSFERT_OUT', volume_l=vol_clair, meta={'dst': str(new_lot.id), 'reason': 'vin_clair'})
            if pertes > 0:
                MouvementLot.objects.create(lot=lot, type='PERTE', volume_l=pertes, meta={'reason': 'lies_soutirage'})
            
            # Entrée lot fils
            MouvementLot.objects.create(lot=new_lot, type='TRANSFERT_IN', volume_l=vol_clair, meta={'src': str(lot.id), 'reason': 'vin_clair'})

            # Stock Vrac (Physique)
            # Sortie du père
            StockManager.move_vrac(lot=vlot, qty_l=vol_clair, move_type='sortie', user=request.user, ref_type='soutirage_transfert', ref_id=new_lot.id, notes=f"Vers {dest_cont}")
            if pertes > 0:
                StockManager.move_vrac(lot=vlot, qty_l=pertes, move_type='sortie', user=request.user, ref_type='soutirage_perte', ref_id=lot.id, notes="Lies")
            
            # Mise à jour père (vide)
            lot.volume_l = Decimal('0')
            lot.statut = 'epuise' # Le père est vide
            lot.save()

            # Intervention Viticulture
            LotIntervention.objects.create(
                organization=vlot.organization,
                lot=vlot,
                type='soutirage',
                date=timezone.now().date(),
                notes=f"Soutirage {mode} vers {new_lot.code} ({dest_cont}). Lies: {pertes}L. {notes}",
                volume_out_l=lot.volume_l # Tout est sorti
            )

            # Redirection vers le nouveau lot
            messages.success(request, f"Soutirage effectué : {vol_clair}L vers {new_lot.code}, {pertes}L de lies retirées.")
            return redirect('production:lot_tech_detail', pk=new_lot.id)

        else:
            # Cas 2 : Soutirage "sur place" (élimination lies sans changement contenant, ou simple update volume)
            # On ne fait que retirer les lies du volume courant
            if pertes > 0:
                MouvementLot.objects.create(lot=lot, type='PERTE', volume_l=pertes, meta={'reason': 'lies_soutirage'})
                StockManager.move_vrac(lot=vlot, qty_l=pertes, move_type='sortie', user=request.user, ref_type='soutirage_perte', ref_id=lot.id, notes="Elimination lies")
                
                lot.volume_l -= pertes
                lot.save()
                vlot.volume_l -= pertes
                vlot.save()
                
                # Coût des pertes
                try:
                    snap = CostSnapshot.objects.filter(organization=org, entity_type='lottech', entity_id=lot.id).first()
                    cmp_vrac = getattr(snap, 'cmp_vrac_eur_l', Decimal('0')) or Decimal('0')
                    amount = (cmp_vrac * pertes).quantize(Decimal('0.0001'))
                    CostEntry.objects.create(
                        organization=org,
                        entity_type='lottech',
                        entity_id=lot.id,
                        nature='vrac_loss',
                        qty=pertes,
                        amount_eur=amount,
                        meta={'action': 'soutirage_lies'},
                        author=request.user,
                    )
                except Exception:
                    pass

            LotIntervention.objects.create(
                organization=vlot.organization,
                lot=vlot,
                type='soutirage',
                date=timezone.now().date(),
                notes=f"Soutirage sur place ({mode}). Elimination {pertes}L lies. {notes}",
                volume_out_l=pertes
            )

            messages.success(request, f"Soutirage enregistré : {pertes}L de lies éliminées.")
            return redirect('production:lot_tech_detail', pk=lot.id)


@method_decorator(login_required, name='dispatch')
class JournalVracListView(ListView):
    template_name = 'production/journal_vrac.html'
    model = StockVracMove
    paginate_by = 25

    def get_queryset(self):
        qs = (StockVracMove.objects
              .select_related('lot', 'lot__cuvee', 'src_warehouse', 'dst_warehouse', 'user'))
        org = getattr(self.request, 'current_org', None)
        if org:
            qs = qs.filter(organization=org)
        # Filtres
        mtype = (self.request.GET.get('type') or '').strip()
        cuvee = (self.request.GET.get('cuvee') or '').strip()
        lot_code = (self.request.GET.get('lot') or '').strip()
        start = (self.request.GET.get('start') or '').strip()
        end = (self.request.GET.get('end') or '').strip()

        if mtype:
            qs = qs.filter(move_type=mtype)
        if cuvee:
            # Accept UUID ID or name icontains
            try:
                _ = _uuid.UUID(cuvee)
                qs = qs.filter(lot__cuvee_id=cuvee)
            except Exception:
                qs = qs.filter(lot__cuvee__nom__icontains=cuvee)
        if lot_code:
            qs = qs.filter(lot__code__icontains=lot_code)
        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        return qs.order_by('-created_at', '-id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Journal des mouvements (vrac)'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Lots & Élevage', 'url': '/production/lots-elevage/'},
            {'name': 'Journal', 'url': None},
        ]
        return ctx


@method_decorator(login_required, name='dispatch')
class LotTechniqueActionView(View):
    def post(self, request, pk, action):
        org = getattr(request, 'current_org', None)
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').select_for_update().filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=pk,
        )
        if action == 'pret_mise':
            if lot.statut in ['en_cours', 'stabilise']:
                lot.statut = 'pret_mise'
                lot.save(update_fields=['statut'])
                messages.success(request, f"Lot {lot.code} marqué 'Prêt mise'")
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        elif action == 'offsite_send':
            tiers = (request.POST.get('tiers') or '').strip() or None
            try:
                _lot, _op = lot_services.send_offsite(lot=lot, third_party=tiers, meta={'notes': (request.POST.get('notes') or '').strip()}, user=request.user)
                messages.success(request, f"Lot {lot.code} envoyé hors site")
            except Exception as e:
                messages.error(request, f"Erreur envoi hors site: {e}")
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        elif action == 'offsite_return_neutral':
            try:
                _lot, _op = lot_services.return_offsite_neutral(lot=lot, meta={'notes': (request.POST.get('notes') or '').strip()}, user=request.user)
                messages.success(request, f"Retour hors site (neutre) enregistré pour {lot.code}")
            except Exception as e:
                messages.error(request, f"Erreur retour hors site: {e}")
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        elif action == 'offsite_return_non_neutral':
            try:
                child, _op = lot_services.return_offsite_non_neutral(lot=lot, meta={'notes': (request.POST.get('notes') or '').strip()}, user=request.user)
                messages.success(request, f"Retour hors site (non neutre) → nouveau lot {child.code}")
            except Exception as e:
                messages.error(request, f"Erreur retour (non neutre): {e}")
                child = None
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': (child.id if child else lot.id)})
            except Exception:
                url = f"/production/lots-techniques/{(child.id if child else lot.id)}/"
            return redirect(url)
        elif action == 'perte':
            try:
                vol = Decimal(str(request.POST.get('volume_l') or '0'))
            except Exception:
                vol = Decimal('0')
            notes = (request.POST.get('notes') or '').strip()
            if vol <= 0:
                messages.error(request, 'Volume invalide')
                try:
                    url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
                except Exception:
                    url = f"/production/lots-techniques/{lot.id}/"
                return redirect(url)
            # Mouvement perte
            MouvementLot.objects.create(lot=lot, type='PERTE', volume_l=vol, meta={'notes': notes}, author=request.user)
            # Comptabiliser la perte au CMP courant (inchangé)
            try:
                snap = CostSnapshot.objects.filter(entity_type='lottech', entity_id=lot.id).first()
                cmp_vrac = getattr(snap, 'cmp_vrac_eur_l', Decimal('0')) or Decimal('0')
                amount = (cmp_vrac * vol).quantize(Decimal('0.0001'))
                CostEntry.objects.create(
                    organization=getattr(snap, 'organization', None),
                    entity_type='lottech',
                    entity_id=lot.id,
                    nature='vrac_loss',
                    qty=vol,
                    amount_eur=amount,
                    meta={'action': 'perte', 'lot': str(lot.id)},
                    author=request.user,
                )
                _recalc_lottech_snapshot(org_id=snap.organization.id if snap else None, lottech_id=lot.id)
            except Exception:
                pass
            # DRM: perte (vrac)
            try:
                org = getattr(getattr(lot, 'cuvee', None), 'organization', None)
                DRMLine.objects.create(
                    organization=org,
                    date=timezone.now().date(),
                    type='perte',
                    volume_l=vol,
                    ref_kind='perte_vrac',
                    ref_id=lot.id,
                    campagne=getattr(lot, 'campagne', ''),
                )
            except Exception:
                pass
            messages.success(request, f"Perte enregistrée ({vol} L)")
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        elif action == 'transfert':
            # Transfert A (lot) → B
            try:
                vol = Decimal(str(request.POST.get('volume_l') or '0'))
            except Exception:
                vol = Decimal('0')
            dst_id = (request.POST.get('dst_lot_id') or '').strip()
            if vol <= 0 or not dst_id:
                messages.error(request, 'Paramètres transfert invalides')
                try:
                    url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
                except Exception:
                    url = f"/production/lots-techniques/{lot.id}/"
                return redirect(url)
            other = get_object_or_404(
                LotTechnique.objects.select_related('cuvee').select_for_update().filter(Q(cuvee__organization=org) | Q(source__organization=org)),
                pk=dst_id,
            )
            # Ordonner locks par id est déjà garanti par select_for_update sur 2 objets distincts
            # Mouvement OUT sur A, IN sur B
            MouvementLot.objects.create(lot=lot, type='TRANSFERT_OUT', volume_l=vol, meta={'dst': str(other.id)}, author=request.user)
            MouvementLot.objects.create(lot=other, type='TRANSFERT_IN', volume_l=vol, meta={'src': str(lot.id)}, author=request.user)
            messages.success(request, f"Transfert {vol} L de {lot.code} → {other.code} enregistré")
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)
        else:
            messages.error(request, 'Action inconnue')
            try:
                url = reverse('production:lot_tech_detail', kwargs={'pk': lot.id})
            except Exception:
                url = f"/production/lots-techniques/{lot.id}/"
            return redirect(url)


@login_required
def lot_mouvements_export(request, pk):
    org = getattr(request, 'current_org', None)
    lot = get_object_or_404(
        LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
        pk=pk,
    )
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"mouvements_{lot.code}.csv" if lot.code else f"mouvements_{lot.id}.csv"
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(resp, delimiter=';')
    writer.writerow(['date', 'type', 'volume_l', 'meta'])
    for mv in lot.mouvements.order_by('date', 'id'):
        try:
            meta_s = '' if mv.meta is None else str(mv.meta)
        except Exception:
            meta_s = ''
        writer.writerow([
            mv.date.strftime('%Y-%m-%d %H:%M:%S'),
            mv.type,
            f"{mv.volume_l}",
            meta_s,
        ])
    return resp

# =============================================================================
# NOUVELLES VUES DE DASHBOARDS & LOGIQUE MÉTIER (HARMONISATION)
# =============================================================================

@method_decorator(login_required, name='dispatch')
class ProductionHomeView(TemplateView):
    template_name = 'production/dashboard_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        # Breadcrumb
        ctx['page_title'] = 'Production'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': None},
        ]
        
        if not org:
            return ctx

        # KPI: Volume total en vrac (tous statuts sauf epuise/embouteille)
        # On exclut epuise, conditionne_partiel (si vide), etc.
        # Simplification: somme volume_l des lots 'en cours' ou équivalents
        active_statuses = ['en_cours', 'stabilise', 'pret_mise', 'MOUT_ENCUVE', 'MOUT_PRESSE', 
                           'MOUT_DEBOURBE', 'VIN_EN_FA', 'VIN_POST_FA', 'VIN_EN_FML', 
                           'VIN_POST_FML', 'VIN_ELEVAGE', 'VIN_STABILISE', 'VIN_FILTRATION_STERILE', 
                           'VIN_PRET_MISE', 'BASE_EFF', 'SUR_LATTES', 'DEGORGEMENT']
        
        qs_lots = LotTechnique.objects.filter(cuvee__organization=org, statut__in=active_statuses)
        total_vol = qs_lots.aggregate(s=Sum('volume_l'))['s'] or Decimal('0')
        ctx['total_volume_hl'] = total_vol / Decimal('100')

        # KPI: Vendanges en cours (statut != close)
        qs_vendanges = VendangeReception.objects.filter(organization=org).exclude(statut='close')
        ctx['vendanges_active_count'] = qs_vendanges.count()
        
        # KPI: Mises prévues (non réalisées ou récentes)
        # On regarde les mises créées récemment
        from apps.produits.models import Mise
        recent_mises = Mise.objects.filter(lots__cuvee__organization=org).order_by('-date').distinct()[:5]
        ctx['recent_mises'] = recent_mises
        
        # KPI: Derniers mouvements
        ctx['last_moves'] = MouvementLot.objects.filter(lot__cuvee__organization=org).select_related('lot', 'lot__source', 'author').order_by('-date')[:10]
        
        return ctx

@method_decorator(login_required, name='dispatch')
class ProductionVigneView(TemplateView):
    template_name = 'production/dash_vigne.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Vigne'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Vigne', 'url': None},
        ]

        if org:
            ctx['parcelles_count'] = Parcelle.objects.filter(organization=org).count()
            ctx['surface_totale'] = Parcelle.objects.filter(organization=org).aggregate(s=Sum('surface'))['s'] or 0
            ctx['vendanges_count'] = VendangeReception.objects.filter(organization=org).count()
            # Dernières vendanges
            ctx['last_vendanges'] = VendangeReception.objects.filter(organization=org).order_by('-date')[:5]
        
        return ctx

@method_decorator(login_required, name='dispatch')
class ProductionChaiView(TemplateView):
    template_name = 'production/dash_chai.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Chai & Vinification'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Chai', 'url': None},
        ]

        if org:
            # Lots en fermentation ou post-fermentation précoce
            fermenting_statuses = ['MOUT_ENCUVE', 'MOUT_PRESSE', 'MOUT_DEBOURBE', 'VIN_EN_FA', 'VIN_POST_FA', 'VIN_EN_FML']
            qs_ferment = LotTechnique.objects.filter(cuvee__organization=org, statut__in=fermenting_statuses)
            ctx['fermentation_vol_hl'] = (qs_ferment.aggregate(s=Sum('volume_l'))['s'] or Decimal('0')) / Decimal('100')
            ctx['fermentation_count'] = qs_ferment.count()
            
            # Lots à surveiller (exemple simple: dernière mesure > 7 jours - mockup logic)
            # Ici on liste simplement les derniers lots créés
            ctx['latest_lots'] = LotTechnique.objects.filter(cuvee__organization=org).order_by('-created_at')[:5]
            
            # Nombre d'encuvages actifs (basé sur VendangeReception statut encuvee)
            ctx['encuvages_count'] = VendangeReception.objects.filter(organization=org, statut='encuvee').count()

        return ctx

@method_decorator(login_required, name='dispatch')
class ProductionElevageView(TemplateView):
    template_name = 'production/dash_elevage.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Suivi & Élevage'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Élevage', 'url': None},
        ]

        if org:
            elevage_statuses = ['VIN_ELEVAGE', 'VIN_STABILISE', 'VIN_FILTRATION_STERILE', 'VIN_PRET_MISE', 'stabilise', 'pret_mise']
            qs_elevage = LotTechnique.objects.filter(cuvee__organization=org, statut__in=elevage_statuses)
            ctx['elevage_vol_hl'] = (qs_elevage.aggregate(s=Sum('volume_l'))['s'] or Decimal('0')) / Decimal('100')
            ctx['elevage_count'] = qs_elevage.count()
            
            # Dernières analyses (mockup ou CostEntry type 'analyse' si on avait)
            # On affiche les lots modifiés récemment
            ctx['active_lots'] = qs_elevage.order_by('-created_at')[:10]

        return ctx

@method_decorator(login_required, name='dispatch')
class ProductionConditionnementView(TemplateView):
    template_name = 'production/dash_conditionnement.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Conditionnement'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Conditionnement', 'url': None},
        ]
        
        if org:
            from apps.produits.models import Mise
            qs_mises = Mise.objects.filter(lots__cuvee__organization=org).distinct()
            ctx['mises_count'] = qs_mises.count()
            ctx['last_mises'] = qs_mises.order_by('-date')[:5]
            
            # Stock produits finis (SKU)
            from apps.stock.models import SKU
            ctx['skus_count'] = SKU.objects.filter(organization=org, is_active=True).count()

        return ctx

@method_decorator(login_required, name='dispatch')
class EncuvageListView(ListView):
    """Vue dédiée à la liste des encuvages (Lots en phase initiale ou Vendanges encuvées)."""
    model = LotTechnique
    template_name = 'production/encuvages_list.html'
    context_object_name = 'lots'
    paginate_by = 50

    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        if not org:
            return LotTechnique.objects.none()
        
        # Statuts correspondant à la phase "Encuvage / Vinification primaire"
        statuses = ['MOUT_ENCUVE', 'MOUT_PRESSE', 'MOUT_DEBOURBE', 'VIN_EN_FA']
        return LotTechnique.objects.filter(
            cuvee__organization=org,
            statut__in=statuses
        ).select_related('cuvee', 'source').order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Encuvages'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Chai', 'url': '/production/chai/'},
            {'name': 'Encuvages', 'url': None},
        ]
        
        # Ajouter aussi les vendanges "à encuver" (non encuvées, avec kg restants)
        org = getattr(self.request, 'current_org', None)
        if org:
            vendanges_todo = []
            # Vendanges qui ont du poids, pas statut clos, et potentiellement pas encore tout encuvé
            qs_v = VendangeReception.objects.filter(organization=org).exclude(statut='close').order_by('date')
            for v in qs_v:
                if v.kg_restant > 0:
                    vendanges_todo.append(v)
            ctx['vendanges_todo'] = vendanges_todo
            
        return ctx
